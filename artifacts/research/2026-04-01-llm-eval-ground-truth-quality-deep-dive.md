## Deep Dive: LLM Evaluation Ground Truth Quality

### Strategic Summary

Leading LLM evaluation frameworks converge on a test case model with clear separation between input, expected output, grading criteria, and metadata -- but diverge significantly in how reference answers and scoring rubrics are structured. The most effective ground truth for LLM-as-judge evaluation combines structured key_facts (atomic, verifiable claims) with dimensional rubrics (separate criteria per evaluation axis) and explicit fail_conditions (bright-line violations that override positive scoring). For compliance/regulatory domains specifically, the IRAC framework (Issue-Rule-Application-Conclusion) provides a proven decomposition structure for both reference answers and evaluation criteria.

### Key Questions

- How do leading frameworks (HELM, lm-eval-harness, RAGAS, DeepEval, OpenAI Evals, Promptfoo) structure ground truth?
- What makes a good reference answer for LLM-as-judge?
- What attributes support multi-dimensional evaluation?
- Best practices for key_facts, must_have, fail_conditions granularity
- Reducing bias and improving ground truth quality
- Compliance/regulatory-specific evaluation approaches
- Schema design patterns supporting both automated and LLM-judge scoring

### Overview

Ground truth quality is the single largest determinant of evaluation reliability, yet it receives disproportionately little attention compared to model architecture and prompt engineering. Across the frameworks studied, a pattern emerges: simple input-output pairs are insufficient for evaluating domain-specific LLMs where reasoning quality, factual precision, and hallucination avoidance all matter. The most robust evaluation systems decompose ground truth into multiple layers -- the reference answer itself, atomic verifiable facts, dimensional scoring criteria, explicit failure modes, and metadata for stratified analysis.

In compliance/regulatory domains, the challenge is amplified. Responses must be simultaneously precise (citing correct clauses), nuanced (acknowledging conditional compliance scenarios), complete (covering all relevant requirements), and honest (refusing to fabricate non-existent requirements). This multi-dimensional nature means a single "expected_response" string is necessary but not sufficient -- it must be accompanied by structured metadata that tells both rule-based scorers and LLM judges exactly what to evaluate and how.

Research on rubric granularity reveals a critical trade-off: alignment between LLM judges and human evaluators degrades as rubric granularity increases. Studies show accuracy drops from 76% to 57% and Cohen's Kappa from 0.51 to 0.34 when moving from binary to 5-way classification. This argues for keeping scoring scales small (3-4 levels maximum) with extremely clear anchoring at each level, which aligns with the project's existing 0-3 scale.

### How Leading Frameworks Structure Ground Truth

#### HELM (Stanford CRFM)

HELM structures evaluation around **Scenarios** and **Instances**. Each Instance contains:

```
Instance:
  input: str                    # The prompt/question
  references: List[Reference]   # Expected answers
  split: TRAIN | VALID | TEST   # Data partition
  id: str                       # Unique identifier

Reference:
  output: str                   # Answer text
  tags: List[str]               # e.g., CORRECT_TAG
```

Key design choices:
- Multiple references allowed per instance (not every correct answer need be enumerated)
- References tagged as CORRECT or not (supports multiple valid answers)
- Evaluation separated into 7 metrics (accuracy, calibration, robustness, fairness, bias, toxicity, efficiency)
- Scenarios defined in YAML schema files (e.g., `schema_enterprise.yaml`)
- No structured decomposition of reference answers -- correctness is binary against tags

**Relevance to CCoP project**: HELM's multi-metric approach validates evaluating across dimensions. Its weakness is the flat reference model -- no support for partial credit or reasoning quality assessment.

#### lm-eval-harness (EleutherAI)

Uses YAML-based task configuration with Jinja2 templating:

```yaml
task: ccop_compliance
dataset_path: local_jsonl
test_split: test

doc_to_text: "{{question}}"
doc_to_target: "{{expected_label}}"       # Ground truth
doc_to_choice: "{{[option_a, option_b]}}" # For multiple-choice

metric_list:
  - metric: acc
    aggregation: mean
    higher_is_better: true
  - metric: !function custom_scorer.irac_score
    aggregation: mean
    higher_is_better: true
```

Key design choices:
- Ground truth is a single `target` field (string, integer index, or function return)
- Supports custom metrics via Python functions
- JSONL output includes: `doc_id`, `doc`, `arguments`, `resps`, `filtered_resps`, `metric`
- Few-shot examples drawn from training split with configurable sampling
- Group-level aggregation with micro/macro averaging

**Relevance**: The custom metric function pattern is directly applicable -- CCoP could define IRAC-phase-specific scoring functions. The `doc_to_target` flexibility (string vs function) supports both simple label matching and complex evaluation.

#### OpenAI Evals

Two-tier structure: basic evals (deterministic) and model-graded evals (LLM-as-judge):

**Basic eval data format (JSONL)**:
```json
{
  "input": [{"role": "user", "content": "question text"}],
  "ideal": "expected answer text"
}
```

**Model-graded eval data format**:
```json
{
  "input": [{"role": "user", "content": "question text"}],
  "ideal": "reference answer for comparison",
  "custom_field": "additional context for grading prompt"
}
```

**Model-graded YAML configuration**:
```yaml
prompt: |
  Given the question: {input}
  The ideal answer: {ideal}
  The model output: {completion}
  Rate the accuracy on a scale of A-E.
choice_strings: "ABCDE"
choice_scores:
  A: 1.0
  B: 0.75
  C: 0.5
  D: 0.25
  E: 0.0
eval_type: cot_classify  # Reason, then answer (recommended)
```

Key design choices:
- `ideal` field serves as reference answer (can be list for multiple valid answers)
- Model-graded evals use `{key}` template substitution in grading prompts
- Three classification methods: `cot_classify` (recommended), `classify_cot`, `classify`
- Built-in templates: `fact.yaml` (factual consistency), `closedqa.yaml` (QA), `battle.yaml` (comparison)
- Chain-of-thought classification produces more reliable grading

**Relevance**: The `cot_classify` pattern directly maps to the project's LLM-judge approach. The `ideal` + custom fields pattern supports rich ground truth beyond simple expected answers.

#### DeepEval (Confident AI)

Most granular test case schema among frameworks studied:

```python
LLMTestCase(
    input: str,                          # Required: user query
    actual_output: str,                  # Required: model response
    expected_output: Optional[str],      # Ground truth reference
    context: Optional[List[str]],        # Golden truth data
    retrieval_context: Optional[List[str]], # RAG retriever results
    tools_called: Optional[List[ToolCall]], # Agent tool usage
    expected_tools: Optional[List[ToolCall]], # Expected tool calls
    token_cost: Optional[float],
    completion_time: Optional[float]
)
```

Key design choices:
- Separates `context` (golden truth supporting data) from `retrieval_context` (actual RAG results)
- 50+ built-in metrics including G-Eval, hallucination, faithfulness, answer relevancy
- All metrics output 0-1 score + reasoning + pass/fail against threshold
- Hallucination metric uses `context` as source of truth, checks for contradictions
- Faithfulness metric checks if output is supported by `retrieval_context`

**Relevance**: The `context` vs `retrieval_context` separation is highly relevant for CCoP -- ground truth CCoP clause text (context) vs what RAG actually retrieves (retrieval_context) enables diagnosing whether failures are retrieval or generation problems.

#### RAGAS

Focused on RAG pipeline evaluation:

```python
Dataset({
    "question": str,        # Input query
    "ground_truth": str,    # Reference answer
    "answer": str,          # Generated response
    "contexts": List[str]   # Retrieved context passages
})
```

Metrics decompose into retriever vs generator quality:
- **Retriever**: context precision, context recall, context relevancy
- **Generator**: faithfulness (factual consistency against context), answer relevancy (completeness, no redundancy)

**Relevance**: RAGAS's retriever/generator decomposition maps directly to CCoP's hybrid RAG pipeline -- separate evaluation of retrieval quality vs generation quality.

#### Promptfoo

Most flexible assertion-based model:

```yaml
tests:
  - vars:
      question: "What are CCoP MFA requirements?"
      context: "Clause 5.3.1(c) requires MFA for privileged access..."
    assert:
      - type: factuality
        value: "CCoP 2.0 requires MFA for privileged access to CII"
      - type: llm-rubric
        value: "Response correctly identifies clause 5.3.1(c) and explains MFA requirement"
        threshold: 0.8
      - type: context-faithfulness
        threshold: 0.9
      - type: not-icontains
        value: "clause 5.9.7"  # Hallucination check
```

Key design choices:
- Multiple assertion types per test case (layered evaluation)
- Combines deterministic checks (contains, regex) with LLM-graded checks
- `factuality` assertion compares against reference statement
- `context-faithfulness` checks output is supported by context
- Threshold + pass logic: both must be true when threshold is set
- Provider override per assertion (use different judge models)

**Relevance**: The multi-assertion pattern is the closest to what CCoP needs -- combining rule-based checks (key_facts, forbidden_claims) with LLM-judge evaluation (reasoning quality, nuance).

### Reference Answer Design for LLM-as-Judge

#### What Makes a Good Reference Answer

Based on analysis across frameworks and the Anthropic engineering guide on evals:

1. **Solvability proof**: A reference answer proves the task is solvable and defines what "good" looks like. Two domain experts should independently reach the same pass/fail verdict when comparing any output to the reference.

2. **Structured over prose**: Reference answers that decompose into clear sections (finding, reasoning, recommendation) are more reliably evaluated than flowing prose. The IRAC framework provides a natural decomposition for compliance domains.

3. **Appropriate detail level**: Reference answers should be detailed enough to disambiguate scoring but not so rigid that valid alternative phrasings fail. The current CCoP project's `expected_response` field demonstrates good practice -- paragraphs with numbered steps and clear reasoning chains.

4. **Acceptable variations explicitly stated**: Research shows LLM judges are more reliable when the ground truth acknowledges valid alternative answers. Adding an `acceptable_variations` field prevents false negatives from legitimate alternative framings.

#### How Detailed Should expected_response Be

The research suggests a middle ground:

- **Too brief** (1-2 sentences): Insufficient for LLM judges to assess reasoning depth and completeness
- **Too verbose** (500+ words): Creates fragile evaluation where any structural deviation is penalized
- **Optimal** (100-250 words): Covers key reasoning steps, cites specific clauses, states conclusion clearly, without over-specifying phrasing

For compliance domains specifically, reference answers should include:
- The regulatory finding (compliant / non-compliant / conditionally compliant)
- The specific clause(s) that govern the scenario
- The reasoning chain connecting facts to conclusion
- Any conditions or caveats

### Multi-Dimensional Evaluation Attributes

Based on framework analysis and the current CCoP project's existing schema, the following attributes emerge as critical for multi-dimensional ground truth:

#### Core Attributes (Required)

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `key_facts` | Atomic verifiable claims that MUST appear | `["Clause 5.3.1(c) requires MFA for privileged access"]` |
| `expected_label` | Short classification/verdict | `"Non-compliant"` |
| `expected_response` | Full reference answer | Structured prose with reasoning |
| `reasoning_dimensions` | Per-dimension evaluation criteria | `{factual_accuracy: "...", logical_coherence: "..."}` |

#### Safety/Hallucination Attributes

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `forbidden_claims` | Claims that indicate hallucination | `["Clause 5.9.7 requires...", "CCoP mandates CISSP certification"]` |
| `safety_checks` | Specific hallucination patterns to detect | `["Citing non-existent clauses", "Inventing vendor requirements"]` |
| `trap_type` | Category of adversarial test | `"non_existent_clause"`, `"non_existent_requirement_detail"` |

#### Quality/Depth Attributes

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `reasoning_chain` | Ordered steps of expected reasoning | `["Identify applicable clause", "Apply to scenario", "State conclusion"]` |
| `acceptable_variations` | Valid alternative framings/conclusions | `["May conclude 'partially compliant' if documented"]` |
| `boundary_conditions` | Edge conditions that affect the answer | `["Answer changes if OT systems are safety-critical"]` |
| `common_errors` | Frequent mistakes to check for | `["Confusing MFA with strong passwords"]` |

#### Metadata Attributes

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `difficulty` | Calibrated difficulty level | `"low"`, `"medium"`, `"high"` |
| `domain` | IT vs OT vs both | `"OT"` |
| `scenario_type` | Taxonomy of scenario pattern | `"compensating_controls_insufficient"` |
| `clause_reference` | Source regulatory clause(s) | `"5.3.1, 5.2.1"` |
| `section` | CCoP section | `"Section 5: Protection"` |

### Best Practices for key_facts, must_have, fail_conditions

#### key_facts Granularity

Research and framework analysis point to these guidelines:

**Atomic**: Each key_fact should be independently verifiable in the model output. Not "Must discuss MFA and explain why compensating controls are insufficient" but two separate facts: `"Clause 5.3.1(c) requires MFA for privileged access"` and `"Compensating controls (logging, monitoring) cannot replace mandated MFA"`.

**Quantity per test case**: 
- Simple factual recall (B1-B2 type): 2-4 key_facts
- Reasoning tasks (B3-B20 type): 3-6 key_facts covering both factual anchors and reasoning conclusions
- Hallucination detection (B21): 1-2 key_facts (what IS true) + 2-4 safety_checks (what must NOT appear)

**Sourced**: Each key_fact should trace to a specific CCoP clause, supplementary document, or CSA guidance. Currently, some test cases have `"Unable to extract key facts automatically"` -- these are quality gaps.

**Scoring weight**: Not all key_facts are equally important. Consider adding a `weight` or `tier` indicator:
```json
"key_facts": [
  {"fact": "Clause 5.3.1(c) requires MFA", "tier": "critical"},
  {"fact": "Compensating controls cannot replace MFA", "tier": "important"},
  {"fact": "Existing monitoring should be retained alongside MFA", "tier": "supporting"}
]
```

#### fail_conditions Design

Fail conditions (currently `safety_checks` in B21 tests) should be **bright-line rules** -- any single violation causes automatic failure regardless of other scoring:

- **Factual fabrication**: Citing non-existent clauses, inventing requirements
- **Dangerous advice**: Recommending non-compliance as acceptable
- **Contradicting mandatory requirements**: Stating that mandated controls are optional
- **Jurisdictional confusion**: Applying requirements from other frameworks as if they were CCoP

These should be separated from quality criteria (which allow partial credit) and evaluated via regex/rule-based checks where possible, reserving LLM judgment for ambiguous cases.

### Compliance/Regulatory Domain Approaches

#### IRAC Framework for Ground Truth Decomposition

The most significant finding for the CCoP project is the IRAC (Issue-Rule-Application-Conclusion) framework from legal evaluation, which several recent papers (HSE-Bench, PLAWBench, LegalSemi) use to structure both test cases and evaluation:

```json
{
  "irac_decomposition": {
    "issue": "Whether compensating controls satisfy CCoP MFA requirement",
    "rule": "Clause 5.3.1(c) mandates MFA for privileged CII access",
    "application": "Logging and monitoring are detective controls, not preventive; they cannot substitute for MFA authentication requirement",
    "conclusion": "Non-compliant. Must implement MFA; retain compensating controls as defense-in-depth"
  }
}
```

This decomposition enables:
- Phase-specific scoring (evaluate Issue-spotting separately from Rule-recall)
- Granular failure diagnosis (model may spot the issue correctly but apply the wrong rule)
- Training data for IRAC-aware fine-tuning

#### LogiSafetyGen Approach (Formal Verification)

Recent research (2025) proposes translating regulatory documents into formal logic (Linear Temporal Logic) to create deterministic ground truth. While full formalization is impractical for CCoP's scope, the principle of **formal oracles** for deterministic test cases is valuable:

- For rule-based benchmarks (B1-B6, B21): Test cases CAN have deterministic correct answers
- For reasoning benchmarks (B3, B7-B20): Test cases require LLM-judge evaluation but should still have deterministic fail conditions

#### Regulatory Citation Accuracy

LLMs in regulatory domains frequently hallucinate statutes, mis-cite clauses, and invent requirements. Best practices:
- Include the actual clause text in `context` field for reference
- Track citation accuracy as a separate metric
- Include adversarial tests with non-existent but plausible clause numbers (the B21 pattern is strong here)

#### HSE-Bench Evaluation Methodology

HSE-Bench (1,020 questions across regulations, court cases, exams, and fieldwork) provides a template for compliance evaluation:
- IRAC-phase-specific scoring
- Dual metrics: accuracy (direct comparison) + AUC-ROC (ranking quality)
- Adversarial augmentation: rewriting to increase logical complexity
- Domain expert verification as quality gate

### Ground Truth Quality Assurance

#### Bias Reduction

1. **Multi-annotator construction**: Ground truth should be created by multiple domain experts independently, with disagreements resolved through discussion rather than majority vote (consensus-based, not democratic).

2. **Adversarial review**: After ground truth creation, a separate reviewer should attempt to find valid answers that would be scored as failures. Any such finding indicates over-specification in the ground truth.

3. **LLM-judge calibration**: Before deploying LLM-as-judge, calibrate against human-labeled samples:
   - Minimum 30-50 examples for initial calibration
   - 100-200 examples for production-grade reliability
   - Track Cohen's Kappa between LLM judge and human evaluators (target: >= 0.6)

4. **Prompt perturbation analysis**: Test whether minor rubric rephrasing changes scores significantly. High sensitivity indicates fragile evaluation criteria.

#### Inter-Annotator Agreement

For compliance domains, inter-annotator agreement should be measured at multiple levels:
- **Verdict agreement**: Do annotators agree on compliant/non-compliant? (target: >= 85%)
- **Key fact agreement**: Do annotators identify the same critical facts? (target: >= 75%)
- **Reasoning agreement**: Do annotators follow the same logical chain? (target: >= 70%)

#### Difficulty Calibration

Current CCoP test cases use `low/medium/high` difficulty, but this should be empirically validated:
- Run all test cases against a baseline model
- Map declared difficulty to actual pass rates
- Recalibrate: "high" difficulty should have < 30% baseline pass rate
- Ensure each difficulty tier has adequate representation (minimum 5-8 cases each)

#### Adversarial Case Design

Each benchmark should include at minimum:
- **Positive cases**: Scenarios where the answer IS compliant (tests for false negatives)
- **Negative cases**: Scenarios where the answer IS NOT compliant (tests for false positives)
- **Edge cases**: Conditional compliance scenarios (tests for nuance)
- **Adversarial cases**: Questions designed to elicit hallucination or over-generalization

Current observation: Most CCoP test cases are scenario-based reasoning questions. Consider adding more **classification-boundary** cases that test whether the model correctly distinguishes between similar-sounding clauses.

### Schema Design Recommendations

Based on the full analysis, here is a recommended v2 schema that supports both rule-based and LLM-judge scoring:

```json
{
  "test_id": "B3-001",
  "version": "2.0",
  "benchmark_id": "B3",
  "benchmark_name": "Conditional Compliance Reasoning",

  "input": {
    "question": "Does shared admin accounts with compensating controls comply with CCoP MFA?",
    "context_mode": "hybrid",
    "supplementary_context": null
  },

  "ground_truth": {
    "expected_label": "non-compliant",
    "expected_response": "Full reference answer text...",

    "key_facts": [
      {
        "fact": "Clause 5.3.1(c) requires multi-factor authentication for privileged access to CII systems",
        "source": "CCoP 2.0 Section 5.3.1(c)",
        "tier": "critical",
        "verification_type": "keyword_overlap"
      },
      {
        "fact": "Compensating controls (logging, monitoring, access reviews) cannot replace mandated MFA",
        "source": "Regulatory interpretation",
        "tier": "critical",
        "verification_type": "semantic"
      },
      {
        "fact": "Existing monitoring controls should be retained as defense-in-depth alongside MFA",
        "source": "CCoP 2.0 defense-in-depth principle",
        "tier": "supporting",
        "verification_type": "semantic"
      }
    ],

    "reasoning_chain": [
      "Identify that the scenario involves privileged access to CII",
      "Recall clause 5.3.1(c) mandating MFA for privileged access",
      "Evaluate whether compensating controls satisfy the MFA mandate",
      "Conclude that detective controls cannot replace preventive controls",
      "Recommend implementing MFA while retaining existing controls"
    ],

    "acceptable_variations": [
      "May frame as 'defense-in-depth' rather than 'compensating controls'",
      "May cite 5.2.1 in addition to 5.3.1(c)",
      "May recommend specific MFA implementation approaches"
    ]
  },

  "fail_conditions": {
    "forbidden_claims": [
      "Compensating controls satisfy the MFA requirement",
      "Shared administrative accounts are acceptable under CCoP"
    ],
    "safety_checks": [
      "Recommending that MFA is optional when monitoring is in place",
      "Citing non-existent CCoP clauses"
    ],
    "hallucination_patterns": [
      "Inventing clause numbers not in CCoP 2.0",
      "Attributing requirements to CCoP that come from other frameworks"
    ]
  },

  "evaluation_rubric": {
    "dimensions": {
      "factual_accuracy": {
        "description": "Correctly identifies applicable clause and states the requirement",
        "weight": 0.35,
        "anchors": {
          "0": "Cites wrong clause or states incorrect requirement",
          "1": "Identifies general area but not specific clause",
          "2": "Correctly cites clause but incomplete explanation",
          "3": "Precisely cites clause with complete, accurate explanation"
        }
      },
      "logical_coherence": {
        "description": "Reasoning chain from facts to conclusion is logically sound",
        "weight": 0.30,
        "anchors": {
          "0": "No reasoning or contradictory logic",
          "1": "Some reasoning but gaps or non-sequiturs",
          "2": "Sound reasoning with minor gaps",
          "3": "Complete, logically rigorous reasoning chain"
        }
      },
      "completeness": {
        "description": "Covers all relevant aspects of the compliance question",
        "weight": 0.20,
        "anchors": {
          "0": "Addresses less than half of relevant aspects",
          "1": "Addresses main point but misses important aspects",
          "2": "Covers most relevant aspects",
          "3": "Comprehensive coverage including edge cases"
        }
      },
      "contextual_nuance": {
        "description": "Demonstrates understanding of regulatory context and practical implications",
        "weight": 0.15,
        "anchors": {
          "0": "Black-and-white answer with no contextual awareness",
          "1": "Acknowledges complexity but doesn't address it",
          "2": "Good contextual awareness with some nuance",
          "3": "Excellent nuance distinguishing between related scenarios"
        }
      }
    }
  },

  "metadata": {
    "section": "Section 5: Protection",
    "clause_reference": ["5.3.1", "5.2.1"],
    "domain": "IT/OT",
    "difficulty": "high",
    "difficulty_validated": false,
    "scenario_type": "compensating_controls_insufficient",
    "related_sections": ["5.2.2"],
    "irac_phase": "application",
    "test_category": "negative",
    "created_date": "2026-04-01",
    "last_reviewed": "2026-04-01",
    "reviewer": null
  }
}
```

#### Schema Design Rationale

1. **Separated concerns**: `ground_truth` (what's correct), `fail_conditions` (what's wrong), `evaluation_rubric` (how to score), and `metadata` (how to slice) are distinct top-level objects.

2. **Tiered key_facts**: Critical vs supporting facts enable weighted scoring and prioritized evaluation.

3. **Explicit reasoning_chain**: Ordered steps enable IRAC-style decomposed evaluation and help LLM judges assess reasoning quality.

4. **Anchored rubric dimensions**: Each dimension has 0-3 anchors matching the project's existing scale, with clear behavioral descriptions at each level. This is the single most important feature for LLM-judge reliability.

5. **Weighted dimensions**: Different benchmarks can weight dimensions differently (e.g., B21 hallucination tests weight factual_accuracy at 0.50+).

6. **fail_conditions separate from evaluation**: Bright-line failures bypass scoring entirely -- if any forbidden_claim appears, the test fails regardless of other quality.

7. **acceptable_variations**: Reduces false negatives from legitimate alternative framings.

8. **Validation metadata**: `difficulty_validated`, `last_reviewed`, `reviewer` support quality assurance processes.

#### Backward Compatibility

The v2 schema subsumes the current schema. Migration path:
- `question` -> `input.question`
- `expected_response` -> `ground_truth.expected_response`
- `expected_label` -> `ground_truth.expected_label`
- `key_facts` (list of strings) -> `ground_truth.key_facts` (list of objects with tier/source)
- `reasoning_dimensions` -> `evaluation_rubric.dimensions`
- `safety_checks` -> `fail_conditions.safety_checks`
- `evaluation_criteria` -> absorbed into `evaluation_rubric.dimensions` anchors
- `metadata` -> `metadata` (unchanged, extended)

### Key Takeaways

1. **Anchored dimensional rubrics are non-negotiable for LLM-judge reliability.** The single highest-impact improvement is replacing prose evaluation criteria with 0-3 anchored descriptions per dimension. Research shows alignment degrades sharply with scale granularity -- the project's 0-3 scale is in the optimal range. Each anchor point must describe observable behavior, not quality adjectives.

2. **Separate fail_conditions from quality scoring.** Hallucination detection (forbidden_claims, safety_checks) should be evaluated via rule-based checks that can override positive LLM-judge scores. A response that scores 3/3 on reasoning but fabricates a clause reference should still fail. This two-layer evaluation (hard fail + soft scoring) is a pattern across DeepEval, Promptfoo, and Anthropic's agent evaluation guidance.

3. **key_facts should be atomic, tiered, and sourced.** Moving from flat string lists to structured objects with `tier` (critical/important/supporting), `source` (clause reference), and `verification_type` (keyword_overlap vs semantic) enables both granular scoring and quality auditing. Target 3-6 key_facts per reasoning test case, with at least 2 at "critical" tier.

### Remaining Unknowns

- [ ] Optimal number of test cases per benchmark for statistical significance (current 3-8 is likely insufficient; HSE-Bench uses 50+ per category, but resource constraints apply)
- [ ] Whether IRAC decomposition in ground truth measurably improves LLM-judge scoring reliability vs unstructured reference answers
- [ ] How to empirically validate difficulty calibration without multiple baseline model runs
- [ ] Whether dimension weights should be fixed per benchmark or tunable per evaluation phase (baseline vs finetuned vs deployment)
- [ ] Inter-annotator agreement baseline for CCoP-specific compliance evaluation (no published benchmarks exist for this domain)
- [ ] Whether `acceptable_variations` can be generated semi-automatically from the reference answer using a strong LLM, or must be human-authored for reliability

### Sources

- [HELM (Stanford CRFM)](https://crfm.stanford.edu/helm/) - Accessed 2026-04-01
- [HELM GitHub Repository](https://github.com/stanford-crfm/helm) - Accessed 2026-04-01
- [HELM Code Documentation](https://github.com/stanford-crfm/helm/blob/main/docs/code.md) - Accessed 2026-04-01
- [EleutherAI lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) - Accessed 2026-04-01
- [lm-eval-harness New Task Guide](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/new_task_guide.md) - Accessed 2026-04-01
- [OpenAI Evals Repository](https://github.com/openai/evals) - Accessed 2026-04-01
- [OpenAI Evals Templates](https://github.com/openai/evals/blob/main/docs/eval-templates.md) - Accessed 2026-04-01
- [OpenAI Evaluation Best Practices](https://platform.openai.com/docs/guides/evaluation-best-practices) - Accessed 2026-04-01
- [DeepEval Test Cases Documentation](https://deepeval.com/docs/evaluation-test-cases) - Accessed 2026-04-01
- [DeepEval Hallucination Metric](https://deepeval.com/docs/metrics-hallucination) - Accessed 2026-04-01
- [RAGAS Documentation](https://docs.ragas.io/en/stable/references/evaluate/) - Accessed 2026-04-01
- [Promptfoo LLM Rubric](https://www.promptfoo.dev/docs/configuration/expected-outputs/model-graded/llm-rubric/) - Accessed 2026-04-01
- [Promptfoo Model-Graded Metrics](https://www.promptfoo.dev/docs/configuration/expected-outputs/model-graded/) - Accessed 2026-04-01
- [Anthropic: Demystifying Evals for AI Agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) - Accessed 2026-04-01
- [G-Eval Paper (Liu et al., 2023)](https://arxiv.org/abs/2303.16634) - Accessed 2026-04-01
- [G-Eval Definitive Guide (Confident AI)](https://www.confident-ai.com/blog/g-eval-the-definitive-guide) - Accessed 2026-04-01
- [HSE-Bench: LLM-based HSE Compliance Assessment](https://arxiv.org/html/2505.22959) - Accessed 2026-04-01
- [LogiSafetyGen: Evaluating Implicit Regulatory Compliance](https://arxiv.org/html/2601.08196) - Accessed 2026-04-01
- [RAFT: Explicating Tacit Regulatory Knowledge](https://arxiv.org/html/2601.09762) - Accessed 2026-04-01
- [PLAWBench: Rubric-Based Benchmark for Legal LLMs](https://arxiv.org/pdf/2601.16669) - Accessed 2026-04-01
- [LegalBench (Stanford)](https://hazyresearch.stanford.edu/legalbench/) - Accessed 2026-04-01
- [LegalBench-RAG](https://github.com/zeroentropy-ai/legalbenchrag) - Accessed 2026-04-01
- [Rubric-Conditioned LLM Grading: Alignment, Uncertainty, and Robustness](https://arxiv.org/html/2601.08843v1) - Accessed 2026-04-01
- [LLM-as-a-Judge Practical Guide (Towards Data Science)](https://towardsdatascience.com/llm-as-a-judge-a-practical-guide/) - Accessed 2026-04-01
- [LLM-as-Judge Best Practices (Monte Carlo Data)](https://www.montecarlodata.com/blog-llm-as-judge/) - Accessed 2026-04-01
- [LLM-as-a-Judge Complete Guide (Evidently AI)](https://www.evidentlyai.com/llm-guide/llm-as-a-judge) - Accessed 2026-04-01
- [Matched Holistic Rubric vs Self-Decomposing Atomic Judges](https://arxiv.org/html/2603.28005) - Accessed 2026-04-01
- [Langfuse Dataset Schema Enforcement](https://langfuse.com/changelog/2025-11-06-dataset-schema-enforcement) - Accessed 2026-04-01
- [GraphCompliance: LLM-Based Regulatory Compliance](https://arxiv.org/html/2510.26309v1) - Accessed 2026-04-01
- [Contractzlab: LLM Compliance Benchmark](https://www.contractzlab.com/en/blog/llm-compliance-benchmark) - Accessed 2026-04-01
