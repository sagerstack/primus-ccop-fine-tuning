"""
Document Grading Node (Measurement-Only)

Phase 1.3: Refactored to measurement-only logger.
No longer filters documents or calls LLM for grading.
Logs reranker scores for observability, passes all documents through.
"""

import logging

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def grade_documents(state: GraphState) -> GraphState:
    """
    Grade retrieved documents (measurement-only).

    No filtering applied. Logs reranker scores for observability.
    All documents pass through to generation node.

    Args:
        state: Current graph state with 'documents' (already reranked top-N)

    Returns:
        Updated state with 'filtered_documents', 'grading_scores', 'retrieval_succeeded'
    """
    settings = get_settings()
    documents = state.get("documents", [])

    logger.info(f"Grading {len(documents)} retrieved documents (measurement-only)...")

    if not documents:
        state["filtered_documents"] = []
        state["grading_scores"] = []
        state["retrieval_succeeded"] = False
        logger.warning("No documents to grade")
        return state

    # Pass all documents through (no filtering)
    state["filtered_documents"] = documents
    state["retrieval_succeeded"] = len(documents) > 0

    # Log reranker scores for measurement
    grading_scores = []
    for i, doc in enumerate(documents, 1):
        reranker_score = doc.metadata.get("reranker_score", 0.0)
        citation_id = doc.metadata.get("citation_id", "unknown")
        content_preview = doc.page_content[:80].replace("\n", " ")

        grading_scores.append(reranker_score)

        logger.info(
            f"Document {i}/{len(documents)}: "
            f"citation_id={citation_id}, "
            f"reranker_score={reranker_score:.3f}, "
            f"preview={content_preview}..."
        )

    # Use reranker scores as grading scores for downstream compatibility
    state["grading_scores"] = grading_scores

    if grading_scores:
        avg_score = sum(grading_scores) / len(grading_scores)
        min_score = min(grading_scores)
        max_score = max(grading_scores)
        logger.info(
            f"Grading complete: {len(documents)} documents passed through "
            f"(scores: min={min_score:.3f}, max={max_score:.3f}, avg={avg_score:.3f})"
        )
    else:
        logger.info("Grading complete: 0 documents with scores")

    return state
