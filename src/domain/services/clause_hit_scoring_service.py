"""
Clause-Hit Scoring Service (Phase 10, plan 10-10, D-15)

Pure, stateless set-valued scoring for the deterministic clause-hit@3
acceptance gate. Mirrors `ScoringService`'s `@staticmethod` domain-service
shape (no external dependencies — this module never touches Neo4j, a
retriever, or I/O; it consumes plain clause-id collections handed to it by
the application-layer harness, `application/use_cases/clause_hit_harness.py`).

Per D-15, the gold reference for a GT case is a clause SET, never a single
id (B01-001 spans multiple clauses/acts — see 10-CONTEXT.md's worked
example). Three metrics, computed per case:

  - hit@3        = 1 if gold_set intersects the top-3 retrieved clause ids,
                    else 0 (binary "did the LLM see at least one right
                    clause in what it was actually shown").
  - recall@3     = |gold ∩ top3| / |gold| (partial-credit fraction — how
                    much of the required clause set made it into the top-3).
  - recall@pool  = |gold ∩ top_pool[:pool_size]| / |gold| (containment,
                    independent of ranking — isolates whether the graph even
                    CONTAINS the right clauses, separate from whether
                    retrieval RANKS them into the top-3).

Clause-id normalization (RESEARCH.md Q8 / Pitfall 4): gold references come
from GT JSONL prose (`§1.2.1`) and the D-17 xlsx bracketed citations, while
retrieved ids come from the seeded `:Clause` backbone (`clause_inventory.json`,
bare ids like `1.2.1` or `section 11`). `normalize_clause_id` strips the `§`
symbol, collapses internal whitespace, lowercases, and — critically — KEEPS
sub-item suffixes like `(c)` (they are semantically distinct clauses, e.g.
`5.3.1` vs `5.3.1(c)`), so both sides compare on the same normalized key.
"""

import re
from typing import Collection, Iterable

_SECTION_SYMBOL_RE = re.compile(r"§")
_WHITESPACE_RE = re.compile(r"\s+")


class ClauseHitScoringService:
    """
    Domain service for scoring retrieved clause ids against a gold clause
    SET (D-15). Stateless, `@staticmethod`-only — no external dependencies,
    runs entirely in the fast unit slice (`-m "not integration"`).
    """

    @staticmethod
    def normalize_clause_id(raw: str) -> str:
        """
        Normalize a single clause id for cross-source set comparison.

        - Strips the `§` section symbol (present in GT JSONL prose, absent
          from the seeded clause backbone).
        - Collapses internal whitespace to a single space (e.g. the D-17
          xlsx's `"NOT DESIGNATED_AS"`-style multi-space artifacts, applied
          here to clause ids like `"section   11"`).
        - Lowercases (the seeded backbone uses lowercase `"section 11"`;
          GT prose sometimes capitalizes).
        - Strips leading/trailing whitespace.
        - KEEPS sub-item suffixes like `(c)` — these are distinct clauses,
          not formatting noise.

        Empty/falsy input normalizes to `""`.
        """
        if not raw:
            return ""
        text = _SECTION_SYMBOL_RE.sub("", raw)
        text = _WHITESPACE_RE.sub(" ", text).strip()
        return text.lower()

    @staticmethod
    def _normalize_set(clause_ids: Iterable[str]) -> set[str]:
        return {
            ClauseHitScoringService.normalize_clause_id(cid)
            for cid in clause_ids
            if cid
        } - {""}

    @staticmethod
    def hit_at_3(gold_set: Collection[str], retrieved_top3: Collection[str]) -> int:
        """
        hit@3 = 1 when the normalized gold set intersects the normalized
        top-3 retrieved clause ids, else 0. An empty gold set or an empty
        retrieved list is always a miss (0), never a vacuous hit.
        """
        gold = ClauseHitScoringService._normalize_set(gold_set)
        top3 = ClauseHitScoringService._normalize_set(retrieved_top3)
        if not gold or not top3:
            return 0
        return 1 if gold & top3 else 0

    @staticmethod
    def recall_at_3(gold_set: Collection[str], retrieved_top3: Collection[str]) -> float:
        """
        recall@3 = |gold ∩ top3| / |gold| — partial-credit fraction of the
        required clause set that appears in the top-3. Returns 0.0 (not a
        ZeroDivisionError) when the gold set is empty.
        """
        gold = ClauseHitScoringService._normalize_set(gold_set)
        if not gold:
            return 0.0
        top3 = ClauseHitScoringService._normalize_set(retrieved_top3)
        return len(gold & top3) / len(gold)

    @staticmethod
    def recall_at_pool(
        gold_set: Collection[str],
        retrieved_pool: Collection[str],
        pool_size: int = 50,
    ) -> float:
        """
        recall@pool(pool_size) = |gold ∩ pool[:pool_size]| / |gold| —
        containment check independent of ranking: does the graph even
        contain the right clauses within the candidate pool, regardless of
        where they rank. Returns 0.0 when the gold set is empty.
        """
        gold = ClauseHitScoringService._normalize_set(gold_set)
        if not gold:
            return 0.0
        pool_list = list(retrieved_pool)[:pool_size]
        pool = ClauseHitScoringService._normalize_set(pool_list)
        return len(gold & pool) / len(gold)


__all__ = ["ClauseHitScoringService"]
