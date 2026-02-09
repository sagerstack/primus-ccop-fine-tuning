"""
Citation Resolution and Formatting

Transforms raw citation anchors (<c>citation_id</c>) from LLM output
into human-readable end-of-response references.
"""

from rag.citations.formatter import format_model_only_response, format_response_with_citations
from rag.citations.resolver import build_citations_from_state, extract_citation_ids, resolve_citations

__all__ = [
    "extract_citation_ids",
    "resolve_citations",
    "build_citations_from_state",
    "format_response_with_citations",
    "format_model_only_response",
]
