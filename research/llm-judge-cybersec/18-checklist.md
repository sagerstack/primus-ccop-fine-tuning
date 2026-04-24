# CheckList — Behavioral Testing of NLP Models (Ribeiro et al., ACL 2020, Best Paper)

**Category**: Ground-truth design — capability-tagged behavioral testing framework
**Canonical sources**:
- Paper: [Ribeiro et al., ACL 2020 — arXiv:2005.04118](https://arxiv.org/abs/2005.04118)
- ACL: [aclanthology.org/2020.acl-main.442](https://aclanthology.org/2020.acl-main.442/)
- Code: [marcotcr/checklist](https://github.com/marcotcr/checklist)

## Why CheckList applies despite being pre-2023

We're not evaluating a chat model against human preferences — we're testing specific, pre-enumerated **capabilities** of a compliance-QA model against a regulatory framework. CheckList's capability-test-type matrix is the canonical GT-design method for this framing, and it's been adopted for LLM evaluation in recent works (e.g., BehaviorBench, Dynabench). Its relevance is structural, not temporal.

## The CheckList grid (core contribution)

Rows = **capabilities**; columns = **test types**. Each cell is a set of test cases.

### Capabilities (task-specific, user-defined)

Examples for sentiment analysis: vocabulary, negation, named-entity handling, temporal reasoning, SRL, fairness, robustness.

For our CCoP compliance use case, the natural capabilities map to our benchmark IDs:
- B1: Applicability / scope recognition
- B3: Conditional compliance reasoning
- B5: Control comprehension
- B7: Gap identification
- B21: Non-existent clause refusal (fabrication resistance)
- ... etc.

Our benchmarks are essentially a CheckList capability matrix already.

### Test types (the three invariants)

| Type | Definition | Example (sentiment) | Our CCoP analogue |
|------|------------|---------------------|-------------------|
| **MFT (Minimum Functionality Test)** | Simple test designed for ONE specific behavior | "This movie is terrible" → negative | "What does Clause 5.3.1 say?" → direct factual |
| **INV (Invariance Test)** | Perturbation must NOT change the label | Swap product names → sentiment stays | Replace "energy sector" with "water sector" → verdict stays if not sector-specific |
| **DIR (Directional Expectation)** | Perturbation SHOULD change the label in a specified direction | Add "I hate that" → negativity increases | Replace "MFA implemented" with "No MFA" → verdict flips to non-compliant |

## Scoring mechanics

CheckList is a **test-harness paradigm**, not a scoring rubric. Scoring is typically:
- Pass/fail per test case (model's output matches expected behavior).
- **Failure rate per capability × test type cell** — a matrix report, not a single score.

The matrix report is itself the deliverable — it shows WHICH capabilities fail and HOW (MFT failure = the model can't do the basic task; INV failure = the model is brittle to irrelevant changes; DIR failure = the model doesn't track the relevant features).

## Prompt scaffolding

N/A — CheckList predates LLM-as-judge. Scoring is typically deterministic (expected label matches predicted label). In LLM-judge adaptations, the judge's role is to classify whether the model's output matches the expected behavior for that test type.

## Ground-truth requirements — **the GT-design contribution**

Each test case carries:

```
{
  "capability": str,         // e.g., "conditional_reasoning"
  "test_type": "MFT" | "INV" | "DIR",
  "template": str,           // parameterized template
  "instances": [str, ...],   // expanded from template
  "expected_label": ...,     // for MFT
  "invariance_pairs": [(a, b), ...]    // for INV — (a, b) must yield same label
  "direction": "increase" | "decrease" | "flip",  // for DIR
}
```

**Templates + perturbations** (the paper's software-tool contribution): the CheckList library generates hundreds of test cases from a single template via slot-filling, so high coverage is achievable with low annotation effort.

## Annotation cost

- Template authoring: 15-60 min per capability × test type.
- Auto-expansion: 100s of cases per template.
- Expert review of generated cases: ~30 min per 100 cases.

CheckList's key efficiency claim: NLP practitioners with CheckList created 2x more tests and found 3x more bugs than practitioners without it (user study, ACL 2020 paper).

## Bias / reliability controls

- **Capability-tagged** scoring exposes WHICH aspects of the model fail — not just an overall score.
- **MFT vs INV vs DIR** separates "doesn't know the task" from "brittle to irrelevant changes" from "doesn't track relevant features."
- Template-based expansion reduces cherry-picked-example bias.

## Reported reliability

Not an LLM method — no judge-agreement numbers. Effectiveness measured by bug-finding: commercial sentiment models passed 80%+ of standard benchmarks but failed 10-40% of CheckList MFTs on basic capabilities.

## Reported limitations

- Template-based expansion can produce unnatural test cases.
- Capability taxonomy is task-specific and requires expert design.
- Binary pass/fail is coarse — no partial credit.
- Doesn't scale to open-ended generation (it assumes classification-style outputs).

## Domain fit for cybersecurity compliance QA

- **Highly applicable — our benchmark structure already resembles CheckList**: our B1-B24 are capability-tagged. We're missing the **test-type** axis (MFT/INV/DIR).
- **Immediate gap**: we have MFTs (most of our cases). We have almost no INV or DIR tests.
  - **INV example we don't have**: "The CIIO operates in the energy sector. [...] Does this comply?" vs "The CIIO operates in the water sector. [...] Does this comply?" — the CCoP verdict should be invariant if the compliance issue is sector-agnostic.
  - **DIR example we don't have**: "The CIIO implements MFA on all remote access [...]" vs "The CIIO does not implement MFA [...]" — verdict should flip to non-compliant.
- **Our B19 (Cross-Scenario Consistency) is a partial INV test** — paraphrased scenarios should yield same verdict. But B19 is under-populated (no `related_scenarios` field filled in sample data).

## Concrete borrowable patterns

1. **Test-type metadata field** added to GT: `test_type: "MFT" | "INV" | "DIR"` with optional `invariance_pair` or `direction` fields.
2. **Template + perturbation** as a GT-expansion pattern — one expert-written "seed scenario" → 5-10 perturbation variants auto-generated.
3. **Capability-test-type matrix report** as a dissertation artifact — shows which benchmarks × test types pass/fail, highlighting failure modes richly than a single aggregate score.
4. **B19 activation**: our `related_scenarios` field is already CheckList-shaped — use it for INV pairs.

## Sources used

- Paper: https://arxiv.org/abs/2005.04118 (accessed 2026-04-24)
- ACL Anthology: https://aclanthology.org/2020.acl-main.442/ (accessed 2026-04-24)
- Code: https://github.com/marcotcr/checklist (accessed 2026-04-24)
