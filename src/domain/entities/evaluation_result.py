"""
Evaluation Result Entity

Represents the outcome of evaluating a model on a test case.
Entity with identity (result_id) combining test case, model response, and scoring.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.exceptions.evaluation_error import EvaluationError
from domain.value_objects.evaluation_metric import EvaluationMetric


class EvaluationResult:
    """
    Entity representing the result of evaluating a model on a test case.

    Identity: result_id (UUID)
    Lifecycle: Created → Scored → Finalized

    This entity combines:
    - Test case (what was asked)
    - Model response (what was answered)
    - Evaluation metrics (how well it was answered)
    """

    def __init__(
        self,
        test_case: TestCase,
        model_response: ModelResponse,
        result_id: UUID | None = None,
        metrics: List[EvaluationMetric] | None = None,
        overall_score: float | None = None,
        passed: bool | None = None,
        evaluator_notes: str = "",
        evaluated_at: datetime | None = None,
        metadata: Dict[str, any] | None = None,
    ) -> None:
        """
        Initialize EvaluationResult entity.

        Args:
            test_case: The test case that was evaluated
            model_response: The model's response
            result_id: Unique identifier (auto-generated if None)
            metrics: List of evaluation metrics
            overall_score: Overall score (0.0 to 1.0)
            passed: Whether evaluation passed
            evaluator_notes: Additional notes from evaluator
            evaluated_at: Timestamp of evaluation
            metadata: Additional result metadata

        Raises:
            EvaluationError: If validation fails
        """
        self._result_id = result_id or uuid4()
        self._test_case = test_case
        self._model_response = model_response
        self._metrics = metrics or []
        self._overall_score = overall_score
        self._passed = passed
        self._evaluator_notes = evaluator_notes
        self._evaluated_at = evaluated_at or datetime.utcnow()
        self._metadata = metadata or {}

        self._validate()

    def _validate(self) -> None:
        """
        Validate entity invariants.

        Business rules:
        - If overall_score is set, must be between 0.0 and 1.0
        - If metrics are provided, overall_score should be calculated
        - If passed is set, overall_score should be available
        """
        if self._overall_score is not None:
            if not 0.0 <= self._overall_score <= 1.0:
                raise EvaluationError(
                    f"Overall score must be between 0.0 and 1.0, got {self._overall_score}",
                    test_case_id=self._test_case.test_id
                )

        if self._passed is not None and self._overall_score is None:
            raise EvaluationError(
                "Cannot determine pass/fail without overall score",
                test_case_id=self._test_case.test_id
            )

    # Business methods

    def calculate_overall_score(self) -> float:
        """
        Business rule: Calculate weighted average of all metrics.

        If no metrics, returns 0.0.
        Uses weighted average based on metric weights.

        Returns:
            Overall score (0.0 to 1.0)
        """
        if not self._metrics:
            return 0.0

        total_weighted_value = sum(m.weighted_value for m in self._metrics)
        total_weight = sum(m.weight for m in self._metrics)

        if total_weight == 0:
            return 0.0

        score = total_weighted_value / total_weight
        self._overall_score = score
        return score

    def determine_pass_fail(self) -> bool:
        """
        Business rule: Determine if evaluation passed.

        Uses test case difficulty's passing threshold.
        If overall_score is None, calculates it first.

        Returns:
            True if score >= threshold
        """
        if self._overall_score is None:
            self.calculate_overall_score()

        threshold = self._test_case.get_passing_threshold()
        passed = self._overall_score >= threshold
        self._passed = passed
        return passed

    def add_metric(self, metric: EvaluationMetric) -> None:
        """
        Add an evaluation metric.

        Args:
            metric: Metric to add
        """
        self._metrics.append(metric)
        # Invalidate cached score
        self._overall_score = None
        self._passed = None

    def get_metric_by_name(self, name: str) -> Optional[EvaluationMetric]:
        """
        Get metric by name.

        Args:
            name: Metric name to search for

        Returns:
            Metric if found, None otherwise
        """
        for metric in self._metrics:
            if metric.name == name:
                return metric
        return None

    def is_finalized(self) -> bool:
        """Check if evaluation is complete (has score and pass/fail)."""
        return self._overall_score is not None and self._passed is not None

    def finalize(self) -> None:
        """
        Finalize the evaluation result.

        Calculates overall score and determines pass/fail if not already done.
        """
        if not self.is_finalized():
            self.calculate_overall_score()
            self.determine_pass_fail()

    def get_performance_summary(self) -> Dict[str, any]:
        """
        Get human-readable performance summary.

        Returns:
            Dictionary with summary information
        """
        return {
            "test_id": self._test_case.test_id,
            "benchmark": self._test_case.benchmark_type.value,
            "difficulty": self._test_case.difficulty.value,
            "overall_score": self._overall_score,
            "percentage": f"{(self._overall_score or 0) * 100:.1f}%",
            "passed": self._passed,
            "threshold": self._test_case.get_passing_threshold(),
            "metrics": {m.name: m.value for m in self._metrics},
            "model": self._model_response.model_name,
            "tokens_used": self._model_response.tokens_used,
            "latency_ms": self._model_response.latency_ms,
        }

    def get_failure_reasons(self) -> List[str]:
        """
        Business logic: Identify reasons for failure.

        Returns:
            List of reasons why evaluation failed (empty if passed)
        """
        if self._passed:
            return []

        reasons = []

        # Check individual metrics
        for metric in self._metrics:
            if not metric.is_passing():
                reasons.append(
                    f"{metric.name}: {metric.percentage:.1f}% "
                    f"(threshold: 70%)"
                )

        # Check for hallucination
        if self._model_response.contains_hallucination_indicators():
            reasons.append("Response contains hallucination indicators")

        # Check for empty response
        if self._model_response.is_empty():
            reasons.append("Response is empty or whitespace only")

        # Check overall score
        if self._overall_score is not None:
            threshold = self._test_case.get_passing_threshold()
            if self._overall_score < threshold:
                reasons.append(
                    f"Overall score {self._overall_score:.2f} "
                    f"below threshold {threshold:.2f}"
                )

        return reasons

    # Properties (identity & attributes)

    @property
    def result_id(self) -> UUID:
        """Unique identifier (entity identity)."""
        return self._result_id

    @property
    def test_case(self) -> TestCase:
        """The test case."""
        return self._test_case

    @property
    def model_response(self) -> ModelResponse:
        """The model response."""
        return self._model_response

    @property
    def metrics(self) -> List[EvaluationMetric]:
        """Evaluation metrics (immutable copy)."""
        return self._metrics.copy()

    @property
    def overall_score(self) -> Optional[float]:
        """Overall evaluation score."""
        return self._overall_score

    @property
    def passed(self) -> Optional[bool]:
        """Whether evaluation passed."""
        return self._passed

    @property
    def evaluator_notes(self) -> str:
        """Evaluator notes."""
        return self._evaluator_notes

    @property
    def evaluated_at(self) -> datetime:
        """Evaluation timestamp."""
        return self._evaluated_at

    @property
    def metadata(self) -> Dict[str, any]:
        """Additional metadata (immutable copy)."""
        return self._metadata.copy()

    # Equality based on identity

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EvaluationResult):
            return False
        return self._result_id == other._result_id

    def __hash__(self) -> int:
        return hash(self._result_id)

    def __repr__(self) -> str:
        return (
            f"EvaluationResult(result_id={self._result_id}, "
            f"test_id='{self._test_case.test_id}', "
            f"score={self._overall_score}, "
            f"passed={self._passed})"
        )

    def __str__(self) -> str:
        status = "✓ PASSED" if self._passed else "✗ FAILED"
        score_str = f"{self._overall_score:.2%}" if self._overall_score else "N/A"
        return f"EvaluationResult[{self._test_case.test_id}]: {score_str} {status}"
