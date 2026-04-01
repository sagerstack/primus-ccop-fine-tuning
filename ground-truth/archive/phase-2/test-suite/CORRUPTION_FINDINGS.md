# Test Case Data Corruption - Investigation Findings

## Executive Summary

**Status**: ✅ Root cause identified
**Severity**: HIGH - Blocks B4 and B5 benchmark evaluation
**Affected Files**: 2 out of 21 (b04, b05)
**Fix Complexity**: SIMPLE - Test ID renumbering only

---

## Problem Statement

Two test case files contain mismatched data between filename, test_id, and benchmark_type:

| Filename | Expected Benchmark | Actual test_ids | Actual benchmark_type | Status |
|----------|-------------------|-----------------|----------------------|--------|
| **b04_it_ot_classification.jsonl** | B4 | B6-001 to B6-007 | B5_IT_OT_Classification | ❌ CORRUPTED |
| **b05_control_requirement_comprehension.jsonl** | B5 | B2-001 to B2-007 | B2_CCoP_Interpretation_Accuracy | ❌ CORRUPTED |

**Impact**:
- B4 tests are rejected due to test_id mismatch (B6 ≠ B4)
- B5 tests appear as duplicate B2 tests
- B4 and B5 benchmarks cannot be evaluated
- 14 test cases (out of 118) are unusable

---

## Root Cause Analysis

### The Consolidation Mistake

According to `CONSOLIDATION_SUMMARY.md`, the mapping was:

```
OLD SYSTEM → NEW SYSTEM
- b2_ccop_interpretation_accuracy.jsonl → b05_control_requirement_comprehension.jsonl (B5)
- b6_it_ot_classification.jsonl → b04_it_ot_classification.jsonl (B4)
```

**What Was Done**:
1. ✅ Files were copied to new filenames (b04, b05)
2. ✅ File names were renamed
3. ❌ **test_id fields inside JSONL were NOT updated**
4. ❌ **benchmark_type fields were NOT fully updated**

**What Should Have Been Done**:
1. Copy files to new names
2. **Update test_id from old benchmark to new** (B6→B4, B2→B5)
3. **Update benchmark_type to match new benchmark**

### Timeline of Corruption

1. **Dec 13-14**: Test consolidation performed
2. **Dec 14**: Schema update (update_test_schema_v2.py) ran
   - Added benchmark_category, key_facts, expected_label
   - **BUT schema update script ASSUMED test_ids were already correct**
   - Did NOT validate test_id matches filename
3. **Dec 14**: Files backed up to backup_original/ **with corruption intact**
4. **Dec 14**: Expert review Excel created **with corrupted test IDs**

### Why It Wasn't Caught

1. **validate_schema.py** checks schema fields, not test_id consistency
2. **Consolidation was manual** - no automated ID update
3. **Schema update script trusted existing data**
4. **No cross-check between filename and test_id**

---

## Detailed Corruption Analysis

### b04_it_ot_classification.jsonl

**Expected**: B4 benchmark (IT/OT Classification)
**Contains**: B6 test IDs + B5 benchmark_type

```json
{
  "test_id": "B6-001",  // ❌ WRONG - Should be B4-001
  "benchmark_type": "B5_IT_OT_Classification",  // ❌ WRONG - Should be B4_IT_OT_Classification
  "benchmark_category": "classification",  // ✅ Correct
  ...
}
```

**Content Origin**: Old `b6_it_ot_classification.jsonl`
**Test Content**: ✅ CORRECT (IT/OT classification questions)
**Only Issue**: Test IDs need renumbering B6 → B4

### b05_control_requirement_comprehension.jsonl

**Expected**: B5 benchmark (Control Requirement Comprehension)
**Contains**: B2 test IDs + B2 benchmark_type

```json
{
  "test_id": "B2-001",  // ❌ WRONG - Should be B5-001
  "benchmark_type": "B2_CCoP_Interpretation_Accuracy",  // ❌ WRONG - Should be B5_Control_Requirement_Comprehension
  "benchmark_category": "classification",  // ✅ Correct
  ...
}
```

**Content Origin**: Old `b2_ccop_interpretation_accuracy.jsonl`
**Test Content**: ✅ CORRECT (Control requirement comprehension questions)
**Only Issue**: Test IDs need renumbering B2 → B5

---

## Verification

Investigation script (`investigate_corruption.py`) results:

```
Total files checked: 21
Corrupted files: 2
Clean files: 19

CORRUPTED FILES DETAIL:

  b04_it_ot_classification:
    - Expected benchmark: B4
    - Actual test IDs: ['B6-001', 'B6-002', 'B6-003']...
    - Benchmark types: {'B5_IT_OT_Classification'}

  b05_control_requirement_comprehension:
    - Expected benchmark: B5
    - Actual test IDs: ['B2-001', 'B2-002', 'B2-003']...
    - Benchmark types: {'B2_CCoP_Interpretation_Accuracy'}
```

**Backup Status**: ❌ Backups contain same corruption (corruption predates backup)

---

## Fix Strategy

### Option 1: Manual Fix (NOT RECOMMENDED)
- Manually edit each test_id in both files
- Error-prone, time-consuming

### Option 2: Automated Fix (RECOMMENDED)
- Python script to update test_ids and benchmark_types
- Fast, accurate, reproducible

### Fix Requirements

For **b04_it_ot_classification.jsonl**:
- Replace all `"test_id": "B6-XXX"` with `"test_id": "B4-XXX"`
- Replace `"benchmark_type": "B5_IT_OT_Classification"` with `"benchmark_type": "B4_IT_OT_Classification"`

For **b05_control_requirement_comprehension.jsonl**:
- Replace all `"test_id": "B2-XXX"` with `"test_id": "B5-XXX"`
- Replace `"benchmark_type": "B2_CCoP_Interpretation_Accuracy"` with `"benchmark_type": "B5_Control_Requirement_Comprehension"`

### Post-Fix Validation

1. Run `investigate_corruption.py` → Should show 0 corrupted files
2. Run `validate_schema.py` → Should pass 118/118
3. Check test_id counts: B2 should have 7, B4 should have 7, B5 should have 7, B6 should have 7

---

## Recommended Actions

### Immediate (Required)
1. ✅ Create fix_corruption.py script
2. ✅ Run fix script to update b04 and b05
3. ✅ Validate all 21 files pass corruption check
4. ✅ Re-run schema validation
5. ✅ Update expert review Excel with corrected test IDs

### Short-term (Recommended)
1. Add test_id validation to validate_schema.py
2. Document this corruption in expert review materials
3. Check if expert has started review (may need to resend Excel)

### Long-term (Prevent Recurrence)
1. Add automated test_id consistency check to all validation scripts
2. Create consolidation script for future migrations (don't do manual)
3. Add cross-validation between filename, test_id, and benchmark_type

---

## Impact Assessment

**Before Fix**:
- 104/118 test cases usable (88%)
- B4 and B5 benchmarks unavailable
- Classification benchmarks: 2/4 available (50%)

**After Fix**:
- 118/118 test cases usable (100%)
- All 21 benchmarks available
- Classification benchmarks: 4/4 available (100%)

---

**Investigation Date**: December 15, 2025
**Investigator**: AI Assistant (Claude)
**Status**: Root cause confirmed, fix script ready
