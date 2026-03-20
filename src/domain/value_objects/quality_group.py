"""
Quality Group Value Object

Defines the 3 quality diagnostic groups for categorizing evaluation metrics.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class QualityGroup:
    """
    Value object representing a quality diagnostic group.

    Quality groups categorize the 6 evaluation metrics into 3 diagnostic areas:
    - Retrieval Quality: How well the retriever finds relevant context
    - Model-RAG Grounding: How faithfully the model uses retrieved context
    - Model Response Quality: How correct, relevant, and well-structured the response is
    """

    name: str
    metrics: List[str]
    description: str

    @staticmethod
    def get_all_groups() -> List['QualityGroup']:
        """
        Get all 3 quality groups with their metric mappings.

        Returns:
            List of all quality groups
        """
        return [
            QualityGroup(
                name="Retrieval Quality",
                metrics=["context_recall", "context_precision"],
                description="How well the retriever finds relevant context from the knowledge base"
            ),
            QualityGroup(
                name="Model-RAG Grounding",
                metrics=["context_faithfulness"],
                description="How faithfully the model uses retrieved context in its response"
            ),
            QualityGroup(
                name="Model Response Quality",
                metrics=["hallucination", "llm_judge", "answer_correctness", "answer_relevancy"],
                description="How correct, relevant, and well-structured the model response is"
            ),
        ]

    @staticmethod
    def get_group_for_metric(metric_name: str) -> Optional['QualityGroup']:
        """
        Find which quality group a metric belongs to.

        Args:
            metric_name: Metric name to search for

        Returns:
            The quality group containing this metric, or None if not found
        """
        for group in QualityGroup.get_all_groups():
            if metric_name in group.metrics:
                return group
        return None

    @staticmethod
    def get_rag_only_groups() -> List[str]:
        """
        Get the names of quality groups that only apply to RAG mode.

        These groups show "N/A" in llm-only mode.

        Returns:
            List of group names that require RAG
        """
        return ["Retrieval Quality", "Model-RAG Grounding"]

    @staticmethod
    def get_display_name(metric_name: str) -> str:
        """
        Get the display name for a metric.

        Maps internal metric names to user-facing display names.

        Args:
            metric_name: Internal metric name

        Returns:
            Display name for the metric
        """
        display_names = {
            "context_recall": "RAGAs: context_recall",
            "context_precision": "RAGAs: context_precision",
            "context_faithfulness": "RAGAs: context_faithfulness",
            "hallucination": "RAGAs: hallucination",
            "answer_correctness": "RAGAs: answer_correctness",
            "answer_relevancy": "RAGAs: answer_relevancy",
            "llm_judge": "LLM Judge",
        }
        return display_names.get(metric_name, metric_name)
