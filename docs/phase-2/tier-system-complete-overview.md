# Complete Tier System Overview
**CCoP 2.0 Evaluation Framework - Phase 2 Baseline Evaluation**

---

## ⚠️ Critical Framing: Target Design vs. Current Implementation

**This document describes the target evaluation methodology.** Phase 2 baseline evaluation represents a **partial implementation** for pipeline validation and relative performance measurement:

- ✅ **Fully Implemented:** Tier 1 (B1, B2, B21)
- ⚠️ **Partially Implemented:** Reasoning Track (B3-B6 only)
- ❌ **Not Implemented:** Tier 2, Tier 3, B7-B20

**Lexical fallbacks (Jaccard similarity) are used for B7-B20 as diagnostic placeholders only.** These scores **do not measure reasoning quality, audit alignment, or regulatory intent** and should **not** be interpreted as valid performance indicators. They serve to:
1. Exercise the full evaluation pipeline
2. Establish baseline infrastructure for future implementation
3. Enable relative comparison across model iterations (if consistently applied)

**Phase 2 evaluation focuses on relative improvement trends for fine-tuning validation, not absolute benchmark scores.**

---

## 1. Tier System Architecture

The evaluation framework uses a **4-tier hybrid scoring system** that balances automation, expert judgment, and scalability. This tiering reflects how compliance knowledge is validated in real CCoP 2.0 audits.

---

## 2. Tier Definitions & Benchmark Mapping

### **Tier 1: Binary Metrics (Automated / Rule-Based)**

**Purpose:** Objective evaluation for classification and detection tasks with clear right/wrong answers

**Benchmarks:**
- **B1**: CCoP Applicability & Core Terminology ✅ **Implemented**
- **B2**: Compliance Classification Accuracy ✅ **Implemented**
- **B21**: Regulatory Hallucination Rate ✅ **Implemented**

**Scoring Method:**
- Binary (correct/incorrect) or multi-level discrete classification (0.0, 0.7, 1.0)
- Label-based accuracy using expected classification labels
- Rule-based pattern matching

**Key Metrics:**
1. **Accuracy**: Exact or partial match of expected label components
   - Exact match: 1.0
   - Partial match (≥60% components): 0.7
   - Incorrect: 0.0

2. **Completeness**: Key-fact recall using 60% term matching threshold
   ```
   Completeness = covered_facts / total_facts
   ```

3. **Grounding**: Safety check detecting fabricated CCoP claims
   - No violations: 1.0
   - 1-2 violations: 0.7
   - 3+ violations: 0.0

**Inter-rater Reliability:** Not required (deterministic automated scoring)

**Automation Level:** 100% automated

---

### **Tier 2: Expert Rubric Metrics (Human-Scored)**

**Purpose:** Subjective quality assessment for complex analytical tasks requiring expert judgment

**Benchmarks:**
- **B7**: Gap Identification Quality
- **B10**: Risk Justification Coherence
- **B14**: Remediation Recommendation Quality
- **B16**: Residual Risk Awareness

**Scoring Method:**
- Structured 1-5 scale rubric evaluated by domain experts (cybersecurity compliance auditors)
- Each response rated across 4 dimensions

**Scoring Dimensions:**
1. **Accuracy** (Weight: 1.0)
   - Technical correctness of compliance interpretation
   - Scale: 1 (incorrect) to 5 (fully accurate)

2. **Completeness** (Weight: 0.8)
   - Coverage of all relevant control requirements
   - Scale: 1 (major gaps) to 5 (comprehensive)

3. **Practicality** (Weight: 0.8)
   - Feasibility of recommendations for real-world CII implementation
   - Scale: 1 (unrealistic) to 5 (highly practical)

4. **Clarity** (Weight: 0.6)
   - Professional communication quality and actionability
   - Scale: 1 (unclear) to 5 (crystal clear)

**Scoring Formula:**
```
Overall Score = (Accuracy×1.0 + Completeness×0.8 + Practicality×0.8 + Clarity×0.6) / 3.2
Normalized to 0-1 range: Overall Score / 5
```

**Inter-rater Reliability:**
- Requires ≥80% agreement among expert raters
- Cohen's kappa ≥ 0.60 for inter-rater reliability
- Minimum 2 expert raters per response
- Adjudication by third expert if disagreement >20%

**Automation Level:** 0% automated (manual expert review required)

---

### **Tier 3: LLM-as-Judge + Human Validation**

**Purpose:** Scalable evaluation for nuanced reasoning tasks where automated metrics fail but full expert review is cost-prohibitive

**Benchmarks:**
- **B12**: Audit Perspective Alignment
- **B13**: Evidence Expectation Awareness
- **B20**: Over-Specification Avoidance

**Scoring Method:**
- Structured rubric applied by LLM judge (GPT-4, Claude Opus, or equivalent)
- Mandatory human validation on random sample

**Process:**
1. **Step 1 - LLM Evaluation (100% of responses)**
   - LLM judge receives response + test case + detailed rubric
   - LLM scores response on 1-5 scale with written justification
   - Captures LLM reasoning in structured format

2. **Step 2 - Human Validation (≥20% random sample)**
   - Expert randomly samples ≥20% of LLM-judged responses
   - Expert re-evaluates independently without seeing LLM score
   - Records agreement/disagreement

3. **Step 3 - Calibration (if agreement <80%)**
   - If human-LLM agreement <80%, recalibrate judge prompts
   - Adjust rubric clarity or add examples
   - Re-run LLM evaluation on full dataset
   - Repeat validation until ≥80% agreement

**Scoring Criteria:** (Similar to Tier 2)
- Accuracy (1-5)
- Completeness (1-5)
- Alignment with audit practice (1-5)

**Human Override:** Expert can override LLM score if confidence <0.8

**Inter-rater Reliability:** ≥80% human-LLM agreement required

**Automation Level:** ~80% automated (LLM primary, human validation secondary)

---

### **Reasoning Track: Lexical-Proxy Reasoning + Key-Fact Recall**

**Purpose:** Automated evaluation for compliance reasoning tasks using lexical similarity as a proxy for semantic understanding

**⚠️ Terminology Clarification:** This track is labeled "Semantic + Key-Fact Recall" in architecture diagrams for aspirational clarity, but the **current implementation uses lexical Jaccard similarity**, not true semantic similarity. True semantic similarity (using sentence embeddings, cosine similarity) is deferred to Phase 3+.

**Benchmarks:**
- **B3**: Conditional Compliance Reasoning
- **B4**: Scenario-to-Control Mapping
- **B5**: Control Requirement Comprehension
- **B6**: Control Intent Understanding
- **B8**: Gap Prioritisation
- **B9**: Risk Identification Accuracy
- **B11**: Risk Severity Assessment
- **B15**: Remediation Feasibility
- **B17**: Policy vs Practice Distinction
- **B18**: Responsibility Attribution (Singapore-Specific)
- **B19**: Cross-Scenario Consistency

**Scoring Method:**
Hybrid approach combining semantic similarity and structured fact verification

**Key Metrics:**

1. **Lexical Similarity (Jaccard Word Overlap)**
   ```
   expected_words = set(words in expected_response)
   response_words = set(words in actual_response)

   accuracy = |expected_words ∩ response_words| / |expected_words ∪ response_words|
   ```

   **⚠️ Important Limitations:**
   - **Does NOT measure semantic meaning** - only counts shared words
   - **Misses synonyms:** "organization" ≠ "entity", "applies" ≠ "required"
   - **No understanding of regulatory intent** - "CCoP applies to CII" vs "CCoP requires CII security" → different scores despite equivalent meaning
   - **Can produce high scores for wrong answers** if phrasing overlaps
   - **Can produce low scores for correct answers** if paraphrased differently

   **Why it's used:** Computational efficiency for baseline screening. Validity limited to B3-B6 where specialized logic supplements lexical matching.

2. **Key-Fact Recall**
   ```
   For each fact in key_facts:
       key_terms = [words > 4 chars]
       if (matched_terms / total_terms) ≥ 0.6:
           covered_facts += 1

   completeness = covered_facts / total_key_facts
   ```

3. **Grounding Check**
   - Same as Tier 1: detects forbidden claims and hallucination patterns

**Overall Score Formula:**
```
Overall Score = Σ(metric.value × metric.weight) / Σ(metric.weight)

Default weights:
- accuracy: 1.0
- completeness: 0.8
- grounding: 1.0

Example:
Overall = (0.45×1.0 + 0.67×0.8 + 1.0×1.0) / (1.0 + 0.8 + 1.0)
        = (0.45 + 0.536 + 1.0) / 2.8
        = 1.986 / 2.8
        = 0.709 (70.9%)
```

**Inter-rater Reliability:** Not applicable (deterministic automated scoring)

**Automation Level:** 100% automated

---

## 3. Implementation Status

### **✅ IMPLEMENTED (Tier 1 Partial + Reasoning Track Partial)**

| Benchmark | Tier/Track | Implementation | Status |
|-----------|-----------|----------------|--------|
| **B1** | Tier 1 | Label-based accuracy + key-fact recall + grounding | ✅ Complete |
| **B2** | Tier 1 | Citation matching (exact/partial) + Jaccard | ✅ Complete |
| **B3** | Reasoning Track | Hallucination detection + Jaccard | ✅ Complete |
| **B4** | Reasoning Track | Terminology coverage ratio + Jaccard | ✅ Complete |
| **B5** | Reasoning Track | IT/OT classification (multi-level) + Jaccard | ✅ Complete |
| **B6** | Reasoning Track | Violation detection coverage + code snippet check | ✅ Complete |

**Code Location:** `src/domain/services/scoring_service.py` lines 54-237

**How It Works:**
```python
benchmark_scorers = {
    "B1": ScoringService._score_b1_interpretation,
    "B2": ScoringService._score_b2_citation,
    "B3": ScoringService._score_b3_hallucination,
    "B4": ScoringService._score_b4_terminology,
    "B5": ScoringService._score_b5_classification,
    "B6": ScoringService._score_b6_violation_detection,
}

for benchmark_key, scorer in benchmark_scorers.items():
    if test_case.benchmark_type == benchmark_key:
        return scorer(test_case, response)
```

---

### **❌ NOT IMPLEMENTED (Tier 1 Partial, Tier 2, Tier 3, Reasoning Track Partial)**

| Benchmark | Tier/Track | Intended Method | Current Fallback |
|-----------|-----------|-----------------|------------------|
| **B7** | Tier 2 | Expert rubric (1-5 scale, 4 dimensions) | ❌ Jaccard similarity |
| **B8** | Reasoning Track | Semantic + key-fact recall | ❌ Jaccard similarity |
| **B9** | Reasoning Track | Semantic + key-fact recall | ❌ Jaccard similarity |
| **B10** | Tier 2 | Expert rubric (1-5 scale, 4 dimensions) | ❌ Jaccard similarity |
| **B11** | Reasoning Track | Semantic + key-fact recall | ❌ Jaccard similarity |
| **B12** | Tier 3 | LLM-as-Judge + human validation | ❌ Jaccard similarity |
| **B13** | Tier 3 | LLM-as-Judge + human validation | ❌ Jaccard similarity |
| **B14** | Tier 2 | Expert rubric (1-5 scale, 4 dimensions) | ❌ Jaccard similarity |
| **B15** | Reasoning Track | Semantic + key-fact recall | ❌ Jaccard similarity |
| **B16** | Tier 2 | Expert rubric (1-5 scale, 4 dimensions) | ❌ Jaccard similarity |
| **B17** | Reasoning Track | Semantic + key-fact recall | ❌ Jaccard similarity |
| **B18** | Reasoning Track | Semantic + key-fact recall | ❌ Jaccard similarity |
| **B19** | Reasoning Track | Semantic + key-fact recall | ❌ Jaccard similarity |
| **B20** | Tier 3 | LLM-as-Judge + human validation | ❌ Jaccard similarity |
| **B21** | Tier 1 | Binary hallucination detection | ❌ Jaccard similarity |

**Fallback Code:** `src/domain/services/scoring_service.py` line 68
```python
# Fallback: basic scoring for B7-B21 and unknown types
return [ScoringService._calculate_basic_accuracy(test_case, response)]
```

**Why Not Implemented:**
- **Tier 2 (Expert Rubric):** Requires actual human expert time, expensive and slow
- **Tier 3 (LLM-Judge):** Requires commercial LLM API access (GPT-4/Claude) and validation infrastructure
- **B8-B19 (Reasoning Track):** Awaiting completion of automated semantic similarity infrastructure
- **B21 (Tier 1):** Should use same logic as B3 but not implemented yet

---

## 4. Score Computation Examples

### **Example 1: B1 Test Case (Tier 1 - Implemented)**

**Input:**
- Question: "Does CCoP apply to this hospital system?"
- Expected Label: "Two criteria: essential service delivery + Singapore location"
- Key Facts: ["Essential service requirement", "Singapore location requirement"]
- Forbidden Claims: ["cryptography officer", "CIIO stands for Cryptography"]

**Model Response:**
"CCoP 2.0 applies to Critical Information Infrastructure that delivers essential services and is located in Singapore."

**Scoring:**
1. **Accuracy (label-based):**
   - Expected: "essential service delivery + Singapore location"
   - Response contains: "essential services" ✓, "located in Singapore" ✓
   - All components present → **1.0**

2. **Completeness (key-fact recall):**
   - Fact 1: "Essential service requirement" → key terms: ["essential", "service", "requirement"]
     - Matched: "essential", "service" → 2/3 = 67% ≥ 60% ✓
   - Fact 2: "Singapore location requirement" → key terms: ["singapore", "location", "requirement"]
     - Matched: "singapore", "located" → 2/3 = 67% ≥ 60% ✓
   - Coverage: 2/2 = **1.0**

3. **Grounding:**
   - Check forbidden claims: "cryptography officer" not found ✓, "CIIO stands for Cryptography" not found ✓
   - No hallucinations detected → **1.0**

**Overall Score:**
```
Overall = (1.0×1.0 + 1.0×0.8 + 1.0×1.0) / (1.0 + 0.8 + 1.0)
        = (1.0 + 0.8 + 1.0) / 2.8
        = 2.8 / 2.8
        = 1.0 (100%) ✓ PASS
```

---

### **Example 2: B7 Test Case (Tier 2 - NOT Implemented)**

**Input:**
- Question: "What control gaps exist in this cloud configuration?"
- Expected: Detailed gap analysis with specific control references

**Model Response:**
"The setup lacks multi-factor authentication (CCoP 10.1.2), insufficient logging (CCoP 12.2.1), and no encryption for data at rest (CCoP 9.3.4)."

**Intended Scoring (Tier 2 Expert Rubric):**

**Expert Rater 1:**
- Accuracy: 4/5 (correct controls but minor interpretation issue)
- Completeness: 3/5 (missed network segmentation gap)
- Practicality: 5/5 (all recommendations are feasible)
- Clarity: 4/5 (clear but could be more structured)

**Expert Rater 2:**
- Accuracy: 4/5
- Completeness: 4/5 (good coverage, one minor gap)
- Practicality: 5/5
- Clarity: 5/5

**Average:**
```
Accuracy = (4+4)/2 = 4.0
Completeness = (3+4)/2 = 3.5
Practicality = (5+5)/2 = 5.0
Clarity = (4+5)/2 = 4.5

Overall = (4.0×1.0 + 3.5×0.8 + 5.0×0.8 + 4.5×0.6) / 3.2
        = (4.0 + 2.8 + 4.0 + 2.7) / 3.2
        = 13.5 / 3.2
        = 4.22 / 5
        = 0.844 (84.4%) ✓ PASS
```

**Current Fallback (Jaccard Similarity):**
```
Expected words: {setup, lacks, multi, factor, authentication, ccop, insufficient, ...}
Response words: {setup, lacks, multi, factor, authentication, ccop, insufficient, ...}

Intersection: ~30 words
Union: ~45 words

Jaccard = 30/45 = 0.67 (67%) ✓ PASS (but score is inaccurate)
```

**Problem:** Jaccard doesn't measure quality, practicality, or audit alignment - it just counts word overlap.

---

### **Example 3: B12 Test Case (Tier 3 - NOT Implemented)**

**Input:**
- Question: "How would a CSA auditor assess this incident response plan?"
- Expected: Audit-perspective evaluation showing understanding of CSA's evaluation framework

**Model Response:**
"A CSA auditor would verify that the plan addresses CCoP 13.1 requirements, includes incident classification criteria aligned with Section 15 of the Cybersecurity Act, demonstrates appropriate escalation procedures to the Commissioner for CII disruptions, and ensures evidence retention for forensic analysis."

**Intended Scoring (Tier 3 LLM-Judge):**

**LLM Judge (GPT-4) Evaluation:**
```
Rubric Criteria:
1. Audit perspective authenticity (1-5): 5
   - Correctly identifies CSA's focus on regulatory compliance
   - Mentions Commissioner escalation (accurate for CII)

2. Evidence awareness (1-5): 4
   - Mentions evidence retention
   - Could elaborate on specific audit artifacts

3. Completeness (1-5): 4
   - Covers key audit concerns
   - Missing continuous improvement aspect

LLM Score: (5+4+4)/3 = 4.33/5 = 0.866 (86.6%)
```

**Human Validation (20% sample - 1 expert checks):**
```
Expert re-evaluation:
1. Audit perspective: 5/5 ✓ (agrees with LLM)
2. Evidence awareness: 4/5 ✓ (agrees with LLM)
3. Completeness: 3/5 ✗ (expert thinks missing incident categorization)

Agreement: 2/3 = 67% < 80% → Needs calibration
```

**Calibration Action:**
- Add example showing importance of incident categorization
- Re-run LLM judge on full dataset
- Validate new sample until ≥80% agreement

**Current Fallback (Jaccard):**
- Just word overlap → doesn't capture audit perspective quality

---

## 5. Tier Comparison Matrix

| Feature | Tier 1 | Tier 2 | Tier 3 | Reasoning Track |
|---------|--------|--------|--------|----------------|
| **Automation** | 100% | 0% | ~80% | 100% |
| **Cost** | $0 | High ($50-100/hr expert) | Medium (API + validation) | $0 |
| **Scalability** | Unlimited | Low (~10 cases/day/expert) | High (~1000 cases/day) | Unlimited |
| **Accuracy** | High (for classification) | Very High (expert judgment) | High (with validation) | Medium (lexical only) |
| **Inter-rater Reliability** | N/A (deterministic) | ≥80% required | ≥80% required | N/A |
| **Turnaround** | Instant | 1-2 days | Minutes-hours | Instant |
| **Use Case** | Binary decisions | Quality assessment | Nuanced reasoning at scale | Compliance reasoning |
| **Implementation Status** | Partial (2/3) | None (0/4) | None (0/3) | Partial (4/11) |

---

## 6. Key Limitations & Methodological Risks

### **Phase 2 Baseline: Implementation Limitations vs. Design Limitations**

**The tier system design is sound.** The weakness lies in the gap between intended scoring methods and current fallbacks. This creates **methodological risk** that must be clearly scoped to avoid score misinterpretation.

---

### **Critical Limitation 1: Jaccard Fallback Creates Directionally Misleading Scores**

**Affected Benchmarks:** B7-B21 (15/21 benchmarks = 71%)

**Problem:** Jaccard similarity does not measure reasoning quality, audit realism, or regulatory intent. For Tier 2 and Tier 3 benchmarks, **Jaccard scores can be high for bad answers and low for good answers**, depending on phrasing.

**Examples of Invalid Scoring:**
- **False High Score:** Response copies expected answer's phrasing but misinterprets regulatory requirement → High Jaccard score, wrong answer
- **False Low Score:** Response provides correct audit-style reasoning using different terminology → Low Jaccard score, correct answer
- **Precision/Recall Confusion:** Jaccard treats "missing remediation steps" and "over-specified requirements" identically (both reduce word overlap)

**Consequence:** Baseline scores for B7-B21 are **not merely noisy—they are directionally misleading**. These scores are invalid as quality indicators.

**Acceptable Use:** These scores may be used for:
1. **Relative comparison** across model iterations (if fallback methodology remains constant)
2. **Pipeline validation** to ensure infrastructure completeness
3. **Diagnostic placeholders** to identify which benchmarks need specialized scorers

**Unacceptable Use:** These scores **must not** be interpreted as:
- ❌ Absolute benchmark performance
- ❌ Quality assessment for Tier 2/3 tasks
- ❌ Audit alignment or practicality measures
- ❌ Deployment readiness indicators

---

### **Critical Limitation 2: "Semantic" Terminology Mismatch**

**Affected Component:** Reasoning Track

**Problem:** The Reasoning Track is described as "Semantic + Key-Fact Recall," but the actual implementation uses **lexical Jaccard overlap**, which is not semantic.

**What "Semantic" Actually Means:**
- ❌ **Current (Lexical):** Word overlap - "organization" ≠ "entity"
- ✅ **True Semantic (Phase 3):** Sentence embeddings + cosine similarity - understands "organization" ≈ "entity"

**Why This Matters:** Calling Jaccard "semantic" overstates measurement fidelity and creates false expectations about reasoning quality assessment.

**Corrected Framing:** Current Reasoning Track uses **lexical-proxy reasoning** with true semantic similarity deferred to Phase 3+.

---

### **Critical Limitation 3: Tier Boundaries Operationally Collapse**

**Problem:** Three epistemically distinct evaluation modes (Tier 2 expert rubric, Tier 3 LLM-judge, Reasoning Track) currently collapse into the same Jaccard fallback path at runtime.

**Implication:** Tier 2, Tier 3, and Reasoning Track benchmarks are **numerically indistinguishable** despite requiring fundamentally different validation methods (human experts, LLM validation, automated reasoning checks).

**Framing:** This is an **implementation limitation**, not a design limitation. The tier system correctly identifies which benchmarks need which evaluation methods; Phase 2 simply has not implemented Tier 2/3 infrastructure yet.

---

### **Known Issue 4: B21 Implementation Gap**

**Problem:** B21 (Regulatory Hallucination Rate) is conceptually Tier 1 (binary detection) and should reuse B3's hallucination detection logic. Instead, it falls back to Jaccard, creating an internal inconsistency.

**Impact:** B21 scores are not valid hallucination rate indicators, undermining Tier 1 safety claims.

**Recommendation:** Fix B21 in Phase 3 by reusing `_score_b3_hallucination()` logic. This requires minimal implementation effort and would strengthen internal coherence.

---

### **Limitation 5: No Expert or LLM Evaluation Infrastructure**

**Missing for Tier 2 (B7, B10, B14, B16):**
- Human expert recruitment and training
- Inter-rater reliability tracking (Cohen's kappa ≥ 0.60)
- Adjudication process for disagreements
- Cost: ~$50-100/hour/expert, ~10 cases/day/expert

**Missing for Tier 3 (B12, B13, B20):**
- API integration with commercial LLMs (GPT-4/Claude)
- Random sampling framework (≥20% validation)
- Human-LLM agreement calibration loop
- Cost: API fees + validation expert time

**Timeline:** Both require significant effort and are deferred to Phase 3+ (post-fine-tuning evaluation).

### **Future Improvements (Phase 3+)**

1. **True Semantic Similarity:**
   - Replace Jaccard with sentence-transformers embeddings
   - Cosine similarity between response and expected answer
   - Better capture regulatory reasoning equivalence

2. **Expert Rubric Infrastructure:**
   - Build expert rating interface
   - Implement inter-rater reliability tracking
   - Create expert recruitment and training pipeline

3. **LLM-Judge Implementation:**
   - API integration with commercial LLMs
   - Automated validation sampling (≥20%)
   - Calibration feedback loop

---

## 7. Summary Table: All 21 Benchmarks

| ID | Benchmark Name | Tier/Track | Scoring Method | Status | Fallback |
|----|---------------|-----------|----------------|--------|----------|
| B1 | CCoP Applicability | Tier 1 | Label + KeyFact + Grounding | ✅ | - |
| B2 | Compliance Classification | Tier 1 | Citation Matching | ✅ | - |
| B3 | Conditional Reasoning | Reasoning | Semantic + KeyFact | ✅ | - |
| B4 | Scenario-Control Mapping | Reasoning | Coverage Ratio | ✅ | - |
| B5 | Control Comprehension | Reasoning | IT/OT Classification | ✅ | - |
| B6 | Control Intent | Reasoning | Violation Detection | ✅ | - |
| B7 | Gap Identification | Tier 2 | Expert Rubric 1-5 | ❌ | Jaccard |
| B8 | Gap Prioritisation | Reasoning | Semantic + KeyFact | ❌ | Jaccard |
| B9 | Risk Identification | Reasoning | Semantic + KeyFact | ❌ | Jaccard |
| B10 | Risk Justification | Tier 2 | Expert Rubric 1-5 | ❌ | Jaccard |
| B11 | Risk Severity | Reasoning | Semantic + KeyFact | ❌ | Jaccard |
| B12 | Audit Perspective | Tier 3 | LLM-Judge + Human | ❌ | Jaccard |
| B13 | Evidence Expectation | Tier 3 | LLM-Judge + Human | ❌ | Jaccard |
| B14 | Remediation Quality | Tier 2 | Expert Rubric 1-5 | ❌ | Jaccard |
| B15 | Remediation Feasibility | Reasoning | Semantic + KeyFact | ❌ | Jaccard |
| B16 | Residual Risk | Tier 2 | Expert Rubric 1-5 | ❌ | Jaccard |
| B17 | Policy vs Practice | Reasoning | Semantic + KeyFact | ❌ | Jaccard |
| B18 | Responsibility (SG) | Reasoning | Semantic + KeyFact | ❌ | Jaccard |
| B19 | Cross-Scenario | Reasoning | Semantic + KeyFact | ❌ | Jaccard |
| B20 | Over-Specification | Tier 3 | LLM-Judge + Human | ❌ | Jaccard |
| B21 | Hallucination Rate | Tier 1 | Binary Detection | ❌ | Jaccard |

**Implementation Progress:**
- ✅ Implemented: 6/21 (29%)
- ❌ Fallback (Jaccard): 15/21 (71%)

**By Tier:**
- Tier 1: 2/3 implemented (67%)
- Tier 2: 0/4 implemented (0%)
- Tier 3: 0/3 implemented (0%)
- Reasoning Track: 4/11 implemented (36%)

---

## 8. Code Architecture

### **Main Scoring Entry Point**
```python
# src/domain/services/scoring_service.py
@staticmethod
def score_response(test_case: TestCase, response: ModelResponse) -> List[EvaluationMetric]:
    """Route to appropriate scorer based on benchmark type."""

    benchmark_scorers = {
        "B1": ScoringService._score_b1_interpretation,
        "B2": ScoringService._score_b2_citation,
        "B3": ScoringService._score_b3_hallucination,
        "B4": ScoringService._score_b4_terminology,
        "B5": ScoringService._score_b5_classification,
        "B6": ScoringService._score_b6_violation_detection,
    }

    for benchmark_key, scorer in benchmark_scorers.items():
        if test_case.benchmark_type == benchmark_key:
            return scorer(test_case, response)

    # Fallback: B7-B21 use Jaccard
    return [ScoringService._calculate_basic_accuracy(test_case, response)]
```

### **Overall Score Aggregation**
```python
# src/domain/entities/evaluation_result.py
@property
def overall_score(self) -> float:
    """Calculate weighted average of all metrics."""
    if not self._metrics:
        return 0.0

    total_weighted_value = sum(m.value * m.weight for m in self._metrics)
    total_weight = sum(m.weight for m in self._metrics)

    return total_weighted_value / total_weight if total_weight > 0 else 0.0
```

---

---

## 9. How to Frame This in the Report (Critical Guidance)

### **Recommended Framing for Academic Report**

To protect against score misinterpretation while preserving framework strength, the report should **explicitly state**:

**1. Tier Definitions Represent Target Methodology**
> "The 4-tier evaluation framework (Tier 1: Binary, Tier 2: Expert Rubric, Tier 3: LLM-Judge, Reasoning Track: Lexical-Proxy) represents the **target evaluation methodology** appropriate for CCoP 2.0 compliance reasoning. This tiering reflects how regulatory compliance knowledge is validated in real audit practice and aligns with evaluation standards in legal, medical, and regulatory NLP systems."

**2. Phase 2 Baseline Results: Partial Implementation**
> "Phase 2 baseline evaluation implements a **subset of the target methodology** for pipeline validation and infrastructure testing:
> - ✅ **Tier 1 (B1, B2):** Fully implemented with label-based accuracy, key-fact recall, and grounding checks
> - ⚠️ **Reasoning Track (B3-B6):** Partially implemented with specialized scorers
> - ❌ **Tier 2 (B7, B10, B14, B16):** Not implemented - uses lexical fallback
> - ❌ **Tier 3 (B12, B13, B20):** Not implemented - uses lexical fallback
> - ❌ **B21:** Not implemented despite being Tier 1"

**3. Lexical Fallbacks Are Diagnostic Placeholders**
> "For B7-B21, Jaccard lexical similarity is used as a **diagnostic placeholder for pipeline validation only**. These scores **do not measure reasoning quality, audit alignment, or regulatory intent** and are **invalid as absolute performance indicators**. Jaccard scores can be directionally misleading (high scores for wrong answers, low scores for paraphrased correct answers) and should not be interpreted as benchmark performance."

**4. Focus on Relative Improvement Trends**
> "Phase 2 evaluation focuses on **relative improvement trends** for fine-tuning validation, not absolute benchmark scores. The baseline establishes infrastructure for:
> - Measuring fine-tuning impact on Tier 1 (B1, B2) and specialized Reasoning Track benchmarks (B3-B6)
> - Enabling consistent comparison across model iterations
> - Identifying which benchmarks require Tier 2/3 implementation for valid scoring"

**5. Design vs. Implementation**
> "The evaluation framework's **design is sound and appropriate for CCoP 2.0**. The gap between target methodology and current implementation represents an **implementation limitation**, not a design flaw. The tier system correctly identifies which benchmarks need which evaluation methods; Phase 2 has simply not yet implemented expert rubric or LLM-judge infrastructure due to cost and scope constraints."

---

### **What NOT to Say in the Report**

❌ **Avoid:** "Phase 2 baseline achieved X% on benchmark B7-B21"
- **Why:** Implies Jaccard scores are valid quality measures

❌ **Avoid:** "The model demonstrates good reasoning quality based on B10 scores"
- **Why:** B10 requires expert rubric scoring; Jaccard fallback is invalid

❌ **Avoid:** "Semantic similarity evaluation shows..."
- **Why:** Current implementation is lexical, not semantic

❌ **Avoid:** Presenting B7-B21 scores in tables without prominent disclaimers
- **Why:** Creates false confidence in invalid scores

✅ **Instead:** "Phase 2 baseline established evaluation infrastructure and validated Tier 1 performance (B1, B2). Fine-tuning impact will be measured through relative improvement on Tier 1 benchmarks, with full Tier 2/3 evaluation deferred to post-fine-tuning validation."

---

## 10. Bottom Line Assessment

| Aspect | Status | Notes |
|--------|--------|-------|
| **Framework Design** | ✅ Strong | Tier system is well-designed, defensible, and appropriate for CCoP 2.0 |
| **Tier Rationale** | ✅ Sound | Aligned with compliance audit reality and regulatory NLP best practices |
| **Tier 1 Implementation** | ⚠️ Mostly Complete | B1, B2 done; B21 needs hallucination logic from B3 |
| **Reasoning Track** | ⚠️ Partially Valid | B3-B6 have specialized logic; B8-B19 use fallback |
| **Tier 2/3 Implementation** | ❌ Not Started | Requires expert/LLM infrastructure - significant effort |
| **Current Scores Beyond Tier 1** | ❌ Not Quality-Valid | Jaccard fallbacks are diagnostic only, not performance indicators |
| **Jaccard Usage** | ⚠️ Acceptable as Placeholder | Valid for relative comparison, dangerous if misinterpreted |
| **Primary Action** | 🔧 Tighten Framing | Fix B21, clearly scope fallbacks, emphasize relative trends |

---

**Document Version:** 4.0 (Updated Post-Expert Review)
**Last Updated:** December 14, 2025
**Status:** Phase 2 Baseline (Partial Implementation with Explicit Limitations)
**Review Status:** ✅ Incorporates expert feedback on methodological risks and framing
