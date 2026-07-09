"""
Emergent Knowledge Graph Builder (Phase 9 — un-governed baseline)

Wraps neo4j-graphrag's SimpleKGPipeline with NO schema constraint (D-03/D-08):
whatever entities/relationships gpt-4o-mini discovers from the Docling-parsed
CCoP prose are written to Neo4j as-is. This is deliberately the un-governed
reference point — Phase 10 layers ontology-grounded extraction onto the same
engine (D-16).

Model roles (must hold, see 09-CONTEXT.md):
    - Extraction LLM = openai/gpt-4o-mini via OpenRouter (D-06a) — never primus.
    - Embeddings = BAAI/bge-large-en-v1.5, in-process (D-07), 1024-dim cosine
      vector index.

All model/pipeline construction lives behind this single class so Phase 10
can add a schema without rewriting the build pipeline (D-16 additivity seam).
LLM/embedder/pipeline are built via injectable factory functions so unit
tests can mock them without hitting the network or a live Neo4j instance.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Optional

import neo4j
from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings
from neo4j_graphrag.embeddings.base import Embedder
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.indexes import create_fulltext_index, create_vector_index
from neo4j_graphrag.llm import LLMInterface, OpenAILLM

from infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)

LLMFactory = Callable[[Settings], LLMInterface]
EmbedderFactory = Callable[[Settings], Embedder]
PipelineFactory = Callable[[LLMInterface, "neo4j.Driver", Embedder], SimpleKGPipeline]


@dataclass
class BuildStats:
    """Aggregate statistics for an emergent KG build run (T-09-08: failures reported, not swallowed)."""

    docs_processed: int = 0
    chunks_written: int = 0
    nodes_created: int = 0
    relationships_created: int = 0
    failures: list[str] = field(default_factory=list)


def _default_llm_factory(settings: Settings) -> LLMInterface:
    """Build the extraction LLM (D-06a: gpt-4o-mini via OpenRouter, never primus)."""
    return OpenAILLM(
        model_name=settings.graph_extraction_model,
        model_params={"temperature": 0},
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
    )


def _default_embedder_factory(settings: Settings) -> Embedder:
    """Build the chunk embedder (D-07: bge-large-en-v1.5, in-process)."""
    return SentenceTransformerEmbeddings(model=settings.graph_embedding_model)


def _default_pipeline_factory(
    llm: LLMInterface, driver: "neo4j.Driver", embedder: Embedder
) -> SimpleKGPipeline:
    """Build the emergent (schema-free) KG pipeline (D-03/D-08: NO schema kwargs)."""
    return SimpleKGPipeline(
        llm=llm,
        driver=driver,
        embedder=embedder,
        from_pdf=False,
    )


class EmergentKGBuilder:
    """
    Builds an un-governed (schema-free) CCoP knowledge graph in Neo4j.

    Extraction = gpt-4o-mini via OpenRouter (D-06a). Embeddings = bge-large-en-v1.5
    in-process (D-07). NO schema/entities/relations constraint (D-03/D-08) — this
    is the emergent baseline; Phase 10 adds ontology governance on the identical
    engine (D-16).
    """

    def __init__(
        self,
        settings: Settings,
        driver: Optional["neo4j.Driver"] = None,
        llm_factory: LLMFactory = _default_llm_factory,
        embedder_factory: EmbedderFactory = _default_embedder_factory,
        pipeline_factory: PipelineFactory = _default_pipeline_factory,
    ) -> None:
        self.settings = settings
        self.driver = driver or neo4j.GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        self.llm = llm_factory(settings)
        self.embedder = embedder_factory(settings)
        self._ensure_vector_index()
        self._ensure_fulltext_index()
        self.pipeline = pipeline_factory(self.llm, self.driver, self.embedder)

    def _ensure_vector_index(self) -> None:
        """
        Idempotently create the Chunk vector index (T-09-05 mitigation N/A here;
        no secrets in this path). "Already exists" is swallowed — any other
        failure (e.g. connection refused) propagates so misconfiguration is
        never silently ignored.
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
        """
        Idempotently create the Chunk fulltext (Lucene) index over `Chunk.text`
        — the sparse leg of the graph HybridCypherRetriever (Wave-6 retrieval
        parity: dense + sparse). `fail_if_exists=False` makes this a no-op when
        the index already exists, so rebuilds and the existing live graph both
        converge to the same index set without manual intervention.
        """
        create_fulltext_index(
            self.driver,
            self.settings.graph_fulltext_index_name,
            label="Chunk",
            node_properties=["text"],
            fail_if_exists=False,
        )

    async def build(self, texts: dict[str, str]) -> BuildStats:
        """
        Run the emergent KG pipeline over each document's full text.

        Args:
            texts: Mapping of doc_name -> full Docling markdown (D-04 constant
                input, produced by rag.graph.build.corpus_source).

        Returns:
            BuildStats aggregated across all documents. Failures are recorded,
            never silently swallowed (T-09-08).
        """
        stats = BuildStats()

        for doc_name, text in texts.items():
            try:
                # Pass doc_name as file_path so each Document node's `path` is the
                # real source name (e.g. "CCoP 2.0", "CCoP Response to Feedback")
                # instead of neo4j-graphrag's generic "document.txt" default. In
                # text mode (from_pdf=False) file_path is used ONLY to set
                # document_info.path — it does NOT trigger file loading. Without
                # this, all 7 docs collapse to one indistinguishable Document node,
                # destroying retrieval provenance (bug: doc source unattributable →
                # model fabricates citations). See bugs.md 2026-07-02.
                await self.pipeline.run_async(text=text, file_path=doc_name)
                stats.docs_processed += 1
            except Exception as e:
                logger.error(f"KG build failed for document '{doc_name}': {e}")
                stats.failures.append(f"{doc_name}: {e}")

        self._accumulate_graph_stats(stats)
        return stats

    def _accumulate_graph_stats(self, stats: BuildStats) -> None:
        """
        Query Neo4j directly for authoritative node/relationship/chunk counts.

        neo4j-graphrag's PipelineResult does not guarantee a stable stats
        schema across versions, so counts are read from the graph itself
        rather than trusted from pipeline-internal result objects.
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


__all__: list[str] = ["EmergentKGBuilder", "BuildStats"]
