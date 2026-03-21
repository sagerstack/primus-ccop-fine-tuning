"""
Tests for scoring service fixes.

Verifies:
1. Sentence completeness requires 60% keywords (B1 rule-based)
2. Judge mode toggle routing (Phase 2.4)
"""

import pytest

from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.services.scoring_service import ScoringService
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.ccop_section import CCoPSection
from domain.value_objects.difficulty_level import DifficultyLevel


class TestSentenceCompletenessLogic:
    """Test sentence completeness requires 60% keywords (Option A fix)."""

    def test_sentence_completeness_requires_60_percent_keywords(self):
        """Sentence coverage requires 60% of keywords, not just ANY keyword."""
        test_case = TestCase(
            test_id="B1-901",
            benchmark_type=BenchmarkType("B1_CCoP_Applicability_Scope"),
            section=CCoPSection("Section 3: Governance"),
            clause_reference="3.1.1",
            difficulty=DifficultyLevel("low"),
            question="Test question with at least fifty characters for validation to pass successfully",
            # Expected response has 5 key words >4 chars: critical, information, infrastructure, owners, required
            expected_response="Critical Information Infrastructure Owners are required.",
            evaluation_criteria={"accuracy": "test"},
            key_facts=[]  # Empty to trigger sentence completeness fallback
        )

        # Response with 3 out of 5 terms (60%) - should be counted
        # Matches: critical, infrastructure, owners = 3/5 = 60%
        response_60_percent = ModelResponse(
            content="Critical Infrastructure Owners must follow guidelines.",
            model_name="test-model"
        )

        # Response with 2 out of 5 terms (40%) - should NOT be counted
        # Matches: critical, infrastructure = 2/5 = 40%
        response_40_percent = ModelResponse(
            content="Critical infrastructure needs review.",
            model_name="test-model"
        )

        # Score 60% response
        metrics_60 = ScoringService.score_response(test_case, response_60_percent)
        completeness_60 = next((m for m in metrics_60 if m.name == "completeness"), None)
        assert completeness_60 is not None
        # Should count the sentence (1/1 = 1.0)
        assert completeness_60.value == 1.0

        # Score 40% response
        metrics_40 = ScoringService.score_response(test_case, response_40_percent)
        completeness_40 = next((m for m in metrics_40 if m.name == "completeness"), None)
        assert completeness_40 is not None
        # Should NOT count the sentence (0/1 = 0.0)
        assert completeness_40.value == 0.0

    def test_sentence_completeness_any_keyword_no_longer_works(self):
        """Old behavior (ANY keyword = covered) should no longer work."""
        test_case = TestCase(
            test_id="B1-902",
            benchmark_type=BenchmarkType("B1_CCoP_Applicability_Scope"),
            section=CCoPSection("Section 3: Governance"),
            clause_reference="3.1.1",
            difficulty=DifficultyLevel("low"),
            question="Test question with at least fifty characters for validation to pass successfully",
            # 10 key terms: [authentication, required, critical, infrastructure, systems, users, provide, credentials, access, protected]
            expected_response="Multi-factor authentication is required for all critical infrastructure systems where users must provide multiple credentials to access protected resources.",
            evaluation_criteria={"accuracy": "test"},
            key_facts=[]  # Empty to trigger sentence completeness fallback
        )

        # Response with only 1 keyword (10%)
        # Old behavior: Would count as covered (ANY keyword)
        # New behavior: Should NOT count (< 60%)
        response = ModelResponse(
            content="Authentication mechanisms should be implemented.",
            model_name="test-model"
        )

        metrics = ScoringService.score_response(test_case, response)
        completeness = next((m for m in metrics if m.name == "completeness"), None)
        assert completeness is not None

        # With new logic, 10% keyword coverage should NOT count
        assert completeness.value == 0.0


class TestJudgeModeToggle:
    """Test judge_mode parameter routing in score_response."""

    def test_score_response_default_judge_mode_is_rubric(self):
        """Default judge_mode='rubric' produces rule-based or rubric results."""
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

        # Call without judge_mode (default is "rubric")
        metrics = ScoringService.score_response(test_case, response)

        # Should return rule-based metrics (accuracy, completeness)
        metric_names = [m.name for m in metrics]
        assert "accuracy" in metric_names or "completeness" in metric_names
        # Should not have judge-specific metrics
        assert "llm_judge" not in metric_names

    def test_score_response_universal_keeps_rule_based(self):
        """judge_mode='universal' keeps B1 (rule-based) as rule-based."""
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

        # Call with judge_mode="universal"
        metrics = ScoringService.score_response(
            test_case, response, judge_mode="universal"
        )

        # B1 should still use rule-based scoring
        metric_names = [m.name for m in metrics]
        assert "accuracy" in metric_names or "completeness" in metric_names


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
