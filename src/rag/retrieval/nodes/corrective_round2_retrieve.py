"""CRAG Round-2 retrieval node (graphont-agentic corrective mode).

Calls omd_retrieval.retrieve() with the rewritten query (from corrective_rewrite
node) to fetch a fresh candidate pool. Used ONLY in Incorrect/Ambiguous routes
when corrective mode is enabled.

Writes Round-2 candidates to state.trace["corrective_round2_pool"] for the
Round-2 evaluator and merge nodes.
"""
import logging

from infrastructure.config.settings import get_settings
from rag.graph.ontology_v2 import omd_retrieval
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def corrective_round2_retrieve(state: GraphState) -> GraphState:
    """Retrieve fresh candidates using the rewritten query (Round-2).
    
    Expects state.trace["corrective_rewrite"]["rewritten_query"] from the
    corrective_rewrite node. If rewrite failed (rewritten_query is None),
    falls back to the original question.
    
    Writes to state.trace["corrective_round2_pool"] with same structure as
    Round-1 (candidates, definitions, ranked_by, etc.) for merge/eval.
    """
    settings = get_settings()
    trace = state.setdefault("retrieval_trace", {})
    
    # Read the rewritten query from corrective_rewrite
    rewrite_data = trace.get("corrective_rewrite", {})
    rewritten_query = rewrite_data.get("rewritten_query")
    original_question = rewrite_data.get("original_question") or state.get("query", "")
    
    # Fallback to original question if rewrite failed
    query = rewritten_query if rewritten_query else original_question
    if not rewritten_query:
        logger.warning(
            "corrective_round2_retrieve: rewrite failed, using original question for Round-2"
        )
    
    # Retrieve with the same pool_k as Round-1 (graphont_agentic_pool_k)
    pool_k = settings.graphont_agentic_pool_k
    out = omd_retrieval.retrieve(query, k=pool_k, dense_query=state.get("hyde_clause"))
    
    # Write Round-2 pool to trace (same structure as Round-1 trace["candidates"])
    trace["corrective_round2_pool"] = {
        "query_used": query,
        "is_rewritten": rewritten_query is not None,
        "candidates": out.get("results", []),
        "definitions": out.get("definitions", []),
        "ranked_by": out.get("ranked_by"),
        "d_cand": out.get("d_cand", 0),
        "query_concepts": out.get("query_concepts", []),
        "n_retrieved": len(out.get("results", [])),
    }
    
    logger.info(
        "corrective_round2_retrieve: retrieved %d candidates (rewritten=%s, query_len=%d)",
        len(out.get("results", [])), rewritten_query is not None, len(query)
    )
    
    return state


__all__ = ["corrective_round2_retrieve"]
