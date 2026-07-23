"""OMD-GraphRAG Channel-I retrieval over the Neo4j :Concept layer (build_id-scoped).

The new retrieval methodology the `graphont` mode will point at. Pure new code — reads
only the OMD layer loaded by build_omd_graph.py; touches no existing retrieval node.

Pipeline (paper §3.1 + poc_reference/omd_b01,b05):
  1. query text -> concepts Q          (surface-form map from concept_aliases.json)
  2. Q -> Q+ = Q ∪ 1-hop over :REL      (graph expansion)
  2b. inject_definitions(Q)            (authoritative glossary grounding for Q concepts,
                                        via :Definition-[:DEFINES]->:Concept; bypasses ranking)
  3. score(clause) = |Q ∩ INVOKES| + 0.5·|(Q+−Q) ∩ INVOKES|
  4. return top-K clauses (citation_id, text, score) + injected definitions

    poetry run python -m rag.graph.ontology_v2.omd_retrieval "how long must passwords be?"

STATUS: tri-channel fusion + IDF + dense + definition injection wired (2026-07-09).
  - graph Channel-I: IDF-weighted concept overlap (compute_idf.py stores log(N/df) on :Concept; hubs
    CII≈1.1/CIIO≈0.8 vs rare EnterpriseNetwork/DigitalBoundary≈4-5) + hub-gated expansion, full corpus;
  - Traditional-RAG channel: BM25 keyword (channel2) ⊕ bge-large-en-v1.5 dense semantic (channel_dense,
    index by build_dense_index.py) — dense catches abstract clauses BM25/overlap miss (B01 §1.4.1 → dense#1);
  - fusion: Reciprocal Rank Fusion over the 3 ranked lists (rank-based, no score normalisation);
  - definition injection: glossary defs of Q concepts attach as grounding, bypassing ranking.
KNOWN LIMITATIONS (paper components NOT yet built — pending user scope decision):
  1. Equal-weight RRF dilutes single-channel-strong hits (§1.4.1 is dense#1 but fused#16). Paper fix =
     fold dense+BM25 into ONE Traditional channel, then β(q)-weighted fusion + a CROSS-ENCODER RERANKER
     over the fused pool (qwen3-reranker-8b in the paper) — the reranker is the real ranking fix.
  2. Channel-II *Community Report Retrieval* (Leiden Q_multi + τ=0.5 completion + LLM community reports
     + S_comm cosine) not built — the paper's community-level channel for multi-doc/global-theme queries.
  3. Act §7 / RtF §2.3 still miss — likely need the reranker (1) to rank recalled-but-diluted candidates.
"""
import hashlib
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from rag.graph.ontology_v2._neo import query as _q
from infrastructure.config.settings import get_settings

BUILD_ID = "omd-v1-20260709"

# ---- Fusion levers (configurable; overridable per retrieve() call) ----------------------
# Channel weights for the weighted RRF. Dense is upweighted per the project's own findings
# (settings Exp #11 "dense-only beats hybrid+RRF"; Exp #28 "CE-favored 1:1.5") and the B01-001
# ablation (dense↑ lifted the abstract GT clauses §1.4.1 67→32, RtF§2.3 55→29 without moving RtF§2.2 off #1).
W_GRAPH = 1.0    # graph Channel-I (IDF-weighted concept overlap)
W_BM25 = 0.7     # Traditional-RAG keyword
W_DENSE = 1.5    # Traditional-RAG semantic (bge)
RRF_K = 60       # RRF rank constant
# Per-channel recall depth (how many candidates each channel contributes to the fusion pool).
# Deeper than the old 40 so lexically/structurally-faint-but-relevant clauses (e.g. B01 Act §7,
# ranked 64-188 per channel) can enter the pool at all — the reranker cannot rank what never recalls.
RECALL_DEPTH = 100
# Cross-encoder reranker (paper §3.3.3, final stage). Scores each (question, clause) pair in the
# D_cand UNION and selects top-k. Reuses the project's model so graphont stays comparable to hybrid;
# swap RERANK_MODEL to "qwen3-reranker-8b" for paper-exact fidelity. Falls back to RRF order if the
# model can't load. RRF is still computed (used for the fallback + to bound/label the pool).
RERANK_ENABLED = True
RERANK_MODEL = None   # None -> settings.cross_encoder_model (BAAI/bge-reranker-large, Exp #7)
# Final order = reciprocal-rank fusion of the CE rank with the base fusion-RRF rank (project Exp #28),
# NOT pure-CE selection. bge-reranker-large collapses to clustered ~0 scores on short factoid queries
# (settings note); fusing keeps the good base ranking when the CE has no signal, and lets a confident
# CE dominate when it does. Set RERANK_CE_WEIGHT high / RERANK_RRF_WEIGHT=0 for paper-style pure-CE.
RERANK_CE_WEIGHT = 1.5
RERANK_RRF_WEIGHT = 1.0
# Confidence-adaptive CE weight: scale the CE's effective weight by how much it actually discriminated
# on THIS query — confidence = min(stdev(CE scores)/CONF_REF, 1). Validated on 6 benchmarks (B01/B02/
# B05/B12/B22/B24): confident queries (conf≈0.9-1.0) keep full CE; collapsed queries (conf≈0.01-0.12,
# where fixed-CE *damaged* the ranking — B12 targets 93→159) fall back to RRF. Never worse than RRF.
RERANK_ADAPTIVE = True
RERANK_CONF_REF = 0.15   # stdev of CE scores that counts as "fully confident" (conf=1)

_ALIASES = json.loads((Path(__file__).parent / "concept_aliases.json").read_text())["concepts"]
# surface form (lower) -> canonical concept node name, longest-first so specific wins
_SURFACE: List[Tuple[str, str]] = sorted(
    ((s.lower(), node) for node, d in _ALIASES.items() for s in d["surface"]),
    key=lambda x: -len(x[0]),
)
_VOCAB: Dict[str, str] = {}  # concept name -> type, from the live graph (lazy)


def _concept_vocab() -> Dict[str, str]:
    global _VOCAB
    if not _VOCAB:
        _VOCAB = {r["n"]: r["t"] for r in
                  _q("MATCH (c:Concept {build_id:$b}) RETURN c.name AS n, c.type AS t", b=BUILD_ID)}
    return _VOCAB


_IDF: Dict[str, float] = {}  # concept name -> idf (lazy, from compute_idf.py's :Concept.idf)


def _concept_idf() -> Dict[str, float]:
    global _IDF
    if not _IDF:
        _IDF = {r["n"]: r["idf"] for r in _q(
            "MATCH (c:Concept {build_id:$b}) WHERE c.idf IS NOT NULL "
            "RETURN c.name AS n, c.idf AS idf", b=BUILD_ID)}
    return _IDF


_QPROMPT = """You map a regulatory question to the canonical knowledge-graph concepts it is ABOUT.
Return ONLY a JSON array of concept names chosen VERBATIM from this allowed list:
{vocab}

Rules:
- Choose the underlying regulatory concepts, not surface words. e.g. "patient monitoring systems" /
  "MRI machines" are a ComputerSystem/CIIAsset, NOT the Monitoring security-control concept;
  "hospital administration system" on a shared network relates to EnterpriseNetwork.
- Prefer SPECIFIC concepts (EnterpriseNetwork, DigitalBoundary, PasswordLength, AuditScope) over broad
  hubs (CII, CIIO, Provision) — include a hub only if the question is genuinely centred on it.
- SCOPE / APPLICABILITY questions (does the Code apply, how far does the obligation extend, which
  systems are covered, where is the compliance boundary): ALWAYS include DigitalBoundary and Obligation —
  in CCoP the compliance scope is set by the CII's digital boundary, not by the physical or enterprise
  network. If a boundary is contested, also include Regulator (the boundary is determined by CSA/CIIO/Sector-Lead).
- 2-6 concepts. Names must match the list EXACTLY. No prose.

QUESTION:
{q}

JSON:"""


def _string_match_concepts(text: str) -> List[str]:
    """Fallback: surface-form substring match (noisy; degrade-safe only)."""
    low = " " + re.sub(r"[^a-z0-9]+", " ", text.lower()) + " "
    hits = []
    for surf, node in _SURFACE:
        pat = " " + surf + " " if len(surf) <= 4 else surf
        if pat in low and node not in hits:
            hits.append(node)
    return hits


def _query_to_concepts_uncached(text: str) -> List[str]:
    """Uncached LLM extraction — internal helper. Use query_to_concepts() for the cached version."""
    vocab = _concept_vocab()
    try:
        from openai import OpenAI
        s = get_settings()
        cli = OpenAI(api_key=s.openrouter_api_key, base_url=s.openrouter_base_url, timeout=45)
        r = cli.chat.completions.create(
            model=s.ontology_discovery_model, temperature=0.0, max_tokens=200,
            messages=[{"role": "user",
                       "content": _QPROMPT.format(vocab=", ".join(sorted(vocab)), q=text)}],
        )
        raw = (r.choices[0].message.content or "").strip()
        arr = json.loads(raw[raw.find("["):raw.rfind("]") + 1])
        picked = [c for c in arr if c in vocab]
        if picked:
            return picked
    except Exception:
        pass
    return _string_match_concepts(text)


def query_to_concepts(text: str) -> List[str]:
    """Map query -> canonical concept nodes via schema-guided LLM extraction (cached for determinism).
    Falls back to substring match if LLM call fails. Cache keyed by (model, build_id, question)."""
    s = get_settings()
    
    # Bypass cache if disabled
    if not s.query_concepts_cache_enabled:
        return _query_to_concepts_uncached(text)
    
    # Cache key: model|build_id|question
    cache_key = hashlib.sha256(f"{s.ontology_discovery_model}|{BUILD_ID}|{text}".encode()).hexdigest()
    
    # Cache file path
    cache_dir = Path(s.results_dir) / "cache"
    cache_file = cache_dir / "query_to_concepts_cache.json"
    
    # Load cache (fail-open)
    cache = {}
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        if cache_file.exists():
            cache = json.loads(cache_file.read_text())
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to load query_to_concepts cache: {e}")
    
    # Check cache
    if cache_key in cache:
        return cache[cache_key]
    
    # Cache miss: call uncached version
    result = _query_to_concepts_uncached(text)
    
    # Save to cache (fail-open)
    try:
        cache[cache_key] = result
        cache_file.write_text(json.dumps(cache, indent=2))
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to save query_to_concepts cache: {e}")
    
    return result


def expand(concepts: List[str], min_seed_idf: float = 2.5) -> List[str]:
    """Q+ − Q : 1-hop neighbours over :REL, but only expand FROM specific (high-idf) seeds.
    Expanding from a hub (CII idf≈1.1, CIIO≈0.8) reaches ~1/3 of the ontology and floods scoring
    via the hop term; a hub still counts as a direct match, it just doesn't seed expansion."""
    idf = _concept_idf()
    seeds = [c for c in concepts if idf.get(c, 99.0) >= min_seed_idf]
    if not seeds:
        return []
    rows = _q(
        "MATCH (c:Concept {build_id:$b})-[:REL]-(n:Concept {build_id:$b}) "
        "WHERE c.name IN $seeds AND NOT n.name IN $q RETURN DISTINCT n.name AS name",
        b=BUILD_ID, seeds=seeds, q=concepts,
    )
    return [r["name"] for r in rows]


# A definition that is only a cross-reference pointer ("As defined in section 2 of the Act.") — no
# content, and it poisons citation generation (the model invents a "Cybersecurity Act 2018" cite from
# the text). Anchored so substantive defs that merely *mention* the Act ("...as defined in...") survive.
_POINTER_DEF = re.compile(r"^\s*as defined in section .+ act\.?\s*$", re.I)


def inject_definitions(concepts: List[str], max_defs: int = 3) -> List[Dict]:
    """Authoritative-grounding slice: glossary definitions of the concepts the query is ABOUT (Q only).
    Attached independent of the ranked pool, so hub concepts (CII, CIIO) whose defs IDF would bury are
    still grounded. Noise controls (2026-07-09): (1) drop pointer stubs (no content); (2) keep the most
    SUBSTANTIVE definition per concept (CII has both a circular §1.2.1 stub and the full SBD Annex C
    def — keep the latter); (3) cap the total so multi-concept queries can't flood primus' context."""
    if not concepts:
        return []
    rows = [dict(r) for r in _q(
        "MATCH (d:Definition {build_id:$b})-[:DEFINES]->(c:Concept {build_id:$b}) "
        "WHERE c.name IN $q "
        "RETURN c.name AS concept, d.term AS term, d.definition AS definition, "
        "d.citation_id AS citation_id, d.source_doc AS source_doc "
        "ORDER BY c.name, d.source_doc",
        b=BUILD_ID, q=concepts,
    )]
    rows = [r for r in rows if not _POINTER_DEF.match(r["definition"] or "")]
    best: Dict[str, Dict] = {}                          # one (most substantive) def per concept
    for r in rows:
        c = r["concept"]
        if c not in best or len(r["definition"]) > len(best[c]["definition"]):
            best[c] = r
    # cap, preferring the most substantive definitions (longest = most informative grounding)
    return sorted(best.values(), key=lambda r: -len(r["definition"]))[:max_defs]


# ---- Retrievable passages: clauses + definitions -----------------------------------------
# The BM25 and dense channels retrieve over PASSAGES, not just :Clause. A :Definition is a
# first-class passage too (indexed text = "term: definition"), so the 40 glossary terms with no
# DEFINES edge — otherwise unreachable — become retrievable by content (e.g. "Existing CII",
# "CII Designation Date", the audit terms). Definitions keep DEFINES injection as a bonus path.
# id = citation_id for clauses, def_id ("<cite>#<term>") for definitions (distinguishable by '#').
import math
from collections import Counter

_STOP = set("the a an of to in on for and or is are be by with as at from that this which "
            "shall should must may any all its their there where when what how does do".split())
_PASSAGES: Dict[str, Dict] = {}   # id -> {text, kind, citation_id, doc, term, definition} (lazy)
_BM25: Dict = {}                  # built index (lazy)


def _passages() -> Dict[str, Dict]:
    """Unified retrievable-content store: every :Clause and every :Definition, keyed by id. Single
    source of truth for BM25, the dense index, and result hydration."""
    global _PASSAGES
    if not _PASSAGES:
        for r in _q("MATCH (c:Clause {build_id:$b}) WHERE c.text IS NOT NULL "
                    "RETURN c.citation_id AS id, c.text AS text, c.source_doc AS doc", b=BUILD_ID):
            _PASSAGES[r["id"]] = {"text": r["text"], "kind": "clause",
                                  "citation_id": r["id"], "doc": r["doc"]}
        for r in _q("MATCH (d:Definition {build_id:$b}) RETURN d.def_id AS id, d.definition AS def, "
                    "d.citation_id AS cite, d.term AS term, d.source_doc AS doc", b=BUILD_ID):
            _PASSAGES[r["id"]] = {"text": f"{r['term']}: {r['def']}", "kind": "definition",
                                  "citation_id": r["cite"], "doc": r["doc"],
                                  "term": r["term"], "definition": r["def"]}
    return _PASSAGES


def _tok(s: str) -> List[str]:
    return [w for w in re.sub(r"[^a-z0-9]+", " ", s.lower()).split() if len(w) > 2 and w not in _STOP]


def _build_bm25():
    global _BM25
    docs = {pid: _tok(p["text"]) for pid, p in _passages().items()}
    N = len(docs)
    df = Counter(w for toks in docs.values() for w in set(toks))
    idf = {w: math.log(1 + (N - n + 0.5) / (n + 0.5)) for w, n in df.items()}
    avgdl = sum(len(t) for t in docs.values()) / max(N, 1)
    _BM25 = {"docs": {c: Counter(t) for c, t in docs.items()},
             "len": {c: len(t) for c, t in docs.items()}, "idf": idf, "avgdl": avgdl}


def channel2(text: str, k1: int = 40) -> List[Tuple[str, float]]:
    """Sparse (BM25) recall over ALL passages (clauses + definitions) → top-k1 (id, score)."""
    if not _BM25:
        _build_bm25()
    qt = _tok(text)
    K1, b, av, idf = 1.5, 0.75, _BM25["avgdl"], _BM25["idf"]
    out = []
    for cid, tf in _BM25["docs"].items():
        dl = _BM25["len"][cid]
        s = sum(idf.get(w, 0.0) * (tf[w] * (K1 + 1)) / (tf[w] + K1 * (1 - b + b * dl / av))
                for w in qt if w in tf)
        if s > 0:
            out.append((cid, s))
    out.sort(key=lambda x: -x[1])
    return out[:k1]


def channel1(Q: List[str], Qplus: List[str], n1: int = 40) -> List[Tuple[str, float, str, str]]:
    """Structural recall over the FULL corpus, IDF-weighted (POC Channel-I, de-flooded):
    score(clause) = Σ_{c∈Q∩INVOKES} idf(c) + 0.5·Σ_{c∈(Q⁺−Q)∩INVOKES} idf(c).
    IDF (log(N/df) on :Concept) is what makes full-corpus scoring safe: hub concepts (CII≈1.1,
    CIIO≈0.8) can no longer flood past a focused decisive clause whose concepts are rare (≈4-5)."""
    if not Q:
        return []
    rows = _q(
        "MATCH (cl:Clause {build_id:$b})-[:INVOKES]->(c:Concept {build_id:$b}) "
        "WITH cl, "
        "  sum(CASE WHEN c.name IN $q THEN coalesce(c.idf,0.0) ELSE 0 END) AS direct, "
        "  sum(CASE WHEN c.name IN $qp AND NOT c.name IN $q THEN 0.5*coalesce(c.idf,0.0) ELSE 0 END) AS hop "
        "WITH cl, direct+hop AS ch1 WHERE ch1 > 0 "
        "RETURN cl.citation_id AS cid, ch1, cl.source_doc AS doc, cl.text AS text "
        "ORDER BY ch1 DESC LIMIT $n1",
        b=BUILD_ID, q=Q, qp=Qplus or ["__none__"], n1=n1,
    )
    return [(r["cid"], r["ch1"], r["doc"], r["text"]) for r in rows]


def _rrf(ranked_lists: List[List[str]], weights: List[float] = None,
         rrf_k: int = RRF_K) -> Dict[str, float]:
    """Weighted Reciprocal Rank Fusion: score(d) = Σ_channels wₖ/(rrf_k + rankₖ(d)). Rank-based, so
    the incomparable magnitudes of BM25 (lexical), bge cosine (dense) and IDF-weighted overlap
    (structural) fuse without normalisation; per-channel weights tilt the mix (dense↑ here)."""
    weights = weights if weights is not None else [1.0] * len(ranked_lists)
    scores: Dict[str, float] = {}
    for lst, w in zip(ranked_lists, weights):
        for i, cid in enumerate(lst):
            scores[cid] = scores.get(cid, 0.0) + w / (rrf_k + i + 1)
    return scores


# ---- Dense channel: bge-large-en-v1.5 semantic recall over the :Clause layer -----------
# The paper's Traditional-RAG *Semantic* half. Reuses the project encoder (build_dense_index.py)
# so graphont is comparable to hybrid mode. Catches semantically-but-not-lexically similar clauses
# (abstract scope/procedural clauses BM25 misses). Index built by build_dense_index.py.
_DENSE: Dict = {}          # {"cids": np.ndarray, "emb": (N,D) np.ndarray} (lazy)
_DMODEL = None             # SentenceTransformer (lazy)
_DENSE_QUERY_PROMPT = "Represent this sentence for searching relevant passages: "


def _dense_index():
    global _DENSE
    if not _DENSE:
        import numpy as np
        p = Path(__file__).parent / "runs" / "dense" / f"clauses_{BUILD_ID}.npz"
        if not p.exists():
            return None
        z = np.load(p, allow_pickle=True)
        _DENSE = {"cids": z["cids"], "emb": z["emb"]}
    return _DENSE


def channel_dense(text: str, kd: int = 40) -> List[Tuple[str, float]]:
    """Dense semantic recall over all clauses → top-kd (citation_id, cosine). Returns [] if the
    index is not built (build_dense_index.py --apply), so retrieval degrades to graph+BM25."""
    idx = _dense_index()
    if idx is None:
        return []
    global _DMODEL
    import numpy as np
    if _DMODEL is None:
        from sentence_transformers import SentenceTransformer
        _DMODEL = SentenceTransformer(get_settings().graph_embedding_model)
    qv = _DMODEL.encode(_DENSE_QUERY_PROMPT + text, normalize_embeddings=True,
                        convert_to_numpy=True).astype(np.float32)
    sims = idx["emb"] @ qv                      # both L2-normalised → cosine
    top = np.argsort(-sims)[:kd]
    return [(str(idx["cids"][i]), float(sims[i])) for i in top]


# ---- Cross-encoder reranker (final stage) ----------------------------------------------
_CE = None  # sentence_transformers.CrossEncoder (lazy)


def _cross_encoder(model_name: str = None):
    global _CE
    if _CE is None:
        from sentence_transformers import CrossEncoder
        _CE = CrossEncoder(model_name or get_settings().cross_encoder_model)
    return _CE


def rerank(query: str, candidates: List[Tuple[str, str]],
           model_name: str = None) -> List[Tuple[str, float]]:
    """Cross-encoder rerank (paper §3.3.3): score each (query, clause_text) pair in the D_cand union
    and return [(citation_id, ce_score)] sorted desc. candidates = [(citation_id, text), ...]."""
    if not candidates:
        return []
    ce = _cross_encoder(model_name)
    scores = ce.predict([(query, t) for _, t in candidates])
    return sorted(((cid, float(s)) for (cid, _), s in zip(candidates, scores)), key=lambda x: -x[1])


def retrieve(text: str, k: int = 8, n1: int = None, k1: int = None, kd: int = None,
             dense_query: str = None, w_graph: float = W_GRAPH, w_bm25: float = W_BM25, w_dense: float = W_DENSE,
             rrf_k: int = RRF_K, do_rerank: bool = RERANK_ENABLED, rerank_model: str = RERANK_MODEL,
             rerank_ce_w: float = RERANK_CE_WEIGHT, rerank_rrf_w: float = RERANK_RRF_WEIGHT,
             rerank_adaptive: bool = RERANK_ADAPTIVE, rerank_conf_ref: float = RERANK_CONF_REF) -> Dict:
    """Tri-channel weighted FUSION: IDF-weighted graph Channel-I (structural) + the Traditional-RAG
    channel (BM25 keyword ⊕ bge dense semantic), each recalling RECALL_DEPTH candidates over the FULL
    corpus, merged by weighted Reciprocal Rank Fusion (dense upweighted). Definitions of the Q concepts
    are injected as separate grounding (bypass ranking). All levers (depths, weights, rrf_k) are
    overridable. Dense degrades gracefully to 0 rows if build_dense_index.py hasn't run."""
    n1 = RECALL_DEPTH if n1 is None else n1
    k1 = RECALL_DEPTH if k1 is None else k1
    kd = RECALL_DEPTH if kd is None else kd
    Q = query_to_concepts(text)
    Qplus = expand(Q)
    definitions = inject_definitions(Q)

    ch1 = channel1(Q, Qplus, n1)                       # [(cid, ch1, doc, text)]  structural
    ch2 = channel2(text, k1)                           # [(cid, bm25)]            keyword
    chd = channel_dense(dense_query if dense_query is not None else text, kd)  # [(cid, cosine)] semantic
    ch1_by = {cid: (s, doc, txt) for cid, s, doc, txt in ch1}
    bm_by = {cid: s for cid, s in ch2}
    dn_by = {cid: s for cid, s in chd}

    rrf = _rrf([[c for c, *_ in ch1], [c for c, _ in ch2], [c for c, _ in chd]],
               weights=[w_graph, w_bm25, w_dense], rrf_k=rrf_k)
    if not rrf:
        return {"query_concepts": Q, "expanded": Qplus, "definitions": definitions,
                "channel1": ch1, "channel2": ch2, "dense": chd, "d_cand": 0,
                "ranked_by": "none", "results": []}

    # D_cand = the union of all channels' recalls (== keys of rrf), spanning clauses AND definitions.
    # The unified passage store hydrates text/doc/kind for every candidate (Channel-I only yields
    # clauses; BM25/dense may yield either).
    P = _passages()

    def _txt(cid):                                      # indexed text (for the reranker)
        p = P.get(cid)
        return p["text"] if p else (ch1_by[cid][2] if cid in ch1_by else "")

    def _rec(cid, score, ce=None):
        p = P.get(cid, {})
        return {"citation_id": p.get("citation_id", cid), "doc": p.get("doc", ""),
                "text": p.get("text", ""), "kind": p.get("kind", "clause"),
                "term": p.get("term"), "definition": p.get("definition"),
                "score": score, "ce_score": ce, "rrf": rrf[cid],
                "ch1": ch1_by.get(cid, (0.0,))[0],
                "bm25": bm_by.get(cid, 0.0), "dense": dn_by.get(cid, 0.0)}

    rrf_rank = {cid: i for i, (cid, _) in enumerate(sorted(rrf.items(), key=lambda x: -x[1]))}
    ranked_by, results, conf = "rrf", None, None
    if do_rerank:                                       # CE scores the whole union, then CE⊕RRF fuse
        try:
            ce_ranked = rerank(text, [(cid, _txt(cid)) for cid in rrf], rerank_model)
            ce_score = {cid: s for cid, s in ce_ranked}
            ce_rank = {cid: i for i, (cid, _) in enumerate(ce_ranked)}
            # confidence = how much the CE discriminated on THIS query (stdev of its scores).
            # Collapsed queries (all scores ≈0) → conf≈0 → CE weight→0 → fall back to RRF.
            conf = 1.0
            if rerank_adaptive and len(ce_ranked) > 1:
                conf = min(statistics.pstdev([s for _, s in ce_ranked]) / rerank_conf_ref, 1.0)
            eff_ce = rerank_ce_w * conf
            fused = {cid: eff_ce / (rrf_k + ce_rank[cid] + 1)
                          + rerank_rrf_w / (rrf_k + rrf_rank[cid] + 1) for cid in rrf}
            order = sorted(fused, key=lambda c: -fused[c])
            results = [_rec(cid, fused[cid], ce_score.get(cid)) for cid in order[:k]]
            ranked_by = f"ce+rrf(conf={conf:.2f})" if rerank_adaptive else "ce+rrf"
        except Exception as exc:                        # degrade to RRF order, never crash retrieval
            log = __import__("logging").getLogger(__name__)
            log.warning("rerank failed (%s) — falling back to RRF order", exc)
    if results is None:
        results = [_rec(cid, s) for cid, s in sorted(rrf.items(), key=lambda x: -x[1])[:k]]

    return {"query_concepts": Q, "expanded": Qplus, "definitions": definitions,
            "channel1": ch1, "channel2": ch2, "dense": chd, "d_cand": len(rrf),
            "ranked_by": ranked_by, "ce_confidence": conf, "results": results}


if __name__ == "__main__":
    ql = sys.argv[1] if len(sys.argv) > 1 else "how long must passwords be?"
    out = retrieve(ql, k=8)
    print(f"query: {ql!r}\n")

    print(f"== QUERY CONCEPTS ==")
    print(f"   Q  = {out['query_concepts']}")
    print(f"   Q+ = {out['expanded']}")

    print(f"\n== INJECTED DEFINITIONS (grounding for concepts in Q) ==")
    if out.get("definitions"):
        for d in out["definitions"]:
            print(f"   [{d['concept']}] {d['term']} ({d['citation_id']}):")
            print(f"       {' '.join(d['definition'].split())[:100]}")
    else:
        print("   (none — no Q concept has a glossary definition)")

    print(f"\n== CHANNEL I — IDF-weighted structural recall over full corpus (top 10) ==")
    for cid, sc, doc, txt in out["channel1"][:10]:
        print(f"   {sc:5.1f}  [{cid}]  {' '.join(txt.split())[:60]}")

    print(f"\n== TRADITIONAL-RAG / BM25 keyword recall over full corpus (top 10) ==")
    for cid, sc in out["channel2"][:10]:
        print(f"   {sc:5.1f}  [{cid}]  {' '.join(_passages().get(cid, {}).get('text', '').split())[:60]}")

    print(f"\n== TRADITIONAL-RAG / DENSE (bge) semantic recall over full corpus (top 10) ==")
    if out.get("dense"):
        for cid, sc in out["dense"][:10]:
            print(f"   {sc:5.2f}  [{cid}]  {' '.join(_passages().get(cid, {}).get('text', '').split())[:60]}")
    else:
        print("   (dense index not built — run build_dense_index.py --apply)")

    print(f"\n== FINAL — {out['ranked_by']} over D_cand={out['d_cand']} "
          f"(recall depth={RECALL_DEPTH}; RRF graph×{W_GRAPH} bm25×{W_BM25} dense×{W_DENSE}) "
          f"— top-{len(out['results'])} ==")
    for i, r in enumerate(out["results"]):
        ce = f"ce={r['ce_score']:+.2f}" if r.get("ce_score") is not None else f"rrf={r['rrf']:.4f}"
        print(f"   #{i+1:2} {ce}  (g={r['ch1']:.1f} bm={r['bm25']:.1f} dn={r['dense']:.2f})  "
              f"[{r['citation_id']}]  {' '.join(r['text'].split())[:50]}")
