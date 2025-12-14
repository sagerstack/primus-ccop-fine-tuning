# Implementation Plan: Phase 2 Scoring Methodology Alignment (App Fixes)

## 1. Objective

Align the evaluation app’s scoring implementation with the **Phase 2 scoring methodology** by correcting metric definitions and benchmark handling while preserving:
- the existing **weighted average aggregation**,
- the **phase-aware threshold logic** (baseline = 0.15),
- the current evaluation pipeline structure.

Success means B1–B21 scoring uses **benchmark-appropriate accuracy and completeness definitions**, and introduces **regulatory grounding checks** where required.

---

## 2. Scope of Changes

### In scope
- Replace **lexical (Jaccard) accuracy** for applicable benchmarks (starting with B1) with **label-based** or **semantic** accuracy.
- Ensure completeness is **key-fact recall** (not sentence overlap).
- Add **grounding safety checks** (hallucination / over-specification) to relevant benchmarks.
- Keep Jaccard as an **optional diagnostic metric**, not the primary “accuracy”.

### Out of scope (Phase 2)
- RAG integration
- Clause citation accuracy as a primary metric
- Performance benchmarking (latency/memory) as a scored category
- Prompt-injection / jailbreak testing

---

## 3. Current Gaps to Fix (Tracking List)

1. **B1 Accuracy uses Jaccard (lexical overlap)**  
   - Needs label-based or semantic scoring.

2. **Completeness may be sentence/keyword-based instead of key-fact recall**  
   - Must use `key_facts[]` coverage.

3. **Grounding / hallucination metric not included in B1 scoring**  
   - Add as a safety metric (recommended).

4. **Tier/category alignment not explicit in code**  
   - Introduce a benchmark-to-scoring-strategy mapping.

---

## 4. Proposed Design

### 4.1 Metric Model (No Breaking Changes)

Continue using `EvaluationMetric(name, value, weight, description)`.

Add new metric factory methods (if not present):
- `label_accuracy_metric(value)`
- `semantic_accuracy_metric(value)`
- `grounding_metric(value)`
- `diagnostic_jaccard_metric(value)` *(optional, weight=0 or excluded from overall)*

### 4.2 Benchmark Scoring Strategy Mapping

Introduce a centralized mapping (single source of truth):

- **Classification-style benchmarks** (e.g., applicability / compliance):  
  `Accuracy = label_match`
- **Interpretation & reasoning benchmarks**:  
  `Accuracy = semantic_similarity`
- **All benchmarks**:  
  `Completeness = key_fact_recall` (if key facts are provided)
- **Safety-sensitive benchmarks**:  
  include `Grounding = unsupported_claim_check` and/or `OverSpecification`

This avoids ad-hoc per-benchmark logic and makes future additions consistent.

---

## 5. Implementation Steps (Concrete Tasks)

### Step 1 — Add required fields to test-case schema (if missing)
**Goal:** support key-fact recall and label scoring.

- Add/confirm optional fields per test case:
  - `expected_label` (string, for classification benchmarks)
  - `key_facts` (list of strings, minimum 3 per case recommended)
  - `forbidden_claims` (list of strings or patterns; optional)
  - `allowed_terms` (optional, for SG terminology checks)

**Deliverable:** updated JSON/YAML schema + sample test case.

---

### Step 2 — Implement label-based accuracy scoring
**Goal:** replace Jaccard for B1 (and any other classification benchmarks).

Add function in `ScoringService`:
- `_calculate_label_accuracy(expected_label, response_text) -> float`

Implementation guidance:
- Extract predicted label from response using robust parsing:
  - explicit keywords (e.g., “Applies/Does not apply”, “Compliant/Non-compliant”)
  - fallback: simple classifier rules
- Map outcomes to:
  - Exact = 1.0
  - Partial/unclear = 0.7
  - Incorrect = 0.0

**Deliverable:** unit tests for label extraction and scoring.

---

### Step 3 — Implement semantic accuracy scoring (embedding-based)
**Goal:** enable semantic equivalence for reasoning benchmarks.

Add function in `ScoringService`:
- `_calculate_semantic_similarity(expected_answer, response_text) -> float`

Implementation options:
- If offline constraints exist:
  - use local embedding model (e.g., sentence-transformers via local runtime)
  - cache embeddings for expected answers
- Normalize similarity to [0, 1] range.

**Deliverable:** deterministic semantic score computation + caching.

---

### Step 4 — Replace completeness logic with key-fact recall
**Goal:** ensure completeness reflects required content, not verbosity.

Update `_calculate_completeness(test_case, response)` to:
- If `key_facts` exists and non-empty:
  - completeness = covered / total
- Else:
  - fallback to existing heuristic (for backward compatibility), but log warning

Implement helper:
- `fact_is_covered(fact, response_text) -> bool`
  - token normalization, synonym handling where feasible
  - optional regex support for structured facts

**Deliverable:** completeness scoring tests using controlled examples.

---

### Step 5 — Add regulatory grounding metric (hallucination/over-specification)
**Goal:** add safety checks without requiring clause citation accuracy.

Implement:
- `_calculate_grounding_score(test_case, response_text) -> float`

Suggested approach:
- Extract “regulatory assertions” from response:
  - clause numbers, “shall/must/required”, defined terms
- Penalize if response contains:
  - items matching `forbidden_claims`
  - fabricated obligations not supported by expected answer constraints
- Do **not** penalize hedging language (“may”, “depends”).

Scoring suggestion:
- 0 violations → 1.0
- 1–2 violations → 0.7
- 3+ violations → 0.0

**Deliverable:** grounding metric + regression tests.

---

### Step 6 — Update benchmark scoring functions (start with B1)
**Goal:** align B1 with Phase 2 scoring.

Update `_score_b1_interpretation`:
- Replace `_calculate_basic_accuracy` with label or semantic (depending on B1 definition)
- Ensure completeness uses key facts
- Add grounding metric (recommended)

Example target metric set for B1:
- `accuracy` (label) weight 1.0
- `completeness` (key facts) weight 0.8
- `grounding` weight 1.0
- optional `diagnostic_jaccard` weight 0.0

**Deliverable:** updated B1 scoring output + worked example.

---

### Step 7 — Apply the strategy mapping across B1–B21
**Goal:** avoid inconsistencies between benchmarks.

Implement a dispatch layer:
- `score_test_case(test_case, response) -> metrics[]`
- Determine strategy by benchmark ID or benchmark category metadata.

**Deliverable:** consistent scoring across benchmark families.

---

### Step 8 — Ensure reporting supports Phase 2 interpretation
**Goal:** prevent misinterpretation.

- Report both:
  - `overall_score`
  - metric breakdown
- Include `phase_threshold_used`
- Add warnings when:
  - semantic scoring is unavailable (fallback used)
  - key_facts missing (completeness fallback used)

**Deliverable:** updated JSON output schema + example result.

---

## 6. Validation Plan

### Unit Tests
- Label extraction correctness (B1/B2 style)
- Semantic similarity stable outputs (with fixed seed/model)
- Key-fact coverage detection
- Grounding violation detection

### Regression Tests
- Re-run a small fixed subset (10–20 cases) and compare:
  - old vs new metric breakdown
  - ensure overall pipeline still executes
  - ensure baseline pass threshold logic is unchanged

### Acceptance Criteria
- B1 no longer uses Jaccard as primary accuracy.
- Completeness uses key facts when present.
- Grounding metric included at least for applicability + interpretation benchmarks.
- Phase thresholds remain:
  - baseline 0.15
  - finetuned 0.50
  - deployment 0.85

---

## 7. Rollout Plan

1. Implement metric functions + schema updates
2. Update B1 scoring and validate outputs
3. Expand mapping to remaining benchmarks incrementally
4. Run regression suite and freeze results format
5. Update documentation (`scoring-methodology-phase2.md`) to reference implemented behavior

---

## 8. Risks and Mitigations

- **Semantic scoring dependency not available offline**  
  Mitigation: implement label scoring for classification; fallback to rubric/manual for reasoning until embeddings are available; log “semantic unavailable”.

- **Key facts missing from existing dataset**  
  Mitigation: allow fallback completeness with warning; progressively backfill key facts.

- **Grounding detection too strict**  
  Mitigation: start with `forbidden_claims`-based violations; expand gradually; avoid penalizing hedging.

---

## 9. Deliverables Checklist

- [ ] Updated test-case schema with `expected_label`, `key_facts`, `forbidden_claims`
- [ ] Label-based accuracy metric implementation + tests
- [ ] Semantic similarity metric implementation + caching (or documented fallback)
- [ ] Key-fact completeness implementation + tests
- [ ] Grounding metric implementation + tests
- [ ] Updated B1 scoring function
- [ ] Benchmark strategy mapping and dispatch layer
- [ ] Updated evaluation output schema + example JSON
- [ ] Regression run summary (baseline subset)
