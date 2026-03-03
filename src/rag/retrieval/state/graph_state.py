"""
LangGraph State Schema

Defines the TypedDict state schema for RAG graph.
State persists across all graph nodes and edges.
"""

from typing import List, TypedDict

from langchain_core.documents import Document


class GraphState(TypedDict):
    """
    State schema for LangGraph RAG graph.

    Fields are updated by graph nodes as the query flows through
    the retrieval pipeline.
    """

    # Pipeline mode: "hybrid" (default), "llm-only", "rag-only"
    mode: str

    # Query fields
    query: str
    rewritten_query: str
    needs_retrieval: bool

    # Retrieval fields
    documents: List[Document]
    filtered_documents: List[Document]
    grading_scores: List[float]
    retrieval_succeeded: bool
    retrieval_attempts: int

    # Reranker fields (Phase 1.3)
    reranker_scores: List[float]  # Cross-encoder scores for all retrieved docs (before top-N selection)

    # Generation fields
    generation: str
    is_rag_augmented: bool
    citations: List[dict]
    llm_context: str

    # Error handling
    error: str
