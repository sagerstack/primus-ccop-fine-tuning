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

        # Metadata (schema v6: run_id required)
        metadata = {
            "run_id": "eval-run-hybrid-benchmark-B1-20260421-1430",
            "schema_version": 6,
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

        # Verify file was created under monthly dir with v6 filename format
        assert Path(filepath).exists()
        assert "eval-run-hybrid-benchmark-B1-20260421-1430" in filepath
        assert "test-model" in filepath

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
            "run_id": "eval-run-hybrid-benchmark-B1-20260421-1430",
            "schema_version": 6,
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
            "run_id": "eval-run-hybrid-benchmark-B1-20260421-1430",
            "schema_version": 6,
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


class TestSchemaV6MonthlyDir:
    """Test schema v6 monthly-directory layout and per-run filenames."""

    def setup_method(self):
        self.logger = Mock()
        self.temp_dir = Path("/tmp/test_results_v6")
        self.temp_dir.mkdir(exist_ok=True)
        self.repo = JSONResultRepository(self.temp_dir, self.logger)

    def test_generate_filename_v6_with_run_id(self):
        """v6 filename = {run_id}-{model}.json."""
        metadata = {
            "run_id": "eval-run-hybrid-benchmark-B3-20260421-1430",
            "model_name": "primus-reasoning",
        }
        filename = self.repo._generate_filename_v6(metadata)
        assert filename == "eval-run-hybrid-benchmark-B3-20260421-1430-primus-reasoning.json"

    def test_generate_filename_v6_raises_without_run_id(self):
        """v6 filename generation raises ValueError when run_id is missing."""
        with pytest.raises(ValueError, match="run_id is required"):
            self.repo._generate_filename_v6({"model_name": "primus-reasoning"})

    def test_monthly_dir_creates_correct_structure(self):
        """monthly_dir creates yyyy-MM subdirectory under results_dir."""
        month_dir = self.repo._monthly_dir("2026-04-21T14:30:00")
        expected = self.temp_dir / "2026-04"
        assert month_dir == expected
        assert month_dir.exists()

    def test_monthly_dir_fallback_on_empty_timestamp(self):
        """monthly_dir uses utcnow() when timestamp is empty."""
        month_dir = self.repo._monthly_dir("")
        # Should be a yyyy-MM directory (current month)
        assert month_dir.parent == self.temp_dir
        assert len(month_dir.name) == 7  # "yyyy-MM"

    @pytest.mark.asyncio
    async def test_save_evaluation_run_lands_in_monthly_dir(self):
        """save_evaluation_run writes file inside {yyyy-MM}/ subdir."""
        test_case = TestCase(
            test_id="B3-001",
            benchmark_type=BenchmarkType.from_string("B3"),
            section="Test",
            clause_reference="5.1",
            difficulty=DifficultyLevel.MEDIUM,
            question="What are the multi-factor authentication requirements under Singapore CCoP 2.0 for CII owners?",
            expected_response="MFA is mandatory for all privileged accounts under CCoP 2.0.",
            evaluation_criteria={},
            metadata={},
        )
        model_response = ModelResponse(
            content="MFA is required.",
            model_name="primus-reasoning",
            tokens_used=50,
            latency_ms=200,
        )
        result = EvaluationResult(
            test_case=test_case,
            model_response=model_response,
            metrics=[accuracy_metric(0.9)],
        )
        result.calculate_overall_score()

        metadata = {
            "run_id": "eval-run-hybrid-benchmark-B3-20260421-1430",
            "schema_version": 6,
            "model_name": "primus-reasoning",
            "evaluated_at": "2026-04-21T14:30:00",
        }
        filepath = await self.repo.save_evaluation_run([result], metadata)

        assert "2026-04" in filepath
        assert "eval-run-hybrid-benchmark-B3-20260421-1430" in filepath
        assert "primus-reasoning" in filepath
        assert Path(filepath).exists()

    @pytest.mark.asyncio
    async def test_save_evaluation_run_writes_sidecar_contexts(self):
        """save_evaluation_run writes {run_id}-contexts.json sidecar when contexts provided."""
        test_case = TestCase(
            test_id="B3-001",
            benchmark_type=BenchmarkType.from_string("B3"),
            section="Test",
            clause_reference="5.1",
            difficulty=DifficultyLevel.MEDIUM,
            question="What access control requirements apply under CCoP 2.0?",
            expected_response="Least privilege must be enforced.",
            evaluation_criteria={},
            metadata={},
        )
        model_response = ModelResponse(
            content="Least privilege is required.",
            model_name="primus-reasoning",
            tokens_used=40,
            latency_ms=150,
        )
        result = EvaluationResult(
            test_case=test_case,
            model_response=model_response,
            metrics=[accuracy_metric(0.85)],
        )
        result.calculate_overall_score()

        run_id = "eval-run-hybrid-benchmark-B3-20260421-1430"
        metadata = {
            "run_id": run_id,
            "schema_version": 6,
            "model_name": "primus-reasoning",
            "evaluated_at": "2026-04-21T14:30:00",
        }
        contexts = {"B3-001": [{"text": "CCoP clause 5.2.1", "citation_id": "c1", "score": 0.95}]}
        filepath = await self.repo.save_evaluation_run([result], metadata, contexts_by_test_id=contexts)

        month_dir = Path(filepath).parent
        sidecar = month_dir / f"{run_id}-contexts.json"
        assert sidecar.exists()
        with open(sidecar) as f:
            data = json.load(f)
        assert "B3-001" in data
        assert data["B3-001"][0]["citation_id"] == "c1"

    @pytest.mark.asyncio
    async def test_save_evaluation_run_result_has_v6_fields(self):
        """Serialized test_results entries include system_prompt, user_prompt, token counts."""
        test_case = TestCase(
            test_id="B1-001",
            benchmark_type=BenchmarkType.from_string("B1"),
            section="Test",
            clause_reference="3.1",
            difficulty=DifficultyLevel.LOW,
            question="Does Singapore CCoP 2.0 apply to financial sector critical information infrastructure owners?",
            expected_response="Yes, all CII owners in the financial sector must comply with CCoP 2.0.",
            evaluation_criteria={},
            metadata={},
        )
        model_response = ModelResponse(
            content="Yes.",
            model_name="primus-reasoning",
            tokens_used=10,
            prompt_tokens=8,
            completion_tokens=2,
            total_tokens=10,
            latency_ms=100,
        )
        result = EvaluationResult(
            test_case=test_case,
            model_response=model_response,
            metrics=[accuracy_metric(1.0)],
            system_prompt="You are a CCoP compliance expert.",
            user_prompt="Does CCoP 2.0 apply to financial sector CIIs?",
        )
        result.calculate_overall_score()

        metadata = {
            "run_id": "eval-run-llm-only-benchmark-B1-20260421-1430",
            "schema_version": 6,
            "model_name": "primus-reasoning",
            "evaluated_at": "2026-04-21T14:30:00",
        }
        filepath = await self.repo.save_evaluation_run([result], metadata)

        with open(filepath) as f:
            data = json.load(f)

        entry = data["test_results"][0]
        assert entry["system_prompt"] == "You are a CCoP compliance expert."
        assert entry["user_prompt"] == "Does CCoP 2.0 apply to financial sector CIIs?"
        assert entry["prompt_tokens"] == 8
        assert entry["completion_tokens"] == 2
        assert entry["total_tokens"] == 10

    @pytest.mark.asyncio
    async def test_save_batch_is_noop(self):
        """save_batch produces no file output (schema v6 deprecation)."""
        import os
        files_before = set(os.listdir(self.temp_dir))
        await self.repo.save_batch([])
        files_after = set(os.listdir(self.temp_dir))
        assert files_before == files_after


class TestSaveQueryRun:
    """Test save_query_run — new method for persisting ad-hoc query results."""

    def setup_method(self):
        self.logger = Mock()
        self.temp_dir = Path("/tmp/test_query_results")
        self.temp_dir.mkdir(exist_ok=True)
        self.repo = JSONResultRepository(self.temp_dir, self.logger)

    @pytest.mark.asyncio
    async def test_save_query_run_creates_monthly_file(self):
        """save_query_run writes {run_id}-{model}.json under {yyyy-MM}/."""
        run_id = "eval-run-hybrid-query-20260421-1430"
        metadata = {
            "run_id": run_id,
            "schema_version": 6,
            "model_name": "primus-reasoning",
            "evaluation_mode": "hybrid",
            "evaluated_at": "2026-04-21T14:30:00",
            "question": "What are the CCoP 2.0 incident response requirements?",
            "is_rag_augmented": True,
        }
        test_results = [{
            "test_id": f"query-{run_id}",
            "question": "What are the CCoP 2.0 incident response requirements?",
            "response": "CII owners must notify MCI within 2 hours of a cyber incident.",
            "is_rag_augmented": True,
        }]

        path = await self.repo.save_query_run(metadata=metadata, test_results=test_results)

        assert "2026-04" in path
        assert run_id in path
        assert "primus-reasoning" in path
        assert Path(path).exists()

    @pytest.mark.asyncio
    async def test_save_query_run_file_structure(self):
        """Saved query JSON has metadata and test_results keys."""
        run_id = "eval-run-llm-only-query-20260421-1445"
        metadata = {
            "run_id": run_id,
            "schema_version": 6,
            "model_name": "primus-reasoning",
            "evaluation_mode": "llm-only",
            "evaluated_at": "2026-04-21T14:45:00",
            "question": "What is CCoP 2.0?",
            "is_rag_augmented": False,
        }
        test_results = [{"test_id": f"query-{run_id}", "question": "What is CCoP 2.0?", "response": "CCoP stands for..."}]

        path = await self.repo.save_query_run(metadata=metadata, test_results=test_results)

        with open(path) as f:
            data = json.load(f)

        assert "metadata" in data
        assert "test_results" in data
        assert data["metadata"]["run_id"] == run_id
        assert data["metadata"]["schema_version"] == 6
        assert len(data["test_results"]) == 1

    @pytest.mark.asyncio
    async def test_save_query_run_writes_contexts_sidecar(self):
        """save_query_run writes sidecar contexts JSON when contexts provided."""
        run_id = "eval-run-hybrid-query-20260421-1500"
        metadata = {
            "run_id": run_id,
            "schema_version": 6,
            "model_name": "primus-reasoning",
            "evaluation_mode": "hybrid",
            "evaluated_at": "2026-04-21T15:00:00",
            "question": "What logging must CII owners maintain?",
            "is_rag_augmented": True,
        }
        query_test_id = f"query-{run_id}"
        test_results = [{"test_id": query_test_id, "question": "What logging must CII owners maintain?", "response": "Audit logs..."}]
        contexts_by_test_id = {
            query_test_id: [{"text": "CCoP clause 8.1 logging", "citation_id": "c2", "score": 0.88}]
        }

        path = await self.repo.save_query_run(
            metadata=metadata,
            test_results=test_results,
            contexts_by_test_id=contexts_by_test_id,
        )

        month_dir = Path(path).parent
        sidecar = month_dir / f"{run_id}-contexts.json"
        assert sidecar.exists()
        with open(sidecar) as f:
            data = json.load(f)
        assert query_test_id in data
        assert data[query_test_id][0]["citation_id"] == "c2"

    @pytest.mark.asyncio
    async def test_save_query_run_no_sidecar_when_no_contexts(self):
        """save_query_run does not write sidecar when contexts_by_test_id is None."""
        import os
        run_id = "eval-run-llm-only-query-20260421-1515"
        metadata = {
            "run_id": run_id,
            "schema_version": 6,
            "model_name": "primus-reasoning",
            "evaluation_mode": "llm-only",
            "evaluated_at": "2026-04-21T15:15:00",
            "question": "What is a CII?",
            "is_rag_augmented": False,
        }
        test_results = [{"test_id": f"query-{run_id}", "question": "What is a CII?", "response": "CII is..."}]

        path = await self.repo.save_query_run(metadata=metadata, test_results=test_results, contexts_by_test_id=None)

        month_dir = Path(path).parent
        sidecar = month_dir / f"{run_id}-contexts.json"
        assert not sidecar.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
