"""
Clause-Aware Chunker

Chunks regulatory documents at clause boundaries using regex pattern matching.
Each chunk maps to one regulatory requirement with clause-level granularity.
"""

import logging
import re
from typing import Dict, List

from rag.ingestion.models import ChunkMetadata, CcopChunk

logger = logging.getLogger(__name__)

# Regex pattern for CCoP clause numbering (e.g., "5.2.1 The CIIO shall...")
CLAUSE_PATTERN = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+?)$", re.MULTILINE)


def chunk_by_clauses(
    markdown_text: str, document_name: str, preamble_max_words: int = 500
) -> List[CcopChunk]:
    """
    Chunk a CCoP document by clause boundaries.

    Uses regex pattern matching to split at numbered clause boundaries
    (e.g., "5.2.1 The CIIO shall..."). Each chunk represents one regulatory
    requirement with deterministic ID.

    Args:
        markdown_text: Markdown text from Docling parser
        document_name: Source document name
        preamble_max_words: Max words for a single preamble chunk before splitting

    Returns:
        List of CcopChunk objects with clause-level metadata
    """
    logger.info(f"Chunking document by clauses: {document_name}")

    # Filter boilerplate before chunking
    filtered_text = _filter_boilerplate(markdown_text)

    chunks = []
    merge_buffer = None

    # Split on clause boundaries
    parts = CLAUSE_PATTERN.split(filtered_text)

    # Handle pre-clause content (text before first numbered clause)
    if parts and parts[0].strip():
        preamble_text = parts[0].strip()
        word_count = len(preamble_text.split())

        if word_count > 50:
            if word_count <= preamble_max_words:
                metadata = ChunkMetadata(
                    document_source=document_name,
                    section="preamble",
                    clause="",
                    citation_id=f"{document_name}::preamble",
                    parent_path="Preamble",
                    chapter="0",
                )
                chunks.append(
                    CcopChunk(
                        id=f"{document_name}::preamble",
                        text=preamble_text,
                        metadata=metadata,
                    )
                )
                logger.info(f"  Created preamble chunk: {word_count} words")
            else:
                preamble_chunks = _split_preamble(
                    preamble_text, document_name, preamble_max_words
                )
                chunks.extend(preamble_chunks)
                logger.info(
                    f"  Split oversized preamble ({word_count} words) "
                    f"into {len(preamble_chunks)} sub-chunks"
                )

    # Process clause groups (groups of 3: clause_number, heading, content)
    i = 1 if parts[0].strip() else 0
    while i < len(parts) - 2:
        clause_number = parts[i].strip()
        clause_heading = parts[i + 1].strip()
        clause_content = parts[i + 2].strip() if i + 2 < len(parts) else ""

        # Build chunk text
        chunk_text = f"{clause_number} {clause_heading}\n\n{clause_content}".strip()

        # Word count for size check
        word_count = len(chunk_text.split())

        # Check if this is a tiny chunk that should be merged
        if word_count < 30:
            # Merge with previous chunk or buffer for next
            if merge_buffer is None:
                merge_buffer = {
                    "text": chunk_text,
                    "clause_number": clause_number,
                    "clause_heading": clause_heading,
                }
            else:
                # Merge with buffer
                merge_buffer["text"] += "\n\n" + chunk_text
            i += 3
            continue

        # Flush merge buffer if exists
        if merge_buffer:
            merged_chunk = _create_clause_chunk(
                merge_buffer["text"],
                document_name,
                merge_buffer["clause_number"],
            )
            chunks.append(merged_chunk)
            merge_buffer = None

        # Create chunk
        chunk = _create_clause_chunk(chunk_text, document_name, clause_number)
        chunks.append(chunk)

        i += 3

    # Don't forget final merge buffer
    if merge_buffer:
        merged_chunk = _create_clause_chunk(
            merge_buffer["text"],
            document_name,
            merge_buffer["clause_number"],
        )
        chunks.append(merged_chunk)

    logger.info(
        f"Produced {len(chunks)} clause-level chunks for {document_name} "
        f"(avg: {sum(len(c.text.split()) for c in chunks) // len(chunks) if chunks else 0} tokens)"
    )

    return chunks


def chunk_all_documents_by_clauses(
    parsed_docs: Dict[str, str], preamble_max_words: int = 500
) -> List[CcopChunk]:
    """
    Chunk all CCoP documents by clause boundaries.

    Args:
        parsed_docs: Dictionary mapping document name to markdown text
        preamble_max_words: Max words for a single preamble chunk before splitting

    Returns:
        Combined list of all chunks from all documents
    """
    logger.info("Chunking all CCoP documents by clauses")

    all_chunks = []

    for doc_name, markdown in parsed_docs.items():
        chunks = chunk_by_clauses(markdown, doc_name, preamble_max_words)

        # Mark RESPONSE-TO-FEEDBACK chunks as clarifications
        if doc_name == "CCoP Response to Feedback":
            for chunk in chunks:
                chunk.metadata.document_type = "clarification"

        all_chunks.extend(chunks)
        logger.info(f"  {doc_name}: {len(chunks)} chunks")

    logger.info(f"Total chunks across all documents: {len(all_chunks)}")

    # Chunk size statistics
    token_counts = [len(c.text.split()) for c in all_chunks]
    if token_counts:
        logger.info(
            f"Chunk size stats: min={min(token_counts)}, "
            f"max={max(token_counts)}, "
            f"avg={sum(token_counts) // len(token_counts)}"
        )

    return all_chunks


def _split_preamble(
    preamble_text: str, document_name: str, max_words: int
) -> List[CcopChunk]:
    """
    Split an oversized preamble into sub-chunks on paragraph boundaries.

    Args:
        preamble_text: Full preamble text
        document_name: Source document name
        max_words: Maximum words per sub-chunk

    Returns:
        List of preamble sub-chunks
    """
    paragraphs = preamble_text.split("\n\n")
    sub_chunks = []
    current_text = ""

    for para in paragraphs:
        test_text = f"{current_text}\n\n{para}".strip() if current_text else para
        if len(test_text.split()) > max_words and current_text:
            sub_chunks.append(current_text)
            current_text = para
        else:
            current_text = test_text

    if current_text:
        sub_chunks.append(current_text)

    chunks = []
    for idx, text in enumerate(sub_chunks, 1):
        chunk_id = f"{document_name}::preamble::{idx}"
        metadata = ChunkMetadata(
            document_source=document_name,
            section="preamble",
            clause="",
            citation_id=chunk_id,
            parent_path="Preamble",
            chapter="0",
        )
        chunks.append(CcopChunk(id=chunk_id, text=text, metadata=metadata))

    return chunks


def _filter_boilerplate(markdown_text: str) -> str:
    """
    Filter out table of contents and page header/footer artifacts.

    This is a best-effort filter. Docling's structural labels handle most cases,
    but regex fallback catches remaining noise.

    Args:
        markdown_text: Raw markdown text

    Returns:
        Filtered markdown text
    """
    lines = markdown_text.split("\n")
    filtered_lines = []

    skip_until_next_heading = False

    for line in lines:
        # Detect table of contents
        if re.search(
            r"^(table of contents|contents|toc)$", line.strip(), re.IGNORECASE
        ):
            skip_until_next_heading = True
            continue

        # Stop skipping at next heading
        if skip_until_next_heading and line.strip().startswith("#"):
            skip_until_next_heading = False

        if skip_until_next_heading:
            continue

        # Filter page headers/footers
        if re.search(r"^page\s+\d+\s+of\s+\d+$", line.strip(), re.IGNORECASE):
            continue
        if re.search(r"^ccop\s+2\.0", line.strip(), re.IGNORECASE):
            continue
        if re.match(r"^\d+$", line.strip()):  # Standalone page numbers
            continue

        filtered_lines.append(line)

    return "\n".join(filtered_lines)


def _extract_section(clause_number: str) -> str:
    """
    Extract parent section from clause number.

    Examples:
        "5.2.1" -> "5.2"
        "5.2.1.1" -> "5.2.1"
        "5" -> "5"

    Args:
        clause_number: Clause number (e.g., "5.2.1")

    Returns:
        Parent section (e.g., "5.2")
    """
    if "." in clause_number:
        return clause_number.rsplit(".", 1)[0]
    return clause_number


def _build_parent_path(clause_number: str) -> str:
    """
    Build hierarchy path from clause number.

    Examples:
        "5.2.1" -> "Chapter 5 > Section 5.2 > 5.2.1"
        "5.2" -> "Chapter 5 > Section 5.2"
        "5" -> "Chapter 5"

    Args:
        clause_number: Clause number (e.g., "5.2.1")

    Returns:
        Hierarchy path string
    """
    parts = clause_number.split(".")

    if len(parts) == 1:
        return f"Chapter {parts[0]}"
    elif len(parts) == 2:
        return f"Chapter {parts[0]} > Section {clause_number}"
    else:
        # Multi-level clause
        section = ".".join(parts[:2])
        return f"Chapter {parts[0]} > Section {section} > {clause_number}"


def _create_clause_chunk(
    chunk_text: str, document_name: str, clause_number: str
) -> CcopChunk:
    """
    Create a CcopChunk with clause-level metadata.

    Args:
        chunk_text: Chunk text content
        document_name: Source document name
        clause_number: Clause number (e.g., "5.2.1")

    Returns:
        CcopChunk with populated metadata
    """
    section = _extract_section(clause_number)
    parent_path = _build_parent_path(clause_number)
    chapter = clause_number.split(".")[0]
    citation_id = f"{document_name}::{clause_number}"
    chunk_id = citation_id  # Same as citation_id - deterministic

    metadata = ChunkMetadata(
        document_source=document_name,
        section=section,
        clause=clause_number,
        citation_id=citation_id,
        parent_path=parent_path,
        chapter=chapter,
    )

    return CcopChunk(
        id=chunk_id,
        text=chunk_text,
        metadata=metadata,
    )
