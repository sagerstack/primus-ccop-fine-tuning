"""
Benchmark Type Value Object

Flexible benchmark type that supports any Bxx_Description format.
Examples:
- B1_CCoP_Applicability_Scope
- B2_Compliance_Classification_Accuracy
- B10_Risk_Justification_Coherence
"""

import re
from typing import Optional


class BenchmarkType:
    """
    Flexible benchmark type value object.

    Parses benchmark identifiers in the format "Bxx_Description" where:
    - xx is a 1-2 digit number (B1, B2, ..., B99)
    - Description is the benchmark name (underscore-separated)

    This is a Value Object - immutable and identified by value, not identity.
    """

    def __init__(self, value: str) -> None:
        """
        Initialize BenchmarkType from string.

        Args:
            value: Benchmark identifier (e.g., "B1", "B1_CCoP_Applicability_Scope")

        Raises:
            ValueError: If value doesn't match Bxx format
        """
        self._value = value.strip()
        self._benchmark_number: Optional[int] = None
        self._description: Optional[str] = None
        self._parse()

    def _parse(self) -> None:
        """Parse benchmark value and extract number and description."""
        # Match patterns like "B1", "B10", "B1_Description", "B10_Description"
        pattern = r"^B(\d{1,2})(?:_(.+))?$"
        match = re.match(pattern, self._value, re.IGNORECASE)

        if not match:
            raise ValueError(
                f"Invalid benchmark type format: '{self._value}'. "
                f"Expected format: Bxx or Bxx_Description (e.g., 'B1', 'B1_CCoP_Applicability_Scope')"
            )

        self._benchmark_number = int(match.group(1))
        self._description = match.group(2) or ""

    @classmethod
    def from_string(cls, value: str) -> "BenchmarkType":
        """
        Convert string to BenchmarkType.

        Args:
            value: String representation (e.g., "B1", "B1_CCoP_Applicability_Scope")

        Returns:
            BenchmarkType instance

        Raises:
            ValueError: If value is not a valid benchmark type
        """
        return cls(value)

    @property
    def value(self) -> str:
        """Get the full benchmark value."""
        return self._value

    @property
    def benchmark_number(self) -> int:
        """Get benchmark number (e.g., 1 for B1, 10 for B10)."""
        return self._benchmark_number or 0

    @property
    def short_name(self) -> str:
        """Get short name (e.g., 'B1', 'B10')."""
        return f"B{self._benchmark_number}"

    @property
    def description(self) -> str:
        """Get human-readable description."""
        if self._description:
            # Convert underscore-separated to title case
            return self._description.replace("_", " ").title()
        return self.short_name

    def __str__(self) -> str:
        return self.short_name

    def __repr__(self) -> str:
        return f"BenchmarkType('{self._value}')"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, BenchmarkType):
            return self._value == other._value
        if isinstance(other, str):
            # Allow comparison with strings like "B1"
            return self.short_name == other or self._value == other
        return False

    def __hash__(self) -> int:
        return hash(self._value)

    def __lt__(self, other: "BenchmarkType") -> bool:
        """Enable sorting by benchmark number."""
        return self.benchmark_number < other.benchmark_number
