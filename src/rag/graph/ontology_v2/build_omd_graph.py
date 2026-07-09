"""Phase 5 — persist the OMD-GraphRAG layer to Neo4j (additive, build_id-tagged).

Seeds, from the hand-authored extraction cache:
  (:Clause {citation_id, text, source_doc, build_id})
  (:Concept {name, type, build_id})
  (:Clause)-[:INVOKES {build_id}]->(:Concept)          # clause invokes concept (POC direction)
  (:Concept)-[:REL {type, citation_id, build_id}]->(:Concept)

Everything carries BUILD_ID so the whole layer drops in one Cypher:
  MATCH (n {build_id:'omd-v1-20260709'}) DETACH DELETE n

    poetry run python -m rag.graph.ontology_v2.build_omd_graph            # dry-run counts
    poetry run python -m rag.graph.ontology_v2.build_omd_graph --apply
"""
import argparse
import json
import re
from pathlib import Path
from rag.graph.ontology_v2._neo import session

BUILD_ID = "omd-v1-20260709"
_ROOT = Path(__file__).parent
_REEXTRACT = _ROOT / "reextract"
_RUNS = _ROOT / "runs" / "extract"


def _load():
    clauses, concepts, invokes, rels = [], {}, [], []
    # every clause (even 0-triple) becomes a :Clause node
    text_by_cid = {}
    for d in sorted(_REEXTRACT.iterdir()):
        f = d / "clauses.clean.json"
        if f.exists():
            for r in json.loads(f.read_text()):
                cid = r["citation_id"]
                text_by_cid[cid] = r["text"]
                clauses.append({"citation_id": cid, "text": r["text"],
                                "source_doc": cid.split("::")[0]})
    for cf in _RUNS.glob("*.json"):
        d = json.loads(cf.read_text())
        if d.get("extractor") != "claude-opus":
            continue
        cid = d["citation_id"]
        invoked = set()
        for t in d["triples"]:
            for name, typ in ((t["s"], t["s_type"]), (t["o"], t["o_type"])):
                concepts[name] = typ
                invoked.add(name)
            rels.append({"s": t["s"], "o": t["o"], "type": t["rel"], "cid": cid})
        for name in sorted(invoked):
            invokes.append({"cid": cid, "name": name})
    return clauses, concepts, invokes, rels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    clauses, concepts, invokes, rels = _load()
    print(f"to load: {len(clauses)} :Clause | {len(concepts)} :Concept | "
          f"{len(invokes)} :INVOKES | {len(rels)} :REL  (build_id={BUILD_ID})")
    if not a.apply:
        print("dry-run — pass --apply to write")
        return
    with session() as s:
        s.run("CREATE CONSTRAINT omd_clause IF NOT EXISTS FOR (c:Clause) REQUIRE (c.citation_id, c.build_id) IS UNIQUE")
        s.run("CREATE CONSTRAINT omd_concept IF NOT EXISTS FOR (c:Concept) REQUIRE (c.name, c.build_id) IS UNIQUE")
        s.run("UNWIND $rows AS r MERGE (c:Clause {citation_id:r.citation_id, build_id:$b}) "
              "SET c.text=r.text, c.source_doc=r.source_doc, c.name=r.citation_id", rows=clauses, b=BUILD_ID)
        s.run("UNWIND $rows AS r MERGE (c:Concept {name:r.name, build_id:$b}) SET c.type=r.type",
              rows=[{"name": k, "type": v} for k, v in concepts.items()], b=BUILD_ID)
        s.run("UNWIND $rows AS r MATCH (cl:Clause {citation_id:r.cid, build_id:$b}), "
              "(co:Concept {name:r.name, build_id:$b}) MERGE (cl)-[:INVOKES {build_id:$b}]->(co)",
              rows=invokes, b=BUILD_ID)
        s.run("UNWIND $rows AS r MATCH (a:Concept {name:r.s, build_id:$b}), "
              "(c:Concept {name:r.o, build_id:$b}) "
              "MERGE (a)-[x:REL {type:r.type, citation_id:r.cid, build_id:$b}]->(c)",
              rows=rels, b=BUILD_ID)
        cl = s.run("MATCH (c:Clause {build_id:$b}) RETURN count(c) AS n", b=BUILD_ID).single()["n"]
        co = s.run("MATCH (c:Concept {build_id:$b}) RETURN count(c) AS n", b=BUILD_ID).single()["n"]
        iv = s.run("MATCH (:Clause {build_id:$b})-[r:INVOKES]->() RETURN count(r) AS n", b=BUILD_ID).single()["n"]
        re_ = s.run("MATCH (:Concept {build_id:$b})-[r:REL]->() RETURN count(r) AS n", b=BUILD_ID).single()["n"]
    print(f"LOADED: {cl} :Clause | {co} :Concept | {iv} :INVOKES | {re_} :REL")


if __name__ == "__main__":
    main()
