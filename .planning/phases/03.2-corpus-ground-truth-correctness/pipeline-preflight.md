# Phase 3.2 Plan 06 — Pipeline Preflight Verification

**Date:** 2026-04-22
**Purpose:** Demonstrate the `patcher → regen` pipeline is ready to run before the user approves Phase C application.

---

## What was verified

Pipeline executed end-to-end against a **copy** of the authoritative Excel (`/tmp/excel-pipeline-test.xlsx`). No in-repo files were modified.

### Step 1 — Patcher (Excel → Excel)

```bash
cp ground-truth/expert-validation/CCoP_V2_Test_Cases_Expert_Review.xlsx /tmp/excel-pipeline-test.xlsx
cd src
poetry run python scripts/patch_ground_truth_excel.py \
  --excel /tmp/excel-pipeline-test.xlsx \
  --all --cluster B24 --cluster B02_564 --cluster DEPRECATE
```

**Result:**

| Cluster | Matched | Modified |
|---------|---------|----------|
| B08 (REMAP-ALL) | 25 | 25 |
| B09 (REMAP-ALL) | 25 | 25 |
| B22 (REMAP-ALL) | 20 | 20 |
| B07_422 | 4 | 4 |
| B03_117 | 2 | 2 |
| B05_523 (MFA bundle) | 2 | 2 |
| SINGLETONS (29 rows) | 29 | 29 |
| B21_EXEMPT | 11 | 11 |
| B24 (per-row) | 24 | 24 |
| B02_564 (→ §5.10.1(e)) | 4 | 4 |
| DEPRECATE (B05-018) | 1 | 1 |
| **TOTAL** | **147** | **147** |

### Step 2 — Idempotency

Re-running the patcher against the already-patched Excel yields **0 modifications** (all target cells match). Safe to re-run without double-edits.

### Step 3 — Regen script (Excel → JSONL)

```bash
poetry run python scripts/regenerate_test_suite_from_excel.py \
  --excel /tmp/excel-pipeline-test.xlsx --dry-run
```

**Result:**

| Metric | Count |
|--------|-------|
| JSONL rows modified | 196 |
| JSONL rows unchanged | 239 |
| JSONL rows missing-in-excel | 0 |

Every `test_id` present in the JSONL files has a corresponding Excel row — no orphans.

### Step 4 — Field-level propagation checks

Direct unit-level inspection confirms all new JSONL fields populate correctly:

| Field | Example row | Source | Target |
|-------|-------------|--------|--------|
| `metadata.section` | B05-013 | Excel col 7 (`"1"`) | JSONL `"metadata.section": "1"` |
| `metadata.clause_reference[]` | B24-001 | Excel col 8 primary | `["7.1.1(b)", "7.1.1(g)", "7.1.1(h)"]` |
| `metadata.support_citations[]` | B24-001 | Excel col 8 `[support: ...]` | `["8.2.1"]` |
| `metadata.audit_exempt` | B21-001 | Excel col 19 `[AUDIT_EXEMPT:...]` | `true` |
| **top-level** `status` | B05-018 | Excel col 19 `[DEPRECATED:...]` | `"deprecated"` |
| **top-level** `deprecated_reason` | B05-018 | Excel col 19 content | `"Cross-border data transfer scoped to PDPA, not CCoP 2.0"` |
| `ground_truth.expected_response` | B24-001 | Excel col 11 | in-text substitution applied |

### Step 5 — Audit flag coverage (Pass-1)

**100% coverage** — all 71 non-B08/B09/B22 Pass-1 flagged `test_id`s have a rule in the patcher.

| Coverage source | Test IDs |
|-----------------|----------|
| B24 per-row map | 24 rows |
| B21_EXEMPT | 6 flagged rows |
| B07_422 cluster | 4 rows |
| B03_117 cluster | 2 rows |
| B02_564 cluster | 4 rows |
| B05_523 cluster | 2 rows |
| SINGLETONS | 29 rows |
| DEPRECATE | 1 row |

---

## Known concerns (flagged for user decision)

1. **B02 `5.6.4` cluster — fabricated timelines in ER** (Cluster 6 CONCERN in `audit-remap-proposal.md`). Citation corrected to §5.10.1(e), but the ER text embeds 14/30-day patch timelines that are NOT in CCoP 2.0 or any supporting doc. User picks Option 1 (accept) / 2 (deprecate) / 3 (rewrite ER to "timely manner").

2. **B03 templating issue** — 22 remaining B3 rows (beyond the 7 flagged) have `["Section 2"]` placeholder in JSONL `metadata.clause_reference`. Scope expansion option deferred to user.

3. **B24-022 BONUS finding** — not flagged by Pass-1 (clauses `8.1, 8.2` exist in CCoP) but semantically wrong (topic is threat intel pre-incident). Proposed remap documented; not in patcher pending user approval.

4. **B24 col 7 format inconsistency** — the patcher sets chapter numbers as digits (`"7"`, `"5"`) where existing rows used labels like `"CCoP 2.0 Section 8"`. The regen script normalises these into strings for `metadata.section`. No action required — cosmetic only.

---

## Readiness gate

Checklist before Phase C can execute:

- [x] Patcher runs cleanly on Excel copy (147 edits)
- [x] Patcher is idempotent (0 edits on re-run)
- [x] Regen script consumes patched Excel (196 JSONL field updates)
- [x] No orphan rows (0 missing-in-excel)
- [x] Deprecation propagates to JSONL top-level
- [x] audit_exempt propagates to JSONL metadata
- [x] Support citations propagate to JSONL metadata
- [x] In-text ER patches apply
- [x] All Pass-1 audit flags covered (71 rows)
- [ ] **User approves Phase B** (blocks all write operations against the authoritative Excel and real JSONL files)

**Once approved,** Phase C sequence:

```bash
cd src
# 1. Patch the authoritative Excel (creates .bak automatically)
poetry run python scripts/patch_ground_truth_excel.py \
  --all --cluster B24 --cluster B02_564 --cluster DEPRECATE

# 2. Regenerate JSONL test-suite from patched Excel (creates .bak per file)
poetry run python scripts/regenerate_test_suite_from_excel.py
```

Both scripts create timestamped `.bak` backups before writing. Recovery is `mv *.bak *` if anything goes wrong.
