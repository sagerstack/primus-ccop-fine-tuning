#!/usr/bin/env python3
"""
V2 Ground Truth Schema Validator

Validates JSONL test case files against test-case-v2.schema.json.
Runs both JSON Schema validation and business rule checks.

Usage:
    python validate.py                          # Validate all files in ../test-suite/
    python validate.py --file ../test-suite/b03_conditional_compliance_reasoning.jsonl
    python validate.py --strict                 # Fail on warnings too
"""

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError


def load_schema() -> dict:
    schema_path = Path(__file__).parent / "test-case-v2.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_business_rules(test_case: dict, warnings: list[str], errors: list[str]) -> None:
    """Business rules beyond what JSON Schema can enforce."""
    test_id = test_case.get("test_id", "UNKNOWN")
    benchmark_id = test_case.get("benchmark_id", "")

    # Rule: test_id prefix must match benchmark_id
    if not test_id.startswith(f"{benchmark_id}-"):
        errors.append(f"{test_id}: test_id prefix does not match benchmark_id '{benchmark_id}'")

    # Rule: reasoning benchmarks need reasoning_chain
    rule_based_benchmarks = {"B1", "B2", "B4", "B21"}
    ground_truth = test_case.get("ground_truth", {})
    if benchmark_id not in rule_based_benchmarks:
        if not ground_truth.get("reasoning_chain"):
            warnings.append(f"{test_id}: LLM-judge benchmark missing reasoning_chain")
        if not ground_truth.get("acceptable_variations"):
            warnings.append(f"{test_id}: LLM-judge benchmark missing acceptable_variations")

    # Rule: rule-based benchmarks need expected_label
    if benchmark_id in rule_based_benchmarks:
        if not ground_truth.get("expected_label"):
            errors.append(f"{test_id}: rule-based benchmark missing expected_label")

    # Rule: minimum 2 critical-tier key_facts for reasoning benchmarks
    key_facts = ground_truth.get("key_facts", [])
    critical_count = sum(1 for kf in key_facts if kf.get("tier") == "critical")
    if benchmark_id not in rule_based_benchmarks and critical_count < 2:
        warnings.append(
            f"{test_id}: reasoning benchmark has {critical_count} critical key_facts (recommend >= 2)"
        )

    # Rule: forbidden_claims should not be empty
    fail_conditions = test_case.get("fail_conditions", {})
    if not fail_conditions.get("forbidden_claims"):
        warnings.append(f"{test_id}: no forbidden_claims defined")


def validate_file(filepath: Path, schema: dict, strict: bool = False) -> tuple[int, int, int]:
    """Validate a single JSONL file. Returns (valid_count, warning_count, error_count)."""
    validator = Draft202012Validator(schema)
    valid_count = 0
    warning_count = 0
    error_count = 0
    seen_ids: set[str] = set()

    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                test_case = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"  ERROR line {line_num}: Invalid JSON — {e}")
                error_count += 1
                continue

            test_id = test_case.get("test_id", f"line-{line_num}")

            # Duplicate ID check
            if test_id in seen_ids:
                print(f"  ERROR {test_id}: Duplicate test_id")
                error_count += 1
            seen_ids.add(test_id)

            # JSON Schema validation
            schema_errors = list(validator.iter_errors(test_case))
            if schema_errors:
                for err in schema_errors:
                    path = ".".join(str(p) for p in err.absolute_path) or "(root)"
                    print(f"  ERROR {test_id} [{path}]: {err.message}")
                error_count += len(schema_errors)
                continue

            # Business rule validation
            warnings: list[str] = []
            biz_errors: list[str] = []
            validate_business_rules(test_case, warnings, biz_errors)

            for w in warnings:
                print(f"  WARN  {w}")
                warning_count += 1

            for e in biz_errors:
                print(f"  ERROR {e}")
                error_count += 1

            if not schema_errors and not biz_errors:
                valid_count += 1

    return valid_count, warning_count, error_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate v2 ground truth test cases")
    parser.add_argument("--file", type=Path, help="Validate a single JSONL file")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    schema = load_schema()
    test_suite_dir = Path(__file__).parent.parent / "test-suite"

    if args.file:
        files = [args.file]
    else:
        files = sorted(test_suite_dir.glob("b*.jsonl"))
        if not files:
            print(f"No JSONL files found in {test_suite_dir}")
            sys.exit(1)

    total_valid = 0
    total_warnings = 0
    total_errors = 0

    for filepath in files:
        print(f"\n--- {filepath.name} ---")
        valid, warnings, errors = validate_file(filepath, schema, args.strict)
        total_valid += valid
        total_warnings += warnings
        total_errors += errors
        print(f"  Result: {valid} valid, {warnings} warnings, {errors} errors")

    print(f"\n=== TOTAL: {total_valid} valid, {total_warnings} warnings, {total_errors} errors ===")

    if total_errors > 0 or (args.strict and total_warnings > 0):
        sys.exit(1)


if __name__ == "__main__":
    main()
