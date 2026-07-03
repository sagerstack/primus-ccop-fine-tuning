"""
Unit tests for GleaningEntityRelationExtractor (Phase 10 — D-11 gleaning).

The LLM is fully mocked (scripted `.ainvoke` responses) — these tests never
touch the network. Base-class JSON-repair/OnError handling is exercised
directly (no hand-rolled parser under test), per the Don't-Hand-Roll
discipline documented in 10-RESEARCH.md.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from neo4j_graphrag.experimental.components.entity_relation_extractor import OnError
from neo4j_graphrag.experimental.components.schema import GraphSchema
from neo4j_graphrag.experimental.components.types import TextChunk

from rag.graph.build.gleaning_extractor import GleaningEntityRelationExtractor

FIRST_PASS_JSON = json.dumps(
    {
        "nodes": [
            {"id": "0", "label": "Clause", "properties": {"name": "5.3.1"}},
        ],
        "relationships": [],
    }
)

GLEAN_PASS_JSON = json.dumps(
    {
        "nodes": [
            {"id": "1", "label": "Control", "properties": {"name": "Access Review"}},
        ],
        "relationships": [
            {
                "start_node_id": "0",
                "end_node_id": "1",
                "type": "GOVERNS",
                "properties": {},
            },
        ],
    }
)


def _schema() -> GraphSchema:
    return GraphSchema(node_types=())


def _chunk() -> TextChunk:
    return TextChunk(text="5.3.1 The CIIO shall conduct periodic access reviews.", index=0)


def _mock_llm(responses: list[str]) -> MagicMock:
    """LLM whose .ainvoke returns each response in `responses`, in order."""
    llm = MagicMock()
    side_effects = [MagicMock(content=r) for r in responses]
    llm.ainvoke = AsyncMock(side_effect=side_effects)
    return llm


class TestGleaningRecoversAdditionalEntities:
    """max_gleanings=1: base pass + 1 follow-up, union of both (no drop)."""

    @pytest.mark.asyncio
    async def test_makes_first_call_then_one_glean_call(self):
        llm = _mock_llm([FIRST_PASS_JSON, GLEAN_PASS_JSON])
        extractor = GleaningEntityRelationExtractor(llm=llm, max_gleanings=1)

        await extractor.extract_for_chunk(_schema(), "", _chunk())

        assert llm.ainvoke.call_count == 2

    @pytest.mark.asyncio
    async def test_returned_graph_contains_entities_from_both_passes(self):
        llm = _mock_llm([FIRST_PASS_JSON, GLEAN_PASS_JSON])
        extractor = GleaningEntityRelationExtractor(llm=llm, max_gleanings=1)

        graph = await extractor.extract_for_chunk(_schema(), "", _chunk())

        node_labels = {node.label for node in graph.nodes}
        assert node_labels == {"Clause", "Control"}
        assert len(graph.nodes) == 2
        assert len(graph.relationships) == 1
        assert graph.relationships[0].type == "GOVERNS"

    @pytest.mark.asyncio
    async def test_glean_prompt_references_already_extracted_entities(self):
        """The follow-up prompt must tell the LLM what was already found (no blind re-ask)."""
        llm = _mock_llm([FIRST_PASS_JSON, GLEAN_PASS_JSON])
        extractor = GleaningEntityRelationExtractor(llm=llm, max_gleanings=1)

        await extractor.extract_for_chunk(_schema(), "", _chunk())

        glean_call_args = llm.ainvoke.call_args_list[1]
        glean_prompt = glean_call_args.args[0]
        assert "Already extracted" in glean_prompt
        assert "ADDITIONAL" in glean_prompt

    @pytest.mark.asyncio
    async def test_max_gleanings_2_makes_three_calls(self):
        third_pass_json = json.dumps({"nodes": [], "relationships": []})
        llm = _mock_llm([FIRST_PASS_JSON, GLEAN_PASS_JSON, third_pass_json])
        extractor = GleaningEntityRelationExtractor(llm=llm, max_gleanings=2)

        await extractor.extract_for_chunk(_schema(), "", _chunk())

        assert llm.ainvoke.call_count == 3


class TestMaxGleaningsZeroEqualsSinglePass:
    """max_gleanings=0 behaves identically to the base single-pass extraction."""

    @pytest.mark.asyncio
    async def test_only_one_llm_call(self):
        llm = _mock_llm([FIRST_PASS_JSON])
        extractor = GleaningEntityRelationExtractor(llm=llm, max_gleanings=0)

        await extractor.extract_for_chunk(_schema(), "", _chunk())

        assert llm.ainvoke.call_count == 1

    @pytest.mark.asyncio
    async def test_graph_matches_single_pass_extraction(self):
        llm = _mock_llm([FIRST_PASS_JSON])
        extractor = GleaningEntityRelationExtractor(llm=llm, max_gleanings=0)

        graph = await extractor.extract_for_chunk(_schema(), "", _chunk())

        assert len(graph.nodes) == 1
        assert graph.nodes[0].label == "Clause"
        assert graph.relationships == []


class TestMalformedGleanJsonHandledByBaseRepairPath:
    """Malformed follow-up JSON goes through the inherited repair/OnError path, no crash."""

    @pytest.mark.asyncio
    async def test_malformed_glean_json_with_on_error_ignore_does_not_crash(self):
        # Empty string is guaranteed (per fix_invalid_json's own contract) to
        # raise InvalidJSONError after repair — a deterministic malformed case,
        # rather than depending on json_repair's best-effort salvage heuristics.
        malformed_json = ""
        llm = _mock_llm([FIRST_PASS_JSON, malformed_json])
        extractor = GleaningEntityRelationExtractor(
            llm=llm, max_gleanings=1, on_error=OnError.IGNORE
        )

        # Must not raise — malformed gleaning pass yields an empty fragment,
        # first-pass entities are preserved.
        graph = await extractor.extract_for_chunk(_schema(), "", _chunk())

        assert len(graph.nodes) == 1
        assert graph.nodes[0].label == "Clause"

    @pytest.mark.asyncio
    async def test_malformed_glean_json_with_on_error_raise_propagates(self):
        malformed_json = ""
        llm = _mock_llm([FIRST_PASS_JSON, malformed_json])
        extractor = GleaningEntityRelationExtractor(
            llm=llm, max_gleanings=1, on_error=OnError.RAISE
        )

        with pytest.raises(Exception):
            await extractor.extract_for_chunk(_schema(), "", _chunk())
