# Research: CRAG Techniques Applicable to CCoP Graphont-Agentic Retrieval

**Date**: 2026-07-23
**Researcher**: pi team lead
**Status**: Final

---

## 1. Executive Summary

- CRAG's core controller is a **three-way retrieval-set decision**—Correct, Incorrect, or Ambiguous—not simply per-document filtering.
- Its strongest immediately applicable mechanisms are: (1) three-way action routing, (2) neutral keyword query rewriting, (3) decompose-filter-recompose knowledge refinement, and (4) selecting corrected evidence rather than appending everything.
- For this closed regulatory corpus, CRAG's web-search fallback should be adapted to a **closed-corpus alternate retrieval action**: rewritten BM25+dense retrieval, typed graph expansion, and direct authoritative clause lookup—not unrestricted web search.
- The B01 failure matches CRAG's motivating failure exactly: topically relevant but misleading controls overwhelmed the answer. Widening and retaining more related clauses is not correction.
- **Recommendation:** implement a three-way aggregate controller plus neutral keyword rewrite first; then add sentence/strip refinement. Do not train a custom evaluator or add external web search yet.

## 2. Problem Statement

Investigate CRAG's actual mechanisms beyond HyDE and determine which can improve `graphont-agentic` retrieval accuracy in a closed CCoP corpus. Success means increasing decision-relevant clause availability and reducing misleading context, while preserving deterministic, bounded execution and avoiding runtime ground-truth use.

## 3. What CRAG Actually Does

CRAG evaluates each query-document pair, aggregates those scores into one of three actions, and then changes the knowledge source/processing strategy:

1. **Correct**: at least one retrieved document exceeds an upper relevance threshold. Refine the internal retrieved documents.
2. **Incorrect**: all retrieved documents fall below a lower threshold. Discard them and obtain replacement knowledge using a rewritten query and web search.
3. **Ambiguous**: confidence lies between the two thresholds. Combine refined internal knowledge with selected external knowledge.

CRAG's knowledge refinement is **decompose → score/filter strips → recompose**. Long passages are split into independently meaningful few-sentence strips; the evaluator scores the strips, irrelevant strips are removed, and retained strips are concatenated in original order.

CRAG's corrective search rewrites the question into at most three keyword-oriented search terms containing both topic background and main intent. Search results are not copied wholesale: content is segmented and selected using the same relevance evaluator.

The paper reports that removing refinement, rewriting, or external knowledge selection reduced PopQA accuracy for both CRAG generator configurations. It also reports that its fine-tuned T5-large evaluator reached 84.3% evaluator accuracy on PopQA versus 58.0% for direct ChatGPT, 62.4% for ChatGPT-CoT, and 64.7% for few-shot ChatGPT. These are PopQA-specific results, not direct evidence that the same evaluator or thresholds transfer to regulatory clauses.

## 4. Techniques to Try in This Project

### 4.1 Three-way aggregate action routing — highest priority

Replace the current single action (`keep score >= 1`) with a retrieval-set decision:

```text
CORRECT:
  essential evidence exists and evidence coverage is sufficient
  → refine/select internal pool only

INCORRECT:
  no essential evidence and pool is uniformly weak
  → discard the initial pool; run a corrective closed-corpus query

AMBIGUOUS:
  mixed essential/related evidence, conflicting evidence, or incomplete coverage
  → refine initial evidence + corrective retrieval; merge and select
```

This is more faithful to CRAG than the current implementation. Current `graphont-agentic` always follows one path: filter then generate.

### 4.2 Neutral keyword query rewriting — high priority

Use CRAG's keyword rewrite rather than answer-shaped HyDE for corrective retrieval. For B01, an appropriate neutral rewrite would resemble:

```text
digital boundary, CCoP applicability scope, enterprise network
```

It should not assert the answer. This avoids the observed HyDE drift where the hypothetical clause asserted that connected enterprise systems should comply.

Run the rewrite only on Incorrect/Ambiguous routes, not every query.

### 4.3 Closed-corpus corrective search — high priority

CRAG uses external web search because its source corpus can be insufficient. This project has a fixed authoritative corpus, so substitute:

```text
rewritten query
  → BM25 + dense search across complete clause inventory
  → typed graph expansion / bridge retrieval
  → direct authoritative source lookup
  → joint reranking and provenance-preserving map-back
```

For Incorrect, discard the bad initial pool rather than appending the corrective results. The B01 pool-widening experiment showed that appending operational controls can make the answer worse.

For Ambiguous, combine refined original evidence with selected corrective evidence, as CRAG does.

### 4.4 Decompose-filter-recompose refinement — high priority

Apply refinement to long CCoP Response-to-Feedback passages, definitions, supplementary guidance, and multi-obligation chunks:

1. Split into sentence/few-sentence strips.
2. Score each strip for exact decision support.
3. Remove unrelated strips.
4. Recompose retained strips in original order, preserving citation/provenance.

This is especially relevant to B01: Response-to-Feedback 11.25 contains a highly useful sentence stating that the corporate network is not covered, surrounded by wireless-network detail. Strip selection can retain the scope sentence without carrying the whole tangent.

Short atomic CCoP clauses should remain intact unless they contain separable conditions/exceptions.

### 4.5 Strict evidence selection after correction — high priority

CRAG selects/refines both internal and searched knowledge. Our current controller retains evaluator scores 1 and 2, preserves retrieval order, and caps afterward. A better selection policy is:

```text
score 2 (decision-essential) before score 1 (related)
retrieval rank as tie-breaker
coverage/diversity constraints
primary-context top-k cap
```

Related operational controls should not crowd out applicability, definition, condition, exception, or boundary evidence.

### 4.6 Ambiguous-route evidence blending — medium priority

When the evaluator cannot confidently declare retrieval correct or incorrect, blend:

- refined essential/related strips from the initial pool;
- selected results from the corrective rewritten query.

Bound the merged pool, deduplicate by citation/strip, and rerank jointly. CRAG's ablation indicates the Ambiguous route improves robustness relative to a hard binary switch.

### 4.7 Dataset/family-specific threshold calibration — medium priority

CRAG used different upper/lower thresholds across PopQA, PubHealth/ARC, and Biography. This supports calibrating action thresholds by benchmark/query family rather than assuming one universal cutoff.

For this project, calibrate on disjoint cases and freeze thresholds before held-out evaluation. Do not use ground truth during runtime.

### 4.8 Fine-tune a lightweight evaluator — later, high cost

CRAG fine-tuned T5-large on positive/negative retrieval pairs and found it outperformed prompted ChatGPT on PopQA. A CCoP-specific evaluator could be trained from audited question-clause pairs plus hard negatives.

Do this only if prompt/evaluator calibration, action routing, and refinement fail. The paper explicitly notes fine-tuning the external evaluator as a limitation, and its reported evaluator accuracy is dataset-specific.

### 4.9 Self-CRAG-style generator criticism — later

CRAG was integrated with Self-RAG, whose critic decides whether retrieval is needed and which documents should be referenced. An analogous future extension could perform pre-generation evidence sufficiency and post-generation citation/claim verification.

This is beyond CRAG's lightweight core and adds latency/complexity; defer until retrieval correction is working.

## 5. Comparative Analysis

| Technique | Expected benefit here | Risk/cost | Priority |
|---|---|---|---|
| Three-way action gate | Stops treating all weak/mixed pools the same | Requires calibrated aggregate rules | 1 |
| Neutral keyword rewrite | Recovers scope terminology without HyDE verdict drift | Query drift still possible | 1 |
| Closed-corpus replacement search | Corrects bad pools without untrusted web content | Must preserve provenance | 1 |
| Strip refinement | Removes tangential content inside long passages | Extra evaluator calls; clause splitting risk | 1 |
| Score-aware + diverse selection | Prevents related controls crowding out essentials | Needs coverage taxonomy/tie-breaks | 1 |
| Ambiguous blending | More robust than hard keep/discard | Can increase context unless bounded | 2 |
| Family-specific thresholds | Better action accuracy | Calibration data requirements | 2 |
| Train T5 evaluator | Potentially more consistent relevance judgments | Training/maintenance/transfer risk | 3 |
| Generator self-critique | Detects evidence/answer mismatch | High latency and complexity | 3 |

## 6. Recommendation

Implement this bounded CRAG adaptation next:

```text
retrieve pool
  → per-clause evaluator
  → aggregate Correct / Incorrect / Ambiguous

Correct:
  decompose/refine internal evidence

Incorrect:
  neutral keyword rewrite
  → closed-corpus replacement retrieval
  → refine/select

Ambiguous:
  refine initial evidence
  + rewritten closed-corpus retrieval
  → merge/deduplicate/select

all routes:
  essential-first selection
  → primary top-k
  → generate
```

Start with one correction maximum. Persist action, original pool, rewritten query, corrected pool, per-strip scores, selected evidence, and stop reason.

## 7. Limitations

- CRAG's experiments used general QA/biography/health/science datasets, not regulatory interpretation.
- Its web-search action is inappropriate as-is for a fixed authoritative compliance corpus.
- Its reported evaluator advantage comes from a fine-tuned T5-large model; our prompted evaluator is mechanically different.
- Strip refinement helps long noisy passages but cannot correct a whole atomic clause that is topically related yet legally conditional.
- Three-way thresholds were empirically dataset-specific in CRAG; they cannot be copied directly.

## 8. Immediate Experiment for B01

Without running generation:

1. Capture all 20 candidate citations and evaluator scores.
2. Aggregate retrieval as Correct/Incorrect/Ambiguous using experimental rules.
3. On Ambiguous/Incorrect, generate a neutral three-keyword rewrite.
4. Retrieve 20 corrected candidates without HyDE.
5. Refine long Response-to-Feedback passages into strips.
6. Select score-2 evidence first, then score-1 only for missing coverage.
7. Measure whether `1.2.1`, `1.4.1`, or valid scope proxies (`2.1`, `2.2`, `11.25`) enter the final top-8.

Primary metric: final decision-relevant recall/coverage. Do not use answer score to tune this stage.

## 9. References

- [Corrective Retrieval Augmented Generation](https://arxiv.org/html/2401.15884v3) — arXiv v3, 2024-10-07 — primary paper; three-way actions, refinement, rewriting/search, experiments and ablations.
- [HuskyInSalt/CRAG](https://github.com/HuskyInSalt/CRAG) — official implementation repository, retrieved 2026-07-23 — implementation modes for refinement, query rewriting/search, ambiguous knowledge combination.
- Local copy: `research/agentic-rag/CRAG.pdf` — fully extracted/read during this research session.
