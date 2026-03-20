"""
Tests for QualityGroup value object.

Validates metric group assignments, display names, and group lookups
after hallucination metric addition and faithfulness rename.
"""

import pytest

from domain.value_objects.quality_group import QualityGroup


class TestQualityGroupMetrics:
    """Test metric assignments in quality groups."""

    def test_grounding_group_has_context_faithfulness(self):
        """Model-RAG Grounding group contains context_faithfulness, not faithfulness."""
        groups = QualityGroup.get_all_groups()
        grounding = [g for g in groups if g.name == "Model-RAG Grounding"][0]

        assert "context_faithfulness" in grounding.metrics
        assert "faithfulness" not in grounding.metrics

    def test_response_quality_group_has_hallucination(self):
        """Model Response Quality group contains hallucination metric."""
        groups = QualityGroup.get_all_groups()
        response_quality = [g for g in groups if g.name == "Model Response Quality"][0]

        assert "hallucination" in response_quality.metrics

    def test_response_quality_group_has_all_expected_metrics(self):
        """Model Response Quality group contains hallucination, llm_judge, answer_correctness, answer_relevancy."""
        groups = QualityGroup.get_all_groups()
        response_quality = [g for g in groups if g.name == "Model Response Quality"][0]

        expected = ["hallucination", "llm_judge", "answer_correctness", "answer_relevancy"]
        assert response_quality.metrics == expected

    def test_retrieval_quality_group_unchanged(self):
        """Retrieval Quality group remains context_recall, context_precision."""
        groups = QualityGroup.get_all_groups()
        retrieval = [g for g in groups if g.name == "Retrieval Quality"][0]

        assert retrieval.metrics == ["context_recall", "context_precision"]

    def test_total_metrics_count_is_seven(self):
        """Total metrics across all groups is 7 (was 6 before hallucination)."""
        groups = QualityGroup.get_all_groups()
        total = sum(len(g.metrics) for g in groups)
        assert total == 7

    def test_faithfulness_not_in_any_group(self):
        """Bare 'faithfulness' should not appear in any group's metrics."""
        groups = QualityGroup.get_all_groups()
        all_metrics = [m for g in groups for m in g.metrics]
        assert "faithfulness" not in all_metrics


class TestQualityGroupDisplayNames:
    """Test display name mapping."""

    def test_context_faithfulness_display_name(self):
        """context_faithfulness maps to 'RAGAs: context_faithfulness'."""
        assert QualityGroup.get_display_name("context_faithfulness") == "RAGAs: context_faithfulness"

    def test_hallucination_display_name(self):
        """hallucination maps to 'RAGAs: hallucination'."""
        assert QualityGroup.get_display_name("hallucination") == "RAGAs: hallucination"

    def test_faithfulness_falls_through_to_default(self):
        """Bare 'faithfulness' should return itself (no mapping)."""
        assert QualityGroup.get_display_name("faithfulness") == "faithfulness"

    def test_existing_display_names_unchanged(self):
        """Existing metric display names remain correct."""
        assert QualityGroup.get_display_name("context_recall") == "RAGAs: context_recall"
        assert QualityGroup.get_display_name("context_precision") == "RAGAs: context_precision"
        assert QualityGroup.get_display_name("answer_correctness") == "RAGAs: answer_correctness"
        assert QualityGroup.get_display_name("answer_relevancy") == "RAGAs: answer_relevancy"
        assert QualityGroup.get_display_name("llm_judge") == "LLM Judge"


class TestQualityGroupLookup:
    """Test get_group_for_metric lookups."""

    def test_hallucination_in_response_quality(self):
        """hallucination belongs to Model Response Quality group."""
        group = QualityGroup.get_group_for_metric("hallucination")
        assert group is not None
        assert group.name == "Model Response Quality"

    def test_context_faithfulness_in_grounding(self):
        """context_faithfulness belongs to Model-RAG Grounding group."""
        group = QualityGroup.get_group_for_metric("context_faithfulness")
        assert group is not None
        assert group.name == "Model-RAG Grounding"

    def test_faithfulness_not_found(self):
        """Bare 'faithfulness' should not be found in any group."""
        group = QualityGroup.get_group_for_metric("faithfulness")
        assert group is None
