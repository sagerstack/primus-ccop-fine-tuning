#!/usr/bin/env python3
"""Per-Clause CE Data Capture (Phase 12, Step 1 of relevance-filter work)

Captures per-clause CE scores + text + is_gold for each of the 8 retrieved clauses
per test case. DATA CAPTURE ONLY — no filtering logic, no analysis.

For each case, records:
- Case-level: test_id, question, gold_set, recall, label
- Clause-level (8 per case): rank, citation_id, ce_score, text, text_len, is_gold

Output: 12-per-clause-ce-data.json (incremental write after each case)
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path (same as calibrate_slice_c_thresholds.py)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from application.use_cases.clause_hit_harness import FIXED_18_TEST_IDS
from domain.services.clause_hit_scoring_service import ClauseHitScoringService
from infrastructure.config.container import Container
from rag.graph.ontology.gold_relation_parser import parse_gold_relations
from rag.graph.ontology_v2 import omd_retrieval


def normalize_citation_id_for_comparison(citation_id: str) -> str:
    """Normalize citation_id to bare clause reference for gold set comparison.
    
    (Copied from calibrate_slice_c_thresholds.py for byte-identical normalization)
    """
    if not citation_id:
        return ""
    
    if "::" in citation_id:
        clause_part = citation_id.split("::", 1)[1]
    else:
        clause_part = citation_id
    
    if "#" in clause_part:
        clause_part = clause_part.split("#", 1)[0]
    
    return clause_part.strip()


# Constants (same paths as calibrate script)
GOLD_XLSX_PATH = Path(__file__).parent.parent.parent.parent / "ground-truth" / "expert-validation" / "CCoP_V2_Test_Cases_Expert_Review.xlsx"
GOLD_SHEET_NAME = "Test Cases Review"
OUTPUT_DIR = Path(__file__).parent
OUTPUT_FILE = OUTPUT_DIR / "12-per-clause-ce-data.json"


def load_gold_relations() -> Dict[str, set[str]]:
    """Load gold clause citations from xlsx (same as calibrate script)."""
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


async def capture_case_per_clause(test_id: str, container: Container, gold_xlsx_by_id: Dict[str, set[str]]) -> Optional[Dict]:
    """Capture per-clause CE data for one test case.
    
    Returns: {test_id, question, gold_set, recall, label, clauses: [{rank, citation_id, ce_score, text, text_len, is_gold}, ...]}
    """
    try:
        # Load test case (same as calibrate)
        repo = container.test_case_repository()
        test_cases = await repo.load_by_ids([test_id])
        if not test_cases:
            return None
        
        test_case = test_cases[0]
        question = test_case.question
        
        # Build gold set (same as calibrate: clause_reference ∪ xlsx citations)
        clause_reference = test_case.metadata.get("clause_reference") or []
        clause_ref_set = {
            ClauseHitScoringService.normalize_clause_id(c)
            for c in clause_reference
        } - {""}
        
        xlsx_set = gold_xlsx_by_id.get(test_id, set())
        gold_set = clause_ref_set | xlsx_set
        
        # Retrieve k=8
        out = omd_retrieval.retrieve(question, k=8)
        candidates = out.get("results", [])
        
        # Capture per-clause data
        clauses = []
        for rank, cand in enumerate(candidates[:8]):
            citation_id = cand.get("citation_id", "")
            normalized_cid = normalize_citation_id_for_comparison(citation_id)
            
            clause_data = {
                "rank": rank,
                "citation_id": citation_id,
                "ce_score": cand.get("ce_score"),
                "text": cand.get("text", ""),
                "text_len": len(cand.get("text", "")),
                "is_gold": normalized_cid in gold_set if normalized_cid else False,
            }
            clauses.append(clause_data)
        
        # Compute recall (same as calibrate)
        retrieved_pool = [
            normalize_citation_id_for_comparison(c.get("citation_id"))
            for c in candidates
            if c.get("citation_id")
        ]
        
        recall = ClauseHitScoringService.recall_at_pool(
            gold_set, retrieved_pool, pool_size=len(retrieved_pool)
        )
        
        # Label (same as calibrate)
        label = "GOOD" if recall > 0 else "BAD"
        if not gold_set:
            label = "N/A"
        
        return {
            "test_id": test_id,
            "question": question,
            "gold_set": sorted(gold_set),
            "recall": recall,
            "label": label,
            "clauses": clauses,
        }
        
    except Exception as e:
        import traceback
        print(f"ERROR on {test_id}: {e}")
        traceback.print_exc()
        return None


async def main():
    """Main capture script."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-ids", type=str, help="Comma-separated test IDs (default: all FIXED_18)")
    args = parser.parse_args()
    
    # Parse test IDs
    if args.test_ids:
        test_ids = [tid.strip() for tid in args.test_ids.split(",")]
    else:
        test_ids = list(FIXED_18_TEST_IDS)
    
    print(f"Capturing per-clause CE data for {len(test_ids)} cases...")
    print()
    
    container = Container()
    gold_xlsx_by_id = load_gold_relations()
    
    # Load existing data if resuming
    results = []
    if OUTPUT_FILE.exists():
        try:
            results = json.loads(OUTPUT_FILE.read_text())
            completed_ids = {r["test_id"] for r in results}
            print(f"Found existing data: {len(completed_ids)} cases")
            # Filter out already-completed
            test_ids = [tid for tid in test_ids if tid not in completed_ids]
            print(f"Resuming: {len(test_ids)} remaining")
            print()
        except:
            results = []
    
    # Process cases
    for i, test_id in enumerate(test_ids, 1):
        print(f"[{i}/{len(test_ids)}] {test_id}...", end=" ", flush=True)
        
        case_data = await capture_case_per_clause(test_id, container, gold_xlsx_by_id)
        
        if case_data is None:
            print("ERROR (skipped)")
            continue
        
        results.append(case_data)
        
        # Compute gold_in_pool count and CE range
        gold_in_pool = sum(1 for c in case_data["clauses"] if c["is_gold"])
        ce_scores = [c["ce_score"] for c in case_data["clauses"] if c["ce_score"] is not None]
        ce_min = min(ce_scores) if ce_scores else None
        ce_max = max(ce_scores) if ce_scores else None
        
        # Print summary line
        print(f"label={case_data['label']} recall={case_data['recall']:.2f} "
              f"gold_in_pool={gold_in_pool} ce_range=[{ce_min:.6f}, {ce_max:.6f}]")
        
        # Write incrementally (keep partial data on crash)
        OUTPUT_FILE.write_text(json.dumps(results, indent=2))
    
    print()
    print(f"Complete! Wrote {len(results)} cases to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
