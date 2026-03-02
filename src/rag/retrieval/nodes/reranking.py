"""
Reranking Node

Cross-encoder reranking for retrieved documents (Phase 1.3).
Re-scores bi-encoder results and selects top-N for LLM context.
"""

import logging
import threading
from typing import Optional

import numpy as np

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)

# Lazy singleton for cross-encoder model (same pattern as EmbeddingService)
_cross_encoder: Optional[object] = None
_cross_encoder_lock = threading.Lock()


def _get_cross_encoder(model_name: str):
    """
    Get or create cross-encoder model (thread-safe lazy initialization).

    Args:
        model_name: HuggingFace model ID (e.g., cross-encoder/ms-marco-MiniLM-L12-v2)

    Returns:
        CrossEncoder model instance
    """
    global _cross_encoder
    if _cross_encoder is None:
        with _cross_encoder_lock:
            if _cross_encoder is None:
                logger.info(f"Loading cross-encoder model: {model_name}")
                from sentence_transformers import CrossEncoder
                _cross_encoder = CrossEncoder(model_name)
                logger.info("Cross-encoder model loaded successfully")
    return _cross_encoder


def rerank_documents(state: GraphState) -> GraphState:
    """
    Rerank retrieved documents using cross-encoder.

    Scores query-document pairs and keeps top-N based on rerank_top_n setting.
    Cross-encoder scores are logits (unbounded, NOT 0-1 normalized).

    Args:
        state: Current graph state with 'documents' and 'rewritten_query'

    Returns:
        Updated state with reranked 'documents' and 'reranker_scores'
    """
    settings = get_settings()
    documents = state.get("documents", [])
    query = state.get("rewritten_query", state.get("query", ""))

    logger.info(f"Reranking {len(documents)} documents with cross-encoder...")

    if not documents:
        state["reranker_scores"] = []
        logger.warning("No documents to rerank")
        return state

    # Load cross-encoder model (lazy, thread-safe)
    model = _get_cross_encoder(settings.cross_encoder_model)

    # Build query-document pairs for scoring
    pairs = [(query, doc.page_content) for doc in documents]

    # Score pairs (returns numpy array of logits)
    scores = model.predict(pairs)

    # Convert to Python floats for JSON serialization
    scores_list = [float(s) for s in scores]

    # Attach scores to document metadata
    for doc, score in zip(documents, scores_list):
        doc.metadata["reranker_score"] = score

    # Sort by score descending
    scored_docs = list(zip(documents, scores_list))
    scored_docs.sort(key=lambda x: x[1], reverse=True)

    # Keep top-N
    top_n = settings.rerank_top_n
    top_docs = [doc for doc, _ in scored_docs[:top_n]]

    # Log reranking results
    if scores_list:
        score_min = min(scores_list)
        score_max = max(scores_list)
        score_mean = np.mean(scores_list)
        logger.info(
            f"Reranking complete: {len(documents)} -> {len(top_docs)} docs "
            f"(score range: [{score_min:.3f}, {score_max:.3f}], mean={score_mean:.3f})"
        )

        # Log which citation_ids made it to top-N
        top_citation_ids = [doc.metadata.get("citation_id", "unknown") for doc in top_docs]
        logger.info(f"Top-{top_n} citation_ids: {top_citation_ids}")
    else:
        logger.warning("No scores generated during reranking")

    # Update state
    state["documents"] = top_docs  # Reranked top-N documents
    state["reranker_scores"] = scores_list  # ALL scores for logging

    return state
