"""Phase 6 — persist the CCoP definition/glossary layer as :Definition nodes (additive).

The 68 term definitions parsed in Phase 0 (definitions/*.json) were never loaded into Neo4j.
This loads them as a SEPARATE label so retrieval can *inject* them as grounding context
(query-concept -> its DEFINES definition) rather than let them compete in the ranked clause pool
(where IDF would bury the hub concepts they define — CII, CIIO, Provision).

Seeds (all carry the same BUILD_ID as build_omd_graph.py, so they drop with the rest of the layer):
  (:Definition {def_id, term, abbr, definition, source_doc, citation_id, build_id})
  (:Definition)-[:DEFINES {build_id}]->(:Concept)      # only for terms that map to a graph concept

def_id = f"{citation_id}#{term}"  — unique (terms unique within a citation_id; citation_id unique
per source). SBD Annex C re-defines CII/OT with its own citation_id, so those are distinct nodes
that DEFINES the same concept (source-specific definitions — intentional, not a dupe).

Mapping term -> concept: exact (normalised) match of the term OR its abbr against the concept
surface forms in concept_aliases.json. Unmapped terms ("shall", "vendor", "periodic", ...) still
load as :Definition nodes (BM25-reachable) but carry no DEFINES edge.

    poetry run python -m rag.graph.ontology_v2.build_definitions            # dry-run manifest
    poetry run python -m rag.graph.ontology_v2.build_definitions --apply
"""
import argparse
import json
import re
from pathlib import Path

from rag.graph.ontology_v2._neo import session, query as _q

BUILD_ID = "omd-v1-20260709"
_ROOT = Path(__file__).parent
_DEFS = _ROOT / "definitions"


# Hand-reviewed corrections to the surface-form auto-match (manifest review, 2026-07-09).
_REMAP = {
    "CII asset": "CIIAsset",                                # dedicated concept, not the CII hub
    "strong encryption": "Cryptography",                    # alias gap
    "scenario-based cybersecurity exercise": "CybersecurityExercise",  # alias gap
}
_BLOCK = {
    "cyber operating environment",  # def = broad environment, NOT the DigitalBoundary scope concept
    "mechanism",                    # generic ("an automated process"), not the def of SecurityControl
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _surface_to_concept() -> dict:
    """normalised surface form -> canonical concept name (from concept_aliases.json)."""
    aliases = json.loads((_ROOT / "concept_aliases.json").read_text())["concepts"]
    m = {}
    for node, d in aliases.items():
        for s in [node] + d.get("surface", []):
            m.setdefault(_norm(s), node)
    return m


def _load():
    surf = _surface_to_concept()
    live_concepts = {r["n"] for r in
                     _q("MATCH (c:Concept {build_id:$b}) RETURN c.name AS n", b=BUILD_ID)}
    defs, edges, unmapped = [], [], []
    seen = set()
    for f in sorted(_DEFS.glob("*.json")):
        for t in json.loads(f.read_text()):
            term, abbr, cid = t["term"], t.get("abbr", ""), t["citation_id"]
            def_id = f"{cid}#{term}"
            if def_id in seen:      # guard against accidental within-file dupes
                continue
            seen.add(def_id)
            defs.append({"def_id": def_id, "term": term, "abbr": abbr,
                         "definition": t["definition"], "source_doc": cid.split("::")[0],
                         "citation_id": cid})
            concept = _REMAP.get(term)
            if concept is None and term not in _BLOCK:
                concept = surf.get(_norm(term)) or (surf.get(_norm(abbr)) if abbr else None)
            if concept and concept in live_concepts:
                edges.append({"def_id": def_id, "concept": concept, "term": term})
            else:
                unmapped.append((term, abbr, cid))
    return defs, edges, unmapped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    defs, edges, unmapped = _load()

    print(f"MANIFEST (build_id={BUILD_ID})")
    print(f"  :Definition nodes to create : {len(defs)}")
    print(f"  :DEFINES edges (term->concept): {len(edges)}")
    print(f"  unmapped (node only, no edge): {len(unmapped)}")
    print(f"\n  -- DEFINES mapping ({len(edges)}) --")
    for e in sorted(edges, key=lambda x: x["concept"]):
        print(f"     {e['term']:42} -> :Concept {{{e['concept']}}}")
    print(f"\n  -- UNMAPPED, load as node only ({len(unmapped)}) --")
    for term, abbr, cid in unmapped:
        print(f"     {term:42} (abbr={abbr!r}, {cid.split('::')[0]})")

    if not a.apply:
        print("\ndry-run — pass --apply to write")
        return

    with session() as s:
        s.run("CREATE CONSTRAINT omd_definition IF NOT EXISTS "
              "FOR (d:Definition) REQUIRE (d.def_id, d.build_id) IS UNIQUE")
        s.run("UNWIND $rows AS r MERGE (d:Definition {def_id:r.def_id, build_id:$b}) "
              "SET d.term=r.term, d.abbr=r.abbr, d.definition=r.definition, "
              "d.source_doc=r.source_doc, d.citation_id=r.citation_id, d.name=r.term",
              rows=defs, b=BUILD_ID)
        s.run("UNWIND $rows AS r MATCH (d:Definition {def_id:r.def_id, build_id:$b}), "
              "(c:Concept {name:r.concept, build_id:$b}) "
              "MERGE (d)-[:DEFINES {build_id:$b}]->(c)", rows=edges, b=BUILD_ID)
        nd = s.run("MATCH (d:Definition {build_id:$b}) RETURN count(d) AS n", b=BUILD_ID).single()["n"]
        ne = s.run("MATCH (:Definition {build_id:$b})-[r:DEFINES]->() RETURN count(r) AS n",
                   b=BUILD_ID).single()["n"]
    print(f"\nLOADED: {nd} :Definition | {ne} :DEFINES")


if __name__ == "__main__":
    main()
