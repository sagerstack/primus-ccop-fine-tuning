"""
Unit tests for EmergentKGBuilder (Phase 9 — un-governed emergent KG baseline).

All neo4j-graphrag classes are mocked — these tests never touch the network
or a live Neo4j instance. Live-Neo4j validation lives in
tests/rag/graph/build/test_kg_builder_integration.py (@pytest.mark.integration).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from infrastructure.config.settings import Settings
from rag.graph.build.kg_builder import EmergentKGBuilder


def _settings() -> Settings:
    return Settings(
        CCOP_GRAPH_EXTRACTION_MODEL="openai/gpt-4o-mini",
        CCOP_OPENROUTER_BASE_URL="https://openrouter.ai/api/v1",
        CCOP_OPENROUTER_API_KEY="test-key",
        CCOP_GRAPH_EMBEDDING_MODEL="BAAI/bge-large-en-v1.5",
        CCOP_GRAPH_EMBEDDING_DIMENSIONS=1024,
        CCOP_GRAPH_VECTOR_INDEX="ccop_chunk_embeddings",
        CCOP_NEO4J_PASSWORD="test-pw",
    )


class TestEmergentKGBuilderConstruction:
    """Constructor wiring: LLM, embedder, vector index, pipeline — no schema."""

    def test_llm_configured_with_settings_model_and_base_url(self):
        with (
            patch("rag.graph.build.kg_builder.OpenAILLM") as mock_llm_cls,
            patch("rag.graph.build.kg_builder.SentenceTransformerEmbeddings"),
            patch("rag.graph.build.kg_builder.SimpleKGPipeline"),
            patch("rag.graph.build.kg_builder.create_vector_index"),
            patch("rag.graph.build.kg_builder.create_fulltext_index"),
        ):
            settings = _settings()
            EmergentKGBuilder(settings=settings, driver=MagicMock())

            mock_llm_cls.assert_called_once()
            _, kwargs = mock_llm_cls.call_args
            assert kwargs["model_name"] == settings.graph_extraction_model
            assert kwargs["base_url"] == settings.openrouter_base_url
            assert kwargs["api_key"] == settings.openrouter_api_key

    def test_embedder_configured_with_settings_model(self):
        with (
            patch("rag.graph.build.kg_builder.OpenAILLM"),
            patch("rag.graph.build.kg_builder.SentenceTransformerEmbeddings") as mock_emb_cls,
            patch("rag.graph.build.kg_builder.SimpleKGPipeline"),
            patch("rag.graph.build.kg_builder.create_vector_index"),
            patch("rag.graph.build.kg_builder.create_fulltext_index"),
        ):
            settings = _settings()
            EmergentKGBuilder(settings=settings, driver=MagicMock())

            mock_emb_cls.assert_called_once()
            _, kwargs = mock_emb_cls.call_args
            assert kwargs["model"] == settings.graph_embedding_model

    def test_vector_index_created_with_1024_cosine(self):
        with (
            patch("rag.graph.build.kg_builder.OpenAILLM"),
            patch("rag.graph.build.kg_builder.SentenceTransformerEmbeddings"),
            patch("rag.graph.build.kg_builder.SimpleKGPipeline"),
            patch("rag.graph.build.kg_builder.create_vector_index") as mock_index,
            patch("rag.graph.build.kg_builder.create_fulltext_index"),
        ):
            settings = _settings()
            EmergentKGBuilder(settings=settings, driver=MagicMock())

            mock_index.assert_called_once()
            _, kwargs = mock_index.call_args
            assert kwargs["dimensions"] == 1024
            assert kwargs["similarity_fn"] == "cosine"
            assert kwargs["label"] == "Chunk"
            assert kwargs["embedding_property"] == "embedding"

    def test_fulltext_index_created_over_chunk_text(self):
        """Wave-6 sparse leg: a Lucene fulltext index over Chunk.text, idempotent."""
        with (
            patch("rag.graph.build.kg_builder.OpenAILLM"),
            patch("rag.graph.build.kg_builder.SentenceTransformerEmbeddings"),
            patch("rag.graph.build.kg_builder.SimpleKGPipeline"),
            patch("rag.graph.build.kg_builder.create_vector_index"),
            patch("rag.graph.build.kg_builder.create_fulltext_index") as mock_ft,
        ):
            settings = _settings()
            EmergentKGBuilder(settings=settings, driver=MagicMock())

            mock_ft.assert_called_once()
            args, kwargs = mock_ft.call_args
            assert args[1] == settings.graph_fulltext_index_name
            assert kwargs["label"] == "Chunk"
            assert kwargs["node_properties"] == ["text"]
            # Idempotent — no-op when the index already exists (rebuilds + live graph).
            assert kwargs["fail_if_exists"] is False

    def test_pipeline_constructed_with_no_schema_kwargs(self):
        with (
            patch("rag.graph.build.kg_builder.OpenAILLM"),
            patch("rag.graph.build.kg_builder.SentenceTransformerEmbeddings"),
            patch("rag.graph.build.kg_builder.SimpleKGPipeline") as mock_pipeline_cls,
            patch("rag.graph.build.kg_builder.create_vector_index"),
            patch("rag.graph.build.kg_builder.create_fulltext_index"),
        ):
            settings = _settings()
            EmergentKGBuilder(settings=settings, driver=MagicMock())

            mock_pipeline_cls.assert_called_once()
            _, kwargs = mock_pipeline_cls.call_args
            assert "schema" not in kwargs
            assert "entities" not in kwargs
            assert "relations" not in kwargs
            assert kwargs["from_pdf"] is False

    def test_vector_index_already_exists_is_swallowed(self):
        with (
            patch("rag.graph.build.kg_builder.OpenAILLM"),
            patch("rag.graph.build.kg_builder.SentenceTransformerEmbeddings"),
            patch("rag.graph.build.kg_builder.SimpleKGPipeline"),
            patch("rag.graph.build.kg_builder.create_vector_index") as mock_index,
            patch("rag.graph.build.kg_builder.create_fulltext_index"),
        ):
            mock_index.side_effect = Exception("An equivalent index already exists")
            settings = _settings()

            # Should not raise.
            EmergentKGBuilder(settings=settings, driver=MagicMock())

    def test_vector_index_other_failure_is_raised(self):
        with (
            patch("rag.graph.build.kg_builder.OpenAILLM"),
            patch("rag.graph.build.kg_builder.SentenceTransformerEmbeddings"),
            patch("rag.graph.build.kg_builder.SimpleKGPipeline"),
            patch("rag.graph.build.kg_builder.create_vector_index") as mock_index,
            patch("rag.graph.build.kg_builder.create_fulltext_index"),
        ):
            mock_index.side_effect = RuntimeError("connection refused")
            settings = _settings()

            with pytest.raises(RuntimeError, match="connection refused"):
                EmergentKGBuilder(settings=settings, driver=MagicMock())


class TestEmergentKGBuilderBuild:
    """build() runs the pipeline per document and aggregates BuildStats."""

    def _driver_with_counts(self, count: int) -> MagicMock:
        driver = MagicMock()
        session = MagicMock()
        session.run.return_value.single.return_value = {"c": count}
        driver.session.return_value.__enter__.return_value = session
        return driver

    @pytest.mark.asyncio
    async def test_build_aggregates_stats_across_docs(self):
        with (
            patch("rag.graph.build.kg_builder.OpenAILLM"),
            patch("rag.graph.build.kg_builder.SentenceTransformerEmbeddings"),
            patch("rag.graph.build.kg_builder.SimpleKGPipeline") as mock_pipeline_cls,
            patch("rag.graph.build.kg_builder.create_vector_index"),
            patch("rag.graph.build.kg_builder.create_fulltext_index"),
        ):
            driver = self._driver_with_counts(5)
            pipeline_instance = mock_pipeline_cls.return_value
            pipeline_instance.run_async = AsyncMock(return_value=MagicMock())

            settings = _settings()
            builder = EmergentKGBuilder(settings=settings, driver=driver)

            stats = await builder.build({"doc1": "text one", "doc2": "text two"})

            assert stats.docs_processed == 2
            assert stats.failures == []
            assert pipeline_instance.run_async.call_count == 2
            assert stats.nodes_created == 5
            assert stats.relationships_created == 5
            # Provenance fix: each doc's name is passed as file_path so the
            # Document node's path is the real source (not "document.txt").
            call_kwargs = [c.kwargs for c in pipeline_instance.run_async.call_args_list]
            assert {c["file_path"] for c in call_kwargs} == {"doc1", "doc2"}
            for c in call_kwargs:
                assert c["text"] == ("text one" if c["file_path"] == "doc1" else "text two")

    @pytest.mark.asyncio
    async def test_build_records_failures_without_raising(self):
        with (
            patch("rag.graph.build.kg_builder.OpenAILLM"),
            patch("rag.graph.build.kg_builder.SentenceTransformerEmbeddings"),
            patch("rag.graph.build.kg_builder.SimpleKGPipeline") as mock_pipeline_cls,
            patch("rag.graph.build.kg_builder.create_vector_index"),
            patch("rag.graph.build.kg_builder.create_fulltext_index"),
        ):
            driver = self._driver_with_counts(0)
            pipeline_instance = mock_pipeline_cls.return_value
            pipeline_instance.run_async = AsyncMock(
                side_effect=RuntimeError("extraction failed")
            )

            settings = _settings()
            builder = EmergentKGBuilder(settings=settings, driver=driver)

            stats = await builder.build({"doc1": "text one"})

            assert stats.docs_processed == 0
            assert len(stats.failures) == 1
            assert "doc1" in stats.failures[0]
