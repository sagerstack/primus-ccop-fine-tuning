"""
Evaluation Metric Value Object

Represents scoring metrics for model evaluation results.
Immutable value object containing score and metadata.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EvaluationMetric:
    """
    Value object representing a single evaluation metric.

    This is immutable (frozen=True) and identified by its values,
    not by identity.

    Attributes:
        name: Metric name (e.g., "accuracy", "precision", "recall")
        value: Metric value (0.0 to 1.0)
        weight: Weight for overall score calculation (0.0 to 1.0)
        description: Optional human-readable description
    """

    name: str
    value: float
    weight: float = 1.0
    description: Optional[str] = None

    def __post_init__(self) -> None:
        """
        Validate metric values after initialization.

        Business rules:
        - value must be between 0.0 and 1.0
        - weight must be between 0.0 and 1.0
        - name cannot be empty
        """
        if not self.name or not self.name.strip():
            raise ValueError("Metric name cannot be empty")

        if not 0.0 <= self.value <= 1.0:
            raise ValueError(
                f"Metric value must be between 0.0 and 1.0, got {self.value}"
            )

        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(
                f"Metric weight must be between 0.0 and 1.0, got {self.weight}"
            )

    @property
    def weighted_value(self) -> float:
        """Calculate weighted value for score aggregation."""
        return self.value * self.weight

    @property
    def percentage(self) -> float:
        """Get value as percentage (0-100)."""
        return self.value * 100

    def is_passing(self, threshold: float = 0.7) -> bool:
        """
        Business rule: Check if metric value meets threshold.

        Args:
            threshold: Minimum acceptable value (default: 0.7 = 70%)

        Returns:
            True if value >= threshold
        """
        return self.value >= threshold

    def __str__(self) -> str:
        return f"{self.name}: {self.percentage:.1f}%"

    def __repr__(self) -> str:
        return (
            f"EvaluationMetric(name='{self.name}', "
            f"value={self.value:.3f}, weight={self.weight})"
        )


# Common metric constructors for convenience
def accuracy_metric(value: float) -> EvaluationMetric:
    """Create accuracy metric."""
    return EvaluationMetric(
        name="accuracy",
        value=value,
        weight=1.0,
        description="Overall correctness of the response"
    )


def completeness_metric(value: float) -> EvaluationMetric:
    """Create completeness metric."""
    return EvaluationMetric(
        name="completeness",
        value=value,
        weight=0.8,
        description="Coverage of all required points"
    )


def citation_accuracy_metric(value: float) -> EvaluationMetric:
    """Create citation accuracy metric."""
    return EvaluationMetric(
        name="citation_accuracy",
        value=value,
        weight=1.0,
        description="Accuracy of clause references"
    )


def hallucination_rate_metric(value: float) -> EvaluationMetric:
    """
    Create hallucination rate metric.

    Note: Lower is better for hallucination, but stored as (1 - rate)
    to maintain consistency where higher = better.
    """
    return EvaluationMetric(
        name="hallucination_resistance",
        value=1.0 - value,  # Invert so higher is better
        weight=1.0,
        description="Resistance to generating false information"
    )


def terminology_accuracy_metric(value: float) -> EvaluationMetric:
    """Create terminology accuracy metric."""
    return EvaluationMetric(
        name="terminology_accuracy",
        value=value,
        weight=0.9,
        description="Correct use of Singapore-specific terminology"
    )


def classification_accuracy_metric(value: float) -> EvaluationMetric:
    """Create IT/OT classification accuracy metric."""
    return EvaluationMetric(
        name="classification_accuracy",
        value=value,
        weight=1.0,
        description="Accuracy of IT/OT infrastructure classification"
    )


def violation_detection_metric(value: float) -> EvaluationMetric:
    """Create code violation detection metric."""
    return EvaluationMetric(
        name="violation_detection",
        value=value,
        weight=1.0,
        description="Accuracy of identifying code violations"
    )
