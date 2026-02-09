"""
Citation Resolver

Extracts citation IDs from LLM generation and resolves them to
document metadata (document, section, clause).
"""

import logging
import re
from typing import TypedDict

logger = logging.getLogger(__name__)


class Citation(TypedDict):
    """Citation metadata structure."""

    document: str
    section: str
    clause: str
    citation_id: str
    document_type: str


def extract_citation_ids(generation: str) -> list[str]:
    """
    Extract citation IDs from LLM generation.

    Extracts all citation anchors in format <c>citation_id</c>
    from the generated text.

    Args:
        generation: LLM output text with citation anchors

    Returns:
        List of unique citation IDs in order of appearance

    Examples:
        >>> extract_citation_ids("Based on <c>CCoP-2.0.5.5.2.1</c> and <c>CCoP-2.0.3.3.1</c>")
        ['CCoP-2.0.5.5.2.1', 'CCoP-2.0.3.3.1']

        >>> extract_citation_ids("No citations here")
        []
    """
    if not generation:
        return []

    # Extract citation IDs using regex
    pattern = r"<c>(.*?)</c>"
    matches = re.findall(pattern, generation)

    # Return unique IDs in order of appearance
    seen = set()
    unique_ids = []
    for citation_id in matches:
        if citation_id not in seen:
            seen.add(citation_id)
            unique_ids.append(citation_id)

    logger.debug(f"Extracted {len(unique_ids)} unique citations from generation")

    return unique_ids


def resolve_citations(citation_ids: list[str], documents: list) -> list[Citation]:
    """
    Resolve citation IDs to document metadata.

    Matches citation IDs against LangChain Document objects and
    extracts metadata for end-of-response references.

    Args:
        citation_ids: List of citation IDs to resolve
        documents: LangChain Document objects with metadata

    Returns:
        List of Citation dicts with document, section, clause, etc.

    Notes:
        - Deduplicates: same citation_id appears only once
        - Missing citations: logged as warning, skipped (no crash)
    """
    if not citation_ids:
        return []

    # Build lookup map: citation_id -> document
    citation_map = {}
    for doc in documents:
        cid = doc.metadata.get("citation_id", "")
        if cid:
            citation_map[cid] = doc

    # Resolve citations
    resolved = []
    seen_ids = set()

    for citation_id in citation_ids:
        # Skip duplicates
        if citation_id in seen_ids:
            continue

        seen_ids.add(citation_id)

        # Find matching document
        if citation_id not in citation_map:
            logger.warning(f"Citation ID not found in documents: {citation_id}")
            continue

        doc = citation_map[citation_id]
        metadata = doc.metadata

        # Extract citation metadata
        citation: Citation = {
            "document": metadata.get("document_source", "Unknown Document"),
            "section": metadata.get("section", ""),
            "clause": metadata.get("clause", ""),
            "citation_id": citation_id,
            "document_type": metadata.get("document_type", "standard"),
        }

        resolved.append(citation)

    logger.debug(
        f"Resolved {len(resolved)}/{len(citation_ids)} citations "
        f"({len(citation_ids) - len(resolved)} missing)"
    )

    return resolved


def build_citations_from_state(state: dict) -> list[Citation]:
    """
    Convenience function to build citations from graph state.

    Extracts citation IDs from state["generation"] and resolves them
    against state["filtered_documents"].

    Args:
        state: LangGraph state with 'generation' and 'filtered_documents'

    Returns:
        List of resolved Citation dicts

    Notes:
        Used by generation node to post-process LLM output.
    """
    generation = state.get("generation", "")
    documents = state.get("filtered_documents", [])

    citation_ids = extract_citation_ids(generation)
    citations = resolve_citations(citation_ids, documents)

    return citations
