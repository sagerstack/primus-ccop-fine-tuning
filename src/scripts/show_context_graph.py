"""Show the per-query Context Graph (triples -> anchors -> hypernyms) for a test-id.
Usage:  cd src && poetry run python scripts/show_context_graph.py B01-001
Requires: Neo4j up + CCOP_OPENROUTER_API_KEY set. Read-only; ~2 min (embeds the pool).
"""
import sys, json, glob, os
from rag.retrieval.nodes.context_graph_extraction import extract_context_graph
from rag.retrieval.nodes.anchor_hypernym_mapping import map_anchors_to_hypernyms

test_id = sys.argv[1] if len(sys.argv) > 1 else "B01-001"
gt_dir = os.environ.get("CCOP_TEST_CASES_DIR", "../ground-truth/test-suite/audit-20260629-1245")
bench = test_id.split("-")[0].lower()
f = glob.glob(f"{gt_dir}/{bench}_*.jsonl")[0]
q = next(json.loads(l)["input"]["question"] for l in open(f) if json.loads(l)["test_id"] == test_id)

print(f"TEST: {test_id}\nQUESTION: {q}\n")
st = {"mode": "graphcpl", "query": q}
st = extract_context_graph(st)
st = map_anchors_to_hypernyms(st)

print("=== ER/SAO TRIPLES ===")
for t in st["context_graph_triples"]:
    print(f"  ({t.get('subject')}) --[{t.get('predicate')}]--> ({t.get('object')})   [{t.get('subject_type')}/{t.get('object_type')}]")
print("\n=== ANCHORS (actor/data/system) ===")
for a in st["anchors"]:
    print(f"  {a['label']}  [{a['type']}]  context={a.get('context')}")
print("\n=== HYPERNYM MAPPINGS ===")
for m in st["hypernym_mappings"]:
    print(f"  {m['anchor']:34} -> {m['label']:36} [{m['strong_weak']}] score={m['score']:.2f}")
    if m.get("supporting_premise"):
        print(f"       <= {m['supporting_premise'][:90]}")
