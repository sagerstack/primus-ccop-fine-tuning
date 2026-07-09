"""Heading-based segmenter for the supplementary guides (ontology_v2).

Docs 3/4/5/7 (Auditing Guidelines, Threat Modelling, Risk Assessment, Cybersecurity
Act) are cleanly heading-structured (`## N TITLE`, `## N.N TITLE`) but the shared
section chunker's token-merge FUSES small sections and swallows the TOC + intro
sections into one blob. This splits on numbered markdown headings instead — one
chunk per section/subsection, no merge, nothing dropped.

Rules:
  - A chunk starts at a NUMBERED heading `#{1,4} N(.N)* TITLE`; content runs to the
    next numbered heading. Non-numbered `## TITLE` headings (e.g. Docling's mis-parsed
    `## a.` list markers) stay as content of the current section.
  - The `## CONTENTS` / table-of-contents section (dot-leaders) is dropped.
  - A glossary section (title contains DEFINITIONS/GLOSSARY/TERMS) is tagged
    is_glossary=True so downstream cleaning can route it to a definitions file.
"""
import re
from typing import Any, Dict, List

_HEADING = re.compile(r"^#{1,4}\s+(.+?)\s*$")
_NUMBERED = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+)$")
_DOT_LEADER = re.compile(r"\.{6,}")
_GLOSSARY = re.compile(r"\b(DEFINITIONS|GLOSSARY|TERMS AND DEFINITIONS)\b", re.I)


def segment_by_headings(markdown: str, doc_name: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    cur: Dict[str, Any] | None = None

    def flush():
        nonlocal cur
        if cur is not None:
            cur["text"] = cur["text"].strip()
            items.append(cur)
            cur = None

    for ln in markdown.splitlines():
        m_h = _HEADING.match(ln)
        num = _NUMBERED.match(m_h.group(1)) if m_h else None
        if num:  # numbered heading -> new section chunk
            flush()
            sec, title = num.group(1), num.group(2).strip()
            cur = {
                "citation_id": f"{doc_name}::{sec}",
                "clause": sec,
                "title": title,
                "is_glossary": bool(_GLOSSARY.search(title)),
                "text": f"{sec} {title}",
            }
            continue
        # non-numbered heading or body line -> content of current section
        if cur is not None:
            cur["text"] += "\n" + ln
    flush()

    # drop the table-of-contents section (dot-leaders, no real body)
    kept = []
    for it in items:
        body = it["text"].split("\n", 1)[1] if "\n" in it["text"] else ""
        if it["title"].upper().startswith("CONTENTS") or (
            _DOT_LEADER.search(body) and len(_DOT_LEADER.findall(body)) >= 3
        ):
            continue
        kept.append(it)
    return kept
