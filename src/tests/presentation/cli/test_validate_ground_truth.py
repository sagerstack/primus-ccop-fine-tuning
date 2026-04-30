"""Tests for the `ccop-eval validate-ground-truth` CLI command.

Covers Plan 07 verify criteria:
  1. Clean v2 ground truth passes (exit 0).
  2. Hallucinated clause_reference fails (non-zero + message).
  3. Deprecated test cases bypass the gate (exit 0).
  4. Hallucinated inline CCoP citation in expected_response fails.

All tests use --no-semantic so Qdrant is not required in CI-adjacent envs;
Plan 07 leaves the semantic gate as an operator-run concern.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from presentation.cli.commands.validate_ground_truth import validate_app

REPO_ROOT = Path(__file__).resolve().parents[4]
REAL_TEST_SUITE = REPO_ROOT / "ground-truth" / "test-suite"
REAL_INVENTORY = (
    REPO_ROOT / "src" / "rag" / "ingestion" / "fixtures" / "clause_inventory.json"
)


def _invoke(runner: CliRunner, *extra: str) -> "pytest.Result":  # type: ignore[name-defined]
    return runner.invoke(validate_app, ["--no-semantic", *extra])


def _valid_v2_row(test_id: str, benchmark_id: str, clause_ref: list[str]) -> dict:
    """Minimal v2 test case satisfying the v2 JSON schema."""
    return {
        "test_id": test_id,
        "version": "2.0",
        "benchmark_id": benchmark_id,
        "metadata": {
            "test_category": "positive",
            "difficulty": "medium",
            "section": "5",
            "clause_reference": clause_ref,
            "domain": "IT",
            "created_date": "2026-04-22",
        },
        "input": {
            "question": (
                "This is a fixture question long enough to satisfy the "
                "minLength 50 character constraint for v2 test cases."
            ),
            "scenario_sector": "banking",
            "scenario_role": "risk_manager",
        },
        "ground_truth": {
            "expected_response": (
                "Reference: CCoP 2.0 §5.3.1 — this is a fixture expected "
                "response long enough to pass the minLength 50 constraint."
            ),
            "key_facts": [
                {
                    "fact": "example fact A for fixture",
                    "source": "CCoP 2.0 §5.3.1",
                    "tier": "critical",
                },
                {
                    "fact": "example fact B for fixture",
                    "source": "CCoP 2.0 §5.3.1",
                    "tier": "critical",
                },
            ],
            "reasoning_chain": ["step 1"],
            "acceptable_variations": ["variant"],
        },
        "fail_conditions": {
            "forbidden_claims": ["must-not-say"],
            "hallucination_patterns": [],
        },
    }


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_validator_accepts_clean_ground_truth(runner: CliRunner) -> None:
    """SC #17 — real corrected ground truth passes the validator."""
    result = _invoke(
        runner,
        "--test-suite-dir",
        str(REAL_TEST_SUITE),
        "--inventory",
        str(REAL_INVENTORY),
    )
    assert result.exit_code == 0, result.stdout


def test_validator_rejects_hallucinated_clause(
    tmp_path: Path, runner: CliRunner
) -> None:
    """A fabricated clause_reference like '9.9.9' must hard-fail."""
    bad = _valid_v2_row("B99-001", "B99", ["9.9.9"])
    fixture = tmp_path / "b99_bad_clause.jsonl"
    fixture.write_text(json.dumps(bad) + "\n")

    result = _invoke(
        runner,
        "--file",
        str(fixture),
        "--inventory",
        str(REAL_INVENTORY),
    )
    assert result.exit_code != 0
    assert "not found in inventory" in result.stdout


def test_validator_skips_deprecated_cases(
    tmp_path: Path, runner: CliRunner
) -> None:
    """Cases marked status=deprecated bypass the gate, even with bad clauses."""
    deprecated = _valid_v2_row("B99-002", "B99", ["9.9.9"])
    deprecated["status"] = "deprecated"
    deprecated["deprecated_reason"] = "fixture — out of scope"

    fixture = tmp_path / "b99_deprecated.jsonl"
    fixture.write_text(json.dumps(deprecated) + "\n")

    result = _invoke(
        runner,
        "--file",
        str(fixture),
        "--inventory",
        str(REAL_INVENTORY),
    )
    assert result.exit_code == 0, result.stdout
    assert "deprecated" in result.stdout.lower()


def test_validator_rejects_inline_citation_hallucination(
    tmp_path: Path, runner: CliRunner
) -> None:
    """Bogus 'CCoP 2.0 §9.9.9' in expected_response must hard-fail."""
    bad = _valid_v2_row("B99-003", "B99", ["5.3.1"])
    bad["ground_truth"]["expected_response"] = (
        "According to CCoP 2.0 §5.3.1 and CCoP 2.0 §9.9.9, the operator must..."
    )
    fixture = tmp_path / "b99_bad_inline.jsonl"
    fixture.write_text(json.dumps(bad) + "\n")

    result = _invoke(
        runner,
        "--file",
        str(fixture),
        "--inventory",
        str(REAL_INVENTORY),
    )
    assert result.exit_code != 0
    assert "9.9.9" in result.stdout
