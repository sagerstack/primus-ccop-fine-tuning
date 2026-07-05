"""
Policy Graph Stage 1 -- CU Classification + Minting (Phase 11, 11-04b /
D-30/D-31/D-32/D-33/D-35).

REWRITE of the 11-04 classifier. Classifies every routed candidate clause
(from `cu_candidate_gate.route_candidates`) into the GraphCompliance typology
and MINTS a typed `:ComplianceUnit` node per classification, MERGE-linked to
its source clause.

The single biggest change vs 11-04 (D-30): typing is now a PER-UNIT LLM
SEMANTIC JUDGMENT, not a predetermined `function_type` table. Every
`llm_classify` candidate gets a real Opus call carrying the paper's verbatim
premise/meta-CU/actor-CU definitions; `function_type` and `doc_class` are
passed only as SOFT HINTS ("prior signal, may be wrong"). The 11-04
warm-start-as-decider (which defaulted every non-CCoP-chapter-1 clause to
actor-CU, producing 744/770 actor-CUs) is GONE.

Two-level typology (D-31), per GraphCompliance §3.1:
- premise: non-deontic definitional/interpretive/scope/purpose text -- needed
  to read the code, NEVER judged. Carries a `premise_kind` facet (D-33:
  definition | scope | purpose | interpretation).
- actor-CU: an obligation/prohibition/permission addressed to a role-bearing
  actor -- the unit judged. Carries a `modality` facet (D-31/D-35: obligation
  | prohibition | permission; regulator powers are permission actor-CUs, NOT
  excluded).
- meta-CU: an applicability/scope gate -- evaluated first, never a standalone
  violation.

Response-to-Feedback candidates arrive pre-routed `force_premise_interpretation`
(D-32): they SKIP the LLM and mint directly as premise(kind=interpretation).

A single clause may spawn MORE THAN ONE CU (D-07 preserved) -- the LLM returns
a JSON array of classifications; a multi-CU clause appends a 1-based ordinal
suffix to keep each `(cu_id, source_doc)` MERGE key unique.

Degrade-safe (T-11-08): malformed/empty LLM output degrades to a single
premise(definition) -- inert, never a false obligation -- and logs; NEVER
raises (one bad unit never aborts the ~770-candidate batch).

Cypher discipline (T-09-12): every query is a static, module-level string
parameterized via `$units`/`$obligation_types` -- no value is ever spliced in.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import neo4j

from application.ports.output.i_model_gateway import IModelGateway
from infrastructure.config.settings import Settings
from rag.graph.ontology.cu_candidate_gate import (
    ROUTE_FORCE_PREMISE_INTERPRETATION,
    Candidate,
    route_candidates,
)

logger = logging.getLogger(__name__)

# LOCKED 3-value type enum (GraphCompliance §3.1) -- never invented/expanded.
VALID_CU_TYPES = frozenset({"premise", "meta-CU", "actor-CU"})

# Deontic modality on actor-CUs (D-31/D-35). Regulator powers are `permission`.
VALID_MODALITIES = frozenset({"obligation", "prohibition", "permission"})

# premise facets (D-33) -- distinguishes glossary definitions from RtF
# clarifications at retrieval time without a new node label.
VALID_PREMISE_KINDS = frozenset({"definition", "scope", "purpose", "interpretation"})

# Safe-degrade default (T-11-08): `premise` is inert -- never judged, never a
# false obligation. Degrading "wrong" is always safer than degrading to an
# obligation type.
DEFAULT_CU_TYPE = "premise"
DEFAULT_PREMISE_KIND = "definition"
DEFAULT_MODALITY = "obligation"

# The forced route (RtF) mints this exact classification, no LLM.
_FORCED_INTERPRETATION_CLASSIFICATION = {
    "cu_type": "premise",
    "modality": "",
    "premise_kind": "interpretation",
}

# CU types Stage 2 (`cu_extractor.py`) formalizes into a 4-tuple. Premises are
# excluded (definitional carriers, never judged). Imported by cu_extractor --
# keep this symbol name stable.
OBLIGATION_CU_TYPES = frozenset({"meta-CU", "actor-CU"})

CU_CLASSIFICATION_PROMPT = """You are classifying ONE regulatory provision into one or more Compliance Units, following the GraphCompliance schema.

Definitions (use these exactly):
- premise: non-deontic DEFINITIONAL / INTERPRETIVE / SCOPE / PURPOSE material -- terms, role definitions, scope statements, purposes, clarifications. Needed to READ the code, but NEVER itself judged for compliance.
- actor-CU: an obligation, prohibition, or permission ADDRESSED TO A ROLE-BEARING ACTOR (e.g. the CIIO, the Commissioner, a vendor). This is a unit that is actually judged. A regulator's discretionary power ("the Commissioner may ...") is an actor-CU with modality "permission".
- meta-CU: an APPLICABILITY / SCOPE GATE (temporal or territorial scope, role qualification, which systems are covered) that decides WHETHER an actor-CU applies. Evaluated first; never a standalone violation.

MOST provisions are a SINGLE unit -- return exactly one object. Return MULTIPLE units ONLY when the provision contains genuinely DISTINCT obligations with different actions (e.g. an applicability gate PLUS a separate obligation). Do NOT split a single requirement's enumerated conditions, exceptions, or lettered sub-items into separate units -- those belong inside that unit's conditions. A "must/shall not X unless (a)(b)(c)" provision is ONE unit whose conditions are (a)(b)(c). A definitional or interpretive provision (premise) is ALWAYS exactly one unit -- never repeat it. Never return the same classification twice.

For each unit return an object with:
- "type": exactly one of premise | actor-CU | meta-CU
- "modality": for actor-CU ONLY, one of obligation | prohibition | permission (the deontic force). Use "" otherwise.
- "premise_kind": for premise ONLY, one of definition | scope | purpose | interpretation. Use "" otherwise.

Prior signal (MAY BE WRONG -- do not trust blindly, judge the text): function_type={function_type}, doc_class={doc_class}.

Provision text:
{text}

Return ONLY a JSON array of objects, e.g. [{{"type":"actor-CU","modality":"obligation","premise_kind":""}}]. No prose, no backticks."""


def _clean_token(value: Any) -> str:
    return value.strip().strip("\"'. \n\t") if isinstance(value, str) else ""


def _normalize_classification(entry: dict[str, Any]) -> Optional[dict[str, str]]:
    """
    Validate + normalize one LLM classification object into
    `{cu_type, modality, premise_kind}`, or None if the type is invalid.
    Modality is only kept for actor-CU; premise_kind only for premise; each
    defaults to a safe value when actor/premise but missing.
    """
    cu_type = _clean_token(entry.get("type"))
    if cu_type not in VALID_CU_TYPES:
        return None

    modality = ""
    premise_kind = ""
    if cu_type == "actor-CU":
        m = _clean_token(entry.get("modality"))
        modality = m if m in VALID_MODALITIES else DEFAULT_MODALITY
    elif cu_type == "premise":
        pk = _clean_token(entry.get("premise_kind"))
        premise_kind = pk if pk in VALID_PREMISE_KINDS else DEFAULT_PREMISE_KIND
    return {"cu_type": cu_type, "modality": modality, "premise_kind": premise_kind}


def _parse_classifications(raw: str) -> list[dict[str, str]]:
    """
    Parse a (possibly multi-unit) LLM classification response into a list of
    normalized classifications. Reuses `neo4j_graphrag`'s `fix_invalid_json`
    (Don't-Hand-Roll). Accepts either a JSON array or a single object.
    Returns [] on total failure (caller degrades).
    """
    from neo4j_graphrag.experimental.components.entity_relation_extractor import (
        fix_invalid_json,
    )
    from neo4j_graphrag.experimental.pipeline.exceptions import InvalidJSONError

    if not raw or not raw.strip():
        return []
    try:
        parsed = json.loads(fix_invalid_json(raw))
    except (json.JSONDecodeError, InvalidJSONError):
        return []

    entries = parsed if isinstance(parsed, list) else [parsed]
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        normalized = _normalize_classification(entry)
        if normalized is None:
            continue
        # Dedup safety net (D-07 guardrail): the LLM sometimes over-splits a
        # single definition/obligation into many identical units, which would
        # mint spurious `#1..#N` duplicate CUs. Collapse identical
        # (type, modality, premise_kind) classifications, preserving order.
        key = (normalized["cu_type"], normalized["modality"], normalized["premise_kind"])
        if key in seen:
            continue
        seen.add(key)
        out.append(normalized)
    return out


async def _classify_candidate(
    candidate: Candidate,
    gateway: IModelGateway,
    settings: Settings,
) -> list[dict[str, str]]:
    """
    Classify one routed candidate into one or more CU classifications (D-30).

    Forced-route (RtF) candidates skip the LLM and return a single
    premise(interpretation). Otherwise a real LLM call classifies the text;
    malformed/empty output degrades to a single premise(definition) and logs
    -- NEVER raises (T-11-08).
    """
    if candidate.route == ROUTE_FORCE_PREMISE_INTERPRETATION:
        return [dict(_FORCED_INTERPRETATION_CLASSIFICATION)]

    cu_ref = f"{candidate.source_doc}::{candidate.clause_id}"
    try:
        response = await gateway.generate_response(
            prompt=CU_CLASSIFICATION_PROMPT.format(
                function_type=candidate.function_type or "unknown",
                doc_class=candidate.doc_class or "unknown",
                text=candidate.text or "",
            ),
            model_name=settings.cu_extraction_model,
            temperature=0.0,
            max_tokens=200,
        )
    except Exception as e:
        logger.warning(
            f"CU classification gateway call failed for {cu_ref}: {e}; "
            f"degrading to premise({DEFAULT_PREMISE_KIND})"
        )
        return [{"cu_type": DEFAULT_CU_TYPE, "modality": "", "premise_kind": DEFAULT_PREMISE_KIND}]

    classifications = _parse_classifications(response.content)
    if not classifications:
        logger.warning(
            f"CU classification for {cu_ref} returned no valid unit "
            f"({response.content!r}); degrading to premise({DEFAULT_PREMISE_KIND})"
        )
        return [{"cu_type": DEFAULT_CU_TYPE, "modality": "", "premise_kind": DEFAULT_PREMISE_KIND}]
    return classifications


def _build_cu_units(
    candidate: Candidate, classifications: list[dict[str, str]]
) -> list[dict[str, Any]]:
    """
    Build the mint payload (one dict per CU) for a classified candidate --
    pure, Neo4j-free. `cu_id` reuses the source clause's namespaced
    `citation_id` for the single-CU case; a multi-CU clause appends a 1-based
    ordinal suffix so every `(cu_id, source_doc)` MERGE key stays unique.
    """
    citation_id = candidate.citation_id
    units: list[dict[str, Any]] = []
    multi = len(classifications) > 1
    for i, cls in enumerate(classifications, start=1):
        cu_id = f"{citation_id}#{i}" if multi else citation_id
        units.append(
            {
                "cu_id": cu_id,
                "cu_type": cls["cu_type"],
                "modality": cls.get("modality", ""),
                "premise_kind": cls.get("premise_kind", ""),
                "clause_id": candidate.clause_id,
                "source_doc": candidate.source_doc,
            }
        )
    return units


# Static, parameterized Cypher (T-09-12).
_FETCH_CANDIDATE_CLAUSES_QUERY = """
MATCH (c:Clause)
WHERE coalesce(c.is_structural_header, false) = false
RETURN c.clause_id AS clause_id, c.source_doc AS source_doc,
       c.citation_id AS citation_id, c.function_type AS function_type,
       c.doc_class AS doc_class, c.text AS text,
       coalesce(c.is_structural_header, false) AS is_structural_header
""".strip()

_MINT_CU_QUERY = """
UNWIND $units AS unit
MATCH (c:Clause {clause_id: unit.clause_id, source_doc: unit.source_doc})
MERGE (cu:ComplianceUnit {cu_id: unit.cu_id, source_doc: unit.source_doc})
SET cu.cu_type = unit.cu_type,
    cu.modality = unit.modality,
    cu.premise_kind = unit.premise_kind
MERGE (cu)-[:FROM_CLAUSE]->(c)
""".strip()

_COUNT_CU_TYPES_QUERY = """
MATCH (cu:ComplianceUnit)
RETURN cu.cu_type AS cu_type, count(cu) AS c
""".strip()

_COUNT_MODALITY_QUERY = """
MATCH (cu:ComplianceUnit {cu_type: 'actor-CU'})
RETURN coalesce(cu.modality, '') AS modality, count(cu) AS c
""".strip()

_COUNT_PREMISE_KIND_QUERY = """
MATCH (cu:ComplianceUnit {cu_type: 'premise'})
RETURN coalesce(cu.premise_kind, '') AS premise_kind, count(cu) AS c
""".strip()

_COUNT_CU_WITHOUT_SOURCE_TEXT_QUERY = """
MATCH (cu:ComplianceUnit)-[:FROM_CLAUSE]->(c:Clause)
WHERE c.text IS NULL OR c.text = ''
RETURN count(cu) AS c
""".strip()

_COUNT_CU_WITHOUT_SOURCE_LINK_QUERY = """
MATCH (cu:ComplianceUnit)
WHERE NOT (cu)-[:FROM_CLAUSE]->(:Clause)
RETURN count(cu) AS c
""".strip()


@dataclass
class CUMintStats:
    """
    Emergent CU-mint build stats (D-07: reported as OUTPUT, never asserted as
    count == clause arithmetic). All count fields are authoritative post-write
    re-queries from Neo4j (T-09-08).
    """

    candidates_considered: int = 0
    forced_premise_count: int = 0
    llm_classification_calls: int = 0
    actor_cu_count: int = 0
    meta_cu_count: int = 0
    premise_count: int = 0
    modality_distribution: dict[str, int] = field(default_factory=dict)
    premise_kind_distribution: dict[str, int] = field(default_factory=dict)
    cu_without_source_text_count: int = 0
    cu_without_source_link_count: int = 0


class CUClassifier:
    """
    Stage 1 (11-04b): route + classify + mint typed `:ComplianceUnit` nodes.

    PRECONDITION: the `:Clause` backbone must already be seeded + source-
    annotated + text-aligned (11-01/11-02). This class only reads `:Clause`
    nodes and MERGEs `:ComplianceUnit` nodes; it never mutates `:Clause`.
    """

    def __init__(
        self,
        settings: Settings,
        driver: Optional["neo4j.Driver"] = None,
        gateway: Optional[IModelGateway] = None,
    ) -> None:
        self.settings = settings
        self.driver = driver or neo4j.GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        if gateway is not None:
            self.gateway = gateway
        else:
            from infrastructure.adapters.logging.console_logger import ConsoleLogger
            from infrastructure.adapters.models.claude_cli_gateway import ClaudeCliGateway

            self.gateway = ClaudeCliGateway(
                logger=ConsoleLogger(log_level=settings.log_level),
                timeout=settings.claude_cli_timeout,
            )
        self._ensure_constraint()

    def _ensure_constraint(self) -> None:
        try:
            with self.driver.session(database=self.settings.neo4j_database) as session:
                session.run(
                    "CREATE CONSTRAINT compliance_unit_id_source_doc_unique IF NOT EXISTS "
                    "FOR (cu:ComplianceUnit) REQUIRE (cu.cu_id, cu.source_doc) IS UNIQUE"
                )
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("ComplianceUnit uniqueness constraint already exists — skipping creation.")
            else:
                logger.warning(f"Could not create ComplianceUnit uniqueness constraint (non-fatal): {e}")

    def _fetch_candidate_clauses(self) -> list[dict[str, Any]]:
        with self.driver.session(database=self.settings.neo4j_database) as session:
            return [dict(record) for record in session.run(_FETCH_CANDIDATE_CLAUSES_QUERY)]

    async def classify_and_mint(self, batch_size: int = 20) -> CUMintStats:
        """
        Route + classify every candidate clause and mint its CU(s), then
        report authoritative post-write counts (T-09-08). Writes incrementally
        every `batch_size` candidates so a crash mid-run (this is a ~770-call
        real-Opus batch) never loses more than one batch of work.
        """
        candidates = route_candidates(self._fetch_candidate_clauses())
        stats = CUMintStats(candidates_considered=len(candidates))

        batch: list[dict[str, Any]] = []
        for i, candidate in enumerate(candidates, start=1):
            if candidate.route == ROUTE_FORCE_PREMISE_INTERPRETATION:
                stats.forced_premise_count += 1
            else:
                stats.llm_classification_calls += 1
            classifications = await _classify_candidate(candidate, self.gateway, self.settings)
            batch.extend(_build_cu_units(candidate, classifications))
            if len(batch) >= batch_size:
                self._mint_batch(batch)
                logger.info(f"CU classify+mint progress: {i}/{len(candidates)} candidates")
                batch = []
        self._mint_batch(batch)

        self._accumulate_stats(stats)
        return stats

    def _mint_batch(self, units: list[dict[str, Any]]) -> None:
        if not units:
            return
        with self.driver.session(database=self.settings.neo4j_database) as session:
            session.run(_MINT_CU_QUERY, units=units)

    def _accumulate_stats(self, stats: CUMintStats) -> None:
        """Query Neo4j directly for authoritative post-mint counts (T-09-08)."""
        try:
            with self.driver.session(database=self.settings.neo4j_database) as session:
                for record in session.run(_COUNT_CU_TYPES_QUERY):
                    cu_type, count = record["cu_type"], record["c"]
                    if cu_type == "actor-CU":
                        stats.actor_cu_count = count
                    elif cu_type == "meta-CU":
                        stats.meta_cu_count = count
                    elif cu_type == "premise":
                        stats.premise_count = count
                stats.modality_distribution = {
                    r["modality"]: r["c"] for r in session.run(_COUNT_MODALITY_QUERY)
                }
                stats.premise_kind_distribution = {
                    r["premise_kind"]: r["c"] for r in session.run(_COUNT_PREMISE_KIND_QUERY)
                }
                stats.cu_without_source_text_count = session.run(
                    _COUNT_CU_WITHOUT_SOURCE_TEXT_QUERY
                ).single()["c"]
                stats.cu_without_source_link_count = session.run(
                    _COUNT_CU_WITHOUT_SOURCE_LINK_QUERY
                ).single()["c"]
        except Exception as e:
            logger.warning(f"Could not query CU-mint stats after classify_and_mint: {e}")


__all__: list[str] = [
    "CUClassifier",
    "CUMintStats",
    "VALID_CU_TYPES",
    "VALID_MODALITIES",
    "VALID_PREMISE_KINDS",
    "DEFAULT_CU_TYPE",
    "DEFAULT_PREMISE_KIND",
    "DEFAULT_MODALITY",
    "OBLIGATION_CU_TYPES",
    "CU_CLASSIFICATION_PROMPT",
    "_parse_classifications",
    "_classify_candidate",
    "_build_cu_units",
]
