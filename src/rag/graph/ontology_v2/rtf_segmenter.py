"""RtF-specific segmenter (ontology_v2).

The Response-to-Feedback doc is a Q&A/clarification document numbered at the
`N.N` sub-clause level (2.1, 2.2 … 11.28 … 15.40), rendered by Docling as
`- N.N. …` markdown list items grouped under `## N  SECTION` headers, `## TOPIC`
subsections, and `## Feedback` / `## CSA's Response` role labels. The shared
clause-aware chunker (tuned for CCoP heading numbering) fuses whole sections
into single blobs, so RtF gets its own segmenter here.

Each `N.N` item becomes one chunk carrying its section/subsection/role context.
The shared ingestion chunker is left untouched (the live RAG still uses it).
"""
import re
from typing import Any, Dict, List

_SECTION = re.compile(r"^#{1,3}\s+(\d{1,2})\s+([A-Z][A-Z0-9 /&,'()-]+?)\s*$")
_ROLE = re.compile(r"^#{1,3}\s+(Feedback|CSA's Response)\s*$")
_SUBSEC = re.compile(r"^#{1,3}\s+([A-Z][A-Z0-9 /&,'()-]+?)\s*$")
_ITEM = re.compile(r"^\s*-?\s*(\d{1,2}\.\d{1,2})\.\s+(.*)$")


def segment_rtf(markdown: str, doc_name: str) -> List[Dict[str, Any]]:
    section = subsection = role = ""
    items: List[Dict[str, Any]] = []
    cur: Dict[str, Any] | None = None

    def flush():
        nonlocal cur
        if cur is not None:
            cur["text"] = cur["text"].strip()
            items.append(cur)
            cur = None

    for ln in markdown.splitlines():
        m_item = _ITEM.match(ln)
        if m_item:
            flush()
            clause = m_item.group(1)
            cur = {
                "citation_id": f"{doc_name}::{clause}",
                "clause": clause,
                "section": section,
                "subsection": subsection,
                "role": role,
                "text": f"{clause}. {m_item.group(2)}".strip(),
            }
            continue
        m_sec = _SECTION.match(ln)
        if m_sec:
            flush()
            section = f"{m_sec.group(1)} {m_sec.group(2).strip()}"
            subsection = role = ""
            continue
        m_role = _ROLE.match(ln)
        if m_role:
            flush()
            role = m_role.group(1)
            continue
        m_sub = _SUBSEC.match(ln)
        if m_sub:
            flush()
            subsection = m_sub.group(1).strip()
            role = ""
            continue
        # continuation line (sub-items "- (a)", prose, blanks) -> current item
        if cur is not None:
            cur["text"] += "\n" + ln
    flush()
    return items
