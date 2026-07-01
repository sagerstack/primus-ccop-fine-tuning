"""
KG Quality Inspector (Phase 9 — D-18/D-19).

Makes the emergent CCoP knowledge graph *seen and measured* before it is ever
scored: node/edge counts, entity-type + degree distributions, orphan/isolated
nodes, clause coverage against `clause_inventory.json`, duplicate/near-
duplicate entities, and extraction failure rate.

This is the quantitative half of D-18 (the other half is the Neo4j Browser
visual workflow, docs/phase-2/neo4j-browser-workflow.md). It is also the
gate for D-19's iterate-and-improve loop: inspect -> adjust -> rebuild ->
re-inspect, so a degenerate graph is never scored.

Honesty guardrail (D-19): these metrics measure functionality (is the
extraction structurally sound?), not a knob for chasing B01/B03/B04 scores.

Threat model (T-09-09): every Cypher query below is either a static literal
with no interpolated values, or a `$parameter`-bound query. No value is ever
spliced into query text via f-string/`.format()`.
"""

import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Union

import neo4j

logger = logging.getLogger(__name__)

# Structural/bookkeeping labels written by neo4j-graphrag's SimpleKGPipeline
# itself — excluded from entity_type_distribution because they are pipeline
# scaffolding, not LLM-discovered entity types (D-03 emergent extraction).
_STRUCTURAL_LABELS = frozenset({"__KGBuilder__", "__Entity__", "Chunk", "Document"})

# Candidate identifying properties tried in priority order when building a
# display name for duplicate-entity grouping. Emergent extraction (no schema,
# D-03/D-08) produces heterogeneous property shapes per entity type — e.g.
# CIIAsset.asset_id vs User.user_id vs Vendor.name — so there is no single
# universal "name" field to group on.
_NAME_PROPERTY_PRIORITY = (
    "name",
    "identifier",
    "id",
    "user_id",
    "asset_id",
    "incident_id",
    "event_id",
    "vendor_id",
    "username",
    "contact_info",
)

# Default clause inventory path, resolved relative to this file so it is
# correct regardless of the caller's working directory (src/rag/graph/inspect
# -> src/rag/ingestion/fixtures/clause_inventory.json).
DEFAULT_CLAUSE_INVENTORY_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "ingestion"
    / "fixtures"
    / "clause_inventory.json"
)

PathLike = Union[str, Path]


class KGInspector:
    """
    Read-only KG-quality inspector for the emergent CCoP graph (D-18).

    Constructed from a live neo4j.Driver; never mutates the graph.
    """

    def __init__(self, driver: neo4j.Driver, database: str = "neo4j") -> None:
        self.driver = driver
        self.database = database

    def _session(self):
        return self.driver.session(database=self.database)

    # ------------------------------------------------------------------
    # Structural counts
    # ------------------------------------------------------------------

    def node_count(self) -> int:
        with self._session() as session:
            return session.run("MATCH (n) RETURN count(n) AS c").single()["c"]

    def edge_count(self) -> int:
        with self._session() as session:
            return session.run(
                "MATCH ()-[r]->() RETURN count(r) AS c"
            ).single()["c"]

    def entity_type_distribution(self) -> dict[str, int]:
        """Label counts, excluding neo4j-graphrag's own bookkeeping labels."""
        with self._session() as session:
            result = session.run(
                "MATCH (n) UNWIND labels(n) AS label "
                "RETURN label, count(*) AS c ORDER BY c DESC"
            )
            return {
                record["label"]: record["c"]
                for record in result
                if record["label"] not in _STRUCTURAL_LABELS
            }

    # ------------------------------------------------------------------
    # Degree / connectivity
    # ------------------------------------------------------------------

    def _degrees(self) -> list[int]:
        with self._session() as session:
            # COUNT { } subquery syntax (Neo4j 5.x) — size() over a pattern
            # expression is deprecated/removed for this use.
            result = session.run("MATCH (n) RETURN COUNT { (n)--() } AS degree")
            return [record["degree"] for record in result]

    def degree_distribution(self) -> dict[str, Any]:
        """Min/max/avg degree plus a coarse histogram, for eyeballing density."""
        degrees = self._degrees()
        if not degrees:
            return {"min": 0, "max": 0, "avg": 0.0, "buckets": {}}

        buckets = {"0": 0, "1-5": 0, "6-20": 0, "21+": 0}
        for degree in degrees:
            if degree == 0:
                buckets["0"] += 1
            elif degree <= 5:
                buckets["1-5"] += 1
            elif degree <= 20:
                buckets["6-20"] += 1
            else:
                buckets["21+"] += 1

        return {
            "min": min(degrees),
            "max": max(degrees),
            "avg": round(sum(degrees) / len(degrees), 2),
            "buckets": buckets,
        }

    def orphan_nodes(self) -> int:
        """Count of degree-0 (fully isolated) nodes."""
        with self._session() as session:
            return session.run(
                "MATCH (n) WHERE NOT (n)--() RETURN count(n) AS c"
            ).single()["c"]

    # ------------------------------------------------------------------
    # Clause coverage (D-18: vs clause_inventory.json)
    # ------------------------------------------------------------------

    def clause_coverage(
        self, inventory_path: PathLike = DEFAULT_CLAUSE_INVENTORY_PATH
    ) -> dict[str, Any]:
        """
        How many of the inventory's unique clause_ids surface among graph
        Chunk text — a proxy for "did the source clause make it into the
        graph at all" (not schema-seeded, D-16 is Phase 10).
        """
        entries = json.loads(Path(inventory_path).read_text())["entries"]
        clause_ids = sorted({entry["clause_id"] for entry in entries})

        with self._session() as session:
            result = session.run("MATCH (c:Chunk) RETURN c.text AS text")
            combined_text = "\n".join(
                record["text"] for record in result if record["text"]
            ).lower()

        covered = sum(
            1 for cid in clause_ids if self._clause_id_appears(cid, combined_text)
        )
        total = len(clause_ids)
        return {
            "covered": covered,
            "total": total,
            "coverage_ratio": round(covered / total, 4) if total else 0.0,
        }

    @staticmethod
    def _clause_id_appears(clause_id: str, haystack_lower: str) -> bool:
        """
        Case-insensitive, boundary-aware substring match — prevents short
        numeric clause_ids (e.g. "1") from spuriously matching inside a
        longer one (e.g. "15.37").
        """
        pattern = re.compile(
            r"(?<![A-Za-z0-9])" + re.escape(clause_id.lower()) + r"(?![A-Za-z0-9])"
        )
        return bool(pattern.search(haystack_lower))

    # ------------------------------------------------------------------
    # Duplicate / near-duplicate entities
    # ------------------------------------------------------------------

    def duplicate_entities(self) -> list[list[dict[str, Any]]]:
        """
        Groups of __Entity__ nodes sharing a normalized display name.

        Emergent extraction without a schema/entity-resolver commonly
        collapses to generic identifier conventions (e.g. multiple distinct
        mentions all extracted as "user123") — surfacing these groups is
        exactly the "garbage" D-19 asks a human to eyeball before scoring.
        """
        with self._session() as session:
            result = session.run(
                "MATCH (n:__Entity__) "
                "RETURN elementId(n) AS node_id, labels(n) AS labels, "
                "properties(n) AS props"
            )
            records = list(result)

        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            display_name = self._display_name(dict(record["props"]))
            normalized = display_name.strip().lower()
            groups[normalized].append(
                {
                    "node_id": record["node_id"],
                    "labels": [
                        label
                        for label in record["labels"]
                        if label not in _STRUCTURAL_LABELS
                    ],
                    "name": display_name,
                }
            )

        return [group for group in groups.values() if len(group) > 1]

    @staticmethod
    def _display_name(props: dict[str, Any]) -> str:
        for key in _NAME_PROPERTY_PRIORITY:
            value = props.get(key)
            if value:
                return str(value)
        # No recognized identifying property — fall back to a stable join of
        # all property values so nodes with identical (but unlabeled)
        # property sets still group together.
        return "|".join(f"{k}={v}" for k, v in sorted(props.items()))

    # ------------------------------------------------------------------
    # Extraction failure rate
    # ------------------------------------------------------------------

    def extraction_failure_rate(self) -> dict[str, Any]:
        """
        BuildStats.failures (rag.graph.build.kg_builder.EmergentKGBuilder) is
        an in-memory, per-run result — it is never persisted to Neo4j, so
        there is no durable failure log to query from the graph itself.
        Honest default (D-19): report 0.0 with an explicit note rather than
        fabricate a number from unrelated graph state.
        """
        return {
            "rate": 0.0,
            "note": (
                "No persisted failure log in Neo4j — BuildStats.failures is "
                "runtime-only; see the most recent `graph build` output for "
                "per-document failure counts."
            ),
        }

    # ------------------------------------------------------------------
    # Aggregate
    # ------------------------------------------------------------------

    def summary(
        self, inventory_path: PathLike = DEFAULT_CLAUSE_INVENTORY_PATH
    ) -> dict[str, Any]:
        """Aggregate every D-18 metric into a single dict (CLI + report consumer)."""
        return {
            "node_count": self.node_count(),
            "edge_count": self.edge_count(),
            "entity_type_distribution": self.entity_type_distribution(),
            "degree_distribution": self.degree_distribution(),
            "orphan_nodes": self.orphan_nodes(),
            "clause_coverage": self.clause_coverage(inventory_path),
            "duplicate_entities": self.duplicate_entities(),
            "extraction_failure_rate": self.extraction_failure_rate(),
        }


__all__: list[str] = ["KGInspector", "DEFAULT_CLAUSE_INVENTORY_PATH"]
