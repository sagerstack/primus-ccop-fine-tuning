"""
Regression tests for EvaluateModelUseCase._aggregate_quality_categories.

P3 (2026-07-02): the summary rollup gated the RAG-only quality groups
(Retrieval Quality, Model-RAG Grounding) on `evaluation_mode != "hybrid"`, so
`graphrag` runs had their context metrics marked N/A in the summary and the
per-benchmark breakdown — even though the per-case RAGAs values existed. These
tests lock the fix: retrieval modes (hybrid, graphrag, graphrag-ontology) keep
those groups populated; non-retrieval modes (llm-only) show them N/A.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from application.use_cases.evaluate_model import (
    _RETRIEVAL_EVAL_MODES,
    EvaluateModelUseCase,
)


def _ragas_metric(name: str, score: float, applicable: bool = True):
    return SimpleNamespace(name=name, score=score, applicable=applicable)


def _result(mode: str):
    """A single evaluated case in benchmark B1 with full RAGAs metrics."""
    ragas = SimpleNamespace(
        evaluation_error=False,
        metrics=[
            _ragas_metric("context_recall", 0.88),
            _ragas_metric("context_precision", 1.00),
            _ragas_metric("context_faithfulness", 0.80),
            _ragas_metric("factual_recall", 0.90),
            _ragas_metric("answer_relevancy", 0.85),
            _ragas_metric("semantic_similarity", 0.87),
        ],
    )
    result = MagicMock()
    result.test_case.benchmark_type.short_name = "B1"
    result.evaluation_mode = mode
    result.overall_score = 0.5  # feeds the llm_judge metric
    result.ragas_evaluation = ragas
    return result


def _use_case() -> EvaluateModelUseCase:
    # _aggregate_quality_categories only reads its `results` arg, not self-state.
    return EvaluateModelUseCase(
        model_gateway=MagicMock(),
        test_case_repository=MagicMock(),
        result_repository=MagicMock(),
        logger=MagicMock(),
        ragas_service=MagicMock(),
    )


def _group_avg(categories: dict, scope: str, group_name: str, benchmark: str = "B1"):
    if scope == "overall":
        groups = categories["overall"]["groups"]
    else:
        groups = categories["by_benchmark"][benchmark]["groups"]
    for g in groups:
        if g["name"] == group_name:
            return g["average"]
    raise AssertionError(f"group {group_name!r} not found in {scope}")


@pytest.mark.parametrize("mode", sorted(_RETRIEVAL_EVAL_MODES))
def test_retrieval_modes_populate_retrieval_quality_group(mode):
    """graphrag / hybrid / graphrag-ontology must NOT N/A the context-metric groups."""
    cats = _use_case()._aggregate_quality_categories([_result(mode)])

    # Retrieval Quality = mean(context_recall, context_precision) = mean(0.88, 1.00)
    assert _group_avg(cats, "by_benchmark", "Retrieval Quality") == pytest.approx(0.94)
    assert _group_avg(cats, "overall", "Retrieval Quality") == pytest.approx(0.94)
    # Model-RAG Grounding = context_faithfulness = 0.80
    assert _group_avg(cats, "overall", "Model-RAG Grounding") == pytest.approx(0.80)


def test_llm_only_mode_marks_retrieval_groups_na():
    """Non-retrieval mode still shows context groups as N/A (None)."""
    cats = _use_case()._aggregate_quality_categories([_result("llm-only")])

    assert _group_avg(cats, "by_benchmark", "Retrieval Quality") is None
    assert _group_avg(cats, "overall", "Retrieval Quality") is None
    assert _group_avg(cats, "overall", "Model-RAG Grounding") is None


def test_graphrag_is_registered_as_a_retrieval_mode():
    """Guard against the run_id._VALID_MODES-style drift that caused P3."""
    assert "graphrag" in _RETRIEVAL_EVAL_MODES
    assert "hybrid" in _RETRIEVAL_EVAL_MODES
    assert "llm-only" not in _RETRIEVAL_EVAL_MODES
