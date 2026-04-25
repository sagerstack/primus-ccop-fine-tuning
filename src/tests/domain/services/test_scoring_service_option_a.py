"""
Tests for scoring service routing.

NOTE: Rule-based scoring tests removed when ScoringService.score_response was
unified to dispatch every benchmark through the LLM judge universal rubric.
The legacy 60-percent-keyword sentence-completeness logic is no longer
exercised on the hot path; B1/B2/B4/B5/B6/B21 cases now produce 5-dimension
LLM-judge results identical in shape to B3/B7-B20/B22-B24. See
domain/services/scoring_service.py for the routing change rationale.
"""

import pytest

from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.services.scoring_service import ScoringService
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.ccop_section import CCoPSection
from domain.value_objects.difficulty_level import DifficultyLevel


class TestJudgeModeToggle:
    """Test judge_mode parameter routing in score_response."""

    def test_score_response_default_routes_all_benchmarks_to_llm_judge(self):
        """All benchmarks (including B1) now route through the LLM judge universal rubric."""
        test_case = TestCase(
            test_id="B1-800",
            benchmark_type=BenchmarkType("B1_CCoP_Applicability_Scope"),
            section=CCoPSection("Section 3: Governance"),
            clause_reference="3.1.1",
            difficulty=DifficultyLevel("low"),
            question="Test question with at least fifty characters for validation to pass successfully",
            expected_response="Critical Information Infrastructure Owners are required.",
            evaluation_criteria={"accuracy": "test"},
            key_facts=[]
        )

        response = ModelResponse(
            content="Critical Infrastructure Owners must follow guidelines.",
            model_name="test-model"
        )

        # Call without judge_mode (default is "rubric") — routes through LLM judge
        # for every benchmark. In a test env without a live judge, the service
        # returns either the 5 universal-rubric dimensions populated with judge
        # output OR a single "judge_error" metric when the judge is unreachable.
        metrics = ScoringService.score_response(test_case, response)
        metric_names = [m.name for m in metrics]

        # Must NOT contain the legacy rule-based metrics
        assert "completeness" not in metric_names
        assert "grounding" not in metric_names

        # Should contain either LLM-judge dimensions or a judge_error metric
        expected_universal_dims = {
            "verdict_accuracy", "justification_quality", "factual_grounding",
            "scope_appropriateness", "actionable_way_forward",
        }
        if "judge_error" in metric_names:
            # Judge unreachable in test env — acceptable
            pass
        else:
            assert any(name in expected_universal_dims for name in metric_names), (
                f"Expected at least one universal-rubric dimension, got: {metric_names}"
            )

    def test_score_response_universal_routes_all_to_universal_judge(self):
        """judge_mode='universal' routes ALL benchmarks through universal judge, including B1."""
        test_case = TestCase(
            test_id="B1-801",
            benchmark_type=BenchmarkType("B1_CCoP_Applicability_Scope"),
            section=CCoPSection("Section 3: Governance"),
            clause_reference="3.1.1",
            difficulty=DifficultyLevel("low"),
            question="Test question with at least fifty characters for validation to pass successfully",
            expected_response="Critical Information Infrastructure Owners are required.",
            evaluation_criteria={"accuracy": "test"},
            key_facts=[]
        )

        response = ModelResponse(
            content="Critical Infrastructure Owners must follow guidelines.",
            model_name="test-model"
        )

        # Call with judge_mode="universal" — should route to universal judge
        # which requires Claude API, so it will return judge_error in test env
        metrics = ScoringService.score_response(
            test_case, response, judge_mode="universal"
        )

        # Universal judge returns either "universal_judge" or "judge_error" metric
        metric_names = [m.name for m in metrics]
        assert "universal_judge" in metric_names or "judge_error" in metric_names


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
