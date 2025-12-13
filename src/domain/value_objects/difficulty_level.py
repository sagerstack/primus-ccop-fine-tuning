"""
Difficulty Level Value Object

Represents the complexity level of a test case:
- LOW: Basic understanding questions
- MEDIUM: Intermediate application questions
- HIGH: Complex analysis and cross-referencing
- CRITICAL: Advanced scenarios requiring deep domain knowledge
"""

from enum import Enum


class DifficultyLevel(str, Enum):
    """
    Enumeration of test case difficulty levels.

    This is a Value Object - immutable and identified by value, not identity.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_string(cls, value: str) -> "DifficultyLevel":
        """
        Convert string to DifficultyLevel enum.

        Args:
            value: String representation (e.g., "low", "LOW", "Low")

        Returns:
            DifficultyLevel enum value

        Raises:
            ValueError: If value is not a valid difficulty level
        """
        normalized = value.lower().strip()
        try:
            return cls(normalized)
        except ValueError:
            valid_values = ", ".join([d.value for d in cls])
            raise ValueError(
                f"Invalid difficulty level: '{value}'. "
                f"Valid values: {valid_values}"
            )

    @property
    def max_tokens(self) -> int:
        """
        Business rule: Maximum tokens allowed for response based on difficulty.

        - LOW: Simple answers (256 tokens)
        - MEDIUM: Moderate detail (512 tokens)
        - HIGH: Detailed analysis (1024 tokens)
        - CRITICAL: Comprehensive responses (2048 tokens)
        """
        token_limits = {
            DifficultyLevel.LOW: 256,
            DifficultyLevel.MEDIUM: 512,
            DifficultyLevel.HIGH: 1024,
            DifficultyLevel.CRITICAL: 2048,
        }
        return token_limits[self]

    @property
    def priority_score(self) -> int:
        """
        Business rule: Priority score for test execution ordering.

        Higher difficulty = higher priority for thorough testing.
        """
        priorities = {
            DifficultyLevel.LOW: 1,
            DifficultyLevel.MEDIUM: 2,
            DifficultyLevel.HIGH: 3,
            DifficultyLevel.CRITICAL: 4,
        }
        return priorities[self]

    @property
    def is_high_priority(self) -> bool:
        """Business rule: High/Critical tests are prioritized."""
        return self in [DifficultyLevel.HIGH, DifficultyLevel.CRITICAL]

    @property
    def passing_threshold(self) -> float:
        """
        Business rule: Minimum score required to pass (0.0 to 1.0).

        Higher difficulty requires stricter evaluation.
        """
        thresholds = {
            DifficultyLevel.LOW: 0.60,     # 60% for basic questions
            DifficultyLevel.MEDIUM: 0.70,  # 70% for intermediate
            DifficultyLevel.HIGH: 0.80,    # 80% for complex
            DifficultyLevel.CRITICAL: 0.85,  # 85% for critical
        }
        return thresholds[self]

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"DifficultyLevel.{self.name}"

    def __lt__(self, other: "DifficultyLevel") -> bool:
        """Enable comparison for sorting."""
        return self.priority_score < other.priority_score
