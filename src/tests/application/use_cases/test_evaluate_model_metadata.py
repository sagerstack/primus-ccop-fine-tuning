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
from application.dtos.evaluation_summary_dto import EvaluationSummaryDTO
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
                benchmark="B1_CCoP_Applicability_Scope",
                model="test-model",
                response="Response",
                score=0.8,
                passed=True,
                metrics=[],
                tokens=100,
                latency_ms=1000,
                evaluated_at=datetime.now().isoformat()
            ),
            EvaluationResultDTO(
                result_id=str(uuid4()),
                test_id="B2-001",
                benchmark="B2_Compliance_Classification_Accuracy",
                model="test-model",
                response="Response",
                score=0.9,
                passed=True,
                metrics=[],
                tokens=100,
                latency_ms=1000,
                evaluated_at=datetime.now().isoformat()
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
                benchmark="B1_CCoP_Applicability_Scope",
                model="test-model",
                response="Response",
                score=0.6,
                passed=True,
                metrics=[],
                tokens=100,
                latency_ms=1000,
                evaluated_at=datetime.now().isoformat()
            ),
            EvaluationResultDTO(
                result_id=str(uuid4()),
                test_id="B1-002",
                benchmark="B1_CCoP_Applicability_Scope",
                model="test-model",
                response="Response",
                score=0.8,
                passed=True,
                metrics=[],
                tokens=100,
                latency_ms=1000,
                evaluated_at=datetime.now().isoformat()
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
                benchmark="B1_CCoP_Applicability_Scope",
                model="test-model",
                response="Response",
                score=0.8,
                passed=True,
                metrics=[],
                tokens=100,
                latency_ms=1000,
                evaluated_at=datetime.now().isoformat()
            ),
            # Safety category (B21)
            EvaluationResultDTO(
                result_id=str(uuid4()),
                test_id="B21-001",
                benchmark="B21_Hallucination_Rate",
                model="test-model",
                response="Response",
                score=0.5,
                passed=True,
                metrics=[],
                tokens=100,
                latency_ms=1000,
                evaluated_at=datetime.now().isoformat()
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
        assert safety["weight"] == 0.10

    def test_category_scores_empty_results(self):
        """Test category scores with empty results."""
        category_scores = self.use_case._calculate_category_scores([])

        # Should return empty dict
        assert category_scores == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
