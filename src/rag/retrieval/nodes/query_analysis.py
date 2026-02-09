"""
Query Analysis Node

LLM-based binary query classification (needs_retrieval vs general)
with query rewriting for optimal retrieval.
"""

import logging

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


class QueryAnalysisResult(BaseModel):
    """
    Query analysis output.

    Binary classification with query rewriting for retrieval optimization.
    """

    needs_retrieval: bool = Field(
        description="Whether query requires document retrieval from CCoP corpus"
    )
    rewritten_query: str = Field(
        description="Query optimized for vector search (expanded acronyms, added context)"
    )
    reasoning: str = Field(description="Explanation of classification decision")


def analyze_query(state: GraphState) -> GraphState:
    """
    Analyze query to determine if retrieval is needed.

    Uses Llama-Primus-Reasoning via ChatOllama with structured output
    for binary classification: needs_retrieval (True/False).

    Also produces rewritten_query optimized for vector search by
    expanding acronyms and adding CCoP compliance context.

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
- Questions asking "what does CCoP say about..."

GENERAL QUESTION (False):
- Generic cybersecurity definitions ("What is cybersecurity?")
- Questions about non-CCoP frameworks (NIST, ISO 27001, etc.)
- Questions outside CCoP scope (attack techniques, penetration testing how-tos)
- Opinion questions or speculation

Also rewrite the query to optimize for vector search:
- Expand acronyms (CII -> Critical Information Infrastructure)
- Add CCoP compliance context
- Make implicit requirements explicit""",
            ),
            ("human", "Query: {query}\n\nAnalyze this query."),
        ]
    )

    # Invoke LLM with structured output
    try:
        analyzer = analysis_prompt | llm.with_structured_output(QueryAnalysisResult)
        result = analyzer.invoke({"query": query})

        state["needs_retrieval"] = result.needs_retrieval
        state["rewritten_query"] = result.rewritten_query

        logger.info(
            f"Query analysis: needs_retrieval={result.needs_retrieval}, "
            f"rewritten='{result.rewritten_query[:80]}...'"
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
