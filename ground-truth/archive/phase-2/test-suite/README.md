# CCoP 2.0 Test Suite - Complete Baseline Evaluation

## Overview

**Consolidated test suite** for comprehensive baseline evaluation of LLMs on Singapore's Code of Practice for Cybersecurity (CCoP 2.0) compliance assessment.

**Framework Version**: CCoP 2.0 Benchmarks Updated (B1-B21)
**Total Test Cases**: 116 test cases across 21 benchmarks
**Quality Level**: Publication-ready
**Status**: ✅ Ready for baseline model evaluation
**Date Consolidated**: December 14, 2025

---

## Quick Start

### Loading Test Suite

```python
import json
import glob

def load_test_suite(suite_dir="test-suite/"):
    """Load all test cases from consolidated suite."""
    all_cases = {}

    for filepath in sorted(glob.glob(f"{suite_dir}/b*.jsonl")):
        benchmark_name = filepath.split('/')[-1].replace('.jsonl', '')
        cases = []

        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():  # Skip blank lines
                    cases.append(json.loads(line))

        all_cases[benchmark_name] = cases
        print(f"Loaded {benchmark_name}: {len(cases)} cases")

    return all_cases

# Load suite
test_suite = load_test_suite()
print(f"\nTotal: {sum(len(cases) for cases in test_suite.values())} test cases")
```

### Running Baseline Evaluation

```python
def run_baseline_evaluation(model, test_suite):
    """Run complete baseline evaluation."""
    results = {}

    for benchmark_name, test_cases in test_suite.items():
        print(f"\nEvaluating {benchmark_name}...")
        benchmark_results = []

        for case in test_cases:
            # Generate model response
            response = model.generate(case['question'])

            # Evaluate based on benchmark type
            score = evaluate_response(case, response)

            benchmark_results.append({
                'test_id': case['test_id'],
                'score': score,
                'response': response
            })

        results[benchmark_name] = benchmark_results
        avg_score = sum(r['score'] for r in benchmark_results) / len(benchmark_results)
        print(f"  Average score: {avg_score:.2f}")

    return results
```

---

## Complete Benchmark List

| # | Benchmark | Name | Cases | Difficulty | Evaluation |
|---|-----------|------|-------|------------|------------|
| **B01** | CCoP Applicability & Scope | 8 | Medium-High | Binary |
| **B02** | Compliance Classification Accuracy | 7 | Low-Medium | Binary |
| **B03** | Conditional Compliance Reasoning | 7 | Medium-High | LLM-Judge |
| **B04** | IT/OT System Classification | 7 | Medium-High | Binary |
| **B05** | Control Requirement Comprehension | 7 | Low-Medium | Binary |
| **B06** | Control Intent Understanding | 7 | Medium-High | LLM-Judge |
| **B07** | Gap Identification Quality | 8 | Medium-High | Expert Rubric |
| **B08** | Gap Prioritisation | 7 | High | LLM-Judge |
| **B09** | Risk Identification Accuracy | 7 | Medium-High | LLM-Judge |
| **B10** | Risk Justification Coherence | 7 | High | Expert Rubric |
| **B11** | Risk Severity Assessment | 7 | Medium-High | LLM-Judge |
| **B12** | Audit Perspective Alignment | 4 | High | LLM-Judge |
| **B13** | Evidence Expectation Awareness | 3 | Medium | LLM-Judge |
| **B14** | Remediation Recommendation Quality | 3 | High | Expert Rubric |
| **B15** | Remediation Feasibility | 3 | High | LLM-Judge |
| **B16** | Residual Risk Awareness | 3 | Medium-High | Expert Rubric |
| **B17** | Policy vs Practice Distinction | 3 | Medium-Critical | Expert Rubric |
| **B18** | Responsibility Attribution (Singapore) | 7 | Medium-High | LLM-Judge |
| **B19** | Cross-Scenario Consistency | 3 | Medium-Critical | LLM-Judge |
| **B20** | Over-Specification Avoidance | 3 | Medium-High | LLM-Judge |
| **B21** | Regulatory Hallucination Rate | 7 | High | Binary |
| **TOTAL** | **21 benchmarks** | **116** | - | - |

---

## File Structure

```
ground-truth/phase-2/test-suite/
├── b01_ccop_applicability_scope.jsonl                    (8 cases)
├── b02_compliance_classification_accuracy.jsonl          (7 cases)
├── b03_conditional_compliance_reasoning.jsonl            (7 cases)
├── b04_it_ot_classification.jsonl                        (7 cases)
├── b05_control_requirement_comprehension.jsonl           (7 cases)
├── b06_control_intent_understanding.jsonl                (7 cases)
├── b07_gap_identification_quality.jsonl                  (8 cases)
├── b08_gap_prioritisation.jsonl                          (7 cases)
├── b09_risk_identification_accuracy.jsonl                (7 cases)
├── b10_risk_justification_coherence.jsonl                (7 cases)
├── b11_risk_severity_assessment.jsonl                    (7 cases)
├── b12_audit_perspective_alignment.jsonl                 (4 cases)
├── b13_evidence_expectation_awareness.jsonl              (3 cases)
├── b14_remediation_recommendation_quality.jsonl          (3 cases)
├── b15_remediation_feasibility.jsonl                     (3 cases)
├── b16_residual_risk_awareness.jsonl                     (3 cases)
├── b17_policy_vs_practice_distinction.jsonl              (3 cases)
├── b18_responsibility_attribution_singapore.jsonl        (7 cases)
├── b19_cross_scenario_consistency.jsonl                  (3 cases)
├── b20_over_specification_avoidance.jsonl                (3 cases)
├── b21_hallucination_rate.jsonl                          (7 cases)
├── README.md                                             (this file)
└── CONSOLIDATION_SUMMARY.md                              (consolidation details)
```

---

## Benchmark Categories

### Foundation Layer (22 cases)
Tests fundamental CCoP understanding and applicability
- **B01**: CCoP Applicability & Scope (8)
- **B04**: IT/OT System Classification (7)
- **B05**: Control Requirement Comprehension (7)

### Compliance Judgment (14 cases)
Tests binary compliance assessment and nuanced reasoning
- **B02**: Compliance Classification Accuracy (7)
- **B03**: Conditional Compliance Reasoning (7)

### Gap Analysis (15 cases)
Tests identification and prioritization of compliance gaps
- **B07**: Gap Identification Quality (8)
- **B08**: Gap Prioritisation (7)

### Risk Reasoning (21 cases)
Tests structured risk identification, justification, and severity assessment
- **B09**: Risk Identification Accuracy (7)
- **B10**: Risk Justification Coherence (7)
- **B11**: Risk Severity Assessment (7)

### Audit Reasoning (7 cases)
Tests CSA auditor perspective and evidence expectations
- **B12**: Audit Perspective Alignment (4)
- **B13**: Evidence Expectation Awareness (3)

### Remediation (9 cases)
Tests practical remediation recommendations and feasibility assessment
- **B14**: Remediation Recommendation Quality (3)
- **B15**: Remediation Feasibility (3)
- **B16**: Residual Risk Awareness (3)

### Governance & Responsibility (10 cases)
Tests policy-practice alignment and Singapore regulatory framework
- **B17**: Policy vs Practice Distinction (3)
- **B18**: Responsibility Attribution (7)

### Consistency & Safety (13 cases)
Tests consistent application and hallucination avoidance
- **B19**: Cross-Scenario Consistency (3)
- **B20**: Over-Specification Avoidance (3)
- **B21**: Regulatory Hallucination Rate (7)

---

## Evaluation Methodology

### Three-Tier Evaluation System

#### Tier 1: Binary Evaluation
**Benchmarks**: B01, B02, B04, B05, B21 (36 cases)
**Method**: Exact match or deterministic validation
**Scoring**: Correct (4) or Incorrect (0)

#### Tier 2: Expert Rubric
**Benchmarks**: B07, B10, B14, B16, B17 (24 cases)
**Method**: Human expert scores 0-4 on multiple dimensions
**Dimensions**: Accuracy, Completeness, Reasoning, Practicality, Clarity

#### Tier 3: LLM-Judge
**Benchmarks**: B03, B06, B08, B09, B11, B12, B13, B15, B18, B19, B20 (56 cases)
**Method**: LLM evaluates response against criteria
**Scoring**: 0-4 scale with justification

---

## Test Case Format

Each test case follows this structure:

```json
{
  "test_id": "B01-001",
  "benchmark_type": "B01_CCoP_Applicability_Scope",
  "section": "Cybersecurity Act 2018 Part 3",
  "clause_reference": "Section 7(1)",
  "difficulty": "medium",
  "question": "Detailed scenario-based question...",
  "expected_response": "Comprehensive expected answer (200-500 words)...",
  "evaluation_criteria": {
    "accuracy": "Must correctly identify...",
    "completeness": "Should mention...",
    "context": "Should explain...",
    "clarity": "Should be understandable..."
  },
  "metadata": {
    "domain": "IT/OT",
    "criticality": "critical",
    "evaluation_method": "binary"
  }
}
```

---

## Quality Standards

All test cases meet these standards:

✅ **Unique Test ID** (B{XX}-{NNN} format)
✅ **Benchmark Type** (mapped to B1-B21)
✅ **CCoP Section Reference** (Sections 1-10)
✅ **Clause Reference** (specific clause numbers)
✅ **Difficulty Rating** (low/medium/high/critical)
✅ **Realistic Question** (scenario-based, audit-realistic)
✅ **Detailed Expected Response** (200-500 words)
✅ **Evaluation Criteria** (specific rubric dimensions)
✅ **Metadata** (domain, criticality, evaluation method)

---

## Singapore-Specific Context

Test cases incorporate Singapore regulatory framework:

- **CIIO** (CII Owner): Organizations designated by Commissioner
- **CSA** (Cyber Security Agency): Regulatory authority and auditor
- **Commissioner of Cybersecurity**: Authority under Cybersecurity Act 2018
- **Essential Services**: 11 sectors (energy, water, healthcare, etc.)
- **Digital Boundary**: Scope of CII systems subject to CCoP
- **Designated Person**: Statutory point of contact (Section 12)
- **Sector Lead**: Sector-specific regulatory coordination

---

## Baseline Testing Guide

### Step 1: Load Test Suite
```python
test_suite = load_test_suite("test-suite/")
```

### Step 2: Run Models
Test on:
- Llama-Primus-Reasoning (baseline cybersecurity LLM)
- DeepSeek-R1 (baseline reasoning LLM)

### Step 3: Evaluate Responses
Use appropriate evaluation method per benchmark:
- Binary: String matching or deterministic check
- Expert Rubric: Manual scoring by domain expert
- LLM-Judge: Automated evaluation with judge model

### Step 4: Generate Report
Document per-benchmark scores and overall performance

---

## Expected Performance

### Baseline (Pre-Fine-Tuning)
- **Generic LLMs**: 30-45% average accuracy
- **Cybersecurity LLMs**: 50-65% average accuracy
- **Weakest areas**: B18 (Singapore-specific), B03 (conditional reasoning), B08 (prioritization)

### Target (Post-Fine-Tuning)
- **85%+ average accuracy** (enterprise compliance threshold)
- **High-impact benchmarks**: >20% improvement
- **Singapore-specific (B18)**: >30% improvement

---

## Consolidation History

This test suite consolidates:
- **44 cases** from `test-cases/` directory (rebalanced B1, B2, B4, B5, B7, B21)
- **72 cases** from `test-cases-new/` directory (newly created B3, B6, B8-B20)
- **Total**: 116 cases with standardized naming (b01-b21)

**Deprecated files removed**:
- b3_clause_citation_accuracy.jsonl (7 cases) - Citation accuracy removed from framework
- b5_singapore_terminology.jsonl (6 cases) - Merged into B01 and B18

**Source Directories** (preserved for reference):
- `../test-cases/` - Original rebalanced test cases
- `../test-cases-new/` - Newly created test cases

---

## Validation

Before baseline testing, validate suite integrity:

```python
import json

def validate_suite(suite_dir="test-suite/"):
    """Validate test suite integrity."""
    issues = []
    all_test_ids = set()

    for filepath in glob.glob(f"{suite_dir}/b*.jsonl"):
        with open(filepath, 'r') as f:
            for i, line in enumerate(f, 1):
                if not line.strip():
                    continue

                try:
                    case = json.loads(line)

                    # Check required fields
                    required = ['test_id', 'benchmark_type', 'question',
                                'expected_response', 'evaluation_criteria']
                    for field in required:
                        if field not in case:
                            issues.append(f"{filepath}:{i} - Missing {field}")

                    # Check unique test_id
                    if case['test_id'] in all_test_ids:
                        issues.append(f"{filepath}:{i} - Duplicate test_id: {case['test_id']}")
                    all_test_ids.add(case['test_id'])

                except json.JSONDecodeError as e:
                    issues.append(f"{filepath}:{i} - Invalid JSON: {e}")

    if issues:
        print(f"❌ Found {len(issues)} issues:")
        for issue in issues[:10]:  # Show first 10
            print(f"  - {issue}")
    else:
        print(f"✅ Suite validation passed! {len(all_test_ids)} unique test cases")

    return len(issues) == 0

# Run validation
validate_suite()
```

---

## Citation

When using this test suite in research:

```
@dataset{ccop2_test_suite_2025,
  title={CCoP 2.0 Benchmark Test Suite for LLM Compliance Assessment},
  author={Singapore CII Research Project},
  year={2025},
  publisher={Singapore},
  note={116 test cases across 21 benchmarks for Singapore Cybersecurity Code of Practice 2.0}
}
```

---

## Support & Documentation

- **Complete Documentation**: See `../test-cases-new/README.md` for detailed usage instructions
- **Consolidation Details**: See `CONSOLIDATION_SUMMARY.md` for merge history
- **Benchmark Framework**: See `../../../report/term1-end/benchmarks-updated.md`

---

## License

This test suite is part of academic research on fine-tuning LLMs for Singapore CCoP 2.0 compliance assessment.

---

**Version**: 1.0
**Last Updated**: December 14, 2025
**Status**: ✅ Production Ready
