"""
Human validation service for LLM judge calibration.

Manages sampling for human validation and tracks human-LLM judge agreement.
Used to calibrate and monitor LLM-as-Judge accuracy.
"""

import random
from typing import Any, List


class HumanValidationService:
    """
    Manages human validation sampling and agreement tracking.

    Used to validate LLM judge performance by comparing with human experts.
    Implements stratified random sampling for validation set selection.
    """

    def __init__(self, sample_rate: float = 0.2) -> None:
        """
        Initialize human validation service.

        Args:
            sample_rate: Fraction of results to sample for human validation (default: 0.2 = 20%)
        """
        self._sample_rate = sample_rate

    def select_validation_sample(
        self,
        results: List[Any]
    ) -> List[Any]:
        """
        Select random sample for human validation.

        Uses stratified random sampling to ensure at least one result
        is selected even for small datasets.

        Args:
            results: List of evaluation results

        Returns:
            Random sample of results for human validation
        """
        if not results:
            return []

        sample_size = max(1, int(len(results) * self._sample_rate))
        return random.sample(results, min(sample_size, len(results)))

    def calculate_agreement(
        self,
        llm_scores: List[float],
        human_scores: List[float],
        tolerance: float = 0.2
    ) -> float:
        """
        Calculate human-LLM agreement rate.

        Args:
            llm_scores: LLM judge scores (0.0-1.0)
            human_scores: Human expert scores (0.0-1.0)
            tolerance: Maximum difference to consider as agreement (default: 0.2)

        Returns:
            Agreement rate (0.0-1.0)
        """
        if not llm_scores or not human_scores:
            return 0.0

        if len(llm_scores) != len(human_scores):
            raise ValueError(
                f"Score lists must have same length: "
                f"llm={len(llm_scores)}, human={len(human_scores)}"
            )

        agreements = sum(
            1 for llm, human in zip(llm_scores, human_scores)
            if abs(llm - human) <= tolerance
        )
        return agreements / len(llm_scores)

    def needs_recalibration(
        self,
        agreement_rate: float,
        threshold: float = 0.8
    ) -> bool:
        """
        Check if LLM judge needs recalibration.

        Args:
            agreement_rate: Current human-LLM agreement rate
            threshold: Minimum acceptable agreement rate (default: 0.8)

        Returns:
            True if recalibration needed
        """
        return agreement_rate < threshold

    def format_for_human_review(self, result: Any) -> str:
        """
        Format evaluation result for human review.

        Args:
            result: Evaluation result to format

        Returns:
            Formatted string for human review
        """
        # Handle EvaluationResult object
        judge_eval = result.metadata.get('judge_evaluation')
        judge_score = result.overall_score if hasattr(result, 'overall_score') else 0.0
        judge_justification = (
            getattr(judge_eval, 'justification', 'N/A')
            if judge_eval else 'N/A'
        )

        return f"""
=== HUMAN VALIDATION REQUIRED ===

Test ID: {result.test_case.test_id}
Question: {result.test_case.question}

Model Response:
{result.model_response.content}

Expected Answer:
{result.test_case.expected_response}

LLM Judge Score: {judge_score:.2f}
LLM Judge Justification: {judge_justification}

Please provide your score (0.0-1.0): _____
Your justification: _____

================================
"""
