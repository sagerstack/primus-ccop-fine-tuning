"""
Model Response Entity

Represents the output from an LLM for a given test case.
Entity with identity (response_id) and lifecycle.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from domain.exceptions.validation_error import ValidationError


class ModelResponse:
    """
    Entity representing an LLM's response to a test case.

    Identity: response_id (UUID)
    Lifecycle: Created → Analyzed → Scored

    This entity encapsulates the model's output and provides
    business logic for parsing and analyzing responses.
    """

    def __init__(
        self,
        response_id: UUID | None = None,
        content: str = "",
        model_name: str = "",
        tokens_used: int = 0,
        latency_ms: int = 0,
        temperature: float = 0.7,
        created_at: datetime | None = None,
        metadata: Dict[str, any] | None = None,
    ) -> None:
        """
        Initialize ModelResponse entity.

        Args:
            response_id: Unique identifier (auto-generated if None)
            content: The actual response text from the model
            model_name: Name of the model that generated this response
            tokens_used: Number of tokens in the response
            latency_ms: Response generation time in milliseconds
            temperature: Temperature parameter used for generation
            created_at: Timestamp of response creation
            metadata: Additional response metadata

        Raises:
            ValidationError: If validation fails
        """
        self._response_id = response_id or uuid4()
        self._content = content
        self._model_name = model_name
        self._tokens_used = tokens_used
        self._latency_ms = latency_ms
        self._temperature = temperature
        self._created_at = created_at or datetime.utcnow()
        self._metadata = metadata or {}

        self._validate()

    def _validate(self) -> None:
        """
        Validate entity invariants.

        Business rules:
        - content cannot be empty after creation
        - tokens_used must be non-negative
        - latency_ms must be non-negative
        - temperature must be between 0.0 and 2.0
        """
        if self._content and not self._content.strip():
            raise ValidationError("Response content cannot be empty", field="content")

        if self._tokens_used < 0:
            raise ValidationError(
                "Tokens used must be non-negative",
                field="tokens_used"
            )

        if self._latency_ms < 0:
            raise ValidationError(
                "Latency must be non-negative",
                field="latency_ms"
            )

        if not 0.0 <= self._temperature <= 2.0:
            raise ValidationError(
                f"Temperature must be between 0.0 and 2.0, got {self._temperature}",
                field="temperature"
            )

    # Business methods

    def extract_citations(self) -> List[str]:
        """
        Extract clause citations from the response.

        Business logic: Identifies references to CCoP 2.0 clauses in format:
        - "Clause 5.1.2"
        - "5.1.2"
        - "Section 5.1.2"

        Returns:
            List of extracted clause references
        """
        patterns = [
            r"[Cc]lause\s+(\d+\.\d+\.?\d*)",
            r"[Ss]ection\s+(\d+\.\d+\.?\d*)",
            r"\b(\d+\.\d+\.\d+)\b",
        ]

        citations = set()
        for pattern in patterns:
            matches = re.findall(pattern, self._content)
            citations.update(matches)

        return sorted(list(citations))

    def contains_hallucination_indicators(self) -> bool:
        """
        Business rule: Check for common hallucination indicators.

        Checks for phrases that suggest the model is making up information:
        - "I'm not sure but..."
        - "I believe..."
        - "It might be..."
        - References to non-existent clauses (>11.x.x)

        Returns:
            True if potential hallucination detected
        """
        hallucination_phrases = [
            r"i'?m not sure",
            r"i believe",
            r"i think",
            r"it might be",
            r"perhaps",
            r"possibly",
            r"i don'?t have specific information",
            r"as far as i know",
        ]

        content_lower = self._content.lower()

        # Check for uncertain language
        for phrase in hallucination_phrases:
            if re.search(phrase, content_lower):
                return True

        # Check for invalid clause references (section > 11)
        invalid_clauses = re.findall(r"\b(1[2-9]|[2-9]\d)\.\d+\.?\d*\b", self._content)
        if invalid_clauses:
            return True

        return False

    def is_empty(self) -> bool:
        """Check if response is empty or whitespace only."""
        return not self._content or not self._content.strip()

    def word_count(self) -> int:
        """Count words in the response."""
        return len(self._content.split())

    def contains_code_snippet(self) -> bool:
        """Check if response contains code snippets (for B6 evaluation)."""
        code_indicators = [
            "```",
            "function",
            "class ",
            "def ",
            "import ",
            "const ",
            "var ",
            "let ",
            "{",
            "}",
        ]
        return any(indicator in self._content for indicator in code_indicators)

    # Properties (identity & attributes)

    @property
    def response_id(self) -> UUID:
        """Unique identifier (entity identity)."""
        return self._response_id

    @property
    def content(self) -> str:
        """Response text content."""
        return self._content

    @property
    def model_name(self) -> str:
        """Name of the model."""
        return self._model_name

    @property
    def tokens_used(self) -> int:
        """Number of tokens used."""
        return self._tokens_used

    @property
    def latency_ms(self) -> int:
        """Response latency in milliseconds."""
        return self._latency_ms

    @property
    def temperature(self) -> float:
        """Generation temperature."""
        return self._temperature

    @property
    def created_at(self) -> datetime:
        """Creation timestamp."""
        return self._created_at

    @property
    def metadata(self) -> Dict[str, any]:
        """Additional metadata."""
        return self._metadata.copy()

    # Equality based on identity

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ModelResponse):
            return False
        return self._response_id == other._response_id

    def __hash__(self) -> int:
        return hash(self._response_id)

    def __repr__(self) -> str:
        return (
            f"ModelResponse(response_id={self._response_id}, "
            f"model='{self._model_name}', "
            f"tokens={self._tokens_used})"
        )

    def __str__(self) -> str:
        preview = self._content[:50] + "..." if len(self._content) > 50 else self._content
        return f"ModelResponse[{self._model_name}]: {preview}"
