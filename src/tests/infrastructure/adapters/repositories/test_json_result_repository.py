"""
Tests for JSON Result Repository enhancements.

Tests the new functionality:
1. Per-run result files with parameterized naming
2. Question field in test results
3. Metadata section with benchmark and category scores
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

from domain.entities.evaluation_result import EvaluationResult
from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.difficulty_level import DifficultyLevel
from domain.value_objects.evaluation_metric import (
    EvaluationMetric,
    accuracy_metric,
    completeness_metric
)
from infrastructure.adapters.repositories.json_result_repository import JSONResultRepository


class TestFilenameGeneration:
    """Test filename generation with different parameter combinations."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = Mock()
        self.temp_dir = Path("/tmp/test_results")
        self.temp_dir.mkdir(exist_ok=True)
        self.repo = JSONResultRepository(self.temp_dir, self.logger)

    def test_filename_with_all_parameters(self):
        """Test filename generation with all parameters."""
        metadata = {
            "model_name": "primus-reasoning",
            "evaluation_phase": "baseline",
            "tier": 1,
            "benchmarks": ["B1", "B2", "B21"],
            "evaluated_at": "2024-12-14T14:40:00"
        }

        filename = self.repo._generate_filename(metadata)

        assert filename.startswith("result-primus-reasoning")
        assert "phase-baseline" in filename
        assert "tier-1" in filename
        assert "benchmarks-3" in filename
        assert filename.endswith(".json")
        assert "20241214" in filename  # Date format

    def test_filename_with_single_benchmark(self):
        """Test filename with single benchmark."""
        metadata = {
            "model_name": "test-model",
            "benchmarks": ["B1"],
            "evaluated_at": "2024-12-14T14:40:00"
        }

        filename = self.repo._generate_filename(metadata)

        assert "benchmark-B1" in filename
        assert "benchmarks-" not in filename  # Should not say "benchmarks-1"

    def test_filename_without_optional_parameters(self):
        """Test filename without phase and tier."""
        metadata = {
            "model_name": "test-model",
            "evaluated_at": "2024-12-14T14:40:00"
        }

        filename = self.repo._generate_filename(metadata)

        assert filename.startswith("result-test-model")
        assert "phase-" not in filename
        assert "tier-" not in filename
        assert filename.endswith(".json")

    def test_filename_timestamp_format(self):
        """Test timestamp is in correct format (yyyymmdd-HHMM)."""
        metadata = {
            "model_name": "test-model",
            "evaluated_at": "2024-12-14T15:30:45.123456"
        }

        filename = self.repo._generate_filename(metadata)

        # Should contain date and time in format: 20241214-1530
        assert "20241214-1530" in filename


class TestSerializationWithQuestion:
    """Test serialization includes question field."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = Mock()
        self.temp_dir = Path("/tmp/test_results")
        self.temp_dir.mkdir(exist_ok=True)
        self.repo = JSONResultRepository(self.temp_dir, self.logger)

    def test_serialization_includes_question(self):
        """Test that serialized result includes question field."""
        # Create test case
        test_case = TestCase(
            test_id="B1-001",
            benchmark_type=BenchmarkType.from_string("B1"),
            section="Test Section",
            clause_reference="5.1",
            difficulty=DifficultyLevel.MEDIUM,
            question="What are the specific cybersecurity requirements for this test case scenario?",
            expected_response="Expected answer",
            evaluation_criteria={"accuracy": "Must be correct"},
            metadata={}
        )

        # Create model response
        model_response = ModelResponse(
            content="Test response",
            model_name="test-model",
            tokens_used=100,
            latency_ms=1000
        )

        # Create evaluation result
        result = EvaluationResult(
            test_case=test_case,
            model_response=model_response,
            metrics=[
                accuracy_metric(0.8),
                completeness_metric(0.9)
            ]
        )
        result.calculate_overall_score()

        # Serialize with question
        serialized = self.repo._serialize_with_question(result)

        # Verify question is included
        assert "question" in serialized
        assert serialized["question"] == "What are the specific cybersecurity requirements for this test case scenario?"
        assert serialized["test_id"] == "B1-001"
        assert serialized["response"] == "Test response"

    def test_serialization_has_all_fields(self):
        """Test that serialization includes all required fields."""
        test_case = TestCase(
            test_id="B2-001",
            benchmark_type=BenchmarkType.from_string("B2"),
            section="Test",
            clause_reference="5.1",
            difficulty=DifficultyLevel.HIGH,
            question="What are the compliance classification requirements for CCoP 2.0 in this scenario?",
            expected_response="Answer",
            evaluation_criteria={"accuracy": "Must be correct"},
            metadata={}
        )

        model_response = ModelResponse(
            content="Response",
            model_name="model",
            tokens_used=50,
            latency_ms=500
        )

        result = EvaluationResult(
            test_case=test_case,
            model_response=model_response,
            metrics=[accuracy_metric(1.0)]
        )
        result.calculate_overall_score()

        serialized = self.repo._serialize_with_question(result)

        # Check all fields present
        expected_fields = [
            "result_id", "test_id", "benchmark", "model", "response",
            "score", "passed", "metrics", "tokens", "latency_ms",
            "evaluated_at", "question"
        ]
        for field in expected_fields:
            assert field in serialized, f"Missing field: {field}"


class TestEvaluationRunSaving:
    """Test save_evaluation_run method."""

    def setup_method(self):
        """Setup test fixtures."""
        self.logger = Mock()
        self.temp_dir = Path("/tmp/test_results")
        self.temp_dir.mkdir(exist_ok=True)
        self.repo = JSONResultRepository(self.temp_dir, self.logger)

    @pytest.mark.asyncio
    async def test_save_evaluation_run_creates_file(self):
        """Test that save_evaluation_run creates a new file."""
        # Create test results
        test_case = TestCase(
            test_id="B1-001",
            benchmark_type=BenchmarkType.from_string("B1"),
            section="Test",
            clause_reference="5.1",
            difficulty=DifficultyLevel.MEDIUM,
            question="What are the compliance classification requirements for CCoP 2.0 in this scenario?",
            expected_response="Answer",
            evaluation_criteria={"accuracy": "Must be correct"},
            metadata={}
        )

        model_response = ModelResponse(
            content="Response",
            model_name="test-model",
            tokens_used=100,
            latency_ms=1000
        )

        result = EvaluationResult(
            test_case=test_case,
            model_response=model_response,
            metrics=[accuracy_metric(0.5)]
        )
        result.calculate_overall_score()

        # Metadata
        metadata = {
            "model_name": "test-model",
            "evaluation_phase": "baseline",
            "tier": 1,
            "benchmarks": ["B1"],
            "total_tests": 1,
            "passed_tests": 0,
            "failed_tests": 1,
            "overall_score": 0.5,
            "evaluated_at": datetime.now().isoformat()
        }

        # Save
        filepath = await self.repo.save_evaluation_run([result], metadata)

        # Verify file was created
        assert Path(filepath).exists()
        assert "result-test-model" in filepath
        assert "phase-baseline" in filepath
        assert "tier-1" in filepath

    @pytest.mark.asyncio
    async def test_save_evaluation_run_structure(self):
        """Test that saved file has correct structure with metadata and test_results."""
        test_case = TestCase(
            test_id="B1-001",
            benchmark_type=BenchmarkType.from_string("B1"),
            section="Test",
            clause_reference="5.1",
            difficulty=DifficultyLevel.MEDIUM,
            question="What are the key cybersecurity controls that must be implemented for this CII system?",
            expected_response="Answer",
            evaluation_criteria={"accuracy": "Must be correct"},
            metadata={}
        )

        model_response = ModelResponse(
            content="Response",
            model_name="test-model",
            tokens_used=100,
            latency_ms=1000
        )

        result = EvaluationResult(
            test_case=test_case,
            model_response=model_response,
            metrics=[
                accuracy_metric(0.8),
                completeness_metric(0.9),
                EvaluationMetric(name="grounding", value=1.0, weight=1.0)
            ]
        )
        result.calculate_overall_score()

        metadata = {
            "model_name": "test-model",
            "evaluation_phase": "baseline",
            "tier": 1,
            "benchmarks": ["B1"],
            "total_tests": 1,
            "benchmark_scores": {
                "B1_CCoP_Applicability_Scope": {
                    "total": 1,
                    "passed": 1,
                    "score": 0.85
                }
            },
            "category_scores": {
                "Regulatory Applicability & Interpretation": {
                    "average_score": 0.85,
                    "weight": 0.25,
                    "weighted_contribution": 0.2125
                }
            },
            "evaluated_at": datetime.now().isoformat()
        }

        filepath = await self.repo.save_evaluation_run([result], metadata)

        # Read and verify structure
        with open(filepath, "r") as f:
            data = json.load(f)

        # Check top-level structure
        assert "metadata" in data
        assert "test_results" in data

        # Check metadata
        assert data["metadata"]["model_name"] == "test-model"
        assert data["metadata"]["tier"] == 1
        assert "benchmark_scores" in data["metadata"]
        assert "category_scores" in data["metadata"]

        # Check test results
        assert len(data["test_results"]) == 1
        assert data["test_results"][0]["test_id"] == "B1-001"
        assert data["test_results"][0]["question"] == "What are the key cybersecurity controls that must be implemented for this CII system?"
        assert "metrics" in data["test_results"][0]

    @pytest.mark.asyncio
    async def test_save_multiple_results(self):
        """Test saving multiple test results in one run."""
        results = []
        for i in range(3):
            test_case = TestCase(
                test_id=f"B1-00{i+1}",
                benchmark_type=BenchmarkType.from_string("B1"),
                section="Test",
                clause_reference="5.1",
                difficulty=DifficultyLevel.MEDIUM,
                question=f"What are the CCoP 2.0 requirements for test scenario {i+1} regarding CII security controls?",
                expected_response="Answer",
                evaluation_criteria={"accuracy": "Must be correct"},
                metadata={}
            )

            model_response = ModelResponse(
                content=f"Response {i+1}",
                model_name="test-model",
                tokens_used=100,
                latency_ms=1000
            )

            result = EvaluationResult(
                test_case=test_case,
                model_response=model_response,
                metrics=[accuracy_metric(0.5 + i * 0.1)]
            )
            result.calculate_overall_score()
            results.append(result)

        metadata = {
            "model_name": "test-model",
            "benchmarks": ["B1"],
            "total_tests": 3,
            "evaluated_at": datetime.now().isoformat()
        }

        filepath = await self.repo.save_evaluation_run(results, metadata)

        # Read and verify
        with open(filepath, "r") as f:
            data = json.load(f)

        assert len(data["test_results"]) == 3
        for i, test_result in enumerate(data["test_results"]):
            assert test_result["test_id"] == f"B1-00{i+1}"
            assert test_result["question"] == f"What are the CCoP 2.0 requirements for test scenario {i+1} regarding CII security controls?"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
