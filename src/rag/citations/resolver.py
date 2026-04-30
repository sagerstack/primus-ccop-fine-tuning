"""
Citation Resolver — pure parser

Parses the model's `**Sources:**` markdown footer into structured Citation
records. Every declared citation is emitted; this module performs no
filtering, no inventory matching, and no hallucination detection.

The model is instructed (in the generation node's system prompt) to end
its response with a single block:

    **Sources:**
    CCoP 2.0: 5.3.1
    Cybersecurity Act 2018: Section 11(7)
    NIST CSF: PR.AC-1

Document attribution is the model's responsibility (it writes the document
name in each entry). The judge routes by claimed document name when
verifying — see `_build_citation_verification_block` in
`domain/services/llm_judge_service.py`.

History note: this module previously parsed three blocks (Sources /
Cross-references / Other Sources). The 3-block design was reverted because
it produced a "citations-only degenerate response" failure mode where the
model emitted the citation blocks but no answer prose. The single-block
instruction is less prescriptive about response structure and reduces the
prompt's verbosity. The `kind` field is preserved on Citation records for
backward compatibility with consumers but is always set to "primary".

The intent of `response.citations` is full audit fidelity: capture exactly
what the model declared. Downstream consumers that want a "grounded subset"
join against `retrieved_contexts_detailed` themselves.

The footer-marker regex is moderately permissive — it accepts `**Sources:**`,
`**Sources**`, and bare `Sources:` — to absorb minor styling variations
without forcing prompt gymnastics.
"""

import logging
import re
from typing import TypedDict

logger = logging.getLogger(__name__)


class Citation(TypedDict):
    """Citation metadata structure.

    `kind` is preserved for backward compat but is always "primary" since
    the resolver no longer distinguishes between Sources, Cross-references,
    and Other Sources blocks (the 3-block design was reverted).
    """

    document: str
    section: str
    clause: str
    citation_id: str
    document_type: str
    kind: str


# Match the **Sources:** footer marker line and capture every line after it
# to the end of the text. We anchor on the literal word "Sources" with
# optional bold wrappers and an optional colon.
_SOURCES_FOOTER_PATTERN = re.compile(
    r"(?:\*\*)?Sources:?(?:\*\*)?\s*\n([\s\S]*?)\Z",
    re.IGNORECASE,
)

KIND_PRIMARY = "primary"


def _parse_block_lines(block_inner: str) -> list[tuple[str, str]]:
    """Split block contents into (document_name, clause_reference) tuples.

    Lines without a colon, or with empty document/clause halves, are skipped.
    """
    pairs: list[tuple[str, str]] = []
    for raw_line in block_inner.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        doc_name, _, clause_ref = line.partition(":")
        doc_name = doc_name.strip()
        clause_ref = clause_ref.strip()
        if not doc_name or not clause_ref:
            continue
        pairs.append((doc_name, clause_ref))
    return pairs


def extract_citation_ids(generation: str) -> list[str]:
    """
    Extract `Document::Clause` citation IDs from the **Sources:** footer.

    Returns the list in order of appearance, deduplicated. The id format
    matches the citation_id metadata convention used elsewhere in the
    pipeline: `<document name>::<clause reference>`.

    Args:
        generation: LLM output text with a trailing **Sources:** footer.

    Returns:
        List of unique citation IDs in order of appearance. Empty if no
        footer is present.

    Examples:
        >>> extract_citation_ids("body...\\n**Sources:**\\nCCoP 2.0: 5.3.1")
        ['CCoP 2.0::5.3.1']

        >>> extract_citation_ids("No footer at all")
        []
    """
    if not generation:
        return []

    match = _SOURCES_FOOTER_PATTERN.search(generation)
    if not match:
        return []

    seen: set[str] = set()
    unique_ids: list[str] = []
    for doc_name, clause_ref in _parse_block_lines(match.group(1)):
        cid = f"{doc_name}::{clause_ref}"
        if cid in seen:
            continue
        seen.add(cid)
        unique_ids.append(cid)

    logger.debug(f"Extracted {len(unique_ids)} unique citations from Sources footer")
    return unique_ids


def parse_citations(generation: str) -> list[Citation]:
    """
    Parse the **Sources:** footer into Citation records.

    Pure parser: no inventory matching, no enrichment beyond what the model
    wrote. Every citation is tagged kind="primary" — the bucket distinction
    was removed after the 3-block design produced citations-only degenerate
    responses. Document attribution is the judge's responsibility (via
    document-name routing on the parsed `document` field).

    Args:
        generation: LLM output text with the **Sources:** footer.

    Returns:
        List of Citation dicts, one per unique declared citation, in
        order of appearance.
    """
    if not generation:
        return []

    match = _SOURCES_FOOTER_PATTERN.search(generation)
    if not match:
        return []

    seen: set[str] = set()
    citations: list[Citation] = []
    for doc_name, clause_ref in _parse_block_lines(match.group(1)):
        cid = f"{doc_name}::{clause_ref}"
        if cid in seen:
            continue
        seen.add(cid)
        citations.append({
            "document": doc_name,
            "section": "",
            "clause": clause_ref,
            "citation_id": cid,
            "document_type": "",
            "kind": KIND_PRIMARY,
        })

    logger.debug(f"Parsed {len(citations)} citations from Sources footer")
    return citations


def resolve_citations(citation_ids: list[str], documents: list) -> list[Citation]:
    """
    Build Citation records from declared IDs, optionally enriched with
    metadata from the retrieved-document set.

    This is the legacy entrypoint used when callers have a flat list of IDs
    rather than the structured block output. Prefer `parse_citations` when
    you have access to the full generation text.

    Citations matching a retrieved chunk are enriched (section, document_type
    pulled from chunk metadata). Unmatched citations get parsed
    document/clause from the citation_id string.

    Args:
        citation_ids: List of citation IDs (format: "<document>::<clause>")
        documents: LangChain Document objects with metadata, typically the
            retrieval pipeline's filtered_documents list.

    Returns:
        List of Citation dicts, one per unique declared citation.
    """
    if not citation_ids:
        return []

    citation_map = {}
    for doc in documents:
        cid = doc.metadata.get("citation_id", "")
        if cid:
            citation_map[cid] = doc

    resolved: list[Citation] = []
    seen_ids: set[str] = set()
    matched = 0

    for citation_id in citation_ids:
        if citation_id in seen_ids:
            continue
        seen_ids.add(citation_id)

        doc = citation_map.get(citation_id)
        if doc is not None:
            metadata = doc.metadata
            citation: Citation = {
                "document": metadata.get("document_source", "Unknown Document"),
                "section": metadata.get("section", ""),
                "clause": metadata.get("clause", ""),
                "citation_id": citation_id,
                "document_type": metadata.get("document_type", "standard"),
                "kind": KIND_PRIMARY,
            }
            matched += 1
        else:
            doc_name, _, clause_ref = citation_id.partition("::")
            citation = {
                "document": doc_name or "Unknown Document",
                "section": "",
                "clause": clause_ref,
                "citation_id": citation_id,
                "document_type": "",
                "kind": KIND_PRIMARY,
            }
        resolved.append(citation)

    logger.debug(
        f"Resolved {len(resolved)} declared citations "
        f"({matched} matched in retrieved set, "
        f"{len(resolved) - matched} not in retrieved set)"
    )
    return resolved


def build_citations_from_state(state: dict) -> list[Citation]:
    """
    Build Citation records from graph state.

    Reads the model's **Sources:** footer from state["generation"] and
    returns Citation records. Does NOT perform inventory matching — pure
    parse output.

    Args:
        state: LangGraph state with 'generation'

    Returns:
        List of Citation dicts.
    """
    generation = state.get("generation", "")
    return parse_citations(generation)
