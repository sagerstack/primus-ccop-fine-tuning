#!/usr/bin/env python3
"""Compute Cohen's κ between human labels and judge scores for B1 validation.

Inputs:
  - human_labels.jsonl      : one row per (test_id, dim) with human score
  - judge_scores.jsonl      : one row per (test_id, dim) with judge score
                              (same schema; multiple judge runs can each be a file)

Both files use the schema:
  {"test_id": str, "mode": "hybrid"|"llm-only", "dim": str,
   "score": 0|1|2|3, "justification": str (optional), "source": str}

Outputs:
  - Per-dimension κ + 95% CI
  - Aggregate κ across all dimensions
  - Disagreement matrix (confusion matrix) per dimension
  - Prints plus writes to kappa_results.md
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable


def load_scores(path: Path) -> dict[tuple[str, str, str], int]:
    """Return mapping (test_id, mode, dim) -> score."""
    scores: dict[tuple[str, str, str], int] = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            key = (row["test_id"], row.get("mode", "hybrid"), row["dim"])
            scores[key] = int(row["score"])
    return scores


def cohens_kappa(pairs: list[tuple[int, int]], categories: Iterable[int] = (0, 1, 2, 3)) -> tuple[float, float, float]:
    """Compute Cohen's κ with 95% CI using Fleiss's asymptotic SE approximation.

    Returns (kappa, ci_lower, ci_upper).
    """
    if not pairs:
        return (float("nan"), float("nan"), float("nan"))

    cats = list(categories)
    n = len(pairs)
    # Observed agreement
    p_o = sum(1 for a, b in pairs if a == b) / n
    # Marginals
    a_counts = {c: 0 for c in cats}
    b_counts = {c: 0 for c in cats}
    for a, b in pairs:
        a_counts[a] = a_counts.get(a, 0) + 1
        b_counts[b] = b_counts.get(b, 0) + 1
    # Expected agreement by chance
    p_e = sum((a_counts.get(c, 0) / n) * (b_counts.get(c, 0) / n) for c in cats)

    if p_e == 1.0:
        return (float("nan"), float("nan"), float("nan"))

    kappa = (p_o - p_e) / (1.0 - p_e)

    # Fleiss approximate SE: sqrt((p_o * (1 - p_o)) / (n * (1 - p_e)**2))
    if n < 2:
        return (kappa, float("nan"), float("nan"))
    se = math.sqrt(max(0.0, p_o * (1.0 - p_o)) / (n * (1.0 - p_e) ** 2))
    ci_half = 1.96 * se
    return (kappa, kappa - ci_half, kappa + ci_half)


def weighted_kappa(pairs: list[tuple[int, int]], categories: list[int] = [0, 1, 2, 3]) -> float:
    """Quadratic-weighted κ for ordinal data. Penalizes large disagreements more."""
    if not pairs:
        return float("nan")
    cats = categories
    k = len(cats)
    n = len(pairs)
    # Observed matrix
    obs = {(a, b): 0 for a in cats for b in cats}
    for a, b in pairs:
        obs[(a, b)] = obs.get((a, b), 0) + 1
    # Marginals
    row = {c: sum(obs.get((c, b), 0) for b in cats) for c in cats}
    col = {c: sum(obs.get((a, c), 0) for a in cats) for c in cats}
    # Weight matrix (quadratic)
    max_d = (k - 1) ** 2
    weights = {
        (a, b): ((cats.index(a) - cats.index(b)) ** 2) / max_d
        for a in cats for b in cats
    }
    # Expected matrix
    exp = {(a, b): row[a] * col[b] / n for a in cats for b in cats}
    num = sum(weights[k2] * obs.get(k2, 0) for k2 in weights)
    den = sum(weights[k2] * exp[k2] for k2 in weights)
    if den == 0:
        return float("nan")
    return 1.0 - num / den


def confusion_matrix(pairs: list[tuple[int, int]], categories: list[int] = [0, 1, 2, 3]) -> list[list[int]]:
    matrix = [[0 for _ in categories] for _ in categories]
    for h, j in pairs:
        if h in categories and j in categories:
            matrix[categories.index(h)][categories.index(j)] += 1
    return matrix


def format_matrix(matrix: list[list[int]], categories: list[int] = [0, 1, 2, 3]) -> str:
    header = "          " + "  ".join(f"J={c}" for c in categories)
    rows = []
    for i, row in enumerate(matrix):
        row_str = f"H={categories[i]}    " + "  ".join(f"{v:4d}" for v in row)
        rows.append(row_str)
    return "\n".join([header] + rows)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--human", required=True, type=Path, help="human_labels.jsonl path")
    p.add_argument("--judge", required=True, type=Path, help="judge_scores.jsonl path")
    p.add_argument("--label", default="run", help="Label for this comparison (e.g., 'pre_A1', 'post_A1')")
    p.add_argument("--output", type=Path, default=None, help="Output markdown path (default: stdout only)")
    p.add_argument("--mode-filter", choices=["hybrid", "llm-only", "all"], default="all")
    args = p.parse_args()

    human = load_scores(args.human)
    judge = load_scores(args.judge)

    if args.mode_filter != "all":
        human = {k: v for k, v in human.items() if k[1] == args.mode_filter}
        judge = {k: v for k, v in judge.items() if k[1] == args.mode_filter}

    common_keys = set(human) & set(judge)
    if not common_keys:
        print("ERROR: no (test_id, mode, dim) keys in common between human and judge files", file=sys.stderr)
        return 2

    dims = sorted({k[2] for k in common_keys})

    lines: list[str] = []
    lines.append(f"# κ results — {args.label}")
    lines.append("")
    lines.append(f"- Mode filter: `{args.mode_filter}`")
    lines.append(f"- Human labels: {len(human)} scores")
    lines.append(f"- Judge scores: {len(judge)} scores")
    lines.append(f"- Paired (used for κ): {len(common_keys)} scores")
    lines.append("")
    lines.append("## Per-dimension κ")
    lines.append("")
    lines.append("| dim | N | κ (unweighted) | 95% CI | quadratic-weighted κ | mean_human | mean_judge | Δ mean |")
    lines.append("|-----|---|----------------|--------|-----------------------|------------|------------|--------|")

    all_pairs: list[tuple[int, int]] = []
    for dim in dims:
        pairs = [
            (human[(tid, mode, d)], judge[(tid, mode, d)])
            for (tid, mode, d) in sorted(common_keys)
            if d == dim
        ]
        if not pairs:
            continue
        all_pairs.extend(pairs)
        k, ci_lo, ci_hi = cohens_kappa(pairs)
        wk = weighted_kappa(pairs)
        mean_h = sum(h for h, _ in pairs) / len(pairs)
        mean_j = sum(j for _, j in pairs) / len(pairs)
        lines.append(
            f"| {dim} | {len(pairs)} | {k:.3f} | [{ci_lo:.2f}, {ci_hi:.2f}] | "
            f"{wk:.3f} | {mean_h:.2f} | {mean_j:.2f} | {mean_j - mean_h:+.2f} |"
        )

    # Aggregate
    if all_pairs:
        k, ci_lo, ci_hi = cohens_kappa(all_pairs)
        wk = weighted_kappa(all_pairs)
        lines.append("")
        lines.append(f"**Aggregate (all dims pooled)**: κ={k:.3f} [95% CI {ci_lo:.2f}, {ci_hi:.2f}]; weighted κ={wk:.3f}")

    # Disagreement detail
    lines.append("")
    lines.append("## Confusion matrices (rows=human, cols=judge)")
    lines.append("")
    for dim in dims:
        pairs = [
            (human[(tid, mode, d)], judge[(tid, mode, d)])
            for (tid, mode, d) in sorted(common_keys)
            if d == dim
        ]
        if not pairs:
            continue
        m = confusion_matrix(pairs)
        lines.append(f"### {dim}")
        lines.append("```")
        lines.append(format_matrix(m))
        lines.append("```")

    # Interpretation footer
    lines.append("")
    lines.append("## Interpretation (Landis & Koch 1977)")
    lines.append("")
    lines.append("| κ range | Label |")
    lines.append("|---------|-------|")
    lines.append("| 0.81-1.00 | Almost perfect |")
    lines.append("| 0.61-0.80 | Substantial |")
    lines.append("| 0.41-0.60 | Moderate |")
    lines.append("| 0.21-0.40 | Fair |")
    lines.append("| 0.00-0.20 | Slight / poor |")
    lines.append("")
    lines.append("Target for dissertation defense: κ ≥ 0.70 on each dimension.")

    output_text = "\n".join(lines)
    print(output_text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_text)
        print(f"\nWrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
