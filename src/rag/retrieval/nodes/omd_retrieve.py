"""Retrieve OMD-GraphRAG candidates and persist their diagnostic trace."""
from rag.graph.ontology_v2 import omd_retrieval
from rag.retrieval.state.graph_state import GraphState

_TOP_K = 8  # paper §retrieval top-k = 8


def omd_retrieve(state: GraphState) -> GraphState:
    """Run tri-channel OMD retrieval and retain candidates for context packing."""
    question = state.get("query", "") or ""
    out = omd_retrieval.retrieve(question, k=_TOP_K)
    candidates = out.get("results", [])

    trace = state.setdefault("retrieval_trace", {})
    trace["candidates"] = candidates
    trace["definitions"] = out.get("definitions", [])
    trace["ce_confidence"] = out.get("ce_confidence")
    trace["ranked_by"] = out.get("ranked_by")
    trace["d_cand"] = out.get("d_cand", 0)
    trace["query_concepts"] = out.get("query_concepts", [])
    trace["per_channel"] = {
        "ch1": [r.get("ch1") for r in candidates],
        "bm25": [r.get("bm25") for r in candidates],
        "dense": [r.get("dense") for r in candidates],
        "rrf": [r.get("rrf") for r in candidates],
    }
    return state


__all__ = ["omd_retrieve"]
