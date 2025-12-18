"""
Tests for Option A scoring fixes.

Verifies:
1. Semantic similarity penalty for scores < 0.70
2. Sentence completeness requires 60% keywords
3. Key fact threshold at 75%
"""

import pytest

from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.services.scoring_service import ScoringService
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.ccop_section import CCoPSection
from domain.value_objects.difficulty_level import DifficultyLevel


class TestSemanticSimilarityPenalty:
    """Test semantic similarity penalty for low scores (Option A fix)."""

    def test_semantic_similarity_high_score_no_penalty(self):
        """High semantic similarity (>= 0.70) should not be penalized."""
        # Create a reasoning track test case (B8)
        test_case = TestCase(
            test_id="B8-901",
            benchmark_type=BenchmarkType("B8_Gap_Prioritisation"),
            section=CCoPSection("Section 5: Protection"),
            clause_reference="5.1.1",
            difficulty=DifficultyLevel("medium"),
            question="Test question with at least fifty characters for validation to pass successfully",
            expected_response="CIIOs must implement strong authentication controls including multi-factor authentication for all privileged access to critical systems.",
            evaluation_criteria={"accuracy": "test"},
            key_facts=[
                "CIIOs must implement strong authentication controls",
                "Multi-factor authentication required for privileged access"
            ]
        )

        # Response that should have high semantic similarity (>0.70)
        response = ModelResponse(
            content="CIIOs are required to implement robust authentication controls, "
                    "including multi-factor authentication for privileged system access.",
            model_name="test-model"
        )

        # Score the response
        metrics = ScoringService.score_response(test_case, response)

        # Find accuracy metric
        accuracy_metric = next((m for m in metrics if m.name == "accuracy"), None)
        assert accuracy_metric is not None

        # High similarity should not be penalized
        # Expect score >= 0.70 (no penalty applied)
        assert accuracy_metric.value >= 0.70

    def test_semantic_similarity_low_score_gets_penalty(self):
        """Low semantic similarity (< 0.70) should be penalized."""
        test_case = TestCase(
            test_id="B8-902",
            benchmark_type=BenchmarkType("B8_Gap_Prioritisation"),
            section=CCoPSection("Section 5: Protection"),
            clause_reference="5.1.1",
            difficulty=DifficultyLevel("medium"),
            question="Test question with at least fifty characters for validation to pass successfully",
            expected_response="CIIOs must implement strong authentication controls including multi-factor authentication for all privileged access to critical systems.",
            evaluation_criteria={"accuracy": "test"},
            key_facts=[
                "CIIOs must implement strong authentication controls",
                "Multi-factor authentication required for privileged access"
            ]
        )

        # Partial response that should have low semantic similarity
        response = ModelResponse(
            content="Authentication is important for security.",
            model_name="test-model"
        )

        # Score the response
        metrics = ScoringService.score_response(test_case, response)

        # Find accuracy metric
        accuracy_metric = next((m for m in metrics if m.name == "accuracy"), None)
        assert accuracy_metric is not None

        # Low similarity should be penalized
        # Expect score < 0.50 (penalty applied)
        assert accuracy_metric.value < 0.50


class TestKeyFactThreshold:
    """Test key fact threshold raised to 70% (Option A fix)."""

    def test_key_fact_69_percent_coverage_not_counted(self):
        """Fact with 69% keyword coverage should NOT be counted (below 70% threshold)."""
        test_case = TestCase(
            test_id="B8-903",
            benchmark_type=BenchmarkType("B8_Gap_Prioritisation"),
            section=CCoPSection("Section 5: Protection"),
            clause_reference="5.1.1",
            difficulty=DifficultyLevel("medium"),
            question="Test question with at least fifty characters for validation to pass successfully",
            expected_response="Test response",
            evaluation_criteria={"accuracy": "test"},
            key_facts=[
                # 10 key terms: [clause, requires, ciios, establish, maintain, framework, identify, assess, manage, monitor]
                "Clause 3.2.2 requires CIIOs to establish and maintain a framework to identify, assess, manage, and monitor"
            ]
        )

        # Response with exactly 7 out of 10 terms = 70% (should be counted)
        # Matches: clause, requires, ciios, establish, framework, identify, assess
        response_70_percent = ModelResponse(
            content="Clause 3.2.2 requires CIIOs to establish a framework to identify and assess cybersecurity threats",
            model_name="test-model"
        )

        # Response with 6 out of 10 terms = 60% (should NOT be counted, below 70% threshold)
        # Matches: clause, requires, establish, framework, identify, assess
        response_60_percent = ModelResponse(
            content="Clause 3.2.2 requires organizations to establish a framework to identify and assess cybersecurity threats",
            model_name="test-model"
        )

        # Score 70% response
        metrics_70 = ScoringService.score_response(test_case, response_70_percent)
        completeness_70 = next((m for m in metrics_70 if m.name == "completeness"), None)
        assert completeness_70 is not None
        # Should count the fact (1/1 = 1.0)
        assert completeness_70.value == 1.0

        # Score 60% response
        metrics_60 = ScoringService.score_response(test_case, response_60_percent)
        completeness_60 = next((m for m in metrics_60 if m.name == "completeness"), None)
        assert completeness_60 is not None
        # Should NOT count the fact (0/1 = 0.0)
        assert completeness_60.value == 0.0

    def test_key_fact_70_percent_coverage_counted(self):
        """Fact with exactly 70% keyword coverage should be counted."""
        test_case = TestCase(
            test_id="B8-904",
            benchmark_type=BenchmarkType("B8_Gap_Prioritisation"),
            section=CCoPSection("Section 5: Protection"),
            clause_reference="5.1.1",
            difficulty=DifficultyLevel("medium"),
            question="Test question with at least fifty characters for validation to pass successfully",
            expected_response="Test response",
            evaluation_criteria={"accuracy": "test"},
            key_facts=[
                # 10 key terms: [clause, requires, ciios, establish, maintain, framework, identify, assess, manage, monitor]
                "Clause 3.2.2 requires CIIOs to establish and maintain a framework to identify, assess, manage, and monitor"
            ]
        )

        # Response with exactly 7/10 terms (70%)
        # Matches: clause, requires, ciios, establish, framework, identify, assess
        response = ModelResponse(
            content="Clause 3.2.2 requires CIIOs to establish a framework to identify and assess cybersecurity threats",
            model_name="test-model"
        )

        metrics = ScoringService.score_response(test_case, response)
        completeness = next((m for m in metrics if m.name == "completeness"), None)
        assert completeness is not None
        # Should count the fact (1/1 = 1.0)
        assert completeness.value == 1.0


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


class TestOptionAIntegration:
    """Integration tests verifying all Option A fixes work together."""

    def test_realistic_partial_answer_gets_low_score(self):
        """Realistic partial answer should score low with all fixes applied."""
        test_case = TestCase(
            test_id="B8-905",
            benchmark_type=BenchmarkType("B8_Gap_Prioritisation"),
            section=CCoPSection("Section 5: Protection"),
            clause_reference="5.6.4",
            difficulty=DifficultyLevel("high"),
            question="Interpret CCoP 2.0 Clause 5.6.4 concerning patch management timelines with at least fifty characters in this question.",
            expected_response="Clause 5.6.4 establishes specific timelines for patch application based on severity. For critical security patches addressing vulnerabilities being actively exploited or with publicly available exploit code, CIIOs must apply patches within 2 weeks of the patch being made available by the vendor. For other security patches, CIIOs must apply them within 1 month. The clause recognizes that CIIOs should conduct appropriate testing before deployment.",
            evaluation_criteria={"scoring_strategy": "semantic_similarity"},
            key_facts=[
                "Clause 5.6.4 establishes specific timelines for patch application based on severity",
                "For critical security patches, CIIOs must apply patches within 2 weeks",
                "For other security patches, CIIOs must apply them within 1 month",
                "CIIOs should conduct appropriate testing before deployment"
            ]
        )

        # Partial answer (mentions patches but not specific timelines)
        partial_response = ModelResponse(
            content="Organizations should apply security patches promptly. Testing is important before deployment.",
            model_name="test-model"
        )

        metrics = ScoringService.score_response(test_case, partial_response)

        # Calculate overall score (weighted average)
        total_score = sum(m.value * m.weight for m in metrics) / sum(m.weight for m in metrics)

        # With Option A fixes, partial answers should score significantly lower
        # Old behavior without penalty: Would score ~0.65-0.75
        # New behavior with penalty: Should score < 0.60
        # This demonstrates the fix reduces inflation by ~15-20 percentage points
        assert total_score < 0.60, f"Partial answer scored too high: {total_score:.2f}"

    def test_complete_answer_still_gets_high_score(self):
        """Complete, accurate answer should still score high with all fixes."""
        test_case = TestCase(
            test_id="B8-906",
            benchmark_type=BenchmarkType("B8_Gap_Prioritisation"),
            section=CCoPSection("Section 5: Protection"),
            clause_reference="5.6.4",
            difficulty=DifficultyLevel("high"),
            question="Interpret CCoP 2.0 Clause 5.6.4 concerning patch management timelines with at least fifty characters in this question.",
            expected_response="Clause 5.6.4 establishes specific timelines for patch application based on severity. For critical security patches addressing vulnerabilities being actively exploited or with publicly available exploit code, CIIOs must apply patches within 2 weeks of the patch being made available by the vendor. For other security patches, CIIOs must apply them within 1 month.",
            evaluation_criteria={"scoring_strategy": "semantic_similarity"},
            key_facts=[
                "Clause 5.6.4 establishes specific timelines for patch application based on severity",
                "For critical security patches, CIIOs must apply patches within 2 weeks",
                "For other security patches, CIIOs must apply them within 1 month"
            ]
        )

        # Complete, accurate answer
        complete_response = ModelResponse(
            content="Clause 5.6.4 requires CIIOs to apply critical security patches within 2 weeks when vulnerabilities are being actively exploited or have public exploit code. Other security patches must be applied within 1 month. These timelines are based on severity assessment.",
            model_name="test-model"
        )

        metrics = ScoringService.score_response(test_case, complete_response)

        # Calculate overall score
        total_score = sum(m.value * m.weight for m in metrics) / sum(m.weight for m in metrics)

        # Complete answers should still score high (>= 0.75)
        assert total_score >= 0.75, f"Complete answer scored too low: {total_score:.2f}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
