"""
Policy Graph Builder (Phase 11, 11-05 / D-01/D-02).

LEGACY / FROZEN (2026-07-06): the graph is no longer rebuilt from this code.
The live Neo4j graph is the artifact of record and is maintained by ordered
patches under `rag/graph/patches/` (see its README). This builder still models
premises as `ComplianceUnit{cu_type:'premise'}` nodes, which patch 001 replaced
with `:Premise`-marked clauses — so running it would REGRESS the graph. Do not
run or edit for graph fixes; apply a patch instead.

The reproducible orchestrator for the offline Policy Graph -- runs the four
Compliance-Unit stages in sequence ON THE PERSISTED 11-02 source layer, reusing
11-04's minter directly (never a divergent second copy):

  Stage 1  cu_classifier.CUClassifier   -- classify + mint typed CUs
  Stage 2  cu_extractor.CUExtractor      -- 4-tuple extraction (retry-on-empty)
  Finalize (deterministic, no LLM)       -- ancestor-subject inheritance +
                                            doc-default actor fallback (folds the
                                            11-04b subjectless cleanup into the
                                            pipeline so a rebuild is regression-free)
  Stage 3  refers_to_linker.RefersToLinker -- REFERS_TO edges

Safety (11-05):
- SCOPED teardown: `--drop` deletes ONLY :ComplianceUnit nodes + REFERS_TO
  edges (a no-op when none exist) -- NEVER :Clause or the 11-02 source layer.
- Source-layer PRECONDITION: fail loud unless the backbone is present (>=1
  :Clause and no textless clauses feeding CUs) -- never mint on an empty/
  textless backbone.
- Per-stage failures collected in a list, never swallowed (T-09-08).

Cypher discipline (T-09-12): every query is static + parameterized.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import neo4j

from application.ports.output.i_model_gateway import IModelGateway
from infrastructure.config.settings import Settings
from rag.graph.ontology.cu_classifier import CUClassifier
from rag.graph.ontology.cu_extractor import CUExtractor
from rag.graph.ontology.refers_to_linker import RefersToLinker

logger = logging.getLogger(__name__)

# Deterministic doc-default actor for the few guidance-doc obligation clauses
# whose actor is only implied (framework/activity descriptions) -- reproduces
# the 11-04b manual cleanup without an LLM call.
_DOC_DEFAULT_ACTOR = [
    {"doc": "Security By Design", "actor": "the organisation"},
    {"doc": "Auditing Guidelines", "actor": "the auditor"},
    {"doc": "Cybersecurity Act 2018", "actor": "the relevant party"},
]

# Deterministic subject canonicalization: fold spelling/case variants of the
# same actor to one string so the Compliance-Gate anchor->subject match doesn't
# fragment (matched on toLower(trim(subject))).
_SUBJECT_CANONICAL = [
    {"variant": "organisations", "canonical": "the organisation"},
    {"variant": "organisation", "canonical": "the organisation"},
    {"variant": "owner of a critical information infrastructure", "canonical": "CIIO"},
    {"variant": "owner of the critical information infrastructure", "canonical": "CIIO"},
    {"variant": "the owner of a critical information infrastructure", "canonical": "CIIO"},
    {"variant": "the ciio", "canonical": "CIIO"},
    {"variant": "ciio", "canonical": "CIIO"},
    {"variant": "project manager", "canonical": "Project Manager"},
    {"variant": "steering committee", "canonical": "Steering Committee"},
    {"variant": "project steering committee", "canonical": "Steering Committee"},
    {"variant": "senior management", "canonical": "Senior Management"},
    {"variant": "the commissioner", "canonical": "Commissioner"},
    {"variant": "commissioner", "canonical": "Commissioner"},
    {"variant": "auditor", "canonical": "the auditor"},
    {"variant": "auditors", "canonical": "the auditor"},
]

_NORMALIZE_SUBJECT_QUERY = """
UNWIND $map AS m
MATCH (cu:ComplianceUnit {cu_type:'actor-CU'})
WHERE toLower(trim(cu.subject)) = m.variant AND cu.subject <> m.canonical
SET cu.subject = m.canonical
RETURN count(cu) AS n
""".strip()

# Object-as-subject extraction slips: a handful of clauses where the extractor
# put the grammatical subject (a document/object -- "the CII", "a licence", "the
# audit finding remediation plan") into the subject slot instead of the deontic
# actor. Corrected to the role-bearing actor named IN the clause. Keyed by cu_id
# (a TARGETED correction, deliberately NOT a general toLower(subject) string fold
# -- "CII"/"licence" can never be role-bearing actors, but the correct actor is
# clause-specific, so we pin each rather than blanket-map the surface string).
_SUBJECT_OVERRIDE = [
    # CCoP 2.1.2: "...remediation actions which the CIIO will take..."
    {"cu_id": "CCoP-2.1.2", "subject": "CIIO"},
    {"cu_id": "CCoP-2.1.2(a)", "subject": "CIIO"},
    # CCoP 3.8.3: CII is infrastructure; the owner (CIIO) contracts the external party.
    {"cu_id": "CCoP-3.8.3", "subject": "CIIO"},
    {"cu_id": "CCoP-3.8.3(c)", "subject": "CIIO"},
    # Act 28: "...in such form as the licensing officer may determine..."
    {"cu_id": "Act-28", "subject": "licensing officer"},
]

_OVERRIDE_SUBJECT_QUERY = """
UNWIND $overrides AS o
MATCH (cu:ComplianceUnit {cu_type:'actor-CU', cu_id: o.cu_id})
WHERE cu.subject <> o.subject
SET cu.subject = o.subject
RETURN count(cu) AS n
""".strip()

_COUNT_CLAUSES_QUERY = "MATCH (c:Clause) RETURN count(c) AS c"
_COUNT_TEXTLESS_NONHEADER_QUERY = (
    "MATCH (c:Clause) WHERE coalesce(c.is_structural_header,false)=false "
    "AND coalesce(c.text,'')='' RETURN count(c) AS c"
)
_SCOPED_TEARDOWN_QUERY = "MATCH (cu:ComplianceUnit) DETACH DELETE cu"

# Finalize: single-hop parent-CU subject inheritance for subjectless obligation
# sub-items (a lettered child's actor = its parent obligation's actor).
_INHERIT_PARENT_SUBJECT_QUERY = """
MATCH (cu:ComplianceUnit)-[:FROM_CLAUSE]->(c:Clause)
WHERE cu.cu_type IN ['actor-CU','meta-CU'] AND coalesce(cu.subject,'')='' AND coalesce(cu.constraint,'')<>''
MATCH (p:Clause)-[:HAS_CHILD]->(c)
MATCH (pcu:ComplianceUnit)-[:FROM_CLAUSE]->(p)
WHERE pcu.cu_type IN ['actor-CU','meta-CU'] AND coalesce(pcu.subject,'')<>''
SET cu.subject = pcu.subject
RETURN count(DISTINCT cu) AS n
""".strip()

_DOC_DEFAULT_SUBJECT_QUERY = """
UNWIND $defaults AS dd
MATCH (cu:ComplianceUnit {cu_type:'actor-CU', source_doc: dd.doc})
WHERE coalesce(cu.subject,'')='' AND coalesce(cu.constraint,'')<>''
SET cu.subject = dd.actor
RETURN count(cu) AS n
""".strip()

_STATS_QUERY = """
MATCH (cu:ComplianceUnit)
RETURN cu.cu_type AS cu_type, count(*) AS n
""".strip()
_COUNT_REFERS_TO_QUERY = "MATCH (:ComplianceUnit)-[r:REFERS_TO]->(:ComplianceUnit) RETURN count(r) AS c"
_COUNT_OBLIGATION_MISSING_TUPLE_QUERY = """
MATCH (cu:ComplianceUnit) WHERE cu.cu_type IN ['actor-CU','meta-CU']
  AND (cu.subject IS NULL OR cu.constraint IS NULL OR cu.context IS NULL OR cu.conditions IS NULL)
RETURN count(cu) AS c
""".strip()


@dataclass
class PolicyBuildStats:
    """Post-build stats, re-queried from Neo4j (T-09-08 -- never in-process counters)."""

    actor_cu_count: int = 0
    meta_cu_count: int = 0
    premise_count: int = 0
    refers_to_edges: int = 0
    obligation_cu_missing_tuple: int = 0
    subjects_inherited: int = 0
    subjects_doc_defaulted: int = 0
    subjects_overridden: int = 0
    subjects_normalized: int = 0
    failures: list[str] = field(default_factory=list)


class PolicyGraphBuilder:
    """
    Reproducible offline Policy-Graph build orchestrator (11-05). Reuses the
    11-04 minter; scoped teardown; source-layer precondition; failures
    collected. Injectable driver/gateway for unit-testability.
    """

    def __init__(
        self,
        settings: Settings,
        driver: Optional["neo4j.Driver"] = None,
        gateway: Optional[IModelGateway] = None,
    ) -> None:
        self.settings = settings
        self.driver = driver or neo4j.GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
        self.gateway = gateway  # injected for tests; None -> stages build their default

    def _run_scalar(self, query: str, **params: Any) -> int:
        with self.driver.session(database=self.settings.neo4j_database) as s:
            return s.run(query, **params).single()["n" if " AS n" in query else "c"]

    def assert_source_layer(self) -> None:
        """Fail loud unless the 11-02 source layer is present (D-19 follow-through)."""
        clauses = self._run_scalar(_COUNT_CLAUSES_QUERY)
        if clauses == 0:
            raise RuntimeError(
                "Policy Graph build precondition FAILED: 0 :Clause nodes. Run the "
                "Wave-2 source build first (graph seed-clauses + text alignment)."
            )
        # A WIPED/broadly-textless backbone is the corruption guard's target;
        # a handful of legitimately-empty structural Parts (e.g. the 4 Act
        # Parts that align to no body) is tolerated.
        textless = self._run_scalar(_COUNT_TEXTLESS_NONHEADER_QUERY)
        _TEXTLESS_TOLERANCE = 10
        if textless > _TEXTLESS_TOLERANCE:
            raise RuntimeError(
                f"Policy Graph build precondition FAILED: {textless} operative :Clause "
                f"node(s) carry no text (> tolerance {_TEXTLESS_TOLERANCE}) -- the source "
                f"layer looks wiped/textless; run the Wave-2 source build first."
            )

    def scoped_teardown(self) -> None:
        """Delete ONLY :ComplianceUnit + REFERS_TO (a no-op when none exist). Never :Clause."""
        with self.driver.session(database=self.settings.neo4j_database) as s:
            before = s.run(_COUNT_CLAUSES_QUERY).single()["c"]
            s.run(_SCOPED_TEARDOWN_QUERY)
            after = s.run(_COUNT_CLAUSES_QUERY).single()["c"]
        if before != after:
            raise RuntimeError(f"Scoped teardown altered :Clause backbone ({before}->{after}).")

    def _finalize_subjects(self, stats: PolicyBuildStats) -> None:
        """Deterministic subject completion (folds the 11-04b cleanup into the pipeline)."""
        with self.driver.session(database=self.settings.neo4j_database) as s:
            stats.subjects_inherited = s.run(_INHERIT_PARENT_SUBJECT_QUERY).single()["n"]
            stats.subjects_doc_defaulted = s.run(
                _DOC_DEFAULT_SUBJECT_QUERY, defaults=_DOC_DEFAULT_ACTOR
            ).single()["n"]
            # Correct object-as-subject slips BEFORE canonicalization so an
            # overridden value still folds through the variant map if needed.
            stats.subjects_overridden = s.run(
                _OVERRIDE_SUBJECT_QUERY, overrides=_SUBJECT_OVERRIDE
            ).single()["n"]
            stats.subjects_normalized = s.run(
                _NORMALIZE_SUBJECT_QUERY, map=_SUBJECT_CANONICAL
            ).single()["n"]

    async def build(self, drop: bool = True, resolve_implicit: bool = False) -> PolicyBuildStats:
        """Run the full offline Policy-Graph build on the persisted source layer."""
        self.assert_source_layer()
        stats = PolicyBuildStats()
        if drop:
            self.scoped_teardown()

        try:
            await CUClassifier(self.settings, driver=self.driver, gateway=self.gateway).classify_and_mint()
        except Exception as e:  # per-stage failure collected, never swallowed
            stats.failures.append(f"classify: {e}")
        try:
            await CUExtractor(self.settings, driver=self.driver, gateway=self.gateway).extract()
        except Exception as e:
            stats.failures.append(f"extract: {e}")
        try:
            self._finalize_subjects(stats)
        except Exception as e:
            stats.failures.append(f"finalize: {e}")
        try:
            await RefersToLinker(self.settings, driver=self.driver, gateway=self.gateway).link(
                resolve_implicit=resolve_implicit
            )
        except Exception as e:
            stats.failures.append(f"link: {e}")

        self._accumulate_stats(stats)
        return stats

    def _accumulate_stats(self, stats: PolicyBuildStats) -> None:
        try:
            with self.driver.session(database=self.settings.neo4j_database) as s:
                for r in s.run(_STATS_QUERY):
                    if r["cu_type"] == "actor-CU":
                        stats.actor_cu_count = r["n"]
                    elif r["cu_type"] == "meta-CU":
                        stats.meta_cu_count = r["n"]
                    elif r["cu_type"] == "premise":
                        stats.premise_count = r["n"]
                stats.refers_to_edges = s.run(_COUNT_REFERS_TO_QUERY).single()["c"]
                stats.obligation_cu_missing_tuple = s.run(
                    _COUNT_OBLIGATION_MISSING_TUPLE_QUERY
                ).single()["c"]
        except Exception as e:
            logger.warning(f"Could not query PolicyBuildStats: {e}")


__all__: list[str] = ["PolicyGraphBuilder", "PolicyBuildStats"]
