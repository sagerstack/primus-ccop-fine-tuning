"""
Unit tests for `ccop-eval graph inspect` / `graph stats` (Phase 9, D-18).

KGInspector and the Neo4j driver are fully mocked — these tests never touch
the network or a live Neo4j instance.
"""
import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from rag.graph.cli.graph import graph_app

runner = CliRunner()


def _fake_summary() -> dict:
    return {
        "node_count": 625,
        "edge_count": 1232,
        "entity_type_distribution": {"CybersecurityIncident": 77, "User": 62},
        "degree_distribution": {
            "min": 1,
            "max": 40,
            "avg": 3.94,
            "buckets": {"0": 0, "1-5": 456, "6-20": 161, "21+": 8},
        },
        "orphan_nodes": 0,
        "clause_coverage": {"covered": 496, "total": 738, "coverage_ratio": 0.6721},
        "duplicate_entities": [
            [
                {"node_id": "1", "labels": ["User"], "name": "user123"},
                {"node_id": "2", "labels": ["User"], "name": "user123"},
            ]
        ],
        "extraction_failure_rate": {
            "rate": 0.0,
            "note": "No persisted failure log in Neo4j.",
        },
    }


def _mock_settings() -> MagicMock:
    settings = MagicMock()
    settings.neo4j_uri = "bolt://localhost:7687"
    settings.neo4j_user = "neo4j"
    settings.neo4j_password = "test-pw"
    settings.neo4j_database = "neo4j"
    return settings


class TestInspectCommand:
    def test_help_exits_zero(self):
        result = runner.invoke(graph_app, ["inspect", "--help"])
        assert result.exit_code == 0

    def test_inspect_output_contains_clause_coverage(self):
        with (
            patch("rag.graph.cli.graph.get_settings", return_value=_mock_settings()),
            patch("rag.graph.cli.graph.neo4j.GraphDatabase.driver", return_value=MagicMock()),
            patch("rag.graph.cli.graph.KGInspector") as mock_inspector_cls,
        ):
            mock_inspector_cls.return_value.summary.return_value = _fake_summary()

            result = runner.invoke(graph_app, ["inspect"])

            assert result.exit_code == 0
            assert "clause_coverage" in result.stdout
            assert "496/738" in result.stdout


class TestStatsCommand:
    def test_help_exits_zero(self):
        result = runner.invoke(graph_app, ["stats", "--help"])
        assert result.exit_code == 0

    def test_stats_prints_valid_json_to_stdout(self):
        with (
            patch("rag.graph.cli.graph.get_settings", return_value=_mock_settings()),
            patch("rag.graph.cli.graph.neo4j.GraphDatabase.driver", return_value=MagicMock()),
            patch("rag.graph.cli.graph.KGInspector") as mock_inspector_cls,
        ):
            mock_inspector_cls.return_value.summary.return_value = _fake_summary()

            result = runner.invoke(graph_app, ["stats"])

            assert result.exit_code == 0
            payload = json.loads(result.stdout)
            assert payload["clause_coverage"]["covered"] == 496
            assert payload["node_count"] == 625

    def test_stats_output_writes_valid_json_file(self, tmp_path):
        output_path = tmp_path / "kg-stats.json"
        with (
            patch("rag.graph.cli.graph.get_settings", return_value=_mock_settings()),
            patch("rag.graph.cli.graph.neo4j.GraphDatabase.driver", return_value=MagicMock()),
            patch("rag.graph.cli.graph.KGInspector") as mock_inspector_cls,
        ):
            mock_inspector_cls.return_value.summary.return_value = _fake_summary()

            result = runner.invoke(
                graph_app, ["stats", "--output", str(output_path)]
            )

            assert result.exit_code == 0
            payload = json.loads(output_path.read_text())
            assert payload["clause_coverage"] == {
                "covered": 496,
                "total": 738,
                "coverage_ratio": 0.6721,
            }
            assert payload["node_count"] == 625
            assert payload["edge_count"] == 1232
