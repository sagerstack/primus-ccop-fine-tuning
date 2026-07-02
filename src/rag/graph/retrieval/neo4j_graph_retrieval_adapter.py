"""
Neo4j Graph Retrieval Adapter (Phase 9 — entity-anchored / "local" retrieval)

Implements IGraphRetrievalProvider using neo4j-graphrag's VectorCypherRetriever:
vector-match relevant Chunk nodes (bge-large-en-v1.5 embeddings, D-07) then
expand one hop to neighboring entities connected via FROM_CHUNK (D-09) to
build a lightweight graph-neighborhood context. All Cypher is a STATIC,
class-level string — the user query is passed only as an embedded query
vector via neo4j-graphrag's own parameterization (T-09-12); it is never
string-formatted into the Cypher body.

Honesty note (D-08/D-19, emergent baseline): the un-governed KG (Plan 02)
does not carry clause-level citation/section metadata on Chunk nodes (only
`text`/`index`/`embedding`) — that clause-grounding is Phase 10's job
(ontology-seeded nodes). `citation_id` here is therefore the chunk's Neo4j
elementId (a stable, unique-but-not-clause-level identifier) and `section`
is always None. This is reported, not silently patched — see 09-04-SUMMARY.md.
"""

import logging
from typing import Optional

import neo4j
from langchain_core.documents import Document
from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings
from neo4j_graphrag.embeddings.base import Embedder
from neo4j_graphrag.retrievers import VectorCypherRetriever
from neo4j_graphrag.types import RetrieverResultItem

from infrastructure.config.settings import Settings
from rag.graph.ports.i_graph_retrieval_provider import IGraphRetrievalProvider

logger = logging.getLogger(__name__)


class Neo4jGraphRetrievalAdapter(IGraphRetrievalProvider):
    """
    Entity-anchored ("local") Neo4j graph retrieval (D-09).

    Vector-searches the `Chunk` embedding index (bge-large-en-v1.5, D-07),
    then expands one hop to neighboring entities via `FROM_CHUNK` to attach
    graph-neighborhood context. Returns hybrid-shaped Documents (D-11) so
    the unchanged primus generation node (D-06) and the judge + RAGAs
    harness run unaffected by the retrieval-provider swap.
    """

    # STATIC, parameterized Cypher (T-09-12). `node` and `score` are the
    # standard variables neo4j-graphrag's VectorCypherRetriever exposes from
    # the underlying vector-index search — never interpolated with user text.
    # Neighborhood expansion is bounded to a single hop (T-09-15): FROM_CHUNK
    # entities directly attached to the matched chunk, no variable-length paths.
    RETRIEVAL_QUERY = """
WITH node AS chunk, score
OPTIONAL MATCH (chunk)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (entity)-[:FROM_CHUNK]->(chunk)
WITH chunk, score, doc, collect(DISTINCT labels(entity)) AS neighbor_label_lists
RETURN
    chunk.text AS original_text,
    elementId(chunk) AS citation_id,
    coalesce(doc.path, 'unknown') AS document_source,
    score AS score,
    neighbor_label_lists AS neighbor_label_lists
ORDER BY score DESC
""".strip()

    _INTERNAL_LABELS = frozenset({"__Entity__", "__KGBuilder__"})

    def __init__(
        self,
        settings: Settings,
        driver: Optional["neo4j.Driver"] = None,
        embedder: Optional[Embedder] = None,
        retriever: Optional[VectorCypherRetriever] = None,
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
        self._retriever = retriever or VectorCypherRetriever(
            driver=self._driver,
            index_name=settings.graph_vector_index_name,
            retrieval_query=self.RETRIEVAL_QUERY,
            embedder=self._embedder,
            result_formatter=self._format_record,
            neo4j_database=settings.neo4j_database,
        )

    def _format_record(self, record: "neo4j.Record") -> RetrieverResultItem:
        """Map a raw Cypher record to the hybrid Document shape (D-11)."""
        original_text = record.get("original_text") or ""
        neighbor_label_lists = record.get("neighbor_label_lists") or []
        neighbor_types = sorted(
            {
                label
                for labels in neighbor_label_lists
                for label in (labels or [])
                if label not in self._INTERNAL_LABELS
            }
        )

        content = original_text
        if neighbor_types:
            content = (
                f"{original_text}\n\n"
                f"[Graph neighborhood — related entity types: {', '.join(neighbor_types)}]"
            )

        metadata = {
            "citation_id": record.get("citation_id"),
            "section": None,
            "document_source": record.get("document_source"),
            "similarity_score": record.get("score"),
            "original_text": original_text,
            "neighbor_entity_types": neighbor_types,
        }
        return RetrieverResultItem(content=content, metadata=metadata)

    def retrieve(self, query: str, top_k: int) -> list[Document]:
        """
        Retrieve graph-neighborhood contexts for `query` (D-06: contexts, not
        an answer). The query text is embedded internally by neo4j-graphrag
        (`self._embedder`) and passed as `query_vector` — never interpolated
        into Cypher (T-09-12).
        """
        self._logger.info(f"Graph retrieval (top_k={top_k}): {query[:80]}...")
        result = self._retriever.search(query_text=query, top_k=top_k)

        documents = [
            Document(page_content=item.content, metadata=dict(item.metadata or {}))
            for item in result.items
        ]

        self._logger.info(f"Graph retrieval returned {len(documents)} documents")
        return documents


__all__: list[str] = ["Neo4jGraphRetrievalAdapter"]
