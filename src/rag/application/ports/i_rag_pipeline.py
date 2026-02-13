"""
RAG Pipeline Port (Interface)

Abstract interface for RAG query operations.
Infrastructure layer will implement this for specific RAG systems (LangGraph, etc.)
"""

from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel, Field


class RagResponse(BaseModel):
    """
    Response from RAG pipeline.

    Contains formatted response, citations, and metadata about
    the RAG process (retrieval attempts, grading scores, etc.).
    """

    response: str = Field(
        description="Formatted response with end-of-response citations"
    )
    raw_response: str = Field(description="Raw LLM output with citation anchors")
    is_rag_augmented: bool = Field(
        description="Whether RAG context was used (vs model-only)"
    )
    citations: list[dict] = Field(
        default_factory=list, description="Resolved citation metadata"
    )
    retrieval_attempts: int = Field(
        default=0, description="Number of retrieval attempts made"
    )
    grading_scores: list[float] = Field(
        default_factory=list, description="Document relevance scores"
    )
    query: str = Field(description="Original query")
    error: Optional[str] = Field(default=None, description="Error message if any")


class IRagPipeline(ABC):
    """
    Port (interface) for RAG pipeline operations.

    This is an output port - the application depends on this abstraction,
    and the infrastructure provides concrete implementations.
    """

    @abstractmethod
    async def query(self, question: str, mode: str = "hybrid") -> RagResponse:
        """
        Query the RAG pipeline.

        Args:
            question: User question
            mode: Pipeline mode — "hybrid", "llm-only", "rag-only"

        Returns:
            RagResponse with formatted response and citations

        Raises:
            RagPipelineError: If query execution fails
        """
        pass

    @abstractmethod
    async def is_available(self, mode: str = "hybrid") -> bool:
        """
        Check if RAG pipeline is operational for the given mode.

        Args:
            mode: Pipeline mode — "hybrid", "llm-only", "rag-only"

        Returns:
            True if pipeline can accept queries in this mode
        """
        pass
