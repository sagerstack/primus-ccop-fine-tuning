#!/usr/bin/env python3
"""
Quick verification: Show test_id ranges and benchmark_types for all files.
"""

import json
from pathlib import Path

def verify_file(filepath):
    """Get test_id range and benchmark_type for a file."""
    filename = filepath.stem

    test_ids = []
    benchmark_types = set()

    with open(filepath, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                test_ids.append(data.get('test_id', 'N/A'))
                benchmark_types.add(data.get('benchmark_type', 'N/A'))
            except:
                pass

    return {
        'filename': filename,
        'test_ids': f"{test_ids[0]} to {test_ids[-1]}" if test_ids else "None",
        'count': len(test_ids),
        'benchmark_type': list(benchmark_types)[0] if len(benchmark_types) == 1 else f"MULTIPLE: {benchmark_types}"
    }

def main():
    test_suite_dir = Path('.')

    print(f"{'File':<45} {'Test IDs':<20} {'Count':<6} {'Benchmark Type':<40}")
    print("=" * 115)

    for jsonl_file in sorted(test_suite_dir.glob("b*.jsonl")):
        result = verify_file(jsonl_file)
        print(f"{result['filename']:<45} {result['test_ids']:<20} {result['count']:<6} {result['benchmark_type']:<40}")

if __name__ == "__main__":
    main()
