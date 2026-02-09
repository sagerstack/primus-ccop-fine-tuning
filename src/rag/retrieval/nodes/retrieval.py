"""
Retrieval Node

Queries Databricks Vector Search hybrid index with top-k=20.
Retrieves relevant CCoP clauses with metadata.
"""

import logging
from typing import Optional

from databricks_langchain import DatabricksVectorSearch
from databricks.vector_search.client import VectorSearchClient
from langchain_community.embeddings import DatabricksEmbeddings

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

        # Initialize clients
        vsc = VectorSearchClient(
            workspace_url=settings.databricks_host,
            personal_access_token=settings.databricks_token,
        )
        embeddings = DatabricksEmbeddings(
            endpoint=settings.databricks_embedding_endpoint,
            host=settings.databricks_host,
            token=settings.databricks_token,
        )

        # Construct index name
        index_name = (
            f"{settings.databricks_catalog}."
            f"{settings.databricks_schema}."
            f"ccop_clauses_hybrid"
        )

        # Create vector store
        _retriever = DatabricksVectorSearch(
            endpoint=vsc.get_endpoint(settings.databricks_vector_search_endpoint),
            index_name=index_name,
            text_column="text",
            embedding=embeddings,
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
    Retrieve documents from Databricks Vector Search.

    Uses hybrid search (dense + sparse via RRF) with top-k=20.
    Retrieves metadata columns for citation extraction.

    Args:
        state: Current graph state with 'rewritten_query' field

    Returns:
        Updated state with 'documents' and incremented 'retrieval_attempts'
    """
    query = state.get("rewritten_query", state.get("query", ""))
    retrieval_attempts = state.get("retrieval_attempts", 0)

    logger.info(f"Retrieving documents (attempt {retrieval_attempts + 1}): {query[:80]}...")

    try:
        # Get retriever (creates if first call)
        retriever = _get_retriever()

        # Convert to LangChain retriever with k=20
        langchain_retriever = retriever.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 20,  # Retrieve 20 candidates
            },
        )

        # Invoke retrieval
        documents = langchain_retriever.invoke(query)

        state["documents"] = documents
        state["retrieval_attempts"] = retrieval_attempts + 1

        # Log retrieval results
        logger.info(
            f"Retrieved {len(documents)} documents. "
            f"Top 3 sources: {[doc.metadata.get('document_source', 'unknown') for doc in documents[:3]]}"
        )

    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        state["documents"] = []
        state["retrieval_attempts"] = retrieval_attempts + 1
        state["error"] = f"Retrieval error: {str(e)}"

    return state
