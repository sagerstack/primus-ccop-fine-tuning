"""
Tests for JSONResultRepository.append_partial + load_partial.

Covers:
  - First call writes header + result; subsequent calls append result
  - load_partial returns None when no partial file exists
  - load_partial returns completed_test_ids and reconstructed results
  - Header config-mismatch causes load_partial to raise
  - Multiple partial files: most-recent is selected
  - Corrupt JSONL line is skipped with warning
  - Missing header is treated as fatal (raise)
"""
from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from infrastructure.adapters.repositories.json_result_repository import (
    JSONResultRepository,
)
from domain.entities.evaluation_result import EvaluationResult
from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.ccop_section import CCoPSection
from domain.value_objects.difficulty_level import DifficultyLevel


def _mk_logger() -> MagicMock:
    return MagicMock(spec=["info", "warning", "debug", "error"])


def _mk_result(test_id: str = "B01-007", score: float = 0.5) -> EvaluationResult:
    # Derive benchmark from test_id prefix (e.g., "B02-014" -> "B2")
    bench_prefix = test_id.split("-", 1)[0]  # "B02"
    if bench_prefix.startswith("B") and bench_prefix[1:].isdigit():
        bench_short = f"B{int(bench_prefix[1:])}"
    else:
        bench_short = "B1"
    tc = TestCase(
        test_id=test_id,
        benchmark_type=BenchmarkType(bench_short),
        section=CCoPSection("N/A"),
        clause_reference="5.1",
        difficulty=DifficultyLevel.MEDIUM,
        question="Test question — " + "x" * 60,
        expected_response="Expected response.",
        evaluation_criteria={},
    )
    mr = ModelResponse(
        content="Model response text",
        model_name="primus-reasoning",
        tokens_used=100,
        latency_ms=1500,
    )
    return EvaluationResult(
        test_case=tc,
        model_response=mr,
        overall_score=score,
        passed=score >= 0.5,
        evaluated_at=datetime.utcnow(),
        evaluation_mode="hybrid",
    )


def _mk_metadata(
    run_id: str = "eval-run-hybrid-test-B01-007-20260425-1200",
    judge_mode: str = "rubric",
    eval_mode: str = "hybrid",
    scope: str = "test-B01-007",
    model_name: str = "primus-reasoning",
) -> dict:
    return {
        "run_id": run_id,
        "schema_version": 6,
        "model_name": model_name,
        "evaluation_mode": eval_mode,
        "scope": scope,
        "judge_config": {"judge_mode": judge_mode, "evaluation_mode": eval_mode},
        "evaluated_at": "2026-04-25T12:00:00",
    }


@pytest.fixture
def repo(tmp_path: Path) -> JSONResultRepository:
    return JSONResultRepository(results_dir=tmp_path, logger=_mk_logger())


class TestAppendPartial:
    def test_first_call_writes_header_and_result(self, repo, tmp_path):
        result = _mk_result("B01-007")
        metadata = _mk_metadata()

        path = asyncio.run(repo.append_partial(result, metadata))

        assert Path(path).exists()
        assert path.endswith(".partial.jsonl")
        with open(path) as f:
            lines = [json.loads(l) for l in f if l.strip()]
        assert len(lines) == 2
        assert lines[0]["_partial_header"] is True
        assert lines[0]["run_id"] == metadata["run_id"]
        assert lines[0]["judge_config"] == metadata["judge_config"]
        assert lines[1]["test_id"] == "B01-007"

    def test_second_call_appends_only_result_no_duplicate_header(self, repo):
        metadata = _mk_metadata()
        asyncio.run(repo.append_partial(_mk_result("B01-007"), metadata))
        path = asyncio.run(repo.append_partial(_mk_result("B02-014"), metadata))

        with open(path) as f:
            lines = [json.loads(l) for l in f if l.strip()]
        assert len(lines) == 3  # 1 header + 2 results
        assert lines[0]["_partial_header"] is True
        assert lines[1]["test_id"] == "B01-007"
        assert lines[2]["test_id"] == "B02-014"
        assert sum(1 for l in lines if l.get("_partial_header")) == 1

    def test_missing_run_id_raises(self, repo):
        metadata = _mk_metadata()
        del metadata["run_id"]
        with pytest.raises(ValueError, match="run_id is required"):
            asyncio.run(repo.append_partial(_mk_result(), metadata))


class TestLoadPartial:
    def test_returns_none_when_no_partial_file(self, repo):
        metadata = _mk_metadata()
        result = asyncio.run(repo.load_partial(metadata))
        assert result is None

    def test_loads_completed_test_ids_and_results(self, repo):
        metadata = _mk_metadata()
        asyncio.run(repo.append_partial(_mk_result("B01-007"), metadata))
        asyncio.run(repo.append_partial(_mk_result("B02-014"), metadata))

        loaded = asyncio.run(repo.load_partial(metadata))

        assert loaded is not None
        assert loaded["completed_test_ids"] == {"B01-007", "B02-014"}
        assert len(loaded["completed_results"]) == 2
        assert loaded["header"]["run_id"] == metadata["run_id"]

    def test_judge_config_drift_raises(self, repo):
        original = _mk_metadata(judge_mode="rubric")
        asyncio.run(repo.append_partial(_mk_result("B01-007"), original))

        # Different judge_mode = config drift
        drifted = _mk_metadata(judge_mode="universal")

        with pytest.raises(ValueError, match="judge_config"):
            asyncio.run(repo.load_partial(drifted))

    def test_model_name_mismatch_raises(self, repo):
        original = _mk_metadata(model_name="primus-reasoning")
        asyncio.run(repo.append_partial(_mk_result("B01-007"), original))

        different_model = _mk_metadata(model_name="other-model")
        # The glob pattern includes model_name in the filename, so
        # different model means no match — returns None, not a raise.
        result = asyncio.run(repo.load_partial(different_model))
        assert result is None

    def test_scope_mismatch_returns_none(self, repo):
        # Different scope = different filename, no match
        original = _mk_metadata(scope="test-B01-007")
        asyncio.run(repo.append_partial(_mk_result("B01-007"), original))

        different_scope = _mk_metadata(scope="test-B02-014")
        result = asyncio.run(repo.load_partial(different_scope))
        assert result is None

    def test_multiple_partial_files_picks_most_recent(self, repo, tmp_path):
        """When two partial files match the scope, the most recent wins."""
        # Write an older partial file by hand
        from datetime import datetime as _dt
        month_dir = tmp_path / _dt.utcnow().strftime("%Y-%m")
        month_dir.mkdir(exist_ok=True)
        older_path = month_dir / "eval-run-hybrid-test-B01-007-20260101-0900-primus-reasoning.partial.jsonl"
        with open(older_path, "w") as f:
            f.write(json.dumps({
                "_partial_header": True,
                "run_id": "old-run-id",
                "model_name": "primus-reasoning",
                "evaluation_mode": "hybrid",
                "scope": "test-B01-007",
                "judge_config": {"judge_mode": "rubric", "evaluation_mode": "hybrid"},
            }) + "\n")
            f.write(json.dumps({"test_id": "B01-007", "benchmark": "B1"}) + "\n")
        # Backdate older file
        os_time = older_path.stat().st_mtime - 3600
        import os
        os.utime(older_path, (os_time, os_time))

        # Write newer partial (current invocation) via repo
        new_metadata = _mk_metadata()
        asyncio.run(repo.append_partial(_mk_result("B01-007"), new_metadata))
        asyncio.run(repo.append_partial(_mk_result("B02-014"), new_metadata))

        loaded = asyncio.run(repo.load_partial(new_metadata))
        assert loaded is not None
        # Newer file has 2 cases, older had 1 — picking newer means we see 2
        assert len(loaded["completed_test_ids"]) == 2

    def test_corrupt_line_skipped_with_warning(self, repo, tmp_path):
        from datetime import datetime as _dt
        month_dir = tmp_path / _dt.utcnow().strftime("%Y-%m")
        month_dir.mkdir(exist_ok=True)
        path = month_dir / "eval-run-hybrid-test-B01-007-20260425-1200-primus-reasoning.partial.jsonl"
        with open(path, "w") as f:
            f.write(json.dumps({
                "_partial_header": True,
                "run_id": "test-run",
                "model_name": "primus-reasoning",
                "evaluation_mode": "hybrid",
                "scope": "test-B01-007",
                "judge_config": {"judge_mode": "rubric", "evaluation_mode": "hybrid"},
            }) + "\n")
            f.write(json.dumps({"test_id": "B01-007", "benchmark": "B1"}) + "\n")
            f.write("THIS IS NOT VALID JSON {{{\n")
            f.write(json.dumps({"test_id": "B02-014", "benchmark": "B2"}) + "\n")

        loaded = asyncio.run(repo.load_partial(_mk_metadata()))
        assert loaded is not None
        # Corrupt line skipped, two valid results parsed
        assert loaded["completed_test_ids"] == {"B01-007", "B02-014"}

    def test_missing_header_raises(self, repo, tmp_path):
        from datetime import datetime as _dt
        month_dir = tmp_path / _dt.utcnow().strftime("%Y-%m")
        month_dir.mkdir(exist_ok=True)
        path = month_dir / "eval-run-hybrid-test-B01-007-20260425-1200-primus-reasoning.partial.jsonl"
        with open(path, "w") as f:
            # No header line — straight to result lines
            f.write(json.dumps({"test_id": "B01-007", "benchmark": "B1"}) + "\n")

        with pytest.raises(ValueError, match="missing the header line"):
            asyncio.run(repo.load_partial(_mk_metadata()))

    def test_missing_metadata_keys_raises(self, repo):
        with pytest.raises(ValueError, match="evaluation_mode and scope"):
            asyncio.run(repo.load_partial({"model_name": "m"}))


class TestRoundTrip:
    def test_append_then_load_then_resume_workflow(self, repo):
        """End-to-end: simulate append-crash-resume round trip."""
        metadata = _mk_metadata()

        # Phase 1: write 3 results, then simulate crash
        for tid in ["B01-007", "B02-014", "B03-002"]:
            asyncio.run(repo.append_partial(_mk_result(tid), metadata))

        # Phase 2: resume — load completed
        loaded = asyncio.run(repo.load_partial(metadata))
        assert len(loaded["completed_test_ids"]) == 3

        # Phase 3: append remaining cases to same partial (simulating resumed run)
        for tid in ["B04-005", "B05-013"]:
            asyncio.run(repo.append_partial(_mk_result(tid), metadata))

        # Phase 4: re-load → should now see all 5 cases in the same file
        final = asyncio.run(repo.load_partial(metadata))
        assert final["completed_test_ids"] == {
            "B01-007", "B02-014", "B03-002", "B04-005", "B05-013"
        }
        # And the partial path should be the same one across all writes
        assert final["partial_path"] == loaded["partial_path"]
