"""
Unit tests for SemanticSimilarityService.

Tests semantic similarity computation using sentence transformers.
"""

import pytest

from domain.services.semantic_similarity_service import SemanticSimilarityService


class TestSemanticSimilarityService:
    """Test suite for SemanticSimilarityService."""

    def test_singleton_pattern(self) -> None:
        """Test that service uses singleton pattern for model caching."""
        service1 = SemanticSimilarityService()
        service2 = SemanticSimilarityService()

        assert service1 is service2
        assert service1._model is service2._model

    def test_calculate_similarity_identical_texts(self) -> None:
        """Test similarity score for identical texts."""
        service = SemanticSimilarityService()

        text = "CCoP 2.0 requires CIIOs to implement security monitoring"
        similarity = service.calculate_similarity(text, text)

        # Identical texts should have similarity close to 1.0
        assert similarity > 0.99

    def test_calculate_similarity_synonym_detection(self) -> None:
        """Test that semantic similarity detects synonyms."""
        service = SemanticSimilarityService()

        text1 = "CIIOs must implement security monitoring capabilities"
        text2 = "Security monitoring systems are required for CII operators"

        similarity = service.calculate_similarity(text1, text2)

        # Semantically similar texts should have high similarity
        # (higher than Jaccard word overlap would give)
        assert similarity > 0.6

    def test_calculate_similarity_different_topics(self) -> None:
        """Test similarity score for completely different topics."""
        service = SemanticSimilarityService()

        text1 = "CCoP 2.0 security monitoring requirements for CII"
        text2 = "Python programming language features and syntax"

        similarity = service.calculate_similarity(text1, text2)

        # Different topics should have low similarity
        assert similarity < 0.3

    def test_calculate_similarity_empty_strings(self) -> None:
        """Test handling of empty strings."""
        service = SemanticSimilarityService()

        assert service.calculate_similarity("", "some text") == 0.0
        assert service.calculate_similarity("some text", "") == 0.0
        assert service.calculate_similarity("", "") == 0.0

    def test_calculate_batch_similarity(self) -> None:
        """Test batch similarity calculation."""
        service = SemanticSimilarityService()

        expected = "CCoP 2.0 requires security monitoring"
        responses = [
            "Security monitoring is required by CCoP 2.0",
            "CCoP mandates monitoring systems",
            "Python programming language"
        ]

        similarities = service.calculate_batch_similarity(expected, responses)

        assert len(similarities) == 3
        assert all(0.0 <= s <= 1.0 for s in similarities)
        # First two responses should be more similar than the third
        assert similarities[0] > 0.6
        assert similarities[1] > 0.5
        assert similarities[2] < 0.3

    def test_calculate_batch_similarity_empty_responses(self) -> None:
        """Test batch similarity with empty responses."""
        service = SemanticSimilarityService()

        expected = "CCoP 2.0 requirements"
        responses: list[str] = []

        similarities = service.calculate_batch_similarity(expected, responses)

        assert similarities == []

    def test_calculate_batch_similarity_empty_expected(self) -> None:
        """Test batch similarity with empty expected text."""
        service = SemanticSimilarityService()

        expected = ""
        responses = ["text1", "text2"]

        similarities = service.calculate_batch_similarity(expected, responses)

        assert similarities == [0.0, 0.0]

    def test_similarity_range(self) -> None:
        """Test that similarity scores are always in valid range [0, 1]."""
        service = SemanticSimilarityService()

        test_pairs = [
            ("CCoP 2.0 security", "CCoP security requirements"),
            ("short", "long text with many words"),
            ("123 numbers", "abc letters"),
        ]

        for text1, text2 in test_pairs:
            similarity = service.calculate_similarity(text1, text2)
            assert 0.0 <= similarity <= 1.0
