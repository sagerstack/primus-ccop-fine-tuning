# GT Audit — Scoring-Layer Critique (LLM Judge + RAGAs)

**Date:** 2026-06-29
**Author:** scoring-accuracy review (manual, case-by-case)
**Angle:** Where prior audit docs (01–03) audited *ground-truth clause consistency*, this doc
audits the **scoring layer** — whether the LLM-Judge score and the RAGAs score are reasonably
accurate against question + model answer + ground truth. It surfaces additional GT defects that
are only visible when you read the judge's per-dimension rationale next to the GT.

## Method & sources

- **Hybrid responses (canonical, locked):**
  `src/results/evaluations/2026-04/eval-run-hybrid-tests-18-bdc4927d-20260430-0232-primus-reasoning.json`
  — 18-case stratified run (one case per active benchmark), overall_score 0.494, all 18 passed
  (0.15 baseline threshold). See memory `canonical-hybrid-baseline-run`.
- **Ground truth:** `ground-truth/test-suite/*.jsonl` (`expected_response`, `key_facts`,
  `fail_conditions.forbidden_claims`, `reasoning_chain`).
- **Judge detail:** `test_results[].metrics` (6 dimensions, 0–3 normalised, weight 0.5 each) +
  embedded `_judge_raw` justification. Judge mode: `rubric`.
- **RAGAs detail:** `test_results[].ragas` (grounding / response_quality / retrieval_quality, schema v5).

**Confidence caveat:** n = 1 case per benchmark, single run. Findings about *systematic* judge/RAGAs
behaviour are high-confidence (they recur across all 18). Per-case numbers are directional.

---

## Bottom line

Neither score is trustworthy as-is, for different reasons:

- **RAGAs is not a usable answer-quality signal.** It sits in a narrow 0.7–0.85 band almost
  regardless of correctness — it scored a *wrong-verdict* answer (B22, 0.746) and a *non-answer*
  (B23, 0.714) about the same as genuinely good answers. Demote to retrieval-diagnostics only.
- **The LLM judge is the better signal and directionally tracks quality**, but has three systematic
  flaws (citation verifier, universal `actionable` dimension, occasional rationale instability).
- **Both scorers are contaminated by real ground-truth defects** — a portion of the model's
  "errors" are the benchmark penalising the model for the benchmark's own bugs. This caps the
  achievable accuracy of *any* scorer until the GT is fixed.

---

## Per-case verdict

| Case | Judge / RAGAs | Judge fair? | RAGAs | Dominant issue |
|---|---|---|---|---|
| B01-001 | 0.611 / 0.83 | ~Fair | Inflated | RAGAs `context_recall`=0.75 but scope clauses (§1.2.1/§1.4.1) weren't retrieved |
| B02-001 | 0.444 / 0.758 | **Too harsh** | Inflated | Judge calls `5.1.5` fabricated — but the question stem **and** key_facts use 5.1.5 |
| B03-001 | 0.278 / 0.802 | Fair | Badly inflated | Judge correctly caught infeasible "upgrade HMIs" vs stated constraint |
| B04-001 | 0.444 / 0.807 | ~Fair | Inflated | Caught historian self-contradiction; `actionable=0` harsh for a classification task |
| B05-001 | 0.278 / 0.362 | **GT-broken** | Low (rare agree) | GT says CCoP prescribes complexity; **B06 GT says the opposite** |
| B06-001 | 0.222 / 0.685 | **Too harsh** | Inflated | verdict=0 for "brute-force *and* dictionary"; contaminated `forbidden_claims` |
| B07-006 | 0.5 / 0.83 | **Too harsh** | Inflated | Judge calls `5.2.1(c)` fabricated — **expected_response itself cites 5.2.1(c)** |
| B08-001 | 0.667 / 0.784 | Fair | Inflated | Good answer; RAGAs `faithfulness`=0.08 (absurd) |
| B09-001 | 0.778 / 0.74 | **Invalid test** | n/a | Leaky case: `expected_response` == the question text verbatim |
| B10-001 | 0.5 / 0.9 | Unreliable | Inflated | Judge rationale flip-flops D6 score 2→1→2→1 incoherently |
| B12-001 | 0.5 / 0.777 | ~Fair | Inflated | — |
| B13-001 | 0.611 / 0.752 | ~Fair | Inflated | Citation harshness on real sub-letter clauses |
| B14-001 | 0.556 / 0.665 | Fair | Inflated | RAGAs `faithfulness`=0.0 on a sound answer |
| B18-001 | 0.889 / 0.749 | **Accurate** | Under-rates | Best-calibrated; judge correctly verified all 6 citations |
| B21-001 | 0.611 / 0.848 | **Too harsh** | Inflated | Judge counts honest "None / Not applicable" as 6 fabricated citations |
| B22-001 | 0.389 / 0.746 | **Accurate** | Badly inflated | Model gave wrong verdict (No vs Yes); RAGAs still 0.746 |
| B23-001 | 0.167 / 0.714 | **Accurate** | Badly inflated | Hand-waved out-of-corpus MAS TRM; RAGAs faithfulness 0.88 for a non-answer |
| B24-001 | 0.167 / 0.591 | **GT-broken** | ~ | Judge demands "Section 8.3 / 2-hr" that `expected_response` says doesn't exist |

---

## RAGAs assessment — not reasonably accurate

1. **No discrimination between right and wrong answers.** Wrong-verdict (B22, 0.746) and
   non-answer (B23, 0.714) score the same as good answers. Driven by `answer_relevancy` and
   `semantic_similarity`, which are uniformly high on fluent CCoP prose.
2. **`faithfulness` is broken for reasoning tasks** — 0.0 (B14), 0.06 (B09), 0.08 (B08) on *good*
   answers, because it measures overlap with the thin retrieved context, not correctness. An answer
   that reasons beyond the retrieved snippets is scored "unfaithful" even when correct.
3. **`context_recall` is unreliable** — 0.75 on B01 where the actual scope clauses were not retrieved.
4. **The composite `ragas_score` masks component failures** by averaging across grounding /
   response-quality / retrieval groups.

**Recommendation:** Drop `ragas_score` from any headline/composite. Keep `context_precision`
(and `context_recall`, with caution) as a *retrieval-only* diagnostic. Never display RAGAs next to
the judge score as if comparable.

---

## LLM judge assessment — good signal, three systematic flaws

1. **`citation_correctness` is over-weighted AND its verifier is frequently wrong.** It is the
   single biggest downward driver of scores, yet its clause-existence verification *disagrees with
   the benchmarks' own references*:
   - B02: flags `5.1.5` as fabricated, but the **question stem and `key_facts` both use 5.1.5**.
   - B07: flags `5.2.1(c)` as fabricated, but the **`expected_response` cites `Section 5.2.1(c)`**.
   - B21: scores the model's honest "CCoP 2.0: None / Not applicable" disclaimers as **6 fabricated
     citations** — penalising the *correct* refusal-to-cite behaviour the benchmark wants.
   Root cause: the judge's clause check is not bound to a single authoritative inventory. Fix: bind
   it to `src/rag/ingestion/fixtures/clause_inventory.json` (the same source `validate-ground-truth`
   uses) and treat "no citation / not applicable" as neutral, not fabricated.
2. **`actionable_way_forward` is applied universally to question types that don't warrant it.**
   Classification (B04), yes/no compliance (B02), definitional "why" (B06) all receive
   `actionable=0` by construction. This is a side-effect of routing every benchmark through one
   universal rubric (commit `cf72ce1`). Fix: make this dimension conditional on question type, or
   exclude it from the denominator where not applicable.
3. **Occasional rationale instability.** B10's justification visibly oscillates on the same
   dimension (D6: 2→1→2→1) and lands arbitrarily. Low frequency but means per-dimension numbers are
   not always reproducible. Mitigation: lower judge temperature for the scoring pass, or
   self-consistency vote on the citation dimension.

Where the judge is clean (B18, B22, B23) it tracks reality well — it caught a genuinely wrong
verdict (B22) that RAGAs entirely missed. **The judge is the signal to trust, after the above fixes.**

---

## Ground-truth defects (root cause — caps every scorer)

These are new findings surfaced by the scoring-layer read. Some overlap the prior audit
(01–03); cross-references noted.

| ID | Severity | Defect | Cases | Notes |
|---|---|---|---|---|
| S-1 | **Critical** | **Cross-benchmark contradiction** on whether CCoP prescribes password complexity | B05 vs B06 | B05 GT: prescribes 8-char + complexity ("5.2.2"). B06 GT: does *not* prescribe, defers to NIST. Mutually exclusive. Model's B05 answer matches B06's GT, scored 0.278. Overlaps prior B05/B06 §3.8 work in `03_agent2_audit.md`. |
| S-2 | **Critical** | **Within-case `expected_response` vs `key_facts` contradiction** | B24, B02 | B24 expected: Code defines no hour-count deadlines; key_facts assert 2-hr/24-hr Form A2/A1 — judge sided with key_facts to penalise. B02 expected cites `5.7.2(b)`; key_facts cite `5.1.5`. |
| S-3 | **High** | **`forbidden_claims` contaminated with required-element criteria** | B05, B06, B07, B09, B10, B12, B13, B14, B22 | Entries like "Reference to applicable CCoP clause", "The security intent of the control", "Specific evidence types required" are *required* elements wrongly placed in the forbidden list. Schema/data bug — likely a generation-template field swap. |
| S-4 | **High** | **Invalid/leaky test case** — `expected_response` is a verbatim copy of the question | B09 | Answer is embedded in the prompt; score is meaningless. Drop or rewrite. |
| S-5 | Medium | **Out-of-corpus expectation** — question requires MAS TRM content not in the 7-doc corpus | B23 | Cross-regulator benchmark cannot be answered from corpus; either ingest the second regulator or reframe the GT as "maintain parallel compliance" only. |

Note: B22 (waiver) is **not** a GT defect — the model genuinely gave the wrong verdict (No vs
"Yes, with compensating controls"); judge correct.

---

## Implications for the GraphRAG spike (decision-relevant)

**A clean GraphRAG-vs-hybrid A/B cannot run against this ground truth yet.** A graph that retrieves
the *correct* clause would still be marked down where the judge's citation verifier or the
contaminated GT disagrees — the measured delta would be GT noise, not retrieval quality.

Recommended order before any spike A/B:

1. **Fix GT defects** S-1..S-4 on at least the spike's target benchmarks (B03/B04/B23 + the B05/B06
   password contradiction). Dedupe `forbidden_claims`, reconcile expected-vs-key_facts, drop/repair B09.
2. **Repair the judge** — bind citation verification to `clause_inventory.json`; make
   `actionable_way_forward` conditional on question type.
3. **Demote RAGAs** to a retrieval-only diagnostic; remove from headline composite.
4. **Then** run the spike A/B.

## Suggested next step

Resolve **S-1** first (B05 vs B06 password complexity) against the CCoP 2.0 PDF
(`ccop-official/CCoP---Second-Edition_Revision-One.pdf`) + `RESPONSE-TO-FEEDBACK.pdf` — it is the
cleanest factual resolution and unblocks the rest of the password-area benchmarks (B05/B06/B14).
