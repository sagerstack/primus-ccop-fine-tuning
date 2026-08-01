# Researcher Config — Maximize RAG vs llm-only

**Created**: 2026-04-25
**Branch**: research/maximize-rag-vs-llm-only

## Objective

Increase hybrid (RAG-augmented) composite score over llm-only on the 30-case stratified sample so that:
1. **Total composite**: hybrid ≥ llm-only + 0.20 (absolute)
2. **Per-benchmark**: every benchmark's hybrid mean > llm-only mean

The hypothesis is that providing correct CCoP context to the model SHOULD improve scoring under the LLM judge. Currently hybrid is *underperforming* llm-only by 1.67 pp — strong evidence of a real defect somewhere in the pipeline (retrieval, generation, or judge).

## Primary Metric

**`hybrid_composite − llm_only_composite`** (higher better; target ≥ +0.20)

Measure: simple mean of per-case `score` across the test set being evaluated.

Direction: higher is better.

## Secondary Metrics

| Metric | Source | Direction | Target |
|--------|--------|-----------|--------|
| ragas_context_recall | RAGAs metrics in result file | higher | > 0.70 from current 0.250 |
| ragas_context_precision | RAGAs | higher | > 0.80 from current 0.533 |
| ragas_context_faithfulness | RAGAs | higher | > 0.80 from current 0.525 |
| Per-benchmark hybrid > llm-only | derived | per-benchmark must hold | every benchmark |
| D3 factual_grounding (hybrid) | LLM judge metrics | higher | > 0.30 from current 0.022 |

## Iteration Strategy

Per user direction: incremental scope expansion.

**Stage A — Single canary case** (~3-5 min/exp): Use one test case to iterate fast on ideas.
- Canary: **B08-001** (compliance prioritization, llm-only=0.500 hybrid=0.389, ctx_precision=1.0 but faithfulness=0.0 — clean signal of "model ignored good context")

**Stage B — Single benchmark** (~10-15 min/exp): When a Stage A change shows promise, validate on all canary's benchmark cases (B08-001 + B08-018).

**Stage C — Subset of 10** (~30 min/exp): Validate generalization across benchmark types using the diverse subset:
- Losers: B02-012, B02-014, B08-001, B08-018, B07-022
- Winners: B05-013, B05-016, B22-015, B18-001
- Worst: B23-001

**Stage D — Full 30** (~75-90 min): Final validation when subset shows hybrid composite ≥ llm-only + 0.10 absolute.

## Run Commands

**Canary single case (Stage A)**:
```bash
poetry run ccop-eval evaluate run --model primus-reasoning --mode hybrid \
  --test-ids B08-001
```

**Single benchmark (Stage B)**: 
```bash
poetry run ccop-eval evaluate run --model primus-reasoning --mode hybrid \
  --test-ids B08-001 --test-ids B08-018
```

**10-case subset (Stage C)** — full TEST_IDS list in scripts/run_subset_hybrid.sh

**Full 30 (Stage D)**: same TEST_IDS as 30-subset sample.

All run from `src/` directory.

## Scope (in)

- `src/rag/**` — retrieval pipeline, fallback prompt, generation prompt, grading
- `src/rag/ingestion/**` — chunking, indexing (re-ingestion permitted; ~30 min)
- `src/domain/services/llm_judge_service.py` — judge prompt, citation handling
- `docs/phase-2/evaluation-rubrics.md` — rubric anchors, prompt scaffolding
- `src/config/.env.example` + `src/infrastructure/config/settings.py` — RAG knobs (top_k, top_n, thresholds)

## Scope (out)

- llm-only baseline (frozen at 0.343 — must NOT be re-run)
- Ground truth files (`ground-truth/test-suite/*.jsonl`) — no biasing
- LLM judge model swap (Qwen3 stays primary)
- Primus model swap (primus-reasoning stays)
- OpenRouter API key, infra config

## Wall-clock Budget

| Stage | Default | Hard cap |
|-------|---------|----------|
| A (1 case) | 5 min | 8 min |
| B (1 benchmark, ~2 cases) | 12 min | 20 min |
| C (10 cases) | 30 min | 45 min |
| D (30 cases) | 90 min | 120 min |

## Termination

Either of:
1. **Target hit**: hybrid composite ≥ llm-only + 0.20 absolute on full 30, AND every benchmark hybrid > llm-only.
2. **User interrupts**.

No self-imposed experiment count cap. `.lab/` persists across sessions.

## Baseline (#0) — known from prior data

| Metric | Value |
|--------|-------|
| llm-only composite (30 cases, simple mean) | **0.3426** |
| hybrid composite (30 cases, simple mean) | **0.3259** |
| Primary metric (hybrid − llm-only) | **−0.0167** ← target ≥ +0.20 |
| RAGAs context_recall (mean, hybrid) | 0.250 |
| RAGAs context_precision (mean, hybrid) | 0.533 |
| RAGAs context_faithfulness (mean, hybrid) | 0.525 |
| D3 factual_grounding mean (hybrid) | 0.022 |
| D3 factual_grounding mean (llm-only) | 0.033 |

Source files:
- llm-only: `src/results/evaluations/2026-04/eval-run-llm-only-tests-30-836edbc5-20260425-1144-primus-reasoning.json`
- hybrid: `src/results/evaluations/2026-04/eval-run-hybrid-tests-30-836edbc5-20260425-1009-primus-reasoning.json`

## Per-benchmark baseline deltas (hybrid − llm-only)

```
B01: -0.056   B02: -0.167   B03: -0.056   B04: +0.028
B05: +0.139   B06: +0.056   B07: -0.083   B08: -0.167
B09: +0.000   B10: +0.056   B12: -0.028   B13: -0.028
B14: +0.000   B18: +0.111   B21: -0.028   B22: +0.111
B23: +0.000   B24: +0.000
```

Hybrid currently wins 6 / loses 8 / ties 4.

## Best so far

| Field | Value |
|-------|-------|
| Best experiment | #0 (baseline) |
| Best metric | −0.0167 |
| Distance to target | 0.217 (very far) |

---

## Metric v3 — Phase A retrieval-quality focus (mid-research revision)

**Date**: 2026-04-26
**Driver**: Per user direction "focus on retrieval quality from Qdrant. Improve to recall@C ≥ 0.8 on 30 subset."

### Primary metric (v3)
**`mean_recall_at_C`** = mean of per-case recall@N where N = case-specific GT cardinality, against agent-team-corrected GT.

- Higher = better. Target ≥ 0.8.
- Measured by `.lab/workspace/retrieval_eval.py` with `--corrected-gt ../.lab/workspace/agents/corrected-gt.json --corrected-gt-field recommended_ccop_only`
- Computed at end of run as `metrics.mean_recall_at_C`

### Secondary metrics
| Metric | Direction | Notes |
|--------|-----------|-------|
| recall_at_K (K=50) | higher | Embedder reachability ceiling. Currently 0.75 |
| recall_at_3 | higher | Production reality (top_n=3) |
| recall_at_5 | higher | If top_n bumped to 5 |
| recall_at_8 | higher | If top_n bumped to 8 |
| precision_at_C | higher | Quality of retrieved chunks |
| f1_at_C | higher | Combined |

### Scope expansion
**Re-ingestion is now in scope.** Approved changes:
- Chunking strategy (parent-child, contextual prefixes, hierarchical, sliding window, etc.)
- Embedding model (e.g., BGE-M3 swap)
- Sparse model (e.g., SPLADE)
- Index structure (multi-collection, parent-child store)
- Query rewriting (HyDE, multi-query)

### Best under v3
| Field | Value |
|-------|-------|
| Best experiment | #13 |
| recall@C | **0.335** |
| recall@K | 0.750 |
| Distance to target | 0.465 (ambitious) |

### Wall-clock budget v3
- Per experiment: 60 min default, 120 min hard cap (re-ingestion can take ~30 min)
