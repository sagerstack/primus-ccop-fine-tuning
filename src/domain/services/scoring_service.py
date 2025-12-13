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
        """Score B1 (CCoP Interpretation Accuracy) test case."""
        accuracy = ScoringService._calculate_basic_accuracy(test_case, response)
        completeness = ScoringService._calculate_completeness(test_case, response)
        return [accuracy, completeness]

    @staticmethod
    def _score_b2_citation(
        test_case: TestCase,
        response: ModelResponse
    ) -> List[EvaluationMetric]:
        """Score B2 (Clause Citation Accuracy) test case."""
        correct_citation = test_case.get_correct_citation()
        extracted_citations = response.extract_citations()

        citation_score = 0.0
        if correct_citation and correct_citation in extracted_citations:
            citation_score = 1.0
        elif correct_citation and any(
            correct_citation in cite for cite in extracted_citations
        ):
            citation_score = 0.7

        basic_accuracy = ScoringService._calculate_basic_accuracy(test_case, response)

        return [
            citation_accuracy_metric(citation_score),
            accuracy_metric(basic_accuracy.value),
        ]

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
        """Calculate completeness score."""
        if response.is_empty():
            return completeness_metric(0.0)

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
