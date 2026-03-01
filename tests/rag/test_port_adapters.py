"""
Port contract tests.

Verifies that adapter implementations correctly implement port interfaces.
"""
import pytest

from rag.domain.ports.i_vector_store import IVectorStore
from rag.domain.ports.i_indexer import IIndexer
from rag.infrastructure.adapters.qdrant.qdrant_vector_store_adapter import QdrantVectorStoreAdapter
from rag.infrastructure.adapters.qdrant.qdrant_indexer_adapter import QdrantIndexerAdapter
from rag.infrastructure.adapters.databricks.databricks_vector_store_adapter import DatabricksVectorStoreAdapter
from rag.infrastructure.adapters.databricks.databricks_indexer_adapter import DatabricksIndexerAdapter


class TestPortContracts:
    """Contract tests verifying adapters implement port interfaces."""

    def test_qdrant_implements_ivectorstore(self):
        """Verify QdrantVectorStoreAdapter implements IVectorStore."""
        assert issubclass(QdrantVectorStoreAdapter, IVectorStore)

    def test_qdrant_implements_iindexer(self):
        """Verify QdrantIndexerAdapter implements IIndexer."""
        assert issubclass(QdrantIndexerAdapter, IIndexer)

    def test_databricks_implements_ivectorstore(self):
        """Verify DatabricksVectorStoreAdapter implements IVectorStore."""
        assert issubclass(DatabricksVectorStoreAdapter, IVectorStore)

    def test_databricks_implements_iindexer(self):
        """Verify DatabricksIndexerAdapter implements IIndexer."""
        assert issubclass(DatabricksIndexerAdapter, IIndexer)
