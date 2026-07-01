"""
Unit tests for KGInspector (Phase 9 — D-18 KG-quality inspection).

All Neo4j interaction is mocked — these tests never touch the network or a
live Neo4j instance. Live-Neo4j validation lives in
tests/rag/graph/inspect/test_kg_metrics_integration.py (@pytest.mark.integration).
"""
import json
from unittest.mock import MagicMock

import pytest

from rag.graph.inspect.metrics import KGInspector


def _make_driver(query_results: dict[str, list[dict]]) -> MagicMock:
    """
    Build a mock neo4j.Driver whose session.run(...) return value is looked
    up by a substring of the Cypher query text, so each test only has to
    describe the rows relevant to the method under test.
    """
    driver = MagicMock()
    session = MagicMock()
    driver.session.return_value.__enter__.return_value = session

    def _run(query: str, *args, **kwargs):
        for needle, rows in query_results.items():
            if needle in query:
                result = MagicMock()
                result.__iter__.return_value = iter(
                    [_Record(row) for row in rows]
                )
                result.single.return_value = _Record(rows[0]) if rows else None
                return result
        raise AssertionError(f"Unexpected query, no fixture matched: {query!r}")

    session.run.side_effect = _run
    return driver


class _Record(dict):
    """Minimal neo4j.Record stand-in — supports record["key"] access."""


class TestNodeEdgeCounts:
    def test_node_count_returns_int(self):
        driver = _make_driver({"MATCH (n) RETURN count(n)": [{"c": 625}]})
        inspector = KGInspector(driver=driver, database="neo4j")

        assert inspector.node_count() == 625

    def test_edge_count_returns_int(self):
        driver = _make_driver({"MATCH ()-[r]->() RETURN count(r)": [{"c": 1232}]})
        inspector = KGInspector(driver=driver, database="neo4j")

        assert inspector.edge_count() == 1232


class TestEntityTypeDistribution:
    def test_returns_label_counts_excluding_structural_labels(self):
        driver = _make_driver(
            {
                "UNWIND labels(n)": [
                    {"label": "__KGBuilder__", "c": 625},
                    {"label": "__Entity__", "c": 439},
                    {"label": "Chunk", "c": 179},
                    {"label": "Document", "c": 7},
                    {"label": "CybersecurityIncident", "c": 77},
                    {"label": "User", "c": 62},
                ]
            }
        )
        inspector = KGInspector(driver=driver, database="neo4j")

        distribution = inspector.entity_type_distribution()

        assert distribution == {"CybersecurityIncident": 77, "User": 62}
        assert "__KGBuilder__" not in distribution
        assert "Chunk" not in distribution


class TestDegreeDistribution:
    def test_returns_histogram_summary(self):
        driver = _make_driver(
            {
                "COUNT { (n)--() }": [
                    {"degree": 0},
                    {"degree": 2},
                    {"degree": 2},
                    {"degree": 10},
                    {"degree": 30},
                ]
            }
        )
        inspector = KGInspector(driver=driver, database="neo4j")

        summary = inspector.degree_distribution()

        assert summary["min"] == 0
        assert summary["max"] == 30
        assert summary["avg"] == pytest.approx(8.8, abs=0.01)
        assert summary["buckets"]["0"] == 1
        assert summary["buckets"]["21+"] == 1

    def test_empty_graph_returns_zeroed_summary(self):
        driver = _make_driver({"COUNT { (n)--() }": []})
        inspector = KGInspector(driver=driver, database="neo4j")

        summary = inspector.degree_distribution()

        assert summary["min"] == 0
        assert summary["max"] == 0
        assert summary["avg"] == 0.0


class TestOrphanNodes:
    def test_returns_count_of_degree_zero_nodes(self):
        driver = _make_driver({"WHERE NOT (n)--()": [{"c": 3}]})
        inspector = KGInspector(driver=driver, database="neo4j")

        assert inspector.orphan_nodes() == 3


class TestClauseCoverage:
    def test_covered_total_and_ratio_computed_from_chunk_text(self, tmp_path):
        inventory = {
            "generated_at": "2026-01-01",
            "source_docs": ["CCoP 2.0"],
            "entries": [
                {"clause_id": "5.2.1", "source_doc": "CCoP 2.0"},
                {"clause_id": "5.2.1", "source_doc": "CCoP 2.0"},  # duplicate on purpose
                {"clause_id": "9.9.9", "source_doc": "CCoP 2.0"},
            ],
        }
        inventory_path = tmp_path / "clause_inventory.json"
        inventory_path.write_text(json.dumps(inventory))

        driver = _make_driver(
            {
                "MATCH (c:Chunk) RETURN c.text": [
                    {"text": "Section 5.2.1 requires access control logging."},
                    {"text": "Unrelated prose with no clause reference."},
                ]
            }
        )
        inspector = KGInspector(driver=driver, database="neo4j")

        coverage = inspector.clause_coverage(inventory_path)

        assert coverage == {"covered": 1, "total": 2, "coverage_ratio": 0.5}

    def test_case_insensitive_and_word_boundary_match(self, tmp_path):
        inventory = {
            "entries": [
                {"clause_id": "1", "source_doc": "doc"},
                {"clause_id": "15.37", "source_doc": "doc"},
            ]
        }
        inventory_path = tmp_path / "clause_inventory.json"
        inventory_path.write_text(json.dumps(inventory))

        # "1" must NOT spuriously match inside "15.37" (boundary safety).
        driver = _make_driver(
            {
                "MATCH (c:Chunk) RETURN c.text": [
                    {"text": "See CLAUSE 15.37 for details."},
                ]
            }
        )
        inspector = KGInspector(driver=driver, database="neo4j")

        coverage = inspector.clause_coverage(inventory_path)

        assert coverage["covered"] == 1  # only "15.37" matches
        assert coverage["total"] == 2


class TestDuplicateEntities:
    def test_groups_nodes_by_normalized_display_name(self):
        driver = _make_driver(
            {
                "MATCH (n:__Entity__)": [
                    {
                        "node_id": "1",
                        "labels": ["__KGBuilder__", "__Entity__", "User"],
                        "props": {"user_id": "user123", "username": "john_doe"},
                    },
                    {
                        "node_id": "2",
                        "labels": ["__KGBuilder__", "__Entity__", "User"],
                        "props": {"user_id": "USER123", "username": "jane_tan"},
                    },
                    {
                        "node_id": "3",
                        "labels": ["__KGBuilder__", "__Entity__", "Vendor"],
                        "props": {"name": "Acme Corp"},
                    },
                ]
            }
        )
        inspector = KGInspector(driver=driver, database="neo4j")

        duplicates = inspector.duplicate_entities()

        assert len(duplicates) == 1
        group = duplicates[0]
        assert len(group) == 2
        assert {member["node_id"] for member in group} == {"1", "2"}

    def test_no_duplicates_returns_empty_list(self):
        driver = _make_driver(
            {
                "MATCH (n:__Entity__)": [
                    {
                        "node_id": "1",
                        "labels": ["__Entity__", "Vendor"],
                        "props": {"name": "Acme Corp"},
                    },
                    {
                        "node_id": "2",
                        "labels": ["__Entity__", "Vendor"],
                        "props": {"name": "Globex Inc"},
                    },
                ]
            }
        )
        inspector = KGInspector(driver=driver, database="neo4j")

        assert inspector.duplicate_entities() == []


class TestExtractionFailureRate:
    def test_returns_zero_with_note_when_no_persisted_log(self):
        driver = _make_driver({})
        inspector = KGInspector(driver=driver, database="neo4j")

        result = inspector.extraction_failure_rate()

        assert result["rate"] == 0.0
        assert "note" in result


class TestSummary:
    def test_summary_aggregates_all_d18_metrics(self, tmp_path):
        inventory_path = tmp_path / "clause_inventory.json"
        inventory_path.write_text(json.dumps({"entries": [{"clause_id": "1"}]}))

        driver = _make_driver(
            {
                "MATCH (n) RETURN count(n)": [{"c": 625}],
                "MATCH ()-[r]->() RETURN count(r)": [{"c": 1232}],
                "UNWIND labels(n)": [{"label": "User", "c": 62}],
                "COUNT { (n)--() }": [{"degree": 2}],
                "WHERE NOT (n)--()": [{"c": 0}],
                "MATCH (c:Chunk) RETURN c.text": [{"text": "clause 1 present"}],
                "MATCH (n:__Entity__)": [],
            }
        )
        inspector = KGInspector(driver=driver, database="neo4j")

        summary = inspector.summary(inventory_path=inventory_path)

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
        assert summary["node_count"] == 625
        assert summary["clause_coverage"]["total"] == 1
