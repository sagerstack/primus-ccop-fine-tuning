---
phase: 03.1-eval-run-traceability
verified: 2026-04-21T00:00:00Z
status: passed
score: 9/9 must-haves verified
---

# Phase 3.1: Eval Run Traceability & I/O Capture — Verification Report

**Phase Goal:** Make every evaluation run traceable and debuggable. Introduce deterministic `run_id` of format `eval-run-{mode}-{scope}-{yyyyMMdd}-{HHmm}`, persist full composed prompt and retrieved contexts per test case in result JSON, and propagate token counts and latency from the RAG graph end-to-end.

**Verified:** 2026-04-21
**Status:** PASSED
**Re-verification:** No — initial verification

---

## SC1: run_id format and generation

**Verdict: PASS**

`src/domain/value_objects/run_id.py` — `RunId.value` property renders:

```
f"eval-run-{self.mode}-{self.scope}-{self.timestamp.strftime('%Y%m%d-%H%M')}"
```

- `mode` constrained by `_VALID_MODES = {"hybrid", "llm-only", "rag-only"}` — invalid values raise `ValueError`
- `scope` is non-empty (empty/whitespace raises `ValueError`)
- `-{HHmm}` suffix is present as decided in CONTEXT.md for sub-day uniqueness — consistent with the goal's stated intent

`build_scope` covers all specified patterns:
- `suite` (no args or all benchmarks)
- `benchmark-{B}` (single)
- `benchmarks-{B1}-{B2}` (multi, sorted numerically via `int(b[1:])`)
- `tier-{N}`
- `test-{id}` / `test-{id1}-{id2}` (sorted ascending)

`for_query()` factory produces `scope="query"`.

CLI wiring (`src/presentation/cli/commands/evaluate.py` line 139–146): `RunId.build_scope(...)` called before `use_case.execute`, `run_id.value` printed and passed into `EvaluationRequestDTO`.

Test evidence: 27/27 tests in `test_run_id.py` pass, covering every branch including numeric sort (`B2 < B3 < B11`).

---

## SC2: Result JSON filename uses run_id as prefix

**Verdict: PASS**

`JSONResultRepository._generate_filename_v6` (line 256–275):

```python
return f"{run_id}-{model_name}.json"
```

Raises `ValueError` if `metadata.run_id` is missing.

Files land under `self._results_dir / dt.strftime("%Y-%m")` (monthly subdir), created lazily via `_monthly_dir`.

Example: `eval-run-hybrid-test-B3-001-20260421-1430-primus-reasoning.json` under `2026-04/`.

Test evidence: `TestSaveEvaluationRunMonthlyLayout.test_file_lands_in_monthly_subdir` verifies exact path including month dir and filename. 19/19 repository tests pass.

---

## SC3: metadata.run_id and schema_version=6 present in JSON

**Verdict: PASS**

`evaluate_model.py._build_evaluation_metadata` (line 722–726):

```python
metadata = {
    "run_id": request.run_id,
    "schema_version": 6,
    ...
}
```

`EvaluationRequestDTO` carries `run_id: Optional[str]` (confirmed via grep on `evaluation_request_dto.py`).

`query.py` (line 176–178) also writes `schema_version: 6` and `run_id` for query persistence.

Test evidence: `test_metadata_run_id_present` and `test_metadata_schema_version_is_6` in repository test file pass.

---

## SC4: Per-test entry persists system_prompt, user_prompt, retrieved contexts, non-zero tokens, non-zero latency

**Verdict: PASS (with one expected exception for rag-only)**

### 4a — system_prompt and user_prompt

Both generation node (`generation.py` lines 133–136) and fallback node (`fallback.py` lines 98–101) extract `system_prompt` and `user_prompt` from formatted LangChain messages before invoking the chain, then write to `GraphState`. `rag_only_response` node sets both to `""` explicitly (no LLM call).

`_serialize` in `json_result_repository.py` (lines 344–349) writes both fields to the test result entry unconditionally.

### 4b — retrieved_contexts sidecar

Written as `{run_id}-contexts.json` in the same monthly dir when `contexts_by_test_id` is provided (non-empty). The map is keyed by `test_id` with full chunk metadata per entry. `rag_only_response` and `generate_response` nodes both populate `retrieved_contexts_detailed` in `GraphState`. `fallback_generation` sets it to `[]`.

Test evidence: `TestSidecarFile` — 3 tests (exists, payload intact, absent when no contexts) all pass.

### 4c — non-zero prompt_tokens / completion_tokens / total_tokens

`generation.py` (lines 144–156) reads from Ollama `response_metadata.prompt_eval_count` (primary) and `usage_metadata.input_tokens` (fallback). `completion_tokens` from `eval_count`. `total_tokens` computed as sum when `usage_metadata.total_tokens` absent.

`fallback.py` uses identical pattern (lines 110–121).

Token fields propagate: `GraphState` → `RagResponse` (fields with `default=0, ge=0`) → `ModelResponse` (constructed with `prompt_tokens`, `completion_tokens`, `total_tokens`) → `EvaluationResult` → serialized via `_serialize`.

**Caveat for rag-only:** `rag_only_response` node explicitly sets all token fields to 0 (no LLM call). This is correct by design and documented in the node's comment.

### 4d — non-zero latency_ms

Both `generate_response` and `fallback_generation` measure `perf_counter()` wall time and write `int((perf_counter() - _start) * 1000)` into `state["latency_ms"]` — set even on exception paths. Propagates through `RagResponse.latency_ms` → `ModelResponse.latency_ms`.

Test evidence: `test_token_and_latency_fields_serialized` in repository test verifies `prompt_tokens=15`, `completion_tokens=25`, `total_tokens=40`, `latency_ms=750` survive the full serialize → write → read cycle.

---

## SC5: End-to-end propagation chain

**Verdict: PASS**

Full chain verified by code inspection:

1. `GraphState` — 7 I/O fields declared in `graph_state.py` (lines 45–52)
2. `RagResponse` — 7 corresponding fields with `default=0/""` in `i_rag_pipeline.py` (lines 44–67)
3. `LangGraphRagAdapter.query` — all 7 fields forwarded from `final_state` to `RagResponse` constructor (lines 79–85 of `langgraph_rag_adapter.py`)
4. `evaluate_model.py._evaluate_test_case` — `system_prompt_captured`, `user_prompt_captured`, `retrieved_contexts_detailed_captured` captured from `rag_response` (lines 211–213); `ModelResponse` built with full token breakdown (lines 199–207)
5. `EvaluationResult` — accepts and stores all three prompt/context fields (constructor args `system_prompt`, `user_prompt`, `retrieved_contexts_detailed`)
6. `EvaluationResultDTO` — 6 traceability fields present (lines 90–109 of `evaluation_result_dto.py`)
7. `_serialize` — writes `system_prompt`, `user_prompt`, `prompt_tokens`, `completion_tokens`, `total_tokens` to test result entry (lines 344–349)

Initial state defaults in `graph.py` (lines 162–169) ensure all 7 I/O fields are initialized to falsy values before graph execution.

---

## SC6: --verbose-io CLI flag

**Verdict: PASS**

`evaluate.py` declares:

```python
verbose_io: bool = typer.Option(
    False,
    "--verbose-io",
    help="Show captured system/user prompts and retrieved contexts per test case"
)
```

When enabled:
- Loads sidecar JSON from `{month_dir}/{run_id}-contexts.json` after evaluation completes
- Displays `system_prompt` (truncated at 600 chars), `user_prompt` (1200 chars) per test case
- Displays each retrieved context from sidecar with `citation_id`, `section`, `clause`, `score`, text preview
- Displays token breakdown `prompt=N completion=N total=N`

Plain `--verbose` on the `query ask` command (unchanged, still works via `query.py`) is additive and not replaced.

---

## SC7: Aggregated file dropped; rglob-based report discovery

**Verdict: PASS — deviation is documented, intentional, and correctly implemented**

Per `03.1-CONTEXT.md` (decisions section, "Filename and directory layout"):

> Existing aggregated `{model}_results.json` file is **dropped** (no longer written)
> `ccop-eval report` tooling rewired to read per-run files via glob pattern over `evaluations/**/*-{model}.json`

`save_batch` is a documented no-op (lines 31–41 of `json_result_repository.py`) with a clear log message explaining the deprecation.

`load_by_model` (lines 125–165) uses `self._results_dir.rglob(f"*-{model_name}.json")`, skips sidecar files (those ending in `-contexts.json`), and skips pre-v6 files (missing `run_id` or `schema_version != 6`) with a warning log.

`generate_report.py` calls `self._result_repository.load_by_model(model_name)` (confirmed via grep), so report tooling reads per-run v6 files across all monthly subdirs.

The deviation is acceptable: the decision is locked in CONTEXT.md, the no-op is explicitly logged, and legacy files are gracefully skipped rather than erroring.

---

## SC8: Tests updated and new tests present

**Verdict: PASS**

Test files exist and pass (88/88 in the Wave 3 sweep):

| File | Tests | Result |
|------|-------|--------|
| `tests/domain/value_objects/test_run_id.py` | 27 | PASS |
| `tests/infrastructure/test_json_result_repository_v6.py` | 19 | PASS |
| `tests/application/use_cases/test_evaluate_model_metadata.py` | 29 | PASS |
| `tests/rag/retrieval/test_graph_state.py` | 13 | PASS |
| **Wave 3 total** | **88** | **PASS** |

Coverage for `run_id.py` and `graph_state.py` shows 100% per the coverage report output.

---

## SC9: Bugs #4 and #5 addressed

**Verdict: PASS**

**Bug #4 — tokens/latency always 0:**

Root cause was no extraction of `prompt_eval_count`/`eval_count` from Ollama response metadata. Now fixed in both `generation.py` and `fallback.py` with `response_metadata.get("prompt_eval_count", usage_metadata.get("input_tokens", 0))`. Latency measured with `perf_counter()` wall time in both generation paths.

`OllamaGateway.generate_response` (direct path) similarly reads `response_data.get("prompt_eval_count", 0)` and `response_data.get("eval_count", 0)` and constructs `ModelResponse` with explicit `prompt_tokens`, `completion_tokens`, `total_tokens` (lines 55–70 of `ollama_gateway.py`).

**Bug #5 — SC13c full prompt not captured:**

Root cause was no storage of composed prompt in results. Fixed by capturing `system_prompt` and `user_prompt` from `formatted_messages` before chain invocation in both `generation.py` and `fallback.py`, propagating through `GraphState` → `RagResponse` → `EvaluationResult` → serialized JSON.

---

## Summary

All 9 success criteria verified. The phase is structurally complete end-to-end:

- Run ID VO is immutable, deterministic, and correctly wired into the CLI entry point
- Schema v6 filename and directory layout implemented and tested
- Token/latency extraction from Ollama response metadata is in place on all LLM-calling paths
- Full prompt capture (system + user with RAG context interpolated) is captured pre-invocation in both generation and fallback nodes
- Sidecar contexts file written per-run for hybrid and rag-only modes
- `--verbose-io` flag wired to display all captured fields post-evaluation
- Report tooling rewired to `rglob`-based discovery; deviation from original aggregated-file spec is documented and intentional
- All 88 Wave 3 tests pass (no regressions observed in the targeted sweep)

**Phase 3.1 is ready to unblock Phase 3.2.**

---

_Verified: 2026-04-21_
_Verifier: Claude (gsd-verifier)_
