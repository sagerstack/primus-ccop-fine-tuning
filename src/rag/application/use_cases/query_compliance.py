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
    """

    def __init__(self, rag_pipeline: IRagPipeline, logger: ILogger):
        self.rag_pipeline = rag_pipeline
        self.logger = logger

    async def execute(self, question: str, mode: str = "hybrid") -> RagResponse:
        """
        Execute compliance query.

        Args:
            question: User question about CCoP compliance
            mode: Pipeline mode — "hybrid", "llm-only", "rag-only"

        Returns:
            RagResponse with formatted answer and citations

        Raises:
            ValueError: If question is empty
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        question = question.strip()

        self.logger.info(f"Executing compliance query (mode={mode}): {question[:100]}...")

        # Check if pipeline is available for this mode
        is_available = await self.rag_pipeline.is_available(mode)
        if not is_available:
            self.logger.warning(f"RAG pipeline not available for mode={mode}")
            return RagResponse(
                response=f"RAG pipeline not available for mode={mode}. Check configuration.",
                raw_response="",
                is_rag_augmented=False,
                citations=[],
                retrieval_attempts=0,
                grading_scores=[],
                query=question,
                error=f"RAG pipeline not configured or unavailable for mode={mode}",
            )

        try:
            response = await self.rag_pipeline.query(question, mode)

            self.logger.info(
                f"Query complete: mode={mode}, is_rag_augmented={response.is_rag_augmented}, "
                f"citations={len(response.citations)}, "
                f"retrieval_attempts={response.retrieval_attempts}"
            )

            return response

        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
