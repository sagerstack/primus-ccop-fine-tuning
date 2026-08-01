# Resume Work — T3 Retrieval-Mode Comparison (as of 2026-08-01)

Handoff doc for the T3 final report. Captures the eval campaign, results, insights,
bugs found/fixed, tooling, and pending work. Read this first to resume.

---

## 1. What we ran

A controlled comparison of **retrieval modes** on the **18-case stratified sample**
(`bdc4927d`, one case per active benchmark: B01-001…B24-001, note B07 = **B07-006**),
model `primus-reasoning`, judge = rubric (qwen3-235b via OpenRouter).

**Primary comparison ladder — all HyDE OFF** (held constant per ADR-011):
hybrid → graphont → graphont-agentic (filter) → + corrective.

Results live in `report/term3-end`? No → **`src/results/evaluations/final/`**, split across
month folders **`2026-07/`** and **`2026-08/`** (UTC rollover — glob BOTH).
Each run has: `<run_id>-primus-reasoning.json` (scores/D1-D6/Q&A/provenance),
`<run_id>-contexts.json` (retrieved contexts), and `logs/eval-<mode><tags>-<ts>.log`
(retrieval filter funnel, stderr).

Run-id tags: `-ctx` (contextual), `-corr` (corrective). **poolk/topk are NOT tagged in the
filename** — distinguish via provenance `retrieval_config.graphont_agentic_pool_k / top_k`.

---

## 2. Results — overall (Tier 3, category-weighted)

| Config | HyDE | Ctx | Corr | pool/top | **T3** | P/F | run_id ts |
|---|---|---|---|---|---|---|---|
| graphont-agentic (no corr) | ✗ | ✗ | ✗ | 8/8 | **0.560** | 18/0 | 20260729-1606 |
| graphont-agentic +corr | ✗ | ✗ | ✓ | 16/8 | 0.550 | 18/0 | 20260731-0137 |
| graphont | ✗ | ✗ | ✗ | 8/8 | 0.546 | 18/0 | 20260728-1530 |
| graphont-agentic +corr | ✗ | ✗ | ✓ | 8/8 | 0.540 | 18/0 | 20260730-1624 |
| graphont-agentic +corr (wide ctx) | ✗ | ✗ | ✓ | **16/16** | **0.493** | 16/2 | 20260801-0253 (2026-08/) |
| hybrid +hyde | ✓ | ✗ | ✗ | 50/3 | 0.484 | 16/2 | 20260727-1411 |
| hybrid (naive) | ✗ | ✗ | ✗ | 50/3 | 0.441 | 13/5 | 20260728-0401 |
| hybrid +hyde +ctx | ✓ | ✓ | ✗ | 50/3 | 0.440 | 17/1 | 20260728-0150 |

*(hybrid poolk/topk = 50 retrieved / 3 reranked. graphont-agentic default 8/8.)*

## 2b. Corrected per-category breakdown (5 cats, Σw = 1.0)

RAI = Regulatory Applicability (w.25) · CRR = Compliance & Risk (w.25) · RAR = Remediation & Audit (w.20) · GCS = Governance (w.10) · SRG = Safety & Grounding (w.20)

| Config | T3 | RAI | CRR | RAR | GCS | SRG |
|---|---|---|---|---|---|---|
| graphont-agentic | 0.560 | 0.544 | 0.542 | 0.574 | 0.407 | 0.667 |
| ga+corr16/8 | 0.550 | 0.478 | 0.634 | 0.500 | 0.389 | 0.667 |
| graphont | 0.546 | 0.556 | 0.481 | 0.556 | 0.426 | 0.667 |
| ga+corr8/8 | 0.540 | 0.533 | 0.560 | 0.500 | 0.333 | 0.667 |
| hybrid+hyde | 0.484 | 0.417 | 0.505 | 0.296 | 0.389 | 0.778 |
| hybrid naive | 0.441 | 0.367 | 0.384 | 0.352 | 0.278 | 0.778 |
| hybrid+hyde+ctx | 0.440 | 0.406 | 0.458 | 0.352 | 0.315 | 0.611 |

*(This breakdown is the RESCORED/CORRECTED one — see bug #1 below. Saved JSON `category_scores`
fields in the OLD runs still contain the buggy version; use these numbers, not those.)*

## 2c. Dimension averages (0-3 scale, over 18 cases) — the ceiling

D1 verdict · D2 justification · D3 grounding · D4 scope · D5 actionable · D6 citation

| Config | D1 | D2 | D3 | D4 | D5 | D6 |
|---|---|---|---|---|---|---|
| graphont-agentic | 1.50 | 2.28 | 1.72 | 2.61 | 0.89 | 0.58 |
| graphont | 1.22 | 2.06 | 1.56 | 2.72 | 1.11 | 0.61 |
| hybrid naive | 0.89 | 1.50 | 1.11 | 1.94 | 0.78 | 0.58 |

**D5 (actionable ~0.9-1.1) and D6 (citation ~0.4-0.7) are the universal floors across ALL modes.**

---

## 3. Insights & conclusions (for the report)

1. **Graph retrieval is the one decisive lever.** hybrid → graphont = **+0.10** (0.44→0.55),
   the only gap clearing the noise floor. Everything above graphont (agentic filter, corrective,
   pool width) sits in a 0.54–0.56 cluster = statistically tied at n=18.
2. **Agentic filter & corrective don't lift the aggregate — they reshuffle.** Corrective wins
   specific slices (CRR 0.634 with corr; recovered gold clause 5.2.1 on B07-006) but is flat-to-
   negative overall. It's a **targeted recall tool for weak-retrieval cases**, not an aggregate booster.
3. **Wider context HURTS.** pool16/top16 corrective → **0.493** (−0.05 vs top8, +2 failures),
   ABOVE noise. Widening the pool (8→16, top fixed 8) was marginal +; widening the **selection**
   (top 8→16) clearly degraded. ⇒ **bottleneck is clause precision, not context quantity.**
4. **HyDE / contextualization: marginal-to-harmful.** HyDE +0.04 on hybrid; contextualization
   flat-to-negative (traced to cross-encoder score collapse on the augmented text).
5. **No mode dominates all categories.** Graph modes win RAI/RAR/CRR; **hybrid wins Safety (SRG 0.778)** —
   safety/hallucination cases don't need graph retrieval. Governance (GCS) is a universal floor.
6. **The real ceiling is D5 actionable + D6 citation, not retrieval.** Retrieval architecture doesn't
   move them. ⇒ highest-leverage improvement is the **model's actionability + citation behavior**
   (the fine-tuning target) and fixing the D6/GT metric so gains are visible.

**One-line takeaway:** *Graph-structured retrieval clearly beats vanilla hybrid (+0.10); the
agentic/corrective/HyDE/context refinements on top are noise-to-negative at n=18; the true score
ceiling is the model's citation + actionability, not how much you retrieve.*

**Confidence:** Only **graph > hybrid** is robust at n=18. Judge is non-deterministic
(~±0.05; ~0.25 swings seen on single cases). **Before publishing per-mode rankings within the graph
cluster, re-run the top 2–3 configs on a LARGER sample** (full 435 or 50–90 stratified).

---

## 4. Bugs found & fixed during the campaign

1. **Category-matching zero-pad bug (FIXED).** `_calculate_category_scores` matched zero-padded
   benchmark ids (`B01`) against non-padded category lists (`B1`) → dropped B01–B09, collapsed the
   `category_scores` breakdown to Σw=0.75, hid the whole Regulatory Applicability category. Fixed via
   `_bench_key()` normalization in `application/use_cases/evaluate_model.py`.
   **IMPORTANT:** the headline `overall_score` (T3) was computed by a *separate correct path* and was
   NEVER wrong — only the metadata breakdown field was. Rankings stand. Old JSONs still hold the buggy
   `category_scores`; use §2b rescored numbers. (Rescore script: `scratchpad/rescore.py` pattern —
   group per-test scores by category with the fix, T3 = Σ(cat_avg×weight).)
2. **retrieval_trace not a declared LangGraph channel (FIXED).** graphont-agentic corrective chain
   dropped state across node boundaries → corrective never fired / 0 docs. Fixed by declaring
   `retrieval_trace` in GraphState.
3. **D6 citation_correctness (FIXED).** Parser dropped 2nd+ clause in multi-clause sources
   (`_extract_clause_ids`); added **half-point** for 0<precision<0.34 (was flat 0). See ADR-related
   note + `gt-improvements-20260727.md` (GT-1: gold sets narrower than legitimately-citable clauses →
   precision metric penalizes thorough answers).

**ADRs added:** ADR-010 (contextualization opt-in, default OFF), ADR-011 (HyDE opt-in, default OFF).

---

## 5. Tooling / how to reproduce

- **Runner:** `src/scripts/run_eval.sh <flags>` — bakes in `--model primus-reasoning`, 18 test-ids,
  `--out-dir results/evaluations/final`, `--verbose --verbose-io`, per-run log, macOS `caffeinate`.
- **Flags added:** `--contextual/--no-contextual`, `--corrective/--no-corrective`, `--hyde/--no-hyde`,
  `--out-dir`, `--poolk`, `--topk`. All record actual state in `metadata.retrieval_config`.
- **The 4 canonical commands:**
  - `scripts/run_eval.sh --mode hybrid --no-contextual`
  - `scripts/run_eval.sh --mode hybrid --contextual`
  - `scripts/run_eval.sh --mode graphont`
  - `scripts/run_eval.sh --mode graphont-agentic --corrective`
- **Provenance block** (`metadata.retrieval_config`): contextualization_enabled, collection,
  corrective_enabled, corrective_max_retries, hyde_rag, hyde_graphont_agentic, hybrid_pool_k/top_k,
  graphont_agentic_pool_k/top_k, judge_primary_model, judge_seed, judge_temperature, retrieval_evaluator_model.
- **Contextual collection** (`ccop_clauses_contextual_v3`) was rebuilt via lab scripts
  `.lab/workspace/contextualize_corpus.py` → `contextualize_corpus_v3.py` (hybrid→contextual→v3,
  ~$0.20 gpt-4o-mini each). These lab scripts are **untracked** (`.lab/` not committed).

---

## 6. Pending / next steps

- **UNCOMMITTED work** (nothing committed this whole campaign). Independent commit streams:
  1. Phase-12 corrective slice (channel fix, round1_survivors, merge log, corrective nodes/tests, --corrective flag)
  2. D6 fixes (`_extract_clause_ids`, half-point, formatter, D6 tests, gt-improvements-20260727.md)
  3. ADR-010 (contextual default flip, --contextual, settings + .env.example)
  4. ADR-011 (HyDE default flip, settings + .env.example)
  5. Category-matching fix (`_bench_key`) + evaluate.py provenance/--out-dir/run-id-suffix
  6. Report tooling: `src/scripts/run_eval.sh`
  7. (optional) commit `.lab/workspace/contextualize_*.py` to make contextual collection reproducible
- **For the report:** use §2/§2b/§2c numbers. Lead with graph>hybrid (+0.10). Present agentic/corrective/
  HyDE/context as within-noise (with wider-context as a clean negative). Frame D5/D6 as the ceiling.
- **Recommended before publishing intra-graph rankings:** larger-sample re-run of graphont /
  graphont-agentic / graphont-agentic+corr (drop `--test-ids` for full 435).
- **Untried:** `graphcpl` mode (Phase-11 compliance gate) — the one structural change not yet run.
- **Known metric caveat:** GT-1 (narrow gold sets) + judge non-determinism cap absolute D6/score meaning.

---

## 7. Key file paths
- Results: `src/results/evaluations/final/{2026-07,2026-08}/`
- Runner: `src/scripts/run_eval.sh`
- Category fix / provenance: `src/application/use_cases/evaluate_model.py`
- D6: `src/domain/services/llm_judge_service.py` + `tests/domain/services/test_citation_correctness_d6.py`
- ADRs: `docs/project_notes/decisions.md` (ADR-010, ADR-011)
- GT improvements: `docs/project_notes/gt-improvements-20260727.md`
- Report: `report/term3-end/T3-Final-Report-Sagar-1010736-Aether-CCoP.docx`
