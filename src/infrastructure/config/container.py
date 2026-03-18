"""
Dependency Injection Container

Configures and wires all dependencies using dependency-injector.
"""

from dependency_injector import containers, providers

from application.use_cases.evaluate_model import EvaluateModelUseCase
from application.use_cases.generate_report import GenerateReportUseCase
from application.use_cases.setup_model import SetupModelUseCase
from infrastructure.adapters.converters.gguf_converter import GGUFConverter
from infrastructure.adapters.logging.console_logger import ConsoleLogger
from infrastructure.adapters.logging.structlog_adapter import StructlogAdapter
from infrastructure.adapters.models.mock_gateway import MockModelGateway
from infrastructure.adapters.models.claude_cli_gateway import ClaudeCliGateway
from infrastructure.adapters.models.ollama_gateway import OllamaGateway
from infrastructure.adapters.models.routing_gateway import RoutingModelGateway
from infrastructure.adapters.repositories.json_result_repository import JSONResultRepository
from infrastructure.adapters.repositories.jsonl_test_case_repository import (
    JSONLTestCaseRepository,
)
from infrastructure.config.settings import Settings, get_settings
from infrastructure.external.huggingface_client import HuggingFaceClient
from infrastructure.external.ollama_client import OllamaClient


class Container(containers.DeclarativeContainer):
    """
    Dependency injection container.

    Wires all dependencies and provides instances to the application.
    """

    # Configuration
    config = providers.Singleton(get_settings)

    # External Clients
    ollama_client = providers.Singleton(
        OllamaClient,
        host=config.provided.ollama_host,
        timeout=config.provided.ollama_timeout,
    )

    huggingface_client = providers.Singleton(
        HuggingFaceClient,
        cache_dir=config.provided.model_cache_dir,
    )

    # Logging
    logger = providers.Selector(
        config.provided.log_format,
        json=providers.Singleton(
            StructlogAdapter,
            log_level=config.provided.log_level,
            log_file=config.provided.log_file,
        ),
        console=providers.Singleton(
            ConsoleLogger,
            log_level=config.provided.log_level,
        ),
    )

    # Model Gateways (backend-specific)
    claude_gateway = providers.Singleton(
        ClaudeCliGateway,
        logger=logger,
        timeout=config.provided.claude_cli_timeout,
    )

    ollama_gateway = providers.Singleton(
        OllamaGateway,
        client=ollama_client,
        logger=logger,
    )

    # Routing Gateway: Claude models → claude CLI, everything else → Ollama
    model_gateway = providers.Singleton(
        RoutingModelGateway,
        claude_gateway=claude_gateway,
        ollama_gateway=ollama_gateway,
        logger=logger,
    )

    # Repositories
    test_case_repository = providers.Singleton(
        JSONLTestCaseRepository,
        test_cases_dir=config.provided.test_cases_dir,
        logger=logger,
    )

    result_repository = providers.Singleton(
        JSONResultRepository,
        results_dir=config.provided.results_dir,
        logger=logger,
    )

    # Model Converter
    model_converter = providers.Singleton(
        GGUFConverter,
        ollama_client=ollama_client,
        hf_client=huggingface_client,
        cache_dir=config.provided.model_cache_dir,
        logger=logger,
    )

    # RAGAs Evaluation Service (optional - only initialized if ragas_enabled)
    @staticmethod
    def _create_ragas_service(settings):
        """
        Create RagasEvaluationService if RAGAs is enabled.

        Returns None when ragas_enabled is False, preventing any RAGAs calls.
        """
        if not settings.ragas_enabled:
            return None

        from domain.services.ragas_evaluation_service import RagasEvaluationService

        return RagasEvaluationService(
            model_name=settings.ragas_evaluator_model,
            embedding_model=settings.ragas_embedding_model,
            api_key=settings.ragas_api_key,
            api_base_url=settings.ragas_api_base_url,
        )

    ragas_service = providers.Singleton(
        _create_ragas_service,
        settings=config,
    )

    # RAG Pipeline (for query and evaluation)
    @staticmethod
    def _create_rag_adapter(settings, logger):
        from rag.infrastructure.adapters.langgraph_rag_adapter import (
            LangGraphRagAdapter,
        )

        return LangGraphRagAdapter(settings=settings, logger=logger)

    rag_pipeline = providers.Singleton(
        _create_rag_adapter,
        settings=config,
        logger=logger,
    )

    # Use Cases
    evaluate_model_use_case = providers.Factory(
        EvaluateModelUseCase,
        model_gateway=model_gateway,
        test_case_repository=test_case_repository,
        result_repository=result_repository,
        logger=logger,
        ragas_service=ragas_service,
        rag_pipeline=rag_pipeline,
    )

    setup_model_use_case = providers.Factory(
        SetupModelUseCase,
        model_converter=model_converter,
        model_gateway=model_gateway,
        logger=logger,
    )

    generate_report_use_case = providers.Factory(
        GenerateReportUseCase,
        result_repository=result_repository,
        logger=logger,
    )

    # RAG Pipeline (optional - only initialized if Databricks configured)
    # Lazy factory functions to avoid circular dependency:
    # RAG modules import Settings → triggers container → imports RAG (cycle).
    # Factory does import + construction in one call, deferred until first use.
    @staticmethod
    def _create_vector_store_adapter(settings, logger):
        """
        Create vector store adapter based on configuration.

        Selection logic:
        - If qdrant_url is set: create QdrantVectorStoreAdapter
        - Elif databricks_host is set: create DatabricksVectorStoreAdapter
        - Else: return None (no vector store configured)
        """
        if settings.qdrant_url:
            from qdrant_client import QdrantClient
            from rag.infrastructure.adapters.qdrant.embedding_service import (
                EmbeddingService,
            )
            from rag.infrastructure.adapters.qdrant.qdrant_vector_store_adapter import (
                QdrantVectorStoreAdapter,
            )

            client = QdrantClient(url=settings.qdrant_url)
            embedding_service = EmbeddingService(
                dense_model_name=settings.qdrant_embedding_model,
                sparse_model_name=settings.qdrant_sparse_model,
            )
            logger.info(f"Initialized QdrantVectorStoreAdapter (collection: {settings.qdrant_collection_name})")
            return QdrantVectorStoreAdapter(
                client=client,
                collection_name=settings.qdrant_collection_name,
                embedding_service=embedding_service,
            )
        elif settings.databricks_host:
            from rag.infrastructure.adapters.databricks.databricks_vector_store_adapter import (
                DatabricksVectorStoreAdapter,
            )

            logger.info("Initialized DatabricksVectorStoreAdapter")
            return DatabricksVectorStoreAdapter(settings=settings)
        else:
            logger.warning("No vector store configured (neither Qdrant nor Databricks)")
            return None

    @staticmethod
    def _create_indexer_adapter(settings, logger):
        """
        Create indexer adapter based on configuration.

        Selection logic:
        - If qdrant_url is set: create QdrantIndexerAdapter
        - Elif databricks_host is set: create DatabricksIndexerAdapter
        - Else: return None (no indexer configured)
        """
        if settings.qdrant_url:
            from qdrant_client import QdrantClient
            from rag.infrastructure.adapters.qdrant.embedding_service import (
                EmbeddingService,
            )
            from rag.infrastructure.adapters.qdrant.qdrant_indexer_adapter import (
                QdrantIndexerAdapter,
            )

            client = QdrantClient(url=settings.qdrant_url)
            embedding_service = EmbeddingService(
                dense_model_name=settings.qdrant_embedding_model,
                sparse_model_name=settings.qdrant_sparse_model,
            )
            logger.info(f"Initialized QdrantIndexerAdapter (collection: {settings.qdrant_collection_name})")
            return QdrantIndexerAdapter(
                client=client,
                collection_name=settings.qdrant_collection_name,
                embedding_service=embedding_service,
            )
        elif settings.databricks_host:
            from rag.infrastructure.adapters.databricks.databricks_indexer_adapter import (
                DatabricksIndexerAdapter,
            )

            logger.info("Initialized DatabricksIndexerAdapter")
            return DatabricksIndexerAdapter(settings=settings)
        else:
            logger.warning("No indexer configured (neither Qdrant nor Databricks)")
            return None

    @staticmethod
    def _create_query_use_case(rag_pipeline, logger):
        from rag.application.use_cases.query_compliance import QueryComplianceUseCase

        return QueryComplianceUseCase(rag_pipeline=rag_pipeline, logger=logger)

    vector_store = providers.Singleton(
        _create_vector_store_adapter,
        settings=config,
        logger=logger,
    )

    indexer = providers.Singleton(
        _create_indexer_adapter,
        settings=config,
        logger=logger,
    )

    query_compliance_use_case = providers.Factory(
        _create_query_use_case,
        rag_pipeline=rag_pipeline,
        logger=logger,
    )


# Global container instance
_container: Container | None = None


def get_container() -> Container:
    """
    Get global container instance.

    Returns:
        Container instance (singleton)
    """
    global _container
    if _container is None:
        _container = Container()
    return _container
