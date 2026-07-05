"""
Policy Graph Stage 1 -- CU classification + minting tests (Phase 11, 11-04b /
D-30/D-31/D-32/D-33).

Pure classification + mint-payload logic against a FAKE gateway -- no Neo4j,
no real Opus. Runs under `pytest -m "not integration"`. The live classify+mint
E2E (real Opus over the 883-clause backbone) is the 11-04b W4 regen run.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from domain.entities.model_response import ModelResponse
from infrastructure.config.settings import get_settings
from rag.graph.ontology.cu_candidate_gate import (
    ROUTE_FORCE_PREMISE_INTERPRETATION,
    ROUTE_LLM_CLASSIFY,
    Candidate,
)
from rag.graph.ontology.cu_classifier import (
    DEFAULT_MODALITY,
    OBLIGATION_CU_TYPES,
    VALID_CU_TYPES,
    _build_cu_units,
    _classify_candidate,
    _normalize_classification,
    _parse_classifications,
)


@dataclass
class FakeGateway:
    scripted_content: str = '[{"type":"premise","premise_kind":"definition"}]'
    calls: list = field(default_factory=list)

    async def generate_response(self, prompt: str, model_name: str, **kwargs):
        self.calls.append({"prompt": prompt, "model_name": model_name})
        return ModelResponse(content=self.scripted_content, model_name=model_name)


class RaisingGateway:
    async def generate_response(self, prompt: str, model_name: str, **kwargs):
        raise RuntimeError("Claude CLI error: simulated timeout")


def _candidate(clause_id="5.7.1", route=ROUTE_LLM_CLASSIFY, source_doc="CCoP 2.0", text="The CIIO shall ...", **kw):
    return Candidate(
        clause_id=clause_id,
        source_doc=source_doc,
        citation_id=f"CCoP-{clause_id}",
        text=text,
        route=route,
        function_type=kw.get("function_type", "ControlClause"),
        doc_class=kw.get("doc_class", "binding"),
    )


class TestParseClassifications:
    def test_valid_array(self):
        out = _parse_classifications('[{"type":"actor-CU","modality":"obligation"}]')
        assert out == [{"cu_type": "actor-CU", "modality": "obligation", "premise_kind": ""}]

    def test_single_object_normalized_to_list(self):
        out = _parse_classifications('{"type":"meta-CU"}')
        assert out == [{"cu_type": "meta-CU", "modality": "", "premise_kind": ""}]

    def test_permission_modality_kept_for_regulator_power(self):
        out = _parse_classifications('[{"type":"actor-CU","modality":"permission"}]')
        assert out[0]["modality"] == "permission"

    def test_actor_cu_missing_modality_defaults_to_obligation(self):
        out = _parse_classifications('[{"type":"actor-CU"}]')
        assert out[0]["modality"] == DEFAULT_MODALITY

    def test_premise_missing_kind_defaults_to_definition(self):
        out = _parse_classifications('[{"type":"premise"}]')
        assert out[0]["premise_kind"] == "definition"

    def test_invalid_type_dropped(self):
        out = _parse_classifications('[{"type":"banana"},{"type":"actor-CU","modality":"obligation"}]')
        assert out == [{"cu_type": "actor-CU", "modality": "obligation", "premise_kind": ""}]

    def test_malformed_json_returns_empty(self):
        assert _parse_classifications("not json at all") == []
        assert _parse_classifications("") == []

    def test_duplicate_classifications_deduped(self):
        out = _parse_classifications('[{"type":"premise"},{"type":"premise"},{"type":"premise"}]')
        assert out == [{"cu_type": "premise", "modality": "", "premise_kind": "definition"}]

    def test_prohibition_plus_duplicate_obligations_collapse(self):
        # A "shall not X unless (a)(b)(c)" over-split into prohibition + 3 identical obligations.
        raw = ('[{"type":"actor-CU","modality":"prohibition"},'
               '{"type":"actor-CU","modality":"obligation"},'
               '{"type":"actor-CU","modality":"obligation"},'
               '{"type":"actor-CU","modality":"obligation"}]')
        out = _parse_classifications(raw)
        assert out == [
            {"cu_type": "actor-CU", "modality": "prohibition", "premise_kind": ""},
            {"cu_type": "actor-CU", "modality": "obligation", "premise_kind": ""},
        ]

    def test_distinct_units_preserved(self):
        out = _parse_classifications('[{"type":"meta-CU"},{"type":"actor-CU","modality":"obligation"}]')
        assert len(out) == 2

    def test_meta_cu_carries_no_modality_or_premise_kind(self):
        out = _normalize_classification({"type": "meta-CU", "modality": "obligation"})
        assert out == {"cu_type": "meta-CU", "modality": "", "premise_kind": ""}


class TestClassifyCandidate:
    @pytest.mark.asyncio
    async def test_forced_route_skips_llm_and_mints_interpretation_premise(self):
        cand = _candidate(route=ROUTE_FORCE_PREMISE_INTERPRETATION, source_doc="CCoP Response to Feedback")
        gateway = FakeGateway(scripted_content='[{"type":"actor-CU"}]')  # would be wrong if called
        out = await _classify_candidate(cand, gateway, get_settings())
        assert out == [{"cu_type": "premise", "modality": "", "premise_kind": "interpretation"}]
        assert gateway.calls == []  # LLM never invoked for RtF

    @pytest.mark.asyncio
    async def test_llm_path_classifies_actor_cu(self):
        cand = _candidate()
        gateway = FakeGateway(scripted_content='[{"type":"actor-CU","modality":"obligation"}]')
        out = await _classify_candidate(cand, gateway, get_settings())
        assert out == [{"cu_type": "actor-CU", "modality": "obligation", "premise_kind": ""}]
        assert len(gateway.calls) == 1
        assert gateway.calls[0]["model_name"] == get_settings().cu_extraction_model

    @pytest.mark.asyncio
    async def test_regulator_power_classifies_as_permission(self):
        cand = _candidate(clause_id="1.6.1", text="the Commissioner may waive ...")
        gateway = FakeGateway(scripted_content='[{"type":"actor-CU","modality":"permission"}]')
        out = await _classify_candidate(cand, gateway, get_settings())
        assert out[0]["modality"] == "permission"

    @pytest.mark.asyncio
    async def test_multi_unit_response_spawns_multiple(self):
        cand = _candidate()
        gateway = FakeGateway(scripted_content='[{"type":"meta-CU"},{"type":"actor-CU","modality":"obligation"}]')
        out = await _classify_candidate(cand, gateway, get_settings())
        assert [c["cu_type"] for c in out] == ["meta-CU", "actor-CU"]

    @pytest.mark.asyncio
    async def test_malformed_output_degrades_to_premise_definition(self):
        cand = _candidate()
        gateway = FakeGateway(scripted_content="banana")
        out = await _classify_candidate(cand, gateway, get_settings())
        assert out == [{"cu_type": "premise", "modality": "", "premise_kind": "definition"}]

    @pytest.mark.asyncio
    async def test_gateway_exception_degrades_never_raises(self):
        cand = _candidate()
        out = await _classify_candidate(cand, RaisingGateway(), get_settings())
        assert out == [{"cu_type": "premise", "modality": "", "premise_kind": "definition"}]


class TestBuildCUUnits:
    def test_premise_yields_no_obligation_cu(self):
        cand = _candidate(clause_id="1.2.1")
        units = _build_cu_units(cand, [{"cu_type": "premise", "modality": "", "premise_kind": "definition"}])
        assert len(units) == 1
        assert units[0]["cu_type"] == "premise"
        assert units[0]["cu_type"] not in OBLIGATION_CU_TYPES
        assert units[0]["premise_kind"] == "definition"

    def test_single_cu_reuses_bare_citation_id(self):
        cand = _candidate(clause_id="5.7.1")
        units = _build_cu_units(cand, [{"cu_type": "actor-CU", "modality": "obligation", "premise_kind": ""}])
        assert units[0]["cu_id"] == "CCoP-5.7.1"
        assert units[0]["modality"] == "obligation"

    def test_multi_cu_gets_ordinal_suffix(self):
        cand = _candidate(clause_id="10.1.1")
        units = _build_cu_units(
            cand,
            [
                {"cu_type": "meta-CU", "modality": "", "premise_kind": ""},
                {"cu_type": "actor-CU", "modality": "obligation", "premise_kind": ""},
            ],
        )
        assert [u["cu_id"] for u in units] == ["CCoP-10.1.1#1", "CCoP-10.1.1#2"]
        assert len({u["cu_id"] for u in units}) == 2

    def test_units_carry_clause_link_fields(self):
        cand = _candidate(clause_id="5.7.1")
        units = _build_cu_units(cand, [{"cu_type": "actor-CU", "modality": "obligation", "premise_kind": ""}])
        assert units[0]["clause_id"] == "5.7.1"
        assert units[0]["source_doc"] == "CCoP 2.0"
        assert all(u["cu_type"] in VALID_CU_TYPES for u in units)
