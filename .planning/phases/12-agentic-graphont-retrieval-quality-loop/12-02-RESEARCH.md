# Phase 12 Research Review — Agentic `graphont` Retrieval-Quality Loop

**Date:** 2026-07-13  
**Reviewer:** pi coding agent (research pass in lieu of spawning a separate researcher runtime here)  
**Inputs reviewed:**
- `.planning/phases/12-agentic-graphont-retrieval-quality-loop/12-01-PLAN.md`
- `report/term3-mid/agentic-rag-graphont-plan.md`
- `src/rag/retrieval/graph.py`
- `src/rag/retrieval/edges/routing.py`
- `src/rag/retrieval/state/graph_state.py`
- `src/rag/retrieval/nodes/omd_context_assembly.py`
- `src/rag/graph/ontology_v2/omd_retrieval.py`
- `src/domain/services/ragas_evaluation_service.py`
- `src/domain/services/llm_judge_service.py`
- `docs/project_notes/decisions.md` (esp. ADR-008)

## Executive verdict

**Overall:** **GO, with amendments**

Why:
- The plan is directionally correct: retrieval-first, additive mode, bounded loop, offline calibration first.
- It matches the actual current `graphont` weakness: retrieval signals already exist in `omd_retrieval.retrieve()` but are discarded by `omd_context_assembly.py`.
- It respects ADR-008 by keeping `graphont` unchanged and adding `graphont-agentic`.

Why not an unconditional GO:
- The current plan is strong on architecture, but still underspecified on **retrieval-eval protocol**, **signal persistence**, and **oracle design**.
- Without tightening those, Phase 12 risks becoming “implement retries and hope D6 moves”.

## Current state summary

| Area | Existing approach today | Implication for Phase 12 |
|---|---|---|
| `graphont` execution path | `query_analysis -> route_by_mode -> omd_context_assembly -> generate -> END` | No retrieval loop exists today. |
| `graphont` retrieval | `omd_retrieval.retrieve()` already computes `ranked_by`, `d_cand`, `ce_confidence`, per-channel scores, graph expansion, weighted RRF, CE+RRF fusion | Strong base to build a deterministic retrieval-quality gate. |
| Signal persistence | `omd_context_assembly.py` logs these signals but does **not** persist them to `GraphState` | Biggest immediate gap. |
| Retrieval grading | Shared `grade_documents` path is used for `hybrid`, not `graphont` | `graphont` currently has no retrieval-quality decision node. |
| Empty retrieval behavior | `graphont` still proceeds to `generate` with empty context | Clear candidate for corrective loop entry. |
| Retrieval-quality evaluation | RAGAs `context_precision/context_recall` exists generally, but the current codebase has no dedicated `graphont` retrieval harness | Phase 12 needs its own offline retrieval audit protocol. |
| Citation evaluation | D6 judge uses static clause inventory + clause-text verification, independent of runtime retrieval membership | Good: avoids “judge contamination”; also means retrieval improvement must be shown causally, not inferred. |

## Research verdict on the plan's core approach

| Topic | Assessment |
|---|---|
| Retrieval-first before citation cleanup | **Agree** |
| Deterministic v1 instead of extra controller LLM | **Agree** |
| Offline GT allowed only for calibration/eval | **Agree** |
| Additive `graphont-agentic` mode | **Required** by ADR-008 |
| Parameter-widening before graph-expansion | **Agree** |
| Runtime labels `strong/weak-recall/weak-focus/empty` | **Partially agree** — use offline first; keep runtime v1 simpler if needed |
| One retry cap in v1 | **Agree** |

## Step-by-step review

| Step | Planned step | Existing approach today | Research finding | Proposed amendment |
|---|---|---|---|---|
| 1 | Inventory current `graphont` retrieval behavior | Mostly manual today; code confirms `graphont` is a single-node retrieval+pack path | Correct starting point | Add a **signal inventory artifact** with exact field names, types, source functions, and whether they survive to sidecar/results. |
| 2 | Define calibration set | No dedicated `graphont` calibration set exists | Necessary | Make it **stratified by failure mode**, not just benchmark family: empty, weak-focus, weak-recall, known good. |
| 3 | Build offline retrieval trace capture | Signals exist in `omd_retrieval.retrieve()` but are discarded | Critical gap | Capture **raw ranked candidate IDs, ranks, per-channel ranks/scores, query concepts, expanded concepts, injected definitions, final packed docs**. Summaries alone are not enough. |
| 4 | Label strong vs weak offline | No labeling framework yet | Correct | Use a **3-layer oracle**: (1) GT clause hit@k, (2) final-citation-in-context, (3) human/auditor rationale for edge cases. Do not rely on GT clause list alone. |
| 5 | Analyze which signals predict weakness | Not done today | Correct | Add an **oracle upper-bound check**: compare heuristic detector vs offline labels before wiring retries. |
| 6 | Refactor retrieval/packing boundary | `omd_context_assembly` is monolithic | Necessary | Preserve a byte-for-byte `graphont` parity fixture before adding any agentic logic. |
| 7 | Extend `GraphState` | Current `GraphState` lacks graphont-specific retrieval diagnostics | Necessary | Add both **raw trace fields** and **decision fields**. Do not store only final grades. |
| 8 | Add `graphont-agentic` mode wiring | Not present in routing/CLI allowlists | Necessary | Update **all** mode allowlists in one change (`route_by_mode`, CLI, result validation, settings, tests) per ADR-008. |
| 9 | Implement weakness detector | No detector today | Correct | Start with **binary gate** (`acceptable` / `needs_retry`) in runtime; keep richer `weak-recall/weak-focus` taxonomy offline until separability is proven. |
| 10 | Implement `retry_wider` | No retry support today | Correct first intervention | Define exact knobs now: `k`, `RECALL_DEPTH`, channel weights, definition cap, rerank pool size. |
| 11 | Evaluate widened retry in isolation | No graphont retrieval ablation harness today | Correct | Add **paired per-case delta reporting**, not only aggregate means. |
| 12 | Implement `retry_graph_expand` | Graph expansion already exists in `omd_retrieval.expand(Q)` at concept stage | Feasible, but name carefully | Distinguish **existing concept expansion** from **new corrective graph-expansion retry** to avoid ambiguous metrics. |
| 13 | Evaluate graph expansion vs widened retry | Not done today | Correct | Include a **detector-off oracle run** (always retry) to separate detector quality from corrective-action quality. |
| 14 | Choose v1 corrective policy | No policy today | Correct | Freeze policy only after action-level win rates are measured by weakness class. |
| 15 | Run bounded end-to-end evaluation | Existing graphont evaluation is mostly end-to-end D6/judge oriented | Correct | Require a **causal chain report**: retry happened -> clause surfaced -> clause cited or grounding improved. |
| 16 | Decide on Phase 12 exit | No exit criteria yet beyond plan text | Correct | Make exit contingent on **retrieval metrics first**, D6 second. If retrieval does not move, do not claim success from citation-only movement. |

## What the existing code already gives you

| Capability already present | Evidence | Use in Phase 12 |
|---|---|---|
| Confidence-like signal | `ce_confidence` returned by `omd_retrieval.retrieve()` | Primary weak-retrieval feature candidate |
| Candidate-pool breadth signal | `d_cand` | Useful for empty/narrow-pool detection |
| Retrieval-mode provenance | `ranked_by`, per-result `ch1`, `bm25`, `dense`, `ce_score`, `rrf` | Useful for diagnosing why retrieval failed |
| Existing graph expansion primitive | `expand(Q)` over `:REL` | Baseline for graph-aware retry |
| Runtime override levers | `retrieve()` already exposes overridable weights/depths | Makes deterministic retry practical |
| Citation-ground truth evaluator | `llm_judge_service.py` inventory + clause-text verification | Good downstream validation, but not enough for retrieval tuning by itself |

## Gaps in the current plan that should be tightened

| Gap | Why it matters | Amendment |
|---|---|---|
| No explicit retrieval-eval harness artifact | Easy to implement loop without proving retrieval got better | Add `12-eval-protocol.md` with exact metrics, datasets, and pass/fail rules before Step 9. |
| Runtime taxonomy may be over-ambitious | `weak-recall` vs `weak-focus` may not separate cleanly from first-pass signals | Make v1 runtime gate binary; keep fine-grained labels offline until validated. |
| GT clause refs are incomplete silver labels | Risk of overfitting detector to narrow expected clauses | Use multiple retrieval success criteria, not only GT hit@k. |
| No detector upper-bound experiment | Could blame retries when detector is the real failure | Run three conditions: no retry, oracle retry, heuristic retry. |
| No explicit sidecar/result schema update | Debugging will be hard without per-case traces | Persist raw trace + decision trace to sidecar JSON. |
| Existing graph expansion already happens once | “retry_graph_expand” could look successful without being meaningfully different | Define the retry as a distinct expansion policy or deeper/wider traversal policy. |

## Recommended amendments to adopt now

| Priority | Amendment | Recommendation |
|---|---|---|
| P0 | Persist raw `graphont` retrieval trace to state/sidecar | **Must add** |
| P0 | Write `12-calibration-set.md` before threshold tuning | **Must add** |
| P0 | Write `12-eval-protocol.md` before implementing detector | **Must add** |
| P1 | Use binary runtime gate first; keep detailed labels offline | **Strongly recommended** |
| P1 | Add oracle-retry ablation | **Strongly recommended** |
| P1 | Require paired per-case before/after reports | **Strongly recommended** |
| P2 | Consider definition-injection overload as a signal | **Recommended** |
| P2 | Distinguish existing expansion vs corrective expansion in naming and metrics | **Recommended** |

## Proposed retrieval-quality evaluation stack

| Layer | Metric | Purpose |
|---|---|---|
| Offline retrieval | GT clause hit@k / recall@pool | Coarse clause-availability check |
| Offline retrieval | final-citation-present-in-context | Strong causal retrieval signal |
| Offline retrieval | action win-rate by weakness class | Tells whether `retry_wider` or `retry_graph_expand` helps |
| Runtime | requery rate, action distribution, latency delta | Cost/control observability |
| End-to-end | D6, citation grounding, benchmark-family deltas | Final outcome, not primary diagnostic |

## GO / NO-GO

| Verdict | Decision | Rationale |
|---|---|---|
| Architecture | **GO** | Additive mode, retrieval-first, deterministic bounded loop are the right shape. |
| Evaluation method | **GO with amendments** | Needs stronger retrieval-harness definition before implementation starts. |
| Runtime detector design | **GO with simplification** | Start binary in runtime; keep richer labels offline until validated. |
| Corrective actions order | **GO** | Widen-first, graph-expand-second is sensible and measurable. |
| Overall Phase 12 plan | **GO** | Proceed, but tighten the eval protocol and trace persistence first. |

## Suggested immediate next files

1. `.planning/phases/12-agentic-graphont-retrieval-quality-loop/12-calibration-set.md`
2. `.planning/phases/12-agentic-graphont-retrieval-quality-loop/12-eval-protocol.md`
3. `.planning/phases/12-agentic-graphont-retrieval-quality-loop/12-signal-inventory.md`
4. `.planning/phases/12-agentic-graphont-retrieval-quality-loop/12-03-IMPLEMENTATION-NOTES.md` (optional)

