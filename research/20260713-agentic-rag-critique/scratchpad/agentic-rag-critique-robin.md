# Research: Critique of Phase 12 `graphont-agentic`

**Date**: 2026-07-13  
**Researcher**: Robin  
**Status**: Draft (P1 independent research)

---

## 1. Executive Summary

- **Verdict: sound as a low-risk experimental v1, but not current agentic-RAG best practice.** A deterministic quality gate, a hard retry cap, offline-only use of ground truth, and an additive control mode are prudent. They create an interpretable causal experiment rather than an unconstrained agent. However, the design is more accurately a **bounded corrective/adaptive retrieval state machine** than a modern agentic RAG system: it does not reason over evidence sufficiency, reformulate a query, plan a path, verify an answer, or select actions from intermediate semantic evidence.
- **The cited inspirations are directionally, not mechanistically, aligned.** CRAG uses a trained T5 retrieval evaluator and three-way correction, not simple score thresholds; HippoRAG 2 uses Personalized PageRank, deeper passage integration, provenance text, and online LLM recognition memory, not merely neighbor expansion; Adaptive-RAG trains a query-complexity classifier to route among no-, single-, and iterative-retrieval strategies, rather than grading one retrieval result with fixed heuristics.[S2][S3][S4][S5]
- **The biggest technical risk is the detector, not the retry.** Raw reranker score thresholds and margins can be domain-, query-, and candidate-pool-dependent. They cannot reliably distinguish `weak-recall` from `weak-focus`, and one proposed signal—whether final citations were in retrieved context—is unavailable before generation. A 2026 CRAG reproduction also found that a learned gate largely behaved as a named-entity matcher and transferred poorly to science, illustrating why even learned retrieval scores need domain calibration.[S3]
- **One bounded retry is the correct starting budget, not a proven optimum.** It protects latency and prevents overextended trajectories, but can prematurely stop genuine multi-hop cases. 2026 evidence finds both premature collapse and over-extension are common failure modes; the cap should therefore be selected by a preregistered 0/1/2-retry ablation, not intuition.[S9]
- **Graph expansion should be typed, connectivity-aware, and provenance-preserving.** Blind one-hop/neighbor expansion risks hub noise, broken paths, and loss of qualifiers. Current evidence favors relation-aware seeds, bounded bridge discovery or degree-normalized PPR, reranking, and mapping graph regions back to source clauses.[S1][S4][S10][S11]
- **The proposed 20–40-case calibration set is too small to both tune and validate the policy across 18 benchmarks.** GT clause references are appropriately called a silver oracle, but incomplete relevance labels can change retriever rankings and retrieval–generation conclusions. Separate calibration and held-out evaluation sets, pooled alternative-support judgments, and semantic/benchmark stratification are required.[S12][S13]

**Recommendation:** proceed only as a measured **`graphont-corrective`/agentic-lite baseline**, strengthen the detector and evaluation protocol before implementation, and pre-register evidence-based promotion criteria for query reformulation, evidence verification, or path planning.

---

## 2. Problem Statement and Local Baseline

Phase 12 asks whether internal `graphont` retrieval signals can detect weak retrieval and whether one deterministic corrective action—wider retrieval or graph expansion—improves clause availability and downstream citation score D6.[P1] The existing Term 3 pipeline already performs ontology-guided query translation, graph traversal, parallel graph/thematic/text recall, rank fusion, cross-encoder reranking, and clause grounding. It was introduced additively so the flat hybrid path remained unchanged.[P2]

This review assesses:

1. fidelity to CRAG, HippoRAG, and Adaptive-RAG;
2. deterministic weakness detection;
3. the single-retry budget and action policy;
4. graph expansion as recall recovery;
5. offline GT calibration and evaluation integrity;
6. backward-compatible additive delivery; and
7. concrete alternatives and escalation criteria.

Success means a design that improves retrieval and citations without runtime label leakage, hidden cost, uncontrolled graph drift, or a false causal claim.

---

## 3. Alignment with the Named Research Bases

| Claimed basis | What the source actually does | Phase 12 alignment | Assessment |
|---|---|---|---|
| **CRAG** | A fine-tuned T5-large evaluator scores query–document pairs; thresholds route to Correct, Incorrect, or Ambiguous. Correct retrieval is decomposed/refined; Incorrect uses external search; Ambiguous combines internal and external evidence.[S2][S3] | Post-retrieval gate followed by a corrective action. | **Conceptually aligned, mechanically different.** Calling a threshold conjunction “CRAG-style” is acceptable only if the report states that it substitutes interpretable domain heuristics for CRAG’s trained evaluator and omits refinement/external search. |
| **HippoRAG / HippoRAG 2** | HippoRAG 2 extends Personalized PageRank with deeper passage integration and stronger online LLM use; it is designed to preserve factual, associative, and sense-making memory.[S4] | Seed concepts, expand graph neighbors, merge clauses, rerank. | **Loose alignment.** Neighbor expansion alone is not HippoRAG. A closer no-extra-LLM analogue would use typed seeds, degree-normalized PPR/bridge scoring, passage nodes, and source-text map-back. |
| **Adaptive-RAG** | A smaller trained classifier predicts query complexity and routes among no retrieval, single-step retrieval, and iterative retrieval.[S5] | A deterministic post-retrieval rule routes strong cases to generation and weak cases to one of two retries. | **Pattern-level alignment only.** Phase 12 adapts after seeing retrieval, whereas Adaptive-RAG predicts strategy from query complexity. It also lacks no-retrieval and true iterative strategies. |
| **2026 adaptive/agentic GraphRAG** | A2RAG checks evidence sufficiency after stages, escalates local → bridge → global PPR, maps graph signals to provenance text, verifies the answer, rewrites failed queries, and terminates within a bounded budget.[S1] | Strong/weak gate, wider or graph retry, one hard cap. | **Good v1 safety posture but materially below the 2026 design envelope.** Missing sufficiency verification, bridge/global escalation, provenance-aware answer verification, and failure-conditioned rewrite. |

### Is it “agentic”?

A 2026 ACL industry comparison characterizes Agentic RAG as an LLM orchestrating which actions to perform, when to perform them, and whether to iterate.[S6] RAGSearch similarly formalizes agentic search as an LLM making dynamic multi-round retrieval and termination decisions; its strongest training-free workflow uses decomposition, retrieval, evidence verification, and query expansion.[S7]

Phase 12 has state, observation, conditional routing, and termination, so “agentic” is not indefensible in the broad workflow sense. But with a fixed rule and fixed action map it has **no autonomous semantic planning**. To avoid overstating novelty, documentation should call it one of:

- bounded corrective GraphRAG;
- deterministic adaptive GraphRAG; or
- agentic-lite retrieval control.

This naming distinction matters because a negative result would disprove only this fixed controller, not agentic RAG generally.

---

## 4. Evaluation of the Core Design Decisions

### 4.1 Deterministic, no-extra-LLM weakness detection

#### What is good

- It is reproducible, inspectable, cheap, and suitable for a compliance system.
- Persisted trigger reasons enable per-case audits and detector error analysis.
- Avoiding an LLM gate isolates whether existing retrieval telemetry is already useful.
- ScoreGate provides recent evidence that signals already emitted by bi-encoder and cross-encoder stages can control retrieval cardinality without another inference call. It reports MRR@10 0.401 with 35% fewer retained chunks on 200 MS MARCO queries, although its small/internal evaluation limits generalization.[S8]

#### What is weak or underspecified

1. **The rule conflates observables with latent failure types.** Low top score is observable. “Needed clause is absent” (`weak-recall`) is not knowable from scores alone. “Relevant region is dominated by distraction” (`weak-focus`) is also semantic. Runtime should initially emit `low_retrieval_confidence` plus reasons, not claim a four-class diagnosis unless held-out evidence supports that classifier.
2. **Thresholds are not inherently comparable.** Cross-encoder scores, score margins, and RRF/channel contributions shift with query type, candidate-pool depth, and corpus updates. A narrow multi-clause query can legitimately have several similar top scores; a high top-1 margin can still represent confidently wrong retrieval.
3. **The proposed OR rule may over-trigger.** Five individually noisy conditions joined by OR can produce a high false-positive rate, paying retry cost and adding noise to already sufficient evidence.
4. **One candidate signal is causally impossible at gate time.** “Whether final generated citations were present in retrieved context” exists only after generation. It is useful offline or for a future post-answer verifier, but must not be in the pre-generation runtime detector.
5. **Even learned evaluators can be brittle.** The 2026 CRAG reproduction found the T5 gate primarily followed named-entity alignment, classified 88.3% of ARC-Challenge cases Ambiguous, and showed domain-transfer failures. This is a warning against interpreting high score as evidence sufficiency.[S3]

#### Better v1 signal set

Use a small calibrated model or monotone rule over features that are available before generation:

- rank-normalized bi-encoder and cross-encoder distributions, not only raw values;
- top-1/top-k margin and entropy conditioned on candidate-pool size;
- agreement across graph, BM25, and dense channels;
- query concept/entity/relation coverage;
- source, section, clause-family, and document diversity;
- whether retrieved clauses form a connected query-aligned subgraph;
- typed-relation match between query intent and retrieved paths;
- provenance-text availability for each graph result;
- exact/rare-term coverage for clause numbers, regulator names, deadlines, and exceptions.

ScoreGate supports dual-score fusion, while A2RAG’s relation-seeding ablation shows entity-only seeding reduced Recall@2 by 6.3 and 7.4 points on its two 200-question samples.[S1][S8] These sources favor **multi-signal, relation-aware** grading over a single confidence threshold. However, A2RAG is a preprint using sampled benchmarks, so its exact gains should not be transferred to CCoP without local validation.

### 4.2 One bounded retry

#### Assessment

The cap is a strong engineering safeguard and an appropriate v1 default. It guarantees termination, limits latency variance, and protects the existing evaluation protocol from an unconstrained loop. A2RAG also uses monotonic bounded escalation and reports about 50% lower token use and latency than iterative baselines, supporting cost-aware progressive retrieval.[S1]

The problem is treating `<=1` as a design truth rather than a hypothesis. AgenticRAGTracer finds that failed trajectories both terminate prematurely and overextend; GPT-5 reached only 22.6% EM on its hardest 4-hop subset.[S9] Thus:

- zero retries can strand recoverable misses;
- one retry may still be insufficient for a multi-hop query with a bad initial seed;
- two or more retries can amplify drift and noise.

**Required experiment:** compare caps 0, 1, and 2 using the same held-out cases and matched candidate/token budgets. Report marginal retry utility, harmful-retry rate, p95 latency, and cases that need an additional hop. Keep production at one unless the second retry has clear net benefit.

### 4.3 Fixed action selection

The plan routes `empty → wider`, `weak-recall → graph-expand`, and `weak-focus → wider`.[P1] This is understandable but premature:

- An empty result caused by failed entity alignment may need lexical fallback or query repair, not merely larger `k`.
- Weak recall can arise because the graph lacks an edge; graph expansion then cannot recover the clause.
- Weak focus more naturally calls for reranking/filtering or diversity control than simply widening the pool.
- If the gate cannot reliably identify weak-recall versus weak-focus, the route table cannot reliably select the right action.

A better action policy chooses from **concrete observed failures**:

| Observed signal | Preferred correction |
|---|---|
| No candidates / restrictive filtering | Relax filters and widen sparse+dense retrieval |
| Channel disagreement or rare exact terms absent | Reweight lexical channel / hybrid retry |
| Adequate candidate pool but flat/noisy reranker scores | Rerank a wider pool; diversity/coverage selection |
| Multiple query entities retrieved but disconnected | Typed bridge discovery or bounded PPR |
| Seed/entity alignment failure | Deferred query/entity reformulation |
| Graph path exists but source qualifier absent | Provenance-text map-back / parent-clause recovery |

A 2026 financial text-and-table benchmark found hybrid retrieval plus cross-encoder reranking achieved Recall@5 0.816 versus 0.695 for hybrid alone, while its CRAG-like query correction reached only 0.658. The corpus differs from CCoP and the paper is a preprint, but it is strong evidence that broad hybrid recall plus reranking should be a mandatory comparator before crediting graph expansion.[S14]

### 4.4 Graph expansion as recall recovery

#### Why it is justified

The local project problem is specifically cross-clause and cross-document retrieval. RAGSearch reports that agentic dense RAG narrows the GraphRAG gap, but explicit graphs remain strongest and more stable for multi-hop QA.[S7] A2RAG likewise finds relation-aware local/bridge/PPR escalation useful for small-k evidence recall.[S1]

#### Failure modes

- **Incomplete graphs:** BRINK finds current KG-RAG methods degrade when direct evidence is missing; about 7:3 of failures in its analysis were retrieval versus reasoning failures.[S10]
- **Hub and topology drift:** broad expansion retrieves structurally close but query-irrelevant clauses.
- **Extraction loss:** graph triples omit conditions, time bounds, numeric thresholds, and exceptions.
- **Compression/detail loss:** WildGraphBench reports GraphRAG helps moderate multi-source aggregation but can overemphasize high-level statements at the expense of fine-grained detail.[S11]
- **Provenance under-reporting:** final cited entities can be necessary yet insufficient; a 2026 graph-ablation study found visited-but-uncited nodes and neighborhood structure affected answers, though its evidence is limited to 30 questions and a workshop preprint.[S15]

#### Minimum safe expansion design

- Use ontology relation types and query-aligned relation seeds, not all neighbors.
- Cap hops, paths per seed pair, nodes, and context tokens.
- Penalize hubs or use degree-normalized PPR.
- Prefer bridge nodes connecting two or more query seeds.
- Merge expansion with the original lexical/dense pool and rerank jointly.
- Map every graph node/path back to verbatim source clauses; generate from source text, not graph summaries alone.
- Persist traversal path, edge types, seed origin, score changes, and visited-but-uncited candidates.
- Apply novelty/diversity constraints so the retry does not fill the context with near-duplicates.

Without these controls, “graph expansion” is likely to trade recall for focus rather than improve both.

### 4.5 Offline GT as a silver oracle

The runtime prohibition is correct and should remain absolute. The concern is evaluation design.

- The project’s expected-clause lists are relevance judgments, not exhaustive truth. A 2026 ICLR paper uncovered 29,824 missing relevant chunks in an IR benchmark and showed that missing labels distort retriever rankings and retrieval–generation conclusions.[S12]
- Aggregate metrics can hide benchmark-family gaps. Semantic-stratification research argues that evaluation-set construction limits metric reliability and recommends explicit corpus coverage strata.[S13]
- Retrieval and generation objectives must align: a 2026 ICTIR study finds coverage-based retrieval metrics correlate with generated information coverage most strongly when the objectives align, while iterative pipelines partially decouple them.[S16]

**Required protocol:**

1. Freeze cases before threshold tuning.
2. Separate threshold-development, validation, and final test splits; never report the tuning set as evidence of improvement.
3. Stratify by active benchmark, query type, single/multi-clause need, known graph miss, corpus-boundary case, and clause specificity.
4. Pool the top results from baseline and every retry variant; have an expert label all valid supporting clauses, including alternatives absent from GT.
5. Report both silver-GT metrics and pooled/expert relevance metrics.
6. Bootstrap confidence intervals and per-family deltas; do not infer general success from 20–40 cases.
7. Retain an untouched broader benchmark run for the final claim.

The initial 20–40 cases are appropriate for instrument discovery and qualitative debugging, not for threshold selection plus performance claims across 435 cases.

### 4.6 Additive, backward-compatible mode

This is a strong architectural and scientific choice. Keeping `graphont` as control supports paired evaluation, rollback, and attribution.[P1][P2]

The hidden risk is that splitting the shared `omd_context_assembly` node can alter both modes even if routing is additive. Required controls are:

- golden-trace parity for `graphont` before/after refactor, including candidate order, packed context, and generation prompt;
- configuration/version IDs in every result;
- deterministic fixtures and stable tie-breaking;
- no new state default that silently changes legacy packing;
- matched generator, prompt, context budget, and judge across modes;
- a feature flag that can disable the new path without reverting the refactor.

---

## 5. Gaps in the Proposed Evaluation

The plan’s causal metric—whether retry surfaced a clause later cited—is valuable but insufficient. A retry can surface a clause that the model cites incorrectly, or add it without changing the answer. Conversely, an answer can improve through uncited context.

The evaluation should cover four levels:

| Level | Required metrics |
|---|---|
| **Detector** | Precision, recall, F1, false-positive/harmful-retry rate, calibration, confusion by failure type, and performance by benchmark family |
| **Retrieval** | Recall@k, MRR/nDCG, pooled clause coverage, source/section diversity, graph connectivity, novelty, provenance availability, and before/after candidate deltas |
| **Trajectory/action** | Requery rate, action distribution, success per action, marginal utility, path/hop count, stop reason, visited versus cited evidence, and 0/1/2-cap ablations |
| **End-to-end** | All judge dimensions, especially D6; claim-level citation entailment and completeness; abstention; latency mean/p95; tokens; regression rate; and confidence intervals |

Add two counterfactual tests:

1. **Retry ablation:** regenerate with the retry-only clauses removed while holding other context fixed. Did the claimed gain disappear?
2. **Action oracle analysis (offline only):** for each weak case, run all allowed actions and measure which would have worked. This estimates the ceiling and exposes route-policy errors without leaking the oracle into runtime.

---

## 6. Prioritized Recommendations

### P0 — before implementing runtime behavior

1. **Reframe the feature as a bounded corrective/adaptive baseline.** Keep the external mode name if compatibility requires it, but state that v1 is agentic-lite and does not implement LLM-directed agentic search.
2. **Fix the calibration protocol.** Freeze a stratified dataset; create disjoint development, validation, and untouched test partitions; pool alternative supporting clauses; pre-register thresholds and success criteria.
3. **Inventory only causally available signals.** Remove post-generation citation presence from the runtime detector. Preserve it as an offline diagnostic.
4. **Use `strong/low-confidence/empty` first.** Do not output `weak-recall` or `weak-focus` unless held-out evidence shows the system can distinguish them. Persist reasons separately.
5. **Benchmark action alternatives offline.** For every detector-positive case, run wider hybrid retrieval, larger-pool reranking, typed graph expansion, and no retry. Build the route table from observed conditional utility.

### P1 — v1 retrieval loop

6. **Implement a multi-signal gate.** Use normalized score distributions, dual-score/reranker evidence, channel agreement, query-concept/relation coverage, diversity, and graph connectivity. Tune for the chosen cost of false positives versus false negatives.
7. **Make expansion relation-aware and provenance-first.** Use typed seeds, bridge discovery or degree-normalized PPR, strict budgets, joint reranking, and verbatim clause map-back.
8. **Retain exactly one production retry initially, but evaluate 0/1/2.** Promotion to two retries requires statistically and operationally meaningful marginal gain.
9. **Add an explicit stop/abstain outcome.** If the retry remains low confidence, do not describe the evidence as sufficient; allow generation to express insufficient grounding or fall back to the unchanged baseline behavior according to policy.
10. **Protect the control.** Add byte/structure-level golden traces for the legacy mode and matched-budget A/B evaluation.

### P2 — only if v1 plateaus

11. **Add cheap evidence-sufficiency verification before a full agent.** An NLI/cross-encoder verifier or constrained local-model check can test whether retrieved clauses jointly cover query entities, conditions, and requested decision—not merely whether they look relevant.
12. **Add feedback-bounded query reformulation when seed/alignment failure dominates.** Reformulation should be selected by ranker feedback and remain budgeted: SIGIR 2026 evidence warns that extra reformulations can cause severe query drift.[S17]
13. **Add RoG/path planning only for path-selection failures.** Trigger this escalation only if offline oracle analysis shows the graph contains the needed path but deterministic bridge/PPR retrieval repeatedly misses it.
14. **Consider answer-level verification last.** A2RAG’s relevance/grounding/adequacy check is closer to current practice, but it introduces model cost and another calibration surface.[S1]

### Is deferring RoG and query reformulation justified?

**Yes for v1.** Deterministic expansion is the cleanest causal test and query reformulation can drift.[S17] But deferral should be tied to explicit exit criteria, for example:

- more than 25% of detector-positive held-out cases fail because of seed/query mismatch → test reformulation;
- more than 25% fail although a short typed graph path exists → test path planning;
- retrieval recall improves but citation/answer quality does not → test evidence/answer verification rather than more retrieval.

The percentages are proposed decision thresholds, not evidence-derived constants; they must be agreed before evaluation and treated as governance criteria.

---

## 7. Final Assessment

Phase 12 is **architecturally conservative, scientifically testable, and worth running**, provided it is described as an interpretable corrective baseline rather than SOTA agentic RAG. Its strongest decisions are offline-only GT, a hard budget, causal retrieval-first metrics, and an additive control mode. Its weakest points are an overconfident four-way detector, fixed action routing before action-oracle analysis, loose use of the CRAG/HippoRAG/Adaptive-RAG labels, and an undersized calibration protocol.

The best near-term design is:

```text
existing graphont retrieval
  -> calibrated low-confidence gate
  -> if confident: unchanged packing/generation
  -> if low confidence: choose one evidence-backed action
       [wider hybrid + rerank | typed bridge/PPR + provenance map-back]
  -> one retry maximum
  -> persist trajectory and stop reason
  -> unchanged packing/generation or explicit insufficient-evidence outcome
```

This is not the most autonomous 2026 architecture; it is the right **controlled experiment** to determine whether more autonomy is warranted.

---

## 8. Limitations and Open Questions

- Much of the newest 2026 evidence is arXiv preprint work. A2RAG uses only 200 questions per public benchmark; ScoreGate uses 200 MS MARCO queries plus an internal benchmark; the graph-provenance study uses 30 questions. Their mechanisms are informative, but their reported gains should not be assumed to transfer to CCoP.
- The exact reliability of current `ce_confidence`, channel scores, and ontology graph completeness cannot be established until Slice A exports real traces.
- No retrieved source establishes universal score thresholds or a universal optimal retry cap; both remain local empirical questions.
- It is unresolved whether the current graph encodes enough relation and provenance metadata for PPR/bridge retrieval without a graph rebuild.

---

## 9. References

### Local design context

- **[P1]** [Phase 12 — Agentic `graphont` Retrieval-Quality Loop](../../../.planning/phases/12-agentic-graphont-retrieval-quality-loop/12-01-PLAN.md) — dated 2026-07-13 — proposed design evaluated here.
- **[P2]** [T3 Mid Report: Aether CCoP](../../../report/term3-mid/T3-Mid-Report-Sagar-1010736-Aether-CCoP.pdf), §§11–19 — 2026 — existing ontology-guided, multi-channel GraphRAG architecture and additive-mode rationale.

### Retrieved external sources

- **[S1]** [A2RAG: Adaptive Agentic Graph Retrieval for Cost-Aware and Reliable Reasoning](https://arxiv.org/abs/2601.21162) — updated 2026-06-04 — progressive local/bridge/PPR retrieval, evidence sufficiency, provenance map-back, bounded retries, and reported efficiency/recall results.
- **[S2]** [Corrective Retrieval Augmented Generation](https://arxiv.org/abs/2401.15884) — updated 2024-01-29 — original CRAG retrieval evaluator and corrective-action architecture.
- **[S3]** [Open-Source Reproduction and Explainability Analysis of Corrective Retrieval Augmented Generation](https://arxiv.org/abs/2603.16169) — published 2026-03-17 — CRAG reproduction, entity-alignment behavior, threshold/domain-transfer failures.
- **[S4]** [From RAG to Memory: Non-Parametric Continual Learning for Large Language Models](https://proceedings.mlr.press/v267/gutierrez25a.html) — ICML 2025, proceedings published 2025-07 — HippoRAG 2’s PPR, deeper passage integration, and online LLM use.
- **[S5]** [Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity](https://aclanthology.org/2024.naacl-long.389/) — published 2024-06 — trained complexity classifier and no/single/iterative retrieval routing.
- **[S6]** [Is Agentic RAG worth it? An experimental comparison of RAG approaches](https://aclanthology.org/2026.acl-industry.5/) — published 2026-07 — empirical framing of enhanced versus LLM-orchestrated agentic RAG.
- **[S7]** [Do We Still Need GraphRAG? Benchmarking RAG and GraphRAG for Agentic Search Systems](https://arxiv.org/abs/2604.09666) — published 2026-04-01 — matched-budget agentic dense/GraphRAG comparison; graph advantages on multi-hop tasks.
- **[S8]** [ScoreGate: Adaptive Chunk Selection for Retrieval-Augmented Generation via Dual-Score Statistical Fusion](https://arxiv.org/abs/2606.14269) — published 2026-06-12 — no-extra-call bi-/cross-encoder score gating and its limited-scale results.
- **[S9]** [AgenticRAGTracer: A Hop-Aware Benchmark for Diagnosing Multi-Step Retrieval Reasoning in Agentic RAG](https://arxiv.org/abs/2602.19127) — updated 2026-07-02, ACL 2026 Findings — premature-collapse and over-extension trajectory failures.
- **[S10]** [What Breaks Knowledge Graph based RAG? Benchmarking and Empirical Insights into Reasoning under Incomplete Knowledge](https://aclanthology.org/2026.eacl-long.114/) — EACL 2026; arXiv updated 2026-01-12 — KG incompleteness, alternative-path failure, retrieval/reasoning error analysis.
- **[S11]** [WildGraphBench: Benchmarking GraphRAG with Wild-Source Corpora](https://arxiv.org/abs/2602.02053) — updated 2026-02-03 — realistic heterogeneous corpus benchmark and graph-aggregation detail loss.
- **[S12]** [Completing Missing Annotation: Multi-Agent Debate for Accurate and Scalable Relevant Assessment for IR Benchmarks](https://arxiv.org/abs/2602.06526) — published 2026-02-06, ICLR 2026 — incomplete relevance labels and distorted retriever/RAG conclusions.
- **[S13]** [Coverage, Not Averages: Semantic Stratification for Trustworthy Retrieval Evaluation](https://arxiv.org/abs/2604.20763) — published 2026-04-22 — evaluation-set coverage bias and semantic stratification.
- **[S14]** [From BM25 to Corrective RAG: Benchmarking Retrieval Strategies for Text-and-Table Documents](https://arxiv.org/abs/2604.01733) — published 2026-04 — large domain benchmark favoring hybrid retrieval plus neural reranking over CRAG-like rewriting.
- **[S15]** [Why Neighborhoods Matter: Traversal Context and Provenance in Agentic GraphRAG](https://arxiv.org/abs/2605.15109) — published 2026-05 — trajectory-level provenance and visited-but-uncited context; small workshop study.
- **[S16]** [Beyond Relevance: On the Relationship Between Retrieval and RAG Information Coverage](https://arxiv.org/abs/2603.08819) — updated 2026-06-20, ICTIR 2026 — alignment between retrieval coverage and generation objectives.
- **[S17]** [When More Reformulations Hurt: Avoiding Drift using Ranker Feedback](https://arxiv.org/abs/2605.00560) — published 2026-05-01, SIGIR 2026 — query-drift risk and budget-aware ranker feedback.
