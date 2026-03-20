# Bug Log

This file logs bugs, their solutions, and prevention notes. Keep entries brief and chronological.

## Format

Each bug entry should include:
- Date (YYYY-MM-DD)
- Brief description of the bug/issue
- Solution or fix applied
- Any prevention notes (optional)

Use bullet lists for simplicity. Older entries can be manually removed when they become irrelevant.

---

## Entries

### 2026-02-04 - Hallucination Detection False Positives
- **Issue**: `ModelResponse.contains_hallucination_indicators()` flags legitimate uncertainty language as hallucinations
- **Root Cause**: Overly aggressive regex patterns treating hedging language ("may require", "depends on context") as hallucination indicators
- **Status**: Known issue (documented in .planning/codebase/CONCERNS.md)
- **Workaround**: None currently - requires distinguishing uncertainty language from fabrication indicators
- **Prevention**: Separate uncertainty detection from fabrication detection in future refactor

### 2026-02-04 - Grounding Score Discontinuity
- **Issue**: Grounding scores jump discontinuously (1.0, 0.7, 0.0) based on discrete violation thresholds
- **Root Cause**: Hardcoded discrete thresholds in `_calculate_grounding_score()` without gradual penalty
- **Status**: Known issue
- **Impact**: Minor grounding issues cause disproportionate score drops
- **Prevention**: Replace discrete thresholds with continuous penalty function

### 2026-03-20 - Reasoning chain-of-thought displayed as raw response
- **Issue**: Llama-Primus-Reasoning produces chain-of-thought ("First, I need to recall...", "Therefore...") followed by "Final Answer:" — entire reasoning chain shown as the response
- **Root Cause**: Model is a reasoning model by design. No post-processing to separate thinking from final answer
- **Status**: Known — cosmetic for evaluation, relevant for user-facing query display
- **Fix**: Post-process response to extract content after "Final Answer:" for display, keep full response for LLM Judge scoring

### 2026-03-20 - Response tokens and latency always show 0
- **Issue**: Per-test-case panel displays "Response (0 tokens, 0ms)" despite model generating full responses
- **Root Cause**: `evaluate_model.py:192-193` hardcodes `tokens_used=0, latency_ms=0` with comment "Not tracked from graph this phase" — RAG graph execution doesn't propagate token count/latency back to ModelResponse
- **Status**: Known gap — same graph execution boundary issue as SC13(c)
- **Impact**: No visibility into inference cost or performance per test case

### 2026-03-20 - DEFERRED: Full prompt display in per-test-case panel (SC13c)
- **Issue**: Per-test-case panel doesn't show the actual prompt sent to the model (system prompt + user prompt with RAG context)
- **Root Cause**: Data pipeline doesn't propagate llm_context or system_prompt from GraphState through RagResponse to EvaluationResult/CLI
- **Status**: Deferred — requires data model changes across GraphState, RagResponse, EvaluationResultDTO
- **Origin**: Phase 2.2 Plan 02, SC13(c)

### 2026-03-20 - Hallucination Metric Penalizes Correct Novel Reasoning
- **Issue**: Hallucination metric uses RAGAs faithfulness with ground truth as context. Any claim not in the ground truth is scored as "unsupported" — including correct reasoning, valid clause citations, and additional analysis
- **Impact**: Metric measures divergence from ground truth, not actual hallucination. Cannot distinguish correct additions (good) from fabricated claims (bad). Directly conflicts with LLM Judge rubric which rewards "additional correct and relevant information" at Score 3
- **Status**: Known design limitation
- **Fix**: Needs a different approach — e.g., use the full CCoP document corpus as context instead of ground truth, or split into two metrics: one for factual accuracy vs ground truth, one for fabrication detection vs source documents

### 2026-03-20 - B3 Ground Truth / Rubric Misalignment
- **Issue**: B3 expected response gives an absolute "non-compliant" answer, but the B3 conditional_logic rubric rewards deep conditional reasoning (specific controls analysis, residual risk trade-offs). The expected response itself would score ~1-2/3 on its own rubric.
- **Impact**: Model is penalized for matching the expected response (high answer_correctness, low LLM Judge). Metrics contradict each other.
- **Status**: Known issue — needs ground truth update
- **Fix**: Update B3 expected response to demonstrate Score 3 conditional reasoning. Audit other B-benchmarks for same misalignment. Then consider system prompt improvements for reasoning depth.

---

## Tips

- Keep descriptions under 2-3 lines
- Focus on what was learned, not exhaustive details
- Include enough context for future reference
- Date entries so you know how recent the issue is
- Periodically clean out very old entries (6+ months)
