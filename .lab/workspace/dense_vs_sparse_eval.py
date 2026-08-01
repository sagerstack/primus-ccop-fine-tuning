#!/usr/bin/env python3
"""
Dense-only vs Sparse-only vs Hybrid retrieval eval.

For each test case, runs three separate searches at top-K against the same
Qdrant collection:
  - dense-only (BGE-large-en-v1.5 cosine)
  - sparse-only (Qdrant/bm25)
  - hybrid (RRF fusion of both)

Reports mean R@K for each at given K. No reranking, no LLM.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

SRC = Path("/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/src")
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Reuse matching logic
sys.path.insert(0, str(Path(__file__).parent))
from retrieval_eval import normalise_clause, match_score  # noqa: E402

STRICT_THRESH = 0.7


def compute_recall_topk(retrieved_clauses: List[str], expected: List[str]) -> float:
    if not expected or not retrieved_clauses:
        return 0.0
    n = 0
    for e in expected:
        best = 0.0
        for r in retrieved_clauses:
            score, _ = match_score(r, e)
            if score > best:
                best = score
        if best >= STRICT_THRESH:
            n += 1
    return n / len(expected)


def search_dense(client, collection, dense_vector, k: int):
    from qdrant_client.models import Prefetch
    results = client.query_points(
        collection_name=collection,
        query=dense_vector,
        using="dense",
        limit=k,
        with_payload=True,
        with_vectors=False,
    )
    return results.points


def search_sparse(client, collection, sparse_dict, k: int):
    from qdrant_client.models import SparseVector
    sv = SparseVector(indices=sparse_dict["indices"], values=sparse_dict["values"])
    results = client.query_points(
        collection_name=collection,
        query=sv,
        using="sparse",
        limit=k,
        with_payload=True,
        with_vectors=False,
    )
    return results.points


def search_hybrid(client, collection, dense_vector, sparse_dict, k: int):
    from qdrant_client.models import Prefetch, FusionQuery, Fusion, SparseVector
    sv = SparseVector(indices=sparse_dict["indices"], values=sparse_dict["values"])
    results = client.query_points(
        collection_name=collection,
        prefetch=[
            Prefetch(query=dense_vector, using="dense", limit=k * 2),
            Prefetch(query=sv, using="sparse", limit=k * 2),
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=k,
        with_payload=True,
        with_vectors=False,
    )
    return results.points


def points_to_clauses(points) -> List[str]:
    return [normalise_clause((p.payload or {}).get("citation_id", "")) for p in points]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-file", required=True)
    ap.add_argument("--top-k", type=int, default=50)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    with open(args.sample_file) as f:
        sample = json.load(f)
    test_ids = [c["test_id"] for c in sample]

    # Load raw test cases
    import glob
    raw_cases = {}
    for f in glob.glob("/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/ground-truth/test-suite/*.jsonl"):
        if ".bak" in f:
            continue
        with open(f) as fh:
            for line in fh:
                if not line.strip():
                    continue
                d = json.loads(line)
                raw_cases[d["test_id"]] = d

    cases = [raw_cases[tid] for tid in test_ids if tid in raw_cases]

    from infrastructure.config.container import get_container
    container = get_container()
    vs = container.vector_store()
    client = vs.client
    collection = vs.collection_name
    embed = vs.embedding_service

    print(f"Collection: {collection}, top_k={args.top_k}, n_cases={len(cases)}", file=sys.stderr)

    rows = []
    t0 = time.time()
    for i, tc in enumerate(cases, 1):
        question = tc["input"]["question"]
        expected = [normalise_clause(x) for x in tc.get("metadata", {}).get("clause_reference", []) or [] if x]
        if not expected:
            continue

        dv = embed.embed_query(question)
        sd = embed.embed_sparse(question)

        dense_pts = search_dense(client, collection, dv, args.top_k)
        sparse_pts = search_sparse(client, collection, sd, args.top_k)
        hybrid_pts = search_hybrid(client, collection, dv, sd, args.top_k)

        d_clauses = points_to_clauses(dense_pts)
        s_clauses = points_to_clauses(sparse_pts)
        h_clauses = points_to_clauses(hybrid_pts)

        d_recall = compute_recall_topk(d_clauses, expected)
        s_recall = compute_recall_topk(s_clauses, expected)
        h_recall = compute_recall_topk(h_clauses, expected)

        rows.append({
            "test_id": tc["test_id"],
            "expected": expected,
            "dense_recall_topk": d_recall,
            "sparse_recall_topk": s_recall,
            "hybrid_recall_topk": h_recall,
            "dense_clauses_top10": d_clauses[:10],
            "sparse_clauses_top10": s_clauses[:10],
        })
        print(f"[{i}/{len(cases)}] {tc['test_id']}: D={d_recall:.2f} S={s_recall:.2f} H={h_recall:.2f}", file=sys.stderr)

    dur = time.time() - t0

    n = len(rows)
    out = {
        "config": {"top_k": args.top_k, "n_cases": n},
        "duration_sec": round(dur, 1),
        "metrics": {
            "mean_dense_recall_topk": sum(r["dense_recall_topk"] for r in rows) / n,
            "mean_sparse_recall_topk": sum(r["sparse_recall_topk"] for r in rows) / n,
            "mean_hybrid_recall_topk": sum(r["hybrid_recall_topk"] for r in rows) / n,
        },
        "per_case": rows,
    }

    Path(args.output).write_text(json.dumps(out, indent=2))
    print(f"\nMean R@K: dense={out['metrics']['mean_dense_recall_topk']:.3f} "
          f"sparse={out['metrics']['mean_sparse_recall_topk']:.3f} "
          f"hybrid={out['metrics']['mean_hybrid_recall_topk']:.3f}", file=sys.stderr)
    print(f"Wrote: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
