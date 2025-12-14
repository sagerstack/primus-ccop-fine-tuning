"""
Evaluation Tier Value Object

Defines the 4-tier evaluation system for benchmark classification.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class EvaluationTier:
    """
    Value object representing an evaluation tier.

    Tiers define the scoring methodology used for groups of benchmarks.
    """

    tier_number: int
    name: str
    benchmarks: List[str]
    description: str
    automation_level: str

    @staticmethod
    def get_all_tiers() -> List['EvaluationTier']:
        """
        Get all 4 evaluation tiers as defined in the tier system.

        Returns:
            List of all evaluation tiers
        """
        return [
            EvaluationTier(
                tier_number=1,
                name="Binary Metrics",
                benchmarks=["B1", "B2", "B21"],
                description="Deterministic evaluation for classification tasks with clear right/wrong answers",
                automation_level="100% automated"
            ),
            EvaluationTier(
                tier_number=2,
                name="Expert Rubric",
                benchmarks=["B7", "B10", "B14", "B16"],
                description="Human expert evaluation for complex analytical tasks (1-5 scale, 4 dimensions)",
                automation_level="0% automated - requires expert review"
            ),
            EvaluationTier(
                tier_number=3,
                name="LLM-as-Judge",
                benchmarks=["B12", "B13", "B20"],
                description="Scalable AI-assisted evaluation with mandatory ≥20% human validation",
                automation_level="~80% automated"
            ),
            # Reasoning Track is separate from numbered tiers but included for completeness
        ]

    @staticmethod
    def get_reasoning_track_benchmarks() -> List[str]:
        """
        Get benchmarks in the Reasoning Track (semantic + key-fact recall).

        Returns:
            List of benchmark IDs in Reasoning Track
        """
        return ["B3", "B4", "B5", "B6", "B8", "B9", "B11", "B15", "B17", "B18", "B19"]

    @staticmethod
    def get_benchmarks_for_tier(tier_number: int) -> List[str]:
        """
        Get benchmarks for a specific tier number.

        Args:
            tier_number: Tier number (1, 2, or 3)

        Returns:
            List of benchmark IDs in this tier
        """
        for tier in EvaluationTier.get_all_tiers():
            if tier.tier_number == tier_number:
                return tier.benchmarks
        return []

    @staticmethod
    def get_tier_for_benchmark(benchmark: str) -> Optional[int]:
        """
        Get the tier number that contains the specified benchmark.

        Args:
            benchmark: Benchmark short name (e.g., "B1")

        Returns:
            Tier number (1, 2, 3) or None if in Reasoning Track or not found
        """
        for tier in EvaluationTier.get_all_tiers():
            if benchmark in tier.benchmarks:
                return tier.tier_number

        # Check if in Reasoning Track
        if benchmark in EvaluationTier.get_reasoning_track_benchmarks():
            return None  # Reasoning Track is separate from numbered tiers

        return None

    @staticmethod
    def get_tier_name(tier_number: int) -> Optional[str]:
        """
        Get the name of a tier by its number.

        Args:
            tier_number: Tier number (1, 2, or 3)

        Returns:
            Tier name or None if not found
        """
        for tier in EvaluationTier.get_all_tiers():
            if tier.tier_number == tier_number:
                return tier.name
        return None
