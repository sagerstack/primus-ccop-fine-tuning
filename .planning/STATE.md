# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-04)

**Core value:** Build a hybrid model that CII organizations can trust to interpret CCoP 2.0 correctly
**Current focus:** Phase 3.2 (Corpus and Ground Truth Correctness) — COMPLETE. Sub-goals A (Plans 01-04) and B (Plans 05-07) both delivered. Verifier passed 18/18 must-haves. Ready for Phase 4 (Re-Baseline).

## Current Position

Phase: 3.2 of 8 (Corpus and Ground Truth Correctness) — COMPLETE (verifier passed 18/18)
Plan: 7 of 7 — COMPLETE (validator hard-fail + CLI landed)
Status: Phase 3.2 closed. Clean ground truth (`ccop-eval validate-ground-truth --no-semantic` → 434 valid, 0 errors); `ccop_clauses_hybrid` re-ingested with all 12 CCoP 2.0 sections 5.1-5.12 present; 691-entry inventory + hard-fail validator + deprecated-skip wired end-to-end. Verifier report at `.planning/phases/03.2-corpus-ground-truth-correctness/03.2-VERIFICATION.md`.
Last activity: 2026-04-22 — Completed 03.2-07: Pass-2 regex context-awareness (76 false positives resolved) + ER_FOOTER patcher cluster (17 footer hallucinations) + `ccop-eval validate-ground-truth` CLI + JSONL repo deprecated-skip + 4 CLI integration tests; phase verifier passed 18/18.

Progress: [███████░░░] 67% (7/11 phase-3 plans + 3/3 phase-3.1 plans + 7/7 phase-3.2 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 32
- Average duration: 5.97 min
- Total execution time: 3.22 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. RAG Infrastructure | 4/5 | 28 min | 7 min |
| 1.1. Evaluation Infrastructure Upgrade | 5/5 | 19 min | 3.8 min |
| 1.2. Local RAG Migration | 4/5 | 17 min | 4.25 min |
| 1.3. RAG Quality - Chunking & Retrieval | 2/4 | 15 min | 7.5 min |
| 2. RAG Evaluation | 3/3 | 10 min | 3.3 min |
| 2.1. Evaluation Quality Categorization | 3/3 | 105 min | 35 min |
| 2.2. RAGAs Hallucination Metric & Renaming | 3/3 | ~17 min | ~6 min |
| 2.3. RAGAs Metric Split & Scoring Formula | 3/3 | ~22 min | ~7 min |
| 2.4. LLM Judge Redesign & Metric Simplification | 5/5 | ~20 min | ~4 min |
| 3.1. Eval Run Traceability & I/O Capture | 3/3 | ~90 min | ~30 min |

**Recent Trend:**
- Last 5 plans: 03.2-01 (chunker regex + merge-rule removal), 03.2-02 (table chunks + TOC gate), 03.2-03 (~15min re-ingest + section/phrase verification, SC #8 N/A), 03.2-04 (~33min B3-001 re-eval + funnel diagnostic + sub-goal A closure, SC #9 N/A), 03.2-05 (~60min clause inventory extraction + committed fixture + Cybersecurity Act legal-numbering extension, SC #11 satisfied)
- Trend: Phase 3.2 plans average ~15-60 min; Plans 04-05 longer due to human-verify checkpoint pauses
- Phase 3.1 VERIFIED COMPLETE: 9/9 success criteria PASS, 88/88 schema-v6 targeted tests passing, verifier report at `.planning/phases/03.1-eval-run-traceability/VERIFICATION.md`
- Phase 3.2 sub-goal A COMPLETE (2026-04-21): bugs #9/#10 corpus-level fix shipped; B3-001 retrieval-ranking gap handed off to Phase 4
- Phase 3.2 sub-goal B COMPLETE (2026-04-22): Plan 05 landed clause inventory (691 entries, 7 docs); Plan 06 audited + applied 176 Excel corrections across 13 clusters, regenerated 196 JSONL rows; Plan 07 Pass-2 regex context-awareness + ER_FOOTER patcher (17 real hallucinations) + validator hard-fail + `ccop-eval validate-ground-truth` CLI + JSONL repo deprecated-skip + 4 CLI integration tests
- Phase 3.2 VERIFIED COMPLETE (2026-04-22): 18/18 success criteria PASS; verifier report at `.planning/phases/03.2-corpus-ground-truth-correctness/03.2-VERIFICATION.md`

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap reordered: RAG Infrastructure first (learning priority), then RAG Eval on 118 cases, then Dataset Expansion, then Re-baseline
- Existing 49.2% baseline (from paper) used as comparison point — no re-run needed before RAG eval
- No LangGraph for dataset generation: plain Python script with structured prompting (critic's recommendation from team research)
- Tier-specific prompt templates for dataset generation (factual, reasoning, safety)
- Multi-source dataset: CIIO practitioner + audit questions + adapted external compliance datasets (NIST, ISO 27001) + existing CCoP datasets
- Hybrid approach (RAG + fine-tuning): RAG for grounding, fine-tuning for reasoning — each addresses different gaps
- 85% accuracy target: Industry standard for compliance automation (Thomson Reuters, GSA references)
- **[01-01] PyMuPDF4LLM for PDF parsing:** Preserves tables and structure better than generic loaders
- **[01-01] Section-level semantic chunking:** 87.7% context recall vs ~65% for fixed-size chunking
- **[01-01] All 8 CCoP documents as standard sections:** RESPONSE-TO-FEEDBACK marked as clarification type
- **[01-01] Databricks settings no defaults:** Forces explicit configuration via .env.local
- **[01-02] Delta Sync index type:** Automatic updates when source table changes (no manual re-indexing)
- **[01-02] Lazy client initialization:** Enables dry-run mode without Databricks credentials
- **[01-02] Hybrid search (dense + sparse RRF):** 85% NDCG@10 vs 72% for dense-only (research-backed improvement)
- **[01-03] LLM-as-judge grading with 0.6 threshold:** Prevents 40-60% silent failure rate of naive RAG
- **[01-03] Max 3 retrieval attempts:** Balances quality and latency via self-correction loop
- **[01-03] Raw citation anchors:** Generation embeds `<c>citation_id</c>` for downstream resolution (Plan 01-04)
- **[01-04] End-of-response citation format:** Clean text + references at bottom. Avoids embedding metadata in chunks (degrades retrieval)
- **[01-04] TYPE_CHECKING for circular imports:** Breaks Settings → Container → RAG adapter cycle
- **[01-04] Lazy DI container imports:** Staticmethod pattern defers RAG imports until first use
- **[01-04] Graceful degradation without Databricks:** Existing eval framework works without RAG config
- **[01.2-01] Port/adapter pattern for vector stores:** IVectorStore and IIndexer abstractions enable swappable implementations (Qdrant, Databricks)
- **[01.2-01] Lazy embedding model initialization:** Thread-safe double-checked locking avoids loading 1.3GB+ models on import
- **[01.2-01] BGE query prompt only for queries:** Improves retrieval, degrades document embeddings (per model documentation)
- **[01.2-01] FastEmbed for BM25 sparse vectors:** Lightweight, Qdrant-maintained, drop-in BM25 support
- **[01.2-02] Prefetch + RRF for hybrid search:** Qdrant native API for combining dense/sparse results. RRF is rank-based (no score normalization needed)
- **[01.2-02] IDF modifier in sparse vectors:** FastEmbed BM25 outputs raw TF, Qdrant applies IDF server-side when `modifier=Modifier.IDF` configured
- **[01.2-02] Delete+recreate collection for local dev:** Clean slate approach acceptable for local environment, production would need incremental updates
- **[01.2-02] Deterministic UUID for point IDs:** uuid5 with NAMESPACE_URL generates consistent IDs from string chunk IDs, enables re-indexing without duplicates
- **[01.2-03] Thin wrappers for Databricks:** DatabricksVectorStoreAdapter and DatabricksIndexerAdapter delegate to existing classes, zero modification to existing code
- **[01.2-04] DI container selects adapters based on config:** Qdrant (when qdrant_url set) > Databricks (when databricks_host set) > None. Lazy factories maintain circular dependency protection
- **[01.2-04] EmbeddingService created inside factory:** Not a separate provider, avoids loading 1.3GB+ models when using Databricks
- **[01.2-04] Ingestion uses factory not container:** Batch script creates indexer directly via _create_indexer factory function
- **[01.3-01] Docling for PDF parsing:** Classic pipeline extracts hierarchical markdown better than PyMuPDF4LLM for regulatory structure
- **[01.3-01] Clause-level chunking:** Each chunk = one regulatory requirement (e.g., "5.2.1"). Non-negotiable for compliance Q&A where auditors need specific clause citations
- **[01.3-01] Deterministic chunk IDs:** {source}::{clause} format generates collision-free uuid5 point IDs, enables re-indexing
- **[01.3-01] Parent hierarchy in metadata only:** ChunkMetadata.parent_path stores "Chapter 5 > Section 5.2 > 5.2.1" but NOT prepended to chunk text (contextual chunking deferred to Experiment 4)
- **[01.3-02] Remove rag_similarity_threshold:** 0.6 threshold applied to RRF scores (0.001-0.033 range) caused 100% document filtering
- **[01.3-02] Cross-encoder reranking funnel:** Retrieve 20 with bi-encoder, rerank with cross-encoder, keep top-3 for LLM. Improves precision@3 by 25-35%
- **[01.3-02] Measurement-only grading:** No filtering, logs reranker scores for observability. LLM-as-judge grading removed (slow, inconsistent)
- **[01.3-02] Lazy cross-encoder loading:** Thread-safe singleton defers 400MB model load until first use
- **[01.1-04] RAGAs evaluator uses Claude Sonnet:** LangchainLLMWrapper(ChatAnthropic) for RAGAs metrics evaluation
- **[01.1-04] Lazy LLM initialization for RAGAs:** ChatAnthropic not loaded until first evaluate_response() call
- **[01.1-04] RagasEvaluationService independent from ScoringService:** Layer 1 (benchmark scoring) and Layer 2 (RAG quality) are separate domain services with no coupling
- **[01.1-04] langchain-anthropic version constraint:** Used <1.0 constraint to get 0.3.22 (compatible with langchain 0.3.x), avoiding langchain-core version conflict
- **[01.1-01] 0-3 anchored scale for LLM judge dimensions:** Matches criteria-establishment.md Component 2 exactly. Discrete level descriptions with concrete CCoP-specific examples at each anchor. Not continuous 0-1 (no anchors) or 1-5 (wrong scale)
- **[01.1-01] Binary 0/3 for safety dimensions:** Over-specification and hallucination (B20, B21) are pass/fail — any fabrication = failure. No partial credit maintains safety threshold
- **[01.1-01] Chain-of-Thought in judge prompts:** "Think step-by-step" instruction increases transparency and justification coherence per LalaEval methodology
- **[01.1-01] Skip-and-flag error pattern:** judge_error=True with overall_score=0.0 and empty dimensions. No fallback conservative scores (hides failures). Errors flagged for manual review
- **[01.1-01] Dynamic dimension scoring:** List[DimensionScore] replaces fixed accuracy/completeness/alignment fields. Supports any number of dimensions per benchmark
- **[01.1-01] Rubric templates in docs/ not code:** evaluation-rubrics.md is single source of truth. Code references it, doesn't embed prompts. Enables non-engineer rubric iteration
- **[01.1-02] Configurable rubric file path:** LLMJudgeService constructor accepts optional rubric_path. Default resolves from project root via Path(__file__). Enables test isolation
- **[01.1-02] Rubric parsing by markdown structure:** Split on `## B{N}:` headers, extract code block after `### Judge Prompt Template`. Cached at init, never reloaded
- **[01.1-02] Score clamping with warning:** Out-of-range judge scores (below 0 or above 3) are clamped, not rejected. Warning logged for observability
- **[01.1-02] ScoringService dynamic dimension conversion:** Tier 3 scorer converts each DimensionScore to EvaluationMetric (score/3.0 normalization). Judge errors produce single judge_error metric with value 0.0
- **[01.1-05] Conditional DI via factory returning None:** staticmethod factory returns None when ragas_enabled=False. Use case checks for None before calling RAGAs
- **[01.1-05] RAGAs provider placement before use cases:** DeclarativeContainer processes attributes top-to-bottom; ragas_service must be defined before evaluate_model_use_case
- **[01.1-05] retrieved_contexts=None for all RAGAs calls:** Current IModelGateway returns ModelResponse without documents. Context metrics deferred until ModelGateway exposes GraphState
- **[01.1-03] Unified _score_llm_judge for all 15 benchmarks:** Single method routes B3, B7-B20 through LLMJudgeService. Benchmark-specific behavior in rubric templates, not code branching
- **[01.1-03] B3 migrated from hallucination detection to LLM judge:** B3 measures conditional reasoning quality, not hallucination presence. LLM judge with B3-specific rubric evaluates appropriate dimensions
- **[01.1-03] B21 retains rule-based hallucination detection:** B21 is binary pass/fail for fabrication detection, appropriate for rule-based scoring. Stays in 6 rule-based benchmarks
- **[02-01] evaluation_mode defaults to hybrid:** RAG-augmented evaluation is the primary use case
- **[02-01] rag-only excluded from evaluation modes:** Not meaningful for benchmark scoring (per CONTEXT.md)
- **[02-01] RAG metadata fields are optional:** retrieved_chunk_ids, chunk_count, evaluation_mode set to None when not RAG-augmented
- **[02-02] Graph-based evaluation:** Evaluation routes through full LangGraph RAG graph instead of direct model_gateway calls. hybrid mode gets RAG-augmented responses, llm-only mode gets fallback generation
- **[02-02] filtered_documents extraction:** Graph's filtered_documents extracted as retrieved_contexts and passed to RAGAs for context-aware metrics
- **[02-02] Qdrant unavailable raises error:** If Qdrant unavailable in hybrid mode, raise clear error instead of silent fallback. User must explicitly choose --mode llm-only
- **[02-02] Backward compatible fallback:** When rag_pipeline is None (not configured), fall back to existing model_gateway.generate_response() path
- **[02-03] RAG Context truncation at 5 IDs:** Display first 5 chunk IDs in panel, show total count if more
- **[02-03] llm-only suppresses RAG Context line:** No RAG Context shown for llm-only mode
- **[02-03] Mode in JSON filename:** mode-hybrid or mode-llm-only appended for easy run identification
- **[02-03] getattr for backward compat:** Older EvaluationResult objects without RAG fields handled gracefully
- **[02.1-01] Three quality groups:** Retrieval Quality (context_recall, context_precision), Model-RAG Grounding (faithfulness), Model Response Quality (llm_judge, answer_correctness, answer_relevancy). LLM Judge sits inside Model Response Quality, not separate
- **[02.1-01] Category-weighted overall aggregation:** Two-step: Step 1 computes category-level group averages, Step 2 computes weighted sum using EvaluationCategory weights. Prevents over-weighting categories with more benchmarks
- **[02.1-01] quality_categories as Dict[str, Any]:** Avoids Pydantic nested serialization complexity. Structure: {"overall": {"groups": [...]}, "by_benchmark": {"B1": {"groups": [...]}, ...}}
- **[02.1-01] RAGAs error handling:** evaluation_error=True counts as 0.0 in averages (simple math, no None propagation)
- **[02.1-01] llm-only mode N/A display:** Check rag_only_groups list (Retrieval Quality, Model-RAG Grounding) and mark metrics as None when evaluation_mode != "hybrid"
- **[02.1-02] Categorized CLI summary tables:** Replace old Evaluation Summary and Results by Benchmark tables with Overall Quality Summary (all 6 metrics grouped by category) and Per-Benchmark Quality Breakdown (all 6 metrics per benchmark with tree structure)
- **[02.1-02] 3-group per-test-case panels:** Model Response Quality (LLM Judge + answer metrics), Model-RAG Grounding (faithfulness), Retrieval Quality (context metrics). Color-coded headers for diagnostic clarity
- **[02.1-02] Metric display consistency:** QualityGroup.get_display_name() for all metric labels. RAGAs metrics with "RAGAs:" prefix, LLM Judge with "LLM Judge" label
- **[02.1-02] Color-coded metrics:** Green >= 0.7, yellow 0.4-0.7, red < 0.4, dim for N/A. Immediate visual feedback on quality thresholds
- **[02.1-03] Grouped ragas structure:** Per-test-case ragas metrics organized by diagnostic group (retrieval_quality, grounding, response_quality). Breaking change from flat metrics array (schema_version: 2)
- **[02.1-03] Self-describing JSON format:** group_definitions included in both ragas output and quality_categories metadata. Consumers don't need external docs to understand metric groupings
- **[02.1-03] JSON group key mapping:** "Retrieval Quality" -> "retrieval_quality", "Model-RAG Grounding" -> "grounding", "Model Response Quality" -> "response_quality" for JSON-friendly snake_case
- **[02.2-01] Three separate RAGAs evaluate() calls:** Base metrics, hallucination (faithfulness vs ground truth), and context metrics (faithfulness vs retrieved docs). Each uses different `retrieved_contexts` argument
- **[02.2-01] Hallucination via faithfulness trick:** Pass `[expected_response]` as `retrieved_contexts` to RAGAs faithfulness — checks if response claims are supported by ground truth. Always applicable (both modes)
- **[02.2-01] context_faithfulness hybrid-only:** Only computed when actual retrieved_contexts available. Non-RAG mode adds with applicable=False, score=0.0
- **[02.2-01] Overall score normalization fix:** `weighted_sum / total_weight` instead of just `weighted_sum`. Running only B3 (weight 0.25) now returns 0.44, not 0.11
- **[02.2-02] Information flow panel order:** Retrieval Quality → Model-RAG Grounding → Model Response Quality. Left-to-right follows RAG pipeline: retrieve → ground → respond
- **[02.2-02] Two-column Overall Quality Summary:** Quality groups as parent rows, individual metrics as indented children. Replaces 6-column N/A-heavy matrix
- **[02.2-02] Flat benchmark table with color-coded headers:** Abbreviated column headers (ctx_recall, ctx_faith, halluc, etc.), one row per benchmark, yellow/magenta/cyan for quality groups
- **[02.2-02] SC13(c) deferred:** Full prompt display (system prompt + user prompt with RAG context) requires data model changes to propagate llm_context from GraphState through RagResponse to EvaluationResult
- **[02.2-03] JSON schema_version 3:** context_faithfulness in grounding, hallucination in response_quality. Backward compat note for v2 files
- **[02.2-03] Query scoring with --no-score:** Only context_faithfulness and answer_relevancy shown (don't require ground truth). Errors suppressed unless verbose
- **[02.3-01] FactualCorrectness split:** answer_correctness replaced by FactualCorrectness(mode="precision") + FactualCorrectness(mode="recall"). Splits 75% factual F1 into separate precision/recall metrics
- **[02.3-01] Hallucination metric removed:** Redundant with factual_precision — both measure ground truth support. Cleaner metric set
- **[02.3-01] SemanticSimilarity diagnostic:** Display-only metric (not in composite score). Useful for understanding semantic overlap without polluting quality signal
- **[02.3-01] Multiplicative penalty formula:** ragas_score = base_score * factual_precision. Quadratic effect: 0.2 precision → 0.11 score, 0.9 precision → 0.75 score. Dramatic separation vs linear averaging
- **[02.3-01] Domain scoring property:** EvaluationResult.ragas_composite_score centralizes formula logic. Single source of truth, application layer is thin delegate
- **[02.3-01] Combined score removed:** Avg of benchmark + RAGAs dropped. Two scores measure different things at different scales — averaging was meaningless
- **[02.3-02] JSON schema version 4:** response_quality group with factual_precision, factual_recall, answer_relevancy, semantic_similarity. Backward compat note for v3 (answer_correctness, hallucination)
- **[02.3-02] Persistence delegates to domain for ragas_score:** JSON reads from result.ragas_composite_score property. No formula duplication in persistence layer
- **[02.4-01] Universal judge fields in JudgeEvaluation:** hallucination_detected, claims, unsupported_count, contradicted_count, reasoning_criteria_met added with backward-compatible defaults
- **[02.4-01] from_universal_judge factory with hallucination gate:** overall_score = 0.0 if hallucination detected, else reasoning_depth_score / 3.0
- **[02.4-01] Question-adaptive reasoning criteria:** clause_citations, conditional_analysis, actionable_steps evaluated for applicability (null for N/A) before scoring
- **[02.4-01] Final answer extraction:** extract_final_answer utility removes chain-of-thought reasoning before judge evaluation to prevent contamination
- **[02.4-01] Combined two-dimension prompt:** UNIVERSAL_JUDGE_PROMPT evaluates hallucination (claim-level verification) + reasoning depth in single Claude call
- **[02.4-01] Path preservation:** Existing rubric-based evaluate_response method unchanged, toggle between paths happens in ScoringService (Plan 03)
- **[02.4-03] judge_mode toggle in ScoringService:** judge_mode parameter (rubric or universal) routes B3, B7-B21 through appropriate judge path. Default "rubric" preserves existing behavior
- **[02.4-03] B21 universal routing:** B21 routes through universal judge hallucination detection when judge_mode="universal" (more sophisticated than regex), stays rule-based when "rubric"
- **[02.4-03] Simple average RAGAs formula:** ragas_score = (factual_recall + answer_relevancy + semantic_similarity) / 3. No multiplicative penalty — dimensions are independent
- **[02.4-03] factual_precision removed:** Dropped from RAGAs metrics, QualityGroup, and composite formula. Penalized valid alternative reasoning, duplicates LLM Judge hallucination check
- **[02.4-03] 7 total metrics:** Model Response Quality reduced from 5 to 4 metrics (factual_precision removed). Total metrics: 6 RAGAs + 1 LLM Judge = 7 (was 8)
- **[02.4-04] Shadow retrieval implementation:** In universal+llm-only mode, RAG pipeline queries for contexts using hybrid mode but only passes them to judge (not model). Enables hallucination detection without changing model input
- **[02.4-04] Judge metadata as JSON in description:** _score_universal_judge serializes judge data as JSON in EvaluationMetric.description. Application layer parses it in _result_to_dto. Avoids modifying domain entity structure
- **[02.4-04] CLI criteria transparency:** Shows clause_citations/conditional_analysis/actionable_steps as YES/NO/N/A with color coding. Hallucination shows binary YES/NO with claim counts (N claims: M unsupported, K contradicted)
- **[02.4-04] JSON schema v5 with judge_evaluation:** New top-level object in test results containing hallucination_detected, unsupported/contradicted counts, reasoning_depth_score, reasoning_criteria_met, claims, justification. Rubric mode gets judge_mode='rubric' without judge_evaluation object
- **[02.4-04] factual_precision display removal:** Dropped from flat benchmark table (7 columns now), RAGAs answer metrics display, and JSON response_quality group check. Already removed from RAGAs service in Plan 03
- **[03-01] *.json gitignore exception for schema file:** ground-truth/schema/test-case-v2.schema.json requires `git add -f` (*.json is project-wide gitignored). Future plans must use force-add for *.json files in schema/
- **[03-01] V2 schema version const "2.0":** JSON Schema `const` enforces exact version string on all test cases
- **[03-01] Business rules complement JSON Schema:** JSON Schema validates structure, validate.py business rules check: test_id prefix match, reasoning_chain for LLM-judge benchmarks, >=2 critical key_facts, expected_label for rule-based benchmarks
- **[03-02] 18 benchmark set finalized:** 21 v1 → 18 v2 via 3 merges (B8+B11, B14+B15, B9+B16), 3 absorptions (B17→B7, B19 removed, B20→B21), 3 new (B22 Waiver, B23 Multi-Regulator, B24 Incident Response)
- **[03-02] Waiver Reasoning as separate benchmark:** Section 11(7) waiver process is a top CIIO pain point; no v1 coverage; distinct enough from B3 conditional compliance to warrant its own benchmark
- **[03-02] Multi-Regulator Coordination new benchmark:** CCoP+MAS-TRM, CCoP+IM8 overlap is top-3 CIIO challenge; no existing benchmark captures regulatory navigation across frameworks
- **[03-04] evaluation_criteria allows empty dict for v2:** V2 test cases use universal judge (no per-test criteria). TestCase Rule 5 relaxed from "non-empty dict" to "must be dict". V1 behavior unchanged.
- **[03-04] _discover_benchmark_files checks both fields:** V2 JSONL files use `benchmark_id` not `benchmark_type`. Discovery now reads `data.get("benchmark_type") or data.get("benchmark_id")`.
- **[03-04] key_facts flattened at repository layer:** V2 key_facts are `list[dict]` with fact/source/tier. Extracted to `list[str]` in `_parse_v2_test_case` before passing to domain entity — scorers see no change.
- **[03-03] 52 Keep (44%), 36 Revise (31%), 30 Discard (25%):** Distribution within spec target; B3 and B7 are zero-discard benchmarks with direct migration path
- **[03-03] B14 (Remediation) full Discard:** 3/3 key_facts placeholders — critical benchmark requires complete regeneration from scratch
- **[03-03] B5 all Revise (not Discard):** All 7 cases have valuable clause references; practitioner reframing preserves generation effort
- **[03-03] B19 (Cross-Scenario) removed:** Meta-benchmark retired; 3/3 cases discard; consistency addressed at dataset analysis level
- **[03-03] B20→B21 full migration:** All 3 over-specification cases Keep to B21 — strong adversarial patterns reusable as-is

### Pending Todos

None yet.

### Roadmap Evolution

- Phase 1.1 inserted after Phase 1: MLflow Experiment Tracking (URGENT) — Record and compare results across all 5 model iterations (baseline LLM, naive RAG, optimized RAG, fine-tuned LLM, hybrid). Phase 2 now depends on 1.1.
- Phase 1.2 inserted after Phase 1: Local RAG Migration — Migrate from Databricks to Qdrant + local BGE. Phase 1.2 runs before Phase 1.1.
- Phase 1.3 inserted after Phase 1.2: RAG Quality — Clause-Level Chunking & Retrieval (URGENT) — Replace PyMuPDF4LLM with Docling, clause-aware chunking, cross-encoder reranking, fix RRF threshold. Discovered during Phase 1.2 human verification: 66 chunks too coarse, RRF threshold broken, zero citations resolving. Research completed first. Phase 1.3 runs before Phase 1.1.
- Phase 2.1 inserted after Phase 2: Evaluation Quality Categorization — Categorize 6 metrics into 3 diagnostic groups (retrieval quality, model grounding, response quality), aggregate RAGAs at benchmark/overall level, CLI summary table, JSON persistence. Discovered during Phase 2 manual verification: RAGAs metrics only shown per test case with no aggregation, no categorized view for diagnosis.
- Phase 2.2 inserted after Phase 2.1: RAGAs Hallucination Metric and Metric Renaming (URGENT) — Add ground-truth faithfulness metric for hallucination detection (works in both modes), rename faithfulness → context_faithfulness for clarity. Discovered during Phase 2.1 UAT: no metric checks model response claims against ground truth expected_response, and "faithfulness" name is ambiguous (faithful to what?).
- Phase 2.3 inserted after Phase 2.2: RAGAs Metric Split & Scoring Formula (URGENT) — Replace aggregated answer_correctness (masks hallucination behind semantic similarity) with separate FactualCorrectness(precision/recall), drop redundant hallucination metric, add SemanticSimilarity as diagnostic, implement multiplicative penalty formula. Discovered during Phase 2.3 triple-score UAT: LLM-only (hallucinating) and hybrid (grounded) responses scored nearly identically (0.87 vs 0.85 RAGAs) because answer_correctness blends 75% factual overlap F1 + 25% semantic similarity.
- Phase 2.4 inserted after Phase 2.3: LLM Judge Redesign and Metric Simplification (URGENT) — Replace per-benchmark rubric dimensions with two universal LLM Judge dimensions (reasoning depth + hallucination check against retrieved context), drop factual_precision from RAGAs scoring (penalizes valid reasoning). Discovered during Phase 2.3 UAT: factual_precision (0.27) penalizes model for introducing valid reasoning not in ground truth; LLM Judge and RAGAs metrics contradict each other; per-benchmark rubrics redundant with RAGAs factual_recall/relevancy/similarity.
- Phase 3 replaced: "Ground Truth Dataset Expansion" (1000+ cases, 21 benchmarks) → "Ground Truth V2 Overhaul" (~435 cases, 18 restructured benchmarks, unified v2 schema, Risk Manager focus). Driven by research on LLM eval ground truth quality practices and Singapore CIIO/CCoP compliance landscape. Spec: docs/superpowers/specs/2026-04-01-ground-truth-v2-design.md
- Phases 3.2 and 3.3 merged into single Phase 3.2 "Corpus and Ground Truth Correctness" (2026-04-21): shared pre-baseline-data-integrity intent, shared dependency (Phase 3.1), shared downstream consumer (Phase 4 re-baseline). Merged to one phase with ~7 sequential plans — sub-goal A (corpus/ingestion fix: bugs #9, #10) before sub-goal B (ground truth clause audit: bug #8). Saves phase-level overhead (one CONTEXT.md, one verification pass, one closeout). All 18 success criteria preserved verbatim across both sub-goals.
- **[03.1-01] RunId as frozen dataclass:** Matches EvaluationMetric pattern; immutable VO with `value` property rendering canonical string
- **[03.1-01] total_tokens auto-summed in ModelResponse:** Auto-sums prompt_tokens + completion_tokens when not explicitly provided; back-populates tokens_used for display back-compat
- **[03.1-01] retrieved_contexts_detailed alongside retrieved_contexts in RagResponse:** Text-only list for RAGAs, detailed dict list for traceability — both coexist on RagResponse
- **[03.1-01] perf_counter() wraps chain.invoke():** Captures wall-clock LLM latency accurately in generation/fallback nodes
- **[03.1-01] response_metadata['prompt_eval_count'] with usage_metadata fallback:** Handles both ChatOllama response_metadata style and LangChain usage_metadata style
- **[03.1-02] Per-run monthly directory layout:** src/results/evaluations/{yyyy-MM}/{run_id}-{model}.json — self-archives as runs accumulate, no explicit cleanup needed
- **[03.1-02] Sidecar contexts file pattern:** {run_id}-contexts.json alongside result JSON — keeps main files small while preserving full retrieval debuggability
- **[03.1-02] save_batch no-op in schema v6:** Retained as logged no-op rather than deleted to avoid breaking callers; per-run writes happen via save_evaluation_run
- **[03.1-02] Non-fatal query persistence:** CLI query wraps save_query_run in try/except; failure logs warning but never blocks user from seeing their answer
- **[03.1-02] container.config() for model_name in query CLI:** Settings singleton accessed via container provider; model_name is the configured Ollama model name
- **[03.1-03] rglob report discovery with name-first legacy filter:** `load_by_model` uses `rglob(f"*-{model_name}.json")` to discover per-run files across monthly subdirs, then filters `-contexts.json` sidecars by name *before* JSON parse so malformed sidecars never log spurious WARNINGs; pre-v6 files (missing `metadata.run_id` or `schema_version != 6`) logged + skipped
- **[03.1-03] _reconstruct_result pads question to satisfy TestCase invariant:** Persisted test_results only carry truncated question text; reconstruction for report summary pads with trailing spaces to ≥50 chars and sets a placeholder `expected_response`. Padding is reporting-only — persisted JSON untouched, summary math unaffected
- **[03.1-03] --verbose-io lazy sidecar load:** CLI opens `{run_id}-contexts.json` only when flag set AND file exists; missing sidecar is silent no-op. Prompts truncated at 600/1200 chars, contexts show first ~200 chars + citation_id/section/clause/score
- **[03.1-03] Schema v6 contract locked by 88 targeted tests:** `test_run_id.py` (27), `test_json_result_repository_v6.py` (19), `test_evaluate_model_metadata.py` v6 additions (4), `test_graph_state.py` I/O capture additions (13). Numeric sort test explicitly guards `B2<B3<B11` ordering in multi-benchmark scope
- **[03.1-03] Legacy migration hint surfaces only on empty v6 result:** `GenerateReportUseCase.get_summary` inspects flat dir for `{model}_results.json` only when `load_by_model` returns empty, emits one-line INFO guidance pointing to re-run; zero cost on happy path
  - **[03.2-01] CLAUSE_PATTERN extended with ## heading prefix:** Docling Classic pipeline emits 56 section/clause headings as `## X.Y heading` format; the original regex only matched bare-digit lines, causing 5.3/5.4/5.3.1/5.4.1 to be unrecognized as boundaries (bug #10 root cause)
  - **[03.2-01] Optional item-letter group in CLAUSE_PATTERN:** `(?:\([a-z]\))?` suffix added per plan; harmless in practice because Docling renders sub-items as `- (a)` list syntax, not as standalone headings
  - **[03.2-01] Merge rule removed unconditionally:** `<30-word merge_buffer` branch deleted entirely — short chunks acceptable with hybrid retrieval; any knob preserves bleed risk
  - **[03.2-01] Loop index i=1 always:** Pre-existing inverted condition (`i = 1 if parts[0].strip() else 0`) masked by real documents always having preamble; fixed to unconditional `i = 1`
  - **[03.2-02] Table chunks are ADDITIVE:** Parent clause chunk keeps full text; table chunks layer on top for filtered retrieval. No replacement — both coexist in the index
  - **[03.2-02] Table detection: >=3 consecutive pipe-lines:** Heading row + separator + at least 1 data row threshold; 2-line pipe blocks excluded
  - **[03.2-02] EXPECTED_CCOP_2_SECTIONS as module constant:** CCoP 2.0 TOC is a structural contract of the PDF, not a runtime parameter; defined once at the top of run_ingestion.py citing source PDF
  - **[03.2-02] TOC gate filters on type='clause' only:** Table chunks and preamble excluded from section evidence; gate positioned at Step 2.5 (after chunking, before upload)
  - **[03.2-03] SC #8 marked N/A (human-approved 2026-04-21):** 'individual accountability'/'individual authentication' phrases are absent from CCoP 2.0 source PDF (verified via 151,269-char Docling parse with 0 matches); their absence from the index is not a chunker defect. Real fix (sections 5.3/5.4 as discrete retrievable chunks) proven by SC #7 PASS
  - **[03.2-03] N/A annotation preserved in plan document:** Phrases kept in `must_haves.truths` + `<success_criteria>` with inline `# N/A — phrase not in source PDF` comments rather than deleted — traceability over silent removal
  - **[03.2-03] 490 chunks -> 477 Qdrant points (13 dedup):** Deterministic uuid5 over citation_id collapses preamble sub-chunks that share parent IDs; functional content preserved, all 12 expected sections retrievable
  - **[03.2-04] SC #9 marked N/A (human-approved 2026-04-21):** context_recall=0 on B3-001 is a retrieval-ranking problem, not a corpus gap; CCoP 2.0::5.3.1 is indexed and scoreable but lands at rank 5/20 post-cross-encoder (score -6.773), below the top-3 cutoff (-5.613). CONTEXT.md defers retriever/reranker tuning to Phase 4
  - **[03.2-04] Sub-goal A CLOSED:** Plans 01-04 collectively deliver the corpus fix — chunker regex (01), table chunks + TOC gate (02), clean re-ingestion (03), retrievability proof (04). Bugs #9 and #10 addressed at the corpus level
  - **[03.2-04] Retrieval funnel diagnostic as closure artifact:** Capturing rank at each stage (hybrid top_k -> cross-encoder rerank -> top-N cutoff) isolates corpus-vs-ranking failures; pattern reusable for any future retrieval metric regression
  - **[03.2-04] Phase 4 candidate fixes pre-identified:** (1) bump rerank_top_n 3->5 (cheapest), (2) domain-tuned cross-encoder (highest signal), (3) query rewriting for privileged/admin synonymy. Documented in b3-001-rerun-evidence.md so Phase 4 planning starts with a named option space

### Blockers/Concerns

- **Ground-truth test_id casing inconsistency (B04/B4, B05/B5, ...):** Pre-existing issue surfaced by the 03.2-04 re-eval logs. Ground-truth files use `B04-001` but benchmark codes are `B4`. Not addressed by Phase 3.2 (out of scope — audit covered citation correctness, not id canonicalization). Carry into Phase 4 acceptance testing.

## Session Continuity

Last session: 2026-04-22
Stopped at: Completed 03.2-07-PLAN.md — validator hard-fail + `ccop-eval validate-ground-truth` CLI + JSONL repo deprecated-skip + 4 CLI integration tests. Phase 3.2 verifier passed 18/18. Phase closed.
Resume file: N/A — Phase 3.2 complete. Next: Phase 4 (Re-Baseline & Re-Evaluate) — plan and execute the main baseline eval on v2 ground truth with corrected corpus.
