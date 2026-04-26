"""
LangGraph State Schema

Defines the TypedDict state schema for RAG graph.
State persists across all graph nodes and edges.
"""

from typing import Dict, List, TypedDict

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

    # Lab Exp #41 production-promoted fields:
    hyde_query: str  # gpt-4o-mini-generated hypothetical clause (used for retrieval embedding)
    dense_ranks: List[int]  # Original dense-retrieval rank for each retrieved doc
    rrf_scores: List[float]  # Reciprocal Rank Fusion combined score
    merged_groups: List[Dict]  # Parent-child merged sibling groups, if any

    # Generation fields
    generation: str
    is_rag_augmented: bool
    citations: List[dict]
    llm_context: str

    # I/O capture fields (Phase 3.1 — traceability)
    system_prompt: str
    user_prompt: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    retrieved_contexts_detailed: List[Dict]  # One entry per filtered doc with full metadata

    # Error handling
    error: str
