"""
Unit tests for ClauseHitHarnessUseCase (Phase 10, plan 10-10, D-15).

Mocks `ITestCaseRepository`, `IGraphRetrievalProvider`, and
`gold_relation_parser.parse_gold_relations` — no live Neo4j connection or
xlsx file is read here. The live-Neo4j B01-001 containment check is a
separate `@pytest.mark.integration` test at the bottom of this file
(mirrors the plan's Task 2 behavior spec's third bullet).
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.documents import Document

from application.use_cases.clause_hit_harness import (
    FIXED_18_TEST_IDS,
    ClauseHitHarnessUseCase,
)
from rag.graph.ontology.gold_relation_parser import CaseGoldRelations


def _test_case(test_id: str, question: str, clause_reference: list[str]):
    tc = MagicMock()
    tc.test_id = test_id
    tc.question = question
    tc.metadata = {"clause_reference": clause_reference}
    return tc


def _doc(citation_id: str, score: float):
    return Document(
        page_content=f"Clause text for {citation_id}",
        metadata={"citation_id": citation_id, "similarity_score": score},
    )


def _repo(test_cases: list) -> AsyncMock:
    repo = AsyncMock()
    repo.load_by_ids.return_value = test_cases
    return repo


def _harness(
    repo,
    provider,
    gold_cases: list[CaseGoldRelations] | None = None,
    pool_size: int = 50,
) -> ClauseHitHarnessUseCase:
    harness = ClauseHitHarnessUseCase(
        test_case_repository=repo,
        graph_retrieval_provider=provider,
        gold_xlsx_path="unused-in-mocked-tests.xlsx",
        pool_size=pool_size,
    )
    if gold_cases is not None:
        harness._load_gold_relations = MagicMock(
            return_value={c.test_id: c for c in gold_cases}
        )
    return harness


class TestClauseHitHarnessScoring:
    """Harness runs the GT cases through the retrieval provider and scores them."""

    @pytest.mark.asyncio
    async def test_single_case_hit_and_recall(self):
        tc = _test_case("B01-001", "digital boundary question", ["1.2.1"])
        provider = MagicMock()
        provider.retrieve.return_value = [
            _doc("5.6", 1.0),
            _doc("1.2.1", 1.0),
            _doc("9.9", 0.5),
        ]
        harness = _harness(_repo([tc]), provider, gold_cases=[])

        result = await harness.execute(test_ids=["B01-001"])

        assert len(result.per_case) == 1
        case = result.per_case[0]
        assert case.test_id == "B01-001"
        assert case.gold_set == {"1.2.1"}
        assert case.retrieved_top3 == ["5.6", "1.2.1", "9.9"]
        assert case.hit_at_3 == 1
        assert case.recall_at_3 == 1.0
        assert result.aggregate_hit_at_3 == 1.0

    @pytest.mark.asyncio
    async def test_provider_retrieve_called_with_pool_size_top_k(self):
        tc = _test_case("B01-001", "q", ["1.2.1"])
        provider = MagicMock()
        provider.retrieve.return_value = []
        harness = _harness(_repo([tc]), provider, gold_cases=[], pool_size=50)

        await harness.execute(test_ids=["B01-001"])

        provider.retrieve.assert_called_once_with(query="q", top_k=50)

    @pytest.mark.asyncio
    async def test_result_ordering_matches_requested_test_ids(self):
        tc_a = _test_case("B02-001", "qa", [])
        tc_b = _test_case("B01-001", "qb", [])
        provider = MagicMock()
        provider.retrieve.return_value = []
        # repository returns cases out of requested order
        harness = _harness(_repo([tc_a, tc_b]), provider, gold_cases=[])

        result = await harness.execute(test_ids=["B01-001", "B02-001"])

        assert [c.test_id for c in result.per_case] == ["B01-001", "B02-001"]

    @pytest.mark.asyncio
    async def test_default_test_ids_is_fixed_18(self):
        provider = MagicMock()
        provider.retrieve.return_value = []
        repo = _repo([])
        harness = _harness(repo, provider, gold_cases=[])

        await harness.execute()

        repo.load_by_ids.assert_called_once_with(list(FIXED_18_TEST_IDS))
        assert len(FIXED_18_TEST_IDS) == 18


class TestGoldSetCrossCheck:
    """Gold set = clause_reference UNION xlsx bracketed citations (Pitfall 4)."""

    @pytest.mark.asyncio
    async def test_gold_set_is_union_of_both_sources(self):
        tc = _test_case("B01-001", "q", ["1.2.1"])
        provider = MagicMock()
        provider.retrieve.return_value = []
        gold = CaseGoldRelations(
            test_id="B01-001",
            clause_citations=["1.2.1", "1.4.1"],
        )
        harness = _harness(_repo([tc]), provider, gold_cases=[gold])

        result = await harness.execute(test_ids=["B01-001"])

        assert result.per_case[0].gold_set == {"1.2.1", "1.4.1"}

    @pytest.mark.asyncio
    async def test_disagreement_flagged_when_sources_differ(self):
        tc = _test_case("B01-001", "q", ["1.2.1"])
        provider = MagicMock()
        provider.retrieve.return_value = []
        gold = CaseGoldRelations(
            test_id="B01-001",
            clause_citations=["1.2.1", "1.4.1"],  # xlsx has MORE than clause_reference
        )
        harness = _harness(_repo([tc]), provider, gold_cases=[gold])

        result = await harness.execute(test_ids=["B01-001"])

        assert result.per_case[0].gold_disagreement is True
        assert "B01-001" in result.disagreement_test_ids

    @pytest.mark.asyncio
    async def test_no_disagreement_when_sources_agree(self):
        tc = _test_case("B01-001", "q", ["1.2.1"])
        provider = MagicMock()
        provider.retrieve.return_value = []
        gold = CaseGoldRelations(test_id="B01-001", clause_citations=["1.2.1"])
        harness = _harness(_repo([tc]), provider, gold_cases=[gold])

        result = await harness.execute(test_ids=["B01-001"])

        assert result.per_case[0].gold_disagreement is False
        assert result.disagreement_test_ids == []

    @pytest.mark.asyncio
    async def test_missing_gold_relations_row_falls_back_to_clause_reference(self):
        tc = _test_case("B01-001", "q", ["1.2.1"])
        provider = MagicMock()
        provider.retrieve.return_value = []
        # No CaseGoldRelations for this test_id at all (xlsx row absent)
        harness = _harness(_repo([tc]), provider, gold_cases=[])

        result = await harness.execute(test_ids=["B01-001"])

        assert result.per_case[0].gold_set == {"1.2.1"}
        assert result.per_case[0].gold_disagreement is True  # {} != {"1.2.1"} -> flagged


class TestDeterminism:
    """D-15: same inputs -> identical output across repeated invocations."""

    @pytest.mark.asyncio
    async def test_repeated_execution_is_byte_identical(self):
        tc = _test_case("B01-001", "digital boundary question", ["1.2.1"])
        provider = MagicMock()
        provider.retrieve.return_value = [
            _doc("1.2.1", 1.5),
            _doc("1.4.1", 1.0),
            _doc("5.6", 1.0),
        ]
        harness = _harness(_repo([tc]), provider, gold_cases=[])

        result_1 = await harness.execute(test_ids=["B01-001"])
        result_2 = await harness.execute(test_ids=["B01-001"])

        assert result_1.per_case[0].retrieved_top3 == result_2.per_case[0].retrieved_top3
        assert result_1.per_case[0].hit_at_3 == result_2.per_case[0].hit_at_3
        assert result_1.per_case[0].recall_at_3 == result_2.per_case[0].recall_at_3
        assert result_1.per_case[0].recall_at_pool == result_2.per_case[0].recall_at_pool
        assert result_1.aggregate_hit_at_3 == result_2.aggregate_hit_at_3


class TestGoldRelationXlsxLoading:
    """`_load_gold_relations` degrades gracefully when the xlsx is unavailable."""

    @pytest.mark.asyncio
    async def test_missing_xlsx_falls_back_to_clause_reference_only(self):
        tc = _test_case("B01-001", "q", ["1.2.1"])
        provider = MagicMock()
        provider.retrieve.return_value = []
        harness = ClauseHitHarnessUseCase(
            test_case_repository=_repo([tc]),
            graph_retrieval_provider=provider,
            gold_xlsx_path="/nonexistent/path/does-not-exist.xlsx",
        )

        with patch(
            "application.use_cases.clause_hit_harness.parse_gold_relations",
            side_effect=FileNotFoundError("nope"),
        ):
            result = await harness.execute(test_ids=["B01-001"])

        assert result.per_case[0].gold_set == {"1.2.1"}
        assert result.per_case[0].xlsx_citation_set == set()

    @pytest.mark.asyncio
    async def test_real_load_gold_relations_path_invokes_parser(self):
        """Exercises `_load_gold_relations` end-to-end (not overridden) against
        a patched `parse_gold_relations` boundary — proves the harness reuses
        `gold_relation_parser` rather than re-implementing xlsx parsing."""
        tc = _test_case("B01-001", "q", ["1.2.1"])
        provider = MagicMock()
        provider.retrieve.return_value = []
        harness = ClauseHitHarnessUseCase(
            test_case_repository=_repo([tc]),
            graph_retrieval_provider=provider,
            gold_xlsx_path="some-path.xlsx",
        )
        gold = CaseGoldRelations(test_id="B01-001", clause_citations=["1.2.1", "1.4.1"])

        with patch(
            "application.use_cases.clause_hit_harness.parse_gold_relations",
            return_value=[gold],
        ) as mock_parse:
            result = await harness.execute(test_ids=["B01-001"])

        mock_parse.assert_called_once_with("some-path.xlsx", sheet_name="eval-18")
        assert result.per_case[0].gold_set == {"1.2.1", "1.4.1"}


@pytest.mark.integration
class TestClauseHitHarnessLiveB01001:
    """
    Live-Neo4j smallest-real-slice E2E (~/.claude/rules/e2e-testing.md;
    mirrors `tests/rag/graph/ontology/test_clause_linker.py`'s
    `TestClauseLinkerE2ESlice` precedent and 10-09's live-slice pattern):
    seed-clauses -> a REAL `OntologyKGBuilder.build()` (real gpt-4o-mini
    call, one tiny synthetic document echoing B01-001's actual scope
    question and citing §1.2.1/§1.4.1) -> `ClauseLinker.link()` -> the REAL
    harness (`ClauseHitHarnessUseCase.execute`) against the REAL B01-001 GT
    question and the REAL `Neo4jOntologyGraphRetrievalAdapter`.

    Proves the full repository -> retrieval -> scoring wiring against a live
    Neo4j instance, not just mocks — WITHOUT depending on the full CCoP
    corpus being built first (that is 10-11's job, per the plan's
    critical_notes). Self-provisions its own tiny slice and restores the
    graph to just the 883 seeded `:Clause` nodes in a `finally` block, same
    as the established precedent.

    Excluded from `poetry run pytest -m "not integration"`; costs one real
    OpenRouter call. Requires `CCOP_NEO4J_URI` (a running local Neo4j).
    """

    # Echoes the REAL B01-001 GT question's topic (healthcare CII digital
    # boundary) and cites both gold clauses verbatim so ClauseLinker's
    # boundary-aware match (KGInspector._clause_id_appears) links this one
    # synthetic chunk to BOTH seeded clause nodes.
    SYNTHETIC_DOC = {
        "synthetic-b01-001-e2e-doc": (
            "1.2.1 Digital Boundary. CCoP 2.0 mandatory compliance applies "
            "only to the designated Critical Information Infrastructure and "
            "its cyber operating environment, not automatically to every "
            "system on the same enterprise network as the CII, such as a "
            "hospital administration system. 1.4.1 Scope of Application. "
            "The digital boundary determining which systems fall within "
            "CCoP 2.0's mandatory requirements is jointly determined by "
            "CSA, the CII owner, and the Sector Lead."
        )
    }

    def _driver(self, settings) -> "neo4j.Driver":
        import neo4j as neo4j_module

        return neo4j_module.GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )

    @pytest.mark.asyncio
    async def test_b01_001_containment_surfaces_scope_clauses(self):
        from infrastructure.config.container import get_container
        from infrastructure.config.settings import get_settings
        from rag.graph.build.ontology_kg_builder import OntologyKGBuilder
        from rag.graph.ontology.clause_linker import ClauseLinker
        from rag.graph.ontology.clause_seeder import ClauseSeeder

        settings = get_settings()
        if not getattr(settings, "neo4j_uri", None):
            pytest.skip("CCOP_NEO4J_URI not configured — skipping live Neo4j test")

        driver = self._driver(settings)
        try:
            with driver.session(database=settings.neo4j_database) as session:
                session.run("MATCH (n) DETACH DELETE n")

            # 1. seed-clauses (deterministic, no LLM) — provides the 1.2.1/
            #    1.4.1 seeded clause nodes this document's text links to.
            seeder = ClauseSeeder(settings=settings, driver=driver)
            seeder.seed()

            # 2. build-ontology (real gpt-4o-mini extraction, ONE tiny doc —
            #    smallest real slice, not the full corpus).
            builder = OntologyKGBuilder(settings=settings, driver=driver)
            build_stats = await builder.build(self.SYNTHETIC_DOC)
            assert build_stats.docs_processed == 1
            assert build_stats.failures == []

            # 3. clause_linker (deterministic, no LLM).
            linker = ClauseLinker(settings=settings, driver=driver)
            link_stats = linker.link()
            assert link_stats.linked_to_edges_total >= 1

            # 4. the REAL harness against the REAL B01-001 question + the
            #    REAL Neo4jOntologyGraphRetrievalAdapter/JSONLTestCaseRepository.
            container = get_container()
            provider = container.graph_retrieval_provider_ontology()
            if provider is None:
                pytest.skip("graphrag-ontology provider unavailable")
            test_case_repository = container.test_case_repository()
            gold_xlsx_path = (
                settings.results_dir / "eval-report-hybrid-suite-20260630-0907.xlsx"
            )

            harness = ClauseHitHarnessUseCase(
                test_case_repository=test_case_repository,
                graph_retrieval_provider=provider,
                gold_xlsx_path=gold_xlsx_path,
                pool_size=50,
            )

            result = await harness.execute(test_ids=["B01-001"])

            assert len(result.per_case) == 1
            case = result.per_case[0]
            pool_normalized = {
                cid.strip().lstrip("§").lower() for cid in case.retrieved_pool
            }
            assert "1.2.1" in pool_normalized or "1.4.1" in pool_normalized, (
                f"Expected §1.2.1/§1.4.1 in the retrieved pool, got: {case.retrieved_pool}"
            )
        finally:
            with driver.session(database=settings.neo4j_database) as session:
                session.run("MATCH (n) DETACH DELETE n")
            # Restore the 883-clause seeded baseline other tests/plans expect
            # (10-09-SUMMARY.md's "Next Phase Readiness" precedent).
            restore_driver = self._driver(settings)
            try:
                ClauseSeeder(settings=settings, driver=restore_driver).seed()
            finally:
                restore_driver.close()
            driver.close()
