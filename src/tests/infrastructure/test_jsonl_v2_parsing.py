"""Tests for v2 JSONL test case parsing."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from domain.entities.test_case import TestCase
from infrastructure.adapters.repositories.jsonl_test_case_repository import (
    JSONLTestCaseRepository,
)


V2_TEST_CASE = {
    "test_id": "B3-001",
    "version": "2.0",
    "benchmark_id": "B3",
    "input": {
        "question": "Your organization uses shared admin accounts with session logging for CII SCADA systems. Does this comply with CCoP 2.0?",
        "scenario_sector": "energy",
        "scenario_role": "risk_manager",
    },
    "ground_truth": {
        "expected_label": "non-compliant",
        "expected_response": "Shared admin accounts do not comply with CCoP 2.0 access control requirements. Clause 5.3.1(c) mandates individual accountability for privileged access to CII systems.",
        "key_facts": [
            {
                "fact": "Clause 5.3.1(c) requires individual accountability",
                "source": "CCoP 2.0 Section 5.3.1(c)",
                "tier": "critical",
            },
            {
                "fact": "Shared accounts prevent attribution of actions",
                "source": "Regulatory interpretation",
                "tier": "critical",
            },
        ],
        "reasoning_chain": [
            "Identify privileged access scenario",
            "Recall individual accountability requirement",
            "Conclude non-compliance",
        ],
        "acceptable_variations": [
            "May recommend PAM tooling",
        ],
    },
    "fail_conditions": {
        "forbidden_claims": ["Shared accounts satisfy CCoP requirements"],
        "hallucination_patterns": ["Citing non-existent clauses"],
    },
    "metadata": {
        "section": "Section 5: Protection",
        "clause_reference": ["5.3.1"],
        "domain": "OT",
        "difficulty": "high",
        "test_category": "negative",
        "created_date": "2026-04-01",
        "reviewer": None,
    },
}


@pytest.fixture
def v2_jsonl_dir(tmp_path: Path) -> Path:
    """Create a temp dir with a v2 JSONL file."""
    filepath = tmp_path / "b03_conditional_compliance_reasoning.jsonl"
    filepath.write_text(json.dumps(V2_TEST_CASE) + "\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def mock_logger() -> MagicMock:
    return MagicMock()


class TestV2Parsing:
    """Test that the repository correctly parses v2 nested format."""

    @pytest.mark.asyncio
    async def test_parses_v2_test_case(
        self, v2_jsonl_dir: Path, mock_logger: MagicMock
    ) -> None:
        repo = JSONLTestCaseRepository(v2_jsonl_dir, mock_logger)
        cases = await repo.load_all()

        assert len(cases) == 1
        case = cases[0]
        assert case.test_id == "B3-001"
        assert case.question == V2_TEST_CASE["input"]["question"]
        assert case.expected_response == V2_TEST_CASE["ground_truth"]["expected_response"]
        assert case.expected_label == "non-compliant"

    @pytest.mark.asyncio
    async def test_parses_v2_key_facts_as_strings(
        self, v2_jsonl_dir: Path, mock_logger: MagicMock
    ) -> None:
        """key_facts property returns list[str] for backward compatibility with scorers."""
        repo = JSONLTestCaseRepository(v2_jsonl_dir, mock_logger)
        cases = await repo.load_all()
        case = cases[0]

        # Scorers expect list[str], not list[dict]
        assert isinstance(case.key_facts[0], str)
        assert "Clause 5.3.1(c) requires individual accountability" in case.key_facts[0]

    @pytest.mark.asyncio
    async def test_parses_v2_forbidden_claims(
        self, v2_jsonl_dir: Path, mock_logger: MagicMock
    ) -> None:
        repo = JSONLTestCaseRepository(v2_jsonl_dir, mock_logger)
        cases = await repo.load_all()
        case = cases[0]

        assert "Shared accounts satisfy CCoP requirements" in case.forbidden_claims

    @pytest.mark.asyncio
    async def test_parses_v2_metadata(
        self, v2_jsonl_dir: Path, mock_logger: MagicMock
    ) -> None:
        repo = JSONLTestCaseRepository(v2_jsonl_dir, mock_logger)
        cases = await repo.load_all()
        case = cases[0]

        assert case.domain == "OT"
        assert case.metadata.get("scenario_sector") == "energy"
        assert case.metadata.get("test_category") == "negative"
