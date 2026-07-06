"""
Anchor Extraction + Hypernym Mapping Node (Phase 11, plan 11-06 Task 3 +
11-06b addendum, D-09/D-10)

Derives actor/data/system anchors from the per-query Context Graph
(`state["context_graph_triples"]`, populated by `context_graph_extraction.py`
Task 1) and hypernym-maps each anchor to policy vocabulary via
`HypernymScoringService` (Task 2, D-09 STRONG/WEAK + beta=0.3 premise bonus).

Mirrors `function_type_routing.py::classify_function_type`'s mode-gated,
state-writing node shape: gated on `state.get("mode") == "graph-compliance"`,
a no-op for every other mode, writing the resolved `anchors` +
`hypernym_mappings` into state for the D-17.2 verbose-io trace.

Anchor derivation is DETERMINISTIC (no second LLM call): Task 1's extraction
prompt already tags each triple's subject/object with a coarse entity type
(`actor` / `system` / `data` / `other`); this node simply collects the unique
(label, type) pairs whose type is one of the three anchor types. Each anchor
also carries its `context` — the (predicate, other-entity-label) relations
from every triple that mentions it (11-06b: enriches step-1 retrieval so the
right definitional premise, e.g. a "designated as CII" system's CII
definition, lands in the candidate pool).

GraphCompliance §3.2's hypernym mapping is THREE steps (Alg. 2 line 3; 11-06b
closes the fidelity gap the D-26 checkpoint surfaced, where 11-06 Task 3
collapsed steps 2+3 into "raw fragment as label, cosine as confidence"):
  1. Retrieve top-M policy fragments per anchor (`_default_fragment_retriever`)
     — grounding only, narrower than the full anchor->CU-Plan retrieval
     (D-11, bi-encoder K1 + cross-encoder rerank over eqs. 3-4; that
     two-channel retriever is out of this plan's scope — a later
     Compliance-Gate wave builds `neo4j_compliance_gate_adapter.py`).
  2. `ctx.hypernym` LLM elicitation (`elicit_hypernyms`) — given the anchor
     (+ its triple context) and the retrieved fragments, the LLM proposes
     NORMALIZED policy-vocabulary hypernym labels with its own confidence
     s(r) in [0,1] and the citation_id of the single fragment that supports
     each proposal. Mirrors `context_graph_extraction.py`'s LLM-call shape
     exactly (openai client, `fix_invalid_json` parse, degrade-to-empty).
  3. Aggregate via `HypernymScoringService` (eqs. 1-2, max-pool + beta=0.3
     premise bonus + top-N=5) — UNCHANGED from 11-06 Task 2. It is fed the
     LLM's (label, confidence, is_premise) proposals, not raw fragments.

Candidate hypernym fragment retrieval (top-M policy fragments per anchor,
D-10): the default retriever embeds every `premise` / `meta-CU` / `actor-CU`
fragment's representative text (clause verbatim text for premises, the
formalized `subject` for CUs) with the SAME embedder as the existing graph
adapters (`SentenceTransformerEmbeddings(model=settings.graph_embedding_model)`,
`neo4j_ontology_graph_retrieval_adapter.py`'s reuse precedent) and ranks by
cosine similarity against an anchor's triple-context-enriched query text
(11-06b), in-process — no new Neo4j vector index is required for this
candidate pool size (~800 CUs). The fragment pool + its embeddings are
lazily cached at module scope (mirrors `reranking.py::_get_cross_encoder`'s
thread-safe lazy singleton) since the Policy Graph is static across queries
within a process.

Degrade-safe: the node NEVER raises. Any Neo4j/embedding/LLM failure during
fragment retrieval or hypernym elicitation is caught, logged, and degrades
that anchor's mapping list to empty (T-11-15-style graceful degradation).

The `fragment_retriever` / `scoring_service` constructor-injection seam
(callable/instance kwargs on `map_anchors_to_hypernyms`) exists so unit tests
never touch a live Neo4j instance — mirrors the constructor-injection
convention used throughout `rag/graph/retrieval/*_adapter.py`. The LLM
elicitation call itself is exercised in tests by patching `openai.OpenAI`
(mirrors `test_context_graph_extraction.py`'s testing shape), not by an
extra injection parameter, so the real settings-gated call path is covered.
"""

import hashlib
import json
import logging
import threading
from typing import Any, Callable, Dict, List, Optional

from infrastructure.config.settings import get_settings
from domain.services.hypernym_scoring_service import HypernymScoringService, ScoredFragment
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)

# The three D-10 anchor entity types (actor/data/system) — "other" triples
# never become anchors.
_ANCHOR_ENTITY_TYPES = frozenset({"actor", "system", "data"})

# Compliance Unit types eligible as hypernym candidate fragments (D-09/D-10):
# premises (definitional/interpretive — the STRONG-bonus source) plus the two
# judged obligation types, whose formalized `subject` is the paper's anchor
# vocabulary (D-37: "paper aligns anchors to subject roles").
_FRAGMENT_CU_TYPES = ("premise", "actor-CU", "meta-CU")

_FETCH_FRAGMENT_POOL_QUERY = """
MATCH (cu:ComplianceUnit)-[:FROM_CLAUSE]->(c:Clause)
WHERE cu.cu_type IN $cu_types
RETURN cu.cu_id AS cu_id, cu.cu_type AS cu_type, cu.premise_kind AS premise_kind,
       cu.subject AS subject, c.citation_id AS citation_id, c.text AS clause_text
""".strip()

# Type alias for the injectable fragment-retriever seam.
FragmentRetriever = Callable[[str, int, Any], List[Dict[str, Any]]]

# Separate locks for the embedder singleton and the fragment-pool cache
# (never nested/acquired-while-held — `_get_fragment_pool_with_embeddings`
# calls `_get_embedder` while NOT holding `_pool_lock`, so a single thread
# never attempts to re-enter a non-reentrant `Lock`, which would deadlock).
_embedder_lock = threading.Lock()
_pool_lock = threading.Lock()
_pool_cache: Optional[Dict[str, Any]] = None  # {"fragments": [...], "embeddings": [...]}
_embedder_cache: Optional[object] = None


def _derive_anchors(triples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Collect unique actor/data/system anchors from Context Graph triples
    (D-10). Both the subject and object slot of each triple can yield an
    anchor. Order-preserving de-duplication on (label.lower(), type).

    11-06b: each anchor also accumulates `context` — the
    `(predicate, other_entity_label)` relation(s) from every triple that
    mentions it, from whichever side (subject or object) it appears on. This
    is the triple context used to enrich the step-1 retrieval query (e.g. a
    "Patient monitoring systems" anchor that is the subject of `("Patient
    monitoring systems", "designated as", "CII")` carries
    `context=[("designated as", "CII")]`), so the retriever surfaces the
    CII-definition premise instead of matching on the bare label alone.
    """
    seen: Dict[tuple, Dict[str, Any]] = {}

    def _anchor(label: str, entity_type: str) -> Dict[str, Any]:
        key = (label.lower(), entity_type)
        if key not in seen:
            seen[key] = {"label": label, "type": entity_type, "context": []}
        return seen[key]

    for triple in triples:
        subject = str(triple.get("subject", "")).strip()
        subject_type = str(triple.get("subject_type", "")).strip().lower()
        predicate = str(triple.get("predicate", "")).strip()
        obj = str(triple.get("object", "")).strip()
        object_type = str(triple.get("object_type", "")).strip().lower()

        if subject and subject_type in _ANCHOR_ENTITY_TYPES:
            anchor = _anchor(subject, subject_type)
            if predicate or obj:
                anchor["context"].append((predicate, obj))

        if obj and object_type in _ANCHOR_ENTITY_TYPES:
            anchor = _anchor(obj, object_type)
            if predicate or subject:
                anchor["context"].append((predicate, subject))

    return list(seen.values())


def _render_anchor_context(anchor: Dict[str, Any]) -> str:
    """Render an anchor's accumulated triple context as a compact string (11-06b)."""
    context = anchor.get("context") or []
    parts = [f"{predicate} {other}".strip() for predicate, other in context if predicate or other]
    return "; ".join(part for part in parts if part)


def _render_anchor_query(anchor: Dict[str, Any]) -> str:
    """
    Triple-context-enriched retrieval query text for an anchor (11-06b step-1
    fix): `"<label> | <predicate> <object>; ..."`. Falls back to the bare
    label when the anchor carries no context (e.g. a stub anchor built for
    unit tests). Keeps the retriever's dense mechanism unchanged — only the
    query text changes.
    """
    label = anchor.get("label", "")
    rendered_context = _render_anchor_context(anchor)
    return f"{label} | {rendered_context}" if rendered_context else label


def _get_embedder(settings):
    """
    Lazy, thread-safe singleton embedder (mirrors reranking.py's cross-encoder
    cache). Uses its OWN lock (`_embedder_lock`), never `_pool_lock` — this
    function is called BOTH standalone and from inside
    `_get_fragment_pool_with_embeddings` while that function holds
    `_pool_lock`; sharing a lock would deadlock a non-reentrant `Lock` on
    re-entry from the same thread.
    """
    global _embedder_cache
    if _embedder_cache is None:
        with _embedder_lock:
            if _embedder_cache is None:
                from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings

                logger.info(f"Loading embedding model for hypernym mapping: {settings.graph_embedding_model}")
                _embedder_cache = SentenceTransformerEmbeddings(model=settings.graph_embedding_model)
    return _embedder_cache


def _fragment_representative_text(fragment: Dict[str, Any]) -> str:
    """
    The text embedded/matched for a fragment (D-10): premises match on their
    verbatim clause text (the definitional/interpretive carrier); actor-CU/
    meta-CU fragments match on their formalized `subject` (falling back to
    clause text if Stage 2 has not yet populated `subject` for that CU).
    """
    if fragment.get("cu_type") == "premise":
        return fragment.get("clause_text") or ""
    return fragment.get("subject") or fragment.get("clause_text") or ""


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _fetch_fragment_pool(settings) -> List[Dict[str, Any]]:
    """Fetch every premise/actor-CU/meta-CU fragment from Neo4j (T-09-12: static, parameterized Cypher)."""
    import neo4j

    driver = neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        with driver.session(database=settings.neo4j_database) as session:
            result = session.run(_FETCH_FRAGMENT_POOL_QUERY, cu_types=list(_FRAGMENT_CU_TYPES))
            return [dict(record) for record in result]
    finally:
        driver.close()


def _get_fragment_pool_with_embeddings(settings) -> Dict[str, Any]:
    """
    Lazy, thread-safe module-scope cache of {fragments, embeddings} (the
    Policy Graph's candidate pool for hypernym mapping is static across
    queries within a process — D-14 "cache per-query extractions/anchors",
    generalized here to the corpus-side candidate pool).
    """
    global _pool_cache
    if _pool_cache is None:
        with _pool_lock:
            if _pool_cache is None:
                fragments = _fetch_fragment_pool(settings)
                embedder = _get_embedder(settings)
                embeddings = [
                    embedder.embed_query(_fragment_representative_text(f)) for f in fragments
                ]
                _pool_cache = {"fragments": fragments, "embeddings": embeddings}
                logger.info(f"Hypernym candidate fragment pool loaded: {len(fragments)} fragment(s)")
    return _pool_cache


def _default_fragment_retriever(anchor_label: str, top_m: int, settings) -> List[Dict[str, Any]]:
    """
    Retrieve the top-M policy fragments (premise/meta-CU/actor-CU) most
    similar to `anchor_label` (D-10). Degrade-safe: any failure (Neo4j
    unreachable, embedding model load failure, etc.) is caught, logged, and
    degrades to an empty candidate list — never raises.
    """
    try:
        pool = _get_fragment_pool_with_embeddings(settings)
        fragments = pool["fragments"]
        embeddings = pool["embeddings"]
        if not fragments:
            return []

        embedder = _get_embedder(settings)
        anchor_vector = embedder.embed_query(anchor_label)

        scored = [
            (fragment, _cosine_similarity(anchor_vector, vector))
            for fragment, vector in zip(fragments, embeddings)
        ]
        scored.sort(key=lambda pair: -pair[1])

        top = scored[:top_m]
        return [
            {
                "cu_id": fragment.get("cu_id", ""),
                "cu_type": fragment.get("cu_type", ""),
                "citation_id": fragment.get("citation_id", ""),
                "text": _fragment_representative_text(fragment),
                "is_premise": fragment.get("cu_type") == "premise",
                "score": score,
            }
            for fragment, score in top
        ]
    except Exception as e:
        logger.warning(f"Hypernym fragment retrieval failed for anchor {anchor_label!r}: {e}")
        return []


# --- ctx.hypernym LLM elicitation (11-06b step 2, Alg. 2 line 3) ----------
#
# Mirrors `context_graph_extraction.py`'s LLM-call shape exactly: `openai`
# client with api_key=settings.openrouter_api_key,
# base_url=settings.openrouter_base_url, model=settings.ontology_discovery_
# model; parse via neo4j_graphrag's `fix_invalid_json`; degrade-to-empty on
# unset api key or any exception; per-(entity, context, fragment-set) cache
# with a lock — the fragments already carry the query-scoping (they were
# retrieved with the anchor's triple-context-enriched query, 11-06b step 1),
# so keying the cache on entity + rendered context + the fragment set's
# citation_ids is equivalent to "cache per (query, entity-label)" without
# threading a separate query-id through this node.

CTX_HYPERNYM_ELICITATION_PROMPT = """You are mapping a specific entity from a Critical Information Infrastructure (CII) cybersecurity compliance scenario to the correct policy-vocabulary term(s) used by a Codes-of-Practice policy corpus.

ENTITY: {entity}
ENTITY CONTEXT (relations extracted from the scenario, may be empty): {entity_context}

RETRIEVED POLICY FRAGMENTS (candidate grounding — "premise" fragments are definitional/interpretive clauses; "actor-CU"/"meta-CU" fragments are formalized obligations/designation rules):
{fragments}

Propose up to 3 NORMALIZED policy-vocabulary hypernym labels for this entity — a clean policy term such as "critical information infrastructure", "computer system", or "controller", NEVER a raw fragment excerpt or enumeration item such as "(a) Operating systems;". For each proposal, give your own confidence in [0.0, 1.0] that the label correctly generalizes the entity (this confidence, not any retrieval similarity score, is the proposal's strength), and cite the citation_id of the single retrieved fragment above that most directly supports this label (or "" if none of the fragments support it).

Return ONLY a JSON array of objects, e.g.:
[{{"hypernym": "critical information infrastructure", "confidence": 0.92, "supporting_frag_id": "CCoP-1.2.1"}}]

No prose, no backticks, no explanation — JSON array only. If no reasonable hypernym can be proposed from the fragments above, return [].

PROPOSALS (JSON array):"""

# Per-(entity, entity_context, fragment-set) elicitation cache (mirrors
# `context_graph_extraction.py`'s `_extraction_cache` shape).
_hypernym_cache: Dict[str, List[Dict[str, Any]]] = {}
_hypernym_cache_lock = threading.Lock()


def _hypernym_cache_key(entity: str, entity_context: str, fragments: List[Dict[str, Any]]) -> str:
    fragment_sig = "|".join(
        f"{frag.get('citation_id') or frag.get('cu_id', '')}:{frag.get('cu_type', '')}"
        for frag in fragments
    )
    raw = f"{entity.strip().lower()}::{entity_context.strip().lower()}::{fragment_sig}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _render_fragment_block(fragments: List[Dict[str, Any]]) -> str:
    return "\n".join(
        f"[{frag.get('citation_id') or frag.get('cu_id', '')}] "
        f"({frag.get('cu_type', '')}) {frag.get('text', '')}"
        for frag in fragments
    )


def _parse_hypernym_proposals(raw: str) -> List[Dict[str, Any]]:
    """
    Parse + validate the LLM's JSON array response into a list of hypernym
    proposal dicts (`{hypernym, confidence, supporting_frag_id}`). Reuses
    `neo4j_graphrag`'s `fix_invalid_json` repair helper (same reuse
    discipline as `context_graph_extraction.py::_parse_triples`). Never
    raises — returns [] on total parse failure or malformed entries.
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
        logger.warning(f"Hypernym elicitation JSON parse failed: {e}")
        return []

    if not isinstance(parsed, list):
        logger.warning("Hypernym elicitation did not return a JSON array; discarding")
        return []

    proposals: List[Dict[str, Any]] = []
    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        hypernym = str(entry.get("hypernym", "")).strip()
        if not hypernym:
            continue
        try:
            confidence = float(entry.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))
        proposals.append(
            {
                "hypernym": hypernym,
                "confidence": confidence,
                "supporting_frag_id": str(entry.get("supporting_frag_id", "")).strip(),
            }
        )
    return proposals


def _elicit_hypernyms_llm(
    entity: str, entity_context: str, fragments: List[Dict[str, Any]], settings
) -> List[Dict[str, Any]]:
    """
    Call OpenRouter for the `ctx.hypernym` elicitation (Alg. 2 line 3).

    Mirrors `context_graph_extraction.py::_extract_context_graph_triples`'s
    settings-gated call + try/except-log-return degradation pattern exactly:
    returns [] (no hypernym proposals for this anchor) on any missing-key or
    LLM-call failure, never raises.
    """
    if not settings.openrouter_api_key:
        logger.warning("Hypernym elicitation enabled but OPENROUTER_API_KEY not set; skipping")
        return []
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=60,
        )
        prompt = CTX_HYPERNYM_ELICITATION_PROMPT.format(
            entity=entity,
            entity_context=entity_context or "(none)",
            fragments=_render_fragment_block(fragments),
        )
        resp = client.chat.completions.create(
            model=settings.ontology_discovery_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=500,
        )
        raw = (resp.choices[0].message.content or "").strip()
        return _parse_hypernym_proposals(raw)
    except Exception as e:
        logger.warning(f"Hypernym elicitation failed for entity {entity!r}: {e}")
        return []


def elicit_hypernyms(
    entity: str, entity_context: str, fragments: List[Dict[str, Any]], settings
) -> List[Dict[str, Any]]:
    """
    Cached `ctx.hypernym` elicitation (11-06b step 2, Alg. 2 line 3): given an
    entity (+ its triple context) and the top-M retrieved policy fragments,
    return LLM-proposed NORMALIZED hypernym labels, each with its own
    confidence s(r) in [0,1] and the citation_id of its supporting fragment.

    No fragments -> nothing to ground an elicitation in -> []  (never calls
    the LLM). Degrade-safe: unset api key or any exception -> [].
    """
    if not fragments:
        return []

    key = _hypernym_cache_key(entity, entity_context, fragments)
    with _hypernym_cache_lock:
        cached = _hypernym_cache.get(key)
    if cached is not None:
        return cached

    proposals = _elicit_hypernyms_llm(entity, entity_context, fragments, settings)

    with _hypernym_cache_lock:
        _hypernym_cache[key] = proposals
    return proposals


def map_anchors_to_hypernyms(
    state: GraphState,
    fragment_retriever: Optional[FragmentRetriever] = None,
    scoring_service: Optional[HypernymScoringService] = None,
) -> GraphState:
    """
    Derive actor/data/system anchors from the Context Graph and hypernym-map
    each to policy vocabulary via the §3.2-faithful 3-step pipeline (11-06b):
    (1) triple-context-enriched retrieval (grounding), (2) `ctx.hypernym` LLM
    elicitation (normalized labels + confidence + premise support), (3)
    `HypernymScoringService` aggregation (eqs. 1-2, unchanged).

    Gated on `mode == "graph-compliance"` — a no-op for every other mode.
    `fragment_retriever`/`scoring_service` are optional injection seams
    (default to the real Neo4j-backed retriever + `HypernymScoringService()`)
    used by tests to avoid touching live infrastructure. The LLM elicitation
    call (`elicit_hypernyms`) is exercised in tests by patching
    `openai.OpenAI`, mirroring `context_graph_extraction.py`'s testing shape.
    """
    if state.get("mode") != "graph-compliance":
        state["anchors"] = state.get("anchors", [])
        state["hypernym_mappings"] = state.get("hypernym_mappings", [])
        return state

    settings = get_settings()
    triples = state.get("context_graph_triples", [])
    anchors = _derive_anchors(triples)
    state["anchors"] = anchors

    retriever = fragment_retriever or _default_fragment_retriever
    scorer = scoring_service or HypernymScoringService()
    top_m = int(getattr(settings, "hypernym_top_m", 10))

    all_mappings: List[Dict[str, Any]] = []
    for anchor in anchors:
        query_text = _render_anchor_query(anchor)
        entity_context = _render_anchor_context(anchor)

        try:
            fragments = retriever(query_text, top_m, settings)
        except Exception as e:
            logger.warning(f"Fragment retriever raised for anchor {anchor['label']!r}: {e}")
            fragments = []

        try:
            proposals = elicit_hypernyms(anchor["label"], entity_context, fragments, settings)
        except Exception as e:
            logger.warning(f"Hypernym elicitation raised for anchor {anchor['label']!r}: {e}")
            proposals = []

        fragments_by_id = {
            (frag.get("citation_id") or frag.get("cu_id", "")): frag for frag in fragments
        }

        candidates: Dict[str, List[ScoredFragment]] = {}
        for proposal in proposals:
            hypernym_label = proposal["hypernym"]
            supporting_frag_id = proposal.get("supporting_frag_id", "")
            supporting_frag = fragments_by_id.get(supporting_frag_id)
            is_premise = bool(supporting_frag.get("is_premise", False)) if supporting_frag else False
            source_id = (
                (supporting_frag.get("citation_id") or supporting_frag.get("cu_id", ""))
                if supporting_frag
                else supporting_frag_id
            )
            # `text` is the SUPPORTING FRAGMENT's own text (e.g. the CII
            # definitional premise's verbatim clause text), not the hypernym
            # label — `ScoredFragment` (unmodified, hypernym_scoring_service.py)
            # is documented as "a single retrieved policy fragment... with its
            # raw retrieval/similarity score", and `HypernymMapping.
            # supporting_premise` is documented as "supporting premise
            # fragment text" (the D-17.2 evidence trail, e.g. "CII means...").
            # Falls back to the hypernym label only if the LLM cited a
            # `supporting_frag_id` that doesn't resolve to a retrieved
            # fragment, so a STRONG/WEAK mapping is never traced to "".
            fragment_text = supporting_frag.get("text", "") if supporting_frag else ""
            candidates.setdefault(hypernym_label, []).append(
                ScoredFragment(
                    text=fragment_text or hypernym_label,
                    score=float(proposal.get("confidence", 0.0)),
                    is_premise=is_premise,
                    source_id=source_id,
                )
            )

        for mapping in scorer.score_candidates(candidates):
            all_mappings.append(
                {
                    "anchor": anchor["label"],
                    "label": mapping.label,
                    "strong_weak": mapping.strong_weak,
                    "supporting_premise": mapping.supporting_premise,
                    "score": mapping.score,
                }
            )

    state["hypernym_mappings"] = all_mappings
    if anchors:
        logger.debug(f"Derived {len(anchors)} anchor(s), {len(all_mappings)} hypernym mapping(s)")

    return state


__all__: List[str] = [
    "map_anchors_to_hypernyms",
    "elicit_hypernyms",
    "FragmentRetriever",
]
