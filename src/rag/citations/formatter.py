"""
Citation Formatter

Formats responses with end-of-response citations.
Removes citation anchors and appends clean reference list.
"""

import logging
import re

from rag.citations.resolver import Citation

logger = logging.getLogger(__name__)


def format_response_with_citations(generation: str, citations: list[Citation]) -> str:
    """
    Format response with end-of-response citations.

    Removes citation anchors from text and appends formatted references
    at the end of the response.

    Args:
        generation: Raw LLM output with <c>...</c> anchors
        citations: Resolved citation metadata

    Returns:
        Formatted response with clean text and end-of-response references

    Examples:
        >>> citations = [
        ...     {"document": "CCoP 2.0", "section": "Section 5: Access Control",
        ...      "clause": "5.2.1", "citation_id": "...", "document_type": "standard"}
        ... ]
        >>> format_response_with_citations(
        ...     "Based on <c>CCoP-2.0.5.5.2.1</c>, access control...",
        ...     citations
        ... )
        'Based on , access control...\\n\\nReferences:\\n[1] CCoP 2.0, Section 5: Access Control, Clause 5.2.1'
    """
    if not generation:
        return ""

    # Remove citation anchors from text
    clean_text = re.sub(r"<c>.*?</c>", "", generation)

    # If no citations, return clean text only
    if not citations:
        return clean_text.strip()

    # Build references section
    references = ["\n\nReferences:"]

    for idx, citation in enumerate(citations, start=1):
        # Build reference line: [1] Document, Section, Clause
        parts = [f"[{idx}]", citation["document"]]

        # Add section if present
        section = citation.get("section", "").strip()
        if section:
            parts.append(section)

        # Add clause if present
        clause = citation.get("clause", "").strip()
        if clause:
            parts.append(f"Clause {clause}")

        reference_line = " ".join(parts)
        references.append(reference_line)

    # Join text and references
    formatted_response = clean_text.strip() + "\n".join(references)

    logger.debug(f"Formatted response with {len(citations)} citations")

    return formatted_response


def format_model_only_response(generation: str) -> str:
    """
    Format model-only response with notice.

    Prepends a notice indicating the response is based on model knowledge
    only, not grounded in specific document retrieval.

    Args:
        generation: LLM output from fallback generation

    Returns:
        Formatted response with notice

    Examples:
        >>> format_model_only_response("Access control requires...")
        '[Note: This response is based on model knowledge only, not grounded in specific CCoP document retrieval.]\\n\\nAccess control requires...'
    """
    if not generation:
        return ""

    notice = (
        "[Note: This response is based on model knowledge only, "
        "not grounded in specific CCoP document retrieval.]"
    )

    formatted_response = f"{notice}\n\n{generation.strip()}"

    logger.debug("Formatted model-only response with notice")

    return formatted_response
