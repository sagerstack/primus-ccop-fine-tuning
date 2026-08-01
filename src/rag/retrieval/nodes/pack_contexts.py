"""Standalone pack node for the retrieval graph.

Calls omd_pack to transform persisted retrieval trace into primus context
documents. Used in corrective flow and as a final step after agentic assembly.
"""
from rag.retrieval.nodes.omd_pack import omd_pack
from rag.retrieval.state.graph_state import GraphState


def pack_contexts(state: GraphState) -> GraphState:
    """Pack the candidates in state.trace into state.documents."""
    return omd_pack(state)


__all__ = ["pack_contexts"]
