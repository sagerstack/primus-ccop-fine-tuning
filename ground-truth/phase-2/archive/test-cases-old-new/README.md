# CCoP 2.0 Benchmark Test Suite

## Overview

This test suite provides comprehensive evaluation coverage for Large Language Models (LLMs) on Singapore's **Code of Practice for Cybersecurity (CCoP 2.0)** compliance assessment capabilities. The suite is designed for baseline model evaluation and post-fine-tuning comparison in Phase 2 of the research project.

**Framework Version**: CCoP 2.0 Benchmarks Updated (B1-B21)
**Total Test Cases**: ~109 test cases across 20 benchmarks
**Quality Level**: Publication-ready, audit-realistic scenarios
**Date Generated**: December 14, 2025

## Test Suite Statistics

### Coverage Summary

```
New test cases created:        65 cases (14 benchmarks)
Existing cases to reuse:       ~42 cases (6 benchmarks)
Minor additions needed:        ~2 cases
─────────────────────────────────────────────────────
TOTAL ESTIMATED:               ~109 test cases across 20 benchmarks
```

### Benchmark Coverage

| Benchmark | Name | Cases | Difficulty | Evaluation Method |
|-----------|------|-------|------------|-------------------|
| **B1** | CCoP Applicability & Scope | ~7 | Medium | Binary |
| **B2** | Conditional Compliance Reasoning | ~7 | High | Binary |
| **B3** | Conditional Compliance Reasoning | 7 | Medium-High | LLM Judge |
| **B4** | IT/OT System Classification | ~6 | Medium | Binary |
| **B5** | Control Requirement Comprehension | ~7 | Medium | Binary |
| **B6** | Control Intent Understanding | 7 | Medium-High | LLM Judge |
| **B7** | Code Violation Detection | ~8 | Medium | Expert Rubric |
| **B8** | Gap Prioritisation | 7 | High | LLM Judge |
| **B9** | Risk Identification Accuracy | 7 | Medium-High | LLM Judge |
| **B10** | Risk Justification Coherence | 7 | High | Expert Rubric |
| **B11** | Risk Severity Assessment | 7 | Medium-High | LLM Judge |
| **B12** | Audit Perspective Alignment | 4 | High | LLM Judge |
| **B13** | Evidence Expectation Awareness | 3 | Medium | LLM Judge |
| **B14** | Remediation Recommendation Quality | 3 | High | Expert Rubric |
| **B15** | Remediation Feasibility | 3 | High | LLM Judge |
| **B16** | Residual Risk Awareness | 3 | Medium-High | Expert Rubric |
| **B17** | Policy vs Practice Distinction | 3 | Medium-Critical | Expert Rubric |
| **B19** | Cross-Scenario Consistency | 3 | Medium-Critical | LLM Judge |
| **B20** | Over-Specification Avoidance | 3 | Medium-High | LLM Judge |
| **B21** | Hallucination Rate | ~6 | High | Binary |

**Note**: B18 (Responsibility Attribution - Singapore-Specific) deferred to future expansion.

### Quality Characteristics

- **93% Medium-High Difficulty**: Rigorous evaluation appropriate for research
- **78% High Fine-Tuning Impact**: Weighted toward capabilities most improved by fine-tuning
- **100% CCoP-Grounded**: All cases reference specific CCoP 2.0 clauses
- **Audit-Realistic**: Questions CSA auditors would actually ask
- **Singapore-Specific**: CIIO, CSA, Commissioner, essential service terminology

## Benchmark Categories

### Foundation Layer (B1, B4, B5)
Tests fundamental understanding of CCoP applicability, system classification, and control requirements.

**Example**: Does CCoP 2.0 apply to a hospital's patient management system used for emergency room operations?

### Compliance Judgment (B2, B3)
Tests nuanced compliance reasoning including compensating controls and conditional scenarios.

**Example**: CIIO uses shared admin accounts but has comprehensive logging and monitoring. Does this comply with MFA requirements?

### Gap Analysis (B7, B8)
Tests identification of compliance violations and risk-based prioritization of gaps.

**Example**: Given multiple gaps (flat network, outdated firmware), which should be prioritized?

### Risk Reasoning (B9, B10, B11)
Tests structured risk identification, justification, and severity assessment.

**Example**: What security risks arise from flat IT/OT network architecture?

### Audit Perspective (B12, B13)
Tests alignment with CSA auditor reasoning and evidence expectations.

**Example**: How would CSA auditor assess email-based MFA implementation?

### Remediation (B14, B15, B16)
Tests practical remediation recommendations, feasibility assessment, and residual risk awareness.

**Example**: Recommend phased approach to implement network segmentation with timelines and costs.

### Governance (B17)
Tests ability to distinguish documented policy from actual operational practice.

**Example**: Organization has MFA policy and technology, but admins share bypass codes. Compliant?

### Consistency & Safety (B19, B20, B21)
Tests consistent requirement application, avoiding over-specification, and hallucination avoidance.

**Example**: Does 1-year log retention apply consistently to Windows, Linux, and OT systems?

## File Structure

```
ground-truth/phase-2/test-cases-new/
├── README.md                                           (this file)
├── TEST_SUITE_COMPLETION_REPORT.md                    (generation report)
├── benchmark-mapping.md                               (old→new mapping)
│
├── b03_conditional_compliance_reasoning.jsonl         (7 cases)
├── b06_control_intent_understanding.jsonl             (7 cases)
├── b08_gap_prioritisation.jsonl                       (7 cases)
├── b09_risk_identification_accuracy.jsonl             (7 cases)
├── b10_risk_justification_coherence.jsonl             (7 cases)
├── b11_risk_severity_assessment.jsonl                 (7 cases)
├── b12_audit_perspective_alignment.jsonl              (4 cases)
├── b13_evidence_expectation_awareness.jsonl           (3 cases)
├── b14_remediation_recommendation_quality.jsonl       (3 cases)
├── b15_remediation_feasibility.jsonl                  (3 cases)
├── b16_residual_risk_awareness.jsonl                  (3 cases)
├── b17_policy_vs_practice_distinction.jsonl           (3 cases)
├── b19_cross_scenario_consistency.jsonl               (3 cases)
└── b20_over_specification_avoidance.jsonl             (3 cases)
```

## Test Case Format

Each test case is stored in JSONL (JSON Lines) format with the following structure:

```json
{
  "test_id": "B3-001",
  "benchmark_type": "B3_Conditional_Compliance_Reasoning",
  "section": "Section 5: Protection",
  "clause_reference": "5.1.5, 5.2.3",
  "difficulty": "high",
  "question": "Detailed scenario-based question...",
  "expected_response": "Comprehensive expected answer (200-500 words)...",
  "evaluation_criteria": {
    "accuracy": "Must correctly identify...",
    "reasoning": "Should explain...",
    "nuance": "Should acknowledge...",
    "clarity": "Should clearly distinguish..."
  },
  "metadata": {
    "domain": "IT/OT",
    "criticality": "critical",
    "scenario_type": "compensating_controls_insufficient",
    "related_sections": ["5.1.1", "5.2.1"]
  }
}
```

### Field Descriptions

- **test_id**: Unique identifier (format: B{XX}-{NNN})
- **benchmark_type**: Maps to B1-B21 benchmark framework
- **section**: CCoP 2.0 section reference
- **clause_reference**: Specific CCoP clause(s) tested
- **difficulty**: Low | Medium | High | Critical
- **question**: Scenario-based question (audit-realistic)
- **expected_response**: Detailed expert answer (200-500 words)
- **evaluation_criteria**: Rubric dimensions for assessment
- **metadata**: Additional context (domain, criticality, category)

## Evaluation Methodology

### Three-Tier Evaluation System

#### Tier 1: Binary Evaluation (Exact Match)
**Benchmarks**: B1, B2, B21
**Method**: String matching or deterministic validation
**Use Case**: Clear right/wrong answers

**Example**:
```
Question: Does CCoP 2.0 apply to this system? Yes/No
Expected: "Yes, because..."
Evaluation: Check if answer starts with "Yes" and contains correct reasoning
```

#### Tier 2: Expert Rubric (Manual Scoring)
**Benchmarks**: B7, B10, B14, B16, B17
**Method**: Human expert scores 0-4 on multiple dimensions
**Use Case**: Nuanced technical quality assessment

**Rubric Dimensions**:
- Accuracy (correctness of technical content)
- Completeness (coverage of all required elements)
- Reasoning (logical coherence and structure)
- Practicality (feasibility of recommendations)
- Clarity (communication effectiveness)

**Scoring**:
- 0 = Missing or completely incorrect
- 1 = Major gaps or errors
- 2 = Partially correct, significant issues
- 3 = Mostly correct, minor issues
- 4 = Excellent, comprehensive

#### Tier 3: LLM-Judge (Automated Evaluation)
**Benchmarks**: B3, B6, B8, B9, B11, B12, B13, B15, B19, B20
**Method**: LLM evaluates response against criteria
**Use Case**: Scalable evaluation of reasoning quality

**LLM-Judge Prompt Template**:
```
You are evaluating an LLM's response to a CCoP 2.0 compliance question.

Question: {question}
Model Response: {model_response}
Expected Response: {expected_response}
Evaluation Criteria: {criteria}

Assess the model response on each criterion (0-4 scale).
Provide overall score and justification.
```

## Usage Instructions

### 1. Loading Test Cases

```python
import json

def load_test_cases(filepath):
    """Load test cases from JSONL file."""
    test_cases = []
    with open(filepath, 'r') as f:
        for line in f:
            test_cases.append(json.loads(line))
    return test_cases

# Load specific benchmark
b3_cases = load_test_cases('b03_conditional_compliance_reasoning.jsonl')
print(f"Loaded {len(b3_cases)} test cases for B3")
```

### 2. Running Baseline Evaluation

```python
def evaluate_model_on_benchmark(model, test_cases):
    """Evaluate model on a benchmark."""
    results = []

    for case in test_cases:
        # Get model response
        model_response = model.generate(case['question'])

        # Evaluate based on benchmark type
        if case['benchmark_type'].startswith('B1') or \
           case['benchmark_type'].startswith('B2') or \
           case['benchmark_type'].startswith('B21'):
            # Binary evaluation
            score = binary_evaluate(model_response, case['expected_response'])
        elif case['benchmark_type'] in ['B7', 'B10', 'B14', 'B16', 'B17']:
            # Expert rubric
            score = expert_rubric_evaluate(model_response, case)
        else:
            # LLM-judge
            score = llm_judge_evaluate(model_response, case)

        results.append({
            'test_id': case['test_id'],
            'score': score,
            'model_response': model_response
        })

    return results
```

### 3. Generating Evaluation Report

```python
def generate_benchmark_report(results, benchmark_name):
    """Generate evaluation report for a benchmark."""
    scores = [r['score'] for r in results]

    report = {
        'benchmark': benchmark_name,
        'total_cases': len(results),
        'average_score': sum(scores) / len(scores),
        'pass_rate': sum(1 for s in scores if s >= 3) / len(scores),
        'score_distribution': {
            '0': sum(1 for s in scores if s == 0),
            '1': sum(1 for s in scores if s == 1),
            '2': sum(1 for s in scores if s == 2),
            '3': sum(1 for s in scores if s == 3),
            '4': sum(1 for s in scores if s == 4)
        }
    }

    return report
```

### 4. Complete Baseline Testing Pipeline

```python
import glob

def run_baseline_evaluation(model, test_suite_dir):
    """Run complete baseline evaluation across all benchmarks."""

    all_results = {}

    # Load all benchmark files
    benchmark_files = glob.glob(f"{test_suite_dir}/b*.jsonl")

    for filepath in sorted(benchmark_files):
        benchmark_name = filepath.split('/')[-1].replace('.jsonl', '')
        print(f"Evaluating {benchmark_name}...")

        # Load and evaluate
        test_cases = load_test_cases(filepath)
        results = evaluate_model_on_benchmark(model, test_cases)

        # Generate report
        report = generate_benchmark_report(results, benchmark_name)
        all_results[benchmark_name] = report

        print(f"  Average Score: {report['average_score']:.2f}")
        print(f"  Pass Rate: {report['pass_rate']*100:.1f}%")

    # Generate overall summary
    overall_avg = sum(r['average_score'] for r in all_results.values()) / len(all_results)
    print(f"\nOverall Average Score: {overall_avg:.2f}")

    return all_results
```

## Benchmark Evaluation Examples

### Example 1: Binary Evaluation (B1)

```python
def binary_evaluate(model_response, expected_response):
    """Binary evaluation for B1, B2, B21."""

    # Extract key answer (Yes/No, Compliant/Non-compliant, etc.)
    model_answer = extract_binary_answer(model_response)
    expected_answer = extract_binary_answer(expected_response)

    # Check if answers match
    if model_answer == expected_answer:
        # Check if reasoning is present and relevant
        reasoning_score = check_reasoning_quality(model_response)
        return 4 if reasoning_score > 0.8 else 3
    else:
        return 0
```

### Example 2: Expert Rubric (B10 - Risk Justification)

```python
def expert_rubric_evaluate(model_response, test_case):
    """Expert rubric evaluation for B7, B10, B14, B16, B17."""

    criteria = test_case['evaluation_criteria']

    scores = {}
    for criterion, description in criteria.items():
        # Human expert scores each criterion 0-4
        scores[criterion] = input(f"Score {criterion} (0-4): {description}\n> ")

    # Average scores across criteria
    return sum(scores.values()) / len(scores)
```

### Example 3: LLM-Judge Evaluation (B3)

```python
def llm_judge_evaluate(model_response, test_case, judge_model):
    """LLM-judge evaluation for B3, B6, B8, B9, B11, B12, B13, B15, B19, B20."""

    judge_prompt = f"""You are evaluating an LLM's response to a CCoP 2.0 compliance question.

Question: {test_case['question']}

Expected Response: {test_case['expected_response']}

Model Response: {model_response}

Evaluation Criteria:
{json.dumps(test_case['evaluation_criteria'], indent=2)}

Rate the model response on a scale of 0-4:
- 0: Completely incorrect or missing critical elements
- 1: Major errors or gaps in reasoning
- 2: Partially correct with significant issues
- 3: Mostly correct with minor issues
- 4: Excellent, meets all criteria

Provide your score and justification."""

    judge_response = judge_model.generate(judge_prompt)
    score = extract_score_from_judge_response(judge_response)

    return score
```

## Quality Assurance Checklist

Before running baseline evaluation, verify:

- [ ] All JSONL files are valid JSON (no syntax errors)
- [ ] All test_ids are unique across the suite
- [ ] All benchmark_type values match B1-B21 framework
- [ ] All clause_reference values exist in CCoP 2.0
- [ ] All difficulty values are in [low, medium, high, critical]
- [ ] All expected_response fields are 200-500 words
- [ ] All evaluation_criteria contain 3-5 specific dimensions
- [ ] All metadata includes domain (IT/OT/Both)

### Validation Script

```python
def validate_test_suite(test_suite_dir):
    """Validate test suite integrity."""

    all_test_ids = set()
    issues = []

    for filepath in glob.glob(f"{test_suite_dir}/b*.jsonl"):
        with open(filepath, 'r') as f:
            for i, line in enumerate(f, 1):
                try:
                    case = json.loads(line)

                    # Check required fields
                    required_fields = ['test_id', 'benchmark_type', 'question',
                                     'expected_response', 'evaluation_criteria']
                    for field in required_fields:
                        if field not in case:
                            issues.append(f"{filepath}:{i} - Missing {field}")

                    # Check test_id uniqueness
                    if case['test_id'] in all_test_ids:
                        issues.append(f"{filepath}:{i} - Duplicate test_id: {case['test_id']}")
                    all_test_ids.add(case['test_id'])

                    # Check expected_response length
                    word_count = len(case['expected_response'].split())
                    if word_count < 100:
                        issues.append(f"{filepath}:{i} - Expected response too short ({word_count} words)")

                except json.JSONDecodeError as e:
                    issues.append(f"{filepath}:{i} - Invalid JSON: {e}")

    if issues:
        print(f"Found {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Test suite validation passed!")

    return len(issues) == 0
```

## Benchmark-Specific Guidance

### High-Impact Benchmarks (Priority for Baseline)

#### B3: Conditional Compliance Reasoning
**Focus**: Nuanced scenarios with compensating controls, edge cases
**Key Challenge**: Distinguishing when compensating controls satisfy requirements vs when they don't
**Scoring Focus**: Accuracy in identifying compliance status + quality of reasoning

#### B9-B11: Risk Reasoning Suite
**Focus**: Risk identification → justification → severity assessment
**Key Challenge**: Structured, coherent risk argumentation
**Scoring Focus**: Cause-effect reasoning chains, proportional severity ratings

#### B12: Audit Perspective Alignment
**Focus**: CSA auditor reasoning patterns
**Key Challenge**: Understanding audit mindset (evidence-based, skeptical, outcome-focused)
**Scoring Focus**: Alignment with regulatory interpretation, not just technical correctness

#### B14: Remediation Recommendation Quality
**Focus**: Practical, phased, costed remediation plans
**Key Challenge**: Balancing urgency, feasibility, resource constraints
**Scoring Focus**: Actionability, risk prioritization, realistic timelines

### Singapore-Specific Context

Test cases incorporate Singapore regulatory environment:

- **CIIO (CII Owner)**: Organizations designated by Commissioner
- **CSA (Cyber Security Agency)**: Regulatory authority and auditor
- **Commissioner of Cybersecurity**: Authority under Cybersecurity Act 2018
- **Essential Services**: 11 sectors (energy, water, healthcare, transport, etc.)
- **Digital Boundary**: Scope of CII systems subject to CCoP
- **CCoP 2.0 Sections**: 10 sections (Governance, Risk Management, Protection, Detection, etc.)

## Integration with Research Pipeline

### Phase 2 Workflow

1. **Baseline Evaluation** (Current Phase)
   - Run Llama-Primus-Reasoning on all 20 benchmarks
   - Run DeepSeek-R1 on all 20 benchmarks
   - Document baseline scores (this test suite)

2. **Fine-Tuning Preparation** (Next Phase)
   - Prepare training dataset aligned with benchmarks
   - Define fine-tuning hyperparameters (QLoRA)

3. **Post-Fine-Tuning Evaluation**
   - Re-run same test suite on fine-tuned models
   - Compare baseline vs post-fine-tuning scores

4. **Analysis & Publication**
   - Calculate improvement deltas per benchmark
   - Identify high-impact vs low-impact benchmarks
   - Generate research findings

### Expected Baseline Performance

Based on domain-specific LLM research:

- **Generic LLMs** (e.g., base Llama): 30-45% accuracy on specialized compliance tasks
- **Cybersecurity LLMs** (e.g., Llama-Primus-Reasoning): 50-65% baseline
- **Post-Fine-Tuning Target**: 85%+ accuracy (enterprise compliance threshold)

**Hypotheses**:
- High-impact benchmarks (B3, B9-B11, B14) should show >20% improvement
- Foundation benchmarks (B1, B5) should show moderate improvement (10-15%)
- Consistency benchmarks (B19, B20) should show significant improvement (15-25%)

## Troubleshooting

### Common Issues

**Issue**: JSONL parsing errors
**Solution**: Validate JSON with `python -m json.tool < file.jsonl`

**Issue**: LLM-judge scores inconsistent
**Solution**: Use temperature=0 for deterministic evaluation, run multiple times and average

**Issue**: Expected responses too generic
**Solution**: This suite provides 200-500 word detailed expected responses with specific CCoP clauses

**Issue**: Model outputs vary wildly
**Solution**: Use consistent prompting template, include few-shot examples if needed

## References

### Regulatory Documents
- [CCoP 2.0 Official PDF](https://isomer-user-content.by.gov.sg/36/2df750a7-a3bc-4d77-a492-d64f0ff4db5a/CCoP---SecondEdition_Revision-One.pdf)
- [Singapore Cybersecurity Act 2018 Part 3](https://sso.agc.gov.sg/Act/CSA2018)
- [CSA Codes of Practice](https://www.csa.gov.sg/legislation/codes-of-practice)

### Research Papers
- [Llama-Primus-Reasoning Model](https://huggingface.co/trendmicro-ailab/Llama-Primus-Reasoning)
- [LalaEval: Human Evaluation for Domain-Specific LLMs](https://arxiv.org/abs/2408.13338)

### Project Documentation
- `report/term1-end/benchmarks-updated.md` - Complete benchmark framework
- `docs/phase1/phase1-user-story.md` - Phase 1 functional requirements
- `TEST_SUITE_COMPLETION_REPORT.md` - Generation report and status

## Support

For questions or issues:
- Review `TEST_SUITE_COMPLETION_REPORT.md` for generation details
- Check `benchmark-mapping.md` for old→new framework mapping
- Refer to `report/term1-end/benchmarks-updated.md` for benchmark definitions

## License

This test suite is part of academic research on fine-tuning LLMs for Singapore CCoP 2.0 compliance assessment.

---

**Version**: 1.0
**Last Updated**: December 14, 2025
**Status**: ✅ Ready for Baseline Evaluation
