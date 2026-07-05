"""
Policy Graph Stage 1 -- CU classification + minting tests (Phase 11, D-03/D-07
corrected).

`TestCUClassificationUnit` / `TestBuildCUUnitsUnit` cover the pure
classification + mint-payload-building logic against a FAKE gateway -- no
Neo4j required, runs under `pytest -m "not integration"` (fast).

`TestCUClassifierIntegration` requires a live local Neo4j with the 11-01/
11-02 source layer already seeded (mirrors `test_clause_source_annotator.py`'s
precedent) -- the mandatory E2E slice for this task. Uses the FAKE gateway
too (no real Opus calls needed: every seeded clause already carries a
recognized `function_type`, so the warm-start path fires for 100% of the
corpus and the LLM path is never exercised in this test).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import neo4j
import pytest

from domain.entities.model_response import ModelResponse
from infrastructure.config.settings import get_settings
from rag.graph.ontology.cu_classifier import (
    DEFAULT_CU_TYPE,
    FUNCTION_TYPE_TO_CU_TYPE,
    OBLIGATION_CU_TYPES,
    VALID_CU_TYPES,
    CUClassifier,
    CUMintStats,
    _build_cu_units,
    _classify_cu_types,
    _split_classification_output,
)


@dataclass
class FakeGateway:
    """Fake `IModelGateway` -- returns a scripted response, never touches a real subprocess."""

    scripted_content: str = "premise"
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


def _ccop_clause(clause_id="5.3.1", function_type=None, text="Some verbatim clause text.") -> dict:
    return {
        "clause_id": clause_id,
        "source_doc": "CCoP 2.0",
        "citation_id": f"CCoP-{clause_id}",
        "function_type": function_type,
        "text": text,
    }


class TestSplitClassificationOutputUnit:
    def test_single_value_passthrough(self):
        assert _split_classification_output("actor-CU") == ["actor-CU"]

    def test_comma_separated_multi_value(self):
        assert _split_classification_output("meta-CU, actor-CU") == ["meta-CU", "actor-CU"]

    def test_newline_and_semicolon_separators(self):
        assert _split_classification_output("premise;\nactor-CU") == ["premise", "actor-CU"]

    def test_strips_quotes_and_punctuation(self):
        assert _split_classification_output('"actor-CU".') == ["actor-CU"]

    def test_empty_input_yields_empty_list(self):
        assert _split_classification_output("") == []
        assert _split_classification_output(None) == []


class TestClassifyCUTypesUnit:
    """Pure classification logic against a fake gateway -- no Neo4j."""

    @pytest.mark.asyncio
    async def test_warm_start_overrides_the_llm_definition_clause(self):
        clause = _ccop_clause(function_type="DefinitionClause")
        gateway = FakeGateway(scripted_content="actor-CU")  # would be wrong if called
        types = await _classify_cu_types(clause, gateway, get_settings())
        assert types == ["premise"]
        assert gateway.calls == []  # warm-start -- LLM never invoked

    @pytest.mark.asyncio
    async def test_warm_start_overrides_the_llm_scope_clause(self):
        clause = _ccop_clause(function_type="ScopeClause")
        gateway = FakeGateway(scripted_content="premise")
        types = await _classify_cu_types(clause, gateway, get_settings())
        assert types == ["meta-CU"]
        assert gateway.calls == []

    @pytest.mark.asyncio
    async def test_warm_start_overrides_the_llm_control_clause(self):
        clause = _ccop_clause(function_type="ControlClause")
        gateway = FakeGateway(scripted_content="premise")
        types = await _classify_cu_types(clause, gateway, get_settings())
        assert types == ["actor-CU"]
        assert gateway.calls == []

    @pytest.mark.asyncio
    async def test_llm_path_fires_when_function_type_missing(self):
        clause = _ccop_clause(function_type=None)
        gateway = FakeGateway(scripted_content="actor-CU")
        types = await _classify_cu_types(clause, gateway, get_settings())
        assert types == ["actor-CU"]
        assert len(gateway.calls) == 1
        assert gateway.calls[0]["model_name"] == get_settings().cu_extraction_model

    @pytest.mark.asyncio
    async def test_llm_path_fires_when_function_type_unrecognized(self):
        clause = _ccop_clause(function_type="SomeUnrecognizedTag")
        gateway = FakeGateway(scripted_content="meta-CU")
        types = await _classify_cu_types(clause, gateway, get_settings())
        assert types == ["meta-CU"]
        assert len(gateway.calls) == 1

    @pytest.mark.asyncio
    async def test_malformed_llm_output_degrades_to_default(self):
        clause = _ccop_clause(function_type=None)
        gateway = FakeGateway(scripted_content="banana")
        types = await _classify_cu_types(clause, gateway, get_settings())
        assert types == [DEFAULT_CU_TYPE]

    @pytest.mark.asyncio
    async def test_gateway_exception_degrades_to_default_never_raises(self):
        clause = _ccop_clause(function_type=None)
        gateway = RaisingGateway()
        types = await _classify_cu_types(clause, gateway, get_settings())
        assert types == [DEFAULT_CU_TYPE]

    @pytest.mark.asyncio
    async def test_multi_obligation_clause_spawns_multiple_types(self):
        clause = _ccop_clause(function_type=None)
        gateway = FakeGateway(scripted_content="meta-CU, actor-CU")
        types = await _classify_cu_types(clause, gateway, get_settings())
        assert types == ["meta-CU", "actor-CU"]
        assert all(t in VALID_CU_TYPES for t in types)

    @pytest.mark.asyncio
    async def test_multi_value_response_drops_invalid_tokens_keeps_valid(self):
        clause = _ccop_clause(function_type=None)
        gateway = FakeGateway(scripted_content="actor-CU, nonsense-label")
        types = await _classify_cu_types(clause, gateway, get_settings())
        assert types == ["actor-CU"]


class TestBuildCUUnitsUnit:
    """Pure mint-payload-building logic -- no Neo4j."""

    def test_premise_classified_source_yields_one_premise_cu_no_obligation(self):
        clause = _ccop_clause(clause_id="1.2", function_type="DefinitionClause")
        units = _build_cu_units(clause, ["premise"])
        assert len(units) == 1
        assert units[0]["cu_type"] == "premise"
        assert units[0]["cu_type"] not in OBLIGATION_CU_TYPES

    def test_single_cu_reuses_bare_citation_id(self):
        clause = _ccop_clause(clause_id="5.3.1")
        units = _build_cu_units(clause, ["actor-CU"])
        assert units[0]["cu_id"] == "CCoP-5.3.1"

    def test_multi_obligation_source_spawns_more_than_one_cu(self):
        clause = _ccop_clause(clause_id="5.7.2")
        units = _build_cu_units(clause, ["meta-CU", "actor-CU"])
        assert len(units) == 2
        assert {u["cu_type"] for u in units} == {"meta-CU", "actor-CU"}
        # Distinct MERGE keys -- ordinal-suffixed, not colliding.
        cu_ids = [u["cu_id"] for u in units]
        assert cu_ids == ["CCoP-5.7.2#1", "CCoP-5.7.2#2"]
        assert len(set(cu_ids)) == 2

    def test_every_unit_carries_clause_link_fields(self):
        clause = _ccop_clause(clause_id="5.3.1")
        units = _build_cu_units(clause, ["actor-CU"])
        assert units[0]["clause_id"] == "5.3.1"
        assert units[0]["source_doc"] == "CCoP 2.0"


class TestCUMintStatsUnit:
    def test_defaults_are_zero(self):
        stats = CUMintStats()
        assert stats.actor_cu_count == 0
        assert stats.meta_cu_count == 0
        assert stats.premise_count == 0
        assert stats.cu_without_source_text_count == 0
        assert stats.cu_without_source_link_count == 0


@pytest.fixture(scope="module")
def _neo4j_driver():
    settings = get_settings()
    driver = neo4j.GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    try:
        driver.verify_connectivity()
    except Exception:
        pytest.skip("Live Neo4j not reachable — skipping CUClassifier integration test")
    yield driver
    driver.close()


@pytest.mark.integration
class TestCUClassifierIntegration:
    """
    Live-Neo4j E2E slice: classify + mint against the REAL 11-01/11-02
    source layer (883 seeded, annotated, text-aligned :Clause nodes).
    Uses a FAKE gateway (deterministic warm-start covers ~100% of the
    corpus per D-03/model_directive -- no real Opus calls needed here;
    the real-Opus proof lives in the Stage-2 4-tuple extractor slice).
    """

    def test_classify_and_mint_produces_emergent_stats_and_hard_links(self, _neo4j_driver):
        settings = get_settings()
        gateway = FakeGateway(scripted_content="premise")
        classifier = CUClassifier(settings=settings, driver=_neo4j_driver, gateway=gateway)

        import asyncio

        stats = asyncio.get_event_loop().run_until_complete(classifier.classify_and_mint())

        assert stats.clauses_considered > 0
        # Emergent — no reconciliation against clause/operative-leaf counts.
        total_minted = stats.actor_cu_count + stats.meta_cu_count + stats.premise_count
        assert total_minted > 0
        assert stats.cu_without_source_text_count == 0
        assert stats.cu_without_source_link_count == 0

        with _neo4j_driver.session(database=settings.neo4j_database) as session:
            record = session.run(
                "MATCH (cu:ComplianceUnit) WHERE NOT cu.cu_type IN $valid "
                "RETURN count(cu) AS c",
                valid=list(VALID_CU_TYPES),
            ).single()
            assert record["c"] == 0
