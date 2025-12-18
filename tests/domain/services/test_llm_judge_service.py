"""
Unit tests for LLMJudgeService.

Tests LLM-as-Judge evaluation using mocked Claude responses.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.services.llm_judge_service import JudgeEvaluation, LLMJudgeService
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.ccop_section import CCoPSection
from domain.value_objects.difficulty_level import DifficultyLevel


class TestLLMJudgeService:
    """Test suite for LLMJudgeService."""

    @pytest.fixture
    def test_case(self) -> TestCase:
        """Create sample test case for testing."""
        return TestCase(
            test_id="B12-001",
            benchmark_type=BenchmarkType.from_string("B12_Audit_Perspective_Alignment"),
            section=CCoPSection.from_string("Section 3: Governance"),
            clause_reference="3.1.1",
            difficulty=DifficultyLevel.from_string("medium"),
            question="What audit evidence would demonstrate compliance with Clause 3.1.1?",
            expected_response="Auditors would expect documented policies, approval records, and evidence of implementation.",
            evaluation_criteria={"accuracy": "Must align with audit expectations"},
        )

    @pytest.fixture
    def model_response(self) -> ModelResponse:
        """Create sample model response."""
        return ModelResponse(
            content="Compliance would be demonstrated through policy documents, board approvals, and implementation logs.",
            metadata={},
        )

    @pytest.fixture
    def rubric(self) -> dict[str, str]:
        """Create sample evaluation rubric."""
        return {
            "accuracy": "Does the response identify correct audit evidence?",
            "completeness": "Are all evidence types covered?",
            "alignment": "Does this match auditor expectations?",
        }

    def test_build_judge_prompt(
        self, test_case: TestCase, model_response: ModelResponse, rubric: dict[str, str]
    ) -> None:
        """Test judge prompt construction."""
        service = LLMJudgeService()
        prompt = service._build_judge_prompt(test_case, model_response, rubric)

        # Verify prompt contains all required elements
        assert "B12-001" in prompt or test_case.question in prompt
        assert model_response.content in prompt
        assert test_case.expected_response in prompt
        assert "accuracy_score" in prompt
        assert "completeness_score" in prompt
        assert "alignment_score" in prompt

    def test_parse_judge_response_clean_json(self) -> None:
        """Test parsing clean JSON response."""
        service = LLMJudgeService()
        response = json.dumps({
            "accuracy_score": 4,
            "completeness_score": 5,
            "alignment_score": 3,
            "justification": "Good coverage of audit evidence",
            "confidence": 0.8,
        })

        evaluation = service._parse_judge_response(response)

        assert evaluation.accuracy_score == 4
        assert evaluation.completeness_score == 5
        assert evaluation.alignment_score == 3
        assert evaluation.justification == "Good coverage of audit evidence"
        assert evaluation.confidence == 0.8
        assert evaluation.overall_score == 12 / 15  # (4+5+3)/15

    def test_parse_judge_response_markdown_code_block(self) -> None:
        """Test parsing JSON wrapped in markdown code block."""
        service = LLMJudgeService()
        response = """```json
{
  "accuracy_score": 3,
  "completeness_score": 4,
  "alignment_score": 4,
  "justification": "Partial alignment",
  "confidence": 0.7
}
```"""

        evaluation = service._parse_judge_response(response)

        assert evaluation.accuracy_score == 3
        assert evaluation.completeness_score == 4
        assert evaluation.alignment_score == 4

    def test_parse_judge_response_plain_code_block(self) -> None:
        """Test parsing JSON in plain code block without json marker."""
        service = LLMJudgeService()
        response = """```
{
  "accuracy_score": 5,
  "completeness_score": 5,
  "alignment_score": 5,
  "justification": "Excellent alignment",
  "confidence": 0.9
}
```"""

        evaluation = service._parse_judge_response(response)

        assert evaluation.accuracy_score == 5
        assert evaluation.overall_score == 1.0  # Perfect score

    def test_parse_judge_response_missing_confidence(self) -> None:
        """Test parsing response with missing confidence field."""
        service = LLMJudgeService()
        response = json.dumps({
            "accuracy_score": 4,
            "completeness_score": 4,
            "alignment_score": 4,
            "justification": "Good response",
        })

        evaluation = service._parse_judge_response(response)

        assert evaluation.confidence == 0.5  # Default value

    @patch('subprocess.run')
    def test_call_claude_agent_success(self, mock_run: MagicMock) -> None:
        """Test successful Claude Agent SDK call."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"accuracy_score": 4, "completeness_score": 4, "alignment_score": 4, "justification": "Good", "confidence": 0.8}',
            stderr=""
        )

        service = LLMJudgeService()
        result = service._call_claude_agent("test prompt")

        assert '"accuracy_score": 4' in result
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_call_claude_agent_error(self, mock_run: MagicMock) -> None:
        """Test Claude Agent SDK error handling."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Connection error"
        )

        service = LLMJudgeService()

        with pytest.raises(RuntimeError, match="Claude Agent SDK error"):
            service._call_claude_agent("test prompt")

    @patch.object(LLMJudgeService, '_call_claude_agent')
    def test_evaluate_response_success(
        self,
        mock_claude: MagicMock,
        test_case: TestCase,
        model_response: ModelResponse,
        rubric: dict[str, str]
    ) -> None:
        """Test successful evaluation."""
        mock_claude.return_value = json.dumps({
            "accuracy_score": 4,
            "completeness_score": 5,
            "alignment_score": 4,
            "justification": "Strong alignment with audit expectations",
            "confidence": 0.85,
        })

        service = LLMJudgeService()
        evaluation = service.evaluate_response(test_case, model_response, rubric)

        assert evaluation.accuracy_score == 4
        assert evaluation.completeness_score == 5
        assert evaluation.alignment_score == 4
        assert evaluation.overall_score == pytest.approx(13 / 15)
        assert evaluation.confidence == 0.85

    @patch.object(LLMJudgeService, '_call_claude_agent')
    def test_evaluate_response_fallback_on_error(
        self,
        mock_claude: MagicMock,
        test_case: TestCase,
        model_response: ModelResponse,
        rubric: dict[str, str]
    ) -> None:
        """Test fallback to conservative scoring on error."""
        mock_claude.side_effect = Exception("Network error")

        service = LLMJudgeService()
        evaluation = service.evaluate_response(test_case, model_response, rubric)

        # Should return conservative scores
        assert evaluation.accuracy_score == 3
        assert evaluation.completeness_score == 3
        assert evaluation.alignment_score == 3
        assert evaluation.overall_score == 0.6
        assert evaluation.confidence == 0.0
        assert "error" in evaluation.justification.lower()
