"""
Neo4j Ontology Graph Retrieval Adapter (Phase 10 — real clause-anchored
retrieval + function-type routing, plan 10-09)

Implements IGraphRetrievalProvider identically in SHAPE to Phase 9's
Neo4jGraphRetrievalAdapter (D-16 additivity: that adapter and its DI provider
are completely untouched by this file — see
`Container._create_graph_retrieval_provider` / `graph_retrieval_provider`).

RETRIEVAL_QUERY now retrieves at seeded `:Clause` granularity (D-10/D-11):
every matched `:Chunk` is `OPTIONAL MATCH`-expanded to its `:Clause` via the
`LINKED_TO` edge created by `ClauseLinker` (plan 10-07), and `citation_id`
carries the REAL seeded `clause_id` (falling back to `elementId(chunk)` only
when a chunk has no linked clause) — the concrete fix for the Phase 9
"Honesty note" limitation. Clauses whose `function_type` (D-09) matches the
`$function_type` bound Cypher parameter (classified by
`rag/retrieval/nodes/function_type_routing.py`, plan 10-09 Task 2) receive a
`$boost` multiplier (D-12) — this is the ranking lever that makes
function-type-matching clauses out-rank distractors. A deterministic
secondary sort key (`clause_id ASC`) resolves score ties per the LOCKED D-15
determinism decision (`docs/project_notes/research/
2026-07-02-neo4j-exact-vector-search-spike.md`: ANN + stable Cypher
tie-break + frozen index — no exact-search API exists at the retriever layer
that preserves hybrid dense+sparse semantics).

Every returned Document is still tagged `metadata["provider"] =
"graphrag-ontology"` (plan 10-02 routing-distinctness marker, preserved).

Lucene special-character escaping (deferred-items.md, carried from plan
10-01's baseline run): the sparse/fulltext leg's query text is escaped for
Lucene classic-QueryParser special characters (e.g. `/`, `'`) before being
sent to `HybridCypherRetriever.search()`, fixing the `TokenMgrError` observed
on B02-001 ("username/password ... user's ..."). The DENSE leg is unaffected
— the query is embedded once via `self._embedder.embed_query(query)` on the
UN-escaped original text and passed as an explicit `query_vector`, so
escaping only ever touches the Lucene fulltext parameter, never the semantic
embedding.
"""

import logging
import re
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

# Lucene classic-QueryParser special characters (per the official Lucene
# QueryParserBase escape() char set: + - && || ! ( ) { } [ ] ^ " ~ * ? : \ /)
# PLUS a single quote, since the observed B02-001 TokenMgrError was produced
# by a `/` immediately followed by text containing a `'` ("username/password
# ... user's ...") — escaping both defensively closes the whole class of
# lexical errors, not just the narrowly-reproduced case.
_LUCENE_SPECIAL_CHARS_RE = re.compile(r"""([+\-!(){}\[\]^"~*?:\\/&|'])""")


def _escape_lucene_query_text(text: str) -> str:
    """
    Backslash-escape Lucene query-parser special characters in `text`.

    Neo4j's Lucene fulltext index (`db.index.fulltext.queryNodes`) parses the
    raw query string with the Lucene classic QueryParser, which raises a
    `TokenMgrError` (surfaced by neo4j-graphrag as `SearchQueryParseError`)
    on unescaped special characters — observed on B02-001's
    "username/password" (see plan 10-01's deferred-items.md entry). This is
    applied ONLY to the text handed to the Lucene/fulltext leg (`query_text`
    passed to `HybridCypherRetriever.search`), never to the dense-vector
    embedding input, which uses the original un-escaped query.
    """
    if not text:
        return text
    return _LUCENE_SPECIAL_CHARS_RE.sub(r"\\\1", text)


class Neo4jOntologyGraphRetrievalAdapter(IGraphRetrievalProvider):
    """
    Ontology-grounded (Phase 10) Neo4j clause-anchored graph retrieval adapter.

    Structurally identical to Neo4jGraphRetrievalAdapter (Phase 9) so both
    providers are swappable behind the same `IGraphRetrievalProvider` port,
    selected mode-aware by `graph_retrieve_documents` (D-11). Unlike Phase 9
    (chunk-only, `citation_id = elementId(chunk)`), this adapter retrieves at
    seeded `:Clause` granularity via `LINKED_TO` (D-10/D-11) and boosts
    clauses matching the classified question intent (`function_type`, D-12).
    Every returned Document carries `metadata["provider"] = "graphrag-ontology"`
    as a live, provable routing marker distinct from Phase 9's `graphrag` path
    (plan 10-02).
    """

    # STATIC, parameterized Cypher (T-09-12/T-10-02-02 discipline preserved).
    # `node`/`score` are bound by neo4j-graphrag's own hybrid dense+fulltext
    # search; `$function_type`/`$boost` are bound Cypher parameters passed via
    # HybridCypherRetriever.search(query_params=...) — NEVER string-
    # interpolated into the Cypher body (T-09-12). Retrieves at seeded
    # :Clause granularity (D-10/D-11) via the LINKED_TO edge (ClauseLinker,
    # plan 10-07) and boosts the matching function-type (D-12/D-09).
    # Deterministic secondary sort key (`ASC` clause_id tie-break, D-15) per
    # the LOCKED determinism decision — no exact-search API exists at the
    # retriever layer, so ties are resolved via a stable Cypher ORDER BY.
    RETRIEVAL_QUERY = """
WITH node AS chunk, score
OPTIONAL MATCH (chunk)-[:FROM_DOCUMENT]->(doc:Document)
OPTIONAL MATCH (chunk)-[:LINKED_TO]->(c:Clause)
WITH chunk, score, doc, c,
     coalesce(c.clause_id, elementId(chunk)) AS resolved_citation_id,
     CASE
         WHEN c.function_type = $function_type THEN score * $boost
         ELSE score
     END AS boosted_score
RETURN
    chunk.text AS original_text,
    resolved_citation_id AS citation_id,
    c.clause_id AS section,
    coalesce(doc.path, 'unknown') AS document_source,
    boosted_score AS score
ORDER BY boosted_score DESC, resolved_citation_id ASC
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
        """Map a raw Cypher record to the hybrid Document shape (D-11), clause-anchored."""
        original_text = record.get("original_text") or ""

        metadata = {
            # Real seeded clause_id (D-10/D-11) — falls back to
            # elementId(chunk) only when the chunk has no LINKED_TO clause
            # (see RETRIEVAL_QUERY's coalesce). Fixes the Phase 9 "Honesty
            # note" limitation (elementId(chunk)-only citation_id).
            "citation_id": record.get("citation_id"),
            "section": record.get("section"),
            "document_source": record.get("document_source"),
            "similarity_score": record.get("score"),
            "original_text": original_text,
            # Provable routing marker (plan 10-02, preserved): distinguishes
            # this provider's output from Phase 9's Neo4jGraphRetrievalAdapter,
            # which never sets this key.
            "provider": "graphrag-ontology",
        }
        return RetrieverResultItem(content=original_text, metadata=metadata)

    def retrieve(self, query: str, top_k: int, function_type: str = "") -> list[Document]:
        """
        Retrieve clause-anchored, function-type-boosted graph contexts (D-12).

        `function_type` is an ADDITIONAL optional keyword-only-in-practice
        argument on this concrete override (the shared `IGraphRetrievalProvider`
        port's abstract signature, `retrieve(query, top_k)`, is intentionally
        left UNCHANGED — Python's ABC machinery does not enforce exact
        signature parity, and Phase 9's `Neo4jGraphRetrievalAdapter.retrieve`
        is untouched, D-16 additivity). The mode-aware caller
        (`graph_retrieve_documents`, `rag/graph/retrieval/graph_retrieval_node.py`)
        passes `state["function_type"]` (populated by
        `rag/retrieval/nodes/function_type_routing.py`) ONLY when
        `mode == "graphrag-ontology"`, so Phase 9's call site
        (`provider.retrieve(query=query, top_k=top_k)`, no function_type) is
        never affected.

        The query is embedded ONCE via `self._embedder.embed_query(query)` on
        the original, un-escaped text (dense leg); a SEPARATE
        Lucene-escaped copy of the text is sent as `query_text` (sparse/
        fulltext leg only) — fixes the B02-001-class `TokenMgrError` on `/`
        and `'` without altering the semantic embedding. `$function_type`/
        `$boost` are passed as bound Cypher parameters via
        `HybridCypherRetriever.search(query_params=...)` — never
        string-interpolated into the static RETRIEVAL_QUERY body (T-09-12).
        """
        self._logger.info(
            f"Ontology graph retrieval (top_k={top_k}, "
            f"function_type={function_type or 'none'}): {query[:80]}..."
        )
        query_vector = self._embedder.embed_query(query)
        escaped_query_text = _escape_lucene_query_text(query)

        result = self._retriever.search(
            query_text=escaped_query_text,
            query_vector=query_vector,
            top_k=top_k,
            query_params={
                "function_type": function_type or "",
                "boost": self.settings.function_type_boost,
            },
        )

        documents = [
            Document(page_content=item.content, metadata=dict(item.metadata or {}))
            for item in result.items
        ]

        self._logger.info(f"Ontology graph retrieval returned {len(documents)} documents")
        return documents


__all__: list[str] = ["Neo4jOntologyGraphRetrievalAdapter"]
