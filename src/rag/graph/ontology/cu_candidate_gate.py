"""
Policy Graph CU Candidate Gate (Phase 11, 11-04b / D-32).

Pure, Neo4j-free, LLM-free ROUTING of seeded `:Clause` nodes into the CU
minting pipeline. Decides, per clause, whether it enters the semantic LLM
classifier or is force-routed to an interpretive premise -- BEFORE any Opus
call is made. This is the single place the doc-type policy lives:

- Structural headers (ToC / chapter-section skeleton, `is_structural_header`)
  are EXCLUDED entirely -- they stay pure `:HAS_CHILD` hierarchy, never a CU
  (unchanged from 11-04).
- Response-to-Feedback (`CCoP Response to Feedback`, doc_class=guidance) is a
  consultation Q&A companion, NOT the operative Code. It is force-routed to
  `premise` (kind=interpretation) -- never an obligation CU (D-32). This
  removes the ~235 spurious actor-CUs the 11-04 build minted from it (64% of
  which extracted to empty tuples; the rest duplicated existing CCoP CUs).
- Every other document (CCoP 2.0, Cybersecurity Act, and the four guidance
  guides -- SBD / Threat / Risk / Audit) is routed to `llm_classify`: the
  per-content LLM decides premise/meta-CU/actor-CU. Guidance guides are NOT
  wholesale-premised -- they contain role-addressed directives the classifier
  must judge on their own merits (user directive 2026-07-05).

Fail-loud (D-19): an unregistered `source_doc` raises via `source_doc_prefix`
rather than being silently swept into a default route.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rag.graph.ontology.clause_source_annotator import source_doc_prefix

# The consultation-response companion doc -- routed to interpretive premise,
# never an obligation CU (D-32). Matches the registered source_doc string in
# `clause_source_annotator._SOURCE_DOC_PREFIX`.
RESPONSE_TO_FEEDBACK_SOURCE_DOC = "CCoP Response to Feedback"

# Route labels (LOCKED 2-value set for 11-04b).
ROUTE_LLM_CLASSIFY = "llm_classify"
ROUTE_FORCE_PREMISE_INTERPRETATION = "force_premise_interpretation"


@dataclass
class Candidate:
    """
    One routed CU candidate. Carries the source-clause fields the downstream
    classifier/extractor need PLUS the routing decision and the soft hints
    (`function_type`, `doc_class`) -- hints, never deciders (D-30).
    """

    clause_id: str
    source_doc: str
    citation_id: str
    text: str
    route: str
    function_type: str = ""  # D-30 soft hint (may be wrong)
    doc_class: str = ""      # D-30 soft hint


def route_candidates(clauses: list[dict[str, Any]]) -> list[Candidate]:
    """
    Route each seeded clause dict into a `Candidate` (or drop it). Structural
    headers are dropped; RtF is forced to interpretive premise; everything
    else is routed to the LLM classifier. Raises on an unregistered
    `source_doc` (fail-loud, D-19).
    """
    candidates: list[Candidate] = []
    for clause in clauses:
        source_doc = clause["source_doc"]
        # Fail-loud on an unregistered doc BEFORE any routing decision.
        source_doc_prefix(source_doc)

        if clause.get("is_structural_header"):
            continue  # ToC / skeleton -- never a CU

        if not (clause.get("text") or "").strip():
            continue  # textless (unaligned/mis-aligned source) -- nothing to classify

        route = (
            ROUTE_FORCE_PREMISE_INTERPRETATION
            if source_doc == RESPONSE_TO_FEEDBACK_SOURCE_DOC
            else ROUTE_LLM_CLASSIFY
        )
        candidates.append(
            Candidate(
                clause_id=clause["clause_id"],
                source_doc=source_doc,
                citation_id=clause.get("citation_id") or "",
                text=clause.get("text") or "",
                route=route,
                function_type=clause.get("function_type") or "",
                doc_class=clause.get("doc_class") or "",
            )
        )
    return candidates


__all__: list[str] = [
    "Candidate",
    "route_candidates",
    "RESPONSE_TO_FEEDBACK_SOURCE_DOC",
    "ROUTE_LLM_CLASSIFY",
    "ROUTE_FORCE_PREMISE_INTERPRETATION",
]
