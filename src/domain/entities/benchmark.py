"""
Benchmark Entity

Represents a collection of test cases for a specific benchmark category (B1-B6).
Entity with identity (benchmark_type) and aggregate business logic.
"""

from typing import Dict, List, Optional

from domain.entities.evaluation_result import EvaluationResult
from domain.entities.test_case import TestCase
from domain.exceptions.validation_error import ValidationError
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.difficulty_level import DifficultyLevel


class Benchmark:
    """
    Entity representing a benchmark category with its test cases.

    Identity: benchmark_type (B1-B6)
    Lifecycle: Created → Populated with test cases → Evaluated

    This entity provides aggregate operations over a collection of test cases.
    """

    def __init__(
        self,
        benchmark_type: BenchmarkType,
        test_cases: List[TestCase] | None = None,
        description: Optional[str] = None,
    ) -> None:
        """
        Initialize Benchmark entity.

        Args:
            benchmark_type: Benchmark category (B1-B6)
            test_cases: List of test cases for this benchmark
            description: Optional description override

        Raises:
            ValidationError: If validation fails
        """
        self._benchmark_type = benchmark_type
        self._test_cases: List[TestCase] = test_cases or []
        self._description = description or benchmark_type.description

        self._validate()

    def _validate(self) -> None:
        """
        Validate entity invariants.

        Business rules:
        - All test cases must belong to this benchmark
        - Test case IDs must be unique
        """
        # Check all test cases belong to this benchmark
        for tc in self._test_cases:
            if tc.benchmark_type != self._benchmark_type:
                raise ValidationError(
                    f"Test case {tc.test_id} belongs to benchmark "
                    f"{tc.benchmark_type.value}, not {self._benchmark_type.value}"
                )

        # Check for duplicate test IDs
        test_ids = [tc.test_id for tc in self._test_cases]
        if len(test_ids) != len(set(test_ids)):
            duplicates = [tid for tid in test_ids if test_ids.count(tid) > 1]
            raise ValidationError(
                f"Duplicate test case IDs found: {duplicates}"
            )

    # Business methods

    def add_test_case(self, test_case: TestCase) -> None:
        """
        Add a test case to this benchmark.

        Args:
            test_case: Test case to add

        Raises:
            ValidationError: If test case doesn't belong to this benchmark
        """
        if test_case.benchmark_type != self._benchmark_type:
            raise ValidationError(
                f"Cannot add test case {test_case.test_id} "
                f"(benchmark {test_case.benchmark_type.value}) "
                f"to benchmark {self._benchmark_type.value}"
            )

        if test_case.test_id in [tc.test_id for tc in self._test_cases]:
            raise ValidationError(
                f"Test case {test_case.test_id} already exists in benchmark"
            )

        self._test_cases.append(test_case)

    def get_test_case_by_id(self, test_id: str) -> Optional[TestCase]:
        """
        Find test case by ID.

        Args:
            test_id: Test case ID to search for

        Returns:
            Test case if found, None otherwise
        """
        for tc in self._test_cases:
            if tc.test_id == test_id:
                return tc
        return None

    def get_test_cases_by_difficulty(self, difficulty: DifficultyLevel) -> List[TestCase]:
        """
        Filter test cases by difficulty level.

        Args:
            difficulty: Difficulty level to filter by

        Returns:
            List of test cases with matching difficulty
        """
        return [tc for tc in self._test_cases if tc.difficulty == difficulty]

    def get_high_priority_test_cases(self) -> List[TestCase]:
        """
        Business rule: Get high priority test cases (high/critical difficulty).

        Returns:
            List of high priority test cases
        """
        return [tc for tc in self._test_cases if tc.is_high_priority()]

    def get_ot_specific_test_cases(self) -> List[TestCase]:
        """
        Business rule: Get OT-specific test cases.

        Returns:
            List of OT-specific test cases
        """
        return [tc for tc in self._test_cases if tc.is_ot_specific()]

    def calculate_overall_score(self, results: List[EvaluationResult]) -> float:
        """
        Business rule: Calculate overall benchmark score from evaluation results.

        Args:
            results: List of evaluation results for this benchmark

        Returns:
            Overall score (0.0 to 1.0)
        """
        if not results:
            return 0.0

        # Filter results that belong to this benchmark
        benchmark_results = [
            r for r in results
            if r.test_case.benchmark_type == self._benchmark_type
        ]

        if not benchmark_results:
            return 0.0

        # Calculate weighted average (high difficulty tests count more)
        total_weighted_score = 0.0
        total_weight = 0.0

        for result in benchmark_results:
            if result.overall_score is not None:
                weight = result.test_case.difficulty.priority_score
                total_weighted_score += result.overall_score * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return total_weighted_score / total_weight

    def get_statistics(self) -> Dict[str, any]:
        """
        Get statistical summary of test cases in this benchmark.

        Returns:
            Dictionary with statistics
        """
        total = len(self._test_cases)
        if total == 0:
            return {"total": 0}

        difficulty_counts = {}
        domain_counts = {"IT": 0, "OT": 0, "IT/OT": 0}

        for tc in self._test_cases:
            # Count by difficulty
            diff = tc.difficulty.value
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1

            # Count by domain
            if tc.is_it_specific():
                domain_counts["IT"] += 1
            elif tc.is_ot_specific():
                domain_counts["OT"] += 1
            else:
                domain_counts["IT/OT"] += 1

        return {
            "benchmark": self._benchmark_type.value,
            "total": total,
            "by_difficulty": difficulty_counts,
            "by_domain": domain_counts,
            "high_priority_count": len(self.get_high_priority_test_cases()),
            "ot_specific_count": len(self.get_ot_specific_test_cases()),
        }

    # Properties (identity & attributes)

    @property
    def benchmark_type(self) -> BenchmarkType:
        """Benchmark type (entity identity)."""
        return self._benchmark_type

    @property
    def description(self) -> str:
        """Benchmark description."""
        return self._description

    @property
    def test_cases(self) -> List[TestCase]:
        """Test cases (immutable copy)."""
        return self._test_cases.copy()

    @property
    def test_case_count(self) -> int:
        """Number of test cases."""
        return len(self._test_cases)

    # Equality based on identity

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Benchmark):
            return False
        return self._benchmark_type == other._benchmark_type

    def __hash__(self) -> int:
        return hash(self._benchmark_type)

    def __repr__(self) -> str:
        return (
            f"Benchmark(type={self._benchmark_type.value}, "
            f"test_cases={self.test_case_count})"
        )

    def __str__(self) -> str:
        return f"Benchmark[{self._benchmark_type.value}]: {self._description} ({self.test_case_count} tests)"
