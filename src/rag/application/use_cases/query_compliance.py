"""
Query Compliance Use Case

Orchestrates RAG pipeline query execution with validation and logging.
"""

import logging

from application.ports.output.i_logger import ILogger
from rag.application.ports.i_rag_pipeline import IRagPipeline, RagResponse


class QueryComplianceUseCase:
    """
    Use case for querying CCoP compliance information via RAG.

    Validates input, invokes RAG pipeline, and logs execution metadata.
    Follows same pattern as existing EvaluateModelUseCase.
    """

    def __init__(self, rag_pipeline: IRagPipeline, logger: ILogger):
        """
        Initialize use case.

        Args:
            rag_pipeline: RAG pipeline port implementation
            logger: Logger port implementation
        """
        self.rag_pipeline = rag_pipeline
        self.logger = logger

    async def execute(self, question: str) -> RagResponse:
        """
        Execute compliance query.

        Args:
            question: User question about CCoP compliance

        Returns:
            RagResponse with formatted answer and citations

        Raises:
            ValueError: If question is empty
            RagPipelineError: If query execution fails
        """
        # Validate input
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        question = question.strip()

        self.logger.info(f"Executing compliance query: {question[:100]}...")

        # Check if pipeline is available
        is_available = await self.rag_pipeline.is_available()
        if not is_available:
            self.logger.warning("RAG pipeline not available, check configuration")
            # Return error response instead of crashing
            return RagResponse(
                response="RAG pipeline not available. Please check Databricks and Ollama configuration.",
                raw_response="",
                is_rag_augmented=False,
                citations=[],
                retrieval_attempts=0,
                grading_scores=[],
                query=question,
                error="RAG pipeline not configured or unavailable",
            )

        # Execute query
        try:
            response = await self.rag_pipeline.query(question)

            # Log execution metadata
            self.logger.info(
                f"Query complete: is_rag_augmented={response.is_rag_augmented}, "
                f"citations={len(response.citations)}, "
                f"retrieval_attempts={response.retrieval_attempts}"
            )

            return response

        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
