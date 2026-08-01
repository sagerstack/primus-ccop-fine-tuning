# Slice C Threshold Calibration Report

Generated: calibrate_slice_c_thresholds.py
Date: 2026-07-16

## Summary

**Test Set**: 18 cases (FIXED_18_TEST_IDS, stratified bdc4927d sample)
- **GOOD** (recall > 0): 4 cases
- **BAD** (recall = 0): 13 cases
- **N/A** (no gold clauses): 1 cases
- **ERROR**: 0 cases

**Aggregate Recall**: 20.6% (0.2059)
- Expected baseline: ~20.6% (per baseline-recall.md)
- Sanity check: ✅ PASS

## Threshold Analysis

For each signal, we present TWO operating points:

1. **CONSERVATIVE τ** = min(GOOD) - ε : Zero false positives on GOOD cases (high precision)
2. **BALANCED τ** = Best separation point: Maximizes (TP - FP) on this sample

### ⚠️  ce_confidence=None Frequency

**0/18 cases** (0%) had ce_confidence=None (reranker did not run or raised).

**Implication**: TAU_CONF is only weakly grounded on this sample. The should_requery
logic in omd_retrieval_grade.py arms ONLY when ce_confidence is PRESENT and below threshold —
a None-confidence marks the grade as low_confidence but does NOT trigger requery (per team-lead
ruling: "None != below-threshold; None = untrustworthy but requery can't fix it").

If most cases have None, then TAU_CONF is calibrated on a small subset and should_requery
rarely arms → **flag for Slice D** (requery loop will rarely activate).

---

### Signal: `top1_ce_score`

**None count**: 0/18 cases

**GOOD distribution** (recall > 0):
  - Values: [0.00010379222658229992, 0.007853551767766476, 0.027582628652453423, 0.06887966394424438]
  - Range: [0.0001, 0.0689]

**BAD distribution** (recall = 0):
  - Values: [0.00019462988711893559, 0.0002637399884406477, 0.0005069351755082607, 0.0007064096280373633, 0.0024643465876579285, 0.003998222760856152, 0.006072319578379393, 0.006881899666041136, 0.008303927257657051, 0.011006561107933521, 0.01458912342786789, 0.030560677871108055, 0.03888334333896637]
  - Range: [0.0002, 0.0389]

⚠️  **GOOD/BAD ranges overlap — no perfect separation possible**

At n=17, no threshold perfectly separates GOOD from BAD. Consider leaving this rule INERT to avoid overfitting.

#### Option A: CONSERVATIVE (zero FP on GOOD)

- **τ = -0.0099**
- Catches 0/13 BAD cases (TP rate: 0%)
- Trips 0/4 GOOD cases (FP rate: 0%)

#### Option B: BALANCED (best separation)

- **τ = 0.0389**
- Catches 12/13 BAD cases (TP rate: 92%)
- Trips 3/4 GOOD cases (FP rate: 75%)
- Separation: 9 (TP - FP)

---

### Signal: `ce_confidence`

**None count**: 0/18 cases

**GOOD distribution** (recall > 0):
  - Values: [0.0, 0.0, 0.0, 1.4257906835893974e-10]
  - Range: [0.0000, 0.0000]

**BAD distribution** (recall = 0):
  - Values: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.4713705182216223e-10, 9.125060374972143e-10, 1.292716886454387e-09, 2.5550169049922002e-08]
  - Range: [0.0000, 0.0000]

⚠️  **GOOD/BAD ranges overlap — no perfect separation possible**

At n=17, no threshold perfectly separates GOOD from BAD. Consider leaving this rule INERT to avoid overfitting.

#### Option A: CONSERVATIVE (zero FP on GOOD)

- **τ = -0.0100**
- Catches 0/13 BAD cases (TP rate: 0%)
- Trips 0/4 GOOD cases (FP rate: 0%)

#### Option B: BALANCED (best separation)

- **τ = 0.0000**
- Catches 12/13 BAD cases (TP rate: 92%)
- Trips 4/4 GOOD cases (FP rate: 100%)
- Separation: 8 (TP - FP)

---

### Signal: `top1_top2_margin`

**None count**: 0/18 cases

**GOOD distribution** (recall > 0):
  - Values: [0.0, 0.0, 0.0, 0.0]
  - Range: [0.0000, 0.0000]

**BAD distribution** (recall = 0):
  - Values: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  - Range: [0.0000, 0.0000]

⚠️  **GOOD/BAD ranges overlap — no perfect separation possible**

At n=17, no threshold perfectly separates GOOD from BAD. Consider leaving this rule INERT to avoid overfitting.

#### Option A: CONSERVATIVE (zero FP on GOOD)

- **τ = -0.0100**
- Catches 0/13 BAD cases (TP rate: 0%)
- Trips 0/4 GOOD cases (FP rate: 0%)

#### Option B: BALANCED (best separation)

- **τ = 0.0000**
- Catches 0/13 BAD cases (TP rate: 0%)
- Trips 0/4 GOOD cases (FP rate: 0%)
- Separation: 0 (TP - FP)

---

## Recommended Operating Point

Based on the above analysis, I recommend:

- **top1_ce_score**: INERT (ranges fully overlap at n=17; avoid overfitting)
- **ce_confidence**: INERT (ranges fully overlap at n=17; avoid overfitting)
- **top1_top2_margin**: INERT (ranges fully overlap at n=17; avoid overfitting)

**Final decision**: Defer to team-lead for operating point selection.

---

## Next Steps

1. Team-lead reviews this report and picks the operating point per signal
2. Builder wires chosen τ values into `omd_retrieval_grade.py` (TAU_* constants)
3. Builder updates goldens (`slice-c-grade-goldens.json`) + threshold assertion
4. Builder updates reason strings to embed chosen threshold literals

**DO NOT proceed to wiring thresholds until team-lead approves the operating point.**

