"""
Patch 006 — backfill + atomize the Cybersecurity Act 2018 s.2(1) definitions.

The graph's Act-2 node is a TRUNCATED blob holding only 3 of the ~27 s.2 defined
terms. This creates all 27 as :Clause:Premise children of Act-2 (sourced from
ccop-official/references/Cybersecurity Act 2018.pdf s.2, extracted programmatically),
then de-premises the Act-2 blob. Same shape as patches 002/004.

Idempotent (MERGE + REMOVE). Content: 006-backfill-act-s2-definitions.json.
Run: cd src && poetry run python rag/graph/patches/006-backfill-act-s2-definitions.py
"""
import json, os, sys, neo4j

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "006-backfill-act-s2-definitions.json")))
PARENT = DATA["parent_citation_id"]

UPSERT = """
MATCH (parent:Clause {citation_id:$parent})
MERGE (t:Clause {citation_id: $parent + '#' + $slug})
SET t:Premise, t.text=$text, t.premise_kind='definition', t.premise_cu_id=$parent+'#'+$slug,
    t.source_doc=parent.source_doc, t.doc_class=parent.doc_class, t.function_type='DefinitionClause',
    t.chapter=parent.chapter, t.clause_id=parent.clause_id+'#'+$slug, t.is_structural_header=false
MERGE (parent)-[:HAS_CHILD]->(t)
RETURN t.citation_id AS created
"""
DEPREMISE = "MATCH (p:Clause:Premise {citation_id:$parent}) REMOVE p:Premise, p.premise_kind, p.premise_cu_id RETURN count(p) AS n"
CHECKS = [
    ("children_created", "MATCH (:Clause {citation_id:$parent})-[:HAS_CHILD]->(t:Clause:Premise) RETURN count(t) AS v", len(DATA["terms"])),
    ("parent_depremised", "MATCH (p:Clause {citation_id:$parent}) RETURN (NOT p:Premise) AS ok", True),
    ("essential_service_present", "MATCH (t:Clause:Premise {citation_id:$parent+'#essential-service'}) RETURN count(t) AS v", 1),
]

def main():
    pw = os.environ.get("CCOP_NEO4J_PASSWORD", "test12345")
    drv = neo4j.GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", pw))
    with drv.session() as s:
        for term in DATA["terms"]:
            s.run(UPSERT, parent=PARENT, slug=term["slug"], text=term["text"]).single()
        print(f"  upserted {len(DATA['terms'])} term nodes under {PARENT}")
        print("  de-premise parent:", s.run(DEPREMISE, parent=PARENT).single()["n"])
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
