# Roberto's P2 Critique of Robin's Independent Artifact

**Reviewer**: Roberto (claude-opus-4-8)
**Target**: `scratchpad/agentic-rag-critique-robin.md`
**Date**: 2026-07-13

## Verdict up front

Robin's artifact is **strong, rigorous, and largely correct**. It is more thorough than mine on mechanistic fidelity and evaluation protocol, and it converges with mine on every load-bearing conclusion (detector is the #1 risk; OR-rule over-triggers; graph expansion needs hub protection; calibration set too small; GT incompleteness; `weak-focus→wider` is wrong; deferring RoG is justified for v1). This is high-confidence convergence. My critique below is tough-but-fair on the places where Robin's framing, evidence-weighting, or scope should be tightened before we merge.

---

## 1. Approach — sound, with one framing tension to resolve

**Strong.** Robin correctly reframes the design as a *bounded corrective/adaptive retrieval state machine* rather than "agentic RAG," and rightly notes a negative result would only disprove *this fixed controller*, not agentic RAG in general. That scientific-scoping point is genuinely valuable and I concede it improves on my artifact, which accepted the "agentic" label more readily.

**Concern (framing tension).** The executive summary's "**sound … but not current agentic-RAG best practice**" and "**materially below the 2026 design envelope**" sit in tension with the plan's *explicit, deliberate* v1 constraints (no extra LLM; RoG/ReAct/reformulation deferred). Much of what Robin holds up as the "envelope" — A2RAG's LLM-driven sufficiency verification, query-aware *LLM-per-edge* weighting, answer verification — requires exactly the LLM calls the plan bans for v1. Robin does reconcile this in the P2 recommendations ("only if v1 plateaus"), but the top-line framing can read as faulting the plan for not doing what it consciously deferred. **Proposed fix for FINAL:** state plainly that v1 is *correctly scoped as a controlled experiment* and that "below SOTA autonomy" is a deliberate design choice, not a defect — then present the richer designs as *escalation options gated on evidence*. This aligns our two artifacts (I concluded "deferral justified"; Robin substantially agrees) and removes the mixed signal.

**Nit (proportionality).** The naming debate (agentic vs agentic-lite) consumes a full subsection plus P0-recommendation #1. It's worth ~2 sentences in the FINAL, not a headline recommendation — it's a documentation/claim-hygiene point, not a technical flaw that blocks implementation.

## 2. Methodology — evidence-gating is sound; a few numerics are load-bearing on single preprints

**Verified.** I independently re-searched Robin's three most decision-critical external sources and confirm they are **real and correctly attributed**: A2RAG (arXiv 2601.21162), AgenticRAGTracer (arXiv 2602.19127 = ACL Findings 2026, 2026.findings-acl.66), and BRINK/"What Breaks KG-RAG" (EACL 2026, 2026.eacl-long.114). No fabrication concern. Robin's search rigor is good and its source set is complementary to mine (little overlap beyond CRAG/ScoreGate/Adaptive-RAG/HippoRAG 2/"Is Agentic RAG worth it").

**Concern (single-preprint load-bearing).** Several *specific numeric* claims each rest on one preprint and are used to drive recommendations:
- A2RAG's "relation-seeding ablation reduced Recall@2 by 6.3 and 7.4 points" and "~50% lower token use" — anchors the "make expansion relation-aware" and "bounded escalation" recs, and A2RAG is positioned as *the* 2026 design envelope.
- S14 "Recall@5 0.816 vs 0.695 … CRAG-like correction 0.658" — anchors the "hybrid+rerank is a mandatory comparator" rec.
- S12 "29,824 missing relevant chunks" and S9 "GPT-5 22.6% EM on 4-hop."

Robin *does* hedge each with preprint/sample-size caveats (commendable, and better than most). But because these numbers will carry evidential weight in the merged artifact, **I recommend we (a) down-weight any single-preprint number that anchors a P0/P1 recommendation, or (b) fetch the full text to confirm the exact figure before it lands in FINAL.** I fetched full text for my load-bearing sources (TASR, ScoreGate, CatRAG); Robin's artifact cites mostly from search-snippet + review-site level, which is acceptable but a notch less verified for exact figures.

**Gap (missed a directly-on-point primary source).** Robin supports the OR-rule over-trigger risk and the detector-signal risk with *general reasoning* and the CRAG-reproduction's entity-matcher finding. It does not cite **TASR (arXiv 2606.13814, KDD'26)**, which I fetched in full and which provides the single strongest *quantitative* anchor for both of our shared P0 conclusions: (i) adding a cross-encoder reranker or BM25 retrieval-confidence score as a gating signal *hurt* F1 by 4–14 and 3.5–17.9 points respectively because the reranker "scores topicality rather than support for the answer," and (ii) OR-combining ~50%-firing signals fires ~75% of the time, so the winning form is an **AND-gate over the single best signal**. This is decisive evidence for exactly the two things Robin argues qualitatively. **FINAL should incorporate TASR as the primary support here.**

## 3. Content — accuracy, gaps, and where each of us is stronger

**Where Robin is clearly stronger (adopt into FINAL):**
1. **Mechanistic-fidelity table (§3).** The point that "CRAG-style/HippoRAG-style/Adaptive-RAG" are *directionally* not *mechanistically* aligned (CRAG = trained T5 evaluator + 3-way + external search; HippoRAG 2 = PPR + recognition memory + online LLM; Adaptive-RAG = trained complexity classifier) is sharper than my treatment and should anchor the FINAL's "labels vs reality" framing.
2. **Counterfactual evaluation design (§5):** the *retry-ablation* (regenerate with retry-only clauses removed) and *offline action-oracle* (run all actions per weak case, measure conditional utility) are excellent, more rigorous causal tests than my artifact proposed. Adopt both.
3. **Action policy built from observed failures** (§4.3 table) is more concrete than my one-line route fix.
4. Evaluation-integrity depth: freeze/split/pool/stratify/bootstrap + explicit stop/abstain outcome. Adopt.

**Where my artifact is stronger (merge in):**
1. **TASR quantitative anchor** (above) — the hardest evidence for the shared detector/OR conclusions.
2. **CatRAG / "Static Graph Fallacy" (arXiv 2602.01965, ACL Findings 2026)** names the *exact* mechanism behind the CII-hub risk: PPR probability mass diffusing into high-degree hub nodes → high partial recall, broken evidence chains, plus a Full-Chain-Retrieval metric. Robin cites BRINK (incomplete-graph) and WildGraphBench (detail loss) for graph failure modes — complementary but less precisely on-point for *graphont's* specific `CII` hub (296 clauses, ~⅓ of graph). **Merge: BRINK + CatRAG together.**
3. **Explicit tie to `graphont`'s existing rarity-gate (report §16.2)** as the ready-made mitigation for hub drift, and reuse of Stage-1 concept selection as a *no-new-LLM* query-aware edge filter. Robin's "degree-normalized PPR / bridge discovery" is good but heavier; the FINAL should present the cheap-reuse option first (respects the no-LLM constraint) and PPR/bridge as escalation.

**Accuracy check — minor.**
- Robin's claim that "one bounded retry … can prematurely stop genuine multi-hop cases" is right, but note the plan's loop *only* retries weak cases and always generates after the cap — so the failure is "under-recovery," not "premature stop of a live trajectory." Small precision point for the FINAL.
- The "25% of detector-positive cases" exit thresholds are explicitly flagged by Robin as non-evidence-based governance numbers — good. Keep them clearly labeled as proposals so they don't read as retrieved facts.

**Shared blind spot (both artifacts).** Neither of us found a 2026 source studying deterministic corrective retrieval specifically on an *ontology-guided clause graph for regulatory compliance*. Robin's domain neighbours (BRINK, WildGraphBench) and mine (GraphCompliance, LegalGraphRAG, ComplianceNLP) are the closest. FINAL should state this as a genuine novelty/limitation, not paper over it.

## 4. Concrete convergence proposals (for P3)

1. Merge the two source sets; **lead the detector/OR critique with TASR**, the graph-hub critique with **CatRAG + BRINK**, and the fidelity critique with **Robin's mechanistic table**.
2. Resolve the framing tension: v1 is *correctly scoped*, not "below SOTA" — present richer autonomy as **evidence-gated escalation**.
3. Adopt Robin's **counterfactual tests** (retry-ablation, action-oracle) and my **rarity-gate/Stage-1-reuse** as the cheap, no-LLM expansion guard.
4. Compress the naming debate to ~2 sentences.
5. Down-weight or full-text-verify any single-preprint numeric that anchors a P0/P1 rec before it enters FINAL.

**Signal:** AGREE on ~90% of substance; the above are refinements, not disputes. Ready for P3 convergence.
