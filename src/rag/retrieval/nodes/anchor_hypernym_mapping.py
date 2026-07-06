"""
Anchor Extraction + Hypernym Mapping Node (Phase 11, plan 11-06 Task 3,
D-09/D-10)

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
(label, type) pairs whose type is one of the three anchor types.

Candidate hypernym fragment retrieval (top-M policy fragments per anchor,
D-10) is a NARROWER, hypernym-mapping-scoped retrieval than the full
anchor->CU-Plan retrieval (D-11, bi-encoder K1 + cross-encoder rerank over
eqs. 3-4) — that two-channel retriever is out of this plan's scope (a later
Compliance-Gate wave builds `neo4j_compliance_gate_adapter.py`, per
11-PATTERNS.md's file classification). Here, the default retriever embeds
every `premise` / `meta-CU` / `actor-CU` fragment's representative text
(clause verbatim text for premises, the formalized `subject` for CUs) with
the SAME embedder as the existing graph adapters
(`SentenceTransformerEmbeddings(model=settings.graph_embedding_model)`,
`neo4j_ontology_graph_retrieval_adapter.py`'s reuse precedent) and ranks by
cosine similarity against the anchor label, in-process — no new Neo4j vector
index is required for this candidate pool size (~800 CUs). The fragment
pool + its embeddings are lazily cached at module scope (mirrors
`reranking.py::_get_cross_encoder`'s thread-safe lazy singleton) since the
Policy Graph is static across queries within a process.

Degrade-safe: the node NEVER raises. Any Neo4j/embedding failure during
fragment retrieval is caught, logged, and degrades that anchor's mapping list
to empty (T-11-15-style graceful degradation, generalized here from LLM
calls to the retrieval call).

The `fragment_retriever` / `scoring_service` constructor-injection seam
(callable/instance kwargs on `map_anchors_to_hypernyms`) exists so unit tests
never touch a live Neo4j instance — mirrors the constructor-injection
convention used throughout `rag/graph/retrieval/*_adapter.py`.
"""

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


def _derive_anchors(triples: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Collect unique actor/data/system anchors from Context Graph triples
    (D-10). Both the subject and object slot of each triple can yield an
    anchor. Order-preserving de-duplication on (label.lower(), type).
    """
    seen: Dict[tuple, Dict[str, str]] = {}
    for triple in triples:
        for role in ("subject", "object"):
            label = str(triple.get(role, "")).strip()
            entity_type = str(triple.get(f"{role}_type", "")).strip().lower()
            if not label or entity_type not in _ANCHOR_ENTITY_TYPES:
                continue
            key = (label.lower(), entity_type)
            if key not in seen:
                seen[key] = {"label": label, "type": entity_type}
    return list(seen.values())


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


def map_anchors_to_hypernyms(
    state: GraphState,
    fragment_retriever: Optional[FragmentRetriever] = None,
    scoring_service: Optional[HypernymScoringService] = None,
) -> GraphState:
    """
    Derive actor/data/system anchors from the Context Graph and hypernym-map
    each to policy vocabulary (D-09/D-10).

    Gated on `mode == "graph-compliance"` — a no-op for every other mode.
    `fragment_retriever`/`scoring_service` are optional injection seams
    (default to the real Neo4j-backed retriever + `HypernymScoringService()`)
    used by tests to avoid touching live infrastructure.
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
        try:
            fragments = retriever(anchor["label"], top_m, settings)
        except Exception as e:
            logger.warning(f"Fragment retriever raised for anchor {anchor['label']!r}: {e}")
            fragments = []

        candidates: Dict[str, List[ScoredFragment]] = {}
        for frag in fragments:
            label = (
                frag.get("subject")
                or frag.get("text", "")[:80]
                or frag.get("citation_id", "")
                or frag.get("cu_id", "")
            )
            candidates.setdefault(label, []).append(
                ScoredFragment(
                    text=frag.get("text", ""),
                    score=float(frag.get("score", 0.0)),
                    is_premise=bool(frag.get("is_premise", False)),
                    source_id=frag.get("citation_id") or frag.get("cu_id", ""),
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
    "FragmentRetriever",
]
