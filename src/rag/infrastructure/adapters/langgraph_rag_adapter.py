"""
LangGraph RAG Adapter

Concrete implementation of IRagPipeline using LangGraph.
Wraps the compiled LangGraph RAG graph.
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
        self.settings = settings
        self.logger = logger
        self._pipeline: Optional[Callable[[str, str], dict]] = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazily initialize the RAG pipeline."""
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

    async def query(self, question: str, mode: str = "hybrid") -> RagResponse:
        """
        Query the RAG pipeline.

        Args:
            question: User question
            mode: Pipeline mode — "hybrid", "llm-only", "rag-only"

        Returns:
            RagResponse with formatted response and citations
        """
        self._ensure_initialized()

        try:
            final_state = self._pipeline(question, mode)

            # Extract retrieved context text for RAGAs evaluation
            retrieved_contexts = [
                doc.page_content for doc in final_state.get("filtered_documents", [])
            ]

            response = RagResponse(
                response=final_state.get("generation", ""),
                raw_response=final_state.get("raw_generation", ""),
                is_rag_augmented=final_state.get("is_rag_augmented", False),
                citations=final_state.get("citations", []),
                retrieval_attempts=final_state.get("retrieval_attempts", 0),
                grading_scores=final_state.get("grading_scores", []),
                query=question,
                error=final_state.get("error"),
                retrieved_contexts=retrieved_contexts,
                # I/O capture fields (Phase 3.1 — traceability)
                system_prompt=final_state.get("system_prompt", ""),
                user_prompt=final_state.get("user_prompt", ""),
                prompt_tokens=final_state.get("prompt_tokens", 0),
                completion_tokens=final_state.get("completion_tokens", 0),
                total_tokens=final_state.get("total_tokens", 0),
                latency_ms=final_state.get("latency_ms", 0),
                retrieved_contexts_detailed=final_state.get("retrieved_contexts_detailed", []),
            )

            return response

        except Exception as e:
            self.logger.error(f"RAG query failed: {e}")

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

    async def is_available(self, mode: str = "hybrid") -> bool:
        """
        Check if RAG pipeline is operational for the given mode.

        llm-only requires only Ollama.
        hybrid and rag-only require vector store (Qdrant or Databricks) + Ollama.
        """
        has_ollama = bool(self.settings.ollama_host)
        if not has_ollama:
            self.logger.debug("Ollama not configured")
            return False

        if mode == "llm-only":
            return True

        # For hybrid/rag-only: check if any vector store is configured
        has_qdrant = bool(self.settings.qdrant_url)
        has_databricks = bool(
            self.settings.databricks_host
            and self.settings.databricks_token
            and self.settings.databricks_catalog
        )

        if not (has_qdrant or has_databricks):
            self.logger.debug("No vector store configured (Qdrant or Databricks)")
            return False

        return True
