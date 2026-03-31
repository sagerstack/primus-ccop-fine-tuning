# Ground Truth V2: Complete Overhaul Design Spec

## Summary

Redesign the CCoP 2.0 evaluation ground truth from scratch: unified schema, restructured benchmarks, research-informed test cases grounded in real CIIO practices, targeting Risk Managers in CII organizations. Single-phase effort producing ~435 test cases across ~18 benchmarks.

## Context

### Current State
- 118 test cases across 21 benchmarks (3-8 per benchmark)
- Inconsistent schema across benchmark types (different optional fields per category)
- `key_facts` quality varies — some benchmarks have `"Unable to extract key facts automatically"`
- `evaluation_criteria` keys not standardized across files
- Questions are mostly well-crafted but lack sector-specific grounding and practitioner framing
- Expert validation still pending on v1

### Evaluation Framework (Post Phase 02.x)
- LLM judge uses universal 2-dimension system: reasoning depth (0-3 anchored) + hallucination detection (binary gate)
- Rule-based scorers (B1, B2, B4-B6, B21) consume: `expected_label`, `key_facts`, `forbidden_claims`, metadata fields
- LLM judge (B3, B7-B20) consumes: `question`, `expected_response`, `key_facts`, retrieved context
- RAGAs composite: `(factual_recall + answer_relevancy + semantic_similarity) / 3`
- Quality groups: Retrieval Quality, Model-RAG Grounding, Model Response Quality

### Research Inputs
- `artifacts/research/2026-04-01-llm-eval-ground-truth-quality-deep-dive.md`
- `artifacts/research/2026-04-01-singapore-ciio-ccop-practices-deep-dive.md`

---

## 1. V2 Test Case Schema

### Design Principles

1. **Separated concerns** — `ground_truth` (what's correct), `fail_conditions` (what's wrong), `metadata` (how to slice) are distinct top-level objects
2. **Tiered key_facts** — critical/important/supporting with source tracing enables weighted scoring and quality auditing
3. **Reasoning chain** — ordered steps for LLM judge to assess logical coherence
4. **Fail conditions override scoring** — bright-line failures bypass positive scores
5. **Acceptable variations** — reduce false negatives from legitimate alternative framings
6. **Scenario context in input** — sector and role make questions filterable and stratifiable
7. **No per-test-case rubrics** — the universal LLM judge handles scoring dimensions; embedding rubrics per test case would require scoring infrastructure changes (out of scope)

### Schema Definition

```json
{
  "test_id": "B3-015",
  "version": "2.0",
  "benchmark_id": "B3",

  "input": {
    "question": "Your organization uses shared admin accounts with session logging for CII SCADA systems because the legacy HMIs don't support individual authentication. The CISO argues this satisfies CCoP access control requirements through compensating controls. Does this approach comply with CCoP 2.0?",
    "scenario_sector": "energy",
    "scenario_role": "risk_manager"
  },

  "ground_truth": {
    "expected_label": "non-compliant",
    "expected_response": "Structured reference answer, 100-250 words...",
    "key_facts": [
      {
        "fact": "Clause 5.3.1(c) requires individual accountability for privileged access to CII systems",
        "source": "CCoP 2.0 Section 5.3.1(c)",
        "tier": "critical"
      },
      {
        "fact": "Shared admin accounts prevent individual attribution of actions, violating accountability requirements",
        "source": "Regulatory interpretation",
        "tier": "critical"
      },
      {
        "fact": "Session logging is a detective control that cannot replace the preventive requirement of individual authentication",
        "source": "CCoP 2.0 defense-in-depth principle",
        "tier": "important"
      },
      {
        "fact": "A waiver under Section 11(7) should be pursued if legacy HMIs genuinely cannot support individual accounts",
        "source": "Cybersecurity Act Section 11(7)",
        "tier": "supporting"
      }
    ],
    "reasoning_chain": [
      "Identify that shared admin accounts on CII systems involve privileged access",
      "Recall that CCoP 2.0 requires individual accountability for privileged access",
      "Evaluate whether compensating controls (session logging) satisfy the accountability mandate",
      "Conclude that detective controls cannot substitute for the preventive requirement",
      "Recommend the waiver mechanism for genuinely infeasible requirements"
    ],
    "acceptable_variations": [
      "May recommend PAM tooling as an alternative to individual HMI accounts",
      "May reference the OT addendum for legacy system considerations",
      "May suggest jumpbox architecture as a compensating control pathway"
    ]
  },

  "fail_conditions": {
    "forbidden_claims": [
      "Shared admin accounts with logging satisfy CCoP access control requirements",
      "Compensating controls can always replace mandated controls"
    ],
    "hallucination_patterns": [
      "Citing non-existent CCoP clauses",
      "Attributing requirements from other frameworks (e.g., ISO 27001) as CCoP mandates"
    ]
  },

  "metadata": {
    "section": "Section 5: Protection",
    "clause_reference": ["5.3.1"],
    "domain": "OT",
    "difficulty": "high",
    "scenario_type": "compensating_controls_insufficient",
    "related_sections": ["5.2.1", "OT Addendum"],
    "test_category": "negative",
    "created_date": "2026-04-01",
    "reviewer": null
  }
}
```

### Field Reference

#### Required Fields (all benchmarks)

| Field | Type | Description |
|-------|------|-------------|
| `test_id` | string | Format: `B{N}-{NNN}` (e.g., B3-015) |
| `version` | string | Always `"2.0"` |
| `benchmark_id` | string | Benchmark identifier (e.g., B3) |
| `input.question` | string | Minimum 50 characters, scenario-grounded |
| `input.scenario_sector` | string | One of: energy, water, banking, healthcare, aviation, transport, maritime, telecoms, government, media, security, cross-sector |
| `input.scenario_role` | string | `"risk_manager"` or `"employee"` |
| `ground_truth.expected_response` | string | 100-250 words, structured reference answer |
| `ground_truth.key_facts` | array | Minimum 2 objects for reasoning benchmarks |
| `ground_truth.key_facts[].fact` | string | Atomic, independently verifiable claim |
| `ground_truth.key_facts[].source` | string | CCoP clause, Act section, or "Regulatory interpretation" |
| `ground_truth.key_facts[].tier` | string | `"critical"`, `"important"`, or `"supporting"` |
| `fail_conditions.forbidden_claims` | array | Claims that indicate hallucination or dangerous advice |
| `fail_conditions.hallucination_patterns` | array | Categories of fabrication to detect |
| `metadata.section` | string | CCoP 2.0 section reference |
| `metadata.clause_reference` | array | Specific clause numbers |
| `metadata.domain` | string | `"IT"`, `"OT"`, or `"IT/OT"` |
| `metadata.difficulty` | string | `"low"`, `"medium"`, or `"high"` |
| `metadata.test_category` | string | `"positive"`, `"negative"`, `"edge_case"`, or `"adversarial"` |
| `metadata.created_date` | string | ISO date |
| `metadata.reviewer` | string or null | Reviewer name after validation |

#### Conditional Fields

| Field | When Required | Description |
|-------|---------------|-------------|
| `ground_truth.expected_label` | Rule-based benchmarks (B1, B2, B4, B21). Optional for LLM-judge benchmarks where a classification verdict exists (e.g., compliant/non-compliant) — included for context, not required for scoring | Classification label |
| `ground_truth.reasoning_chain` | LLM-judge benchmarks (B3, B5-B18+) | Ordered reasoning steps |
| `ground_truth.acceptable_variations` | LLM-judge benchmarks | Valid alternative framings |
| `metadata.scenario_type` | Recommended for all | Taxonomy of scenario pattern |
| `metadata.related_sections` | When cross-references exist | Related CCoP sections |

### Backward Compatibility Mapping (V1 to V2)

| V1 Field | V2 Field | Migration |
|----------|----------|-----------|
| `question` | `input.question` | Direct move |
| `expected_response` | `ground_truth.expected_response` | Direct move |
| `expected_label` | `ground_truth.expected_label` | Direct move |
| `key_facts` (string list) | `ground_truth.key_facts` (object list) | Requires enrichment: add source, tier |
| `reasoning_dimensions` | Removed | Replaced by `reasoning_chain` |
| `safety_checks` | `fail_conditions` | Split into `forbidden_claims` + `hallucination_patterns` |
| `evaluation_criteria` | Removed | Absorbed into universal LLM judge |
| `violations` | `fail_conditions.forbidden_claims` | Restructured |
| `metadata` | `metadata` | Extended with new fields |

### Design Note: LLM Judge Scoring Scale

The 0-3 scoring scale used by the LLM judge lives in the judge's prompt, not in the ground truth schema. The v2 schema is scale-agnostic — `key_facts`, `reasoning_chain`, `fail_conditions`, and `acceptable_variations` are reference material consumed regardless of scoring scale.

If more scoring granularity is needed in the future, the research recommends adding more evaluation dimensions (e.g., separate scores for factual accuracy, logical coherence, completeness) rather than expanding the per-dimension scale. LLM-judge alignment with human evaluators degrades sharply as scale granularity increases (76% accuracy at binary, 57% at 5-way classification). The current 0-3 scale (4 levels) sits in the optimal range.

This is a future scoring infrastructure decision, not a ground truth concern.

---

## 2. Benchmark Audit

### Audit Criteria

Each benchmark evaluated against:

| Criterion | Question |
|-----------|----------|
| **CIIO Relevance** | Does this test something a Risk Manager in a CII org actually needs? |
| **Distinctiveness** | Does this measure something no other benchmark covers? |
| **Scorer Alignment** | Does the current scoring infrastructure effectively evaluate this? |
| **Question Feasibility** | Can we write 20+ high-quality, scenario-grounded questions? |
| **Evaluation Clarity** | Is there a clear distinction between a good and bad response? |

### Benchmark Decisions

#### Keep (core Risk Manager needs)

| Benchmark | Rationale |
|-----------|-----------|
| B1 — CCoP Applicability & Scope | Foundation. Adding CCoP 1.0 evolution, IM8 context, ESCI/STCC/FDI awareness |
| B3 — Conditional Compliance Reasoning | Core — "is this compliant IF we have compensating controls?" |
| B7 — Gap Identification Quality | Directly maps to audit prep and gap analysis |
| B9 — Risk Identification Accuracy | Core risk management function |
| B10 — Risk Justification Coherence | Risk Managers articulate risk rationale to boards |
| B11 — Risk Severity Assessment | Prioritization decisions for remediation |
| B14 — Remediation Recommendation Quality | Actionable guidance is the primary use case |
| B21 — Hallucination Rate | Safety-critical, non-negotiable |

#### Keep but Refocus

| Benchmark | Current Focus | Proposed Refocus |
|-----------|---------------|-----------------|
| B2 — Compliance Classification | Generic classification | Sector-specific with IT/OT nuance |
| B4 — IT/OT Classification | Simple label check | Scenario-based IT/OT boundary reasoning across sectors |
| B5 — Control Requirement Comprehension | Abstract comprehension | Practical "what does this mean for my org" framing |
| B6 — Control Intent Understanding | Intent in isolation | Intent applied to real CIIO scenarios |
| B12 — Audit Perspective Alignment | CSA auditor viewpoint | Dual: auditor viewpoint AND Risk Manager audit prep |
| B13 — Evidence Expectation Awareness | What auditors want | What Risk Managers should prepare |
| B18 — Responsibility Attribution (SG) | CIIO/CSA attribution | Extended to BoD, CISO, Risk Manager, vendor responsibilities |

#### Merge

| From | Into | Rationale |
|------|------|-----------|
| B8 (Gap Prioritisation) + B11 (Risk Severity) | **B8 — Risk-Based Prioritization** | Both assess prioritization/severity, natural combination |
| B15 (Remediation Feasibility) + B14 (Remediation Quality) | **B14 — Remediation Quality** | Feasibility is a sub-dimension of recommendation quality |
| B16 (Residual Risk Awareness) + B9 (Risk Identification) | **B9 — Risk Identification** | Residual risk is an extension of risk identification |

#### Remove / Absorb

| Benchmark | Absorbed Into | Rationale |
|-----------|---------------|-----------|
| B17 (Policy vs Practice) | B7 (Gap Identification) | Thin concept, tested as a scenario type within gap analysis |
| B19 (Cross-Scenario Consistency) | Quality check across all benchmarks | Meta-benchmark, not a compliance capability |
| B20 (Over-Specification Avoidance) | B21 (Hallucination Rate) | Over-specification is a form of fabricating requirements |

#### New Benchmarks

| Benchmark | Rationale | Source |
|-----------|-----------|--------|
| **Waiver & Exception Reasoning** | Risk Managers frequently navigate the waiver process (Section 11(7)). No current benchmark tests this | CIIO research — waiver process is a key pain point |
| **Multi-Regulator Coordination** | CIIOs face overlapping requirements (CCoP + MAS-TRM, CCoP + IM8). No benchmark tests regulatory overlap navigation | CIIO research — top-3 challenge |
| **Incident Response Guidance** | 2-hour notification, multi-regulator reporting (CSA + MAS + PDPC), crisis communication. High-stakes Risk Manager scenario | CIIO research — incident response coordination |

### Final Benchmark Set (~18 benchmarks)

| ID | Name | Scoring Path | Notes |
|----|------|-------------|-------|
| B1 | CCoP Applicability & Scope | Rule-based | Extended with CCoP 1.0, IM8, ESCI/FDI |
| B2 | Compliance Classification | Rule-based | Sector-specific refocus |
| B3 | Conditional Compliance Reasoning | LLM-judge | — |
| B4 | IT/OT Classification & Boundary | Rule-based | Refocused to boundary reasoning |
| B5 | Control Requirement Comprehension | LLM-judge | Practical refocus |
| B6 | Control Intent Understanding | LLM-judge | Scenario-applied refocus |
| B7 | Gap Identification Quality | LLM-judge | Absorbs B17 scenarios |
| B8 | Risk-Based Prioritization | LLM-judge | Merged B8+B11 |
| B9 | Risk Identification & Residual Risk | LLM-judge | Merged B9+B16 |
| B10 | Risk Justification Coherence | LLM-judge | — |
| B12 | Audit Perspective Alignment | LLM-judge | Dual perspective refocus |
| B13 | Evidence Expectation Awareness | LLM-judge | Risk Manager prep refocus |
| B14 | Remediation Quality & Feasibility | LLM-judge | Merged B14+B15 |
| B18 | Responsibility Attribution (SG) | LLM-judge | Extended role hierarchy |
| B21 | Hallucination & Over-Specification | Rule-based + LLM-judge | Absorbs B20 |
| B22 | Waiver & Exception Reasoning | LLM-judge | New |
| B23 | Multi-Regulator Coordination | LLM-judge | New |
| B24 | Incident Response Guidance | LLM-judge | New |

---

## 3. Test Case Generation Strategy

### Target Audience

**Dual-audience questions:**
- An employee in a CII organization asking their Risk Manager
- A Risk Manager consulting the tool for their own compliance work

Every question must be practitioner-grounded and scenario-specific.

### Question Design Principles

| Principle | Test |
|-----------|------|
| **Practitioner-grounded** | Would a Risk Manager or someone asking their Risk Manager actually ask this? |
| **Scenario-specific** | References a concrete organizational situation, not abstract/definitional |
| **Sector-aware** | Grounded in a realistic sector context |
| **Dual-audience** | Works for both employee-to-RM and RM-consulting-tool |
| **Unambiguous verdict** | Ground truth has a defensible correct answer |
| **Single focus** | Tests one compliance reasoning capability |

### Question Sourcing

1. **CIIO Research Scenarios** — 15 sector-specific scenarios and 33 Risk Manager questions from research, adapted into properly structured test cases
2. **CCoP 2.0 Clause Walk** — systematic coverage analysis across all 220 clauses, identifying gaps
3. **Current Ground Truth Critique** — review all 118 existing test cases (keep/revise/discard)

### Quantity Allocation

Minimum 20 per benchmark. Additional allocation based on reasoning complexity, CCoP section coverage, IT/OT variance, and difficulty distribution needs.

| Benchmark | Target | Rationale |
|-----------|--------|-----------|
| B1 — Applicability & Scope | 25 | CCoP 1.0, IM8, ESCI/FDI context additions |
| B2 — Compliance Classification | 25 | Sector variance |
| B3 — Conditional Compliance | 30 | Many conditional reasoning patterns |
| B4 — IT/OT Classification | 25 | 11 sectors x IT/OT/hybrid profiles |
| B5 — Control Requirement | 25 | Spans many CCoP sections |
| B6 — Control Intent | 20 | — |
| B7 — Gap Identification | 30 | Complex reasoning, many failure modes |
| B8 — Risk-Based Prioritization | 25 | Merged, severity + prioritization |
| B9 — Risk Identification | 25 | Merged, includes residual risk |
| B10 — Risk Justification | 20 | — |
| B12 — Audit Perspective | 20 | — |
| B13 — Evidence Expectation | 20 | — |
| B14 — Remediation Quality | 30 | Merged, includes feasibility |
| B18 — Responsibility Attribution | 25 | Extended role hierarchy |
| B21 — Hallucination | 25 | Adversarial variety |
| B22 — Waiver Reasoning | 20 | New |
| B23 — Multi-Regulator | 20 | New |
| B24 — Incident Response | 25 | Multiple reporting pathways |
| **Total** | **~435** | |

### Difficulty Distribution

| Difficulty | Target % | Description |
|------------|----------|-------------|
| Low | 25% | Single clause, straightforward scenario, clear verdict |
| Medium | 45% | Multiple clauses or conditional reasoning, sector-specific context |
| High | 30% | IT/OT boundary ambiguity, multi-regulator overlap, waiver edge cases, adversarial framing |

### Test Category Distribution

Each benchmark should include:
- **Positive cases**: Scenarios where the answer IS compliant (tests for false negatives)
- **Negative cases**: Scenarios where the answer IS NOT compliant (tests for false positives)
- **Edge cases**: Conditional compliance, compensating controls, partial compliance
- **Adversarial cases**: Designed to elicit hallucination or over-specification

### Existing Test Case Triage

| Category | Estimated % | Action |
|----------|-------------|--------|
| Salvageable | ~40-50% | Migrate to v2 schema, improve key_facts, add fail_conditions |
| Revise | ~30% | Rewrite question for practitioner grounding, reconstruct ground truth |
| Discard | ~20-30% | Too abstract, definitional, or have unrecoverable key_facts gaps |

### Generation Pipeline

```
Step 1: Seed Collection
  - Extract scenarios from CIIO research
  - Walk CCoP clauses for uncovered areas
  - Triage existing 118 test cases

Step 2: Question Drafting (LLM-assisted)
  - Generate using research context + CCoP source text
  - Apply question design principles as constraints
  - Ensure sector diversity within each benchmark

Step 3: Ground Truth Construction (LLM-assisted + human)
  - Per question: expected_response, key_facts (tiered + sourced),
    reasoning_chain, fail_conditions, acceptable_variations
  - All clause references verified against CCoP 2.0 PDF

Step 4: Schema Validation (automated)
  - Validate against v2 JSON schema
  - All required fields present
  - Key_facts have sources
  - Minimum 2 critical-tier facts per reasoning case
  - Question length >= 50 chars
  - No duplicate test_ids

Step 5: Human Review
  - Clause reference verification
  - Question quality against design principles
  - Expected response accuracy and completeness
  - Key facts correctness and tier accuracy

Step 6: Expert Validation
  - Domain expert reviews via structured spreadsheet
  - Approve / Revise / Reject per test case
  - Rejected cases loop back to Step 2
```

---

## 4. Execution Workflow

### Parallel Workstreams

```
Phase Start
    |
    +-- Stream 1: Schema Design -----------------+
    |   1a. Finalize v2 schema from research      |
    |   1b. Build JSON schema validator           |
    |   1c. Write migration mapping (v1 to v2)    |
    |                                             |
    +-- Stream 2: Benchmark Audit ----------------+
    |   2a. Audit all 21 benchmarks               |
    |   2b. Propose merges/adds/removals          |
    |   2c. Finalize benchmark set + IDs          |
    |                                             |
    v                                             |
  Merge Point <-----------------------------------+
    |  Reconcile schema with benchmark set
    |  Assign scoring path per benchmark
    |
    v
  Test Case Generation (Steps 1-4)
    |
    v
  Quality Gate 1: Human Review (Step 5)
    |
    v
  Quality Gate 2: Expert Validation (Step 6)
    |
    v
  Deliverables
```

### Directory Structure

```
ground-truth/
+-- archive/
|   +-- phase-2/                    # V1 files archived here
|       +-- test-suite/             # Original 21 JSONL files
|       +-- expert-validation/      # Original Excel + review docs
+-- test-suite/                     # V2 JSONL files (one per benchmark)
+-- schema/                         # V2 schema definition + validator
|   +-- test-case-v2.schema.json
|   +-- validate.py
+-- expert-validation/              # V2 expert review spreadsheet
+-- coverage-matrix.md              # Benchmarks x sections x sectors
```

### Deliverables

| Deliverable | Format | Location |
|-------------|--------|----------|
| V2 test suite | JSONL per benchmark | `ground-truth/test-suite/` |
| V2 schema + validator | JSON Schema + Python | `ground-truth/schema/` |
| Expert validation spreadsheet | Excel | `ground-truth/expert-validation/` |
| Coverage matrix | Markdown | `ground-truth/coverage-matrix.md` |
| Archived v1 ground truth | JSONL + Excel | `ground-truth/archive/phase-2/` |
| Benchmark registry | Markdown | `docs/phase-2/benchmark-registry.md` |
| Migration report | Markdown | `docs/phase-2/ground-truth-v2-migration.md` |

### Success Criteria

| Criterion | Target |
|-----------|--------|
| Minimum test cases per benchmark | 20 |
| Total test cases | ~435 |
| Schema validation pass rate | 100% |
| Every key_fact has a source reference | 100% |
| Every reasoning test case has >= 2 critical-tier key_facts | 100% |
| CCoP section coverage | 11/11 sections |
| Sector diversity per benchmark | >= 3 sectors |
| Difficulty distribution | ~25% low, ~45% medium, ~30% high |
| No empty or placeholder key_facts | 0 |
| Expert validation first-pass approval | >= 80% |

### Out of Scope

- Changes to scoring infrastructure (scorers, LLM judge prompts, scoring formula)
- Changes to CLI or evaluation pipeline code
- Fine-tuning dataset derivation (future phase)
- Running baseline evaluation against v2 (separate effort)
- Automated difficulty calibration (requires baseline run)
