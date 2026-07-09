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

    if mode == "graphcpl":
        # GraphCompliance Compliance Gate (Phase 11): query_analysis routes into
        # the Context Graph chain (context_graph_extraction -> anchor_hypernym_mapping
        # -> compliance_gate_retrieval -> compliance_judgment), which terminates at
        # END with the grounded verdict/answer. Distinct branch (D-16 additivity).
        logger.info("Routing: mode=graphcpl -> context_graph_extraction node")
        return "context_graph_extraction"

    if mode == "graphont":
        # OMD-GraphRAG (ontology_v2): a single assembly node calls the tri-channel
        # retriever (which reranks internally) and packs filtered_documents, then edges
        # straight to `generate` — mirrors graphcpl option (a). Distinct branch (additive).
        logger.info("Routing: mode=graphont -> omd_context_assembly node")
        return "omd_context_assembly"

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
        # SEPARATE branch from `graphrag` above — the route key is
        # intentionally DISTINCT ("graph_retrieval_ontology", closing
        # RESEARCH Pitfall 3, plan 10-02). As of plan 10-09 (D-12), this key
        # maps to the `function_type_routing` node in the compiled graph
        # (see rag/retrieval/graph.py's conditional-edge map), NOT directly
        # to `graph_retrieval` — the D-09 function-type classification MUST
        # run and persist to state before the boosted ontology Cypher query
        # executes (conditional-edge functions cannot themselves persist
        # state mutations in LangGraph, verified empirically). That node then
        # edges into the SAME mode-aware `graph_retrieval` node
        # (graph_retrieve_documents), which selects
        # container.graph_retrieval_provider_ontology() vs
        # container.graph_retrieval_provider() based on state["mode"] and
        # threads state["function_type"] into the ontology provider only.
        logger.info(f"Routing: mode={mode} -> function_type_routing node (ontology provider)")
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
