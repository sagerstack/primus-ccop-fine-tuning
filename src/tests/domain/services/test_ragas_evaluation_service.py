"""
Tests for RagasEvaluationService.

Validates metric name mapping, hallucination and context_faithfulness computation
across hybrid and llm-only modes.
"""

import pytest
from unittest.mock import patch, MagicMock

from domain.services.ragas_evaluation_service import (
    RagasEvaluationService,
    RagasEvaluation,
    RagasMetricScore,
)

RAGAS_PKG = "ragas"
RAGAS_METRICS_PKG = "ragas.metrics"


def _mock_evaluate_result(scores_dict: dict) -> MagicMock:
    """Create a mock RAGAs evaluate() result with the given scores."""
    mock_result = MagicMock()
    mock_result.scores = MagicMock()
    mock_result.scores.to_dict.return_value = [scores_dict]
    return mock_result


@pytest.fixture
def mock_settings():
    """Mock settings for RagasEvaluationService initialization."""
    with patch("infrastructure.config.settings.get_settings") as mock:
        settings = MagicMock()
        settings.ragas_evaluator_model = "test-model"
        settings.ragas_embedding_model = "test-embedding"
        settings.ragas_api_key = "test-key"
        settings.ragas_api_base_url = "http://test"
        mock.return_value = settings
        yield mock


@pytest.fixture
def service(mock_settings):
    """Create a RagasEvaluationService with mocked settings."""
    return RagasEvaluationService()


def _run_evaluate(service, mock_evaluate_results, retrieved_contexts=None, **kwargs):
    """Helper to run evaluate_response with mocked RAGAs internals."""
    with patch.object(service, '_get_evaluator_llm'), \
         patch.object(service, '_get_evaluator_embeddings'), \
         patch(f"{RAGAS_PKG}.evaluate") as mock_evaluate, \
         patch(f"{RAGAS_PKG}.EvaluationDataset"), \
         patch(f"{RAGAS_PKG}.SingleTurnSample"), \
         patch(f"{RAGAS_METRICS_PKG}.FactualCorrectness"), \
         patch(f"{RAGAS_METRICS_PKG}.SemanticSimilarity"), \
         patch(f"{RAGAS_METRICS_PKG}._AnswerRelevancy"), \
         patch(f"{RAGAS_METRICS_PKG}._Faithfulness"), \
         patch(f"{RAGAS_METRICS_PKG}._ContextPrecision"), \
         patch(f"{RAGAS_METRICS_PKG}._ContextRecall"):

        mock_evaluate.side_effect = mock_evaluate_results

        return service.evaluate_response(
            question=kwargs.get("question", "What is CCoP?"),
            response=kwargs.get("response", "CCoP is..."),
            reference=kwargs.get("reference", "CCoP is a regulatory framework."),
            retrieved_contexts=retrieved_contexts,
        )


class TestFactualRecallMetric:
    """Test factual_recall metric behavior."""

    def test_factual_recall_present_in_hybrid_mode(self, service):
        """factual_recall metric returned with applicable=True in hybrid mode."""
        results = [
            _mock_evaluate_result({"factual_correctness_recall": 0.8, "answer_relevancy": 0.7, "semantic_similarity": 0.85}),
            _mock_evaluate_result({"faithfulness": 0.6, "context_precision": 0.7, "context_recall": 0.8}),
        ]

        result = _run_evaluate(service, results, retrieved_contexts=["Context about CCoP."])

        assert not result.evaluation_error
        metric_names = [m.name for m in result.metrics]
        assert "factual_recall" in metric_names

        recall = [m for m in result.metrics if m.name == "factual_recall"][0]
        assert recall.applicable is True
        assert recall.score == 0.8

    def test_factual_recall_present_in_llm_only_mode(self, service):
        """factual_recall metric returned with applicable=True even without retrieved_contexts."""
        results = [
            _mock_evaluate_result({"factual_correctness_recall": 0.75, "answer_relevancy": 0.8, "semantic_similarity": 0.9}),
        ]

        result = _run_evaluate(service, results, retrieved_contexts=None)

        assert not result.evaluation_error
        metric_names = [m.name for m in result.metrics]
        assert "factual_recall" in metric_names

        recall = [m for m in result.metrics if m.name == "factual_recall"][0]
        assert recall.applicable is True
        assert recall.score == 0.75

    def test_no_factual_precision_metric(self, service):
        """factual_precision should NOT be present (removed from RAGAs)."""
        results = [
            _mock_evaluate_result({"factual_correctness_recall": 0.8, "answer_relevancy": 0.7, "semantic_similarity": 0.85}),
            _mock_evaluate_result({"faithfulness": 0.6, "context_precision": 0.7, "context_recall": 0.8}),
        ]

        result = _run_evaluate(service, results, retrieved_contexts=["Context about CCoP."])

        assert not result.evaluation_error
        metric_names = [m.name for m in result.metrics]
        assert "factual_precision" not in metric_names


class TestContextFaithfulness:
    """Test context_faithfulness metric behavior."""

    def test_context_faithfulness_applicable_in_hybrid(self, service):
        """context_faithfulness returned with applicable=True when retrieved_contexts provided."""
        results = [
            _mock_evaluate_result({"factual_correctness_precision": 0.9, "factual_correctness_recall": 0.8, "answer_relevancy": 0.7, "semantic_similarity": 0.85}),
            _mock_evaluate_result({"faithfulness": 0.75, "context_precision": 0.7, "context_recall": 0.8}),
        ]

        result = _run_evaluate(service, results, retrieved_contexts=["Context about CCoP."])

        assert not result.evaluation_error
        cf = [m for m in result.metrics if m.name == "context_faithfulness"][0]
        assert cf.applicable is True
        assert cf.score == 0.75

    def test_context_faithfulness_not_applicable_without_contexts(self, service):
        """context_faithfulness returned with applicable=False when no retrieved_contexts."""
        results = [
            _mock_evaluate_result({"factual_correctness_precision": 0.85, "factual_correctness_recall": 0.75, "answer_relevancy": 0.8, "semantic_similarity": 0.9}),
        ]

        result = _run_evaluate(service, results, retrieved_contexts=None)

        assert not result.evaluation_error
        cf = [m for m in result.metrics if m.name == "context_faithfulness"][0]
        assert cf.applicable is False
        assert cf.score == 0.0


class TestMetricCompleteness:
    """Test that all expected metrics are present."""

    def test_hybrid_mode_has_six_metrics(self, service):
        """Hybrid mode produces 6 metrics (factual_precision removed)."""
        results = [
            _mock_evaluate_result({"factual_correctness_recall": 0.8, "answer_relevancy": 0.7, "semantic_similarity": 0.85}),
            _mock_evaluate_result({"faithfulness": 0.75, "context_precision": 0.7, "context_recall": 0.8}),
        ]

        result = _run_evaluate(service, results, retrieved_contexts=["ctx"])

        metric_names = sorted([m.name for m in result.metrics])
        expected = sorted([
            "factual_recall", "answer_relevancy", "semantic_similarity",
            "context_faithfulness", "context_precision", "context_recall"
        ])
        assert metric_names == expected

    def test_llm_only_mode_metrics(self, service):
        """LLM-only mode produces all 6 metrics with appropriate applicable flags."""
        results = [
            _mock_evaluate_result({"factual_correctness_recall": 0.75, "answer_relevancy": 0.8, "semantic_similarity": 0.9}),
        ]

        result = _run_evaluate(service, results, retrieved_contexts=None)

        metric_names = sorted([m.name for m in result.metrics])
        expected = sorted([
            "factual_recall", "answer_relevancy", "semantic_similarity",
            "context_faithfulness", "context_precision", "context_recall"
        ])
        assert metric_names == expected

        applicable_metrics = [m.name for m in result.metrics if m.applicable]
        not_applicable_metrics = [m.name for m in result.metrics if not m.applicable]

        assert "factual_recall" in applicable_metrics
        assert "answer_relevancy" in applicable_metrics
        assert "semantic_similarity" in applicable_metrics
        assert "context_faithfulness" in not_applicable_metrics
        assert "context_precision" in not_applicable_metrics
        assert "context_recall" in not_applicable_metrics

    def test_no_bare_faithfulness_metric(self, service):
        """No metric should be named 'faithfulness'."""
        results = [
            _mock_evaluate_result({"factual_correctness_recall": 0.8, "answer_relevancy": 0.7, "semantic_similarity": 0.85}),
            _mock_evaluate_result({"faithfulness": 0.75, "context_precision": 0.7, "context_recall": 0.8}),
        ]

        result = _run_evaluate(service, results, retrieved_contexts=["ctx"])

        metric_names = [m.name for m in result.metrics]
        assert "faithfulness" not in metric_names

    def test_no_answer_correctness_metric(self, service):
        """No metric should be named 'answer_correctness' (only recall remains, precision removed)."""
        results = [
            _mock_evaluate_result({"factual_correctness_recall": 0.8, "answer_relevancy": 0.7, "semantic_similarity": 0.85}),
            _mock_evaluate_result({"faithfulness": 0.75, "context_precision": 0.7, "context_recall": 0.8}),
        ]

        result = _run_evaluate(service, results, retrieved_contexts=["ctx"])

        metric_names = [m.name for m in result.metrics]
        assert "answer_correctness" not in metric_names

    def test_no_hallucination_metric(self, service):
        """No metric should be named 'hallucination' (removed from RAGAs)."""
        results = [
            _mock_evaluate_result({"factual_correctness_recall": 0.8, "answer_relevancy": 0.7, "semantic_similarity": 0.85}),
            _mock_evaluate_result({"faithfulness": 0.75, "context_precision": 0.7, "context_recall": 0.8}),
        ]

        result = _run_evaluate(service, results, retrieved_contexts=["ctx"])

        metric_names = [m.name for m in result.metrics]
        assert "hallucination" not in metric_names


class TestSemanticSimilarityMetric:
    """Test semantic_similarity metric behavior."""

    def test_semantic_similarity_present_always(self, service):
        """semantic_similarity metric returned with applicable=True in both modes."""
        # Test hybrid mode
        results_hybrid = [
            _mock_evaluate_result({"factual_correctness_recall": 0.8, "answer_relevancy": 0.7, "semantic_similarity": 0.92}),
            _mock_evaluate_result({"faithfulness": 0.75, "context_precision": 0.7, "context_recall": 0.8}),
        ]
        result = _run_evaluate(service, results_hybrid, retrieved_contexts=["ctx"])

        assert not result.evaluation_error
        metric_names = [m.name for m in result.metrics]
        assert "semantic_similarity" in metric_names

        sem_sim = [m for m in result.metrics if m.name == "semantic_similarity"][0]
        assert sem_sim.applicable is True
        assert sem_sim.score == 0.92

        # Test llm-only mode
        results_llm = [
            _mock_evaluate_result({"factual_correctness_recall": 0.75, "answer_relevancy": 0.8, "semantic_similarity": 0.88}),
        ]
        result_llm = _run_evaluate(service, results_llm, retrieved_contexts=None)

        assert not result_llm.evaluation_error
        sem_sim_llm = [m for m in result_llm.metrics if m.name == "semantic_similarity"][0]
        assert sem_sim_llm.applicable is True
        assert sem_sim_llm.score == 0.88
