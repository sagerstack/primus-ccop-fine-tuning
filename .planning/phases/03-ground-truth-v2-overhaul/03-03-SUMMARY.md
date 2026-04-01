---
phase: 03-ground-truth-v2-overhaul
plan: 03
subsystem: ground-truth
tags: [triage, v2-migration, benchmark-mapping, test-cases, classification]

# Dependency graph
requires:
  - phase: 03-02
    provides: v2 benchmark registry (18 benchmarks, IDs, merge/absorption decisions)
  - phase: 03-01
    provides: v2 schema definition and validation rules
provides:
  - Per-test-case classification (Keep/Revise/Discard) for all 118 v1 cases
  - V2 benchmark mapping for every v1 case
  - Actionability analysis for test case generation plans
  - Quantified migration effort: 52 Keep (immediate), 36 Revise, 30 Discard
affects:
  - 03-04 through 03-11 (test case generation plans — know what exists and what to generate)
  - Any plan that generates v2 test cases for specific benchmarks

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Triage classification: Keep/Revise/Discard with explicit criteria mapped to benchmark audit findings"
    - "Per-benchmark triage tables with V2 Benchmark column for direct registry linkage"

key-files:
  created:
    - ground-truth/archive/phase-2/triage-report.md
  modified: []

key-decisions:
  - "Keep 52 cases (44%) — within spec target 40-50%; B3 and B7 are strongest v1 benchmarks with zero discards"
  - "B14 (Remediation): 3/3 Discard — 100% key_facts placeholders; critical benchmark requires full regeneration"
  - "B17 (Policy vs Practice): 3/3 Discard — all key_facts placeholders; scenario concepts will inform B7 generation"
  - "B19 (Cross-Scenario): 3/3 Discard — meta-benchmark retired; consistency addressed at dataset analysis level"
  - "B20 (Over-Specification): 3/3 Keep → B21 — all 3 cases are strong adversarial patterns, direct migration"
  - "B5 (Control Requirement): 0 Keep, 7 Revise — all cases need practitioner reframing, none are discards"
  - "Revise criteria for B13: audit-centric → Risk Manager preparation framing (all 3 cases)"

patterns-established:
  - "Triage rationale documents both the issue type (placeholder key_facts, abstract framing) and the fix path (reframe/regenerate)"
  - "Absorbed benchmark cases (B17→B7, B20→B21) documented as Discard with 'scenario concepts inform X generation' note"

# Metrics
duration: 5min
completed: 2026-04-01
---

# Phase 3 Plan 03: V1 Test Case Triage Summary

**118 v1 test cases classified across 21 benchmarks: 52 Keep (44%), 36 Revise (31%), 30 Discard (25%) — with v2 benchmark mapping for each**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-01T02:45:48Z
- **Completed:** 2026-04-01T02:50:39Z
- **Tasks:** 2
- **Files modified:** 1 (created)

## Accomplishments

- Classified all 118 v1 test cases with explicit Keep/Revise/Discard criteria for each
- Mapped every case to its v2 benchmark ID using the registry from 03-02 (direct, merged, and absorbed mappings)
- Identified 52 immediately migratable cases and 36 revise-and-use cases, reducing generation effort for plans 03-04 through 03-11
- B3 (Conditional Compliance) confirmed as only zero-discard benchmark — all 7 cases Keep
- B7 (Gap Identification) confirmed as all-Keep (8/8) — strong 30-case generation foundation
- B21 + B20 absorption = 10 toward 25-case target without any generation

## Task Commits

Each task was committed atomically:

1. **Task 1 + Task 2: Classify all 118 cases and write triage report** - `ede9f60` (feat)

**Plan metadata:** (pending final commit)

## Files Created/Modified

- `ground-truth/archive/phase-2/triage-report.md` — 450-line triage with per-benchmark tables, summary stats, v2 mapping summary, and actionability analysis

## Decisions Made

- **52 Keep** is within spec target (40-50%) — distribution validates assessment methodology
- **B5 all Revise (not Discard)**: 7/7 cases have valuable clause references and key_facts; question reframing preserves 70% of generation effort
- **B6 4 Discard**: placeholder key_facts + abstract intent questions with no scenario = unusable; 3 Revise cases have at least 1 good key_fact
- **B13 all Revise (not Keep)**: evidence expectation content is sound but framing is audit-centric; all 3 need RM perspective reframing
- **B14 full Discard**: 100% key_facts placeholders across all 3 cases — no salvageable ground truth; regeneration from scratch required for this critical benchmark

## Deviations from Plan

None — plan executed exactly as written. Triage classification performed directly from reading all 21 JSONL files, benchmark registry confirmed mappings.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Triage report is actionable input for all test case generation plans (03-04 through 03-11)
- Each generation plan can reference the triage to know: how many cases already exist (Keep), how many need rewriting (Revise), and how many need full generation (Discard + gap-to-target)
- B3 (30 target - 7 Keep = 23 to generate), B7 (30 target - 8 Keep = 22 to generate), B21 (25 target - 10 salvaged = 15 to generate)
- No blockers — ready to proceed to Plan 04

---
*Phase: 03-ground-truth-v2-overhaul*
*Completed: 2026-04-01*
