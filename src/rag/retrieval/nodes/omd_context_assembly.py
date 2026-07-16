"""OMD-GraphRAG context assembly dispatcher for primus (--mode graphont).

The graph topology retains this single node. Its OMD path retrieves candidates and
packs them through plain Python function calls, then degrades safely to empty context.
"""
import logging

from rag.retrieval.nodes.omd_pack import omd_pack
from rag.retrieval.nodes.omd_retrieve import omd_retrieve
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)

_MODE = "graphont"


def omd_context_assembly(state: GraphState) -> GraphState:
    """Retrieve and pack OMD-GraphRAG context for primus."""
    if state.get("mode") != _MODE:
        return state

    try:
        omd_retrieve(state)
        omd_pack(state)
        trace = state["retrieval_trace"]
        logger.info(
            "OMD-GraphRAG context assembled for primus: %d document(s) "
            "(%d clauses + %d definitions, ranked_by=%s, D_cand=%d)",
            len(state["documents"]), len(trace["candidates"]), len(trace["definitions"]),
            trace.get("ranked_by"), trace.get("d_cand", 0))
        return state
    except Exception as e:  # degrade-safe: empty context, primus answers without grounding
        state.pop("retrieval_trace", None)
        logger.warning("OMD-GraphRAG retrieval failed (%s) — empty graphont context", e)

    docs = []
    state["filtered_documents"] = docs
    state["documents"] = docs
    state["is_rag_augmented"] = True
    state["retrieval_succeeded"] = bool(docs)
    return state


__all__ = ["omd_context_assembly"]
