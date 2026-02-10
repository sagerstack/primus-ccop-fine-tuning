"""
Query Analysis Node

Keyword-based query classification (needs_retrieval vs general).
No LLM call — the base model doesn't know CCoP terminology and
corrupts domain terms during rewriting (e.g. CII -> CUI).
"""

import logging

from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)

# CCoP domain keywords that indicate retrieval is needed
_RETRIEVAL_KEYWORDS = [
    "ccop", "cii", "critical information infrastructure", "ciio",
    "cybersecurity code of practice", "code of practice",
    "csa", "cyber security agency",
    "compliance", "requirement", "clause", "section", "annex",
    "access control", "incident response", "risk assessment",
    "audit", "penetration test", "vulnerability assessment",
    "cybersecurity exercise", "cybersecurity awareness",
    "security-by-design", "threat model",
]

# Keywords that indicate a general question (no retrieval)
_GENERAL_KEYWORDS = [
    "what is cybersecurity", "define cybersecurity",
    "what is a firewall", "what is encryption",
    "explain", "definition of",
]


def _needs_retrieval(query: str) -> bool:
    """
    Classify query as needing retrieval or not via keyword matching.

    Returns True (needs retrieval) for CCoP-related queries.
    Returns False for generic cybersecurity definitions.
    Defaults to True (safer — attempt retrieval when unclear).
    """
    query_lower = query.lower()

    # Check for general question patterns first
    if any(kw in query_lower for kw in _GENERAL_KEYWORDS):
        # But override if CCoP terms are also present
        if any(kw in query_lower for kw in _RETRIEVAL_KEYWORDS[:8]):
            return True
        return False

    # Check for CCoP domain keywords
    if any(kw in query_lower for kw in _RETRIEVAL_KEYWORDS):
        return True

    # Default: attempt retrieval (safer)
    return True


def analyze_query(state: GraphState) -> GraphState:
    """
    Classify query and pass original query through for retrieval.

    No LLM call, no query rewriting. Classification is keyword-based.
    The original query goes directly to vector search, which handles
    semantic matching via embeddings.

    Args:
        state: Current graph state with 'query' field

    Returns:
        Updated state with needs_retrieval and rewritten_query fields
    """
    query = state.get("query", "")

    logger.info(f"Analyzing query: {query[:100]}...")

    needs_retrieval = _needs_retrieval(query)

    state["needs_retrieval"] = needs_retrieval
    state["rewritten_query"] = query  # Pass original query through

    logger.info(f"Query analysis: needs_retrieval={needs_retrieval} (keyword-based)")

    return state
