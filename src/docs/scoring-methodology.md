# Scoring Methodology

## Overview

This document describes the evaluation and scoring methodology used to assess model performance on CCoP 2.0 benchmarks. The scoring system evaluates model responses against ground-truth test cases using benchmark-specific metrics.

## Evaluation Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. Load Test Case                                                      │
│    - Question: The prompt sent to the model                            │
│    - Expected Response: Ground-truth answer                            │
│    - Evaluation Criteria: Benchmark-specific requirements              │
└────────────────────────────┬────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. Generate Model Response                                             │
│    - System Prompt: "You are a cybersecurity compliance expert..."     │
│    - Model generates response via Ollama API                           │
│    - Captures: response content, tokens used, latency                  │
└────────────────────────────┬────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. Score Response (Benchmark-Specific)                                 │
│    - Apply benchmark-specific scoring function                         │
│    - Calculate multiple metrics (accuracy, completeness, etc.)         │
│    - Each metric has a value (0.0-1.0) and weight                     │
└────────────────────────────┬────────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. Calculate Final Score                                               │
│    - Weighted average of all metrics                                   │
│    - Pass/Fail determination (threshold: 70%)                          │
│    - Save result to JSON file                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Scoring Formula

### Weighted Average Score

For each test case, the overall score is calculated as a weighted average of all metrics:

```
Overall Score = Σ(metric.value × metric.weight) / Σ(metric.weight)
```

Where:
- `metric.value`: Metric score between 0.0 and 1.0
- `metric.weight`: Importance weight of the metric

**Example:**
```
Metrics:
  - Accuracy: value=0.85, weight=1.0
  - Completeness: value=0.90, weight=0.8

Score = (0.85 × 1.0 + 0.90 × 0.8) / (1.0 + 0.8)
      = (0.85 + 0.72) / 1.8
      = 1.57 / 1.8
      = 0.872 (87.2%)
```

### Pass/Fail Threshold

```python
PASS_THRESHOLD = 0.70  # 70%

if overall_score >= 0.70:
    status = "PASSED" ✅
else:
    status = "FAILED" ❌
```

**Rationale**: The 70% threshold is based on:
- Industry standards for AI compliance systems (Thomson Reuters research: 85% accuracy requirement)
- US GSA CUI Protection Guide threshold
- Phase 1 baseline establishment requirements

## Benchmark-Specific Scoring

Different benchmarks use different scoring methodologies based on what they're testing:

### B1: CCoP Applicability & Scope

**Metrics:**
1. **Accuracy** (weight: 1.0)
   - Measures semantic similarity to expected response
   - Uses Jaccard similarity (word overlap)
2. **Completeness** (weight: 0.8)
   - Measures coverage of key points
   - Checks if major concepts are mentioned

**Implementation:** `ScoringService._score_b1_interpretation()`

### B2: Compliance Classification Accuracy

**Metrics:**
1. **Citation Accuracy** (weight: 1.0)
   - Verifies correct section/clause references
   - Exact match: 1.0, Partial match: 0.7, Wrong: 0.0
2. **Accuracy** (weight: 1.0)
   - Basic semantic similarity

**Implementation:** `ScoringService._score_b2_citation()`

### B3: Conditional Compliance Reasoning

**Metrics:**
1. **Hallucination Rate** (weight: 1.0)
   - Detects fabricated information
   - Penalizes responses with hallucination indicators
2. **Accuracy** (weight: 1.0)
   - Reduced accuracy if hallucinations detected

**Implementation:** `ScoringService._score_b3_hallucination()`

### B4: Singapore Terminology Accuracy

**Metrics:**
1. **Terminology Accuracy** (weight: 1.0)
   - Checks usage of Singapore-specific terms
   - Score = (found_terms / total_expected_terms)
2. **Accuracy** (weight: 1.0)
   - Basic semantic similarity

**Implementation:** `ScoringService._score_b4_terminology()`

### B5: IT/OT Classification

**Metrics:**
1. **Classification Accuracy** (weight: 1.0)
   - Verifies correct IT/OT domain identification
   - Exact match: 1.0, Partial: 0.7, Wrong: 0.0
2. **Accuracy** (weight: 1.0)
   - Basic semantic similarity

**Implementation:** `ScoringService._score_b5_classification()`

### B6: Code Violation Detection

**Metrics:**
1. **Violation Detection** (weight: 1.0)
   - Measures detection of security violations
   - Score = (detected_violations / expected_violations)
2. **Completeness** (weight: 0.8)
   - Checks if code analysis is included

**Implementation:** `ScoringService._score_b6_violation_detection()`

### B7-B21: General Scoring

For benchmarks without specific scoring functions, uses basic accuracy metric.

**Implementation:** `ScoringService._calculate_basic_accuracy()`

## Core Metric Calculations

### 1. Accuracy (Jaccard Similarity)

Measures word overlap between expected and actual responses.

```python
def calculate_accuracy(expected: str, actual: str) -> float:
    # Extract words (alphanumeric tokens)
    expected_words = set(re.findall(r'\w+', expected.lower()))
    actual_words = set(re.findall(r'\w+', actual.lower()))

    # Calculate Jaccard similarity
    intersection = len(expected_words & actual_words)
    union = len(expected_words | actual_words)

    return intersection / union if union > 0 else 0.0
```

**Example:**
```
Expected: "The Commissioner designates CII systems"
Actual: "The Commissioner identifies critical infrastructure"

expected_words = {the, commissioner, designates, cii, systems}
actual_words = {the, commissioner, identifies, critical, infrastructure}

intersection = {the, commissioner} = 2 words
union = {the, commissioner, designates, cii, systems, identifies, critical, infrastructure} = 8 words

accuracy = 2/8 = 0.25 (25%)
```

**Strengths:**
- Simple and interpretable
- Punishes verbose responses with many irrelevant words
- Language-agnostic

**Weaknesses:**
- Doesn't understand synonyms (e.g., "designate" vs "identify")
- Doesn't capture semantic meaning
- Sensitive to response length

### 2. Completeness

Measures coverage of key points from expected response.

```python
def calculate_completeness(expected: str, actual: str) -> float:
    # Split expected into sentences
    sentences = re.split(r'[.!?]', expected)

    covered_points = 0
    for sentence in sentences:
        # Extract key words (length > 4)
        key_words = [w for w in re.findall(r'\w+', sentence.lower()) if len(w) > 4]

        # Check if any key word appears in actual response
        if any(word in actual.lower() for word in key_words):
            covered_points += 1

    return covered_points / len(sentences) if sentences else 0.0
```

**Example:**
```
Expected: "The Commissioner may designate a computer system as CII.
           The system must be necessary for essential services.
           It must be located in Singapore."

Sentences = 3
Actual mentions: "essential services" ✓, "Singapore" ✓, but not "designate" ✗

covered_points = 2
completeness = 2/3 = 0.67 (67%)
```

### 3. Citation Accuracy

Verifies correct legal references (B2 benchmark).

```python
def calculate_citation_accuracy(expected_citation: str, actual_citations: list) -> float:
    if expected_citation in actual_citations:
        return 1.0  # Exact match
    elif any(expected_citation in cite for cite in actual_citations):
        return 0.7  # Partial match
    else:
        return 0.0  # Not cited
```

**Example:**
```
Expected: "Section 7(1)"
Actual: ["Section 7(1)", "Section 11"]

citation_accuracy = 1.0 (100%) ✓
```

### 4. Hallucination Detection

Identifies fabricated information (B3 benchmark).

```python
def detect_hallucination(response: str) -> bool:
    hallucination_indicators = [
        "i think", "i believe", "probably", "maybe",
        "i'm not sure", "it seems", "appears to be"
    ]

    response_lower = response.lower()
    return any(indicator in response_lower for indicator in hallucination_indicators)
```

If hallucination detected:
- Hallucination rate = 1.0
- Accuracy capped at 0.5 (50% penalty)

## Actual Results Example (B1 Benchmark)

### Test Case: B1-001

**Question:**
"What are the criteria that the Commissioner uses to designate a computer or computer system as Critical Information Infrastructure (CII) under the Cybersecurity Act 2018?"

**Expected Response:**
"According to Section 7(1) of the Cybersecurity Act 2018, the Commissioner may designate a computer or computer system as CII if two criteria are satisfied: (a) the computer or computer system is necessary for the continuous delivery of an essential service, and the loss or compromise of the computer or computer system will have a debilitating effect on the availability of the essential service in Singapore; and (b) the computer or computer system is located wholly or partly in Singapore."

**Model Response (primus-reasoning):**
"Okay, let me try to recall the key points here. So, the Cybersecurity Act 2018 in Singapore introduced the concept of Critical Information Infrastructures (CCIs). The Commissioner, who's part of the Cyber Security Agency (CSA), uses certain criteria to designate systems as CCI. From what I remember, the Commissioner considers several factors when determining whether a computer system or network should be designated as a CII..."

**Scoring:**
```
Metrics:
  - Accuracy: 0.134 (13.4%) - Low word overlap, many incorrect/extra words
  - Completeness: 1.0 (100%) - Mentioned most key concepts

Overall Score = (0.134 × 1.0 + 1.0 × 0.8) / (1.0 + 0.8)
              = (0.134 + 0.8) / 1.8
              = 0.934 / 1.8
              = 0.519 (51.9%)

Status: FAILED ❌ (below 70% threshold)
```

**Issues Identified:**
1. **Hallucination**: Model fabricates "several factors" not in ground truth
2. **Wrong terminology**: Says "CCI" instead of "CII"
3. **Verbose**: 512 tokens vs expected concise answer
4. **Missing specifics**: Doesn't cite Section 7(1) explicitly

### Benchmark Summary (B1)

| Test ID | Accuracy | Completeness | Score | Status | Issue |
|---------|----------|--------------|-------|--------|-------|
| B1-001 | 13.4% | 100% | 51.9% | ❌ | Hallucinated criteria |
| B1-002 | 22.5% | 88.9% | 52.0% | ❌ | Confused CII/Essential Services |
| B1-003 | 17.8% | 100% | 54.4% | ❌ | Wrong CIIO definition |
| B1-004 | 21.5% | 81.8% | 48.3% | ❌ | Incorrect scope |
| B1-005 | 20.2% | 100% | 55.7% | ❌ | Generic answer |
| B1-006 | 14.5% | 28.6% | 20.7% | ❌ | Refused to answer |
| B1-007 | 17.3% | 80.0% | 45.2% | ❌ | Wrong definition |
| B1-008 | 28.0% | 82.4% | 52.2% | ❌ | Verbose |

**Overall B1 Score: 47.54%** (0/8 passed)

## Interpreting Results

### Score Ranges

| Range | Interpretation | Action |
|-------|----------------|--------|
| 90-100% | Excellent | Model ready for production |
| 70-89% | Good | Minor fine-tuning needed |
| 50-69% | Moderate | Significant fine-tuning needed |
| 30-49% | Poor | Major fine-tuning required |
| 0-29% | Critical | Complete retraining needed |

### Common Failure Patterns

1. **Low Accuracy + High Completeness**
   - **Symptom**: Score ~40-60%
   - **Cause**: Model is verbose, includes correct concepts but with many extra/wrong words
   - **Example**: B1-001 (13.4% accuracy, 100% completeness)
   - **Fix**: Fine-tune with concise, precise answers

2. **Low Accuracy + Low Completeness**
   - **Symptom**: Score <30%
   - **Cause**: Model doesn't understand the question or refuses to answer
   - **Example**: B1-006 (14.5% accuracy, 28.6% completeness)
   - **Fix**: Improve instruction-following and domain knowledge

3. **Hallucination**
   - **Symptom**: Model fabricates facts
   - **Cause**: Lack of domain-specific training data
   - **Example**: B1-003 (wrong CIIO definition)
   - **Fix**: Fine-tune on authoritative CCoP 2.0 documents

## Limitations & Future Improvements

### Current Limitations

1. **Lexical Similarity Only**
   - Jaccard similarity doesn't understand semantics
   - Synonyms are not recognized as correct
   - Example: "designate" vs "identify" scored as different

2. **No Semantic Understanding**
   - Cannot evaluate logical correctness
   - May accept grammatically similar but factually wrong answers

3. **Language Dependency**
   - Only works for English text
   - Case-sensitive for certain patterns

4. **Manual Threshold**
   - 70% threshold is based on industry standards
   - May need adjustment based on benchmark difficulty

### Planned Improvements

1. **Semantic Similarity**
   - Add BERT-based semantic similarity scoring
   - Use embeddings for meaning comparison
   - Example: SentenceTransformers cosine similarity

2. **LLM-as-Judge**
   - Use Claude/GPT-4 to evaluate responses
   - Provide rubric-based scoring
   - Better handling of paraphrasing

3. **Citation Extraction**
   - Improved regex for legal references
   - Validate section numbers against CCoP 2.0

4. **Multi-dimensional Scoring**
   - Add factual accuracy dimension
   - Add legal precision dimension
   - Add response conciseness dimension

## References

- **Source Code**: `src/domain/services/scoring_service.py`
- **Evaluation Flow**: `src/application/use_cases/evaluate_model.py`
- **Metric Definitions**: `src/domain/value_objects/evaluation_metric.py`
- **Results Format**: `src/infrastructure/adapters/repositories/json_result_repository.py`

## Appendix: Metric Weights

| Benchmark | Metric 1 | Weight | Metric 2 | Weight |
|-----------|----------|--------|----------|--------|
| B1 | Accuracy | 1.0 | Completeness | 0.8 |
| B2 | Citation Accuracy | 1.0 | Accuracy | 1.0 |
| B3 | Hallucination Rate | 1.0 | Accuracy | 1.0 |
| B4 | Terminology Accuracy | 1.0 | Accuracy | 1.0 |
| B5 | Classification Accuracy | 1.0 | Accuracy | 1.0 |
| B6 | Violation Detection | 1.0 | Completeness | 0.8 |
| B7-B21 | Accuracy | 1.0 | - | - |

---

**Document Version**: 1.0
**Last Updated**: 2025-12-14
**Author**: CCoP Evaluation Framework
