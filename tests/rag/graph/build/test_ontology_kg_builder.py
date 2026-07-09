"""
Unit tests for OntologyKGBuilder (Phase 10 -- D-06/D-07/D-11 schema-constrained
KG builder).

All neo4j-graphrag pipeline construction is captured via an injectable
`runner_factory` seam (mirrors `test_kg_builder.py`'s `SimpleKGPipeline`
mock, but the runner itself is a factory function here -- see
`ontology_kg_builder.py`'s module docstring for why: `PipelineRunner.from_config`
eagerly builds a `Neo4jWriter` that queries the live driver for its server
version at CONSTRUCTION time, so a bare `MagicMock()` driver cannot be used
to build a real `PipelineRunner` in a unit test). These tests never touch the
network or a live Neo4j instance.

`TestOntologyKGPipelineConfigExtractor` tests `_get_extractor()`/`_get_resolver()`
directly against the REAL `_OntologyKGPipelineConfig` class (no factory mock)
using `MagicMock(spec=...)` driver/llm/embedder objects, which satisfy
neo4j-graphrag's pydantic `isinstance` validation without any network access --
this is the one place these tests exercise real neo4j-graphrag component
construction, proving the gleaning extractor + exact-match resolver are
ACTUALLY wired, not just passed as opaque arguments.

Live-Neo4j + live-LLM E2E validation lives in
tests/rag/graph/ontology/test_clause_linker.py (@pytest.mark.integration,
Task 2 -- seed -> build -> link chain).
"""
from unittest.mock import AsyncMock, MagicMock

import neo4j
import pytest
from neo4j_graphrag.embeddings.base import Embedder
from neo4j_graphrag.experimental.components.resolver import (
    SinglePropertyExactMatchResolver,
)
from neo4j_graphrag.llm import LLMInterface

from infrastructure.config.settings import Settings
from rag.graph.build.gleaning_extractor import GleaningEntityRelationExtractor
from rag.graph.build.ontology_kg_builder import (
    DEFAULT_ONTOLOGY_CONFIG_PATH,
    ONTOLOGY_EXTRACTION_PROMPT,
    OntologyKGBuilder,
    _OntologyKGPipelineConfig,
    load_locked_schema,
)
from rag.graph.build.section_aligned_splitter import SectionAlignedSplitter


def _settings(**overrides) -> Settings:
    defaults = dict(
        CCOP_GRAPH_EXTRACTION_MODEL="openai/gpt-4o-mini",
        CCOP_OPENROUTER_BASE_URL="https://openrouter.ai/api/v1",
        CCOP_OPENROUTER_API_KEY="test-key",
        CCOP_GRAPH_EMBEDDING_MODEL="BAAI/bge-large-en-v1.5",
        CCOP_GRAPH_EMBEDDING_DIMENSIONS=1024,
        CCOP_GRAPH_VECTOR_INDEX="ccop_chunk_embeddings",
        CCOP_NEO4J_PASSWORD="test-pw",
    )
    defaults.update(overrides)
    return Settings(**defaults)


def _mock_llm_factory(_settings: Settings) -> MagicMock:
    return MagicMock(spec=LLMInterface)


def _mock_embedder_factory(_settings: Settings) -> MagicMock:
    return MagicMock(spec=Embedder)


class _CapturingRunnerFactory:
    """Records the arguments OntologyKGBuilder passes to build its runner."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.runner = MagicMock()
        self.runner.run = AsyncMock(return_value=MagicMock())

    def __call__(self, llm, driver, embedder, schema, text_splitter, prompt_template, max_gleanings):
        self.calls.append(
            dict(
                llm=llm,
                driver=driver,
                embedder=embedder,
                schema=schema,
                text_splitter=text_splitter,
                prompt_template=prompt_template,
                max_gleanings=max_gleanings,
            )
        )
        return self.runner


def _driver_with_counts(count: int) -> MagicMock:
    driver = MagicMock(spec=neo4j.Driver)
    session = MagicMock()
    session.run.return_value.single.return_value = {"c": count}
    driver.session.return_value.__enter__.return_value = session
    return driver


class TestLoadLockedSchema:
    """Pure function: locked ontology_config.json -> GraphSchema-shaped dict."""

    def test_strict_mode_locks_vocabulary(self):
        schema = load_locked_schema(DEFAULT_ONTOLOGY_CONFIG_PATH, permissive=False)
        assert schema["additional_node_types"] is False
        assert schema["additional_relationship_types"] is False
        assert len(schema["node_types"]) == 24
        assert len(schema["relationship_types"]) == 48
        assert len(schema["patterns"]) == 9
        # patterns are 3-tuples, not lists (GraphSchema requires tuples)
        assert all(isinstance(p, tuple) and len(p) == 3 for p in schema["patterns"])

    def test_permissive_flag_flips_additional_types_true(self):
        """RESEARCH.md Pitfall 1 escape hatch -- iteration mode."""
        schema = load_locked_schema(DEFAULT_ONTOLOGY_CONFIG_PATH, permissive=True)
        assert schema["additional_node_types"] is True
        assert schema["additional_relationship_types"] is True

    def test_node_types_carry_real_locked_labels(self):
        schema = load_locked_schema(DEFAULT_ONTOLOGY_CONFIG_PATH, permissive=False)
        labels = {nt["label"] for nt in schema["node_types"]}
        # D-08 regulatory-structure layer must be present.
        assert {"Clause", "Control", "Obligation", "Definition"} <= labels
        # D-09 function-type tags must be present.
        assert {"ScopeClause", "ControlClause", "DefinitionClause"} <= labels


class TestOntologyExtractionPrompt:
    """D-07: canonical-name + ignore-illustrative-passages prompt content."""

    def test_prompt_ignores_illustrative_passages(self):
        assert "John Doe" in ONTOLOGY_EXTRACTION_PROMPT
        assert "illustrative" in ONTOLOGY_EXTRACTION_PROMPT.lower()
        assert "regulatory" in ONTOLOGY_EXTRACTION_PROMPT.lower()

    def test_prompt_requires_canonical_name(self):
        assert "canonical" in ONTOLOGY_EXTRACTION_PROMPT.lower()
        assert '"name"' in ONTOLOGY_EXTRACTION_PROMPT

    def test_prompt_preserves_required_placeholders(self):
        """LLMEntityRelationExtractor.extract_for_chunk .format()s exactly these three."""
        assert "{schema}" in ONTOLOGY_EXTRACTION_PROMPT
        assert "{examples}" in ONTOLOGY_EXTRACTION_PROMPT
        assert "{text}" in ONTOLOGY_EXTRACTION_PROMPT


class TestOntologyKGBuilderConstruction:
    """Constructor wiring: locked schema, custom prompt, splitter, gleaning -- via the runner_factory seam."""

    def test_locked_schema_passed_with_additional_node_types_false(self):
        factory = _CapturingRunnerFactory()
        settings = _settings()
        OntologyKGBuilder(
            settings=settings,
            driver=_driver_with_counts(0),
            llm_factory=_mock_llm_factory,
            embedder_factory=_mock_embedder_factory,
            runner_factory=factory,
        )

        assert len(factory.calls) == 1
        schema = factory.calls[0]["schema"]
        assert schema["additional_node_types"] is False
        assert schema["additional_relationship_types"] is False
        assert len(schema["node_types"]) == 24
        assert len(schema["relationship_types"]) == 48

    def test_permissive_toggle_flips_additional_node_types_true(self):
        """A --permissive build mode is available for iteration (Pitfall 1)."""
        factory = _CapturingRunnerFactory()
        settings = _settings()
        OntologyKGBuilder(
            settings=settings,
            driver=_driver_with_counts(0),
            llm_factory=_mock_llm_factory,
            embedder_factory=_mock_embedder_factory,
            runner_factory=factory,
            permissive=True,
        )

        schema = factory.calls[0]["schema"]
        assert schema["additional_node_types"] is True
        assert schema["additional_relationship_types"] is True

    def test_custom_prompt_template_passed_to_runner_factory(self):
        factory = _CapturingRunnerFactory()
        settings = _settings()
        OntologyKGBuilder(
            settings=settings,
            driver=_driver_with_counts(0),
            llm_factory=_mock_llm_factory,
            embedder_factory=_mock_embedder_factory,
            runner_factory=factory,
        )

        prompt = factory.calls[0]["prompt_template"]
        assert "John Doe" in prompt
        assert "canonical" in prompt.lower()

    def test_section_aligned_splitter_injected_not_default(self):
        factory = _CapturingRunnerFactory()
        settings = _settings()
        OntologyKGBuilder(
            settings=settings,
            driver=_driver_with_counts(0),
            llm_factory=_mock_llm_factory,
            embedder_factory=_mock_embedder_factory,
            runner_factory=factory,
        )

        splitter = factory.calls[0]["text_splitter"]
        assert isinstance(splitter, SectionAlignedSplitter)

    def test_gleaning_max_gleanings_defaults_to_settings(self):
        factory = _CapturingRunnerFactory()
        settings = _settings(gleaning_max_gleanings=2)
        OntologyKGBuilder(
            settings=settings,
            driver=_driver_with_counts(0),
            llm_factory=_mock_llm_factory,
            embedder_factory=_mock_embedder_factory,
            runner_factory=factory,
        )

        assert factory.calls[0]["max_gleanings"] == 2

    def test_gleaning_max_gleanings_explicit_override(self):
        factory = _CapturingRunnerFactory()
        settings = _settings(gleaning_max_gleanings=1)
        OntologyKGBuilder(
            settings=settings,
            driver=_driver_with_counts(0),
            llm_factory=_mock_llm_factory,
            embedder_factory=_mock_embedder_factory,
            runner_factory=factory,
            max_gleanings=5,
        )

        assert factory.calls[0]["max_gleanings"] == 5

    def test_vector_index_created_with_1024_cosine(self):
        with pytest.MonkeyPatch.context() as mp:
            mock_index = MagicMock()
            mp.setattr("rag.graph.build.ontology_kg_builder.create_vector_index", mock_index)
            mp.setattr("rag.graph.build.ontology_kg_builder.create_fulltext_index", MagicMock())

            settings = _settings()
            OntologyKGBuilder(
                settings=settings,
                driver=_driver_with_counts(0),
                llm_factory=_mock_llm_factory,
                embedder_factory=_mock_embedder_factory,
                runner_factory=_CapturingRunnerFactory(),
            )

            mock_index.assert_called_once()
            _, kwargs = mock_index.call_args
            assert kwargs["dimensions"] == 1024
            assert kwargs["similarity_fn"] == "cosine"
            assert kwargs["label"] == "Chunk"

    def test_vector_index_already_exists_is_swallowed(self):
        with pytest.MonkeyPatch.context() as mp:
            mock_index = MagicMock(side_effect=Exception("An equivalent index already exists"))
            mp.setattr("rag.graph.build.ontology_kg_builder.create_vector_index", mock_index)
            mp.setattr("rag.graph.build.ontology_kg_builder.create_fulltext_index", MagicMock())

            settings = _settings()
            # Should not raise.
            OntologyKGBuilder(
                settings=settings,
                driver=_driver_with_counts(0),
                llm_factory=_mock_llm_factory,
                embedder_factory=_mock_embedder_factory,
                runner_factory=_CapturingRunnerFactory(),
            )

    def test_vector_index_other_failure_is_raised(self):
        with pytest.MonkeyPatch.context() as mp:
            mock_index = MagicMock(side_effect=RuntimeError("connection refused"))
            mp.setattr("rag.graph.build.ontology_kg_builder.create_vector_index", mock_index)
            mp.setattr("rag.graph.build.ontology_kg_builder.create_fulltext_index", MagicMock())

            settings = _settings()
            with pytest.raises(RuntimeError, match="connection refused"):
                OntologyKGBuilder(
                    settings=settings,
                    driver=_driver_with_counts(0),
                    llm_factory=_mock_llm_factory,
                    embedder_factory=_mock_embedder_factory,
                    runner_factory=_CapturingRunnerFactory(),
                )


class TestOntologyKGBuilderBuild:
    """build() runs the runner per document, preserving provenance (file_path=doc_name)."""

    @pytest.mark.asyncio
    async def test_build_aggregates_stats_across_docs(self):
        factory = _CapturingRunnerFactory()
        driver = _driver_with_counts(5)
        settings = _settings()
        builder = OntologyKGBuilder(
            settings=settings,
            driver=driver,
            llm_factory=_mock_llm_factory,
            embedder_factory=_mock_embedder_factory,
            runner_factory=factory,
        )

        stats = await builder.build({"doc1": "text one", "doc2": "text two"})

        assert stats.docs_processed == 2
        assert stats.failures == []
        assert factory.runner.run.call_count == 2
        assert stats.nodes_created == 5
        assert stats.relationships_created == 5

        # Provenance fix: each doc's name is passed as file_path so the
        # Document node's path is the real source (not "document.txt").
        run_calls = [c.args[0] for c in factory.runner.run.call_args_list]
        assert {c["file_path"] for c in run_calls} == {"doc1", "doc2"}
        for c in run_calls:
            assert c["text"] == ("text one" if c["file_path"] == "doc1" else "text two")

    @pytest.mark.asyncio
    async def test_build_records_failures_without_raising(self):
        factory = _CapturingRunnerFactory()
        factory.runner.run = AsyncMock(side_effect=RuntimeError("extraction failed"))
        driver = _driver_with_counts(0)
        settings = _settings()
        builder = OntologyKGBuilder(
            settings=settings,
            driver=driver,
            llm_factory=_mock_llm_factory,
            embedder_factory=_mock_embedder_factory,
            runner_factory=factory,
        )

        stats = await builder.build({"doc1": "text one"})

        assert stats.docs_processed == 0
        assert len(stats.failures) == 1
        assert "doc1" in stats.failures[0]


class TestOntologyKGPipelineConfigExtractor:
    """
    Proves the gleaning extractor + exact-match resolver are ACTUALLY wired
    into the real neo4j-graphrag component graph -- exercises
    `_OntologyKGPipelineConfig` directly (no runner_factory mock), using
    `MagicMock(spec=...)` driver/llm/embedder (satisfies neo4j-graphrag's
    pydantic isinstance validation with zero network access).
    """

    def _config(self, max_gleanings: int = 3) -> _OntologyKGPipelineConfig:
        schema = load_locked_schema(DEFAULT_ONTOLOGY_CONFIG_PATH, permissive=False)
        config = _OntologyKGPipelineConfig.model_validate(
            dict(
                llm_config=MagicMock(spec=LLMInterface),
                neo4j_config=MagicMock(spec=neo4j.Driver),
                embedder_config=MagicMock(spec=Embedder),
                schema=schema,
                from_file=False,
                prompt_template=ONTOLOGY_EXTRACTION_PROMPT,
                perform_entity_resolution=True,
                max_gleanings=max_gleanings,
            )
        )
        # Populate _global_data the same way PipelineRunner.from_config's
        # .parse() call does, without touching the network (raw
        # llm/driver/embedder instances parse to themselves).
        config._global_data = config._parse_global_data()
        return config

    def test_get_extractor_returns_gleaning_extractor_not_default(self):
        config = self._config(max_gleanings=3)
        extractor = config._get_extractor()

        assert isinstance(extractor, GleaningEntityRelationExtractor)
        assert extractor.max_gleanings == 3

    def test_get_extractor_uses_configured_llm_and_prompt(self):
        config = self._config()
        extractor = config._get_extractor()

        assert extractor.llm is config.get_default_llm()
        assert "John Doe" in extractor.prompt_template.template

    def test_get_resolver_is_single_property_exact_match_on_name(self):
        """D-07 dedup: SimpleKGPipelineConfig's DEFAULT resolver already satisfies this."""
        config = self._config()
        resolver = config._get_resolver()

        assert isinstance(resolver, SinglePropertyExactMatchResolver)
        assert resolver.resolve_property == "name"
