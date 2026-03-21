"""
Tests for EvaluationResult entity.

Validates ragas_composite_score formula after Phase 2.4 changes
(simple average of factual_recall, answer_relevancy, semantic_similarity).
"""

import pytest

from domain.entities.evaluation_result import EvaluationResult
from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.services.ragas_evaluation_service import RagasEvaluation, RagasMetricScore
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.ccop_section import CCoPSection
from domain.value_objects.difficulty_level import DifficultyLevel


def _make_test_case(test_id: str = "B3-001") -> TestCase:
    """Helper to create a minimal TestCase for composite score tests."""
    return TestCase(
        test_id=test_id,
        benchmark_type=BenchmarkType("B3_Conditional_Compliance_Reasoning"),
        section=CCoPSection("Section 3: Governance"),
        clause_reference="3.1.1",
        difficulty=DifficultyLevel("medium"),
        question="Test question with at least fifty characters for validation to pass successfully",
        expected_response="Test expected response content",
        evaluation_criteria={"accuracy": "test"},
    )


def _make_model_response() -> ModelResponse:
    """Helper to create a minimal ModelResponse for composite score tests."""
    return ModelResponse(
        content="Test response content",
        model_name="test-model",
    )


def _make_ragas_evaluation(
    factual_recall: float,
    answer_relevancy: float,
    semantic_similarity: float,
    context_faithfulness: float = 0.8,
    context_recall: float = 0.9,
    context_precision: float = 0.85,
) -> RagasEvaluation:
    """Helper to create RagasEvaluation with given metrics."""
    metrics = [
        RagasMetricScore(name="factual_recall", score=factual_recall, applicable=True),
        RagasMetricScore(name="answer_relevancy", score=answer_relevancy, applicable=True),
        RagasMetricScore(name="semantic_similarity", score=semantic_similarity, applicable=True),
        RagasMetricScore(name="context_faithfulness", score=context_faithfulness, applicable=True),
        RagasMetricScore(name="context_recall", score=context_recall, applicable=True),
        RagasMetricScore(name="context_precision", score=context_precision, applicable=True),
    ]
    return RagasEvaluation(metrics=metrics, is_rag_response=True, evaluation_error=False)


class TestRagasCompositeScore:
    """Test ragas_composite_score property with new Phase 2.4 formula."""

    def test_ragas_composite_score_new_formula(self):
        """ragas_score = (factual_recall + answer_relevancy + semantic_similarity) / 3."""
        ragas = _make_ragas_evaluation(
            factual_recall=0.8,
            answer_relevancy=0.7,
            semantic_similarity=0.9,
        )

        result = EvaluationResult(
            test_case=_make_test_case(),
            model_response=_make_model_response(),
            overall_score=0.8,
            ragas_evaluation=ragas,
        )

        # (0.8 + 0.7 + 0.9) / 3 = 2.4 / 3 = 0.8
        assert result.ragas_composite_score == pytest.approx(0.8, rel=0.01)

    def test_ragas_composite_score_missing_semantic_similarity_returns_none(self):
        """ragas_score returns None if semantic_similarity is missing."""
        metrics = [
            RagasMetricScore(name="factual_recall", score=0.8, applicable=True),
            RagasMetricScore(name="answer_relevancy", score=0.7, applicable=True),
            # semantic_similarity missing
            RagasMetricScore(name="context_faithfulness", score=0.8, applicable=True),
        ]
        ragas = RagasEvaluation(metrics=metrics, is_rag_response=True, evaluation_error=False)

        result = EvaluationResult(
            test_case=_make_test_case("B3-002"),
            model_response=_make_model_response(),
            overall_score=0.8,
            ragas_evaluation=ragas,
        )

        assert result.ragas_composite_score is None

    def test_ragas_composite_score_missing_factual_recall_returns_none(self):
        """ragas_score returns None if factual_recall is missing."""
        metrics = [
            # factual_recall missing
            RagasMetricScore(name="answer_relevancy", score=0.7, applicable=True),
            RagasMetricScore(name="semantic_similarity", score=0.9, applicable=True),
        ]
        ragas = RagasEvaluation(metrics=metrics, is_rag_response=True, evaluation_error=False)

        result = EvaluationResult(
            test_case=_make_test_case("B3-003"),
            model_response=_make_model_response(),
            overall_score=0.8,
            ragas_evaluation=ragas,
        )

        assert result.ragas_composite_score is None

    def test_ragas_composite_score_no_ragas_evaluation_returns_none(self):
        """ragas_score returns None when ragas_evaluation is None."""
        result = EvaluationResult(
            test_case=_make_test_case("B3-010"),
            model_response=_make_model_response(),
            overall_score=0.8,
            ragas_evaluation=None,
        )

        assert result.ragas_composite_score is None

    def test_ragas_composite_score_evaluation_error_returns_none(self):
        """ragas_score returns None when ragas_evaluation has evaluation_error=True."""
        ragas = RagasEvaluation(metrics=[], is_rag_response=True, evaluation_error=True)

        result = EvaluationResult(
            test_case=_make_test_case("B3-004"),
            model_response=_make_model_response(),
            overall_score=0.8,
            ragas_evaluation=ragas,
        )

        assert result.ragas_composite_score is None

    def test_ragas_composite_score_various_values(self):
        """Test composite score with various input values."""
        # Test case 1: All metrics at 1.0
        ragas1 = _make_ragas_evaluation(1.0, 1.0, 1.0)
        result1 = EvaluationResult(
            test_case=_make_test_case("B3-005"),
            model_response=_make_model_response(),
            overall_score=1.0,
            ragas_evaluation=ragas1,
        )
        assert result1.ragas_composite_score == pytest.approx(1.0, rel=0.01)

        # Test case 2: All metrics at 0.0
        ragas2 = _make_ragas_evaluation(0.0, 0.0, 0.0)
        result2 = EvaluationResult(
            test_case=_make_test_case("B3-006"),
            model_response=_make_model_response(),
            overall_score=0.0,
            ragas_evaluation=ragas2,
        )
        assert result2.ragas_composite_score == pytest.approx(0.0, rel=0.01)

        # Test case 3: Mixed values
        ragas3 = _make_ragas_evaluation(0.6, 0.8, 0.7)
        result3 = EvaluationResult(
            test_case=_make_test_case("B3-007"),
            model_response=_make_model_response(),
            overall_score=0.7,
            ragas_evaluation=ragas3,
        )
        # (0.6 + 0.8 + 0.7) / 3 = 2.1 / 3 = 0.7
        assert result3.ragas_composite_score == pytest.approx(0.7, rel=0.01)
