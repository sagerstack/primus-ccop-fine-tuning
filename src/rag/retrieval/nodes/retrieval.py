"""
Retrieval Node

Queries Databricks Vector Search index with configurable top-k.
Retrieves relevant CCoP clauses with metadata and similarity scores.
"""

import logging
import os
from typing import Optional

from databricks_langchain import DatabricksVectorSearch

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)

# Module-level retriever (initialized once, reused across queries)
_retriever: Optional[DatabricksVectorSearch] = None


def _get_retriever() -> DatabricksVectorSearch:
    """
    Get or create Databricks Vector Search retriever.

    Retriever is created once and reused across queries for efficiency.

    Returns:
        DatabricksVectorSearch retriever configured for hybrid search
    """
    global _retriever

    if _retriever is None:
        settings = get_settings()

        # Validate Databricks configuration
        if not settings.databricks_host:
            raise ValueError(
                "CCOP_DATABRICKS_HOST not configured. Add to .env.local"
            )
        if not settings.databricks_token:
            raise ValueError(
                "CCOP_DATABRICKS_TOKEN not configured. Add to .env.local"
            )
        if not settings.databricks_vector_search_endpoint:
            raise ValueError(
                "CCOP_DATABRICKS_VECTOR_SEARCH_ENDPOINT not configured. Add to .env.local"
            )

        # Bridge CCOP-prefixed settings to standard Databricks env vars
        # (MLflow/Databricks SDK unified auth reads DATABRICKS_HOST/TOKEN)
        os.environ.setdefault("DATABRICKS_HOST", settings.databricks_host)
        os.environ.setdefault("DATABRICKS_TOKEN", settings.databricks_token)

        # Construct index name
        index_name = (
            f"{settings.databricks_catalog}."
            f"{settings.databricks_schema}."
            f"ccop_clauses_hybrid"
        )

        # Create vector store
        # Index uses Databricks-managed embeddings with source column 'text',
        # so we omit embedding and text_column params (index config handles both).
        _retriever = DatabricksVectorSearch(
            endpoint=settings.databricks_vector_search_endpoint,
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

    return _retriever


def retrieve_documents(state: GraphState) -> GraphState:
    """
    Retrieve documents from Databricks Vector Search with similarity scores.

    Uses similarity_search_with_relevance_scores() to capture scores in
    document metadata for downstream similarity-based filtering.

    Args:
        state: Current graph state with 'rewritten_query' field

    Returns:
        Updated state with 'documents' (including similarity_score in metadata)
        and incremented 'retrieval_attempts'
    """
    settings = get_settings()
    query = state.get("rewritten_query", state.get("query", ""))
    retrieval_attempts = state.get("retrieval_attempts", 0)
    top_k = settings.rag_retrieval_top_k

    logger.info(f"Retrieving documents (attempt {retrieval_attempts + 1}, k={top_k}): {query[:80]}...")

    try:
        # Get retriever (creates if first call)
        retriever = _get_retriever()

        # Use similarity_search_with_relevance_scores to get scores
        results = retriever.similarity_search_with_relevance_scores(
            query=query,
            k=top_k,
        )

        # Attach similarity score to each document's metadata
        documents = []
        for doc, score in results:
            doc.metadata["similarity_score"] = score
            documents.append(doc)

        state["documents"] = documents
        state["retrieval_attempts"] = retrieval_attempts + 1

        # Log retrieval results
        score_summary = ""
        if documents:
            scores = [d.metadata["similarity_score"] for d in documents]
            score_summary = (
                f" Scores: min={min(scores):.3f}, max={max(scores):.3f}, "
                f"avg={sum(scores)/len(scores):.3f}"
            )

        logger.info(
            f"Retrieved {len(documents)} documents.{score_summary} "
            f"Top 3 sources: {[doc.metadata.get('document_source', 'unknown') for doc in documents[:3]]}"
        )

    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        state["documents"] = []
        state["retrieval_attempts"] = retrieval_attempts + 1
        state["error"] = f"Retrieval error: {str(e)}"

    return state
