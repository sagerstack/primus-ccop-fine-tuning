"""CRAG-style corrective query rewrite node (graphont-agentic ONLY).

Rewrites the original question into a retrieval query using the corpus's
canonical vocabulary (from concept_aliases.json) without asserting a verdict.
Used ONLY in Incorrect/Ambiguous routes for Round-2 corrective retrieval.

Slice 2: observational only — writes to trace but does NOT trigger Round-2 yet.
Slice 3 wires this into the live graph conditional routing.
"""
import hashlib
import json
import logging
import re
from pathlib import Path

from infrastructure.config.settings import get_settings
from infrastructure.external.openrouter_client import OpenRouterClient
from rag.retrieval.prompts.corrective_rewrite_prompt import (
    PROMPT_VERSION,
    build_rewrite_prompt,
)
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)

# Verdict tokens that would violate neutrality (the rewrite should NOT conclude
# or imply the answer). If any appear in the LLM output, reject and fall back.
_VERDICT_TOKENS = [
    "must comply",
    "not in scope",
    "exempt",
    "is required",
    "prohibited",
    "does not apply",
    "mandatory",
    "optional",
]


def corrective_rewrite(state: GraphState) -> GraphState:
    """Rewrite the question into a corpus-canonical retrieval query (CRAG).
    
    Observational in Slice 2: writes to trace["corrective_rewrite"] but does
    NOT alter routing. Slice 3 wires this into the live conditional graph.
    
    Fail-open: on any LLM/parse error or neutrality violation → fallback to
    the original question (logged at WARNING) and set rewrite=None in trace.
    """
    settings = get_settings()
    question = state.get("query", "") or ""
    
    if not question:
        logger.warning("corrective_rewrite: no question in state, no-op")
        return state
    
    # Cache key: model | PROMPT_VERSION | question
    cache_key = hashlib.sha256(
        f"{settings.rag_hyde_model}|{PROMPT_VERSION}|{question}".encode()
    ).hexdigest()
    
    cache_file = Path(settings.results_dir) / "cache" / "corrective_rewrite_cache.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Try cache load
    cache = {}
    try:
        if cache_file.exists():
            cache = json.loads(cache_file.read_text())
    except Exception as e:
        logger.warning("corrective_rewrite: cache load failed: %s", e)
    
    if cache_key in cache:
        cached = cache[cache_key]
        logger.info("corrective_rewrite: cache hit (key=%s...)", cache_key[:12])
        state.setdefault("retrieval_trace", {})["corrective_rewrite"] = {
            "original_question": question,
            "rewritten_query": cached.get("search_query"),
            "keyphrases": cached.get("keyphrases"),
            "source": "cache",
        }
        return state
    
    # LLM call (OpenRouterClient takes a single prompt string, not messages list)
    client = OpenRouterClient(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )
    messages = build_rewrite_prompt(question)
    # Format messages into a single prompt: <system>\n\n<user>
    prompt = "\n\n".join(m["content"] for m in messages)
    
    try:
        response = client.call(
            prompt=prompt,
            model=settings.rag_hyde_model,  # reusing the HyDE model setting for now
            temperature=0.0,
            seed=0,
        )
    except Exception as e:
        logger.warning(
            "corrective_rewrite: LLM call failed (%s), fallback to original question",
            e,
        )
        state.setdefault("retrieval_trace", {})["corrective_rewrite"] = {
            "original_question": question,
            "rewritten_query": None,
            "error": f"LLM call failed: {str(e)[:100]}",
        }
        return state
    
    # Parse JSON (strip markdown fences if present)
    raw = response.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    
    try:
        parsed = json.loads(raw)
        search_query = parsed.get("search_query", "")
        keyphrases = parsed.get("keyphrases", [])
    except Exception as e:
        logger.warning(
            "corrective_rewrite: JSON parse failed (%s), fallback to original question. Raw: %s",
            e, raw[:200]
        )
        state.setdefault("retrieval_trace", {})["corrective_rewrite"] = {
            "original_question": question,
            "rewritten_query": None,
            "error": f"Parse failed: {str(e)[:100]}",
            "raw_response": raw[:200],
        }
        return state
    
    # Neutrality post-check: reject if verdict tokens appear
    combined = (search_query + " " + " ".join(keyphrases)).lower()
    for token in _VERDICT_TOKENS:
        if token.lower() in combined:
            logger.warning(
                "corrective_rewrite: neutrality violation (token='%s'), fallback to original question",
                token,
            )
            state.setdefault("retrieval_trace", {})["corrective_rewrite"] = {
                "original_question": question,
                "rewritten_query": None,
                "neutrality_violation": token,
                "rejected_output": raw[:200],
            }
            return state
    
    # Success: cache and write to trace
    cache[cache_key] = {"search_query": search_query, "keyphrases": keyphrases}
    try:
        cache_file.write_text(json.dumps(cache, indent=2))
    except Exception as e:
        logger.warning("corrective_rewrite: cache write failed: %s", e)
    
    state.setdefault("retrieval_trace", {})["corrective_rewrite"] = {
        "original_question": question,
        "rewritten_query": search_query,
        "keyphrases": keyphrases,
        "source": "llm",
    }
    
    logger.info(
        "corrective_rewrite: rewritten (len=%d) using %d keyphrases",
        len(search_query), len(keyphrases)
    )
    
    return state


__all__ = ["corrective_rewrite"]
