"""
Query Analysis Node

If HyDE is enabled (per settings), generates a hypothetical CCoP-style clause
via OpenRouter (gpt-4o-mini) and uses it as the retrieval embedding query.
The original user query is preserved for downstream reranker scoring.

Lab provenance: Experiment #17 (HyDE) + #41 (acronyms-only style).
"""

import logging

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


HYDE_PROMPT = """You are simulating a CCoP 2.0 (Cybersecurity Code of Practice for Critical Information Infrastructure, Singapore) regulatory clause that would be cited as the answer to the question below. Write 2-3 sentences in formal regulatory style using the vocabulary of CCoP 2.0 ("the CIIO shall...", "the Commissioner may...", "waiver", "compliance", clause-style language). Do not include preamble — output only the hypothetical clause text.

QUESTION:
{q}

HYPOTHETICAL CLAUSE:"""


def _generate_hyde(question: str, settings) -> str:
    """Call OpenRouter to generate a hypothetical CCoP clause."""
    if not settings.openrouter_api_key:
        logger.warning("HyDE enabled but OPENROUTER_API_KEY not set; skipping")
        return ""
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=60,
        )
        resp = client.chat.completions.create(
            model=settings.rag_hyde_model,
            messages=[{"role": "user", "content": HYDE_PROMPT.format(q=question)}],
            temperature=0.2,
            max_tokens=200,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.warning(f"HyDE generation failed: {e}")
        return ""


def analyze_query(state: GraphState) -> GraphState:
    """
    Pass original query through; optionally generate HyDE rewrite for retrieval.

    Original query stays in state["query"] (used by reranker, generator).
    HyDE-rewritten query goes to state["rewritten_query"] (used by retrieval).
    """
    settings = get_settings()
    query = state.get("query", "")
    state["needs_retrieval"] = True

    if settings.rag_hyde_enabled and state.get("mode", "hybrid") in ("hybrid", "rag-only"):
        logger.info(f"HyDE rewriting query (model={settings.rag_hyde_model})")
        hyde = _generate_hyde(query, settings)
        if hyde:
            state["hyde_query"] = hyde
            state["rewritten_query"] = hyde  # used by retrieval node for embedding
            logger.debug(f"HyDE: {hyde[:120]}...")
        else:
            state["rewritten_query"] = query
            state["hyde_query"] = ""
    else:
        state["rewritten_query"] = query
        state["hyde_query"] = ""

    return state
