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
        "graph_retrieval" for graphrag/graphrag-retrieval, "retrieval" for
        hybrid/rag-only, "fallback" for llm-only
    """
    mode = state.get("mode", "hybrid")

    if mode == "llm-only":
        logger.info("Routing: mode=llm-only -> fallback node")
        return "fallback"

    if mode in ("graphrag", "graphrag-retrieval"):
        # Graph retrieval (Phase 9): swaps ONLY the retrieval node — the
        # graph provides contexts. For `graphrag` the unchanged primus
        # `generate` node still produces the scored answer (D-06); for
        # `graphrag-retrieval` (the rag-only analog) decide_after_grading
        # routes straight to rag_response with no generation.
        logger.info(f"Routing: mode={mode} -> graph_retrieval node")
        return "graph_retrieval"

    if mode == "graphrag-ontology":
        # Ontology-grounded graph retrieval (Phase 10, D-16 additivity): a
        # SEPARATE branch from `graphrag` above — this plan (10-02) closes
        # RESEARCH Pitfall 3, so the route key is intentionally DISTINCT
        # ("graph_retrieval_ontology") even though it targets the SAME
        # `graph_retrieval` node in the compiled graph (see
        # rag/retrieval/graph.py's conditional-edge map). The node itself is
        # mode-aware (graph_retrieve_documents) and selects
        # container.graph_retrieval_provider_ontology() vs
        # container.graph_retrieval_provider() based on state["mode"] — this
        # branch's job is solely to prove the route is distinguishable, not
        # to duplicate the node.
        logger.info(f"Routing: mode={mode} -> graph_retrieval node (ontology provider)")
        return "graph_retrieval_ontology"

    logger.info(f"Routing: mode={mode} -> retrieval node")
    return "retrieval"


def decide_after_grading(state: GraphState) -> str:
    """
    Decide next step after document grading.

    Routes based on mode and retrieval results:
    - rag-only / graphrag-retrieval: always → rag_response (no LLM generation)
    - graphrag + hybrid + docs found: → generate
    - hybrid + no docs: → fallback

    Args:
        state: Current graph state

    Returns:
        "generate" | "fallback" | "rag_response"
    """
    mode = state.get("mode", "hybrid")

    if mode in ("rag-only", "graphrag-retrieval"):
        logger.info(f"Routing: mode={mode} -> rag_response node")
        return "rag_response"

    retrieval_succeeded = state.get("retrieval_succeeded", False)

    if retrieval_succeeded:
        logger.info("Routing: relevant documents found -> generate node")
        return "generate"

    logger.warning("Routing: no relevant documents -> fallback node")
    return "fallback"
