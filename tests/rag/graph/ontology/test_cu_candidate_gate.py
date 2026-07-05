"""
Policy Graph CU Candidate Gate tests (Phase 11, 11-04b / D-32).

Pure routing logic -- no Neo4j, no LLM. Runs under `pytest -m "not
integration"`.
"""

from __future__ import annotations

import pytest

from rag.graph.ontology.cu_candidate_gate import (
    ROUTE_FORCE_PREMISE_INTERPRETATION,
    ROUTE_LLM_CLASSIFY,
    Candidate,
    route_candidates,
)


def _clause(clause_id, source_doc, is_structural_header=False, function_type="", doc_class="", text="body"):
    return {
        "clause_id": clause_id,
        "source_doc": source_doc,
        "citation_id": f"{source_doc[:3]}-{clause_id}",
        "function_type": function_type,
        "doc_class": doc_class,
        "text": text,
        "is_structural_header": is_structural_header,
    }


class TestRouteCandidates:
    def test_structural_headers_are_dropped(self):
        clauses = [
            _clause("5", "CCoP 2.0", is_structural_header=True),
            _clause("5.7.1", "CCoP 2.0"),
        ]
        cands = route_candidates(clauses)
        assert [c.clause_id for c in cands] == ["5.7.1"]

    def test_rtf_forced_to_interpretive_premise(self):
        cands = route_candidates([_clause("15.24", "CCoP Response to Feedback")])
        assert cands[0].route == ROUTE_FORCE_PREMISE_INTERPRETATION

    def test_all_rtf_route_to_force_premise_none_to_llm(self):
        clauses = [_clause(f"11.{i}", "CCoP Response to Feedback") for i in range(1, 40)]
        cands = route_candidates(clauses)
        assert all(c.route == ROUTE_FORCE_PREMISE_INTERPRETATION for c in cands)
        assert not any(c.route == ROUTE_LLM_CLASSIFY for c in cands)

    def test_guidance_doc_routes_to_llm_not_forced_premise(self):
        # A "should"-style SBD clause must be LLM-decided, not wholesale-premised.
        cands = route_candidates([_clause("2.1", "Security By Design", doc_class="guidance")])
        assert cands[0].route == ROUTE_LLM_CLASSIFY

    def test_ccop_and_act_route_to_llm(self):
        clauses = [
            _clause("5.7.1", "CCoP 2.0", doc_class="binding"),
            _clause("section 7", "Cybersecurity Act 2018", doc_class="binding"),
        ]
        cands = route_candidates(clauses)
        assert all(c.route == ROUTE_LLM_CLASSIFY for c in cands)

    def test_hints_carried_not_lost(self):
        cands = route_candidates(
            [_clause("5.7.1", "CCoP 2.0", function_type="ControlClause", doc_class="binding")]
        )
        assert cands[0].function_type == "ControlClause"
        assert cands[0].doc_class == "binding"
        assert isinstance(cands[0], Candidate)

    def test_unregistered_source_doc_raises(self):
        with pytest.raises(ValueError, match="No D-08 citation-namespace prefix"):
            route_candidates([_clause("1", "Some Unknown Doc")])

    def test_candidate_count_excludes_structural(self):
        clauses = [
            _clause("5", "CCoP 2.0", is_structural_header=True),
            _clause("5.7", "CCoP 2.0", is_structural_header=True),
            _clause("5.7.1", "CCoP 2.0"),
            _clause("5.7.2", "CCoP 2.0"),
        ]
        assert len(route_candidates(clauses)) == 2
