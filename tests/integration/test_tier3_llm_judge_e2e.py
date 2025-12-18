"""
E2E Integration test for Tier 3 LLM-as-Judge scoring.

Tests the full evaluation flow for subjective benchmarks (B12, B13, B20)
using Claude as an expert judge.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.services.scoring_service import ScoringService
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.ccop_section import CCoPSection
from domain.value_objects.difficulty_level import DifficultyLevel


class TestTier3LLMJudgeE2E:
    """E2E test suite for Tier 3 LLM-as-Judge scoring."""

    @pytest.fixture
    def b12_test_case(self) -> TestCase:
        """Create B12 (Audit Perspective Alignment) test case."""
        return TestCase(
            test_id="B12-001",
            benchmark_type=BenchmarkType.from_string("B12_Audit_Perspective_Alignment"),
            section=CCoPSection.from_string("Section 3: Governance"),
            clause_reference="3.1.1",
            difficulty=DifficultyLevel.from_string("high"),
            question="What evidence would a CSA auditor expect to verify compliance with Clause 3.1.1 regarding CIIO appointment?",
            expected_response="Auditors would expect: (1) Board resolution or official letter appointing CIIO, (2) Documentation of CIIO's authority and reporting structure, (3) Evidence CIIO has access to board or senior management, (4) CIIO job description or charter, (5) Organizational chart showing CIIO position.",
            evaluation_criteria={
                "scoring_strategy": "llm_judge",
                "audit_alignment": True,
            },
        )

    @pytest.fixture
    def good_response(self) -> ModelResponse:
        """Create audit-aligned response."""
        return ModelResponse(
            content="An auditor would look for formal appointment documentation such as board minutes or executive letters, organizational structure showing CIIO reporting lines, evidence of direct management access, role definition documents, and verification of operational authority.",
            metadata={},
        )

    @pytest.fixture
    def mock_claude_good_evaluation(self) -> str:
        """Mock Claude response for good evaluation."""
        return json.dumps({
            "accuracy_score": 4,
            "completeness_score": 4,
            "alignment_score": 5,
            "justification": "Response demonstrates strong understanding of audit evidence requirements. Correctly identifies key documentation auditors would verify.",
            "confidence": 0.85,
        })

    @pytest.fixture
    def mock_claude_poor_evaluation(self) -> str:
        """Mock Claude response for poor evaluation."""
        return json.dumps({
            "accuracy_score": 2,
            "completeness_score": 2,
            "alignment_score": 2,
            "justification": "Response lacks specificity and misses critical audit evidence types.",
            "confidence": 0.7,
        })

    @patch('domain.services.llm_judge_service.subprocess.run')
    def test_b12_llm_judge_good_response(
        self,
        mock_run: MagicMock,
        b12_test_case: TestCase,
        good_response: ModelResponse,
        mock_claude_good_evaluation: str,
    ) -> None:
        """Test that LLM judge correctly evaluates good response."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_claude_good_evaluation,
            stderr=""
        )

        metrics = ScoringService.score_response(b12_test_case, good_response)

        # Should have accuracy, completeness, alignment metrics
        assert len(metrics) == 3

        accuracy = next(m for m in metrics if m.name == "accuracy")
        completeness = next(m for m in metrics if m.name == "completeness")
        alignment = next(m for m in metrics if m.name == "alignment")

        # Check scores match judge evaluation (normalized to 0-1)
        assert accuracy.value == pytest.approx(4 / 5.0)
        assert completeness.value == pytest.approx(4 / 5.0)
        assert alignment.value == pytest.approx(5 / 5.0)

        # Verify descriptions
        assert "LLM judge" in accuracy.description
        assert "LLM judge" in completeness.description
        assert "LLM judge" in alignment.description

    @patch('domain.services.llm_judge_service.subprocess.run')
    def test_b12_llm_judge_poor_response(
        self,
        mock_run: MagicMock,
        b12_test_case: TestCase,
        good_response: ModelResponse,
        mock_claude_poor_evaluation: str,
    ) -> None:
        """Test that LLM judge correctly evaluates poor response."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_claude_poor_evaluation,
            stderr=""
        )

        metrics = ScoringService.score_response(b12_test_case, good_response)

        accuracy = next(m for m in metrics if m.name == "accuracy")
        completeness = next(m for m in metrics if m.name == "completeness")
        alignment = next(m for m in metrics if m.name == "alignment")

        # Low scores for poor response
        assert accuracy.value == pytest.approx(2 / 5.0)
        assert completeness.value == pytest.approx(2 / 5.0)
        assert alignment.value == pytest.approx(2 / 5.0)

    @patch('domain.services.llm_judge_service.subprocess.run')
    def test_b12_llm_judge_error_fallback(
        self,
        mock_run: MagicMock,
        b12_test_case: TestCase,
        good_response: ModelResponse,
    ) -> None:
        """Test fallback behavior when LLM judge fails."""
        mock_run.side_effect = Exception("Network error")

        metrics = ScoringService.score_response(b12_test_case, good_response)

        # Should still return metrics (conservative scores)
        assert len(metrics) == 3

        accuracy = next(m for m in metrics if m.name == "accuracy")

        # Fallback score should be moderate (3/5 = 0.6)
        assert accuracy.value == pytest.approx(3 / 5.0)

    def test_tier3_benchmarks_use_llm_judge(self) -> None:
        """Test that all Tier 3 benchmarks use LLM judge."""
        tier3_benchmarks = ["B12", "B13", "B20"]

        for benchmark_code in tier3_benchmarks:
            test_case = TestCase(
                test_id=f"{benchmark_code}-001",
                benchmark_type=BenchmarkType.from_string(f"{benchmark_code}_Test"),
                section=CCoPSection.from_string("Section 3: Governance"),
                clause_reference="3.1.1",
                difficulty=DifficultyLevel.from_string("high"),
                question="Test question for LLM judge verification and scoring methodology?",
                expected_response="Expected answer for testing LLM judge implementation",
                evaluation_criteria={"test": "value"},
            )

            response = ModelResponse(content="Test answer", metadata={})

            # Mock Claude to avoid actual API calls
            with patch('domain.services.llm_judge_service.subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout=json.dumps({
                        "accuracy_score": 3,
                        "completeness_score": 3,
                        "alignment_score": 3,
                        "justification": "Test evaluation",
                        "confidence": 0.7,
                    }),
                    stderr=""
                )

                metrics = ScoringService.score_response(test_case, response)

                # Verify LLM judge is used
                accuracy = next(m for m in metrics if m.name == "accuracy")
                assert "judge" in accuracy.description.lower(), (
                    f"{benchmark_code} should use LLM judge"
                )

    @patch('domain.services.llm_judge_service.subprocess.run')
    def test_b12_returns_three_metrics(
        self,
        mock_run: MagicMock,
        b12_test_case: TestCase,
        good_response: ModelResponse,
        mock_claude_good_evaluation: str,
    ) -> None:
        """Test that B12 returns accuracy, completeness, and alignment metrics."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_claude_good_evaluation,
            stderr=""
        )

        metrics = ScoringService.score_response(b12_test_case, good_response)

        metric_names = {m.name for m in metrics}
        assert metric_names == {"accuracy", "completeness", "alignment"}

    @patch('domain.services.llm_judge_service.subprocess.run')
    def test_llm_judge_metric_properties(
        self,
        mock_run: MagicMock,
        b12_test_case: TestCase,
        good_response: ModelResponse,
        mock_claude_good_evaluation: str,
    ) -> None:
        """Test that LLM judge metrics have correct properties."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_claude_good_evaluation,
            stderr=""
        )

        metrics = ScoringService.score_response(b12_test_case, good_response)

        for metric in metrics:
            # All metrics should be normalized to [0, 1]
            assert 0.0 <= metric.value <= 1.0

            # Metrics should have descriptions
            assert len(metric.description) > 0

            # Weights should be positive
            assert metric.weight > 0

    @patch('domain.services.llm_judge_service.subprocess.run')
    def test_b12_uses_correct_rubric(
        self,
        mock_run: MagicMock,
        b12_test_case: TestCase,
        good_response: ModelResponse,
        mock_claude_good_evaluation: str,
    ) -> None:
        """Test that B12 uses audit perspective rubric."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_claude_good_evaluation,
            stderr=""
        )

        ScoringService.score_response(b12_test_case, good_response)

        # Verify Claude was called with correct rubric
        call_args = mock_run.call_args[1]["input"]
        assert "audit" in call_args.lower()
        assert "CSA auditor" in call_args or "auditor" in call_args
