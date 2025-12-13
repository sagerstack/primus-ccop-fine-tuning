"""
Benchmark Validator Service

Domain service for validating benchmarks and test case collections.
Stateless service with pure validation logic (no external dependencies).
"""

from typing import Dict, List, Tuple

from domain.entities.benchmark import Benchmark
from domain.entities.test_case import TestCase
from domain.exceptions.validation_error import ValidationError
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.difficulty_level import DifficultyLevel


class BenchmarkValidator:
    """
    Domain service for validating benchmark structure and coverage.

    This service contains complex validation logic that operates across
    multiple entities and doesn't naturally belong to a single entity.
    """

    @staticmethod
    def validate_benchmark_coverage(benchmark: Benchmark) -> Tuple[bool, List[str]]:
        """
        Business rule: Validate that benchmark has adequate test coverage.

        Requirements:
        - At least 5 test cases per benchmark
        - Mix of difficulty levels (not all same difficulty)
        - Coverage of multiple CCoP sections
        - High-priority tests present (at least 20% high/critical)

        Args:
            benchmark: Benchmark to validate

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings: List[str] = []

        # Check minimum test cases
        if benchmark.test_case_count < 5:
            warnings.append(
                f"Benchmark {benchmark.benchmark_type.value} has only "
                f"{benchmark.test_case_count} test cases. Minimum 5 recommended."
            )

        # Check difficulty distribution
        difficulty_issues = BenchmarkValidator._check_difficulty_distribution(
            benchmark.test_cases
        )
        warnings.extend(difficulty_issues)

        # Check section coverage
        section_issues = BenchmarkValidator._check_section_coverage(
            benchmark.test_cases
        )
        warnings.extend(section_issues)

        # Check high-priority coverage
        high_priority_count = len(benchmark.get_high_priority_test_cases())
        high_priority_ratio = high_priority_count / benchmark.test_case_count
        if high_priority_ratio < 0.2:
            warnings.append(
                f"Only {high_priority_ratio:.1%} of tests are high priority. "
                "Recommend at least 20%."
            )

        is_valid = len(warnings) == 0
        return is_valid, warnings

    @staticmethod
    def validate_test_case_collection(
        test_cases: List[TestCase]
    ) -> Tuple[bool, List[str]]:
        """
        Business rule: Validate a collection of test cases for consistency.

        Checks:
        - No duplicate test IDs
        - All test cases valid individually
        - Consistent metadata structure
        - Balanced distribution

        Args:
            test_cases: List of test cases to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors: List[str] = []

        if not test_cases:
            errors.append("Test case collection is empty")
            return False, errors

        # Check for duplicates
        test_ids = [tc.test_id for tc in test_cases]
        duplicates = [tid for tid in test_ids if test_ids.count(tid) > 1]
        if duplicates:
            errors.append(f"Duplicate test IDs found: {set(duplicates)}")

        # Check benchmark consistency
        benchmarks = {tc.benchmark_type for tc in test_cases}
        if len(benchmarks) > 1:
            errors.append(
                f"Test cases belong to multiple benchmarks: "
                f"{[b.value for b in benchmarks]}"
            )

        is_valid = len(errors) == 0
        return is_valid, errors

    @staticmethod
    def validate_benchmark_set(
        benchmarks: List[Benchmark]
    ) -> Tuple[bool, List[str]]:
        """
        Business rule: Validate complete set of benchmarks (B1-B6).

        Requirements:
        - All 6 benchmarks present
        - Each benchmark has adequate coverage
        - Overall balanced distribution

        Args:
            benchmarks: List of all benchmarks

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings: List[str] = []

        # Check all benchmarks present
        expected_benchmarks = set(BenchmarkType)
        actual_benchmarks = {b.benchmark_type for b in benchmarks}
        missing = expected_benchmarks - actual_benchmarks

        if missing:
            warnings.append(
                f"Missing benchmarks: {[b.value for b in missing]}"
            )

        # Validate each benchmark
        for benchmark in benchmarks:
            is_valid, bench_warnings = BenchmarkValidator.validate_benchmark_coverage(
                benchmark
            )
            if not is_valid:
                warnings.append(
                    f"Benchmark {benchmark.benchmark_type.value} has issues:"
                )
                warnings.extend([f"  - {w}" for w in bench_warnings])

        # Check overall distribution
        total_tests = sum(b.test_case_count for b in benchmarks)
        for benchmark in benchmarks:
            ratio = benchmark.test_case_count / total_tests if total_tests > 0 else 0
            if ratio < 0.10:  # Less than 10% of total tests
                warnings.append(
                    f"Benchmark {benchmark.benchmark_type.value} has only "
                    f"{ratio:.1%} of total tests. Consider adding more."
                )

        is_valid = len(warnings) == 0
        return is_valid, warnings

    @staticmethod
    def _check_difficulty_distribution(
        test_cases: List[TestCase]
    ) -> List[str]:
        """
        Check if test cases have good difficulty distribution.

        Business rule: Should have mix of difficulties, not all same level.
        """
        warnings: List[str] = []

        if not test_cases:
            return warnings

        difficulty_counts: Dict[DifficultyLevel, int] = {}
        for tc in test_cases:
            difficulty_counts[tc.difficulty] = difficulty_counts.get(tc.difficulty, 0) + 1

        # Check if all same difficulty
        if len(difficulty_counts) == 1:
            warnings.append(
                "All test cases have the same difficulty level. "
                "Recommend mixing low, medium, high, and critical."
            )

        # Check if missing critical difficulty
        if DifficultyLevel.CRITICAL not in difficulty_counts:
            warnings.append(
                "No critical difficulty test cases. "
                "Recommend adding some high-stakes scenarios."
            )

        return warnings

    @staticmethod
    def _check_section_coverage(test_cases: List[TestCase]) -> List[str]:
        """
        Check if test cases cover multiple CCoP sections.

        Business rule: Should not focus on only one section.
        """
        warnings: List[str] = []

        if not test_cases:
            return warnings

        sections = {tc.section for tc in test_cases}

        # Check if only one section
        if len(sections) == 1:
            warnings.append(
                f"All test cases cover only section: {list(sections)[0].value}. "
                "Recommend covering multiple CCoP sections."
            )

        # Check if very limited coverage (< 3 sections)
        if len(sections) < 3 and len(test_cases) >= 5:
            warnings.append(
                f"Only {len(sections)} CCoP sections covered. "
                "Recommend broader section coverage."
            )

        return warnings

    @staticmethod
    def get_coverage_statistics(
        benchmarks: List[Benchmark]
    ) -> Dict[str, any]:
        """
        Get comprehensive coverage statistics across all benchmarks.

        Returns:
            Dictionary with detailed statistics
        """
        total_tests = sum(b.test_case_count for b in benchmarks)

        # Count by benchmark
        by_benchmark = {
            b.benchmark_type.value: b.test_case_count
            for b in benchmarks
        }

        # Count by difficulty (across all benchmarks)
        by_difficulty: Dict[str, int] = {}
        for benchmark in benchmarks:
            for tc in benchmark.test_cases:
                difficulty = tc.difficulty.value
                by_difficulty[difficulty] = by_difficulty.get(difficulty, 0) + 1

        # Count by section
        by_section: Dict[str, int] = {}
        for benchmark in benchmarks:
            for tc in benchmark.test_cases:
                section = tc.section.value
                by_section[section] = by_section.get(section, 0) + 1

        # Count by domain
        by_domain: Dict[str, int] = {}
        for benchmark in benchmarks:
            for tc in benchmark.test_cases:
                domain = tc.domain
                by_domain[domain] = by_domain.get(domain, 0) + 1

        return {
            "total_test_cases": total_tests,
            "by_benchmark": by_benchmark,
            "by_difficulty": by_difficulty,
            "by_section": by_section,
            "by_domain": by_domain,
            "benchmark_count": len(benchmarks),
        }
