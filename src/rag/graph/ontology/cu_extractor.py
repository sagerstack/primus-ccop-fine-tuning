"""
Policy Graph Stage 2 -- 4-Tuple Extraction on Obligation CUs (Phase 11,
D-04/D-07/D-13).

Formalizes every obligation `:ComplianceUnit` (`cu_type` in
`OBLIGATION_CU_TYPES` = `{meta-CU, actor-CU}`, minted by `cu_classifier.py`)
into the GraphCompliance 4-tuple **subject / constraint / context /
conditions** via schema-constrained LLM extraction, modeled on
`ontology_kg_builder.ONTOLOGY_EXTRACTION_PROMPT`'s locked-vocabulary,
do-not-invent, strict-JSON-only discipline (swap the node/relationship
schema for the CU-tuple schema).

Premises are explicitly EXCLUDED from this pass (D-07/D-09 -- they are
definitional text carriers for hypernym mapping, never obligations, never
judged). Extraction routes through the SAME injectable `IModelGateway` the
Stage-1 classifier uses -- the LOCAL `ClaudeCliGateway`
(`settings.cu_extraction_model` = `claude-opus-4-8`, user directive
2026-07-05), NOT OpenRouter.

JSON parsing/validation mirrors `gleaning_extractor.py`'s
`_parse_graph_response` try/except/degrade shape EXACTLY: reuse
`neo4j_graphrag`'s `fix_invalid_json` (Don't-Hand-Roll -- no hand-rolled JSON
repair), Pydantic-validate into `CUTuple`, and on ANY parse/validation/
gateway failure degrade to an EMPTY `CUTuple` (all four fields explicit
empty string, never null) -- log, never raise, never crash the batch
(T-09-08/T-11-08). The CU's source clause `text` property is NEVER written
by this module (D-13: tuple = reasoning representation, text = citation
payload -- extraction loss can never remove the real text, because this
module only SETs tuple fields on the `:ComplianceUnit` node, never touches
`:Clause`).

Cypher discipline (T-09-12): every query below is a static, module-level
string parameterized via `$obligation_types`/`$tuples` -- no value is ever
spliced into query text via f-string/`.format()`.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

import neo4j
from pydantic import BaseModel, ValidationError, field_validator

from application.ports.output.i_model_gateway import IModelGateway
from infrastructure.config.settings import Settings
from rag.graph.ontology.cu_classifier import OBLIGATION_CU_TYPES

logger = logging.getLogger(__name__)

_TUPLE_FIELDS = ("subject", "constraint", "context", "conditions")


class CUTuple(BaseModel):
    """
    GraphCompliance's obligation 4-tuple (D-04). All four fields default to
    an explicit empty string -- `null` is never a valid persisted value
    (acceptance criteria: "empty-string allowed, null not allowed"); the
    `mode="before"` validator coerces any `null`/missing field the LLM (or a
    degrade path) produces into `""` rather than letting it through as
    `None`.
    """

    subject: str = ""
    constraint: str = ""
    context: str = ""
    conditions: str = ""

    @field_validator("subject", "constraint", "context", "conditions", mode="before")
    @classmethod
    def _null_to_empty(cls, value: Any) -> str:
        return "" if value is None else value

    def is_empty(self) -> bool:
        """True iff every field is the empty string (the degrade-path shape)."""
        return not any(getattr(self, f) for f in _TUPLE_FIELDS)


# D-04/D-07: schema-constrained 4-tuple extraction prompt, modeled on
# `ontology_kg_builder.ONTOLOGY_EXTRACTION_PROMPT`'s locked-vocabulary,
# do-not-invent, strict-JSON-only discipline -- swapping the node/
# relationship schema for the CU-tuple schema.
CU_TUPLE_EXTRACTION_PROMPT = """
You are formalizing ONE regulatory Compliance Unit (an obligation) into its
canonical 4-tuple representation for structured compliance reasoning.

IMPORTANT: This text is a REGULATORY CODE OF PRACTICE. Do NOT invent facts,
actors, or requirements that are not explicitly stated in the clause text
below. If a field cannot be determined from the text, return an empty
string ("") for that field -- never omit the key, never return null.

Formalize the clause text into EXACTLY these four fields:
- "subject": the role-bearing actor this obligation applies to (e.g. "CIIO", "the Commissioner", "the owner")
- "constraint": the deontic action/requirement imposed (what must/must not be done)
- "context": the object/system/domain the constraint applies to
- "conditions": any qualifying conditions, exceptions, or triggers (empty string if unconditional)

Return result as JSON using EXACTLY this format (no other keys, no nesting):
{{"subject": "...", "constraint": "...", "context": "...", "conditions": "..."}}

Make sure you adhere to the following rules to produce valid JSON objects:
- Do not return any additional information other than the JSON in it.
- Omit any backticks around the JSON - simply output the JSON on its own.
- The JSON object must not be wrapped into a list - it is its own JSON object.
- Property names must be enclosed in double quotes.

Clause citation: {citation_id}

Clause text:
{text}
""".strip()


async def _extract_cu_tuple(
    cu: dict[str, Any],
    gateway: IModelGateway,
    settings: Settings,
) -> CUTuple:
    """
    Extract one obligation CU's 4-tuple via `gateway` (Claude CLI,
    `settings.cu_extraction_model`). Mirrors
    `gleaning_extractor._parse_graph_response`'s try/except/degrade shape:
    ANY gateway error, invalid JSON, or Pydantic validation failure degrades
    to an empty `CUTuple()` and logs -- NEVER raises (T-09-08/T-11-08 --
    one bad unit never aborts the ~876-CU batch).
    """
    # Local import: `neo4j_graphrag`'s JSON-repair helper -- reused, not
    # hand-rolled (Don't-Hand-Roll discipline), matching
    # `gleaning_extractor.py`'s import shape.
    from neo4j_graphrag.experimental.components.entity_relation_extractor import (
        fix_invalid_json,
    )
    from neo4j_graphrag.experimental.pipeline.exceptions import InvalidJSONError

    cu_ref = f"{cu.get('source_doc')}::{cu.get('cu_id')}"
    try:
        response = await gateway.generate_response(
            prompt=CU_TUPLE_EXTRACTION_PROMPT.format(
                citation_id=cu.get("citation_id") or "",
                text=cu.get("text") or "",
            ),
            model_name=settings.cu_extraction_model,
            temperature=0.0,
            max_tokens=512,
        )
    except Exception as e:
        logger.warning(
            f"4-tuple extraction gateway call failed for {cu_ref}: {e}; "
            f"degrading to an empty tuple"
        )
        return CUTuple()

    try:
        repaired_json = fix_invalid_json(response.content)
        result = json.loads(repaired_json)
    except (json.JSONDecodeError, InvalidJSONError) as e:
        logger.error(f"4-tuple extraction for {cu_ref} returned invalid JSON: {e}")
        logger.debug(f"Invalid JSON for {cu_ref}: {response.content!r}")
        return CUTuple()

    try:
        return CUTuple.model_validate(result)
    except ValidationError as e:
        logger.error(f"4-tuple extraction for {cu_ref} has improper format: {e}")
        logger.debug(f"Invalid tuple shape for {cu_ref}: {result!r}")
        return CUTuple()


# Static, parameterized Cypher (T-09-12) -- every variable input is bound via
# session.run(..., **params), never string-interpolated.
_FETCH_OBLIGATION_CUS_QUERY = """
MATCH (cu:ComplianceUnit)-[:FROM_CLAUSE]->(c:Clause)
WHERE cu.cu_type IN $obligation_types
RETURN cu.cu_id AS cu_id, cu.source_doc AS source_doc, cu.cu_type AS cu_type,
       c.citation_id AS citation_id, c.text AS text
""".strip()

# Resume support (T-11-08 mitigation, extended): a multi-hour sequential
# Opus-CLI batch (~876 obligation CUs) must survive a crash/timeout partway
# through without re-paying for already-extracted CUs. `subject IS NULL` is
# the "not yet processed" marker -- `extract()` writes all four tuple
# fields together (never a partial write), so `subject IS NULL` reliably
# means "this CU has no tuple yet".
_FETCH_UNEXTRACTED_OBLIGATION_CUS_QUERY = """
MATCH (cu:ComplianceUnit)-[:FROM_CLAUSE]->(c:Clause)
WHERE cu.cu_type IN $obligation_types AND cu.subject IS NULL
RETURN cu.cu_id AS cu_id, cu.source_doc AS source_doc, cu.cu_type AS cu_type,
       c.citation_id AS citation_id, c.text AS text
""".strip()

_WRITE_TUPLES_QUERY = """
UNWIND $tuples AS t
MATCH (cu:ComplianceUnit {cu_id: t.cu_id, source_doc: t.source_doc})
SET cu.subject = t.subject, cu.constraint = t.constraint,
    cu.context = t.context, cu.conditions = t.conditions
""".strip()

_COUNT_OBLIGATION_CU_MISSING_TUPLE_QUERY = """
MATCH (cu:ComplianceUnit)
WHERE cu.cu_type IN $obligation_types
  AND (cu.subject IS NULL OR cu.constraint IS NULL
       OR cu.context IS NULL OR cu.conditions IS NULL)
RETURN count(cu) AS c
""".strip()

_COUNT_PREMISE_WITH_TUPLE_QUERY = """
MATCH (cu:ComplianceUnit {cu_type: 'premise'})
WHERE cu.subject IS NOT NULL OR cu.constraint IS NOT NULL
   OR cu.context IS NOT NULL OR cu.conditions IS NOT NULL
RETURN count(cu) AS c
""".strip()


@dataclass
class ExtractionStats:
    """
    Aggregate statistics for a Stage-2 4-tuple extraction run (T-09-08:
    reported, never swallowed). `obligation_cu_missing_tuple_count` and
    `premise_with_tuple_count` are authoritative post-write re-queries from
    Neo4j -- the acceptance-gate assertions (D-04/D-07: 0 and 0
    respectively).
    """

    cus_considered: int = 0
    cus_extracted: int = 0
    cus_degraded_empty: int = 0
    obligation_cu_missing_tuple_count: int = 0
    premise_with_tuple_count: int = 0


class CUExtractor:
    """
    Stage 2: formalize every obligation `:ComplianceUnit` (meta-CU/actor-CU)
    into its 4-tuple. Premises are never fetched by this class's query --
    they are structurally excluded, not filtered post-hoc.

    PRECONDITION: Stage 1 (`cu_classifier.CUClassifier`) must already have
    minted the `:ComplianceUnit` nodes this class reads.
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
            # Lazy import — mirrors `cu_classifier.CUClassifier`'s default
            # construction, avoiding a hard ILogger/ClaudeCliGateway
            # dependency for callers that always inject a gateway.
            from infrastructure.adapters.logging.console_logger import ConsoleLogger
            from infrastructure.adapters.models.claude_cli_gateway import ClaudeCliGateway

            self.gateway = ClaudeCliGateway(
                logger=ConsoleLogger(log_level=settings.log_level),
                timeout=settings.claude_cli_timeout,
            )

    def _fetch_obligation_cus(self, resume: bool = True) -> list[dict[str, Any]]:
        query = (
            _FETCH_UNEXTRACTED_OBLIGATION_CUS_QUERY if resume else _FETCH_OBLIGATION_CUS_QUERY
        )
        with self.driver.session(database=self.settings.neo4j_database) as session:
            result = session.run(query, obligation_types=list(OBLIGATION_CU_TYPES))
            return [dict(record) for record in result]

    def _write_tuple_batch(self, batch: list[dict[str, Any]]) -> None:
        if not batch:
            return
        with self.driver.session(database=self.settings.neo4j_database) as session:
            session.run(_WRITE_TUPLES_QUERY, tuples=batch)

    async def extract(self, resume: bool = True, batch_size: int = 20) -> ExtractionStats:
        """
        Extract + write the 4-tuple for every obligation CU.

        Writes incrementally every `batch_size` CUs (never one giant
        end-of-run write) -- this is a multi-hour, sequential, real-Opus-CLI
        batch (~876 obligation CUs, T-11-08); incremental persistence means
        a crash/timeout partway through loses at most one batch's worth of
        work, not the whole run. `resume=True` (default) skips CUs that
        already carry a tuple (`subject IS NOT NULL`) so a re-invocation
        after a crash never re-pays for already-extracted CUs; pass
        `resume=False` to force re-extraction of every obligation CU.
        """
        cus = self._fetch_obligation_cus(resume=resume)
        stats = ExtractionStats(cus_considered=len(cus))

        batch: list[dict[str, Any]] = []
        for i, cu in enumerate(cus, start=1):
            tup = await _extract_cu_tuple(cu, self.gateway, self.settings)
            if tup.is_empty():
                stats.cus_degraded_empty += 1
            else:
                stats.cus_extracted += 1
            batch.append(
                {
                    "cu_id": cu["cu_id"],
                    "source_doc": cu["source_doc"],
                    **tup.model_dump(),
                }
            )
            if len(batch) >= batch_size:
                self._write_tuple_batch(batch)
                logger.info(f"4-tuple extraction progress: {i}/{len(cus)} obligation CUs")
                batch = []

        self._write_tuple_batch(batch)

        self._accumulate_stats(stats)
        return stats

    def _accumulate_stats(self, stats: ExtractionStats) -> None:
        """Query Neo4j directly for authoritative post-write counts (T-09-08)."""
        try:
            with self.driver.session(database=self.settings.neo4j_database) as session:
                stats.obligation_cu_missing_tuple_count = session.run(
                    _COUNT_OBLIGATION_CU_MISSING_TUPLE_QUERY,
                    obligation_types=list(OBLIGATION_CU_TYPES),
                ).single()["c"]
                stats.premise_with_tuple_count = session.run(
                    _COUNT_PREMISE_WITH_TUPLE_QUERY
                ).single()["c"]
        except Exception as e:
            logger.warning(f"Could not query 4-tuple extraction stats after extract: {e}")


__all__: list[str] = [
    "CUExtractor",
    "ExtractionStats",
    "CUTuple",
    "CU_TUPLE_EXTRACTION_PROMPT",
]
