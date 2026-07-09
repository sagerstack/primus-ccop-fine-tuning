"""
Unit tests for the Phase 10 A/B report aggregation logic (plan 10-11, D-16).

All fixtures are small in-memory dicts — no real eval-run JSON files, no
Neo4j, no filesystem I/O. This exercises `build_three_way_comparison` and its
helpers directly, proving the deltas/aggregation math is correct before it is
pointed at the real three-leg data by
`scripts/generate_phase10_ab_report.py`.
"""

import json

import pytest

from application.use_cases.ab_report import (
    CaseMetrics,
    ThreeWayComparisonResult,
    build_three_way_comparison,
    extract_case_metrics,
    extract_clause_id_from_citation,
    load_run_json_text,
    repair_test_id,
    repair_test_results,
    score_top3_from_contexts,
)


def _run_json(test_id: str, score: float, ragas_score: float = 0.7, passed: bool = True) -> dict:
    return {
        "metadata": {"total_tests": 1},
        "test_results": [
            {
                "test_id": test_id,
                "score": score,
                "ragas_score": ragas_score,
                "passed": passed,
                "metrics": [
                    {"name": "citation_correctness", "value": 0.5},
                    {"name": "factual_grounding", "value": 0.75},
                ],
                "ragas": {
                    "retrieval_quality": {
                        "context_recall": {"score": 0.8, "applicable": True},
                        "context_precision": {"score": 0.9, "applicable": True},
                    },
                    "grounding": {
                        "context_faithfulness": {"score": 0.6, "applicable": True},
                    },
                },
            }
        ],
    }


class TestLoadRunJsonTextTolerance:
    """10-01's corrupted-B04 caveat: strict=False + positional repair."""

    def test_loads_valid_json_normally(self):
        raw = json.dumps({"test_results": [{"test_id": "B01-001"}]})
        assert load_run_json_text(raw)["test_results"][0]["test_id"] == "B01-001"

    def test_tolerates_embedded_control_character(self):
        # A literal (unescaped) newline inside a string value is invalid per
        # strict JSON but is exactly the documented 10-01 corruption.
        raw = '{"test_results": [{"test_id": "\n      "}]}'
        parsed = load_run_json_text(raw)
        assert parsed["test_results"][0]["test_id"] == "\n      "

    def test_strict_json_loads_would_raise_on_the_same_input(self):
        raw = '{"test_results": [{"test_id": "\n      "}]}'
        with pytest.raises(json.JSONDecodeError):
            json.loads(raw)  # strict=True default — proves the fixture is a real repro


class TestRepairTestId:
    def test_valid_id_in_expected_order_passes_through_unchanged(self):
        order = ["B01-001", "B02-001", "B03-001"]
        assert repair_test_id("B02-001", 1, order) == "B02-001"

    def test_corrupted_id_repaired_via_position(self):
        order = ["B01-001", "B02-001", "B03-001", "B04-001"]
        assert repair_test_id("\n      ", 3, order) == "B04-001"

    def test_empty_id_repaired_via_position(self):
        order = ["B01-001", "B02-001"]
        assert repair_test_id("", 0, order) == "B01-001"

    def test_out_of_range_index_returns_original(self):
        order = ["B01-001"]
        assert repair_test_id("garbage", 5, order) == "garbage"


class TestRepairTestResults:
    def test_repairs_only_the_corrupted_entry_never_drops_cases(self):
        run = {
            "test_results": [
                {"test_id": "B01-001", "score": 0.1},
                {"test_id": "\n      ", "score": 0.2},
                {"test_id": "B03-001", "score": 0.3},
            ]
        }
        order = ["B01-001", "B02-001", "B03-001"]
        repaired = repair_test_results(run, order)
        ids = [tr["test_id"] for tr in repaired["test_results"]]
        assert ids == ["B01-001", "B02-001", "B03-001"]
        assert len(repaired["test_results"]) == 3  # no case silently dropped
        # original untouched (pure function)
        assert run["test_results"][1]["test_id"] == "\n      "


class TestExtractCaseMetrics:
    def test_pulls_score_ragas_and_judge_dims(self):
        run = _run_json("B01-001", score=0.5)
        cm = extract_case_metrics(run, "B01-001")
        assert isinstance(cm, CaseMetrics)
        assert cm.score == 0.5
        assert cm.ragas_score == 0.7
        assert cm.citation_correctness == 0.5
        assert cm.factual_grounding == 0.75
        assert cm.context_recall == 0.8
        assert cm.context_precision == 0.9
        assert cm.context_faithfulness == 0.6

    def test_returns_none_for_missing_case(self):
        run = _run_json("B01-001", score=0.5)
        assert extract_case_metrics(run, "B99-001") is None

    def test_returns_none_for_none_run(self):
        assert extract_case_metrics(None, "B01-001") is None


class TestExtractClauseIdFromCitation:
    def test_extracts_clause_id_from_document_prefixed_citation(self):
        assert extract_clause_id_from_citation("CCoP 2.0::5.1.1") == "5.1.1"

    def test_extracts_clause_id_from_table_citation(self):
        assert extract_clause_id_from_citation("CCoP 2.0::1.2.1::table::3") == "1.2.1"

    def test_returns_none_for_neo4j_element_id(self):
        # Phase 9's unfixed emergent adapter: single-colon separated, no "::"
        assert extract_clause_id_from_citation("4:73019583-14cc-4aee-a046:145") is None

    def test_returns_none_for_empty(self):
        assert extract_clause_id_from_citation("") is None


class TestScoreTop3FromContexts:
    def test_scores_hit_and_recall_from_real_clause_citations(self):
        contexts = [
            {"citation_id": "CCoP 2.0::5.6.2"},
            {"citation_id": "CCoP 2.0::1.2.1"},
            {"citation_id": "CCoP 2.0::9.9.9"},
        ]
        hit3, recall3 = score_top3_from_contexts(contexts, {"1.2.1", "1.4.1"})
        assert hit3 == 1
        assert recall3 == pytest.approx(0.5)  # 1 of 2 gold clauses present

    def test_not_computable_for_neo4j_element_ids(self):
        contexts = [
            {"citation_id": "4:73019583-abc:145"},
            {"citation_id": "4:73019583-abc:146"},
        ]
        hit3, recall3 = score_top3_from_contexts(contexts, {"1.2.1"})
        assert (hit3, recall3) == (None, None)

    def test_not_computable_for_empty_contexts(self):
        assert score_top3_from_contexts([], {"1.2.1"}) == (None, None)


class TestBuildThreeWayComparison:
    def test_aggregates_all_three_legs_per_case(self):
        ontology_run = _run_json("B01-001", score=0.6)
        graphrag_run = _run_json("B01-001", score=0.4)
        hybrid_run = _run_json("B01-001", score=0.5)

        result = build_three_way_comparison(
            ontology_run=ontology_run,
            graphrag_run=graphrag_run,
            hybrid_run=hybrid_run,
            test_ids=["B01-001"],
        )

        assert isinstance(result, ThreeWayComparisonResult)
        assert result.baseline_present is True
        row = result.rows[0]
        assert row.benchmark == "B01"
        assert row.ontology.score == 0.6
        assert row.graphrag.score == 0.4
        assert row.hybrid.score == 0.5
        assert row.delta_score_vs_graphrag == pytest.approx(0.2)
        assert row.delta_score_vs_hybrid == pytest.approx(0.1)

    def test_baseline_present_false_when_graphrag_run_missing(self):
        # D-16 hard-dependency caveat: no baseline -> flag explicitly.
        result = build_three_way_comparison(
            ontology_run=_run_json("B01-001", score=0.6),
            graphrag_run=None,
            hybrid_run=_run_json("B01-001", score=0.5),
            test_ids=["B01-001"],
        )
        assert result.baseline_present is False
        assert result.rows[0].graphrag is None
        assert result.rows[0].delta_score_vs_graphrag is None

    def test_improved_regressed_unchanged_classification(self):
        result = build_three_way_comparison(
            ontology_run={
                "test_results": [
                    {"test_id": "B01-001", "score": 0.6},
                    {"test_id": "B02-001", "score": 0.2},
                    {"test_id": "B03-001", "score": 0.3},
                ]
            },
            graphrag_run={
                "test_results": [
                    {"test_id": "B01-001", "score": 0.4},
                    {"test_id": "B02-001", "score": 0.5},
                    {"test_id": "B03-001", "score": 0.3},
                ]
            },
            hybrid_run={"test_results": []},
            test_ids=["B01-001", "B02-001", "B03-001"],
        )
        assert result.improved_vs_graphrag == ["B01-001"]
        assert result.regressed_vs_graphrag == ["B02-001"]
        assert result.unchanged_vs_graphrag == ["B03-001"]

    def test_ontology_clause_hit_injected_from_harness_output(self):
        result = build_three_way_comparison(
            ontology_run=_run_json("B01-001", score=0.6),
            graphrag_run=None,
            hybrid_run=None,
            test_ids=["B01-001"],
            ontology_clause_hit_by_id={
                "B01-001": {"hit_at_3": 1, "recall_at_3": 0.5, "recall_at_pool": 1.0}
            },
        )
        row = result.rows[0]
        assert row.ontology.hit_at_3 == 1
        assert row.ontology.recall_at_3 == 0.5
        assert row.ontology.recall_at_pool == 1.0

    def test_hybrid_clause_hit_scored_from_contexts_sidecar_top3_only(self):
        result = build_three_way_comparison(
            ontology_run=None,
            graphrag_run=None,
            hybrid_run=_run_json("B01-001", score=0.5),
            test_ids=["B01-001"],
            hybrid_contexts={
                "B01-001": [
                    {"citation_id": "CCoP 2.0::1.2.1"},
                    {"citation_id": "CCoP 2.0::5.6.2"},
                    {"citation_id": "CCoP 2.0::9.9.9"},
                ]
            },
            gold_sets={"B01-001": {"1.2.1", "1.4.1"}},
        )
        row = result.rows[0]
        assert row.hybrid.hit_at_3 == 1
        assert row.hybrid.recall_at_3 == pytest.approx(0.5)
        # recall@pool intentionally not computable from a top-3-only sidecar
        assert row.hybrid.recall_at_pool is None

    def test_graphrag_clause_hit_not_computable_from_element_ids(self):
        # Phase 9's basic-graphrag leg: raw Neo4j elementIds, not
        # clause-anchored -- must surface as not-computable, not a fake 0.
        result = build_three_way_comparison(
            ontology_run=None,
            graphrag_run=_run_json("B01-001", score=0.4),
            hybrid_run=None,
            test_ids=["B01-001"],
            graphrag_contexts={
                "B01-001": [
                    {"citation_id": "4:73019583-abc:145"},
                    {"citation_id": "4:73019583-abc:146"},
                ]
            },
            gold_sets={"B01-001": {"1.2.1", "1.4.1"}},
        )
        row = result.rows[0]
        assert row.graphrag.hit_at_3 is None
        assert row.graphrag.recall_at_3 is None

    def test_aggregate_skips_none_values(self):
        result = build_three_way_comparison(
            ontology_run={
                "test_results": [
                    {"test_id": "B01-001", "score": 0.4},
                    {"test_id": "B02-001", "score": 0.6},
                ]
            },
            graphrag_run=None,
            hybrid_run=None,
            test_ids=["B01-001", "B02-001"],
        )
        assert result.aggregate("ontology", "score") == pytest.approx(0.5)
        assert result.aggregate("graphrag", "score") is None  # no data at all
