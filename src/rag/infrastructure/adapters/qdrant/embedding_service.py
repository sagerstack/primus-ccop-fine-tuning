"""
Embedding Service for Local RAG

Wraps sentence-transformers (dense embeddings) and FastEmbed (sparse embeddings)
for local embedding generation. Replaces Databricks managed BGE endpoint.
"""

import logging
import threading
from typing import Any, Dict, List

from fastembed import SparseTextEmbedding
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating dense and sparse embeddings locally.

    Uses sentence-transformers for dense embeddings (BAAI/bge-large-en-v1.5)
    and FastEmbed for sparse embeddings (BM25).

    Thread-safe lazy initialization - models are loaded on first use.
    """

    def __init__(
        self, dense_model_name: str, sparse_model_name: str, device: str = "auto"
    ):
        """
        Initialize embedding service.

        Args:
            dense_model_name: Dense embedding model (e.g., "BAAI/bge-large-en-v1.5")
            sparse_model_name: Sparse embedding model (e.g., "Qdrant/bm25")
            device: Device for dense model - "auto", "cuda", "mps", or "cpu"
                    Auto selects strongest available (CUDA > MPS > CPU)
        """
        self.dense_model_name = dense_model_name
        self.sparse_model_name = sparse_model_name
        self.device = device

        # Lazy initialization fields
        self._dense_model: SentenceTransformer | None = None
        self._sparse_model: SparseTextEmbedding | None = None
        self._dense_lock = threading.Lock()
        self._sparse_lock = threading.Lock()

    def _ensure_dense_model(self) -> SentenceTransformer:
        """
        Lazy initialization of dense embedding model (thread-safe).

        Returns:
            SentenceTransformer model instance
        """
        if self._dense_model is not None:
            return self._dense_model

        with self._dense_lock:
            # Double-checked locking
            if self._dense_model is not None:
                return self._dense_model

            logger.info(
                f"Loading dense embedding model: {self.dense_model_name} (device={self.device})"
            )
            self._dense_model = SentenceTransformer(
                self.dense_model_name, device=self.device
            )
            logger.info(
                f"Dense model loaded successfully (dimension={self.embedding_dimension})"
            )
            return self._dense_model

    def _ensure_sparse_model(self) -> SparseTextEmbedding:
        """
        Lazy initialization of sparse embedding model (thread-safe).

        Returns:
            SparseTextEmbedding model instance
        """
        if self._sparse_model is not None:
            return self._sparse_model

        with self._sparse_lock:
            # Double-checked locking
            if self._sparse_model is not None:
                return self._sparse_model

            logger.info(f"Loading sparse embedding model: {self.sparse_model_name}")
            self._sparse_model = SparseTextEmbedding(model_name=self.sparse_model_name)
            logger.info("Sparse model loaded successfully")
            return self._sparse_model

    def embed_query(self, text: str) -> List[float]:
        """
        Generate dense embedding for a query.

        Applies BGE query prompt for improved retrieval performance.

        Args:
            text: Query text

        Returns:
            Dense embedding vector (1024 dimensions, normalized)
        """
        model = self._ensure_dense_model()
        # BGE models perform best with this prompt for queries
        prompt = "Represent this sentence for searching relevant passages: "
        embedding = model.encode(
            prompt + text, normalize_embeddings=True, convert_to_numpy=True
        )
        return embedding.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate dense embeddings for documents (batch processing).

        Does NOT apply query prompt (documents should be embedded without it).

        Args:
            texts: List of document texts

        Returns:
            List of dense embedding vectors (1024 dimensions each, normalized)
        """
        model = self._ensure_dense_model()
        logger.debug(f"Embedding {len(texts)} documents in batch")
        embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True,  # Required for COSINE distance
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    def embed_sparse(self, text: str) -> Dict[str, Any]:
        """
        Generate sparse embedding (BM25) for a single text.

        Args:
            text: Query or document text

        Returns:
            Sparse vector as dict with "indices" and "values" keys
        """
        model = self._ensure_sparse_model()
        sparse_embeddings = list(model.embed([text]))
        sparse_emb = sparse_embeddings[0]

        # Convert to Qdrant sparse vector format
        return {
            "indices": sparse_emb.indices.tolist(),
            "values": sparse_emb.values.tolist(),
        }

    def embed_sparse_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Generate sparse embeddings (BM25) for multiple texts.

        Args:
            texts: List of query or document texts

        Returns:
            List of sparse vectors (each as dict with "indices" and "values")
        """
        model = self._ensure_sparse_model()
        logger.debug(f"Embedding {len(texts)} texts (sparse) in batch")
        sparse_embeddings = list(model.embed(texts))

        return [
            {"indices": emb.indices.tolist(), "values": emb.values.tolist()}
            for emb in sparse_embeddings
        ]

    @property
    def embedding_dimension(self) -> int:
        """
        Dense embedding dimension.

        Returns:
            1024 (bge-large-en-v1.5 dimension)
        """
        return 1024
