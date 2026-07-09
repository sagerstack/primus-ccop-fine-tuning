"""
Integration test: builds a TINY emergent KG against a live local Neo4j service.

Mirrors tests/rag/test_qdrant_vector_store_adapter.py's integration-test
precedent — requires `docker compose up -d neo4j` and a configured
CCOP_OPENROUTER_API_KEY. Uses the REAL SimpleKGPipeline (real gpt-4o-mini
calls via OpenRouter), kept to two short synthetic documents to bound cost.

Excluded from `poetry run pytest -m "not integration"`. Not run as part of
09-02 execution itself per the cost-control directive — the coordinator
decides when to run the full 8-doc corpus build separately.
"""
import neo4j
import pytest

from infrastructure.config.settings import get_settings
from rag.graph.build.kg_builder import EmergentKGBuilder

SYNTHETIC_DOCS = {
    "synthetic-doc-1": (
        "Acme Corp operates a critical information infrastructure system called "
        "the Power Grid Control Platform. The Chief Information Security Officer, "
        "Jane Tan, is responsible for ensuring the platform complies with the "
        "Cybersecurity Code of Practice. Acme Corp must submit an annual audit "
        "report to the Cyber Security Agency of Singapore."
    ),
    "synthetic-doc-2": (
        "The Power Grid Control Platform uses multi-factor authentication to "
        "protect privileged accounts. Jane Tan reviews access control logs "
        "monthly and reports findings to the Board of Directors."
    ),
}


@pytest.mark.integration
class TestEmergentKGBuilderIntegration:
    """Builds a tiny emergent KG against a live local Neo4j instance."""

    @pytest.mark.asyncio
    async def test_build_writes_nodes_and_relationships_to_live_neo4j(self):
        settings = get_settings()
        driver = neo4j.GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

        try:
            # Clean slate so node/relationship counts are unambiguous.
            with driver.session(database=settings.neo4j_database) as session:
                session.run("MATCH (n) DETACH DELETE n")

            builder = EmergentKGBuilder(settings=settings, driver=driver)
            stats = await builder.build(SYNTHETIC_DOCS)

            assert stats.docs_processed == 2
            assert stats.failures == []

            with driver.session(database=settings.neo4j_database) as session:
                node_count = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
                rel_count = session.run(
                    "MATCH ()-[r]->() RETURN count(r) AS c"
                ).single()["c"]

            assert node_count > 0
            assert rel_count > 0
        finally:
            driver.close()
