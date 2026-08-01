# Planning: Agentic-RAG Integration Options for `graphont` Mode

**Date**: 2026-07-12
**Author**: planner agent (SG-1)
**Status**: v1 SUPERSEDED by §§ v2 (post-review) at the bottom of this doc — read v2 for the corrected impact claims, the B/B′/A decision framework, and the re-sequenced slices. v1 is retained for provenance.
**Inputs**: `research/agentic-rag.md` (researcher) + Scout code-contract map (verified against code this session) + plan-reviewer critique (D6 metric mismatch, verified against `docs/phase-2/evaluation-rubrics.md` §D6 + `domain/services/llm_judge_service.py`)

---

## 0. Reconciliation — researcher's report vs. the real `graphont` contract

The researcher's "stack-specific" recommendations (upgrade `grade_documents`, reuse
`decide_after_grading`, re-query the **Qdrant hybrid** retriever) describe the **SHARED/hybrid**
pipeline. **They do not apply to `graphont` as written.** Verified against code:

- **graphont topology** is `query_analysis → route_by_mode(=="graphont") → omd_context_assembly →
  generate → END`. It **bypasses** `reranking`, `grade_documents`, and `decide_after_grading`
  entirely (`graph.py`: `omd_context_assembly` has an unconditional edge to `generate`;
  `generate` has an unconditional edge to `END`).
- **graphont retrieves from Neo4j**, not Qdrant: tri-channel (IDF-weighted graph Channel-I ⊕
  in-memory BM25 ⊕ bge-large dense npz) → weighted RRF → confidence-adaptive cross-encoder rerank
  (`bge-reranker-large`), a **single** `omd_retrieval.retrieve()` call, hardcoded `_TOP_K=8`. Qdrant
  hybrid is a *different* mode. The researcher's "enhance `grade_documents`" idea belongs to that
  other mode.
- **Consequence:** for graphont you cannot "just enhance a grader node" — there is no grader in the
  branch. You must either **(i) insert NEW node(s) into the graphont branch**, or **(ii) wrap
  `omd_retrieval.retrieve()`**, or **(iii) route graphont through a new gated sub-graph.** All three
  options below take approach (i)/(ii), kept additive.
- **LangGraph gotcha (confirmed in `routing.py` comments + `graph.py` `function_type_routing`
  precedent):** conditional-**edge** functions do NOT persist state mutations — only **node** return
  values merge into `GraphState`. Any grader/gate whose output must survive **must be a NODE**; the
  branch decision that reads it is the edge.

### Newly-surfaced fact that reframes the whole task (verified in `generation.py` + `resolver.py`)

`generate` builds citations via `build_citations_from_state → parse_citations`, which is a **pure
`**Sources:**` footer parser**. Its docstring claims "citations referencing clauses not in the
retrieved set are dropped" — **the code does no such check.** There is currently **no verification
anywhere in graphont** that a cited clause ID was actually retrieved. The judge scores citation
correctness post-hoc, but the pipeline never gates on it. **This is the single most direct,
currently-unguarded lever on D6 citation-correctness (0.278, the number to beat).**

---

## 1. Signals already computed but unused (cheap wins)

- `omd_retrieval.retrieve()` returns `ce_confidence` (CE-score stdev/CONF_REF, ∈[0,1]),
  `ranked_by` (`"ce+rrf(conf=…)"` vs `"rrf"` vs `"none"`), `d_cand`, and per-channel candidate lists
  — **computed, but discarded** by `omd_context_assembly` (it only reads `results`/`definitions`).
  An agentic gate can branch on these with **zero** extra model calls.
- `retrieve()` already accepts every lever as a kwarg (`k`, `n1/k1/kd`, `w_graph/w_bm25/w_dense`,
  `rrf_k`, rerank weights) → a re-query pass can widen `k`, re-weight channels, or deepen recall with
  **no retriever change**.
- graphont has **no fallback net**: on empty retrieval `omd_context_assembly` silently writes
  `retrieval_succeeded=False` and still edges to `generate`. An agentic grade/gate closes this hole.

---

## 2. Design stance: additive & reversible

**Strongly additive.** Mirror how `graphont`/`graphcpl`/`graphrag-ontology` were each added as
separate `route_by_mode` branches. Introduce the agentic behavior as a **new mode key**
(`graphont-agentic`) routed to a graphont-specific sub-branch — **do not mutate the `graphont`
branch in place.** Rationale: (a) keeps a clean A/B control (`graphont` vs `graphont-agentic`) on the
same retriever; (b) trivial rollback; (c) `generate` is SHARED across hybrid/graphcpl/graphont, so
any post-generate gate must be mode-scoped to avoid collateral impact. **Iteration-cap everything**
(hardcoded-but-configurable) for batch reproducibility/cost across 435 cases; `temperature=0` on any
LLM grader; log every branch decision to the existing `-contexts.json` sidecar.

---

## 3. Integration OPTIONS

### OPTION A — Bounded CRAG-lite re-query loop on `ce_confidence` (retrieval-side)

- **Pattern**: Corrective-RAG, corpus-internal. A grade **node** reads the free `ce_confidence` /
  `ranked_by` / `d_cand` / empty-retrieval signal; a conditional **edge** loops to a re-query node
  that re-invokes `retrieve()` with a deterministic strategy ladder (widen `k`/recall depth → flip
  channel weights dense↔graph → inject a targeted concept), capped at **≤1–2 passes**, then to
  `generate`. No web fallback (closed corpus).
- **Touch points**:
  - `omd_context_assembly.py` — **split** into `omd_retrieve` (calls `retrieve()`, stores raw `out`
    + `ce_confidence`/`ranked_by`/`d_cand` in state) and `omd_pack` (builds Documents). Needed so the
    loop can re-retrieve without re-packing prematurely. *(Or keep monolithic and pass overrides via
    state — messier.)*
  - **NEW** `nodes/omd_retrieval_grade.py` (NODE — persists `retrieval_grade`, `ce_confidence`).
  - **NEW** `nodes/omd_requery.py` (NODE — bumps `requery_count`, sets `retrieval_overrides`).
  - `edges/routing.py` — **NEW** `decide_after_omd_grade` edge (grade→requery vs grade→pack/generate).
  - `graph.py` — register nodes + conditional edges on the `graphont-agentic` branch.
  - `graph/ontology_v2/omd_retrieval.py` — **no change** (levers already parameterized); optionally
    surface top-result score gap.
  - `state/graph_state.py` — add `ce_confidence: float`, `retrieval_grade: str`,
    `requery_count: int`, `retrieval_overrides: Dict`. *(Can reuse existing unused
    `retrieval_attempts`.)*
- **Expected impact**: ↑ retrieval recall@k on under-recalled clauses (named open problems: Act §7,
  RtF §2.3, RRF dilution, weak-CE-on-short-queries). Indirect ↑ on D6 (right clauses in front of the
  model to cite). Closes the empty-retrieval silent-proceed hole.
- **Costs/risks**: +0 model calls for the *decision* (uses free signals); +1 `retrieve()` per
  re-query pass (cross-encoder rerank cost, not an LLM call) — moderate latency, no token cost unless
  the ladder adds an LLM query-rewrite. Complexity: requires the assembly split (refactor risk).
  Empirical payoff (does any rewrite actually recover the missed clause?). LangGraph pitfall: grade
  MUST be a node.
- **Compatibility**: Works directly with the Neo4j tri-channel retriever and CE+RRF stage (levers are
  kwargs). No citation-resolver interaction. `GraphState` needs the 4 new fields above.
- **Evaluation**: retrieval recall@k vs ground-truth expected citations in `ground-truth/test-suite/`;
  A/B `graphont` vs `graphont-agentic` on the 18-case κ bed then 435; log `ranked_by`/`requery_count`
  per case to the sidecar. Requires re-inference (retrieval changes).

### OPTION B — Self-RAG clause-citation grounding gate before emit (generation-side) ★ primary

- **Pattern**: Self-RAG `ISSUP`-lite groundedness gate. After `generate`, a **node** extracts the
  asserted clause IDs from the `**Sources:**` footer and checks each against the retrieved
  `citation_id` set. Unsupported IDs are stripped (deterministic) and/or trigger **one** corrective
  regeneration. Directly targets the currently-unguarded citation path.
- **Touch points**:
  - **NEW** `nodes/citation_grounding_gate.py` (NODE — persists `cited_ids`, `grounded_ids`,
    `unsupported_ids`, `citation_grounded`; may rewrite `generation`/`citations`).
  - `graph.py` — replace graphont's `generate → END` with a **conditional edge** from `generate`
    routing `graphont-agentic → citation_grounding_gate`, all other modes → `END` (additive; leaves
    hybrid/graphcpl untouched). Gate → `END` (Slice 1–2) or gate →(regen)→ `generate` (Slice 3).
  - `citations/resolver.py` — reuse `extract_citation_ids()`; **NEW** `citation_id` normalization
    helper (footer `"<doc>: <clause>"` → canonical id) to align with omd `citation_id`.
  - `nodes/omd_context_assembly.py` — *optional* enrichment: add `document_type`/`clause` to omd doc
    metadata so `resolve_citations` enrichment path fires (currently omitted → unmatched-ID path).
  - `nodes/generation.py` — **no change** (gate is a separate node; regen reuses the existing node).
  - `state/graph_state.py` — add `cited_ids`, `grounded_ids`, `unsupported_ids: List[str]`,
    `citation_grounded: bool`, `regenerate_count: int`.
- **Expected impact**: **Direct ↑ on D6 citation-correctness (0.278 → target).** Every hallucinated
  clause ID (cited but never retrieved) is caught — the exact failure D6 penalizes. Retrieval-quality
  impact: none (retrieval unchanged); this is a faithfulness lever, not a recall lever.
- **Costs/risks**: Slice 1–2 = **+0 LLM calls** (pure set membership + string strip). Slice 3 regen =
  **+≤1 LLM call/case** (capped). Main risk = **citation_id ↔ footer alignment**: omd `citation_id`
  (from Neo4j `c.citation_id`, e.g. `CCoP 2.0::5.3.1`) vs model footer (`CCoP 2.0: 5.3.1`) may differ
  in doc-name spelling / clause punctuation → a naive membership check under- or over-strips. **Must
  calibrate normalization on the 18-case bed before trusting it.** Over-strip risk: a *correct*
  citation whose id merely fails to string-match gets removed → hurts D6. LangGraph pitfall: gate is a
  node; regen decision is the edge; `regenerate_count` capped in state.
- **Compatibility**: `GraphState` needs the 5 fields above. Neo4j retriever & CE+RRF stage untouched.
  Citation resolver/formatter: gate sits *after* `parse_citations`; the optional metadata enrichment
  makes `resolve_citations` richer but is not required for the membership check (which keys on
  `citation_id` present in omd docs).
- **Evaluation**: D6 citation-correctness (primary), citation precision/recall vs ground-truth
  expected citations; 18-benchmark LLM-Judge suite for regression; A/B on 18-case κ bed → 435. Slice 1
  is a **read-only audit** answering the researcher's diagnostic Q (is the error retrieval- or
  generation-side?). Requires re-inference only from Slice 3 (Slice 1–2 could be applied
  post-hoc/rescore-style on captured generations for a fast first read).

### OPTION C — ReAct retrieval agent with graph tools (structural, deepest)

- **Pattern**: ReAct Thought→Action→Observation. Wrap `omd_retrieval` primitives as tools
  (`search_graph`, `get_definition(concept)`, `expand_neighbors(concept)`) an agent calls
  iteratively for multi-hop / cross-clause questions, bounded tool-call budget.
- **Touch points**: **NEW** tool wrappers over `omd_retrieval.{retrieve,inject_definitions,expand}`;
  **NEW** orchestrator node + a graphont sub-graph; `state/graph_state.py` for a tool-call trace.
  `generation.py` uses plain `ChatPromptTemplate|ChatOllama` — **Primus has NO tool-calling** — so
  this needs either a tool-calling model or a separate orchestrator LLM (e.g. gpt-4o-mini) that plans
  retrieval and hands contexts to Primus.
- **Expected impact**: best multi-hop recall for cross-clause benchmarks (B03 conditional reasoning,
  B23 multi-regulator). Citation impact indirect.
- **Costs/risks**: **highest** — most LLM calls, **least deterministic → worst for a batch evaluation
  framework** whose purpose is stable measurement; largest structural change; hardest to eval/rollback.
- **Compatibility**: heavy new state; orchestrator sits outside the current single-shot contract.
- **Evaluation**: hard to make run-to-run comparable; better suited to interactive `query ask`.
- **Verdict**: **defer / out-of-scope for the batch evaluator.** Listed for completeness.

---

## 4. Recommendation — **Option B primary**, with Option A staged as phase-2

**Why B first:** it is the lowest-risk, most-reversible, and *most directly* aimed at the exact
number to beat (D6=0.278). It exploits a genuine, verified gap — the pipeline currently performs
**zero** citation-grounding — and its cheapest form adds **no** model calls. It also produces, as its
first slice, the diagnostic the researcher flagged as the top open question (*is the citation error
retrieval-driven or generation-driven?*). If that audit shows the governing clause is usually
retrieved but mis-cited, **B alone may close most of the gap**; if it shows the clause is often *not
retrieved*, that is the trigger to build Option A. So B-first also *sequences the decision* about A.

**Composed target:** a new `--mode graphont-agentic` = graphont retriever + (B) grounding gate, with
(A) ce_confidence re-query added only if the Slice-1 audit justifies it. Option C is out of scope.

### Vertical slices (tracer-bullet — each independently testable & shippable behind the new mode)

**Slice 1 — Grounding *audit* (read-only, zero behavior change).**
- *Scope*: add `graphont-agentic` mode; `citation_grounding_gate` NODE computes `cited_ids` vs
  retrieved `citation_id` set, writes `grounded_ids`/`unsupported_ids` to state + sidecar. **No
  stripping, no regen.** Ship the `citation_id` normalization helper.
- *Files*: `routing.py` (new mode key), `graph.py` (wire branch + generate→gate conditional),
  new `nodes/citation_grounding_gate.py`, `resolver.py` (normalization helper), `graph_state.py`.
- *Test*: unit-test normalization + membership on fixtures (footer/id spelling variants); run 18-case
  κ bed, inspect sidecar; assert generations byte-identical to `graphont` (no behavior change).
- *Success*: audit numbers produced (how many cited clauses are ungrounded); normalization validated;
  answers the retrieval-vs-generation diagnostic.

**Slice 2 — Strip unsupported citations (deterministic, +0 model calls).**
- *Scope*: gate removes ungrounded lines from the `**Sources:**` footer + `citations` before emit.
- *Files*: extend `citation_grounding_gate.py`.
- *Test*: fixture citing a non-retrieved clause → stripped; over-strip guard (correct-but-unmatched id
  must survive — validates normalization); A/B D6 on κ bed.
- *Success*: D6 ↑ or held; no regression on other 17 benchmarks; latency delta ≈ 0.

**Slice 3 — Single grounded regeneration (Self-RAG `ISSUP`-lite, +≤1 call/case).**
- *Scope*: if `unsupported_ids` non-empty, regenerate **once** with a corrective instruction naming
  the ungrounded IDs; cap `regenerate_count ≤ 1`; edge gate→generate→gate→END.
- *Files*: `routing.py` (edge + cap), `graph.py` (loop edge). `generation.py` reused, not modified.
- *Test*: fixture forcing one regen; assert cap prevents >1; A/B D6.
- *Success*: further D6 ↑; bounded +≤1 LLM call/case; no infinite loop.

**Slice 4 — ce_confidence re-query gate (bridges to Option A; gated on Slice-1 findings).**
- *Scope*: BEFORE generate, if retrieval empty **or** `ce_confidence < τ`, one re-query pass
  (widen `k`/recall depth → flip weights → targeted concept); cap `requery_count ≤ 1`. Closes the
  empty-retrieval hole.
- *Files*: split `omd_context_assembly` → `omd_retrieve`+`omd_pack`; new `nodes/omd_requery.py`;
  `routing.py` (`decide_after_omd_grade`); `graph.py`; `graph_state.py`.
- *Test*: low-confidence + empty-retrieval fixtures trigger exactly one re-query; recall@k on Act §7.
- *Success*: recall@k ↑ on under-recalled cases; bounded cost; empty retrieval no longer silent.

---

## 5. Open questions / decisions for the parent

1. **Diagnostic (blocks A):** is the D6 error retrieval-driven or generation-driven? Slice 1 answers
   it; A (Slice 4) only justified if clauses are frequently *not retrieved*.
2. **citation_id ↔ footer alignment:** need real samples of omd `citation_id` vs model footer strings
   to design normalization (exact / canonical doc-name+clause / fuzzy). **Make-or-break for B.**
3. **Mode vs flag:** `--mode graphont-agentic` (recommended, clean A/B + additive) vs a `--agentic`
   flag on graphont.
4. **Cost envelope:** acceptable extra LLM calls/case × 435? Determines whether Slice 3 regen and
   Slice 4 re-query both ship, or only the +0-call Slices 1–2.
5. **Strip vs annotate:** should an ungrounded citation be silently removed or flagged for audit?
6. **Cap values:** `regenerate_count ≤ 1`; `requery_count ≤ 1` (or ≤2). Confidence threshold τ.

## 6. Out of scope

- Option C ReAct tool-agent / Primus tool-calling → defer to interactive `query ask` (non-deterministic
  for the batch evaluator).
- Channel-II community-report retrieval (unbuilt).
- The judge/scoring subsystem (`domain/services/llm_judge_service.py`) — unchanged.
- The **hybrid/Qdrant** mode and its `grade_documents`/`decide_after_grading` — the researcher's
  "enhance the grader" idea applies THERE, not graphont; not this task.
- Fine-tuning / a trained Self-RAG critic (prompted approximation only).

---
---

# v2 — POST-REVIEW (supersedes v1 above)

**Revised**: 2026-07-12 · folds in the plan-reviewer's CRITICAL finding (D6 target mismatch),
verified this session against `docs/phase-2/evaluation-rubrics.md` §D6 + `src/domain/services/llm_judge_service.py`.

## v2.0 — What v1 got wrong (the CRITICAL correction)

v1 Option B checked cited clause IDs against **this turn's retrieved `citation_id` set**. That is the
**wrong oracle**. Verified D6 mechanics:

- **D6 Step 1 (existence)** — each cited `(claimed_doc, clause)` is routed via the judge's
  `_normalize_doc_name` (`_DOC_ALIASES`, 7 canonical docs) into a **doc-keyed set built from the
  static 883-entry `src/rag/ingestion/fixtures/clause_inventory.json`** (`entries[].clause_id` /
  `source_doc`). `EXISTS` vs `FABRICATED` (doc in corpus, clause not in that doc's inventory) vs
  `EXTERNAL` (doc outside the 7-doc corpus → **excluded** from D6). `_build_citation_verification_block`.
- **D6 Step 2 (fidelity)** — for `EXISTS`, the **judge LLM** compares the model's description to the
  clause's **actual cached TEXT** → `CORRECT / IMPRECISE / MISATTRIBUTED`. The text cache is loaded
  from **Qdrant, `document_source == "CCoP 2.0"` only** (`_load_clause_text_cache`), with a sub-letter
  parent fallback (`5.3.1(c)→5.3.1`, `_resolve_clause_text`). So **content-fidelity checking only
  bites on CCoP 2.0 citations**; other docs are `EXISTS` with no text to compare.
- **D6 Step 3** — `ratio = (CORRECT + 0.5·IMPRECISE) / (CORRECT+IMPRECISE+MISATTRIBUTED+FABRICATED)`;
  `1.0→3 | ≥0.67→2 | ≥0.34→1 | <0.34→0`; **0 citations → D6=1**.

**Consequences (internalized):**
1. D6 is **corpus-existence + content-fidelity against a STATIC inventory**, *independent of what was
   retrieved this turn.*
2. A retrieval-membership gate (v1 B) catches pure **FABRICATIONS** (a fabricated ID is never
   retrieved) — real, keep that — but it **does nothing for MISATTRIBUTED** (real ID, wrong claim),
   and it will **wrongly strip genuinely-CORRECT citations to real clauses that missed this turn's
   top-8** (the documented Act §7 / RtF §2.3 recall misses) → **pushing D6 DOWN.**
3. v1's "**Direct ↑ on D6**" for Option B was **overstated.** Corrected below.

**The fix — use the inventory oracle, not retrieval membership.** An *inventory*-existence gate strips
only non-inventory (FABRICATED/EXTERNAL) citations. Because those contribute to `verifiable_total`
(FABRICATED) or are excluded (EXTERNAL) but **never** to `correct_weight`, removing them is
**monotonically non-harmful to D6** (ratio rises or holds; e.g. `1 CORRECT + 1 FABRICATED`: ratio
0.5→D6=1 becomes ratio 1.0→D6=3; all-fabricated: ratio 0→D6=0 becomes 0-citations→D6=1). This is the
rigorous basis for calling the inventory gate a **no-regret** first ship. **Normalization is already
solved** — reuse the judge's `_DOC_ALIASES` + `^(?:Section|Clause|§|Part|Chapter)\s+` stripping +
sub-letter parent fallback; do NOT rebuild a citation_id/footer normalizer on 18 cases (v1's
"alignment worry" is dropped — `parse_citations` already emits `f"{doc}::{clause}"`).

## v2.0.1 — Convergence: two independent findings say "TEST it, don't assume it"

Two lines of evidence reached the **same** conclusion from opposite directions, and this is a
**strength of the plan's diagnostic-first sequencing** worth stating to the parent:
- **Code-based (plan-reviewer):** D6 is measured against the **static inventory** (existence) +
  **content-fidelity** vs cached clause text — *not* against this-turn retrieval. So neither
  retrieval-membership (v1 B) nor KG-path-groundedness *automatically* buys a D6 gain.
- **Literature-based (researcher §9):** **no fetched paper** proves agentic clause-citation gains on a
  numbered regulatory corpus; "grounded path ≈ citation" is an explicit **hypothesis**, not a result.

**Therefore the redesigned Slice-1 2×3 confusion table must TEST which remedy pays off — it must not
be assumed.** This is precisely why the plan is diagnostic-first and why B / B′ / A are contingent.

## v2.1 — The B / B′ / A decision framework (data-gated, not pre-assumed)

Three distinct remedies map to three distinct error modes. **The Slice-1 confusion table selects
among them** — do not pre-commit:

| Dominant error mode (from Slice-1 table) | Correct remedy | Why |
|---|---|---|
| **FABRICATED** (mostly not-retrieved) | **Option B — inventory-existence gate** | Strips non-existent IDs; monotonically non-harmful to D6; +0 model calls. |
| **EXISTS-MISATTRIBUTED** (real ID, wrong claim) | **Option B′ — content-support gate (true Self-RAG ISSUP)** | Must compare claim vs actual clause TEXT; ID-membership can't see this. Materially harder. |
| **EXISTS-CORRECT-but-not-retrieved** | **Option A — recall re-query** | The clause is real & correctly cited; the fix is *getting it into context*, not gating. B would actively hurt. |

**Honest primary recommendation:** **run the Slice-1 diagnostic FIRST; it selects B / B′ / A.**
If a most-likely primary must be named now, it is **Option B (inventory gate) as the no-regret first
ship** — justified not by an assumed error mix but by the **monotonicity proof** (it cannot lower D6
and removes all fabrication penalty at +0 model cost) — with **B′ and A explicitly contingent on the
table.** Evidence caveat: D6=0.278 is very low and Act §7 / RtF §2.3 recall misses are documented, so
a meaningful share of errors are plausibly **MISATTRIBUTED and/or CORRECT-but-unretrieved** — i.e. B
alone is unlikely to be sufficient; expect to invest in B′ and/or A once the table is in hand.

## v2.2 — Revised options (impact claims corrected)

**Option A — bounded corpus-internal re-query on `ce_confidence`** *(unchanged from v1 §3-A; still
valid).* Recall lever. Helps the **EXISTS-CORRECT-but-not-retrieved** cell. Uses the free
`ce_confidence`/`ranked_by`/empty-signal (no model call for the decision); `retrieve()` levers are
already kwargs. Closes the empty-retrieval silent-proceed hole. Grade = NODE, branch = edge.

**Option B — inventory-existence citation gate** *(REVISED oracle).* NODE after `generate`: extract
cited `(doc, clause)` via `parse_citations`; classify against the **static inventory** reusing the
judge's `_DOC_ALIASES` + stripping regex + sub-letter fallback; flag/strip FABRICATED, pass EXISTS &
EXTERNAL through untouched. **Impact: removes the fabrication component of the D6 penalty;
monotonically non-harmful; +0 model calls.** Does **NOT** help MISATTRIBUTED. Risk is **inventory
incompleteness** (a real clause absent from `clause_inventory.json` → false-FABRICATED → stripping a
good citation) — hence the Slice-2 calibration gate below.

**Option B′ — content-support (Self-RAG ISSUP) gate** *(NEW; for MISATTRIBUTED).* NODE after
`generate`: for each `EXISTS` CCoP-2.0 citation, fetch the clause TEXT (mirror the judge's Qdrant
CCoP-2.0 cache + parent fallback) and check the model's description against it; on mismatch, flag or
regenerate once. **This is the only lever that touches MISATTRIBUTED — which D6 penalizes as harshly
as fabrication.** Materially harder than B: needs a clause-text lookup and a per-citation support
judgment (one batched grader call, `temperature=0`, mirroring the judge to avoid a train/eval oracle
split). **B′ is a content-fidelity/text-comparison check** — note the KG-path methods (RoG/ToG-2) are
**retrieval-side** (they change *which* clause is retrieved) and therefore belong to **Option A**, not
B′; they do not fix B′'s fidelity target. See v2.6 + the convergence note (v2.0.1).

**Option C — ReAct graph-tool agent** *(unchanged: deferred/out-of-scope for the batch evaluator;
Primus has no tool-calling; least deterministic).* Reserve for interactive `query ask`.

## v2.3 — Re-sequenced vertical slices

**Slice 1 — Diagnostic confusion table + scaffolding (selects B/B′/A).**
- *1a — Offline confusion table (no pipeline change).* An analysis script over the **existing latest
  `--mode graphont` eval run** (`src/results/evaluations/…`) + its `-contexts.json` sidecar. For every
  cited citation, compute the **deterministic** axis (FABRICATED vs EXISTS) by replicating
  `_build_citation_verification_block` (inventory sets + `_DOC_ALIASES` + stripping + sub-letter
  fallback), the **fidelity** axis (CORRECT/IMPRECISE/MISATTRIBUTED) by **mining the run's existing
  judge justifications** (no re-inference), and the **retrieval** axis (retrieved vs not) from the
  sidecar's per-case retrieved `citation_id`s. Emit the **2×3 (actually 3×2) table**:
  `{FABRICATED, EXISTS-CORRECT/IMPRECISE, EXISTS-MISATTRIBUTED} × {retrieved, not-retrieved}`. Cell
  reads: FABRICATED×not-retrieved→B wins; CORRECT×not-retrieved→**do NOT** ID-gate, favour A;
  MISATTRIBUTED×retrieved→B′ (text is in-context); MISATTRIBUTED×not-retrieved→B′+A.
- *1b — Scaffolding (behaviour-neutral).* Register `--mode graphont-agentic` as an **exact clone** of
  the graphont branch (`omd_context_assembly → generate → END`) plus a **log-only passthrough gate
  node** (no strip). Wire CLI/settings/env-vars: `--mode graphont-agentic`, and reserve caps/thresholds
  `CCOP_AGENTIC_REGENERATE_CAP` (`regenerate_count`), `CCOP_AGENTIC_REQUERY_CAP` (`requery_count`),
  `CCOP_AGENTIC_CE_CONF_TAU` (τ) in `Settings` + `GraphState`.
- *Files*: new `scripts/` diagnostic (1a); `edges/routing.py` (new mode key), `graph.py` (clone branch
  + `generate` out-edge becomes conditional: `graphont-agentic → gate`, **all else → END**), new
  `nodes/citation_grounding_gate.py` (log-only), `state/graph_state.py` (+`cited_ids`, `grounded_ids`,
  `fabricated_ids`, `regenerate_count`, `requery_count`), `infrastructure/config/settings.py`.
- *Test*: unit-test the classification against fixtures reusing the judge's helpers; **REGRESSION TEST
  (item 6b): assert `mode=="graphont"` still resolves to the unconditional `generate → END` edge** and
  never enters the gate once `generate`'s out-edge is conditional (guards a mode-typo silent reroute);
  assert `graphont-agentic` generations are byte-identical to `graphont` at this slice.
- *Success*: confusion table produced; B/B′/A decision made from data; zero behaviour change vs
  graphont; regression test green.

**Slice 2 — Inventory-existence gate (flag → strip), the no-regret D6 lever.**
- *Scope*: gate strips FABRICATED (and leaves EXISTS/EXTERNAL) from the `**Sources:**` footer +
  `citations` before emit. Ship **flag-only first**; enable **strip** only after calibration.
- *Honesty note to parent (item 4)*: the residual risk is **not string alignment** but **inventory
  incompleteness** — a real clause missing from `clause_inventory.json` is mislabelled FABRICATED and a
  good, judge-scored citation would be stripped. The metric-mismatch failure of v1 (stripping
  correct-but-unretrieved) is **eliminated** by using the inventory oracle, but inventory-coverage risk
  remains. **Gate strip-enablement behind a 50–100 case calibration** (not just the 18-case κ bed):
  confirm the false-FABRICATED rate ≈ 0 against inventory coverage.
- *Files*: extend `nodes/citation_grounding_gate.py`; `citations/resolver.py` (reuse helpers only).
- *Test*: fixtures (fabricated → stripped; real-but-inventory-absent → NOT stripped in flag-mode);
  monotonicity check on a held-out set (D6 non-decreasing). *Success*: D6 ↑ or held on the calibration
  sample; false-FABRICATED ≈ 0; latency Δ ≈ 0; +0 model calls.

**Slice 3 — Content-support gate B′ + single regen (only if table shows MISATTRIBUTED dominant).**
- *Scope*: for EXISTS CCoP-2.0 citations, fetch clause TEXT (judge-mirrored cache) and run one batched
  `temperature=0` support check; on unsupported, regenerate **once** (`regenerate_count ≤ 1`) with a
  corrective instruction naming the mis-described clauses.
- *Files*: `nodes/citation_grounding_gate.py` (+support check), `routing.py` (regen edge + cap),
  `graph.py` (gate→generate→gate→END loop). `generation.py` reused, not modified.
- *Test*: fixture with a real clause + wrong description → flagged/regen; cap prevents >1 loop.
  *Success*: MISATTRIBUTED count ↓, D6 ↑; bounded extra calls (see ceiling); no infinite loop.

**Slice 4 — Recall (re-scoped into 4a/4b/4c; not equal-effort).**
- *4a — Empty-retrieval fallback + assembly state-split (small).* Split `omd_context_assembly` into
  `omd_retrieve` (stores raw `out`+`ce_confidence` in state) and `omd_pack`; add an empty-retrieval
  guard so retrieval failure no longer silently proceeds to `generate`. *Test*: empty fixture hits the
  guard. *Success*: safety net closed; no behaviour change on non-empty cases.
- *4b — `ce_confidence` threshold gate (medium).* Grade NODE branches on `ce_confidence < τ`; +0 model
  calls. *Test*: low-confidence fixture flagged. *Success*: gate fires correctly, logged.
- *4c — Re-query toolkit + ablation (larger). Ordered by cost, cheapest-first:*
  1. **HippoRAG-style Personalized PageRank (PPR) FIRST** (arXiv 2405.14831) — a **single-pass** PPR
     over the concept graph, **no extra LLM call per hop**, reported ~10–30× cheaper than iterative
     loops. Preferred first experiment because it directly respects the 435-case cost ceiling; a
     one-shot PPR recall pass can approximate multi-hop quality without a loop. *(New retrieval method
     added to `omd_retrieval` / a PPR recall channel.)*
  2. **Deterministic levers as cheap comparators** — widen k/recall depth, flip channel weights,
     targeted-concept injection (`requery_count ≤ 1`, +0 LLM calls) — baseline to measure PPR against.
  3. **RoG-style `concept_plan` as phase-3 escalation** (arXiv 2310.01061) — an LLM relation-path plan
     over `:REL`/`:INVOKES` (**+1 LLM call/case**); sequence **only AFTER PPR is tried and found
     insufficient**.
  *Out of this slice's scope* (same tier as Option C): ToG-2 alternation, community-report/Channel-II.
  *Test*: ablation harness on the coarse recall@k gold, PPR vs deterministic vs (if escalated) RoG.
  *Success*: recall@k ↑ on documented misses (Act §7, RtF §2.3) at the **lowest** cost tier that works.

## v2.4 — Cost ceiling for 435 cases (item 6a)

Distinguish **local Ollama Primus** calls (cheap; generation/regen) from **OpenRouter grader** calls
(rate-limited/paid). Per case, worst case:
- Slice 2: **+0** model calls (deterministic).
- Slice 3: **+1 OpenRouter** support check (batched, all citations in one call) **+ ≤1 Ollama** regen.
- Slice 4: 4b **+0**; 4c **+≤1 Ollama** query-rewrite (if the ladder uses LLM rewrite) **+ ≤1**
  `retrieve()` (cross-encoder rerank pass — **not** an LLM call).
- **Combined Slice 3+4 worst case per case**: **≤1 OpenRouter call + ≤2 Ollama calls + ≤1 rerank
  pass.** Across 435: **≤435 extra OpenRouter grader calls**, **≤870 extra Ollama generations**,
  **≤435 extra rerank passes.** Slices 1–2 alone add **zero** model calls. Mitigate OpenRouter load
  with `temperature=0`, hard caps, and only entering B′/4c for cases the table/threshold flags.

## v2.5 — Evaluation rigor caveats (item 7)

- **Primary oracle = the D6 judge itself** (rubric §D6). A/B `--mode graphont` (control) vs
  `--mode graphont-agentic` on the 18-case κ bed → then a **50–100 case calibration** (Slice-2 strip)
  → then the full 435. Log every gate/branch decision to `-contexts.json`.
- **recall@k gold is COARSE, not ready-made:** `metadata.clause_reference` in
  `ground-truth/test-suite/*.jsonl` is **reused, not purpose-built** — inconsistent formats
  (`["1.4.3", "section 11"]`), partial coverage. Usable as a **coarse** recall@k signal for Option A
  only; state the format/coverage gaps; do **not** present recall@k as clean. D6 (judge) remains the
  target metric; recall@k is a secondary retrieval-quality diagnostic.
- **Determinism:** `temperature=0` on B′/graders; fixed caps; per-decision logging so agentic runs stay
  diff-able for an *evaluation* framework.

## v2.6 — Optional / out-of-primary-scope (from refreshed research)

KG-agentic patterns are **retrieval-side = Option A**, NOT a B/B′ grounding-gate rescue (they change
*which* clause is retrieved; they do not change the D6 oracle = static-inventory existence +
content-fidelity). Placement:
- **In Option A / Slice 4c (in-scope, ordered):** **HippoRAG PPR first** (cost lever, single-pass,
  arXiv 2405.14831) → **RoG `concept_plan`** phase-3 escalation (+1 LLM/case, arXiv 2310.01061).
- **Out of scope (Option C tier):** **ToG-2 alternation**; **community-report / Channel-II**
  (Microsoft GraphRAG, arXiv 2404.16130) — would close graphont's *own* documented "Channel-II not
  built" gap for global/thematic questions, but is a bigger structural add.
- **Honest gap (researcher §9):** no fetched paper measures agentic clause-citation accuracy on a
  numbered regulatory corpus → treat "grounded KG path ≈ clause citation" as a **hypothesis to test**,
  not a proven lever (see convergence note v2.0.1).

## v2.7 — Retained from v1 (reviewer-praised, unchanged)

Additive new-mode design (`--mode graphont-agentic`, never mutate `graphont` in place); **grader =
NODE, branch = edge** LangGraph discipline; **Option C deferral**; **`ce_confidence` as a free
signal**; iteration-cap everything for batch reproducibility/cost.

## v2.8 — Open questions for the parent

1. **Diagnostic gates everything** — the Slice-1 table selects B / B′ / A. Run it before committing
   build effort beyond Slice 1.
2. **Inventory coverage** — what is the false-FABRICATED rate of `clause_inventory.json` on 50–100
   cases? Gates Slice-2 strip enablement.
3. **B′ oracle fidelity** — mirror the judge's Qdrant CCoP-2.0 text cache exactly to avoid an
   eval/gate oracle split; MISATTRIBUTED detection is CCoP-2.0-only (accept, or extend text cache?).
4. **Cost envelope** — is ≤435 extra OpenRouter calls + ≤870 extra Ollama gens acceptable? Determines
   whether Slice 3 (B′) and 4c ship, or only the +0-call Slices 1–2.
5. **Mode vs flag** — `--mode graphont-agentic` (recommended) vs a `--agentic` flag on graphont.
6. **Cap values** — `regenerate_count ≤ 1`, `requery_count ≤ 1`, τ default.

---
---

# v3 — AGENTIC RE-FRAME (parent-facing §4 / §5 / §6)

**Revised**: 2026-07-12 · re-frames v2 so the genuinely-agentic components are the headline (parent
feedback: "we asked for an agentic-RAG plan, not a citation-cleanup plan"). **No new evidence** — same
v2 facts, D6 honesty preserved. The deterministic inventory gate is retained but demoted to a
co-shipped hygiene layer. Ready to drop into `report/term3-mid/agentic-rag-graphont-plan.md`.

## §4 — Options (each tagged with its agentic-RAG pattern)

**What "agentic" means for this plan:** the LLM sits *inside* the retrieval/verification loop —
deciding when to re-retrieve, and whether each cited clause actually *supports* the claim — instead of
running a fixed single-shot `retrieve → generate`. Control flow **branches on model/confidence
signals**, it is not a straight line.

**Option A — Agentic corrective + iterative, KG-guided retrieval loop.**
*Patterns: Corrective RAG / CRAG (corpus-internal, no web) + Adaptive/iterative retrieval + KG-guided
retrieval (HippoRAG PPR, RoG relation-path planning).* **GENUINELY AGENTIC** — a grade node reads the
free `ce_confidence` / empty-retrieval signal and a conditional edge loops back to re-retrieve
(HippoRAG-PPR-first ladder), capped. Targets the **EXISTS-CORRECT-but-not-retrieved** error cell +
closes the empty-retrieval hole (Act §7, RtF §2.3 recall misses). Retriever levers already kwargs;
grade = NODE, branch = edge. Cost: confidence gate + PPR + deterministic levers = **+0 LLM calls**;
RoG path-planning escalation = **+1 LLM/case**.

**Option B′ — Agentic post-hoc citation critic.**
*Patterns: Self-RAG (ISSUP support token) / post-hoc citation critic.* **GENUINELY AGENTIC** — an LLM
verifies each cited clause's **claim-support against the actual clause TEXT** (not mere existence), and
regenerates ≤1 on unsupported. This is the **only** lever that touches **MISATTRIBUTED** (real ID,
wrong claim) — which D6 penalizes as harshly as fabrication. Cost: **1 batched grader call +
≤1 regen** per case; `temperature=0`, mirroring the judge's Qdrant CCoP-2.0 text cache to avoid an
eval/gate oracle split.

**Option B — Deterministic inventory-existence gate (hygiene, NOT agentic).**
*Pattern: none — set-membership string filtering against the static inventory.* Stated honestly: **this
is a hygiene layer, not agentic** (no LLM, no loop, no decision). Strips FABRICATED citations;
**monotonically non-harmful to D6** (removes only non-inventory items from `verifiable_total`, never
from `correct_weight`); **+0 model calls**. Cheap and safe → **co-ship alongside** the agentic core, do
not headline it.

**Option C — ReAct tool-using retrieval agent (agentic, DEFERRED).**
*Pattern: ReAct (Thought→Action→Observation over graph tools).* Agentic, but deferred: Primus has **no
tool-calling** and free-form tool loops are **non-deterministic** — wrong for a batch *evaluation*
framework. Reserve for interactive `query ask`.

## §5 — Recommended plan (agentic loop is the architecture; gate rides alongside)

**Headline recommendation — build the composed agentic loop for graphont, as a new additive
`--mode graphont-agentic`:**
> an **iterative corrective-retrieval loop** (CRAG-lite on the free `ce_confidence` signal, with a
> **HippoRAG-PPR-first** re-query ladder, iteration-capped) **+ a Self-RAG-style post-hoc citation
> critic** (content-support vs the actual clause text, regenerate ≤1). That is the **agentic core**
> (Options A + B′). A **deterministic inventory hygiene gate** (Option B) is **co-shipped alongside** —
> cheap, safe, monotonically non-harmful — but is explicitly *not* the headline and *not* agentic.

**Role of the diagnostic (honesty preserved):** the Slice-1 2×3 confusion table tells us the **error
mix** and therefore **how much each agentic component pays off for D6** — it **tunes emphasis and
sequencing within the agentic build**, it is *not* a go/no-go that could cancel the agentic effort.
The parent wants agentic RAG built; the diagnostic prioritizes *within* it. (Convergence, §v2.0.1: both
the code-based D6 finding and the literature gap say *test* which agentic remedy pays — don't assume —
which is exactly what the diagnostic-first sequencing does.)

### Tracer-bullet slices (each independently measurable; agentic parts first-class)

**Slice 1 — Read-only diagnostic + scaffolding + regression test.** *(enabling; 0 model calls)*
- *Scope*: 2×3 confusion table `{FABRICATED, EXISTS-CORRECT/IMPRECISE, MISATTRIBUTED} × {retrieved,
  not-retrieved}` mined from the latest `--mode graphont` run + `-contexts.json` (deterministic axis
  replicating `_build_citation_verification_block`; fidelity axis from existing judge justifications;
  retrieval axis from the sidecar). Register `--mode graphont-agentic` (clone of graphont + a log-only
  passthrough node). Wire CLI/settings/env: `CCOP_AGENTIC_REGENERATE_CAP`, `CCOP_AGENTIC_REQUERY_CAP`,
  `CCOP_AGENTIC_CE_CONF_TAU`.
- *Files*: `scripts/` diagnostic; `edges/routing.py`, `graph.py` (`generate` out-edge → conditional:
  `graphont-agentic→gate`, else `END`), new `nodes/citation_grounding_gate.py` (log-only),
  `state/graph_state.py`, `infrastructure/config/settings.py`.
- *Test*: unit-test classification vs fixtures reusing judge helpers; **REGRESSION TEST: `mode=="graphont"`
  always resolves to the unconditional `generate→END` edge** (guards a mode-typo reroute); assert
  `graphont-agentic` generations byte-identical to `graphont` at this slice.
- *Success*: table produced; error mix known; zero behaviour change; regression green.

**Slice 1.5 — Inventory-existence hygiene gate (co-ship; deterministic, NOT agentic; 0 model calls).**
- *Scope*: strip FABRICATED citations from the **visible** generation text; log pre-strip footprint to
  the `-contexts.json` sidecar (Q3 decided). Leaves EXISTS/EXTERNAL untouched.
- *Files*: extend `nodes/citation_grounding_gate.py`; reuse `citations/resolver.py` + judge
  `_DOC_ALIASES` / stripping / sub-letter fallback.
- *Test*: fabricated → stripped; real-but-inventory-absent → NOT stripped; D6 non-decreasing on a
  held-out set. *Success*: D6 ↑ or held; false-FABRICATED ≈ 0 after Q3b calibration; latency Δ ≈ 0.

**Slice 2 — AGENTIC: Self-RAG post-hoc citation critic (Option B′).** *(+1 grader + ≤1 regen/case)*
- *Scope*: for each EXISTS CCoP-2.0 citation, fetch clause TEXT (judge-mirrored Qdrant cache + parent
  fallback), run one batched `temperature=0` claim-support check; regenerate **once**
  (`regenerate_count ≤ 1`) naming unsupported clauses. **First genuinely-agentic slice; targets
  MISATTRIBUTED — which the hygiene gate cannot touch.**
- *Files*: new `nodes/citation_support_critic.py` (or extend the gate); clause-text cache helper;
  `edges/routing.py` (regen edge + cap), `graph.py` (gate→generate→gate→END loop); `generation.py`
  reused, not modified.
- *Test*: real clause + wrong description → flagged/regen; cap prevents >1 loop. *Success*:
  MISATTRIBUTED count ↓, D6 ↑; bounded calls; no infinite loop.

**Slice 3 — AGENTIC: corrective/iterative retrieval loop (Option A).** *(HippoRAG/deterministic +0 LLM;
retrieve/rerank passes only)*
- *Scope*: split `omd_context_assembly` → `omd_retrieve` (stores raw `out`+`ce_confidence`) + `omd_pack`;
  add a CRAG-lite **grade NODE** on `ce_confidence < τ` / empty retrieval → **HippoRAG-PPR-first
  re-query ladder** (single-pass PPR → deterministic widen-k/flip-weights comparators),
  `requery_count ≤ 1–2`. Closes the empty-retrieval hole + recall misses.
- *Files*: `nodes/omd_context_assembly.py` (split), new `nodes/omd_retrieval_grade.py` +
  `nodes/omd_requery.py`, `graph/ontology_v2/omd_retrieval.py` (add PPR recall channel),
  `edges/routing.py` (`decide_after_omd_grade`), `graph.py`, `state/graph_state.py`.
- *Test*: empty + low-confidence fixtures trigger exactly one re-query; PPR-vs-deterministic ablation on
  the coarse recall@k gold. *Success*: recall@k ↑ on Act §7 / RtF §2.3 at the lowest cost tier that works.

**Slice 4 — AGENTIC, optional escalation: RoG concept-path planning / deeper multi-hop.** *(+1 LLM/case)*
- *Scope*: only if Slices 2–3 leave residual recall gaps — an LLM relation-path plan over `:REL`/`:INVOKES`
  from query concepts, grounding retrieval in auditable graph paths. *(ToG-2 alternation +
  community-report/Channel-II remain out of scope, Option C tier.)*
- *Files*: new `nodes/concept_plan.py`; `omd_retrieval.py` (path-guided retrieval); `state`.
- *Test*: ablation vs Slice-3 baseline on recall@k. *Success*: incremental recall ↑ that justifies the
  +1 LLM/case at 435-scale.

### Cost ceiling (435 cases) — which slices are free vs +LLM

| Slice | Agentic? | Extra OpenRouter (grader) | Extra Ollama (gen/regen) | Extra retrieve/rerank |
|---|---|---|---|---|
| 1 diagnostic | no (enabling) | 0 | 0 | 0 |
| 1.5 hygiene gate | no (hygiene) | 0 | 0 | 0 |
| 2 B′ critic | **yes** | ≤1 (batched) | ≤1 (regen) | 0 |
| 3 A loop | **yes** | 0 | 0 | ≤1–2 passes |
| 4 RoG plan | **yes (opt)** | 0 or ≤1 | ≤1 | ≤1 pass |
| **All-on worst case** | | **≤435 total** | **≤~1300 total** | **≤~870 total** |

`temperature=0` on all graders; hard caps; per-decision logging to the sidecar for reproducibility.

## §6 — Open questions (Q3 now DECIDED; Q1/Q2/Q4–Q8 open)

- **Q1 (open) — Error-mix / emphasis.** Which cell dominates the Slice-1 table (MISATTRIBUTED vs
  CORRECT-but-unretrieved vs FABRICATED)? Tunes how hard we push Slice 2 (B′) vs Slice 3 (A) — *within*
  the agentic build, not whether to build it.
- **Q2 (open) — B′ oracle fidelity.** Mirror the judge's Qdrant CCoP-2.0 text cache exactly; note
  MISATTRIBUTED detection is **CCoP-2.0-only** (accept, or extend the text cache to other docs?).
- **Q3 (DECIDED, code-verified) — Citation-gate strip policy + calibration.**
  - *Q3a = STRIP fabricated citations from the visible generation text + log the pre-strip footprint to
    the `-contexts.json` sidecar.* Rationale: the judge scores only the visible `response.content`
    (re-derived by regex), so annotation would still be parsed and penalized; the sidecar is
    judge-invisible, preserving audit fidelity.
  - *Q3b = n=100 calibration, STRATIFIED to cover the 6 not-yet-PDF-validated supporting docs.*
    CCoP-2.0's 415/883 inventory entries were audited complete on 2026-06-29, so false-FABRICATED risk
    is concentrated in the other 6 docs; extra n costs **0 model calls**.
- **Q4 (open) — Cost envelope.** Is ≤435 extra OpenRouter + ≤~1300 extra Ollama calls acceptable at
  435-scale? Governs whether Slice 4 (RoG, +1 LLM/case) ships.
- **Q5 (open) — Mode vs flag.** `--mode graphont-agentic` (recommended, clean A/B, additive) vs an
  `--agentic` flag on graphont.
- **Q6 (open) — Caps / threshold.** `regenerate_count ≤ 1`, `requery_count ≤ 1–2`, `ce_confidence` τ
  default (calibrate on the κ bed).
- **Q7 (open) — HippoRAG PPR feasibility.** Does the concept graph support a Personalized-PageRank pass
  (seed/edge-weight availability) without a new offline build step?
- **Q8 (open) — Agentic determinism for an eval framework.** The B′ critic + retrieval loop add
  branching; is the reproducibility tradeoff acceptable, or do we need multi-seed/aggregate reporting?
