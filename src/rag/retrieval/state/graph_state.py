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

    # Generation fields
    generation: str
    is_rag_augmented: bool
    citations: List[dict]

    # Error handling
    error: str
