"""
Policy Graph Stage 1 -- CU Classification + Minting (Phase 11, D-03/D-07
corrected).

Classifies every non-structural seeded `:Clause` (11-01/11-02's source
layer -- verbatim text + namespaced `citation_id` + `doc_class` +
`function_type` + `is_structural_header`) three ways -- `premise` /
`meta-CU` / `actor-CU` -- and MINTS a typed `:ComplianceUnit` node per
classification, MERGE-linked to its source clause. A Compliance Unit is a
GraphCompliance OBLIGATION (D-07, corrected): CU identity and count are the
OUTPUT of this pass, EMERGENT -- never reconciled against clause/
operative-leaf arithmetic. A clause classified purely `premise` still mints
a `:ComplianceUnit` (typed `premise`, D-09 -- premise text stays embedded/
retrievable as a runtime confidence signal) but that CU is never an
"obligation CU" (`OBLIGATION_CU_TYPES` = meta-CU/actor-CU only, the set
Stage 2 (`cu_extractor.py`) formalizes into a 4-tuple). A structural header
(chapter/section skeleton) never becomes a CU at all -- it stays pure
`:HAS_CHILD` hierarchy (D-06/D-07).

Warm-start (D-03): Phase-10's `function_type` tag (`ScopeClause` /
`ControlClause` / `DefinitionClause`, stamped on every `:Clause` by
`clause_seeder.py`'s `_derive_function_type`) maps DETERMINISTICALLY onto a
CU type via `FUNCTION_TYPE_TO_CU_TYPE` -- NO LLM call for any clause that
already carries a recognized tag (per the corpus state at build time, this
is effectively every clause, D-03/model_directive). The LLM classification
path (`_classify_cu_types`) is a fallback for any clause with a missing or
unrecognized `function_type`, routed through an injectable `IModelGateway`
-- the LOCAL `ClaudeCliGateway` (`claude -p --model claude-opus-4-8` per
`settings.cu_extraction_model`), NOT OpenRouter (user directive
2026-07-05) -- mirroring `function_type_routing.py::_classify_function_type`'s
defensive quote-strip / enum-or-default / never-raise shape, extended to
parse a POSSIBLY MULTI-VALUE response: a clause carrying more than one
distinct obligation classifies into more than one CU type, comma/semicolon/
newline-separated, and mints more than one `:ComplianceUnit` (D-07's "a
clause may spawn more than one CU").

Minting reuses `clause_seeder.py`'s idempotent MERGE + composite-uniqueness-
constraint discipline: the `(cu_id, source_doc)` pair is the CU's MERGE key,
mirroring the `(clause_id, source_doc)` key already established for
`:Clause` (D-08 namespacing). `cu_id` reuses the source clause's namespaced
`citation_id` for the (overwhelmingly common) single-CU case; a multi-CU
clause appends a 1-based ordinal suffix (`"CCoP-5.3.1#2"`) to keep the key
unique.

Cypher discipline (T-09-12): every query below is a static, module-level
string parameterized via `$units`/`$entries` -- no value is ever spliced
into query text via f-string/`.format()`.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

import neo4j

from application.ports.output.i_model_gateway import IModelGateway
from infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)

# D-07 corrected: a Compliance Unit is an obligation typed one of exactly
# these three values -- LOCKED 3-value enum, never invented/expanded.
VALID_CU_TYPES = frozenset({"premise", "meta-CU", "actor-CU"})

# Safe degrade default (never raise on bad LLM output, T-09-08): `premise`
# is inert -- it is never judged and never falsely creates an obligation
# that Stage 2 would try to formalize into a 4-tuple. Degrading "wrong" is
# always safer here than degrading to an obligation type.
DEFAULT_CU_TYPE = "premise"

# CU types that Stage 2 (`cu_extractor.py`) formalizes into a 4-tuple.
# Premises are explicitly excluded (D-07/D-09 -- definitional text carriers
# for hypernym mapping, never judged).
OBLIGATION_CU_TYPES = frozenset({"meta-CU", "actor-CU"})

# D-03 warm-start: Phase-10 function-type tags (`clause_seeder.py`'s
# `FUNCTION_TYPE_TAGS`) map deterministically onto a CU type. This dict is
# the ENTIRE warm-start rule -- no clause-id-specific special-casing here
# (that lives in `clause_seeder.py`'s own `_derive_function_type`).
FUNCTION_TYPE_TO_CU_TYPE: dict[str, str] = {
    "DefinitionClause": "premise",
    "ScopeClause": "meta-CU",
    "ControlClause": "actor-CU",
}

CU_CLASSIFICATION_PROMPT = """Classify this regulatory clause's content as one or more of:
premise (non-deontic definitional/interpretive text -- never an obligation), meta-CU (an applicability/scope gate), actor-CU (an obligation imposed on a role-bearing actor).

If the clause text contains more than one distinct obligation, return each classification separated by a comma, in the order they appear. Otherwise return exactly one label.

Clause text:
{text}

Answer with ONLY the label(s) -- one or more of: premise, meta-CU, actor-CU (comma-separated if more than one). No other text."""

_SPLIT_RE = re.compile(r"[,;\n]")


def _split_classification_output(raw: str) -> list[str]:
    """
    Split a (possibly multi-value) LLM classification response into
    individual, defensively-stripped tokens (mirrors
    `function_type_routing.py::_classify_function_type`'s quote/punctuation
    stripping, extended to a list instead of a single value).
    """
    if not raw:
        return []
    return [tok.strip().strip("\"'. \n\t") for tok in _SPLIT_RE.split(raw) if tok.strip()]


async def _classify_cu_types(
    clause: dict[str, Any],
    gateway: IModelGateway,
    settings: Settings,
) -> list[str]:
    """
    Classify one clause into one or more CU types (D-03).

    Warm-start short-circuit: a recognized `function_type` tag resolves
    deterministically, NO LLM call. Otherwise falls back to an LLM
    classification call through `gateway` (Claude CLI,
    `settings.cu_extraction_model` = `claude-opus-4-8` per the user
    directive), parsing a possibly multi-value response. Malformed/empty/
    all-invalid output degrades to `[DEFAULT_CU_TYPE]` and logs a warning --
    NEVER raises (one bad unit never aborts the batch, T-09-08/T-11-08).
    """
    function_type = clause.get("function_type") or ""
    warm_start = FUNCTION_TYPE_TO_CU_TYPE.get(function_type)
    if warm_start is not None:
        return [warm_start]

    clause_ref = f"{clause.get('source_doc')}::{clause.get('clause_id')}"
    try:
        response = await gateway.generate_response(
            prompt=CU_CLASSIFICATION_PROMPT.format(text=clause.get("text") or ""),
            model_name=settings.cu_extraction_model,
            temperature=0.0,
            max_tokens=20,
        )
        tokens = _split_classification_output(response.content)
        valid = [tok for tok in tokens if tok in VALID_CU_TYPES]
        if not valid:
            logger.warning(
                f"CU classification for {clause_ref} returned no valid "
                f"label(s) ({response.content!r}); defaulting to {DEFAULT_CU_TYPE!r}"
            )
            return [DEFAULT_CU_TYPE]
        return valid
    except Exception as e:
        logger.warning(
            f"CU classification failed for {clause_ref}: {e}; "
            f"defaulting to {DEFAULT_CU_TYPE!r}"
        )
        return [DEFAULT_CU_TYPE]


def _build_cu_units(clause: dict[str, Any], cu_types: list[str]) -> list[dict[str, Any]]:
    """
    Build the mint payload (one dict per CU) for a classified clause -- pure,
    Neo4j-free, unit-testable in isolation. `cu_id` reuses the source
    clause's namespaced `citation_id` (D-08) for the single-CU case; a
    multi-obligation clause (`len(cu_types) > 1`) appends a 1-based ordinal
    suffix so every CU's `(cu_id, source_doc)` MERGE key stays unique.
    """
    citation_id = clause["citation_id"]
    clause_id = clause["clause_id"]
    source_doc = clause["source_doc"]
    units: list[dict[str, Any]] = []
    for i, cu_type in enumerate(cu_types, start=1):
        cu_id = citation_id if len(cu_types) == 1 else f"{citation_id}#{i}"
        units.append(
            {
                "cu_id": cu_id,
                "cu_type": cu_type,
                "clause_id": clause_id,
                "source_doc": source_doc,
            }
        )
    return units


# Static, parameterized Cypher (T-09-12) -- every variable input is bound via
# session.run(..., **params), never string-interpolated.
_FETCH_CANDIDATE_CLAUSES_QUERY = """
MATCH (c:Clause)
WHERE coalesce(c.is_structural_header, false) = false
RETURN c.clause_id AS clause_id, c.source_doc AS source_doc,
       c.citation_id AS citation_id, c.function_type AS function_type,
       c.text AS text
""".strip()

_MINT_CU_QUERY = """
UNWIND $units AS unit
MATCH (c:Clause {clause_id: unit.clause_id, source_doc: unit.source_doc})
MERGE (cu:ComplianceUnit {cu_id: unit.cu_id, source_doc: unit.source_doc})
SET cu.cu_type = unit.cu_type
MERGE (cu)-[:FROM_CLAUSE]->(c)
""".strip()

_COUNT_CU_TYPES_QUERY = """
MATCH (cu:ComplianceUnit)
RETURN cu.cu_type AS cu_type, count(cu) AS c
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
    Emergent CU-mint build stats (D-07 corrected: reported as an OUTPUT,
    NEVER asserted as `count == operative-leaf`/`== 883`/any clause
    arithmetic). `actor_cu_count`/`meta_cu_count`/`premise_count` are
    authoritative post-write re-queries from Neo4j (T-09-08 -- never
    trusted from in-process counters).
    """

    clauses_considered: int = 0
    llm_classification_calls: int = 0
    actor_cu_count: int = 0
    meta_cu_count: int = 0
    premise_count: int = 0
    cu_without_source_text_count: int = 0
    cu_without_source_link_count: int = 0


class CUClassifier:
    """
    Stage 1: classify every non-structural seeded `:Clause` into premise/
    meta-CU/actor-CU and MINT the typed `:ComplianceUnit` node(s), MERGE-
    linked to the source clause.

    PRECONDITION: the `:Clause` backbone must already be seeded + source-
    annotated + text-aligned (11-01/11-02 -- `ClauseSeeder`,
    `ClauseSourceAnnotator`, `ClauseTextAligner`). This class only reads
    `:Clause` nodes and MERGEs new `:ComplianceUnit` nodes; it never mutates
    `:Clause` properties.
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
            # Lazy import: avoids a hard dependency on the Claude CLI
            # gateway (+ its ILogger port) for callers that always inject a
            # gateway (e.g. unit tests with a fake).
            from infrastructure.adapters.logging.console_logger import ConsoleLogger
            from infrastructure.adapters.models.claude_cli_gateway import ClaudeCliGateway

            self.gateway = ClaudeCliGateway(
                logger=ConsoleLogger(log_level=settings.log_level),
                timeout=settings.claude_cli_timeout,
            )
        self._ensure_constraint()

    def _ensure_constraint(self) -> None:
        """Idempotently create a composite uniqueness constraint on (cu_id, source_doc)."""
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
            result = session.run(_FETCH_CANDIDATE_CLAUSES_QUERY)
            return [dict(record) for record in result]

    async def classify_and_mint(self) -> CUMintStats:
        """
        Classify every candidate (non-structural-header) clause and mint its
        CU(s), then report authoritative post-write counts (T-09-08).
        """
        clauses = self._fetch_candidate_clauses()
        stats = CUMintStats(clauses_considered=len(clauses))

        units: list[dict[str, Any]] = []
        for clause in clauses:
            if not FUNCTION_TYPE_TO_CU_TYPE.get(clause.get("function_type") or ""):
                stats.llm_classification_calls += 1
            cu_types = await _classify_cu_types(clause, self.gateway, self.settings)
            units.extend(_build_cu_units(clause, cu_types))

        if units:
            with self.driver.session(database=self.settings.neo4j_database) as session:
                session.run(_MINT_CU_QUERY, units=units)

        self._accumulate_stats(stats)
        return stats

    def _accumulate_stats(self, stats: CUMintStats) -> None:
        """Query Neo4j directly for authoritative post-mint counts (T-09-08)."""
        try:
            with self.driver.session(database=self.settings.neo4j_database) as session:
                for record in session.run(_COUNT_CU_TYPES_QUERY):
                    cu_type = record["cu_type"]
                    count = record["c"]
                    if cu_type == "actor-CU":
                        stats.actor_cu_count = count
                    elif cu_type == "meta-CU":
                        stats.meta_cu_count = count
                    elif cu_type == "premise":
                        stats.premise_count = count
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
    "DEFAULT_CU_TYPE",
    "OBLIGATION_CU_TYPES",
    "FUNCTION_TYPE_TO_CU_TYPE",
    "CU_CLASSIFICATION_PROMPT",
]
