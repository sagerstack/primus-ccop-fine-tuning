# Tier System Implementation Plan
**CCoP 2.0 Evaluation Framework - Phase 3+ Roadmap**

---

## Executive Summary

This document outlines the implementation plan to close the gap between the designed 4-tier evaluation framework and the current Phase 2 baseline implementation (29% complete). The plan prioritizes incremental improvements that maximize evaluation validity while managing cost and complexity.

**Current State:**
- ✅ Implemented: 6/21 benchmarks (B1-B6)
- ❌ Jaccard Fallback: 15/21 benchmarks (B7-B21)
- Implementation Coverage: 29%

**Target State:**
- ✅ All 21 benchmarks implemented with appropriate scoring methods
- ✅ True semantic similarity for Reasoning Track
- ✅ Expert rubric infrastructure for Tier 2
- ✅ LLM-as-Judge infrastructure for Tier 3
- Implementation Coverage: 100%

---

## 1. Implementation Priorities

### **Priority 1: Fix B21 Hallucination Detection (Quick Win)**
**Effort:** Low (2-4 hours)
**Impact:** High (fixes Tier 1 internal inconsistency)
**Timeline:** Immediate (Phase 3 kickoff)

**Rationale:** B21 is conceptually identical to B3 but currently uses Jaccard fallback. This is an avoidable inconsistency that undermines Tier 1 credibility.

---

### **Priority 2: Implement True Semantic Similarity for Reasoning Track**
**Effort:** Medium (1-2 days)
**Impact:** High (validates 11 benchmarks: B8-B19)
**Timeline:** Early Phase 3

**Rationale:** Replaces lexical Jaccard with sentence embeddings for B8-B19, significantly improving measurement validity for reasoning tasks.

---

### **Priority 3: Implement LLM-as-Judge Infrastructure (Tier 3)**
**Effort:** Medium-High (3-5 days)
**Impact:** Medium (validates 3 benchmarks: B12, B13, B20)
**Timeline:** Mid Phase 3

**Rationale:** More scalable and cost-effective than Tier 2 expert rubrics. Provides automated validation for nuanced reasoning tasks.

---

### **Priority 4: Implement Expert Rubric Infrastructure (Tier 2)**
**Effort:** High (1-2 weeks + ongoing expert time)
**Impact:** Medium (validates 4 benchmarks: B7, B10, B14, B16)
**Timeline:** Late Phase 3 or Phase 4

**Rationale:** Most expensive and time-intensive. Requires expert recruitment, training, and ongoing coordination. Deferred until post-fine-tuning when high-fidelity validation becomes critical.

---

## 2. Priority 1: Fix B21 Hallucination Detection

### **Current State**
```python
# src/domain/services/scoring_service.py (line 68)
# B21 falls through to Jaccard fallback
return [ScoringService._calculate_basic_accuracy(test_case, response)]
```

### **Target State**
```python
benchmark_scorers = {
    "B1": ScoringService._score_b1_interpretation,
    "B2": ScoringService._score_b2_citation,
    "B3": ScoringService._score_b3_hallucination,
    "B21": ScoringService._score_b3_hallucination,  # ← Reuse B3 logic
    # ... rest of scorers
}
```

### **Implementation Steps**

**Step 1: Update Benchmark Scorer Mapping**
- File: `src/domain/services/scoring_service.py`
- Add `"B21": ScoringService._score_b3_hallucination` to `benchmark_scorers` dictionary
- No new code required - just route B21 to existing B3 scorer

**Step 2: Verify B21 Test Cases Have Forbidden Claims**
- File: `src/data/benchmarks/b21_hallucination_rate.jsonl`
- Ensure all test cases have `forbidden_claims` array in ground truth
- Format should match B3 test cases:
  ```json
  {
    "test_case_id": "B21-001",
    "ground_truth": {
      "forbidden_claims": [
        "CIIO stands for Cryptography",
        "CCoP requires blockchain"
      ]
    }
  }
  ```

**Step 3: Add Unit Tests**
- File: `tests/unit/test_scoring_service.py`
- Add test cases for B21 hallucination detection:
  ```python
  def test_score_b21_no_hallucinations():
      # Test case with clean response
      assert result.overall_score == 1.0

  def test_score_b21_with_hallucinations():
      # Test case with forbidden claims
      assert result.overall_score < 1.0
  ```

**Step 4: Run Regression Tests**
- Verify B1-B6 scoring unchanged
- Verify B21 no longer uses Jaccard
- Compare B21 scores before/after (should differ significantly)

**Step 5: Update Documentation**
- Mark B21 as ✅ Implemented in tier system overview
- Update implementation coverage: 7/21 (33%)

### **Code Changes Required**

**File 1: `src/domain/services/scoring_service.py`**
```python
# Line 54-62 (current)
benchmark_scorers = {
    "B1": ScoringService._score_b1_interpretation,
    "B2": ScoringService._score_b2_citation,
    "B3": ScoringService._score_b3_hallucination,
    "B4": ScoringService._score_b4_terminology,
    "B5": ScoringService._score_b5_classification,
    "B6": ScoringService._score_b6_violation_detection,
}

# Updated version:
benchmark_scorers = {
    "B1": ScoringService._score_b1_interpretation,
    "B2": ScoringService._score_b2_citation,
    "B3": ScoringService._score_b3_hallucination,
    "B4": ScoringService._score_b4_terminology,
    "B5": ScoringService._score_b5_classification,
    "B6": ScoringService._score_b6_violation_detection,
    "B21": ScoringService._score_b3_hallucination,  # ← ADD THIS LINE
}
```

**File 2: `src/data/benchmarks/b21_hallucination_rate.jsonl`**
- Verify all test cases have `forbidden_claims` in ground truth
- If missing, add based on CCoP 2.0 common hallucination patterns

### **Success Criteria**
- ✅ B21 uses binary hallucination detection instead of Jaccard
- ✅ B21 test cases have appropriate forbidden claims
- ✅ Unit tests pass
- ✅ Regression tests show no impact on B1-B6
- ✅ Documentation updated

### **Estimated Effort**
- Code changes: 30 minutes
- Test case verification: 1 hour
- Unit tests: 1 hour
- Documentation: 30 minutes
- **Total: 2-4 hours**

---

## 3. Priority 2: Implement True Semantic Similarity

### **Current State**
- B8-B19 use Jaccard lexical similarity (word overlap)
- Does not capture semantic meaning or synonyms
- Directionally misleading for paraphrased responses

### **Target State**
- Use sentence embeddings (sentence-transformers)
- Cosine similarity between response and expected answer
- Captures semantic equivalence: "organization" ≈ "entity"

### **Technical Approach**

**Option A: Sentence-Transformers (Recommended)**
- Library: `sentence-transformers`
- Model: `all-MiniLM-L6-v2` (local, fast, 80MB)
- Advantages:
  - Runs locally (no API costs)
  - Fast inference (~50ms per pair)
  - Good performance on regulatory text
  - No internet required

**Option B: OpenAI Embeddings**
- API: `text-embedding-3-small`
- Advantages: Higher quality
- Disadvantages: Requires API key, costs $0.02 per 1M tokens

**Recommendation:** Start with Option A for Phase 3 baseline, consider Option B for deployment if quality gap is significant.

### **Implementation Steps**

**Step 1: Add Dependencies**
```bash
poetry add sentence-transformers torch
```

**Step 2: Create Semantic Similarity Service**
- File: `src/domain/services/semantic_similarity_service.py`
```python
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

class SemanticSimilarityService:
    """Semantic similarity using sentence embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model = SentenceTransformer(model_name)

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts."""
        embeddings = self._model.encode([text1, text2])
        similarity = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        return float(similarity)

    def calculate_batch_similarity(
        self, expected: str, responses: List[str]
    ) -> List[float]:
        """Calculate similarity for multiple responses against expected."""
        expected_embedding = self._model.encode(expected)
        response_embeddings = self._model.encode(responses)

        similarities = [
            np.dot(expected_embedding, resp_emb) / (
                np.linalg.norm(expected_embedding) * np.linalg.norm(resp_emb)
            )
            for resp_emb in response_embeddings
        ]
        return [float(s) for s in similarities]
```

**Step 3: Update Scoring Service**
- File: `src/domain/services/scoring_service.py`
- Replace `_calculate_basic_accuracy` with semantic similarity for Reasoning Track

```python
class ScoringService:
    def __init__(self):
        self._semantic_service = SemanticSimilarityService()

    @staticmethod
    def _score_reasoning_track(
        test_case: TestCase,
        response: ModelResponse
    ) -> List[EvaluationMetric]:
        """Semantic similarity + key-fact recall for B8-B19."""

        # 1. Semantic similarity (replaces Jaccard)
        semantic_score = self._semantic_service.calculate_similarity(
            test_case.expected_response,
            response.content
        )
        accuracy_metric = EvaluationMetric(
            name="accuracy",
            value=semantic_score,
            weight=1.0,
            description="Semantic similarity using sentence embeddings"
        )

        # 2. Key-fact recall (unchanged)
        completeness_metric = ScoringService._calculate_completeness(
            test_case, response
        )

        # 3. Grounding check (unchanged)
        grounding_metric = ScoringService._calculate_grounding(
            test_case, response
        )

        return [accuracy_metric, completeness_metric, grounding_metric]
```

**Step 4: Update Benchmark Routing**
```python
# Reasoning Track benchmarks
reasoning_benchmarks = ["B8", "B9", "B11", "B15", "B17", "B18", "B19"]

benchmark_scorers = {
    # Tier 1
    "B1": ScoringService._score_b1_interpretation,
    "B2": ScoringService._score_b2_citation,
    "B21": ScoringService._score_b3_hallucination,

    # Reasoning Track (specialized)
    "B3": ScoringService._score_b3_hallucination,
    "B4": ScoringService._score_b4_terminology,
    "B5": ScoringService._score_b5_classification,
    "B6": ScoringService._score_b6_violation_detection,
}

# Add reasoning track routing
for benchmark in reasoning_benchmarks:
    benchmark_scorers[benchmark] = ScoringService._score_reasoning_track
```

**Step 5: Performance Optimization**
- Cache model loading (singleton pattern)
- Batch embedding computation for multiple test cases
- Consider quantization for faster inference

**Step 6: Validation**
- Compare semantic vs. Jaccard scores on B8-B19
- Manual review of high-divergence cases
- Verify semantic similarity handles synonyms correctly

**Step 7: Add Configuration**
- File: `src/config.py`
```python
class EvaluationConfig:
    # Semantic similarity settings
    SEMANTIC_MODEL: str = "all-MiniLM-L6-v2"
    SEMANTIC_CACHE_DIR: str = ".cache/sentence-transformers"
    SEMANTIC_BATCH_SIZE: int = 32
```

### **Code Changes Required**

**New File: `src/domain/services/semantic_similarity_service.py`**
- Implement `SemanticSimilarityService` class
- Model loading with caching
- Cosine similarity calculation
- Batch processing support

**Modified File: `src/domain/services/scoring_service.py`**
- Add `_score_reasoning_track()` method
- Update `benchmark_scorers` dictionary
- Add semantic service initialization
- Keep existing Jaccard as fallback for debugging

**Modified File: `pyproject.toml`**
```toml
[tool.poetry.dependencies]
sentence-transformers = "^2.2.2"
torch = "^2.1.0"
```

**New File: `tests/unit/test_semantic_similarity_service.py`**
- Test similarity calculation
- Test synonym detection
- Test batch processing
- Test model caching

### **Success Criteria**
- ✅ Semantic similarity outperforms Jaccard on synonym detection
- ✅ B8-B19 scores reflect semantic meaning, not word overlap
- ✅ Inference time <100ms per test case
- ✅ No external API dependencies
- ✅ Unit tests pass
- ✅ Documentation updated

### **Estimated Effort**
- Service implementation: 4 hours
- Scoring service integration: 3 hours
- Testing and validation: 4 hours
- Performance optimization: 2 hours
- Documentation: 1 hour
- **Total: 1-2 days**

---

## 4. Priority 3: Implement LLM-as-Judge Infrastructure

### **Current State**
- B12, B13, B20 use Jaccard fallback
- No LLM evaluation infrastructure
- No human validation framework

### **Target State**
- LLM judge evaluates responses using structured rubric
- Random 20% sample validated by human experts
- Calibration loop for human-LLM agreement ≥80%

### **Technical Approach**

**LLM Selection:**
- **Option A:** OpenAI GPT-4 Turbo ($10/1M input tokens)
- **Option B:** Anthropic Claude Opus ($15/1M input tokens)
- **Option C:** Local Llama-3.1-70B via Ollama (free, slower)

**Recommendation:** Use Ollama for development/validation, switch to GPT-4/Claude for production if needed.

### **Implementation Steps**

**Step 1: Create LLM Judge Service**
- File: `src/domain/services/llm_judge_service.py`

```python
from typing import Dict, List, Optional
from dataclasses import dataclass
import json

@dataclass
class JudgeEvaluation:
    """LLM judge evaluation result."""
    accuracy_score: int  # 1-5
    completeness_score: int  # 1-5
    alignment_score: int  # 1-5
    justification: str
    overall_score: float  # 0-1
    confidence: float  # 0-1

class LLMJudgeService:
    """LLM-as-Judge evaluation service."""

    def __init__(self, model_name: str = "llama3.1:70b"):
        self._model = model_name
        self._gateway = OllamaGateway()

    def evaluate_response(
        self,
        test_case: TestCase,
        response: ModelResponse,
        rubric: Dict[str, str]
    ) -> JudgeEvaluation:
        """Evaluate response using LLM judge with structured rubric."""

        judge_prompt = self._build_judge_prompt(test_case, response, rubric)
        judge_response = self._gateway.generate_response(
            model=self._model,
            prompt=judge_prompt,
            temperature=0.1  # Low temperature for consistent scoring
        )

        evaluation = self._parse_judge_response(judge_response)
        return evaluation

    def _build_judge_prompt(
        self,
        test_case: TestCase,
        response: ModelResponse,
        rubric: Dict[str, str]
    ) -> str:
        """Build structured prompt for LLM judge."""
        return f"""You are an expert CCoP 2.0 compliance auditor evaluating a model's response.

**Test Question:**
{test_case.input_text}

**Model Response:**
{response.content}

**Expected Answer:**
{test_case.expected_response}

**Evaluation Rubric:**
{json.dumps(rubric, indent=2)}

**Instructions:**
Rate the response on a 1-5 scale for each criterion:
1. Accuracy: Technical correctness of compliance interpretation
2. Completeness: Coverage of all relevant control requirements
3. Alignment: Matches how a CSA auditor would evaluate this

Provide your evaluation in JSON format:
{{
  "accuracy_score": <1-5>,
  "completeness_score": <1-5>,
  "alignment_score": <1-5>,
  "justification": "<2-3 sentence explanation>",
  "confidence": <0.0-1.0>
}}
"""

    def _parse_judge_response(self, response: str) -> JudgeEvaluation:
        """Parse JSON response from LLM judge."""
        try:
            data = json.loads(response)
            overall = (
                data["accuracy_score"] +
                data["completeness_score"] +
                data["alignment_score"]
            ) / 15.0  # Normalize to 0-1

            return JudgeEvaluation(
                accuracy_score=data["accuracy_score"],
                completeness_score=data["completeness_score"],
                alignment_score=data["alignment_score"],
                justification=data["justification"],
                overall_score=overall,
                confidence=data.get("confidence", 0.5)
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to conservative scoring on parse error
            return JudgeEvaluation(
                accuracy_score=3,
                completeness_score=3,
                alignment_score=3,
                justification="Parse error - conservative default score",
                overall_score=0.6,
                confidence=0.0
            )
```

**Step 2: Create Human Validation Framework**
- File: `src/domain/services/human_validation_service.py`

```python
from typing import List, Tuple
import random

class HumanValidationService:
    """Manages human validation sampling and agreement tracking."""

    def __init__(self, sample_rate: float = 0.2):
        self._sample_rate = sample_rate

    def select_validation_sample(
        self,
        results: List[EvaluationResult]
    ) -> List[EvaluationResult]:
        """Select random 20% sample for human validation."""
        sample_size = max(1, int(len(results) * self._sample_rate))
        return random.sample(results, sample_size)

    def calculate_agreement(
        self,
        llm_scores: List[float],
        human_scores: List[float],
        tolerance: float = 0.2
    ) -> float:
        """Calculate human-LLM agreement rate."""
        agreements = sum(
            1 for llm, human in zip(llm_scores, human_scores)
            if abs(llm - human) <= tolerance
        )
        return agreements / len(llm_scores)

    def needs_recalibration(
        self,
        agreement_rate: float,
        threshold: float = 0.8
    ) -> bool:
        """Check if LLM judge needs recalibration."""
        return agreement_rate < threshold
```

**Step 3: Create Tier 3 Scorer**
- File: `src/domain/services/scoring_service.py`

```python
@staticmethod
def _score_tier3_llm_judge(
    test_case: TestCase,
    response: ModelResponse
) -> List[EvaluationMetric]:
    """Tier 3: LLM-as-Judge evaluation for B12, B13, B20."""

    # Define rubric for this benchmark
    rubric = {
        "accuracy": "Does response correctly identify audit perspective?",
        "completeness": "Are all relevant audit concerns covered?",
        "alignment": "Does this match how CSA auditors evaluate CII?"
    }

    judge_service = LLMJudgeService()
    evaluation = judge_service.evaluate_response(test_case, response, rubric)

    # Convert judge scores to metrics
    accuracy_metric = EvaluationMetric(
        name="accuracy",
        value=evaluation.accuracy_score / 5.0,
        weight=1.0,
        description="LLM judge accuracy score"
    )

    completeness_metric = EvaluationMetric(
        name="completeness",
        value=evaluation.completeness_score / 5.0,
        weight=0.8,
        description="LLM judge completeness score"
    )

    alignment_metric = EvaluationMetric(
        name="alignment",
        value=evaluation.alignment_score / 5.0,
        weight=1.0,
        description="LLM judge audit alignment score"
    )

    return [accuracy_metric, completeness_metric, alignment_metric]
```

**Step 4: Update Benchmark Routing**
```python
# Tier 3 benchmarks
tier3_benchmarks = ["B12", "B13", "B20"]

for benchmark in tier3_benchmarks:
    benchmark_scorers[benchmark] = ScoringService._score_tier3_llm_judge
```

**Step 5: Create Validation CLI Command**
- File: `src/cli/commands/validate_llm_judge.py`

```python
@click.command()
@click.option("--benchmark", required=True, help="Benchmark to validate (B12/B13/B20)")
@click.option("--sample-rate", default=0.2, help="Validation sample rate")
def validate_llm_judge(benchmark: str, sample_rate: float):
    """Run LLM-judge validation with human review."""

    # 1. Run LLM judge on all test cases
    results = run_llm_evaluation(benchmark)

    # 2. Select random sample for human validation
    validation_service = HumanValidationService(sample_rate)
    sample = validation_service.select_validation_sample(results)

    # 3. Prompt expert for manual review
    click.echo(f"\nValidating {len(sample)} cases. Please review:")
    human_scores = []
    llm_scores = []

    for result in sample:
        display_case_for_review(result)
        human_score = click.prompt("Your score (0-1)", type=float)
        human_scores.append(human_score)
        llm_scores.append(result.overall_score)

    # 4. Calculate agreement
    agreement = validation_service.calculate_agreement(llm_scores, human_scores)
    click.echo(f"\nHuman-LLM Agreement: {agreement:.1%}")

    if validation_service.needs_recalibration(agreement):
        click.echo("⚠️ Agreement <80%. Rubric recalibration needed.")
    else:
        click.echo("✅ Agreement ≥80%. LLM judge validated.")
```

**Step 6: Store LLM Judge Evaluations**
- Extend `EvaluationResult` to store judge justifications
- Enable human reviewers to see LLM reasoning

### **Code Changes Required**

**New Files:**
- `src/domain/services/llm_judge_service.py`
- `src/domain/services/human_validation_service.py`
- `src/cli/commands/validate_llm_judge.py`
- `tests/unit/test_llm_judge_service.py`

**Modified Files:**
- `src/domain/services/scoring_service.py` (add Tier 3 scorer)
- `src/domain/entities/evaluation_result.py` (add judge metadata)
- `src/cli/main.py` (register validation command)

### **Success Criteria**
- ✅ LLM judge evaluates B12, B13, B20 with structured rubric
- ✅ Human validation achieves ≥80% agreement
- ✅ Calibration loop implemented for low agreement
- ✅ Judge justifications stored for transparency
- ✅ CLI command for validation workflow
- ✅ Documentation updated

### **Estimated Effort**
- LLM judge service: 6 hours
- Human validation framework: 4 hours
- Tier 3 scorer integration: 3 hours
- CLI validation command: 3 hours
- Testing and calibration: 4 hours
- Documentation: 2 hours
- **Total: 3-5 days**

---

## 5. Priority 4: Implement Expert Rubric Infrastructure

### **Current State**
- B7, B10, B14, B16 use Jaccard fallback
- No expert recruitment or training process
- No rubric rating interface
- No inter-rater reliability tracking

### **Target State**
- Expert rubric interface for manual scoring
- Inter-rater reliability ≥80% (Cohen's kappa ≥0.60)
- Adjudication process for disagreements
- Structured 1-5 scale across 4 dimensions

### **Technical Approach**

**Challenges:**
- Most expensive tier (expert time: $50-100/hour)
- Slowest throughput (~10 cases/day/expert)
- Requires expert recruitment and training
- Needs ongoing coordination

**Recommendation:** Defer to late Phase 3 or Phase 4. Only implement when fine-tuning performance justifies high-fidelity validation.

### **Implementation Steps (High-Level)**

**Step 1: Build Expert Rating Interface**
- Web-based UI for expert reviewers
- Display test case, response, rubric
- Collect 1-5 ratings for 4 dimensions
- Store ratings with expert ID and timestamp

**Step 2: Implement Inter-Rater Reliability Tracking**
- Calculate Cohen's kappa for expert pairs
- Flag low-reliability cases for adjudication
- Track expert calibration over time

**Step 3: Create Expert Training Materials**
- CCoP 2.0 compliance fundamentals
- Rubric interpretation guidelines
- Example cases with target ratings
- Calibration exercises

**Step 4: Develop Adjudication Workflow**
- Identify cases with >20% disagreement
- Route to senior expert for resolution
- Document adjudication rationale

**Step 5: Expert Recruitment**
- Hire 2-3 cybersecurity compliance auditors
- Require CCoP 2.0 or equivalent experience
- Onboard with training materials
- Run calibration phase before production rating

### **Cost Estimation**

**Expert Time:**
- Rating: ~10 cases/day/expert × 4 benchmarks × avg 10 cases = 40 ratings
- Time: 40 ratings × 5 min/rating = 200 min/day/expert
- Cost: 200 min × $1.50/min = $300/day/expert
- For 40 test cases across B7, B10, B14, B16: ~$300-600 total

**Development:**
- UI development: 2-3 days
- Reliability tracking: 1 day
- Training materials: 1-2 days
- Testing: 1 day
- **Total: 5-7 days development + $300-600 expert time**

### **Deferred Implementation**

Given cost and complexity, Tier 2 should be implemented only when:
1. Fine-tuning has improved baseline performance significantly
2. Tier 1 and Reasoning Track scores are strong
3. Deployment readiness requires high-fidelity validation
4. Budget is available for expert time

### **Estimated Effort**
- UI development: 3 days
- Reliability tracking: 1 day
- Training materials: 2 days
- Expert recruitment/onboarding: 1 week
- Calibration and testing: 2 days
- **Total: 1-2 weeks + $300-600 ongoing expert costs**

---

## 6. Testing Strategy

### **Unit Tests**

**New Test Files:**
- `tests/unit/test_semantic_similarity_service.py`
- `tests/unit/test_llm_judge_service.py`
- `tests/unit/test_human_validation_service.py`

**Coverage Requirements:**
- All new services: ≥90% code coverage
- Edge cases: empty responses, parse errors, invalid scores
- Performance: inference time benchmarks

### **Integration Tests**

**Test Scenarios:**
- End-to-end evaluation with all tiers
- Benchmark routing to correct scorers
- Score aggregation across multiple metrics
- Result persistence and retrieval

**Test File:**
- `tests/integration/test_tier_system_e2e.py`

### **Regression Tests**

**Critical Checks:**
- B1-B6 scores unchanged after new tier implementation
- Overall score calculation matches legacy method
- No performance degradation (inference time)

### **Validation Tests**

**Semantic Similarity:**
- Manual review of 20 high-divergence cases (semantic vs. Jaccard)
- Verify synonym detection works
- Check edge cases (identical responses, completely different responses)

**LLM Judge:**
- Human validation on 20% sample
- Agreement rate ≥80%
- Calibration loop test

---

## 7. Rollout Plan

### **Phase 3A: Quick Wins (Week 1-2)**
**Focus:** Fix B21, validate infrastructure

**Milestones:**
- ✅ B21 hallucination detection implemented
- ✅ B21 test cases verified
- ✅ Unit tests pass
- ✅ Documentation updated
- **Output:** 7/21 benchmarks implemented (33%)

---

### **Phase 3B: Semantic Similarity (Week 3-4)**
**Focus:** Implement true semantic similarity for Reasoning Track

**Milestones:**
- ✅ Sentence-transformers integrated
- ✅ Semantic similarity service implemented
- ✅ B8-B19 routing updated
- ✅ Validation shows semantic > Jaccard
- **Output:** 18/21 benchmarks implemented (86%)

---

### **Phase 3C: LLM-as-Judge (Week 5-6)**
**Focus:** Implement Tier 3 infrastructure

**Milestones:**
- ✅ LLM judge service implemented
- ✅ Human validation framework ready
- ✅ B12, B13, B20 using LLM judge
- ✅ Agreement ≥80% achieved
- **Output:** 21/21 benchmarks implemented (100%)

---

### **Phase 4: Expert Rubric (Deferred)**
**Focus:** Implement Tier 2 when fine-tuning validates need

**Conditions for Starting:**
- Fine-tuning complete
- Tier 1 + Reasoning Track scores strong
- Budget approved for expert time
- Deployment timeline requires high-fidelity validation

---

## 8. Risk Mitigation

### **Risk 1: Semantic Similarity Underperforms Jaccard**
**Likelihood:** Low
**Impact:** Medium

**Mitigation:**
- Run A/B comparison on B8-B19 before full rollout
- Keep Jaccard as fallback option
- Manual review of high-divergence cases
- Consider hybrid approach (weighted average of both)

---

### **Risk 2: LLM Judge Agreement <80%**
**Likelihood:** Medium
**Impact:** High

**Mitigation:**
- Implement calibration loop with rubric refinement
- Add example cases to judge prompt
- Lower temperature for more consistent scoring
- Consider using multiple judges and averaging

---

### **Risk 3: Sentence-Transformers Model Too Large for M3**
**Likelihood:** Low
**Impact:** Medium

**Mitigation:**
- Use `all-MiniLM-L6-v2` (only 80MB)
- Fallback to `paraphrase-MiniLM-L3-v2` (60MB)
- Consider quantization for smaller footprint
- Load model lazily (only when needed)

---

### **Risk 4: Implementation Timeline Slips**
**Likelihood:** Medium
**Impact:** Low

**Mitigation:**
- Prioritize B21 fix (2-4 hours) for quick win
- Defer Tier 2 to Phase 4 if needed
- Run semantic similarity and LLM judge in parallel
- Skip expert rubric if budget/time constrained

---

## 9. Success Metrics

### **Implementation Completeness**
- **Current:** 6/21 benchmarks (29%)
- **Phase 3A Target:** 7/21 benchmarks (33%)
- **Phase 3B Target:** 18/21 benchmarks (86%)
- **Phase 3C Target:** 21/21 benchmarks (100%)

### **Evaluation Quality**
- **Semantic Similarity:** Outperforms Jaccard on synonym detection
- **LLM Judge:** ≥80% human-LLM agreement
- **Expert Rubric:** Cohen's kappa ≥0.60

### **Performance**
- **Inference Time:** <200ms per test case (including semantic embeddings)
- **LLM Judge Time:** <5s per test case (acceptable for offline evaluation)
- **Cost:** $0 for Tier 1 + Reasoning Track, <$50 for Tier 3 full evaluation

### **Documentation**
- ✅ Tier system overview updated
- ✅ Code architecture documented
- ✅ Testing strategy defined
- ✅ Rollout plan finalized

---

## 10. Next Steps

### **Immediate Actions (This Week)**
1. **Fix B21 Hallucination Detection**
   - Update `scoring_service.py` benchmark routing
   - Verify B21 test cases have `forbidden_claims`
   - Run unit tests
   - Update documentation

2. **Prepare Semantic Similarity Environment**
   - Install `sentence-transformers` and `torch`
   - Test model loading and inference time
   - Run baseline Jaccard vs. semantic comparison

### **Short-Term Actions (Next 2 Weeks)**
1. Implement semantic similarity service
2. Update B8-B19 scoring to use semantic embeddings
3. Validate semantic > Jaccard on manual review
4. Update tier system documentation

### **Medium-Term Actions (Weeks 3-6)**
1. Implement LLM judge service
2. Create human validation framework
3. Run Tier 3 calibration loop
4. Achieve ≥80% human-LLM agreement

### **Long-Term Actions (Phase 4)**
1. Assess need for Tier 2 expert rubric
2. Build expert rating interface if needed
3. Recruit and train expert reviewers
4. Run full high-fidelity evaluation

---

## Appendix A: Code Architecture Changes

### **New Services**
- `SemanticSimilarityService`: Sentence embeddings + cosine similarity
- `LLMJudgeService`: Structured LLM evaluation with rubrics
- `HumanValidationService`: Sampling + agreement tracking

### **Modified Services**
- `ScoringService`: Add Tier 3 scorer, update Reasoning Track scorer

### **New CLI Commands**
- `validate-llm-judge`: Human validation workflow

### **New Dependencies**
- `sentence-transformers`: Semantic similarity
- `torch`: Sentence-transformers backend

---

## Appendix B: Testing Checklist

### **Unit Tests**
- [ ] `test_semantic_similarity_service.py`
  - [ ] Synonym detection works
  - [ ] Batch processing works
  - [ ] Model caching works
  - [ ] Edge cases handled
- [ ] `test_llm_judge_service.py`
  - [ ] Judge prompt formatting
  - [ ] Response parsing
  - [ ] Error handling
- [ ] `test_human_validation_service.py`
  - [ ] Random sampling
  - [ ] Agreement calculation
  - [ ] Recalibration detection

### **Integration Tests**
- [ ] `test_tier_system_e2e.py`
  - [ ] All tiers route correctly
  - [ ] Scores aggregate properly
  - [ ] Results persist correctly

### **Regression Tests**
- [ ] B1-B6 scores unchanged
- [ ] Overall score calculation matches
- [ ] No performance degradation

### **Validation Tests**
- [ ] Semantic vs. Jaccard comparison
- [ ] LLM judge human agreement ≥80%
- [ ] Manual review of edge cases

---

**Document Version:** 1.0
**Last Updated:** December 14, 2025
**Status:** Implementation Plan for Phase 3+
**Owner:** CCoP 2.0 Fine-Tuning Project Team
