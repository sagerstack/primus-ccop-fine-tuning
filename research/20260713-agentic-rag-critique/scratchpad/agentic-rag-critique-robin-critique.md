# P2 Cross-Review: Robin’s Critique of Roberto’s P1 Artifact

**Date:** 2026-07-13  
**Reviewer:** Robin  
**Artifact reviewed:** `scratchpad/agentic-rag-critique-roberto.md`  
**Scope:** approach, methodology, evidence quality, accuracy, gaps, and recommendations

---

## Overall assessment

Roberto’s artifact is strong on two concrete design failures: **`weak-focus → retry_wider` is poorly motivated**, and unfiltered graph expansion risks **hub/topology drift**. It also correctly emphasizes full-chain retrieval, thin calibration data, incomplete silver labels, legacy-mode isolation, and the value of a bounded/auditable controller.

However, its headline—“the overall approach … matches 2026 best practice”—is not supported by its own analysis. Later sections say query-agnostic expansion is behind the frontier and recommend answer-grounding signals that the proposed pre-generation/no-extra-LLM architecture cannot compute. The defensible conclusion is narrower: **Phase 12 is a sound, low-risk corrective baseline, but not current agentic/graph-RAG best practice.**

The most consequential methodological problem is over-generalizing TASR, a *post-generation iterative stopping* study, into rules for a *pre-generation weak-retrieval detector*. TASR supports caution around topicality scores and uncontrolled OR rules, but it does not establish that Phase 12 should invert its detector to an AND gate or use answer/citation grounding as its primary runtime signal.

---

## 1. Approach: strengths

1. **Good project-specific focus.** The critique is not a generic RAG survey. It connects the detector and expansion policy to the local reranker behavior, the CII hub, the existing rarity gate, D6, and the B01 multi-document chain.
2. **Correctly distinguishes recall recovery from reranking.** The bounded-recall observation is directly relevant: a reranker cannot recover clauses absent from its candidate pool.
3. **Correctly identifies action-policy mismatch.** `weak-focus → retry_wider` deserves challenge because widening can add distractors. A prune/diversify/rerank action is an important comparator.
4. **Correctly protects evaluation integrity.** Offline-only GT, adjudication/pooling, a full-chain metric, and causal tracing from retry to later citation are all high-value recommendations.
5. **Correctly values determinism without romanticizing it.** The artifact recognizes auditability and hard budgets as virtues in a compliance setting.

These points should survive into the merged artifact.

---

## 2. Approach: major issues

### 2.1 “Matches 2026 best practice” is internally inconsistent and too strong

The artifact simultaneously claims that the architecture is “squarely in the mainstream” and that its query-agnostic expansion is “already behind the frontier.” It also describes only a fixed gate and fixed route table, whereas 2026 agentic systems typically add query decomposition/reformulation, evidence-sufficiency verification, adaptive action choice, and trajectory-aware stopping.

The most directly applicable missing source is [A2RAG](https://arxiv.org/abs/2601.21162), updated 2026-06-04. It uses:

- stage-wise evidence-sufficiency checks;
- monotonic local → bridge → global/PPR escalation;
- relation seeding;
- map-back to provenance text under extraction loss;
- answer-level relevance/grounding/adequacy verification; and
- failure-conditioned rewriting with bounded retries.

Phase 12 shares the budgeted escalation idea, but lacks most of those mechanisms. A2RAG therefore supports **“directionally aligned, intentionally minimal v1,” not “matches best practice.”**

The artifact should also use [RAGSearch](https://arxiv.org/abs/2604.09666) to frame agentic search more precisely: graph structure remains valuable for complex multi-hop cases, while strong agentic dense retrieval can narrow the gap. This argues for comparing graph expansion against wider hybrid+rereanking—not presuming the graph retry is the preferred correction.

### 2.2 The TASR analogy is useful but overextended

TASR’s actual policy stops iterative retrieval when:

1. the generated answer repeats across rounds; **and**
2. an isotonically calibrated answer-token logit margin clears a threshold.

It requires generation each round, cannot fire at round one, and optimizes when to stop revealing more already-ranked passages. Phase 12 instead wants to classify the first retrieval *before generation* using retrieval telemetry and then choose a correction. These are different targets, states, and action spaces.

Therefore:

- TASR’s finding that reranker scores are poor **answer-correctness stopping signals** does not prove they are poor **retrieval-weakness predictors**.
- TASR’s OR-subset failure does not justify globally replacing Phase 12’s OR detector with AND. In Phase 12, `not retrieval_succeeded OR empty` are legitimate hard-failure sentinels. An AND gate could suppress obvious failure.
- The correct recommendation is a **two-level rule**: OR over hard failures; calibrated combination/consensus over soft score signals.

ScoreGate’s evidence should be reconciled rather than placed beside TASR without a target distinction. [ScoreGate](https://arxiv.org/abs/2606.14269) suggests bi-/cross-encoder scores can adapt retrieval cardinality. TASR suggests those same scores do not certify downstream answer correctness. The synthesis is: **score telemetry may be useful for deciding “retrieve more,” but cannot be treated as evidence sufficiency or answer support without local held-out calibration.**

### 2.3 The P0 answer/citation-grounding recommendation is not implementable in the proposed loop

The artifact says to “lead the detector with an answer/citation-grounding signal” and make a proxy for final-citation presence primary, then acknowledges in Open Questions that such a signal may not be computable pre-generation.

This is a central contradiction. The plan’s proposed runtime gate occurs before generation and forbids an extra LLM. Final citations, answer stability, answer-token logits, and entailment against an answer do not yet exist. They can be:

- offline diagnostics;
- a future post-generation verification loop; or
- runtime signals only if the architecture accepts a draft-generation/verification call.

They cannot be P0 requirements for the existing v1. The merged recommendation should instead lead with **pre-generation evidence features**: normalized score distributions, channel agreement, concept/relation coverage, source diversity, connectedness, and provenance-text availability. It should explicitly move final-citation presence to offline evaluation.

### 2.4 One retry is a hypothesis, not an evidence-backed optimum

Roberto labels the single retry “sound” using TASR/BCAS, but those sources support budgets generally, not the exact cap of one for CCoP. [AgenticRAGTracer](https://arxiv.org/abs/2602.19127) reports both premature collapse and over-extension. A2RAG uses multiple bounded stages and typically small 2–3 controller retries, although its experiments are limited.

A better conclusion is:

- one retry is a prudent production default for v1;
- evaluate caps 0/1/2 on held-out cases;
- report marginal utility, harmful-retry rate, and p95 latency;
- promote beyond one only if evidence supports it.

### 2.5 `weak-focus → wider` is risky, but “design error” is too categorical

The direction of Roberto’s criticism is right. Yet a wider *candidate pool followed by a stronger rerank* can sometimes improve top-context focus by introducing better candidates that were previously absent. The action should not be condemned purely from intuition.

The stronger recommendation is an offline **action-oracle matrix**: run no retry, wider+rerank, prune/diversify, and graph expansion for every detector-positive calibration case. Select routes from conditional utility. This also exposes whether `weak-recall` and `weak-focus` can be distinguished reliably at runtime.

---

## 3. Methodology and evidence quality

### 3.1 Search breadth and freshness are good

The artifact retrieved a broad 2026 set spanning gating, stopping, graph traversal, adaptive routing, evaluation, and compliance-adjacent systems. It seeks disconfirming evidence and does not rely only on the named foundational papers. This meets the spirit of search-first research.

### 3.2 Source maturity needs to be made explicit

Several headline sources are very recent preprints or workshop papers:

- TASR is a KDD 2026 workshop paper/preprint;
- ScoreGate is a June 2026 preprint with 200 MS MARCO queries and an internal n=300 benchmark;
- CatRAG/DOTRAG and several uncertainty papers are early 2026 work.

The artifact repeats “zero false positives” for ScoreGate without emphasizing **zero observed** false positives, the internal dataset, or the reported confidence-bound limitations. It also transfers TASR’s findings from QA stopping to compliance retrieval gating too confidently.

The merged report should grade evidence:

- peer-reviewed primary source;
- accepted conference/workshop;
- arXiv preprint;
- vendor/production guide;
- small/internal benchmark.

Reported metrics should be accompanied by dataset size and generalization caveats.

### 3.3 Unsupported or weakly supported claims

- “LangGraph/Milvus production guides, Jun 2026” are mentioned but not listed in References.
- The CII hub count and report-specific reranker behavior are not cited inline to the local report/plan.
- “SOTA” is used for HippoRAG/PPR without defining the task, benchmark, or comparison class. HippoRAG 2 combines PPR with deeper passage integration and online LLM recognition memory; PPR alone is not what its result validates.
- “The plan’s Slice 3 gate is a faithful … instantiation” overstates fidelity. Original CRAG uses a trained T5-large evaluator and Correct/Incorrect/Ambiguous actions with refinement and external search. The 2026 [CRAG reproduction](https://arxiv.org/abs/2603.16169) further shows entity-alignment and domain-transfer weaknesses. Phase 12 borrows the gate/correct concept, not the mechanism.

### 3.4 References do not fully meet the research-methodology format

The methodology skill requests published/updated `YYYY-MM-DD` dates and relevance notes. Many references provide only a year/month, and some labels are ambiguous (for example, “ScoreGate/CAR” conflates distinct works). This is repairable but matters for a freshness-sensitive 2026 report.

### 3.5 Missing disconfirming sources

Roberto should have searched and incorporated:

- [BRINK / What Breaks Knowledge Graph based RAG?](https://aclanthology.org/2026.eacl-long.114/) — graph incompleteness, retrieval versus reasoning failures, and the danger of assuming expansion can traverse a missing path.
- [WildGraphBench](https://arxiv.org/abs/2602.02053) — graph aggregation helps moderate multi-source synthesis but can lose fine-grained details.
- [Why Neighborhoods Matter](https://arxiv.org/abs/2605.15109) — final citations can omit behaviorally relevant traversal context; provenance should include paths/visited context, not only final cited clauses. This is a small workshop study and should be caveated.
- [Completing Missing Annotation / DREAM](https://arxiv.org/abs/2602.06526) — 29,824 missing relevant chunks changed retriever rankings and RAG conclusions; directly strengthens the silver-oracle warning.
- [Coverage, Not Averages](https://arxiv.org/abs/2604.20763) — semantic/benchmark stratification and coverage gaps.

These sources would make the graph-risk and evaluation-integrity sections more balanced.

---

## 4. Content accuracy and gaps

### 4.1 CRAG/HippoRAG/Adaptive-RAG alignment needs a mechanism table

The artifact treats the named bases as stronger validation than warranted:

- **CRAG:** trained evaluator + three-way corrective action; Phase 12 uses hand-calibrated deterministic heuristics.
- **HippoRAG 2:** PPR + passage integration + online LLM; Phase 12 proposes typed neighbor expansion and no extra LLM.
- **Adaptive-RAG:** trained query-complexity classifier routing no/single/iterative retrieval; Phase 12 routes after first retrieval and has no no-retrieval or true iterative strategy.

The merged report should say “pattern-level alignment” and itemize what is adopted versus omitted.

### 4.2 Runtime labels are over-semantic

Roberto does not challenge the plan’s proposal to emit `weak-recall` versus `weak-focus` at runtime. Those are latent evaluation labels. A score gate may identify low confidence but cannot know that a needed clause is absent or that ranking is distractor-dominated without exhaustive relevance judgments.

Recommend runtime outputs initially be:

- `strong`;
- `low_confidence`;
- `empty`;
- plus persisted trigger reasons.

Only promote to failure-type classification if held-out evidence demonstrates it.

### 4.3 Calibration controls are still too weak

Roberto correctly flags 20–40 cases as thin and recommends adjudication, but does not require disjoint tuning/validation/test data. With multiple thresholds across 18 active benchmarks, using the same cases to choose labels, signals, thresholds, routes, and claim improvement will overfit.

Required controls:

1. freeze cases before tuning;
2. create disjoint development and held-out evaluation sets;
3. pool outputs from all retrieval variants for expert relevance labeling;
4. stratify by benchmark, single/multi-clause need, and known corpus-boundary failure;
5. report bootstrap confidence intervals and per-family effects;
6. reserve an untouched broader run for the final causal claim.

Twenty to forty cases are adequate for trace discovery, not for a general performance claim.

### 4.4 Provenance and extraction loss are underdeveloped

The expansion guidance focuses on relevance filtering but should also require mapping graph nodes/paths back to verbatim clause text. HippoRAG 2’s paper does not by itself fully motivate this, while A2RAG explicitly treats graph structure as a navigational scaffold and source text as the final evidence store under extraction loss.

Persist:

- seeds and their origin;
- traversed edge types and path scores;
- expanded/visited-but-uncited nodes;
- map-back source clause IDs;
- before/after candidates and score changes.

This is necessary for D6 attribution and graph auditability.

### 4.5 Retrieval gain does not guarantee answer/citation gain

A2RAG reports the best Recall@k but not always the best EM/F1, demonstrating a retrieval-to-generation gap. The plan’s causal metric “retry introduced a later-cited clause” is useful but insufficient: the model might cite that clause incorrectly or not use it to improve the answer.

Add counterfactual evaluation:

- regenerate with retry-only clauses removed while holding the remaining context fixed;
- measure claim-level entailment and citation completeness;
- report detector precision/recall, action success/harm, retrieval metrics, end-to-end judge dimensions, latency/tokens, and trajectory outcomes separately.

---

## 5. Specific amendments recommended for Roberto’s position

1. Replace **“matches 2026 best practice”** with **“sound, interpretable corrective baseline that is directionally aligned with 2026 practice but deliberately below the current agentic design envelope.”**
2. Replace **“invert OR to AND”** with **“OR hard-failure sentinels; calibrate or require consensus among soft score signals.”**
3. Remove answer/citation grounding as a P0 pre-generation runtime requirement; retain it offline or explicitly propose a future draft-generation verifier.
4. Distinguish the targets of ScoreGate and TASR: retrieval cardinality versus answer-correctness stopping.
5. Treat one retry as a v1 cap to test with 0/1/2 ablations, not as evidence-proven.
6. Make `weak-focus → retry_wider` an empirically tested route-policy concern, with prune/diversify/rerank as a comparator.
7. Add A2RAG, BRINK, RAGSearch, WildGraphBench, and traversal-provenance evidence.
8. Require disjoint calibration/held-out evaluation and pooled alternative-support judgments.
9. Add typed bridge/PPR expansion plus verbatim provenance map-back, not generic neighbor expansion.
10. Explicitly state source maturity and the limits of small/internal 2026 preprints.

---

## Final reviewer signal for P3

Roberto’s core direction is valuable, but I do **not** agree with the current headline or the TASR-derived P0 prescriptions. The synthesis I can support is:

- proceed with Phase 12 as an agentic-lite/corrective baseline;
- keep a hard one-retry production default while testing 0/1/2;
- use a two-tier deterministic detector (hard-failure OR, calibrated soft evidence);
- derive action routing from held-out action-oracle analysis;
- use typed, bounded, provenance-preserving graph expansion;
- separate calibration from evaluation and treat GT as incomplete silver labels; and
- pre-register escalation criteria for reformulation, path planning, or answer-level verification.

**CONCERNS:** best-practice overclaim; category error transferring TASR stopping results to pre-generation retrieval gating; impossible answer/citation signal proposed as P0; insufficient held-out calibration controls; incomplete treatment of provenance and graph incompleteness.
