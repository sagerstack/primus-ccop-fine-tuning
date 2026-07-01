"""
Unit tests for Neo4jGraphRetrievalAdapter (Phase 9 Plan 04, Task 2).

All tests mock the neo4j-graphrag retriever / driver / embedder — no live
Neo4j connection is made here. See test_graph_retrieval_adapter_integration.py
for the live-Neo4j read-only counterpart.
"""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from rag.graph.retrieval.neo4j_graph_retrieval_adapter import (
    Neo4jGraphRetrievalAdapter,
)


def _make_settings(**overrides):
    settings = MagicMock()
    settings.neo4j_uri = "bolt://localhost:7687"
    settings.neo4j_user = "neo4j"
    settings.neo4j_password = "test-password"
    settings.neo4j_database = "neo4j"
    settings.graph_vector_index_name = "ccop_chunk_embeddings"
    settings.graph_embedding_model = "BAAI/bge-large-en-v1.5"
    settings.graph_embedding_dimensions = 1024
    for key, value in overrides.items():
        setattr(settings, key, value)
    return settings


class TestNeo4jGraphRetrievalAdapterRetrieve:
    """retrieve() maps neo4j-graphrag search results to hybrid-shaped Documents."""

    def test_retrieve_returns_documents_with_required_metadata_keys(self):
        mock_retriever = MagicMock()
        mock_result = MagicMock()
        mock_item_1 = MagicMock(
            content="Clause text about access control.",
            metadata={
                "citation_id": "chunk-12",
                "section": None,
                "document_source": "document.txt",
                "similarity_score": 0.87,
                "original_text": "Clause text about access control.",
            },
        )
        mock_result.items = [mock_item_1]
        mock_retriever.search.return_value = mock_result

        adapter = Neo4jGraphRetrievalAdapter(
            settings=_make_settings(),
            driver=MagicMock(),
            embedder=MagicMock(),
            retriever=mock_retriever,
        )

        docs = adapter.retrieve("What are the access control requirements?", top_k=3)

        assert len(docs) == 1
        doc = docs[0]
        assert isinstance(doc, Document)
        for key in (
            "citation_id",
            "section",
            "document_source",
            "similarity_score",
            "original_text",
        ):
            assert key in doc.metadata

        mock_retriever.search.assert_called_once_with(
            query_text="What are the access control requirements?", top_k=3
        )

    def test_retrieve_returns_empty_list_when_no_results(self):
        mock_retriever = MagicMock()
        mock_result = MagicMock()
        mock_result.items = []
        mock_retriever.search.return_value = mock_result

        adapter = Neo4jGraphRetrievalAdapter(
            settings=_make_settings(),
            driver=MagicMock(),
            embedder=MagicMock(),
            retriever=mock_retriever,
        )

        docs = adapter.retrieve("irrelevant query", top_k=5)

        assert docs == []


class TestNeo4jGraphRetrievalAdapterConstruction:
    """Construction wires bge embeddings + the configured vector index name."""

    @patch("rag.graph.retrieval.neo4j_graph_retrieval_adapter.VectorCypherRetriever")
    @patch("rag.graph.retrieval.neo4j_graph_retrieval_adapter.SentenceTransformerEmbeddings")
    def test_uses_configured_embedding_model_and_index(
        self, mock_embedder_cls, mock_retriever_cls
    ):
        settings = _make_settings()

        Neo4jGraphRetrievalAdapter(settings=settings, driver=MagicMock())

        mock_embedder_cls.assert_called_once_with(model=settings.graph_embedding_model)
        _, kwargs = mock_retriever_cls.call_args
        assert kwargs["index_name"] == settings.graph_vector_index_name
        assert kwargs["neo4j_database"] == settings.neo4j_database


class TestNeo4jGraphRetrievalAdapterCypherSafety:
    """T-09-12: retrieval_query is static/parameterized — never f-string'd with user text."""

    def test_retrieval_query_is_a_plain_static_string(self):
        assert isinstance(Neo4jGraphRetrievalAdapter.RETRIEVAL_QUERY, str)
        # No placeholder tokens that would imply runtime string interpolation
        # of user-controlled query text into the Cypher body.
        assert "{query" not in Neo4jGraphRetrievalAdapter.RETRIEVAL_QUERY
        assert "%s" not in Neo4jGraphRetrievalAdapter.RETRIEVAL_QUERY

    def test_retrieval_query_bounds_neighborhood_to_one_hop(self):
        # D-09/T-09-15: entity-anchored local retrieval, single-hop expansion,
        # no unbounded variable-length traversal (e.g. "*1..3" or "*..").
        query = Neo4jGraphRetrievalAdapter.RETRIEVAL_QUERY
        assert "*" not in query


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
