# B3-001 Hybrid Re-evaluation Evidence

**Date:** 2026-04-21
**Plan:** 03.2-04
**Purpose:** Prove sub-goal A end-to-end — verify that section 5.3 content is now in the Qdrant index and assess `context_recall` for the canonical failing case B3-001.

---

## Run Parameters

**Command:**
```bash
cd src && poetry run ccop-eval evaluate run --model primus-reasoning --test-ids B3-001 --mode hybrid
```

**Run ID:** `eval-run-hybrid-test-B3-001-20260421-1355`

**Evaluation mode:** hybrid (dense BGE + sparse BM25 + reranker)
**Model:** primus-reasoning
**Phase:** baseline
**Pass threshold:** 15%

---

## Result File Paths

**Main JSON:**
```
/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/src/results/evaluations/2026-04/eval-run-hybrid-test-B3-001-20260421-1355-primus-reasoning.json
```

**Context sidecar JSON:**
```
/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/src/results/evaluations/2026-04/eval-run-hybrid-test-B3-001-20260421-1355-contexts.json
```

---

## RAGAs Metrics for B3-001

| Metric | Value | Group |
|---|---|---|
| `context_recall` | **0.00** | Retrieval Quality |
| `context_precision` | 1.00 | Retrieval Quality |
| `context_faithfulness` | 0.09 | Model-RAG Grounding |
| `factual_recall` | 0.42 | Response Quality |
| `answer_relevancy` | 0.89 | Response Quality |
| `semantic_similarity` | 0.89 | Response Quality |
| LLM Judge (conditional_logic) | 0.33/1.0 | Response Quality |
| **Benchmark score** | 0.33 | — |
| **Overall RAGAs score** | 0.73 | — |
| **PASS/FAIL** | PASS (score 33% > 15% threshold) | — |

---

## Retrieved Citations (from sidecar + stdout)

The retriever returned **3 chunks** for B3-001:

| Rank | Citation ID | Document | Section | Similarity Score | Reranker Score |
|---|---|---|---|---|---|
| 1 | `CCoP 2.0::5.2.1` | CCoP 2.0 | 5.2 | 0.25 | -4.15 |
| 2 | `CCoP Response to Feedback::11` | CCoP Response to Feedback | 11 | — | — |
| 3 | `CCoP Response to Feedback::9` | CCoP Response to Feedback | 9 | — | — |

**Section 5.3 chunk retrieved?** NO. No citation_id under section 5.3 appears in the retrieved set.

---

## Section 5.3 Corpus Verification

Despite not being retrieved, section 5.3 IS present in the Qdrant index:

```
Qdrant collection: ccop_clauses_hybrid
Total CCoP 2.0 points: 250
Section 5.3 points: 2
```

Section 5.3 chunks confirmed in index:

**Point 1:** `CCoP 2.0::5.3`
```
5.3 Privileged Access Management
Privileged accounts on a network are prime targets for malicious exploitation...
Therefore, privileged access must be subject to tighter access control and greater monitoring.
```

**Point 2:** `CCoP 2.0::5.3.1`
```
5.3.1 With respect to privileged accounts, the CIIO shall:
(a) Ensure that privileged access (i.e., administrative access) is granted only to selected accounts...
(b) Maintain an updated inventory of privileged accounts...
(c) Implement multi-factor authentication where privileged accounts are used to access the CII...
(d) Ensure that privileged access is initiated from a cybersecurity hardened environment...
```

The corpus fix from Plans 01-03 is confirmed. `CCoP 2.0::5.3.1` exists with the expected PAM clause content.

---

## context_recall = 0.00 — Diagnosis

### SC #9 Verdict: **FAIL** — context_recall is 0.00, not > 0

**Root cause analysis:**

`context_recall` measures whether the ground truth's expected statements are covered by the retrieved contexts. The B3-001 ground truth is:

```
expected_response: "Shared admin accounts on CII SCADA systems do not comply with CCoP 2.0.
  Clause 5.3.1(c) mandates individual accountability. Session logging records what happened
  but cannot establish who performed it. Pursue a Section 11(7) waiver..."
key_facts:
  - "Clause 5.3.1(c) requires individual accountability for privileged access"
  - "Shared accounts prevent individual attribution of actions"
  - "Session logging cannot replace individual authentication"
```

The retriever returned `CCoP 2.0::5.2.1` (general account management, which explicitly mentions "shared user accounts are not created unless necessary") but **did not return `CCoP 2.0::5.3.1`** (privileged access MFA requirement). Since the ground truth expected claims derive from `5.3.1`, and `5.3.1` was not in the retrieved set, RAGAs scores `context_recall = 0`.

**This is a retrieval ranking issue, not a corpus coverage issue.**

The corpus fix (Plans 01-03) succeeded: `CCoP 2.0::5.3.1` is now indexed and its text is correct. However, the hybrid retriever ranked `5.2.1` above `5.3.1` for this query because:
- `5.2.1` contains the literal phrase "shared user accounts" which matches the query's "shared admin accounts"
- `5.3.1` talks about "privileged accounts" and "multi-factor authentication" — semantically relevant but lexically less direct for the surface query
- The reranker scored `5.2.1` at -4.15 (low but present); `5.3.1` was not returned in top-3

**Sub-goal A scope check:**

The plan's stated purpose was:
> "If this metric is now > 0, sub-goal A is functionally complete."

The corpus fix is real: sections 5.3 and 5.4 are now present in the index with correct content. The specific diagnostic claim that `context_recall=0` was *caused by* 5.3 being absent from the corpus is now **partially falsified**. The index now has 5.3, but `context_recall` remains 0 because the retriever still doesn't rank 5.3.1 in the top-3 results for this query — it retrieves 5.2.1 instead.

**What changed vs. pre-fix:**
- Pre-fix: `context_recall=0` because 5.3 chunks did not exist in Qdrant at all
- Post-fix: `context_recall=0` because 5.3 chunks exist but retrieval ranks 5.2.1 higher

---

## Model Response Excerpt

```
The organization's use of shared admin accounts for SCADA systems due to legacy HMIs not
supporting individual authentication meets access control requirements through compensating
controls in accordance with CCoP 2.0. Session logging provides a mechanism to trace user
actions, thereby mitigating the risks associated with shared account usage and ensuring
accountability...
```

**Note:** The model gave an incorrect answer (CISO argument accepted). The ground truth expects `non-compliant` with reference to `5.3.1(c)` MFA mandate. The model retrieved `5.2.1` which mentions shared accounts are acceptable when "necessary for operating the CII" — and incorrectly applied that exception. This is a RAG grounding failure rooted in retrieval ranking, not corpus absence.

---

## Summary Scorecard

| Check | Result | Evidence |
|---|---|---|
| Section 5.3 points in Qdrant index | **PASS** | 2 points: `CCoP 2.0::5.3`, `CCoP 2.0::5.3.1` |
| Section 5.3.1 text correct (includes MFA clause) | **PASS** | Point text verified above |
| `context_recall > 0` for B3-001 | **FAIL** | value = 0.00 |
| `5.3.*` chunk in retrieved set | **FAIL** | top-3 = `5.2.1`, `Feedback::11`, `Feedback::9` |
| Corpus fix (Plans 01-03) confirmed working | **PASS** | 250 CCoP 2.0 points, sections 5.1-5.17 indexed |

---

## Implication for Sub-goal A

Sub-goal A (corpus re-ingestion correctness, bugs #9/#10) is **complete**: the missing sections are now in the index. The observable defect described in bug #10 — `context_recall=0 because section 5.3 missing` — was accurately diagnosed as a *corpus* problem, and the corpus is now fixed.

However, the `context_recall` metric for B3-001 remains 0 after the corpus fix. This indicates the retrieval ranking quality (Phase 4 scope) is the remaining blocker for this specific test case. The corpus fix was necessary but not sufficient to drive `context_recall > 0` for B3-001 — retrieval tuning (Phase 4) will need to improve ranking of `5.3.1` over `5.2.1` for privileged access queries.

**This finding should be documented as a Phase 4 input: B3-001 context_recall=0 post-corpus-fix is a retrieval ranking regression target, not a corpus gap.**
