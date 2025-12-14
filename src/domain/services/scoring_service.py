"""
Scoring Service

Domain service containing business logic for scoring model responses.
Stateless service with pure functions (no external dependencies).
"""

import re
from typing import List

from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.evaluation_metric import (
    EvaluationMetric,
    accuracy_metric,
    citation_accuracy_metric,
    classification_accuracy_metric,
    completeness_metric,
    hallucination_rate_metric,
    terminology_accuracy_metric,
    violation_detection_metric,
)


class ScoringService:
    """
    Domain service for scoring model responses against test cases.

    This is a stateless service containing domain logic that operates
    on entities but doesn't naturally belong to any single entity.
    """

    @staticmethod
    def score_response(
        test_case: TestCase,
        response: ModelResponse
    ) -> List[EvaluationMetric]:
        """
        Business rule: Score a model response based on benchmark type.

        Delegates to benchmark-specific scoring methods.

        Args:
            test_case: The test case
            response: The model response

        Returns:
            List of evaluation metrics
        """
        # Map benchmark short names to scoring functions
        # BenchmarkType supports string comparison via __eq__
        benchmark_scorers = {
            "B1": ScoringService._score_b1_interpretation,
            "B2": ScoringService._score_b2_citation,
            "B3": ScoringService._score_b3_hallucination,
            "B4": ScoringService._score_b4_terminology,
            "B5": ScoringService._score_b5_classification,
            "B6": ScoringService._score_b6_violation_detection,
            "B21": ScoringService._score_b3_hallucination,  # Tier 1: Binary hallucination detection
        }

        # Find scorer by checking if benchmark type matches each key
        for benchmark_key, scorer in benchmark_scorers.items():
            if test_case.benchmark_type == benchmark_key:
                return scorer(test_case, response)

        # Fallback: basic scoring for B7-B21 and unknown types
        return [ScoringService._calculate_basic_accuracy(test_case, response)]

    @staticmethod
    def _score_b1_interpretation(
        test_case: TestCase,
        response: ModelResponse
    ) -> List[EvaluationMetric]:
        """
        Score B1 (CCoP Applicability & Scope) test case.

        Phase 2: Uses label-based accuracy, key-fact completeness, and grounding checks.
        """
        # Determine accuracy strategy
        scoring_strategy = test_case.evaluation_criteria.get("scoring_strategy", "label_based")

        if scoring_strategy == "label_based" and test_case.expected_label:
            accuracy = ScoringService._calculate_label_accuracy(test_case, response)
        else:
            # Fallback to Jaccard similarity
            accuracy = ScoringService._calculate_basic_accuracy(test_case, response)

        # Completeness (uses key-fact recall if available)
        completeness = ScoringService._calculate_completeness(test_case, response)

        # Grounding check (Phase 2 safety metric)
        grounding = ScoringService._calculate_grounding_score(test_case, response)

        return [accuracy, completeness, grounding]

    @staticmethod
    def _score_b2_citation(
        test_case: TestCase,
        response: ModelResponse
    ) -> List[EvaluationMetric]:
        """
        Score B2 (Compliance Classification Accuracy) test case.

        B2 evaluates binary classification (Compliant/Non-Compliant) accuracy.
        Uses label-based scoring similar to B1.
        """
        # Determine accuracy strategy
        scoring_strategy = test_case.evaluation_criteria.get("scoring_strategy", "label_based")

        if scoring_strategy == "label_based" and test_case.expected_label:
            accuracy = ScoringService._calculate_label_accuracy(test_case, response)
        else:
            # Fallback to Jaccard similarity
            accuracy = ScoringService._calculate_basic_accuracy(test_case, response)

        # Completeness (uses key-fact recall if available)
        completeness = ScoringService._calculate_completeness(test_case, response)

        # Grounding check (Phase 2 safety metric)
        grounding = ScoringService._calculate_grounding_score(test_case, response)

        return [accuracy, completeness, grounding]

    @staticmethod
    def _score_b3_hallucination(
        test_case: TestCase,
        response: ModelResponse
    ) -> List[EvaluationMetric]:
        """Score B3 (Hallucination Rate) test case."""
        has_hallucination = response.contains_hallucination_indicators()
        hallucination_rate = 1.0 if has_hallucination else 0.0

        basic_accuracy = ScoringService._calculate_basic_accuracy(test_case, response)

        if has_hallucination:
            accuracy_value = min(basic_accuracy.value, 0.5)
        else:
            accuracy_value = basic_accuracy.value

        return [
            hallucination_rate_metric(hallucination_rate),
            accuracy_metric(accuracy_value),
        ]

    @staticmethod
    def _score_b4_terminology(
        test_case: TestCase,
        response: ModelResponse
    ) -> List[EvaluationMetric]:
        """Score B4 (Singapore Terminology) test case."""
        key_terms = test_case.get_key_terminology()
        if not key_terms:
            return [ScoringService._calculate_basic_accuracy(test_case, response)]

        response_lower = response.content.lower()
        found_terms = sum(
            1 for term in key_terms
            if term.lower() in response_lower
        )

        terminology_score = found_terms / len(key_terms) if key_terms else 0.0
        basic_accuracy = ScoringService._calculate_basic_accuracy(test_case, response)

        return [
            terminology_accuracy_metric(terminology_score),
            accuracy_metric(basic_accuracy.value),
        ]

    @staticmethod
    def _score_b5_classification(
        test_case: TestCase,
        response: ModelResponse
    ) -> List[EvaluationMetric]:
        """Score B5 (IT/OT Classification) test case."""
        expected_domain = test_case.domain
        response_lower = response.content.lower()

        classification_score = 0.0

        if expected_domain == "IT":
            if "information technology" in response_lower or " it " in response_lower:
                classification_score = 1.0
            elif "ot" in response_lower or "operational technology" in response_lower:
                classification_score = 0.0
            else:
                classification_score = 0.5

        elif expected_domain == "OT":
            if "operational technology" in response_lower or "ot" in response_lower:
                classification_score = 1.0
            elif "information technology" in response_lower and "operational" not in response_lower:
                classification_score = 0.0
            else:
                classification_score = 0.5

        elif expected_domain == "IT/OT":
            has_it = "information technology" in response_lower or " it " in response_lower
            has_ot = "operational technology" in response_lower or " ot " in response_lower
            if has_it and has_ot:
                classification_score = 1.0
            elif has_it or has_ot:
                classification_score = 0.7
            else:
                classification_score = 0.5

        basic_accuracy = ScoringService._calculate_basic_accuracy(test_case, response)

        return [
            classification_accuracy_metric(classification_score),
            accuracy_metric(basic_accuracy.value),
        ]

    @staticmethod
    def _score_b6_violation_detection(
        test_case: TestCase,
        response: ModelResponse
    ) -> List[EvaluationMetric]:
        """Score B6 (Code Violation Detection) test case."""
        expected_violations = test_case.get_expected_violations()
        if not expected_violations:
            return [ScoringService._calculate_basic_accuracy(test_case, response)]

        response_lower = response.content.lower()
        detected_violations = sum(
            1 for violation in expected_violations
            if violation.lower() in response_lower
        )

        detection_score = (
            detected_violations / len(expected_violations)
            if expected_violations else 0.0
        )

        has_code_analysis = response.contains_code_snippet()
        completeness_score = 1.0 if has_code_analysis else 0.7

        return [
            violation_detection_metric(detection_score),
            completeness_metric(completeness_score),
        ]

    @staticmethod
    def _calculate_basic_accuracy(
        test_case: TestCase,
        response: ModelResponse
    ) -> EvaluationMetric:
        """Calculate basic accuracy using simple text similarity."""
        if response.is_empty():
            return accuracy_metric(0.0)

        expected_words = set(
            re.findall(r'\w+', test_case.expected_response.lower())
        )
        response_words = set(
            re.findall(r'\w+', response.content.lower())
        )

        if not expected_words and not response_words:
            return accuracy_metric(0.0)

        intersection = len(expected_words & response_words)
        union = len(expected_words | response_words)

        similarity = intersection / union if union > 0 else 0.0
        return accuracy_metric(similarity)

    @staticmethod
    def _calculate_completeness(
        test_case: TestCase,
        response: ModelResponse
    ) -> EvaluationMetric:
        """
        Calculate completeness score.

        Phase 2: Uses key-fact recall if available, otherwise falls back to sentence-based.
        """
        if response.is_empty():
            return completeness_metric(0.0)

        # Phase 2: Use key-fact recall if available
        if test_case.key_facts and len(test_case.key_facts) > 0:
            return ScoringService._calculate_key_fact_completeness(test_case, response)

        # Legacy: Sentence-based completeness (backward compatible)
        return ScoringService._calculate_sentence_completeness(test_case, response)

    @staticmethod
    def _calculate_key_fact_completeness(
        test_case: TestCase,
        response: ModelResponse
    ) -> EvaluationMetric:
        """
        Phase 2: Key-fact recall completeness.

        Measures coverage of required regulatory facts.
        """
        key_facts = test_case.key_facts
        if not key_facts:
            return completeness_metric(0.0)

        response_lower = response.content.lower()
        covered_facts = 0

        for fact in key_facts:
            # Extract key terms (words > 4 chars)
            key_terms = [w for w in re.findall(r'\w+', fact.lower()) if len(w) > 4]

            # Check if majority of key terms present (60% threshold)
            if key_terms:
                matches = sum(1 for term in key_terms if term in response_lower)
                if matches / len(key_terms) >= 0.6:
                    covered_facts += 1

        completeness_score = covered_facts / len(key_facts)
        return completeness_metric(completeness_score)

    @staticmethod
    def _calculate_sentence_completeness(
        test_case: TestCase,
        response: ModelResponse
    ) -> EvaluationMetric:
        """Legacy: Sentence-based completeness (backward compatible)."""
        expected_sentences = [
            s.strip()
            for s in re.split(r'[.!?]', test_case.expected_response)
            if s.strip()
        ]

        if not expected_sentences:
            return completeness_metric(0.5)

        response_lower = response.content.lower()
        covered_points = 0

        for sentence in expected_sentences:
            key_words = [
                w for w in re.findall(r'\w+', sentence.lower())
                if len(w) > 4
            ]

            if key_words and any(word in response_lower for word in key_words):
                covered_points += 1

        completeness_score = covered_points / len(expected_sentences) if expected_sentences else 0.0
        return completeness_metric(completeness_score)

    @staticmethod
    def _calculate_label_accuracy(
        test_case: TestCase,
        response: ModelResponse
    ) -> EvaluationMetric:
        """
        Phase 2: Label-based accuracy for classification benchmarks.

        Checks if response contains the expected classification label.
        """
        expected_label = test_case.expected_label
        if not expected_label:
            # Fallback to Jaccard if no label provided
            return ScoringService._calculate_basic_accuracy(test_case, response)

        response_lower = response.content.lower()
        expected_lower = expected_label.lower()

        # Exact match
        if expected_lower in response_lower:
            return accuracy_metric(1.0)

        # Check for partial match (key components)
        # Split by semicolon, colon, or "and"
        label_components = re.split(r'[;:]|\band\b', expected_label)
        label_components = [comp.strip() for comp in label_components if comp.strip()]

        if not label_components:
            return accuracy_metric(0.0)

        matches = sum(1 for comp in label_components if comp.strip().lower() in response_lower)

        if matches == len(label_components):
            return accuracy_metric(1.0)  # All components present
        elif matches / len(label_components) >= 0.6:
            return accuracy_metric(0.7)  # Partial credit (60%+ components)
        else:
            return accuracy_metric(0.0)  # Incorrect

    @staticmethod
    def _calculate_grounding_score(
        test_case: TestCase,
        response: ModelResponse
    ) -> EvaluationMetric:
        """
        Phase 2: Regulatory grounding check (safety metric).

        Detects fabricated CCoP claims, not uncertainty language.
        Uncertainty ("may", "depends", "should consider") is acceptable.
        """
        if response.is_empty():
            return EvaluationMetric(name="grounding", value=1.0, weight=1.0)

        response_lower = response.content.lower()
        violations = 0

        # Check forbidden claims from test case
        for claim in test_case.forbidden_claims:
            if claim.lower() in response_lower:
                violations += 1

        # Check for common hallucination patterns (from B1 analysis)
        hallucination_patterns = [
            r"cryptography.*implementation.*officer",
            r"cryptography.*incident.*reporting.*officer",
            r"cybersecurity classification guide",
            r"ciio.*stands for.*cryptography",
            r"ccop.*requires.*\w+.*that does not exist",
        ]

        for pattern in hallucination_patterns:
            if re.search(pattern, response_lower):
                violations += 1

        # Scoring
        if violations == 0:
            return EvaluationMetric(name="grounding", value=1.0, weight=1.0, description="No fabricated claims")
        elif violations <= 2:
            return EvaluationMetric(name="grounding", value=0.7, weight=1.0, description="Minor grounding issues")
        else:
            return EvaluationMetric(name="grounding", value=0.0, weight=1.0, description="Multiple fabricated claims")
