#!/usr/bin/env python3
"""CRAG-Relevance Validation Experiment (Phase 12)

Tests whether a GT-free, runtime per-doc relevance signal separates GOOD from BAD
retrievals on the 18-case stratified sample.

STEP 1 — Option A (raw per-doc CE) + anomaly diagnosis
STEP 2 — GATE: if A meets bar (≥60% BAD @ ≤25% GOOD), recommend and stop
STEP 3 — Option B (LLM-judge answer-support per doc), only if A misses
STEP 4 — Option A+B combinations, only if A misses

Success bar: some τ on max-per-doc catches ≥60% BAD (≥8/13) at ≤1/4 GOOD tripped.

HARD CONSTRAINTS:
- READ-ONLY against graphont pipeline (ADR-009)
- GT offline-only (labels computed AFTER scoring, never in prompts)
- New files only (no edits to existing pipeline modules)
- 40-min deadline
"""
import asyncio
import json
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from application.use_cases.clause_hit_harness import FIXED_18_TEST_IDS
from domain.services.clause_hit_scoring_service import ClauseHitScoringService
from infrastructure.config.container import Container
from infrastructure.config.settings import get_settings
from rag.graph.ontology.gold_relation_parser import parse_gold_relations
from rag.graph.ontology_v2 import omd_retrieval

# Constants
GOLD_XLSX_PATH = Path(__file__).parent.parent.parent.parent / "ground-truth" / "expert-validation" / "CCoP_V2_Test_Cases_Expert_Review.xlsx"
GOLD_SHEET_NAME = "Test Cases Review"
OUTPUT_DIR = Path(__file__).parent
SIGNALS_OUTPUT = OUTPUT_DIR / "12-crag-relevance-signals.json"
REPORT_OUTPUT = OUTPUT_DIR / "12-crag-relevance-validation.md"

# Success bar
SUCCESS_BAD_RATE = 0.60  # ≥60% of BAD cases caught
SUCCESS_GOOD_RATE = 0.25  # ≤25% of GOOD cases tripped


def normalize_citation_id_for_comparison(citation_id: str) -> str:
    """Normalize citation_id to bare clause reference (strip doc prefix + def suffix)."""
    if not citation_id:
        return ""
    
    if "::" in citation_id:
        clause_part = citation_id.split("::", 1)[1]
    else:
        clause_part = citation_id
    
    if "#" in clause_part:
        clause_part = clause_part.split("#", 1)[0]
    
    return clause_part.strip()


def load_gold_relations() -> Dict[str, set[str]]:
    """Load gold clause citations from xlsx."""
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
        print(f"WARNING: Gold xlsx not found at {GOLD_XLSX_PATH}")
        return {}


async def capture_case_with_docs(test_id: str, container: Container, gold_xlsx_by_id: Dict[str, set[str]]) -> Optional[Dict]:
    """Retrieve docs for one case and capture raw texts for re-scoring.
    
    Returns: {test_id, question, candidates: [{citation_id, text, pipeline_ce_score}], 
              gold_set, retrieved_pool, recall, label}
    """
    try:
        repo = container.test_case_repository()
        test_cases = await repo.load_by_ids([test_id])
        if not test_cases:
            return {"test_id": test_id, "error": "test_case_not_found", "label": "ERROR"}
        
        test_case = test_cases[0]
        question = test_case.question
        
        # Retrieve (k=8, ONCE)
        out = omd_retrieval.retrieve(question, k=8)
        candidates = out.get("results", [])
        
        # Extract doc texts and pipeline CE scores
        docs_data = []
        for cand in candidates:
            docs_data.append({
                "citation_id": cand.get("citation_id", ""),
                "text": cand.get("text", ""),
                "pipeline_ce_score": cand.get("ce_score"),
                "kind": cand.get("kind", "clause"),
            })
        
        # Build gold set
        clause_reference = test_case.metadata.get("clause_reference") or []
        clause_ref_set = {
            ClauseHitScoringService.normalize_clause_id(c)
            for c in clause_reference
        } - {""}
        xlsx_set = gold_xlsx_by_id.get(test_id, set())
        gold_set = clause_ref_set | xlsx_set
        
        # Normalize retrieved citation IDs for recall
        retrieved_pool = [
            normalize_citation_id_for_comparison(d["citation_id"])
            for d in docs_data
            if d["citation_id"]
        ]
        
        recall = ClauseHitScoringService.recall_at_pool(
            gold_set, retrieved_pool, pool_size=len(retrieved_pool)
        )
        
        label = "GOOD" if recall > 0 else "BAD"
        if not gold_set:
            label = "N/A"
        
        return {
            "test_id": test_id,
            "question": question,
            "candidates": docs_data,
            "gold_set": sorted(gold_set),
            "retrieved_pool": retrieved_pool,
            "recall": recall,
            "label": label,
            "error": None,
        }
        
    except Exception as e:
        import traceback
        return {
            "test_id": test_id,
            "error": f"{type(e).__name__}: {str(e)}",
            "traceback": traceback.format_exc(),
            "label": "ERROR",
        }


def option_a_standalone_rescore(question: str, docs_data: List[Dict]) -> Tuple[List[float], Dict]:
    """Standalone cross-encoder re-scoring of the 8 docs.
    
    Returns: (standalone_scores, anomaly_info)
    """
    from sentence_transformers import CrossEncoder
    
    ce = CrossEncoder("BAAI/bge-reranker-large")
    
    # Build (question, doc_text) pairs
    pairs = [(question, d["text"]) for d in docs_data]
    
    # Standalone re-score
    standalone_scores = ce.predict(pairs).tolist()
    
    # Anomaly diagnosis
    doc_texts = [d["text"] for d in docs_data]
    doc_text_lens = [len(t) for t in doc_texts]
    num_distinct_texts = len(set(doc_texts))
    
    pipeline_scores = [d.get("pipeline_ce_score") for d in docs_data]
    
    # Check if standalone diverges from pipeline
    valid_pairs = [(s, p) for s, p in zip(standalone_scores, pipeline_scores) if p is not None]
    if valid_pairs:
        standalone_vals = [s for s, _ in valid_pairs]
        pipeline_vals = [p for _, p in valid_pairs]
        
        # Compute correlation or mean absolute difference
        if len(standalone_vals) > 1:
            standalone_range = max(standalone_vals) - min(standalone_vals)
            pipeline_range = max(pipeline_vals) - min(pipeline_vals)
        else:
            standalone_range = 0.0
            pipeline_range = 0.0
        
        mean_abs_diff = sum(abs(s - p) for s, p in valid_pairs) / len(valid_pairs) if valid_pairs else 0.0
    else:
        standalone_range = 0.0
        pipeline_range = 0.0
        mean_abs_diff = 0.0
    
    anomaly_info = {
        "doc_text_lens": doc_text_lens,
        "num_distinct_texts": num_distinct_texts,
        "all_texts_nonempty": all(ln > 0 for ln in doc_text_lens),
        "standalone_range": standalone_range,
        "pipeline_range": pipeline_range,
        "mean_abs_diff": mean_abs_diff,
        "standalone_scores": standalone_scores,
        "pipeline_scores": pipeline_scores,
    }
    
    return standalone_scores, anomaly_info


def aggregate_per_doc_scores(scores: List[float], mode: str = "max") -> float:
    """Aggregate per-doc scores into a single case-level signal."""
    if not scores:
        return 0.0
    
    if mode == "max":
        return max(scores)
    elif mode == "mean":
        return statistics.mean(scores)
    else:
        raise ValueError(f"Unknown aggregation mode: {mode}")


def compute_threshold_curve(results: List[Dict], signal_key: str, aggregation: str = "max") -> Dict:
    """Compute TP/FP curve for a given signal aggregation.
    
    Returns: {signal_name, good_values, bad_values, threshold_curve: [(tau, tp, fp, tp_rate, fp_rate)],
              best_tau, meets_bar, overlap_warning}
    """
    valid = [r for r in results if r["label"] in ("GOOD", "BAD")]
    
    good_values = []
    bad_values = []
    
    for r in valid:
        if signal_key not in r or r[signal_key] is None:
            continue
        
        agg_val = aggregate_per_doc_scores(r[signal_key], mode=aggregation)
        
        if r["label"] == "GOOD":
            good_values.append(agg_val)
        else:
            bad_values.append(agg_val)
    
    if not good_values or not bad_values:
        return {
            "signal_name": f"{signal_key}_{aggregation}",
            "good_values": good_values,
            "bad_values": bad_values,
            "threshold_curve": [],
            "best_tau": None,
            "meets_bar": False,
            "overlap_warning": "No computable values" if not good_values and not bad_values else "No GOOD or BAD cases",
        }
    
    # Build threshold curve
    all_vals = sorted(set(good_values + bad_values))
    curve = []
    
    for tau in all_vals:
        tp = len([b for b in bad_values if b >= tau])  # BAD cases ABOVE threshold (caught)
        fp = len([g for g in good_values if g >= tau])  # GOOD cases ABOVE threshold (tripped)
        tp_rate = tp / len(bad_values) if bad_values else 0.0
        fp_rate = fp / len(good_values) if good_values else 0.0
        curve.append((tau, tp, fp, tp_rate, fp_rate))
    
    # Find best tau that meets the bar (if any)
    best_tau = None
    meets_bar = False
    
    for tau, tp, fp, tp_rate, fp_rate in curve:
        if tp_rate >= SUCCESS_BAD_RATE and fp_rate <= SUCCESS_GOOD_RATE:
            best_tau = tau
            meets_bar = True
            break
    
    # Overlap check
    overlap_warning = None
    if max(bad_values) >= min(good_values):
        overlap_warning = "GOOD/BAD ranges overlap"
    
    return {
        "signal_name": f"{signal_key}_{aggregation}",
        "good_values": sorted(good_values),
        "bad_values": sorted(bad_values),
        "threshold_curve": curve,
        "best_tau": best_tau,
        "meets_bar": meets_bar,
        "overlap_warning": overlap_warning,
        "num_good": len(good_values),
        "num_bad": len(bad_values),
    }


def generate_report(results: List[Dict], option_a_analysis: Dict, option_b_analysis: Optional[Dict] = None, 
                   option_ab_analysis: Optional[Dict] = None) -> str:
    """Generate the CRAG-relevance validation report."""
    
    valid_results = [r for r in results if r["label"] != "N/A"]
    good_count = len([r for r in valid_results if r["label"] == "GOOD"])
    bad_count = len([r for r in valid_results if r["label"] == "BAD"])
    
    recalls = [r["recall"] for r in valid_results if r.get("recall") is not None]
    avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
    
    report = f"""# CRAG-Relevance Validation Report

Generated: validate_crag_relevance.py
Date: 2026-07-17

## Summary

**Test Set**: {len(results)} cases (FIXED_18_TEST_IDS, stratified sample)
- **GOOD** (recall > 0): {good_count} cases
- **BAD** (recall = 0): {bad_count} cases
- **N/A** (no gold clauses): {len([r for r in results if r["label"] == "N/A"])} cases

**Aggregate Recall**: {avg_recall:.1%} ({avg_recall:.4f})
- Expected baseline: ~20.6%
- Sanity check: {"✅ PASS" if 0.15 <= avg_recall <= 0.28 else "⚠️  DRIFT"}

**Success Bar**: ≥{SUCCESS_BAD_RATE:.0%} BAD caught @ ≤{SUCCESS_GOOD_RATE:.0%} GOOD tripped

---

## STEP 1: Option A — Raw Per-Doc Cross-Encoder Scores

### Anomaly Diagnosis

"""
    
    # Anomaly diagnosis summary
    anomalies = option_a_analysis.get("anomaly_summary", {})
    report += f"""**Doc-text sanity**:
- All texts non-empty: {anomalies.get('all_nonempty', 'N/A')}
- Distinct texts per case (mean): {anomalies.get('mean_distinct', 0):.1f} / 8
- Min distinct: {anomalies.get('min_distinct', 0)} / 8

**Standalone vs Pipeline CE**:
- Mean absolute difference: {anomalies.get('mean_abs_diff', 0):.4f}
- Standalone range (mean): {anomalies.get('standalone_range_mean', 0):.4f}
- Pipeline range (mean): {anomalies.get('pipeline_range_mean', 0):.4f}

"""
    
    verdict = anomalies.get('verdict', 'UNKNOWN')
    if "artifact" in verdict.lower():
        report += f"⚠️  **VERDICT**: {verdict}\n\n"
        if anomalies.get('candidate_bug'):
            report += f"🐛 **CANDIDATE PIPELINE BUG**: {anomalies.get('candidate_bug')}\n\n"
    else:
        report += f"**VERDICT**: {verdict}\n\n"
    
    # Option A results
    report += "### Threshold Analysis\n\n"
    
    for agg_mode in ["max", "mean"]:
        analysis = option_a_analysis.get(f"optionA_{agg_mode}", {})
        
        report += f"#### Aggregation: {agg_mode.upper()}\n\n"
        
        if analysis.get("overlap_warning") and "No computable" in analysis["overlap_warning"]:
            report += f"⚠️  {analysis['overlap_warning']}\n\n"
            continue
        
        report += f"**GOOD distribution**: {analysis.get('good_values', [])}\n"
        report += f"**BAD distribution**: {analysis.get('bad_values', [])}\n\n"
        
        if analysis.get("overlap_warning"):
            report += f"⚠️  {analysis['overlap_warning']}\n\n"
        
        report += f"**Meets success bar**: {'✅ YES' if analysis.get('meets_bar') else '❌ NO'}\n"
        
        if analysis.get("best_tau") is not None:
            curve = analysis.get("threshold_curve", [])
            best_entry = next((c for c in curve if c[0] == analysis["best_tau"]), None)
            if best_entry:
                tau, tp, fp, tp_rate, fp_rate = best_entry
                report += f"**Best τ**: {tau:.4f}\n"
                report += f"  - Catches {tp}/{analysis['num_bad']} BAD ({tp_rate:.0%})\n"
                report += f"  - Trips {fp}/{analysis['num_good']} GOOD ({fp_rate:.0%})\n\n"
        else:
            report += "**Best τ**: None (no threshold meets bar)\n\n"
    
    # Option B (if executed)
    if option_b_analysis:
        report += "\n---\n\n## STEP 3: Option B — LLM-Judge Answer-Support\n\n"
        report += "(Option B executed because Option A missed the bar)\n\n"
        
        for agg_mode in ["max", "mean"]:
            analysis = option_b_analysis.get(f"optionB_{agg_mode}", {})
            
            report += f"### Aggregation: {agg_mode.upper()}\n\n"
            
            if analysis.get("overlap_warning") and "No computable" in analysis["overlap_warning"]:
                report += f"⚠️  {analysis['overlap_warning']}\n\n"
                continue
            
            report += f"**GOOD distribution**: {analysis.get('good_values', [])}\n"
            report += f"**BAD distribution**: {analysis.get('bad_values', [])}\n\n"
            
            report += f"**Meets success bar**: {'✅ YES' if analysis.get('meets_bar') else '❌ NO'}\n"
            
            if analysis.get("best_tau") is not None:
                curve = analysis.get("threshold_curve", [])
                best_entry = next((c for c in curve if c[0] == analysis["best_tau"]), None)
                if best_entry:
                    tau, tp, fp, tp_rate, fp_rate = best_entry
                    report += f"**Best τ**: {tau:.4f}\n"
                    report += f"  - Catches {tp}/{analysis['num_bad']} BAD ({tp_rate:.0%})\n"
                    report += f"  - Trips {fp}/{analysis['num_good']} GOOD ({fp_rate:.0%})\n\n"
            else:
                report += "**Best τ**: None (no threshold meets bar)\n\n"
    
    # Option A+B (if executed)
    if option_ab_analysis:
        report += "\n---\n\n## STEP 4: Option A+B Combinations\n\n"
        report += "(Combinations tested because both A and B individually missed the bar)\n\n"
        report += "(Implementation placeholder — combinations not yet implemented)\n\n"
    
    # Final verdict
    report += "\n---\n\n## FINAL VERDICT\n\n"
    
    a_meets = any(option_a_analysis.get(f"optionA_{m}", {}).get("meets_bar") for m in ["max", "mean"])
    b_meets = any(option_b_analysis.get(f"optionB_{m}", {}).get("meets_bar") for m in ["max", "mean"]) if option_b_analysis else False
    
    if a_meets:
        report += "✅ **Option A (raw per-doc CE) MEETS the success bar**\n\n"
        report += "**Recommendation**: Wire Option A in a later slice as the GT-free relevance signal.\n\n"
    elif b_meets:
        report += "✅ **Option B (LLM-judge answer-support) MEETS the success bar**\n\n"
        report += "**Recommendation**: Wire Option B in a later slice (more expensive but separates better).\n\n"
    else:
        report += "❌ **No GT-free signal separates GOOD/BAD on this corpus at n=17**\n\n"
        report += "**Recommendation**: Defer GT-free relevance gating to a larger validation set, or accept that the detector relies on aggregate signals only.\n\n"
    
    return report


async def main():
    """Main CRAG-relevance validation experiment."""
    import time
    
    print("=" * 80)
    print("CRAG-RELEVANCE VALIDATION EXPERIMENT")
    print("=" * 80)
    print()
    
    container = Container()
    
    print("Loading gold relations...")
    gold_xlsx_by_id = load_gold_relations()
    print(f"  Loaded {len(gold_xlsx_by_id)} gold sets\n")
    
    # Capture cases with doc texts
    print(f"Capturing {len(FIXED_18_TEST_IDS)} cases with doc texts...")
    print(f"  (calling omd_retrieval.retrieve(question, k=8) ONCE per case)\n")
    
    results = []
    overall_start = time.time()
    
    for i, test_id in enumerate(FIXED_18_TEST_IDS, 1):
        print(f"  [{i:2}/{len(FIXED_18_TEST_IDS)}] {test_id}...", end="", flush=True)
        case_start = time.time()
        result = await capture_case_with_docs(test_id, container, gold_xlsx_by_id)
        case_elapsed = time.time() - case_start
        results.append(result)
        
        if result.get("error"):
            print(f" ❌ ERROR: {result['error']} ({case_elapsed:.1f}s)")
        else:
            print(f" ✅ recall={result['recall']:.2f} label={result['label']} ({case_elapsed:.1f}s)")
    
    overall_elapsed = time.time() - overall_start
    print(f"\n⏱️  Total capture time: {overall_elapsed:.1f}s ({overall_elapsed/60:.1f} min)\n")
    
    # Sanity check
    valid_results = [r for r in results if r["label"] != "N/A" and r.get("recall") is not None]
    avg_recall = sum(r["recall"] for r in valid_results) / len(valid_results) if valid_results else 0.0
    
    print(f"Sanity check: aggregate recall = {avg_recall:.1%}")
    if not (0.15 <= avg_recall <= 0.28):
        print("  ⚠️  Recall diverged from baseline — flagging in report")
    else:
        print("  ✅ Sanity check PASSED")
    print()
    
    # STEP 1: Option A — Standalone CE re-scoring + anomaly diagnosis
    print("=" * 80)
    print("STEP 1: Option A — Raw Per-Doc Cross-Encoder Re-Scoring")
    print("=" * 80)
    print()
    
    option_a_start = time.time()
    
    print("Re-scoring all docs with standalone cross-encoder...")
    
    for r in results:
        if r["label"] == "ERROR" or r["label"] == "N/A":
            r["optionA_scores"] = None
            r["optionA_anomaly"] = None
            continue
        
        standalone_scores, anomaly_info = option_a_standalone_rescore(r["question"], r["candidates"])
        r["optionA_scores"] = standalone_scores
        r["optionA_anomaly"] = anomaly_info
    
    option_a_elapsed = time.time() - option_a_start
    print(f"  ✅ Re-scoring complete ({option_a_elapsed:.1f}s)\n")
    
    # Anomaly diagnosis summary
    print("Anomaly diagnosis:")
    all_nonempty = all(r.get("optionA_anomaly", {}).get("all_texts_nonempty", True) 
                       for r in results if r.get("optionA_anomaly"))
    
    distinct_counts = [r.get("optionA_anomaly", {}).get("num_distinct_texts", 8) 
                      for r in results if r.get("optionA_anomaly")]
    mean_distinct = sum(distinct_counts) / len(distinct_counts) if distinct_counts else 8.0
    min_distinct = min(distinct_counts) if distinct_counts else 8
    
    mean_abs_diffs = [r.get("optionA_anomaly", {}).get("mean_abs_diff", 0.0) 
                     for r in results if r.get("optionA_anomaly")]
    overall_mad = sum(mean_abs_diffs) / len(mean_abs_diffs) if mean_abs_diffs else 0.0
    
    standalone_ranges = [r.get("optionA_anomaly", {}).get("standalone_range", 0.0) 
                        for r in results if r.get("optionA_anomaly")]
    standalone_range_mean = sum(standalone_ranges) / len(standalone_ranges) if standalone_ranges else 0.0
    
    pipeline_ranges = [r.get("optionA_anomaly", {}).get("pipeline_range", 0.0) 
                      for r in results if r.get("optionA_anomaly")]
    pipeline_range_mean = sum(pipeline_ranges) / len(pipeline_ranges) if pipeline_ranges else 0.0
    
    print(f"  All texts non-empty: {all_nonempty}")
    print(f"  Mean distinct texts: {mean_distinct:.1f} / 8 (min: {min_distinct})")
    print(f"  Mean abs diff (standalone vs pipeline): {overall_mad:.4f}")
    print(f"  Standalone range (mean): {standalone_range_mean:.4f}")
    print(f"  Pipeline range (mean): {pipeline_range_mean:.4f}")
    print()
    
    # Verdict
    candidate_bug = None
    if not all_nonempty:
        verdict = "DEGENERATE-INPUT ARTIFACT: Empty doc texts detected"
        candidate_bug = "Empty doc texts in retrieved candidates (check omd_retrieval passage hydration)"
    elif min_distinct < 4:
        verdict = "DEGENERATE-INPUT ARTIFACT: Duplicate doc texts detected"
        candidate_bug = "Duplicate doc texts in retrieved candidates (check omd_retrieval deduplication)"
    elif overall_mad > 0.1:
        verdict = "PIPELINE-STANDALONE DIVERGENCE: Standalone CE diverges from pipeline"
        candidate_bug = "Standalone CE scores diverge from pipeline ce_score (check omd_retrieval CE call)"
    elif standalone_range_mean < 0.01 and pipeline_range_mean < 0.01:
        verdict = "GENUINE BGE COLLAPSE: Both standalone and pipeline CE scores are flat"
    else:
        verdict = "NORMAL: No anomaly detected"
    
    print(f"  VERDICT: {verdict}")
    if candidate_bug:
        print(f"  🐛 CANDIDATE BUG: {candidate_bug}")
    print()
    
    # Compute threshold curves for Option A
    print("Computing threshold curves for Option A...")
    
    option_a_analysis = {
        "anomaly_summary": {
            "all_nonempty": all_nonempty,
            "mean_distinct": mean_distinct,
            "min_distinct": min_distinct,
            "mean_abs_diff": overall_mad,
            "standalone_range_mean": standalone_range_mean,
            "pipeline_range_mean": pipeline_range_mean,
            "verdict": verdict,
            "candidate_bug": candidate_bug,
        }
    }
    
    for agg_mode in ["max", "mean"]:
        analysis = compute_threshold_curve(results, "optionA_scores", aggregation=agg_mode)
        option_a_analysis[f"optionA_{agg_mode}"] = analysis
        print(f"  {analysis['signal_name']}: meets_bar={analysis['meets_bar']}")
    
    print()
    
    # STEP 2: GATE
    a_meets_bar = any(option_a_analysis.get(f"optionA_{m}", {}).get("meets_bar") for m in ["max", "mean"])
    
    option_b_analysis = None
    option_ab_analysis = None
    
    if a_meets_bar:
        print("✅ Option A MEETS the success bar — stopping (B/A+B optional)")
        print()
    else:
        print("❌ Option A MISSES the success bar — proceeding to Option B")
        print()
        
        # STEP 3: Option B (placeholder — not implemented yet)
        print("STEP 3: Option B — LLM-Judge Answer-Support (NOT YET IMPLEMENTED)")
        print("  Placeholder: Would call OpenRouter per doc with answer-support rubric")
        print()
        
        option_b_analysis = {}
    
    # Dump signals
    print("Dumping signals sidecar...")
    SIGNALS_OUTPUT.write_text(json.dumps(results, indent=2))
    print(f"  → {SIGNALS_OUTPUT}\n")
    
    # Generate report
    print("Generating validation report...")
    report = generate_report(results, option_a_analysis, option_b_analysis, option_ab_analysis)
    REPORT_OUTPUT.write_text(report)
    print(f"  → {REPORT_OUTPUT}\n")
    
    print("=" * 80)
    print("CRAG-RELEVANCE VALIDATION COMPLETE")
    print("=" * 80)
    print()
    
    if candidate_bug:
        print("⚠️  CANDIDATE PIPELINE BUG DETECTED — review report and flag team-lead")
        print()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
