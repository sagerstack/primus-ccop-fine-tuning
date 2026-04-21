"""
Tests for the committed CCoP clause inventory fixture.

These tests load the pre-built clause_inventory.json fixture and assert
structural and content invariants. No Docling re-parse is required —
the fixture is committed and treated as ground truth.

Four invariants:
  1. Known-real clause IDs are present (5.3.1, 5.3.1(c), 5.2.1 in CCoP 2.0)
  2. Known-hallucinated clause IDs are absent (5.1.5 — bug #8: section 5.1 ends at 5.1.4)
  3. Inventory covers all 7 source documents (7 parsed; Cybersecurity Act 2018 yields 0 CCoP-style IDs)
  4. Entry schema is minimal: exactly {clause_id, source_doc} — no drift
"""

import json
from pathlib import Path

import pytest

# Fixture path — committed at src/rag/ingestion/fixtures/clause_inventory.json
# Test file lives at src/tests/rag/ingestion/scripts/ so we navigate:
#   .parent (scripts/) -> .parent (ingestion/) -> .parent (rag/) -> .parent (tests/) -> .parent (src/)
_FIXTURE_PATH = (
    Path(__file__).parent.parent.parent.parent.parent
    / "rag"
    / "ingestion"
    / "fixtures"
    / "clause_inventory.json"
)


@pytest.fixture(scope="module")
def inventory() -> dict:
    """Load the committed clause inventory fixture once per test module."""
    assert _FIXTURE_PATH.exists(), (
        f"clause_inventory.json not found at {_FIXTURE_PATH}. "
        "Run: cd src && poetry run python -m rag.ingestion.scripts.build_clause_inventory "
        "--ccop-dir ../ccop-official"
    )
    with open(_FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def entry_set(inventory: dict) -> set[tuple[str, str]]:
    """Return inventory entries as a set of (clause_id, source_doc) tuples for O(1) lookup."""
    return {(e["clause_id"], e["source_doc"]) for e in inventory["entries"]}


class TestInventoryContainsKnownRealClauses:
    """Known-real CCoP 2.0 clause IDs must appear in the inventory."""

    def test_5_3_1_present(self, entry_set: set) -> None:
        assert ("5.3.1", "CCoP 2.0") in entry_set, (
            "Clause 5.3.1 (Privileged Access Management requirements) missing from inventory"
        )

    def test_5_3_1_c_present(self, entry_set: set) -> None:
        assert ("5.3.1(c)", "CCoP 2.0") in entry_set, (
            "Clause 5.3.1(c) (MFA for privileged access) missing from inventory. "
            "Item-letter IDs are synthesised from '- (c) ...' list items in Docling markdown."
        )

    def test_5_2_1_present(self, entry_set: set) -> None:
        assert ("5.2.1", "CCoP 2.0") in entry_set, (
            "Clause 5.2.1 (Account Management) missing from inventory"
        )


class TestInventoryExcludesKnownHallucinatedClauses:
    """
    Clause IDs fabricated by LLM-generated ground truth must NOT appear.

    Bug #8: section 5.1 (Access Control) ends at 5.1.4 (session termination).
    Clause 5.1.5 does not exist. Any test case citing 5.1.5 is hallucinated.
    """

    def test_5_1_5_absent(self, entry_set: set) -> None:
        assert ("5.1.5", "CCoP 2.0") not in entry_set, (
            "Hallucinated clause 5.1.5 found in inventory. "
            "Section 5.1 ends at 5.1.4 — this is a fabricated citation (bug #8)."
        )


class TestInventoryCoversAllDocuments:
    """Inventory must span all parsed source documents."""

    # The extraction pipeline parses 7 documents. Cybersecurity Act 2018
    # yields 0 CCoP-format clause IDs (different numbering scheme) but
    # IS listed in source_docs. Total distinct source_docs >= 7.
    EXPECTED_MIN_DOCS = 7
    EXPECTED_CCOP_DOC = "CCoP 2.0"

    def test_source_docs_cardinality(self, inventory: dict) -> None:
        source_docs = set(inventory["source_docs"])
        assert len(source_docs) >= self.EXPECTED_MIN_DOCS, (
            f"Expected >= {self.EXPECTED_MIN_DOCS} source documents, "
            f"found {len(source_docs)}: {sorted(source_docs)}"
        )

    def test_ccop_2_0_is_included(self, inventory: dict) -> None:
        assert self.EXPECTED_CCOP_DOC in inventory["source_docs"], (
            f"'{self.EXPECTED_CCOP_DOC}' must be in source_docs"
        )

    def test_entries_span_multiple_documents(self, inventory: dict) -> None:
        docs_in_entries = {e["source_doc"] for e in inventory["entries"]}
        assert len(docs_in_entries) >= 2, (
            "Entries must span at least 2 source documents "
            "(Cybersecurity Act 2018 has 0 entries but other docs should contribute)"
        )


class TestInventorySchemaMinimal:
    """Every entry must have exactly two keys: clause_id and source_doc."""

    REQUIRED_KEYS = {"clause_id", "source_doc"}

    def test_every_entry_has_exactly_two_keys(self, inventory: dict) -> None:
        bad_entries = [
            e for e in inventory["entries"]
            if set(e.keys()) != self.REQUIRED_KEYS
        ]
        assert not bad_entries, (
            f"{len(bad_entries)} entries have unexpected keys. "
            f"Expected exactly {self.REQUIRED_KEYS}. "
            f"First offender: {bad_entries[0] if bad_entries else None}"
        )

    def test_no_empty_clause_ids(self, inventory: dict) -> None:
        empty = [e for e in inventory["entries"] if not e.get("clause_id", "").strip()]
        assert not empty, f"{len(empty)} entries have empty clause_id"

    def test_no_empty_source_docs(self, inventory: dict) -> None:
        empty = [e for e in inventory["entries"] if not e.get("source_doc", "").strip()]
        assert not empty, f"{len(empty)} entries have empty source_doc"
