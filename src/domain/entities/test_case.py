"""
Test Case Entity

Represents a single CCoP 2.0 evaluation test case.
Entity with identity (test_id) and comprehensive business logic.
"""

import re
from typing import Any, Dict

from domain.exceptions.validation_error import ValidationError
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.ccop_section import CCoPSection
from domain.value_objects.difficulty_level import DifficultyLevel


class TestCase:
    """
    Entity representing a single CCoP 2.0 evaluation test case.

    Identity: test_id (e.g., "B1-001", "B3-015")
    Lifecycle: Created → Validated → Evaluated → Archived

    This entity encapsulates test case data and business rules for:
    - Validation of test case structure
    - Benchmark-specific requirements
    - Domain classification (IT/OT)
    - Evaluation parameter determination
    """

    def __init__(
        self,
        test_id: str,
        benchmark_type: BenchmarkType,
        section: CCoPSection,
        clause_reference: str,
        difficulty: DifficultyLevel,
        question: str,
        expected_response: str,
        evaluation_criteria: Dict[str, Any],
        metadata: Dict[str, Any] | None = None,
        # Phase 2 fields
        key_facts: list[str] | None = None,
        expected_label: str | None = None,
        forbidden_claims: list[str] | None = None,
    ) -> None:
        """
        Initialize TestCase entity.

        Args:
            test_id: Unique identifier (format: Bxx-nnn, e.g., B1-001, B10-042)
            benchmark_type: Benchmark category (any Bxx format)
            section: CCoP 2.0 section
            clause_reference: CCoP clause reference (e.g., "5.1.2" or "N/A")
            difficulty: Difficulty level
            question: The test question
            expected_response: Expected/reference answer
            evaluation_criteria: Criteria for scoring
            metadata: Additional metadata (domain, tags, etc.)
            key_facts: Phase 2 - List of atomic facts to check for completeness
            expected_label: Phase 2 - Expected classification label (for label-based scoring)
            forbidden_claims: Phase 2 - List of fabricated claims to penalize

        Raises:
            ValidationError: If validation fails
        """
        self._test_id = test_id
        self._benchmark_type = benchmark_type
        self._section = section
        self._clause_reference = clause_reference
        self._difficulty = difficulty
        self._question = question
        self._expected_response = expected_response
        self._evaluation_criteria = evaluation_criteria
        self._metadata = metadata or {}

        # Phase 2 fields
        self._key_facts = key_facts or []
        self._expected_label = expected_label
        self._forbidden_claims = forbidden_claims or []

        # Validate on creation (fail fast)
        self._validate()

    def _validate(self) -> None:
        """
        Enforce all business rules and invariants.

        Business rules:
        1. test_id must match format Bxx-nnn (e.g., B1-001, B10-042)
        2. test_id prefix must match benchmark_type
        3. question must be substantial (>= 50 chars)
        4. expected_response cannot be empty
        5. evaluation_criteria must be non-empty dict
        """
        # Rule 1: test_id format
        if not self._is_valid_test_id_format():
            raise ValidationError(
                f"test_id must match format Bxx-nnn (e.g., B1-001, B10-042), got '{self._test_id}'",
                field="test_id"
            )

        # Rule 2: test_id matches benchmark
        expected_prefix = f"{self._benchmark_type.short_name}-"
        if not self._test_id.startswith(expected_prefix):
            raise ValidationError(
                f"test_id '{self._test_id}' does not match benchmark type "
                f"'{self._benchmark_type.short_name}'",
                field="test_id"
            )

        # Rule 3: question minimum length
        if len(self._question.strip()) < 50:
            raise ValidationError(
                f"Question too short ({len(self._question)} chars). "
                "Minimum 50 characters required for meaningful evaluation.",
                field="question"
            )

        # Rule 4: expected response required
        if not self._expected_response or not self._expected_response.strip():
            raise ValidationError(
                "Expected response cannot be empty",
                field="expected_response"
            )

        # Rule 5: evaluation criteria required
        if not self._evaluation_criteria or not isinstance(self._evaluation_criteria, dict):
            raise ValidationError(
                "Evaluation criteria must be a non-empty dictionary",
                field="evaluation_criteria"
            )

    def _is_valid_test_id_format(self) -> bool:
        """Validate test_id format: Bxx-nnn where xx is 1-99 and nnn is 001-999"""
        pattern = r"^B\d{1,2}-\d{3}$"
        return bool(re.match(pattern, self._test_id))

    # Business methods

    def is_high_priority(self) -> bool:
        """Business rule: High/Critical tests are high priority."""
        return self._difficulty.is_high_priority

    def is_ot_specific(self) -> bool:
        """Business rule: Check if test is OT-specific."""
        return (
            self._section.is_ot_specific or
            self._metadata.get("domain") == "OT"
        )

    def is_it_specific(self) -> bool:
        """Business rule: Check if test is IT-specific."""
        domain = self._metadata.get("domain")
        return domain == "IT"

    def is_cross_domain(self) -> bool:
        """Business rule: Check if test applies to both IT and OT."""
        domain = self._metadata.get("domain")
        return domain == "IT/OT" or domain is None

    def get_max_tokens_for_response(self) -> int:
        """
        Business rule: Determine max tokens based on difficulty.

        Delegates to DifficultyLevel value object.
        """
        return self._difficulty.max_tokens

    def get_passing_threshold(self) -> float:
        """
        Business rule: Get passing threshold based on difficulty.

        Delegates to DifficultyLevel value object.
        """
        return self._difficulty.passing_threshold

    def get_metadata_field(self, field_name: str, default: Any = None) -> Any:
        """
        Get a metadata field value.

        Args:
            field_name: Name of metadata field
            default: Default value if field not present

        Returns:
            Field value or default
        """
        return self._metadata.get(field_name, default)

    def get_key_terminology(self) -> list[str]:
        """
        Get key terminology for B4 terminology scoring.

        Extracts Singapore-specific cybersecurity terms that should appear
        in responses (e.g., "CII", "CIIO", "CSA", "CCoP").

        Returns:
            List of key terms from metadata, or empty list if not defined
        """
        # Try multiple possible metadata keys
        terminology = self._metadata.get("key_terminology") or \
                     self._metadata.get("key_terms") or \
                     self._metadata.get("terminology") or []

        return terminology if isinstance(terminology, list) else []

    def get_expected_violations(self) -> list[str]:
        """
        Get expected code violations for B6 violation detection scoring.

        Extracts list of CCoP 2.0 control violations that should be
        identified in code review scenarios.

        Returns:
            List of expected violations from metadata, or empty list if not defined
        """
        # Try multiple possible metadata keys
        violations = self._metadata.get("expected_violations") or \
                    self._metadata.get("violations") or \
                    self._metadata.get("code_violations") or []

        return violations if isinstance(violations, list) else []

    # Properties (identity & attributes)

    @property
    def test_id(self) -> str:
        """Unique identifier (entity identity)."""
        return self._test_id

    @property
    def benchmark_type(self) -> BenchmarkType:
        """Benchmark category."""
        return self._benchmark_type

    @property
    def section(self) -> CCoPSection:
        """CCoP 2.0 section."""
        return self._section

    @property
    def clause_reference(self) -> str:
        """CCoP clause reference."""
        return self._clause_reference

    @property
    def difficulty(self) -> DifficultyLevel:
        """Difficulty level."""
        return self._difficulty

    @property
    def question(self) -> str:
        """Test question."""
        return self._question

    @property
    def expected_response(self) -> str:
        """Expected/reference answer."""
        return self._expected_response

    @property
    def evaluation_criteria(self) -> Dict[str, Any]:
        """Evaluation criteria (immutable copy)."""
        return self._evaluation_criteria.copy()

    @property
    def metadata(self) -> Dict[str, Any]:
        """Additional metadata (immutable copy)."""
        return self._metadata.copy()

    @property
    def domain(self) -> str:
        """Infrastructure domain (IT, OT, or IT/OT)."""
        return self._metadata.get("domain", "IT/OT")

    # Phase 2 properties

    @property
    def key_facts(self) -> list[str]:
        """Phase 2: List of atomic facts for completeness scoring."""
        return self._key_facts.copy()

    @property
    def expected_label(self) -> str | None:
        """Phase 2: Expected classification label for label-based scoring."""
        return self._expected_label

    @property
    def forbidden_claims(self) -> list[str]:
        """Phase 2: List of fabricated claims to penalize in grounding checks."""
        return self._forbidden_claims.copy()

    # Equality based on identity

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TestCase):
            return False
        return self._test_id == other._test_id

    def __hash__(self) -> int:
        return hash(self._test_id)

    def __repr__(self) -> str:
        return (
            f"TestCase(test_id='{self._test_id}', "
            f"benchmark={self._benchmark_type.value}, "
            f"difficulty={self._difficulty.value})"
        )

    def __str__(self) -> str:
        return f"TestCase[{self._test_id}]: {self._benchmark_type.description}"
