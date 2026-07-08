"""Apply approved P0 cleaning decisions to a re-extracted document (ontology_v2).

Consumes reextract/<NN-slug>/clauses.json and emits:
  - clauses.clean.json     the retained clause corpus (obligations/provisions)
  - definitions/<NN-slug>.json + .txt   term->definition pairs pulled OUT of the
    clause corpus (glossary), the Phase-1 entity/premise seed
  - CLEAN-LEDGER.md         before/after counts + exactly what was dropped/moved

Decisions are per-doc (reviewed one at a time). This module holds the rules
approved for each doc index; rules are explicit and auditable, never silent.

    poetry run python -m rag.graph.ontology_v2.apply_clean <index>
"""
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from rag.ingestion.parsers.ccop_pdf_parser import CCOP_DOCUMENTS

_ROOT = Path(__file__).parent
_REEXTRACT = _ROOT / "reextract"
_DEFS = _ROOT / "definitions"
_TERM_RE = re.compile(r"^'([^']+)'(?:\s*\('([^']+)'\))?")


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


_SN = re.compile(r"^\d+(?:\.\d+)*$")


def _parse_glossary(text: str, citation: str) -> List[Dict[str, Any]]:
    """Parse a pipe-table glossary into term/abbr/definition records.

    Handles two layouts seen in the corpus:
      - 2-col  `'term' ('ABBR') | definition`         (CCoP §1.2.1)
      - 3-col  `SN | term | definition`               (Auditing Guidelines §8)
    Definitions may span multiple rows (continuation rows have an empty leading
    cell); those are folded into the current term until the next term row.
    """
    defs: List[Dict[str, Any]] = []
    for ln in text.splitlines():
        if ln.count("|") < 2:
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 2 or all(set(c) <= set("-: ") for c in cells):  # separator/empty
            continue

        if len(cells) >= 3 and _SN.match(cells[0]):  # 3-col SN | term | def
            term, defn = cells[1], " ".join(cells[2:]).strip()
            if term and defn:
                m = _TERM_RE.match(term)
                t, abbr = (m.group(1).strip(), (m.group(2) or "").strip()) if m else (term, "")
                defs.append({"term": t, "abbr": abbr, "definition": defn,
                             "citation_id": citation, "incomplete": False})
            elif defs:  # continuation
                defs[-1]["definition"] = (defs[-1]["definition"] + " " + defn).strip()
            continue

        term_cell, defn = cells[0], " ".join(cells[1:]).strip()  # 2-col 'term' | def
        m = _TERM_RE.match(term_cell)
        if m and defn:
            defs.append({"term": m.group(1).strip(), "abbr": (m.group(2) or "").strip(),
                         "definition": defn, "citation_id": citation, "incomplete": False})
        elif defs and not term_cell:  # continuation row
            defs[-1]["definition"] = (defs[-1]["definition"] + " " + defn).strip()
    for d in defs:
        d["incomplete"] = d["definition"].rstrip().endswith(":") or len(d["definition"]) < 6
    return defs


# ---- per-doc approved rules -------------------------------------------------
def _decide(index: int, records: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Return (kept_clauses, dropped_with_reason, definitions)."""
    kept, dropped, definitions = [], [], []
    if index == 1:  # CCoP 2.0 — decisions approved 2026-07-08
        for r in records:
            cid = r["citation_id"]
            base = cid.split("::table::")[0]
            if "::preamble::" in cid:
                dropped.append({**r, "drop_reason": "front-matter (cover/history/TOC)"})
            elif base == "CCoP 2.0::1.2.1":
                # glossary -> definitions file; remove from clause corpus
                if "::table::" not in cid:
                    definitions.extend(_parse_glossary(r["text"], "CCoP 2.0::1.2.1"))
                dropped.append({**r, "drop_reason": "glossary -> definitions file"})
            elif "tiny" in r["flags"]:
                dropped.append({**r, "drop_reason": "heading/list-item (content in parent or child)"})
            else:
                kept.append(r)
    elif index == 2:  # CCoP Response to Feedback — approved 2026-07-08
        # Atomic N.N sub-clauses, already 0-flagged; keep all (POC-faithful:
        # atomic answer sub-clauses linked later by shared entities, not Q&A merge).
        kept = list(records)
    elif index in (3, 4, 5):  # Auditing / Threat Modelling / Risk Assessment — approved 2026-07-08
        # heading-segmented supplementary guides: drop tiny headers, bibliography
        # (REFERENCES) sections, route glossaries to the definitions file.
        for r in records:
            title = (r.get("title") or "").upper()
            if r.get("is_glossary"):
                definitions.extend(_parse_glossary(r["text"], r["citation_id"]))
                dropped.append({**r, "drop_reason": "glossary -> definitions file"})
            elif "REFERENCES" in title:
                dropped.append({**r, "drop_reason": "bibliography (no domain content)"})
            elif "tiny" in r["flags"]:
                dropped.append({**r, "drop_reason": "content-less section header (body in subsections)"})
            else:
                kept.append(r)
    elif index == 6:  # Security By Design — approved 2026-07-08
        # clause_aware doc where tables ARE content; drop front-matter, redundant
        # additive ::table:: re-splits (parent clause keeps the full table text),
        # and content-less tiny headers.
        for r in records:
            cid = r["citation_id"]
            if cid.endswith("::preamble"):
                dropped.append({**r, "drop_reason": "front-matter (cover/TOC)"})
            elif "::table::" in cid:
                dropped.append({**r, "drop_reason": "redundant additive table sub-chunk (parent carries it)"})
            elif len(r["text"].split()) < 4:
                dropped.append({**r, "drop_reason": "empty after fragment-strip (diagram-only header)"})
            elif "tiny" in r["flags"]:
                dropped.append({**r, "drop_reason": "content-less section header (body in children)"})
            else:
                kept.append(r)
    elif index == 7:  # Cybersecurity Act 2018 — first cut 2026-07-08
        # legal-section + schedule chunks; drop the bare header stubs (tiny),
        # keep all sections + schedule content (essential-services sectors, etc).
        # NOTE: §2 Interpretation is a prose definitions section — kept as a
        # normal section for now; parsing to term->def pairs deferred.
        for r in records:
            if "tiny" in r["flags"]:
                dropped.append({**r, "drop_reason": "schedule header stub (no body)"})
            else:
                kept.append(r)
    else:
        raise SystemExit(f"No approved cleaning rules for doc index {index} yet.")
    return kept, dropped, definitions


def apply_clean(index: int) -> Dict[str, Any]:
    doc = CCOP_DOCUMENTS[index - 1]
    slug = f"{index:02d}-{_slug(doc.name)}"
    src = _REEXTRACT / slug / "clauses.json"
    records = json.loads(src.read_text())
    kept, dropped, definitions = _decide(index, records)

    # write cleaned clause corpus
    (_REEXTRACT / slug / "clauses.clean.json").write_text(json.dumps(kept, indent=2))

    # write definitions file (+ readable txt)
    _DEFS.mkdir(parents=True, exist_ok=True)
    if definitions:
        (_DEFS / f"{slug}.json").write_text(json.dumps(definitions, indent=2))
        txt = [f"# Definitions — {doc.name} (§1.2.1)  [{len(definitions)} terms]\n"]
        for d in definitions:
            head = d["term"] + (f" ({d['abbr']})" if d["abbr"] else "")
            mark = "  ⚠INCOMPLETE" if d["incomplete"] else ""
            txt.append(f"- {head}: {d['definition']}{mark}")
        (_DEFS / f"{slug}.txt").write_text("\n".join(txt))

    # ledger
    from collections import Counter
    reasons = Counter(d["drop_reason"] for d in dropped)
    L = [
        f"# Clean ledger — {doc.name}",
        f"\n- input chunks: **{len(records)}**",
        f"- kept clauses: **{len(kept)}**",
        f"- dropped: **{len(dropped)}**",
        f"- definitions extracted: **{len(definitions)}** ({sum(1 for d in definitions if d['incomplete'])} flagged incomplete)",
        f"\n## Drop reasons",
    ] + [f"- {r}: {n}" for r, n in reasons.most_common()]
    L.append("\n## Dropped citation_ids")
    for d in dropped:
        L.append(f"- `{d['citation_id']}` — {d['drop_reason']}")
    (_REEXTRACT / slug / "CLEAN-LEDGER.md").write_text("\n".join(L))

    print(f"[{index}] {doc.name}: {len(records)} -> kept {len(kept)}, dropped {len(dropped)}, defs {len(definitions)}")
    print(f"  drop reasons: {dict(reasons)}")
    print(f"  -> {_REEXTRACT/slug}/clauses.clean.json, CLEAN-LEDGER.md")
    if definitions:
        print(f"  -> {_DEFS/(slug+'.json')} (+ .txt)")
    return {"kept": len(kept), "dropped": len(dropped), "defs": len(definitions)}


if __name__ == "__main__":
    apply_clean(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
