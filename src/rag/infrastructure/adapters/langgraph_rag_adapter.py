"""
LangGraph RAG Adapter

Concrete implementation of IRagPipeline using LangGraph.
Wraps the compiled LangGraph adaptive RAG graph.
"""

import logging
from typing import TYPE_CHECKING, Callable, Optional

from application.ports.output.i_logger import ILogger
from rag.application.ports.i_rag_pipeline import IRagPipeline, RagResponse
from rag.retrieval.graph import create_rag_pipeline

if TYPE_CHECKING:
    from infrastructure.config.settings import Settings


class LangGraphRagAdapter(IRagPipeline):
    """
    LangGraph implementation of IRagPipeline.

    Lazily initializes the RAG pipeline on first query to avoid
    startup errors when Databricks is not configured.
    """

    def __init__(self, settings: "Settings", logger: ILogger):
        """
        Initialize adapter.

        Args:
            settings: Application settings
            logger: Logger instance
        """
        self.settings = settings
        self.logger = logger
        self._pipeline: Optional[Callable[[str], dict]] = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """
        Lazily initialize the RAG pipeline.

        Only initializes on first use to avoid startup errors when
        Databricks is not configured.
        """
        if self._initialized:
            return

        try:
            self.logger.info("Initializing LangGraph RAG pipeline...")
            self._pipeline = create_rag_pipeline(self.settings)
            self._initialized = True
            self.logger.info("LangGraph RAG pipeline initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG pipeline: {e}")
            raise

    async def query(self, question: str) -> RagResponse:
        """
        Query the RAG pipeline.

        Args:
            question: User question

        Returns:
            RagResponse with formatted response and citations
        """
        # Ensure pipeline is initialized
        self._ensure_initialized()

        try:
            # Invoke graph pipeline
            final_state = self._pipeline(question)

            # Map graph state to RagResponse
            response = RagResponse(
                response=final_state.get("generation", ""),
                raw_response=final_state.get("raw_generation", ""),
                is_rag_augmented=final_state.get("is_rag_augmented", False),
                citations=final_state.get("citations", []),
                retrieval_attempts=final_state.get("retrieval_attempts", 0),
                grading_scores=final_state.get("grading_scores", []),
                query=question,
                error=final_state.get("error"),
            )

            return response

        except Exception as e:
            self.logger.error(f"RAG query failed: {e}")

            # Return error response instead of crashing
            return RagResponse(
                response=f"Error executing RAG query: {str(e)}",
                raw_response="",
                is_rag_augmented=False,
                citations=[],
                retrieval_attempts=0,
                grading_scores=[],
                query=question,
                error=str(e),
            )

    async def is_available(self) -> bool:
        """
        Check if RAG pipeline is operational.

        Returns:
            True if Databricks and Ollama are configured
        """
        # Check Databricks settings
        has_databricks = bool(
            self.settings.databricks_host
            and self.settings.databricks_token
            and self.settings.databricks_catalog
        )

        if not has_databricks:
            self.logger.debug("Databricks not configured")
            return False

        # Check Ollama settings
        has_ollama = bool(self.settings.ollama_host)

        if not has_ollama:
            self.logger.debug("Ollama not configured")
            return False

        return True
