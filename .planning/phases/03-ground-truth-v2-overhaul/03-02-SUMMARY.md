---
phase: 03-ground-truth-v2-overhaul
plan: 02
subsystem: ground-truth
tags: [benchmark-registry, audit, ground-truth, risk-manager, ciio, ccop, test-case-design]

# Dependency graph
requires:
  - phase: 03-ground-truth-v2-overhaul
    plan: 01
    provides: V2 schema and directory structure
  - phase: 02.4-llm-judge-redesign-and-metric-simplification
    provides: universal LLM judge (scoring infrastructure benchmark definitions must target)
provides:
  - V2 benchmark registry with audit decisions for all 21 v1 benchmarks
  - Final 18-benchmark set with scoring paths, target counts, CCoP section coverage
  - Merges, removals, and additions documented with rationale
  - Question design guidance per benchmark for test case generation
affects: [03-03 through 03-11 — all test case generation plans use this registry as authoritative reference]

# Tech tracking
tech-stack:
  added: []
  patterns: [benchmark audit methodology (5 criteria), registry-driven test case generation]

key-files:
  created:
    - docs/phase-2/benchmark-registry.md

# Decisions
decisions:
  - "B8+B11 merged into B8 Risk-Based Prioritization: both test prioritization/severity — combined scoring target is richer"
  - "B14+B15 merged into B14 Remediation Quality & Feasibility: feasibility is a required sub-dimension of recommendation quality"
  - "B9+B16 merged into B9 Risk Identification & Residual Risk: residual risk is the natural extension of risk identification"
  - "B17 absorbed into B7: policy-vs-practice gap is a scenario type within gap identification, not a distinct capability"
  - "B19 removed: meta-benchmark testing consistency, not a compliance reasoning capability"
  - "B20 absorbed into B21: over-specification is a form of hallucination — same detection mechanism"
  - "B22 Waiver Reasoning added: Section 11(7) waiver process is top CIIO pain point with no v1 coverage"
  - "B23 Multi-Regulator Coordination added: CCoP+MAS-TRM/IM8/PDPC overlap is top-3 CIIO challenge"
  - "B24 Incident Response Guidance added: 2-hour notification + multi-regulator reporting is critical Risk Manager scenario"

# Metrics
metrics:
  duration: 6 min
  completed: 2026-04-01
---

# Phase 03 Plan 02: V2 Benchmark Registry Summary

One-liner: Audited 21 v1 benchmarks against 5 CIIO-relevance criteria and produced the authoritative v2 benchmark registry defining 18 restructured benchmarks with scoring paths, ~435 target cases, and question design guidance.

## What Was Done

### Task 1: V1 Benchmark Audit

Read all 21 v1 JSONL files from `ground-truth/phase-2/test-suite/` (Plan 01 has not yet archived them). Evaluated each against 5 audit criteria using CIIO research for practitioner context.

Key audit findings:
- 3 benchmarks had 100% placeholder key_facts (B6, B17, B14) — unusable in current form
- 5 benchmarks had majority abstract/definitional questions (B5, B6, B10, B13, B21) — practitioner reframing required
- B3, B7 were strongest v1 benchmarks (zero quality issues, all scenario-grounded)
- B12, B13, B14, B15, B16, B17, B19, B20 were critically underpopulated (3-4 cases each)
- B19 was a meta-benchmark testing consistency across other benchmarks, not a compliance capability

### Task 2: V2 Benchmark Registry

Created `docs/phase-2/benchmark-registry.md` with:
- V1 audit table (21 benchmarks, all criteria, decision rationale)
- Changes from V1 (merges, removals/absorptions, new benchmarks)
- 18 benchmark definitions with: scoring path, description, V2 changes, target count, key CCoP sections, question design guidance

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| B8+B11 → B8 Risk-Based Prioritization | Gap prioritization and risk severity are both prioritization judgements — merged scoring target is richer |
| B14+B15 → B14 Remediation Quality & Feasibility | Feasibility is not a separate capability; it is a required dimension of any good remediation recommendation |
| B9+B16 → B9 Risk Identification & Residual Risk | Risk identification → residual risk is one continuous cycle; testing them separately created redundant thin benchmarks |
| B17 absorbed into B7 | Policy-vs-practice gap is a scenario type (100% key_fact issues in v1); B7 already covers evidence-based gap analysis |
| B19 removed | Cross-scenario consistency is a dataset-level quality property, not something the model needs to be tested for per se |
| B20 absorbed into B21 | Over-specification is fabricating requirements beyond what CCoP mandates — same as hallucination, same detector |
| B22, B23, B24 added | CIIO research identified waiver process, multi-regulator overlap, and incident response as top Risk Manager pain points with zero v1 coverage |

## Deviations from Plan

None — plan executed exactly as written.

## Next Phase Readiness

Plan 03-03 onwards can begin test case generation using this registry as the authoritative reference. The registry defines per-benchmark:
- Scoring path (informs which schema fields are required)
- Question design guidance (informs question generation prompts)
- Target count and key CCoP sections (informs coverage matrix)
- V2 changes (informs which v1 cases to salvage vs discard)
