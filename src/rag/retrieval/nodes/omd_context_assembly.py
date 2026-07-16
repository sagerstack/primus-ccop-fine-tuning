"""OMD-GraphRAG context assembly dispatcher for primus (--mode graphont).

The graph topology retains this single node. Its OMD path retrieves candidates and
packs them through plain Python function calls, then degrades safely to empty context.
"""
import logging

from rag.retrieval.nodes.omd_pack import omd_pack
from rag.retrieval.nodes.omd_retrieval_grade import omd_retrieval_grade
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
        # Slice C (DETECT): grade retrieval quality AFTER packing. Own try/except so a
        # detector fault degrades to grade="unknown" WITHOUT discarding the packed docs
        # (it must not fall through to the empty-context fallback below). Additive keys
        # only; the four protected Slice-B keys and the log message above are untouched,
        # so graphont stays byte-identical (parity harness excludes additive keys).
        try:
            omd_retrieval_grade(state)
        except Exception as ge:
            state["retrieval_grade"] = "unknown"
            state.setdefault("retrieval_grade_reasons", [])
            state["retrieval_grade_reasons"].append(f"detector_exception: {ge!r}")
            state["should_requery"] = False
            logger.warning("retrieval-grade detector failed (%s) — grade=unknown", ge)
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
