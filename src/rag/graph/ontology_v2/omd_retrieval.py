"""OMD-GraphRAG Channel-I retrieval over the Neo4j :Concept layer (build_id-scoped).

The new retrieval methodology the `graphont` mode will point at. Pure new code — reads
only the OMD layer loaded by build_omd_graph.py; touches no existing retrieval node.

Pipeline (paper §3.1 + poc_reference/omd_b01,b05):
  1. query text -> concepts Q          (surface-form map from concept_aliases.json)
  2. Q -> Q+ = Q ∪ 1-hop over :REL      (graph expansion)
  3. score(clause) = |Q ∩ INVOKES| + 0.5·|(Q+−Q) ∩ INVOKES|
  4. return top-K clauses (citation_id, text, score)

    poetry run python -m rag.graph.ontology_v2.omd_retrieval "how long must passwords be?"

STATUS: works on specific-concept queries (B05 password bridge reproduces: 5.9.2(b)<->11.28).
KNOWN ISSUES (fix before wiring `graphont` / benchmarking) — surfaced by E2E on 2026-07-09:
  1. Mega-hub over-expansion: hub concepts (CII in 296 clauses, Provision, CIIO) expand 1-hop
     into ~half the ontology and flood scoring. FIX: concept-IDF weighting (weight ∝ 1/clause-freq;
     CII≈0) and/or don't expand from hubs. The POC reference handles this; this scorer is equal-weight.
  2. Thin query->concept coverage: only curated concept_aliases surface forms match, so concepts
     whose surface form isn't an alias (PenetrationTesting -> "penetration test", Monitoring, ...)
     map to Q=[]. FIX: auto-derive surface forms from CamelCase entity names + embedding/LLM fallback.
"""
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from rag.graph.ontology_v2._neo import query as _q
from infrastructure.config.settings import get_settings

BUILD_ID = "omd-v1-20260709"
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


_QPROMPT = """You map a regulatory question to the canonical knowledge-graph concepts it is ABOUT.
Return ONLY a JSON array of concept names chosen VERBATIM from this allowed list:
{vocab}

Rules:
- Choose the underlying regulatory concepts, not surface words. e.g. "patient monitoring systems" /
  "MRI machines" are a ComputerSystem/CIIAsset, NOT the Monitoring security-control concept;
  "hospital administration system" on a shared network relates to EnterpriseNetwork.
- Prefer SPECIFIC concepts (EnterpriseNetwork, DigitalBoundary, PasswordLength, AuditScope) over broad
  hubs (CII, CIIO, Provision) — include a hub only if the question is genuinely centred on it.
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


def query_to_concepts(text: str) -> List[str]:
    """Map query -> canonical concept nodes via schema-guided LLM extraction (POC design):
    the LLM reads the question and picks the concepts it is *about* from the graph's concept
    vocabulary — understanding meaning, not spotting keywords. Falls back to substring match."""
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


def expand(concepts: List[str]) -> List[str]:
    """Q+ − Q : 1-hop neighbours over :REL (either direction)."""
    if not concepts:
        return []
    rows = _q(
        "MATCH (c:Concept {build_id:$b})-[:REL]-(n:Concept {build_id:$b}) "
        "WHERE c.name IN $q AND NOT n.name IN $q RETURN DISTINCT n.name AS name",
        b=BUILD_ID, q=concepts,
    )
    return [r["name"] for r in rows]


# ---- Channel II: sparse (BM25) candidate generation over all clause texts --------------
import math
from collections import Counter

_STOP = set("the a an of to in on for and or is are be by with as at from that this which "
            "shall should must may any all its their there where when what how does do".split())
_CLAUSES: Dict[str, str] = {}   # citation_id -> text (lazy)
_BM25: Dict = {}                # built index (lazy)


def _tok(s: str) -> List[str]:
    return [w for w in re.sub(r"[^a-z0-9]+", " ", s.lower()).split() if len(w) > 2 and w not in _STOP]


def _build_bm25():
    global _CLAUSES, _BM25
    _CLAUSES = {r["cid"]: r["t"] for r in
                _q("MATCH (c:Clause {build_id:$b}) WHERE c.text IS NOT NULL "
                   "RETURN c.citation_id AS cid, c.text AS t", b=BUILD_ID)}
    docs = {cid: _tok(t) for cid, t in _CLAUSES.items()}
    N = len(docs)
    df = Counter(w for toks in docs.values() for w in set(toks))
    idf = {w: math.log(1 + (N - n + 0.5) / (n + 0.5)) for w, n in df.items()}
    avgdl = sum(len(t) for t in docs.values()) / max(N, 1)
    _BM25 = {"docs": {c: Counter(t) for c, t in docs.items()},
             "len": {c: len(t) for c, t in docs.items()}, "idf": idf, "avgdl": avgdl}


def channel2(text: str, k1: int = 40) -> List[Tuple[str, float]]:
    """Sparse (BM25) recall over ALL clause texts → top-k1 candidate (citation_id, score)."""
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


def retrieve(text: str, k: int = 8, k1: int = 40) -> Dict:
    """Dual-channel: Channel-II (BM25) recalls k1 candidates over all clauses → Channel-I
    (concept overlap) re-ranks ONLY those → light fusion. Mirrors the POC (Ch-I over a pool)."""
    Q = query_to_concepts(text)
    Qplus = expand(Q)
    cand = channel2(text, k1)
    cand_ids = [c for c, _ in cand]
    bm = {c: s for c, s in cand}
    bmax = max(bm.values()) if bm else 1.0
    if not cand_ids:
        return {"query_concepts": Q, "expanded": Qplus, "candidates": 0, "results": []}
    rows = _q(
        "MATCH (cl:Clause {build_id:$b})-[:INVOKES]->(c:Concept {build_id:$b}) "
        "WHERE cl.citation_id IN $cand "
        "WITH cl, "
        "  sum(CASE WHEN c.name IN $q THEN 1.0 ELSE 0 END) AS direct, "
        "  sum(CASE WHEN c.name IN $qp AND NOT c.name IN $q THEN 0.5 ELSE 0 END) AS hop "
        "RETURN cl.citation_id AS citation_id, cl.source_doc AS doc, cl.text AS text, direct+hop AS ch1",
        b=BUILD_ID, cand=cand_ids, q=Q or ["__none__"], qp=Qplus or ["__none__"],
    )
    res = []
    for r in rows:
        r = dict(r)
        r["bm25"] = bm.get(r["citation_id"], 0.0)
        r["score"] = r["ch1"] + 0.5 * (r["bm25"] / bmax)   # Ch-I primary, BM25 normalised secondary
        res.append(r)
    res.sort(key=lambda x: (-x["score"], -x["bm25"]))
    return {"query_concepts": Q, "expanded": Qplus, "candidates": len(cand_ids),
            "channel2": cand, "results": res[:k]}


if __name__ == "__main__":
    ql = sys.argv[1] if len(sys.argv) > 1 else "how long must passwords be?"
    out = retrieve(ql, k=8)
    print(f"query: {ql!r}\n")

    print(f"== CHANNEL II — BM25 sparse recall over all clauses (top 12 of {out['candidates']} candidates) ==")
    for cid, sc in out["channel2"][:12]:
        print(f"   {sc:5.1f}  [{cid}]  {' '.join(_CLAUSES.get(cid, '').split())[:66]}")

    print(f"\n== QUERY CONCEPTS ==")
    print(f"   Q  = {out['query_concepts']}")
    print(f"   Q+ = {out['expanded']}")

    print(f"\n== CHANNEL I — concept-overlap re-rank of the pool (final, fused) ==")
    for r in out["results"]:
        print(f"   {r['score']:.2f}  (ch1={r['ch1']:.1f} bm25={r['bm25']:.1f})  "
              f"[{r['citation_id']}]  {' '.join(r['text'].split())[:60]}")
