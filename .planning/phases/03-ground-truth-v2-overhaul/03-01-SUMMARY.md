---
phase: 03-ground-truth-v2-overhaul
plan: 01
subsystem: ground-truth
tags: [jsonschema, python, json-schema, validation, ground-truth, test-cases]

# Dependency graph
requires:
  - phase: 02.4-llm-judge-redesign-and-metric-simplification
    provides: universal LLM judge consuming key_facts, reasoning_chain, fail_conditions from ground truth
provides:
  - V1 ground truth archived at ground-truth/archive/phase-2/
  - V2 directory structure (test-suite/, schema/, expert-validation/) ready for test case generation
  - JSON Schema definition for v2 test cases (test-case-v2.schema.json)
  - Schema validator with business rules (validate.py)
  - Sample v2 test case B3-001 validating against schema
affects: [03-02 through 03-11 — all test case generation plans consume this schema]

# Tech tracking
tech-stack:
  added: [jsonschema ^4.0.0]
  patterns: [JSONL per benchmark, nested JSON schema with separated concerns, Draft 2020-12 validation]

key-files:
  created:
    - ground-truth/schema/test-case-v2.schema.json
    - ground-truth/schema/validate.py
    - ground-truth/test-suite/b03_conditional_compliance_reasoning.jsonl
  modified:
    - src/pyproject.toml (added jsonschema dependency)

key-decisions:
  - "*.json gitignore pattern excludes schema file — forced git add -f for test-case-v2.schema.json"
  - "V2 directories (test-suite/, schema/, expert-validation/) created empty, ready for subsequent plans"
  - "All phase-2 v1 artifacts (21 JSONL + subdirs + scripts) moved to archive, not just the top-level JSONL files"

patterns-established:
  - "JSONL test case format: one JSON object per line, one file per benchmark"
  - "Schema validator pattern: JSON Schema validation first, then business rules on passing cases"
  - "Tiered key_facts: critical/important/supporting with mandatory source reference"

# Metrics
duration: 5min
completed: 2026-04-01
---

# Phase 3 Plan 1: Archive V1 Ground Truth and Establish V2 Schema Summary

**V1 ground truth archived (21 JSONL + all phase-2 artifacts), V2 schema contract defined with Draft 2020-12 JSON Schema and business rule validator, B3-001 sample validates with 0 errors.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-04-01T02:30:44Z
- **Completed:** 2026-04-01T02:35:30Z
- **Tasks:** 2/2
- **Files modified:** 4 (3 created, 1 modified)

## Accomplishments

- Archived all phase-2 v1 artifacts (21 benchmark JSONL files, expert validation spreadsheet/scripts, internal subdirs/backups) to ground-truth/archive/phase-2/ — clean slate for v2
- Created V2 JSON Schema (Draft 2020-12) enforcing nested structure: input (question/sector/role), ground_truth (tiered key_facts, reasoning_chain, acceptable_variations), fail_conditions, metadata with domain/difficulty/test_category
- Built schema validator (validate.py) combining JSON Schema + business rules: test_id prefix check, reasoning_chain requirement for LLM-judge benchmarks, critical key_facts minimum count, expected_label requirement for rule-based benchmarks
- Sample test case B3-001 (energy/SCADA shared admin accounts) validates cleanly: 1 valid, 0 warnings, 0 errors

## Task Commits

1. **Task 1: Archive V1 and create V2 directory structure** - `38a98db` (chore)
2. **Task 2: V2 schema, validator, sample test case** - `66c18db` (feat) + `2d2c91b` (feat — schema forced-add past .gitignore)

## Files Created/Modified

- `ground-truth/schema/test-case-v2.schema.json` — V2 JSON Schema definition (Draft 2020-12)
- `ground-truth/schema/validate.py` — Schema validator: JSON Schema + business rules, CLI with --file/--strict
- `ground-truth/test-suite/b03_conditional_compliance_reasoning.jsonl` — B3-001 sample test case
- `src/pyproject.toml` — Added jsonschema ^4.0.0 dependency

## Decisions Made

- `*.json` is in .gitignore (project-wide pattern to exclude result JSON files). The schema file requires force-add: `git add -f ground-truth/schema/test-case-v2.schema.json`. Future plans generating test suite JSONL files will not face this issue (*.jsonl is not ignored).
- V1 directory had more content than expected (test-suite had backup_original/, updated/, updated_v2/ subdirs + scripts). All moved to archive — archive is a complete record of v1 work.
- jsonschema installed via `poetry run pip install` since network was unavailable for `poetry add`. pyproject.toml updated manually with `^4.0.0` constraint.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Additional v1 artifacts beyond 21 JSONL files**

- **Found during:** Task 1
- **Issue:** ground-truth/phase-2/test-suite/ contained backup_original/, updated/, updated_v2/ subdirs plus scripts/docs. Plan specified moving "21 JSONL files" but all of this is v1 content.
- **Fix:** Moved all content (subdirs, scripts, docs) to archive to ensure clean v2 directories.
- **Files modified:** ground-truth/archive/phase-2/test-suite/ (extended with all subdirs)

**2. [Rule 3 - Blocking] *.json gitignore pattern blocked schema file**

- **Found during:** Task 2 commit
- **Issue:** .gitignore has `*.json` pattern excluding schema file from tracking.
- **Fix:** Used `git add -f` to force-add the schema file. Documented as decision for future plans.
- **Files modified:** N/A (git operation only)

**3. [Rule 3 - Blocking] No network access for `poetry add jsonschema`**

- **Found during:** Task 2 setup
- **Issue:** `poetry add jsonschema` failed (no internet). Package not in existing lock file.
- **Fix:** Installed via `poetry run pip install jsonschema` (pip within poetry venv had cached package). Added to pyproject.toml manually.
- **Files modified:** src/pyproject.toml

## Next Phase Readiness

- V2 schema is the contract for all subsequent test case generation plans (03-02 through 03-11)
- validator.py is the quality gate for every generated JSONL file
- The forced git add pattern for schema file is documented — future plans should use `git add -f` for `*.json` files in ground-truth/schema/
