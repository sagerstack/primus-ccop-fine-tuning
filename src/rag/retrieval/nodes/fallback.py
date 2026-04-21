"""
Fallback Generation Node

Model-only response generation when retrieval fails.
Logs failure for Phase 2 gap analysis.
"""

import json
import logging
from time import perf_counter

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from infrastructure.config.settings import get_settings
from rag.retrieval.nodes.generation import strip_thinking_tokens
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
                """You are a CCoP 2.0 compliance expert advising Critical Information Infrastructure Owners (CIIOs) in Singapore. Answer based on your training knowledge.

IMPORTANT: This response is NOT grounded in specific CCoP document retrieval. If the question requires precise clause references, state this limitation clearly and recommend consulting the official CCoP 2.0 documentation.

RESPONSE STRUCTURE:
1. CLAUSE CITATIONS: Reference specific CCoP clauses you are confident about from your training knowledge (e.g., Clause 5.2.1, Section 3.4). Clearly distinguish between clauses you are certain about and those you are less confident about.
2. CONDITIONAL ANALYSIS: Where applicable, analyze conditions, scenarios, or trade-offs relevant to the compliance question.
3. ACTIONABLE STEPS: Where applicable, provide concrete implementation steps the CIIO should take to achieve compliance.

Not all questions require all three elements — adapt your response to the question type.""",
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

    # Fallback path has no retrieval — no retrieved_contexts_detailed
    state["retrieved_contexts_detailed"] = []

    _start = perf_counter()
    try:
        # Log complete LLM input
        formatted_messages = fallback_prompt.format_messages(query=query)
        logger.info("=" * 60)
        logger.info("LLM INPUT (fallback)")
        logger.info("=" * 60)
        for msg in formatted_messages:
            logger.info(f"[{msg.type}]\n{msg.content}")
        logger.info("=" * 60)

        # Capture system_prompt and user_prompt
        _system_msg = next((m for m in formatted_messages if m.type == "system"), None)
        _human_msg = next((m for m in formatted_messages if m.type == "human"), None)
        state["system_prompt"] = _system_msg.content if _system_msg else ""
        state["user_prompt"] = _human_msg.content if _human_msg else ""

        # Generate fallback response
        chain = fallback_prompt | llm
        response = chain.invoke({"query": query})

        state["latency_ms"] = int((perf_counter() - _start) * 1000)

        # Extract token counts from Ollama response metadata
        response_metadata = getattr(response, "response_metadata", {}) or {}
        usage_metadata = getattr(response, "usage_metadata", {}) or {}
        prompt_tokens = response_metadata.get(
            "prompt_eval_count", usage_metadata.get("input_tokens", 0)
        )
        completion_tokens = response_metadata.get(
            "eval_count", usage_metadata.get("output_tokens", 0)
        )
        total_tokens = usage_metadata.get("total_tokens") or (prompt_tokens + completion_tokens)
        state["prompt_tokens"] = prompt_tokens
        state["completion_tokens"] = completion_tokens
        state["total_tokens"] = total_tokens

        generation_text = (
            response.content if hasattr(response, "content") else str(response)
        )
        generation_text = strip_thinking_tokens(generation_text)

        state["generation"] = generation_text
        state["is_rag_augmented"] = False
        state["citations"] = []

        logger.info(
            f"Fallback response generated: {len(generation_text)} chars, "
            f"tokens={total_tokens}, latency={state['latency_ms']}ms"
        )

    except Exception as e:
        state["latency_ms"] = int((perf_counter() - _start) * 1000)
        state["prompt_tokens"] = 0
        state["completion_tokens"] = 0
        state["total_tokens"] = 0
        logger.error(f"Fallback generation failed: {e}")
        state["generation"] = (
            f"Unable to generate response. Error: {str(e)}. "
            f"Please consult official CCoP 2.0 documentation for: {query}"
        )
        state["is_rag_augmented"] = False
        state["citations"] = []
        state["error"] = f"Fallback generation error: {str(e)}"

    return state
