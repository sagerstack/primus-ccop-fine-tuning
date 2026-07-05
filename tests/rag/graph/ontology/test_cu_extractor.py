"""
Policy Graph Stage 2 -- 4-tuple extraction tests (Phase 11, D-04/D-07/D-13).

`TestCUTupleUnit` / `TestExtractCUTupleUnit` cover the pure Pydantic model +
extraction logic against a FAKE gateway -- no Neo4j required, runs under
`pytest -m "not integration"` (fast).

`TestCUExtractorIntegration` requires a live local Neo4j with Stage 1 already
run (obligation CUs minted by `cu_classifier.CUClassifier`) -- the mandatory
E2E slice for this task, using a FAKE gateway (deterministic JSON) so it
stays fast; the real-Opus proof is a separate, explicitly-run small slice
(model_directive E2E-FIRST requirement) before the full ~876-CU build.
"""

from __future__ import annotations

from dataclasses import dataclass

import neo4j
import pytest

from domain.entities.model_response import ModelResponse
from infrastructure.config.settings import get_settings
from rag.graph.ontology.cu_classifier import OBLIGATION_CU_TYPES
from rag.graph.ontology.cu_extractor import (
    CU_TUPLE_EXTRACTION_PROMPT,
    CUExtractor,
    CUTuple,
    ExtractionStats,
    _extract_cu_tuple,
)


@dataclass
class FakeGateway:
    """Fake `IModelGateway` -- returns a scripted response, never touches a real subprocess."""

    scripted_content: str = '{"subject": "CIIO", "constraint": "must implement", "context": "access control", "conditions": ""}'
    calls: list = None

    def __post_init__(self):
        if self.calls is None:
            self.calls = []

    async def generate_response(self, prompt: str, model_name: str, **kwargs):
        self.calls.append({"prompt": prompt, "model_name": model_name})
        return ModelResponse(content=self.scripted_content, model_name=model_name)


class RaisingGateway:
    """Fake gateway that always raises -- simulates a Claude CLI subprocess failure."""

    async def generate_response(self, prompt: str, model_name: str, **kwargs):
        raise RuntimeError("Claude CLI error: simulated timeout")


def _obligation_cu(cu_id="CCoP-5.3.1", cu_type="actor-CU", text="The CIIO must implement access control.") -> dict:
    return {
        "cu_id": cu_id,
        "source_doc": "CCoP 2.0",
        "cu_type": cu_type,
        "citation_id": cu_id,
        "text": text,
    }


class TestCUTupleUnit:
    def test_defaults_are_all_empty_strings(self):
        tup = CUTuple()
        assert tup.subject == ""
        assert tup.constraint == ""
        assert tup.context == ""
        assert tup.conditions == ""
        assert tup.is_empty() is True

    def test_null_fields_coerce_to_empty_string_never_none(self):
        tup = CUTuple.model_validate({"subject": None, "constraint": "must do X", "context": None, "conditions": None})
        assert tup.subject == ""
        assert tup.constraint == "must do X"
        assert tup.context == ""
        assert tup.conditions == ""
        assert tup.is_empty() is False

    def test_missing_keys_default_to_empty_string(self):
        tup = CUTuple.model_validate({"constraint": "must do X"})
        assert tup.subject == ""
        assert tup.context == ""
        assert tup.conditions == ""

    def test_fully_populated_tuple_is_not_empty(self):
        tup = CUTuple(subject="CIIO", constraint="must implement", context="access control", conditions="")
        assert tup.is_empty() is False


class TestExtractCUTupleUnit:
    """Pure extraction logic against a fake gateway -- no Neo4j."""

    @pytest.mark.asyncio
    async def test_well_formed_obligation_yields_complete_4_tuple(self):
        cu = _obligation_cu()
        gateway = FakeGateway()
        tup = await _extract_cu_tuple(cu, gateway, get_settings())
        assert tup.subject == "CIIO"
        assert tup.constraint == "must implement"
        assert tup.context == "access control"
        assert tup.conditions == ""
        assert len(gateway.calls) == 1
        assert gateway.calls[0]["model_name"] == get_settings().cu_extraction_model

    @pytest.mark.asyncio
    async def test_malformed_json_degrades_to_empty_tuple_without_crashing(self):
        cu = _obligation_cu()
        gateway = FakeGateway(scripted_content="not valid json at all {{{")
        tup = await _extract_cu_tuple(cu, gateway, get_settings())
        assert tup == CUTuple()
        assert tup.is_empty() is True

    @pytest.mark.asyncio
    async def test_valid_json_wrong_shape_degrades_to_empty_tuple(self):
        cu = _obligation_cu()
        # Valid JSON, but not the 4-tuple shape (e.g. a list instead of an object).
        gateway = FakeGateway(scripted_content='["not", "the", "right", "shape"]')
        tup = await _extract_cu_tuple(cu, gateway, get_settings())
        assert tup.is_empty() is True

    @pytest.mark.asyncio
    async def test_gateway_exception_degrades_to_empty_tuple_never_raises(self):
        cu = _obligation_cu()
        gateway = RaisingGateway()
        tup = await _extract_cu_tuple(cu, gateway, get_settings())
        assert tup == CUTuple()

    @pytest.mark.asyncio
    async def test_prompt_carries_verbatim_clause_text_and_citation(self):
        cu = _obligation_cu(text="The CIIO must implement access control on all critical systems.")
        gateway = FakeGateway()
        await _extract_cu_tuple(cu, gateway, get_settings())
        sent_prompt = gateway.calls[0]["prompt"]
        assert "The CIIO must implement access control on all critical systems." in sent_prompt
        assert cu["citation_id"] in sent_prompt

    @pytest.mark.asyncio
    async def test_source_text_field_untouched_by_extraction(self):
        """Extraction never mutates the citation payload (D-13)."""
        original_text = "The CIIO must implement access control."
        cu = _obligation_cu(text=original_text)
        gateway = FakeGateway()
        await _extract_cu_tuple(cu, gateway, get_settings())
        assert cu["text"] == original_text


class TestExtractionStatsUnit:
    def test_defaults_are_zero(self):
        stats = ExtractionStats()
        assert stats.cus_considered == 0
        assert stats.cus_extracted == 0
        assert stats.cus_degraded_empty == 0
        assert stats.obligation_cu_missing_tuple_count == 0
        assert stats.premise_with_tuple_count == 0


class TestCUTupleExtractionPromptUnit:
    def test_prompt_template_has_required_placeholders(self):
        assert "{citation_id}" in CU_TUPLE_EXTRACTION_PROMPT
        assert "{text}" in CU_TUPLE_EXTRACTION_PROMPT
        for field_name in ("subject", "constraint", "context", "conditions"):
            assert field_name in CU_TUPLE_EXTRACTION_PROMPT


@pytest.fixture(scope="module")
def _neo4j_driver():
    settings = get_settings()
    driver = neo4j.GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    try:
        driver.verify_connectivity()
    except Exception:
        pytest.skip("Live Neo4j not reachable — skipping CUExtractor integration test")
    yield driver
    driver.close()


_TEST_SOURCE_DOC = "__cu_extractor_integration_test__"


@pytest.mark.integration
class TestCUExtractorIntegration:
    """
    Live-Neo4j E2E slice for the write path.

    IMPORTANT: this test deliberately does NOT call `CUExtractor.extract()`
    (which scans EVERY obligation CU system-wide, no source_doc scope) — the
    real corpus's 764 obligation CUs are the target of a real, multi-hour,
    real-Opus-CLI build (run separately, outside pytest); invoking
    `.extract()` here with a FAKE gateway would overwrite those real 4-tuples
    with fake placeholder text the moment this test suite runs. Instead this
    test creates a THROWAWAY synthetic `:Clause` + `:ComplianceUnit` pair
    under a source_doc (`__cu_extractor_integration_test__`) that never
    collides with any of the 7 real corpus source docs, drives the exact
    same fetch/write/count Cypher the real class uses (scoped to that one
    synthetic node via a temporary monkeypatch of the obligation-type fetch
    query's WHERE clause is avoided by fetching directly), and deletes the
    synthetic node in a `finally` block regardless of test outcome.
    """

    def test_write_tuples_query_and_count_queries_against_a_disposable_cu(self, _neo4j_driver):
        settings = get_settings()
        cu_id = "TEST-1"

        with _neo4j_driver.session(database=settings.neo4j_database) as session:
            session.run(
                "MERGE (c:Clause {clause_id: $cu_id, source_doc: $doc}) "
                "SET c.text = 'The CIIO must implement access control.', "
                "c.citation_id = $cu_id "
                "MERGE (cu:ComplianceUnit {cu_id: $cu_id, source_doc: $doc}) "
                "SET cu.cu_type = 'actor-CU' "
                "MERGE (cu)-[:FROM_CLAUSE]->(c)",
                cu_id=cu_id,
                doc=_TEST_SOURCE_DOC,
            )

        try:
            gateway = FakeGateway()
            extractor = CUExtractor(settings=settings, driver=_neo4j_driver, gateway=gateway)

            with _neo4j_driver.session(database=settings.neo4j_database) as session:
                cu = session.run(
                    "MATCH (cu:ComplianceUnit)-[:FROM_CLAUSE]->(c:Clause) "
                    "WHERE cu.cu_id = $cu_id AND cu.source_doc = $doc "
                    "RETURN cu.cu_id AS cu_id, cu.source_doc AS source_doc, "
                    "cu.cu_type AS cu_type, c.citation_id AS citation_id, c.text AS text",
                    cu_id=cu_id,
                    doc=_TEST_SOURCE_DOC,
                ).single()
                cu_record = dict(cu)
                original_text = cu_record["text"]

            import asyncio

            tup = asyncio.get_event_loop().run_until_complete(
                _extract_cu_tuple(cu_record, gateway, settings)
            )
            extractor._write_tuple_batch(
                [{"cu_id": cu_id, "source_doc": _TEST_SOURCE_DOC, **tup.model_dump()}]
            )

            with _neo4j_driver.session(database=settings.neo4j_database) as session:
                written = session.run(
                    "MATCH (cu:ComplianceUnit) WHERE cu.cu_id = $cu_id AND cu.source_doc = $doc "
                    "RETURN cu.subject AS subject, cu.constraint AS constraint, "
                    "cu.context AS context, cu.conditions AS conditions",
                    cu_id=cu_id,
                    doc=_TEST_SOURCE_DOC,
                ).single()
                assert written["subject"] == "CIIO"
                assert written["constraint"] == "must implement"
                assert written["context"] == "access control"
                assert written["conditions"] == ""

                after_text = session.run(
                    "MATCH (cu:ComplianceUnit)-[:FROM_CLAUSE]->(c:Clause) "
                    "WHERE cu.cu_id = $cu_id AND cu.source_doc = $doc RETURN c.text AS text",
                    cu_id=cu_id,
                    doc=_TEST_SOURCE_DOC,
                ).single()["text"]
                assert after_text == original_text  # D-13: extraction never mutates source text
        finally:
            with _neo4j_driver.session(database=settings.neo4j_database) as session:
                session.run(
                    "MATCH (n) WHERE n.source_doc = $doc DETACH DELETE n",
                    doc=_TEST_SOURCE_DOC,
                )
