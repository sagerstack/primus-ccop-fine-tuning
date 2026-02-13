"""
Query Analysis Node

Passthrough node — all queries route to retrieval.
No classification, no rewriting. The original query goes
directly to vector search, which handles semantic matching
via embeddings.
"""

import logging

from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def analyze_query(state: GraphState) -> GraphState:
    """
    Pass original query through for retrieval.

    All queries are sent to vector search. No classification or
    rewriting — embeddings handle semantic matching.

    Args:
        state: Current graph state with 'query' field

    Returns:
        Updated state with rewritten_query set to original query
    """
    query = state.get("query", "")

    logger.info(f"Query received: {query[:100]}...")

    state["needs_retrieval"] = True
    state["rewritten_query"] = query

    return state
