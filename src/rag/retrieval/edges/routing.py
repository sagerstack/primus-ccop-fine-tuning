"""
Routing Logic

Conditional edge functions for LangGraph routing decisions.
"""

import logging

from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def route_by_mode(state: GraphState) -> str:
    """
    Route based on pipeline mode.

    First routing decision after query_analysis.

    Args:
        state: Current graph state with 'mode'

    Returns:
        "graph_retrieval" for graphrag, "retrieval" for hybrid/rag-only,
        "fallback" for llm-only
    """
    mode = state.get("mode", "hybrid")

    if mode == "llm-only":
        logger.info("Routing: mode=llm-only -> fallback node")
        return "fallback"

    if mode == "graphrag":
        # Graph retrieval (Phase 9): swaps ONLY the retrieval node — the
        # graph provides contexts, the unchanged primus `generate` node still
        # produces the scored answer (D-06).
        logger.info("Routing: mode=graphrag -> graph_retrieval node")
        return "graph_retrieval"

    logger.info(f"Routing: mode={mode} -> retrieval node")
    return "retrieval"


def decide_after_grading(state: GraphState) -> str:
    """
    Decide next step after document grading.

    Routes based on mode and retrieval results:
    - rag-only: always → rag_response (no LLM generation)
    - hybrid + docs found: → generate
    - hybrid + no docs: → fallback

    Args:
        state: Current graph state

    Returns:
        "generate" | "fallback" | "rag_response"
    """
    mode = state.get("mode", "hybrid")

    if mode == "rag-only":
        logger.info("Routing: mode=rag-only -> rag_response node")
        return "rag_response"

    retrieval_succeeded = state.get("retrieval_succeeded", False)

    if retrieval_succeeded:
        logger.info("Routing: relevant documents found -> generate node")
        return "generate"

    logger.warning("Routing: no relevant documents -> fallback node")
    return "fallback"
