"""
Section-Level Semantic Chunker

Chunks regulatory documents at section boundaries while preserving structure.
"""

import logging
import re
from typing import Dict, List

from langchain.text_splitter import MarkdownHeaderTextSplitter

from rag.ingestion.models import ChunkMetadata, CcopChunk, QAPair
from rag.ingestion.parsers.ccop_pdf_parser import parse_all_ccop_documents
from rag.ingestion.parsers.feedback_qa_parser import parse_feedback_qa

logger = logging.getLogger(__name__)


def chunk_document(markdown_text: str, document_name: str) -> List[CcopChunk]:
    """
    Chunk a CCoP document by section boundaries.

    Uses MarkdownHeaderTextSplitter to split at section/subsection boundaries,
    then enriches each chunk with metadata (section, clause, citation_id).
    Applies size constraints (min 200 tokens, max 1000 tokens).

    Args:
        markdown_text: Markdown text from PDF parser
        document_name: Source document name

    Returns:
        List of CcopChunk objects with metadata
    """
    logger.info(f"Chunking document: {document_name}")

    # Define header hierarchy for splitting
    headers_to_split_on = [
        ("#", "Document"),
        ("##", "Section"),
        ("###", "Subsection"),
    ]

    # Split by headers
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,  # Keep headers for context
    )

    try:
        initial_chunks = markdown_splitter.split_text(markdown_text)
    except Exception as e:
        logger.warning(f"MarkdownHeaderTextSplitter failed for {document_name}: {e}")
        # Fallback: treat entire document as single chunk
        initial_chunks = [type("Document", (), {"page_content": markdown_text, "metadata": {}})]

    logger.info(f"Initial split produced {len(initial_chunks)} chunks for {document_name}")

    # Enrich chunks with metadata and apply size constraints
    enriched_chunks = []
    merged_buffer = None

    for i, chunk in enumerate(initial_chunks):
        # Extract metadata from chunk
        section = chunk.metadata.get("Section", "")
        subsection = chunk.metadata.get("Subsection", "")

        # Extract clause number from first 200 chars
        clause = _extract_clause_number(chunk.page_content[:200])

        # Create citation ID
        citation_id = _create_citation_id(document_name, section, clause)

        # Token count approximation (word count)
        token_count = len(chunk.page_content.split())

        # Apply size constraints
        if token_count < 200:
            # Chunk too small - merge with previous or buffer for next
            if merged_buffer is None:
                merged_buffer = {
                    "text": chunk.page_content,
                    "section": section,
                    "subsection": subsection,
                    "clause": clause,
                    "citation_id": citation_id,
                }
            else:
                # Merge with buffer
                merged_buffer["text"] += "\n\n" + chunk.page_content
                # Keep first section/clause info
            continue
        elif token_count > 1000:
            # Chunk too large - recursively split on paragraph boundaries
            split_chunks = _split_large_chunk(
                chunk.page_content, document_name, section, subsection, clause
            )
            enriched_chunks.extend(split_chunks)
            continue

        # Flush merged buffer if exists
        if merged_buffer:
            enriched_chunks.append(
                _create_chunk(
                    merged_buffer["text"],
                    document_name,
                    merged_buffer["section"],
                    merged_buffer["subsection"],
                    merged_buffer["clause"],
                    len(enriched_chunks),
                )
            )
            merged_buffer = None

        # Add current chunk
        enriched_chunks.append(
            _create_chunk(chunk.page_content, document_name, section, subsection, clause, len(enriched_chunks))
        )

    # Don't forget final merged buffer
    if merged_buffer:
        enriched_chunks.append(
            _create_chunk(
                merged_buffer["text"],
                document_name,
                merged_buffer["section"],
                merged_buffer["subsection"],
                merged_buffer["clause"],
                len(enriched_chunks),
            )
        )

    logger.info(
        f"Produced {len(enriched_chunks)} chunks for {document_name} "
        f"(min: {min((len(c.text.split()) for c in enriched_chunks), default=0)} tokens, "
        f"max: {max((len(c.text.split()) for c in enriched_chunks), default=0)} tokens, "
        f"avg: {sum(len(c.text.split()) for c in enriched_chunks) // len(enriched_chunks) if enriched_chunks else 0} tokens)"
    )

    return enriched_chunks


def chunk_qa_pairs(qa_pairs: List[QAPair], document_name: str) -> List[CcopChunk]:
    """
    Convert Q&A pairs into CcopChunk objects.

    Args:
        qa_pairs: List of QAPair objects
        document_name: Source document name

    Returns:
        List of CcopChunk objects
    """
    chunks = []

    for i, qa in enumerate(qa_pairs):
        # Format text as "Q: ... A: ..."
        text = f"Q: {qa.question}\n\nA: {qa.answer}"

        chunk = CcopChunk(
            id=f"{document_name}-qa-{i}",
            text=text,
            metadata=qa.metadata,
        )
        chunks.append(chunk)

    logger.info(f"Converted {len(chunks)} Q&A pairs to chunks")

    return chunks


def chunk_all_documents(parsed_docs: Dict[str, str], ccop_dir: str) -> List[CcopChunk]:
    """
    Orchestrate parsing and chunking for all 8 CCoP documents.

    Args:
        parsed_docs: Dictionary of document_name -> markdown text
        ccop_dir: Base directory (used for parsing RESPONSE-TO-FEEDBACK separately)

    Returns:
        Combined list of all chunks from all documents
    """
    logger.info("Chunking all CCoP documents")

    all_chunks = []

    for doc_name, markdown in parsed_docs.items():
        # Standard section-level chunking for all documents
        chunks = chunk_document(markdown, doc_name)

        # Mark RESPONSE-TO-FEEDBACK chunks as clarifications
        if doc_name == "CCoP Response to Feedback":
            for chunk in chunks:
                chunk.metadata.document_type = "clarification"

        all_chunks.extend(chunks)
        logger.info(f"  {doc_name}: {len(chunks)} chunks")

    logger.info(f"Total chunks across all documents: {len(all_chunks)}")

    # Chunk size statistics
    token_counts = [len(c.text.split()) for c in all_chunks]
    logger.info(
        f"Chunk size stats: min={min(token_counts, default=0)}, "
        f"max={max(token_counts, default=0)}, "
        f"avg={sum(token_counts) // len(token_counts) if token_counts else 0}"
    )

    return all_chunks


# Helper functions


def _extract_clause_number(text: str) -> str:
    """Extract clause number from text (e.g., '5.2.1')."""
    match = re.search(r"\b(\d+\.\d+\.?\d*)\b", text)
    return match.group(1) if match else ""


def _create_citation_id(document_name: str, section: str, clause: str) -> str:
    """Create citation ID from document, section, and clause."""
    # Sanitize document name for citation ID
    doc_id = document_name.replace(" ", "-").replace(".", "")
    if clause:
        return f"{doc_id}.{section}.{clause}"
    else:
        return f"{doc_id}.{section}" if section else doc_id


def _create_chunk(
    text: str, document_name: str, section: str, subsection: str, clause: str, index: int
) -> CcopChunk:
    """Create a CcopChunk with metadata."""
    citation_id = _create_citation_id(document_name, section, clause)

    metadata = ChunkMetadata(
        document_source=document_name,
        section=section,
        subsection=subsection,
        clause=clause,
        citation_id=citation_id,
    )

    return CcopChunk(
        id=f"{document_name}-{index}",
        text=text,
        metadata=metadata,
    )


def _split_large_chunk(
    text: str, document_name: str, section: str, subsection: str, clause: str
) -> List[CcopChunk]:
    """
    Recursively split chunks larger than 1000 tokens.

    Splits on paragraph boundaries (double newlines).
    If a single paragraph exceeds 1000 tokens, splits on sentences.
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para_token_count = len(para.split())

        # If single paragraph exceeds limit, split it further on sentences
        if para_token_count > 1000:
            # Split on sentences (period followed by space or newline)
            import re
            sentences = re.split(r'(?<=[.!?])\s+', para)

            for sent in sentences:
                test_chunk = current_chunk + " " + sent if current_chunk else sent
                if len(test_chunk.split()) > 1000:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sent
                else:
                    current_chunk = test_chunk
        else:
            # Normal paragraph handling
            test_chunk = current_chunk + "\n\n" + para if current_chunk else para
            token_count = len(test_chunk.split())

            if token_count > 1000:
                # Flush current chunk
                if current_chunk:
                    chunks.append(current_chunk)
                # Start new chunk with current paragraph
                current_chunk = para
            else:
                current_chunk = test_chunk

    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk)

    # Convert to CcopChunk objects
    return [
        _create_chunk(chunk_text, document_name, section, subsection, clause, i)
        for i, chunk_text in enumerate(chunks)
    ]
