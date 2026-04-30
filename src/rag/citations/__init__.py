"""
Citation Resolution and Formatting

Parses the model's `**Sources:**` markdown footer into structured records.
Single-block format — the 3-block design (Sources / Cross-references /
Other Sources) was reverted because it produced citations-only degenerate
responses where the model emitted blocks without answer prose.
"""

from rag.citations.formatter import format_model_only_response, format_response_with_citations
from rag.citations.resolver import (
    build_citations_from_state,
    extract_citation_ids,
    parse_citations,
    resolve_citations,
)

__all__ = [
    "extract_citation_ids",
    "parse_citations",
    "resolve_citations",
    "build_citations_from_state",
    "format_response_with_citations",
    "format_model_only_response",
]
