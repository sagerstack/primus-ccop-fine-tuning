"""
Policy Graph Stage 2 -- 4-Tuple Extraction on Obligation CUs (Phase 11,
11-04b / D-34/D-36/D-37).

REWRITE of the 11-04 extractor. Formalizes every obligation `:ComplianceUnit`
(`cu_type` in `OBLIGATION_CU_TYPES` = {meta-CU, actor-CU}) into the
GraphCompliance 4-tuple ⟨subject, constraint, context, conditions⟩ via
schema-constrained LLM extraction. Three fixes over 11-04:

- RETRY-ON-EMPTY (D-36): the 11-04 build silently persisted a fully-empty
  tuple for 325/764 obligation CUs whose source text was real, and a NULL-only
  gate reported "764/764 complete". Here, if extraction returns an all-empty
  tuple for a CU with non-trivial text, it RETRIES once with a repair prompt;
  the acceptance gate counts EMPTY-STRING tuples, not just NULL.
- SUBJECT INHERITANCE (D-34): a lettered sub-clause (e.g. 5.7.2(a)) whose
  actor lives only in the parent stem ("The CIIO shall:") gets the parent
  clause text injected into its extraction prompt, so the LLM resolves the
  inherited subject itself -- no more subjectless obligation fragments. (This
  is done at extraction time, not mint time: subjects do not exist until this
  pass, so there is nothing to "stamp" in Stage 1.)
- NORMALIZED SUBJECT + STRUCTURED CONDITIONS (D-37): the prompt asks for the
  subject in its shortest role form (paper aligns anchors to subject roles),
  and allows `conditions` to be a structured any/all object, serialized as
  JSON-in-string.

Premises are EXCLUDED from this pass (they are definitional carriers, never
judged). Degrade-safe (T-11-08): any gateway/JSON/validation failure degrades
to an empty `CUTuple`, logs, never raises. The CU's source clause `text` is
NEVER written by this module (D-13: tuple = reasoning representation, text =
citation payload).

Cypher discipline (T-09-12): every query is a static, module-level string
parameterized via `$obligation_types`/`$tuples`.
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
from rag.graph.ontology.clause_seeder import _ITEM_SUFFIX_RE
from rag.graph.ontology.cu_classifier import (
    OBLIGATION_CU_TYPES,
    GatewayUnavailableError,
    _default_cu_gateway,
)

logger = logging.getLogger(__name__)

_TUPLE_FIELDS = ("subject", "constraint", "context", "conditions")

# A CU whose source text is shorter than this is treated as genuinely
# trivial/non-obligation -- an empty tuple for it is NOT retried (D-36).
_NONTRIVIAL_TEXT_MIN_CHARS = 40


class CUTuple(BaseModel):
    """
    GraphCompliance's obligation 4-tuple. All four fields default to an
    explicit empty string -- `null` is never a valid persisted value. The
    `mode="before"` validator coerces `null`/missing to `""` AND serializes a
    structured value (dict/list -- e.g. the paper's `{"any": [...]}` condition
    disjunction, D-37) to a JSON string, since Neo4j properties are scalar.
    """

    subject: str = ""
    constraint: str = ""
    context: str = ""
    conditions: str = ""

    @field_validator("subject", "constraint", "context", "conditions", mode="before")
    @classmethod
    def _coerce_to_str(cls, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return value

    def is_empty(self) -> bool:
        """True iff every field is the empty string (the degrade-path shape)."""
        return not any(getattr(self, f) for f in _TUPLE_FIELDS)


CU_TUPLE_EXTRACTION_PROMPT = """You are formalizing ONE regulatory Compliance Unit (an obligation) into its canonical GraphCompliance 4-tuple for structured compliance reasoning.

IMPORTANT: This is a REGULATORY text. Do NOT invent facts, actors, or requirements not explicitly stated. If a field cannot be determined, return "" for it -- never omit the key, never return null.

Formalize into EXACTLY these four fields:
- "subject": the role-bearing actor this obligation applies to, in its SHORTEST canonical role form (e.g. normalize "the owner of a Critical Information Infrastructure ('CIIO')" to "CIIO"; "the Commissioner"; "a vendor").
- "constraint": the COMPLETE, self-contained requirement -- what must / must not / may be done -- carrying the deontic verb (shall / must / may / shall not) AND the direct object of the action, so it reads as a whole sentence (e.g. "shall ensure only authorised accounts can connect to and query databases"; "shall segment the network architecture into different network segments"). NEVER leave the constraint grammatically incomplete by moving its object into "context". If the clause only introduces lettered sub-items (its own text is a stem such as "shall ensure that:"), summarise the parent directive at a high level and do NOT re-list every sub-item -- each sub-item is formalised as its own unit.
- "context": ONLY scope that is NOT already stated in the constraint -- the wider system, asset class, or domain the obligation sits within. Use "" when the constraint is already self-contained; never pull a word out of the constraint into "context".
- "conditions": qualifying conditions, exceptions, or triggers. If there are multiple alternative triggers, return an object like {{"any": ["...", "..."]}}; if all must hold, {{"all": ["..."]}}. Use "" if unconditional.
{parent_block}
Return ONLY JSON in exactly this shape (no other keys, no nesting beyond conditions, no backticks):
{{"subject": "...", "constraint": "...", "context": "...", "conditions": "..."}}

Clause citation: {citation_id}

Clause text:
{text}""".strip()

CU_TUPLE_REPAIR_PROMPT = """Extract the compliance 4-tuple from the regulatory clause below. The previous attempt returned nothing. This clause DOES impose a requirement -- read it carefully.

Return ONLY this JSON (fill every field you can; use an empty string only if truly absent):
{{"subject": "<the actor, shortest role form>", "constraint": "<what must/must not/may be done>", "context": "<object/system, or empty>", "conditions": "<triggers/exceptions, or empty>"}}
{parent_block}
Clause citation: {citation_id}

Clause text:
{text}""".strip()


def _parent_block(cu: dict[str, Any]) -> str:
    """
    Build the subject-inheritance prompt fragment (D-34): for a lettered
    sub-clause whose parent stem carries the actor, inject the parent text so
    the LLM can resolve the inherited subject. Empty for non-sub-clauses.
    """
    clause_id = cu.get("citation_id") or ""
    parent_text = cu.get("parent_text") or ""
    if not parent_text or not _ITEM_SUFFIX_RE.search(clause_id):
        return ""
    return (
        "\nThis clause is a lettered sub-item; its actor may live only in the "
        "parent stem below. If the sub-item omits the actor, inherit 'subject' "
        f"from this parent stem:\nParent stem: {parent_text}\n"
    )


def _build_prompt(template: str, cu: dict[str, Any]) -> str:
    return template.format(
        citation_id=cu.get("citation_id") or "",
        text=cu.get("text") or "",
        parent_block=_parent_block(cu),
    )


async def _call_and_parse(
    prompt: str, cu_ref: str, gateway: IModelGateway, settings: Settings
) -> CUTuple:
    """
    Single extraction call + parse/validate/degrade. Mirrors
    `gleaning_extractor._parse_graph_response`'s try/except/degrade shape:
    ANY gateway/JSON/validation failure degrades to an empty `CUTuple` and
    logs -- NEVER raises (T-11-08).
    """
    from neo4j_graphrag.experimental.components.entity_relation_extractor import (
        fix_invalid_json,
    )
    from neo4j_graphrag.experimental.pipeline.exceptions import InvalidJSONError

    try:
        response = await gateway.generate_response(
            prompt=prompt,
            model_name=settings.cu_extraction_model,
            temperature=0.0,
            max_tokens=512,
        )
    except Exception as e:
        # Infra failure (CLI dead / spend limit / timeout) -- do NOT write an
        # empty tuple (which resume would then skip forever). Signal the caller
        # to SKIP + retry on resume (11-04b harden).
        raise GatewayUnavailableError(
            f"4-tuple extraction gateway call failed for {cu_ref}: {e}"
        ) from e

    try:
        result = json.loads(fix_invalid_json(response.content))
    except (json.JSONDecodeError, InvalidJSONError) as e:
        logger.error(f"4-tuple extraction for {cu_ref} returned invalid JSON: {e}")
        return CUTuple()

    try:
        return CUTuple.model_validate(result)
    except ValidationError as e:
        logger.error(f"4-tuple extraction for {cu_ref} has improper format: {e}")
        return CUTuple()


# Static, parameterized Cypher (T-09-12).
_FETCH_OBLIGATION_CUS_QUERY = """
MATCH (cu:ComplianceUnit)-[:FROM_CLAUSE]->(c:Clause)
WHERE cu.cu_type IN $obligation_types
OPTIONAL MATCH (parent:Clause)-[:HAS_CHILD]->(c)
RETURN cu.cu_id AS cu_id, cu.source_doc AS source_doc, cu.cu_type AS cu_type,
       c.citation_id AS citation_id, c.text AS text, parent.text AS parent_text
""".strip()

_FETCH_UNEXTRACTED_OBLIGATION_CUS_QUERY = """
MATCH (cu:ComplianceUnit)-[:FROM_CLAUSE]->(c:Clause)
WHERE cu.cu_type IN $obligation_types AND cu.subject IS NULL
OPTIONAL MATCH (parent:Clause)-[:HAS_CHILD]->(c)
RETURN cu.cu_id AS cu_id, cu.source_doc AS source_doc, cu.cu_type AS cu_type,
       c.citation_id AS citation_id, c.text AS text, parent.text AS parent_text
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

# D-36: the empty-STRING-aware gate the 11-04 NULL-only check was missing.
_COUNT_OBLIGATION_CU_ALL_EMPTY_QUERY = """
MATCH (cu:ComplianceUnit)
WHERE cu.cu_type IN $obligation_types
  AND coalesce(cu.subject, '') = '' AND coalesce(cu.constraint, '') = ''
  AND coalesce(cu.context, '') = '' AND coalesce(cu.conditions, '') = ''
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
    Aggregate stats for a Stage-2 run (T-09-08: reported, never swallowed).
    `obligation_cu_all_empty_count` is the D-36 hard gate (empty-string-aware,
    target ~0); the count fields are authoritative post-write re-queries.
    """

    cus_considered: int = 0
    cus_extracted: int = 0
    cus_degraded_empty: int = 0
    cus_retried: int = 0
    cus_still_empty_after_retry: int = 0
    cus_skipped_gateway_error: int = 0
    aborted_incomplete: bool = False
    obligation_cu_missing_tuple_count: int = 0
    obligation_cu_all_empty_count: int = 0
    premise_with_tuple_count: int = 0


class CUExtractor:
    """
    Stage 2 (11-04b): formalize every obligation `:ComplianceUnit` into its
    4-tuple, with retry-on-empty + subject inheritance. Premises are never
    fetched (structurally excluded).

    PRECONDITION: Stage 1 (`CUClassifier`) must already have minted the CUs.
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
        self.gateway = gateway if gateway is not None else _default_cu_gateway(settings)

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

    async def _extract_one(self, cu: dict[str, Any], stats: ExtractionStats) -> CUTuple:
        """Extract one CU's tuple, retrying once on empty for non-trivial text (D-36)."""
        cu_ref = f"{cu.get('source_doc')}::{cu.get('cu_id')}"
        tup = await _call_and_parse(
            _build_prompt(CU_TUPLE_EXTRACTION_PROMPT, cu), cu_ref, self.gateway, self.settings
        )
        if tup.is_empty() and len((cu.get("text") or "").strip()) >= _NONTRIVIAL_TEXT_MIN_CHARS:
            stats.cus_retried += 1
            logger.info(f"Empty tuple for {cu_ref} with non-trivial text -- retrying (D-36)")
            tup = await _call_and_parse(
                _build_prompt(CU_TUPLE_REPAIR_PROMPT, cu), cu_ref, self.gateway, self.settings
            )
            if tup.is_empty():
                stats.cus_still_empty_after_retry += 1
                logger.warning(f"Still empty after retry for {cu_ref} (text present) -- flagged")
        return tup

    async def extract(
        self, resume: bool = True, batch_size: int = 20, max_consecutive_errors: int = 8
    ) -> ExtractionStats:
        """
        Extract + write the 4-tuple for every obligation CU. Writes
        incrementally every `batch_size` CUs (crash-safe); `resume=True` skips
        CUs that already carry a tuple (`subject IS NOT NULL`).

        Death-resilient (11-04b harden): a gateway/CLI failure SKIPS the CU
        (leaves `subject` NULL so the next resume pass retries it) rather than
        writing an empty tuple that resume would then skip forever. A genuinely
        empty extraction (valid response, no obligation found) IS written
        (flagged by the all-empty gate). After `max_consecutive_errors`
        consecutive gateway failures the pass aborts early and flags
        `aborted_incomplete`; re-invoke to resume.
        """
        cus = self._fetch_obligation_cus(resume=resume)
        stats = ExtractionStats(cus_considered=len(cus))

        batch: list[dict[str, Any]] = []
        consecutive_errors = 0
        for i, cu in enumerate(cus, start=1):
            try:
                tup = await self._extract_one(cu, stats)
            except GatewayUnavailableError as e:
                stats.cus_skipped_gateway_error += 1
                consecutive_errors += 1
                logger.warning(f"{e}; skipping (will retry on resume)")
                if consecutive_errors >= max_consecutive_errors:
                    stats.aborted_incomplete = True
                    self._write_tuple_batch(batch)
                    logger.error(
                        f"Gateway unavailable for {consecutive_errors} consecutive CUs "
                        f"-- aborting extract pass at {i}/{len(cus)}; resume later"
                    )
                    return self._finalize(stats)
                continue
            consecutive_errors = 0
            if tup.is_empty():
                stats.cus_degraded_empty += 1
            else:
                stats.cus_extracted += 1
            batch.append(
                {"cu_id": cu["cu_id"], "source_doc": cu["source_doc"], **tup.model_dump()}
            )
            if len(batch) >= batch_size:
                self._write_tuple_batch(batch)
                logger.info(f"4-tuple extraction progress: {i}/{len(cus)} obligation CUs")
                batch = []
        self._write_tuple_batch(batch)

        return self._finalize(stats)

    def _finalize(self, stats: ExtractionStats) -> ExtractionStats:
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
                stats.obligation_cu_all_empty_count = session.run(
                    _COUNT_OBLIGATION_CU_ALL_EMPTY_QUERY,
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
    "CU_TUPLE_REPAIR_PROMPT",
]
