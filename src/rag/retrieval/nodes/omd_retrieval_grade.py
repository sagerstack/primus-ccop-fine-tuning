"""Deterministic weak-retrieval detector for the graphont path (Phase 12, Slice C).

Pure-Python, side-effect-scoped classifier (NOT a LangGraph node). It reads the
Slice-B diagnostic trace (``state["retrieval_trace"]``) plus the protected, read-only
``state["retrieval_succeeded"]`` flag, applies deterministic v1 rules, and writes three
NEW, interpretable keys to ``state``:

  * ``retrieval_grade``          -> "strong" | "low_confidence" | "empty"
  * ``retrieval_grade_reasons``  -> list[str] naming ONLY the rule(s) that triggered
  * ``should_requery``           -> bool (Slice D reads this; this slice does NOT re-query)

Scope discipline (12-02 §1 / ADR-009): DETECT ONLY. This module re-routes nothing and
mutates none of the four protected Slice-B output keys
(``filtered_documents``, ``documents``, ``is_rag_augmented``, ``retrieval_succeeded``).
graphont stays byte/structure-identical; only the graphont-agentic loop (Slice D) will
consume ``retrieval_grade``/``should_requery``.

------------------------------------------------------------------------------------------
v1 RULE SHAPE (thresholds are PLACEHOLDERS — calibrated later from Slice A0). Signal
mappings are grounded in the real ``retrieve()`` return contract (verified by scout recon):

  ce_confidence      = retrieval_trace["ce_confidence"]  (float|None; normalized CE
                       discrimination in [0,1] == the adaptive `conf` from retrieve()).
                       None when the reranker did not run (RRF-only) or raised. Per the
                       team-lead ruling ("None != below-threshold; None = untrustworthy"),
                       None is treated as a WEAK signal -> grade low_confidence with reason
                       "ce_confidence=None(untrustworthy)". It does NOT set should_requery,
                       however: a re-query cannot restore a reranker that did not run, so
                       auto-requery is reserved for a *computed*-low confidence (see below)
                       to avoid unbounded requery loops when the CE is globally unavailable
                       (Slice D owns requery budgeting/guards).
  top1_rerank_score  = retrieval_trace["candidates"][0]["ce_score"]  (the actual
                       cross-encoder score). Deliberately NOT candidates[0]["score"]:
                       `score` is an RRF-scale fused value bounded at ~<=0.04
                       (eff_ce/(RRF_K+1) + rerank_rrf_w/(RRF_K+1) with RRF_K=60), so
                       `score < TAU_TOP1(0.5)` would fire on 100% of retrievals and render
                       the rule useless. `ce_score` is the calibratable rerank signal.
                       (This overrides team-lead non-binding guidance 3(a) on evidence.)
                       None -> rule NOT-APPLICABLE (skipped).
  top1_top2_margin   = candidates[0]["ce_score"] - candidates[1]["ce_score"]. Requires
                       >=2 candidates, both with a CE score; otherwise NOT-APPLICABLE.
  concept_coverage   = DEFERRED for v1. Not computable from retrieval_trace as populated
                       by Slice B (per-candidate concept sets are not persisted; adding
                       them would require forbidden Slice-B edits). TAU_COVERAGE is
                       reserved for forward-compatibility but the rule is inactive.
  retrieval_succeeded= state["retrieval_succeeded"] (protected; read-only here).

GRADE:
  empty          iff retrieval_trace is absent OR not retrieval_succeeded
  low_confidence iff (not empty) and ANY active low-confidence rule fires
  strong         otherwise

SHOULD_REQUERY (conservative v1): True iff grade == low_confidence AND ce_confidence was
PRESENT and below TAU_CONF (a *computed*-low confidence). "empty" never re-queries (same
query -> same empty result; reformulation is a Slice-D concern) and "strong" never
re-queries. A purely top1/margin-driven low_confidence, and a None-confidence
(untrustworthy) low_confidence, do NOT re-query in v1 (a re-query is unlikely to help
without query reformulation / a working reranker, which Slice D owns).
"""
from typing import Any, Dict, List, Optional

from rag.retrieval.state.graph_state import GraphState

# ---- v1 thresholds (PLACEHOLDERS; calibrated from Slice A0 later) -------------------------
TAU_CONF = 0.3       # ce_confidence below this -> weak
TAU_TOP1 = 0.5       # top1 cross-encoder score below this -> weak
TAU_MARGIN = 0.05    # top1-top2 CE-score margin below this -> weak
TAU_COVERAGE = 0.5   # RESERVED (concept_coverage deferred; rule inactive in v1)

GRADE_STRONG = "strong"
GRADE_LOW_CONFIDENCE = "low_confidence"
GRADE_EMPTY = "empty"

# The four Slice-B output keys the detector must never write (documented invariant).
_PROTECTED_KEYS = ("filtered_documents", "documents", "is_rag_augmented", "retrieval_succeeded")


def _fmt(v: float) -> str:
    """Deterministic compact float rendering for reason strings (e.g. 0.0024643 -> '0.002464')."""
    return f"{v:.4g}"


def _top1_ce_score(candidates: List[Dict[str, Any]]) -> Optional[float]:
    if not candidates:
        return None
    return candidates[0].get("ce_score")


def _top1_top2_margin(candidates: List[Dict[str, Any]]) -> Optional[float]:
    if len(candidates) < 2:
        return None
    s1 = candidates[0].get("ce_score")
    s2 = candidates[1].get("ce_score")
    if s1 is None or s2 is None:
        return None
    return s1 - s2


def omd_retrieval_grade(state: GraphState) -> GraphState:
    """Classify the current graphont retrieval and annotate ``state`` in place.

    Deterministic and side-effect-scoped: identical input state -> identical
    (retrieval_grade, retrieval_grade_reasons, should_requery). Reads retrieval_trace +
    retrieval_succeeded; writes only the three new keys.
    """
    # Establish the new keys with defaults first (Slice-B `setdefault` convention), so a
    # downstream consumer always finds them even if a later branch is added.
    state.setdefault("retrieval_grade", None)
    state.setdefault("retrieval_grade_reasons", [])
    state.setdefault("should_requery", False)

    reasons: List[str] = []

    # ---- EMPTY: trace absent (retrieval raised -> dispatcher popped it) or retrieval failed.
    trace = state.get("retrieval_trace")
    if trace is None:
        state["retrieval_grade"] = GRADE_EMPTY
        state["retrieval_grade_reasons"] = ["empty: retrieval_trace absent"]
        state["should_requery"] = False
        return state
    if not state.get("retrieval_succeeded", False):
        state["retrieval_grade"] = GRADE_EMPTY
        state["retrieval_grade_reasons"] = ["empty: retrieval_succeeded=False"]
        state["should_requery"] = False
        return state

    # ---- LOW-CONFIDENCE: zero ranked candidates but retrieval succeeded. -----------------
    # Reachable: omd_pack sets retrieval_succeeded=bool(docs) and docs can come from injected
    # definitions ALONE, so succeeded==True with candidates==[] is a real (not hypothetical)
    # state. "No ranked candidates" is a weakness, not "strong" (no signal != strong). This
    # short-circuits before the ce_confidence rule for a precise reason string.
    candidates = trace.get("candidates") or []
    if not candidates:
        state["retrieval_grade"] = GRADE_LOW_CONFIDENCE
        state["retrieval_grade_reasons"] = ["no_ranked_candidates"]
        state["should_requery"] = False
        return state

    # ---- LOW-CONFIDENCE rules (each active only when its signal is computable). ----------
    ce_confidence = trace.get("ce_confidence")

    # ce_confidence rule. None is treated as a weakness (untrustworthy) per team-lead ruling,
    # but only a *computed*-low confidence arms should_requery (see module docstring).
    ce_confidence_requery = False
    if ce_confidence is None:
        reasons.append("ce_confidence=None(untrustworthy)")
    elif ce_confidence < TAU_CONF:
        reasons.append(f"ce_confidence={_fmt(ce_confidence)}<{TAU_CONF}")
        ce_confidence_requery = True

    top1 = _top1_ce_score(candidates)
    if top1 is not None and top1 < TAU_TOP1:
        reasons.append(f"top1_rerank_score={_fmt(top1)}<{TAU_TOP1}")

    margin = _top1_top2_margin(candidates)
    if margin is not None and margin < TAU_MARGIN:
        reasons.append(f"top1_top2_margin={_fmt(margin)}<{TAU_MARGIN}")

    # concept_coverage: DEFERRED v1 (not computable from retrieval_trace) — no rule.

    if reasons:
        state["retrieval_grade"] = GRADE_LOW_CONFIDENCE
        state["retrieval_grade_reasons"] = reasons
        # Conservative v1: only a *computed*-low ce_confidence warrants a re-query.
        state["should_requery"] = ce_confidence_requery
        return state

    # ---- STRONG: no weakness detected.
    state["retrieval_grade"] = GRADE_STRONG
    state["retrieval_grade_reasons"] = []
    state["should_requery"] = False
    return state


__all__ = ["omd_retrieval_grade", "TAU_CONF", "TAU_TOP1", "TAU_MARGIN", "TAU_COVERAGE"]
