"""
Qdrant Vector Store Adapter

Implements IVectorStore port for Qdrant hybrid search operations.
Uses dense (BGE) + sparse (BM25) vectors with RRF fusion.
"""

import logging
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import (
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    MatchValue,
    Prefetch,
    ScoredPoint,
    SparseVector,
)

from rag.domain.ports.i_vector_store import IVectorStore
from rag.infrastructure.adapters.qdrant.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class QdrantVectorStoreAdapter(IVectorStore):
    """
    Qdrant implementation of IVectorStore.

    Performs hybrid search (dense + sparse) with Reciprocal Rank Fusion.
    Returns LangChain Documents with similarity scores.
    """

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        embedding_service: EmbeddingService,
    ):
        """
        Initialize Qdrant vector store adapter.

        Args:
            client: QdrantClient instance
            collection_name: Name of Qdrant collection
            embedding_service: Service for generating embeddings
        """
        self.client = client
        self.collection_name = collection_name
        self.embedding_service = embedding_service

    def similarity_search_with_scores(
        self, query: str, k: int = 10, filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Document, float]]:
        """
        Search for similar documents with relevance scores.

        Uses hybrid search: dense (BGE) + sparse (BM25) with RRF fusion.

        Args:
            query: Query text to search for
            k: Number of results to return (default: 10)
            filter: Optional metadata filters (dict format)

        Returns:
            List of (document, similarity_score) tuples, sorted by relevance (descending)
        """
        # Generate embeddings
        dense_vector = self.embedding_service.embed_query(query)
        sparse_dict = self.embedding_service.embed_sparse(query)
        sparse_vector = SparseVector(
            indices=sparse_dict["indices"], values=sparse_dict["values"]
        )

        # Build metadata filter if provided
        query_filter = self._build_filter(filter) if filter else None

        # Log query
        query_preview = query[:80] + "..." if len(query) > 80 else query
        logger.info(f"Executing hybrid search for query: '{query_preview}'")
        if query_filter:
            logger.debug(f"Applied metadata filter: {filter}")

        # Execute hybrid search with prefetch + RRF
        results = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                Prefetch(query=dense_vector, using="dense", limit=k * 2),
                Prefetch(query=sparse_vector, using="sparse", limit=k * 2),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=k,
            query_filter=query_filter,
            with_payload=True,
            with_vectors=False,  # Don't return raw vectors
        )

        # Convert to LangChain Documents with scores
        documents_with_scores = [
            (self._to_document(point), point.score) for point in results.points
        ]

        # Log results
        if documents_with_scores:
            scores = [score for _, score in documents_with_scores]
            logger.info(
                f"Retrieved {len(documents_with_scores)} documents "
                f"(scores: {min(scores):.4f} - {max(scores):.4f})"
            )
        else:
            logger.warning("No documents found for query")

        return documents_with_scores

    def _build_filter(self, filter_dict: Dict[str, Any]) -> Filter:
        """
        Build Qdrant Filter from dict format.

        Args:
            filter_dict: Dict mapping metadata field names to match values

        Returns:
            Qdrant Filter object with FieldCondition entries
        """
        must_conditions = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in filter_dict.items()
        ]
        return Filter(must=must_conditions)

    def _to_document(self, point: ScoredPoint) -> Document:
        """
        Convert ScoredPoint to LangChain Document.

        Args:
            point: Qdrant ScoredPoint with payload

        Returns:
            LangChain Document with text and metadata
        """
        # Extract text from payload
        page_content = point.payload.get("text", "")

        # Extract metadata (all fields except text)
        metadata = {k: v for k, v in point.payload.items() if k != "text"}

        return Document(page_content=page_content, metadata=metadata)
