"""
Policy Graph Stage 3 -- REFERS_TO Linker (Phase 11, 11-05 / D-05).

Creates `(:ComplianceUnit)-[:REFERS_TO]->(:ComplianceUnit)` edges -- the
cross-reference structure the Compliance Gate (11-08) traverses for
reference-closure / exception handling. Two-pronged per GraphCompliance §3.1:

- EXPLICIT references ("Clause 5.7.2", "sub-clause 3.2.1(a)") -- deterministic,
  boundary-aware detection over each CU's source clause text, matched against
  the OTHER clause ids in the SAME source document.
- IMPLICIT / relative references ("paragraph 1", "the preceding sub-clause") --
  a settings-gated small-LLM call (mirrors `function_type_routing`'s
  degrade-to-default-never-raise shape) that returns candidate target clause
  ids, id-validated against the known clause set. Degrades to no edges on any
  failure -- never raises, never fabricates a target.

Over-linking guard (Finding 3): the reused `KGInspector._clause_id_appears`
boundary matcher does NOT stop "5.3" matching inside "5.3.10" (a `.` passes its
`(?![A-Za-z0-9])` trailing lookahead). `_reference_appears` STRENGTHENS it --
rejecting a match immediately followed by a dotted continuation (a further
".<digit>") or a lettered sub-item ("(a)") -- so a bare "5.3" never links to
"5.3.10" / "5.3.1(a)".

Cypher discipline (T-09-12): the MERGE below is a static, module-level string
parameterized via `$pairs` -- no value is ever spliced into query text.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

import neo4j

from application.ports.output.i_model_gateway import IModelGateway
from infrastructure.config.settings import Settings
from rag.graph.ontology.cu_classifier import OBLIGATION_CU_TYPES

logger = logging.getLogger(__name__)


def _reference_appears(clause_id: str, haystack_lower: str) -> bool:
    """
    Boundary-aware reference match, STRENGTHENED past
    `KGInspector._clause_id_appears` to also reject a dotted continuation or a
    lettered sub-item immediately after the id (Finding 3): a bare "5.3" must
    NOT match inside "5.3.10" or "5.3.1(a)".
    """
    cid = clause_id.lower()
    pattern = re.compile(
        r"(?<![A-Za-z0-9.])" + re.escape(cid) + r"(?![A-Za-z0-9]|\.\d|\([a-z]+\))"
    )
    return bool(pattern.search(haystack_lower))


_IMPLICIT_REF_PROMPT = """This regulatory clause (id {clause_id}) contains RELATIVE references (e.g. "the preceding sub-clause", "paragraph (a)"). Resolve them to the ABSOLUTE clause id(s) they point to.

Clause text:
{text}

Return ONLY the absolute clause id(s), comma-separated (e.g. "5.7.2, 3.2.1(a)"). If none can be resolved, return "NONE". No other text."""

# Clause-id-shaped token (dotted number with optional lettered sub-item).
_REF_TOKEN_RE = re.compile(r"[0-9]+(?:\.[0-9]+)*(?:\([a-z]+\))?")


def _split_ref_tokens(raw: str) -> list[str]:
    """Extract clause-id-shaped tokens from a (possibly noisy) LLM response."""
    if not raw or "none" in raw.strip().lower()[:6]:
        return []
    return _REF_TOKEN_RE.findall(raw)


# Static, parameterized Cypher (T-09-12) -- $pairs is the only variable input.
_LINK_REFERS_TO_QUERY = """
UNWIND $pairs AS pair
MATCH (src:ComplianceUnit {cu_id: pair.src_cu_id, source_doc: pair.source_doc})
MATCH (tgt:ComplianceUnit {cu_id: pair.tgt_cu_id, source_doc: pair.source_doc})
MERGE (src)-[:REFERS_TO]->(tgt)
""".strip()

_FETCH_CUS_QUERY = """
MATCH (cu:ComplianceUnit)-[:FROM_CLAUSE]->(c:Clause)
RETURN cu.cu_id AS cu_id, cu.source_doc AS source_doc, cu.cu_type AS cu_type,
       c.clause_id AS clause_id, c.text AS text
""".strip()

_COUNT_REFERS_TO_QUERY = "MATCH (:ComplianceUnit)-[r:REFERS_TO]->(:ComplianceUnit) RETURN count(r) AS c"


@dataclass
class LinkStats:
    """Aggregate stats for a REFERS_TO link run (T-09-08: reported, never swallowed)."""

    cus_scanned: int = 0
    explicit_pairs: int = 0
    implicit_pairs: int = 0
    refers_to_edges_total: int = 0


class RefersToLinker:
    """
    Stage 3: create `REFERS_TO` edges between CUs (explicit regex + implicit
    small-LLM). Reads `:ComplianceUnit` + its `FROM_CLAUSE` source clause text;
    writes only `REFERS_TO` edges (never mutates CU properties or clauses).
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
        self.gateway = gateway  # optional -- only needed for the implicit half

    def _fetch_cus(self) -> list[dict[str, Any]]:
        with self.driver.session(database=self.settings.neo4j_database) as session:
            return [
                {
                    "cu_id": r["cu_id"],
                    "source_doc": r["source_doc"],
                    "cu_type": r["cu_type"],
                    "clause_id": r["clause_id"],
                    "text": r["text"] or "",
                }
                for r in session.run(_FETCH_CUS_QUERY)
            ]

    @staticmethod
    def _compute_explicit_pairs(cus: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Deterministic WITHIN-DOCUMENT explicit-reference pairs: a source CU's
        text references another clause's id (boundary-aware, over-linking-
        guarded). Links the source CU to every CU minted from the referenced
        clause. Self-references (same clause) are skipped.
        """
        # (source_doc, clause_id) -> list of cu_ids minted from that clause
        clause_to_cus: dict[tuple[str, str], list[str]] = {}
        for cu in cus:
            clause_to_cus.setdefault((cu["source_doc"], cu["clause_id"]), []).append(cu["cu_id"])

        pairs: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for src in cus:
            # Only OBLIGATION CUs are reference-closure sources (11-08 traverses
            # REFERS_TO from judged CUs); edges emanating from premises (e.g. the
            # RtF interpretive block) are noise, not exception structure.
            if src.get("cu_type") not in OBLIGATION_CU_TYPES:
                continue
            haystack = src["text"].lower()
            if not haystack:
                continue
            for (doc, clause_id), tgt_cu_ids in clause_to_cus.items():
                if doc != src["source_doc"] or clause_id == src["clause_id"]:
                    continue
                if not _reference_appears(clause_id, haystack):
                    continue
                for tgt_cu_id in tgt_cu_ids:
                    key = (src["cu_id"], tgt_cu_id, doc)
                    if key in seen:
                        continue
                    seen.add(key)
                    pairs.append(
                        {"src_cu_id": src["cu_id"], "tgt_cu_id": tgt_cu_id, "source_doc": doc}
                    )
        return pairs

    # Relative-reference markers that an explicit boundary match cannot resolve
    # (they name no absolute clause id) -- these route to the small-LLM half.
    _RELATIVE_REF_RE = re.compile(
        r"\b(?:the (?:preceding|following|above|said) (?:clause|sub-?clause|paragraph|section)"
        r"|paragraph\s+\(?[a-z0-9]+\)?|sub-?clause\s+\(?[a-z0-9]+\)?)\b",
        re.IGNORECASE,
    )

    async def _compute_implicit_pairs(
        self, cus: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Settings-gated small-LLM resolution of RELATIVE references ("the
        preceding sub-clause") into target clause ids, id-validated against the
        known clause set. Degrades to NO edges on any gateway/parse failure --
        never raises, never fabricates a target (mirrors
        `function_type_routing`'s degrade-to-default-never-raise shape).
        """
        if self.gateway is None:
            return []
        valid_clause_ids = {(cu["source_doc"], cu["clause_id"]) for cu in cus}
        clause_to_cus: dict[tuple[str, str], list[str]] = {}
        for cu in cus:
            clause_to_cus.setdefault((cu["source_doc"], cu["clause_id"]), []).append(cu["cu_id"])

        pairs: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for src in cus:
            if not self._RELATIVE_REF_RE.search(src["text"] or ""):
                continue
            try:
                response = await self.gateway.generate_response(
                    prompt=_IMPLICIT_REF_PROMPT.format(
                        clause_id=src["clause_id"], text=src["text"] or ""
                    ),
                    model_name=self.settings.cu_extraction_model,
                    temperature=0.0,
                    max_tokens=100,
                )
            except Exception as e:
                logger.warning(f"Implicit-ref LLM call failed for {src['cu_id']}: {e}; no edges")
                continue
            for token in _split_ref_tokens(response.content):
                key = (src["source_doc"], token)
                if key not in valid_clause_ids or token == src["clause_id"]:
                    continue  # id-validate; never fabricate a target
                for tgt_cu_id in clause_to_cus[key]:
                    pair_key = (src["cu_id"], tgt_cu_id)
                    if pair_key in seen:
                        continue
                    seen.add(pair_key)
                    pairs.append(
                        {"src_cu_id": src["cu_id"], "tgt_cu_id": tgt_cu_id, "source_doc": src["source_doc"]}
                    )
        return pairs

    def _write_pairs(self, pairs: list[dict[str, Any]]) -> None:
        if not pairs:
            return
        with self.driver.session(database=self.settings.neo4j_database) as session:
            session.run(_LINK_REFERS_TO_QUERY, pairs=pairs)

    async def link(self, resolve_implicit: bool = False) -> LinkStats:
        """
        Create REFERS_TO edges: EXPLICIT (deterministic) always; IMPLICIT
        (small-LLM) when `resolve_implicit` and a gateway is injected (degrade-
        safe). Reports the authoritative post-write edge count (T-09-08).
        """
        cus = self._fetch_cus()
        stats = LinkStats(cus_scanned=len(cus))

        explicit = self._compute_explicit_pairs(cus)
        stats.explicit_pairs = len(explicit)
        self._write_pairs(explicit)

        if resolve_implicit and self.gateway is not None:
            implicit = await self._compute_implicit_pairs(cus)
            stats.implicit_pairs = len(implicit)
            self._write_pairs(implicit)

        self._accumulate_stats(stats)
        return stats

    def _accumulate_stats(self, stats: LinkStats) -> None:
        """Query Neo4j directly for the authoritative post-link edge count (T-09-08)."""
        try:
            with self.driver.session(database=self.settings.neo4j_database) as session:
                stats.refers_to_edges_total = session.run(
                    _COUNT_REFERS_TO_QUERY
                ).single()["c"]
        except Exception as e:
            logger.warning(f"Could not query REFERS_TO stats after linking: {e}")


__all__: list[str] = ["RefersToLinker", "LinkStats", "_reference_appears"]
