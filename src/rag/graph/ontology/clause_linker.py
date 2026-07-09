"""
Post-Extraction Entity/Chunk -> Clause Linker (Phase 10 -- D-10/D-11 fix)

Deterministic, LLM-free post-hoc linking pass -- 10-RESEARCH.md Q4's
RECOMMENDED strategy over extraction-time linking, which would require the
extraction LLM to reproduce exact `clause_id` strings verbatim (a
hallucination risk). For every `:Chunk` node written by `OntologyKGBuilder`,
this matches the chunk's text against every seeded `:Clause`'s `clause_id`
(10-05's `ClauseSeeder` backbone) using the SAME boundary-aware match
`KGInspector._clause_id_appears` (`rag/graph/inspect/metrics.py`) already
implements for D-18 clause coverage -- reused here rather than reimplemented
a third time (Don't-Hand-Roll, 10-PATTERNS.md).

Chunks get `LINKED_TO` the clauses their text cites; entities extracted FROM
those chunks (`:FROM_CHUNK` edge -- neo4j-graphrag's lexical-graph
convention, `LexicalGraphConfig.node_to_chunk_relationship_type`) inherit the
SAME `LINKED_TO` edges -- deterministically anchoring extracted entities to
the D-10 seeded clause backbone (the D-11 fine-grained retrieval unit)
without ever asking the extraction LLM to emit a clause_id.

Cypher discipline (T-09-12 / threat T-10-07-02): both Cypher statements below
are static, module-level strings parameterized via bound `$pairs` -- no
value is ever spliced into query text via f-string/`.format()`. Driver
parameterization neutralizes any Cypher-shaped content in extracted entity
text at the write layer.
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

import neo4j

from infrastructure.config.settings import Settings
from rag.graph.inspect.metrics import KGInspector

logger = logging.getLogger(__name__)

# Static, parameterized Cypher (T-09-12) -- $pairs is the only variable input,
# bound via session.run(..., pairs=pairs), never string-interpolated.
_LINK_CHUNKS_TO_CLAUSES_QUERY = """
UNWIND $pairs AS pair
MATCH (chunk) WHERE elementId(chunk) = pair.chunk_id
MATCH (clause:Clause) WHERE elementId(clause) = pair.clause_element_id
MERGE (chunk)-[:LINKED_TO]->(clause)
""".strip()

_LINK_ENTITIES_TO_CLAUSES_QUERY = """
UNWIND $pairs AS pair
MATCH (chunk) WHERE elementId(chunk) = pair.chunk_id
MATCH (clause:Clause) WHERE elementId(clause) = pair.clause_element_id
MATCH (entity)-[:FROM_CHUNK]->(chunk)
MERGE (entity)-[:LINKED_TO]->(clause)
""".strip()


@dataclass
class LinkStats:
    """Aggregate statistics for a clause-linking run (T-09-08: reported, never swallowed)."""

    chunks_scanned: int = 0
    clauses_scanned: int = 0
    chunk_clause_pairs: int = 0
    linked_to_edges_total: int = 0


class ClauseLinker:
    """
    Deterministic post-extraction entity/chunk -> `:Clause` `LINKED_TO` pass
    (D-10/D-11). No LLM call anywhere in this module -- every edge is either
    a real boundary-aware text match, or not created at all.
    """

    def __init__(
        self,
        settings: Settings,
        driver: Optional["neo4j.Driver"] = None,
    ) -> None:
        self.settings = settings
        self.driver = driver or neo4j.GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    def _fetch_chunks(self) -> list[dict[str, Any]]:
        with self.driver.session(database=self.settings.neo4j_database) as session:
            result = session.run(
                "MATCH (c:Chunk) RETURN elementId(c) AS chunk_id, c.text AS text"
            )
            return [
                {"chunk_id": record["chunk_id"], "text": record["text"] or ""}
                for record in result
            ]

    def _fetch_clauses(self) -> list[dict[str, Any]]:
        with self.driver.session(database=self.settings.neo4j_database) as session:
            result = session.run(
                "MATCH (c:Clause) RETURN elementId(c) AS clause_element_id, "
                "c.clause_id AS clause_id"
            )
            return [
                {
                    "clause_element_id": record["clause_element_id"],
                    "clause_id": record["clause_id"],
                }
                for record in result
                if record["clause_id"]
            ]

    @staticmethod
    def _compute_pairs(
        chunks: list[dict[str, Any]], clauses: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Deterministic (chunk_id, clause_element_id) match pairs, reusing the
        SAME boundary-aware text match `KGInspector._clause_id_appears`
        already implements for D-18 clause coverage (no reimplementation --
        prevents e.g. "5.3.1" from spuriously matching inside "5.3.10").
        """
        pairs: list[dict[str, Any]] = []
        for chunk in chunks:
            haystack_lower = chunk["text"].lower()
            if not haystack_lower:
                continue
            for clause in clauses:
                if KGInspector._clause_id_appears(clause["clause_id"], haystack_lower):
                    pairs.append(
                        {
                            "chunk_id": chunk["chunk_id"],
                            "clause_element_id": clause["clause_element_id"],
                        }
                    )
        return pairs

    def link(self) -> LinkStats:
        """
        Run the deterministic linking pass:
        1. Match every `:Chunk`'s text against every seeded `:Clause`'s
           `clause_id` (boundary-aware).
        2. MERGE `:Chunk-[:LINKED_TO]->:Clause` edges for every match.
        3. MERGE `:Entity-[:LINKED_TO]->:Clause` edges for every entity
           extracted FROM a linked chunk (`:FROM_CHUNK`, neo4j-graphrag's
           lexical-graph edge) -- entities inherit their chunk's clause
           links rather than being independently text-matched, since
           extracted entity nodes do not themselves carry the source prose.
        """
        chunks = self._fetch_chunks()
        clauses = self._fetch_clauses()
        pairs = self._compute_pairs(chunks, clauses)

        stats = LinkStats(
            chunks_scanned=len(chunks),
            clauses_scanned=len(clauses),
            chunk_clause_pairs=len(pairs),
        )

        if pairs:
            with self.driver.session(database=self.settings.neo4j_database) as session:
                session.run(_LINK_CHUNKS_TO_CLAUSES_QUERY, pairs=pairs)
                session.run(_LINK_ENTITIES_TO_CLAUSES_QUERY, pairs=pairs)

        self._accumulate_stats(stats)
        return stats

    def _accumulate_stats(self, stats: LinkStats) -> None:
        """Query Neo4j directly for the authoritative post-link edge count (T-09-08)."""
        try:
            with self.driver.session(database=self.settings.neo4j_database) as session:
                stats.linked_to_edges_total = session.run(
                    "MATCH ()-[r:LINKED_TO]->(:Clause) RETURN count(r) AS c"
                ).single()["c"]
        except Exception as e:
            logger.warning(f"Could not query LINKED_TO stats after linking: {e}")


__all__: list[str] = ["ClauseLinker", "LinkStats"]
