"""
Clause-Hit Harness Use Case (Phase 10, plan 10-10, D-15)

The deterministic clause-hit@3 acceptance gate for Phase 10. For each of the
18 fixed-GT `bdc4927d` cases, runs the REAL graphrag-ontology retrieval path
(`Neo4jOntologyGraphRetrievalAdapter`, plan 10-09 — deterministic per the
LOCKED D-15 tie-break decision, plan 10-01) and scores the retrieved clause
ids against a gold clause SET via `ClauseHitScoringService` (plan 10-10
Task 1).

Gold-set construction (Pitfall 4, RESEARCH.md Q8): `metadata.clause_reference`
alone under-represents the true gold clause set for several GT cases (e.g.
B01-001 needs §1.2.1 + §1.4.1, but `clause_reference` lists only `["1.2.1"]`).
The gold set for each case is therefore the UNION of `clause_reference` and
the D-17 xlsx's hand-authored bracketed citations (`gold_relation_parser`,
plan 10-03), with any case where the two sources DISAGREE flagged for human
review rather than silently trusting `clause_reference` alone.

Determinism (D-15): this use case performs no randomness itself. Given the
same retrieval provider output (deterministic per the ANN + stable
`ORDER BY score DESC, citation_id ASC` tie-break on a frozen index, plan
10-01/10-09) and the same gold-source inputs, `execute()` produces
byte-identical results across repeated invocations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from application.ports.output.i_test_case_repository import ITestCaseRepository
from domain.services.clause_hit_scoring_service import ClauseHitScoringService
from rag.graph.ontology.gold_relation_parser import CaseGoldRelations, parse_gold_relations

if TYPE_CHECKING:
    from rag.graph.ports.i_graph_retrieval_provider import IGraphRetrievalProvider

logger = logging.getLogger(__name__)

# The 18-case fixed GT set (`bdc4927d`) — one test case per active benchmark,
# the same stratified sample used across Phase 9/10's A/B comparisons
# (10-01-SUMMARY.md's per-case baseline table; MEMORY.md canonical-run note).
FIXED_18_TEST_IDS: tuple[str, ...] = (
    "B01-001",
    "B02-001",
    "B03-001",
    "B04-001",
    "B05-001",
    "B06-001",
    "B07-006",
    "B08-001",
    "B09-001",
    "B10-001",
    "B12-001",
    "B13-001",
    "B14-001",
    "B18-001",
    "B21-001",
    "B22-001",
    "B23-001",
    "B24-001",
)

DEFAULT_GOLD_RELATION_SHEET = "eval-18"


@dataclass
class CaseClauseHitResult:
    """Per-case clause-hit@3 scoring result (D-15)."""

    test_id: str
    gold_set: set[str]
    clause_reference_set: set[str]
    xlsx_citation_set: set[str]
    gold_disagreement: bool
    retrieved_top3: list[str]
    retrieved_pool: list[str]
    hit_at_3: int
    recall_at_3: float
    recall_at_pool: float


@dataclass
class ClauseHitHarnessResult:
    """Aggregate clause-hit@3 harness result over the 18-case GT (D-15)."""

    per_case: list[CaseClauseHitResult] = field(default_factory=list)
    aggregate_hit_at_3: float = 0.0
    aggregate_recall_at_3: float = 0.0
    aggregate_recall_at_pool: float = 0.0

    @property
    def disagreement_test_ids(self) -> list[str]:
        """Test ids where clause_reference and the xlsx gold citations disagree."""
        return [c.test_id for c in self.per_case if c.gold_disagreement]


class ClauseHitHarnessUseCase:
    """
    Runs deterministic graphrag-ontology retrieval over the 18-case fixed GT
    and scores it against cross-checked gold clause sets (D-15).
    """

    def __init__(
        self,
        test_case_repository: ITestCaseRepository,
        graph_retrieval_provider: "IGraphRetrievalProvider",
        gold_xlsx_path: str | Path,
        logger_: Optional[logging.Logger] = None,
        gold_sheet_name: str = DEFAULT_GOLD_RELATION_SHEET,
        pool_size: int = 50,
    ) -> None:
        self._test_case_repository = test_case_repository
        self._graph_retrieval_provider = graph_retrieval_provider
        self._gold_xlsx_path = gold_xlsx_path
        self._logger = logger_ or logger
        self._gold_sheet_name = gold_sheet_name
        self._pool_size = pool_size

    async def execute(
        self, test_ids: Optional[list[str]] = None
    ) -> ClauseHitHarnessResult:
        """
        Run the clause-hit@3 harness over `test_ids` (defaults to the fixed
        18-case GT set, `FIXED_18_TEST_IDS`).
        """
        ids = list(test_ids) if test_ids else list(FIXED_18_TEST_IDS)

        test_cases = await self._test_case_repository.load_by_ids(ids)
        found_ids = {tc.test_id for tc in test_cases}
        missing = [tid for tid in ids if tid not in found_ids]
        if missing:
            self._logger.warning(f"Clause-hit harness: test case(s) not found: {missing}")

        gold_relations_by_id = self._load_gold_relations()

        per_case: list[CaseClauseHitResult] = []
        for test_case in test_cases:
            per_case.append(
                self._score_case(test_case, gold_relations_by_id.get(test_case.test_id))
            )

        # Preserve requested ordering (load_by_ids does not guarantee it).
        order = {tid: i for i, tid in enumerate(ids)}
        per_case.sort(key=lambda c: order.get(c.test_id, len(order)))

        return ClauseHitHarnessResult(
            per_case=per_case,
            aggregate_hit_at_3=self._average([c.hit_at_3 for c in per_case]),
            aggregate_recall_at_3=self._average([c.recall_at_3 for c in per_case]),
            aggregate_recall_at_pool=self._average([c.recall_at_pool for c in per_case]),
        )

    def _load_gold_relations(self) -> dict[str, CaseGoldRelations]:
        try:
            cases = parse_gold_relations(
                self._gold_xlsx_path, sheet_name=self._gold_sheet_name
            )
        except FileNotFoundError:
            self._logger.warning(
                f"Gold-relation xlsx not found at {self._gold_xlsx_path}; "
                "gold sets will fall back to clause_reference only (Pitfall 4 "
                "cross-check unavailable)."
            )
            return {}
        return {c.test_id: c for c in cases}

    def _score_case(
        self,
        test_case,
        gold_relations: Optional[CaseGoldRelations],
    ) -> CaseClauseHitResult:
        clause_reference = test_case.metadata.get("clause_reference") or []
        xlsx_citations = gold_relations.clause_citations if gold_relations else []

        clause_reference_set = {
            ClauseHitScoringService.normalize_clause_id(c) for c in clause_reference
        } - {""}
        xlsx_citation_set = {
            ClauseHitScoringService.normalize_clause_id(c) for c in xlsx_citations
        } - {""}

        gold_set = clause_reference_set | xlsx_citation_set
        # Pitfall 4: flag (don't silently resolve) any case where the two
        # gold sources disagree — do NOT silently trust clause_reference alone.
        gold_disagreement = clause_reference_set != xlsx_citation_set

        pool_documents = self._graph_retrieval_provider.retrieve(
            query=test_case.question, top_k=self._pool_size
        )
        retrieved_pool = [
            doc.metadata.get("citation_id")
            for doc in pool_documents
            if doc.metadata.get("citation_id")
        ]
        retrieved_top3 = retrieved_pool[:3]

        return CaseClauseHitResult(
            test_id=test_case.test_id,
            gold_set=gold_set,
            clause_reference_set=clause_reference_set,
            xlsx_citation_set=xlsx_citation_set,
            gold_disagreement=gold_disagreement,
            retrieved_top3=retrieved_top3,
            retrieved_pool=retrieved_pool,
            hit_at_3=ClauseHitScoringService.hit_at_3(gold_set, retrieved_top3),
            recall_at_3=ClauseHitScoringService.recall_at_3(gold_set, retrieved_top3),
            recall_at_pool=ClauseHitScoringService.recall_at_pool(
                gold_set, retrieved_pool, pool_size=self._pool_size
            ),
        )

    @staticmethod
    def _average(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0


__all__ = [
    "ClauseHitHarnessUseCase",
    "ClauseHitHarnessResult",
    "CaseClauseHitResult",
    "FIXED_18_TEST_IDS",
]
