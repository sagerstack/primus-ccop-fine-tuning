# Research: Critical Evaluation of the Phase 12 "graphont-agentic" Bounded Retrieval-Quality Loop

**Date**: 2026-07-13
**Researcher**: Roberto (claude-opus-4-8)
**Status**: Draft (P1 independent artifact)

---

## 1. Executive Summary

- **The overall approach is sound and matches 2026 best practice.** The plan's core pattern — a retrieval-quality gate (CRAG) → bounded corrective action → graph-based recall recovery (HippoRAG) → lightweight routing (Adaptive-RAG), with no extra LLM and one bounded retry — is squarely in the mainstream of the corrective/agentic-RAG literature and is well-motivated by the project's own residual (citation D6 = 0.278; broken cross-document chains).
- **Its single biggest methodological risk is the weak-retrieval detector's reliance on retriever-side scores.** Fresh 2026 evidence (TASR) shows cross-encoder/reranker and retrieval-confidence scores are *poor* predictors of downstream answer correctness for a closely-related gating decision — the reranker "scores evidence topicality rather than support for the answer" and adding it *hurt* F1 by 4–14 points. The plan's `ce_confidence` / `top1_rerank` / margin signals are exactly this family.
- **The v1 rule shape (a large OR of conditions) will over-trigger retries.** TASR shows OR-combining signals that each fire ~50% of the time produces a combined trigger ~75% of the time, firing before evidence accumulates; the winning form was an **AND-gate over the single best signal**. The plan should invert its rule logic.
- **Graph-expansion recall recovery has a named, directly-applicable failure mode: the "Static Graph Fallacy" / hub-node semantic drift.** HippoRAG-style PPR diffuses probability mass into high-degree hubs, giving high partial recall but broken evidence chains — and `graphont`'s `CII` hub (296 clauses, ~⅓ of the graph) is precisely such a hub. The existing rarity-gate (report §16.2) is the right mitigation and must be preserved; a naïve one-hop `:REL`/`:INVOKES` expansion would regress.
- **Recommendation (one line):** Proceed with the plan, but (a) re-calibrate the detector to lead with an **answer/citation-grounding signal** and demote raw reranker scores, (b) replace the OR rule with a calibrated AND/single-signal gate, (c) protect graph expansion with the existing rarity-gate + a cheap query-aware edge filter reusing Stage-1 concepts, (d) add a **full-chain** retrieval metric and adjudicate the small GT calibration set, and (e) fix the `weak-focus → retry_wider` mapping (widening adds distractors).

---

## 2. Problem Statement

Phase 12 proposes an additive `graphont-agentic` mode: a deterministic, stateful loop that (1) detects weak `graphont` retrieval from internal signals, (2) applies one bounded corrective action (parameter-widening or graph expansion), and (3) re-assesses before generation — with GT used *offline only* for calibration, and RoG/ReAct/query-reformulation explicitly deferred. Success = weak retrieval reliably detected and one retry improves clause availability enough to lift citation accuracy/D6 *because retrieval improved*.

This artifact evaluates: (a) whether CRAG/HippoRAG/Adaptive-RAG remain SOTA-appropriate bases; (b) the soundness of the key design decisions (deterministic no-LLM detection, single bounded retry, graph-expansion recall recovery, GT-as-silver-oracle, additive mode); (c) gaps, errors, and failure modes; (d) whether deferring RoG/reformulation is justified. All claims are grounded in sources retrieved this session (§10).

---

## 3. Best Practices & Industry Standards (evidence)

- **Retrieval-quality gating is the established corrective-RAG pattern.** CRAG inserts a lightweight retrieval evaluator between retrieval and generation and triggers corrective retrieval when quality is low (arXiv 2401.15884). It remains a live, reproduced technique in 2026 (open-source reproduction 2603.16169; LangGraph/Milvus production guides, Jun 2026). **The plan's Slice 3 gate is a faithful, mainstream instantiation.**
- **Deterministic, no-extra-inference score-space gating is validated and current.** **ScoreGate** (arXiv 2606.14269, 12 Jun 2026) controls retrieval cardinality using *only the bi-encoder similarity and cross-encoder reranker score already produced* — "no additional model inference calls required" — and reports zero false positives at 97.8–99.3% recall on an internal benchmark and MRR@10 = 0.401 with 35% fewer chunks on MS MARCO. Its core insight ("cross-encoder affirmation can rescue chunks the bi-encoder ranks poorly") **directly supports the plan's deterministic detector** built from existing `graphont` scores.
- **Graph-expansion via Personalized PageRank is SOTA for multi-hop recall.** HippoRAG 2 (arXiv 2502.14802, ICML 2025, PMLR 267:21497) reaches 59.8 avg F1 vs 57.0 for NV-Embed-v2 across seven RAG benchmarks using query-to-triple PPR — validating graph-seeded expansion as a cheap recall-recovery step (the plan's Slice E basis).
- **Query-complexity routing is standard.** Adaptive-RAG (NAACL 2024, 2024.naacl-long.389) routes queries to no-/single-/multi-step retrieval so only hard cases pay the cost; 2026 work continues this (RAGRouter-Bench 2602.00296; Keiro). **The plan's "only weak cases pay the retry cost" is orthodox.**
- **Reranking alone cannot fix recall — the "bounded recall problem."** "Adaptive Retrieval for Reasoning" (ACL 2026, 2026.acl-long.1734): "any relevant document missing from the initial retrieval pool cannot be recovered by [reasoning-based] reranking." **This is the strongest external justification for the plan's premise** that a *recall-recovery* retry (widening / graph expansion), not better ranking, is what surfaces missed clauses.
- **Bounded, auditable, training-free control is a recognized virtue.** TASR (arXiv 2606.13814, KDD'26 workshop) shows a two-scalar, training-free stopping rule Pareto-dominates fixed budgets and learned controllers, and argues for auditability. **This validates the plan's interpretable-detector + `requery_count ≤ 1` cap over an LLM controller.**

## 4. Emerging Approaches (relevant, 2026)

- **Query-adaptive graph traversal** is the clear research frontier and the most important signal for the plan's graph-expansion slice: CatRAG / "Breaking the Static Graph" (arXiv 2602.01965, ACL Findings 2026), QAFD-RAG (ICLR 2026, flow diffusion with subgraph-recovery guarantees), FlowRAG (2026.findings-acl.1050), DOTRAG (2605.18760, retrieval-time reasoning along paths). Maturity: early-research/experimental but converging.
- **Answer/generation-usefulness signals** rather than relevance scores: CAR confidence-aware reranking (2605.04495), Confidence-Gated RAG (OpenReview 5BOaSaHY6t), Interpretable Uncertainty for Adaptive Retrieval (2607.07380), calibrated retrieval-budget allocation (2606.29959). Maturity: early but well-motivated.
- **Evaluation-integrity tooling** for incomplete/silver ground truth: PRECISE prediction-powered inference (AAAI 2026, 2601.18777), DREAM multi-agent relevance adjudication (2602.06526), topic-specific classifiers vs prompted-LLM judges (Gienapp 2026), formalized information needs for LLM judges (2604.04140). Maturity: production-adjacent.

## 5. Comparative Analysis — plan decision vs. evidence

| Plan decision | Evidence verdict | Notes |
|---|---|---|
| CRAG-style quality gate before generation | **Sound / mainstream** | 2401.15884; reproduced 2026 |
| Deterministic no-LLM detector from existing scores | **Sound, with a caveat** | ScoreGate 2606.14269 validates the *mechanism*; TASR warns the *specific signals chosen* (reranker/retrieval scores) are weak for answer-correctness gating |
| v1 rule = OR of many weak conditions | **Weak / likely over-triggers** | TASR: OR of ~50%-firing signals → ~75% trigger rate; AND-gate over best single signal won |
| HippoRAG-style graph expansion (Slice E) | **Sound but hazard-prone** | HippoRAG 2 SOTA; but Static Graph Fallacy (2602.01965) → hub-node drift; `CII` hub is a textbook hazard |
| Single bounded retry (`requery_count ≤ 1`) | **Sound** | TASR/BCAS (2603.08877): agentic cost is 3–10× tokens; bound the loop |
| `weak-focus → retry_wider` | **Design error** | Widening k adds distractors; weak-focus needs pruning/diversification, not more recall |
| GT as offline silver oracle only | **Correct discipline, incomplete-judgment risk** | NIST incompleteness; 2604.04140; adjudicate/pool the small set; PPI (2601.18777) if scaling |
| Defer RoG / query-reformulation / ReAct | **Justified for v1** | Agentic cost (2501.09136 survey; acl-industry.5); attribution/determinism concerns valid |
| Additive `graphont-agentic` mode (ADR-008) | **Best practice** | Backward-compat + clean ablation; matches report §14 |

## 6. Recommendation

**Proceed with the plan's architecture — it is correctly shaped — but apply five prioritized corrections before/inside calibration (Slice A/C/E/F/G):**

**P0 (integrity-critical):**
1. **Lead the detector with an answer/citation-grounding signal, not raw reranker scores.** The plan already lists "whether final generated citations were present in retrieved context" as a signal; make a *proxy for it* the primary weak-recall predictor in calibration, and treat `ce_confidence`/`top1_rerank`/margins as *secondary* until Slice A proves their separability. Rationale: TASR found retriever-side and cross-encoder signals fire on topicality, not answer-support, and *hurt* a related gate by 4–14 F1. This is the biggest risk to the whole phase.
2. **Replace the OR rule with a calibrated AND-gate or a single best-separating signal** (TASR). An OR of five weak conditions will inflate the requery rate and add distractor-driven noise, confounding the "did retrieval improve" measurement.

**P1 (design correctness):**
3. **Protect graph expansion from hub-node drift.** Keep the report's rarity-gate (§16.2) inside the retry, and add a cheap **query-aware edge filter** that reuses the Stage-1 selected concepts (no new LLM) to prune `:REL`/`:INVOKES` neighbours not aligned to the query — the deterministic analogue of CatRAG's symbolic anchoring / edge weighting. Otherwise `CII`-adjacent generic clauses will flood the merged pool.
4. **Fix `weak-focus → retry_wider`.** Route `weak-focus` to a **prune/diversify/rerank-only** action (or tighter k), not a wider pool.

**P2 (measurement):**
5. **Add a full-chain retrieval metric and adjudicate the calibration set.** Report a "all expected clauses present *together*" metric (à la CatRAG's Full-Chain Retrieval), because coarse GT recall@pool can rise while the multi-document bridge (e.g., B01's three-doc chain) stays broken. Manually pool/adjudicate the 20–40 calibration cases so incomplete GT does not mislabel good retrieval as weak.

## 7. Disadvantages & Limitations of the plan as written

- **Detector signal risk (P0-1).** Heavy dependence on `ce_confidence` and reranker top-1/margins, which 2026 evidence flags as weak correctness predictors; the report itself notes the reranker gives "undifferentiated / tightly-clustered scores on very short factoid questions" (§16.5, §17.1) — the exact regime where the gate must decide.
- **Over-triggering (P0-2).** OR rule inflates requery rate; higher latency and distractor injection, and it muddies attribution of any D6 gain to retrieval.
- **Hub-node drift (P1-3).** Graph expansion can raise partial recall while breaking evidence chains (Static Graph Fallacy).
- **Thin calibration set for many thresholds.** 20–40 cases across 18 benchmarks (~1–2 each) to fit `tau_conf, tau_top1, tau_margin, tau_coverage`. TASR found per-cell threshold tuning unreliable at *100* questions (7–9 F1 train/eval gap) and that a single locked threshold beat per-cell tuning by 0.18 F1. Over-fitting risk is high; prefer fewer knobs / a global threshold / held-out validation.
- **Silver-oracle bias.** Incomplete GT clause refs (NIST; 2604.04140) can both under-estimate true recall and mislabel calibration cases; thresholds fit to annotation gaps.
- **Query-agnostic expansion is already behind the frontier.** 2026 SOTA is query-conditioned traversal; the plan's deterministic one-hop expansion is the known-weak baseline the frontier improves on.

## 8. Implementation Guidance (concrete, minimal-diff)

- **Slice A/C:** In the trace capture, log per-case: (i) a citation-in-context proxy, (ii) reranker top-1/top-k/margins, (iii) per-channel provenance, (iv) concept coverage. Rank signals by held-out class-conditional separation (Cohen's d on strong-vs-weak), *not* tune-set fit (TASR §5.5 caution). Freeze the smallest rule that separates.
- **Slice E:** Reuse `graphont` Stage-1 concept selection as the anchor set; expand only rarity-passing concepts (existing gate); score candidate edges by query-concept alignment before merge; always rerank the merged pool (the plan already does). Cap neighbour fan-out per seed (CatRAG uses `K_edge=15`).
- **Slice F:** `empty → retry_wider`; `weak-recall → retry_graph_expand`; **`weak-focus → prune/rerank-only`**; else `accept`.
- **Slice G:** Track requery rate, action distribution, latency delta, before/after coarse GT recall, **full-chain presence**, and the causal metric "retry surfaced a later-cited clause." Compare baseline vs widen-only vs graph-expand on the *same adjudicated* set.
- **Optional (calibration only, no runtime LLM):** capture the generator's answer-token logit margin (à la FLARE/TASR) as an offline check on whether "weak" retrieval actually correlated with wrong answers — a sanity signal for the labels.

## 9. Open Questions & Risks

- Will an answer-grounding proxy be computable *pre-generation* deterministically? If not, the detector may need a post-generation re-entry (a different loop shape than the plan's pre-generation gate) — worth resolving in Slice A.
- Is `requery_count ≤ 1` sufficient for B01-style 3-document chains, or does full-chain recovery need ≤ 2 (the plan's deferred question)? Decide from full-chain metric, not aggregate recall.
- Does the rarity-gate alone tame the `CII` hub under expansion, or is query-aware edge weighting required? Test widen-only vs expand explicitly (the plan does).
- **UNRESOLVED (no direct evidence retrieved):** no 2026 source specifically studies deterministic corrective retrieval on *ontology-guided clause graphs for regulatory compliance*; nearest neighbours (GraphCompliance 2510.26309, LegalGraphRAG 2026.acl-long.1738, ComplianceNLP 2604.23585) are graph-compliance systems but not corrective-loop calibrations. The plan operates slightly ahead of published domain-specific precedent — a novelty, not a flaw, but external validation is thin.

## 10. References

- [Corrective Retrieval Augmented Generation (CRAG)](https://arxiv.org/abs/2401.15884) — 2024-01 — origin of the retrieval-quality gate + corrective action (plan's core basis).
- [Open-Source Reproduction & Explainability of CRAG](https://arxiv.org/pdf/2603.16169) — 2026 — CRAG still live/reproduced; T5 evaluator explainability.
- [ScoreGate: Adaptive Chunk Selection via Dual-Score Statistical Fusion](https://arxiv.org/abs/2606.14269) — 2026-06-12 — deterministic no-extra-inference gate from bi-/cross-encoder scores; validates plan's detector mechanism.
- [TASR: Training-Free Adaptive Stopping for Iterative Retrieval](https://arxiv.org/html/2606.13814v1) — 2026 — retriever/reranker scores are weak correctness gates (−4 to −18 F1); OR-signals over-fire; AND-gate over best single signal wins; auditability; threshold-tuning fragility.
- [HippoRAG 2 / From RAG to Memory](https://arxiv.org/html/2502.14802v2) — 2025-02 (ICML 2025) — PPR graph expansion SOTA (59.8 vs 57.0 F1); plan's Slice E basis.
- [HippoRAG (v1)](https://arxiv.org/abs/2405.14831) — 2024-05 — original PPR-over-KG memory retrieval.
- [Breaking the Static Graph / CatRAG](https://arxiv.org/html/2602.01965v1) — 2026 (ACL Findings) — "Static Graph Fallacy": PPR drifts into high-degree hub nodes → high partial recall, broken chains; Full-Chain-Retrieval metric.
- [Adaptive Retrieval for Reasoning](https://aclanthology.org/2026.acl-long.1734.pdf) — 2026 (ACL) — "bounded recall problem": reranking can't recover docs missing from the pool → justifies recall-recovery retries.
- [Adaptive-RAG](https://doi.org/10.18653/v1/2024.naacl-long.389) — 2024 (NAACL) — query-complexity routing; plan's routing basis.
- [RAGRouter-Bench](https://arxiv.org/pdf/2602.00296) — 2026 — adaptive-RAG routing benchmark.
- [SoK: Agentic RAG — Taxonomy/Architectures/Evaluation](https://arxiv.org/html/2603.07379v1) — 2026 — agentic-RAG framing and evaluation directions.
- [Agentic RAG: A Survey](https://arxiv.org/html/2501.09136v4) — 2025 — agentic RAG landscape.
- [Is Agentic RAG worth it?](https://aclanthology.org/2026.acl-industry.5/) — 2026 (ACL Industry) — enhanced vs agentic RAG cost/benefit; supports deferring heavy agency.
- [Budget-Constrained Agentic Search (BCAS)](https://arxiv.org/pdf/2603.08877) — 2026 — accuracy/cost of search depth under budgets; supports bounded retry.
- [ScoreGate/CAR: Confidence-Aware Reranking](https://arxiv.org/html/2605.04495) — 2026 — generation-usefulness > relevance for ranking signals.
- [Calibrated Retrieval-Budget Allocation](https://arxiv.org/html/2606.29959) — 2026 — when-to-retrieve as calibrated decision.
- [Confidence-Gated RAG for Sequential Agents](https://openreview.net/forum?id=5BOaSaHY6t) — 2026 — confidence-gated adaptive retrieval.
- [Interpretable Uncertainty for Adaptive Retrieval](https://arxiv.org/html/2607.07380) — 2026 — internal-signal uncertainty for adaptive QA.
- [PRECISE: Prediction-Powered Ranking Estimation](https://arxiv.org/abs/2601.18777v1) — 2026 (AAAI/IAAI) — correct LLM-judge/silver-label bias with few human annotations.
- [Retrieval Evaluation with Incomplete Information (NIST)](https://www.nist.gov/publications/retrieval-evaluation-incomplete-information) — incompleteness breaks standard IR metrics; silver-oracle caution.
- [Formalized Information Needs Improve LLM Relevance Judgments](https://arxiv.org/pdf/2604.04140) — 2026 — LLM-judge relevance reliability.
- [DREAM: Multi-Agent Debate for Relevance Assessment](https://arxiv.org/pdf/2602.06526v1) — 2026 — completing missing relevance annotations.
- [GraphCompliance](https://arxiv.org/html/2510.26309) — 2025 — policy/context graph compliance reasoning (domain neighbour; report §12/§18 cites it).
- [LegalGraphRAG](https://aclanthology.org/2026.acl-long.1738.pdf) — 2026 — multi-granular legal GraphRAG (domain neighbour).
- [ComplianceNLP: KG-Augmented RAG for Regulatory Gap Detection](https://arxiv.org/html/2604.23585v1) — 2026 — regulatory KG-RAG (domain neighbour).
- [Reasoning on Graphs (RoG)](https://arxiv.org/pdf/2310.01061) / [DOTRAG](https://arxiv.org/html/2605.18760v1) — 2023 / 2026 — LLM path-planning over graphs; the deferred alternative.
