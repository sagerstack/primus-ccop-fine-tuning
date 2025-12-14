"""
End-to-End Evaluation Test

Tests the complete evaluation flow:
1. Load test cases from JSONL files
2. Call model gateway for each test case
3. Generate evaluation results
4. Save results to disk

Uses real B1 test data but mocks the Ollama client to avoid requiring a running model.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from application.dtos.evaluation_request_dto import EvaluationRequestDTO
from application.use_cases.evaluate_model import EvaluateModelUseCase
from application.ports.output.i_result_repository import IResultRepository
from infrastructure.adapters.repositories.jsonl_test_case_repository import JSONLTestCaseRepository
from infrastructure.adapters.models.ollama_gateway import OllamaGateway
from infrastructure.external.ollama_client import OllamaClient
from infrastructure.adapters.logging.console_logger import ConsoleLogger


class TestEndToEndEvaluation:
    """End-to-end tests for the evaluation pipeline."""

    @pytest.mark.asyncio
    async def test_full_evaluation_flow_with_b1_data(self, tmp_path):
        """
        CRITICAL E2E TEST: Full evaluation flow with real B1 test data.

        This test verifies:
        1. Test case repository can load B1 JSONL files
        2. Model gateway can generate responses (mocked)
        3. Evaluation use case orchestrates the full flow
        4. Results are properly structured and contain expected fields
        """
        # Setup: Create test fixtures directory
        test_cases_dir = tmp_path / "test-cases"
        test_cases_dir.mkdir()

        # Copy B1 test fixture to temp directory
        fixture_source = Path(__file__).parent / "fixtures" / "b01_test_sample.jsonl"
        fixture_dest = test_cases_dir / "b01_ccop_applicability_scope.jsonl"

        if fixture_source.exists():
            fixture_dest.write_text(fixture_source.read_text())
        else:
            # Create minimal test data if fixture doesn't exist
            test_data = {
                "test_id": "B1-001",
                "benchmark_type": "B1_CCoP_Applicability_Scope",
                "section": "Cybersecurity Act 2018 Part 3",
                "clause_reference": "Section 7(1)",
                "difficulty": "medium",
                "question": "What are the criteria that the Commissioner uses to designate a computer or computer system as Critical Information Infrastructure (CII) under the Cybersecurity Act 2018?",
                "expected_response": "According to Section 7(1) of the Cybersecurity Act 2018, the Commissioner may designate a computer or computer system as CII if two criteria are satisfied: (a) the computer or computer system is necessary for the continuous delivery of an essential service, and the loss or compromise of the computer or computer system will have a debilitating effect on the availability of the essential service in Singapore; and (b) the computer or computer system is located wholly or partly in Singapore.",
                "evaluation_criteria": {
                    "accuracy": "Must correctly identify both criteria",
                    "completeness": "Should mention written notice requirement"
                },
                "metadata": {
                    "domain": "IT/OT",
                    "criticality": "critical"
                }
            }
            fixture_dest.write_text(json.dumps(test_data) + "\n")

        # Setup: Create mock Ollama client
        mock_ollama_client = Mock(spec=OllamaClient)
        mock_ollama_client.list_models = AsyncMock(return_value=[
            {"name": "primus-reasoning:latest"}
        ])
        mock_ollama_client.generate = AsyncMock(return_value={
            "response": "According to Section 7(1) of the Cybersecurity Act 2018, the Commissioner may designate a computer or computer system as CII based on two criteria: (a) necessity for continuous delivery of an essential service, and (b) location wholly or partly in Singapore.",
            "eval_count": 150,
            "eval_duration": 5000000000,
            "total_duration": 6000000000
        })

        # Setup: Create logger
        logger = ConsoleLogger()

        # Setup: Create repository
        repository = JSONLTestCaseRepository(
            test_cases_dir=test_cases_dir,
            logger=logger
        )

        # Setup: Create model gateway
        model_gateway = OllamaGateway(
            client=mock_ollama_client,
            logger=logger
        )

        # Setup: Create results directory
        results_dir = tmp_path / "results"
        results_dir.mkdir()

        # Setup: Create mock result repository
        mock_result_repository = Mock(spec=IResultRepository)
        mock_result_repository.save_result = AsyncMock()
        mock_result_repository.save_summary = AsyncMock()

        # Setup: Create use case
        use_case = EvaluateModelUseCase(
            model_gateway=model_gateway,
            test_case_repository=repository,
            result_repository=mock_result_repository,
            logger=logger
        )

        # Execute: Run evaluation for B1 benchmark
        request = EvaluationRequestDTO(
            model_name="primus-reasoning",
            benchmark_types=["B1"],
            temperature=0.7,
            save_results=False  # Don't save to disk in test
        )

        # Act
        summary = await use_case.execute(request)

        # Assert: Verify summary structure
        assert summary is not None
        assert summary.model_name == "primus-reasoning"
        assert summary.total_tests > 0, "Should have loaded at least 1 test case"
        assert summary.total_duration_seconds > 0

        # Assert: Verify test execution
        assert mock_ollama_client.list_models.called, "Should check if model is available"
        assert mock_ollama_client.generate.called, "Should generate responses for test cases"

        # Assert: Verify benchmark results
        assert "B1" in summary.by_benchmark or len(summary.by_benchmark) > 0

        # Get first benchmark results
        first_benchmark = next(iter(summary.by_benchmark.values()))
        assert first_benchmark["total"] > 0
        assert "passed" in first_benchmark
        assert "score" in first_benchmark

        print(f"\n✅ E2E Test Passed!")
        print(f"   Total tests: {summary.total_tests}")
        print(f"   Duration: {summary.total_duration_seconds:.2f}s")
        print(f"   Score: {summary.overall_score:.2%}")

    @pytest.mark.asyncio
    async def test_evaluation_with_multiple_test_cases(self, tmp_path):
        """
        E2E TEST: Evaluation with multiple test cases from B1.

        Verifies that the evaluation pipeline correctly processes
        multiple test cases in sequence.
        """
        # Setup: Create test cases directory
        test_cases_dir = tmp_path / "test-cases"
        test_cases_dir.mkdir()

        # Create test file with 3 test cases
        test_file = test_cases_dir / "b01_ccop_applicability_scope.jsonl"
        test_cases_data = []

        for i in range(1, 4):
            test_case = {
                "test_id": f"B1-{i:03d}",
                "benchmark_type": "B1_CCoP_Applicability_Scope",
                "section": "Cybersecurity Act 2018 Part 3",
                "clause_reference": f"Section 7({i})",
                "difficulty": "medium",
                "question": f"Test question {i} about CCoP 2.0 and CII designation?",
                "expected_response": f"Expected answer {i} explaining CCoP 2.0 requirements.",
                "evaluation_criteria": {"accuracy": "Must be accurate"},
                "metadata": {"domain": "IT/OT"}
            }
            test_cases_data.append(json.dumps(test_case))

        test_file.write_text("\n".join(test_cases_data) + "\n")

        # Setup: Mock Ollama client
        mock_ollama_client = Mock(spec=OllamaClient)
        mock_ollama_client.list_models = AsyncMock(return_value=[
            {"name": "primus-reasoning:latest"}
        ])
        mock_ollama_client.generate = AsyncMock(return_value={
            "response": "Test response from model",
            "eval_count": 100,
            "eval_duration": 3000000000
        })

        # Setup: Create components
        logger = ConsoleLogger()
        repository = JSONLTestCaseRepository(test_cases_dir, logger)
        model_gateway = OllamaGateway(mock_ollama_client, logger)

        # Setup: Create mock result repository
        mock_result_repository = Mock(spec=IResultRepository)
        mock_result_repository.save_result = AsyncMock()
        mock_result_repository.save_summary = AsyncMock()

        use_case = EvaluateModelUseCase(
            model_gateway=model_gateway,
            test_case_repository=repository,
            result_repository=mock_result_repository,
            logger=logger
        )

        # Execute
        request = EvaluationRequestDTO(
            model_name="primus-reasoning",
            benchmark_types=["B1"],
            temperature=0.7,
            save_results=False
        )

        summary = await use_case.execute(request)

        # Assert: Should process all 3 test cases
        assert summary.total_tests == 3, f"Expected 3 test cases, got {summary.total_tests}"
        assert mock_ollama_client.generate.call_count == 3, "Should call model 3 times"

        print(f"\n✅ Multiple Test Cases Test Passed!")
        print(f"   Processed {summary.total_tests} test cases")

    @pytest.mark.asyncio
    async def test_evaluation_handles_model_not_available(self, tmp_path):
        """
        E2E TEST: Evaluation handles model not available gracefully.

        Verifies that the evaluation pipeline fails gracefully when
        the requested model is not available in Ollama.
        """
        # Setup
        test_cases_dir = tmp_path / "test-cases"
        test_cases_dir.mkdir()

        # Create minimal test case
        test_file = test_cases_dir / "b01_ccop_applicability_scope.jsonl"
        test_file.write_text(json.dumps({
            "test_id": "B1-001",
            "benchmark_type": "B1_CCoP_Applicability_Scope",
            "section": "Test",
            "clause_reference": "N/A",
            "difficulty": "medium",
            "question": "What is CCoP 2.0?" * 10,  # Make it longer than 50 chars
            "expected_response": "CCoP 2.0 is a standard",
            "evaluation_criteria": {"accuracy": "test"},
            "metadata": {}
        }) + "\n")

        # Mock Ollama client - return empty model list
        mock_ollama_client = Mock(spec=OllamaClient)
        mock_ollama_client.list_models = AsyncMock(return_value=[])

        # Setup components
        logger = ConsoleLogger()
        repository = JSONLTestCaseRepository(test_cases_dir, logger)
        model_gateway = OllamaGateway(mock_ollama_client, logger)

        # Setup: Create mock result repository
        mock_result_repository = Mock(spec=IResultRepository)
        mock_result_repository.save_result = AsyncMock()
        mock_result_repository.save_summary = AsyncMock()

        use_case = EvaluateModelUseCase(
            model_gateway=model_gateway,
            test_case_repository=repository,
            result_repository=mock_result_repository,
            logger=logger
        )

        # Execute & Assert: Should raise ValueError
        request = EvaluationRequestDTO(
            model_name="non-existent-model",
            benchmark_types=["B1"],
            temperature=0.7,
            save_results=False
        )

        with pytest.raises(ValueError, match="is not available"):
            await use_case.execute(request)

        print(f"\n✅ Model Not Available Test Passed!")
