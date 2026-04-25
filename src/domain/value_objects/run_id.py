"""
RunId Value Object

Immutable identifier for an evaluation run.
Format: eval-run-{mode}-{scope}-{yyyyMMdd}-{HHmm}
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


# Filename-safety: most filesystems cap individual path components at 255 bytes.
# When many test_ids would be concatenated into a scope string, we collapse the
# full list into a count + content hash to keep run-id-derived filenames under
# the limit. Threshold chosen so the longest suffix used for filenames
# (-yyyyMMdd-HHmm-...-mode-name.json, ~50 chars) plus the eval-run-mode-test-
# prefix and 5 dash-separated test IDs (e.g., 5 * 8 + 4 dashes = 44 chars) fits
# well under 255.
_MAX_INLINE_TEST_IDS = 5


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

    def partial_filename(self, model_name: str) -> str:
        """Filename for the per-case incremental JSONL written during a run.

        The partial file lives alongside the eventual consolidated .json output
        and shares the same run-id prefix. Format:
            {value}-{model_name}.partial.jsonl

        On crash the partial file preserves all completed cases and supports
        resume via a fresh `--resume` invocation matching the same scope+mode.
        """
        return f"{self.value}-{model_name}.partial.jsonl"

    @staticmethod
    def partial_glob_pattern(mode: str, scope: str, model_name: str) -> str:
        """Glob pattern matching all partial files for a given (mode, scope, model).

        Timestamp is wildcarded so a single resume can find the latest partial
        file from any prior crashed run with matching invocation flags.
        """
        return f"eval-run-{mode}-{scope}-*-{model_name}.partial.jsonl"

    @classmethod
    def build_scope(
        cls,
        tier: Optional[int],
        benchmarks: Optional[List[str]],
        test_ids: Optional[List[str]],
        total_benchmarks_available: int,
    ) -> str:
        """
        Deterministically encode the evaluation scope as a string.

        Precedence (highest to lowest):
            test_ids  >  tier  >  benchmarks  >  suite

        Benchmark sort uses numeric ordering (B1, B3, B7 — not lexicographic).

        Args:
            tier: Evaluation tier number (1, 2, or 3); takes precedence over benchmarks.
            benchmarks: List of benchmark IDs (e.g. ["B1", "B3"]); used when tier is None.
            test_ids: Specific test case IDs; takes highest precedence.
            total_benchmarks_available: Total number of benchmarks in the suite.

        Returns:
            Scope string, one of:
                "test-{id}"
                "test-{id1}-{id2}-..."
                "tier-{N}"
                "benchmark-{B}"
                "benchmarks-{B1}-{B2}-..."
                "suite"
        """
        if test_ids:
            sorted_ids = sorted(test_ids)
            if len(sorted_ids) == 1:
                return f"test-{sorted_ids[0]}"
            if len(sorted_ids) <= _MAX_INLINE_TEST_IDS:
                return "test-" + "-".join(sorted_ids)
            # Collapse large lists to count + deterministic hash to keep the
            # filename within OS limits (255-byte component cap on most FSes).
            joined = "|".join(sorted_ids)
            digest = hashlib.sha1(joined.encode("utf-8")).hexdigest()[:8]
            return f"tests-{len(sorted_ids)}-{digest}"

        if tier is not None:
            return f"tier-{tier}"

        if benchmarks:

            def _benchmark_sort_key(b: str) -> int:
                if b.startswith("B") and b[1:].isdigit():
                    return int(b[1:])
                return 0

            sorted_benchmarks = sorted(benchmarks, key=_benchmark_sort_key)
            if len(benchmarks) < total_benchmarks_available:
                if len(sorted_benchmarks) == 1:
                    return f"benchmark-{sorted_benchmarks[0]}"
                return "benchmarks-" + "-".join(sorted_benchmarks)

        return "suite"

    @classmethod
    def for_query(cls, mode: str = "hybrid", timestamp: Optional[datetime] = None) -> "RunId":
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
