"""
Unit tests for QdrantIndexerAdapter.

Tests collection creation and indexing integration.
"""
import pytest
from unittest.mock import MagicMock

from qdrant_client import QdrantClient
from rag.ingestion.models import CcopChunk, ChunkMetadata

from rag.infrastructure.adapters.qdrant.qdrant_indexer_adapter import QdrantIndexerAdapter
from rag.infrastructure.adapters.qdrant.embedding_service import EmbeddingService


class TestQdrantIndexerAdapter:
    """Tests for QdrantIndexerAdapter - indexing and collection management."""

    @pytest.mark.integration
    def test_verify_index_returns_stats(self):
        """Integration: Verify verify_index returns collection stats."""
        # Use real Qdrant instance populated by ingestion
        client = QdrantClient(url="http://localhost:6333")
        embedding_service = EmbeddingService(
            dense_model_name="BAAI/bge-large-en-v1.5",
            sparse_model_name="Qdrant/bm25",
        )

        adapter = QdrantIndexerAdapter(
            client=client,
            collection_name="ccop_clauses_hybrid",
            embedding_service=embedding_service,
        )

        stats = adapter.verify_index("ccop_clauses_hybrid", "test query")

        # Verify stats structure
        assert "collection_name" in stats
        assert "point_count" in stats
        assert "result_count" in stats
        assert "results" in stats
        assert stats["point_count"] > 0

    def test_adapter_initialization(self):
        """Unit: Verify adapter can be initialized."""
        mock_client = MagicMock()
        mock_embedding_service = MagicMock(spec=EmbeddingService)

        adapter = QdrantIndexerAdapter(
            client=mock_client,
            collection_name="test_collection",
            embedding_service=mock_embedding_service,
        )

        assert adapter is not None
        assert adapter.collection_name == "test_collection"
