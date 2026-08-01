"""LIVE e2e gate: drive the REFACTORED omd_context_assembly for B02-001 on REAL infra
(live retrieve() -> Neo4j + dense npz + cross-encoder + live query_to_concepts LLM).
NO monkeypatch/freeze. Compare 4 output keys to the pre-refactor baseline sidecar.
"""
import json
import logging
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# capture any OMD-GraphRAG log line + logger name
logs = []
class _Cap(logging.Handler):
    def emit(self, r):
        if "OMD-GraphRAG" in r.getMessage():
            logs.append((r.name, r.levelname, r.getMessage()))
logging.getLogger().addHandler(_Cap())
logging.getLogger().setLevel(logging.INFO)

# real B02-001 question
q = None
with (REPO / "ground-truth/test-suite/b02_compliance_classification.jsonl").open() as fh:
    for line in fh:
        d = json.loads(line)
        if d["test_id"] == "B02-001":
            q = d["input"]["question"]
            break
assert q, "B02-001 not found"

from rag.retrieval.nodes.omd_context_assembly import omd_context_assembly

state = {"mode": "graphont", "query": q}
t0 = time.time()
omd_context_assembly(state)          # LIVE — real retrieve()
dt = time.time() - t0

fd = state["filtered_documents"]
live = [{"citation_id": d.metadata["citation_id"],
         "section": d.metadata["section"],
         "score": d.metadata["similarity_score"]} for d in fd]

# baseline sidecar
base = json.load(open(REPO / "src/results/evaluations/2026-07/"
                      "eval-run-graphont-test-B02-001-20260713-1059-contexts.json"))["B02-001"]
basel = [{"citation_id": e["citation_id"], "section": e["metadata"]["section"],
          "score": e["score"]} for e in base]

print(f"question: {q[:80]}...")
print(f"wall_time: {dt:.1f}s")
print(f"n_docs live={len(live)} baseline={len(basel)}")
print(f"is_rag_augmented={state['is_rag_augmented']} retrieval_succeeded={state['retrieval_succeeded']}")
print(f"log: {logs}")
tr = state.get("retrieval_trace", {})
print(f"\nretrieval_trace: ranked_by={tr.get('ranked_by')} d_cand={tr.get('d_cand')} "
      f"ce_confidence={tr.get('ce_confidence')} n_candidates={len(tr.get('candidates',[]))}")
print(f"  query_concepts={tr.get('query_concepts')}")
pc = tr.get("per_channel", {})
print(f"  per_channel.dense={[round(x,3) if x is not None else None for x in pc.get('dense',[])]}")
print(f"  per_channel.ch1 ={[round(x,2) if x is not None else None for x in pc.get('ch1',[])]}")

print("\n== SIDE-BY-SIDE (citation_id / score) ==")
print(f"{'#':>2} {'LIVE':30} {'BASELINE':30} match")
cid_match = order_match = True
for i in range(max(len(live), len(basel))):
    L = live[i]["citation_id"] if i < len(live) else "—"
    B = basel[i]["citation_id"] if i < len(basel) else "—"
    m = "✓" if L == B else "✗"
    if L != B:
        order_match = False
    print(f"{i+1:>2} {L:30} {B:30} {m}")

live_set = {d["citation_id"] for d in live}
base_set = {d["citation_id"] for d in basel}
cid_match = live_set == base_set

# score jitter (same-citation float delta)
score_deltas = []
bmap = {e["citation_id"]: e["score"] for e in basel}
for d in live:
    if d["citation_id"] in bmap:
        score_deltas.append(abs(d["score"] - bmap[d["citation_id"]]))
maxd = max(score_deltas) if score_deltas else 0.0

print(f"\nSET EQUAL (same clauses, any order): {cid_match}")
print(f"ORDER IDENTICAL: {order_match}")
print(f"MAX score delta (same cid): {maxd:.2e}")
print(f"RECALL@pool 5.7.2 present: {any('5.7.2' in c for c in live_set)}")
