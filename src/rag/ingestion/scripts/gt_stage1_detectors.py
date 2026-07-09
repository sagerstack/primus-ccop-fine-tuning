"""
Ground-Truth Stage-1 Deterministic Defect Detectors

Read-only, stdlib-only, LLM-free scan of every v2 ground-truth test case. Produces
a reproducible defect ledger that feeds the (later) Stage-2 grounded relevance
verifier. Catches ONLY mechanically-decidable defects — no semantic judgment.

Detectors
---------
  D-CITE-KF   Citation existence for fields the existing citation auditor does
              NOT cover: `key_facts[*].source` and `metadata.support_citations`.
              Extracts dotted CCoP clause tokens and checks each against
              clause_inventory.json. Flags tokens absent from the inventory
              (e.g. 5.1.5, 8.3, 5.9.7 — clauses that do not exist).

  D-FAMILY    Section-family consistency: the set of clause section-families
              (leading number) implied by `key_facts[*].source` must overlap
              the families in `metadata.clause_reference`. Disjoint => flag.
              (Reproduces the dominant signal from 01_scanner_findings.md in code.)

  D-FORBIDDEN `fail_conditions.forbidden_claims` contamination: entries that are
              required-element descriptors ("Reference to applicable CCoP clause",
              "Missing: ...", "Evidence quality considerations") wrongly placed in
              the forbidden list. Heuristic, high-precision, flagged for review.

  D-LEAK      `ground_truth.expected_response` is a near-verbatim copy of
              `input.question` (answer leaked into the prompt).

Why deterministic-only: clause EXISTENCE and structural defects are decidable in
code, reproducibly and for free. An LLM asked "does 5.1.5 exist?" recalls and
hallucinates — the exact failure mode this pipeline removes. Citation RELEVANCE /
misattribution / hallucination are semantic and are deferred to Stage 2, which
reasons over the *fetched* clause text one record at a time.

The inventory is the authority (validated in
docs/project_notes/gt_audit_2026-04-28/05_clause_inventory_validation.md).

Usage
-----
    cd src && poetry run python -m rag.ingestion.scripts.gt_stage1_detectors \
        --inventory rag/ingestion/fixtures/clause_inventory.json \
        --test-suite-dir ../ground-truth/test-suite \
        --out-dir ../docs/project_notes/gt_audit_2026-04-28
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Clause-token extraction
# ---------------------------------------------------------------------------

# Dotted CCoP clause numbers: 1-2 leading digits, then 1-3 ".N" groups.
# e.g. 5.1.5, 8.3, 5.9.7, 4.1.1 — optional trailing sub-letter like (c) stripped.
_DOTTED_CLAUSE_RE = re.compile(r"\b(\d{1,2}(?:\.\d{1,2}){1,3})\b")

# Valid CCoP 2.0 top-level section numbers (1..11). Tokens outside this range are
# almost certainly version strings, dates, or cross-doc artefacts — not clauses.
_CCOP_MAX_SECTION = 11

# "N.0" is a version string (e.g. the "2.0" in "CCoP 2.0"), never a real clause —
# CCoP clause numbering has no ".0" segments. Exclude to avoid false positives.
_VERSION_TOKEN_RE = re.compile(r"^\d{1,2}\.0$")


def extract_ccop_clause_tokens(text: str) -> set[str]:
    """Return the set of plausible CCoP 2.0 dotted clause IDs mentioned in *text*.

    Naive: extracts every in-range dotted token. Use this only where the text is
    known to be CCoP-attributed (e.g. test bodies). For free-form `key_facts.source`
    strings that mix document references, use `extract_ccop_citations_from_source`.
    """
    out: set[str] = set()
    if not text:
        return out
    for m in _DOTTED_CLAUSE_RE.finditer(text):
        tok = m.group(1)
        if _VERSION_TOKEN_RE.match(tok):
            continue
        # exclude RtF question numbers like "Q2.3"
        start = m.start(1)
        if start > 0 and text[start - 1] in ("Q", "q"):
            continue
        head = int(tok.split(".")[0])
        if 1 <= head <= _CCOP_MAX_SECTION:
            out.add(tok)
    return out


# Document-attribution markers for free-form source strings.
_RTF_MARKERS = ("response-to-feedback", "response to feedback", "rtf", "feedback q")
_ACT_MARKERS = ("cybersecurity act", "amendment act", "cybersecurity (amendment)")
_OTHER_DOC_MARKERS = (
    "security by design", "risk assessment guide", "threat modelling",
    "auditing guideline", "im8", "iso 27001", "iso/iec", "nist", "mas ",
    "multi-regulatory", "sector",
)


def _segment_is_ccop(segment: str) -> bool:
    """True only if a source segment is EXPLICITLY CCoP-attributed.

    High-precision: requires an explicit "CCoP"/"clause" marker. Bare dotted
    tokens with no document context (e.g. B08's ['4.2','4.3'], which are Risk
    Assessment Guide sections) are NOT assumed to be CCoP — assuming so produces
    false "non-existent CCoP clause" flags. Such ambiguous citations are caught
    structurally by D-FAMILY and resolved in Stage 2 instead.
    """
    s = segment.lower()
    if any(m in s for m in _RTF_MARKERS) or any(m in s for m in _ACT_MARKERS):
        return False
    if any(m in s for m in _OTHER_DOC_MARKERS):
        return False
    return "ccop" in s or "clause" in s


def extract_ccop_citations_from_source(text: str) -> set[str]:
    """CCoP clause tokens from a free-form source string, per-segment attribution-aware.

    Splits on commas/semicolons and only extracts dotted tokens from segments
    attributed to CCoP 2.0 — avoids false positives from RtF "Q2.3", Act sections,
    and cross-framework references.
    """
    out: set[str] = set()
    if not text:
        return out
    for segment in re.split(r"[,;]", text):
        if _segment_is_ccop(segment):
            out |= extract_ccop_clause_tokens(segment)
    return out


def section_family(clause_id: str) -> str:
    """Leading section number of a clause id ('5.1.5' -> '5')."""
    return clause_id.split(".")[0]


# ---------------------------------------------------------------------------
# Inventory (the authority)
# ---------------------------------------------------------------------------


def load_ccop_clause_ids(inventory_path: Path) -> set[str]:
    """Load the set of CCoP 2.0 clause IDs (numeric + sub-letter) from the inventory."""
    data = json.loads(inventory_path.read_text(encoding="utf-8"))
    return {
        e["clause_id"]
        for e in data["entries"]
        if e["source_doc"] == "CCoP 2.0"
    }


# ---------------------------------------------------------------------------
# D-FORBIDDEN heuristic vocabulary
# ---------------------------------------------------------------------------

# A legit forbidden_claim asserts a WRONG behaviour/statement. A contaminated
# entry is a noun-phrase describing a REQUIRED answer element. We flag the latter
# only when no "bad-behaviour" marker is present (high precision over recall).

_REQUIRED_ELEMENT_PATTERNS = [
    r"^missing:",
    r"^reference to ",
    r"^identification of ",
    r"^assessment of ",
    r"^consideration of ",
    r"^coordination strategy",
    r"^clear ",
    r"^specific ",
    r"^justification for ",
    r"^evidence (quality|requirements|of)",
    r"^sector-specific ",
    r"^risk-based justification",
    r"^the security intent",
    r"^the threat or risk",
    r"^how the control",
    r"^mandatory elements",
    # trailing-noun descriptors — NOT "requirements", which legitimately ends many
    # genuine prohibitions ("X satisfies/violates CCoP requirements").
    r"(considerations|awareness|recommendations|perspective on)\s*$",
]
_REQUIRED_ELEMENT_RE = re.compile("|".join(_REQUIRED_ELEMENT_PATTERNS), re.IGNORECASE)

# Presence of any of these => it is a genuine prohibition, NOT contamination.
_BAD_BEHAVIOUR_MARKERS = [
    "does not", "do not", "cannot", "can't", "without", "substitut", "replace",
    "optional", "discretionary", "acceptable", "sufficient", "ignor", "downplay",
    "dismiss", "disregard", "assum", "stating", "confus", "misclass", "misrepresent",
    "attribut", "invent", "non-existent", "prioritizing low", "suggesting",
    "proposing infeasible", "personally liable", "delayed reporting",
]


def looks_like_required_element(entry: str) -> bool:
    """True if a forbidden_claims entry reads as a required-element descriptor."""
    e = entry.strip().lower()
    if any(m in e for m in _BAD_BEHAVIOUR_MARKERS):
        return False
    return bool(_REQUIRED_ELEMENT_RE.search(e))


# ---------------------------------------------------------------------------
# D-LEAK helper
# ---------------------------------------------------------------------------


def _norm_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def question_answer_overlap(question: str, expected: str) -> float:
    """Token Jaccard overlap between question and expected_response (0..1)."""
    q, e = set(_norm_tokens(question)), set(_norm_tokens(expected))
    if not q or not e:
        return 0.0
    return len(q & e) / len(q | e)


# ---------------------------------------------------------------------------
# Defect record
# ---------------------------------------------------------------------------


@dataclass
class Defect:
    test_id: str
    benchmark: str
    detector: str          # D-CITE-KF | D-FAMILY | D-FORBIDDEN | D-LEAK
    field_path: str        # where the defect lives
    offending_value: str   # the exact token/string that triggered the flag
    reason: str            # one-line, human-readable
    confidence: str = "high"  # high (decidable) | heuristic (review-recommended)


# ---------------------------------------------------------------------------
# Detectors (one record at a time, pure functions)
# ---------------------------------------------------------------------------


def detect_cite_kf(rec: dict, ccop_ids: set[str]) -> list[Defect]:
    """D-CITE-KF: CCoP clause tokens in key_facts.source / support_citations not in inventory."""
    tid = rec.get("test_id", "")
    bm = rec.get("benchmark_id", "")
    out: list[Defect] = []
    gt = rec.get("ground_truth", {}) or {}
    meta = rec.get("metadata", {}) or {}

    sources: list[tuple[str, str]] = []
    for i, kf in enumerate(gt.get("key_facts", []) or []):
        sources.append((f"ground_truth.key_facts[{i}].source", str(kf.get("source", ""))))
    sc = meta.get("support_citations", []) or []
    if isinstance(sc, str):
        sc = [sc]
    for i, s in enumerate(sc):
        sources.append((f"metadata.support_citations[{i}]", str(s)))

    for field_path, text in sources:
        for tok in sorted(extract_ccop_citations_from_source(text)):
            if tok not in ccop_ids:
                out.append(Defect(
                    test_id=tid, benchmark=bm, detector="D-CITE-KF",
                    field_path=field_path, offending_value=tok,
                    reason=f"CCoP clause {tok!r} cited in {field_path} but absent from clause inventory",
                ))
    return out


def detect_family(rec: dict) -> list[Defect]:
    """D-FAMILY: key_facts.source clause families disjoint from clause_reference families."""
    tid = rec.get("test_id", "")
    bm = rec.get("benchmark_id", "")
    gt = rec.get("ground_truth", {}) or {}
    meta = rec.get("metadata", {}) or {}

    cref = meta.get("clause_reference", []) or []
    if isinstance(cref, str):
        cref = [cref]
    cref_fams = {section_family(t) for c in cref for t in extract_ccop_clause_tokens(str(c))}
    if not cref_fams:
        return []  # nothing to compare against

    kf_tokens: set[str] = set()
    for kf in gt.get("key_facts", []) or []:
        kf_tokens |= extract_ccop_citations_from_source(str(kf.get("source", "")))
    kf_fams = {section_family(t) for t in kf_tokens}
    if not kf_fams:
        return []

    if kf_fams.isdisjoint(cref_fams):
        return [Defect(
            test_id=tid, benchmark=bm, detector="D-FAMILY",
            field_path="ground_truth.key_facts[*].source vs metadata.clause_reference",
            offending_value=f"key_facts families {sorted(kf_fams)} vs clause_reference families {sorted(cref_fams)}",
            reason="key_facts.source clause families are disjoint from clause_reference families",
        )]
    return []


def detect_forbidden(rec: dict) -> list[Defect]:
    """D-FORBIDDEN: required-element descriptors contaminating forbidden_claims."""
    tid = rec.get("test_id", "")
    bm = rec.get("benchmark_id", "")
    fc = (rec.get("fail_conditions", {}) or {}).get("forbidden_claims", []) or []
    out: list[Defect] = []
    for i, entry in enumerate(fc):
        if looks_like_required_element(str(entry)):
            out.append(Defect(
                test_id=tid, benchmark=bm, detector="D-FORBIDDEN",
                field_path=f"fail_conditions.forbidden_claims[{i}]",
                offending_value=str(entry),
                reason="forbidden_claims entry reads as a REQUIRED element, not a prohibited claim",
                confidence="heuristic",
            ))
    return out


def detect_leak(rec: dict, threshold: float = 0.92) -> list[Defect]:
    """D-LEAK: expected_response is a near-verbatim copy of the question."""
    tid = rec.get("test_id", "")
    bm = rec.get("benchmark_id", "")
    q = (rec.get("input", {}) or {}).get("question", "") or ""
    e = (rec.get("ground_truth", {}) or {}).get("expected_response", "") or ""
    if not q or not e:
        return []
    # substring or very high token overlap
    overlap = question_answer_overlap(q, e)
    q_in_e = q.strip().lower() in e.strip().lower()
    if q_in_e or overlap >= threshold:
        return [Defect(
            test_id=tid, benchmark=bm, detector="D-LEAK",
            field_path="ground_truth.expected_response vs input.question",
            offending_value=f"overlap={overlap:.2f} substring={q_in_e}",
            reason="expected_response duplicates the question (answer leaked into the prompt)",
        )]
    return []


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def load_test_suite(test_suite_dir: Path) -> list[dict]:
    recs: list[dict] = []
    for fp in sorted(test_suite_dir.glob("b*.jsonl")):
        for line in fp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs


def scan(records: list[dict], ccop_ids: set[str]) -> list[Defect]:
    defects: list[Defect] = []
    for rec in records:
        defects.extend(detect_cite_kf(rec, ccop_ids))
        defects.extend(detect_family(rec))
        defects.extend(detect_forbidden(rec))
        defects.extend(detect_leak(rec))
    return defects


def write_ledger(defects: list[Defect], records: list[dict], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()

    by_detector = Counter(d.detector for d in defects)
    by_benchmark = Counter(d.benchmark for d in defects)

    json_path = out_dir / "stage1_defect_ledger.json"
    json_path.write_text(json.dumps({
        "generated_at": ts,
        "total_records": len(records),
        "total_defects": len(defects),
        "by_detector": dict(by_detector),
        "by_benchmark": dict(sorted(by_benchmark.items())),
        "defects": [asdict(d) for d in defects],
    }, indent=2), encoding="utf-8")

    lines = [
        "# GT Stage-1 Defect Ledger (deterministic)",
        "",
        f"Generated: {ts}  |  Records scanned: **{len(records)}**  |  Defects: **{len(defects)}**",
        "",
        "Read-only, LLM-free, reproducible. Catches mechanically-decidable defects only;",
        "citation relevance/hallucination is deferred to Stage 2.",
        "",
        "## By detector",
        "",
        "| Detector | Count | What it means |",
        "|---|---:|---|",
        f"| D-CITE-KF | {by_detector['D-CITE-KF']} | clause cited in key_facts/support_citations does not exist |",
        f"| D-FAMILY | {by_detector['D-FAMILY']} | key_facts.source families disjoint from clause_reference |",
        f"| D-FORBIDDEN | {by_detector['D-FORBIDDEN']} | required element contaminating forbidden_claims (heuristic) |",
        f"| D-LEAK | {by_detector['D-LEAK']} | expected_response duplicates the question |",
        "",
        "## By benchmark",
        "",
        "| Benchmark | Defects |",
        "|---|---:|",
    ]
    for bm, n in sorted(by_benchmark.items()):
        lines.append(f"| {bm} | {n} |")
    lines += ["", "## Defects", ""]
    for d in defects:
        lines.append(
            f"- **{d.test_id}** `{d.detector}` ({d.confidence}) — {d.reason}  \n"
            f"  · `{d.field_path}` → `{d.offending_value}`"
        )
    md_path = out_dir / "stage1_defect_ledger.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> None:
    ap = argparse.ArgumentParser(description="GT Stage-1 deterministic defect detectors")
    ap.add_argument("--inventory", type=Path,
                    default=Path("rag/ingestion/fixtures/clause_inventory.json"))
    ap.add_argument("--test-suite-dir", type=Path,
                    default=Path("../ground-truth/test-suite"))
    ap.add_argument("--out-dir", type=Path,
                    default=Path("../docs/project_notes/gt_audit_2026-04-28"))
    args = ap.parse_args()

    ccop_ids = load_ccop_clause_ids(args.inventory)
    records = load_test_suite(args.test_suite_dir)
    defects = scan(records, ccop_ids)
    json_path, md_path = write_ledger(defects, records, args.out_dir)

    by_detector = Counter(d.detector for d in defects)
    print(f"Scanned {len(records)} records | inventory CCoP ids: {len(ccop_ids)}")
    print(f"Defects: {len(defects)}  {dict(by_detector)}")
    print(f"Ledger: {json_path}")
    print(f"Summary: {md_path}")


if __name__ == "__main__":
    main()
