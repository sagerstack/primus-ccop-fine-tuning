"""
Compliance Gate — anchor→CU retrieval + CU Plan reranking (GraphCompliance §3.3,
eqs. 3-4). Mode-gated on `graphcpl`.

Per anchor (from the Context Graph, 11-06b), score every obligation CU
(actor-CU / meta-CU) by the paper's three-part bi-encoder (eq. 3):

    S(a,c) = w_ent·cos(v_ent(a), v_subj(c))
           + w_hyp·cos(v_hyp(a), v_subj(c))
           + w_bonus·1[ H(a) ∩ Subj(c) ≠ ∅ ]

take top-K1, then cross-encoder rerank (eq. 4) q(a)=[predicate; actor_type;
object_type] vs d(c)=[subject; constraint; condition] → the CU Plan. Retrieval unit
is the ATOMIC CU (never a chunk). Premises are NOT retrieved here — they enter the
grounding via the 11-06b hypernym STRONG-support. Writes `state["cu_plan"]` and
`state["verbatim_clause_texts"]`.

Pure paper (locked decision): no hybrid-text second channel / fallback floor.
Degrade-safe: any failure → empty CU Plan, never raises. Reuses the hypernym node's
embedder + cosine and reranking.py's cross-encoder.
"""
import logging
import threading
from typing import Any, Dict, List, Optional

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState
from rag.retrieval.nodes.anchor_hypernym_mapping import _get_embedder, _cosine_similarity

logger = logging.getLogger(__name__)

_MODE = "graphcpl"

_FETCH_CU_POOL_QUERY = """
MATCH (cu:ComplianceUnit)-[:FROM_CLAUSE]->(c:Clause)
WHERE cu.cu_type IN ['actor-CU', 'meta-CU']
RETURN cu.cu_id AS cu_id, cu.cu_type AS cu_type, cu.subject AS subject,
       cu.constraint AS constraint, cu.context AS context, cu.conditions AS conditions,
       cu.modality AS modality, c.citation_id AS citation_id, c.text AS clause_text
""".strip()

_cu_pool_lock = threading.Lock()
_cu_pool_cache: Optional[Dict[str, Any]] = None  # {"cus": [...], "subj_emb": [...]}


def _cfg(settings, name: str, default):
    return getattr(settings, name, default)


def _fetch_cu_pool(settings) -> List[Dict[str, Any]]:
    import neo4j
    driver = neo4j.GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        with driver.session(database=settings.neo4j_database) as s:
            return [dict(r) for r in s.run(_FETCH_CU_POOL_QUERY)]
    finally:
        driver.close()


def _get_cu_pool_with_embeddings(settings) -> Dict[str, Any]:
    """Lazy module-scope cache of the obligation-CU pool + subject embeddings (static G_P)."""
    global _cu_pool_cache
    if _cu_pool_cache is None:
        with _cu_pool_lock:
            if _cu_pool_cache is None:
                cus = _fetch_cu_pool(settings)
                embedder = _get_embedder(settings)
                subj_emb = [embedder.embed_query(c.get("subject") or "") for c in cus]
                _cu_pool_cache = {"cus": cus, "subj_emb": subj_emb}
                logger.info(f"Compliance-Gate CU pool loaded: {len(cus)} obligation CU(s)")
    return _cu_pool_cache


def _anchor_hypernyms(anchor_label: str, hypernym_mappings: List[Dict[str, Any]]) -> List[str]:
    return [m.get("label", "") for m in hypernym_mappings if m.get("anchor") == anchor_label and m.get("label")]


def _render_anchor_context(anchor: Dict[str, Any]) -> str:
    parts = [f"{p} {o}".strip() for p, o in (anchor.get("context") or []) if (p or o)]
    return "; ".join(x for x in parts if x)


def _subject_overlap(hyps: List[str], subject: str) -> bool:
    subj_terms = set(w for w in (subject or "").lower().replace(",", " ").split() if len(w) > 2)
    for h in hyps:
        if set(w for w in h.lower().split() if len(w) > 2) & subj_terms:
            return True
    return False


def _query_side(anchor: Dict[str, Any]) -> str:
    """q(a) = [predicate; actor_type; object_type] (eq. 4)."""
    preds = "; ".join(p for p, _ in (anchor.get("context") or []) if p)
    return f"{anchor.get('label','')} | {preds} | {anchor.get('type','')}".strip()


def _doc_side(cu: Dict[str, Any]) -> str:
    """d(c) = [subject; constraint; condition] (eq. 4)."""
    return f"{cu.get('subject','')}; {cu.get('constraint') or ''}; {cu.get('conditions') or ''}".strip()


def compliance_gate_retrieval(
    state: GraphState,
    cu_pool: Optional[Dict[str, Any]] = None,
    cross_encoder: Optional[Any] = None,
) -> GraphState:
    """
    Retrieve the CU Plan for the query's anchors (eqs. 3-4). Mode-gated on `graphcpl`,
    no-op otherwise. `cu_pool`/`cross_encoder` are injection seams for tests.
    """
    if state.get("mode") != _MODE:
        state["cu_plan"] = state.get("cu_plan", [])
        state["verbatim_clause_texts"] = state.get("verbatim_clause_texts", [])
        return state

    settings = get_settings()
    anchors = state.get("anchors", [])
    hypernym_mappings = state.get("hypernym_mappings", [])
    w_ent = float(_cfg(settings, "graphcpl_w_ent", 1.0))
    w_hyp = float(_cfg(settings, "graphcpl_w_hyp", 1.0))
    w_bonus = float(_cfg(settings, "graphcpl_w_bonus", 0.3))
    k1 = int(_cfg(settings, "graphcpl_k1", 20))
    k = int(_cfg(settings, "graphcpl_cu_plan_k", 8))

    try:
        pool = cu_pool or _get_cu_pool_with_embeddings(settings)
        cus, subj_emb = pool["cus"], pool["subj_emb"]
        if not cus or not anchors:
            state["cu_plan"] = []
            state["verbatim_clause_texts"] = []
            return state

        embedder = _get_embedder(settings)
        from rag.retrieval.nodes.reranking import _get_cross_encoder
        cross = cross_encoder or _get_cross_encoder(settings.cross_encoder_model)

        best: Dict[str, Dict[str, Any]] = {}  # cu_id -> {cu, score, anchors}
        for anchor in anchors:
            label = anchor.get("label", "")
            hyps = _anchor_hypernyms(label, hypernym_mappings)
            v_ent = embedder.embed_query(f"{label} | {_render_anchor_context(anchor)}".strip())
            v_hyp = embedder.embed_query("; ".join(hyps)) if hyps else v_ent

            # eq. 3 — bi-encoder over CU subjects
            scored = []
            for cu, v_subj in zip(cus, subj_emb):
                s = (w_ent * _cosine_similarity(v_ent, v_subj)
                     + w_hyp * _cosine_similarity(v_hyp, v_subj)
                     + (w_bonus if _subject_overlap(hyps, cu.get("subject", "")) else 0.0))
                scored.append((cu, s))
            scored.sort(key=lambda p: -p[1])
            cand = [cu for cu, _ in scored[:k1]]

            # eq. 4 — cross-encoder rerank
            q = _query_side(anchor)
            pairs = [(q, _doc_side(cu)) for cu in cand]
            rr = cross.predict(pairs) if pairs else []
            reranked = sorted(zip(cand, rr), key=lambda p: -float(p[1]))[:k]

            for cu, rscore in reranked:
                cid = cu["cu_id"]
                if cid not in best or float(rscore) > best[cid]["score"]:
                    best[cid] = {"cu": cu, "score": float(rscore), "anchor": label}

        cu_plan_items = sorted(best.values(), key=lambda x: -x["score"])
        state["cu_plan"] = [
            {
                "cu_id": b["cu"]["cu_id"],
                "cu_type": b["cu"]["cu_type"],
                "subject": b["cu"].get("subject", ""),
                "modality": b["cu"].get("modality", ""),
                "constraint": b["cu"].get("constraint") or "",
                "context": b["cu"].get("context") or "",
                "conditions": b["cu"].get("conditions") or "",
                "citation_id": b["cu"].get("citation_id", ""),
                "clause_text": b["cu"].get("clause_text", ""),
                "matched_anchor": b["anchor"],
                "score": b["score"],
            }
            for b in cu_plan_items
        ]
        state["verbatim_clause_texts"] = [
            {"citation_id": p["citation_id"], "text": p["clause_text"]} for p in state["cu_plan"]
        ]
        logger.info(f"Compliance-Gate CU Plan: {len(state['cu_plan'])} CU(s) over {len(anchors)} anchor(s)")
    except Exception as e:  # degrade-safe
        logger.warning(f"Compliance-Gate retrieval failed: {e}")
        state["cu_plan"] = []
        state["verbatim_clause_texts"] = []
    return state


__all__ = ["compliance_gate_retrieval"]
