"""
Tests for the D-14/D-17 coverage checker (plan 10-03, Task 1).
"""

import json

from rag.graph.ontology.discovery.coverage_check import (
    benchmark_coverage,
    gold_relation_coverage_from_cases,
)
from rag.graph.ontology.gold_relation_parser import CaseGoldRelations

FIXTURE_ONTOLOGY = {
    "node_types": [
        {
            "label": "Clause",
            "description": "A CCoP regulatory clause or provision",
            "example_terms": ["clause", "section", "provision"],
            "provenance": ["seeded (D-08)"],
        },
        {
            "label": "Waiver",
            "description": "A waiver or exception granted under section 11(7)",
            "example_terms": ["waiver", "exception"],
            "provenance": ["method_c:benchmark_definitions"],
        },
    ],
    # Deliberately missing CANNOT_SATISFY (a D-18 relation) — the gap this
    # test suite must surface.
    "relationship_types": ["GOVERNS", "REQUIRES", "NOT_DESIGNATED_AS"],
    "patterns": [],
}


class TestGoldRelationCoverageFromCases:
    def test_missing_relations_includes_gap(self):
        cases = [
            CaseGoldRelations(
                test_id="B01-001",
                triples=[("x", "GOVERNS", "y"), ("x", "CANNOT_SATISFY", "z")],
                relation_types={"GOVERNS", "CANNOT_SATISFY"},
                entity_terms={"x", "y", "z"},
                clause_citations=["1.2.1"],
            )
        ]
        report = gold_relation_coverage_from_cases(FIXTURE_ONTOLOGY, cases)
        assert "CANNOT_SATISFY" in report["missing_relations"]
        assert "GOVERNS" not in report["missing_relations"]

    def test_per_case_missing_relations(self):
        cases = [
            CaseGoldRelations(
                test_id="B22-001",
                triples=[("x", "CANNOT_SATISFY", "y")],
                relation_types={"CANNOT_SATISFY"},
                entity_terms={"x", "y"},
                clause_citations=[],
            )
        ]
        report = gold_relation_coverage_from_cases(FIXTURE_ONTOLOGY, cases)
        assert report["per_case"]["B22-001"]["missing_relations"] == ["CANNOT_SATISFY"]

    def test_no_gap_when_ontology_covers_all_gold_relations(self):
        cases = [
            CaseGoldRelations(
                test_id="B01-001",
                triples=[("x", "GOVERNS", "y")],
                relation_types={"GOVERNS"},
                entity_terms={"x", "y"},
                clause_citations=[],
            )
        ]
        report = gold_relation_coverage_from_cases(FIXTURE_ONTOLOGY, cases)
        assert report["missing_relations"] == []

    def test_empty_cases_returns_empty_report(self):
        report = gold_relation_coverage_from_cases(FIXTURE_ONTOLOGY, [])
        assert report["gold_relation_types"] == []
        assert report["missing_relations"] == []
        assert report["cases_covered"] == 0


class TestBenchmarkCoverage:
    @staticmethod
    def _write_jsonl(path, records):
        with open(path, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")

    def test_maps_benchmark_to_covering_type_via_keyword_overlap(self, tmp_path):
        self._write_jsonl(
            tmp_path / "b22_waiver_exception_reasoning.jsonl",
            [
                {
                    "test_id": "B22-001",
                    "benchmark_id": "B22",
                    "input": {
                        "question": "Can a CIIO request a waiver from a specific clause requirement?"
                    },
                    "ground_truth": {
                        "expected_response": "Section 11(7) allows the Commissioner to grant a waiver or exception."
                    },
                    "key_facts": [{"fact": "Waiver requests must be justified", "tier": "critical"}],
                }
            ],
        )
        report = benchmark_coverage(FIXTURE_ONTOLOGY, tmp_path)
        assert "B22" in report["benchmark_map"]
        assert "Waiver" in report["benchmark_map"]["B22"]["covering_types"]
        assert "B22" not in report["unmapped"]

    def test_flags_unmapped_benchmark(self, tmp_path):
        self._write_jsonl(
            tmp_path / "b99_unrelated_topic.jsonl",
            [
                {
                    "test_id": "B99-001",
                    "benchmark_id": "B99",
                    "input": {"question": "zzqxvv wwbbnn plplpl kjkjkj?"},
                    "ground_truth": {"expected_response": "qqzzvv nnbbww lplplp jkjkjk."},
                    "key_facts": [],
                }
            ],
        )
        report = benchmark_coverage(FIXTURE_ONTOLOGY, tmp_path)
        assert "B99" in report["unmapped"]
        assert report["benchmark_map"]["B99"]["covering_types"] == []

    def test_all_benchmarks_present_with_no_unmapped_when_covered(self, tmp_path):
        self._write_jsonl(
            tmp_path / "b01_clause_scope.jsonl",
            [
                {
                    "test_id": "B01-001",
                    "benchmark_id": "B01",
                    "input": {"question": "Does this clause apply to the section in question?"},
                    "ground_truth": {"expected_response": "The clause governs the relevant provision."},
                    "key_facts": [],
                }
            ],
        )
        self._write_jsonl(
            tmp_path / "b22_waiver_exception_reasoning.jsonl",
            [
                {
                    "test_id": "B22-001",
                    "benchmark_id": "B22",
                    "input": {
                        "question": "Can a CIIO request a waiver from a specific clause requirement?"
                    },
                    "ground_truth": {"expected_response": "Section 11(7) allows a waiver or exception."},
                    "key_facts": [],
                }
            ],
        )
        report = benchmark_coverage(FIXTURE_ONTOLOGY, tmp_path)
        assert report["total_benchmarks"] == 2
        assert report["unmapped"] == []

    def test_direct_provenance_match_covers_benchmark_without_keyword_overlap(self, tmp_path):
        """A node type whose provenance explicitly names the benchmark_id
        counts as covering, even with zero keyword overlap in the question/
        response text."""
        self._write_jsonl(
            tmp_path / "b22_waiver_exception_reasoning.jsonl",
            [
                {
                    "test_id": "B22-001",
                    "benchmark_id": "B22",
                    "input": {"question": "abstract regulatory scenario prompt text only"},
                    "ground_truth": {"expected_response": "abstract regulatory scenario response text only"},
                    "key_facts": [],
                }
            ],
        )
        ontology = {
            "node_types": [
                {
                    "label": "ExplicitProvenanceType",
                    "description": "",
                    "example_terms": [],
                    "provenance": ["B22"],
                }
            ],
            "relationship_types": [],
            "patterns": [],
        }
        report = benchmark_coverage(ontology, tmp_path)
        assert "ExplicitProvenanceType" in report["benchmark_map"]["B22"]["covering_types"]

    def test_ignores_deprecated_records(self, tmp_path):
        self._write_jsonl(
            tmp_path / "b22_waiver_exception_reasoning.jsonl",
            [
                {
                    "test_id": "B22-001",
                    "benchmark_id": "B22",
                    "status": "deprecated",
                    "input": {"question": "waiver exception clause"},
                    "ground_truth": {"expected_response": "waiver"},
                    "key_facts": [],
                },
                {
                    "test_id": "B22-002",
                    "benchmark_id": "B22",
                    "input": {"question": "Can a CIIO request a waiver or exception?"},
                    "ground_truth": {"expected_response": "Yes, a waiver may be granted."},
                    "key_facts": [],
                },
            ],
        )
        report = benchmark_coverage(FIXTURE_ONTOLOGY, tmp_path)
        assert "B22" in report["benchmark_map"]
        assert "Waiver" in report["benchmark_map"]["B22"]["covering_types"]
