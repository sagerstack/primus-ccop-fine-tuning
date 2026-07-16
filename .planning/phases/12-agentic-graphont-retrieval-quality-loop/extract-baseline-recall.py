#!/usr/bin/env python3
"""
Phase 12 Slice A0 — Baseline Recall Extractor

Computes clause-hit@k and recall@pool for the 18-case graphont baseline run
by globbing per-case context sidecars and joining against GT clause references.

Handles:
- Per-case context sidecars (tests-1-*-contexts.json)
- Missing sidecars (B01-001) flagged as "sidecar missing"
- Empty pools / empty retrievals
- Clause ID normalization (strip doc prefix, definition suffixes)

Output: JSON with per-case results + aggregate metrics
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Configuration
EVAL_DIR = Path("src/results/evaluations/2026-07")
GT_DIR = Path("ground-truth/test-suite/audit-20260629-1245")
OUTPUT_FILE = Path(".planning/phases/12-agentic-graphont-retrieval-quality-loop/baseline-recall-results.json")

# Target test cases (18 stratified validation sample)
TARGET_CASES = [
    "B01-001", "B02-001", "B03-001", "B04-001", "B05-001", "B06-001",
    "B07-006", "B08-001", "B09-001", "B10-001", "B12-001", "B13-001",
    "B14-001", "B18-001", "B21-001", "B22-001", "B23-001", "B24-001"
]

# Map test_id -> benchmark_id -> JSONL file
TEST_TO_BENCHMARK = {
    "B01-001": ("B01", "b01_ccop_applicability_scope.jsonl"),
    "B02-001": ("B02", "b02_compliance_classification.jsonl"),
    "B03-001": ("B03", "b03_conditional_compliance_reasoning.jsonl"),
    "B04-001": ("B04", "b04_it_ot_classification_boundary.jsonl"),
    "B05-001": ("B05", "b05_control_comprehension.jsonl"),
    "B06-001": ("B06", "b06_intent_understanding.jsonl"),
    "B07-006": ("B07", "b07_gap_identification_quality.jsonl"),
    "B08-001": ("B08", "b08_risk_based_prioritization.jsonl"),
    "B09-001": ("B09", "b09_risk_identification_residual_risk.jsonl"),
    "B10-001": ("B10", "b10_risk_justification_coherence.jsonl"),
    "B12-001": ("B12", "b12_audit_perspective_alignment.jsonl"),
    "B13-001": ("B13", "b13_evidence_expectation_awareness.jsonl"),
    "B14-001": ("B14", "b14_remediation_quality_feasibility.jsonl"),
    "B18-001": ("B18", "b18_responsibility_attribution_sg.jsonl"),
    "B21-001": ("B21", "b21_hallucination_over_specification.jsonl"),
    "B22-001": ("B22", "b22_waiver_exception_reasoning.jsonl"),
    "B23-001": ("B23", "b23_multi_regulator_coordination.jsonl"),
    "B24-001": ("B24", "b24_incident_response_guidance.jsonl"),
}


def normalize_citation_id(citation_id: str) -> str:
    """
    Normalize a citation_id to a bare clause reference.

    Rules:
    1. Strip document prefix (e.g., "CCoP 2.0::" or "CCoP Response to Feedback::")
    2. Strip definition suffix (e.g., "#remote access" -> remove)
    3. DO NOT strip subsection letter in parens (e.g., "3.2.2(a)" stays distinct from "3.2.2")
    4. Return empty string if input is empty/null

    Examples:
        "CCoP 2.0::5.7.2(b)" -> "5.7.2(b)"  (preserved!)
        "CCoP Response to Feedback::11.19" -> "11.19"
        "CCoP 2.0::1.2.1#remote access" -> "1.2.1"
        "Security By Design::AnnexC" -> "AnnexC"
        "CCoP 2.0::5.7.2" -> "5.7.2"
    """
    if not citation_id:
        return ""

    # Strip document prefix (everything before and including "::")
    if "::" in citation_id:
        clause_part = citation_id.split("::", 1)[1]
    else:
        clause_part = citation_id

    # Strip definition suffix (everything from "#" onwards)
    if "#" in clause_part:
        clause_part = clause_part.split("#", 1)[0]

    # NOTE: Intentionally do NOT strip subsection letter in parens.
    # Lettered sub-clauses (e.g., "3.2.2(a)" vs "3.2.2") are DISTINCT entries
    # in clause_inventory.json and should be matched exactly.

    return clause_part.strip()


def find_context_sidecar(test_id: str) -> Optional[Path]:
    """Find the most recent context sidecar for a test case (any recent timestamp)."""
    # Match any recent timestamp (20260713 or 20260714, etc.)
    pattern = f"eval-run-graphont-test-{test_id}-*contexts.json"
    matches = list(EVAL_DIR.glob(pattern))
    if not matches:
        return None
    # Return most recent (sort by file modification time, newest first)
    return sorted(matches, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def load_retrieved_citations(sidecar_path: Path) -> List[Dict]:
    """Load retrieved citations from a context sidecar."""
    with open(sidecar_path) as f:
        data = json.load(f)

    # Context sidecar format: {"TEST_ID": [{"citation_id": ..., "score": ...}, ...]}
    # Find the test_id key (should be the only key, or find matching one)
    for key, citations in data.items():
        if citations:  # Non-empty list
            return citations

    return []


def load_gt_clauses(test_id: str) -> List[str]:
    """Load ground-truth clause references for a test case."""
    if test_id not in TEST_TO_BENCHMARK:
        return []

    benchmark_id, jsonl_file = TEST_TO_BENCHMARK[test_id]
    jsonl_path = GT_DIR / jsonl_file

    if not jsonl_path.exists():
        return []

    with open(jsonl_path) as f:
        for line in f:
            try:
                test_case = json.loads(line)
                if test_case.get("test_id") == test_id:
                    # Try ground_truth.clause_reference first, then metadata.clause_reference
                    gt = test_case.get("ground_truth", {})
                    clauses = gt.get("clause_reference")
                    if clauses is None:
                        clauses = test_case.get("metadata", {}).get("clause_reference", [])
                    return clauses or []
            except json.JSONDecodeError:
                continue

    return []


def compute_recall_for_case(test_id: str) -> Dict:
    """Compute recall metrics for a single test case."""
    # Load GT clauses
    gt_clauses = load_gt_clauses(test_id)

    # Find context sidecar
    sidecar_path = find_context_sidecar(test_id)

    # Handle missing sidecar
    if sidecar_path is None:
        return {
            "test_id": test_id,
            "benchmark_id": TEST_TO_BENCHMARK[test_id][0] if test_id in TEST_TO_BENCHMARK else "unknown",
            "gt_clauses": gt_clauses,
            "retrieved_clauses": [],
            "normalized_retrieved": [],
            "pool_size": 0,
            "clause_hits": 0,
            "gt_count": len(gt_clauses),
            "clause_hit_at_k": None,  # Cannot compute without sidecar
            "recall_at_pool": None,  # Cannot compute without sidecar
            "status": "sidecar_missing",
            "sidecar_path": None,
            "notes": "No 20260713 context sidecar found — retrieval trace not captured; recommend re-run on this test case separately"
        }

    # Load retrieved citations
    retrieved = load_retrieved_citations(sidecar_path)

    # Extract and normalize citation IDs
    retrieved_citation_ids = [cite.get("citation_id", "") for cite in retrieved]
    normalized_retrieved = [normalize_citation_id(cid) for cid in retrieved_citation_ids]
    # Remove empty strings
    normalized_retrieved = [nc for nc in normalized_retrieved if nc]

    # Normalize GT clauses (apply normalization unconditionally to every GT clause)
    normalized_gt = [normalize_citation_id(str(gc)) for gc in gt_clauses]
    normalized_gt = [ng for ng in normalized_gt if ng]

    # Compute metrics
    # Convert to sets for matching
    retrieved_set = set(normalized_retrieved)
    gt_set = set(normalized_gt)

    # Clause-hit@k: did we retrieve at least one GT clause?
    clause_hits = len(retrieved_set & gt_set)

    # Recall@pool: proportion of GT clauses retrieved
    if len(gt_set) == 0:
        recall_at_pool = None  # No GT clauses to recall
    else:
        recall_at_pool = clause_hits / len(gt_set)

    # Clause-hit@k: binary (1 if any hit, 0 if none)
    clause_hit_at_k = 1 if clause_hits > 0 else 0

    # Determine status
    if len(retrieved) == 0:
        status = "empty_retrieval"
    elif recall_at_pool == 0.0:
        status = "no_match"
    elif recall_at_pool is None:
        status = "no_gt_clauses"
    else:
        status = "ok"

    return {
        "test_id": test_id,
        "benchmark_id": TEST_TO_BENCHMARK[test_id][0],
        "gt_clauses": gt_clauses,
        "normalized_gt": normalized_gt,
        "retrieved_clauses": retrieved_citation_ids,
        "normalized_retrieved": normalized_retrieved,
        "pool_size": len(retrieved),
        "clause_hits": clause_hits,
        "gt_count": len(gt_set),
        "clause_hit_at_k": clause_hit_at_k,
        "recall_at_pool": recall_at_pool,
        "status": status,
        "sidecar_path": str(sidecar_path),
        "notes": ""
    }


def main():
    """Main extraction pipeline."""
    print("=== Phase 12 Slice A0 — Baseline Recall Extractor ===\n")

    results = []
    for test_id in TARGET_CASES:
        print(f"Processing {test_id}...", end=" ")
        result = compute_recall_for_case(test_id)
        results.append(result)
        if result["status"] == "sidecar_missing":
            print("⚠️  SIDECAR MISSING")
        elif result["status"] == "empty_retrieval":
            print("⚠️  EMPTY RETRIEVAL")
        else:
            print(f"✓ pool={result['pool_size']}, hits={result['clause_hits']}/{result['gt_count']}, "
                  f"recall={result['recall_at_pool']:.2f}" if result['recall_at_pool'] is not None
                  else f"✓ pool={result['pool_size']}, hits={result['clause_hits']}/{result['gt_count']}, "
                       f"recall=N/A (no GT)")

    # Compute aggregate metrics (excluding missing sidecars and cases with no GT)
    valid_results = [r for r in results if r["status"] != "sidecar_missing"]
    results_with_gt = [r for r in valid_results if r["recall_at_pool"] is not None]

    aggregate = {
        "total_cases": len(TARGET_CASES),
        "completed_cases": len(valid_results),
        "missing_sidecars": len([r for r in results if r["status"] == "sidecar_missing"]),
        "empty_retrievals": len([r for r in valid_results if r["status"] == "empty_retrieval"]),
        "cases_with_gt": len(results_with_gt),
        "mean_pool_size": sum(r["pool_size"] for r in valid_results) / len(valid_results) if valid_results else 0,
        "mean_recall_at_pool": sum(r["recall_at_pool"] for r in results_with_gt) / len(results_with_gt) if results_with_gt else None,
        "clause_hit_at_k_rate": sum(r["clause_hit_at_k"] for r in results_with_gt) / len(results_with_gt) if results_with_gt else None,
    }

    # Save results
    output = {
        "metadata": {
            "extractor_version": "1.0",
            "extraction_date": "2026-07-14",
            "gt_directory": str(GT_DIR),
            "evaluation_directory": str(EVAL_DIR),
            "normalization_rule": "Strip document prefix (text before '::'), strip definition suffix (text after '#'), strip subsection letter in parens (e.g., '(b)')",
        },
        "per_case_results": results,
        "aggregate_metrics": aggregate,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n=== Aggregate Metrics (over {aggregate['completed_cases']}/{aggregate['total_cases']} completed) ===")
    print(f"Missing sidecars: {aggregate['missing_sidecars']}")
    print(f"Empty retrievals: {aggregate['empty_retrievals']}")
    print(f"Cases with GT clauses: {aggregate['cases_with_gt']}")
    print(f"Mean pool size: {aggregate['mean_pool_size']:.1f}")
    if aggregate['mean_recall_at_pool'] is not None:
        print(f"Mean recall@pool: {aggregate['mean_recall_at_pool']:.3f}")
        print(f"Clause-hit@k rate: {aggregate['clause_hit_at_k_rate']:.3f}")
    print(f"\nResults saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
