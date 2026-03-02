"""
Qdrant Indexer Adapter

Implements IIndexer port for Qdrant collection creation and indexing operations.
Creates hybrid collections (dense + sparse) and indexes CCoP chunks.
"""

import logging
import uuid
from typing import Any, Dict, List

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    Modifier,
    PointStruct,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from rag.domain.ports.i_indexer import IIndexer
from rag.infrastructure.adapters.qdrant.embedding_service import EmbeddingService
from rag.ingestion.models import CcopChunk

logger = logging.getLogger(__name__)


class QdrantIndexerAdapter(IIndexer):
    """
    Qdrant implementation of IIndexer.

    Creates collections with dense (COSINE) + sparse (IDF) vectors.
    Indexes CCoP chunks with both vector types in batches.
    """

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        embedding_service: EmbeddingService,
    ):
        """
        Initialize Qdrant indexer adapter.

        Args:
            client: QdrantClient instance
            collection_name: Name of Qdrant collection to create/update
            embedding_service: Service for generating embeddings
        """
        self.client = client
        self.collection_name = collection_name
        self.embedding_service = embedding_service

    def index_chunks(self, chunks: List[CcopChunk]) -> str:
        """
        Index CCoP chunks into Qdrant collection.

        Creates collection with hybrid vector config (dense + sparse).
        For local dev, deletes and recreates collection to ensure clean state.

        Args:
            chunks: List of CcopChunk objects to index

        Returns:
            Collection name created
        """
        # Delete existing collection if it exists (local dev clean slate)
        if self.client.collection_exists(self.collection_name):
            logger.info(
                f"Deleting existing collection '{self.collection_name}' for fresh index"
            )
            self.client.delete_collection(self.collection_name)

        # Create collection with hybrid vector config
        logger.info(
            f"Creating collection '{self.collection_name}' with hybrid vectors "
            "(dense: 1024-dim COSINE, sparse: BM25 IDF)"
        )
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={"dense": VectorParams(size=1024, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams(modifier=Modifier.IDF)},
        )

        # Extract texts for batch embedding
        texts = [chunk.text for chunk in chunks]

        # Generate embeddings in batch
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        dense_embeddings = self.embedding_service.embed_documents(texts)
        sparse_embeddings = self.embedding_service.embed_sparse_batch(texts)

        # Build PointStruct objects
        points = []
        for i, chunk in enumerate(chunks):
            # Generate deterministic UUID from chunk.id
            point_id = uuid.uuid5(uuid.NAMESPACE_URL, chunk.id)

            # Build payload with all metadata fields + text
            payload = {
                "text": chunk.text,
                "chunk_id": chunk.id,
                "document_source": chunk.metadata.document_source,
                "section": chunk.metadata.section,
                "subsection": chunk.metadata.subsection,
                "clause": chunk.metadata.clause,
                "citation_id": chunk.metadata.citation_id,
                "document_type": chunk.metadata.document_type,
                "parent_path": chunk.metadata.parent_path,
                "chapter": chunk.metadata.chapter,
            }

            # Add page if present (optional field)
            if chunk.metadata.page is not None:
                payload["page"] = chunk.metadata.page

            # Create point with dense + sparse vectors
            point = PointStruct(
                id=str(point_id),  # Qdrant accepts UUID as string
                vector={
                    "dense": dense_embeddings[i],
                    "sparse": SparseVector(
                        indices=sparse_embeddings[i]["indices"],
                        values=sparse_embeddings[i]["values"],
                    ),
                },
                payload=payload,
            )
            points.append(point)

        # Upload in batches of 100
        batch_size = 100
        total_batches = (len(points) + batch_size - 1) // batch_size

        logger.info(f"Uploading {len(points)} points in {total_batches} batches...")
        for batch_idx in range(0, len(points), batch_size):
            batch = points[batch_idx : batch_idx + batch_size]
            batch_num = (batch_idx // batch_size) + 1
            logger.info(f"Uploading batch {batch_num}/{total_batches}...")
            self.client.upsert(
                collection_name=self.collection_name, points=batch, wait=True
            )

        logger.info(
            f"Indexing complete: {len(chunks)} chunks indexed to '{self.collection_name}'"
        )
        return self.collection_name

    def verify_index(self, index_name: str, sample_query: str) -> Dict[str, Any]:
        """
        Verify index integrity and search functionality.

        Args:
            index_name: Name of index/collection to verify
            sample_query: Sample query text for verification

        Returns:
            Dictionary with verification results:
                - collection_name: str - Collection name verified
                - point_count: int - Total points in collection
                - result_count: int - Number of results for sample query
                - results: List[Dict] - Sample results with citation_id, section, score
        """
        # Get collection info
        collection_info = self.client.get_collection(index_name)
        point_count = collection_info.points_count

        logger.info(f"Verifying collection '{index_name}' ({point_count} points)")

        # Run sample search
        dense_vector = self.embedding_service.embed_query(sample_query)
        sparse_dict = self.embedding_service.embed_sparse(sample_query)

        # Use query_points similar to QdrantVectorStoreAdapter
        from qdrant_client.models import Fusion, FusionQuery, Prefetch

        results = self.client.query_points(
            collection_name=index_name,
            prefetch=[
                Prefetch(query=dense_vector, using="dense", limit=10),
                Prefetch(
                    query=SparseVector(
                        indices=sparse_dict["indices"], values=sparse_dict["values"]
                    ),
                    using="sparse",
                    limit=10,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=5,  # Small sample for verification
            with_payload=True,
        )

        # Extract sample results
        sample_results = [
            {
                "citation_id": point.payload.get("citation_id", "unknown"),
                "section": point.payload.get("section", "unknown"),
                "score": point.score,
            }
            for point in results.points
        ]

        verification = {
            "collection_name": index_name,
            "point_count": point_count,
            "result_count": len(results.points),
            "results": sample_results,
        }

        logger.info(
            f"Verification complete: {verification['result_count']} results "
            f"for sample query '{sample_query[:50]}...'"
        )

        return verification
