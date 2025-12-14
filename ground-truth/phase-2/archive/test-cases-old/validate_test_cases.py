#!/usr/bin/env python3
"""
Test Case Validation Script for CCoP 2.0 Phase 1 Baseline Evaluation

This script validates the structure, completeness, and quality of the 40 test cases
created for benchmarks B1-B6 against CCoP 2.0 standards.

Usage:
    python validate_test_cases.py

Requirements:
    - Python 3.8+
    - Standard library only (no external dependencies)
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


class TestCaseValidator:
    """Validates CCoP 2.0 test cases for Phase 1 baseline evaluation."""

    REQUIRED_FIELDS = {
        'B1': ['test_id', 'benchmark_type', 'section', 'clause_reference', 'difficulty',
               'question', 'expected_response', 'evaluation_criteria', 'metadata'],
        'B2': ['test_id', 'benchmark_type', 'section', 'clause_reference', 'difficulty',
               'question', 'expected_response', 'correct_citation', 'evaluation_criteria', 'metadata'],
        'B3': ['test_id', 'benchmark_type', 'section', 'clause_reference', 'difficulty',
               'question', 'expected_response', 'correct_answer', 'hallucination_indicators',
               'evaluation_criteria', 'metadata'],
        'B4': ['test_id', 'benchmark_type', 'section', 'clause_reference', 'difficulty',
               'question', 'expected_response', 'key_terminology', 'evaluation_criteria', 'metadata'],
        'B5': ['test_id', 'benchmark_type', 'section', 'clause_reference', 'difficulty',
               'question', 'expected_response', 'evaluation_criteria', 'metadata'],
        'B6': ['test_id', 'benchmark_type', 'section', 'clause_reference', 'difficulty',
               'question', 'expected_response', 'violations', 'evaluation_criteria', 'metadata']
    }

    VALID_DIFFICULTIES = ['low', 'medium', 'high', 'critical']
    VALID_DOMAINS = ['IT', 'OT', 'IT/OT']

    def __init__(self, test_cases_dir: str = '.'):
        """Initialize validator with test cases directory."""
        self.test_cases_dir = Path(test_cases_dir)
        self.test_cases: Dict[str, List[Dict]] = {}
        self.validation_results: Dict[str, Any] = {}

    def load_test_cases(self) -> None:
        """Load all JSONL test case files."""
        jsonl_files = {
            'B1': 'b1_ccop_interpretation_accuracy.jsonl',
            'B2': 'b2_clause_citation_accuracy.jsonl',
            'B3': 'b3_hallucination_rate.jsonl',
            'B4': 'b4_singapore_terminology.jsonl',
            'B5': 'b5_it_ot_classification.jsonl',
            'B6': 'b6_code_violation_detection.jsonl'
        }

        for benchmark, filename in jsonl_files.items():
            filepath = self.test_cases_dir / filename
            if not filepath.exists():
                print(f"❌ ERROR: File not found: {filepath}")
                continue

            test_cases = []
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        test_case = json.loads(line.strip())
                        test_cases.append(test_case)
                    except json.JSONDecodeError as e:
                        print(f"❌ ERROR: Invalid JSON in {filename} line {line_num}: {e}")

            self.test_cases[benchmark] = test_cases
            print(f"✅ Loaded {len(test_cases)} test cases from {filename}")

    def validate_structure(self) -> Dict[str, List[str]]:
        """Validate test case structure and required fields."""
        issues = defaultdict(list)

        for benchmark, cases in self.test_cases.items():
            required_fields = self.REQUIRED_FIELDS[benchmark]

            for idx, case in enumerate(cases, 1):
                test_id = case.get('test_id', f'{benchmark}-{idx:03d}')

                # Check required fields
                missing_fields = [field for field in required_fields if field not in case]
                if missing_fields:
                    issues[benchmark].append(
                        f"{test_id}: Missing required fields: {', '.join(missing_fields)}"
                    )

                # Validate difficulty
                if case.get('difficulty') not in self.VALID_DIFFICULTIES:
                    issues[benchmark].append(
                        f"{test_id}: Invalid difficulty '{case.get('difficulty')}' "
                        f"(must be one of {', '.join(self.VALID_DIFFICULTIES)})"
                    )

                # Validate domain in metadata
                domain = case.get('metadata', {}).get('domain')
                if domain and domain not in self.VALID_DOMAINS:
                    issues[benchmark].append(
                        f"{test_id}: Invalid domain '{domain}' "
                        f"(must be one of {', '.join(self.VALID_DOMAINS)})"
                    )

                # Validate test_id format
                expected_prefix = f"{benchmark}-"
                if not test_id.startswith(expected_prefix):
                    issues[benchmark].append(
                        f"{test_id}: Test ID should start with '{expected_prefix}'"
                    )

        return dict(issues)

    def generate_statistics(self) -> Dict[str, Any]:
        """Generate statistics about the test cases."""
        stats = {
            'total_count': 0,
            'by_benchmark': {},
            'by_difficulty': defaultdict(int),
            'by_domain': defaultdict(int),
            'by_section': defaultdict(int),
            'clause_coverage': set()
        }

        for benchmark, cases in self.test_cases.items():
            stats['total_count'] += len(cases)
            stats['by_benchmark'][benchmark] = len(cases)

            for case in cases:
                # Count by difficulty
                difficulty = case.get('difficulty', 'unknown')
                stats['by_difficulty'][difficulty] += 1

                # Count by domain
                domain = case.get('metadata', {}).get('domain', 'unknown')
                stats['by_domain'][domain] += 1

                # Count by section
                section = case.get('section', 'unknown')
                stats['by_section'][section] += 1

                # Track clause coverage
                clause = case.get('clause_reference')
                if clause and clause != 'N/A':
                    stats['clause_coverage'].add(clause)

        stats['clause_coverage'] = sorted(list(stats['clause_coverage']))
        stats['by_difficulty'] = dict(stats['by_difficulty'])
        stats['by_domain'] = dict(stats['by_domain'])
        stats['by_section'] = dict(sorted(stats['by_section'].items()))

        return stats

    def validate_content_quality(self) -> List[str]:
        """Validate content quality of test cases."""
        warnings = []

        for benchmark, cases in self.test_cases.items():
            for case in cases:
                test_id = case.get('test_id', 'unknown')

                # Check question length (should be substantial)
                question = case.get('question', '')
                if len(question) < 50:
                    warnings.append(
                        f"{test_id}: Question seems too short ({len(question)} chars)"
                    )

                # Check expected response length (should be detailed)
                expected = case.get('expected_response', '')
                if len(expected) < 100:
                    warnings.append(
                        f"{test_id}: Expected response seems too short ({len(expected)} chars)"
                    )

                # Check evaluation criteria structure
                eval_criteria = case.get('evaluation_criteria', {})
                if not isinstance(eval_criteria, dict):
                    warnings.append(
                        f"{test_id}: Evaluation criteria should be a dictionary"
                    )
                elif len(eval_criteria) < 2:
                    warnings.append(
                        f"{test_id}: Evaluation criteria has only {len(eval_criteria)} items"
                    )

        return warnings

    def print_report(self) -> None:
        """Print comprehensive validation report."""
        print("\n" + "="*80)
        print("CCoP 2.0 TEST CASE VALIDATION REPORT")
        print("="*80 + "\n")

        # Statistics
        stats = self.generate_statistics()
        print(f"📊 STATISTICS")
        print(f"{'─'*80}")
        print(f"Total Test Cases: {stats['total_count']}")
        print(f"\nBy Benchmark:")
        for benchmark, count in stats['by_benchmark'].items():
            print(f"  {benchmark}: {count} test cases")

        print(f"\nBy Difficulty:")
        for difficulty, count in stats['by_difficulty'].items():
            print(f"  {difficulty.title()}: {count} test cases")

        print(f"\nBy Domain:")
        for domain, count in stats['by_domain'].items():
            print(f"  {domain}: {count} test cases")

        print(f"\nClause Coverage: {len(stats['clause_coverage'])} unique clauses")

        # Structure validation
        print(f"\n🔍 STRUCTURE VALIDATION")
        print(f"{'─'*80}")
        structure_issues = self.validate_structure()
        if not structure_issues:
            print("✅ All test cases have valid structure")
        else:
            for benchmark, issues in structure_issues.items():
                print(f"\n{benchmark} Issues:")
                for issue in issues:
                    print(f"  ❌ {issue}")

        # Content quality
        print(f"\n📝 CONTENT QUALITY")
        print(f"{'─'*80}")
        quality_warnings = self.validate_content_quality()
        if not quality_warnings:
            print("✅ All test cases meet content quality standards")
        else:
            for warning in quality_warnings:
                print(f"  ⚠️  {warning}")

        # Coverage analysis
        print(f"\n📋 SECTION COVERAGE")
        print(f"{'─'*80}")
        for section, count in stats['by_section'].items():
            print(f"  {section}: {count} test cases")

        # Summary
        print(f"\n{'='*80}")
        total_issues = sum(len(issues) for issues in structure_issues.values())
        total_warnings = len(quality_warnings)

        if total_issues == 0 and total_warnings == 0:
            print("✅ VALIDATION PASSED: All test cases are valid and ready for use")
        elif total_issues == 0:
            print(f"⚠️  VALIDATION PASSED WITH WARNINGS: {total_warnings} content quality warnings")
        else:
            print(f"❌ VALIDATION FAILED: {total_issues} structure issues, {total_warnings} warnings")

        print("="*80 + "\n")

    def export_for_gemini_validation(self, output_file: str = 'test_cases_for_gemini_validation.json') -> None:
        """Export test cases in format suitable for Gemini validation."""
        all_test_cases = []

        for benchmark, cases in self.test_cases.items():
            for case in cases:
                all_test_cases.append({
                    'test_id': case['test_id'],
                    'benchmark': benchmark,
                    'question': case['question'],
                    'expected_response': case['expected_response'],
                    'clause_reference': case.get('clause_reference'),
                    'section': case.get('section')
                })

        output_path = self.test_cases_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_test_cases, f, indent=2, ensure_ascii=False)

        print(f"✅ Exported {len(all_test_cases)} test cases for Gemini validation to {output_file}")


def main():
    """Main validation workflow."""
    print("\n🚀 CCoP 2.0 Test Case Validation")
    print("─" * 80)

    # Initialize validator
    validator = TestCaseValidator()

    # Load test cases
    print("\n📂 Loading test cases...")
    validator.load_test_cases()

    # Print validation report
    validator.print_report()

    # Export for Gemini validation
    print("📤 Exporting for Gemini validation...")
    validator.export_for_gemini_validation()

    print("\n✨ Validation complete!\n")


if __name__ == '__main__':
    main()
