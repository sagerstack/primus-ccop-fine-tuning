"""
Compliance Gate — context assembly for primus (--mode graphcpl, option (a)).

Instead of a standalone judgment LLM, the Gate assembles the graph content into
`state["filtered_documents"]` (the format the `generate` node feeds primus), so
graphcpl measures **primus + GraphCompliance retrieval** — comparable to hybrid.

Context documents (all 4, all CUs — "try all first, reduce later"):
  1. SCENARIO ANALYSIS — ER/SAO triples + anchor→hypernym classifications
  2. DEFINITIONS/PREMISES — the STRONG-supporting premises (11-06b)
  3. OBLIGATIONS — the CU Plan (subject|modality|constraint header + verbatim clause text)
  4. REFERENCES — REFERS_TO neighbours of the CU-Plan CUs

Mode-gated on `graphcpl`; degrade-safe. Downstream `generate` (primus) does the reasoning.
"""
import logging
import os
from typing import Any, Dict, List

from langchain_core.documents import Document

from infrastructure.config.settings import get_settings
from rag.retrieval.state.graph_state import GraphState

logger = logging.getLogger(__name__)

_MODE = "graphcpl"

# Experiment gate (2026-07-07): when set to "minimal", send ONLY Scenario
# Analysis (triples + STRONG/WEAK classifications) + Definitions/premises —
# drop the Obligations (CU Plan) and Referenced-obligation blocks that flood
# the 4096 window. Default ("") = current full behavior.
_CONTEXT_MODE = os.environ.get("CCOP_GRAPHCPL_CONTEXT", "").strip().lower()

_FETCH_REFS_QUERY = """
UNWIND $cu_ids AS cid
MATCH (s:ComplianceUnit {cu_id: cid})-[:REFERS_TO]->(t:ComplianceUnit)-[:FROM_CLAUSE]->(c:Clause)
RETURN DISTINCT c.citation_id AS citation_id, t.subject AS subject,
       t.constraint AS constraint, c.text AS clause_text
""".strip()


def _fetch_references(settings, cu_ids: List[str]) -> List[Dict[str, Any]]:
    if not cu_ids:
        return []
    import neo4j
    drv = neo4j.GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
    try:
        with drv.session(database=settings.neo4j_database) as s:
            return [dict(r) for r in s.run(_FETCH_REFS_QUERY, cu_ids=cu_ids)]
    finally:
        drv.close()


def _doc(text: str, citation_id: str, section: str) -> Document:
    return Document(
        page_content=text,
        metadata={
            "citation_id": citation_id,
            "document_source": "GraphCompliance",
            "section": section,
            "similarity_score": 1.0,
        },
    )


def compliance_context_assembly(state: GraphState) -> GraphState:
    """Pack triples + hypernyms + premises + obligations + references into filtered_documents."""
    if state.get("mode") != _MODE:
        return state

    settings = get_settings()
    cu_plan = state.get("cu_plan", [])
    hm = state.get("hypernym_mappings", [])
    docs: List[Document] = []

    # 1. Scenario analysis (triples + anchor→hypernym classifications)
    triples = "\n".join(
        f"- ({t.get('subject','')}) --[{t.get('predicate','')}]--> ({t.get('object','')})"
        for t in state.get("context_graph_triples", [])
    )
    classes = "\n".join(
        f"- {a['label']} [{a['type']}] -> "
        + ", ".join(f"{m['label']}({m['strong_weak']})" for m in hm if m.get("anchor") == a["label"])
        for a in state.get("anchors", [])
    )
    if triples or classes:
        docs.append(_doc(
            f"Entity-relation triples:\n{triples}\n\nExtracted entity classifications:\n{classes}",
            "context-graph", "Scenario Analysis"))

    # 2. Definitions / premises (STRONG support)
    seen = set()
    for m in hm:
        prem = (m.get("supporting_premise") or "").strip()
        if prem and prem not in seen and m.get("strong_weak") == "STRONG":
            seen.add(prem)
            docs.append(_doc(prem, f"def:{m.get('label','')}", f"Definition ({m.get('label','')})"))

    if _CONTEXT_MODE == "minimal":
        # Experiment: scenario + definitions only — skip obligations + references.
        logger.info("Compliance-Gate context: MINIMAL mode (scenario + definitions only)")
    else:
        # 3. Obligations (CU Plan — all CUs, 4-tuple header + verbatim clause text)
        for c in cu_plan:
            header = f"[{c.get('subject','')} | {c.get('modality','')}] {str(c.get('constraint',''))}".strip()
            body = c.get("clause_text", "") or ""
            docs.append(_doc(f"{header}\n\n{body}", c.get("citation_id", ""), f"Obligation ({c.get('cu_type','')})"))

        # 4. References (REFERS_TO neighbours)
        try:
            refs = _fetch_references(settings, [c["cu_id"] for c in cu_plan if c.get("cu_id")])
        except Exception as e:
            logger.warning(f"Reference fetch failed: {e}")
            refs = []
        for r in refs:
            docs.append(_doc(
                f"[{r.get('subject','')}] {str(r.get('constraint',''))}\n\n{r.get('clause_text','')}",
                r.get("citation_id", ""), "Referenced obligation"))

    state["filtered_documents"] = docs
    state["documents"] = docs
    state["is_rag_augmented"] = True
    state["retrieval_succeeded"] = bool(docs)
    logger.info(f"Compliance-Gate context assembled for primus: {len(docs)} document(s)")
    return state


__all__ = ["compliance_context_assembly"]
