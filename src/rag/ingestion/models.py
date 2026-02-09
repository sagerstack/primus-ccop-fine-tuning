"""
RAG Ingestion Data Models

Pydantic models for CCoP document chunks and metadata.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """
    Metadata for a CCoP document chunk.

    Contains source information, section hierarchy, and citation details.
    """

    document_source: str = Field(
        description="Source document name (e.g., 'CCoP 2.0', 'Auditing Guidelines')"
    )
    section: str = Field(description="Section heading from document hierarchy")
    subsection: str = Field(default="", description="Subsection heading if present")
    clause: str = Field(default="", description="Clause number (e.g., '5.2.1')")
    citation_id: str = Field(
        description="Unique citation identifier (e.g., 'CCoP-2.0.5.5.2.1')"
    )
    page: Optional[int] = Field(default=None, description="Source page number")
    document_type: str = Field(
        default="primary", description="Document type: 'primary' or 'clarification'"
    )


class CcopChunk(BaseModel):
    """
    A chunk of CCoP document text with metadata.

    Represents a section-level semantic chunk from a CCoP document,
    enriched with metadata for retrieval and citation.
    """

    id: str = Field(description="Unique chunk identifier")
    text: str = Field(description="Chunk text content")
    metadata: ChunkMetadata = Field(description="Chunk metadata")


class QAPair(BaseModel):
    """
    A question-answer pair from RESPONSE-TO-FEEDBACK document.

    Represents official clarifications linked to CCoP clauses.
    """

    question: str = Field(description="Question text")
    answer: str = Field(description="Answer text")
    linked_clause: str = Field(
        default="", description="CCoP clause number this Q&A clarifies"
    )
    metadata: ChunkMetadata = Field(description="Q&A metadata")
