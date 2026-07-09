"""
Tests for benchmark id / test id casing normalization (Phase 9 Plan 05, D-10).

Resolves the carried blocker (STATE.md "Ground-truth test_id casing
inconsistency (B04/B4, B05/B5, ...)"): ground-truth JSONL files use
zero-padded ids ("B04", "B04-001") while `BenchmarkType.short_name` strips
padding ("B4"). `domain.value_objects.benchmark_id.normalize()` canonicalizes
both forms to a single identity, and `JSONLTestCaseRepository` applies it at
every id-based lookup so a caller using either form resolves to exactly one
ground-truth row (no dropped/duplicated cases).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from domain.value_objects.benchmark_id import ids_match, normalize
from domain.value_objects.benchmark_type import BenchmarkType
from infrastructure.adapters.repositories.jsonl_test_case_repository import (
    JSONLTestCaseRepository,
)


class TestNormalize:
    def test_normalize_pads_bare_benchmark_id(self):
        assert normalize("B4") == "B04"

    def test_normalize_is_idempotent_on_already_padded_id(self):
        assert normalize("B04") == "B04"

    def test_normalize_pads_full_test_id(self):
        assert normalize("B4-001") == "B04-001"

    def test_normalize_full_test_id_equivalence(self):
        assert normalize("B4-001") == normalize("B04-001")

    def test_normalize_is_case_insensitive_on_prefix(self):
        assert normalize("b4-001") == "B04-001"

    def test_normalize_unaffected_for_already_two_digit_ids(self):
        assert normalize("B21") == "B21"
        assert normalize("B21-014") == "B21-014"

    def test_normalize_passes_through_non_matching_strings(self):
        assert normalize("not-a-benchmark-id") == "not-a-benchmark-id"

    def test_normalize_empty_string(self):
        assert normalize("") == ""


class TestIdsMatch:
    def test_ids_match_across_padding(self):
        assert ids_match("B4-001", "B04-001") is True
        assert ids_match("B4", "B04") is True

    def test_ids_match_false_for_different_benchmarks(self):
        assert ids_match("B4-001", "B5-001") is False
        assert ids_match("B4", "B14") is False


@pytest.fixture
def gt_repo(tmp_path: Path) -> JSONLTestCaseRepository:
    """A JSONLTestCaseRepository backed by a single fabricated B04 GT file.

    Mirrors the real ground-truth v2 shape (zero-padded benchmark_id="B04",
    test_id="B04-001"), matching how b04_it_ot_classification_boundary.jsonl
    is actually keyed in ground-truth/test-suite/.
    """
    row = {
        "test_id": "B04-001",
        "version": "2.0",
        "benchmark_id": "B04",
        "input": {
            "question": (
                "A facility runs a SCADA system controlling turbine operations "
                "alongside a corporate email server. Classify each system as "
                "IT, OT, or hybrid per CCoP 2.0 Section 10."
            )
        },
        "ground_truth": {
            "expected_label": "OT: SCADA; IT: email server",
            "expected_response": (
                "The SCADA system is OT because it controls physical turbine "
                "operations, while the corporate email server is IT because it "
                "manages data and business communication per CCoP 2.0 Section 10."
            ),
            "key_facts": [],
        },
        "fail_conditions": {"forbidden_claims": [], "hallucination_patterns": []},
        "metadata": {"section": "Section 10", "clause_reference": ["1.2.1"], "difficulty": "medium"},
    }
    gt_file = tmp_path / "b04_it_ot_classification_boundary.jsonl"
    gt_file.write_text(json.dumps(row) + "\n", encoding="utf-8")

    logger = MagicMock()
    return JSONLTestCaseRepository(test_cases_dir=tmp_path, logger=logger)


class TestJSONLRepositoryPaddingAgnosticLookup:
    """The blocker's actual symptom: GT keyed 'B04' must resolve when a
    caller (CLI --test-ids, --benchmarks, tier list) passes the unpadded
    'B4' form, and vice versa — never silently dropped or duplicated."""

    @pytest.mark.asyncio
    async def test_load_by_id_resolves_unpadded_request_to_padded_gt_row(self, gt_repo):
        case = await gt_repo.load_by_id("B4-001")
        assert case is not None
        assert case.test_id == "B04-001"

    @pytest.mark.asyncio
    async def test_load_by_id_resolves_padded_request_directly(self, gt_repo):
        case = await gt_repo.load_by_id("B04-001")
        assert case is not None
        assert case.test_id == "B04-001"

    @pytest.mark.asyncio
    async def test_load_by_ids_produces_exactly_one_row_no_duplicates(self, gt_repo):
        # Even if both the padded and unpadded forms are requested together,
        # the GT row must appear exactly once in the result (D-10 acceptance:
        # "exactly one result row keyed to the GT id").
        cases = await gt_repo.load_by_ids(["B4-001", "B04-001"])
        assert len(cases) == 1
        assert cases[0].test_id == "B04-001"

    @pytest.mark.asyncio
    async def test_load_by_ids_unpadded_only_still_resolves(self, gt_repo):
        cases = await gt_repo.load_by_ids(["B4-001"])
        assert len(cases) == 1
        assert cases[0].test_id == "B04-001"

    @pytest.mark.asyncio
    async def test_load_by_benchmark_resolves_unpadded_benchmark_type(self, gt_repo):
        cases = await gt_repo.load_by_benchmark(BenchmarkType.from_string("B4"))
        assert len(cases) == 1
        assert cases[0].test_id == "B04-001"

    @pytest.mark.asyncio
    async def test_load_by_id_returns_none_for_unrelated_id(self, gt_repo):
        case = await gt_repo.load_by_id("B4-999")
        assert case is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
