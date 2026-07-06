"""
Context Graph Extraction Node (Phase 11, plan 11-06 Task 1, D-10)

Per-query Context Graph: extracts ER/SAO (Entity-Relation Subject-Action-
Object) triples from the scenario text via a settings-gated OpenRouter call,
mirroring `rag/retrieval/nodes/query_analysis.py::_generate_hyde`'s
settings-gated LLM call + graceful-degradation shape exactly (`function_type_
routing.py::classify_function_type`'s mode-gated no-op shape for the node
itself).

GraphCompliance §3.2 identifies the Context Graph as the paper's biggest
single lever (S2 ablation, -10.2pp when removed) — this is the concrete
per-query scenario anchoring the pre-Phase-11 system throws away (Finding 0,
query embedded as a bare string).

Each triple also carries a coarse entity-type tag on both subject and object
(`actor` / `system` / `data` / `other`) so anchor derivation
(`anchor_hypernym_mapping.py`, Task 3) can select actor/data/system anchors
deterministically from the extracted triples without a second LLM call
(ER-triple / anchor extraction prompt design is Claude's discretion per
11-CONTEXT.md).

Gated on `state.get("mode") == "graph-compliance"` — a no-op for every other
mode (`hybrid`/`llm-only`/`graphrag`/`graphrag-ontology` requests are
entirely unaffected), never fails the whole request on an LLM error, and
degrades to an empty triple list on any classification/parsing failure
(T-11-15: settings-gated degrade-to-empty is also the Denial-of-Service
mitigation for this per-query LLM call, per the threat register).

Caching: extraction is cached per query text (a query-id proxy — this node
runs before any run/case id is threaded through GraphState) so repeated
evaluation runs over the same 18-case fixture never re-issue the same
OpenRouter call (D-14: "cache per-query extractions/anchors").
"""

import hashlib
import json
import logging
import threading
from typing import Any, Dict, List

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


CONTEXT_GRAPH_EXTRACTION_PROMPT = """Extract ER/SAO (Entity-Relation Subject-Action-Object) triples from the following Critical Information Infrastructure (CII) cybersecurity compliance scenario. For each triple, identify the subject, the predicate (the relation or action linking them), and the object. Classify BOTH the subject and the object into exactly one of: "actor" (an organization, role, regulator, or system operator), "system" (an IT/OT system, network, application, or technical asset), "data" (information, records, or data flows), or "other" (anything that does not fit the above).

Return ONLY a JSON array of objects, e.g.:
[{{"subject": "Hospital administration system", "subject_type": "system", "predicate": "shares network with", "object": "enterprise network", "object_type": "system"}}]

No prose, no backticks, no explanation — JSON array only. If no clear triples can be extracted, return [].

SCENARIO:
{q}

TRIPLES (JSON array):"""

_REQUIRED_TRIPLE_KEYS = ("subject", "subject_type", "predicate", "object", "object_type")
_VALID_ENTITY_TYPES = frozenset({"actor", "system", "data", "other"})

# Per-query-text extraction cache (D-14). Keyed on a hash of the raw scenario
# text — cheap, avoids retaining unbounded raw-text keys, and is stable
# across repeated eval runs over the same fixture.
_extraction_cache: Dict[str, List[Dict[str, Any]]] = {}
_extraction_cache_lock = threading.Lock()


def _cache_key(question: str) -> str:
    return hashlib.sha256(question.encode("utf-8")).hexdigest()


def _parse_triples(raw: str) -> List[Dict[str, Any]]:
    """
    Parse + validate the LLM's JSON array response into a list of triple
    dicts. Reuses `neo4j_graphrag`'s `fix_invalid_json` repair helper (same
    reuse discipline as `gleaning_extractor.py::_parse_graph_response` —
    never hand-roll a new JSON repair function). Any triple missing a
    required key, or carrying an entity type outside the locked 4-value enum,
    is dropped rather than trusted un-validated. Never raises — returns []
    on total parse failure.
    """
    if not raw:
        return []
    try:
        from neo4j_graphrag.experimental.components.entity_relation_extractor import (
            fix_invalid_json,
        )
        from neo4j_graphrag.experimental.pipeline.exceptions import InvalidJSONError

        try:
            repaired = fix_invalid_json(raw)
            parsed = json.loads(repaired)
        except (json.JSONDecodeError, InvalidJSONError):
            parsed = json.loads(raw)
    except Exception as e:
        logger.warning(f"Context Graph triple JSON parse failed: {e}")
        return []

    if not isinstance(parsed, list):
        logger.warning("Context Graph extraction did not return a JSON array; discarding")
        return []

    triples: List[Dict[str, Any]] = []
    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        if not all(k in entry for k in _REQUIRED_TRIPLE_KEYS):
            continue
        subject_type = str(entry.get("subject_type", "")).strip().lower()
        object_type = str(entry.get("object_type", "")).strip().lower()
        if subject_type not in _VALID_ENTITY_TYPES or object_type not in _VALID_ENTITY_TYPES:
            logger.warning(
                f"Dropping triple with unrecognized entity type "
                f"(subject_type={subject_type!r}, object_type={object_type!r})"
            )
            continue
        triples.append(
            {
                "subject": str(entry.get("subject", "")).strip(),
                "subject_type": subject_type,
                "predicate": str(entry.get("predicate", "")).strip(),
                "object": str(entry.get("object", "")).strip(),
                "object_type": object_type,
            }
        )
    return triples


def _extract_context_graph_triples(question: str, settings) -> List[Dict[str, Any]]:
    """
    Call OpenRouter to extract ER/SAO triples from the scenario (D-10).

    Mirrors `query_analysis.py::_generate_hyde`'s settings-gated call +
    try/except-log-return degradation pattern exactly: returns [] (no
    Context Graph) on any missing-key or LLM-call failure, never raises.
    """
    if not settings.openrouter_api_key:
        logger.warning("Context Graph extraction enabled but OPENROUTER_API_KEY not set; skipping")
        return []
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=60,
        )
        resp = client.chat.completions.create(
            model=settings.ontology_discovery_model,
            messages=[{"role": "user", "content": CONTEXT_GRAPH_EXTRACTION_PROMPT.format(q=question)}],
            temperature=0.0,
            max_tokens=800,
        )
        raw = (resp.choices[0].message.content or "").strip()
        return _parse_triples(raw)
    except Exception as e:
        logger.warning(f"Context Graph extraction failed: {e}")
        return []


def _extract_context_graph_triples_cached(question: str, settings) -> List[Dict[str, Any]]:
    """Per-query-text cache wrapper around `_extract_context_graph_triples` (D-14)."""
    key = _cache_key(question)
    with _extraction_cache_lock:
        cached = _extraction_cache.get(key)
    if cached is not None:
        logger.debug("Context Graph extraction cache hit")
        return cached

    triples = _extract_context_graph_triples(question, settings)

    with _extraction_cache_lock:
        _extraction_cache[key] = triples
    return triples


def extract_context_graph(state: GraphState) -> GraphState:
    """
    Extract the per-query Context Graph (ER/SAO triples) from the scenario
    (D-10, GraphCompliance §3.2).

    Gated on `mode == "graph-compliance"` (mirrors `classify_function_type`'s
    mode-gating) — a no-op for every other mode, so `hybrid`/`llm-only`/
    `graphrag`/`graphrag-ontology` requests are entirely unaffected. Runs
    early in the pipeline so `state["context_graph_triples"]` is populated
    before anchor derivation (`map_anchors_to_hypernyms`, plan 11-06 Task 3).
    """
    settings = get_settings()
    query = state.get("query", "")

    if state.get("mode") != "graph-compliance":
        state["context_graph_triples"] = state.get("context_graph_triples", [])
        return state

    logger.info(f"Extracting Context Graph (model={settings.ontology_discovery_model})")
    triples = _extract_context_graph_triples_cached(query, settings)
    state["context_graph_triples"] = triples
    if triples:
        logger.debug(f"Context Graph: {len(triples)} triple(s) extracted")
    else:
        logger.warning("Context Graph extraction produced no triples (degraded or empty scenario)")

    return state


__all__: List[str] = [
    "CONTEXT_GRAPH_EXTRACTION_PROMPT",
    "extract_context_graph",
]
