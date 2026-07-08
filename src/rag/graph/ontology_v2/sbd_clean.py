"""Security By Design targeted cleanup (ontology_v2, option 1 — text-only).

SBD is diagram-heavy; Docling OCR'd its process diagrams into single-word
fragment runs, and its tail (References + Annex A diagrams + Annex B roles +
Annex C glossary) — none of which carry clause numbers — got absorbed into a
garbage `::6` blob. Single-digit section headers (`## 4.`, `## 6.`) also bled
into clauses 3.4 / 5.8.3.

This does NOT re-parse; it post-processes the existing chunks:
  1. strip Figure captions / <!-- image --> / diagram fragment runs from every chunk
  2. split the garbage ::6 -> Annex C glossary to definitions, Annex B roles to
     its own chunk, garbage head dropped
  3. rebuild ::6 as the real §6 intro (bled into 5.8.3); trim 3.4/5.8.3 bleeds

    poetry run python -m rag.graph.ontology_v2.sbd_clean
"""
import json
import re
from pathlib import Path

_DIR = Path(__file__).parent / "reextract" / "06-security-by-design"
_DEFS = Path(__file__).parent / "definitions"
_DOC = "Security By Design"
_FIGURE = re.compile(r"^\s*Figure [A-Z0-9]", re.I)
_IMG = re.compile(r"^\s*<!--\s*image\s*-->\s*$")


def _strip_frags(text: str) -> str:
    """Keep prose / tables / lists / headings; drop diagram-label fragment lines."""
    out, blanks = [], 0
    for l in text.splitlines():
        s = l.strip()
        if not s:
            blanks += 1
            if blanks <= 1:
                out.append("")
            continue
        blanks = 0
        if _FIGURE.match(s) or _IMG.match(s):
            continue
        if s[0] in "|-#" or s.startswith("- ") or re.match(r"^\(?[a-z]\)", s):
            out.append(l); continue  # table/list/heading
        # prose if long enough or ends with sentence punctuation; else a fragment
        if len(s.split()) >= 6 or s.rstrip()[-1:] in ".:;)]":
            out.append(l)
        # else: short unpunctuated fragment (diagram label / OCR junk) -> drop
    return "\n".join(out).strip()


def _parse_sbd_glossary(text: str, citation: str):
    """Annex C: `| TERM (ABBR) | DEFINITION |` unquoted 2-col table."""
    defs = []
    for ln in text.splitlines():
        if ln.count("|") < 2:
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 2 or all(set(c) <= set("-: ") for c in cells):
            continue
        term_cell, defn = cells[0], " ".join(cells[1:]).strip()
        if term_cell.upper() in ("TERM", "") or not defn or defn.upper() == "DEFINITION":
            continue
        m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", term_cell)
        term, abbr = (m.group(1).strip(), m.group(2).strip()) if m else (term_cell, "")
        defs.append({"term": term, "abbr": abbr, "definition": defn,
                     "citation_id": citation, "incomplete": defn.endswith(":")})
    return defs


def clean():
    recs = json.loads((_DIR / "clauses.json").read_text())
    byid = {r["citation_id"]: r for r in recs}

    # --- 2. dismantle the garbage ::6 blob ---
    blob = byid.get(f"{_DOC}::6", {}).get("text", "")
    definitions, annex_b = [], None
    if "## ANNEX C" in blob:
        b_start = blob.find("## ANNEX B")
        c_start = blob.find("## ANNEX C")
        annex_b_txt = blob[b_start:c_start].strip() if b_start >= 0 else ""
        annex_c_txt = blob[c_start:].strip()
        definitions = _parse_sbd_glossary(annex_c_txt, f"{_DOC}::AnnexC")
        if annex_b_txt:
            annex_b = {"citation_id": f"{_DOC}::AnnexB", "clause": "AnnexB",
                       "title": "Roles and Responsibilities", "text": _strip_frags(annex_b_txt)}

    # --- 3. recover the real §6 intro bled into 5.8.3 ---
    s583 = byid.get(f"{_DOC}::5.8.3")
    six_intro = ""
    if s583 and "## 6." in s583["text"]:
        head, _, tail = s583["text"].partition("## 6.")
        s583["text"] = head.strip()
        six_intro = ("6. " + tail).strip()
    # trim 3.4's bled "## 4." garbage tail
    s34 = byid.get(f"{_DOC}::3.4")
    if s34 and "## 4." in s34["text"]:
        s34["text"] = s34["text"].split("## 4.")[0].strip()

    # --- rebuild records: strip frags everywhere, replace ::6, drop nothing silently ---
    out = []
    for r in recs:
        if r["citation_id"] == f"{_DOC}::6":
            r = {**r, "text": _strip_frags(six_intro) or "6 Security-by-Design Framework Implementation"}
        else:
            r = {**r, "text": _strip_frags(r["text"])}
        r["chars"] = len(r["text"].strip()); r["words"] = len(r["text"].split())
        out.append(r)
    if annex_b:
        annex_b["chars"] = len(annex_b["text"]); annex_b["words"] = len(annex_b["text"].split())
        annex_b["flags"] = []
        out.append(annex_b)

    (_DIR / "clauses.json").write_text(json.dumps(out, indent=2))
    # definitions
    if definitions:
        (_DEFS / "06-security-by-design.json").write_text(json.dumps(definitions, indent=2))
        (_DEFS / "06-security-by-design.txt").write_text(
            f"# Definitions — {_DOC} (Annex C)  [{len(definitions)} terms]\n\n" +
            "\n".join(f"- {d['term']}" + (f" ({d['abbr']})" if d['abbr'] else "") + f": {d['definition']}"
                      for d in definitions))
    print(f"SBD cleaned: {len(recs)} -> {len(out)} chunks (+AnnexB={annex_b is not None}), "
          f"{len(definitions)} definitions extracted")
    return out, definitions


if __name__ == "__main__":
    clean()
