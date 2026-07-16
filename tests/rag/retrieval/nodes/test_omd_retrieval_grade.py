"""Slice C — deterministic weak-retrieval detector tests (no network, no Neo4j).

Verifies the five reviewer invariants:
  (a) deterministic — same input -> identical output twice
  (b) every state mutation has a clear reason string (or is 'strong' with [] reasons)
  (d) detector does NOT mutate the 4 protected Slice-B keys
  + golden-table conformance (input state -> expected grade/reasons/should_requery)
  + additive-only: detector writes ONLY the 3 new keys
"""
import copy
import json
from pathlib import Path

import pytest

from rag.retrieval.nodes.omd_retrieval_grade import (
    GRADE_EMPTY,
    GRADE_LOW_CONFIDENCE,
    GRADE_STRONG,
    TAU_CONF,
    TAU_MARGIN,
    TAU_TOP1,
    omd_retrieval_grade,
)

_GOLDEN = (
    Path(__file__).resolve().parents[4]
    / ".planning" / "phases" / "12-agentic-graphont-retrieval-quality-loop"
    / "slice-c-grade-goldens.json"
)

_PROTECTED_KEYS = ("filtered_documents", "documents", "is_rag_augmented", "retrieval_succeeded")
_NEW_KEYS = {"retrieval_grade", "retrieval_grade_reasons", "should_requery"}


def _cases():
    data = json.loads(_GOLDEN.read_text())
    return [pytest.param(c, id=c["name"]) for c in data["cases"]]


@pytest.mark.parametrize("case", _cases())
def test_golden_triples(case):
    """input_state -> expected (retrieval_grade, retrieval_grade_reasons, should_requery)."""
    state = copy.deepcopy(case["input_state"])
    omd_retrieval_grade(state)
    exp = case["expected"]
    assert state["retrieval_grade"] == exp["retrieval_grade"], case["name"]
    assert state["retrieval_grade_reasons"] == exp["retrieval_grade_reasons"], case["name"]
    assert state["should_requery"] == exp["should_requery"], case["name"]


@pytest.mark.parametrize("case", _cases())
def test_deterministic(case):
    """(a) Running twice on the same input yields byte-identical grade/reasons/should_requery."""
    s1 = copy.deepcopy(case["input_state"])
    s2 = copy.deepcopy(case["input_state"])
    omd_retrieval_grade(s1)
    omd_retrieval_grade(s2)
    triple1 = (s1["retrieval_grade"], s1["retrieval_grade_reasons"], s1["should_requery"])
    triple2 = (s2["retrieval_grade"], s2["retrieval_grade_reasons"], s2["should_requery"])
    assert triple1 == triple2
    # Idempotent: a second pass over the SAME state does not drift.
    omd_retrieval_grade(s1)
    triple3 = (s1["retrieval_grade"], s1["retrieval_grade_reasons"], s1["should_requery"])
    assert triple3 == triple1


@pytest.mark.parametrize("case", _cases())
def test_reasons_are_nonempty_strings_when_weak(case):
    """(b) Every non-strong grade carries >=1 human-readable reason string; strong carries none."""
    state = copy.deepcopy(case["input_state"])
    omd_retrieval_grade(state)
    reasons = state["retrieval_grade_reasons"]
    assert isinstance(reasons, list)
    assert all(isinstance(r, str) and r for r in reasons)
    if state["retrieval_grade"] == GRADE_STRONG:
        assert reasons == []
    else:
        assert len(reasons) >= 1


@pytest.mark.parametrize("case", _cases())
def test_does_not_mutate_protected_keys(case):
    """(d) Detector never writes/alters the 4 protected Slice-B output keys."""
    base = copy.deepcopy(case["input_state"])
    # Seed protected keys with sentinels; detector must leave them byte-identical.
    sentinels = {
        "filtered_documents": ["SENTINEL_FD"],
        "documents": ["SENTINEL_D"],
        "is_rag_augmented": "SENTINEL_RAG",
    }
    state = copy.deepcopy(base)
    state.update(sentinels)
    # Preserve whatever retrieval_succeeded the case declared (it's a protected input).
    succeeded_before = state.get("retrieval_succeeded")
    omd_retrieval_grade(state)
    assert state["filtered_documents"] == ["SENTINEL_FD"]
    assert state["documents"] == ["SENTINEL_D"]
    assert state["is_rag_augmented"] == "SENTINEL_RAG"
    assert state.get("retrieval_succeeded") == succeeded_before


@pytest.mark.parametrize("case", _cases())
def test_additive_keys_only(case):
    """Detector adds ONLY the three new keys relative to the input state."""
    base = copy.deepcopy(case["input_state"])
    before = set(base)
    state = copy.deepcopy(base)
    omd_retrieval_grade(state)
    added = set(state) - before
    assert added <= _NEW_KEYS
    assert _NEW_KEYS <= set(state)  # all three are always present after the detector runs


def test_grade_values_are_in_enum():
    """retrieval_grade is always one of the three declared values for the golden set."""
    valid = {GRADE_STRONG, GRADE_LOW_CONFIDENCE, GRADE_EMPTY}
    for case in json.loads(_GOLDEN.read_text())["cases"]:
        state = copy.deepcopy(case["input_state"])
        omd_retrieval_grade(state)
        assert state["retrieval_grade"] in valid


def test_thresholds_are_expected_v1_defaults():
    """Guard the v1 placeholder thresholds so a silent change is caught."""
    assert (TAU_CONF, TAU_TOP1, TAU_MARGIN) == (0.3, 0.5, 0.05)


def test_dispatcher_isolates_detector_exception():
    """Dispatcher fault path: a detector exception -> grade='unknown', reason appended,
    should_requery=False, and the packed docs are PRESERVED (must not fall through to the
    empty-context fallback). Locks the degrade-safe contract (reviewer defect #2)."""
    import rag.retrieval.nodes.omd_context_assembly as disp
    from rag.graph.ontology_v2 import omd_retrieval

    payload = {
        "definitions": [], "ranked_by": "ce+rrf(conf=0.90)", "d_cand": 2, "ce_confidence": 0.9,
        "results": [
            {"kind": "clause", "citation_id": "CCoP::1", "doc": "CCoP", "text": "clause one",
             "score": 0.04, "ce_score": 5.0, "rrf": 0.04, "ch1": 1.0, "bm25": 1.0, "dense": 0.5},
            {"kind": "clause", "citation_id": "CCoP::2", "doc": "CCoP", "text": "clause two",
             "score": 0.03, "ce_score": 3.0, "rrf": 0.03, "ch1": 1.0, "bm25": 1.0, "dense": 0.5},
        ],
    }
    orig_retrieve = omd_retrieval.retrieve
    orig_detector = disp.omd_retrieval_grade
    omd_retrieval.retrieve = lambda *a, **k: payload

    def _boom(_s):
        raise RuntimeError("boom")

    disp.omd_retrieval_grade = _boom
    try:
        state = disp.omd_context_assembly({"mode": "graphont", "query": "q"})
    finally:
        omd_retrieval.retrieve = orig_retrieve
        disp.omd_retrieval_grade = orig_detector

    assert state["retrieval_grade"] == "unknown"
    assert any("detector_exception" in r for r in state["retrieval_grade_reasons"])
    assert state["should_requery"] is False
    # Degrade-safe: the successfully packed docs survive the detector fault.
    assert len(state["documents"]) == 2
    assert state["retrieval_succeeded"] is True
