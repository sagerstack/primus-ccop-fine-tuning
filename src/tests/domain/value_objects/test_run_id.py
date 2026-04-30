"""
Tests for RunId value object.

Covers:
- Value rendering in canonical format
- Invalid mode rejection
- build_scope for every branch (suite, single benchmark, multi benchmark, tier, test-id(s))
- Numeric sort for multi-benchmark (B2 < B3 < B11, not alphabetical)
- for_query factory method
"""

import pytest
from datetime import datetime

from domain.value_objects.run_id import RunId


class TestRunIdValueRendering:
    def test_value_renders_hybrid_mode(self):
        ts = datetime(2026, 4, 21, 14, 30)
        run_id = RunId(mode="hybrid", scope="suite", timestamp=ts)
        assert run_id.value == "eval-run-hybrid-suite-20260421-1430"

    def test_value_renders_llm_only_mode(self):
        ts = datetime(2026, 4, 21, 9, 5)
        run_id = RunId(mode="llm-only", scope="benchmark-B3", timestamp=ts)
        assert run_id.value == "eval-run-llm-only-benchmark-B3-20260421-0905"

    def test_value_renders_rag_only_mode(self):
        ts = datetime(2026, 4, 21, 0, 0)
        run_id = RunId(mode="rag-only", scope="suite", timestamp=ts)
        assert run_id.value == "eval-run-rag-only-suite-20260421-0000"

    def test_str_returns_value(self):
        ts = datetime(2026, 1, 1, 12, 0)
        run_id = RunId(mode="hybrid", scope="suite", timestamp=ts)
        assert str(run_id) == run_id.value

    def test_repr_contains_mode_and_scope(self):
        ts = datetime(2026, 1, 1, 12, 0)
        run_id = RunId(mode="hybrid", scope="suite", timestamp=ts)
        r = repr(run_id)
        assert "hybrid" in r
        assert "suite" in r


class TestRunIdInvalidMode:
    def test_invalid_mode_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid mode"):
            RunId(mode="streaming", scope="suite", timestamp=datetime.utcnow())

    def test_empty_mode_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid mode"):
            RunId(mode="", scope="suite", timestamp=datetime.utcnow())

    def test_empty_scope_raises_value_error(self):
        with pytest.raises(ValueError, match="scope cannot be empty"):
            RunId(mode="hybrid", scope="", timestamp=datetime.utcnow())

    def test_whitespace_scope_raises_value_error(self):
        with pytest.raises(ValueError, match="scope cannot be empty"):
            RunId(mode="hybrid", scope="   ", timestamp=datetime.utcnow())


class TestBuildScopeSuite:
    def test_suite_when_nothing_provided(self):
        scope = RunId.build_scope(
            tier=None,
            benchmarks=None,
            test_ids=None,
            total_benchmarks_available=21,
        )
        assert scope == "suite"

    def test_suite_when_benchmarks_match_total(self):
        benchmarks = [f"B{i}" for i in range(1, 4)]
        scope = RunId.build_scope(
            tier=None,
            benchmarks=benchmarks,
            test_ids=None,
            total_benchmarks_available=3,
        )
        assert scope == "suite"


class TestBuildScopeTier:
    def test_tier_1(self):
        scope = RunId.build_scope(
            tier=1,
            benchmarks=["B1"],
            test_ids=None,
            total_benchmarks_available=21,
        )
        assert scope == "tier-1"

    def test_tier_2(self):
        scope = RunId.build_scope(
            tier=2,
            benchmarks=None,
            test_ids=None,
            total_benchmarks_available=21,
        )
        assert scope == "tier-2"

    def test_tier_3(self):
        scope = RunId.build_scope(
            tier=3,
            benchmarks=None,
            test_ids=None,
            total_benchmarks_available=21,
        )
        assert scope == "tier-3"


class TestBuildScopeSingleBenchmark:
    def test_single_benchmark(self):
        scope = RunId.build_scope(
            tier=None,
            benchmarks=["B3"],
            test_ids=None,
            total_benchmarks_available=21,
        )
        assert scope == "benchmark-B3"


class TestBuildScopeMultiBenchmark:
    def test_multi_benchmark_sorted_numerically(self):
        # Pass unsorted; output must be sorted numerically B1 < B3 < B7
        scope = RunId.build_scope(
            tier=None,
            benchmarks=["B7", "B1", "B3"],
            test_ids=None,
            total_benchmarks_available=21,
        )
        assert scope == "benchmarks-B1-B3-B7"

    def test_numeric_sort_not_alphabetical(self):
        # B2, B11, B3 — alphabetically B11 < B2 < B3, numerically B2 < B3 < B11
        scope = RunId.build_scope(
            tier=None,
            benchmarks=["B2", "B11", "B3"],
            test_ids=None,
            total_benchmarks_available=21,
        )
        assert scope == "benchmarks-B2-B3-B11"

    def test_multi_benchmark_explicit(self):
        scope = RunId.build_scope(
            tier=None,
            benchmarks=["B1", "B3", "B7"],
            test_ids=None,
            total_benchmarks_available=21,
        )
        assert scope == "benchmarks-B1-B3-B7"


class TestBuildScopeTestIds:
    def test_single_test_id(self):
        scope = RunId.build_scope(
            tier=None,
            benchmarks=None,
            test_ids=["B3-001"],
            total_benchmarks_available=21,
        )
        assert scope == "test-B3-001"

    def test_multi_test_id(self):
        scope = RunId.build_scope(
            tier=None,
            benchmarks=None,
            test_ids=["B3-002", "B3-001"],
            total_benchmarks_available=21,
        )
        assert scope == "test-B3-001-B3-002"

    def test_test_ids_take_precedence_over_benchmarks(self):
        scope = RunId.build_scope(
            tier=None,
            benchmarks=["B1", "B3"],
            test_ids=["B3-001"],
            total_benchmarks_available=21,
        )
        assert scope == "test-B3-001"

    def test_test_ids_take_precedence_over_tier(self):
        scope = RunId.build_scope(
            tier=2,
            benchmarks=None,
            test_ids=["B3-001"],
            total_benchmarks_available=21,
        )
        assert scope == "test-B3-001"

    def test_five_test_ids_inlined(self):
        """Up to 5 test ids stay in the filename for legibility."""
        scope = RunId.build_scope(
            tier=None,
            benchmarks=None,
            test_ids=["B01-007", "B01-009", "B02-012", "B02-014", "B03-002"],
            total_benchmarks_available=24,
        )
        assert scope == "test-B01-007-B01-009-B02-012-B02-014-B03-002"

    def test_six_test_ids_collapsed_to_count_and_hash(self):
        """Beyond 5 test ids, filename collapses to count + content hash."""
        scope = RunId.build_scope(
            tier=None,
            benchmarks=None,
            test_ids=["B01-007", "B01-009", "B02-012", "B02-014", "B03-002", "B03-030"],
            total_benchmarks_available=24,
        )
        assert scope.startswith("tests-6-")
        assert len(scope) == len("tests-6-") + 8  # 8-char sha1 prefix

    def test_thirty_test_ids_keeps_filename_short(self):
        """The B1 stratified-sample case: 30 test_ids must not blow OS filename limit."""
        ids = [f"B0{i}-{j:03d}" for i in range(1, 4) for j in range(1, 11)]
        scope = RunId.build_scope(
            tier=None,
            benchmarks=None,
            test_ids=ids,
            total_benchmarks_available=24,
        )
        assert scope.startswith("tests-30-")
        # Full filename including run-id prefix and result suffix must stay
        # well under the 255-byte filesystem limit.
        full_filename = (
            f"eval-run-llm-only-{scope}-20260425-1100-primus-reasoning.json"
        )
        assert len(full_filename) < 255

    def test_collapse_is_deterministic_under_reordering(self):
        """Hash uses sorted ids, so input order must not matter."""
        ids_a = ["B01-007", "B01-009", "B02-012", "B02-014", "B03-002", "B03-030"]
        ids_b = list(reversed(ids_a))
        scope_a = RunId.build_scope(
            tier=None, benchmarks=None, test_ids=ids_a, total_benchmarks_available=24
        )
        scope_b = RunId.build_scope(
            tier=None, benchmarks=None, test_ids=ids_b, total_benchmarks_available=24
        )
        assert scope_a == scope_b


class TestForQuery:
    def test_for_query_produces_scope_query(self):
        run_id = RunId.for_query()
        assert run_id.scope == "query"

    def test_for_query_default_mode_is_hybrid(self):
        run_id = RunId.for_query()
        assert run_id.mode == "hybrid"

    def test_for_query_accepts_custom_mode(self):
        run_id = RunId.for_query(mode="llm-only")
        assert run_id.mode == "llm-only"

    def test_for_query_accepts_custom_timestamp(self):
        ts = datetime(2026, 4, 21, 14, 0)
        run_id = RunId.for_query(timestamp=ts)
        assert run_id.timestamp == ts
        assert "query" in run_id.value

    def test_for_query_value_format(self):
        ts = datetime(2026, 4, 21, 14, 30)
        run_id = RunId.for_query(mode="hybrid", timestamp=ts)
        assert run_id.value == "eval-run-hybrid-query-20260421-1430"
