"""
Regression tests for verify_clause_completeness.py (Phase 11, D-19/D-20/D-25.3).

Two groups:
  - Synthetic-corpus unit tests (no live services) proving the gate fails
    non-zero when a clause body is absent, and passes when every entry
    resolves — including the item-letter and "section N" decomposition
    fallbacks discovered against the real corpus.
  - Integration tests against the REAL re-ingested corpus (live Qdrant/Neo4j,
    `@pytest.mark.integration`), spot-checking 5.3/5.4 resolve and that the
    committed clause_inventory.json (883 entries) is 100% resolved with
    correct 7-doc provenance.
"""

import json

import pytest

from infrastructure.config.settings import get_settings
from rag.ingestion.scripts.verify_clause_completeness import (
    DEFAULT_INVENTORY_PATH,
    _clause_resolves,
    check_completeness,
    check_provenance,
)


class _FakePoint:
    def __init__(self, payload):
        self.payload = payload


class _FakeQdrantClient:
    """
    Minimal fake matching the subset of `qdrant_client.QdrantClient` used by
    `_build_haystacks`: a single-page `scroll()` call returning every record
    with `next_page_offset=None` — sufficient for small synthetic fixtures
    (no live Qdrant dependency).
    """

    def __init__(self, records):
        self._records = records

    def scroll(self, collection_name, limit, offset, with_payload, with_vectors):
        return self._records, None


def _records(entries):
    return [
        _FakePoint(payload={"document_source": doc, "text": text})
        for doc, text in entries
    ]


# ---------------------------------------------------------------------------
# _clause_resolves: direct match + decomposition fallbacks
# ---------------------------------------------------------------------------


class TestClauseResolvesDecomposition:
    def test_direct_boundary_aware_match(self):
        assert _clause_resolves("5.3", "## 5.3 privileged access management")

    def test_boundary_aware_match_rejects_substring_collision(self):
        """A short numeric clause_id ("1") must not spuriously match inside
        a longer one ("15.37") — the exact case `_clause_id_appears`'s
        docstring documents (`rag/graph/inspect/metrics.py`)."""
        assert not _clause_resolves("1", "see clause 15.37 for details")

    def test_item_letter_decomposition_resolves(self):
        hay = "10.2.5 the ciio shall:\n- (a) do the thing"
        assert _clause_resolves("10.2.5(a)", hay)

    def test_item_letter_decomposition_fails_without_parent(self):
        hay = "- (a) do the thing"  # parent "10.2.5" never appears
        assert not _clause_resolves("10.2.5(a)", hay)

    def test_item_letter_decomposition_fails_without_letter_marker(self):
        hay = "10.2.5 the ciio shall do various things"  # no "(a)" marker
        assert not _clause_resolves("10.2.5(a)", hay)

    def test_section_prefix_decomposition_resolves(self):
        hay = "14.-(1) the commissioner may direct the owner"
        assert _clause_resolves("section 14", hay)

    def test_unresolved_when_absent_entirely(self):
        assert not _clause_resolves("99.99", "nothing relevant in this haystack")


# ---------------------------------------------------------------------------
# check_completeness: synthetic corpus (fail-loud + pass cases)
# ---------------------------------------------------------------------------


class TestCheckCompletenessSyntheticCorpus:
    def test_gate_fails_non_zero_on_missing_clause(self, tmp_path):
        """The core D-19 fail-loud requirement: a missing clause body must
        surface as a non-conforming report, naming the unresolved id."""
        inventory_path = tmp_path / "clause_inventory.json"
        inventory_path.write_text(
            json.dumps(
                {
                    "entries": [
                        {"clause_id": "5.3", "source_doc": "TestDoc"},
                        {"clause_id": "5.4", "source_doc": "TestDoc"},
                    ]
                }
            )
        )
        client = _FakeQdrantClient(
            _records([("TestDoc", "5.3 some real verbatim body text")])
            # 5.4 is deliberately never indexed
        )

        report = check_completeness(
            inventory_path=inventory_path, client=client, collection_name="fake"
        )

        assert report.conforms is False
        assert report.total == 2
        assert report.resolved == 1
        assert len(report.unresolved) == 1
        assert report.unresolved[0].clause_id == "5.4"
        assert report.unresolved[0].source_doc == "TestDoc"

    def test_gate_passes_when_every_entry_resolves(self, tmp_path):
        inventory_path = tmp_path / "clause_inventory.json"
        inventory_path.write_text(
            json.dumps(
                {
                    "entries": [
                        {"clause_id": "5.3", "source_doc": "TestDoc"},
                        {"clause_id": "5.3.1", "source_doc": "TestDoc"},
                        {"clause_id": "5.3.1(a)", "source_doc": "TestDoc"},
                    ]
                }
            )
        )
        client = _FakeQdrantClient(
            _records(
                [
                    ("TestDoc", "5.3 privileged access management"),
                    (
                        "TestDoc",
                        "5.3.1 with respect to privileged accounts, the ciio shall:",
                    ),
                    ("TestDoc", "(a) ensure that privileged access is granted"),
                ]
            )
        )

        report = check_completeness(
            inventory_path=inventory_path, client=client, collection_name="fake"
        )

        assert report.conforms is True
        assert report.unresolved == []

    def test_toc_section_parity_skipped_for_non_ccop_fixture(self, tmp_path):
        """A synthetic fixture with no CCoP 2.0 entries must not spuriously
        fail on the (irrelevant) CCoP 2.0 TOC section-parity assertion."""
        inventory_path = tmp_path / "clause_inventory.json"
        inventory_path.write_text(
            json.dumps({"entries": [{"clause_id": "1", "source_doc": "TestDoc"}]})
        )
        client = _FakeQdrantClient(_records([("TestDoc", "1 some body text")]))

        report = check_completeness(
            inventory_path=inventory_path, client=client, collection_name="fake"
        )

        assert report.conforms is True
        assert report.toc_section_parity.get("skipped") is True


# ---------------------------------------------------------------------------
# Integration: the REAL re-ingested corpus (live Qdrant/Neo4j)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestRealCorpusCompleteness:
    """
    Runs against the live, re-ingested `ccop_clauses_hybrid` Qdrant
    collection — this IS the Wave-0 BLOCKING acceptance gate (D-19): every
    one of the committed clause_inventory.json's 883 entries must resolve.
    """

    def test_committed_inventory_fully_resolves(self):
        settings = get_settings()
        if not settings.qdrant_url:
            pytest.skip("CCOP_QDRANT_URL not configured — skipping live gate check")

        report = check_completeness(inventory_path=DEFAULT_INVENTORY_PATH)

        assert report.conforms, (
            f"{len(report.unresolved)}/{report.total} clause ids unresolved: "
            f"{[u.clause_id for u in report.unresolved[:20]]}"
        )

    def test_5_3_and_5_4_spot_check_resolve(self):
        settings = get_settings()
        if not settings.qdrant_url:
            pytest.skip("CCOP_QDRANT_URL not configured — skipping live gate check")

        report = check_completeness(inventory_path=DEFAULT_INVENTORY_PATH)

        unresolved_ids = {u.clause_id for u in report.unresolved}
        assert "5.3" not in unresolved_ids
        assert "5.4" not in unresolved_ids


@pytest.mark.integration
class TestRealCorpusProvenance:
    """D-20 guard against the live Neo4j graph."""

    def test_seven_distinct_docs_zero_document_txt(self):
        settings = get_settings()
        if not settings.neo4j_uri:
            pytest.skip("CCOP_NEO4J_URI not configured — skipping live provenance check")

        report = check_provenance()

        assert report.document_txt_count == 0
        assert len(report.distinct_source_docs) == 7
