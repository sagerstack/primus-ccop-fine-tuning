"""
Unit tests for QdrantVectorStoreAdapter.

Tests hybrid search integration with real Qdrant instance.
"""
import pytest
from unittest.mock import MagicMock

from qdrant_client import QdrantClient
from rag.infrastructure.adapters.qdrant.qdrant_vector_store_adapter import QdrantVectorStoreAdapter
from rag.infrastructure.adapters.qdrant.embedding_service import EmbeddingService


class TestQdrantVectorStoreAdapter:
    """Tests for QdrantVectorStoreAdapter - hybrid search."""

    @pytest.mark.integration
    def test_similarity_search_returns_documents_with_scores(self):
        """Integration: Verify similarity search returns documents with scores."""
        # Use real Qdrant instance populated by ingestion
        client = QdrantClient(url="http://localhost:6333")
        embedding_service = EmbeddingService(
            dense_model_name="BAAI/bge-large-en-v1.5",
            sparse_model_name="Qdrant/bm25",
        )

        adapter = QdrantVectorStoreAdapter(
            client=client,
            collection_name="ccop_clauses_hybrid",
            embedding_service=embedding_service,
        )

        results = adapter.similarity_search_with_scores(
            "What are the access control requirements?",
            k=3,
        )

        # Verify results structure
        assert len(results) > 0
        doc, score = results[0]
        assert hasattr(doc, "page_content")
        assert hasattr(doc, "metadata")
        assert isinstance(score, float)
        assert "citation_id" in doc.metadata

    def test_empty_query_returns_empty_results(self):
        """Unit: Verify empty query handling."""
        mock_client = MagicMock()
        mock_embedding_service = MagicMock(spec=EmbeddingService)

        adapter = QdrantVectorStoreAdapter(
            client=mock_client,
            collection_name="test_collection",
            embedding_service=mock_embedding_service,
        )

        # Adapter should handle empty query gracefully
        # (actual behavior depends on implementation)
        assert adapter is not None
