#!/usr/bin/env python3
"""
Measure recall headroom: recall@8 vs recall@20 on the 18-case validation set.

Shows how many gold clauses that MISS top-8 would be RECOVERED by widening to k=20.
"""
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.config.settings import Settings
from infrastructure.config.container import Container
from rag.graph.ontology_v2 import omd_retrieval

# 18-case stratified validation sample (bdc4927d hash)
TEST_IDS = [
    "B01-001", "B02-001", "B03-001", "B04-001", "B05-001", "B06-001",
    "B07-001", "B08-001", "B09-001", "B10-001", "B12-001", "B13-001",
    "B14-001", "B18-001", "B21-001", "B22-001", "B23-001", "B24-001",
]

def normalize_clause_id(clause_id: str) -> str:
    """Normalize clause ID to canonical format."""
    if not clause_id:
        return clause_id
    
    # Strip leading "CCoP 2.0::" or "CCoP 2.0:" prefix
    for prefix in ["CCoP 2.0::", "CCoP 2.0:"]:
        if clause_id.startswith(prefix):
            clause_id = clause_id[len(prefix):]
    
    # Extract just the clause number (before any description)
    if " " in clause_id:
        clause_id = clause_id.split(" ")[0]
    if "(" in clause_id:
        clause_id = clause_id.split("(")[0]
    
    return clause_id.strip()

def main():
    settings = Settings()
    
    # Load test suite
    test_suite_dir = Path(settings.test_cases_dir)
    
    results = []
    
    print("Measuring recall@8 vs recall@20 headroom...")
    print()
    
    for test_id in TEST_IDS:
        # Load test case
        benchmark_id = test_id.split("-")[0]
        test_file = test_suite_dir / f"b{benchmark_id[1:].zfill(2)}_*.jsonl"
        test_files = list(test_suite_dir.glob(test_file.name))
        
        if not test_files:
            print(f"❌ {test_id}: Test file not found")
            continue
        
        # Find the specific test case
        test_case_data = None
        for tf in test_files:
            with open(tf) as f:
                for line in f:
                    tc = json.loads(line)
                    if tc["test_id"] == test_id:
                        test_case_data = tc
                        break
            if test_case_data:
                break
        
        if not test_case_data:
            print(f"❌ {test_id}: Test case not found")
            continue
        
        question = test_case_data["input"]["question"]
        
        # Build gold set (normalized)
        gold_set = set()
        
        # From clause_reference (in ground_truth)
        gt = test_case_data.get("ground_truth", {})
        clause_ref = gt.get("clause_reference", "")
        if clause_ref:
            gold_set.add(normalize_clause_id(clause_ref))
        
        # From key_facts.source
        key_facts = gt.get("key_facts", [])
        for kf in key_facts:
            source = kf.get("source", "")
            if source and source.startswith("CCoP 2.0"):
                normalized = normalize_clause_id(source)
                if normalized:
                    gold_set.add(normalized)
        
        # Retrieve @8
        result8 = omd_retrieval.retrieve(question, k=8)
        pool8 = result8["results"]
        retrieved8 = {normalize_clause_id(c["citation_id"]) for c in pool8}
        
        # Retrieve @20
        result20 = omd_retrieval.retrieve(question, k=20)
        pool20 = result20["results"]
        retrieved20 = {normalize_clause_id(c["citation_id"]) for c in pool20}
        
        # Compute recall
        hits8 = gold_set & retrieved8
        hits20 = gold_set & retrieved20
        
        recall8 = len(hits8) / len(gold_set) if gold_set else 0.0
        recall20 = len(hits20) / len(gold_set) if gold_set else 0.0
        
        # Find recoverable golds (in top-20 but not top-8)
        recoverable = hits20 - hits8
        
        # Get ranks of recoverable golds
        recoverable_with_ranks = []
        for i, chunk in enumerate(pool20, start=1):
            cid_normalized = normalize_clause_id(chunk["citation_id"])
            if cid_normalized in recoverable:
                recoverable_with_ranks.append((cid_normalized, i))
        
        results.append({
            "test_id": test_id,
            "gold_set": sorted(gold_set),
            "recall8": recall8,
            "recall20": recall20,
            "recoverable": sorted([(cid, rank) for cid, rank in recoverable_with_ranks], key=lambda x: x[1])
        })
        
        print(f"{test_id}: R@8={recall8:.2f} R@20={recall20:.2f} recoverable={len(recoverable)}")
    
    print()
    print("=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)
    print()
    
    for r in results:
        print(f"### {r['test_id']}")
        print(f"Gold Set ({len(r['gold_set'])}): {r['gold_set']}")
        print(f"Recall@8: {r['recall8']:.2%} ({r['recall8'] * len(r['gold_set']):.0f}/{len(r['gold_set'])})")
        print(f"Recall@20: {r['recall20']:.2%} ({r['recall20'] * len(r['gold_set']):.0f}/{len(r['gold_set'])})")
        
        if r['recoverable']:
            print(f"Recoverable at rank 9-20 ({len(r['recoverable'])}):")
            for cid, rank in r['recoverable']:
                print(f"  - {cid} @ rank {rank}")
        else:
            print("Recoverable at rank 9-20: none")
        print()
    
    print("=" * 80)
    print("AGGREGATES")
    print("=" * 80)
    
    mean_recall8 = sum(r['recall8'] for r in results) / len(results)
    mean_recall20 = sum(r['recall20'] for r in results) / len(results)
    cases_with_recoverable = sum(1 for r in results if r['recoverable'])
    total_recoverable = sum(len(r['recoverable']) for r in results)
    
    print(f"Mean Recall@8: {mean_recall8:.2%}")
    print(f"Mean Recall@20: {mean_recall20:.2%}")
    print(f"Headroom gain: +{(mean_recall20 - mean_recall8):.2%}")
    print(f"Cases with ≥1 recoverable gold: {cases_with_recoverable}/{len(results)} ({cases_with_recoverable/len(results):.0%})")
    print(f"Total recoverable golds across all cases: {total_recoverable}")
    
    # Save to JSON
    output_file = Path(__file__).parent / "12-recall-headroom.json"
    with open(output_file, "w") as f:
        json.dump({
            "summary": {
                "mean_recall8": mean_recall8,
                "mean_recall20": mean_recall20,
                "headroom_gain": mean_recall20 - mean_recall8,
                "cases_with_recoverable": cases_with_recoverable,
                "total_recoverable": total_recoverable,
            },
            "per_case": results
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
