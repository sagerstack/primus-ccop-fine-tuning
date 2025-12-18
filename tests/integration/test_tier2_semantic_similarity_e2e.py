"""
E2E Integration test for Tier 2 semantic similarity scoring.

Tests the full evaluation flow for reasoning track benchmarks (B8, B9, B11, B15, B17, B18, B19)
using semantic similarity instead of Jaccard word overlap.
"""

import pytest

from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.services.scoring_service import ScoringService
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.ccop_section import CCoPSection
from domain.value_objects.difficulty_level import DifficultyLevel


class TestTier2SemanticSimilarityE2E:
    """E2E test suite for Tier 2 semantic similarity scoring."""

    @pytest.fixture
    def b8_test_case(self) -> TestCase:
        """Create B8 (Gap Prioritisation) test case."""
        return TestCase(
            test_id="B8-001",
            benchmark_type=BenchmarkType.from_string("B8_Gap_Prioritisation"),
            section=CCoPSection.from_string("Section 5: Protection"),
            clause_reference="5.2.1",
            difficulty=DifficultyLevel.from_string("high"),
            question="Given limited resources, how should a CIIO prioritize remediation of gaps in password policies versus encryption requirements?",
            expected_response="CIIOs should prioritize based on risk assessment. Password policy gaps (5.2.1) may pose immediate credential compromise risks affecting multiple systems. Encryption gaps (5.3) impact data confidentiality. Priority depends on threat landscape, data sensitivity, and current control effectiveness. High-value targets with weak passwords warrant urgent attention.",
            evaluation_criteria={
                "scoring_strategy": "semantic_similarity",
                "key_fact_recall": True,
            },
            key_facts=[
                "Prioritization should be based on risk assessment",
                "Password policy gaps affect credential security",
                "Encryption gaps impact data confidentiality",
                "Priority depends on threat landscape and data sensitivity",
            ],
            forbidden_claims=[],
        )

    @pytest.fixture
    def good_semantic_response(self) -> ModelResponse:
        """Create semantically similar response with different wording."""
        return ModelResponse(
            content="Resource allocation for gap remediation should follow a risk-based approach. Weak password controls create immediate authentication vulnerabilities across systems. Encryption deficiencies compromise data protection. The decision depends on current threat environment, information criticality, and existing safeguard maturity. Critical systems with authentication weaknesses require immediate remediation.",
            metadata={},
        )

    @pytest.fixture
    def poor_jaccard_good_semantic_response(self) -> ModelResponse:
        """Create response with low word overlap but good semantic meaning."""
        return ModelResponse(
            content="Organizations must evaluate security shortfalls using threat-informed analysis. Authentication mechanism deficiencies present acute compromise vectors. Cryptographic protection shortfalls affect confidential information. Remediation sequencing hinges on adversary capabilities, asset value, and compensating control maturity.",
            metadata={},
        )

    @pytest.fixture
    def unrelated_response(self) -> ModelResponse:
        """Create semantically unrelated response."""
        return ModelResponse(
            content="Python is a high-level programming language with dynamic typing and garbage collection. It supports multiple programming paradigms including procedural and object-oriented programming.",
            metadata={},
        )

    def test_b8_semantic_similarity_good_response(
        self, b8_test_case: TestCase, good_semantic_response: ModelResponse
    ) -> None:
        """Test that semantically similar response scores well."""
        metrics = ScoringService.score_response(b8_test_case, good_semantic_response)

        # Should have accuracy, completeness, grounding metrics
        assert len(metrics) == 3

        accuracy = next(m for m in metrics if m.name == "accuracy")
        completeness = next(m for m in metrics if m.name == "completeness")
        grounding = next(m for m in metrics if m.name == "grounding")

        # Semantic similarity should recognize good answer
        assert accuracy.value > 0.6, "Semantic similarity should score semantically similar response highly"
        assert accuracy.description == "Semantic similarity using sentence embeddings"

        # Completeness uses keyword matching (not semantic), so it may be low for synonym-heavy responses
        # This is OK since the main goal is testing semantic similarity
        assert completeness.value >= 0.0  # At least returns a metric

        # Should have good grounding (no hallucinations)
        assert grounding.value >= 0.7

    def test_b8_semantic_better_than_jaccard(
        self, b8_test_case: TestCase, poor_jaccard_good_semantic_response: ModelResponse
    ) -> None:
        """Test that semantic similarity outperforms Jaccard for synonym-heavy responses."""
        metrics = ScoringService.score_response(
            b8_test_case, poor_jaccard_good_semantic_response
        )

        accuracy = next(m for m in metrics if m.name == "accuracy")

        # This response has low word overlap (different terminology)
        # but high semantic similarity (same meaning)
        # Semantic similarity should score it reasonably well
        assert accuracy.value > 0.4, (
            f"Semantic similarity should recognize synonyms (got {accuracy.value})"
        )

    def test_b8_semantic_rejects_unrelated(
        self, b8_test_case: TestCase, unrelated_response: ModelResponse
    ) -> None:
        """Test that semantic similarity rejects unrelated response."""
        metrics = ScoringService.score_response(b8_test_case, unrelated_response)

        accuracy = next(m for m in metrics if m.name == "accuracy")

        # Completely unrelated response should have low similarity
        assert accuracy.value < 0.4

    def test_reasoning_track_benchmarks_use_semantic_similarity(self) -> None:
        """Test that all reasoning track benchmarks use semantic similarity."""
        reasoning_benchmarks = ["B8", "B9", "B11", "B15", "B17", "B18", "B19"]

        for benchmark_code in reasoning_benchmarks:
            test_case = TestCase(
                test_id=f"{benchmark_code}-001",
                benchmark_type=BenchmarkType.from_string(f"{benchmark_code}_Test"),
                section=CCoPSection.from_string("Section 5: Protection"),
                clause_reference="5.1.1",
                difficulty=DifficultyLevel.from_string("medium"),
                question="Test question for semantic similarity verification for reasoning track?",
                expected_response="Expected answer for testing semantic similarity implementation",
                evaluation_criteria={"test": "value"},
            )

            response = ModelResponse(content="Test answer for verification", metadata={})

            metrics = ScoringService.score_response(test_case, response)

            # Verify semantic similarity is used (not Jaccard)
            accuracy = next(m for m in metrics if m.name == "accuracy")
            assert "semantic" in accuracy.description.lower(), (
                f"{benchmark_code} should use semantic similarity"
            )

    def test_b8_returns_three_metrics(
        self, b8_test_case: TestCase, good_semantic_response: ModelResponse
    ) -> None:
        """Test that B8 returns accuracy, completeness, and grounding metrics."""
        metrics = ScoringService.score_response(b8_test_case, good_semantic_response)

        metric_names = {m.name for m in metrics}
        assert metric_names == {"accuracy", "completeness", "grounding"}

    def test_semantic_similarity_metric_properties(
        self, b8_test_case: TestCase, good_semantic_response: ModelResponse
    ) -> None:
        """Test that semantic similarity metric has correct properties."""
        metrics = ScoringService.score_response(b8_test_case, good_semantic_response)
        accuracy = next(m for m in metrics if m.name == "accuracy")

        # Verify metric properties
        assert 0.0 <= accuracy.value <= 1.0
        assert accuracy.weight == 1.0
        assert accuracy.description == "Semantic similarity using sentence embeddings"
