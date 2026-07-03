"""
Unit tests for ClauseHitScoringService (Phase 10, plan 10-10, D-15).

Pure, dependency-free set-valued scoring: hit@3 / recall@3 / recall@pool(50).
No Neo4j, no I/O — fixtures with known gold/retrieved clause sets only.
"""

from domain.services.clause_hit_scoring_service import ClauseHitScoringService


class TestNormalizeClauseId:
    """Clause-id normalization must be consistent between gold and retrieved sides."""

    def test_strips_section_symbol(self):
        assert ClauseHitScoringService.normalize_clause_id("§1.2.1") == "1.2.1"

    def test_collapses_internal_whitespace(self):
        assert (
            ClauseHitScoringService.normalize_clause_id("section   11")
            == "section 11"
        )

    def test_lowercases(self):
        assert ClauseHitScoringService.normalize_clause_id("Section 11") == "section 11"

    def test_keeps_sub_item_suffix(self):
        assert ClauseHitScoringService.normalize_clause_id("5.3.1(c)") == "5.3.1(c)"

    def test_strips_surrounding_whitespace(self):
        assert ClauseHitScoringService.normalize_clause_id("  1.2.1  ") == "1.2.1"

    def test_empty_string_stays_empty(self):
        assert ClauseHitScoringService.normalize_clause_id("") == ""

    def test_gold_and_retrieved_variants_normalize_identically(self):
        # § prefix (common in GT prose) vs bare id (seeded clause backbone)
        assert ClauseHitScoringService.normalize_clause_id(
            "§1.2.1"
        ) == ClauseHitScoringService.normalize_clause_id("1.2.1")


class TestHitAt3:
    """hit@3 = 1 when gold_set ∩ top3_clause_ids != empty, else 0."""

    def test_hit_when_intersection_nonempty(self):
        gold = {"1.2.1", "1.4.1"}
        top3 = ["5.6", "1.2.1", "9.9"]
        assert ClauseHitScoringService.hit_at_3(gold, top3) == 1

    def test_miss_when_no_overlap(self):
        gold = {"1.2.1", "1.4.1"}
        top3 = ["5.6", "9.9", "3.3"]
        assert ClauseHitScoringService.hit_at_3(gold, top3) == 0

    def test_hit_is_normalization_aware(self):
        gold = {"§1.2.1"}
        top3 = ["1.2.1", "5.6", "9.9"]
        assert ClauseHitScoringService.hit_at_3(gold, top3) == 1

    def test_empty_gold_set_is_a_miss(self):
        assert ClauseHitScoringService.hit_at_3(set(), ["1.2.1"]) == 0

    def test_empty_retrieved_is_a_miss(self):
        assert ClauseHitScoringService.hit_at_3({"1.2.1"}, []) == 0


class TestRecallAt3:
    """recall@3 = |gold ∩ top3| / |gold| (partial-credit fraction)."""

    def test_full_recall(self):
        gold = {"1.2.1", "1.4.1"}
        top3 = ["1.2.1", "1.4.1", "9.9"]
        assert ClauseHitScoringService.recall_at_3(gold, top3) == 1.0

    def test_partial_recall(self):
        gold = {"1.2.1", "1.4.1"}
        top3 = ["1.2.1", "5.6", "9.9"]
        assert ClauseHitScoringService.recall_at_3(gold, top3) == 0.5

    def test_zero_recall(self):
        gold = {"1.2.1", "1.4.1"}
        top3 = ["5.6", "9.9", "3.3"]
        assert ClauseHitScoringService.recall_at_3(gold, top3) == 0.0

    def test_empty_gold_set_returns_zero_not_divide_by_zero(self):
        assert ClauseHitScoringService.recall_at_3(set(), ["1.2.1"]) == 0.0

    def test_larger_gold_set_partial_credit(self):
        # B01-001-style multi-clause gold set
        gold = {"1.2.1", "1.4.1", "section 7", "section 11"}
        top3 = ["1.2.1", "1.4.1", "5.6"]
        assert ClauseHitScoringService.recall_at_3(gold, top3) == 0.5


class TestRecallAtPool:
    """recall@pool(50) = |gold ∩ top50| / |gold| (containment, ranking-independent)."""

    def test_full_pool_containment(self):
        gold = {"1.2.1", "1.4.1"}
        pool = ["9.9"] * 48 + ["1.2.1", "1.4.1"]
        assert ClauseHitScoringService.recall_at_pool(gold, pool, pool_size=50) == 1.0

    def test_pool_size_truncates_before_scoring(self):
        gold = {"1.2.1"}
        # gold clause appears only past position 50 -> must NOT count
        pool = ["9.9"] * 50 + ["1.2.1"]
        assert ClauseHitScoringService.recall_at_pool(gold, pool, pool_size=50) == 0.0

    def test_partial_pool_containment(self):
        gold = {"1.2.1", "1.4.1", "5.6"}
        pool = ["1.2.1", "9.9", "9.8"]
        assert ClauseHitScoringService.recall_at_pool(gold, pool, pool_size=50) == 1 / 3

    def test_empty_gold_set_returns_zero(self):
        assert ClauseHitScoringService.recall_at_pool(set(), ["1.2.1"], pool_size=50) == 0.0

    def test_default_pool_size_is_50(self):
        gold = {"1.2.1"}
        pool = ["9.9"] * 50 + ["1.2.1"]
        # default pool_size kwarg should truncate at 50, same as explicit above
        assert ClauseHitScoringService.recall_at_pool(gold, pool) == 0.0
