"""
Patch 005 — atomize the Auditing Guidelines glossary (section 8) into 10 :Premise
term clauses under AuditGuide-8, de-premise that parent, AND de-premise the 5
DUPLICATE copies (AuditGuide-1..5, which the chunking bug filled with this same
glossary text). Same atomize shape as 002/004 + an extra de-premise list.

Idempotent (MERGE + REMOVE). Content: 005-atomize-auditguide-glossary.json.
Run: cd src && poetry run python rag/graph/patches/005-atomize-auditguide-glossary.py
"""
import json, os, sys, neo4j

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "005-atomize-auditguide-glossary.json")))
PARENT = DATA["parent_citation_id"]
EXTRA = DATA.get("extra_depremise", [])

UPSERT = """
MATCH (parent:Clause {citation_id:$parent})
MERGE (t:Clause {citation_id: $parent + '#' + $slug})
SET t:Premise, t.text=$text, t.premise_kind='definition', t.premise_cu_id=$parent+'#'+$slug,
    t.source_doc=parent.source_doc, t.doc_class=parent.doc_class, t.function_type='DefinitionClause',
    t.chapter=parent.chapter, t.clause_id=parent.clause_id+'#'+$slug, t.is_structural_header=false
MERGE (parent)-[:HAS_CHILD]->(t)
RETURN t.citation_id AS created
"""
DEPREMISE = "MATCH (p:Clause:Premise {citation_id:$cid}) REMOVE p:Premise, p.premise_kind, p.premise_cu_id RETURN count(p) AS n"
CHECKS = [
    ("children_created", "MATCH (:Clause {citation_id:$parent})-[:HAS_CHILD]->(t:Clause:Premise) RETURN count(t) AS v", len(DATA["terms"])),
    ("parent_depremised", "MATCH (p:Clause {citation_id:$parent}) RETURN (NOT p:Premise) AS ok", True),
    ("dups_depremised", "MATCH (c:Clause:Premise) WHERE c.citation_id IN $extra RETURN count(c) AS v", 0),
]

def main():
    pw = os.environ.get("CCOP_NEO4J_PASSWORD", "test12345")
    drv = neo4j.GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", pw))
    with drv.session() as s:
        for term in DATA["terms"]:
            print("  upsert", s.run(UPSERT, parent=PARENT, slug=term["slug"], text=term["text"]).single()["created"])
        print("  de-premise parent:", s.run(DEPREMISE, cid=PARENT).single()["n"])
        for cid in EXTRA:
            print(f"  de-premise dup {cid}:", s.run(DEPREMISE, cid=cid).single()["n"])
        print("\npost-conditions:")
        ok = True
        for name, q, expected in CHECKS:
            got = s.run(q, parent=PARENT, extra=EXTRA).single()[0]
            if got != expected: ok = False
            print(f"  [{'OK ' if got==expected else 'FAIL'}] {name}: got={got} expected={expected}")
    drv.close()
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
