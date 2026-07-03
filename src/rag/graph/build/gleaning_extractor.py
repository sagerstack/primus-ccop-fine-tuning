"""
Gleaning (Multi-Pass) Entity/Relation Extractor (Phase 10 — D-11 gleaning)

Implements the "recall recovery" half of D-11's chunking decouple: gleaning
recovers entity/relationship recall lost to Phase 10's larger, section-scale
extraction chunks (10-06's SectionAlignedSplitter). neo4j-graphrag 1.18.0 has
no native gleaning parameter (confirmed against installed source,
10-RESEARCH.md Q2) — this is a user-added override of the ONE clean subclass
point: `LLMEntityRelationExtractor.extract_for_chunk`.

Each gleaning pass re-prompts the extraction LLM with a compact summary of
what was already found and asks specifically for ADDITIONAL entities/
relationships not already listed — the union of all passes is returned
(no drop). Follow-up LLM output is parsed with the EXACT SAME JSON-repair /
validation / OnError path the base class already uses for its first pass
(`fix_invalid_json`, `Neo4jGraph.model_validate`) — no hand-rolled parser
(Don't-Hand-Roll discipline, RESEARCH.md).

Designed to be injected into a hand-built neo4j-graphrag `Pipeline`
(`loader -> splitter -> schema -> extractor(gleaning) -> resolver -> writer`),
NOT `SimpleKGPipeline` — `SimpleKGPipeline` hardcodes its own
`LLMEntityRelationExtractor` construction and does not expose an
`extractor=` override kwarg in the version installed (verify against the
live `SimpleKGPipeline` constructor signature at ontology_kg_builder
implementation time, 10-07).
"""

import json
import logging
from typing import Any

from pydantic import ValidationError

from neo4j_graphrag.exceptions import LLMGenerationError
from neo4j_graphrag.experimental.components.entity_relation_extractor import (
    LLMEntityRelationExtractor,
    OnError,
    fix_invalid_json,
)
from neo4j_graphrag.experimental.components.schema import GraphSchema
from neo4j_graphrag.experimental.components.types import Neo4jGraph, TextChunk
from neo4j_graphrag.experimental.pipeline.exceptions import InvalidJSONError

logger = logging.getLogger(__name__)


def _summarize_graph(graph: Neo4jGraph) -> str:
    """
    Compact, human-readable list of already-extracted nodes/relationships for
    the glean-again follow-up prompt. Keeps the follow-up prompt short
    (avoids re-sending the full first-pass JSON) while giving the LLM enough
    context to avoid re-emitting duplicates.
    """
    if not graph.nodes and not graph.relationships:
        return "(none)"

    node_lines = [
        f"- {node.label}: {node.properties.get('name', node.id)}"
        for node in graph.nodes
    ]
    relationship_lines = [
        f"- {rel.start_node_id} -{rel.type}-> {rel.end_node_id}"
        for rel in graph.relationships
    ]
    return "\n".join(node_lines + relationship_lines)


class GleaningEntityRelationExtractor(LLMEntityRelationExtractor):
    """
    `LLMEntityRelationExtractor` subclass that adds `max_gleanings` follow-up
    extraction passes per chunk on top of the base class's single-pass
    extraction (D-11).

    `max_gleanings=0` is byte-for-byte equivalent to the base class's
    single-pass `extract_for_chunk` — gleaning is strictly additive.
    """

    # neo4j-graphrag's `ComponentMeta` requires every class in the hierarchy
    # to declare its OWN `run` (it inspects `attrs`, not the resolved MRO) —
    # rebinding to the base implementation satisfies that check without
    # duplicating `LLMEntityRelationExtractor.run`'s body. Only
    # `extract_for_chunk` (the documented override point, RESEARCH.md Q2) is
    # actually customized below.
    run = LLMEntityRelationExtractor.run

    def __init__(
        self,
        *args: Any,
        max_gleanings: int = 1,
        **kwargs: Any,
    ) -> None:
        """
        Args:
            max_gleanings: Number of additional "what did you miss?" passes
                to run per chunk after the base single-pass extraction.
                Explicit, testable constructor param (factory-injection
                discipline mirrored from `kg_builder.py`) — mirrors
                `settings.gleaning_max_gleanings` (D-11) at the call site,
                not read from Settings directly here so unit tests can
                script exact pass counts without constructing Settings.
            *args, **kwargs: Forwarded to `LLMEntityRelationExtractor`
                (llm, prompt_template, create_lexical_graph, on_error,
                max_concurrency, use_structured_output).
        """
        super().__init__(*args, **kwargs)
        self.max_gleanings = max_gleanings

    async def extract_for_chunk(
        self, schema: GraphSchema, examples: str, chunk: TextChunk
    ) -> Neo4jGraph:
        """
        Run the base single-pass extraction, then `max_gleanings` additional
        "what was missed?" passes, unioning all passes' nodes/relationships
        into one graph (no drop).
        """
        graph = await super().extract_for_chunk(schema, examples, chunk)

        for pass_number in range(1, self.max_gleanings + 1):
            extra_graph = await self._glean_pass(
                schema, examples, chunk, graph, pass_number
            )
            graph.nodes.extend(extra_graph.nodes)
            graph.relationships.extend(extra_graph.relationships)

        return graph

    async def _glean_pass(
        self,
        schema: GraphSchema,
        examples: str,
        chunk: TextChunk,
        graph_so_far: Neo4jGraph,
        pass_number: int,
    ) -> Neo4jGraph:
        """Issue one follow-up extraction call asking for ADDITIONAL entities/relationships."""
        found_so_far = _summarize_graph(graph_so_far)
        glean_instruction = (
            f"Already extracted:\n{found_so_far}\n\n"
            "MANY entities and relationships were missed on the first pass. "
            "Find ADDITIONAL entities and relationships in the text that are "
            "NOT already listed above. Do not repeat anything already extracted."
        )
        glean_prompt = self.prompt_template.format(
            text=chunk.text,
            schema=schema.model_dump(exclude_none=True),
            examples=f"{examples}\n\n{glean_instruction}" if examples else glean_instruction,
        )

        llm_result = await self.llm.ainvoke(glean_prompt)
        return self._parse_graph_response(llm_result.content, chunk, pass_number)

    def _parse_graph_response(
        self, raw_content: str, chunk: TextChunk, pass_number: int
    ) -> Neo4jGraph:
        """
        Parse a gleaning pass's raw LLM output into a `Neo4jGraph`, reusing
        the base class's own JSON-repair (`fix_invalid_json`) and validation
        (`Neo4jGraph.model_validate`) — same error handling shape as
        `LLMEntityRelationExtractor.extract_for_chunk`'s V1 path, so
        malformed follow-up JSON is handled identically to a malformed
        first-pass response (T-09-08: errors reported, never silently
        swallowed).
        """
        try:
            repaired_json = fix_invalid_json(raw_content)
            result = json.loads(repaired_json)
        except (json.JSONDecodeError, InvalidJSONError) as e:
            if self.on_error == OnError.RAISE:
                raise LLMGenerationError(
                    f"Gleaning pass {pass_number} LLM response is not valid JSON"
                ) from e
            logger.error(
                f"Gleaning pass {pass_number} LLM response is not valid JSON "
                f"for chunk_index={chunk.index}"
            )
            logger.debug(f"Invalid JSON: {raw_content}")
            return Neo4jGraph()

        try:
            return Neo4jGraph.model_validate(result)
        except ValidationError as e:
            if self.on_error == OnError.RAISE:
                raise LLMGenerationError(
                    f"Gleaning pass {pass_number} LLM response has improper format"
                ) from e
            logger.error(
                f"Gleaning pass {pass_number} LLM response has improper format "
                f"for chunk_index={chunk.index}"
            )
            logger.debug(f"Invalid JSON format: {result}")
            return Neo4jGraph()


__all__: list[str] = ["GleaningEntityRelationExtractor"]
