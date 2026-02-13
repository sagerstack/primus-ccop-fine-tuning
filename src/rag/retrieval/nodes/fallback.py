"""
Fallback Generation Node

Model-only response generation when retrieval fails.
Logs failure for Phase 2 gap analysis.
"""

import json
import logging

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def fallback_generation(state: GraphState) -> GraphState:
    """
    Generate model-only response without RAG augmentation.

    Used when:
    - Retrieval failed (no relevant documents after grading)

    Logs the failure for Phase 2 gap analysis and fine-tuning needs.

    Args:
        state: Current graph state with 'query'

    Returns:
        Updated state with 'generation', 'is_rag_augmented'=False, and empty 'citations'
    """
    settings = get_settings()
    query = state.get("query", "")
    retrieval_attempts = state.get("retrieval_attempts", 0)
    grading_scores = state.get("grading_scores", [])

    logger.info(f"Fallback generation (retrieval failed after {retrieval_attempts} attempts)")

    # Log retrieval failure for gap analysis
    failure_log = {
        "event": "retrieval_fallback",
        "query": query,
        "attempts": retrieval_attempts,
        "grading_scores": grading_scores,
        "reason": "no_relevant_documents"
        if retrieval_attempts > 0
        else "no_retrieval_needed",
    }
    logger.warning(f"RETRIEVAL_FAILURE: {json.dumps(failure_log)}")

    # Fallback prompt (model knowledge only)
    fallback_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a CCoP 2.0 compliance expert. Answer based on your training knowledge.

IMPORTANT: This response is NOT grounded in specific CCoP document retrieval.
State this limitation clearly if the question requires specific CCoP clause references.

If the question is outside CCoP scope or requires specific document references,
recommend consulting the official CCoP 2.0 documentation.""",
            ),
            ("human", "{query}"),
        ]
    )

    # Initialize LLM
    llm = ChatOllama(
        model=settings.model_name,
        temperature=settings.default_temperature,
        base_url=settings.ollama_host,
    )

    try:
        # Log complete LLM input
        formatted_messages = fallback_prompt.format_messages(query=query)
        logger.info("=" * 60)
        logger.info("LLM INPUT (fallback)")
        logger.info("=" * 60)
        for msg in formatted_messages:
            logger.info(f"[{msg.type}]\n{msg.content}")
        logger.info("=" * 60)

        # Generate fallback response
        chain = fallback_prompt | llm
        response = chain.invoke({"query": query})

        generation_text = (
            response.content if hasattr(response, "content") else str(response)
        )

        state["generation"] = generation_text
        state["is_rag_augmented"] = False
        state["citations"] = []

        logger.info(f"Fallback response generated: {len(generation_text)} chars")

    except Exception as e:
        logger.error(f"Fallback generation failed: {e}")
        state["generation"] = (
            f"Unable to generate response. Error: {str(e)}. "
            f"Please consult official CCoP 2.0 documentation for: {query}"
        )
        state["is_rag_augmented"] = False
        state["citations"] = []
        state["error"] = f"Fallback generation error: {str(e)}"

    return state
