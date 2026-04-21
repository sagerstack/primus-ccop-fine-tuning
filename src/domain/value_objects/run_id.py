"""
RunId Value Object

Immutable identifier for an evaluation run.
Format: eval-run-{mode}-{scope}-{yyyyMMdd}-{HHmm}
"""

from dataclasses import dataclass
from datetime import datetime


_VALID_MODES = {"hybrid", "llm-only", "rag-only"}


@dataclass(frozen=True)
class RunId:
    """
    Value object representing the unique identity of an evaluation run.

    Identified by its values (mode, scope, timestamp), not by reference.
    Immutable — cannot be altered after construction.

    Attributes:
        mode: Pipeline mode — one of "hybrid", "llm-only", "rag-only"
        scope: Scope descriptor (e.g., "suite", "benchmark-B3", "query")
        timestamp: UTC datetime the run was initiated
    """

    mode: str
    scope: str
    timestamp: datetime

    def __post_init__(self) -> None:
        if self.mode not in _VALID_MODES:
            raise ValueError(
                f"Invalid mode '{self.mode}'. Must be one of: {sorted(_VALID_MODES)}"
            )
        if not self.scope or not self.scope.strip():
            raise ValueError("RunId scope cannot be empty")

    @property
    def value(self) -> str:
        """Render the run ID string in canonical format."""
        return f"eval-run-{self.mode}-{self.scope}-{self.timestamp.strftime('%Y%m%d-%H%M')}"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"RunId(mode='{self.mode}', scope='{self.scope}', value='{self.value}')"

    @classmethod
    def for_query(cls, mode: str = "hybrid", timestamp: datetime | None = None) -> "RunId":
        """
        Construct a RunId for an ad-hoc query invocation.

        Args:
            mode: Pipeline mode (default "hybrid")
            timestamp: UTC datetime override (auto-generated if None)

        Returns:
            RunId with scope="query"
        """
        return cls(
            mode=mode,
            scope="query",
            timestamp=timestamp or datetime.utcnow(),
        )
