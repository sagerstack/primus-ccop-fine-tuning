# Research: Critical Evaluation of the Phase 12 "graphont-agentic" Bounded Retrieval-Quality Loop

**Date**: 2026-07-13
**Researchers**: Roberto (`claude-opus-4-8`, drafter) + Robin (`gpt-5.6-sol`, reviewer) — peer-reviewed merged artifact
**Status**: Final

---

## 1. Executive Summary

- **Verdict: sound, interpretable, low-risk corrective baseline — and worth building — but describe it accurately.** Phase 12 is a *bounded corrective / adaptive retrieval state machine* ("agentic-lite"), **directionally aligned** with 2026 corrective/graph-RAG practice (CRAG gate → bounded action → HippoRAG-style graph recall recovery → Adaptive-RAG-style routing) but **deliberately below the current agentic design envelope**. That gap (no extra LLM, no query reformulation, no evidence-sufficiency/answer verification, no path planning) is a *conscious v1 trade-off for a clean causal experiment*, not an implementation defect.
- **The named bases are pattern-level, not mechanistic, matches.** CRAG uses a *trained* T5 evaluator + 3-way correction + external search; HippoRAG 2 uses Personalized PageRank + deeper passage integration + *online* LLM recognition memory; Adaptive-RAG *trains* a query-complexity classifier. Phase 12 borrows the *concepts* (gate-then-correct, graph expansion, route weak cases), not the mechanisms. The report/plan should say so to avoid overstating validation or novelty. [S2][S3][S4][S5]
- **The detector is the #1 risk, not the retry.** Raw reranker/retrieval scores certify *topicality*, not answer support or evidence sufficiency, and shift with query type and candidate-pool depth. Two 2026 results bound this: ScoreGate shows bi-/cross-encoder scores *can* steer retrieval cardinality with no extra call [S8]; TASR shows those same score families *do not certify downstream correctness* and that OR-ing several soft, high-frequency triggers overfires [S18]. **Synthesis → a two-tier deterministic gate:** OR over *hard* sentinels (`retrieval_failed`, `empty`); a locally-calibrated consensus/AND (or best held-out rule) over *soft* score signals.
- **Graph expansion must be typed, hub-safe, and provenance-preserving.** Naïve one-hop expansion over `graphont`'s `CII` hub (296 clauses, ≈⅓ of the graph [P2]) is a textbook "Static Graph Fallacy" hazard — PPR/probability mass drifts into high-degree hubs, yielding high *partial* recall but broken evidence chains [S19]; and expansion cannot traverse a path the graph does not contain [S10]. Lead the guard with `graphont`'s **existing rarity-gate** (report §16.2 [P2]) + reuse of the Stage-1 selected concepts as a no-new-LLM query-aware edge filter; keep degree-normalized PPR / typed bridge discovery + verbatim clause map-back as escalation.
- **Evaluation integrity is the make-or-break for the causal claim.** GT clause lists are an *incomplete* silver oracle; 20–40 cases cannot both tune (labels, signals, thresholds, routes) and validate across 18 benchmarks without overfitting. Require disjoint calibration/held-out/test splits, pooled expert adjudication of alternative support, stratification, bootstrap CIs, a **full-chain** retrieval metric, and two counterfactuals (retry-ablation + offline action-oracle). [S12][S13][S16]

**Recommendation (one line):** Proceed with Phase 12 as an explicitly-scoped agentic-lite corrective baseline; before wiring runtime behavior, fix the detector to a two-tier rule over pre-generation features, derive the action policy from an offline action-oracle, make graph expansion typed/hub-safe/provenance-first, and separate calibration from held-out evaluation — then let evidence gate any escalation to reformulation, path planning, or answer verification.

---

## 2. Problem Statement & Local Baseline

Phase 12 adds an additive `graphont-agentic` mode: a deterministic, stateful loop that (1) detects weak `graphont` retrieval from internal signals, (2) applies one bounded corrective action (parameter-widening or graph expansion), and (3) re-assesses before generation — with ground truth used *offline only* for calibration, and RoG/ReAct/query-reformulation explicitly deferred (no extra LLM in v1). [P1]

The existing Term-3 `graphont` pipeline already performs ontology-guided query→concept translation, one-step rarity-gated graph traversal, three parallel recall channels (graph/BM25/dense), weighted RRF fusion, cross-encoder reranking, and glossary-augmented clause grounding, delivered additively so the flat hybrid path is unchanged. Its stated residuals are low citation correctness (D6 = 0.278) and broken cross-document chains; the report itself flags the reranker's "tightly-clustered scores on very short factoid questions" as a known limitation (§16.5, §17.1). [P2]

This artifact evaluates: (1) fidelity to CRAG/HippoRAG/Adaptive-RAG; (2) deterministic no-LLM weakness detection; (3) the single-retry budget and action policy; (4) graph expansion as recall recovery; (5) offline GT calibration and evaluation integrity; (6) additive/backward-compatible delivery; and (7) whether deferring RoG/reformulation is justified. All claims trace to sources retrieved this session (§9).

---

## 3. Alignment With the Named Research Bases (pattern-level, not mechanistic)

| Claimed basis | What the source actually does | Phase 12 adopts / omits | Assessment |
|---|---|---|---|
| **CRAG** [S2][S3] | *Trained* T5-large retrieval evaluator scores query–doc pairs; routes to Correct / Incorrect / Ambiguous; refinement + external web search. | Adopts: post-retrieval quality gate → corrective action. Omits: trained evaluator, refinement, external search. | **Conceptually aligned, mechanically different.** Acceptable only if documented as "interpretable deterministic heuristics substituting for CRAG's trained evaluator." The 2026 CRAG reproduction shows even the *trained* gate behaved largely as a named-entity matcher and transferred poorly across domains — a caution against trusting scores as sufficiency. [S3] |
| **HippoRAG / HippoRAG 2** [S4] | PPR over a KG + deeper passage integration + provenance text + *online* LLM recognition memory; SOTA multi-hop recall (59.8 vs 57.0 avg F1 vs NV-Embed-v2 across 7 benchmarks). | Adopts: seed→neighbor graph expansion + rerank. Omits: PPR, recognition memory, passage-node integration, online LLM. | **Loose alignment.** Neighbor expansion alone is not HippoRAG; "SOTA" validates the *full* PPR+integration+LLM system, not bare one-hop expansion. A closer no-extra-LLM analogue = typed seeds + degree-normalized PPR/bridge scoring + source-text map-back. |
| **Adaptive-RAG** [S5] | *Trained* query-complexity classifier routes among no-/single-/multi-step retrieval *before* retrieving. | Adopts: route weak vs strong cases to different effort. Omits: trained classifier, no-retrieval + true iterative strategies; routes *after* first retrieval. | **Pattern-level only.** Phase 12 adapts on observed retrieval, not predicted query complexity. |
| **2026 agentic/graph envelope** [S1][S7][S6] | e.g. A2RAG: stage-wise evidence-sufficiency checks, monotonic local→bridge→global/PPR escalation, relation seeding, provenance map-back under extraction loss, answer-level grounding/adequacy verification, failure-conditioned rewrite within a bounded budget. | Adopts: budgeted escalation idea + additive control. Omits: sufficiency verification, bridge/global escalation, provenance-aware answer verification, failure-conditioned rewrite. | **Good v1 safety posture, materially below the 2026 envelope — by design.** Supports "directionally aligned, intentionally minimal," not "matches best practice." |

**Is it "agentic"?** It has state, observation, conditional routing, and termination, so the *broad workflow* sense is defensible [S6][S7]. But with a fixed rule and fixed action map it performs *no autonomous semantic planning*. **Name it precisely** — "bounded corrective GraphRAG" / "deterministic adaptive GraphRAG" / "agentic-lite retrieval control" — because a negative result would disprove only *this fixed controller*, not agentic RAG in general. (Keep the external mode name `graphont-agentic` if compatibility requires; add the scoping in prose.)

---

## 4. Evaluation of the Core Design Decisions

### 4.1 Deterministic, no-extra-LLM weakness detection — the central risk

**Strong.** Reproducible, inspectable, cheap, audit-friendly (persisted trigger reasons enable per-case error analysis), and appropriate for a compliance system. Avoiding an LLM gate isolates whether existing retrieval telemetry is already useful. ScoreGate corroborates the mechanism: signals already emitted by bi-/cross-encoder stages can control retrieval cardinality with **no extra inference call** (MRR@10 0.401 with 35% fewer chunks on 200 MS MARCO queries; *zero observed* false positives at 97.8–99.3% recall on an internal n=300 set — small/internal, so treat as indicative). [S8]

**Weak / underspecified as written:**
1. **The v1 rule conflates observables with latent failure types.** Low top-score is observable; "needed clause is absent" (`weak-recall`) and "relevant region dominated by distractors" (`weak-focus`) are *semantic* and not knowable from scores alone.
2. **Thresholds are not inherently comparable.** Cross-encoder scores, margins, and RRF/channel contributions shift with query type, pool depth, and corpus updates; a narrow multi-clause query legitimately has several similar top scores, and a high top-1 margin can be *confidently wrong*.
3. **The OR rule over-triggers.** Several individually noisy soft conditions joined by OR yields a high false-positive rate — paying retry cost and injecting distractors into already-sufficient evidence. TASR quantifies the general hazard: soft signals that each fire on ~50% of decisions produce an OR that fires ~75% of the time, and adding a cross-encoder reranker or BM25 retrieval-confidence score as an OR-vote *hurt* its F1 by 4–14 / 3.5–17.9 points because the reranker "scores evidence topicality rather than support for the answer." [S18]
4. **One candidate signal is causally impossible at gate time.** "Whether final generated citations were present in retrieved context" exists only *after* generation. Keep it as an **offline diagnostic** (or a future post-generation verifier); it must not be a pre-generation runtime signal.

**Scope note on TASR (avoid a category error).** TASR is a *post-generation iterative stopping* rule (answer-stability AND a calibrated answer-token logit margin, after ≥2 LLM calls). Phase 12's gate is *pre-generation* retrieval classification — different target, state, and action space. TASR therefore does **not** prove that reranker scores are poor *retrieval-weakness* predictors, nor that Phase 12 must globally invert its detector to AND (`retrieval_failed`/`empty` are legitimate hard-failure OR sentinels). It supports two *narrower* cautions: (a) topicality scores do not certify answer support, and (b) OR-ing several soft, high-frequency triggers overfires.

**Synthesis → two-tier deterministic detector:**
- **Tier 1 — hard-failure sentinels (OR):** `not retrieval_succeeded`, `empty`/near-empty pool → immediate weak.
- **Tier 2 — soft evidence (calibrated consensus / AND, or the single best held-out rule):** over *pre-generation, rank-normalized* features:
  - rank-normalized bi-encoder & cross-encoder distributions (not raw values); top-1/top-k margin & entropy *conditioned on pool size*;
  - cross-channel agreement (graph/BM25/dense);
  - query concept/entity/**relation** coverage;
  - source/section/clause-family/document diversity;
  - whether retrieved clauses form a **connected, query-aligned subgraph**; provenance-text availability;
  - exact/rare-term coverage (clause numbers, regulator names, deadlines, exceptions).
- **Runtime labels:** emit `strong` / `low_confidence` / `empty` + persisted reasons **first**; only promote to a `weak-recall`/`weak-focus` classifier if held-out evidence shows the system can actually distinguish them.

This reconciles ScoreGate (scores *can* decide "retrieve more") with TASR (scores *do not* prove sufficiency) — score telemetry guides cardinality but is not evidence sufficiency without local held-out calibration.

### 4.2 One bounded retry — a prudent default, not a proven optimum

The cap guarantees termination, limits latency variance, and protects the ablation from an unbounded loop; iterative agentic loops add retrieval/LLM calls and can materially raise token and latency costs [S6][S1] (one vendor guide estimates 3–10× tokens [S20] — an industry estimate, not used here as decision evidence), while progressive bounded escalation reports ~50% lower token/latency than iterative baselines [S1]. But `≤1` is a **hypothesis, not a truth**: trajectory diagnostics find both premature collapse *and* over-extension in failed multi-hop runs (e.g., GPT-5 at 22.6% EM on a hardest 4-hop subset) [S9]. In this loop the specific risk is **under-recovery** (the loop only retries weak cases and always generates after the cap), not premature termination of a live trajectory. **Do:** keep one production retry; run a pre-registered **0/1/2** ablation on held-out cases with matched candidate/token budgets; report marginal retry utility, harmful-retry rate, p95 latency, and share needing an extra hop; promote to two only on clear net benefit.

### 4.3 Fixed action selection — decide by action-oracle, not intuition

The plan routes `empty → wider`, `weak-recall → graph-expand`, `weak-focus → wider`. This is premature: an empty result from failed entity alignment may need lexical fallback/query repair, not larger `k`; weak-recall from a *missing graph edge* cannot be fixed by expansion; and **`weak-focus → wider` is a high-risk hypothesis** — widening adds distractors, though a wider pool *followed by a stronger rerank* can occasionally improve focus by introducing better candidates. Do not condemn or bless it from intuition.

**Build the route table from an offline action-oracle:** for every detector-positive calibration case, run {no-retry, wider+rerank, prune/diversify, typed graph-expand} and measure conditional utility. Preferred mapping from *observed* signals:

| Observed signal | Preferred correction (to be confirmed by action-oracle) |
|---|---|
| No candidates / over-restrictive filtering | Relax filters; widen sparse+dense |
| Channel disagreement / rare exact terms absent | Reweight lexical channel / hybrid retry |
| Adequate pool but flat/noisy reranker scores | Rerank a wider pool; diversity/coverage selection |
| Multiple query entities retrieved but disconnected | Typed bridge discovery / bounded degree-normalized PPR |
| Seed/entity alignment failure | *Deferred* query/entity reformulation (escalation) |
| Graph path exists but source qualifier absent | Provenance map-back / parent-clause recovery |

A 2026 text-and-table benchmark found hybrid + cross-encoder rerank reached Recall@5 0.816 vs 0.695 (hybrid alone), while a CRAG-like query-correction reached only 0.658 — different corpus and a preprint, but strong reason to make **wide hybrid + rerank a mandatory comparator before crediting graph expansion**. [S14]

### 4.4 Graph expansion as recall recovery — justified, but hazard-prone

**Why justified.** The local problem is precisely cross-clause/cross-document retrieval, and a reranker cannot recover a clause absent from its candidate pool (the "bounded recall problem") [S21] — so a *recall-recovery* retry, not better ranking, is what surfaces the missed clause. Graph structure remains strongest/most stable for multi-hop even as strong agentic dense retrieval narrows the gap [S7].

**Failure modes (evidence-backed):**
- **Static Graph Fallacy / hub drift:** fixed transition probabilities divert PPR/random-walk mass into high-degree hub nodes → high *partial* recall, broken evidence chains [S19]. `graphont`'s `CII` hub (296 clauses, ≈⅓ of the graph [P2]) is exactly such a node.
- **Graph incompleteness:** KG-RAG degrades when the needed edge/path is missing; expansion cannot traverse what isn't there (BRINK: retrieval-vs-reasoning failure mix ≈7:3) [S10].
- **Extraction / detail loss:** triples drop conditions, time bounds, numeric thresholds, exceptions; GraphRAG can over-emphasize high-level statements and lose fine-grained detail [S11].
- **Provenance under-reporting:** final cited nodes can be necessary-but-insufficient; visited-but-uncited traversal context affects answers [S15] (small workshop study — caveat).

**Minimum-safe expansion (no new LLM in v1):**
- Reuse Stage-1 selected concepts as anchors; expand only **rarity-passing** concepts (existing §16.2 gate [P2]); score candidate edges by query-concept alignment before merge; cap hops/paths-per-seed-pair/nodes/context-tokens (cf. `K_edge` bounds).
- Prefer **bridge nodes** connecting ≥2 query seeds; penalize hubs (degree-normalized PPR as escalation).
- Merge with the original lexical/dense pool and **rerank jointly**; apply novelty/diversity to avoid near-duplicate filling.
- **Map every graph node/path back to verbatim clause text; generate from source text, not graph summaries.**
- Persist traversal provenance: seeds+origin, edge types, path scores, expanded/visited-but-uncited nodes, map-back clause IDs, before/after candidates & score deltas.

### 4.5 Offline GT as a silver oracle — right discipline, protect the evaluation

The runtime prohibition on GT is correct and must remain absolute. The risk is *evaluation design*:
- Expected-clause lists are relevance judgments, not exhaustive truth; incomplete labels distort retriever rankings and retrieval→generation conclusions (a 2026 study surfaced 29,824 missing relevant chunks and showed altered conclusions) [S12].
- Aggregate metrics hide benchmark-family gaps; coverage/semantic stratification is needed [S13]. Retrieval and generation objectives only align under coverage-aware metrics; iterative pipelines partially decouple them [S16].

**Required protocol:** (1) freeze cases before tuning; (2) disjoint development / validation / untouched-test splits — never report the tuning set as improvement; (3) stratify by active benchmark, single/multi-clause need, known graph miss, corpus-boundary case, clause specificity; (4) pool baseline + every retry variant and have an expert label *all* valid supporting clauses, including alternatives absent from GT; (5) report silver-GT *and* pooled-expert metrics; (6) bootstrap CIs + per-family deltas — no general claim from 20–40 cases; (7) retain an untouched broader run for the final causal claim. The 20–40 cases are for instrument discovery/debugging, not threshold selection *plus* a performance claim across 435 cases.

### 4.6 Additive, backward-compatible mode — strong choice, guard the refactor

Keeping `graphont` as control supports paired evaluation, rollback, and clean attribution [P1][P2]. Hidden risk: splitting the shared `omd_context_assembly` node can alter *both* modes. Controls: golden-trace parity for legacy `graphont` (candidate order, packed context, generation prompt) before activating the new path; config/version IDs in every result; deterministic fixtures + stable tie-breaking; no new state default that silently changes legacy packing; matched generator/prompt/context-budget/judge across modes; a feature flag that disables the new path without reverting the refactor.

---

## 5. Evaluation Gaps & Required Metrics

The plan's causal metric — "did retry surface a clause later cited?" — is valuable but insufficient: a retry can surface a clause the model cites *incorrectly*, or add it without changing the answer; conversely an answer can improve via uncited context (retrieval-gain ≠ answer/citation-gain, as A2RAG's best-Recall-not-always-best-F1 shows [S1]). Evaluate at four levels + two counterfactuals:

| Level | Metrics |
|---|---|
| **Detector** | precision/recall/F1, false-positive & harmful-retry rate, calibration, confusion by failure type, per-benchmark-family |
| **Retrieval** | Recall@k, MRR/nDCG, **full-chain retrieval** (all gold clauses present *together*), pooled clause coverage, source/section diversity, subgraph connectivity, novelty, provenance availability, before/after candidate deltas |
| **Trajectory / action** | requery rate, action distribution, success/harm per action, marginal utility, hop/path count, stop reason, visited-vs-cited evidence, 0/1/2-cap ablation |
| **End-to-end** | all judge dimensions (esp. **D6**), claim-level citation entailment & completeness, abstention, latency mean/p95, tokens, regression rate, bootstrap CIs |

**Counterfactuals:** (1) **Retry-ablation** — regenerate with retry-only clauses removed, other context fixed; did the claimed gain disappear? (2) **Offline action-oracle** — per weak case, run all allowed actions to estimate the ceiling and expose route-policy errors (oracle never enters runtime).

---

## 6. Prioritized Recommendations

### P0 — before wiring runtime behavior
1. **Reframe the feature** as a bounded corrective / agentic-lite baseline (keep the external mode name; state v1 is deliberately below the 2026 agentic envelope). Compress the naming point to ~2 sentences in project docs.
2. **Fix the calibration protocol:** freeze a stratified set; disjoint development/validation/untouched-test; pool alternative-support judgments; pre-register thresholds and success criteria.
3. **Inventory only causally-available signals:** remove post-generation citation-presence from the runtime detector (retain offline).
4. **Emit `strong`/`low_confidence`/`empty` first;** do not output `weak-recall`/`weak-focus` unless held-out evidence supports the distinction; persist reasons separately.
5. **Benchmark action alternatives offline** (action-oracle) for every detector-positive case; build the route table from observed conditional utility.

### P1 — the v1 retrieval loop
6. **Two-tier detector:** hard-failure OR sentinels + locally-calibrated consensus/AND (or best held-out rule) over rank-normalized soft features (dual-score, channel agreement, concept/relation coverage, diversity, subgraph connectedness, provenance availability); tune for the chosen false-positive/false-negative cost.
7. **Typed, hub-safe, provenance-first expansion:** rarity-gate + Stage-1 concept reuse first; typed bridge / degree-normalized PPR + verbatim clause map-back as escalation; strict budgets; joint rerank; novelty/diversity.
8. **Keep one production retry; evaluate 0/1/2;** promote only on statistically + operationally meaningful marginal gain.
9. **Add an explicit stop/abstain outcome:** if retry stays low-confidence, do not present evidence as sufficient — allow "insufficient grounding" or fall back to unchanged baseline per policy.
10. **Protect the control:** byte/structure-level golden traces for legacy mode + matched-budget A/B.

### P2 — only if v1 plateaus (evidence-gated escalation)
11. **Cheap evidence-sufficiency check** (NLI/cross-encoder or constrained local-model) testing whether retrieved clauses *jointly* cover query entities/conditions/decision — before a full agent.
12. **Feedback-bounded query reformulation** when seed/alignment failure dominates; budget it — extra reformulations can cause severe query drift [S17].
13. **RoG / path planning** only for path-selection failures where the offline oracle shows the graph contains the needed path but deterministic bridge/PPR repeatedly misses it.
14. **Answer-level verification last** (A2RAG-style relevance/grounding/adequacy) — adds model cost + another calibration surface. [S1]

**Is deferring RoG & query reformulation justified? Yes for v1** — deterministic expansion is the cleanest causal test and reformulation can drift [S17] — provided deferral is tied to *pre-registered, evidence-gated* exit criteria, e.g. (proposed governance thresholds, not evidence-derived constants): >25% of detector-positive held-out cases fail on seed/query mismatch → test reformulation; >25% fail although a short typed path exists → test path planning; recall improves but citation/answer quality does not → test evidence/answer verification rather than more retrieval.

---

## 7. Final Assessment

Phase 12 is **architecturally conservative, scientifically testable, and worth running**, provided it is described as an interpretable corrective baseline rather than SOTA agentic RAG. Strongest decisions: offline-only GT, a hard budget, retrieval-first causal metrics, an additive control mode. Weakest points as written: an over-semantic four-way detector built on a wide OR of soft scores, fixed action routing decided before action-oracle analysis, loose CRAG/HippoRAG/Adaptive-RAG labelling, and an undersized calibration protocol. The best near-term design:

```text
existing graphont retrieval
  -> two-tier gate: hard-failure OR sentinels; calibrated soft-evidence consensus
  -> if confident: unchanged packing/generation
  -> if low-confidence: choose ONE evidence-backed action (from offline action-oracle)
       [ wider hybrid + rerank | typed bridge / degree-normalized PPR + provenance map-back ]
  -> one retry maximum (evaluate 0/1/2)
  -> persist trajectory + stop reason
  -> unchanged packing/generation OR explicit insufficient-evidence outcome
```

This is not the most autonomous 2026 architecture; it is the right **controlled experiment** to decide whether more autonomy is warranted.

---

## 8. Limitations & Open Questions

- **Source maturity:** much of the strongest 2026 evidence is preprint/workshop with small samples — A2RAG and AgenticRAGTracer use sampled benchmarks; ScoreGate uses 200 MS MARCO queries + an internal n=300; the traversal-provenance study uses 30 questions. Mechanisms are informative; **no single reported number is treated as load-bearing**, and figures are quoted with sample sizes.
- **Local unknowns:** the reliability of current `ce_confidence`/channel scores and whether the ontology graph encodes enough relation + provenance metadata for bridge/PPR retrieval *without a rebuild* cannot be settled until Slice A exports real traces. No retrieved source establishes a universal score threshold or an optimal retry cap — both are local empirical questions.
- **Shared blind spot / genuine novelty (UNRESOLVED — no direct evidence retrieved):** no 2026 source studies *deterministic corrective retrieval on an ontology-guided clause graph for regulatory compliance*. Nearest neighbours are graph-compliance systems (GraphCompliance [S22], LegalGraphRAG [S23], ComplianceNLP [S24]) but not corrective-loop calibrations. Phase 12 operates slightly ahead of published domain-specific precedent — a novelty, not a flaw, but external validation is thin, which raises the value of the internal held-out protocol.

---

## 9. References

*Maturity key: [PR] peer-reviewed/accepted · [PP] arXiv preprint · [WS] workshop · [SB] small/internal benchmark · [VG] vendor/production guide.*

**Local design context**
- **[P1]** Phase 12 — Agentic `graphont` Retrieval-Quality Loop — `.planning/phases/12-agentic-graphont-retrieval-quality-loop/12-01-PLAN.md` — 2026-07-13 — the design under review.
- **[P2]** T3 Mid Report: Aether CCoP — `report/term3-mid/T3-Mid-Report-Sagar-1010736-Aether-CCoP.pdf`, §§11–19 — 2026 — existing ontology-guided multi-channel `graphont` pipeline + additive-mode rationale.

**Retrieved external sources**
- **[S1]** [A2RAG: Adaptive Agentic Graph Retrieval for Cost-Aware and Reliable Reasoning](https://arxiv.org/abs/2601.21162) — updated 2026-06-04 [PP][SB] — evidence-sufficiency checks, local→bridge→PPR escalation, provenance map-back, bounded retries; the "2026 envelope."
- **[S2]** [Corrective Retrieval Augmented Generation (CRAG)](https://arxiv.org/abs/2401.15884) — 2024-01-29 [PR] — trained T5 evaluator + 3-way corrective action (plan's gate concept).
- **[S3]** [Open-Source Reproduction & Explainability of CRAG](https://arxiv.org/abs/2603.16169) — 2026-03-17 [PP] — CRAG gate behaves as entity-matcher; domain-transfer weakness.
- **[S4]** [From RAG to Memory: HippoRAG 2](https://proceedings.mlr.press/v267/gutierrez25a.html) — ICML 2025 (2025-07) [PR] — PPR + passage integration + online LLM; 59.8 vs 57.0 avg F1.
- **[S5]** [Adaptive-RAG](https://aclanthology.org/2024.naacl-long.389/) — NAACL 2024-06 [PR] — trained complexity classifier; no/single/iterative routing.
- **[S6]** [Is Agentic RAG worth it?](https://aclanthology.org/2026.acl-industry.5/) — ACL Industry 2026-07 [PR] — enhanced vs agentic RAG cost/benefit.
- **[S7]** [Do We Still Need GraphRAG? Benchmarking RAG & GraphRAG for Agentic Search](https://arxiv.org/abs/2604.09666) — 2026-04-01 [PP][SB] — matched-budget agentic dense vs graph; graph strongest on multi-hop.
- **[S8]** [ScoreGate: Adaptive Chunk Selection via Dual-Score Statistical Fusion](https://arxiv.org/abs/2606.14269) — 2026-06-12 [PP][SB] — no-extra-call bi-/cross-encoder cardinality gating; MRR@10 0.401, −35% chunks; zero *observed* FPs (internal n=300).
- **[S9]** [AgenticRAGTracer: Hop-Aware Benchmark for Multi-Step Retrieval Reasoning](https://arxiv.org/abs/2602.19127) — ACL Findings 2026 (updated 2026-07-02) [PR][SB] — premature-collapse & over-extension failures.
- **[S10]** [What Breaks Knowledge-Graph-based RAG? (BRINK)](https://aclanthology.org/2026.eacl-long.114/) — EACL 2026 [PR] — KG incompleteness; retrieval-vs-reasoning failure mix; missing-path failure.
- **[S11]** [WildGraphBench](https://arxiv.org/abs/2602.02053) — updated 2026-02-03 [PP][SB] — GraphRAG aggregation vs fine-grained detail loss.
- **[S12]** [Completing Missing Annotation / DREAM](https://arxiv.org/abs/2602.06526) — ICLR 2026 (2026-02-06) [PR] — 29,824 missing relevant chunks distort retriever/RAG conclusions.
- **[S13]** [Coverage, Not Averages: Semantic Stratification for Trustworthy Retrieval Evaluation](https://arxiv.org/abs/2604.20763) — 2026-04-22 [PP] — evaluation-set coverage bias; stratification.
- **[S14]** [From BM25 to Corrective RAG: Retrieval Strategies for Text-and-Table Documents](https://arxiv.org/abs/2604.01733) — 2026-04 [PP][SB] — hybrid+rerank Recall@5 0.816 vs 0.695; CRAG-like correction 0.658.
- **[S15]** [Why Neighborhoods Matter: Traversal Context & Provenance in Agentic GraphRAG](https://arxiv.org/abs/2605.15109) — 2026-05 [WS][SB] — visited-but-uncited context matters; provenance should include paths.
- **[S16]** [Beyond Relevance: Retrieval vs RAG Information Coverage](https://arxiv.org/abs/2603.08819) — ICTIR 2026 (updated 2026-06-20) [PR] — coverage-metric/objective alignment; iterative pipelines decouple.
- **[S17]** [When More Reformulations Hurt: Avoiding Drift using Ranker Feedback](https://arxiv.org/abs/2605.00560) — SIGIR 2026 (2026-05-01) [PR] — query-drift risk; budget-aware reformulation.
- **[S18]** [TASR: Training-Free Adaptive Stopping for Iterative Retrieval](https://arxiv.org/abs/2606.13814) — KDD'26 workshop (2026) [WS] — a *post-generation stopping* study; when reranker/BM25 signals were added as OR-votes in its stopping rule, macro-F1 dropped (−4..−14 reranker / −3.5..−17.9 BM25) and an OR of ~50%-firing signals fires ~75%. Used here **only** for the two scoped cautions in §4.1 (topicality ≠ answer support; OR-of-soft-triggers overfires) — not as evidence about pre-generation retrieval gating.
- **[S19]** [Breaking the Static Graph: Context-Aware Traversal for Robust RAG (CatRAG)](https://arxiv.org/abs/2602.01965) — ACL Findings 2026 [PR] — "Static Graph Fallacy": PPR mass drifts into high-degree hub nodes → partial recall, broken chains; Full-Chain-Retrieval metric.
- **[S20]** [Agentic RAG: Enterprise Implementation Guide (2026)](https://sumatosoft.com/blog/agentic-rag-enterprise-implementation-guide) — 2026 [VG] — agentic RAG token cost 3–10× traditional.
- **[S21]** [Adaptive Retrieval for Reasoning](https://aclanthology.org/2026.acl-long.1734.pdf) — ACL 2026 [PR] — "bounded recall problem": reranking cannot recover docs absent from the pool.
- **[S22]** [GraphCompliance](https://arxiv.org/abs/2510.26309) — 2025 [PP] — policy/context-graph compliance reasoning (domain neighbour; cited in report §12/§18).
- **[S23]** [LegalGraphRAG](https://aclanthology.org/2026.acl-long.1738.pdf) — ACL 2026 [PR] — multi-granular legal GraphRAG (domain neighbour).
- **[S24]** [ComplianceNLP: KG-Augmented RAG for Regulatory Gap Detection](https://arxiv.org/abs/2604.23585) — 2026 [PP] — regulatory KG-RAG (domain neighbour).
