"""
DI container + settings tests for mode-aware graph retrieval provider
selection (Phase 10, plan 10-02 — closes RESEARCH Pitfall 3).

Verifies:
- container.graph_retrieval_provider_ontology() returns
  Neo4jOntologyGraphRetrievalAdapter when neo4j_uri is set (and the
  Phase 10 feature flag is enabled), None otherwise.
- container.graph_retrieval_provider() (Phase 9) is UNCHANGED — still returns
  Neo4jGraphRetrievalAdapter (D-16 additivity).
- All new Phase 10 settings fields load with documented defaults and read
  from CCOP_-prefixed env vars.

Provider override note: `container.config` is a `providers.Singleton(get_settings)`
bound to the real `get_settings` function object at container.py IMPORT time.
Patching `infrastructure.config.settings.get_settings` (or even
`infrastructure.config.container.get_settings`) after import does NOT change
what the already-constructed Singleton provider calls — it only rebinds a
module attribute the provider no longer looks up. The dependency_injector-
idiomatic override is `container.config.override(mock_settings)` /
`container.config.reset_override()`, used throughout this file.
"""

from unittest.mock import MagicMock, patch

import pytest

from infrastructure.config.container import Container
from infrastructure.config.settings import Settings
from rag.graph.retrieval.neo4j_graph_retrieval_adapter import (
    Neo4jGraphRetrievalAdapter,
)
from rag.graph.retrieval.neo4j_ontology_graph_retrieval_adapter import (
    Neo4jOntologyGraphRetrievalAdapter,
)


def _neo4j_settings_mock(neo4j_uri="bolt://localhost:7687", ontology_enabled=True):
    mock_settings = MagicMock()
    mock_settings.neo4j_uri = neo4j_uri
    mock_settings.neo4j_user = "neo4j"
    mock_settings.neo4j_password = "test"
    mock_settings.neo4j_database = "neo4j"
    mock_settings.graph_vector_index_name = "ccop_chunk_embeddings"
    mock_settings.graph_fulltext_index_name = "ccop_chunk_fulltext"
    mock_settings.graph_embedding_model = "BAAI/bge-large-en-v1.5"
    mock_settings.graphrag_ontology_enabled = ontology_enabled
    # Required by container.logger = providers.Selector(config.provided.log_format, ...)
    mock_settings.log_format = "console"
    mock_settings.log_level = "INFO"
    return mock_settings


@pytest.fixture
def container():
    """Fresh Container with config overridden per-test, always reset after."""
    c = Container()
    yield c
    c.config.reset_override()


class TestOntologyProviderSelection:
    """New Phase 10 mode-aware DI provider: graph_retrieval_provider_ontology."""

    def test_returns_ontology_adapter_when_neo4j_uri_set(self, container: Container):
        container.config.override(_neo4j_settings_mock())

        with (
            patch("neo4j.GraphDatabase.driver"),
            patch(
                "rag.graph.retrieval.neo4j_ontology_graph_retrieval_adapter.SentenceTransformerEmbeddings"
            ),
            patch(
                "rag.graph.retrieval.neo4j_ontology_graph_retrieval_adapter.HybridCypherRetriever"
            ),
        ):
            provider = container.graph_retrieval_provider_ontology()

        assert isinstance(provider, Neo4jOntologyGraphRetrievalAdapter)

    def test_returns_none_when_neo4j_uri_unset(self, container: Container):
        container.config.override(_neo4j_settings_mock(neo4j_uri=None))

        provider = container.graph_retrieval_provider_ontology()

        assert provider is None

    def test_returns_none_when_feature_flag_disabled(self, container: Container):
        container.config.override(_neo4j_settings_mock(ontology_enabled=False))

        provider = container.graph_retrieval_provider_ontology()

        assert provider is None


class TestPhase9ProviderAdditivity:
    """D-16: Phase 9's graph_retrieval_provider() must be byte-for-byte untouched."""

    def test_phase9_provider_still_returns_neo4j_graph_retrieval_adapter(
        self, container: Container
    ):
        container.config.override(_neo4j_settings_mock())

        with (
            patch("neo4j.GraphDatabase.driver"),
            patch(
                "rag.graph.retrieval.neo4j_graph_retrieval_adapter.SentenceTransformerEmbeddings"
            ),
            patch(
                "rag.graph.retrieval.neo4j_graph_retrieval_adapter.HybridCypherRetriever"
            ),
        ):
            provider = container.graph_retrieval_provider()

        assert isinstance(provider, Neo4jGraphRetrievalAdapter)


class TestPhase10OntologySettings:
    """Front-loaded Phase 10 settings fields (plan 10-02) — documented defaults."""

    _ENV_VARS = (
        "CCOP_ONTOLOGY_CONFIG_PATH",
        "CCOP_SHACL_SHAPES_PATH",
        "CCOP_ONTOLOGY_DISCOVERY_MODEL",
        "CCOP_FUNCTION_TYPE_BOOST",
        "CCOP_GLEANING_MAX_GLEANINGS",
        "CCOP_GRAPHRAG_ONTOLOGY_ENABLED",
    )

    @pytest.fixture
    def default_settings(self, monkeypatch: pytest.MonkeyPatch) -> Settings:
        for var in self._ENV_VARS:
            monkeypatch.delenv(var, raising=False)
        return Settings(_env_file=None)

    def test_ontology_config_path_default(self, default_settings: Settings) -> None:
        assert (
            default_settings.ontology_config_path
            == "src/rag/graph/ontology/ontology_config.json"
        )

    def test_shacl_shapes_path_default(self, default_settings: Settings) -> None:
        assert default_settings.shacl_shapes_path == "src/rag/graph/ontology/shapes.ttl"

    def test_ontology_discovery_model_default(self, default_settings: Settings) -> None:
        assert default_settings.ontology_discovery_model == "openai/gpt-4o-mini"

    def test_function_type_boost_default(self, default_settings: Settings) -> None:
        assert default_settings.function_type_boost == 1.5

    def test_gleaning_max_gleanings_default(self, default_settings: Settings) -> None:
        assert default_settings.gleaning_max_gleanings == 1

    def test_graphrag_ontology_enabled_default(self, default_settings: Settings) -> None:
        assert default_settings.graphrag_ontology_enabled is True

    def test_settings_read_ccop_prefixed_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for var in self._ENV_VARS:
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("CCOP_FUNCTION_TYPE_BOOST", "2.0")
        monkeypatch.setenv("CCOP_GRAPHRAG_ONTOLOGY_ENABLED", "false")
        settings = Settings(_env_file=None)
        assert settings.function_type_boost == 2.0
        assert settings.graphrag_ontology_enabled is False
