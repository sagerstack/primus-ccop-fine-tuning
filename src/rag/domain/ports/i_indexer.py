"""
Indexer Port (Interface)

Abstract interface for vector store indexing operations.
Infrastructure layer provides concrete implementations (Qdrant, Databricks, etc.)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from rag.ingestion.models import CcopChunk


class IIndexer(ABC):
    """
    Port for vector store indexing operations.

    This abstraction enables swappable indexer implementations
    (Qdrant, Databricks, etc.) without changing ingestion code.
    """

    @abstractmethod
    def index_chunks(self, chunks: List[CcopChunk]) -> str:
        """
        Index CCoP chunks into vector store.

        Args:
            chunks: List of CcopChunk objects to index

        Returns:
            Index/collection name created

        Raises:
            IndexerError: If indexing operation fails
        """
        pass

    @abstractmethod
    def verify_index(self, index_name: str, sample_query: str) -> Dict[str, Any]:
        """
        Verify index integrity and search functionality.

        Args:
            index_name: Name of index/collection to verify
            sample_query: Sample query text for verification

        Returns:
            Dictionary with verification results:
                - total_chunks: int - Total chunks in index
                - sample_results: int - Number of results for sample query
                - status: str - "healthy" or error description

        Raises:
            IndexerError: If verification fails
        """
        pass
