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

    def test_response_quality_group_has_factual_precision(self):
        """Model Response Quality group contains factual_precision metric."""
        groups = QualityGroup.get_all_groups()
        response_quality = [g for g in groups if g.name == "Model Response Quality"][0]

        assert "factual_precision" in response_quality.metrics

    def test_response_quality_group_has_all_expected_metrics(self):
        """Model Response Quality group contains factual_precision, factual_recall, answer_relevancy, semantic_similarity, llm_judge."""
        groups = QualityGroup.get_all_groups()
        response_quality = [g for g in groups if g.name == "Model Response Quality"][0]

        expected = ["factual_precision", "factual_recall", "answer_relevancy", "semantic_similarity", "llm_judge"]
        assert response_quality.metrics == expected

    def test_retrieval_quality_group_unchanged(self):
        """Retrieval Quality group remains context_recall, context_precision."""
        groups = QualityGroup.get_all_groups()
        retrieval = [g for g in groups if g.name == "Retrieval Quality"][0]

        assert retrieval.metrics == ["context_recall", "context_precision"]

    def test_total_metrics_count_is_eight(self):
        """Total metrics across all groups is 8 (was 6 before split)."""
        groups = QualityGroup.get_all_groups()
        total = sum(len(g.metrics) for g in groups)
        assert total == 8

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

    def test_factual_precision_display_name(self):
        """factual_precision maps to 'RAGAs: factual_precision'."""
        assert QualityGroup.get_display_name("factual_precision") == "RAGAs: factual_precision"

    def test_factual_recall_display_name(self):
        """factual_recall maps to 'RAGAs: factual_recall'."""
        assert QualityGroup.get_display_name("factual_recall") == "RAGAs: factual_recall"

    def test_semantic_similarity_display_name(self):
        """semantic_similarity maps to 'RAGAs: semantic_similarity'."""
        assert QualityGroup.get_display_name("semantic_similarity") == "RAGAs: semantic_similarity"

    def test_faithfulness_falls_through_to_default(self):
        """Bare 'faithfulness' should return itself (no mapping)."""
        assert QualityGroup.get_display_name("faithfulness") == "faithfulness"

    def test_existing_display_names_unchanged(self):
        """Existing metric display names remain correct."""
        assert QualityGroup.get_display_name("context_recall") == "RAGAs: context_recall"
        assert QualityGroup.get_display_name("context_precision") == "RAGAs: context_precision"
        assert QualityGroup.get_display_name("answer_relevancy") == "RAGAs: answer_relevancy"
        assert QualityGroup.get_display_name("llm_judge") == "LLM Judge"

    def test_answer_correctness_falls_through(self):
        """answer_correctness falls through to default (no mapping, returns raw)."""
        assert QualityGroup.get_display_name("answer_correctness") == "answer_correctness"

    def test_hallucination_falls_through(self):
        """hallucination falls through to default (no mapping, returns raw)."""
        assert QualityGroup.get_display_name("hallucination") == "hallucination"


class TestQualityGroupLookup:
    """Test get_group_for_metric lookups."""

    def test_factual_precision_in_response_quality(self):
        """factual_precision belongs to Model Response Quality group."""
        group = QualityGroup.get_group_for_metric("factual_precision")
        assert group is not None
        assert group.name == "Model Response Quality"

    def test_factual_recall_in_response_quality(self):
        """factual_recall belongs to Model Response Quality group."""
        group = QualityGroup.get_group_for_metric("factual_recall")
        assert group is not None
        assert group.name == "Model Response Quality"

    def test_semantic_similarity_in_response_quality(self):
        """semantic_similarity belongs to Model Response Quality group."""
        group = QualityGroup.get_group_for_metric("semantic_similarity")
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

    def test_hallucination_not_found(self):
        """hallucination should not be found in any group (replaced by factual_precision)."""
        group = QualityGroup.get_group_for_metric("hallucination")
        assert group is None

    def test_answer_correctness_not_found(self):
        """answer_correctness should not be found in any group (split into precision/recall)."""
        group = QualityGroup.get_group_for_metric("answer_correctness")
        assert group is None
