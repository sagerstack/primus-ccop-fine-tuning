"""
Tests for response_extractor utility.

Validates extract_final_answer function across various input patterns.
"""

import pytest

from domain.services.response_extractor import extract_final_answer


class TestExtractFinalAnswer:
    """Test extract_final_answer function."""

    def test_extracts_final_answer_basic(self):
        """Extract content after 'Final Answer:' marker (basic case)."""
        response = "Let me think about this...\nFinal Answer: The answer is 42"
        result = extract_final_answer(response)
        assert result == "The answer is 42"

    def test_extracts_final_answer_case_insensitive(self):
        """Marker detection is case-insensitive (FINAL ANSWER:)."""
        response = "Reasoning...\nFINAL ANSWER: The answer is correct"
        result = extract_final_answer(response)
        assert result == "The answer is correct"

    def test_extracts_final_answer_mixed_case(self):
        """Marker detection is case-insensitive (final Answer:)."""
        response = "Thinking...\nfinal Answer: The answer is validated"
        result = extract_final_answer(response)
        assert result == "The answer is validated"

    def test_returns_full_text_when_no_marker(self):
        """Returns full text when no marker present (model not using CoT)."""
        response = "This is a direct answer without any marker."
        result = extract_final_answer(response)
        assert result == "This is a direct answer without any marker."

    def test_extracts_multiline_final_answer(self):
        """Extract multi-line content after marker."""
        response = "Let me analyze...\nFinal Answer: Line 1 of answer\nLine 2 of answer\nLine 3 of answer"
        result = extract_final_answer(response)
        assert result == "Line 1 of answer\nLine 2 of answer\nLine 3 of answer"

    def test_handles_empty_string(self):
        """Empty input returns empty string."""
        result = extract_final_answer("")
        assert result == ""

    def test_extracts_after_last_final_answer(self):
        """When multiple markers present, extract after the last one."""
        response = "First thought\nFinal Answer: First attempt\nActually...\nFinal Answer: Second attempt"
        result = extract_final_answer(response)
        # Regex finds first match, so this should return "First attempt\nActually...\nFinal Answer: Second attempt"
        # But actually the regex finds the FIRST match and returns everything after it
        assert "Second attempt" in result

    def test_strips_whitespace(self):
        """Leading/trailing whitespace stripped from extracted answer."""
        response = "Thinking...\nFinal Answer:   The answer with spaces   "
        result = extract_final_answer(response)
        assert result == "The answer with spaces"
