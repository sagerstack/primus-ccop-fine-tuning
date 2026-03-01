"""
DI container tests for vector store adapter selection.

Tests that container selects correct adapter based on configuration.
"""
import pytest
from unittest.mock import patch, MagicMock

from infrastructure.config.container import get_container, Container
from infrastructure.config.settings import Settings
from rag.infrastructure.adapters.qdrant.qdrant_vector_store_adapter import QdrantVectorStoreAdapter
from rag.infrastructure.adapters.databricks.databricks_vector_store_adapter import DatabricksVectorStoreAdapter


class TestContainerVectorStore:
    """Tests for DI container adapter selection logic."""

    def test_container_selects_qdrant_when_qdrant_url_set(self):
        """Verify QdrantVectorStoreAdapter returned when qdrant_url configured."""
        # Patch get_settings to return test config
        with patch("infrastructure.config.settings.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.qdrant_url = "http://localhost:6333"
            mock_settings.qdrant_collection_name = "test_collection"
            mock_settings.qdrant_embedding_model = "BAAI/bge-large-en-v1.5"
            mock_settings.qdrant_sparse_model = "Qdrant/bm25"
            mock_settings.databricks_host = None
            mock_get_settings.return_value = mock_settings

            container = Container()
            vector_store = container.vector_store()

            assert isinstance(vector_store, QdrantVectorStoreAdapter)


    def test_container_prefers_qdrant_over_databricks(self):
        """Verify Qdrant selected when both Qdrant and Databricks configured."""
        with patch("infrastructure.config.settings.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.qdrant_url = "http://localhost:6333"
            mock_settings.qdrant_collection_name = "test_collection"
            mock_settings.qdrant_embedding_model = "BAAI/bge-large-en-v1.5"
            mock_settings.qdrant_sparse_model = "Qdrant/bm25"
            mock_settings.databricks_host = "https://test.databricks.com"
            mock_get_settings.return_value = mock_settings

            container = Container()
            vector_store = container.vector_store()

            # Should prefer Qdrant
            assert isinstance(vector_store, QdrantVectorStoreAdapter)
