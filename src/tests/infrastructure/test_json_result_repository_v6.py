"""
Tests for JSONResultRepository schema-v6 behavior.

Covers:
- Monthly directory layout: {results_dir}/{yyyy-MM}/{run_id}-{model}.json
- Sidecar file: {run_id}-contexts.json in same monthly dir
- schema_version=6 marker in metadata
- run_id in metadata
- Non-zero token/latency field serialization
- save_query_run produces same filename shape
- load_by_model glob across monthly subdirs, skips legacy v5 and sidecars
- save_batch is a no-op (logs, writes nothing)
- _generate_filename_v6 raises when metadata lacks run_id
"""

import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest

from domain.entities.evaluation_result import EvaluationResult
from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.ccop_section import CCoPSection
from domain.value_objects.difficulty_level import DifficultyLevel
from infrastructure.adapters.repositories.json_result_repository import JSONResultRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MODEL_NAME = "primus-reasoning"
RUN_ID = "eval-run-hybrid-suite-20260421-1430"
MONTH = "2026-04"
EVAL_AT = f"{MONTH}-21T14:30:00"


def _make_logger():
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    return logger


def _make_test_case(test_id: str = "B3-001", benchmark: str = "B3") -> TestCase:
    # TestCase.question must be >= 50 chars
    question = "What are the MFA requirements under CCoP 2.0 for privileged access?"
    return TestCase(
        test_id=test_id,
        benchmark_type=BenchmarkType(benchmark),
        section=CCoPSection("Section 5"),
        clause_reference="5.1.1",
        difficulty=DifficultyLevel.MEDIUM,
        question=question,
        expected_response="MFA is required for privileged access.",
        evaluation_criteria={},
    )


def _make_model_response(
    prompt_tokens: int = 10,
    completion_tokens: int = 20,
    latency_ms: int = 500,
) -> ModelResponse:
    return ModelResponse(
        content="MFA is required.",
        model_name=MODEL_NAME,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=latency_ms,
    )


def _make_evaluation_result(
    test_id: str = "B3-001",
    benchmark: str = "B3",
    prompt_tokens: int = 10,
    completion_tokens: int = 20,
    latency_ms: int = 500,
    system_prompt: str = "You are a CCoP expert.",
    user_prompt: str = "What are the MFA requirements under CCoP 2.0 for privileged access?",
) -> EvaluationResult:
    return EvaluationResult(
        test_case=_make_test_case(test_id=test_id, benchmark=benchmark),
        model_response=_make_model_response(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
        ),
        overall_score=0.75,
        passed=True,
        evaluation_mode="hybrid",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )


def _make_metadata(
    run_id: str = RUN_ID,
    model_name: str = MODEL_NAME,
    evaluated_at: str = EVAL_AT,
) -> dict:
    return {
        "run_id": run_id,
        "model_name": model_name,
        "evaluated_at": evaluated_at,
        "schema_version": 6,
        "evaluation_phase": "baseline",
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSaveEvaluationRunMonthlyLayout:
    """save_evaluation_run writes to {results_dir}/{yyyy-MM}/{run_id}-{model}.json."""

    def test_file_lands_in_monthly_subdir(self, tmp_path):
        repo = JSONResultRepository(tmp_path, _make_logger())
        result = _make_evaluation_result()
        metadata = _make_metadata()

        import asyncio
        filepath = asyncio.run(repo.save_evaluation_run([result], metadata))

        expected_dir = tmp_path / MONTH
        assert expected_dir.is_dir()
        expected_file = expected_dir / f"{RUN_ID}-{MODEL_NAME}.json"
        assert expected_file.exists()
        assert filepath == str(expected_file)

    def test_metadata_run_id_present(self, tmp_path):
        repo = JSONResultRepository(tmp_path, _make_logger())
        result = _make_evaluation_result()
        metadata = _make_metadata()

        import asyncio
        asyncio.run(repo.save_evaluation_run([result], metadata))

        saved = json.loads((tmp_path / MONTH / f"{RUN_ID}-{MODEL_NAME}.json").read_text())
        assert saved["metadata"]["run_id"] == RUN_ID

    def test_metadata_schema_version_is_6(self, tmp_path):
        repo = JSONResultRepository(tmp_path, _make_logger())
        result = _make_evaluation_result()
        metadata = _make_metadata()

        import asyncio
        asyncio.run(repo.save_evaluation_run([result], metadata))

        saved = json.loads((tmp_path / MONTH / f"{RUN_ID}-{MODEL_NAME}.json").read_text())
        assert saved["metadata"]["schema_version"] == 6

    def test_token_and_latency_fields_serialized(self, tmp_path):
        repo = JSONResultRepository(tmp_path, _make_logger())
        result = _make_evaluation_result(prompt_tokens=15, completion_tokens=25, latency_ms=750)
        metadata = _make_metadata()

        import asyncio
        asyncio.run(repo.save_evaluation_run([result], metadata))

        saved = json.loads((tmp_path / MONTH / f"{RUN_ID}-{MODEL_NAME}.json").read_text())
        entry = saved["test_results"][0]
        assert entry["prompt_tokens"] == 15
        assert entry["completion_tokens"] == 25
        assert entry["total_tokens"] == 40  # 15 + 25
        assert entry["latency_ms"] == 750

    def test_system_prompt_serialized(self, tmp_path):
        sys_prompt = "You are a CCoP expert."
        repo = JSONResultRepository(tmp_path, _make_logger())
        result = _make_evaluation_result(system_prompt=sys_prompt)
        metadata = _make_metadata()

        import asyncio
        asyncio.run(repo.save_evaluation_run([result], metadata))

        saved = json.loads((tmp_path / MONTH / f"{RUN_ID}-{MODEL_NAME}.json").read_text())
        assert saved["test_results"][0]["system_prompt"] == sys_prompt


class TestSidecarFile:
    """Sidecar {run_id}-contexts.json written alongside main file."""

    def test_sidecar_written_when_contexts_provided(self, tmp_path):
        repo = JSONResultRepository(tmp_path, _make_logger())
        result = _make_evaluation_result()
        metadata = _make_metadata()
        contexts = {"B3-001": [{"text": "MFA text", "citation_id": "CCoP-5.2.1"}]}

        import asyncio
        asyncio.run(repo.save_evaluation_run([result], metadata, contexts_by_test_id=contexts))

        sidecar = tmp_path / MONTH / f"{RUN_ID}-contexts.json"
        assert sidecar.exists()

    def test_sidecar_payload_intact(self, tmp_path):
        repo = JSONResultRepository(tmp_path, _make_logger())
        result = _make_evaluation_result()
        metadata = _make_metadata()
        contexts = {
            "B3-001": [
                {"text": "MFA text", "citation_id": "CCoP-5.2.1", "score": 0.85},
                {"text": "Another chunk", "citation_id": "CCoP-5.3.1", "score": 0.72},
            ]
        }

        import asyncio
        asyncio.run(repo.save_evaluation_run([result], metadata, contexts_by_test_id=contexts))

        sidecar_data = json.loads(
            (tmp_path / MONTH / f"{RUN_ID}-contexts.json").read_text()
        )
        assert sidecar_data == contexts

    def test_no_sidecar_when_contexts_not_provided(self, tmp_path):
        repo = JSONResultRepository(tmp_path, _make_logger())
        result = _make_evaluation_result()
        metadata = _make_metadata()

        import asyncio
        asyncio.run(repo.save_evaluation_run([result], metadata))

        sidecar = tmp_path / MONTH / f"{RUN_ID}-contexts.json"
        assert not sidecar.exists()


class TestSaveQueryRun:
    """save_query_run writes {run_id}-{model}.json in same monthly layout."""

    def test_query_run_filename_shape(self, tmp_path):
        repo = JSONResultRepository(tmp_path, _make_logger())
        run_id = "eval-run-hybrid-query-20260421-1430"
        metadata = {
            "run_id": run_id,
            "model_name": MODEL_NAME,
            "evaluated_at": EVAL_AT,
            "schema_version": 6,
        }
        test_results = [{"question": "What are MFA requirements?", "response": "MFA required."}]

        import asyncio
        filepath = asyncio.run(repo.save_query_run(metadata, test_results))

        expected_file = tmp_path / MONTH / f"{run_id}-{MODEL_NAME}.json"
        assert expected_file.exists()
        assert filepath == str(expected_file)

    def test_query_run_sidecar_written(self, tmp_path):
        repo = JSONResultRepository(tmp_path, _make_logger())
        run_id = "eval-run-hybrid-query-20260421-1430"
        metadata = {
            "run_id": run_id,
            "model_name": MODEL_NAME,
            "evaluated_at": EVAL_AT,
            "schema_version": 6,
        }
        test_results = [{"question": "q", "response": "r"}]
        contexts = {"query-001": [{"text": "t", "citation_id": "c"}]}

        import asyncio
        asyncio.run(repo.save_query_run(metadata, test_results, contexts_by_test_id=contexts))

        sidecar = tmp_path / MONTH / f"{run_id}-contexts.json"
        assert sidecar.exists()


class TestLoadByModel:
    """load_by_model discovers v6 files via rglob, skips sidecars and legacy files."""

    # Minimum 50 chars required by TestCase.question validator
    _QUESTION = "What are the MFA requirements under CCoP 2.0 for privileged access?"

    def _write_v6_file(self, base_dir: Path, month: str, run_id: str, model: str, test_id: str = "B3-001"):
        """Write a minimal schema-v6 result file."""
        month_dir = base_dir / month
        month_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "metadata": {
                "run_id": run_id,
                "model_name": model,
                "evaluated_at": f"{month}-01T10:00:00",
                "schema_version": 6,
            },
            "test_results": [
                {
                    "test_id": test_id,
                    "benchmark": "B3",
                    "model": model,
                    "question": self._QUESTION,
                    "response": "Test response for MFA requirements.",
                    "score": 0.75,
                    "passed": True,
                    "tokens": 100,
                    "latency_ms": 500,
                    "prompt_tokens": 40,
                    "completion_tokens": 60,
                    "total_tokens": 100,
                    "system_prompt": "You are a CCoP 2.0 expert assistant.",
                    "user_prompt": self._QUESTION,
                    "evaluated_at": f"{month}-01T10:00:00",
                }
            ],
        }
        filepath = month_dir / f"{run_id}-{model}.json"
        filepath.write_text(json.dumps(data))
        return filepath

    def _write_legacy_file(self, base_dir: Path, model: str, month: str = "2026-04"):
        """
        Write a legacy pre-v6 result file that matches the glob but fails schema check.

        Uses same filename format as v6 (*-{model}.json) but omits run_id / schema_version.
        """
        month_dir = base_dir / month
        month_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "metadata": {"model_name": model},  # no run_id, no schema_version
            "test_results": [],
        }
        filepath = month_dir / f"legacy-result-{model}.json"
        filepath.write_text(json.dumps(data))
        return filepath

    def test_discovers_v6_files_across_monthly_subdirs(self, tmp_path):
        self._write_v6_file(tmp_path, "2026-03", "run-01", MODEL_NAME, "B3-001")
        self._write_v6_file(tmp_path, "2026-04", "run-02", MODEL_NAME, "B3-002")

        import asyncio
        repo = JSONResultRepository(tmp_path, _make_logger())
        results = asyncio.run(repo.load_by_model(MODEL_NAME))

        assert len(results) == 2

    def test_skips_legacy_pre_v6_file(self, tmp_path):
        self._write_v6_file(tmp_path, "2026-04", "run-01", MODEL_NAME)
        self._write_legacy_file(tmp_path, MODEL_NAME)

        logger = _make_logger()
        import asyncio
        repo = JSONResultRepository(tmp_path, logger)
        results = asyncio.run(repo.load_by_model(MODEL_NAME))

        # Only the v6 file should be loaded
        assert len(results) == 1
        # Legacy skip should have been warned about
        logger.warning.assert_called()
        warning_calls = [str(c) for c in logger.warning.call_args_list]
        assert any("legacy" in c.lower() for c in warning_calls)

    def test_skips_sidecar_files(self, tmp_path):
        self._write_v6_file(tmp_path, "2026-04", "run-01", MODEL_NAME)
        # Write a sidecar manually
        month_dir = tmp_path / "2026-04"
        sidecar = month_dir / f"run-01-contexts.json"
        sidecar.write_text(json.dumps({"B3-001": []}))

        import asyncio
        repo = JSONResultRepository(tmp_path, _make_logger())
        results = asyncio.run(repo.load_by_model(MODEL_NAME))

        # Only the main file result, not the sidecar
        assert len(results) == 1

    def test_returns_empty_when_no_v6_files(self, tmp_path):
        import asyncio
        repo = JSONResultRepository(tmp_path, _make_logger())
        results = asyncio.run(repo.load_by_model(MODEL_NAME))
        assert results == []

    def test_reconstructed_results_have_correct_test_id(self, tmp_path):
        self._write_v6_file(tmp_path, "2026-04", "run-01", MODEL_NAME, "B3-099")

        import asyncio
        repo = JSONResultRepository(tmp_path, _make_logger())
        results = asyncio.run(repo.load_by_model(MODEL_NAME))

        assert len(results) == 1
        assert results[0].test_case.test_id == "B3-099"


class TestSaveBatchNoOp:
    """save_batch is a logged no-op in schema v6."""

    def test_save_batch_writes_no_files(self, tmp_path):
        repo = JSONResultRepository(tmp_path, _make_logger())
        result = _make_evaluation_result()

        import asyncio
        asyncio.run(repo.save_batch([result]))

        # No files should have been written
        all_files = list(tmp_path.rglob("*.json"))
        assert len(all_files) == 0

    def test_save_batch_logs_no_op_message(self, tmp_path):
        logger = _make_logger()
        repo = JSONResultRepository(tmp_path, logger)
        result = _make_evaluation_result()

        import asyncio
        asyncio.run(repo.save_batch([result]))

        logger.debug.assert_called_once()
        debug_msg = str(logger.debug.call_args)
        assert "no-op" in debug_msg.lower() or "v6" in debug_msg.lower()


class TestGenerateFilenameV6:
    """_generate_filename_v6 raises when run_id missing."""

    def test_raises_without_run_id(self, tmp_path):
        repo = JSONResultRepository(tmp_path, _make_logger())
        with pytest.raises(ValueError, match="run_id"):
            repo._generate_filename_v6({"model_name": MODEL_NAME})

    def test_generates_correct_filename(self, tmp_path):
        repo = JSONResultRepository(tmp_path, _make_logger())
        filename = repo._generate_filename_v6({"run_id": RUN_ID, "model_name": MODEL_NAME})
        assert filename == f"{RUN_ID}-{MODEL_NAME}.json"
