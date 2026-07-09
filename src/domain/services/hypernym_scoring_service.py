"""
Hypernym Scoring Service (Phase 11, plan 11-06 Task 2, D-09/D-10)

Pure, stateless confidence scorer for GraphCompliance's hypernym-mapping step
(§3.2, eqs. 1-2). Mirrors `ClauseHitScoringService`'s `@staticmethod` domain-
service shape (no external dependencies — this module never touches Neo4j, an
embedder, or I/O; it consumes plain, pre-scored fragment collections handed
to it by the retrieval node, `rag/retrieval/nodes/anchor_hypernym_mapping.py`).

Hypernym mapping normalizes ANCHORS (actor/data/system entities extracted
from the per-query Context Graph) to policy vocabulary — never relations
(correction carried from the B01-001 draft, D-10).

Scoring (eqs. 1-2):
  - For each candidate hypernym label, max-pool over its supporting
    fragments' retrieval scores (the single best-matching fragment's score
    is the candidate's base confidence — max-pool, not average-pool, so one
    strong match is never diluted by weaker paraphrase-duplicates).
  - A candidate is marked STRONG iff at least one of its supporting
    fragments is a `premise` (D-09 — a definitional premise, e.g.
    "CII means...", NOT a meta-CU designation rule), earning a `beta=0.3`
    confidence bonus on top of the max-pooled score. Otherwise WEAK, no
    bonus.
  - Candidates are kept to the top-N=5 per anchor, ordered deterministically
    by final score (descending) then label (ascending) to break ties.

`beta` and `top_n` are constructor-configurable (defaults = paper's
starting values, D-09/D-10) — "Claude's discretion" per 11-CONTEXT.md notes
these as tunable without being locked to the paper's exact figures.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ScoredFragment:
    """
    A single retrieved policy fragment (premise or CU) supporting a
    candidate hypernym label, with its raw retrieval/similarity score.

    `is_premise` is the D-09 runtime confidence signal: True iff this
    fragment's source `:ComplianceUnit` is a `premise` (never a meta-CU or
    actor-CU) — the label the service uses to decide STRONG vs WEAK.
    `source_id` is optional traceability (e.g. citation_id or cu_id), not
    used in scoring.
    """

    text: str
    score: float
    is_premise: bool = False
    source_id: str = ""


@dataclass(frozen=True)
class HypernymMapping:
    """A single anchor->hypernym-label confidence mapping (D-17.2 trace payload shape)."""

    label: str
    strong_weak: str  # "STRONG" or "WEAK"
    supporting_premise: str  # supporting premise fragment text, "" if WEAK
    score: float


class HypernymScoringService:
    """
    Domain service scoring anchor->hypernym-label candidate mappings
    (GraphCompliance §3.2, eqs. 1-2). Stateless — every method call is
    self-contained; the beta bonus and top-N truncation are configured once
    at construction time.
    """

    def __init__(self, beta: float = 0.3, top_n: int = 5) -> None:
        if top_n < 1:
            raise ValueError("top_n must be >= 1")
        self.beta = beta
        self.top_n = top_n

    def score_candidates(
        self, candidates: Dict[str, List[ScoredFragment]]
    ) -> List[HypernymMapping]:
        """
        Score every candidate hypernym label against its supporting
        fragments and return up to `top_n` mappings, deterministically
        ordered (score desc, label asc).

        Candidates with an empty fragment list are skipped (nothing to
        support the mapping). Empty `candidates` returns [].
        """
        mappings: List[HypernymMapping] = []

        for label, fragments in candidates.items():
            if not fragments:
                continue
            mappings.append(self._score_one(label, fragments))

        mappings.sort(key=lambda m: (-m.score, m.label))
        return mappings[: self.top_n]

    def _score_one(self, label: str, fragments: List[ScoredFragment]) -> HypernymMapping:
        """Max-pool + STRONG/WEAK + beta bonus for a single candidate (eqs. 1-2)."""
        best_overall = max(fragments, key=lambda f: f.score)
        premise_fragments = [f for f in fragments if f.is_premise]

        if premise_fragments:
            # STRONG iff supported by a premise fragment (D-09) — the
            # definitional premise, not a meta-CU designation rule. Max-pool
            # over premise fragments specifically for the supporting text,
            # but the base confidence is still the best score across ALL
            # supporting fragments (a premise need not be the single
            # highest-scoring match to confer STRONG; it only needs to be
            # present among the top-M supporting fragments per D-09).
            best_premise = max(premise_fragments, key=lambda f: f.score)
            return HypernymMapping(
                label=label,
                strong_weak="STRONG",
                supporting_premise=best_premise.text,
                score=best_overall.score + self.beta,
            )

        return HypernymMapping(
            label=label,
            strong_weak="WEAK",
            supporting_premise="",
            score=best_overall.score,
        )


__all__ = ["HypernymScoringService", "HypernymMapping", "ScoredFragment"]
