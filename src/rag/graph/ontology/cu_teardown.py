"""
Policy Graph CU Teardown (Phase 11, 11-04b / D-38).

Snapshots the current `:ComplianceUnit` layer to JSON, then DETACH DELETEs
every CU node + its relationships so the corrected 11-04b pipeline can
regenerate from a clean slate. The `:Clause` backbone (883 nodes, seeded +
annotated + text-aligned by 11-01/11-02) is NEVER touched -- teardown asserts
its count is unchanged before returning (fail-loud, T-09-08).

Why snapshot-before-delete (D-38): the regen is a destructive, multi-hour,
real-Opus rebuild. Capturing the pre-teardown CU layer (770 CUs -- 744
actor / 20 meta / 6 premise, 325 empty tuples per the 11-04 audit) gives the
acceptance step a diffable baseline AND a rollback artifact if the rebuild is
abandoned partway.

Cypher discipline (T-09-12): every query below is a static, module-level
string -- no value is ever spliced into query text via f-string/`.format()`.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

import neo4j

from infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)

PathLike = Union[str, Path]

# Static, parameterized Cypher (T-09-12).
_SNAPSHOT_QUERY = """
MATCH (cu:ComplianceUnit)
OPTIONAL MATCH (cu)-[:FROM_CLAUSE]->(c:Clause)
RETURN cu { .* } AS cu, c.clause_id AS source_clause_id
ORDER BY cu.source_doc, cu.cu_id
""".strip()

_COUNT_CU_QUERY = "MATCH (cu:ComplianceUnit) RETURN count(cu) AS c"

_COUNT_CLAUSE_QUERY = "MATCH (c:Clause) RETURN count(c) AS c"

_DELETE_CU_QUERY = "MATCH (cu:ComplianceUnit) DETACH DELETE cu"


@dataclass
class TeardownStats:
    """
    Aggregate stats for a CU-teardown run (T-09-08: reported, never
    swallowed). `clause_count_before`/`clause_count_after` are the D-38
    backbone-preservation guard -- they MUST be equal.
    """

    cu_count_before: int = 0
    cu_count_after: int = 0
    clause_count_before: int = 0
    clause_count_after: int = 0
    snapshot_path: Optional[str] = None
    snapshot_records: int = 0
    type_distribution_before: dict[str, int] = field(default_factory=dict)

    @property
    def backbone_preserved(self) -> bool:
        """D-38: the :Clause backbone count is unchanged by teardown."""
        return self.clause_count_before == self.clause_count_after

    @property
    def cus_cleared(self) -> bool:
        """Every :ComplianceUnit node is gone after teardown."""
        return self.cu_count_after == 0


class CUTeardown:
    """
    Snapshot + DETACH DELETE the `:ComplianceUnit` layer (D-38).

    PRECONDITION: none beyond a reachable Neo4j. Running against an already-
    empty CU layer is a safe no-op that still writes a (0-CU) snapshot, so a
    re-invocation after a partial run never errors.
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

    def snapshot(self, path: PathLike) -> int:
        """
        Write every `:ComplianceUnit` (all properties + its FROM_CLAUSE
        target clause_id) to `path` as JSON. Returns the record count. Safe
        on an empty layer (writes `{"compliance_units": []}`).
        """
        with self.driver.session(database=self.settings.neo4j_database) as session:
            records = [
                {**record["cu"], "source_clause_id": record["source_clause_id"]}
                for record in session.run(_SNAPSHOT_QUERY)
            ]
        payload = {"compliance_units": records, "count": len(records)}
        Path(path).write_text(json.dumps(payload, indent=2, default=str))
        logger.info(f"Snapshotted {len(records)} :ComplianceUnit node(s) to {path}")
        return len(records)

    def teardown(self, snapshot_path: Optional[PathLike] = None) -> TeardownStats:
        """
        Snapshot (if `snapshot_path` given) then DETACH DELETE all CU nodes.
        Asserts the `:Clause` backbone count is unchanged (D-38 guard) and
        raises if it is not -- teardown must never touch the source layer.
        """
        stats = TeardownStats()
        with self.driver.session(database=self.settings.neo4j_database) as session:
            stats.cu_count_before = session.run(_COUNT_CU_QUERY).single()["c"]
            stats.clause_count_before = session.run(_COUNT_CLAUSE_QUERY).single()["c"]
            stats.type_distribution_before = {
                record["t"]: record["n"]
                for record in session.run(
                    "MATCH (cu:ComplianceUnit) RETURN cu.cu_type AS t, count(cu) AS n"
                )
            }

        if snapshot_path is not None:
            stats.snapshot_path = str(snapshot_path)
            stats.snapshot_records = self.snapshot(snapshot_path)

        with self.driver.session(database=self.settings.neo4j_database) as session:
            session.run(_DELETE_CU_QUERY)
            stats.cu_count_after = session.run(_COUNT_CU_QUERY).single()["c"]
            stats.clause_count_after = session.run(_COUNT_CLAUSE_QUERY).single()["c"]

        if not stats.backbone_preserved:
            raise RuntimeError(
                f"CU teardown altered the :Clause backbone "
                f"({stats.clause_count_before} -> {stats.clause_count_after}) -- "
                f"this must never happen (D-38). Aborting."
            )
        logger.info(
            f"CU teardown complete: {stats.cu_count_before} CU(s) deleted, "
            f":Clause backbone intact ({stats.clause_count_after})"
        )
        return stats


__all__: list[str] = ["CUTeardown", "TeardownStats"]
