# Phase 12 Slice A0 — Baseline Graphont Retrieval Recall

**Date:** 2026-07-14
**Mode:** graphont
**Model:** primus-reasoning
**GT directory:** `ground-truth/test-suite/audit-20260629-1245`
**Test cases:** 18 stratified validation sample (one per active benchmark)

---

## Executive Summary

**18/18 cases completed** with valid context sidecars. ✅

**Aggregate metrics (over 18 completed cases, excluding B21-001 which has no GT clauses):**
- **Mean pool size:** 8.0 (consistent top-k=8 across all cases)
- **Mean recall@pool:** 0.206 (20.6%)
- **Clause-hit@k rate:** 0.235 (4/17 cases with GT clauses retrieved at least one match)

**Key finding:** Graphont's baseline recall is low (20.6%). Only 4 out of 17 cases with GT clauses successfully retrieved at least one decisive clause. This is well below the 50% finetuned threshold and indicates significant retrieval quality issues that warrant the planned Slice A/B/C improvements.

---

## Per-Case Results

| Test ID | Benchmark | Pool Size | Clause Hits | GT Count | Recall@Pool | Status |
|---------|-----------|-----------|-------------|----------|-------------|--------|
| B01-001 | B01 | 8 | 0 | 2 | 0.00 | no_match |
| B02-001 | B02 | 8 | 1 | 1 | **1.00** | ok |
| B03-001 | B03 | 8 | 0 | 2 | 0.00 | no_match |
| B04-001 | B04 | 8 | 1 | 1 | **1.00** | ok |
| B05-001 | B05 | 8 | 0 | 2 | 0.00 | no_match |
| B06-001 | B06 | 8 | 0 | 2 | 0.00 | no_match |
| B07-006 | B07 | 8 | 0 | 1 | 0.00 | no_match |
| B08-001 | B08 | 8 | 0 | 2 | 0.00 | no_match |
| B09-001 | B09 | 8 | 1 | 1 | **1.00** | ok |
| B10-001 | B10 | 8 | 1 | 2 | 0.50 | ok |
| B12-001 | B12 | 8 | 0 | 2 | 0.00 | no_match |
| B13-001 | B13 | 8 | 0 | 1 | 0.00 | no_match |
| B14-001 | B14 | 8 | 0 | 1 | 0.00 | no_match |
| B18-001 | B18 | 8 | 0 | 1 | 0.00 | no_match |
| B21-001 | B21 | 8 | 0 | 0 | N/A | empty_gt (no GT clauses) |
| B22-001 | B22 | 8 | 0 | 3 | 0.00 | no_match |
| B23-001 | B23 | 8 | 0 | 3 | 0.00 | no_match |
| B24-001 | B24 | 8 | 0 | 1 | 0.00 | no_match |

**Status legend:**
- `ok` — At least one GT clause retrieved
- `no_match` — Retrieved 8 clauses but none matched GT
- `empty_gt` — GT has no clause references (excluded from recall aggregate)
- `sidecar_missing` — No 20260713 context sidecar found

---

## B01-001 Successfully Retrieved ✅

**Status:** Completed successfully (context sidecar: `eval-run-graphont-test-B01-001-20260714-0159-contexts.json`)

**Results:**
- GT clauses: `1.2.1`, `1.4.1`
- Retrieved: 8 Response to Feedback sections (2.2, 2.13, 8.10, 13.12, 2.1, 2.5, 2.15, 2.9)
- **No match** — all retrievals are off-target Response to Feedback sections, not the decisive CCoP 2.0 §1.2.1/§1.4.1 clauses

**Analysis:** This case (healthcare/MRI CII designation) requires the exact CCoP 2.0 §1.2.1 (CII definition) and §1.4.1 (applicability scope) clauses. Graphont retrieved Response to Feedback clarifications instead, suggesting the query→concept extraction is surfacing ancillary clarifications rather than the core definitional clauses.

---

## Empty Retrievals

**No empty retrievals detected.** All 17 completed cases returned exactly 8 retrieved clauses (pool size = 8 consistently).

---

## Clause ID Normalization Rule

To match retrieved `citation_id`s against GT `clause_reference` values, the following normalization is applied:

1. **Strip document prefix** — Remove everything before and including `::`
   - `"CCoP 2.0::5.7.2(b)"` → `"5.7.2(b)"`
   - `"CCoP Response to Feedback::11.19"` → `"11.19"`
   - `"Security By Design::AnnexC"` → `"AnnexC"`

2. **Strip definition suffix** — Remove everything from `#` onwards
   - `"1.2.1#remote access"` → `"1.2.1"`

3. **DO NOT strip subsection letter in parens** — Lettered sub-clauses are DISTINCT entries
   - `"5.7.2(b)"` stays as `"5.7.2(b)"` (not collapsed to `"5.7.2"`)
   - `"3.2.2(a)"` stays as `"3.2.2(a)"` (distinct from `"3.2.2"`)
   - Rationale: `clause_inventory.json` treats lettered sub-clauses as separate entries

4. **Trim whitespace**

**Rationale:** Pure format mismatches (e.g., `CCoP 2.0::5.3.1` vs `Section 5.3.1` vs bare `5.3.1`) MUST NOT be counted as misses. However, semantic distinctions (e.g., `3.2.2` vs `3.2.2(a)`) MUST be preserved. The normalization rule above ensures both invariants hold.

**Verification:** Cross-checked against `src/rag/ingestion/fixtures/clause_inventory.json` (883 entries, 738 unique clause_ids). The normalized format matches the inventory format for both lettered and non-lettered sub-clauses.

---

## Detailed Per-Case Analysis

### Cases with successful retrieval (4/17):

**B02-001** (Compliance Classification)
- GT: `["5.7.2"]`
- Retrieved: `CCoP 2.0::5.7.2(b)`, `CCoP 2.0::5.7.2`, `CCoP Response to Feedback::11.19`, etc.
- **Match:** `5.7.2` found in pool
- Recall: 1.00

**B04-001** (IT/OT Classification Boundary)
- GT: `["1.2.1"]`
- Retrieved: Multiple CCoP 2.0 and Response to Feedback citations
- **Match:** `1.2.1` found (from `CCoP 2.0::1.2.1#operational technology`)
- Recall: 1.00

**B09-001** (Risk Identification / Residual Risk)
- GT: `["3.2.2(a)"]`
- Retrieved (8): `CCoP 2.0::3.2.2(a)`, `CCoP 2.0::3.2.2`, `CCoP Response to Feedback::5.6`, `CCoP 2.0::1`, `CCoP Response to Feedback::11.46`, `CCoP 2.0::5.9.1`, `CCoP Response to Feedback::2.3`, `CCoP Response to Feedback::8.14`
- Normalized retrieved: `3.2.2(a)`, `3.2.2`, `5.6`, `1`, `11.46`, `5.9.1`, `2.3`, `8.14`
- Match: `3.2.2(a)` (from `CCoP 2.0::3.2.2(a)`)
- Recall: 1.00 (1/1)
- Note: this case was a hidden miss in the original report — the asymmetric normalizer (`if "::" in str(gc)`) was stripping parens from retrieved but not GT, causing `3.2.2(a)` to never match itself. Fixed in v2.

**B10-001** (Risk Justification Coherence)
- GT: `["4.1.1", "4.1.2"]`
- Retrieved: `CCoP Response to Feedback::5.6`, `CCoP 2.0::4.1`, `CCoP 2.0::4.1.1`, etc.
- **Match:** Only `4.1.1` retrieved; `4.1.2` not in pool
- Recall: 0.50 (1/2 GT clauses retrieved)

### Cases with no retrieval match (13/17):

13 out of 17 cases with GT clauses failed to retrieve any decisive clause. This indicates a systematic retrieval quality issue in the current graphont implementation, not random noise.

**Hypothesis (for next phase):** The low recall suggests that the current graphont retrieval may be:
1. Retrieving topically-related but not semantically-matching clauses
2. Missing key bridging concepts in the query→concept extraction
3. Ranking high-confidence but off-target clauses (e.g., OT/access controls instead of scope/applicability)

---

## Environment & Prerequisites

**Confirmed:**
- ✅ Neo4j healthcheck cleared (reachable at `http://localhost:7474`)
- ✅ Qdrant stopped (per memory-savings instruction)
- ✅ GT directory confirmed: `audit-20260629-1245`
- ✅ RAGAs disabled (`CCOP_RAGAS_ENABLED=false`)
- ✅ Zero pipeline/corpus changes
- ✅ Extractor lives outside `src/rag/` (standalone script)

**Run parameters:**
- `--model primus-reasoning`
- `--mode graphont`
- `--verbose-io` (captures context sidecars)
- One process per case (memory safety)
- `--resume` flag used for early cases, then removed for forced fresh runs

---

## Artifacts

**Context sidecars:** `src/results/evaluations/2026-07/eval-run-graphont-test-*-*contexts.json` (18 files)

**Run logs:** `.planning/phases/12-agentic-graphont-retrieval-quality-loop/logs/` (all attempts persisted)

**Extractor script:** `.planning/phases/12-agentic-graphont-retrieval-quality-loop/extract-baseline-recall.py`

**Raw results JSON:** `.planning/phases/12-agentic-graphont-retrieval-quality-loop/baseline-recall-results.json`

---

## Next Steps

1. **Reviewer verification** — Independent verification of normalization rule + recall math
2. **Slice A/B/C planning** — Design improvements based on this baseline (target: 50% recall for finetuned phase, 85% for deployment)

**Threshold context:**
- Baseline threshold: 15% (current: 20.6% — passing)
- Finetuned threshold: 50% (current: 20.6% — 2.4x improvement needed)
- Deployment threshold: 85% (current: 20.6% — 4.1x improvement needed)

The baseline passes the 15% threshold. Significant retrieval improvements are still required to reach finetuned (2.4x) and deployment (4.1x) thresholds.
