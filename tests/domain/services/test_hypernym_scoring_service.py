"""
Unit tests for HypernymScoringService (Phase 11, plan 11-06 Task 2, D-09/D-10).

Pure-domain scorer: no I/O, no mocks needed. Covers:
- Premise-supported mapping is STRONG with the beta=0.3 bonus.
- Non-premise-supported mapping is WEAK, no bonus.
- Max-pool aggregation (best fragment score wins, not average).
- Top-N=5 truncation across candidates.
- Deterministic ordering (score desc, label asc tie-break).
- Domain purity: no infrastructure/rag imports.
"""

import ast
from pathlib import Path

import pytest

from domain.services.hypernym_scoring_service import (
    HypernymMapping,
    HypernymScoringService,
    ScoredFragment,
)


class TestStrongVsWeak:
    def test_premise_supported_mapping_is_strong_with_beta_bonus(self):
        service = HypernymScoringService(beta=0.3, top_n=5)
        candidates = {
            "non-designated system": [
                ScoredFragment(text="CII means a computer system...", score=0.80, is_premise=True),
            ],
        }

        mappings = service.score_candidates(candidates)

        assert len(mappings) == 1
        mapping = mappings[0]
        assert mapping.label == "non-designated system"
        assert mapping.strong_weak == "STRONG"
        assert mapping.supporting_premise == "CII means a computer system..."
        assert mapping.score == pytest.approx(0.80 + 0.3)

    def test_non_premise_supported_mapping_is_weak_no_bonus(self):
        service = HypernymScoringService(beta=0.3, top_n=5)
        candidates = {
            "the CIIO": [
                ScoredFragment(text="The CIIO shall implement...", score=0.75, is_premise=False),
            ],
        }

        mappings = service.score_candidates(candidates)

        assert len(mappings) == 1
        mapping = mappings[0]
        assert mapping.strong_weak == "WEAK"
        assert mapping.supporting_premise == ""
        assert mapping.score == pytest.approx(0.75)

    def test_strong_requires_a_premise_fragment_not_meta_cu_designation_rule(self):
        """
        D-09: STRONG comes from a definitional premise ("CII means..."), NOT
        from a meta-CU designation rule (e.g. Act §7). A candidate supported
        only by a non-premise meta-CU fragment stays WEAK.
        """
        service = HypernymScoringService()
        candidates = {
            "designated CII": [
                ScoredFragment(
                    text="The Commissioner may designate a computer system as CII...",
                    score=0.70,
                    is_premise=False,  # meta-CU designation rule, not a premise
                ),
            ],
        }

        mappings = service.score_candidates(candidates)

        assert mappings[0].strong_weak == "WEAK"

    def test_strong_when_any_supporting_fragment_is_a_premise_even_if_not_top_scoring(self):
        service = HypernymScoringService(beta=0.3)
        candidates = {
            "hospital admin system": [
                ScoredFragment(text="best matching CU subject", score=0.90, is_premise=False),
                ScoredFragment(text="CII means a computer system...", score=0.60, is_premise=True),
            ],
        }

        mappings = service.score_candidates(candidates)

        mapping = mappings[0]
        assert mapping.strong_weak == "STRONG"
        assert mapping.supporting_premise == "CII means a computer system..."
        # Base confidence remains the best OVERALL fragment score (max-pool),
        # plus the beta bonus — the premise need not be the top-scoring match.
        assert mapping.score == pytest.approx(0.90 + 0.3)


class TestMaxPoolAggregation:
    def test_best_fragment_score_wins_not_average(self):
        service = HypernymScoringService(beta=0.0)
        candidates = {
            "system X": [
                ScoredFragment(text="weak match", score=0.10, is_premise=False),
                ScoredFragment(text="strong match", score=0.95, is_premise=False),
                ScoredFragment(text="mid match", score=0.50, is_premise=False),
            ],
        }

        mappings = service.score_candidates(candidates)

        assert mappings[0].score == pytest.approx(0.95)


class TestTopNTruncation:
    def test_top_n_5_truncates_across_candidates(self):
        service = HypernymScoringService(top_n=5)
        candidates = {
            f"label-{i}": [ScoredFragment(text=f"frag-{i}", score=score, is_premise=False)]
            for i, score in enumerate([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3])
        }

        mappings = service.score_candidates(candidates)

        assert len(mappings) == 5
        assert [m.score for m in mappings] == sorted(
            (m.score for m in mappings), reverse=True
        )

    def test_custom_top_n(self):
        service = HypernymScoringService(top_n=2)
        candidates = {
            "a": [ScoredFragment(text="a", score=0.9, is_premise=False)],
            "b": [ScoredFragment(text="b", score=0.8, is_premise=False)],
            "c": [ScoredFragment(text="c", score=0.7, is_premise=False)],
        }

        mappings = service.score_candidates(candidates)

        assert len(mappings) == 2
        assert [m.label for m in mappings] == ["a", "b"]

    def test_top_n_must_be_at_least_one(self):
        with pytest.raises(ValueError):
            HypernymScoringService(top_n=0)


class TestDeterministicOrdering:
    def test_ties_broken_by_label_ascending(self):
        service = HypernymScoringService()
        candidates = {
            "zebra": [ScoredFragment(text="z", score=0.5, is_premise=False)],
            "alpha": [ScoredFragment(text="a", score=0.5, is_premise=False)],
            "mid": [ScoredFragment(text="m", score=0.5, is_premise=False)],
        }

        mappings = service.score_candidates(candidates)

        assert [m.label for m in mappings] == ["alpha", "mid", "zebra"]

    def test_higher_score_ranks_first(self):
        service = HypernymScoringService()
        candidates = {
            "low": [ScoredFragment(text="l", score=0.2, is_premise=False)],
            "high": [ScoredFragment(text="h", score=0.9, is_premise=False)],
        }

        mappings = service.score_candidates(candidates)

        assert [m.label for m in mappings] == ["high", "low"]


class TestEmptyInput:
    def test_empty_candidates_returns_empty_list(self):
        service = HypernymScoringService()
        assert service.score_candidates({}) == []

    def test_candidate_with_no_fragments_is_skipped(self):
        service = HypernymScoringService()
        mappings = service.score_candidates({"empty": []})
        assert mappings == []


class TestReturnShape:
    def test_returns_hypernym_mapping_instances(self):
        service = HypernymScoringService()
        candidates = {
            "x": [ScoredFragment(text="frag", score=0.5, is_premise=True)],
        }
        mappings = service.score_candidates(candidates)
        assert isinstance(mappings[0], HypernymMapping)


class TestDomainPurity:
    def test_module_imports_nothing_from_infrastructure_or_rag(self):
        """
        Pure domain service (D-10) — no infra/rag deps. Statically inspects
        the module's import statements rather than relying on already-loaded
        `sys.modules` (which could false-negative if another test imported
        `rag`/`infrastructure` first).
        """
        module_path = (
            Path(__file__).resolve().parents[3]
            / "src"
            / "domain"
            / "services"
            / "hypernym_scoring_service.py"
        )
        tree = ast.parse(module_path.read_text())

        imported_roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_roots.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

        assert "infrastructure" not in imported_roots
        assert "rag" not in imported_roots


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
