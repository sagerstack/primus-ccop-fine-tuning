"""
Benchmark ID Casing Normalization

Ground-truth JSONL files key rows with a zero-padded `benchmark_id`
(e.g. "B04", test_id "B04-001"), while `BenchmarkType.short_name` strips
zero-padding when deriving a benchmark's short display form (e.g. "B4").
Both are valid representations of the same benchmark — this module does
NOT replace `BenchmarkType` or renumber benchmarks; it provides a pure
normalization function used at comparison/lookup boundaries (repository
matching, GT-to-result alignment) so "B4" and "B04" (and full test ids
"B4-001" / "B04-001") are never silently treated as distinct identities.

Blocker: .planning/STATE.md — "Ground-truth test_id casing inconsistency
(B04/B4, B05/B5, ...)".
"""

import re

# Matches a benchmark prefix "B<1-2 digits>" optionally followed by a
# "-<suffix>" (e.g. "-001" for a full test_id). Case-insensitive on the
# leading "B" (accepts "b4-001" too).
_PATTERN = re.compile(r"^[Bb](\d{1,2})(-.*)?$")


def normalize(value: str) -> str:
    """
    Canonicalize a benchmark id or test id to its zero-padded form.

    Examples:
        normalize("B4") == "B04"
        normalize("B04") == "B04"
        normalize("b4-001") == "B04-001"
        normalize("B04-001") == "B04-001"
        normalize("B21") == "B21"  # already 2 digits, unaffected

    Args:
        value: A benchmark id ("B4", "B04") or full test id ("B4-001").

    Returns:
        The canonical zero-padded form (e.g. "B04", "B04-001"). Input that
        does not match the `B<digits>[-suffix]` shape is returned stripped
        but otherwise unchanged, so callers can pass arbitrary strings
        without raising.
    """
    if not value:
        return value

    stripped = value.strip()
    match = _PATTERN.match(stripped)
    if not match:
        return stripped

    number, suffix = match.group(1), match.group(2) or ""
    return f"B{int(number):02d}{suffix}"


def ids_match(left: str, right: str) -> bool:
    """Return True if two benchmark/test ids are equal after normalization."""
    return normalize(left) == normalize(right)


__all__ = ["normalize", "ids_match"]
