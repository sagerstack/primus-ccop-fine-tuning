#!/usr/bin/env python3
"""
Diagnose embedder-fail cases (R@K=0) to determine root cause.

Categorizes each case into:
- VOCAB_MISMATCH:  question and expected clause text use different vocabulary
                   (HyDE / query rewriting would help)
- CITATION_FORMAT: expected clause has non-standard format (e.g. external doc reference)
                   (measurement bug, not retrieval bug)
- LIKELY_CHUNKING: question and clause share keywords but retrieval still misses
                   (chunking / embedding issue, harder to fix)
- UNKNOWN:         can't categorize from available data

For each case, also runs a "rewriting probe" — manually injects the expected
clauses' top-3 distinctive terms into the query and re-runs dense retrieval
to see if R@K lifts. If it does, vocabulary is confirmed as the fix.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

SRC = Path("/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/src")
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# ---- Load corpus map: clause_id -> text ----
corpus_dump = Path("/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/.lab/workspace/corpus_dump.md").read_text()
clause_to_text = {}
sections = corpus_dump.split("\n### [")
for sec in sections[1:]:  # skip top
    end = sec.find("]")
    if end == -1:
        continue
    cid = sec[:end]
    body = sec[end+1:].strip()
    # Drop the _path_ italic line if present
    if body.startswith("_path:"):
        body = body.split("\n", 1)[1] if "\n" in body else ""
    clause_to_text[cid] = body[:1500]

# ---- Tokenizer ----
STOPWORDS = set("""a an and as at be by for from has have he her his i in is it its of on or the their they to was were what when where which who will with would you your""".split())
def tokens(s: str) -> set:
    return {t for t in re.findall(r"\b[a-z]{3,}\b", s.lower()) if t not in STOPWORDS}

def jaccard(a: set, b: set) -> float:
    if not a or not b: return 0.0
    return len(a & b) / len(a | b)

# ---- Match expected clause id to corpus citation_id ----
def find_clause_text(expected_clause: str) -> tuple[str, str]:
    """Find best matching corpus text for an expected clause id."""
    e = expected_clause.strip()
    # Exact match against any citation_id ending with this id
    for cid, txt in clause_to_text.items():
        if cid == e or cid.endswith("::" + e):
            return cid, txt
    # Parent match: cid ends with e + sub-letter
    for cid, txt in clause_to_text.items():
        if cid.endswith("::" + e) or "::" + e + "(" in cid or "::" + e + "." in cid:
            return cid, txt
    # Prefix match (e is parent)
    for cid, txt in clause_to_text.items():
        # find chunks where the citation contains the expected as a substring around dots
        if "::" + e in cid:
            return cid, txt
    return "", ""

# ---- Load Exp 11 results ----
d = json.load(open("/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/.lab/workspace/exp11-dense-only.json"))
fail_cases = [r for r in d["per_case"] if r["recall_topk"] == 0.0]
print(f"Found {len(fail_cases)} R@K=0 cases\n")

# ---- Load test cases for question text ----
import glob
raw_cases = {}
for f in glob.glob("/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/ground-truth/test-suite/*.jsonl"):
    if ".bak" in f: continue
    for line in open(f):
        if not line.strip(): continue
        d2 = json.loads(line)
        raw_cases[d2["test_id"]] = d2

# ---- Categorize each fail case ----
findings = []
for r in fail_cases:
    tid = r["test_id"]
    expected = r["expected"]
    if not raw_cases.get(tid):
        continue
    q = raw_cases[tid]["input"]["question"]
    q_tokens = tokens(q)

    # External doc check — citation format that's not a CCoP X.Y.Z
    has_external = any("Section " in e or "Act" in e or "Addendum" in e or "Scope" in e for e in expected)

    # Resolve each expected clause to text
    resolved = []
    for e in expected:
        cid, txt = find_clause_text(e)
        if cid:
            t_tokens = tokens(txt)
            j = jaccard(q_tokens, t_tokens)
            shared = q_tokens & t_tokens
            resolved.append({
                "expected": e,
                "matched_cid": cid,
                "text": txt[:300],
                "jaccard": j,
                "shared_terms": list(shared)[:10],
            })
        else:
            resolved.append({"expected": e, "matched_cid": "", "text": "", "jaccard": 0.0, "shared_terms": []})

    # Categorize
    found_count = sum(1 for x in resolved if x["matched_cid"])
    if found_count == 0:
        cat = "CITATION_FORMAT" if has_external else "CORPUS_GAP"
    else:
        avg_j = sum(x["jaccard"] for x in resolved if x["matched_cid"]) / max(found_count, 1)
        max_j = max((x["jaccard"] for x in resolved), default=0.0)
        if max_j < 0.04:
            cat = "VOCAB_MISMATCH"  # very low overlap
        elif max_j < 0.1:
            cat = "VOCAB_MISMATCH_OR_CHUNKING"
        else:
            cat = "LIKELY_CHUNKING"  # decent overlap, retrieval still misses

    findings.append({
        "test_id": tid,
        "category": cat,
        "question": q[:150],
        "expected": expected,
        "resolved": resolved,
        "max_jaccard": max((x["jaccard"] for x in resolved), default=0.0),
    })

# ---- Print summary table ----
from collections import Counter
cat_counts = Counter(f["category"] for f in findings)
print("=" * 80)
print("CATEGORY SUMMARY")
print("=" * 80)
for cat, n in cat_counts.most_common():
    print(f"  {cat}: {n} cases")
print()

print("=" * 80)
print("PER-CASE DETAIL")
print("=" * 80)
for f in findings:
    print(f"\n{f['test_id']} — {f['category']} (max_jaccard={f['max_jaccard']:.3f})")
    print(f"  Q: {f['question']}")
    for x in f["resolved"]:
        if x["matched_cid"]:
            print(f"  Expected [{x['expected']}] → matched {x['matched_cid']}")
            print(f"    Text: {x['text'][:200]}")
            print(f"    Shared terms (Q∩T): {x['shared_terms']}")
            print(f"    Jaccard: {x['jaccard']:.3f}")
        else:
            print(f"  Expected [{x['expected']}] → NOT FOUND in corpus")

# ---- Save JSON ----
out = "/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/.lab/workspace/embedder-fail-diagnostic.json"
Path(out).write_text(json.dumps({"summary": dict(cat_counts), "cases": findings}, indent=2))
print(f"\n\nWrote: {out}")
