"""
Databricks Vector Store Adapter

Wraps existing DatabricksVectorSearch retriever behind IVectorStore port.
"""

import logging
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from databricks_langchain import DatabricksVectorSearch
from langchain_core.documents import Document

from rag.domain.ports.i_vector_store import IVectorStore

if TYPE_CHECKING:
    from infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


class DatabricksVectorStoreAdapter(IVectorStore):
    """
    Databricks implementation of IVectorStore.

    Wraps existing DatabricksVectorSearch retriever with lazy initialization
    and graceful config validation. Delegates to the same retriever code
    used in src/rag/retrieval/nodes/retrieval.py.
    """

    def __init__(self, settings: "Settings"):
        """
        Initialize Databricks Vector Store adapter.

        Args:
            settings: Application settings with Databricks configuration

        Note:
            Actual retriever is created lazily on first similarity_search_with_scores call.
            This enables dry-run mode without Databricks credentials.
        """
        self.settings = settings
        self._retriever: Optional[DatabricksVectorSearch] = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """
        Lazy initialization of Databricks Vector Search retriever.

        Validates configuration and creates DatabricksVectorSearch instance.
        Only called when similarity_search_with_scores is invoked.

        Raises:
            ValueError: If required Databricks settings are missing
        """
        if self._initialized:
            return

        # Validate Databricks configuration
        if not self.settings.databricks_host:
            raise ValueError(
                "CCOP_DATABRICKS_HOST not configured. Add to .env.local"
            )
        if not self.settings.databricks_token:
            raise ValueError(
                "CCOP_DATABRICKS_TOKEN not configured. Add to .env.local"
            )
        if not self.settings.databricks_vector_search_endpoint:
            raise ValueError(
                "CCOP_DATABRICKS_VECTOR_SEARCH_ENDPOINT not configured. Add to .env.local"
            )

        # Bridge CCOP-prefixed settings to standard Databricks env vars
        # (MLflow/Databricks SDK unified auth reads DATABRICKS_HOST/TOKEN)
        os.environ.setdefault("DATABRICKS_HOST", self.settings.databricks_host)
        os.environ.setdefault("DATABRICKS_TOKEN", self.settings.databricks_token)

        # Construct index name
        index_name = (
            f"{self.settings.databricks_catalog}."
            f"{self.settings.databricks_schema}."
            f"ccop_clauses_hybrid"
        )

        # Create vector store
        # Index uses Databricks-managed embeddings with source column 'text',
        # so we omit embedding and text_column params (index config handles both).
        self._retriever = DatabricksVectorSearch(
            endpoint=self.settings.databricks_vector_search_endpoint,
            index_name=index_name,
            columns=[
                "document_source",
                "section",
                "subsection",
                "clause",
                "citation_id",
                "document_type",
            ],
        )

        logger.info(f"Initialized Databricks Vector Search retriever: {index_name}")
        self._initialized = True

    def similarity_search_with_scores(
        self, query: str, k: int = 10, filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Document, float]]:
        """
        Search for similar documents with relevance scores.

        Args:
            query: Query text to search for
            k: Number of results to return (default: 10)
            filter: Optional metadata filters (logged as warning - Databricks
                   handles filtering differently through index config)

        Returns:
            List of (document, similarity_score) tuples, sorted by relevance (descending)

        Raises:
            ValueError: If Databricks configuration is invalid
            Exception: If search operation fails
        """
        self._ensure_initialized()

        if filter:
            logger.warning(
                "Filter parameter provided but not used. Databricks Vector Search "
                "handles filtering through index configuration, not at query time."
            )

        # Delegate to existing Databricks retriever
        # similarity_search_with_relevance_scores returns List[tuple[Document, float]]
        results = self._retriever.similarity_search_with_relevance_scores(
            query=query,
            k=k,
        )

        return results
