"""Regression test: every JSONL row's test_id prefix must equal its benchmark_id.

Prevents re-introducing the B1-001/benchmark_id=B1 vs B04-001/benchmark_id=B04
padding drift that was cleaned up during Phase 3.2 follow-up.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_SUITE_DIR = REPO_ROOT / "ground-truth" / "test-suite"


def _iter_rows():
    for path in sorted(TEST_SUITE_DIR.glob("*.jsonl")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            yield path.name, lineno, json.loads(line)


def test_test_id_prefix_matches_benchmark_id() -> None:
    mismatches: list[str] = []
    for filename, lineno, row in _iter_rows():
        tid = row.get("test_id", "")
        bid = row.get("benchmark_id", "")
        prefix = tid.split("-", 1)[0] if "-" in tid else tid
        if prefix != bid:
            mismatches.append(f"{filename}:{lineno} test_id={tid!r} benchmark_id={bid!r}")
    assert not mismatches, "test_id prefix must equal benchmark_id:\n" + "\n".join(mismatches)


@pytest.mark.parametrize(
    "filename, expected_bid",
    [
        ("b01_ccop_applicability_scope.jsonl", "B01"),
        ("b02_compliance_classification.jsonl", "B02"),
        ("b03_conditional_compliance_reasoning.jsonl", "B03"),
    ],
)
def test_padded_benchmarks_use_zero_prefix(filename: str, expected_bid: str) -> None:
    path = TEST_SUITE_DIR / filename
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        assert row["benchmark_id"] == expected_bid, (
            f"{filename}:{lineno} expected benchmark_id={expected_bid}, got {row['benchmark_id']}"
        )
        assert row["test_id"].startswith(f"{expected_bid}-"), (
            f"{filename}:{lineno} expected test_id prefix {expected_bid}-, got {row['test_id']}"
        )
