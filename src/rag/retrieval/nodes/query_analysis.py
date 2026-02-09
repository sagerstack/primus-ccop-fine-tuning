"""
Query Analysis Node

LLM-based binary query classification (needs_retrieval vs general)
with query rewriting for optimal retrieval.
"""

import logging

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def _parse_needs_retrieval(response_text: str) -> bool:
    """
    Parse needs_retrieval from LLM response text.

    Looks for explicit TRUE/FALSE or keywords indicating retrieval need.
    Defaults to True (safer — attempt retrieval when unclear).
    """
    text_lower = response_text.lower()

    # Check for explicit classification
    if "needs_retrieval: true" in text_lower or "needs_retrieval:true" in text_lower:
        return True
    if "needs_retrieval: false" in text_lower or "needs_retrieval:false" in text_lower:
        return False

    # Check for general/no-retrieval indicators
    no_retrieval_keywords = ["general question", "does not require retrieval", "no retrieval needed"]
    if any(kw in text_lower for kw in no_retrieval_keywords):
        return False

    # Default: attempt retrieval (safer)
    return True


def analyze_query(state: GraphState) -> GraphState:
    """
    Analyze query to determine if retrieval is needed.

    Uses Llama-Primus-Reasoning via ChatOllama for binary classification:
    needs_retrieval (True/False). Also produces rewritten_query optimized
    for vector search.

    Args:
        state: Current graph state with 'query' field

    Returns:
        Updated state with needs_retrieval and rewritten_query fields
    """
    settings = get_settings()
    query = state.get("query", "")

    logger.info(f"Analyzing query: {query[:100]}...")

    # Initialize LLM
    llm = ChatOllama(
        model=settings.model_name, temperature=0.0, base_url=settings.ollama_host
    )

    # Prompt for binary classification
    analysis_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a CCoP 2.0 compliance expert analyzing user queries.

Determine if the query requires retrieval from CCoP compliance documents.

NEEDS RETRIEVAL (True):
- Questions about specific CCoP requirements, clauses, or compliance obligations
- Questions about CII organization responsibilities
- Questions about security controls, access control, incident response procedures

GENERAL QUESTION (False):
- Generic cybersecurity definitions ("What is cybersecurity?")
- Questions about non-CCoP frameworks only
- Opinion questions or speculation

Respond in this exact format:
NEEDS_RETRIEVAL: True or False
REWRITTEN_QUERY: <query optimized for vector search with expanded acronyms>""",
            ),
            ("human", "Query: {query}"),
        ]
    )

    try:
        chain = analysis_prompt | llm
        response = chain.invoke({"query": query})
        response_text = response.content if hasattr(response, "content") else str(response)

        needs_retrieval = _parse_needs_retrieval(response_text)

        # Extract rewritten query if present
        rewritten_query = query  # default to original
        if "REWRITTEN_QUERY:" in response_text:
            parts = response_text.split("REWRITTEN_QUERY:")
            if len(parts) > 1:
                rewritten_query = parts[1].strip().split("\n")[0].strip()

        state["needs_retrieval"] = needs_retrieval
        state["rewritten_query"] = rewritten_query

        logger.info(
            f"Query analysis: needs_retrieval={needs_retrieval}, "
            f"rewritten='{rewritten_query[:80]}...'"
        )

    except Exception as e:
        # If LLM call fails, default to needs_retrieval=True (safer - attempt retrieval)
        logger.warning(
            f"Query analysis failed: {e}. Defaulting to needs_retrieval=True"
        )
        state["needs_retrieval"] = True
        state["rewritten_query"] = query  # Use original query as fallback
        state["error"] = f"Query analysis error: {str(e)}"

    return state
