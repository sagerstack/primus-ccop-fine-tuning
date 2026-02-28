"""
Vector Store Port (Interface)

Abstract interface for vector store retrieval operations.
Infrastructure layer provides concrete implementations (Qdrant, Databricks, etc.)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document


class IVectorStore(ABC):
    """
    Port for vector store retrieval operations.

    This abstraction enables swappable vector store implementations
    (Qdrant, Databricks, etc.) without changing application code.
    """

    @abstractmethod
    def similarity_search_with_scores(
        self, query: str, k: int = 10, filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Document, float]]:
        """
        Search for similar documents with relevance scores.

        Args:
            query: Query text to search for
            k: Number of results to return (default: 10)
            filter: Optional metadata filters (implementation-specific format)

        Returns:
            List of (document, similarity_score) tuples, sorted by relevance (descending)

        Raises:
            VectorStoreError: If search operation fails
        """
        pass
