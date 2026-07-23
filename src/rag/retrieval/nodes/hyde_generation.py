"""Reusable HyDE generation node for graphont-agentic dense retrieval."""

import hashlib
import json
import logging
from pathlib import Path

from infrastructure.config.settings import get_settings
from rag.retrieval.nodes.query_analysis import _generate_hyde
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)

HYDE_PROMPT_VERSION = "v1"


def hyde_generation(state: GraphState) -> GraphState:
    """Generate and cache a hypothetical clause for dense-channel retrieval."""
    settings = get_settings()
    mode = state.get("mode", "")
    if mode == "graphont":
        enabled = settings.graphont_hyde_enabled
    elif mode == "graphont-agentic":
        enabled = settings.graphont_agentic_hyde_enabled
    else:
        return state
    if not enabled:
        return state

    question = state.get("query", "") or ""
    if not question:
        return state

    cache_key = hashlib.sha256(
        f"{settings.rag_hyde_model}|0.0|{HYDE_PROMPT_VERSION}|{question}".encode()
    ).hexdigest()
    cache_dir = Path("results/evaluations/cache")
    cache_file = cache_dir / "hyde_cache.json"
    cache = {}

    if settings.hyde_cache_enabled:
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            if cache_file.exists():
                cache = json.loads(cache_file.read_text())
        except Exception as e:
            logger.warning(f"Failed to load HyDE cache: {e}")

    if settings.hyde_cache_enabled and cache_key in cache:
        clause = cache[cache_key]
    else:
        try:
            clause = _generate_hyde(question, settings, temperature=0.0)
        except Exception as e:
            logger.warning(f"HyDE generation failed: {e}")
            return state

        if clause and settings.hyde_cache_enabled:
            try:
                cache[cache_key] = clause
                cache_file.write_text(json.dumps(cache, indent=2))
            except Exception as e:
                logger.warning(f"Failed to save HyDE cache: {e}")

    if not clause:
        logger.warning("HyDE generation returned an empty clause; skipping")
        return state

    state["hyde_clause"] = clause
    logger.info(f"HyDE clause generated (len={len(clause)})")
    return state
