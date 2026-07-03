"""
Ontology-Constrained Knowledge Graph Builder (Phase 10 -- D-06/D-07/D-11 fix)

Wraps neo4j-graphrag's SimpleKGPipeline machinery with the LOCKED ontology
schema (24 node types / 48 relationship types / 9 patterns,
`additional_node_types=False`, `additional_relationship_types=False`,
`src/rag/graph/ontology/ontology_config.json`), a custom extraction prompt
enforcing canonical names + ignoring illustrative/example passages (D-07),
the section-aligned extraction-unit splitter (10-06 `SectionAlignedSplitter`,
D-11), the gleaning multi-pass extractor (10-06
`GleaningEntityRelationExtractor`, D-11), and `SinglePropertyExactMatchResolver`
dedup (D-07, `resolve_property="name"` -- already the default resolver
`SimpleKGPipelineConfig` builds when entity resolution is enabled).

This is deliberately the GOVERNED counterpart to `EmergentKGBuilder`
(`rag/graph/build/kg_builder.py`, Phase 9's un-governed baseline, D-16) --
same factory-injection discipline, LLM/embedder roles held constant
(D-06a/D-07), same idempotent-index-bootstrap and provenance-preserving
(`file_path=doc_name`) build loop (bugs.md 2026-07-02 fix, preserved
verbatim).

Integration note -- supersedes 10-RESEARCH.md Q2/A5's "hand-built Pipeline"
assumption (verified live against installed neo4j-graphrag==1.18.0 source,
per A5's own "verify constructor signature at implementation time"
instruction): the public `SimpleKGPipeline` class indeed has NO `extractor=`
override kwarg (confirmed via `inspect.signature`). BUT the underlying
`SimpleKGPipelineConfig` (a `TemplatePipelineConfig`) resolves every pipeline
component through a documented, purpose-built extension point --
`_get_<component_name>()` methods, dynamically dispatched by
`TemplatePipelineConfig._get_component` (`getattr(self, f"_get_{name}")`).
Subclassing `SimpleKGPipelineConfig` and overriding ONLY `_get_extractor()`
(verified live: the subclass identity and the override both survive
`PipelineRunner.from_config()`'s pydantic discriminated-union validation --
`isinstance(parsed_config, MySubclass)` still holds afterwards) injects the
gleaning extractor through the EXACT SAME
loader -> splitter -> schema -> extractor -> pruner -> writer -> resolver
wiring `SimpleKGPipeline` itself uses in production, avoiding the risk of
hand-reproducing that wiring incorrectly. `_OntologyKGPipelineConfig` below
is that one-method-override subclass; `OntologyKGBuilder` drives it via
`PipelineRunner`, mirroring `SimpleKGPipeline.run_async`'s own
`self.runner.run(...)` call shape exactly.
"""

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

import neo4j
from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings
from neo4j_graphrag.embeddings.base import Embedder
from neo4j_graphrag.experimental.components.entity_relation_extractor import (
    EntityRelationExtractor,
)
from neo4j_graphrag.experimental.components.text_splitters.base import TextSplitter
from neo4j_graphrag.experimental.pipeline.config.object_config import ComponentType
from neo4j_graphrag.experimental.pipeline.config.runner import PipelineRunner
from neo4j_graphrag.experimental.pipeline.config.template_pipeline.simple_kg_builder import (
    SimpleKGPipelineConfig,
)
from neo4j_graphrag.indexes import create_fulltext_index, create_vector_index
from neo4j_graphrag.llm import LLMInterface, OpenAILLM

from infrastructure.config.settings import Settings
from rag.graph.build.gleaning_extractor import GleaningEntityRelationExtractor
from rag.graph.build.section_aligned_splitter import SectionAlignedSplitter

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]

# Resolved relative to this file so it is correct regardless of the caller's
# working directory (src/rag/graph/build -> src/rag/graph/ontology).
DEFAULT_ONTOLOGY_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent / "ontology" / "ontology_config.json"
)

LLMFactory = Callable[[Settings], LLMInterface]
EmbedderFactory = Callable[[Settings], Embedder]
PipelineRunnerFactory = Callable[
    [LLMInterface, "neo4j.Driver", Embedder, dict[str, Any], TextSplitter, str, int],
    PipelineRunner,
]

# D-07: canonical-name enforcement + ignore-illustrative-passages, layered onto
# the base ERExtractionTemplate's JSON-extraction instructions (RESEARCH.md
# Q1). Placeholders {schema}/{examples}/{text} MUST be preserved verbatim --
# LLMEntityRelationExtractor.extract_for_chunk .format()s this string with
# exactly those three kwargs (neo4j_graphrag.generation.prompts.PromptTemplate).
ONTOLOGY_EXTRACTION_PROMPT = """
You are a top-tier algorithm designed for extracting
information in structured formats to build a knowledge graph.

Extract the entities (nodes) and specify their type from the following text.
Also extract the relationships between these nodes.

IMPORTANT: This text is a REGULATORY CODE OF PRACTICE. Do NOT extract entities
or relationships from illustrative examples, hypothetical scenarios, or
placeholder names (e.g. "John Doe", "Company X", "N.A."). Only extract
entities and relationships stated as normative regulatory content
(obligations, definitions, scope statements, controls). Every extracted node
MUST carry a canonical "name" property using the EXACT term as it appears in
the source clause -- do not paraphrase, abbreviate, or invent a name.

Return result as JSON using the following format:
{{"nodes": [ {{"id": "0", "label": "Person", "properties": {{"name": "John"}} }}],
"relationships": [{{"type": "KNOWS", "start_node_id": "0", "end_node_id": "1", "properties": {{"since": "2024-08-01"}} }}] }}

Use ONLY the following node and relationship types -- this vocabulary is
LOCKED (do not invent new labels):
{schema}

Assign a unique ID (string) to each node, and reuse it to define relationships.
Do respect the source and target node types for relationship and
the relationship direction.

Make sure you adhere to the following rules to produce valid JSON objects:
- Do not return any additional information other than the JSON in it.
- Omit any backticks around the JSON - simply output the JSON on its own.
- The JSON object must not wrapped into a list - it is its own JSON object.
- Property names must be enclosed in double quotes

Examples:
{examples}

Input text:

{text}
""".strip()


@dataclass
class BuildStats:
    """Aggregate statistics for an ontology-constrained KG build run (T-09-08: failures reported, not swallowed)."""

    docs_processed: int = 0
    chunks_written: int = 0
    nodes_created: int = 0
    relationships_created: int = 0
    failures: list[str] = field(default_factory=list)


def _default_llm_factory(settings: Settings) -> LLMInterface:
    """Build the extraction LLM (D-06a: gpt-4o-mini via OpenRouter, held constant P9->P10)."""
    return OpenAILLM(
        model_name=settings.graph_extraction_model,
        model_params={"temperature": 0},
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
    )


def _default_embedder_factory(settings: Settings) -> Embedder:
    """Build the chunk embedder (D-07: bge-large-en-v1.5, in-process, held constant P9->P10)."""
    return SentenceTransformerEmbeddings(model=settings.graph_embedding_model)


def load_locked_schema(
    ontology_config_path: PathLike = DEFAULT_ONTOLOGY_CONFIG_PATH,
    permissive: bool = False,
) -> dict[str, Any]:
    """
    Load the LOCKED ontology (`ontology_config.json`, 24 node types / 48
    relationship types / 9 patterns) into the `schema=` dict shape
    `neo4j_graphrag.experimental.components.schema.GraphSchema` accepts.

    Verified live against the installed package: extra JSON keys per node
    type (`example_terms`, `provenance`, `flagged_ambiguities`) are silently
    ignored by `NodeType`'s pydantic validation -- only `label`/`description`
    are consumed; `relationship_types` accepts the flat string list as-is;
    `patterns` requires 3-tuples (JSON gives 3-lists, converted below).

    `additional_node_types`/`additional_relationship_types` are FLIPPED to
    True when `permissive=True` -- the RESEARCH.md Pitfall 1 escape hatch for
    iteration (D-06/D-07 lock the vocabulary once benchmark/gold-relation
    coverage is verified; permissive mode lets extraction surface
    out-of-schema terms during dev instead of silently dropping them).
    """
    config = json.loads(Path(ontology_config_path).read_text())
    return {
        "node_types": config["node_types"],
        "relationship_types": config["relationship_types"],
        "patterns": [tuple(p) for p in config["patterns"]],
        "additional_node_types": permissive or config["additional_node_types"],
        "additional_relationship_types": (
            permissive or config["additional_relationship_types"]
        ),
    }


class _OntologyKGPipelineConfig(SimpleKGPipelineConfig):
    """
    `SimpleKGPipelineConfig` subclass injecting the gleaning extractor (D-11)
    via the library's documented per-component override point (module
    docstring). Every other component (`_get_splitter`, `_get_schema`,
    `_get_writer`, `_get_resolver`, `_get_pruner`, connection wiring, ...) is
    inherited UNCHANGED from `SimpleKGPipelineConfig` -- this is a
    single-method override, not a reimplementation of the pipeline graph.

    `_get_resolver()` (inherited, unchanged) already returns
    `SinglePropertyExactMatchResolver(driver=..., neo4j_database=...)` with
    its own default `resolve_property="name"` whenever
    `perform_entity_resolution=True` -- exactly the D-07 dedup requirement,
    with no override needed here.
    """

    max_gleanings: int = 1

    def _get_extractor(self) -> EntityRelationExtractor:
        llm = self.get_default_llm()
        return GleaningEntityRelationExtractor(
            llm=llm,
            prompt_template=self.prompt_template,
            on_error=self.on_error,
            use_structured_output=llm.supports_structured_output,
            max_gleanings=self.max_gleanings,
        )


def _default_runner_factory(
    llm: LLMInterface,
    driver: "neo4j.Driver",
    embedder: Embedder,
    schema: dict[str, Any],
    text_splitter: TextSplitter,
    prompt_template: str,
    max_gleanings: int,
) -> PipelineRunner:
    """
    Build the hand-configured `PipelineRunner` (schema-constrained + gleaning
    + section-aligned splitter + exact-match resolver). Kept as an injectable
    factory function -- mirrors `kg_builder.py`'s `PipelineFactory` seam --
    so unit tests can assert on the arguments passed here (schema content,
    prompt content, splitter/gleaning wiring) without constructing a real
    `PipelineRunner`, which eagerly builds a `Neo4jWriter` that queries the
    live driver for its server version at construction time.
    """
    config = _OntologyKGPipelineConfig.model_validate(
        dict(
            llm_config=llm,
            neo4j_config=driver,
            embedder_config=embedder,
            schema=schema,
            from_file=False,
            text_splitter=ComponentType(text_splitter),
            on_error="IGNORE",
            prompt_template=prompt_template,
            perform_entity_resolution=True,
            max_gleanings=max_gleanings,
        )
    )
    return PipelineRunner.from_config(config)


class OntologyKGBuilder:
    """
    Builds a SCHEMA-CONSTRAINED CCoP knowledge graph in Neo4j (Phase 10).

    Extraction = gpt-4o-mini via OpenRouter (D-06a, held constant with Phase
    9). Embeddings = bge-large-en-v1.5 in-process (D-07, held constant).
    Schema = the LOCKED `ontology_config.json` (D-06/D-07 fix for Phase 9's
    fragmented-duplicate/junk-instance/scenario-not-regulation
    anti-patterns). Extraction unit = `SectionAlignedSplitter` + gleaning
    (D-11, 10-06). Dedup = `SinglePropertyExactMatchResolver`
    (`resolve_property="name"`, D-07).
    """

    def __init__(
        self,
        settings: Settings,
        driver: Optional["neo4j.Driver"] = None,
        llm_factory: LLMFactory = _default_llm_factory,
        embedder_factory: EmbedderFactory = _default_embedder_factory,
        runner_factory: PipelineRunnerFactory = _default_runner_factory,
        ontology_config_path: PathLike = DEFAULT_ONTOLOGY_CONFIG_PATH,
        permissive: bool = False,
        max_gleanings: Optional[int] = None,
        text_splitter: Optional[TextSplitter] = None,
    ) -> None:
        self.settings = settings
        self.driver = driver or neo4j.GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        self.llm = llm_factory(settings)
        self.embedder = embedder_factory(settings)
        self.permissive = permissive
        self._ensure_vector_index()
        self._ensure_fulltext_index()

        self.schema = load_locked_schema(ontology_config_path, permissive=permissive)
        self.text_splitter = text_splitter or SectionAlignedSplitter()
        self.max_gleanings = (
            max_gleanings if max_gleanings is not None else settings.gleaning_max_gleanings
        )

        self.runner = runner_factory(
            self.llm,
            self.driver,
            self.embedder,
            self.schema,
            self.text_splitter,
            ONTOLOGY_EXTRACTION_PROMPT,
            self.max_gleanings,
        )

    def _ensure_vector_index(self) -> None:
        """
        Idempotently create the Chunk vector index. "Already exists" is
        swallowed -- any other failure (e.g. connection refused) propagates
        so misconfiguration is never silently ignored (mirrors
        `EmergentKGBuilder`, same index name/shape -- Phase 9/10 share one
        Chunk vector index since both write `:Chunk` nodes to the same
        Neo4j database).
        """
        try:
            create_vector_index(
                self.driver,
                self.settings.graph_vector_index_name,
                label="Chunk",
                embedding_property="embedding",
                dimensions=self.settings.graph_embedding_dimensions,
                similarity_fn="cosine",
            )
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(
                    f"Vector index '{self.settings.graph_vector_index_name}' "
                    "already exists — skipping creation."
                )
            else:
                raise

    def _ensure_fulltext_index(self) -> None:
        """Idempotently create the Chunk fulltext (Lucene) index (mirrors `EmergentKGBuilder`)."""
        create_fulltext_index(
            self.driver,
            self.settings.graph_fulltext_index_name,
            label="Chunk",
            node_properties=["text"],
            fail_if_exists=False,
        )

    async def build(self, texts: dict[str, str]) -> BuildStats:
        """
        Run the ontology-constrained KG pipeline over each document's full
        text.

        Args:
            texts: Mapping of doc_name -> full Docling markdown (D-04
                constant input, produced by rag.graph.build.corpus_source --
                same input Phase 9's EmergentKGBuilder consumes).

        Returns:
            BuildStats aggregated across all documents. Failures are
            recorded, never silently swallowed (T-09-08).
        """
        stats = BuildStats()

        for doc_name, text in texts.items():
            try:
                # Pass doc_name as file_path so each Document node's `path` is
                # the real source name, not neo4j-graphrag's generic
                # "document.txt" default (provenance-collapse fix, bugs.md
                # 2026-07-02, preserved verbatim from EmergentKGBuilder).
                await self.runner.run(
                    {"text": text, "file_path": doc_name, "document_metadata": None}
                )
                stats.docs_processed += 1
            except Exception as e:
                logger.error(f"Ontology KG build failed for document '{doc_name}': {e}")
                stats.failures.append(f"{doc_name}: {e}")

        self._accumulate_graph_stats(stats)
        return stats

    def _accumulate_graph_stats(self, stats: BuildStats) -> None:
        """
        Query Neo4j directly for authoritative node/relationship/chunk
        counts (mirrors `EmergentKGBuilder`'s convention -- pipeline-internal
        result objects are not trusted for a stable stats schema).
        """
        try:
            with self.driver.session(database=self.settings.neo4j_database) as session:
                node_count = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
                rel_count = session.run(
                    "MATCH ()-[r]->() RETURN count(r) AS c"
                ).single()["c"]
                chunk_count = session.run(
                    "MATCH (c:Chunk) RETURN count(c) AS c"
                ).single()["c"]
            stats.nodes_created = node_count
            stats.relationships_created = rel_count
            stats.chunks_written = chunk_count
        except Exception as e:
            logger.warning(f"Could not query graph stats after build: {e}")


__all__: list[str] = [
    "OntologyKGBuilder",
    "BuildStats",
    "ONTOLOGY_EXTRACTION_PROMPT",
    "DEFAULT_ONTOLOGY_CONFIG_PATH",
    "load_locked_schema",
]
