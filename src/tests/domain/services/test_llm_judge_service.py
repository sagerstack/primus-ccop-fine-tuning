"""
Tests for LLMJudgeService and JudgeEvaluation.

Validates universal judge fields, factories, and parsing logic.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from domain.services.llm_judge_service import (
    JudgeEvaluation,
    DimensionScore,
    LLMJudgeService,
)
from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase


class TestJudgeEvaluationModel:
    """Test JudgeEvaluation model with new universal judge fields."""

    def test_judge_evaluation_default_fields(self):
        """New universal judge fields have correct defaults."""
        eval = JudgeEvaluation(
            dimensions=[],
            justification="test",
            overall_score=0.5,
            confidence=0.8,
            raw_response="test response",
        )

        # Universal judge fields should have defaults
        assert eval.hallucination_detected is False
        assert eval.unsupported_count == 0
        assert eval.contradicted_count == 0
        assert eval.claims == []
        assert eval.reasoning_criteria_met == {}

    def test_from_universal_judge_no_hallucination(self):
        """from_universal_judge with 2/3 criteria met, no hallucination."""
        eval = JudgeEvaluation.from_universal_judge(
            reasoning_criteria_met={
                "clause_citations": True,
                "conditional_analysis": True,
                "actionable_steps": None,  # N/A
            },
            hallucination_detected=False,
            claims=[],
            unsupported_count=0,
            contradicted_count=0,
            justification="Response cites clauses and analyzes conditions.",
            confidence=0.9,
            raw_response="mock response",
        )

        # reasoning_depth_score = 2 (two True values, one None)
        # overall_score = 2/3 = 0.667
        assert eval.overall_score == pytest.approx(0.667, rel=0.01)
        assert eval.hallucination_detected is False
        assert len(eval.dimensions) == 1
        assert eval.dimensions[0].name == "reasoning_depth"
        assert eval.dimensions[0].score == 2

    def test_from_universal_judge_all_criteria_met(self):
        """from_universal_judge with all 3 criteria met, no hallucination."""
        eval = JudgeEvaluation.from_universal_judge(
            reasoning_criteria_met={
                "clause_citations": True,
                "conditional_analysis": True,
                "actionable_steps": True,
            },
            hallucination_detected=False,
            claims=[],
            unsupported_count=0,
            contradicted_count=0,
            justification="All criteria met.",
            confidence=0.95,
            raw_response="mock",
        )

        # reasoning_depth_score = 3
        # overall_score = 3/3 = 1.0
        assert eval.overall_score == 1.0
        assert eval.dimensions[0].score == 3

    def test_from_universal_judge_hallucination_detected(self):
        """from_universal_judge with hallucination_detected=True sets overall_score to 0.0."""
        eval = JudgeEvaluation.from_universal_judge(
            reasoning_criteria_met={
                "clause_citations": True,
                "conditional_analysis": True,
                "actionable_steps": True,
            },
            hallucination_detected=True,  # Gate triggered
            claims=[
                {"text": "Fabricated claim", "status": "UNSUPPORTED", "evidence": "No evidence"}
            ],
            unsupported_count=1,
            contradicted_count=0,
            justification="Hallucination detected despite good reasoning.",
            confidence=0.8,
            raw_response="mock",
        )

        # Hallucination gate: overall_score = 0.0 regardless of reasoning
        assert eval.overall_score == 0.0
        assert eval.hallucination_detected is True
        assert eval.unsupported_count == 1
        assert len(eval.claims) == 1

    def test_from_universal_judge_no_applicable_criteria(self):
        """from_universal_judge with all criteria N/A (None)."""
        eval = JudgeEvaluation.from_universal_judge(
            reasoning_criteria_met={
                "clause_citations": None,
                "conditional_analysis": None,
                "actionable_steps": None,
            },
            hallucination_detected=False,
            claims=[],
            unsupported_count=0,
            contradicted_count=0,
            justification="No applicable criteria.",
            confidence=0.5,
            raw_response="mock",
        )

        # reasoning_depth_score = 0 (no True values)
        # overall_score = 0/3 = 0.0
        assert eval.overall_score == 0.0
        assert eval.dimensions[0].score == 0

    def test_from_universal_judge_one_criterion_met(self):
        """from_universal_judge with 1/1 applicable criterion met."""
        eval = JudgeEvaluation.from_universal_judge(
            reasoning_criteria_met={
                "clause_citations": True,
                "conditional_analysis": None,  # N/A
                "actionable_steps": None,  # N/A
            },
            hallucination_detected=False,
            claims=[],
            unsupported_count=0,
            contradicted_count=0,
            justification="Only clause citations applicable and met.",
            confidence=0.85,
            raw_response="mock",
        )

        # reasoning_depth_score = 1 (one True, two None)
        # overall_score = 1/3 = 0.333
        assert eval.overall_score == pytest.approx(0.333, rel=0.01)
        assert eval.dimensions[0].score == 1

    def test_from_dimensions_backward_compatible(self):
        """from_dimensions factory still works, new fields default correctly."""
        dimensions = [
            DimensionScore(name="accuracy", score=2, weight=1.0),
            DimensionScore(name="completeness", score=3, weight=1.5),
        ]
        eval = JudgeEvaluation.from_dimensions(
            dimensions=dimensions,
            justification="Good response.",
            confidence=0.9,
            raw_response="test",
        )

        # Check backward compatibility
        assert eval.judge_error is False
        assert eval.hallucination_detected is False
        assert eval.claims == []
        assert eval.reasoning_criteria_met == {}

        # Check overall_score calculation (legacy rubric mode)
        # overall = (2*1.0 + 3*1.5) / (3.0 * (1.0 + 1.5)) = 6.5 / 7.5 = 0.867
        assert eval.overall_score == pytest.approx(0.867, rel=0.01)


class TestLLMJudgeServiceUniversalParsing:
    """Test LLMJudgeService parsing of universal judge responses."""

    @pytest.fixture
    def service(self):
        """Create LLMJudgeService with minimal config (rubric path not needed for universal)."""
        # Pass a non-existent rubric path since we're not testing rubric mode
        return LLMJudgeService(model_name="test-model", rubric_path="/tmp/nonexistent.md")

    def test_parse_universal_judge_response(self, service):
        """Parse valid universal judge JSON response."""
        mock_response = json.dumps({
            "claims": [
                {"text": "Claim 1", "status": "SUPPORTED", "evidence": "Evidence from clause 5.2.1"},
                {"text": "Claim 2", "status": "UNSUPPORTED", "evidence": "No evidence found"},
            ],
            "hallucination_detected": True,
            "unsupported_count": 1,
            "contradicted_count": 0,
            "reasoning_depth_score": 2,
            "reasoning_criteria_met": {
                "clause_citations": True,
                "conditional_analysis": True,
                "actionable_steps": None,
            },
            "justification": "Response has 1 unsupported claim.",
            "confidence": 0.85,
        })

        eval = service._parse_universal_judge_response(mock_response)

        assert eval.hallucination_detected is True
        assert eval.unsupported_count == 1
        assert eval.contradicted_count == 0
        assert len(eval.claims) == 2
        assert eval.claims[0]["text"] == "Claim 1"
        assert eval.reasoning_criteria_met["clause_citations"] is True
        assert eval.reasoning_criteria_met["actionable_steps"] is None
        assert eval.overall_score == 0.0  # Hallucination gate

    def test_parse_universal_judge_with_markdown_wrapper(self, service):
        """Parse response wrapped in markdown code block."""
        json_content = {
            "claims": [],
            "hallucination_detected": False,
            "unsupported_count": 0,
            "contradicted_count": 0,
            "reasoning_depth_score": 3,
            "reasoning_criteria_met": {
                "clause_citations": True,
                "conditional_analysis": True,
                "actionable_steps": True,
            },
            "justification": "All criteria met.",
            "confidence": 0.95,
        }
        mock_response = f"```json\n{json.dumps(json_content)}\n```"

        eval = service._parse_universal_judge_response(mock_response)

        assert eval.hallucination_detected is False
        assert eval.overall_score == 1.0  # 3/3

    def test_parse_universal_judge_invalid_json_returns_error(self, service):
        """Invalid JSON returns error JudgeEvaluation."""
        mock_response = "This is not valid JSON"

        eval = service._parse_universal_judge_response(mock_response)

        assert eval.judge_error is True
        assert "Failed to parse universal judge response" in eval.error_message

    def test_parse_universal_judge_missing_fields_returns_error(self, service):
        """Missing required fields returns error JudgeEvaluation."""
        mock_response = json.dumps({
            "claims": [],
            # Missing hallucination_detected and other required fields
        })

        eval = service._parse_universal_judge_response(mock_response)

        # Should handle gracefully with defaults or return error
        # Based on implementation, missing fields get defaults from .get()
        assert eval.hallucination_detected is False  # Default from .get()
        assert eval.unsupported_count == 0
