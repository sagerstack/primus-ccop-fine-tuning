"""
Critical path tests for ModelResponse entity.

Tests implemented functionality: citation extraction and hallucination detection.
"""
import pytest

from domain.entities.model_response import ModelResponse


class TestModelResponse:
    """Tests for ModelResponse entity - implemented functionality only."""

    def test_extract_citations(self):
        """CRITICAL: Extract section citations from response text."""
        response = ModelResponse(
            content="According to Section 13.1 and Section 9.2, organizations must...",
            model_name="test-model",
            tokens_used=20,
            latency_ms=1000,
        )

        citations = response.extract_citations()
        assert "13.1" in citations
        assert "9.2" in citations
        assert len(citations) == 2

    def test_detect_hallucination_indicators(self):
        """CRITICAL: Detect potential hallucination markers."""
        hallucination_response = ModelResponse(
            content="I'm not sure but the blockchain-powered quantum AI solution might enhance security.",
            model_name="test-model",
            tokens_used=15,
            latency_ms=1000,
        )

        # Should detect hedging words like "I'm not sure" and "might"
        has_hallucination = hallucination_response.contains_hallucination_indicators()
        assert has_hallucination is True

        # Clean response should not have indicators
        clean_response = ModelResponse(
            content="Organizations must implement cybersecurity controls as specified in CCoP 2.0.",
            model_name="test-model",
            tokens_used=15,
            latency_ms=1000,
        )
        has_hallucination_clean = clean_response.contains_hallucination_indicators()
        assert has_hallucination_clean is False
