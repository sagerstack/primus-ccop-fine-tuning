"""Padding-agnostic test_id/benchmark_type validation for TestCase.

Regression test: before the fix, TestCase._validate used
`benchmark_type.short_name` (non-padded, e.g. 'B1') as the expected test_id
prefix, so a padded row like test_id='B01-001' with benchmark_type='B01'
would fail with "does not match benchmark type 'B1'". The validator now
normalizes both sides via BenchmarkType.short_name.
"""
from __future__ import annotations

import pytest

from domain.entities.test_case import TestCase
from domain.exceptions.validation_error import ValidationError
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.ccop_section import CCoPSection
from domain.value_objects.difficulty_level import DifficultyLevel


QUESTION = "This is a fixture question long enough to satisfy the 50-character minimum for TestCase validation."
EXPECTED = "This is a fixture expected response long enough to pass the minimum length check."
CRITERIA = {"rubric": "non-empty"}


def _make(test_id: str, benchmark: str) -> TestCase:
    return TestCase(
        test_id=test_id,
        benchmark_type=BenchmarkType(benchmark),
        section=CCoPSection("5.3"),
        clause_reference="5.3.1",
        difficulty=DifficultyLevel.MEDIUM,
        question=QUESTION,
        expected_response=EXPECTED,
        evaluation_criteria=CRITERIA,
    )


@pytest.mark.parametrize(
    "test_id, benchmark",
    [
        ("B01-001", "B01"),
        ("B01-001", "B1"),
        ("B1-001", "B01"),
        ("B1-001", "B1"),
        ("B10-042", "B10"),
        ("B10-042", "B10_Risk_Justification_Coherence"),
    ],
)
def test_accepts_padded_and_unpadded_forms(test_id: str, benchmark: str) -> None:
    tc = _make(test_id, benchmark)
    assert tc.test_id == test_id


def test_rejects_prefix_mismatch() -> None:
    with pytest.raises(ValidationError, match="does not match benchmark type"):
        _make("B02-001", "B01")


def test_rejects_garbage_prefix() -> None:
    with pytest.raises(ValidationError):
        _make("X1-001", "B1")
