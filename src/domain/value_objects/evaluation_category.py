"""
Evaluation Category Value Object

Defines the 5 evaluation categories with their weights and benchmark mappings.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class EvaluationCategory:
    """
    Value object representing an evaluation category.

    Categories define groups of benchmarks evaluated together with a specific weight
    in the overall evaluation score calculation.
    """

    name: str
    weight: float
    benchmarks: List[str]
    description: str

    @staticmethod
    def get_all_categories() -> List['EvaluationCategory']:
        """
        Get all 5 evaluation categories as defined in the evaluation framework.

        Returns:
            List of all evaluation categories with their weights
        """
        return [
            EvaluationCategory(
                name="Regulatory Applicability & Interpretation",
                weight=0.25,
                benchmarks=["B1", "B2", "B3", "B4", "B5"],
                description="Ensures correct understanding of CCoP scope, terminology, and core requirements"
            ),
            EvaluationCategory(
                name="Compliance & Risk Reasoning",
                weight=0.25,
                benchmarks=["B6", "B7", "B8", "B9", "B10", "B11", "B12"],
                description="Primary focus of fine-tuning; gap identification, risk reasoning, and audit-style judgement"
            ),
            EvaluationCategory(
                name="Remediation & Audit Reasoning",
                weight=0.20,
                benchmarks=["B13", "B14", "B15", "B16"],
                description="Assesses practical remediation quality and alignment with audit expectations"
            ),
            EvaluationCategory(
                name="Governance & Consistency (SG Context)",
                weight=0.10,
                benchmarks=["B17", "B18", "B19"],
                description="Validates responsibility attribution and stable reasoning within Singapore's CII governance"
            ),
            EvaluationCategory(
                name="Safety & Regulatory Grounding",
                weight=0.20,
                benchmarks=["B20", "B21"],
                description="Prevents hallucinated or over-specified regulatory claims"
            ),
        ]

    @staticmethod
    def get_category_for_benchmark(benchmark: str) -> Optional['EvaluationCategory']:
        """
        Get the category that contains the specified benchmark.

        Args:
            benchmark: Benchmark short name (e.g., "B1")

        Returns:
            The category containing this benchmark, or None if not found
        """
        for category in EvaluationCategory.get_all_categories():
            if benchmark in category.benchmarks:
                return category
        return None

    @staticmethod
    def get_category_weights() -> Dict[str, float]:
        """
        Get a dictionary mapping category names to their weights.

        Returns:
            Dictionary of {category_name: weight}
        """
        return {
            cat.name: cat.weight
            for cat in EvaluationCategory.get_all_categories()
        }
