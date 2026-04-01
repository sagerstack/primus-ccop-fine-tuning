#!/usr/bin/env python3
"""
Investigate test case file corruption.
Check if test_id matches filename and benchmark_type.
"""

import json
from pathlib import Path
from collections import defaultdict

def investigate_file(filepath):
    """Investigate a single file for corruption."""
    filename = filepath.stem
    # Extract expected benchmark from filename (e.g., b04 -> B4)
    if filename.startswith('b0'):
        expected_benchmark = 'B' + filename[2:filename.find('_')]
    else:
        expected_benchmark = 'B' + filename[1:filename.find('_')]

    test_ids = []
    benchmark_types = []

    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                test_id = data.get('test_id', 'N/A')
                benchmark_type = data.get('benchmark_type', 'N/A')

                test_ids.append(test_id)
                benchmark_types.append(benchmark_type)
            except json.JSONDecodeError as e:
                print(f"  ⚠️  JSON error at line {line_num}: {e}")

    # Analyze
    unique_test_ids = set([tid.split('-')[0] for tid in test_ids if tid != 'N/A'])
    unique_benchmark_types = set(benchmark_types)

    return {
        'filename': filename,
        'expected_benchmark': expected_benchmark,
        'test_ids': test_ids,
        'unique_test_id_prefixes': unique_test_ids,
        'unique_benchmark_types': unique_benchmark_types,
        'count': len(test_ids)
    }

def main():
    test_suite_dir = Path('.')

    print("="*80)
    print("TEST CASE FILE CORRUPTION INVESTIGATION")
    print("="*80)
    print()

    all_results = []
    corrupted_files = []

    for jsonl_file in sorted(test_suite_dir.glob("b*.jsonl")):
        result = investigate_file(jsonl_file)
        all_results.append(result)

        # Check for corruption
        is_corrupted = False
        issues = []

        # Check if test_id prefixes match expected benchmark
        if result['expected_benchmark'] not in result['unique_test_id_prefixes']:
            is_corrupted = True
            issues.append(f"Expected {result['expected_benchmark']} test IDs, found: {result['unique_test_id_prefixes']}")

        # Check if there are multiple different test_id prefixes
        if len(result['unique_test_id_prefixes']) > 1:
            is_corrupted = True
            issues.append(f"Multiple test_id prefixes in single file: {result['unique_test_id_prefixes']}")

        # Check if benchmark_type is consistent
        if len(result['unique_benchmark_types']) > 1:
            is_corrupted = True
            issues.append(f"Multiple benchmark_types: {result['unique_benchmark_types']}")

        # Print results
        if is_corrupted:
            print(f"❌ CORRUPTED: {result['filename']}")
            corrupted_files.append(result)
        else:
            print(f"✅ OK: {result['filename']}")

        print(f"   Expected: {result['expected_benchmark']}")
        print(f"   Test ID prefixes found: {result['unique_test_id_prefixes']}")
        print(f"   Benchmark types found: {result['unique_benchmark_types']}")
        print(f"   Test count: {result['count']}")

        if is_corrupted:
            print(f"   ISSUES:")
            for issue in issues:
                print(f"     - {issue}")

        print()

    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total files checked: {len(all_results)}")
    print(f"Corrupted files: {len(corrupted_files)}")
    print(f"Clean files: {len(all_results) - len(corrupted_files)}")
    print()

    if corrupted_files:
        print("CORRUPTED FILES DETAIL:")
        print()
        for cf in corrupted_files:
            print(f"  {cf['filename']}:")
            print(f"    - Expected benchmark: {cf['expected_benchmark']}")
            print(f"    - Actual test IDs: {sorted(cf['test_ids'][:3])}...")
            print(f"    - Benchmark types: {cf['unique_benchmark_types']}")
            print()

if __name__ == "__main__":
    main()
