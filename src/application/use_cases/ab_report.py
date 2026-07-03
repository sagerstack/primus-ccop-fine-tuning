"""
Phase 10 A/B Report Aggregation (plan 10-11, D-16)

Pure aggregation logic for the phase's headline deliverable: the three-way
A/B comparison (graphrag-ontology vs basic graphrag [Phase 9, 10-01 baseline]
vs hybrid [canonical `bdc4927d`]) on the identical 18-case fixed GT,
isolating the single variable — extraction governance (D-16).

Every function here is pure: given already-loaded dicts (parsed run JSONs,
contexts sidecars, the `graph clause-hit` output, and gold clause sets), it
computes deltas and per-leg case metrics without touching the filesystem,
Neo4j, or any network call. I/O (reading the three run JSONs, the contexts
sidecars, the clause-hit harness, and the gold-relation xlsx) is the
responsibility of the orchestration script
(`scripts/generate_phase10_ab_report.py`), which is why this module is the
one covered by `tests/application/use_cases/test_ab_report.py` on small
in-memory fixtures.

Two structural facts drive the design, both discovered while preparing this
plan (not assumptions):

1. **The canonical hybrid baseline JSON has one corrupted `test_id`** (10-01
   deferred-items: a raw literal newline instead of `"B04-001"`, at the
   entry occupying B04-001's ordinal position). This is not just a wrong
   string — the embedded control character makes the file invalid per
   Python's `json` module in its default *strict* mode, so a naive
   `json.load()` raises `JSONDecodeError`. `load_run_json_text` parses with
   `strict=False` (tolerating the embedded control character) and
   `repair_test_results` then repairs the corrupted id via a positional
   cross-check against the expected ordered 18-id list — never silently
   dropping the B04 case.

2. **Only the graphrag-ontology leg's retrieval is clause-anchored.**
   Hybrid's `citation_id`s are already real clause ids
   (`"{document}::{clause_id}"`, from the Phase 1.3 clause-level chunker) so
   hit@3/recall@3 ARE computable for hybrid from its captured top-3 contexts
   sidecar (though NOT recall@pool — only the top-3 was persisted, not a
   50-deep pool). Phase 9's basic-graphrag leg's `citation_id`s are raw Neo4j
   `elementId()` strings (single-colon separated, e.g.
   `"4:73019583-...:145"`) — the exact "Honesty note" gap that 10-09 fixed
   ONLY for the ontology adapter (D-16 additivity: Phase 9's adapter is
   untouched). `extract_clause_id_from_citation` returns `None` for such
   ids, so `score_top3_from_contexts` correctly surfaces "not computable"
   (`None`, `None`) for that leg instead of fabricating a 0.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional

from domain.services.clause_hit_scoring_service import ClauseHitScoringService

LEG_ONTOLOGY = "ontology"
LEG_GRAPHRAG = "graphrag"
LEG_HYBRID = "hybrid"


# ---------------------------------------------------------------------------
# Corrupted-JSON tolerant loading + test_id repair (10-01 B04 caveat)
# ---------------------------------------------------------------------------


def load_run_json_text(raw_text: str) -> dict:
    """
    Parse a run JSON's raw text tolerating embedded control characters
    (`strict=False`) — the canonical hybrid baseline's corrupted B04 entry
    otherwise raises `JSONDecodeError` under Python's default strict mode.
    """
    return json.loads(raw_text, strict=False)


def repair_test_id(raw_test_id: str, index: int, expected_order: list[str]) -> str:
    """
    Repair a corrupted/whitespace-only `test_id` via positional cross-check
    against `expected_order` (the known-correct ordered 18-id list, e.g. from
    the sibling `.partial.jsonl`'s ordering or `FIXED_18_TEST_IDS`).

    Returns the original value unchanged when it already looks valid (a
    non-blank id present in `expected_order`), so this is a no-op for the
    other 17 well-formed entries.
    """
    if raw_test_id and raw_test_id.strip() and raw_test_id in expected_order:
        return raw_test_id
    if 0 <= index < len(expected_order):
        return expected_order[index]
    return raw_test_id


def repair_test_results(run_json: dict, expected_order: list[str]) -> dict:
    """
    Return a copy of `run_json` with any corrupted `test_id` in
    `test_results` repaired via `repair_test_id`. Never drops a case.
    """
    test_results = run_json.get("test_results", [])
    repaired = []
    for i, tr in enumerate(test_results):
        tr = dict(tr)
        tr["test_id"] = repair_test_id(tr.get("test_id", ""), i, expected_order)
        repaired.append(tr)
    out = dict(run_json)
    out["test_results"] = repaired
    return out


# ---------------------------------------------------------------------------
# Per-case metric extraction (LLM-judge citation/grounding dims + RAGAs)
# ---------------------------------------------------------------------------


@dataclass
class CaseMetrics:
    """One leg's scored metrics for one GT case."""

    test_id: str
    score: Optional[float] = None
    passed: Optional[bool] = None
    ragas_score: Optional[float] = None
    citation_correctness: Optional[float] = None
    factual_grounding: Optional[float] = None
    context_recall: Optional[float] = None
    context_precision: Optional[float] = None
    context_faithfulness: Optional[float] = None
    hit_at_3: Optional[int] = None
    recall_at_3: Optional[float] = None
    recall_at_pool: Optional[float] = None  # None = not computable for this leg


def _metric_value(metrics: list[dict], name: str) -> Optional[float]:
    for m in metrics or []:
        if m.get("name") == name:
            return m.get("value")
    return None


def extract_case_metrics(run_json: Optional[dict], test_id: str) -> Optional[CaseMetrics]:
    """
    Pull one case's benchmark score, LLM-judge citation/grounding dims
    (`metrics` array: `citation_correctness`, `factual_grounding`), and
    RAGAs context metrics (`ragas.retrieval_quality.{context_recall,
    context_precision}`, `ragas.grounding.context_faithfulness`) out of a
    parsed run JSON. Returns None if `run_json` is None or the case is
    absent (never raises on a missing case — callers must handle absence
    explicitly, e.g. to render "N/A" rather than crash).
    """
    if run_json is None:
        return None
    for tr in run_json.get("test_results", []):
        if tr.get("test_id") == test_id:
            ragas = tr.get("ragas") or {}
            retrieval_quality = ragas.get("retrieval_quality") or {}
            grounding = ragas.get("grounding") or {}
            metrics = tr.get("metrics") or []
            return CaseMetrics(
                test_id=test_id,
                score=tr.get("score"),
                passed=tr.get("passed"),
                ragas_score=tr.get("ragas_score"),
                citation_correctness=_metric_value(metrics, "citation_correctness"),
                factual_grounding=_metric_value(metrics, "factual_grounding"),
                context_recall=(retrieval_quality.get("context_recall") or {}).get("score"),
                context_precision=(retrieval_quality.get("context_precision") or {}).get(
                    "score"
                ),
                context_faithfulness=(grounding.get("context_faithfulness") or {}).get(
                    "score"
                ),
            )
    return None


# ---------------------------------------------------------------------------
# Clause-hit@3 from a captured top-3 contexts sidecar (hybrid + graphrag legs)
# ---------------------------------------------------------------------------


def extract_clause_id_from_citation(citation_id: str) -> Optional[str]:
    """
    Extract the bare clause id from a `{document}::{clause_id}` or
    `{document}::{clause_id}::table::N` citation_id (the Phase 1.3
    clause-aware chunker's format, reused by the hybrid/basic-graphrag
    contexts sidecars).

    Returns None for ids that do NOT follow this pattern — in particular,
    Phase 9's unfixed emergent-graph adapter emits raw Neo4j `elementId()`
    strings (single-colon separated, e.g. `"4:73019583-...:145"`, no `"::"`
    substring), which are NOT clause-anchored. Returning None (rather than a
    best-effort guess) lets callers correctly report "not computable" for
    that leg instead of a fabricated score.
    """
    if not citation_id or "::" not in citation_id:
        return None
    parts = citation_id.split("::")
    return parts[1] if len(parts) >= 2 and parts[1] else None


def score_top3_from_contexts(
    contexts: list[dict], gold_set: set[str]
) -> tuple[Optional[int], Optional[float]]:
    """
    Compute (hit@3, recall@3) from a captured top-N contexts sidecar list
    (only the first 3 entries are used, matching what the model was actually
    shown). Returns (None, None) when none of the entries carry a
    clause-anchored citation_id (see `extract_clause_id_from_citation`) —
    i.e. clause-hit@3 is structurally not computable for that leg's captured
    contexts, not a silent 0.
    """
    clause_ids = [
        cid
        for cid in (
            extract_clause_id_from_citation(c.get("citation_id", "")) for c in (contexts or [])
        )
        if cid
    ]
    if not clause_ids:
        return None, None
    top3 = clause_ids[:3]
    return (
        ClauseHitScoringService.hit_at_3(gold_set, top3),
        ClauseHitScoringService.recall_at_3(gold_set, top3),
    )


# ---------------------------------------------------------------------------
# Three-way comparison aggregation
# ---------------------------------------------------------------------------


@dataclass
class ThreeWayCaseRow:
    """One GT case's metrics across all three legs, plus computed deltas."""

    test_id: str
    benchmark: str
    ontology: Optional[CaseMetrics] = None
    graphrag: Optional[CaseMetrics] = None
    hybrid: Optional[CaseMetrics] = None

    @property
    def delta_score_vs_graphrag(self) -> Optional[float]:
        if (
            self.ontology
            and self.graphrag
            and self.ontology.score is not None
            and self.graphrag.score is not None
        ):
            return self.ontology.score - self.graphrag.score
        return None

    @property
    def delta_score_vs_hybrid(self) -> Optional[float]:
        if (
            self.ontology
            and self.hybrid
            and self.ontology.score is not None
            and self.hybrid.score is not None
        ):
            return self.ontology.score - self.hybrid.score
        return None


@dataclass
class ThreeWayComparisonResult:
    """Aggregate three-way A/B result over the 18-case fixed GT (D-16)."""

    rows: list[ThreeWayCaseRow] = field(default_factory=list)
    baseline_present: bool = False  # graphrag_run (10-01) was supplied

    def aggregate(self, leg: str, field_name: str) -> Optional[float]:
        """Average `field_name` (e.g. "score", "hit_at_3") across all cases
        for `leg` ("ontology"|"graphrag"|"hybrid"), skipping cases where the
        leg or the field is None (not computable/absent). Returns None if no
        case has a value for this (leg, field) pair."""
        values = []
        for row in self.rows:
            cm = getattr(row, leg, None)
            if cm is None:
                continue
            v = getattr(cm, field_name, None)
            if v is not None:
                values.append(v)
        return sum(values) / len(values) if values else None

    @property
    def improved_vs_graphrag(self) -> list[str]:
        return [r.test_id for r in self.rows if (r.delta_score_vs_graphrag or 0) > 0]

    @property
    def regressed_vs_graphrag(self) -> list[str]:
        return [r.test_id for r in self.rows if (r.delta_score_vs_graphrag or 0) < 0]

    @property
    def unchanged_vs_graphrag(self) -> list[str]:
        return [
            r.test_id
            for r in self.rows
            if r.delta_score_vs_graphrag is not None and r.delta_score_vs_graphrag == 0
        ]


def build_three_way_comparison(
    ontology_run: Optional[dict],
    graphrag_run: Optional[dict],
    hybrid_run: Optional[dict],
    test_ids: list[str],
    ontology_clause_hit_by_id: Optional[dict[str, dict]] = None,
    hybrid_contexts: Optional[dict[str, list[dict]]] = None,
    graphrag_contexts: Optional[dict[str, list[dict]]] = None,
    gold_sets: Optional[dict[str, set[str]]] = None,
) -> ThreeWayComparisonResult:
    """
    Build the full three-way per-case comparison (D-16). Every input is
    already-loaded data (no I/O here):

    - `ontology_run`/`graphrag_run`/`hybrid_run`: parsed eval-run JSONs (or
      None if a leg is unavailable — `graphrag_run=None` triggers the D-16
      hard-dependency caveat via `baseline_present=False`).
    - `ontology_clause_hit_by_id`: `{test_id: {"hit_at_3", "recall_at_3",
      "recall_at_pool"}}` from the real `ccop-eval graph clause-hit` run
      (pool_size=50 — the only leg with a real 50-deep pool).
    - `hybrid_contexts`/`graphrag_contexts`: `{test_id: [context_dict, ...]}`
      from each run's `-contexts.json` sidecar (top-3 only).
    - `gold_sets`: `{test_id: {normalized_clause_id, ...}}`, the D-15 gold
      SET (clause_reference UNION D-17 xlsx citations).
    """
    rows: list[ThreeWayCaseRow] = []
    for test_id in test_ids:
        benchmark = test_id.split("-")[0]
        ontology_cm = extract_case_metrics(ontology_run, test_id)
        graphrag_cm = extract_case_metrics(graphrag_run, test_id)
        hybrid_cm = extract_case_metrics(hybrid_run, test_id)

        gold_set = (gold_sets or {}).get(test_id, set())

        if ontology_cm and ontology_clause_hit_by_id and test_id in ontology_clause_hit_by_id:
            ch = ontology_clause_hit_by_id[test_id]
            ontology_cm.hit_at_3 = ch.get("hit_at_3")
            ontology_cm.recall_at_3 = ch.get("recall_at_3")
            ontology_cm.recall_at_pool = ch.get("recall_at_pool")

        if hybrid_cm and hybrid_contexts and test_id in hybrid_contexts and gold_set:
            hit3, recall3 = score_top3_from_contexts(hybrid_contexts[test_id], gold_set)
            hybrid_cm.hit_at_3, hybrid_cm.recall_at_3 = hit3, recall3
            # recall@pool intentionally left None: sidecar only captured top-3

        if graphrag_cm and graphrag_contexts and test_id in graphrag_contexts and gold_set:
            hit3, recall3 = score_top3_from_contexts(graphrag_contexts[test_id], gold_set)
            graphrag_cm.hit_at_3, graphrag_cm.recall_at_3 = hit3, recall3
            # Phase 9 elementId citations -> extract_clause_id_from_citation
            # returns None for every entry -> (None, None): structurally not
            # clause-anchored, correctly surfaced rather than faked as 0.

        rows.append(
            ThreeWayCaseRow(
                test_id=test_id,
                benchmark=benchmark,
                ontology=ontology_cm,
                graphrag=graphrag_cm,
                hybrid=hybrid_cm,
            )
        )
    return ThreeWayComparisonResult(rows=rows, baseline_present=graphrag_run is not None)


__all__ = [
    "LEG_ONTOLOGY",
    "LEG_GRAPHRAG",
    "LEG_HYBRID",
    "load_run_json_text",
    "repair_test_id",
    "repair_test_results",
    "CaseMetrics",
    "extract_case_metrics",
    "extract_clause_id_from_citation",
    "score_top3_from_contexts",
    "ThreeWayCaseRow",
    "ThreeWayComparisonResult",
    "build_three_way_comparison",
]
