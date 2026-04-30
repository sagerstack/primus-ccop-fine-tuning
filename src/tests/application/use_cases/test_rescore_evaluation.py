"""
Tests for RescoreEvaluationUseCase.

Mocked unit tests covering:
  - Source file lookup by run_id (single match)
  - Source file lookup raises on no match / multiple matches
  - Run ID timestamp replacement preserves mode/scope
  - Scope extraction from run_id
  - Reconstructed ModelResponse carries frozen content
  - Retrieved-context sidecar parsing (string list and dict list)
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from application.use_cases.rescore_evaluation import RescoreEvaluationUseCase
from domain.entities.model_response import ModelResponse


def _mk_logger() -> MagicMock:
    return MagicMock(spec=["info", "warning", "debug", "error"])


def _mk_uc(tmp_path: Path) -> RescoreEvaluationUseCase:
    return RescoreEvaluationUseCase(
        test_case_repository=AsyncMock(),
        result_repository=AsyncMock(),
        results_dir=tmp_path,
        logger=_mk_logger(),
    )


class TestSourceFileLookup:
    def test_finds_single_match(self, tmp_path):
        # Arrange: write a fake source file
        month_dir = tmp_path / "2026-04"
        month_dir.mkdir()
        target = month_dir / "eval-run-llm-only-test-B01-007-20260425-0458-primus-reasoning.json"
        target.write_text("{}")
        # Decoy that should NOT match
        (month_dir / "eval-run-llm-only-test-B01-007-20260425-0458-contexts.json").write_text("{}")

        uc = _mk_uc(tmp_path)
        path = uc._find_source_file("eval-run-llm-only-test-B01-007-20260425-0458")
        assert path == target

    def test_raises_on_no_match(self, tmp_path):
        uc = _mk_uc(tmp_path)
        with pytest.raises(FileNotFoundError, match="No source result file"):
            uc._find_source_file("eval-run-bogus-id")

    def test_raises_on_multiple_matches(self, tmp_path):
        month_dir = tmp_path / "2026-04"
        month_dir.mkdir()
        # Two files share the same run_id prefix (unusual but possible)
        (month_dir / "eval-run-llm-only-x-20260425-0458-primus-reasoning.json").write_text("{}")
        (month_dir / "eval-run-llm-only-x-20260425-0458-other-model.json").write_text("{}")

        uc = _mk_uc(tmp_path)
        with pytest.raises(ValueError, match="Ambiguous source"):
            uc._find_source_file("eval-run-llm-only-x-20260425-0458")

    def test_excludes_partial_jsonl(self, tmp_path):
        """Partial files must not be picked up as source files."""
        month_dir = tmp_path / "2026-04"
        month_dir.mkdir()
        target = month_dir / "eval-run-llm-only-y-20260425-0458-primus.json"
        target.write_text("{}")
        # Partial file with same prefix
        (month_dir / "eval-run-llm-only-y-20260425-0458-primus.partial.jsonl").write_text("")

        uc = _mk_uc(tmp_path)
        path = uc._find_source_file("eval-run-llm-only-y-20260425-0458")
        assert path == target


class TestRunIdConstruction:
    def test_rebuilds_with_current_timestamp(self, tmp_path):
        uc = _mk_uc(tmp_path)
        new_id = uc._build_rescore_run_id(
            "eval-run-hybrid-tests-30-abc12345-20260425-0458",
            datetime(2026, 4, 26, 12, 30),
        )
        assert new_id == "eval-run-hybrid-tests-30-abc12345-20260426-1230"

    def test_handles_unexpected_format_with_fallback(self, tmp_path):
        uc = _mk_uc(tmp_path)
        # Truly weird single-segment id — rsplit yields just one part, fallback
        new_id = uc._build_rescore_run_id(
            "weirdid",
            datetime(2026, 4, 26, 12, 30),
        )
        assert new_id.startswith("weirdid-rescored-")
        assert "20260426-1230" in new_id


class TestScopeExtraction:
    def test_extracts_scope_for_known_mode(self, tmp_path):
        uc = _mk_uc(tmp_path)
        scope = uc._extract_scope_from_run_id(
            "eval-run-hybrid-tests-30-abc12345-20260425-0458",
            "hybrid",
        )
        assert scope == "tests-30-abc12345"

    def test_strips_eval_run_prefix_when_mode_unknown(self, tmp_path):
        """When mode is None, prefix is just 'eval-run-' so the rest of the id
        (mode-and-scope) is captured. Best-effort extraction — not strictly
        the scope alone, but usable for matching partial files."""
        uc = _mk_uc(tmp_path)
        scope = uc._extract_scope_from_run_id(
            "eval-run-hybrid-tests-30-abc12345-20260425-0458",
            None,
        )
        # mode-and-scope gets returned as a unit
        assert scope == "hybrid-tests-30-abc12345"

    def test_returns_unknown_when_run_id_doesnt_match_format(self, tmp_path):
        uc = _mk_uc(tmp_path)
        scope = uc._extract_scope_from_run_id("totally-weird-id", "hybrid")
        assert scope == "unknown"


class TestReconstruct:
    def test_model_response_uses_frozen_content(self, tmp_path):
        uc = _mk_uc(tmp_path)
        entry = {
            "response": "frozen primus output text",
            "model": "primus-reasoning",
            "tokens": 250,
            "latency_ms": 8500,
            "prompt_tokens": 120,
            "completion_tokens": 130,
            "total_tokens": 250,
        }
        mr = uc._reconstruct_model_response(entry)
        assert isinstance(mr, ModelResponse)
        assert mr.content == "frozen primus output text"
        assert mr.model_name == "primus-reasoning"
        assert mr.tokens_used == 250

    def test_extract_contexts_string_list(self, tmp_path):
        uc = _mk_uc(tmp_path)
        ctxs = uc._extract_retrieved_contexts(["clause text 1", "clause text 2"])
        assert ctxs == ["clause text 1", "clause text 2"]

    def test_extract_contexts_dict_list(self, tmp_path):
        uc = _mk_uc(tmp_path)
        ctxs = uc._extract_retrieved_contexts([
            {"text": "clause 5.3.1", "score": 0.9},
            {"content": "clause 5.3.2"},
        ])
        assert ctxs == ["clause 5.3.1", "clause 5.3.2"]

    def test_extract_contexts_none_or_empty(self, tmp_path):
        uc = _mk_uc(tmp_path)
        assert uc._extract_retrieved_contexts(None) is None
        assert uc._extract_retrieved_contexts([]) is None
