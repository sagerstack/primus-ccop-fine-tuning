#!/usr/bin/env python3
"""
Recall check: k=20 retrieval for 4 cases (B05-001, B01-001, B10-001, B04-001).
Compare recall@8 vs recall@20 to see if widening recovers GT gold clauses.
"""
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.config.settings import Settings
from rag.graph.ontology_v2 import omd_retrieval

# 4 test cases
TEST_IDS = ["B05-001", "B01-001", "B10-001", "B04-001"]

def normalize_clause_id(clause_id: str) -> str:
    """Normalize clause ID to canonical format."""
    if not clause_id:
        return clause_id
    
    # Strip leading "CCoP 2.0::" or "CCoP 2.0:" prefix
    for prefix in ["CCoP 2.0::", "CCoP 2.0:"]:
        if clause_id.startswith(prefix):
            clause_id = clause_id[len(prefix):]
    
    # Extract just the clause number (before any description, but KEEP parentheses like (b))
    if " " in clause_id:
        clause_id = clause_id.split(" ")[0]
    
    # Strip trailing punctuation like semicolons, commas
    clause_id = clause_id.rstrip(";,")
    
    return clause_id.strip()

def main():
    settings = Settings()
    
    # Load test suite
    test_suite_dir = Path(settings.test_cases_dir)
    
    results = []
    
    print("=" * 80)
    print("RECALL CHECK: k=20 retrieval for 4 cases")
    print("=" * 80)
    print()
    
    for test_id in TEST_IDS:
        print(f"Processing {test_id}...")
        
        # Load test case
        benchmark_id = test_id.split("-")[0]
        benchmark_num = benchmark_id[1:].zfill(2)
        test_files = list(test_suite_dir.glob(f"b{benchmark_num}_*.jsonl"))
        
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
        
        # From ground_truth key_facts sources
        gt = test_case_data.get("ground_truth", {})
        key_facts = gt.get("key_facts", [])
        for kf in key_facts:
            source = kf.get("source", "")
            # Format: "CCoP 2.0 X.Y.Z" or "CCoP 2.0 §X.Y.Z" or multi "...; CCoP 2.0 X.Y.Z; ..."
            # Split by semicolons first to handle multiple sources
            for src_part in source.split(";"):
                if "CCoP 2.0" in src_part:
                    # Extract clause after "CCoP 2.0"
                    parts = src_part.split("CCoP 2.0")
                    if len(parts) > 1:
                        clause_part = parts[1].strip()
                        # Remove § if present
                        clause_part = clause_part.lstrip("§").strip()
                        # Take first token (clause ID), strip trailing punctuation
                        clause_id = clause_part.split()[0] if clause_part else ""
                        clause_id = clause_id.rstrip(";,")
                        if clause_id and clause_id[0].isdigit():
                            gold_set.add(clause_id)
        
        print(f"  Gold set ({len(gold_set)}): {sorted(gold_set)}")
        
        # Retrieve @20
        print(f"  Retrieving k=20...")
        result20 = omd_retrieval.retrieve(question, k=20)
        pool20 = result20["results"]
        
        # Get citation IDs in rank order
        citation_ids_20 = [c["citation_id"] for c in pool20]
        citation_ids_20_norm = [normalize_clause_id(cid) for cid in citation_ids_20]
        
        print(f"  Retrieved {len(pool20)} chunks")
        
        # Compute recall@8 and recall@20
        retrieved8_norm = set(citation_ids_20_norm[:8])
        retrieved20_norm = set(citation_ids_20_norm)
        
        hits8 = gold_set & retrieved8_norm
        hits20 = gold_set & retrieved20_norm
        
        recall8 = len(hits8) / len(gold_set) if gold_set else 0.0
        recall20 = len(hits20) / len(gold_set) if gold_set else 0.0
        
        # Find recovered golds (in top-20 but not top-8)
        recovered = hits20 - hits8
        
        # Get ranks of recovered golds (9-20)
        recovered_with_ranks = []
        for i, cid_norm in enumerate(citation_ids_20_norm, start=1):
            if cid_norm in recovered:
                recovered_with_ranks.append((cid_norm, i))
        
        results.append({
            "test_id": test_id,
            "gold_set": sorted(gold_set),
            "citation_ids_20": citation_ids_20,
            "recall8": recall8,
            "recall20": recall20,
            "hits8": sorted(hits8),
            "hits20": sorted(hits20),
            "recovered": sorted([(cid, rank) for cid, rank in recovered_with_ranks], key=lambda x: x[1])
        })
        
        print(f"  Recall@8: {recall8:.2%}, Recall@20: {recall20:.2%}, Recovered: {len(recovered)}")
        print()
    
    print("=" * 80)
    print("RESULTS TABLE")
    print("=" * 80)
    print()
    
    for r in results:
        print(f"### {r['test_id']}")
        print(f"Gold Set ({len(r['gold_set'])}): {r['gold_set']}")
        print(f"Recall@8: {r['recall8']:.2%} ({len(r['hits8'])}/{len(r['gold_set'])})")
        print(f"Recall@20: {r['recall20']:.2%} ({len(r['hits20'])}/{len(r['gold_set'])})")
        print()
        print(f"Retrieved (top-20 in rank order):")
        for i, cid in enumerate(r['citation_ids_20'], start=1):
            cid_norm = normalize_clause_id(cid)
            in_gold = "✓ GOLD" if cid_norm in r['gold_set'] else ""
            in_8 = "(in top-8)" if i <= 8 else f"(rank {i})"
            print(f"  {i:2d}. {cid} {in_8} {in_gold}")
        print()
        
        if r['recovered']:
            print(f"Recovered at rank 9-20 ({len(r['recovered'])}):")
            for cid, rank in r['recovered']:
                print(f"  ✓ {cid} @ rank {rank}")
        else:
            print("Recovered at rank 9-20: none")
        print()
    
    # Save to JSON
    output_file = Path(__file__).parent / "12-recall-check-4cases.json"
    with open(output_file, "w") as f:
        json.dump({"per_case": results}, f, indent=2)
    
    print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()
