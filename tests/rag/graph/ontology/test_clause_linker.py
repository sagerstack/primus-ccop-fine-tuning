"""
Deterministic entity/chunk -> clause linker tests (D-10/D-11).

`TestClauseLinkerUnit` covers the pure boundary-aware match logic
(`_compute_pairs`), no Neo4j required, runs under `pytest -m "not integration"`.

`TestClauseLinkerIntegration` requires a live local Neo4j
(`docker compose up -d neo4j`) -- mirrors
`tests/rag/graph/ontology/test_clause_seeding.py`'s precedent. Builds a
small synthetic :Chunk/:Clause/:__Entity__ graph directly via Cypher (no LLM
calls) to prove the LINKED_TO wiring deterministically, including the
boundary-aware match (does NOT match "5.3.10" for "5.3.1").

`TestClauseLinkerE2ESlice` is the smallest-real-slice end-to-end proof
(per ~/.claude/rules/e2e-testing.md): `seed-clauses` -> a REAL
`OntologyKGBuilder.build()` (real gpt-4o-mini call via OpenRouter, one tiny
synthetic document) -> `ClauseLinker.link()`, asserting >=1 LINKED_TO edge
and that extracted entities carry canonical names (no "N.A."/"John Doe"
junk placeholders, D-06/D-07).
"""

import neo4j
import pytest

from infrastructure.config.settings import get_settings
from rag.graph.build.ontology_kg_builder import OntologyKGBuilder
from rag.graph.ontology.clause_linker import ClauseLinker
from rag.graph.ontology.clause_seeder import ClauseSeeder


class TestClauseLinkerUnit:
    """Pure `_compute_pairs` boundary-aware match -- no external services required."""

    def test_matches_exact_clause_id_mention(self):
        chunks = [{"chunk_id": "chunk-1", "text": "Section 5.3.1 requires MFA."}]
        clauses = [{"clause_element_id": "clause-1", "clause_id": "5.3.1"}]

        pairs = ClauseLinker._compute_pairs(chunks, clauses)

        assert pairs == [{"chunk_id": "chunk-1", "clause_element_id": "clause-1"}]

    def test_does_not_falsely_match_longer_clause_id(self):
        """"5.3.1" must NOT match inside chunk text that only mentions "5.3.10"."""
        chunks = [{"chunk_id": "chunk-1", "text": "See section 5.3.10 for details."}]
        clauses = [{"clause_element_id": "clause-1", "clause_id": "5.3.1"}]

        pairs = ClauseLinker._compute_pairs(chunks, clauses)

        assert pairs == []

    def test_does_not_falsely_match_shorter_clause_id(self):
        """"5.3.10" must NOT match a chunk that only mentions "5.3.1"."""
        chunks = [{"chunk_id": "chunk-1", "text": "Section 5.3.1 requires MFA."}]
        clauses = [{"clause_element_id": "clause-1", "clause_id": "5.3.10"}]

        pairs = ClauseLinker._compute_pairs(chunks, clauses)

        assert pairs == []

    def test_case_insensitive_match(self):
        chunks = [{"chunk_id": "chunk-1", "text": "SECTION 5.3.1 REQUIRES MFA."}]
        clauses = [{"clause_element_id": "clause-1", "clause_id": "5.3.1"}]

        pairs = ClauseLinker._compute_pairs(chunks, clauses)

        assert len(pairs) == 1

    def test_multiple_clauses_matched_in_one_chunk(self):
        chunks = [{"chunk_id": "chunk-1", "text": "See 5.3.1 and 5.3.2 for details."}]
        clauses = [
            {"clause_element_id": "clause-1", "clause_id": "5.3.1"},
            {"clause_element_id": "clause-2", "clause_id": "5.3.2"},
            {"clause_element_id": "clause-3", "clause_id": "5.4"},
        ]

        pairs = ClauseLinker._compute_pairs(chunks, clauses)

        matched_ids = {p["clause_element_id"] for p in pairs}
        assert matched_ids == {"clause-1", "clause-2"}

    def test_empty_chunk_text_produces_no_pairs(self):
        chunks = [{"chunk_id": "chunk-1", "text": ""}]
        clauses = [{"clause_element_id": "clause-1", "clause_id": "5.3.1"}]

        pairs = ClauseLinker._compute_pairs(chunks, clauses)

        assert pairs == []


@pytest.mark.integration
class TestClauseLinkerIntegration:
    """
    Requires a live local Neo4j (docker compose up -d neo4j). Builds a small
    synthetic :Chunk/:Clause/:__Entity__ graph directly via Cypher (no LLM
    calls) to prove LINKED_TO wiring, including boundary-aware matching.
    """

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
            session.run("MATCH (n) WHERE n:Chunk OR n:Clause OR n:__Entity__ DETACH DELETE n")
        driver.close()
        yield
        driver = self._driver()
        with driver.session(database=settings.neo4j_database) as session:
            session.run("MATCH (n) WHERE n:Chunk OR n:Clause OR n:__Entity__ DETACH DELETE n")
        driver.close()

    def test_chunk_linked_to_matching_clause(self):
        settings = get_settings()
        driver = self._driver()
        try:
            with driver.session(database=settings.neo4j_database) as session:
                session.run(
                    "CREATE (:Chunk {text: 'Section 5.3.1 requires MFA.'}) "
                    "CREATE (:Clause {clause_id: '5.3.1', source_doc: 'CCoP 2.0'}) "
                    "CREATE (:Clause {clause_id: '5.3.10', source_doc: 'CCoP 2.0'})"
                )

            linker = ClauseLinker(settings=settings, driver=driver)
            stats = linker.link()

            assert stats.chunks_scanned == 1
            assert stats.clauses_scanned == 2
            assert stats.chunk_clause_pairs == 1
            assert stats.linked_to_edges_total == 1

            with driver.session(database=settings.neo4j_database) as session:
                linked = session.run(
                    "MATCH (:Chunk)-[:LINKED_TO]->(c:Clause) RETURN c.clause_id AS cid"
                ).single()
                assert linked["cid"] == "5.3.1"
        finally:
            driver.close()

    def test_entity_inherits_chunk_clause_link_via_from_chunk(self):
        settings = get_settings()
        driver = self._driver()
        try:
            with driver.session(database=settings.neo4j_database) as session:
                session.run(
                    "CREATE (chunk:Chunk {text: 'Section 5.3.1 requires MFA.'}) "
                    "CREATE (clause:Clause {clause_id: '5.3.1', source_doc: 'CCoP 2.0'}) "
                    "CREATE (entity:__Entity__:MultiFactorAuthentication {name: 'MFA'}) "
                    "CREATE (entity)-[:FROM_CHUNK]->(chunk)"
                )

            linker = ClauseLinker(settings=settings, driver=driver)
            linker.link()

            with driver.session(database=settings.neo4j_database) as session:
                linked = session.run(
                    "MATCH (e:__Entity__)-[:LINKED_TO]->(c:Clause) "
                    "RETURN e.name AS name, c.clause_id AS cid"
                ).single()
                assert linked["name"] == "MFA"
                assert linked["cid"] == "5.3.1"
        finally:
            driver.close()

    def test_relink_is_idempotent(self):
        settings = get_settings()
        driver = self._driver()
        try:
            with driver.session(database=settings.neo4j_database) as session:
                session.run(
                    "CREATE (:Chunk {text: 'Section 5.3.1 requires MFA.'}) "
                    "CREATE (:Clause {clause_id: '5.3.1', source_doc: 'CCoP 2.0'})"
                )

            linker = ClauseLinker(settings=settings, driver=driver)
            linker.link()
            second_stats = linker.link()

            assert second_stats.linked_to_edges_total == 1
        finally:
            driver.close()


@pytest.mark.integration
class TestClauseLinkerE2ESlice:
    """
    Smallest-real-slice E2E (~/.claude/rules/e2e-testing.md): seed-clauses ->
    a REAL OntologyKGBuilder.build() (real gpt-4o-mini call, one tiny
    synthetic document) -> ClauseLinker.link(). Proves the full seed -> build
    -> link chain, not just mocked units. Excluded from
    `poetry run pytest -m "not integration"`; costs one real OpenRouter call.
    """

    SYNTHETIC_DOC = {
        "synthetic-e2e-doc": (
            "5.3.1 Access Control. The CIIO must implement multi-factor "
            "authentication for all privileged access to the Power Grid "
            "Control Platform, a critical information infrastructure."
        )
    }

    def _driver(self) -> neo4j.Driver:
        settings = get_settings()
        return neo4j.GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )

    @pytest.mark.asyncio
    async def test_seed_build_link_chain_produces_linked_to_edges(self):
        settings = get_settings()
        driver = self._driver()
        try:
            with driver.session(database=settings.neo4j_database) as session:
                session.run("MATCH (n) DETACH DELETE n")

            # 1. seed-clauses (deterministic, no LLM) -- provides the 5.3.1
            #    seeded clause node this document's text should link to.
            seeder = ClauseSeeder(settings=settings, driver=driver)
            seeder.seed()

            # 2. build-ontology (real gpt-4o-mini extraction, ONE tiny doc --
            #    smallest real slice).
            builder = OntologyKGBuilder(settings=settings, driver=driver)
            build_stats = await builder.build(self.SYNTHETIC_DOC)
            assert build_stats.docs_processed == 1
            assert build_stats.failures == []

            # 3. clause_linker (deterministic, no LLM).
            linker = ClauseLinker(settings=settings, driver=driver)
            link_stats = linker.link()

            assert link_stats.linked_to_edges_total >= 1

            # D-06/D-07: extracted entities must carry a canonical name --
            # no junk placeholders.
            with driver.session(database=settings.neo4j_database) as session:
                names = [
                    record["name"]
                    for record in session.run(
                        "MATCH (e:__Entity__) WHERE e.name IS NOT NULL "
                        "RETURN e.name AS name"
                    )
                ]
            assert names, "expected at least one extracted entity with a canonical name"
            junk = {"n.a.", "n/a", "", "a", "john doe", "company x"}
            for name in names:
                assert name.strip().lower() not in junk, f"junk placeholder name: {name!r}"
        finally:
            with driver.session(database=settings.neo4j_database) as session:
                session.run("MATCH (n) DETACH DELETE n")
            driver.close()
