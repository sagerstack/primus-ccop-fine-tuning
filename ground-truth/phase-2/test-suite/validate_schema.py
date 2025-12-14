#!/usr/bin/env python3
"""
Validate updated test case schema against scoring methodology requirements.
"""

import json
import glob
from collections import defaultdict
from pathlib import Path

REQUIRED_CATEGORIES = {"classification", "reasoning", "safety"}

BENCHMARK_CATEGORY_MAP = {
    "B1": "classification", "B2": "classification", "B3": "reasoning", "B4": "classification",
    "B5": "classification", "B6": "reasoning", "B7": "reasoning", "B8": "reasoning",
    "B9": "reasoning", "B10": "reasoning", "B11": "reasoning", "B12": "reasoning",
    "B13": "reasoning", "B14": "reasoning", "B15": "reasoning", "B16": "reasoning",
    "B17": "reasoning", "B18": "reasoning", "B19": "reasoning", "B20": "safety", "B21": "safety"
}

def validate_test_case(case: dict, benchmark_id: str, line_num: int) -> list:
    """Validate a single test case."""
    issues = []

    # Universal field checks
    if "benchmark_category" not in case:
        issues.append(f"Missing 'benchmark_category'")
    elif case["benchmark_category"] not in REQUIRED_CATEGORIES:
        issues.append(f"Invalid benchmark_category: {case['benchmark_category']}")
    elif case["benchmark_category"] != BENCHMARK_CATEGORY_MAP.get(benchmark_id):
        issues.append(f"Wrong category: expected {BENCHMARK_CATEGORY_MAP.get(benchmark_id)}, got {case['benchmark_category']}")

    if "key_facts" not in case:
        issues.append(f"Missing 'key_facts'")
    elif not isinstance(case["key_facts"], list):
        issues.append(f"'key_facts' must be a list")
    elif len(case["key_facts"]) == 0:
        issues.append(f"'key_facts' is empty")

    # Category-specific checks
    category = case.get("benchmark_category")

    if category in ["classification", "safety"]:
        if "expected_label" not in case:
            issues.append(f"{category} benchmark missing 'expected_label'")

    if category == "safety":
        if "safety_checks" not in case:
            issues.append(f"Safety benchmark missing 'safety_checks'")

    if category == "reasoning":
        if "reasoning_dimensions" not in case:
            issues.append(f"Reasoning benchmark missing 'reasoning_dimensions'")

    # Check for old fields that should be removed
    if "correct_classification" in case:
        issues.append(f"Old field 'correct_classification' still present (should be 'expected_label')")
    if "correct_answer" in case:
        issues.append(f"Old field 'correct_answer' still present (should be 'expected_label')")
    if "hallucination_indicators" in case:
        issues.append(f"Old field 'hallucination_indicators' still present (should be 'safety_checks')")

    return issues


def validate_file(filepath: Path):
    """Validate all test cases in a file."""
    filename = filepath.name
    benchmark_id = filename.split('_')[0].upper().replace('B0', 'B')

    print(f"\n{'='*60}")
    print(f"Validating: {filename}")
    print(f"Benchmark: {benchmark_id}")
    print(f"Expected category: {BENCHMARK_CATEGORY_MAP.get(benchmark_id, 'unknown')}")
    print(f"{'='*60}")

    file_issues = []
    case_count = 0

    with open(filepath, 'r') as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                case = json.loads(line)
                case_count += 1
                test_id = case.get('test_id', f'line-{i}')

                issues = validate_test_case(case, benchmark_id, i)

                if issues:
                    print(f"  ⚠️  {test_id}:")
                    for issue in issues:
                        print(f"      - {issue}")
                    file_issues.extend(issues)
                else:
                    num_facts = len(case.get('key_facts', []))
                    category = case.get('benchmark_category', '?')
                    print(f"  ✓ {test_id}: {category}, {num_facts} facts")

            except json.JSONDecodeError as e:
                print(f"  ✗ Line {i}: Invalid JSON - {e}")
                file_issues.append(f"Line {i}: Invalid JSON")

    if not file_issues:
        print(f"\n  ✅ All {case_count} test cases valid!")
    else:
        print(f"\n  ⚠️  Found {len(file_issues)} issues in {case_count} test cases")

    return len(file_issues), case_count


def main():
    """Validate all test case files."""
    test_suite_dir = Path(__file__).parent

    print("\n" + "="*60)
    print("Test Case Schema Validation")
    print("="*60)

    stats = defaultdict(int)
    total_issues = 0
    total_cases = 0

    for jsonl_file in sorted(test_suite_dir.glob("b*.jsonl")):
        issues, cases = validate_file(jsonl_file)
        total_issues += issues
        total_cases += cases

        benchmark_id = jsonl_file.stem.split('_')[0].upper().replace('B0', 'B')
        category = BENCHMARK_CATEGORY_MAP.get(benchmark_id, 'unknown')
        stats[category] += cases

    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"\nTotal test cases validated: {total_cases}")
    print(f"Total issues found: {total_issues}")

    print(f"\nTest cases by category:")
    for category in ["classification", "reasoning", "safety"]:
        print(f"  {category:15s}: {stats[category]:3d} cases")

    if total_issues == 0:
        print(f"\n✅ ALL VALIDATIONS PASSED!")
        print(f"   Schema updates successfully applied to all {total_cases} test cases.")
    else:
        print(f"\n⚠️  VALIDATION FAILED")
        print(f"   Found {total_issues} issues across {total_cases} test cases.")
        print(f"   Review issues above and fix manually.")

    print("="*60)


if __name__ == "__main__":
    main()
