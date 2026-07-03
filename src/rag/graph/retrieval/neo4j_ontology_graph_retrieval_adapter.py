"""
Neo4j Ontology Graph Retrieval Adapter (Phase 10 — skeleton / contract only)

Implements IGraphRetrievalProvider identically in SHAPE to Phase 9's
Neo4jGraphRetrievalAdapter (D-16 additivity: that adapter and its DI provider
are completely untouched by this file — see
`Container._create_graph_retrieval_provider` / `graph_retrieval_provider`).

This is a CONTRACT-ONLY skeleton (plan 10-02): RETRIEVAL_QUERY is a minimal
placeholder whose sole job is to prove routing distinctness — every returned
Document is tagged `metadata["provider"] = "graphrag-ontology"` so an E2E test
can assert the ontology path is live and separate from Phase 9's `graphrag`
path (closes RESEARCH Pitfall 3). The REAL clause-anchored,
function-type-boosted (D-12) Cypher query lands in plan 10-09 once the
ontology-seeded graph schema exists.
"""

import logging
from typing import Optional

import neo4j
from langchain_core.documents import Document
from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings
from neo4j_graphrag.embeddings.base import Embedder
from neo4j_graphrag.retrievers import HybridCypherRetriever
from neo4j_graphrag.types import RetrieverResultItem

from infrastructure.config.settings import Settings
from rag.graph.ports.i_graph_retrieval_provider import IGraphRetrievalProvider

logger = logging.getLogger(__name__)


class Neo4jOntologyGraphRetrievalAdapter(IGraphRetrievalProvider):
    """
    Skeleton ontology-grounded (Phase 10) Neo4j graph retrieval adapter.

    Structurally identical to Neo4jGraphRetrievalAdapter (Phase 9) so both
    providers are swappable behind the same `IGraphRetrievalProvider` port,
    selected mode-aware by `graph_retrieve_documents` (D-11). The
    RETRIEVAL_QUERY here is a PLACEHOLDER — real clause-anchored,
    function-type-boosted retrieval (D-11/D-12) is implemented in plan 10-09.
    Every returned Document carries `metadata["provider"] = "graphrag-ontology"`
    as a live, provable routing marker distinct from Phase 9's `graphrag` path.
    """

    # STATIC, parameterized Cypher (T-10-02-02) — placeholder only. Same
    # hybrid dense+fulltext shape as Phase 9's adapter; the user query is
    # passed only as a bound parameter via neo4j-graphrag's own
    # parameterization (embedding vector + fulltext query text), never
    # string-interpolated into the Cypher body. Real clause-anchored query
    # with function_type boosting (D-12) lands in plan 10-09.
    RETRIEVAL_QUERY = """
WITH node AS chunk, score
OPTIONAL MATCH (chunk)-[:FROM_DOCUMENT]->(doc:Document)
RETURN
    chunk.text AS original_text,
    elementId(chunk) AS citation_id,
    coalesce(doc.path, 'unknown') AS document_source,
    score AS score
ORDER BY score DESC
""".strip()

    def __init__(
        self,
        settings: Settings,
        driver: Optional["neo4j.Driver"] = None,
        embedder: Optional[Embedder] = None,
        retriever: Optional[HybridCypherRetriever] = None,
        logger_: Optional[logging.Logger] = None,
    ) -> None:
        self.settings = settings
        self._logger = logger_ or logger
        self._driver = driver or neo4j.GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        self._embedder = embedder or SentenceTransformerEmbeddings(
            model=settings.graph_embedding_model
        )
        self._retriever = retriever or HybridCypherRetriever(
            driver=self._driver,
            vector_index_name=settings.graph_vector_index_name,
            fulltext_index_name=settings.graph_fulltext_index_name,
            retrieval_query=self.RETRIEVAL_QUERY,
            embedder=self._embedder,
            result_formatter=self._format_record,
            neo4j_database=settings.neo4j_database,
        )

    def _format_record(self, record: "neo4j.Record") -> RetrieverResultItem:
        """Map a raw Cypher record to the hybrid Document shape, tagged Phase 10."""
        original_text = record.get("original_text") or ""

        metadata = {
            "citation_id": record.get("citation_id"),
            "section": None,
            "document_source": record.get("document_source"),
            "similarity_score": record.get("score"),
            "original_text": original_text,
            # Provable routing marker (plan 10-02): distinguishes this
            # skeleton provider's output from Phase 9's Neo4jGraphRetrievalAdapter,
            # which never sets this key.
            "provider": "graphrag-ontology",
        }
        return RetrieverResultItem(content=original_text, metadata=metadata)

    def retrieve(self, query: str, top_k: int) -> list[Document]:
        """
        Retrieve ontology-grounded graph contexts for `query`.

        Skeleton implementation (plan 10-02) — real clause-anchored,
        function-type-boosted retrieval (D-11/D-12) lands in plan 10-09. The
        query text is embedded internally by neo4j-graphrag and used as the
        Lucene fulltext query for the sparse leg — in both cases via
        neo4j-graphrag's own parameterization, never interpolated into the
        static RETRIEVAL_QUERY Cypher body (T-10-02-02).
        """
        self._logger.info(f"Ontology graph retrieval (top_k={top_k}): {query[:80]}...")
        result = self._retriever.search(query_text=query, top_k=top_k)

        documents = [
            Document(page_content=item.content, metadata=dict(item.metadata or {}))
            for item in result.items
        ]

        self._logger.info(f"Ontology graph retrieval returned {len(documents)} documents")
        return documents


__all__: list[str] = ["Neo4jOntologyGraphRetrievalAdapter"]
