"""
Unit tests for HumanValidationService.

Tests human validation sampling and agreement tracking.
"""

import pytest

from domain.services.human_validation_service import HumanValidationService


class TestHumanValidationService:
    """Test suite for HumanValidationService."""

    def test_select_validation_sample_20_percent(self) -> None:
        """Test selecting 20% sample from results."""
        service = HumanValidationService(sample_rate=0.2)
        results = list(range(100))  # 100 dummy results

        sample = service.select_validation_sample(results)

        assert len(sample) == 20
        assert all(item in results for item in sample)

    def test_select_validation_sample_custom_rate(self) -> None:
        """Test custom sample rate."""
        service = HumanValidationService(sample_rate=0.1)
        results = list(range(50))

        sample = service.select_validation_sample(results)

        assert len(sample) == 5  # 10% of 50

    def test_select_validation_sample_small_dataset(self) -> None:
        """Test sampling from small dataset (ensures at least 1 sample)."""
        service = HumanValidationService(sample_rate=0.2)
        results = [1, 2]  # Only 2 results

        sample = service.select_validation_sample(results)

        assert len(sample) == 1  # At least 1 sample

    def test_select_validation_sample_empty_results(self) -> None:
        """Test sampling from empty results."""
        service = HumanValidationService(sample_rate=0.2)
        results: list[int] = []

        sample = service.select_validation_sample(results)

        assert sample == []

    def test_select_validation_sample_randomness(self) -> None:
        """Test that sampling is random."""
        service = HumanValidationService(sample_rate=0.2)
        results = list(range(100))

        # Take multiple samples and verify they differ
        sample1 = set(service.select_validation_sample(results))
        sample2 = set(service.select_validation_sample(results))

        # Samples should differ (probabilistically)
        # With 20 items sampled from 100, identical samples are extremely unlikely
        assert sample1 != sample2

    def test_calculate_agreement_perfect(self) -> None:
        """Test agreement calculation with perfect agreement."""
        service = HumanValidationService()
        llm_scores = [0.8, 0.6, 0.9, 0.7]
        human_scores = [0.8, 0.6, 0.9, 0.7]

        agreement = service.calculate_agreement(llm_scores, human_scores)

        assert agreement == 1.0

    def test_calculate_agreement_within_tolerance(self) -> None:
        """Test agreement with scores within tolerance."""
        service = HumanValidationService()
        llm_scores = [0.8, 0.6, 0.9, 0.7]
        human_scores = [0.85, 0.55, 0.95, 0.65]  # All within 0.2 tolerance

        agreement = service.calculate_agreement(
            llm_scores, human_scores, tolerance=0.2
        )

        assert agreement == 1.0

    def test_calculate_agreement_partial(self) -> None:
        """Test agreement with partial disagreement."""
        service = HumanValidationService()
        llm_scores = [0.8, 0.6, 0.9, 0.7]
        human_scores = [0.8, 0.3, 0.9, 0.4]  # 2 agree, 2 disagree

        agreement = service.calculate_agreement(
            llm_scores, human_scores, tolerance=0.2
        )

        assert agreement == 0.5

    def test_calculate_agreement_no_agreement(self) -> None:
        """Test agreement with complete disagreement."""
        service = HumanValidationService()
        llm_scores = [0.8, 0.8, 0.8]
        human_scores = [0.2, 0.3, 0.1]  # All outside tolerance

        agreement = service.calculate_agreement(
            llm_scores, human_scores, tolerance=0.2
        )

        assert agreement == 0.0

    def test_calculate_agreement_empty_lists(self) -> None:
        """Test agreement calculation with empty lists."""
        service = HumanValidationService()

        agreement = service.calculate_agreement([], [])

        assert agreement == 0.0

    def test_calculate_agreement_mismatched_lengths(self) -> None:
        """Test that mismatched list lengths raise error."""
        service = HumanValidationService()
        llm_scores = [0.8, 0.6, 0.9]
        human_scores = [0.8, 0.6]

        with pytest.raises(ValueError, match="same length"):
            service.calculate_agreement(llm_scores, human_scores)

    def test_needs_recalibration_below_threshold(self) -> None:
        """Test recalibration detection when agreement is low."""
        service = HumanValidationService()

        assert service.needs_recalibration(0.75, threshold=0.8) is True
        assert service.needs_recalibration(0.5, threshold=0.8) is True

    def test_needs_recalibration_above_threshold(self) -> None:
        """Test no recalibration needed when agreement is high."""
        service = HumanValidationService()

        assert service.needs_recalibration(0.85, threshold=0.8) is False
        assert service.needs_recalibration(1.0, threshold=0.8) is False

    def test_needs_recalibration_at_threshold(self) -> None:
        """Test recalibration at exact threshold."""
        service = HumanValidationService()

        # At threshold should NOT need recalibration
        assert service.needs_recalibration(0.8, threshold=0.8) is False

    def test_format_for_human_review(self) -> None:
        """Test formatting evaluation result for human review."""
        service = HumanValidationService()

        # Create mock result object
        class MockResult:
            def __init__(self) -> None:
                from domain.entities.model_response import ModelResponse
                from domain.entities.test_case import TestCase
                from domain.value_objects.benchmark_type import BenchmarkType
                from domain.value_objects.ccop_section import CCoPSection
                from domain.value_objects.difficulty_level import DifficultyLevel

                self.test_case = TestCase(
                    test_id="B12-001",
                    benchmark_type=BenchmarkType.from_string("B12_Audit_Perspective_Alignment"),
                    section=CCoPSection.from_string("Section 3: Governance"),
                    clause_reference="3.1.1",
                    difficulty=DifficultyLevel.from_string("medium"),
                    question="What audit evidence would demonstrate compliance with this requirement?",
                    expected_response="Expected answer for testing formatting",
                    evaluation_criteria={"test": "value"},
                )
                self.model_response = ModelResponse(content="Model answer", metadata={})
                self.overall_score = 0.85
                self.metadata: dict[str, any] = {}

        result = MockResult()
        formatted = service.format_for_human_review(result)

        assert "B12-001" in formatted
        assert "What audit evidence would demonstrate compliance" in formatted
        assert "Model answer" in formatted
        assert "Expected answer for testing formatting" in formatted
        assert "0.85" in formatted
