#!/usr/bin/env python3
"""Slice C threshold calibration script (Phase 12)

Captures (signal, recall) pairs over the FIXED 18-case stratified sample by running
omd_retrieval.retrieve() ONCE per case, extracting the 3 low-confidence detector
signals byte-identically to the live detector (reusing its own helpers), and scoring
recall against the union gold set (clause_reference ∪ xlsx bracketed citations).

Outputs:
  - 12-slice-c-calibration-signals.json : per-case {test_id, top1_ce_score, ce_confidence,
    top1_top2_margin, ce_confidence_is_none, recall, hit, gold_set, label}
  - 12-slice-c-threshold-calibration.md : per-signal GOOD/BAD distributions, BOTH
    conservative + balanced threshold options with TP/FP counts, None-frequency headline

HARD CONSTRAINTS:
  - READ-ONLY against the graphont pipeline (ADR-009): no mutations to omd_retrieval,
    omd_retrieve, omd_retrieval_grade, graph_state, or the corpus/index
  - REUSE detector helpers byte-identically: import _top1_ce_score, _top1_top2_margin
    from omd_retrieval_grade.py; read ce_confidence from retrieval_trace
  - REUSE scoring: ClauseHitScoringService.normalize_clause_id + recall methods
  - NO new metric code; NO edits to existing pipeline modules this step

30-min deadline. Errors on individual cases are captured but don't abort the run.
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path so we can import from the project
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from application.use_cases.clause_hit_harness import FIXED_18_TEST_IDS
from domain.services.clause_hit_scoring_service import ClauseHitScoringService
from infrastructure.config.container import Container
from rag.graph.ontology.gold_relation_parser import parse_gold_relations
from rag.graph.ontology_v2 import omd_retrieval
from rag.retrieval.nodes.omd_retrieval_grade import (
    _top1_ce_score,
    _top1_top2_margin,
)


def normalize_citation_id_for_comparison(citation_id: str) -> str:
    """Normalize citation_id to bare clause reference for gold set comparison.
    
    Rules:
    1. Strip document prefix (e.g., "CCoP 2.0::" or "CCoP Response to Feedback::")
    2. Strip definition suffix (e.g., "#remote access")
    3. Keep subsection letters in parens (e.g., "5.7.2(b)")
    
    Examples:
        "CCoP 2.0::5.7.2(b)" -> "5.7.2(b)"
        "CCoP Response to Feedback::11.19" -> "11.19"
        "CCoP 2.0::1.2.1#remote access" -> "1.2.1"
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
    
    return clause_part.strip()

# Constants
# Paths are relative to repo root since script is run from src/ with poetry run
GOLD_XLSX_PATH = Path(__file__).parent.parent.parent.parent / "ground-truth" / "expert-validation" / "CCoP_V2_Test_Cases_Expert_Review.xlsx"
GT_DIR = Path(__file__).parent.parent.parent.parent / "ground-truth" / "test-suite" / "audit-20260629-1245"
GOLD_SHEET_NAME = "Test Cases Review"
OUTPUT_DIR = Path(__file__).parent
SIGNALS_OUTPUT = OUTPUT_DIR / "12-slice-c-calibration-signals.json"
SIGNALS_PARTIAL = OUTPUT_DIR / "12-slice-c-calibration-signals.partial.json"
REPORT_OUTPUT = OUTPUT_DIR / "12-slice-c-threshold-calibration.md"

# Expected baseline recall from baseline-recall.md (~20.6%, ~4/17 non-N/A cases)
EXPECTED_RECALL_MIN = 0.15
EXPECTED_RECALL_MAX = 0.28


def load_gold_relations() -> Dict[str, set[str]]:
    """Load gold clause citations from the D-17 xlsx (eval-18 sheet).
    
    Returns: dict mapping test_id -> set of normalized clause citations
    """
    try:
        cases = parse_gold_relations(GOLD_XLSX_PATH, sheet_name=GOLD_SHEET_NAME)
        return {
            c.test_id: {
                ClauseHitScoringService.normalize_clause_id(cid)
                for cid in c.clause_citations
            } - {""}
            for c in cases
        }
    except FileNotFoundError:
        print(f"WARNING: Gold xlsx not found at {GOLD_XLSX_PATH}; falling back to clause_reference only")
        return {}


async def capture_case_signals(test_id: str, container: Container, gold_xlsx_by_id: Dict[str, set[str]]) -> Optional[Dict]:
    """Capture (signals, recall) for one test case.
    
    Returns: dict with {test_id, top1_ce_score, ce_confidence, top1_top2_margin,
             ce_confidence_is_none, recall, hit, gold_set, label, error}
             or None on fatal error
    """
    try:
        # Load test case
        repo = container.test_case_repository()
        test_cases = await repo.load_by_ids([test_id])
        if not test_cases:
            return {
                "test_id": test_id,
                "error": "test_case_not_found",
                "top1_ce_score": None,
                "ce_confidence": None,
                "top1_top2_margin": None,
                "ce_confidence_is_none": None,
                "recall": None,
                "hit": None,
                "gold_set": [],
                "retrieved_pool": [],
                "label": "ERROR",
            }
        
        test_case = test_cases[0]
        
        # Retrieve (k=8, ONCE per case)
        out = omd_retrieval.retrieve(test_case.question, k=8)
        
        # Build retrieval_trace exactly as omd_retrieve.py does
        candidates = out.get("results", [])
        retrieval_trace = {
            "candidates": candidates,
            "definitions": out.get("definitions", []),
            "ce_confidence": out.get("ce_confidence"),
            "ranked_by": out.get("ranked_by"),
            "d_cand": out.get("d_cand", 0),
            "query_concepts": out.get("query_concepts", []),
        }
        
        # Extract the 3 signals using detector helpers (byte-identical)
        top1_ce = _top1_ce_score(candidates)
        top1_top2_m = _top1_top2_margin(candidates)
        ce_conf = retrieval_trace.get("ce_confidence")
        ce_conf_is_none = ce_conf is None
        
        # Build gold set: clause_reference ∪ xlsx citations
        clause_reference = test_case.metadata.get("clause_reference") or []
        clause_ref_set = {
            ClauseHitScoringService.normalize_clause_id(c)
            for c in clause_reference
        } - {""}
        
        xlsx_set = gold_xlsx_by_id.get(test_id, set())
        gold_set = clause_ref_set | xlsx_set
        
        # Compute recall using existing ClauseHitScoringService
        # CRITICAL: normalize retrieved citation_ids to strip doc prefix ("CCoP 2.0::")
        # so they match the bare clause IDs in the gold set ("1.2.1", etc.)
        retrieved_pool = [
            normalize_citation_id_for_comparison(r.get("citation_id"))
            for r in candidates
            if r.get("citation_id")
        ]
        
        # Recall and hit
        recall = ClauseHitScoringService.recall_at_pool(
            gold_set, retrieved_pool, pool_size=len(retrieved_pool)
        )
        hit = ClauseHitScoringService.hit_at_3(gold_set, retrieved_pool[:3])
        
        # Label: GOOD iff recall > 0 (exclude B21-001 with no GT clauses as N/A later)
        label = "GOOD" if recall > 0 else "BAD"
        if not gold_set:
            label = "N/A"  # B21-001 has no GT clauses
        
        return {
            "test_id": test_id,
            "top1_ce_score": top1_ce,
            "ce_confidence": ce_conf,
            "top1_top2_margin": top1_top2_m,
            "ce_confidence_is_none": ce_conf_is_none,
            "recall": recall,
            "hit": hit,
            "gold_set": sorted(gold_set),
            "retrieved_pool": retrieved_pool,  # for debugging
            "label": label,
            "error": None,
        }
        
    except Exception as e:
        import traceback
        return {
            "test_id": test_id,
            "error": f"{type(e).__name__}: {str(e)}",
            "traceback": traceback.format_exc(),
            "top1_ce_score": None,
            "ce_confidence": None,
            "top1_top2_margin": None,
            "ce_confidence_is_none": None,
            "recall": None,
            "hit": None,
            "gold_set": [],
            "retrieved_pool": [],
            "label": "ERROR",
        }


def compute_thresholds(results: List[Dict], signal_name: str, signal_key: str) -> Dict:
    """Compute BOTH conservative and balanced threshold options for one signal.
    
    Args:
        results: list of case dicts with label and signal values
        signal_name: human-readable name (e.g. "top1_ce_score")
        signal_key: key in result dict
    
    Returns: dict with {signal, good_values, bad_values, conservative_tau, balanced_tau,
             overlap_warning, none_count}
    """
    # Filter out N/A and ERROR cases
    valid = [r for r in results if r["label"] in ("GOOD", "BAD")]
    
    # Separate GOOD and BAD
    good = [r[signal_key] for r in valid if r["label"] == "GOOD" and r[signal_key] is not None]
    bad = [r[signal_key] for r in valid if r["label"] == "BAD" and r[signal_key] is not None]
    
    # Count None values across all 18 cases (including N/A)
    none_count = sum(1 for r in results if r[signal_key] is None or r.get(f"{signal_key}_is_none"))
    
    # Check if signal is computable
    if not good and not bad:
        return {
            "signal": signal_name,
            "good_values": [],
            "bad_values": [],
            "conservative_tau": None,
            "conservative_tp": 0,
            "conservative_fp": 0,
            "balanced_tau": None,
            "balanced_tp": 0,
            "balanced_fp": 0,
            "overlap_warning": "No computable values",
            "none_count": none_count,
        }
    
    if not good:
        return {
            "signal": signal_name,
            "good_values": [],
            "bad_values": sorted(bad),
            "conservative_tau": None,
            "conservative_tp": 0,
            "conservative_fp": 0,
            "balanced_tau": None,
            "balanced_tp": 0,
            "balanced_fp": 0,
            "overlap_warning": "No GOOD cases with this signal",
            "none_count": none_count,
        }
    
    good_sorted = sorted(good)
    bad_sorted = sorted(bad)
    
    # Conservative τ = min(GOOD) - ε (zero FP on GOOD)
    # For "low if below threshold" signals, this means τ = min(GOOD) - small epsilon
    conservative_tau = min(good_sorted) - 0.01
    conservative_tp = len([b for b in bad if b < conservative_tau])
    conservative_fp = len([g for g in good if g < conservative_tau])  # Should be 0
    
    # Balanced τ = maximize separation (TP - FP)
    # Try all possible thresholds at BAD values
    best_separation = -999
    balanced_tau = None
    balanced_tp = 0
    balanced_fp = 0
    
    # Try thresholds at each BAD value
    for b in bad_sorted:
        tp = len([v for v in bad if v < b])
        fp = len([v for v in good if v < b])
        separation = tp - fp
        if separation > best_separation:
            best_separation = separation
            balanced_tau = b
            balanced_tp = tp
            balanced_fp = fp
    
    # Also try min(GOOD) as a threshold
    tau_at_min_good = min(good_sorted)
    tp = len([b for b in bad if b < tau_at_min_good])
    fp = len([g for g in good if g < tau_at_min_good])
    separation = tp - fp
    if separation > best_separation:
        best_separation = separation
        balanced_tau = tau_at_min_good
        balanced_tp = tp
        balanced_fp = fp
    
    # Check for complete overlap (no separating threshold exists)
    overlap_warning = None
    if max(bad_sorted) >= min(good_sorted):
        overlap_warning = "GOOD/BAD ranges overlap — no perfect separation possible"
    
    return {
        "signal": signal_name,
        "good_values": good_sorted,
        "bad_values": bad_sorted,
        "conservative_tau": round(conservative_tau, 4),
        "conservative_tp": conservative_tp,
        "conservative_fp": conservative_fp,
        "balanced_tau": round(balanced_tau, 4) if balanced_tau is not None else None,
        "balanced_tp": balanced_tp,
        "balanced_fp": balanced_fp,
        "overlap_warning": overlap_warning,
        "none_count": none_count,
    }


def generate_report(results: List[Dict], threshold_analyses: Dict) -> str:
    """Generate the markdown calibration report."""
    
    # Filter out N/A cases for aggregate stats
    valid_results = [r for r in results if r["label"] != "N/A"]
    good_count = len([r for r in valid_results if r["label"] == "GOOD"])
    bad_count = len([r for r in valid_results if r["label"] == "BAD"])
    error_count = len([r for r in results if r["label"] == "ERROR"])
    
    # Aggregate recall
    recalls = [r["recall"] for r in valid_results if r["recall"] is not None]
    avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
    
    report = f"""# Slice C Threshold Calibration Report

Generated: {Path(__file__).name}
Date: 2026-07-16

## Summary

**Test Set**: {len(results)} cases (FIXED_18_TEST_IDS, stratified bdc4927d sample)
- **GOOD** (recall > 0): {good_count} cases
- **BAD** (recall = 0): {bad_count} cases
- **N/A** (no gold clauses): {len([r for r in results if r["label"] == "N/A"])} cases
- **ERROR**: {error_count} cases

**Aggregate Recall**: {avg_recall:.1%} ({avg_recall:.4f})
- Expected baseline: ~20.6% (per baseline-recall.md)
- Sanity check: {"✅ PASS" if EXPECTED_RECALL_MIN <= avg_recall <= EXPECTED_RECALL_MAX else "⚠️  DRIFT DETECTED"}

## Threshold Analysis

For each signal, we present TWO operating points:

1. **CONSERVATIVE τ** = min(GOOD) - ε : Zero false positives on GOOD cases (high precision)
2. **BALANCED τ** = Best separation point: Maximizes (TP - FP) on this sample

"""
    
    # ce_confidence headline
    ce_conf_analysis = threshold_analyses.get("ce_confidence", {})
    none_freq = ce_conf_analysis.get("none_count", 0)
    report += f"""### ⚠️  ce_confidence=None Frequency

**{none_freq}/18 cases** ({none_freq/18*100:.0f}%) had ce_confidence=None (reranker did not run or raised).

**Implication**: TAU_CONF is only weakly grounded on this sample. The should_requery
logic in omd_retrieval_grade.py arms ONLY when ce_confidence is PRESENT and below threshold —
a None-confidence marks the grade as low_confidence but does NOT trigger requery (per team-lead
ruling: "None != below-threshold; None = untrustworthy but requery can't fix it").

If most cases have None, then TAU_CONF is calibrated on a small subset and should_requery
rarely arms → **flag for Slice D** (requery loop will rarely activate).

"""
    
    # Per-signal analysis
    for signal_name in ["top1_ce_score", "ce_confidence", "top1_top2_margin"]:
        analysis = threshold_analyses[signal_name]
        report += f"""---

### Signal: `{signal_name}`

**None count**: {analysis["none_count"]}/18 cases

"""
        
        if analysis.get("overlap_warning") == "No computable values":
            report += "⚠️  **No computable values for this signal** (all None or N/A)\n\n"
            report += "**Recommendation**: Leave this rule INERT (signal not available).\n\n"
            continue
        
        if analysis.get("overlap_warning") == "No GOOD cases with this signal":
            report += "⚠️  **No GOOD cases with this signal** (cannot calibrate)\n\n"
            report += "**Recommendation**: Leave this rule INERT (signal not available on GOOD cases).\n\n"
            continue
        
        # GOOD/BAD distributions
        report += "**GOOD distribution** (recall > 0):\n"
        if analysis["good_values"]:
            report += f"  - Values: {analysis['good_values']}\n"
            report += f"  - Range: [{min(analysis['good_values']):.4f}, {max(analysis['good_values']):.4f}]\n"
        else:
            report += "  - (none)\n"
        report += "\n"
        
        report += "**BAD distribution** (recall = 0):\n"
        if analysis["bad_values"]:
            report += f"  - Values: {analysis['bad_values']}\n"
            report += f"  - Range: [{min(analysis['bad_values']):.4f}, {max(analysis['bad_values']):.4f}]\n"
        else:
            report += "  - (none)\n"
        report += "\n"
        
        # Overlap warning
        if analysis.get("overlap_warning") and "overlap" in analysis["overlap_warning"]:
            report += f"⚠️  **{analysis['overlap_warning']}**\n\n"
            report += "At n=17, no threshold perfectly separates GOOD from BAD. Consider leaving this rule INERT to avoid overfitting.\n\n"
        
        # Threshold options
        report += "#### Option A: CONSERVATIVE (zero FP on GOOD)\n\n"
        if analysis["conservative_tau"] is not None:
            report += f"- **τ = {analysis['conservative_tau']:.4f}**\n"
            report += f"- Catches {analysis['conservative_tp']}/{bad_count} BAD cases (TP rate: {analysis['conservative_tp']/bad_count*100:.0f}%)\n"
            report += f"- Trips {analysis['conservative_fp']}/{good_count} GOOD cases (FP rate: {analysis['conservative_fp']/good_count*100:.0f}%)\n"
        else:
            report += "- Not computable\n"
        report += "\n"
        
        report += "#### Option B: BALANCED (best separation)\n\n"
        if analysis["balanced_tau"] is not None:
            report += f"- **τ = {analysis['balanced_tau']:.4f}**\n"
            report += f"- Catches {analysis['balanced_tp']}/{bad_count} BAD cases (TP rate: {analysis['balanced_tp']/bad_count*100:.0f}%)\n"
            report += f"- Trips {analysis['balanced_fp']}/{good_count} GOOD cases (FP rate: {analysis['balanced_fp']/good_count*100:.0f}%)\n"
            report += f"- Separation: {analysis['balanced_tp'] - analysis['balanced_fp']} (TP - FP)\n"
        else:
            report += "- Not computable\n"
        report += "\n"
    
    report += """---

## Recommended Operating Point

Based on the above analysis, I recommend:

"""
    
    # Make recommendations
    for signal_name in ["top1_ce_score", "ce_confidence", "top1_top2_margin"]:
        analysis = threshold_analyses[signal_name]
        if analysis.get("overlap_warning") in ["No computable values", "No GOOD cases with this signal"]:
            report += f"- **{signal_name}**: INERT (signal not available)\n"
        elif analysis.get("overlap_warning") and "overlap" in analysis["overlap_warning"]:
            report += f"- **{signal_name}**: INERT (ranges fully overlap at n=17; avoid overfitting)\n"
        else:
            # Pick based on FP rate of balanced vs conservative
            if analysis["balanced_fp"] == 0 and analysis["balanced_tau"] is not None:
                report += f"- **{signal_name}**: BALANCED τ={analysis['balanced_tau']:.4f} (zero FP, better TP than conservative)\n"
            elif analysis["conservative_tp"] >= analysis["balanced_tp"] * 0.8:
                report += f"- **{signal_name}**: CONSERVATIVE τ={analysis['conservative_tau']:.4f} (high precision, acceptable TP)\n"
            else:
                report += f"- **{signal_name}**: BALANCED τ={analysis['balanced_tau']:.4f} (better TP, acceptable FP)\n"
    
    report += "\n**Final decision**: Defer to team-lead for operating point selection.\n\n"
    
    report += """---

## Next Steps

1. Team-lead reviews this report and picks the operating point per signal
2. Builder wires chosen τ values into `omd_retrieval_grade.py` (TAU_* constants)
3. Builder updates goldens (`slice-c-grade-goldens.json`) + threshold assertion
4. Builder updates reason strings to embed chosen threshold literals

**DO NOT proceed to wiring thresholds until team-lead approves the operating point.**

"""
    
    return report


async def main():
    """Main calibration script."""
    import time
    
    print("=" * 80)
    print("SLICE C THRESHOLD CALIBRATION")
    print("=" * 80)
    print()
    
    # Setup container
    container = Container()
    
    # Load gold relations from xlsx
    print("Loading gold relations from xlsx...")
    gold_xlsx_by_id = load_gold_relations()
    print(f"  Loaded {len(gold_xlsx_by_id)} gold sets from xlsx\n")
    
    # Check for partial results (resume support)
    results = []
    completed_ids = set()
    if SIGNALS_PARTIAL.exists():
        try:
            partial_data = json.loads(SIGNALS_PARTIAL.read_text())
            results = partial_data
            completed_ids = {r["test_id"] for r in results}
            print(f"📂 Found partial results: {len(completed_ids)} cases already completed")
            print(f"   Resuming from case {len(completed_ids) + 1}...\n")
        except Exception as e:
            print(f"⚠️  Could not load partial results ({e}), starting fresh\n")
            results = []
            completed_ids = set()
    
    # Capture signals for all 18 cases
    remaining = [tid for tid in FIXED_18_TEST_IDS if tid not in completed_ids]
    print(f"Capturing signals for {len(remaining)} remaining cases (total: {len(FIXED_18_TEST_IDS)})...")
    print(f"  (calling omd_retrieval.retrieve(question, k=8) ONCE per case)")
    print(f"  Estimated time: ~{len(remaining) * 25} seconds (~{len(remaining) * 25 / 60:.1f} min)\n")
    
    overall_start = time.time()
    for i, test_id in enumerate(FIXED_18_TEST_IDS, 1):
        if test_id in completed_ids:
            print(f"  [{i:2}/{len(FIXED_18_TEST_IDS)}] {test_id}... ⏭️  (already completed)")
            continue
            
        print(f"  [{i:2}/{len(FIXED_18_TEST_IDS)}] {test_id}...", end="", flush=True)
        case_start = time.time()
        result = await capture_case_signals(test_id, container, gold_xlsx_by_id)
        case_elapsed = time.time() - case_start
        results.append(result)
        
        if result.get("error"):
            print(f" ❌ ERROR: {result['error']} ({case_elapsed:.1f}s)")
        else:
            print(f" ✅ recall={result['recall']:.2f} label={result['label']} ({case_elapsed:.1f}s)")
        
        # Save partial results after each case (checkpoint)
        SIGNALS_PARTIAL.write_text(json.dumps(results, indent=2))
    
    overall_elapsed = time.time() - overall_start
    print(f"\n⏱️  Total capture time: {overall_elapsed:.1f}s ({overall_elapsed/60:.1f} min)\n")
    
    # Sanity check: aggregate recall
    valid_results = [r for r in results if r["label"] != "N/A" and r["recall"] is not None]
    avg_recall = sum(r["recall"] for r in valid_results) / len(valid_results) if valid_results else 0.0
    
    print(f"Sanity check: aggregate recall = {avg_recall:.1%} ({avg_recall:.4f})")
    print(f"  Expected: {EXPECTED_RECALL_MIN:.1%} - {EXPECTED_RECALL_MAX:.1%}")
    
    if not (EXPECTED_RECALL_MIN <= avg_recall <= EXPECTED_RECALL_MAX):
        print()
        print("⚠️  SANITY CHECK FAILED: Recall diverged from baseline!")
        print("     Possible causes: pool/gold drift, retrieval changes, index changes")
        print("     STOPPING before threshold calibration.")
        print()
        print("  Dumping signals for inspection...")
        SIGNALS_OUTPUT.write_text(json.dumps(results, indent=2))
        print(f"  → {SIGNALS_OUTPUT}")
        return 1
    
    print("  ✅ Sanity check PASSED\n")
    
    # Error check: abort if >2 cases failed
    error_count = len([r for r in results if r["label"] == "ERROR"])
    if error_count > 2:
        print(f"⚠️  {error_count} cases failed (>2 threshold) — aborting")
        SIGNALS_OUTPUT.write_text(json.dumps(results, indent=2))
        print(f"  → {SIGNALS_OUTPUT}")
        return 1
    
    # Dump final signals sidecar
    print("Dumping final signals sidecar...")
    SIGNALS_OUTPUT.write_text(json.dumps(results, indent=2))
    print(f"  → {SIGNALS_OUTPUT}")
    
    # Clean up partial file
    if SIGNALS_PARTIAL.exists():
        SIGNALS_PARTIAL.unlink()
        print(f"  🧹 Removed partial checkpoint\n")
    else:
        print()
    
    # Compute thresholds for each signal
    print("Computing threshold options for each signal...")
    threshold_analyses = {
        "top1_ce_score": compute_thresholds(results, "top1_ce_score", "top1_ce_score"),
        "ce_confidence": compute_thresholds(results, "ce_confidence", "ce_confidence"),
        "top1_top2_margin": compute_thresholds(results, "top1_top2_margin", "top1_top2_margin"),
    }
    print("  ✅ Done\n")
    
    # Generate report
    print("Generating calibration report...")
    report = generate_report(results, threshold_analyses)
    REPORT_OUTPUT.write_text(report)
    print(f"  → {REPORT_OUTPUT}\n")
    
    print("=" * 80)
    print("CALIBRATION COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Review the report and pick operating points")
    print("  2. Report to team-lead")
    print("  3. Wait for team-lead approval before wiring thresholds")
    print()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
