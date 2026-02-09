"""
Routing Logic

Conditional edge functions for LangGraph routing decisions.
Includes query rewriting for self-correction loop.
"""

import logging

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def route_query(state: GraphState) -> str:
    """
    Route query after analysis.

    First routing decision after query analysis node.

    Args:
        state: Current graph state with 'needs_retrieval'

    Returns:
        "retrieval" if needs_retrieval=True, "fallback" otherwise
    """
    needs_retrieval = state.get("needs_retrieval", True)

    if needs_retrieval:
        logger.info("Routing: query needs retrieval -> retrieval node")
        return "retrieval"
    else:
        logger.info("Routing: general query -> fallback node")
        return "fallback"


def decide_after_grading(state: GraphState) -> str:
    """
    Decide next step after document grading.

    Routing decision after grading node:
    - If relevant docs found: proceed to generation
    - If max attempts reached (3): give up, route to fallback
    - Otherwise: rewrite query and retry retrieval (self-correction loop)

    Args:
        state: Current graph state with 'retrieval_succeeded' and 'retrieval_attempts'

    Returns:
        "generate" | "rewrite" | "fallback"
    """
    retrieval_succeeded = state.get("retrieval_succeeded", False)
    retrieval_attempts = state.get("retrieval_attempts", 0)

    if retrieval_succeeded:
        logger.info("Routing: relevant documents found -> generate node")
        return "generate"

    # Check retry budget (max 3 attempts)
    if retrieval_attempts >= 3:
        logger.warning(
            f"Routing: max retrieval attempts reached ({retrieval_attempts}) -> fallback node"
        )
        return "fallback"

    # Self-correction: rewrite query and retry
    logger.info(
        f"Routing: no relevant docs (attempt {retrieval_attempts}/3) -> rewrite query and retry"
    )
    return "rewrite"


def rewrite_query(state: GraphState) -> GraphState:
    """
    Rewrite query for better retrieval (self-correction loop).

    Uses LLM to reformulate query when initial retrieval failed.
    This is a graph node (not just an edge function) because it mutates state.

    Args:
        state: Current graph state with 'query' and 'rewritten_query'

    Returns:
        Updated state with new 'rewritten_query'
    """
    settings = get_settings()
    original_query = state.get("query", "")
    previous_rewrite = state.get("rewritten_query", original_query)
    retrieval_attempts = state.get("retrieval_attempts", 0)

    logger.info(f"Rewriting query (attempt {retrieval_attempts + 1})...")

    # Rewrite prompt
    rewrite_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a CCoP compliance expert. The previous query did not retrieve relevant documents.

Rewrite the query to improve retrieval from the CCoP document corpus:
- Try different terminology or phrasing
- Break down complex questions into simpler components
- Focus on key CCoP concepts (access control, incident response, risk management, etc.)
- Add context that might match document sections

Previous attempts:
- Original query: {original_query}
- Previous rewrite: {previous_rewrite}

Provide a NEW rewrite that approaches the question differently.""",
            ),
            ("human", "Rewrite this query for better CCoP document retrieval."),
        ]
    )

    # Initialize LLM
    llm = ChatOllama(
        model=settings.model_name, temperature=0.3, base_url=settings.ollama_host
    )

    try:
        chain = rewrite_prompt | llm
        response = chain.invoke(
            {"original_query": original_query, "previous_rewrite": previous_rewrite}
        )

        new_rewrite = (
            response.content if hasattr(response, "content") else str(response)
        )

        state["rewritten_query"] = new_rewrite.strip()

        logger.info(f"Query rewritten: '{new_rewrite[:80]}...'")

    except Exception as e:
        logger.error(f"Query rewrite failed: {e}. Using previous query.")
        # Keep previous query if rewrite fails
        state["error"] = f"Query rewrite error: {str(e)}"

    return state
