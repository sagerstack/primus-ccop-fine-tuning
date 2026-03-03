"""
Section-Level Semantic Chunker

Chunks regulatory documents at section boundaries while preserving structure.
"""

import logging
import re
from typing import List

from langchain.text_splitter import MarkdownHeaderTextSplitter

from rag.ingestion.models import ChunkMetadata, CcopChunk, QAPair

logger = logging.getLogger(__name__)


def chunk_document(
    markdown_text: str,
    document_name: str,
    min_tokens: int = 200,
    max_tokens: int = 1000,
) -> List[CcopChunk]:
    """
    Chunk a CCoP document by section boundaries.

    Uses MarkdownHeaderTextSplitter to split at section/subsection boundaries,
    then enriches each chunk with metadata (section, clause, citation_id).
    Applies size constraints (min min_tokens, max max_tokens).

    Args:
        markdown_text: Markdown text from PDF parser
        document_name: Source document name
        min_tokens: Merge threshold - chunks smaller than this are merged
        max_tokens: Split threshold - chunks larger than this are split

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
        if token_count < min_tokens:
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
        elif token_count > max_tokens:
            # Chunk too large - recursively split on paragraph boundaries
            split_chunks = _split_large_chunk(
                chunk.page_content, document_name, section, subsection, clause, max_tokens
            )
            enriched_chunks.extend(split_chunks)
            continue

        # Flush merged buffer if exists
        if merged_buffer:
            enriched_chunks.extend(
                _flush_buffer(merged_buffer, document_name, len(enriched_chunks), max_tokens)
            )
            merged_buffer = None

        # Add current chunk
        enriched_chunks.append(
            _create_chunk(chunk.page_content, document_name, section, subsection, clause, len(enriched_chunks))
        )

    # Don't forget final merged buffer
    if merged_buffer:
        enriched_chunks.extend(
            _flush_buffer(merged_buffer, document_name, len(enriched_chunks), max_tokens)
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


# Helper functions


def _flush_buffer(
    buffer: dict, document_name: str, start_index: int, max_tokens: int
) -> List[CcopChunk]:
    """
    Flush a merged buffer, splitting if it exceeds max_tokens.

    Returns one or more CcopChunks.
    """
    word_count = len(buffer["text"].split())
    if word_count > max_tokens:
        return _split_large_chunk(
            buffer["text"],
            document_name,
            buffer["section"],
            buffer["subsection"],
            buffer["clause"],
            max_tokens,
        )
    return [
        _create_chunk(
            buffer["text"],
            document_name,
            buffer["section"],
            buffer["subsection"],
            buffer["clause"],
            start_index,
        )
    ]


def _extract_clause_number(text: str) -> str:
    """Extract clause number from text (e.g., '5.2.1')."""
    match = re.search(r"\b(\d+\.\d+\.?\d*)\b", text)
    return match.group(1) if match else ""


def _create_citation_id(document_name: str, section: str, clause: str) -> str:
    """Create citation ID from document, section, and clause."""
    if clause:
        return f"{document_name}::{section}::{clause}"
    elif section:
        return f"{document_name}::{section}"
    else:
        return document_name


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
        id=f"{document_name}::section::{index}",
        text=text,
        metadata=metadata,
    )


def _split_large_chunk(
    text: str, document_name: str, section: str, subsection: str, clause: str,
    max_tokens: int = 1000,
) -> List[CcopChunk]:
    """
    Recursively split chunks larger than max_tokens.

    Splits on paragraph boundaries (double newlines).
    If a single paragraph exceeds max_tokens, splits on sentences.
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para_token_count = len(para.split())

        # If single paragraph exceeds limit, split it further on sentences
        if para_token_count > max_tokens:
            sentences = re.split(r'(?<=[.!?])\s+', para)

            for sent in sentences:
                test_chunk = current_chunk + " " + sent if current_chunk else sent
                if len(test_chunk.split()) > max_tokens:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sent
                else:
                    current_chunk = test_chunk
        else:
            # Normal paragraph handling
            test_chunk = current_chunk + "\n\n" + para if current_chunk else para
            token_count = len(test_chunk.split())

            if token_count > max_tokens:
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
