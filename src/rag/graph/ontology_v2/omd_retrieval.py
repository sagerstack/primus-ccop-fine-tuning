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

BUILD_ID = "omd-v1-20260709"
_ALIASES = json.loads((Path(__file__).parent / "concept_aliases.json").read_text())["concepts"]
# surface form (lower) -> canonical concept node name, longest-first so specific wins
_SURFACE: List[Tuple[str, str]] = sorted(
    ((s.lower(), node) for node, d in _ALIASES.items() for s in d["surface"]),
    key=lambda x: -len(x[0]),
)


def query_to_concepts(text: str) -> List[str]:
    """Map free-text query to canonical concept nodes by surface-form match."""
    low = " " + re.sub(r"[^a-z0-9]+", " ", text.lower()) + " "
    hits = []
    for surf, node in _SURFACE:
        pat = " " + surf + " " if len(surf) <= 4 else surf  # whole-word for short tokens
        if pat in low and node not in hits:
            hits.append(node)
    return hits


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


def retrieve(text: str, k: int = 8) -> Dict:
    """Full Channel-I retrieval. Returns {query_concepts, expanded, results:[...]}."""
    Q = query_to_concepts(text)
    Qplus = expand(Q)
    if not Q:
        return {"query_concepts": [], "expanded": [], "results": []}
    rows = _q(
        "MATCH (cl:Clause {build_id:$b})-[:INVOKES]->(c:Concept {build_id:$b}) "
        "WITH cl, "
        "  sum(CASE WHEN c.name IN $q THEN 1.0 ELSE 0 END) AS direct, "
        "  sum(CASE WHEN c.name IN $qp AND NOT c.name IN $q THEN 0.5 ELSE 0 END) AS hop "
        "WITH cl, direct + hop AS score WHERE score > 0 "
        "RETURN cl.citation_id AS citation_id, cl.source_doc AS doc, cl.text AS text, score "
        "ORDER BY score DESC, citation_id LIMIT $k",
        b=BUILD_ID, q=Q, qp=Qplus, k=k,
    )
    return {"query_concepts": Q, "expanded": Qplus, "results": rows}


if __name__ == "__main__":
    ql = sys.argv[1] if len(sys.argv) > 1 else "how long must passwords be?"
    out = retrieve(ql, k=8)
    print(f"query: {ql!r}")
    print(f"  Q  = {out['query_concepts']}")
    print(f"  Q+ = {out['expanded']}")
    print("  top clauses:")
    for r in out["results"]:
        print(f"    {r['score']:.1f}  [{r['citation_id']}]  {' '.join(r['text'].split())[:80]}")
