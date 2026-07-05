"""
Policy Graph Stage 2 -- 4-tuple extraction tests (Phase 11, 11-04b /
D-34/D-36/D-37).

Pure extraction logic against a FAKE gateway -- no Neo4j, no real Opus. Runs
under `pytest -m "not integration"`. Covers: null/structured coercion,
subject-inheritance parent block, degrade-to-empty, and retry-on-empty (D-36).
The live real-Opus extraction is the 11-04b W4 regen run.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from domain.entities.model_response import ModelResponse
from infrastructure.config.settings import get_settings
from rag.graph.ontology.cu_classifier import OBLIGATION_CU_TYPES
from rag.graph.ontology.cu_extractor import (
    CU_TUPLE_EXTRACTION_PROMPT,
    CUExtractor,
    CUTuple,
    ExtractionStats,
    _build_prompt,
    _call_and_parse,
    _parent_block,
)


@dataclass
class FakeGateway:
    """Returns scripted responses in order; repeats the last once exhausted."""

    responses: list = field(
        default_factory=lambda: ['{"subject":"CIIO","constraint":"shall X","context":"","conditions":""}']
    )
    calls: list = field(default_factory=list)

    async def generate_response(self, prompt: str, model_name: str, **kwargs):
        idx = min(len(self.calls), len(self.responses) - 1)
        self.calls.append({"prompt": prompt, "model_name": model_name})
        return ModelResponse(content=self.responses[idx], model_name=model_name)


class RaisingGateway:
    async def generate_response(self, prompt: str, model_name: str, **kwargs):
        raise RuntimeError("Claude CLI error: simulated timeout")


class _FakeDriver:
    """Truthy stand-in so CUExtractor.__init__ does not open a real driver."""

    def session(self, database=None):  # pragma: no cover - never called in unit tests
        raise AssertionError("driver must not be used in _extract_one unit tests")


def _extractor(gateway) -> CUExtractor:
    return CUExtractor(settings=get_settings(), driver=_FakeDriver(), gateway=gateway)


def _cu(
    cu_id="CCoP-5.7.1",
    citation_id="CCoP-5.7.1",
    text="The CIIO shall secure all remote connections to the CII.",
    parent_text=None,
):
    return {
        "cu_id": cu_id,
        "source_doc": "CCoP 2.0",
        "cu_type": "actor-CU",
        "citation_id": citation_id,
        "text": text,
        "parent_text": parent_text,
    }


class TestCUTuple:
    def test_null_coerced_to_empty_string(self):
        t = CUTuple.model_validate(
            {"subject": None, "constraint": "x", "context": None, "conditions": None}
        )
        assert t.subject == "" and t.context == "" and t.conditions == ""

    def test_structured_conditions_serialized_to_json_string(self):
        t = CUTuple.model_validate(
            {"subject": "CIIO", "constraint": "x", "conditions": {"any": ["a", "b"]}}
        )
        assert t.conditions == '{"any": ["a", "b"]}'

    def test_is_empty_true_when_all_blank(self):
        assert CUTuple().is_empty() is True
        assert CUTuple(subject="CIIO").is_empty() is False


class TestParentBlock:
    def test_lettered_subclause_with_parent_injects_stem(self):
        block = _parent_block({"citation_id": "CCoP-5.7.2(a)", "parent_text": "The CIIO shall:"})
        assert "Parent stem: The CIIO shall:" in block

    def test_non_subclause_returns_empty(self):
        assert _parent_block({"citation_id": "CCoP-5.7.2", "parent_text": "The CIIO shall:"}) == ""

    def test_subclause_without_parent_text_returns_empty(self):
        assert _parent_block({"citation_id": "CCoP-5.7.2(a)", "parent_text": ""}) == ""

    def test_build_prompt_includes_parent_block_for_subclause(self):
        cu = _cu(citation_id="CCoP-5.7.2(a)", parent_text="The CIIO shall:")
        prompt = _build_prompt(CU_TUPLE_EXTRACTION_PROMPT, cu)
        assert "Parent stem: The CIIO shall:" in prompt


class TestCallAndParse:
    @pytest.mark.asyncio
    async def test_valid_json_yields_tuple(self):
        gw = FakeGateway(
            responses=['{"subject":"CIIO","constraint":"shall secure","context":"remote","conditions":""}']
        )
        t = await _call_and_parse("p", "ref", gw, get_settings())
        assert t.subject == "CIIO" and t.constraint == "shall secure" and t.context == "remote"

    @pytest.mark.asyncio
    async def test_malformed_json_degrades_to_empty(self):
        gw = FakeGateway(responses=["not json"])
        assert (await _call_and_parse("p", "ref", gw, get_settings())).is_empty()

    @pytest.mark.asyncio
    async def test_gateway_exception_degrades_to_empty(self):
        assert (await _call_and_parse("p", "ref", RaisingGateway(), get_settings())).is_empty()


class TestRetryOnEmpty:
    @pytest.mark.asyncio
    async def test_retry_recovers_empty_tuple_for_nontrivial_text(self):
        gw = FakeGateway(
            responses=[
                '{"subject":"","constraint":"","context":"","conditions":""}',
                '{"subject":"CIIO","constraint":"shall secure remote connections","context":"CII","conditions":""}',
            ]
        )
        stats = ExtractionStats()
        tup = await _extractor(gw)._extract_one(_cu(), stats)
        assert tup.subject == "CIIO"
        assert stats.cus_retried == 1
        assert stats.cus_still_empty_after_retry == 0
        assert len(gw.calls) == 2

    @pytest.mark.asyncio
    async def test_no_retry_for_trivial_text(self):
        gw = FakeGateway(responses=['{"subject":"","constraint":"","context":"","conditions":""}'])
        stats = ExtractionStats()
        tup = await _extractor(gw)._extract_one(_cu(text="short."), stats)
        assert tup.is_empty()
        assert stats.cus_retried == 0
        assert len(gw.calls) == 1

    @pytest.mark.asyncio
    async def test_still_empty_after_retry_is_flagged(self):
        gw = FakeGateway(responses=['{"subject":"","constraint":"","context":"","conditions":""}'])
        stats = ExtractionStats()
        tup = await _extractor(gw)._extract_one(_cu(), stats)
        assert tup.is_empty()
        assert stats.cus_retried == 1
        assert stats.cus_still_empty_after_retry == 1
        assert len(gw.calls) == 2


class TestObligationTypes:
    def test_premise_not_an_obligation_type(self):
        assert "premise" not in OBLIGATION_CU_TYPES
        assert OBLIGATION_CU_TYPES == frozenset({"meta-CU", "actor-CU"})
