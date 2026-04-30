# Current Judge Rubric Summary (Phase 1 Baseline)

## Source files

- Rubric spec: `docs/phase-2/evaluation-rubrics.md`
- Judge code: `src/domain/services/llm_judge_service.py`
- Weight invariant: `src/domain/value_objects/evaluation_metric.py`

## Scoring scale

Discrete anchored 0-3 per dimension. Composite score normalized to 0.0-1.0:

```
composite = sum(d.score * d.weight for d in dimensions) / (3.0 * sum(d.weight for d in dimensions))
```

`EvaluationMetric` enforces value in `[0.0, 1.0]` and weight in `[0.0, 1.0]` (`__post_init__` in `evaluation_metric.py`).

## Universal rubric (5 dimensions, benchmark-agnostic)

Applied to all benchmarks via `_load_rubrics()` — one parsed `## UNIVERSAL RUBRIC` section mapped to every known B1-B24 ID.

| ID | Name | Weight | What it measures |
|----|------|--------|------------------|
| D1 | verdict_accuracy | 0.5 | Final verdict matches expected, including qualifications and secondary conclusions |
| D2 | justification_quality | 0.5 | Reasoning logically sound; every inference traceable to premises |
| D3 | factual_grounding | 1.0 | Citations exist in CCoP and correctly interpreted; forbidden-claim and hallucination-pattern hits reduce score |
| D4 | scope_appropriateness | 0.5 | No drift from question; no constraint violations |
| D5 | actionable_way_forward | 0.5 | Specific action + correct mechanism + feasibility-aware given constraints |

Total weight = 3.0. D3 has 2x the influence of any single other dimension — explicit hallucination penalty.

### Dimension anchors (verbatim from `evaluation-rubrics.md`)

**D1 verdict_accuracy**
- 0 — contradicts expected
- 1 — directionally right, misses key qualifications
- 2 — correct main verdict, misses secondary aspects
- 3 — fully matches including qualifications

**D2 justification_quality**
- 0 — absent or self-contradictory reasoning
- 1 — drifts from actual question
- 2 — sound reasoning, minor gaps in inferential links
- 3 — tight logical chain, every inference traceable

**D3 factual_grounding** (stepwise procedure in prompt)
- 0 — any FABRICATED citation
- 1 — MISATTRIBUTED citation without offsetting correct grounding
- 2 — all CORRECT or CORRECT + at most one IMPRECISE
- 3 — all CORRECT, every claim traceable
- Forbidden-claims / hallucination-pattern hits: each reduces score by one level, floor 0

**D4 scope_appropriateness**
- 0 — constraint violation (proposes infeasible action contradicted by scenario)
- 1 — verbose with tangential sections
- 2 — mostly on-topic, minor drift
- 3 — focused, no drift, no constraint violation

**D5 actionable_way_forward**
- 0 — (a) no next steps OR (b) steps contradict constraints
- 1 — vague direction only
- 2 — specific action, lacks detail or feasibility awareness
- 3 — specific action + mechanism + feasibility-aware

## Ground-truth artifacts injected into judge prompt

`LLMJudgeService._build_judge_prompt` substitutes these placeholders:

| Placeholder | Source | What it carries | Dimension(s) served |
|-------------|--------|-----------------|---------------------|
| `{question}` | `test_case.question` | Question under test | All |
| `{response}` | `response.content` | Model output to judge | All |
| `{expected_response}` | `test_case.expected_response` | Free-text reference answer | D1, D2 |
| `{key_facts}` | `test_case.metadata.key_facts_structured` | Tier-grouped (CRITICAL / IMPORTANT) fact list with source tags | D1, D2, D3 |
| `{clause_reference}` | `test_case.clause_reference` (string) | Expected clause IDs | D3 |
| `{expected_citations_text}` | `_build_expected_citations_block(clause_reference)` | Actual clause text fetched from Qdrant cache for each expected ID | D3 |
| `{citation_verifications}` | `_build_citation_verification_block(response.content)` | Programmatic EXISTS / FABRICATED per citation extracted from response + actual clause text | D3 |
| `{forbidden_claims}` | `test_case.forbidden_claims` | Must-not-appear assertions | D3 |
| `{hallucination_patterns}` | `test_case.metadata.hallucination_patterns` | Regex patterns flagging fabrication | D3 |
| `{related_scenarios}` | `test_case.metadata.related_scenarios` | Parallel scenarios for consistency (B19 only) | D4 |

## Universal judge (alternate path: `universal_evaluate_response`)

Separate prompt in `UNIVERSAL_JUDGE_PROMPT` class constant. Two-part scoring:

1. **Hallucination check** — extracts atomic claims from response, classifies each SUPPORTED / UNSUPPORTED / CONTRADICTED against retrieved contexts. `hallucination_detected = true` if ANY claim is UNSUPPORTED or CONTRADICTED → `overall_score = 0.0` (binary gate).
2. **Reasoning depth (3 question-adaptive criteria)** — `clause_citations`, `conditional_analysis`, `actionable_steps`. Each `true`/`false`/`null` (N/A). Score = count of True values, 0-3.

This path is an alternate surface (currently used only when `retrieved_contexts` passed). The 5-dim universal rubric is the primary production path.

## Citation verification infrastructure

- `_load_inventory_ids()` loads the clause-ID whitelist from `src/rag/ingestion/fixtures/clause_inventory.json` (deterministic EXISTS / FABRICATED check).
- `_load_clause_text_cache()` pre-loads CCoP 2.0 clause text from Qdrant for misattribution detection. Sub-letter fallback: `5.3.1(c)` falls back to parent `5.3.1` text. Cache keyed on `clause` or stripped `citation_id`.
- `_extract_citations()` uses two regex patterns (lead-in + bare 3-part) to avoid matching version strings like `CCoP 2.0`.
- Verification is lexical — judge still has to decide whether the cited clause actually supports the claim made.

## Judge execution

- `_call_claude_agent()` shells out via `subprocess.run(["claude", "chat", "--model", self._model], input=prompt, ...)` with timeout from settings.
- Default model: `settings.llm_judge_model` (currently `"sonnet"`).
- Single pass, no N-sample averaging, no seed pinning, no position-swap.
- Response parsed from JSON; scores clamped to 0-3.

## Error handling

Skip-and-flag pattern: on parse failure or subprocess error, returns `JudgeEvaluation.error()` with `judge_error=True`, `overall_score=0.0`, `confidence=0.0`. No fallback conservative scores.

## Known failure modes (from commit history + CLAUDE.md observations)

| Failure mode | Source | Evidence |
|--------------|--------|----------|
| Single-sample noise swamps treatment effect | temperature=0.7 default, N=1 | No seed pinning, no averaging |
| Binary verdict collapses nuance | B03/B02 labels are compliant/non-compliant/partial; D1 anchors collapse 1 and 2 at mid-score | `evaluation-rubrics.md` L41-47 |
| Citation verification is existence-only + one-shot text compare | No retrieval of multiple candidate chunks, no NLI between claim and clause text | `_build_citation_verification_block` signature |
| D5 weakly anchored | Anchors reference "specific action + mechanism" but ground-truth `way_forward` shape is inconsistent across benchmarks | `evaluation-rubrics.md` L88-96 |
| Hallucination detection is coarse for intra-clause fabrication | Inventory check catches fake clause IDs; fabricated facts inside real clauses require the judge to notice via `{expected_citations_text}` | `_build_citation_verification_block` only flags FABRICATED at ID level |
| No safety dimension | Harmful advice ("disable logging to avoid audit failure") not explicitly scored | Rubric has no D6 |
| No judge self-consistency / N-sample | Single subprocess call per test case | `evaluate_response` body |
| No position bias control | Judge sees response in fixed position; no swap pass | Not implemented |
| Free-text `expected_response` requires judge to implicitly decompose | No atomic-fact field; D2/D3 rely on judge's ability to pick out load-bearing claims | Prompt injection shape |
| Sub-letter citation fallback silently widens match scope | `5.3.1(c)` → `5.3.1` parent in `_resolve_clause_text` when the sub-letter lacks its own chunk | Code comment acknowledges limited verification |

## Commit-history context (recent rubric changes)

- `af46faa feat(llm-judge): close ground-truth gaps in judge prompt` — added explicit "SCORE STRICTLY FROM GROUND TRUTH" instruction.
- `b75f28e feat(llm-judge): anchor judge to ground truth; close blind spots` — introduced `{expected_citations_text}` block.
- `dbdd54c feat(llm-judge): benchmark-agnostic 5-dim universal rubric` — consolidated per-benchmark rubrics to one universal rubric.

## Summary

The current judge is a **single-pass, anchored-0-3, 5-dimension rubric** with a **2x-weighted factual grounding dimension** and a **lexical clause-inventory pre-verification** step. Ground-truth injection is rich (expected response + tiered key facts + expected clause text + forbidden claims + hallucination patterns), but the rubric itself makes no use of per-case anchors and has no calibration, multi-sample, or position-bias controls. D1's 4-point scale is effectively 2-point for binary-verdict benchmarks. D5 anchors rely on structure (`way_forward`) that is inconsistent in ground truth. No safety dimension. No inter-judge agreement measurement.
