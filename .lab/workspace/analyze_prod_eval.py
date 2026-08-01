#!/usr/bin/env python3
"""
Analyze production eval results to compute lab-equivalent retrieval metrics.

Loads:
  - results JSONL (with retrieved_chunk_ids per test case)
  - contexts sidecar JSON (with metadata.merged_member_citation_ids — needed
    to expand parent-merge anchors into full citation lists)
  - corrected GT JSONLs (with metadata.clause_reference)

Computes per-case and aggregate:
  - recall@3, recall@5, recall@8, recall@C, recall@K
  - precision@N, f1@N

Same `match_score` as .lab/workspace/retrieval_eval.py — strict threshold 0.7.
"""
from __future__ import annotations
import argparse
import glob
import json
import os
from typing import Dict, List, Tuple

BASE = "/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc"
STRICT_THRESH = 0.7


def normalise_clause(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    if s.startswith("CCoP 2.0::"):
        s = s[len("CCoP 2.0::"):]
    return s


def is_subletter_of(child: str, parent: str) -> bool:
    if child == parent or not child.startswith(parent):
        return False
    rest = child[len(parent):]
    return rest.startswith(".") or rest.startswith("(")


def match_score(retrieved: str, expected: str) -> Tuple[float, str]:
    r, e = normalise_clause(retrieved), normalise_clause(expected)
    if not r or not e:
        return 0.0, "empty"
    if r == e:
        return 1.0, "exact"
    if is_subletter_of(e, r):
        return 0.7, "parent_of_expected"
    if is_subletter_of(r, e):
        return 0.7, "child_of_expected"
    r_parts, e_parts = r.split("."), e.split(".")
    if len(r_parts) >= 2 and len(e_parts) >= 2 and r_parts[:2] == e_parts[:2]:
        return 0.3, "same_section"
    if len(r_parts) >= 1 and len(e_parts) >= 1 and r_parts[0] == e_parts[0]:
        return 0.1, "same_chapter"
    return 0.0, "no_match"


def load_corrected_gt() -> Dict[str, List[str]]:
    gt = {}
    for fp in glob.glob(f"{BASE}/ground-truth/test-suite/*.jsonl"):
        if ".bak" in fp:
            continue
        with open(fp) as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                tid = row.get("test_id")
                refs = row.get("metadata", {}).get("clause_reference") or []
                if tid:
                    gt[tid] = [normalise_clause(r) for r in refs]
    return gt


def load_results(path: str) -> List[dict]:
    rows = []
    with open(path) as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("_partial_header"):
                continue
            rows.append(r)
    return rows


def load_contexts_expanded(path: str) -> Dict[str, List[List[str]]]:
    """Map test_id -> list of position groups, where each group is a list of
    citation_ids that this position represents (anchor + merged members)."""
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data = json.load(f)
    out: Dict[str, List[List[str]]] = {}
    for tid, ctxs in data.items():
        if not isinstance(ctxs, list):
            continue
        positions: List[List[str]] = []
        for c in ctxs:
            md = c.get("metadata") or {}
            members = md.get("merged_member_citation_ids")
            if members:
                positions.append([normalise_clause(m) for m in members])
            else:
                cid = c.get("citation_id") or ""
                positions.append([normalise_clause(cid)])
        out[tid] = positions
    return out


def compute_recall_at(retrieved_positions: List[List[str]], expected: List[str], n: int) -> Tuple[float, float, float]:
    """Compute recall/precision/f1 at top-N positions.

    A position is one slot in the LLM context window (an anchor + its merged
    siblings). For recall, an expected clause is "matched" if ANY citation in
    ANY of the first N positions matches strictly.
    For precision, count how many of the first N positions contain at least
    one citation that strictly matches an expected clause.
    """
    if not expected:
        return float("nan"), float("nan"), float("nan")
    if not retrieved_positions or n <= 0:
        return 0.0, 0.0, 0.0
    top_positions = retrieved_positions[:n]
    # Flatten into bag of citations (for recall)
    flat = [c for pos in top_positions for c in pos]
    matched = 0
    for e in expected:
        for r in flat:
            s, _ = match_score(r, e)
            if s >= STRICT_THRESH:
                matched += 1
                break
    recall = matched / len(expected)
    # Precision: positions that contain a strict match
    pmatches = 0
    for pos in top_positions:
        hit = False
        for r in pos:
            for e in expected:
                s, _ = match_score(r, e)
                if s >= STRICT_THRESH:
                    hit = True
                    break
            if hit:
                break
        if hit:
            pmatches += 1
    precision = pmatches / len(top_positions)
    f1 = (2 * recall * precision / (recall + precision)) if (recall + precision) > 0 else 0.0
    return recall, precision, f1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results", help="Path to results JSONL or partial.jsonl")
    ap.add_argument("--contexts", help="Path to contexts sidecar (auto-detected if omitted)", default=None)
    args = ap.parse_args()

    # Auto-detect contexts file
    contexts_path = args.contexts
    if not contexts_path:
        # results: ...primus-reasoning.partial.jsonl  or  primus-reasoning.json
        guess = args.results.replace("-primus-reasoning.partial.jsonl", "-contexts.json")
        guess = guess.replace("-primus-reasoning.json", "-contexts.json")
        if os.path.exists(guess):
            contexts_path = guess

    print(f"Loading corrected GT ...")
    gt = load_corrected_gt()
    print(f"  GT entries: {len(gt)}")

    print(f"Loading results from {args.results}")
    rows = load_results(args.results)
    print(f"  Result rows: {len(rows)}")

    print(f"Loading contexts (with merged_member_citation_ids) from {contexts_path}")
    contexts_map = load_contexts_expanded(contexts_path) if contexts_path else {}
    print(f"  Contexts: {len(contexts_map)} test cases")

    per_case = []
    for r in rows:
        tid = r.get("test_id")
        # Prefer expanded positions from contexts; fall back to retrieved_chunk_ids
        if tid in contexts_map:
            positions = contexts_map[tid]
        else:
            chunks = r.get("retrieved_chunk_ids", []) or []
            positions = [[normalise_clause(c)] for c in chunks]
        expected = gt.get(tid, [])
        if not expected:
            per_case.append({"test_id": tid, "n_expected": 0, "skip": True})
            continue
        cardinality = len(expected)
        K = len(positions)
        rec_3, prec_3, f1_3 = compute_recall_at(positions, expected, 3)
        rec_5, prec_5, f1_5 = compute_recall_at(positions, expected, 5)
        rec_8, prec_8, f1_8 = compute_recall_at(positions, expected, 8)
        rec_C, prec_C, f1_C = compute_recall_at(positions, expected, cardinality)
        rec_K, prec_K, f1_K = compute_recall_at(positions, expected, K)
        # Total expanded citations (sum of position sizes)
        n_expanded = sum(len(p) for p in positions)
        per_case.append({
            "test_id": tid,
            "cardinality": cardinality,
            "K": K,
            "n_expanded_citations": n_expanded,
            "expected": expected,
            "positions": positions,
            "recall@3": rec_3, "precision@3": prec_3, "f1@3": f1_3,
            "recall@5": rec_5, "precision@5": prec_5, "f1@5": f1_5,
            "recall@8": rec_8, "precision@8": prec_8, "f1@8": f1_8,
            "recall@C": rec_C, "precision@C": prec_C, "f1@C": f1_C,
            "recall@K": rec_K,
            "score": r.get("score"),
            "passed": r.get("passed"),
        })

    valid = [c for c in per_case if not c.get("skip")]
    avg_card = sum(c["cardinality"] for c in valid) / len(valid)
    avg_expand = sum(c["n_expanded_citations"] for c in valid) / len(valid)
    print()
    print("=" * 78)
    print(f"AGGREGATE — {len(valid)} cases (avg cardinality={avg_card:.1f}, "
          f"avg expanded citations per case={avg_expand:.1f})")
    print("=" * 78)
    keys = ["recall@3", "recall@5", "recall@8", "recall@C", "recall@K",
            "precision@3", "precision@C", "f1@3", "f1@C"]
    metrics = {}
    for k in keys:
        vals = [c[k] for c in valid if isinstance(c.get(k), (int, float))]
        avg = sum(vals) / len(vals) if vals else 0.0
        metrics[k] = avg
        print(f"  mean_{k:14s} = {avg:.4f}  (n={len(vals)})")

    print()
    print("Lab Exp #41 reference: R@C=0.5484, R@K=0.752, R@8=0.647, prec@3=0.292, f1@C=0.312")
    print()

    print("=" * 78)
    print("PER-CASE BREAKDOWN")
    print("=" * 78)
    print(f"{'test_id':10s} {'C':>2s} {'expK':>4s} {'r@3':>5s} {'r@5':>5s} {'r@8':>5s} {'r@C':>5s} {'r@K':>5s}")
    for c in valid:
        print(f"{c['test_id']:10s} {c['cardinality']:>2d} {c['n_expanded_citations']:>4d} "
              f"{c['recall@3']:.3f} {c['recall@5']:.3f} {c['recall@8']:.3f} "
              f"{c['recall@C']:.3f} {c['recall@K']:.3f}")

    out = f"{BASE}/.lab/workspace/prod_eval_metrics.json"
    summary = {
        "n_cases": len(valid),
        "results_file": args.results,
        "contexts_file": contexts_path,
        "avg_cardinality": avg_card,
        "avg_expanded_citations_per_case": avg_expand,
        "metrics": metrics,
        "per_case": valid,
    }
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print()
    print(f"Saved metrics to {out}")


if __name__ == "__main__":
    main()
