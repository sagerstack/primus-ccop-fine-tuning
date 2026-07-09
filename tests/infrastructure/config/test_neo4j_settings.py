"""
Unit tests for Neo4j + GraphRAG settings (Phase 9, plan 09-01).

Verifies the Neo4j connection settings and the two interceptable GraphRAG
infrastructure models (extraction = gpt-4o-mini via OpenRouter, D-06a;
embeddings = bge-large-en-v1.5 @ 1024-dim, D-07).

Defaults are asserted with env-file loading disabled (``_env_file=None``) and
the relevant ``CCOP_*`` environment variables cleared, so the tests pin the
Python field defaults in settings.py rather than whatever ``.env.example`` or a
developer's shell happens to carry.
"""

import pytest

from infrastructure.config.settings import Settings

# CCOP_* env vars that could otherwise shadow the field defaults under test.
_NEO4J_ENV_VARS = (
    "CCOP_NEO4J_URI",
    "CCOP_NEO4J_USER",
    "CCOP_NEO4J_PASSWORD",
    "CCOP_NEO4J_DATABASE",
    "CCOP_GRAPH_VECTOR_INDEX",
    "CCOP_GRAPH_EXTRACTION_MODEL",
    "CCOP_GRAPH_EMBEDDING_MODEL",
    "CCOP_GRAPH_EMBEDDING_DIMENSIONS",
)


@pytest.fixture
def default_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Settings instance with env-file loading disabled and Neo4j env vars cleared."""
    for var in _NEO4J_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    return Settings(_env_file=None)


class TestNeo4jConnectionSettings:
    """Neo4j connection defaults (D-01/D-12)."""

    def test_neo4j_uri_default(self, default_settings: Settings) -> None:
        assert default_settings.neo4j_uri == "bolt://localhost:7687"

    def test_neo4j_user_default(self, default_settings: Settings) -> None:
        assert default_settings.neo4j_user == "neo4j"

    def test_neo4j_database_default(self, default_settings: Settings) -> None:
        assert default_settings.neo4j_database == "neo4j"

    def test_neo4j_password_defaults_to_none(self, default_settings: Settings) -> None:
        """Password must never carry a committed literal — supplied via env only."""
        assert default_settings.neo4j_password is None

    def test_neo4j_password_reads_from_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When set, CCOP_NEO4J_PASSWORD flows into the setting."""
        monkeypatch.setenv("CCOP_NEO4J_PASSWORD", "s3cret-local")
        settings = Settings(_env_file=None)
        assert settings.neo4j_password == "s3cret-local"


class TestGraphModelSettings:
    """GraphRAG extraction/embedding model defaults (D-06a / D-07)."""

    def test_graph_extraction_model_default(self, default_settings: Settings) -> None:
        """Extraction LLM = gpt-4o-mini via OpenRouter (D-06a), interceptable seam."""
        assert default_settings.graph_extraction_model == "openai/gpt-4o-mini"

    def test_graph_embedding_model_default(self, default_settings: Settings) -> None:
        """Embeddings = bge-large-en-v1.5 (D-07), parity with hybrid's embedder."""
        assert default_settings.graph_embedding_model == "BAAI/bge-large-en-v1.5"

    def test_graph_embedding_dimensions_default(
        self, default_settings: Settings
    ) -> None:
        assert default_settings.graph_embedding_dimensions == 1024

    def test_graph_vector_index_name_default(self, default_settings: Settings) -> None:
        assert default_settings.graph_vector_index_name == "ccop_chunk_embeddings"
