"""
Integration test: runs KGInspector against the LIVE Neo4j emergent CCoP graph.

Isolation-safety (per the coordinator's directive): the live graph is a real,
expensive-to-rebuild corpus KG (~625 nodes / 1,232 relationships / 179 chunks /
7 documents at time of writing) that downstream retrieval/eval plans depend
on. This test is READ-ONLY — it never writes, deletes, or wipes any node or
relationship. It only asserts the existing graph's metrics are present and
plausible (> 0), which the live corpus graph guarantees.

Mirrors tests/rag/test_qdrant_vector_store_adapter.py's integration-test
precedent (`@pytest.mark.integration` against a live local service). Excluded
from `poetry run pytest -m "not integration"`.
"""
import neo4j
import pytest

from infrastructure.config.settings import get_settings
from rag.graph.inspect.metrics import KGInspector


@pytest.mark.integration
class TestKGInspectorIntegration:
    """Read-only assertions against the live emergent CCoP graph."""

    def _inspector(self) -> tuple[KGInspector, neo4j.Driver]:
        settings = get_settings()
        driver = neo4j.GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        return KGInspector(driver=driver, database=settings.neo4j_database), driver

    def test_node_and_edge_counts_are_positive(self):
        inspector, driver = self._inspector()
        try:
            assert inspector.node_count() > 0
            assert inspector.edge_count() > 0
        finally:
            driver.close()

    def test_summary_returns_all_d18_metric_keys(self):
        inspector, driver = self._inspector()
        try:
            summary = inspector.summary()

            assert set(summary.keys()) == {
                "node_count",
                "edge_count",
                "entity_type_distribution",
                "degree_distribution",
                "orphan_nodes",
                "clause_coverage",
                "duplicate_entities",
                "extraction_failure_rate",
            }
            # The live corpus graph guarantees non-zero structural content.
            assert summary["node_count"] > 0
            assert summary["edge_count"] > 0
            assert len(summary["entity_type_distribution"]) > 0

            coverage = summary["clause_coverage"]
            assert coverage["total"] > 0
            assert 0.0 <= coverage["coverage_ratio"] <= 1.0
        finally:
            driver.close()
