"""
CCoP Section Value Object

Flexible section representation that supports:
- Standard CCoP 2.0 sections (1-11)
- Cybersecurity Act sections
- Multiple sections
- Custom section references

Examples:
- "Section 5: Protection"
- "Cybersecurity Act 2018 Part 3"
- "Multiple Sections"
- "CCoP 2.0 & RESPONSE-TO-FEEDBACK"
"""

import re
from typing import Optional


class CCoPSection:
    """
    Flexible CCoP section value object.

    Accepts any section string but provides helpers for common CCoP sections.
    This is a Value Object - immutable and identified by value, not identity.
    """

    def __init__(self, value: str) -> None:
        """
        Initialize CCoPSection from string.

        Args:
            value: Section identifier (any string)
        """
        self._value = value.strip()
        self._section_number: Optional[int] = None
        self._parse_section_number()

    def _parse_section_number(self) -> None:
        """Extract section number if present (e.g., 'Section 5: Protection' -> 5)."""
        # Match patterns like "Section 5", "Section 10:", etc.
        match = re.search(r"Section\s+(\d+)", self._value, re.IGNORECASE)
        if match:
            self._section_number = int(match.group(1))

    @classmethod
    def from_string(cls, value: str) -> "CCoPSection":
        """
        Convert string to CCoPSection.

        Args:
            value: String representation

        Returns:
            CCoPSection instance
        """
        return cls(value)

    @property
    def value(self) -> str:
        """Get the section value."""
        return self._value

    @property
    def section_number(self) -> Optional[int]:
        """Get section number if present (e.g., 5 for 'Section 5: Protection')."""
        return self._section_number

    @property
    def is_ot_specific(self) -> bool:
        """Business rule: Check if section is OT/ICS specific."""
        lower_value = self._value.lower()
        return any(keyword in lower_value for keyword in ["ot", "ics", "operational technology", "industrial"])

    @property
    def applies_to_it(self) -> bool:
        """Business rule: Check if section applies to IT infrastructure."""
        # Most sections apply to IT unless explicitly OT-only
        return not self.is_ot_specific or "it" in self._value.lower()

    @property
    def applies_to_ot(self) -> bool:
        """Business rule: Check if section applies to OT infrastructure."""
        # All sections apply to OT
        return True

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"CCoPSection('{self._value}')"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CCoPSection):
            return self._value == other._value
        if isinstance(other, str):
            return self._value == other
        return False

    def __hash__(self) -> int:
        return hash(self._value)

    def __lt__(self, other: "CCoPSection") -> bool:
        """Enable comparison for sorting by section number."""
        # If both have section numbers, compare by number
        if self._section_number is not None and other._section_number is not None:
            return self._section_number < other._section_number
        # Otherwise, sort alphabetically
        return self._value < other._value
