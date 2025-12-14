# Current Test Case Mapping to Updated Framework

## Mapping Analysis (Old Framework → New Framework)

| Old Benchmark | Cases | Maps to New Benchmark(s) | Coverage Status |
|--------------|-------|--------------------------|-----------------|
| Old B1: Applicability & Scope | 7 | **B1**: CCoP Applicability & Core Terminology | ✅ Partial (need rebalancing) |
| Old B2: Interpretation Accuracy | 7 | **B5**: Control Requirement Comprehension | ✅ Good coverage |
| Old B3: Clause Citation | 7 | **REMOVED** (strategic decision) | ❌ Not applicable |
| Old B4: Hallucination | 6 | **B21**: Regulatory Hallucination Rate | ✅ Good coverage |
| Old B5: SG Terminology | 6 | **B1** + **B18**: Applicability + Responsibility Attribution | ✅ Partial (split across benchmarks) |
| Old B6: IT/OT Classification | 6 | **B4**: Scenario-to-Control Mapping | ✅ Partial coverage |
| Old B7: Violation Detection | 8 | **B2** + **B7**: Compliance Classification + Gap Identification | ✅ Partial (split) |

## New Framework Coverage Analysis

| New Benchmark | Target | Have | Need | Priority |
|--------------|--------|------|------|----------|
| **B1**: CCoP Applicability & Core Terminology | 8 | ~10 | Rebalance | High |
| **B2**: Compliance Classification Accuracy | 7 | ~4 | 3 | Critical |
| **B3**: Conditional Compliance Reasoning | 7 | 0 | 7 | Critical |
| **B4**: Scenario-to-Control Mapping | 7 | ~6 | 1 | Medium |
| **B5**: Control Requirement Comprehension | 7 | ~7 | 0 | ✅ Complete |
| **B6**: Control Intent Understanding | 7 | 0 | 7 | Critical |
| **B7**: Gap Identification Quality | 8 | ~4 | 4 | High |
| **B8**: Gap Prioritisation | 7 | 0 | 7 | Critical |
| **B9**: Risk Identification Accuracy | 7 | 0 | 7 | Critical |
| **B10**: Risk Justification Coherence | 7 | 0 | 7 | Critical |
| **B11**: Risk Severity Assessment | 7 | 0 | 7 | Critical |
| **B12**: Audit Perspective Alignment | 7 | 0 | 7 | Critical |
| **B13**: Evidence Expectation Awareness | 7 | 0 | 7 | Critical |
| **B14**: Remediation Recommendation Quality | 7 | 0 | 7 | Critical |
| **B15**: Remediation Feasibility | 7 | 0 | 7 | Critical |
| **B16**: Residual Risk Awareness | 7 | 0 | 7 | Critical |
| **B17**: Policy vs Practice Distinction | 6 | 0 | 6 | High |
| **B18**: Responsibility Attribution (SG) | 6 | ~3 | 3 | High |
| **B19**: Cross-Scenario Consistency | 6 | 0 | 6 | High |
| **B20**: Over-Specification Avoidance | 6 | 0 | 6 | Critical |
| **B21**: Regulatory Hallucination Rate | 7 | ~6 | 1 | Medium |

## Summary Statistics

**Current State:**
- Total test cases: 47 (but some need remapping/rewriting)
- Benchmarks with coverage: 6 (B1, B2, B4, B5, B7, B21)
- Benchmarks without coverage: 15

**Target State:**
- Total test cases needed: ~147 (7 per benchmark × 21)
- Net new test cases needed: ~100
- Rebalancing needed: ~10 cases

## Test Case Generation Plan

### Phase 1: Foundation & Safety (Critical Priority)
- B1: Rebalance existing (keep 8 best cases)
- B2: Add 3 new cases
- B3: Create 7 new cases
- B20: Create 6 new cases
- B21: Add 1 new case
**Subtotal: 17 new cases**

### Phase 2: Core Capabilities (High Priority)
- B4: Add 1 new case
- B6: Create 7 new cases
- B7: Add 4 new cases
- B8: Create 7 new cases
- B9: Create 7 new cases
- B14: Create 7 new cases
**Subtotal: 33 new cases**

### Phase 3: Advanced Reasoning (Critical Priority)
- B10: Create 7 new cases
- B11: Create 7 new cases
- B15: Create 7 new cases
- B16: Create 7 new cases
**Subtotal: 28 new cases**

### Phase 4: Audit & Governance (High Priority)
- B12: Create 7 new cases
- B13: Create 7 new cases
- B17: Create 6 new cases
- B18: Add 3 new cases
- B19: Create 6 new cases
**Subtotal: 29 new cases**

**TOTAL NEW CASES NEEDED: ~107**
**FINAL SUITE: ~147 test cases across 21 benchmarks**
