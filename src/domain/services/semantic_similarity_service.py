"""
Semantic Similarity Service using sentence embeddings.

Tier 2 scoring methodology for reasoning track benchmarks (B8, B9, B11, B15, B17, B18, B19).
Uses sentence transformers to compute semantic similarity instead of Jaccard word overlap.
"""

from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


class SemanticSimilarityService:
    """
    Semantic similarity using sentence embeddings.

    Implements Tier 2 scoring for reasoning track benchmarks.
    Uses all-MiniLM-L6-v2 model for efficient semantic similarity computation.
    Singleton pattern to cache model across evaluations.
    """

    _instance = None
    _model = None
    _model_name = None

    def __new__(cls, model_name: str = "all-MiniLM-L6-v2") -> "SemanticSimilarityService":
        """Singleton pattern for model caching."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """
        Initialize semantic similarity service.

        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2)
        """
        # Only initialize model once (singleton behavior)
        if self._model is None or self._model_name != model_name:
            self._model = SentenceTransformer(model_name)
            self._model_name = model_name

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        if not text1 or not text2:
            return 0.0

        embeddings = self._model.encode([text1, text2])
        similarity = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        # Clamp to [0, 1] range (cosine similarity can be negative for very dissimilar texts)
        return float(max(0.0, min(1.0, similarity)))

    def calculate_batch_similarity(
        self, expected: str, responses: List[str]
    ) -> List[float]:
        """
        Calculate similarity for multiple responses against expected.

        More efficient than calling calculate_similarity repeatedly
        as it batches encoding operations.

        Args:
            expected: Expected reference text
            responses: List of model responses to compare

        Returns:
            List of similarity scores (0.0 to 1.0)
        """
        if not expected or not responses:
            return [0.0] * len(responses)

        # Encode expected text once
        expected_embedding = self._model.encode(expected)

        # Batch encode all responses
        response_embeddings = self._model.encode(responses)

        # Calculate cosine similarity for each response
        similarities = [
            np.dot(expected_embedding, resp_emb) / (
                np.linalg.norm(expected_embedding) * np.linalg.norm(resp_emb)
            )
            for resp_emb in response_embeddings
        ]
        # Clamp to [0, 1] range (cosine similarity can be negative for very dissimilar texts)
        return [float(max(0.0, min(1.0, s))) for s in similarities]
