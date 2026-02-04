# Codebase Concerns

**Analysis Date:** 2026-02-04

## Tech Debt

### Large Service Classes with Multiple Responsibilities

**Issue:** `src/domain/services/scoring_service.py` (580 lines) has grown too large with extensive scoring logic consolidated in one class.

**Files:**
- `src/domain/services/scoring_service.py` (580 LOC)
- `src/domain/services/benchmark_validator.py` (281 LOC)

**Impact:** Difficult to modify individual benchmark scoring without affecting others. Adding new benchmarks requires editing this large monolithic class. High risk of unintended side effects when changing scoring criteria.

**Fix approach:**
1. Extract benchmark-specific scorers into separate strategy classes (Strategy pattern)
2. Create `ScorerRegistry` to map benchmark types to scorer instances
3. Move each `_score_bX_*` method into dedicated `BXScorer` class
4. Reduce main scoring_service to orchestration logic only

### Hardcoded Threshold Values in Settings

**Issue:** Business logic thresholds are hardcoded in `src/infrastructure/config/settings.py` and scattered throughout scoring logic.

**Files:**
- `src/infrastructure/config/settings.py` (baseline_threshold=0.15, finetuned_threshold=0.50, deployment_threshold=0.85)
- `src/domain/services/scoring_service.py` (lines 290-292, 456-460: 0.70, 0.60 thresholds hardcoded)

**Impact:** Changing evaluation criteria requires code changes. Cannot run A/B testing without redeployment. Phase transitions are inflexible.

**Fix approach:**
1. Create `ThresholdConfiguration` value object
2. Load all thresholds from environment or configuration database
3. Use threshold registry pattern for benchmark-specific thresholds
4. Make thresholds runtime-configurable without code changes

### Unimplemented Benchmarks (Tier 2 Expert Rubric)

**Issue:** Benchmarks B7, B10, B14, B16 deliberately raise `NotImplementedError`.

**Files:**
- `src/domain/services/scoring_service.py` (line 87-91)

**Impact:** Code path explicitly blocks certain benchmarks. Running evaluation on these benchmarks fails with unclear messaging. Creates ambiguity about whether they're unsupported or incomplete.

**Fix approach:**
1. Document which benchmarks are intentionally deferred
2. Create `UnsupportedBenchmarkException` with clearer messaging
3. Add entry in CONCERNS about planned implementation
4. Consider placeholder scorers that return neutral scores instead of errors

## Known Bugs

### Hallucination Detection Overly Aggressive

**Issue:** `src/domain/entities/model_response.py:contains_hallucination_indicators()` (lines 136-159) flags uncertainty language as hallucinations.

**Symptoms:** Legitimate phrases like "may require", "depends on context", "should consider" trigger false positives. Reasonable compliance responses penalized.

**Files:** `src/domain/entities/model_response.py`

**Trigger:** Model responses using hedging language common in cybersecurity compliance (which emphasizes context-sensitivity).

**Workaround:** None currently. Responses using cautious language automatically fail hallucination check.

**Fix approach:**
1. Distinguish between uncertainty language (acceptable) and fabrication indicators (forbidden)
2. Separate `contains_uncertainty_language()` from `contains_fabrication_indicators()`
3. Only mark as hallucination if fabrication patterns detected (e.g., "CCoP requires X that doesn't exist")
4. Update grounding check to use fabrication patterns only

### Floating Point Precision in Grounding Score

**Issue:** `src/domain/services/scoring_service.py:_calculate_grounding_score()` (lines 570-580) uses hardcoded violation thresholds without tolerance for edge cases.

**Symptoms:** Grounding scores jump discontinuously between 1.0, 0.7, and 0.0 based on discrete violation count thresholds. No gradual penalty.

**Files:** `src/domain/services/scoring_service.py`

**Impact:** Minor grounding issues cause disproportionate score drops.

**Fix approach:**
1. Replace discrete thresholds with continuous penalty function
2. Calculate grounding_score = 1.0 - (violations_count * penalty_per_violation)
3. Clamp to [0.0, 1.0] range

## Security Considerations

### External Model Gateway Dependency Without Timeout Fallback

**Issue:** `src/infrastructure/adapters/models/ollama_gateway.py` depends on Ollama being available and responsive.

**Risk:** If Ollama becomes unresponsive, evaluation hangs until timeout (300 seconds). No circuit breaker pattern or graceful degradation.

**Files:**
- `src/infrastructure/external/ollama_client.py` (timeout=300)
- `src/infrastructure/adapters/models/ollama_gateway.py`

**Current mitigation:** Basic exception handling with re-raising.

**Recommendations:**
1. Implement circuit breaker pattern (fail-fast after N consecutive timeouts)
2. Add retries with exponential backoff for transient failures
3. Implement health check endpoint
4. Add timeout per request, not just client-level timeout
5. Consider fallback to mock gateway for non-critical evaluations

### Subprocess Execution via Claude Agent SDK

**Issue:** `src/domain/services/llm_judge_service.py` (lines 100-111) calls external subprocess without input validation.

**Risk:** If `self._model` or `prompt` contain special characters, potential command injection through subprocess argument.

**Files:** `src/domain/services/llm_judge_service.py`

**Current approach:** `subprocess.run()` with shell=False (safe) but prompt is user-controlled indirectly through test cases.

**Recommendations:**
1. Validate prompt for dangerous characters before subprocess call
2. Use explicit list form for subprocess args (already done with shell=False)
3. Add prompt sanitization layer
4. Consider switching to OpenAI SDK if Anthropic provides Python SDK instead of CLI

### Hardcoded Hallucination Patterns

**Issue:** `src/domain/services/scoring_service.py` (lines 562-568) contains hardcoded regex patterns for hallucination detection.

**Risk:** Patterns are specific to observed hallucinations. New hallucination types won't be caught. If CCoP evolves, patterns become stale.

**Files:** `src/domain/services/scoring_service.py`

**Recommendations:**
1. Move hallucination patterns to configuration file
2. Load patterns from database or external source
3. Version hallucination detection patterns
4. Add telemetry to track which patterns catch which hallucinations
5. Regular audits to update patterns based on new model outputs

## Performance Bottlenecks

### Semantic Embedding Computation Per Response

**Issue:** `src/domain/services/semantic_similarity_service.py` uses `SentenceTransformer` model that requires full encoding for each comparison.

**Problem:** Encoding expected_response + all key_facts for every response is O(n) per evaluation. For 100 responses × 5 key facts = 500 encode operations.

**Files:**
- `src/domain/services/semantic_similarity_service.py`
- `src/domain/services/scoring_service.py` (Tier 2 scoring)

**Cause:** Key fact completeness check encodes each fact independently. Batch encoding exists but not used for key facts.

**Improvement path:**
1. Pre-compute and cache expected_response embedding at evaluation start
2. Pre-compute key_fact embeddings once during test case loading
3. Use `calculate_batch_similarity()` for key_fact recall
4. Cache embeddings in result artifact for reuse in reports

### Unbounded Concurrent Evaluations

**Issue:** `src/infrastructure/config/settings.py` has `max_concurrent_evaluations=3` but concurrency control not implemented in codebase.

**Files:**
- `src/infrastructure/config/settings.py` (line 60)
- `src/application/use_cases/evaluate_model.py`

**Problem:** Setting defined but never used. No semaphore or queue in evaluation orchestration.

**Impact:** Could exceed resource limits if evaluation framework later implements concurrency without respect for setting.

**Fix approach:**
1. Implement semaphore in `evaluate_model.py` use case
2. Use `asyncio.Semaphore(max_concurrent_evaluations)` for async/await
3. Add queue for pending evaluations
4. Log queue depth for monitoring

## Fragile Areas

### ModelResponse Entity with Complex Business Logic

**Files:** `src/domain/entities/model_response.py`

**Why fragile:** Entity mixes three concerns:
1. Identity/lifecycle (response_id, created_at)
2. Content analysis (extract_citations, contains_hallucination_indicators, contains_code_snippet)
3. Validation rules

**Safe modification:**
- Changing validation rules: Safe, confined to `_validate()` method
- Adding new analysis methods: Moderate risk, doesn't affect persistence
- Changing extraction patterns: High risk, affects downstream scoring

**Test coverage:** Limited to basic entity tests. Content analysis methods have minimal test coverage for edge cases.

### Scoring Service Benchmark-Specific Logic

**Files:** `src/domain/services/scoring_service.py`

**Why fragile:**
1. 580 lines concentrated in single class
2. Multiple scoring strategies (label-based, Jaccard, semantic, LLM judge) intermingled
3. Each benchmark scorer has custom thresholds and heuristics
4. Changes to one benchmark affect readability of others

**Safe modification:**
- Adding new evaluation metric: Find the relevant `_score_bX_*` method, extract new metric calculation
- Changing benchmark threshold: Modify specific threshold value in that method (but hardcoded!)
- Modifying scoring logic: Must carefully test that changes don't affect other benchmarks

**Test coverage:** High-level integration tests exist, but unit tests for individual scorer methods are sparse.

### Test Case Entity with Many Optional Fields

**Files:** `src/domain/entities/test_case.py`

**Why fragile:**
- 312 lines with ~30+ optional fields
- Different benchmarks use different subset of fields
- Validation doesn't enforce which fields are required for which benchmarks
- Easy to add test case without required fields for specific benchmark, causing scorer to fail

**Safe modification:**
- Adding new optional field: Safe, backward compatible
- Adding new required field: High risk, existing test cases missing it
- Modifying validation: Could break existing test cases

**Test coverage:** Basic entity tests pass, but semantic validation (field requirements per benchmark) not tested.

## Scaling Limits

### Sentence Transformer Model Memory Usage

**Current capacity:** all-MiniLM-L6-v2 model (33M parameters, ~130MB) loads into memory once (singleton).

**Limit:** If adding larger models (base/large variants ~440M parameters, ~1.7GB), memory usage becomes significant. Concurrent inference could require multiple model instances.

**Scaling path:**
1. Monitor peak memory usage with current model
2. If scaling to multiple concurrent evaluations: Consider model quantization
3. Use ONNX runtime for faster inference
4. Consider model serving (vLLM, TensorRT) if semantic similarity becomes bottleneck
5. Implement lazy loading: Load model only when Tier 2 scoring starts

### Test Case Data File I/O

**Current capacity:** JSONL test case files loaded entirely into memory via `JsonlTestCaseRepository`.

**Files:**
- `src/infrastructure/adapters/repositories/jsonl_test_case_repository.py`

**Limit:** 1000s of test cases load quickly, but 100k+ test cases cause memory bloat.

**Scaling path:**
1. Implement streaming/chunked reading for large test case files
2. Add indexing (offset table) to JSONL files for random access
3. Move to database (SQLite for local, PostgreSQL for prod) if test cases exceed 10k
4. Implement pagination for test case retrieval

### Ollama Model Size Constraints

**Current constraint:** Models downloaded to `~/.cache/ccop-models` via huggingface-hub.

**Files:**
- `src/infrastructure/config/settings.py` (line 46)
- `src/infrastructure/adapters/converters/gguf_converter.py`

**Limit:** Primus-Reasoning 70B with Q5_K_M quantization ~45GB. Won't fit on constrained dev machines.

**Scaling path:**
1. Support multiple quantization levels (current: Q4_K_M to Q8_0)
2. Implement model streaming from remote server for prod
3. Document minimum hardware requirements per model variant
4. Consider smaller model fine-tuning for critical benchmarks

## Dependencies at Risk

### sentence-transformers Library Stability

**Risk:** sentence-transformers is research library with frequent breaking changes between major versions.

**Current:** `^3.3.1` in pyproject.toml

**Impact:** PyTorch 2.5.0 dependency tight coupling could break with environment updates.

**Migration plan:**
1. Consider switching to `all-mpnet-base-v2` model on stable `sentence-transformers>=2.0`
2. Evaluate `onnx-runtime` + HuggingFace transformers as alternative
3. Pin to specific minor version if breaking changes detected in v3.x
4. Maintain compatibility matrix for torch versions

### Click/Typer CLI Framework Compatibility

**Risk:** Click pinned to `8.1.7` due to breaking changes in 8.2+. Typer built on Click.

**Current:**
- click = "8.1.7" (pinned)
- typer = "^0.12.5" (float version)

**Impact:** Future Click updates won't be picked up. Typer may require newer Click, creating conflict.

**Migration plan:**
1. Test Typer compatibility with Click 8.2+ when stable
2. If incompatible, consider switching to `argparse` with decorators or `cleo`
3. Monitor Typer releases for Click pin updates

### OpenAI Library for Ollama Compatibility

**Risk:** Using OpenAI library as generic LLM client via Ollama compatibility mode. OpenAI may remove compatibility layer.

**Current:** `openai = "^1.50.0"` (not actively used in visible code, likely planned for Claude integration)

**Impact:** If OpenAI library deprecates Ollama compatibility, would need custom HTTP client (which exists in `ollama_client.py`).

**Migration plan:**
1. OllamaClient is already custom implementation, redundant dependency
2. Remove openai dependency if unused
3. If used for Claude calls, validate compatibility with current OpenAI SDK version

## Missing Critical Features

### Benchmark Implementation Roadmap Transparency

**Problem:** Some benchmarks explicitly unimplemented (B7, B10, B14, B16) but no clear roadmap or priorities.

**Blocks:** Running comprehensive evaluation across all planned benchmarks.

**Recommendations:**
1. Create ROADMAP.md documenting benchmark implementation status
2. Document why B7/B10/B14/B16 deferred (complexity? data availability? scope?)
3. Provide ETA or success criteria for implementation
4. Consider partial implementation (e.g., basic scorer + TODO for expert rubric)

### Caching Layer for Expensive Computations

**Problem:** No caching for semantic embeddings, model responses, or evaluation results between runs.

**Blocks:** Efficient re-evaluation of subsets of benchmarks. Development iteration is slow.

**Recommendations:**
1. Implement response cache keyed by (model, test_id, temperature)
2. Cache semantic embeddings keyed by text_hash
3. Cache evaluation results keyed by (response_id, benchmark_type)
4. Add cache invalidation triggers
5. Monitor cache hit rates

### Rollback Strategy for Scoring Logic Changes

**Problem:** Scoring service changes affect all historical evaluations. No way to re-score with old logic or run A/B tests.

**Blocks:** Safe iteration on scoring algorithms. Can't compare "Option A" vs "Option B" scoring on same dataset.

**Recommendations:**
1. Version scoring algorithms (ScorerV1, ScorerV2)
2. Store scorer_version in EvaluationResult
3. Implement scorer registry with version selection
4. Add re-score capability to regenerate results with different scorer versions
5. Archive old scorer implementations with change history

## Test Coverage Gaps

### Scoring Service Edge Cases Untested

**What's not tested:**
- Division by zero in Jaccard similarity (union = 0)
- Empty key_facts list behavior
- Null/None handling in grounding check
- Penalty logic interactions (semantic penalty + key-fact thresholds)

**Files:** `src/domain/services/scoring_service.py`

**Risk:** Regressions in scoring logic could go undetected. Edge cases in specific benchmarks affect only certain test types.

**Priority:** High - Scoring is core domain logic

### Semantic Similarity Service Batch Processing

**What's not tested:**
- Batch similarity with empty responses list
- Mixed empty/non-empty responses
- Very long text encoding (performance)
- Similarity clamping edge cases

**Files:** `src/domain/services/semantic_similarity_service.py`

**Risk:** Batch scoring for Tier 2 benchmarks could produce incorrect results under edge conditions.

**Priority:** High - Affects multiple benchmarks (B8, B9, B11, B15, B17, B18, B19)

### LLM Judge Service Parsing Robustness

**What's not tested:**
- Malformed JSON responses (missing quotes, trailing commas)
- Score values outside 1-5 range
- Very long justifications
- Non-ASCII characters in Claude response

**Files:** `src/domain/services/llm_judge_service.py`

**Risk:** Judge service crashes on unexpected Claude output format instead of graceful fallback.

**Priority:** Medium - Has error fallback but could be more robust

### Integration Between Validators and Scorers

**What's not tested:**
- Validator allows test case through, but scorer doesn't handle all fields
- Benchmark validator changes without corresponding scorer updates
- Test case fails validation but evaluation still attempted
- Metadata fields validator doesn't check but scorer uses

**Files:**
- `src/domain/services/benchmark_validator.py`
- `src/domain/services/scoring_service.py`

**Risk:** Validator and scorer divergence causes runtime errors during evaluation.

**Priority:** Medium - Affects all benchmarks

### Infrastructure Adapter Error Scenarios

**What's not tested:**
- Ollama connection timeouts (uses real network)
- HuggingFace model download failures
- File system permission errors in repositories
- Corrupted JSONL test case files

**Files:**
- `src/infrastructure/adapters/models/ollama_gateway.py`
- `src/infrastructure/adapters/repositories/jsonl_test_case_repository.py`

**Risk:** Production evaluation fails with opaque error messages instead of clear diagnostics.

**Priority:** Medium - Affects reliability

---

*Concerns audit: 2026-02-04*
