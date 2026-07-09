"""Re-extract ONE source document, fresh from its PDF (ontology_v2, Phase 0).

Nothing from the existing Neo4j / prior ingestion is reused. For a single doc
(by 1-based index into the canonical CCOP_DOCUMENTS set) this:

  1. Parses the source PDF with the project's Docling parser.
  2. Segments into clause/section chunks with the project's configured chunker.
  3. Writes the raw Docling markdown + segmented clauses + a NOISE LEDGER under
     rag/graph/ontology_v2/reextract/<NN-slug>/ for human approval.

It writes artifacts only — no Neo4j writes, no downstream ingestion. Review the
LEDGER, approve, then move to the next doc.

    poetry run python -m rag.graph.ontology_v2.reextract_doc <index>
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from infrastructure.config.settings import get_settings
from rag.ingestion.chunkers.clause_aware_chunker import chunk_by_clauses
from rag.ingestion.chunkers.section_chunker import chunk_document
from rag.ingestion.models import ChunkerType
from rag.ingestion.parsers.ccop_pdf_parser import CCOP_DOCUMENTS
from rag.ingestion.parsers.docling_parser import parse_ccop_pdf_with_docling

_OUT_ROOT = Path(__file__).parent / "reextract"
_DOT_LEADER = re.compile(r"\.{6,}")
_FOOTER = re.compile(r"^\s*(JULY 2022|JANUARY 2020)\s*$")
_HEADING = re.compile(r"^\s*#{1,4}\s")


def _strip_boilerplate(text: str) -> str:
    """Remove page-footer lines anywhere + trailing bled headings/blank lines.

    Content is never on a footer line, so dropping `JULY 2022` / `JANUARY 2020`
    page footers and any `##` heading that bled onto the end of a chunk is safe.
    """
    lines = [l for l in text.splitlines() if not _FOOTER.match(l)]
    while lines and (not lines[-1].strip() or _HEADING.match(lines[-1])):
        lines.pop()
    return "\n".join(lines).strip()


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _pipe_lines(text: str) -> int:
    return sum(1 for ln in text.splitlines() if ln.count("|") >= 2)


def _profile(text: str) -> List[str]:
    flags = []
    body = text.strip()
    if not body:
        flags.append("blank")
    if _DOT_LEADER.search(text):
        flags.append("toc-dot-leader")
    if _pipe_lines(text) >= 3:
        flags.append("table")
    if 0 < len(body) < 40:
        flags.append("tiny")
    return flags


def reextract(index: int) -> Dict[str, Any]:
    if not (1 <= index <= len(CCOP_DOCUMENTS)):
        raise SystemExit(f"index must be 1..{len(CCOP_DOCUMENTS)}")
    settings = get_settings()
    doc = CCOP_DOCUMENTS[index - 1]
    ccop_dir = Path(settings.rag_source_documents_path) if hasattr(settings, "rag_source_documents_path") else Path("../ccop-official")
    pdf_path = str((ccop_dir / doc.path).resolve())

    print(f"[{index}/{len(CCOP_DOCUMENTS)}] Re-extracting: {doc.name}\n  PDF: {pdf_path}\n  chunker: {doc.chunker_type.value}")
    parsed = parse_ccop_pdf_with_docling(pdf_path, doc.name)
    markdown = parsed.markdown

    # RtF is a Q&A doc numbered at N.N sub-clause level; the shared clause-aware
    # chunker fuses its sections, so route it to the dedicated segmenter.
    if doc.name == "CCoP Response to Feedback":
        from rag.graph.ontology_v2.rtf_segmenter import segment_rtf
        raw = segment_rtf(markdown, doc.name)
    elif doc.name == "Cybersecurity Act 2018":
        from rag.graph.ontology_v2.act_segmenter import segment_act
        raw = segment_act(markdown, doc.name)
    elif doc.chunker_type == ChunkerType.CLAUSE_AWARE:
        raw = [{"citation_id": getattr(c.metadata, "citation_id", ""),
                "clause": getattr(c.metadata, "clause", ""), "text": c.text or ""}
               for c in chunk_by_clauses(markdown, doc.name, preamble_max_words=settings.preamble_max_words)]
    else:
        # Supplementary guides are heading-structured; the shared section chunker's
        # token-merge fuses/drops sections, so segment on numbered headings instead.
        from rag.graph.ontology_v2.heading_segmenter import segment_by_headings
        raw = segment_by_headings(markdown, doc.name)

    records = []
    for r in raw:
        text = _strip_boilerplate(r.pop("text", "") or "")
        records.append({**r, "chars": len(text.strip()), "words": len(text.split()),
                        "flags": _profile(text), "text": text})

    # cross-chunk duplicate-body detection (shared-blob failure)
    bodies = Counter(r["text"].strip() for r in records if len(r["text"].strip()) > 60)
    shared = {b: n for b, n in bodies.items() if n > 1}
    for r in records:
        if shared.get(r["text"].strip(), 0) > 1:
            r["flags"] = r["flags"] + ["shared-blob"]

    out = _OUT_ROOT / f"{index:02d}-{_slug(doc.name)}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "source.md").write_text(markdown)
    (out / "clauses.json").write_text(json.dumps(records, indent=2))

    # ---- noise ledger (the review artifact) ----
    total = len(records)
    fl = Counter(f for r in records for f in r["flags"])
    clean = sum(1 for r in records if not r["flags"])
    ledger = [
        f"# Re-extraction ledger — {doc.name}",
        f"\nSource PDF: `{doc.path}`  |  chunker: `{doc.chunker_type.value}`",
        f"\n## Counts (verified this run)",
        f"- segmented chunks: **{total}**",
        f"- clean (no noise flag): **{clean}**  ({100*clean//max(total,1)}%)",
        f"- flagged: **{total-clean}**",
        f"\n## Noise breakdown",
    ] + [f"- `{f}`: {n}" for f, n in fl.most_common()] + [
        f"\n## Shared-blob groups: {len(shared)} (covering {sum(shared.values())} chunks)",
    ]
    if shared:
        worst = max(shared.items(), key=lambda p: p[1])
        ledger.append(f"- worst: {worst[1]} chunks share one body — `{worst[0][:120].replace(chr(10),' ')}…`")
    ledger.append("\n## Flagged samples")
    shown = 0
    for r in records:
        if r["flags"] and shown < 12:
            ledger.append(f"\n### `{r['citation_id']}`  {r['flags']}  ({r['chars']} chars)")
            ledger.append("```\n" + r["text"][:300].strip() + "\n```")
            shown += 1
    ledger.append("\n## First 8 clean clauses (spot-check verbatim vs PDF)")
    shown = 0
    for r in records:
        if not r["flags"] and shown < 8:
            ledger.append(f"\n### `{r['citation_id']}`  ({r['chars']} chars)")
            ledger.append("```\n" + r["text"][:300].strip() + "\n```")
            shown += 1
    (out / "LEDGER.md").write_text("\n".join(ledger))

    print(f"\n  chunks={total}  clean={clean}  flagged={total-clean}")
    print(f"  noise: {dict(fl)}")
    print(f"  shared-blob groups: {len(shared)}")
    print(f"  artifacts: {out}/  (source.md, clauses.json, LEDGER.md)")
    return {"doc": doc.name, "total": total, "clean": clean, "flags": dict(fl), "out": str(out)}


if __name__ == "__main__":
    reextract(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
