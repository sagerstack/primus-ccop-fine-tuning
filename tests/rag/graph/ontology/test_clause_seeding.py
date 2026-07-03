"""
Deterministic clause-backbone seeder tests (D-10/D-09).

`TestClauseSeederUnit` covers the pure hierarchy/function-type derivation
helpers (no Neo4j required, runs under `pytest -m "not integration"`).

`TestClauseSeederIntegration` requires a live local Neo4j
(`docker compose up -d neo4j`) — mirrors
`tests/rag/graph/build/test_kg_builder_integration.py`'s precedent. No LLM
calls anywhere in this module (D-10: no hallucinated/unnamed clauses).
"""

import json
from pathlib import Path

import neo4j
import pytest

from infrastructure.config.settings import get_settings
from rag.graph.ontology.clause_seeder import (
    DEFAULT_CLAUSE_INVENTORY_PATH,
    DEFAULT_FUNCTION_TYPE,
    FUNCTION_TYPE_TAGS,
    ClauseSeeder,
    _derive_chapter,
    _derive_function_type,
    _derive_parent,
)


def _fixture_entries_count() -> int:
    payload = json.loads(Path(DEFAULT_CLAUSE_INVENTORY_PATH).read_text())
    return len(payload["entries"])


class TestClauseSeederUnit:
    """Pure derivation-function tests — no external services required."""

    def test_derive_parent_plain_dot_hierarchy(self):
        assert _derive_parent("6.1.2") == "6.1"
        assert _derive_parent("6.1") == "6"

    def test_derive_parent_root_clause_has_no_parent(self):
        assert _derive_parent("6") is None
        assert _derive_parent("Part 1") is None
        assert _derive_parent("section 5") is None

    def test_derive_parent_item_letter_suffix_parents_to_enclosing_clause(self):
        # "10.2.5(a)" must parent to "10.2.5", NOT the naive dot-rsplit "10.2".
        assert _derive_parent("10.2.5(a)") == "10.2.5"
        assert _derive_parent("1(a)") == "1"

    def test_derive_chapter(self):
        assert _derive_chapter("10.2.5(a)") == "10"
        assert _derive_chapter("6.1.2") == "6"
        assert _derive_chapter("Part 1") == "Part 1"

    def test_derive_function_type_ccop_2_0_glossary_section_is_definition(self):
        assert _derive_function_type("1.2.1", "CCoP 2.0") == "DefinitionClause"
        assert _derive_function_type("1.2", "CCoP 2.0") == "DefinitionClause"

    def test_derive_function_type_ccop_2_0_preliminary_chapter_is_scope(self):
        assert _derive_function_type("1.4.1", "CCoP 2.0") == "ScopeClause"
        assert _derive_function_type("1", "CCoP 2.0") == "ScopeClause"

    def test_derive_function_type_ccop_2_0_body_clause_defaults_to_control(self):
        assert _derive_function_type("5.2.1", "CCoP 2.0") == DEFAULT_FUNCTION_TYPE
        assert _derive_function_type("5.2.1", "CCoP 2.0") in FUNCTION_TYPE_TAGS

    def test_derive_function_type_non_ccop_2_0_docs_fall_back_to_default(self):
        assert _derive_function_type("1.2.1", "Cybersecurity Act 2018") == DEFAULT_FUNCTION_TYPE
        assert _derive_function_type("6.1", "Auditing Guidelines") == DEFAULT_FUNCTION_TYPE


@pytest.mark.integration
class TestClauseSeederIntegration:
    """Requires a live local Neo4j (docker compose up -d neo4j)."""

    def _driver(self) -> neo4j.Driver:
        settings = get_settings()
        return neo4j.GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )

    @pytest.fixture(autouse=True)
    def _clean_slate(self):
        settings = get_settings()
        driver = self._driver()
        with driver.session(database=settings.neo4j_database) as session:
            session.run("MATCH (c:Clause) DETACH DELETE c")
        driver.close()
        yield
        driver = self._driver()
        with driver.session(database=settings.neo4j_database) as session:
            session.run("MATCH (c:Clause) DETACH DELETE c")
        driver.close()

    def test_seed_creates_exactly_the_fixture_clause_count(self):
        settings = get_settings()
        driver = self._driver()
        try:
            seeder = ClauseSeeder(settings=settings, driver=driver)
            stats = seeder.seed()

            expected_total = _fixture_entries_count()
            assert stats.nodes_seeded == expected_total
            assert stats.entries_total == expected_total

            with driver.session(database=settings.neo4j_database) as session:
                count = session.run("MATCH (c:Clause) RETURN count(c) AS c").single()["c"]
            assert count == expected_total
        finally:
            driver.close()

    def test_known_child_clause_has_parent_hierarchy_edges(self):
        settings = get_settings()
        driver = self._driver()
        try:
            seeder = ClauseSeeder(settings=settings, driver=driver)
            seeder.seed()

            with driver.session(database=settings.neo4j_database) as session:
                child_edge = session.run(
                    "MATCH (parent:Clause {clause_id: '6.1', source_doc: 'CCoP 2.0'})"
                    "-[:HAS_CHILD]->(child:Clause {clause_id: '6.1.2', source_doc: 'CCoP 2.0'}) "
                    "RETURN count(*) AS c"
                ).single()["c"]
                assert child_edge == 1

                grandparent_edge = session.run(
                    "MATCH (gp:Clause {clause_id: '6', source_doc: 'CCoP 2.0'})"
                    "-[:HAS_CHILD]->(parent:Clause {clause_id: '6.1', source_doc: 'CCoP 2.0'}) "
                    "RETURN count(*) AS c"
                ).single()["c"]
                assert grandparent_edge == 1
        finally:
            driver.close()

    def test_reseeding_is_idempotent(self):
        settings = get_settings()
        driver = self._driver()
        try:
            seeder = ClauseSeeder(settings=settings, driver=driver)
            seeder.seed()
            second_stats = seeder.seed()

            expected_total = _fixture_entries_count()
            assert second_stats.nodes_seeded == expected_total

            with driver.session(database=settings.neo4j_database) as session:
                count = session.run("MATCH (c:Clause) RETURN count(c) AS c").single()["c"]
            assert count == expected_total
        finally:
            driver.close()

    def test_every_clause_has_a_valid_function_type(self):
        settings = get_settings()
        driver = self._driver()
        try:
            seeder = ClauseSeeder(settings=settings, driver=driver)
            seeder.seed()

            with driver.session(database=settings.neo4j_database) as session:
                missing = session.run(
                    "MATCH (c:Clause) WHERE c.function_type IS NULL "
                    "OR NOT c.function_type IN $tags "
                    "RETURN count(c) AS c",
                    tags=list(FUNCTION_TYPE_TAGS),
                ).single()["c"]
            assert missing == 0
        finally:
            driver.close()
