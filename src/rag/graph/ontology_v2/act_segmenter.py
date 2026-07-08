"""Cybersecurity Act 2018 segmenter (ontology_v2).

The Act is a statute: `## Part N`, then per-section `## <marginal title>` headings
whose body begins `N.` / `N.—(1)`, with subsection markers `(1)`,`( a )` as body.
Docling renders it TWICE — a short contents pass then the full GOVERNMENT GAZETTE
text; we segment only the gazette portion.

Boundary = each `## <title>` heading. The section number is read from the first
`N.` in that block's body → `Cybersecurity Act 2018::N`. Part-name echoes
(PRELIMINARY, ADMINISTRATION…) and masthead noise are skipped. Schedules (First/
Second) are emitted as their own chunks (First Schedule = essential-services list).
"""
import re
from typing import Any, Dict, List

_HEAD = re.compile(r"^#{2,3}\s+(.+?)\s*$")
_PART = re.compile(r"^(?:Part|PART)\s+(\d+)\b\s*(.*)$")
_SECNUM = re.compile(r"^\s*(\d{1,3})\.\s*(?:[-—]\s*\(1\))?")
_NOISE = re.compile(r"^(REPUBLIC|CYBERSECURITY ACT 2018|Date of Commencement)", re.I)
# all-caps Part-name echoes rendered as standalone headings (not sections)
_PART_ECHO = re.compile(r"^[A-Z][A-Z ,'&/()-]+$")
_SCHEDULE = re.compile(r"^(FIRST|SECOND|THIRD)\s+SCHEDULE", re.I)


def segment_act(markdown: str, doc_name: str) -> List[Dict[str, Any]]:
    lines = markdown.splitlines()
    gz = next((i for i, l in enumerate(lines) if "GOVERNMENT GAZETTE" in l), 0)
    body_lines = lines[gz:]

    items: List[Dict[str, Any]] = []
    cur: Dict[str, Any] | None = None
    part = ""
    in_schedule = ""
    sched_tag = ""

    def _slug(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]

    def flush():
        nonlocal cur
        if cur is not None:
            cur["text"] = cur["text"].strip()
            if cur["kind"] == "section" and not cur["clause"]:
                # resolve section number from the block body (first N.)
                for ln in cur["text"].splitlines()[1:]:
                    m = _SECNUM.match(ln)
                    if m:
                        cur["clause"] = m.group(1)
                        cur["citation_id"] = f"{doc_name}::{m.group(1)}"
                        break
            elif cur["kind"] == "schedule-item":
                # namespace under the schedule to avoid colliding with sections
                num = ""
                for ln in cur["text"].splitlines()[1:]:
                    m = _SECNUM.match(ln)
                    if m:
                        num = m.group(1); break
                key = num or _slug(cur["title"])
                cur["clause"] = f"{cur['sched_tag']}.{key}"
                cur["citation_id"] = f"{doc_name}::{cur['sched_tag']}.{key}"
            items.append(cur)
            cur = None

    for ln in body_lines:
        mh = _HEAD.match(ln)
        if mh:
            title = mh.group(1).strip()
            mpart = _PART.match(title)
            msched = _SCHEDULE.match(title)
            if _NOISE.match(title):
                flush(); continue
            if mpart:
                flush(); part = f"Part {mpart.group(1)} {mpart.group(2)}".strip(); in_schedule = ""; continue
            if msched:
                flush(); in_schedule = title; sched_tag = f"{title.split()[0].title()}Schedule"; part = title
                cur = {"citation_id": f"{doc_name}::{sched_tag}", "clause": sched_tag,
                       "title": title, "part": part, "kind": "schedule", "text": title,
                       "sched_tag": sched_tag}
                continue
            if _PART_ECHO.match(title) and not in_schedule:
                flush(); continue  # Part-name echo (PRELIMINARY, ADMINISTRATION…)
            # a section (or schedule sub-item) title
            flush()
            cur = {"citation_id": f"{doc_name}::?", "clause": "", "title": title,
                   "part": part, "kind": "schedule-item" if in_schedule else "section",
                   "text": title, "sched_tag": sched_tag}
            continue
        if cur is not None:
            cur["text"] += "\n" + ln
    flush()

    # keep sections with a resolved number + schedule chunks; drop title-only stubs
    out = []
    for it in items:
        body = it["text"].split("\n", 1)[1].strip() if "\n" in it["text"] else ""
        if it["kind"] == "section" and not it["clause"]:
            continue  # unnumbered stray heading, no body number
        if not body and it["kind"] == "section":
            continue
        out.append(it)
    return out
