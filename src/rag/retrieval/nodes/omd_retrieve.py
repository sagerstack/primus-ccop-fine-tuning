"""Retrieve OMD-GraphRAG candidates and persist their diagnostic trace."""
from infrastructure.config.settings import get_settings
from rag.graph.ontology_v2 import omd_retrieval
from rag.retrieval.nodes.omd_pack import cap_primary_candidates
from rag.retrieval.state.graph_state import GraphState

_TOP_K = 8  # default paper §retrieval top-k; overridable via settings.graphont_top_k (CCOP_GRAPHONT_TOP_K)


def omd_retrieve(state: GraphState) -> GraphState:
    """Run tri-channel OMD retrieval and retain candidates for context packing."""
    question = state.get("query", "") or ""
    settings = get_settings()
    pool_k = settings.graphont_pool_k
    out = omd_retrieval.retrieve(question, k=pool_k, dense_query=state.get("hyde_clause"))
    candidate_pool = out.get("results", [])
    selected = cap_primary_candidates(candidate_pool, settings.graphont_top_k)

    trace = state.setdefault("retrieval_trace", {})
    trace["candidate_pool"] = candidate_pool
    trace["candidates"] = selected
    trace["definitions"] = out.get("definitions", [])
    trace["ce_confidence"] = out.get("ce_confidence")
    trace["ranked_by"] = out.get("ranked_by")
    trace["d_cand"] = out.get("d_cand", 0)
    trace["query_concepts"] = out.get("query_concepts", [])
    trace["pool_k"] = pool_k
    trace["top_k"] = settings.graphont_top_k
    trace["n_retrieved"] = len(candidate_pool)
    trace["n_primary_selected"] = sum(1 for r in selected if r.get("kind") != "definition")
    trace["n_auxiliary_selected"] = sum(1 for r in selected if r.get("kind") == "definition")
    trace["per_channel"] = {
        "ch1": [r.get("ch1") for r in candidate_pool],
        "bm25": [r.get("bm25") for r in candidate_pool],
        "dense": [r.get("dense") for r in candidate_pool],
        "rrf": [r.get("rrf") for r in candidate_pool],
    }
    return state


__all__ = ["omd_retrieve"]
