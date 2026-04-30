"""
Citation Formatter

Pass-through for the model's response. The model emits its own
`<Sources>...</Sources>` footer block, which is preserved verbatim in the
final response body — no auto-built References footer is appended.

The model-only-response notice (used in non-RAG fallback paths) is kept here.
"""

import logging

from rag.citations.resolver import Citation

logger = logging.getLogger(__name__)


def format_response_with_citations(generation: str, citations: list[Citation]) -> str:
    """
    Pass through the model's response unchanged.

    The model is responsible for emitting its own `<Sources>` block. The
    `citations` argument is accepted for backward compatibility with callers
    but no longer drives any rendering — structured citation metadata flows
    via state["citations"] for audit/panel use, separate from this function.

    Args:
        generation: LLM output text (already includes the model's `<Sources>` block)
        citations: Resolved citation metadata (unused here; kept for compat)

    Returns:
        The generation text, stripped of trailing whitespace.
    """
    if not generation:
        return ""
    return generation.strip()


def format_model_only_response(generation: str) -> str:
    """
    Format model-only response with notice.

    Prepends a notice indicating the response is based on model knowledge
    only, not grounded in specific document retrieval.

    Args:
        generation: LLM output from fallback generation

    Returns:
        Formatted response with notice
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
