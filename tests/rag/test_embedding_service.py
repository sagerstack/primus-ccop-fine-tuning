"""
Unit tests for EmbeddingService.

Tests embedding generation for both dense and sparse vectors,
including query prompt handling and lazy initialization.
"""
import pytest
from unittest.mock import MagicMock, patch

from rag.infrastructure.adapters.qdrant.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Tests for EmbeddingService - dense and sparse embedding generation."""

    @pytest.mark.integration
    def test_embed_query_returns_1024_dim_vector(self):
        """Integration: Verify query embedding returns 1024-dim vector."""
        service = EmbeddingService(
            dense_model_name="BAAI/bge-large-en-v1.5",
            sparse_model_name="Qdrant/bm25",
        )

        query = "What are the access control requirements?"
        embedding = service.embed_query(query)

        assert isinstance(embedding, list)
        assert len(embedding) == 1024
        assert all(isinstance(x, float) for x in embedding)


    @pytest.mark.integration
    def test_embed_documents_batch_returns_list(self):
        """Integration: Verify batch embedding returns list of vectors."""
        service = EmbeddingService(
            dense_model_name="BAAI/bge-large-en-v1.5",
            sparse_model_name="Qdrant/bm25",
        )

        docs = [
            "Access control requirements for CII",
            "Incident response procedures",
            "Network security controls",
        ]
        embeddings = service.embed_documents(docs)

        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(len(emb) == 1024 for emb in embeddings)

    @pytest.mark.integration
    def test_embed_sparse_returns_indices_and_values(self):
        """Integration: Verify sparse embedding returns correct format."""
        service = EmbeddingService(
            dense_model_name="BAAI/bge-large-en-v1.5",
            sparse_model_name="Qdrant/bm25",
        )

        text = "access control requirements"
        sparse = service.embed_sparse(text)

        assert isinstance(sparse, dict)
        assert "indices" in sparse
        assert "values" in sparse
        assert len(sparse["indices"]) == len(sparse["values"])
        assert all(isinstance(i, int) for i in sparse["indices"])
        assert all(isinstance(v, float) for v in sparse["values"])

    def test_lazy_initialization(self):
        """Unit: Verify models not loaded until first embed call."""
        service = EmbeddingService(
            dense_model_name="BAAI/bge-large-en-v1.5",
            sparse_model_name="Qdrant/bm25",
        )

        # Before any embed call, models should be None
        assert service._dense_model is None
        assert service._sparse_model is None
