# Agentic-RAG Integration for `graphont` — Plan

**Date:** 2026-07-12 (Rev 2: 2026-07-12, agentic re-frame)
**Status:** Rev 2 — draft for parent review (agentic re-frame, per parent feedback)
**Target metric:** D6 (clause-citation correctness), currently **0.278**
**Mode:** Planning only — no code changes proposed in this document

> **"Agentic" for this plan:** the LLM sits *inside* the retrieval / verification loop — deciding when
> to re-retrieve and whether each cited clause actually *supports* the claim — instead of running a
> fixed single-shot `retrieve → generate`. Control flow **branches on model / confidence signals**; it
> is not a straight line.

---

## 1. Executive summary

- **Goal.** Raise clause-citation correctness (D6, currently 0.278) and lift retrieval quality inside `graphont` by building a **composed agentic-RAG loop** — an *iterative* corrective / KG-guided retrieval loop *plus* a Self-RAG-style post-hoc citation critic — delivered as a new additive mode. **Agentic = the LLM sits inside the retrieval / verification loop** (branches on confidence / model signals), not a single-shot `retrieve → generate`.
- **Delivery shape — agentic core, hygiene co-shipped.** Ship a new `--mode graphont-agentic` containing the **agentic core**:
  - **Iterative corrective-retrieval loop** (CRAG-lite on the free `ce_confidence` signal, HippoRAG-PPR-first re-query ladder, capped) — *Option A*.
  - **Self-RAG post-hoc citation critic** (content-support vs actual clause text, regenerate ≤1) — *Option B′*.

  A **deterministic inventory-existence citation gate** (*Option B*) is **co-shipped alongside** as cheap, safe hygiene — explicitly *not* the headline and *not* agentic. The full build mirrors how `graphont` / `graphcpl` were each added as separate `route_by_mode` branches; `graphont` is the unchanged control, `graphont-agentic` is the experiment. Rollback is trivial.
- **Diagnostic-first — tunes emphasis within the agentic build.** D6 is scored against a **static 883-entry clause inventory** plus a judge LLM doing content fidelity, *independent* of this-turn retrieval. The Slice-1 2×3 confusion table tells us the **error mix** and therefore **how much each agentic component pays off for D6** — it *tunes emphasis and sequencing within the agentic build*; it is **not** a go/no-go that could cancel the agentic effort.
- **No-regret first ship.** Slice 1.5 (inventory-existence hygiene gate) is **monotonically non-harmful to D6** and adds **zero** model calls — it can ship in isolation while the agentic Slices 2–3 build out behind it.
- **Cost ceiling.** Slices 1 + 1.5 = **+0** model calls across 435 cases. Slice 2 (B′ critic) = **+≤1** batched OpenRouter grader + **+≤1** Ollama regen per case. Slice 3 (A loop) = **+0** LLM (HippoRAG PPR + deterministic levers + ≤1–2 rerank passes). Slice 4 (RoG, optional) = **+≤1** Ollama. The full agentic stack is bounded and deterministic.

---

## 2. Current state recap — `graphont` today

- **What it is.** A LangGraph branch `query_analysis → route_by_mode(=="graphont") → omd_context_assembly → generate → END`. The retriever is **OMD-GraphRAG** (the Term-3 build): a typed Neo4j KG with `:Concept` / `:Clause` / `:Definition` nodes and `:INVOKES` / `:REL` edges. Tri-channel ranking — graph Channel-I (IDF overlap) ⊕ in-memory BM25 ⊕ bge-large dense — fused by **weighted RRF** (`W_GRAPH=1.0, W_BM25=0.7, W_DENSE=1.5`, `RRF_K=60`), then **cross-encoder rerank** (`bge-reranker-large`), hardcoded **top-k=8**. A glossary-definition injector feeds grounding concepts into the context. One `omd_retrieval.retrieve()` call, **single-shot**.
- **Store.** Neo4j (`rag/graph/ontology_v2/_neo.py`), build-ID `omd-v1-20260709`. **Qdrant is the older `hybrid` mode, not `graphont`** — agentic changes here do not touch it.
- **Citation path.** `generate` builds the `**Sources:**` footer via `build_citations_from_state → parse_citations` (a pure footer parser in `citations/resolver.py`). The docstring claims unsupported clauses are dropped — **the code does no such check.** There is **no verification anywhere in `graphont`** that a cited clause ID was actually retrieved this turn, and no feedback from generation/citations back into retrieval. **The judge scores citation correctness post-hoc; the pipeline never gates on it.**
- **Known retrieval gaps (in-code).** Equal-weight RRF dilutes single-channel-strong hits; **Channel-II community-report retrieval is not built**; some clauses (Act §7, RtF §2.3) are still missed. `ce_confidence` / `ranked_by` / `d_cand` are **computed and discarded** by `omd_context_assembly`.
- **Silent failure mode.** On empty retrieval, `omd_context_assembly` writes `retrieval_succeeded=False` and still edges to `generate` — no fallback net.
- **What's not here.** No `grade_documents`, no `decide_after_grading`, no tool-calling, no re-query, no agent loop. The branch is a linear DAG. (Those nodes exist in the **hybrid** mode; they do not apply to `graphont`.)

---

## 3. Agentic-RAG research summary

*All citations were live-sourced from `arxiv.org` on 2026-07-12 and verified by abstract read; quotes are verbatim.*

- **What agentic RAG is.** The 2025 survey (arXiv 2501.09136) defines agentic RAG as embedding "autonomous AI agents into the RAG pipeline" with "reflection, planning, tool use, and multi-agent collaboration" to "dynamically manage retrieval strategies, iteratively refine contextual understanding, and adapt workflows" — structurally a **cyclic graph** over retrieval, not a one-shot DAG.
- **Text-RAG agentic patterns directly relevant to our metric.**
  - **Self-RAG** (arXiv 2310.11511) — reflection tokens for retrieve-on-demand and self-critique; reports "significant gains in improving factuality **and citation accuracy** for long-form generations." This is the only cited family that targets our exact metric.
  - **CRAG** (arXiv 2401.15884) — a "lightweight retrieval evaluator" returns a confidence degree and triggers corrective actions; "decompose-then-recompose" filter. Uses web search as a fallback — **wrong for our closed regulatory corpus**; substitute corpus-internal re-query.
  - **Adaptive-RAG** (arXiv 2403.14403) — trained query-complexity classifier routes no-retrieval / single-step / iterative; useful for cost control across 435 cases.
  - **FLARE** (arXiv 2305.06983), **IRCoT** (arXiv 2212.10509), **Self-Ask** (arXiv 2210.03350), **Rewrite-Retrieve-Read** (arXiv 2305.14283), **HyDE** (arXiv 2212.10496), **Step-Back** (arXiv 2310.06117), **ReAct** (arXiv 2210.03629) — all useful, none directly aimed at our metric.
- **KG-agentic patterns — the on-point cluster for our Neo4j clause graph.**
  - **ToG** (arXiv 2307.07697), **ToG-2** (arXiv 2407.10805) — LLM as agent doing beam search over the KG; "knowledge traceability and knowledge correctability" — for numbered clauses, every hop is an auditable citation chain.
  - **RoG** (arXiv 2310.01061) — relation-path planning → grounded retrieval → "faithful and interpretable" reasoning. The path *is* the citation chain.
  - **GraphRAG (Microsoft)** (arXiv 2404.16130) — LLM-built entity KG + Leiden community summaries for global sensemaking. This is exactly the in-code missing "Channel-II" gap.
  - **HippoRAG** (arXiv 2405.14831) — KG + Personalized PageRank; single-step matches iterative IRCoT at **10–30× cheaper, 6–13× faster** — a *cost* lever for any re-query ladder.
  - **Graph-CoT** (arXiv 2404.07103), **G-Retriever** (arXiv 2402.07630) — generic graph-traversal-as-tool / subgraph-selection patterns.
- **Citation / faithfulness evidence.**
  - **ALCE** (arXiv 2305.14627) — first automatic citation-eval benchmark; reports even the best systems "lack complete citation support 50% of the time." Closest public analog to D6.
  - **RAGAS** (arXiv 2309.15217) — reference-free retrieval/faithfulness metrics; useful vocabulary.
- **Honest gap.** **No fetched paper measures agentic clause-citation accuracy on a numbered regulatory corpus.** "Grounded KG path ≈ clause citation" is a well-motivated **hypothesis**, not a proven result. Treat as such.

---

## 4. Integration options

The options below are **additive** (new mode key, never mutate `graphont` in place), **state-safe** (graders are NODE-fns, not edge-fns — LangGraph's conditional edges do not persist state), and **iteration-capped** (every loop has a hard counter in `GraphState`).

**What "agentic" means here (and what it does not).** The LLM sits *inside* the retrieval / verification loop — branches on confidence / model signals. A pure set-membership string filter is **not** agentic (no LLM, no loop, no decision); we say so plainly so the agentic core does not get lost in the hygiene layer.

### Options matrix (pattern-tagged; "agentic?" column is visible)

| Option | Agentic pattern | Agentic? | Primary error mode addressed | LLM calls / case | D6 impact (honest) | Ship priority |
|---|---|---|---|---|---|---|
| **A** | **CRAG** (corpus-internal, no web) + **Adaptive / iterative** retrieval + **KG-guided** (HippoRAG PPR, RoG relation-path) | **YES** | **EXISTS-CORRECT-but-not-retrieved** (recall lever); also closes empty-retrieval hole | +0 decision; +≤1 `retrieve()` rerank pass (not an LLM); +≤1 Ollama if the ladder escalates to LLM query-rewrite | **Indirect ↑ on D6** (right clauses into context to cite); no direct effect on fabrication | **Slice 3** (the agentic core) |
| **B′** | **Self-RAG ISSUP** / post-hoc citation critic | **YES** | **EXISTS-MISATTRIBUTED** (real ID, wrong claim) — the only lever that touches this cell | +1 OpenRouter grader (batched) + ≤1 Ollama regen | **Direct ↑ on D6** for MISATTRIBUTED only; cannot see FABRICATED | **Slice 2** (the agentic core) |
| **B** | None — deterministic set-membership string filter against the static inventory | **NO — hygiene** | **FABRICATED** (the only mode a membership-check can see) | +0 | **Monotonically non-harmful to D6** (proven by ratio monotonicity); strips fabrication penalty | **Slice 1.5** (co-shipped hygiene, *not* headline) |
| **C** | **ReAct** (Thought → Action → Observation over graph tools) | YES, but DEFERRED | All of the above, plus multi-hop | +3–5 LLM calls/case | Best multi-hop; **worst determinism** for a batch evaluator; Primus has no tool-calling | **Out of scope** for the batch evaluator |

### Option A — Agentic corrective + iterative, KG-guided retrieval loop

- **Patterns.** Corrective RAG / CRAG (corpus-internal — no web fallback) + Adaptive / iterative retrieval + KG-guided retrieval (HippoRAG Personalized PageRank first; RoG relation-path planning as later escalation).
- **Pattern detail.** A grade **NODE** reads the free `ce_confidence` / `ranked_by` / `d_cand` / empty-retrieval signal (all already computed by `retrieve()` and discarded today). A conditional **edge** loops to a re-query NODE that re-invokes `retrieve()` with a deterministic ladder — **HippoRAG-PPR-first** (single-pass Personalized PageRank over `:REL`/`:INVOKES`) → widen `k` / deepen `RECALL_DEPTH` → flip channel weights (e.g. lift `W_DENSE`) → inject a targeted concept from a RoG-style plan. Capped at **≤1–2 passes**, then to `generate`.
- **Why genuinely agentic.** Control flow branches on a model / confidence signal (`ce_confidence < τ` or empty retrieval) and a re-retrieve decision is made inside the loop — the LLM sits in the control plane, not just the generation plane.
- **Touch points.** `omd_context_assembly.py` (split into `omd_retrieve` + `omd_pack` so the loop can re-retrieve without re-packing); **new** `nodes/omd_retrieval_grade.py` (NODE — persists `retrieval_grade`, `ce_confidence`); **new** `nodes/omd_requery.py` (NODE — bumps `requery_count`, sets `retrieval_overrides`); `graph/ontology_v2/omd_retrieval.py` (add PPR recall channel; existing levers already kwargs); `edges/routing.py` (new `decide_after_omd_grade` edge); `graph.py` (register on the `graphont-agentic` branch); `state/graph_state.py` (`+ce_confidence`, `+retrieval_grade`, `+requery_count`, `+retrieval_overrides`).
- **Cost / risk.** **+0 LLM calls** for the decision and for the HippoRAG-PPR-first pass; **+≤1** LLM if the ladder escalates to RoG path planning. **+1 `retrieve()` rerank pass** per re-query (cross-encoder rerank cost only, not an LLM call); moderate latency. Refactor risk in the assembly split. Empirical payoff depends on whether PPR / channel reweight actually recover the missed clause — to be measured in Slice 3's ablation.
- **Compatibility.** Works directly with the Neo4j tri-channel retriever and CE+RRF stage. `GraphState` needs the 4 new fields.
- **Evaluation.** retrieval recall@k vs ground-truth expected citations (coarse; see §5 caveat), 18-case κ bed A/B → 435; log `ranked_by` / `requery_count` per case to `-contexts.json`. Requires re-inference.

### Option B′ — Agentic Self-RAG post-hoc citation critic

- **Pattern.** Self-RAG ISSUP / post-hoc citation critic. After `generate`, an LLM verifies each cited clause's **claim-support against the actual clause TEXT** (not mere existence), and triggers one corrective regen if the citation is unsupported.
- **Pattern detail.** For each **EXISTS** CCoP-2.0 citation, fetch clause TEXT (mirror the judge's `_load_clause_text_cache` Qdrant CCoP-2.0 cache + `_resolve_clause_text` sub-letter parent fallback) and run **one batched** `temperature=0` support check across all citations. Unsupported → flag and regenerate **once** with a corrective instruction naming the mis-described clauses; cap `regenerate_count ≤ 1`.
- **Why genuinely agentic.** The LLM judges whether the generation is supported and decides whether to re-emit it — a model-based control decision inside the verification loop, not a string filter.
- **Why this is the only lever for MISATTRIBUTED.** A real clause with a wrong description is a real `(EXISTS)` ID from the inventory's perspective; Option B cannot see it. B′ checks *content support*, which is what D6's Step-2 fidelity scoring also checks. **Mirror the judge's text cache to avoid an eval/gate oracle split.**
- **Touch points.** **New** `nodes/citation_support_critic.py` (or extend the gate with a support-check subnode); clause-text cache helper; `routing.py` (regen edge + cap); `graph.py` (gate → generate → gate → END loop, capped). `generation.py` reused, not modified.
- **Cost / risk.** **+1 OpenRouter grader** (batched across all citations, `temperature=0`) **+ ≤1 Ollama regen** per case. Hard cap `regenerate_count ≤ 1`. **CCoP-2.0-only by default** (matches judge's text cache); other docs are EXISTS with no text to compare.
- **Optional support signal.** A **RoG-style `:REL`/`:INVOKES` path** as a *support signal* (grounded KG path ≈ citation chain) — **hypothesis, not proven** for numbered regulatory corpora. Keep optional.
- **Evaluation.** MISATTRIBUTED count ↓ (mined from existing judge justifications), D6 ↑; cap-prevention test; A/B on κ bed → 435.

### Option B — Deterministic inventory-existence citation gate (HYGIENE, NOT agentic)

- **Pattern.** None — pure set-membership string filter against the static 883-entry `clause_inventory.json` (reusing the judge's `_DOC_ALIASES` + `^(?:Section|Clause|§|Part|Chapter)\s+` stripping + sub-letter parent fallback).
- **Pattern detail.** After `generate`, a **node** extracts asserted clause IDs from the `**Sources:**` footer via `parse_citations` and classifies each `(doc, clause)`. **FABRICATED** (cited ID not in inventory) → strip from the visible generation text + `citations` before emit; log the pre-strip footprint to the `-contexts.json` sidecar. **EXISTS** and **EXTERNAL** → pass through untouched.
- **Stated honestly.** **This is a hygiene layer, not agentic** (no LLM, no loop, no decision). It is cheap, safe, and monotonically non-harmful to D6 — that is why we co-ship it; it is *not* the headline.
- **Why monotonically non-harmful to D6.** D6's ratio is `(CORRECT + 0.5·IMPRECISE) / (CORRECT+IMPRECISE+MISATTRIBUTED+FABRICATED)`. FABRICATED items contribute to the denominator but never to `correct_weight`. Stripping a FABRICATED citation either raises the ratio (mixed citations) or leaves it at D6=1 (all-fabricated → 0 citations → D6=1). The gate **cannot lower D6** *if* the inventory is complete; the only failure mode is **inventory incompleteness** (a real clause missing from `clause_inventory.json` → false-FABRICATED → strip a good citation). Mitigated by the Slice-1.5 n=100 stratified calibration.
- **Touch points.** `nodes/citation_grounding_gate.py` (shared with B′ where it makes sense; B runs first to filter FABRICATED, B′ then checks content support on what survives); `graph.py` (replace graphont's `generate → END` with a conditional edge: `graphont-agentic → gate`, all other modes → `END` — additive, leaves hybrid/graphcpl untouched); `citations/resolver.py` (reuse `extract_citation_ids()` and judge helpers); `state/graph_state.py` (`+cited_ids`, `+grounded_ids`, `+fabricated_ids`, `+citation_grounded`, `+regenerate_count`).
- **Cost / risk.** **+0 LLM calls.** Main residual risk is inventory coverage, not string alignment. Reuse the judge's `_DOC_ALIASES` and stripping regex; **do not** rebuild a citation_id/footer normalizer on 18 cases.
- **Compatibility.** `GraphState` needs the 5 new fields. Neo4j retriever and CE+RRF stage untouched. Citation resolver/formatter reused.
- **Evaluation.** D6 (primary) on the 18-case κ bed; **n=100 stratified calibration** (Q3b) for false-FABRICATED rate; 17-benchmark regression; A/B `graphont` vs `graphont-agentic`. Can run **post-hoc** on captured generations for a fast first read (no re-inference).

### Option C — ReAct graph-tool agent (deferred)

- **Pattern.** ReAct (Thought → Action → Observation over graph tools). Wrap `omd_retrieval` primitives as tools (`search_graph`, `get_definition`, `expand_neighbors`); an agent calls them iteratively for multi-hop / cross-clause Qs, bounded tool-call budget.
- **Why deferred.** **Primus has no tool-calling** — orchestrator would need a separate LLM (e.g. gpt-4o-mini), breaking our model-fixed ablation. **Least deterministic** of the four options — worst fit for a batch *evaluation* framework whose purpose is stable measurement. **Largest structural change**, hardest to eval/rollback. Reserve for interactive `query ask`.

---

## 5. Recommended plan

### 5.0 Headline — composed agentic loop is the architecture; hygiene gate rides alongside

> Build the **composed agentic loop** for `graphont`, as a new additive `--mode graphont-agentic`:
> an **iterative corrective-retrieval loop** (CRAG-lite on the free `ce_confidence` signal, with a
> **HippoRAG-PPR-first** re-query ladder, iteration-capped) **+ a Self-RAG-style post-hoc citation
> critic** (content-support vs the actual clause text, regenerate ≤1). That is the **agentic core**
> (Options A + B′). A **deterministic inventory hygiene gate** (Option B) is **co-shipped alongside** —
> cheap, safe, monotonically non-harmful — but is explicitly *not* the headline and *not* agentic.

**Role of the diagnostic (honesty preserved).** The Slice-1 2×3 confusion table tells us the **error mix** and therefore **how much each agentic component pays off for D6** — it **tunes emphasis and sequencing within the agentic build**; it is *not* a go/no-go that could cancel the agentic effort. The parent wants agentic RAG built; the diagnostic prioritizes *within* it.

### 5.1 Core insight (drives the sequencing)

> D6 is scored against a **static 883-entry clause inventory** + content fidelity (independent of this-turn retrieval). So the choice between B / B′ / A must be **data-gated by the Slice-1 confusion table** — not assumed.

### 5.2 The B / B′ / A decision framework (also tunes emphasis *within* the agentic build)

Slice 1 produces this 2×3 table (cells labelled by the recommended remedy):

|  | **retrieved** | **not retrieved** |
|---|---|---|
| **FABRICATED** | B (strip) | **B (strip)** ← the no-regret cell |
| **EXISTS — CORRECT / IMPRECISE** | (no action; already correct) | **A (re-query)** — do **not** ID-gate |
| **EXISTS — MISATTRIBUTED** | **B′ (content-support gate)** | **B′ + A** (gate + retrieve) |

**Reading the table:**
- **FABRICATED × retrieved** can occur only when a fabricated ID happens to lexically match a retrieved id (rare). B still strips it cheaply.
- **EXISTS-CORRECT × not-retrieved** is the documented Act §7 / RtF §2.3 recall miss case. A pure ID-membership gate (v1 Option B) would **wrongly strip these** and lower D6. **This is the exact failure mode of v1's Option B** and the reason the v2 revision switched the oracle from retrieval-membership to inventory-membership.
- **EXISTS-MISATTRIBUTED × anything** is the only case where Option B does nothing and Option B′ is required.

**How the table tunes emphasis (within the agentic build, not whether to build it):**
- If the table is **MISATTRIBUTED-dominant** → push Slice 2 (B′) hardest; Slice 3 (A) lower priority.
- If the table is **EXISTS-CORRECT-not-retrieved-dominant** → push Slice 3 (A) hardest; Slice 2 (B′) lower priority.
- If the table is **FABRICATED-dominant** → Slice 1.5 (B hygiene) is the biggest single win, and Slice 2's content critic has less to do.
- Mixed cells → ship all three; weighting per the table.

### 5.3 Vertical slices — each independently testable & shippable behind `--mode graphont-agentic`

> **Slice numbering has been re-sequenced per the v3 agentic re-frame.** Slices 2–4 are *all* agentic
> (with the B′ Self-RAG critic landing first because it directly targets D6's hardest penalty); the
> hygiene gate is **Slice 1.5** because it is non-agentic and *co-shipped alongside*, not headline.

#### Slice 1 — Diagnostic confusion table + scaffolding + regression test (enabling; 0 model calls)
- **Scope.** 2×3 confusion table `{FABRICATED, EXISTS-CORRECT/IMPRECISE, MISATTRIBUTED} × {retrieved, not-retrieved}` mined from the latest `--mode graphont` run + `-contexts.json` (deterministic axis replicating `_build_citation_verification_block`; fidelity axis from existing judge justifications; retrieval axis from the sidecar). Register `--mode graphont-agentic` as an exact clone of the graphont branch plus a log-only passthrough gate node. Wire CLI / settings / env: `CCOP_AGENTIC_REGENERATE_CAP`, `CCOP_AGENTIC_REQUERY_CAP`, `CCOP_AGENTIC_CE_CONF_TAU`.
- **Files touched.** new `scripts/` diagnostic; `edges/routing.py`, `graph.py` (`generate` out-edge → conditional: `graphont-agentic → gate`, **all else → END**), new `nodes/citation_grounding_gate.py` (log-only), `state/graph_state.py`, `infrastructure/config/settings.py`.
- **Test approach.** Unit-test classification against fixtures reusing judge helpers. **Regression test:** `mode=="graphont"` always resolves to the unconditional `generate → END` edge (guards a mode-typo reroute); assert `graphont-agentic` generations are byte-identical to `graphont` at this slice.
- **Success criteria.**
  - Confusion table produced; error mix known.
  - **Zero** behaviour change vs `graphont`; regression test green.
  - 0 model calls.

#### Slice 1.5 — Inventory-existence hygiene gate (co-ship; deterministic, NOT agentic; 0 model calls)
- **Scope.** Strip FABRICATED citations from the **visible** generation text; log pre-strip footprint to the `-contexts.json` sidecar (Q3a, decided). Leaves EXISTS / EXTERNAL untouched.
- **Honest residual risk (item 4 of the planner's review).** Not string alignment — that is solved by reusing the judge's normalizers. The residual risk is **inventory incompleteness** (a real clause missing from `clause_inventory.json` would be mislabelled FABRICATED and a good, judge-scored citation would be stripped). Mitigated by the **n=100 stratified calibration** (Q3b, decided): the calibration is stratified to cover the 6 not-yet-PDF-validated supporting docs, since CCoP-2.0's 415/883 inventory entries were audited complete on 2026-06-29. Extra n costs **0 model calls**.
- **Files touched.** Extend `nodes/citation_grounding_gate.py`; reuse `citations/resolver.py` + judge `_DOC_ALIASES` / stripping / sub-letter fallback.
- **Test approach.** Fixtures: fabricated → stripped; real-but-inventory-absent → NOT stripped; D6 non-decreasing on a held-out set. D6 monotonicity check.
- **Success criteria.**
  - D6 ↑ or held on the calibration sample.
  - False-FABRICATED ≈ 0.
  - Latency Δ ≈ 0.
  - 0 model calls.

#### Slice 2 — AGENTIC: Self-RAG post-hoc citation critic (Option B′) (+1 grader + ≤1 regen / case)
- **Scope.** For each **EXISTS** CCoP-2.0 citation, fetch clause TEXT (judge-mirrored Qdrant cache + parent fallback), run one batched `temperature=0` claim-support check; regenerate **once** (`regenerate_count ≤ 1`) naming unsupported clauses. **First genuinely-agentic slice; targets MISATTRIBUTED — which the hygiene gate cannot touch.**
- **Files touched.** New `nodes/citation_support_critic.py` (or extend the gate with a support-check subnode); clause-text cache helper; `edges/routing.py` (regen edge + cap), `graph.py` (gate → generate → gate → END loop); `generation.py` reused, not modified.
- **Test approach.** Real clause + wrong description → flagged / regen; cap prevents > 1 loop. A/B D6 on κ bed.
- **Success criteria.**
  - MISATTRIBUTED count ↓, D6 ↑.
  - Bounded calls; no infinite loop.

#### Slice 3 — AGENTIC: corrective / iterative retrieval loop (Option A) (+0 LLM for HippoRAG PPR + deterministic; ≤1–2 rerank passes)
- **Scope.** Split `omd_context_assembly` → `omd_retrieve` (stores raw `out` + `ce_confidence`) + `omd_pack`; add a CRAG-lite **grade NODE** on `ce_confidence < τ` / empty retrieval → **HippoRAG-PPR-first re-query ladder** (single-pass Personalized PageRank over `:REL`/`:INVOKES` → deterministic widen-k / flip-weights / targeted-concept comparators), `requery_count ≤ 1–2`. Closes the empty-retrieval hole + recall misses (Act §7, RtF §2.3).
- **Files touched.** `nodes/omd_context_assembly.py` (split); new `nodes/omd_retrieval_grade.py` + `nodes/omd_requery.py`; `graph/ontology_v2/omd_retrieval.py` (add PPR recall channel); `edges/routing.py` (`decide_after_omd_grade`); `graph.py`; `state/graph_state.py`.
- **Test approach.** Empty + low-confidence fixtures trigger exactly one re-query; PPR-vs-deterministic ablation on the coarse recall@k gold.
- **Success criteria.**
  - recall@k ↑ on Act §7 / RtF §2.3 at the lowest cost tier that works.
  - Empty retrieval no longer silent; no behaviour change on non-empty cases.

#### Slice 4 — AGENTIC, optional escalation: RoG concept-path planning / deeper multi-hop (+1 LLM / case)
- **Scope.** Only if Slices 2–3 leave residual recall gaps — an LLM relation-path plan over `:REL`/`:INVOKES` from query concepts, grounding retrieval in auditable graph paths. *(ToG-2 alternation + community-report / Channel-II remain out of scope, Option C tier.)*
- **Files touched.** New `nodes/concept_plan.py`; `omd_retrieval.py` (path-guided retrieval); `state`.
- **Test approach.** Ablation vs Slice-3 baseline on recall@k.
- **Success criteria.**
  - Incremental recall ↑ that justifies the +1 LLM/case at 435-scale.

### 5.4 Cost ceiling for 435 cases (re-numbered; agentic column visible)

| Slice | Agentic? | Extra OpenRouter (grader) | Extra Ollama (gen/regen) | Extra retrieve/rerank |
|---|---|---|---|---|
| 1 diagnostic | no (enabling) | 0 | 0 | 0 |
| 1.5 hygiene gate | **no (hygiene)** | 0 | 0 | 0 |
| 2 B′ critic | **yes** | **≤1** (batched) | **≤1** (regen) | 0 |
| 3 A loop | **yes** | 0 | 0 | **≤1–2** rerank passes |
| 4 RoG plan | **yes (optional)** | 0 or ≤1 | ≤1 | ≤1 pass |
| **All-on worst case** | | **≤435 total** | **≤~1300 total** | **≤~870 total** |

`temperature=0` on all graders; hard caps; per-decision logging to the sidecar for reproducibility. **Slices 1 + 1.5 are the "cheap and safe" floor** — ship in any case, with **zero** model calls.

### 5.5 Evaluation rigor (per planner §v2.5)

- **Primary oracle = the D6 judge itself** (rubric §D6). A/B `--mode graphont` (control) vs `--mode graphont-agentic` on the 18-case κ bed → then the **n=100 stratified calibration** (Q3b) for Slice 1.5 strip enablement → then the full 435. Log every gate / branch decision to the existing `-contexts.json` sidecar.
- **recall@k gold is coarse, not ready-made.** `metadata.clause_reference` in `ground-truth/test-suite/*.jsonl` is **reused, not purpose-built** — inconsistent formats (`["1.4.3", "section 11"]`), partial coverage. Usable as a **coarse** recall@k signal for Slice 3 / Slice 4 only; state the format / coverage gaps; do **not** present recall@k as clean. D6 (judge) remains the target metric; recall@k is a secondary retrieval-quality diagnostic.
- **Determinism.** `temperature=0` on Slice-2 graders; fixed caps; per-decision logging so agentic runs stay diff-able for an *evaluation* framework. **Q8 (open)** asks whether the added branching costs enough determinism to require multi-seed aggregate reporting.

### 5.6 Sequencing summary

```
Slice 1 (0 calls, enabling)
   │
   ├──► Slice 1.5 (0 calls, hygiene)  ← co-shipped, can land in parallel
   │        │
   │        └──► Slice 2 (AGENTIC, B′ critic, +1 grader + ≤1 regen)  ← targets MISATTRIBUTED
   │                  │
   │                  └──► Slice 3 (AGENTIC, A loop, +0 LLM)  ← targets EXISTS-CORRECT-not-retrieved
   │                            │
   │                            └──► Slice 4 (AGENTIC opt, RoG plan, +1 LLM)  ← if 2–3 leave gaps
```

The **confusion table** tunes emphasis *within* the agentic build (which slice to push hardest), not whether to build it. Each arrow is **independently shippable behind `--mode graphont-agentic`** and **independently reversible** (drop the node, restore unconditional `generate → END`).

---

## 6. Open questions / decisions for the parent

> Q3 is **DECIDED** (code-verified); Q1 / Q2 / Q4–Q8 are open and follow the planner's refreshed Q-list.
> The diagnostic (Q1) tunes emphasis *within* the agentic build, not whether to build it.

- **Q1 (open) — Error-mix / emphasis.** Which cell dominates the Slice-1 table (MISATTRIBUTED vs CORRECT-but-not-retrieved vs FABRICATED)? Tunes how hard we push Slice 2 (B′) vs Slice 3 (A) vs Slice 1.5 (B) — *within* the agentic build, not whether to build it. See §5.2.
- **Q2 (open) — B′ oracle fidelity.** Mirror the judge's Qdrant CCoP-2.0 text cache exactly; note MISATTRIBUTED detection is **CCoP-2.0-only** (accept, or extend the text cache to other docs?). Mirror-the-judge default avoids an eval/gate oracle split.
- **Q3 (DECIDED, code-verified) — Citation-gate strip policy + calibration.**
  - *Q3a = STRIP fabricated citations from the visible generation text + log the pre-strip footprint to the `-contexts.json` sidecar.* Rationale: the judge scores only the visible `response.content` (re-derived by regex), so annotation would still be parsed and penalised; the sidecar is judge-invisible, preserving audit fidelity.
  - *Q3b = n=100 calibration, STRATIFIED to cover the 6 not-yet-PDF-validated supporting docs.* CCoP-2.0's 415/883 inventory entries were audited complete on 2026-06-29, so false-FABRICATED risk is concentrated in the other 6 docs; extra n costs **0 model calls**.
- **Q4 (open) — Cost envelope → Slice 4.** Is ≤435 extra OpenRouter + ≤~1300 extra Ollama calls acceptable at 435-scale? Governs whether Slice 4 (RoG, +1 LLM/case) ships. Slices 1 + 1.5 + 2 + 3 are the bounded core; Slice 4 is the open cost question.
- **Q5 (open) — Mode vs flag.** `--mode graphont-agentic` (recommended, clean A/B, additive) vs an `--agentic` flag on graphont. **Recommend new mode** — parallels how `graphont` / `graphcpl` were each added as separate `route_by_mode` branches; trivial rollback.
- **Q6 (open) — Caps / threshold.** `regenerate_count ≤ 1`, `requery_count ≤ 1–2`, `ce_confidence` τ default (calibrate on the κ bed).
- **Q7 (open) — HippoRAG PPR feasibility.** Does the concept graph support a Personalized-PageRank pass (seed / edge-weight availability) without a new offline build step? Gates whether Slice 3's PPR-first re-query ladder is feasible as designed, or whether the ladder must default to deterministic widen-k / channel-flip levers.
- **Q8 (open) — Agentic determinism for an eval framework.** The B′ critic + retrieval loop add branching; is the reproducibility tradeoff acceptable, or do we need multi-seed / aggregate reporting?

---

## 7. Out of scope

- **Option C / ReAct tool agent / Primus tool-calling** — non-deterministic for a batch evaluator; reserve for interactive `query ask`.
- **ToG-2 graph↔clause-text alternation** — promising for deep multi-clause Qs; deferred until Slice 4c's single re-query proves insufficient.
- **Channel-II community reports (Microsoft GraphRAG)** — closes graphont's own documented "Channel-II not built" gap; separate workstream.
- **Judge / scoring subsystem** (`domain/services/llm_judge_service.py`) — unchanged.
- **Hybrid / Qdrant mode and its `grade_documents` / `decide_after_grading`** — the researcher's "enhance the grader" idea applies there, not here.
- **Fine-tuning / a trained Self-RAG critic** — prompted approximation only.

---

## Provenance

Synthesized by **SG-1** (studio-ssdlc). Inputs:

- `research/agentic-rag-graphont-integration-options.md` — planner options doc; **v2 (POST-REVIEW) and v3 (AGENTIC RE-FRAME)** sections are canonical; v3 supersedes v2's §1 / §4 / §5 / §6 framing in this Rev 2.
- `research/agentic-rag.md` — researcher live-sourced agentic-RAG report (abstracts fetched from arxiv.org on 2026-07-12; HTTP-200 verification on Neo4j GraphRAG + LangGraph tutorial URLs).
- Plan-reviewer critique (D6 metric mismatch + LangGraph conditional-edge state-persistence pitfall) — folded into v2 and into this plan.
- Scout code-contract map — verified against `src/rag/retrieval/graph.py`, `src/rag/retrieval/nodes/omd_context_assembly.py`, `src/rag/graph/ontology_v2/omd_retrieval.py`, `src/rag/citations/resolver.py`, `src/rag/retrieval/nodes/generation.py`, `src/rag/retrieval/state/graph_state.py`, `docs/phase-2/evaluation-rubrics.md` §D6, `src/domain/services/llm_judge_service.py`.

**Code contract captured in source documents; this plan introduces no code changes.**
