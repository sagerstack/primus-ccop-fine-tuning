"""
LangGraph State Schema

Defines the TypedDict state schema for adaptive RAG graph.
State persists across all graph nodes and edges.
"""

from typing import List, TypedDict

from langchain_core.documents import Document


class GraphState(TypedDict):
    """
    State schema for LangGraph adaptive RAG graph.

    Fields are updated by graph nodes as the query flows through
    the retrieval pipeline. State is kept lightweight - stores
    document references, not full content where possible.
    """

    # Query fields
    query: str  # Original user query
    rewritten_query: str  # Query optimized for retrieval
    needs_retrieval: bool  # Whether query requires document retrieval

    # Retrieval fields
    documents: List[Document]  # Retrieved LangChain Document objects
    filtered_documents: List[Document]  # Documents that passed grading
    grading_scores: List[float]  # Per-document relevance scores
    retrieval_succeeded: bool  # Whether relevant documents were found
    retrieval_attempts: int  # Number of retrieval attempts (for loop detection)

    # Generation fields
    generation: str  # Generated response text
    is_rag_augmented: bool  # Whether response used RAG context
    citations: List[dict]  # Citation metadata from retrieved documents

    # Error handling
    error: str  # Error message if any node fails
