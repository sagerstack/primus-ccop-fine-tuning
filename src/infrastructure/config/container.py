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
from infrastructure.adapters.models.ollama_gateway import OllamaGateway
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

    # Model Gateway (defaults to Ollama, can be overridden with mock_mode=True)
    model_gateway = providers.Singleton(
        OllamaGateway,
        client=ollama_client,
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

    # Use Cases
    evaluate_model_use_case = providers.Factory(
        EvaluateModelUseCase,
        model_gateway=model_gateway,
        test_case_repository=test_case_repository,
        result_repository=result_repository,
        logger=logger,
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
