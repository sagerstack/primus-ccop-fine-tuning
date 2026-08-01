# CRAG-Relevance Validation Report

Generated: validate_crag_relevance.py
Date: 2026-07-17

## Summary

**Test Set**: 18 cases (FIXED_18_TEST_IDS, stratified sample)
- **GOOD** (recall > 0): 4 cases
- **BAD** (recall = 0): 13 cases
- **N/A** (no gold clauses): 1 cases

**Aggregate Recall**: 20.6% (0.2059)
- Expected baseline: ~20.6%
- Sanity check: ✅ PASS

**Success Bar**: ≥60% BAD caught @ ≤25% GOOD tripped

---

## STEP 1: Option A — Raw Per-Doc Cross-Encoder Scores

### Anomaly Diagnosis

**Doc-text sanity**:
- All texts non-empty: False
- Distinct texts per case (mean): 1.0 / 8
- Min distinct: 1 / 8

**Standalone vs Pipeline CE**:
- Mean absolute difference: 0.0000
- Standalone range (mean): 0.0000
- Pipeline range (mean): 0.0000

⚠️  **VERDICT**: DEGENERATE-INPUT ARTIFACT: Empty doc texts detected

🐛 **CANDIDATE PIPELINE BUG**: Empty doc texts in retrieved candidates (check omd_retrieval passage hydration)

### Threshold Analysis

#### Aggregation: MAX

**GOOD distribution**: [0.00010379213199485093, 0.007853551767766476, 0.027582628652453423, 0.06887966394424438]
**BAD distribution**: [0.0001946300471900031, 0.0002637399884406477, 0.0005069349426776171, 0.0007064096280373633, 0.0024643465876579285, 0.003998222760856152, 0.006072319578379393, 0.006881906185299158, 0.008303927257657051, 0.011006561107933521, 0.01458912342786789, 0.030560677871108055, 0.03888334333896637]

⚠️  GOOD/BAD ranges overlap

**Meets success bar**: ❌ NO
**Best τ**: None (no threshold meets bar)

#### Aggregation: MEAN

**GOOD distribution**: [0.00010379213199485093, 0.007853551767766476, 0.027582628652453423, 0.06887966394424438]
**BAD distribution**: [0.0001946300471900031, 0.0002637399884406477, 0.0005069349426776171, 0.0007064096280373633, 0.0024643465876579285, 0.003998222760856152, 0.006072319578379393, 0.006881906185299158, 0.008303927257657051, 0.011006561107933521, 0.01458912342786789, 0.030560677871108055, 0.03888334333896637]

⚠️  GOOD/BAD ranges overlap

**Meets success bar**: ❌ NO
**Best τ**: None (no threshold meets bar)


---

## FINAL VERDICT

❌ **No GT-free signal separates GOOD/BAD on this corpus at n=17**

**Recommendation**: Defer GT-free relevance gating to a larger validation set, or accept that the detector relies on aggregate signals only.

