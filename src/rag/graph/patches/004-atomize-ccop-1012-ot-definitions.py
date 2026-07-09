"""
Patch 004 — atomize the CCoP-10.1.2 OT/ICS definitions table into 8 :Premise term
clauses, then de-premise the parent blob. Same shape as patch 002 (paper-aligned:
each term is a :Clause:Premise child; parent stops being a retrieval target).

Idempotent (MERGE on citation_id; REMOVE is a no-op if already done). Content:
004-atomize-ccop-1012-ot-definitions.json. Text passed as params — no escaping.

Run:  cd src && poetry run python rag/graph/patches/004-atomize-ccop-1012-ot-definitions.py
"""
import json, os, sys, neo4j

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "004-atomize-ccop-1012-ot-definitions.json")))
PARENT = DATA["parent_citation_id"]

UPSERT = """
MATCH (parent:Clause {citation_id:$parent})
MERGE (t:Clause {citation_id: $parent + '#' + $slug})
SET t:Premise,
    t.text = $text,
    t.premise_kind = 'definition',
    t.premise_cu_id = $parent + '#' + $slug,
    t.source_doc = parent.source_doc,
    t.doc_class = parent.doc_class,
    t.function_type = 'DefinitionClause',
    t.chapter = parent.chapter,
    t.clause_id = parent.clause_id + '#' + $slug,
    t.is_structural_header = false
MERGE (parent)-[:HAS_CHILD]->(t)
RETURN t.citation_id AS created
"""
DEPREMISE_PARENT = "MATCH (p:Clause:Premise {citation_id:$parent}) REMOVE p:Premise RETURN count(p) AS depremised"

CHECKS = [
    ("children_created",  "MATCH (:Clause {citation_id:$parent})-[:HAS_CHILD]->(t:Clause:Premise) RETURN count(t) AS v", len(DATA["terms"])),
    ("parent_depremised", "MATCH (p:Clause {citation_id:$parent}) RETURN (NOT p:Premise) AS ok", True),
    ("all_have_kind",     "MATCH (:Clause {citation_id:$parent})-[:HAS_CHILD]->(t:Premise) WHERE t.premise_kind='definition' RETURN count(t) AS v", len(DATA["terms"])),
]

def main():
    pw = os.environ.get("CCOP_NEO4J_PASSWORD", "test12345")
    drv = neo4j.GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", pw))
    with drv.session() as s:
        for term in DATA["terms"]:
            print("  upsert", s.run(UPSERT, parent=PARENT, slug=term["slug"], text=term["text"]).single()["created"])
        print("  de-premise parent:", s.run(DEPREMISE_PARENT, parent=PARENT).single()["depremised"])
        print("\npost-conditions:")
        ok = True
        for name, q, expected in CHECKS:
            got = s.run(q, parent=PARENT).single()[0]
            if got != expected: ok = False
            print(f"  [{'OK ' if got==expected else 'FAIL'}] {name}: got={got} expected={expected}")
    drv.close()
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
