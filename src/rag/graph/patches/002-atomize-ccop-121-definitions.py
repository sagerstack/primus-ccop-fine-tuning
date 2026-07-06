"""
Patch 002 — atomize the CCoP-1.2.1 definitions table into 8 :Premise term clauses,
then de-premise the parent blob. Paper-aligned (patch 001): each term is a
:Clause:Premise child of CCoP-1.2.1; the parent stops being a retrieval target.

Idempotent: MERGE on citation_id (re-run overwrites, never duplicates); REMOVE is a no-op
if already done. Content is authored in 002-atomize-ccop-121-definitions.json (reviewable).
Text is passed as parameters — no Cypher string escaping.

Run:  cd src && poetry run python rag/graph/patches/002-atomize-ccop-121-definitions.py
"""
import json, os, sys, neo4j

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "002-atomize-ccop-121-definitions.json")))
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
    ("children_created",  "MATCH (:Clause {citation_id:$parent})-[:HAS_CHILD]->(t:Clause:Premise) RETURN count(t) AS v", 8),
    ("parent_depremised", "MATCH (p:Clause {citation_id:$parent}) RETURN (NOT p:Premise) AS ok", True),
    ("cii_has_7_1",       "MATCH (t:Clause {citation_id:$parent+'#CII'}) RETURN t.text CONTAINS 'section 7(1)' AS ok", True),
    ("all_have_kind",     "MATCH (:Clause {citation_id:$parent})-[:HAS_CHILD]->(t:Premise) WHERE t.premise_kind='definition' RETURN count(t) AS v", 8),
]

def main():
    pw = os.environ.get("CCOP_NEO4J_PASSWORD", "test12345")
    drv = neo4j.GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", pw))
    with drv.session() as s:
        for term in DATA["terms"]:
            r = s.run(UPSERT, parent=PARENT, slug=term["slug"], text=term["text"]).single()
            print("  upsert", r["created"])
        print("  de-premise parent:", s.run(DEPREMISE_PARENT, parent=PARENT).single()["depremised"])
        print("\npost-conditions:")
        ok = True
        for name, q, expected in CHECKS:
            got = s.run(q, parent=PARENT).single()[0]
            flag = "OK " if got == expected else "FAIL"
            if got != expected: ok = False
            print(f"  [{flag}] {name}: got={got} expected={expected}")
    drv.close()
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
