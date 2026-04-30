"""
Tests for Evaluate Model Use Case metadata building.

Tests the new metadata functionality:
1. Metadata building with all evaluation parameters
2. Category scores calculation
3. Tier detection from benchmarks
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from application.dtos.evaluation_request_dto import EvaluationRequestDTO
from application.dtos.evaluation_result_dto import EvaluationSummaryDTO
from application.dtos.evaluation_result_dto import EvaluationResultDTO
from application.use_cases.evaluate_model import EvaluateModelUseCase
from domain.entities.evaluation_result import EvaluationResult
from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.difficulty_level import DifficultyLevel
from domain.value_objects.evaluation_metric import accuracy_metric, completeness_metric


class TestMetadataBuilding:
    """Test _build_evaluation_metadata method."""

    def setup_method(self):
        """Setup test fixtures."""
        self.model_gateway = Mock()
        self.test_case_repository = Mock()
        self.result_repository = Mock()
        self.logger = Mock()

        self.use_case = EvaluateModelUseCase(
            self.model_gateway,
            self.test_case_repository,
            self.result_repository,
            self.logger
        )

    def test_metadata_includes_all_required_fields(self):
        """Test metadata includes all required fields."""
        request = EvaluationRequestDTO(
            model_name="primus-reasoning",
            benchmark_types=["B1", "B2"],
            evaluation_phase="baseline",
            pass_threshold=0.15,
            temperature=0.7
        )

        summary = EvaluationSummaryDTO(
            model_name="primus-reasoning",
            total_tests=10,
            passed_tests=8,
            failed_tests=2,
            overall_score=0.75,
            by_benchmark={"B1": {"total": 5, "passed": 4, "score": 0.8}},
            by_difficulty={},
            evaluation_started_at=datetime.now(),
            evaluation_completed_at=datetime.now(),
            total_duration_seconds=100.0,
            results=[]
        )

        start_time = datetime.now()
        end_time = datetime.now()

        metadata = self.use_case._build_evaluation_metadata(
            request, summary, start_time, end_time
        )

        # Check all required fields
        assert metadata["model_name"] == "primus-reasoning"
        assert metadata["evaluation_phase"] == "baseline"
        assert metadata["pass_threshold"] == 0.15
        assert metadata["benchmarks"] == ["B1", "B2"]
        assert metadata["total_tests"] == 10
        assert metadata["passed_tests"] == 8
        assert metadata["failed_tests"] == 2
        assert metadata["overall_score"] == 0.75
        assert "evaluated_at" in metadata
        assert "completed_at" in metadata
        assert metadata["temperature"] == 0.7

    def test_metadata_detects_tier_1(self):
        """Test metadata correctly detects Tier 1 from benchmarks."""
        request = EvaluationRequestDTO(
            model_name="test-model",
            benchmark_types=["B1", "B2", "B21"],  # Tier 1 benchmarks
            evaluation_phase="baseline"
        )

        summary = EvaluationSummaryDTO(
            model_name="test-model",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            overall_score=0.5,
            by_benchmark={},
            by_difficulty={},
            evaluation_started_at=datetime.now(),
            evaluation_completed_at=datetime.now(),
            total_duration_seconds=10.0,
            results=[]
        )

        metadata = self.use_case._build_evaluation_metadata(
            request, summary, datetime.now(), datetime.now()
        )

        assert metadata["tier"] == 1
        assert metadata["tier_name"] == "Binary Metrics"

    def test_metadata_without_tier(self):
        """Test metadata when benchmarks don't match a tier."""
        request = EvaluationRequestDTO(
            model_name="test-model",
            benchmark_types=["B1", "B3"],  # Not a complete tier
            evaluation_phase="baseline"
        )

        summary = EvaluationSummaryDTO(
            model_name="test-model",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            overall_score=0.5,
            by_benchmark={},
            by_difficulty={},
            evaluation_started_at=datetime.now(),
            evaluation_completed_at=datetime.now(),
            total_duration_seconds=10.0,
            results=[]
        )

        metadata = self.use_case._build_evaluation_metadata(
            request, summary, datetime.now(), datetime.now()
        )

        assert "tier" not in metadata
        assert "tier_name" not in metadata

    def test_metadata_includes_benchmark_scores(self):
        """Test metadata includes benchmark scores."""
        request = EvaluationRequestDTO(
            model_name="test-model",
            benchmark_types=["B1"],
            evaluation_phase="baseline"
        )

        benchmark_scores = {
            "B1_CCoP_Applicability_Scope": {
                "total": 8,
                "passed": 6,
                "score": 0.75
            }
        }

        summary = EvaluationSummaryDTO(
            model_name="test-model",
            total_tests=8,
            passed_tests=6,
            failed_tests=2,
            overall_score=0.75,
            by_benchmark=benchmark_scores,
            by_difficulty={},
            evaluation_started_at=datetime.now(),
            evaluation_completed_at=datetime.now(),
            total_duration_seconds=10.0,
            results=[]
        )

        metadata = self.use_case._build_evaluation_metadata(
            request, summary, datetime.now(), datetime.now()
        )

        assert "benchmark_scores" in metadata
        assert "B1_CCoP_Applicability_Scope" in metadata["benchmark_scores"]
        assert metadata["benchmark_scores"]["B1_CCoP_Applicability_Scope"]["score"] == 0.75


class TestCategoryScoresCalculation:
    """Test _calculate_category_scores method."""

    def setup_method(self):
        """Setup test fixtures."""
        self.model_gateway = Mock()
        self.test_case_repository = Mock()
        self.result_repository = Mock()
        self.logger = Mock()

        self.use_case = EvaluateModelUseCase(
            self.model_gateway,
            self.test_case_repository,
            self.result_repository,
            self.logger
        )

    def test_category_scores_structure(self):
        """Test category scores have correct structure."""
        # Create mock result DTOs for B1 and B2 (Regulatory category)
        results = [
            EvaluationResultDTO(
                result_id=str(uuid4()),
                test_id="B1-001",
                benchmark_type="B1_CCoP_Applicability_Scope",
                question="Test question for B1-001",
                model_name="test-model",
                response_content="Response",
                overall_score=0.8,
                passed=True,
                metrics=[],
                threshold=0.15,
                tokens_used=100,
                latency_ms=1000,
                evaluated_at=datetime.now()
            ),
            EvaluationResultDTO(
                result_id=str(uuid4()),
                test_id="B2-001",
                benchmark_type="B2_Compliance_Classification_Accuracy",
                question="Test question for B2-001",
                model_name="test-model",
                response_content="Response",
                overall_score=0.9,
                passed=True,
                metrics=[],
                threshold=0.15,
                tokens_used=100,
                latency_ms=1000,
                evaluated_at=datetime.now()
            )
        ]

        category_scores = self.use_case._calculate_category_scores(results)

        # Should have Regulatory category
        assert "Regulatory Applicability & Interpretation" in category_scores

        regulatory = category_scores["Regulatory Applicability & Interpretation"]

        # Check structure
        assert "average_score" in regulatory
        assert "weight" in regulatory
        assert "weighted_contribution" in regulatory
        assert "test_count" in regulatory
        assert "benchmarks" in regulatory

    def test_category_scores_calculation(self):
        """Test category scores are calculated correctly."""
        results = [
            EvaluationResultDTO(
                result_id=str(uuid4()),
                test_id="B1-001",
                benchmark_type="B1_CCoP_Applicability_Scope",
                question="Test question for B1-001",
                model_name="test-model",
                response_content="Response",
                overall_score=0.6,
                passed=True,
                metrics=[],
                threshold=0.15,
                tokens_used=100,
                latency_ms=1000,
                evaluated_at=datetime.now()
            ),
            EvaluationResultDTO(
                result_id=str(uuid4()),
                test_id="B1-002",
                benchmark_type="B1_CCoP_Applicability_Scope",
                question="Test question for B1-002",
                model_name="test-model",
                response_content="Response",
                overall_score=0.8,
                passed=True,
                metrics=[],
                threshold=0.15,
                tokens_used=100,
                latency_ms=1000,
                evaluated_at=datetime.now()
            )
        ]

        category_scores = self.use_case._calculate_category_scores(results)

        regulatory = category_scores["Regulatory Applicability & Interpretation"]

        # Average should be (0.6 + 0.8) / 2 = 0.7
        assert regulatory["average_score"] == 0.7

        # Weight should be 0.25 (25%)
        assert regulatory["weight"] == 0.25

        # Weighted contribution should be 0.7 * 0.25 = 0.175
        assert regulatory["weighted_contribution"] == 0.175

        # Test count should be 2
        assert regulatory["test_count"] == 2

    def test_category_scores_multiple_categories(self):
        """Test category scores with results from multiple categories."""
        results = [
            # Regulatory category (B1)
            EvaluationResultDTO(
                result_id=str(uuid4()),
                test_id="B1-001",
                benchmark_type="B1_CCoP_Applicability_Scope",
                question="Test question for B1-001",
                model_name="test-model",
                response_content="Response",
                overall_score=0.8,
                passed=True,
                metrics=[],
                threshold=0.15,
                tokens_used=100,
                latency_ms=1000,
                evaluated_at=datetime.now()
            ),
            # Safety category (B21)
            EvaluationResultDTO(
                result_id=str(uuid4()),
                test_id="B21-001",
                benchmark_type="B21_Hallucination_Rate",
                question="Test question for B21-001",
                model_name="test-model",
                response_content="Response",
                overall_score=0.5,
                passed=True,
                metrics=[],
                threshold=0.15,
                tokens_used=100,
                latency_ms=1000,
                evaluated_at=datetime.now()
            )
        ]

        category_scores = self.use_case._calculate_category_scores(results)

        # Should have both categories
        assert "Regulatory Applicability & Interpretation" in category_scores
        assert "Safety & Regulatory Grounding" in category_scores

        # Regulatory: B1 score = 0.8
        regulatory = category_scores["Regulatory Applicability & Interpretation"]
        assert regulatory["average_score"] == 0.8
        assert regulatory["weight"] == 0.25

        # Safety: B21 score = 0.5
        safety = category_scores["Safety & Regulatory Grounding"]
        assert safety["average_score"] == 0.5
        assert safety["weight"] == 0.20

    def test_category_scores_empty_results(self):
        """Test category scores with empty results."""
        category_scores = self.use_case._calculate_category_scores([])

        # Should return empty dict
        assert category_scores == {}


class TestOverallScoreNormalization:
    """Test _calculate_category_weighted_score normalization."""

    def setup_method(self):
        """Setup test fixtures."""
        self.model_gateway = Mock()
        self.test_case_repository = Mock()
        self.result_repository = Mock()
        self.logger = Mock()

        self.use_case = EvaluateModelUseCase(
            self.model_gateway,
            self.test_case_repository,
            self.result_repository,
            self.logger
        )

    def _make_result(self, benchmark_short_name: str, overall_score: float) -> EvaluationResult:
        """Create a mock EvaluationResult with the given benchmark and score."""
        test_case = Mock(spec=TestCase)
        test_case.benchmark_type = Mock()
        test_case.benchmark_type.short_name = benchmark_short_name
        test_case.benchmark_type.value = f"{benchmark_short_name}_Test"

        model_response = Mock(spec=ModelResponse)
        model_response.content = "Response"
        model_response.model_name = "test-model"
        model_response.tokens_used = 100
        model_response.latency_ms = 500

        result = Mock(spec=EvaluationResult)
        result.test_case = test_case
        result.model_response = model_response
        result.overall_score = overall_score
        result.passed = overall_score >= 0.5
        result.ragas_evaluation = None
        result.evaluation_mode = None

        return result

    def test_normalization_single_category(self):
        """Single category (B3, weight 0.25): score should be category avg, not avg * weight.

        Bug: Without normalization, score = 0.6 * 0.25 = 0.15.
        Fixed: score = (0.6 * 0.25) / 0.25 = 0.6.
        """
        results = [
            self._make_result("B3", 0.6),
            self._make_result("B3", 0.6),
        ]

        score = self.use_case._calculate_category_weighted_score(results)

        # Should equal category average (0.6), not 0.6 * 0.25 = 0.15
        assert abs(score - 0.6) < 0.001

    def test_normalization_two_categories(self):
        """Two categories: B1 (weight 0.25) and B21 (weight 0.20).

        Expected: weighted_sum / total_weight = (0.8*0.25 + 0.5*0.20) / 0.45
        """
        results = [
            self._make_result("B1", 0.8),
            self._make_result("B21", 0.5),
        ]

        score = self.use_case._calculate_category_weighted_score(results)

        expected = (0.8 * 0.25 + 0.5 * 0.20) / (0.25 + 0.20)
        assert abs(score - expected) < 0.001

    def test_normalization_all_five_categories(self):
        """All 5 categories present: weights sum to 1.0, so normalization has no effect."""
        results = [
            self._make_result("B1", 0.8),   # Regulatory (0.25)
            self._make_result("B6", 0.7),   # Compliance (0.25)
            self._make_result("B13", 0.9),  # Remediation (0.20)
            self._make_result("B17", 0.6),  # Governance (0.10)
            self._make_result("B20", 0.5),  # Safety (0.20)
        ]

        score = self.use_case._calculate_category_weighted_score(results)

        expected = (0.8 * 0.25 + 0.7 * 0.25 + 0.9 * 0.20 + 0.6 * 0.10 + 0.5 * 0.20) / 1.0
        assert abs(score - expected) < 0.001


class TestTripleOverallScores:
    """Test per-test and summary-level triple overall scores (Benchmark, RAGAs, Combined)."""

    def setup_method(self):
        """Setup test fixtures."""
        self.model_gateway = Mock()
        self.test_case_repository = Mock()
        self.result_repository = Mock()
        self.logger = Mock()

        self.use_case = EvaluateModelUseCase(
            self.model_gateway,
            self.test_case_repository,
            self.result_repository,
            self.logger
        )

    def _make_ragas_evaluation(
        self,
        factual_precision: float = 0.8,
        factual_recall: float = 0.7,
        answer_relevancy: float = 0.8,
        semantic_similarity: float = 0.9,
        error: bool = False,
    ):
        """Create a mock RagasEvaluation with factual_precision, factual_recall, answer_relevancy, semantic_similarity."""
        from domain.services.ragas_evaluation_service import RagasMetricScore, RagasEvaluation

        if error:
            return RagasEvaluation(
                metrics=[],
                is_rag_response=False,
                evaluation_error=True,
                error_message="Test error",
            )

        metrics = [
            RagasMetricScore(name="factual_precision", score=factual_precision, applicable=True),
            RagasMetricScore(name="factual_recall", score=factual_recall, applicable=True),
            RagasMetricScore(name="answer_relevancy", score=answer_relevancy, applicable=True),
            RagasMetricScore(name="semantic_similarity", score=semantic_similarity, applicable=True),
        ]
        return RagasEvaluation(
            metrics=metrics,
            is_rag_response=False,
            evaluation_error=False,
        )

    def _make_result(
        self,
        benchmark_short_name: str,
        overall_score: float,
        ragas_eval=None,
    ) -> EvaluationResult:
        """Create a mock EvaluationResult with optional RAGAs evaluation."""
        test_case = Mock(spec=TestCase)
        test_case.benchmark_type = Mock()
        test_case.benchmark_type.short_name = benchmark_short_name
        test_case.benchmark_type.value = f"{benchmark_short_name}_Test"
        test_case.test_id = f"{benchmark_short_name}-001"
        test_case.question = "Test question"
        test_case.difficulty = Mock()
        test_case.difficulty.value = "medium"
        test_case.get_passing_threshold = Mock(return_value=0.15)

        model_response = Mock(spec=ModelResponse)
        model_response.content = "Response"
        model_response.model_name = "test-model"
        model_response.tokens_used = 100
        model_response.latency_ms = 500
        model_response.prompt_tokens = 0
        model_response.completion_tokens = 0
        model_response.total_tokens = 0

        result = Mock(spec=EvaluationResult)
        result.test_case = test_case
        result.model_response = model_response
        result.overall_score = overall_score
        result.passed = overall_score >= 0.5
        result.evaluator_notes = ""
        result.evaluated_at = datetime.now()
        result.metadata = {}
        result.metrics = []
        result.result_id = uuid4()
        result.ragas_evaluation = ragas_eval
        result.evaluation_mode = "hybrid"
        result.retrieved_chunk_ids = None
        result.chunk_count = None
        result.system_prompt = None
        result.user_prompt = None
        result.retrieved_contexts_detailed = None

        # Mock ragas_composite_score property
        if ragas_eval and not ragas_eval.evaluation_error:
            metrics_dict = {m.name: m.score for m in ragas_eval.metrics if m.applicable}
            factual_precision = metrics_dict.get("factual_precision")
            factual_recall = metrics_dict.get("factual_recall")
            answer_relevancy = metrics_dict.get("answer_relevancy")
            if factual_precision is not None and factual_recall is not None and answer_relevancy is not None:
                w = 1.0 / 3.0
                base_score = w * factual_recall + w * factual_precision + w * answer_relevancy
                result.ragas_composite_score = base_score * factual_precision
            else:
                result.ragas_composite_score = None
        else:
            result.ragas_composite_score = None

        return result

    # --- _extract_ragas_score tests ---

    def test_extract_ragas_score_with_multiplicative_formula(self):
        """RAGAs score should use multiplicative penalty: base_score * factual_precision."""
        ragas_eval = self._make_ragas_evaluation(
            factual_precision=0.9,
            factual_recall=0.7,
            answer_relevancy=0.8,
        )
        result = self._make_result("B3", 0.33, ragas_eval=ragas_eval)

        score = self.use_case._extract_ragas_score(result)

        # base_score = (0.7 + 0.9 + 0.8) / 3 = 0.8
        # ragas_score = 0.8 * 0.9 = 0.72
        assert abs(score - 0.72) < 0.001

    def test_extract_ragas_score_hallucinating_response(self):
        """Hallucinating response (low precision) should score dramatically lower."""
        ragas_eval = self._make_ragas_evaluation(
            factual_precision=0.2,
            factual_recall=0.8,
            answer_relevancy=0.7,
        )
        result = self._make_result("B3", 0.33, ragas_eval=ragas_eval)

        score = self.use_case._extract_ragas_score(result)

        # base_score = (0.8 + 0.2 + 0.7) / 3 = 0.5667
        # ragas_score = 0.5667 * 0.2 = 0.1133
        assert score < 0.15  # Much lower than grounded response

    def test_extract_ragas_score_grounded_vs_hallucinating(self):
        """Grounded response must score dramatically higher than hallucinating one."""
        grounded = self._make_ragas_evaluation(factual_precision=0.9, factual_recall=0.8, answer_relevancy=0.85)
        hallucinating = self._make_ragas_evaluation(factual_precision=0.2, factual_recall=0.8, answer_relevancy=0.85)

        grounded_result = self._make_result("B3", 0.33, ragas_eval=grounded)
        hallucinating_result = self._make_result("B3", 0.33, ragas_eval=hallucinating)

        grounded_score = self.use_case._extract_ragas_score(grounded_result)
        hallucinating_score = self.use_case._extract_ragas_score(hallucinating_result)

        # Grounded should be at least 3x higher
        assert grounded_score > hallucinating_score * 3

    def test_extract_ragas_score_returns_none_when_no_ragas(self):
        """RAGAs score should be None when no RAGAs evaluation."""
        result = self._make_result("B3", 0.33, ragas_eval=None)

        score = self.use_case._extract_ragas_score(result)

        assert score is None

    def test_extract_ragas_score_returns_none_on_error(self):
        """RAGAs score should be None when RAGAs evaluation errored."""
        ragas_eval = self._make_ragas_evaluation(error=True)
        result = self._make_result("B3", 0.33, ragas_eval=ragas_eval)

        score = self.use_case._extract_ragas_score(result)

        assert score is None

    # --- Per-test DTO population tests ---

    def test_result_dto_has_dual_scores(self):
        """EvaluationResultDTO should carry benchmark and RAGAs scores (no combined_score)."""
        ragas_eval = self._make_ragas_evaluation(
            factual_precision=0.9,
            factual_recall=0.7,
            answer_relevancy=0.8,
        )
        result = self._make_result("B3", 0.33, ragas_eval=ragas_eval)

        dto = self.use_case._result_to_dto(result)

        assert dto.overall_score == 0.33
        # base = (0.7 + 0.9 + 0.8)/3 = 0.8, ragas = 0.8 * 0.9 = 0.72
        assert abs(dto.ragas_score - 0.72) < 0.001
        assert not hasattr(dto, 'combined_score') or dto.combined_score is None

    def test_result_dto_none_scores_without_ragas(self):
        """DTO should have None ragas_score without RAGAs."""
        result = self._make_result("B3", 0.33, ragas_eval=None)

        dto = self.use_case._result_to_dto(result)

        assert dto.overall_score == 0.33
        assert dto.ragas_score is None

    # --- Summary-level dual score tests ---

    def test_summary_has_dual_scores(self):
        """Summary should carry ragas_overall_score (no combined_overall_score)."""
        ragas_eval = self._make_ragas_evaluation(
            factual_precision=0.9,
            factual_recall=0.7,
            answer_relevancy=0.8,
        )
        results = [self._make_result("B3", 0.33, ragas_eval=ragas_eval)]

        summary = self.use_case._generate_summary(
            "test-model", results, datetime.now(), datetime.now()
        )

        assert summary.overall_score is not None
        # base = (0.7 + 0.9 + 0.8)/3 = 0.8, ragas = 0.8 * 0.9 = 0.72
        assert abs(summary.ragas_overall_score - 0.72) < 0.001
        assert not hasattr(summary, 'combined_overall_score') or summary.combined_overall_score is None

    def test_summary_none_ragas_when_no_ragas(self):
        """Summary should have None RAGAs score when no RAGAs."""
        results = [self._make_result("B3", 0.33, ragas_eval=None)]

        summary = self.use_case._generate_summary(
            "test-model", results, datetime.now(), datetime.now()
        )

        assert summary.ragas_overall_score is None

    # --- Category-weighted RAGAs score tests ---

    def test_category_weighted_ragas_single_category(self):
        """Category-weighted RAGAs score with single category normalizes correctly."""
        ragas_eval1 = self._make_ragas_evaluation(factual_precision=0.9, factual_recall=0.7, answer_relevancy=0.8)
        ragas_eval2 = self._make_ragas_evaluation(factual_precision=0.85, factual_recall=0.65, answer_relevancy=0.75)
        results = [
            self._make_result("B3", 0.33, ragas_eval=ragas_eval1),
            self._make_result("B3", 0.33, ragas_eval=ragas_eval2),
        ]

        score = self.use_case._calculate_category_weighted_ragas_score(results)

        # ragas1: base = (0.7+0.9+0.8)/3 = 0.8, score = 0.8*0.9 = 0.72
        # ragas2: base = (0.65+0.85+0.75)/3 = 0.75, score = 0.75*0.85 = 0.6375
        # avg = (0.72 + 0.6375) / 2 = 0.67875
        assert abs(score - 0.67875) < 0.001

    def test_category_weighted_ragas_two_categories(self):
        """Category-weighted RAGAs score with two categories uses proper weighting."""
        ragas_b1 = self._make_ragas_evaluation(factual_precision=0.9, factual_recall=0.8, answer_relevancy=0.85)
        ragas_b21 = self._make_ragas_evaluation(factual_precision=0.6, factual_recall=0.7, answer_relevancy=0.65)
        results = [
            self._make_result("B1", 0.33, ragas_eval=ragas_b1),  # Regulatory (0.25)
            self._make_result("B21", 0.33, ragas_eval=ragas_b21),  # Safety (0.20)
        ]

        score = self.use_case._calculate_category_weighted_ragas_score(results)

        # B1: base = (0.8+0.9+0.85)/3 = 0.85, score = 0.85*0.9 = 0.765
        # B21: base = (0.7+0.6+0.65)/3 = 0.65, score = 0.65*0.6 = 0.39
        expected = (0.765 * 0.25 + 0.39 * 0.20) / (0.25 + 0.20)
        assert abs(score - expected) < 0.001

    def test_category_weighted_ragas_empty(self):
        """Category-weighted RAGAs score returns None for empty results."""
        score = self.use_case._calculate_category_weighted_ragas_score([])

        assert score is None

    def test_category_weighted_ragas_all_errors(self):
        """Category-weighted RAGAs score returns None when all RAGAs errored."""
        ragas_eval = self._make_ragas_evaluation(error=True)
        results = [self._make_result("B3", 0.33, ragas_eval=ragas_eval)]

        score = self.use_case._calculate_category_weighted_ragas_score(results)

        assert score is None

    # --- Metadata dual scores ---

    def test_metadata_includes_dual_scores(self):
        """Metadata should include overall_score and ragas_overall_score (no combined_overall_score)."""
        request = EvaluationRequestDTO(
            model_name="test-model",
            benchmark_types=["B1"],
            evaluation_phase="baseline"
        )

        summary = EvaluationSummaryDTO(
            model_name="test-model",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            overall_score=0.33,
            ragas_overall_score=0.72,
            by_benchmark={},
            by_difficulty={},
            evaluation_started_at=datetime.now(),
            evaluation_completed_at=datetime.now(),
            total_duration_seconds=10.0,
            results=[]
        )

        metadata = self.use_case._build_evaluation_metadata(
            request, summary, datetime.now(), datetime.now()
        )

        assert metadata["overall_score"] == 0.33
        assert metadata["ragas_overall_score"] == 0.72
        assert "combined_overall_score" not in metadata


class TestMetadataSchemaV6Fields:
    """Test schema-v6 fields (run_id, schema_version) are present in metadata."""

    def setup_method(self):
        self.model_gateway = Mock()
        self.test_case_repository = Mock()
        self.result_repository = Mock()
        self.logger = Mock()

        self.use_case = EvaluateModelUseCase(
            self.model_gateway,
            self.test_case_repository,
            self.result_repository,
            self.logger
        )

    def test_metadata_includes_run_id(self):
        """Metadata must include run_id (schema v6 marker)."""
        request = EvaluationRequestDTO(
            model_name="primus-reasoning",
            benchmark_types=["B3"],
            evaluation_phase="baseline",
            run_id="eval-run-llm-only-benchmark-B3-20260421-1430",
        )

        summary = EvaluationSummaryDTO(
            model_name="primus-reasoning",
            total_tests=5,
            passed_tests=4,
            failed_tests=1,
            overall_score=0.8,
            by_benchmark={},
            by_difficulty={},
            evaluation_started_at=datetime.now(),
            evaluation_completed_at=datetime.now(),
            total_duration_seconds=30.0,
            results=[],
        )

        metadata = self.use_case._build_evaluation_metadata(
            request, summary, datetime.now(), datetime.now()
        )

        assert "run_id" in metadata
        assert metadata["run_id"] == "eval-run-llm-only-benchmark-B3-20260421-1430"

    def test_metadata_includes_schema_version_6(self):
        """Metadata must include schema_version=6."""
        request = EvaluationRequestDTO(
            model_name="primus-reasoning",
            benchmark_types=["B3"],
            evaluation_phase="baseline",
        )

        summary = EvaluationSummaryDTO(
            model_name="primus-reasoning",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            overall_score=0.8,
            by_benchmark={},
            by_difficulty={},
            evaluation_started_at=datetime.now(),
            evaluation_completed_at=datetime.now(),
            total_duration_seconds=10.0,
            results=[],
        )

        metadata = self.use_case._build_evaluation_metadata(
            request, summary, datetime.now(), datetime.now()
        )

        assert metadata.get("schema_version") == 6


class TestSaveEvaluationRunSignature:
    """Test the repository save_evaluation_run signature expectations."""

    def setup_method(self):
        self.model_gateway = Mock()
        self.test_case_repository = Mock()
        self.result_repository = Mock()
        self.result_repository.save_evaluation_run = AsyncMock(return_value="/tmp/run.json")
        self.logger = Mock()

        self.use_case = EvaluateModelUseCase(
            self.model_gateway,
            self.test_case_repository,
            self.result_repository,
            self.logger
        )

    def test_save_evaluation_run_called_with_contexts_by_test_id_kwarg(self):
        """save_evaluation_run must be called with contexts_by_test_id= keyword arg."""
        import inspect
        from application.ports.output.i_result_repository import IResultRepository

        # Verify the abstract method signature includes contexts_by_test_id
        sig = inspect.signature(IResultRepository.save_evaluation_run)
        assert "contexts_by_test_id" in sig.parameters

    def test_save_evaluation_run_contexts_kwarg_is_optional(self):
        """contexts_by_test_id must be optional (has default None)."""
        import inspect
        from application.ports.output.i_result_repository import IResultRepository

        sig = inspect.signature(IResultRepository.save_evaluation_run)
        param = sig.parameters["contexts_by_test_id"]
        assert param.default is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
