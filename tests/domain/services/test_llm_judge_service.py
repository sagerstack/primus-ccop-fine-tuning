"""
Unit tests for LLMJudgeService.

Tests LLM-as-Judge evaluation with universal rubric (D1-D6 dimensions).
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.services.llm_judge_service import DimensionScore, JudgeEvaluation, LLMJudgeService
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
            key_facts=["Board must approve cybersecurity policy"],
            forbidden_claims=["No documentation needed"],
            metadata={
                "key_facts_structured": [
                    {"fact": "Board approval required", "source": "CCoP 2.0 3.1.1", "tier": "critical"}
                ]
            }
        )

    @pytest.fixture
    def model_response(self) -> ModelResponse:
        """Create sample model response with Sources."""
        return ModelResponse(
            content="""Compliance would be demonstrated through policy documents, board approvals, and implementation logs.

**Sources:**
CCoP 2.0: 3.1.1
""",
            metadata={},
        )

    def test_build_judge_prompt(
        self, test_case: TestCase, model_response: ModelResponse
    ) -> None:
        """Test judge prompt construction with new contract (no Qdrant placeholders)."""
        service = LLMJudgeService()
        prompt = service._build_judge_prompt(test_case, model_response, "B12")

        # Verify prompt contains required elements
        assert test_case.question in prompt
        assert model_response.content in prompt
        assert test_case.expected_response in prompt
        assert "{clause_reference}" not in prompt  # Should be substituted
        assert "{key_facts}" not in prompt  # Should be substituted
        assert "{forbidden_claims}" not in prompt  # Should be substituted
        
        # Verify Qdrant-dependent placeholders are ABSENT
        assert "{citation_verifications}" not in prompt
        assert "{expected_citations_text}" not in prompt
        
        # Verify GT placeholders ARE present/substituted
        assert "3.1.1" in prompt  # clause_reference substituted
        assert "Board" in prompt or "approval" in prompt  # key_facts substituted

    def test_parse_judge_response_clean_json(self) -> None:
        """Test parsing clean 5-dimension JSON response (D1-D5)."""
        service = LLMJudgeService()
        # LLM now returns 5 dimensions (D1-D5), D6 computed separately
        response = json.dumps({
            "dimensions": [
                {"dimension": "verdict_accuracy", "score": 3, "weight": 0.5},
                {"dimension": "justification_quality", "score": 2, "weight": 0.5},
                {"dimension": "factual_grounding", "score": 2, "weight": 0.5},
                {"dimension": "scope_appropriateness", "score": 3, "weight": 0.5},
                {"dimension": "actionable_way_forward", "score": 1, "weight": 0.5},
            ],
            "justification": "Good coverage of audit evidence with minor gaps.",
            "confidence": 0.8,
        })

        dimensions, justification, confidence, raw_response = service._parse_judge_response(response)

        # Assert tuple components
        assert len(dimensions) == 5  # D1-D5 only
        assert dimensions[0].name == "verdict_accuracy"
        assert dimensions[0].score == 3
        assert dimensions[0].weight == 0.5
        assert justification == "Good coverage of audit evidence with minor gaps."
        assert confidence == 0.8
        assert raw_response == response

    def test_parse_judge_response_markdown_code_block(self) -> None:
        """Test parsing JSON wrapped in markdown code block."""
        service = LLMJudgeService()
        response = """```json
{
  "dimensions": [
    {"dimension": "verdict_accuracy", "score": 2, "weight": 0.5},
    {"dimension": "justification_quality", "score": 2, "weight": 0.5},
    {"dimension": "factual_grounding", "score": 1, "weight": 0.5},
    {"dimension": "scope_appropriateness", "score": 2, "weight": 0.5},
    {"dimension": "actionable_way_forward", "score": 1, "weight": 0.5}
  ],
  "justification": "Partial alignment",
  "confidence": 0.7
}
```"""

        dimensions, justification, confidence, raw_response = service._parse_judge_response(response)

        assert len(dimensions) == 5
        assert dimensions[0].score == 2
        assert dimensions[2].name == "factual_grounding"
        assert dimensions[2].score == 1

    def test_parse_judge_response_plain_code_block(self) -> None:
        """Test parsing JSON in plain code block without json marker."""
        service = LLMJudgeService()
        response = """```
{
  "dimensions": [
    {"dimension": "verdict_accuracy", "score": 3, "weight": 0.5},
    {"dimension": "justification_quality", "score": 3, "weight": 0.5},
    {"dimension": "factual_grounding", "score": 3, "weight": 0.5},
    {"dimension": "scope_appropriateness", "score": 3, "weight": 0.5},
    {"dimension": "actionable_way_forward", "score": 3, "weight": 0.5}
  ],
  "justification": "Excellent alignment",
  "confidence": 0.9
}
```"""

        dimensions, justification, confidence, _ = service._parse_judge_response(response)

        assert len(dimensions) == 5
        assert all(d.score == 3 for d in dimensions)  # Perfect scores

    def test_parse_judge_response_missing_confidence(self) -> None:
        """Test parsing response with missing confidence field."""
        service = LLMJudgeService()
        response = json.dumps({
            "dimensions": [
                {"dimension": "verdict_accuracy", "score": 2, "weight": 0.5},
                {"dimension": "justification_quality", "score": 2, "weight": 0.5},
                {"dimension": "factual_grounding", "score": 2, "weight": 0.5},
                {"dimension": "scope_appropriateness", "score": 2, "weight": 0.5},
                {"dimension": "actionable_way_forward", "score": 2, "weight": 0.5},
            ],
            "justification": "Good response",
        })

        dimensions, justification, confidence, _ = service._parse_judge_response(response)

        assert confidence == 0.5  # Default value
        assert len(dimensions) == 5

    # NOTE: test_call_claude_agent_* tests REMOVED - deprecated code path.
    # The current LLMJudgeService uses _call_judge() which routes through
    # OpenRouter, not the old Claude Agent SDK. The _call_claude_agent()
    # method no longer exists in the codebase.

    @patch.object(LLMJudgeService, '_call_judge')
    def test_evaluate_response_success(
        self,
        mock_judge: MagicMock,
        test_case: TestCase,
        model_response: ModelResponse,
    ) -> None:
        """Test successful evaluation with 5-dim LLM + computed D6."""
        # Mock LLM judge returns 5 dimensions (D1-D5)
        mock_judge.return_value = json.dumps({
            "dimensions": [
                {"dimension": "verdict_accuracy", "score": 3, "weight": 0.5},
                {"dimension": "justification_quality", "score": 2, "weight": 0.5},
                {"dimension": "factual_grounding", "score": 2, "weight": 0.5},
                {"dimension": "scope_appropriateness", "score": 3, "weight": 0.5},
                {"dimension": "actionable_way_forward", "score": 1, "weight": 0.5},
            ],
            "justification": "Strong alignment with audit expectations",
            "confidence": 0.85,
        })

        service = LLMJudgeService()
        evaluation = service.evaluate_response(test_case, model_response, "B12")

        # Assert final JudgeEvaluation has ALL 6 dimensions (D1-D5 from LLM + D6 computed)
        assert len(evaluation.dimensions) == 6
        
        # Check D1-D5
        assert evaluation.dimensions[0].name == "verdict_accuracy"
        assert evaluation.dimensions[0].score == 3
        assert evaluation.dimensions[1].name == "justification_quality"
        assert evaluation.dimensions[1].score == 2
        
        # Check D6 (citation_correctness) was computed and appended
        d6 = next((d for d in evaluation.dimensions if d.name == "citation_correctness"), None)
        assert d6 is not None, "D6 (citation_correctness) should be computed and appended"
        assert d6.weight == 0.5
        # D6 should be 3 (perfect precision): model cites 3.1.1, GT has 3.1.1
        assert d6.score == 3
        
        assert evaluation.confidence == 0.85
        # Overall score = sum(score * weight) / (3.0 * sum(weight))
        # = (3*0.5 + 2*0.5 + 2*0.5 + 3*0.5 + 1*0.5 + 3*0.5) / (3.0 * 3.0)
        # = (1.5 + 1.0 + 1.0 + 1.5 + 0.5 + 1.5) / 9.0 = 7.0 / 9.0
        assert evaluation.overall_score == pytest.approx(7.0 / 9.0)

    @patch.object(LLMJudgeService, '_call_judge')
    def test_evaluate_response_fallback_on_error(
        self,
        mock_judge: MagicMock,
        test_case: TestCase,
        model_response: ModelResponse,
    ) -> None:
        """Test graceful error handling on judge failure."""
        mock_judge.side_effect = Exception("Network error")

        service = LLMJudgeService()
        evaluation = service.evaluate_response(test_case, model_response, "B12")

        # Should return error evaluation with judge_error=True
        assert evaluation.judge_error is True
        assert "error" in evaluation.error_message.lower() or "failed" in evaluation.error_message.lower()
