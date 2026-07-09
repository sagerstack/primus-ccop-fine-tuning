"""
Policy Graph Stage 3 -- REFERS_TO linker tests (Phase 11, 11-05 / D-05).

Pure explicit-pair + boundary-matcher logic and the degrade-safe implicit half
against fakes -- no Neo4j. Runs under `pytest -m "not integration"`.
"""

from __future__ import annotations

import pytest

from infrastructure.config.settings import get_settings
from rag.graph.ontology.refers_to_linker import (
    RefersToLinker,
    _reference_appears,
    _split_ref_tokens,
)


class _FakeDriver:
    def session(self, database=None):  # pragma: no cover - not used in these unit tests
        raise AssertionError("driver must not be used in pure unit tests")


class RaisingGateway:
    async def generate_response(self, prompt, model_name, **kwargs):
        raise RuntimeError("simulated LLM failure")


def _cu(cu_id, clause_id, text, doc="CCoP 2.0", cu_type="actor-CU"):
    return {"cu_id": cu_id, "source_doc": doc, "cu_type": cu_type, "clause_id": clause_id, "text": text}


class TestReferenceAppears:
    def test_explicit_reference_matches(self):
        assert _reference_appears("5.7.2", "obligations under clause 5.7.2 apply")

    def test_short_id_does_not_match_longer_dotted(self):
        # Finding 3: "5.3" must NOT match inside "5.3.10"
        assert _reference_appears("5.3", "see clause 5.3.10 for detail") is False

    def test_short_id_does_not_match_lettered_subitem(self):
        assert _reference_appears("5.3", "see 5.3(a)") is False

    def test_exact_dotted_id_matches(self):
        assert _reference_appears("5.3.10", "see clause 5.3.10 for detail")

    def test_not_matched_when_embedded_in_larger_number(self):
        assert _reference_appears("1", "as in 15.37") is False

    def test_lettered_subitem_id_matches_at_sentence_end(self):
        assert _reference_appears("5.7.2(a)", "per 5.7.2(a).")


class TestSplitRefTokens:
    def test_extracts_clause_ids(self):
        assert _split_ref_tokens("5.7.2, 3.2.1(a)") == ["5.7.2", "3.2.1(a)"]

    def test_none_yields_empty(self):
        assert _split_ref_tokens("NONE") == []
        assert _split_ref_tokens("") == []


class TestComputeExplicitPairs:
    def test_explicit_reference_links(self):
        cus = [
            _cu("CCoP-5.7.1", "5.7.1", "see Clause 5.7.2 for remote-connection controls"),
            _cu("CCoP-5.7.2", "5.7.2", "Remote connections shall be secured."),
        ]
        pairs = RefersToLinker._compute_explicit_pairs(cus)
        assert {"src_cu_id": "CCoP-5.7.1", "tgt_cu_id": "CCoP-5.7.2", "source_doc": "CCoP 2.0"} in pairs

    def test_short_id_does_not_over_link(self):
        cus = [
            _cu("CCoP-5.9.1", "5.9.1", "as required under clause 5.3.10"),
            _cu("CCoP-5.3", "5.3", "..."),
            _cu("CCoP-5.3.10", "5.3.10", "..."),
        ]
        pairs = RefersToLinker._compute_explicit_pairs(cus)
        tgt_ids = {p["tgt_cu_id"] for p in pairs if p["src_cu_id"] == "CCoP-5.9.1"}
        assert "CCoP-5.3.10" in tgt_ids
        assert "CCoP-5.3" not in tgt_ids  # Finding 3 guard

    def test_premise_source_not_linked(self):
        # REFERS_TO sources are obligation CUs only; a premise never emits edges.
        cus = [
            _cu("RtF-11.6", "11.6", "see 5.7.2 and 5.7.1", cu_type="premise"),
            _cu("CCoP-5.7.2", "5.7.2", "..."),
            _cu("CCoP-5.7.1", "5.7.1", "..."),
        ]
        pairs = RefersToLinker._compute_explicit_pairs(cus)
        assert all(p["src_cu_id"] != "RtF-11.6" for p in pairs)

    def test_self_reference_skipped(self):
        cus = [_cu("CCoP-5.7.1", "5.7.1", "this clause 5.7.1 is self-referential")]
        assert RefersToLinker._compute_explicit_pairs(cus) == []

    def test_cross_document_not_linked_by_bare_id(self):
        # within-doc only: a bare id in one doc must not link into another
        cus = [
            _cu("CCoP-11.1", "11.1", "see clause 11.2", doc="CCoP 2.0"),
            _cu("Act-11", "11", "...", doc="Cybersecurity Act 2018"),
            _cu("CCoP-11.2", "11.2", "...", doc="CCoP 2.0"),
        ]
        pairs = RefersToLinker._compute_explicit_pairs(cus)
        assert all(p["source_doc"] == "CCoP 2.0" for p in pairs)
        assert not any(p["tgt_cu_id"] == "Act-11" for p in pairs)


class TestImplicitDegrades:
    @pytest.mark.asyncio
    async def test_llm_failure_degrades_to_no_edges(self):
        linker = RefersToLinker(settings=get_settings(), driver=_FakeDriver(), gateway=RaisingGateway())
        cus = [_cu("CCoP-3.2.1", "3.2.1", "as set out in the preceding sub-clause")]
        pairs = await linker._compute_implicit_pairs(cus)
        assert pairs == []  # degrade cleanly, never raise

    @pytest.mark.asyncio
    async def test_no_gateway_yields_no_implicit(self):
        linker = RefersToLinker(settings=get_settings(), driver=_FakeDriver(), gateway=None)
        cus = [_cu("CCoP-3.2.1", "3.2.1", "as set out in the preceding sub-clause")]
        assert await linker._compute_implicit_pairs(cus) == []
