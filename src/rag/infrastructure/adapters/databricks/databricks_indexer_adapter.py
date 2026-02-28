"""
Databricks Indexer Adapter

Wraps existing DatabricksIndexer behind IIndexer port.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from rag.domain.ports.i_indexer import IIndexer
from rag.ingestion.models import CcopChunk

if TYPE_CHECKING:
    from infrastructure.config.settings import Settings
    from rag.ingestion.indexers.databricks_indexer import DatabricksIndexer

logger = logging.getLogger(__name__)


class DatabricksIndexerAdapter(IIndexer):
    """
    Databricks implementation of IIndexer.

    Wraps existing DatabricksIndexer with lazy initialization and
    delegates all indexing operations. This thin wrapper enables
    swappable indexer implementations without changing ingestion code.
    """

    def __init__(self, settings: "Settings"):
        """
        Initialize Databricks Indexer adapter.

        Args:
            settings: Application settings with Databricks configuration

        Note:
            Actual DatabricksIndexer is created lazily on first index_chunks call.
            This enables dry-run mode without Databricks credentials.
        """
        self.settings = settings
        self._indexer: Optional["DatabricksIndexer"] = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """
        Lazy initialization of DatabricksIndexer.

        Creates DatabricksIndexer instance, which handles its own config validation.
        Only called when index_chunks or verify_index is invoked.

        Raises:
            ValueError: If required Databricks settings are missing (raised by DatabricksIndexer)
        """
        if self._initialized:
            return

        # Import here to avoid circular dependency and deferred databricks SDK import
        from rag.ingestion.indexers.databricks_indexer import DatabricksIndexer

        # DatabricksIndexer validates its own config in __init__
        self._indexer = DatabricksIndexer(self.settings)
        self._initialized = True

        logger.info("Initialized DatabricksIndexer via adapter")

    def index_chunks(self, chunks: List[CcopChunk]) -> str:
        """
        Index CCoP chunks into Databricks Delta table and vector search index.

        Args:
            chunks: List of CcopChunk objects to index

        Returns:
            Index name created

        Raises:
            ValueError: If chunks empty or configuration invalid
            PermissionError: If insufficient Databricks permissions
            TimeoutError: If index creation times out
            RuntimeError: For other indexing failures
        """
        self._ensure_initialized()

        # Delegate to existing DatabricksIndexer
        # It orchestrates: table creation -> index creation -> wait -> verify
        index_name = self._indexer.index_chunks(chunks)

        return index_name

    def verify_index(self, index_name: str, sample_query: str) -> Dict[str, Any]:
        """
        Verify index integrity and search functionality.

        Args:
            index_name: Name of index to verify
            sample_query: Sample query text for verification

        Returns:
            Dictionary with verification results:
                - index_name: str - Index name
                - query: str - Sample query used
                - result_count: int - Number of results returned
                - results: List[Dict] - Sample results (up to 3)

        Raises:
            RuntimeError: If verification fails
        """
        self._ensure_initialized()

        # Delegate to existing DatabricksIndexer
        verification = self._indexer.verify_index(index_name, sample_query)

        return verification
