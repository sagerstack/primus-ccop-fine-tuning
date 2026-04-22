# Phase 3.2 Plan 06 — Pipeline Preflight Verification

**Date:** 2026-04-22 (updated after user decisions)
**Purpose:** Demonstrate the `patcher → regen` pipeline is ready to run before the user approves Phase C application.

## User decisions applied (Phase B, pre-execution)

1. **B02 cluster** (Option 3): ER text rewritten for all 4 rows (B2-003, B2-010, B2-014, B2-024) — fabricated 14/30-day timelines removed, replaced with CCoP §5.10 "timely manner" + risk-based prioritisation language verbatim from the source.
2. **B3 cluster** (full scope): All 27 non-waiver B3 rows mapped per-row (B3-004 and B3-011 continue to be handled by B03_117). Five previously wrong singleton entries (B3-005/006/019/021/024 → waiver) corrected against actual ER topics (§5.1.4, §5.10, §7.3, §5.10.1(g), §8.1.4).
3. **B24-022 BONUS** finding: added to per-row map as `6.4.1, 6.4.3, 7.1.1(a), 7.1.1(d) [support: 7.3.3(a)]` with 3 in-text ER substitutions fixing wrong Section 8.1 / 8.2 / 5.1 references.

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
| SINGLETONS (52 rows incl. 28 B3 full scope) | 52 | 52 |
| B21_EXEMPT | 11 | 11 |
| B24 (per-row, incl. B24-022) | 25 | 25 |
| B24 ER patches (B24-022 multi-sub) | 1 | 1 |
| B02_564 (→ §5.10.1(e)) | 4 | 4 |
| B02_564 ER full rewrite (timely-manner) | 4 | 4 |
| DEPRECATE (B05-018) | 1 | 1 |
| **TOTAL** | **176** | **176** |

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

## Known concerns — status after user decisions

1. **B02 `5.6.4` cluster — fabricated timelines in ER** — **RESOLVED (user chose Option 3)**. ER text rewritten for all 4 rows using CCoP §5.10 "timely manner" + risk-based prioritisation language only; no fabricated day counts remain.

2. **B03 templating issue — 29-row scope** — **RESOLVED (user chose expand to all 29)**. All B3 rows have CCoP-verified per-row mappings. Five previously wrong singleton entries corrected. B3-004 and B3-011 continue via B03_117 cluster.

3. **B24-022 BONUS finding** — **RESOLVED (user chose fix now)**. Added to per-row map with `6.4.1, 6.4.3, 7.1.1(a), 7.1.1(d) [support: 7.3.3(a)]` and 3 in-text ER substitutions.

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
