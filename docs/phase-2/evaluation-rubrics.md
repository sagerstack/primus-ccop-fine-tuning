# Evaluation Rubrics: LLM-as-Judge Prompt Templates

**Purpose**: This document formalizes rubric prompt templates for all 15 LLM-judged benchmarks (B3, B7-B20). Each template is ready for direct use with only placeholder substitution.

**Relationship to Criteria Establishment**: Anchor definitions and examples are derived from [criteria-establishment.md](criteria-establishment.md) (Component 2). Dimension names, weights, and scoring scales match exactly.

**Scoring Scale**: All rubrics use a discrete 0-3 anchored scale (not 1-5, not continuous 0-1):

| Score | Level | Definition |
|-------|-------|------------|
| 0 | Incorrect | Contains factually wrong regulatory information, fabricated claims, or fundamentally misinterprets the requirement |
| 1 | Partial | Correct core answer but incomplete — missing key regulatory details, clauses, or context |
| 2 | Complete | Fully consistent with expected answer — all required regulatory points covered accurately |
| 3 | Exceeds | Fully consistent plus provides additional correct and relevant information |

**JSON Response Format**: All judge prompts require this standardized output:

```json
{
  "dimensions": [
    {"dimension": "<name>", "score": <0-3>, "weight": <float>}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## UNIVERSAL RUBRIC

**Purpose**: A single benchmark-agnostic rubric applied to every LLM-judged benchmark. Benchmark-specific signal comes from each test case's ground truth (`key_facts`, `clause_reference`, `expected_response`), not from the rubric itself.

**Dimensions**: Five generic dimensions, each scored on the anchored 0-3 scale. `factual_grounding` carries the full weight 1.0; all other dimensions carry half weight 0.5 — giving factual_grounding effectively 2× the influence of any other single dimension on the composite (a deliberate hallucination penalty). Composite score = weighted sum / (3.0 × total weight); maximum composite = 1.0.

### Dimension Definitions and Anchors

#### D1: Verdict Accuracy (weight 0.5)

Does the response's final verdict or conclusion match the expected answer, including any qualifications and secondary conclusions?

| Score | Anchor |
|-------|--------|
| 0 | Final verdict contradicts the expected answer |
| 1 | Directionally right but misses key qualifications, conditions, or secondary conclusions |
| 2 | Correct main verdict; misses one or more secondary aspects |
| 3 | Fully matches expected answer including all qualifications and secondary conclusions |

#### D2: Justification Quality (weight 0.5)

Is the reasoning logically sound, internally consistent, and does it follow from stated premises?

| Score | Anchor |
|-------|--------|
| 0 | No justification offered OR reasoning is internally contradictory |
| 1 | Justification present but drifts from the actual question; reasoning partially off-target |
| 2 | Sound reasoning chain addressing the core issue; minor gaps in inferential links |
| 3 | Tight logical chain directly addressing the question; every inference traceable to premises |

#### D3: Factual Grounding (weight 1.0)

Are all factual claims — regulatory citations, procedural assertions, quoted requirements — either verifiable against the provided ground truth or correctly attributed to cited sources?

Distinguish two claim types when evaluating:

- **Regulatory assertions** (response claims the regulation specifies X): require traceability to the corpus, `key_facts`, or `clause_reference`.
- **Derived inferences** (response draws conclusions from cited clauses or general security principles): require logical soundness; the inference itself need not appear verbatim in ground truth.

| Score | Anchor |
|-------|--------|
| 0 | Fabricated citations (cites clauses/sections that don't exist) OR no citations anywhere |
| 1 | Real citations present but significant misattribution — cited source doesn't support the claim made |
| 2 | Real citations, mostly correct interpretation; one loose attribution or one imprecise claim |
| 3 | All citations real, correctly interpreted; every claim traceable to cited source or sound derivation |

#### D4: Scope Appropriateness (weight 0.5)

Does the response stay within what was asked, without drifting, over-specifying, or contradicting stated scenario constraints?

| Score | Anchor |
|-------|--------|
| 0 | Substantially off-topic OR proposes actions that contradict stated scenario constraints |
| 1 | Verbose with multiple tangential sections; core answer diluted or buried |
| 2 | Mostly on-topic with minor drift; longer than needed but doesn't mislead |
| 3 | Focused response that directly addresses what was asked; no drift, no bloat |

#### D5: Actionable Way Forward (weight 0.5)

Does the response translate its analysis into concrete, feasible next steps the reader can act on, accounting for any constraints stated in the scenario?

| Score | Anchor |
|-------|--------|
| 0 | No next steps given OR suggested steps contradict the scenario's stated constraints |
| 1 | Vague direction only; no specific mechanism, instrument, or action named |
| 2 | Names a specific action or mechanism but lacks detail, specificity, or feasibility awareness |
| 3 | Specific action + correct mechanism/instrument + feasibility-aware given stated constraints |

### Judge Prompt Template

```
You are an expert compliance auditor evaluating a model's response to a compliance scenario. Score the response on 5 dimensions using an anchored 0-3 scale for each. The `factual_grounding` dimension carries weight 1.0; all other dimensions carry weight 0.5 — giving factual_grounding effectively 2× the influence of any other dimension (deliberate hallucination penalty).

**Question**:
{question}

**Model Response**:
{response}

**Expected Response** (provided for factual context only — evaluate the response's correctness, not its phrasing similarity to this reference):
{expected_response}

**Key Facts** (tier-critical facts that should be present):
{key_facts}

**Evaluation Instructions**:

Score each dimension independently on the 0-3 anchored scale. A response can score high on some dimensions and low on others — each dimension measures a different aspect of quality.

**D1 — verdict_accuracy**: Does the final verdict match the expected answer, including qualifications and secondary conclusions? Score 0 if contradicts; 1 if directionally right but incomplete; 2 if correct on main point; 3 if fully matches including secondary aspects.

**D2 — justification_quality**: Is the reasoning logically sound and internally consistent? Does each inference follow from stated premises? Flag internal contradictions. Score 0 for no reasoning or self-contradictory; 1 for drifting reasoning; 2 for sound with minor gaps; 3 for tight logical chain.

**D3 — factual_grounding** (weight 1.0 vs. 0.5 for others): For every factual claim, classify as:
- Regulatory assertion (attributed to a regulation or clause) → must be traceable to corpus, key_facts, or clause_reference
- Derived inference (conclusion drawn from cited clauses or general principles) → must be logically sound; need not appear in ground truth verbatim

Score 0 if any fabricated citation detected (cites clauses/sections that don't exist) or no citations present; 1 for significant misattribution (real clause, wrong description); 2 for real citations with minor imprecision; 3 for clean grounding throughout.

**D4 — scope_appropriateness**: Does the response stay within what was asked? Does it respect the scenario's stated constraints (e.g., if the scenario states a technical constraint, don't recommend actions that assume the constraint doesn't exist)? Score 0 for substantially off-topic or constraint-violating; 1 for verbose with tangents; 2 for mostly on-topic; 3 for focused and direct.

**D5 — actionable_way_forward**: Does the response translate analysis into concrete, feasible next steps? Vague advice scores low; specific mechanisms with feasibility awareness score high. Score 0 if no next steps or steps contradict constraints; 1 for vague direction only; 2 for specific mechanism lacking detail; 3 for specific + correct + feasibility-aware.

**Output Format** (JSON only, no other text):

{
  "dimensions": [
    {"dimension": "verdict_accuracy",       "score": <0-3>, "weight": 0.5},
    {"dimension": "justification_quality",  "score": <0-3>, "weight": 0.5},
    {"dimension": "factual_grounding",      "score": <0-3>, "weight": 1.0},
    {"dimension": "scope_appropriateness",  "score": <0-3>, "weight": 0.5},
    {"dimension": "actionable_way_forward", "score": <0-3>, "weight": 0.5}
  ],
  "justification": "<2-3 sentences per dimension, citing specific evidence from the response>",
  "confidence": <0.0-1.0>
}
```

---

## B3: Conditional Logic

**Dimension**: conditional_logic
**Weight**: 1.0
**Category**: Reasoning Quality

### Anchored Scale (0-3)

| Score | Anchor | Example |
|-------|--------|---------|
| 0 | Ignores conditions or gives absolute answer to conditional question | "This is non-compliant" with no consideration of compensating controls |
| 1 | Acknowledges conditions exist but doesn't reason through them | "It depends on compensating controls" without specifying which or how |
| 2 | Correctly reasons through conditions with specific controls cited | "Non-compliant as-is, but acceptable if compensating controls include: (a) network monitoring per 5.4, (b) enhanced logging per 5.5, because these mitigate the residual risk of..." |
| 3 | Complete conditional reasoning plus risk trade-off analysis | Full reasoning plus "The compensating controls reduce risk to acceptable levels, but residual risk X remains and should be documented in the risk register per Section 3.2" |

### Judge Prompt Template

```
You are an expert CCoP 2.0 compliance auditor evaluating a model's conditional reasoning quality.

**Task**: Evaluate how well the response handles conditional compliance scenarios.

**Question**:
{question}

**Model Response**:
{response}

**Expected Response**:
{expected_response}

**Key Facts**:
{key_facts}

**Evaluation Instructions**:

Think step-by-step about the response quality.

The "conditional_logic" dimension assesses whether the model:
- Recognizes that compliance depends on conditions (not absolute yes/no)
- Identifies which specific compensating controls apply
- Explains how those controls mitigate the compliance gap
- Analyzes residual risks after controls are applied

**Anchored Scale**:

Score 0 (Incorrect): Ignores conditions or gives absolute answer to conditional question.
Example: "This is non-compliant" with no consideration of compensating controls.

Score 1 (Partial): Acknowledges conditions exist but doesn't reason through them.
Example: "It depends on compensating controls" without specifying which or how.

Score 2 (Complete): Correctly reasons through conditions with specific controls cited.
Example: "Non-compliant as-is, but acceptable if compensating controls include: (a) network monitoring per 5.4, (b) enhanced logging per 5.5, because these mitigate the residual risk of..."

Score 3 (Exceeds): Complete conditional reasoning plus risk trade-off analysis.
Example: Full reasoning plus "The compensating controls reduce risk to acceptable levels, but residual risk X remains and should be documented in the risk register per Section 3.2"

**Output Format** (JSON only):

{
  "dimensions": [
    {"dimension": "conditional_logic", "score": <0-3>, "weight": 1.0}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## B7: Gap Identification

**Dimension**: gap_identification
**Weight**: 1.0
**Category**: Gap & Risk Analysis

### Anchored Scale (0-3)

| Score | Anchor | Example |
|-------|--------|---------|
| 0 | Misses major gaps or identifies non-existent gaps | Fails to notice missing MFA; invents a "mandatory encryption gateway" requirement |
| 1 | Identifies some gaps but misses critical ones | Finds logging gaps but misses missing network segmentation between IT and OT |
| 2 | Identifies all major gaps with correct clause references | "Gaps identified: (1) No MFA for remote access (5.1.5), (2) No IT/OT segmentation (10.2.3), (3) Patch delay exceeds timeline (5.6.4)" |
| 3 | All gaps plus severity classification and interdependencies | Adds "Gap 2 (segmentation) amplifies Gap 1 (MFA) — without segmentation, compromised remote access provides direct OT path" |

### Judge Prompt Template

```
You are an expert CCoP 2.0 compliance auditor evaluating a model's gap identification capability.

**Task**: Evaluate how comprehensively and accurately the response identifies compliance gaps.

**Question**:
{question}

**Model Response**:
{response}

**Expected Response**:
{expected_response}

**Key Facts**:
{key_facts}

**CCoP Clause Reference**:
{clause_reference}

**Evaluation Instructions**:

Think step-by-step about the response quality.

The "gap_identification" dimension assesses whether the model:
- Identifies all major compliance gaps (not just obvious ones)
- Cites correct CCoP clause references for each gap
- Avoids inventing non-existent requirements
- Classifies gap severity and interdependencies

**Anchored Scale**:

Score 0 (Incorrect): Misses major gaps or identifies non-existent gaps.
Example: Fails to notice missing MFA; invents a "mandatory encryption gateway" requirement.

Score 1 (Partial): Identifies some gaps but misses critical ones.
Example: Finds logging gaps but misses missing network segmentation between IT and OT.

Score 2 (Complete): Identifies all major gaps with correct clause references.
Example: "Gaps identified: (1) No MFA for remote access (5.1.5), (2) No IT/OT segmentation (10.2.3), (3) Patch delay exceeds timeline (5.6.4)"

Score 3 (Exceeds): All gaps plus severity classification and interdependencies.
Example: Adds "Gap 2 (segmentation) amplifies Gap 1 (MFA) — without segmentation, compromised remote access provides direct OT path"

**Output Format** (JSON only):

{
  "dimensions": [
    {"dimension": "gap_identification", "score": <0-3>, "weight": 1.0}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## B8: Gap Prioritization

**Dimension**: gap_prioritization
**Weight**: 1.0
**Category**: Gap & Risk Analysis

### Anchored Scale (0-3)

| Score | Anchor | Example |
|-------|--------|---------|
| 0 | No prioritization logic or reversed priorities | Lists gaps alphabetically; prioritizes cosmetic issue over critical MFA gap |
| 1 | Prioritization attempted but criteria unclear or inconsistent | "Fix MFA first because it's important" without risk-based reasoning |
| 2 | Risk-based prioritization with clear criteria (likelihood × impact) | "Priority 1: MFA (critical — remote access is primary attack vector, direct essential service impact). Priority 2: Segmentation (high — limits blast radius). Priority 3: Logging (medium — detective, not preventive)" |
| 3 | Risk-based plus implementation sequencing and quick-win identification | Adds "Quick win: MFA can be deployed in 2 weeks with existing IAM. Strategic: segmentation requires network redesign — start architecture review now, implement in phases" |

### Judge Prompt Template

```
You are an expert CCoP 2.0 compliance auditor evaluating a model's gap prioritization capability.

**Task**: Evaluate how effectively the response prioritizes compliance gaps using risk-based criteria.

**Question**:
{question}

**Model Response**:
{response}

**Expected Response**:
{expected_response}

**Key Facts**:
{key_facts}

**Evaluation Instructions**:

Think step-by-step about the response quality.

The "gap_prioritization" dimension assesses whether the model:
- Uses risk-based criteria (likelihood × impact) for prioritization
- Provides clear rationale for priority ordering
- Considers implementation sequencing and quick wins
- Aligns priorities with CII essential service criticality

**Anchored Scale**:

Score 0 (Incorrect): No prioritization logic or reversed priorities.
Example: Lists gaps alphabetically; prioritizes cosmetic issue over critical MFA gap.

Score 1 (Partial): Prioritization attempted but criteria unclear or inconsistent.
Example: "Fix MFA first because it's important" without risk-based reasoning.

Score 2 (Complete): Risk-based prioritization with clear criteria (likelihood × impact).
Example: "Priority 1: MFA (critical — remote access is primary attack vector, direct essential service impact). Priority 2: Segmentation (high — limits blast radius). Priority 3: Logging (medium — detective, not preventive)"

Score 3 (Exceeds): Risk-based plus implementation sequencing and quick-win identification.
Example: Adds "Quick win: MFA can be deployed in 2 weeks with existing IAM. Strategic: segmentation requires network redesign — start architecture review now, implement in phases"

**Output Format** (JSON only):

{
  "dimensions": [
    {"dimension": "gap_prioritization", "score": <0-3>, "weight": 1.0}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## B9: Risk Identification

**Dimension**: risk_identification
**Weight**: 1.0
**Category**: Gap & Risk Analysis

### Anchored Scale (0-3)

| Score | Anchor | Example |
|-------|--------|---------|
| 0 | Misses primary risks or identifies irrelevant risks | Discusses brand reputation risk for an air-gapped OT system; misses compromise path from shared credentials |
| 1 | Identifies obvious risks but misses cascading or multi-dimensional risks | "Shared credentials are a security risk" without tracing attack paths or compliance implications |
| 2 | Comprehensive risk identification: technical, compliance, and operational dimensions | "Risks: (1) No non-repudiation — actions unattributable (technical). (2) Audit failure — shared accounts violate 5.1.5 (compliance). (3) Essential service disruption via undetected malicious access (operational)" |
| 3 | All dimensions plus cascading risk chains and quantified impact | Adds "Cascading path: shared credentials → no attribution → undetected insider action → OT manipulation → essential service disruption → Commissioner notification under Section 14 within 2 hours" |

### Judge Prompt Template

```
You are an expert CCoP 2.0 compliance auditor evaluating a model's risk identification capability.

**Task**: Evaluate how comprehensively the response identifies risks across technical, compliance, and operational dimensions.

**Question**:
{question}

**Model Response**:
{response}

**Expected Response**:
{expected_response}

**Key Facts**:
{key_facts}

**Evaluation Instructions**:

Think step-by-step about the response quality.

The "risk_identification" dimension assesses whether the model:
- Identifies technical risks (attack paths, vulnerabilities)
- Identifies compliance risks (CCoP violations, audit findings)
- Identifies operational risks (essential service disruption)
- Traces cascading risk chains specific to CII environments

**Anchored Scale**:

Score 0 (Incorrect): Misses primary risks or identifies irrelevant risks.
Example: Discusses brand reputation risk for an air-gapped OT system; misses compromise path from shared credentials.

Score 1 (Partial): Identifies obvious risks but misses cascading or multi-dimensional risks.
Example: "Shared credentials are a security risk" without tracing attack paths or compliance implications.

Score 2 (Complete): Comprehensive risk identification: technical, compliance, and operational dimensions.
Example: "Risks: (1) No non-repudiation — actions unattributable (technical). (2) Audit failure — shared accounts violate 5.1.5 (compliance). (3) Essential service disruption via undetected malicious access (operational)"

Score 3 (Exceeds): All dimensions plus cascading risk chains and quantified impact.
Example: Adds "Cascading path: shared credentials → no attribution → undetected insider action → OT manipulation → essential service disruption → Commissioner notification under Section 14 within 2 hours"

**Output Format** (JSON only):

{
  "dimensions": [
    {"dimension": "risk_identification", "score": <0-3>, "weight": 1.0}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## B10: Risk Justification Coherence

**Dimension**: risk_justification_coherence
**Weight**: 1.0
**Category**: Gap & Risk Analysis

### Anchored Scale (0-3)

| Score | Anchor | Example |
|-------|--------|---------|
| 0 | Circular reasoning or unjustified risk claims | "This is risky because it's not secure" |
| 1 | Some reasoning but logical gaps or unsupported claims | "Delayed patching increases risk because vulnerabilities exist" without explaining exploit window or CII impact |
| 2 | Coherent causal chain from vulnerability to impact | "6-month patch delay → known CVEs remain exploitable → internet-facing CII exposed → weaponized exploit available within weeks of disclosure → essential service disruption. CCoP 5.6.4 requires 2-week remediation for critical patches specifically because of this exploit window" |
| 3 | Coherent chain plus regulatory consequence and organizational impact | Adds "Non-compliance finding in CSA audit → enforcement action under Cybersecurity Act Section 18 → potential designation conditions per Section 9" |

### Judge Prompt Template

```
You are an expert CCoP 2.0 compliance auditor evaluating a model's risk justification coherence.

**Task**: Evaluate how logically the response explains causal chains from vulnerabilities to impacts.

**Question**:
{question}

**Model Response**:
{response}

**Expected Response**:
{expected_response}

**Key Facts**:
{key_facts}

**Evaluation Instructions**:

Think step-by-step about the response quality.

The "risk_justification_coherence" dimension assesses whether the model:
- Provides coherent causal chains (not circular reasoning)
- Connects vulnerabilities to specific CII impacts
- References CCoP requirements in justification
- Explains regulatory and organizational consequences

**Anchored Scale**:

Score 0 (Incorrect): Circular reasoning or unjustified risk claims.
Example: "This is risky because it's not secure"

Score 1 (Partial): Some reasoning but logical gaps or unsupported claims.
Example: "Delayed patching increases risk because vulnerabilities exist" without explaining exploit window or CII impact.

Score 2 (Complete): Coherent causal chain from vulnerability to impact.
Example: "6-month patch delay → known CVEs remain exploitable → internet-facing CII exposed → weaponized exploit available within weeks of disclosure → essential service disruption. CCoP 5.6.4 requires 2-week remediation for critical patches specifically because of this exploit window"

Score 3 (Exceeds): Coherent chain plus regulatory consequence and organizational impact.
Example: Adds "Non-compliance finding in CSA audit → enforcement action under Cybersecurity Act Section 18 → potential designation conditions per Section 9"

**Output Format** (JSON only):

{
  "dimensions": [
    {"dimension": "risk_justification_coherence", "score": <0-3>, "weight": 1.0}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## B11: Proportional Judgment

**Dimension**: proportional_judgment
**Weight**: 1.0
**Category**: Reasoning Quality

### Anchored Scale (0-3)

| Score | Anchor | Example |
|-------|--------|---------|
| 0 | Grossly misjudges severity (critical risk called low, or minor issue called critical) | "6-month patch delay on internet-facing CII is low risk" |
| 1 | Correct direction but wrong magnitude | "6-month patch delay is concerning" without assessing severity relative to CII criticality and exposure |
| 2 | Proportional assessment with appropriate severity level and justification | "Critical risk: 6-month delay on internet-facing CII creates weaponizable attack surface. Essential service disruption potential elevates beyond standard IT risk" |
| 3 | Proportional assessment plus comparative context or cascading impact analysis | Adds comparison to CCoP timeline requirements (2 weeks critical / 1 month standard), quantifies deviation, and traces cascading impact path |

### Judge Prompt Template

```
You are an expert CCoP 2.0 compliance auditor evaluating a model's proportional judgment capability.

**Task**: Evaluate whether the response assesses severity proportional to CII criticality and CCoP requirements.

**Question**:
{question}

**Model Response**:
{response}

**Expected Response**:
{expected_response}

**Key Facts**:
{key_facts}

**Evaluation Instructions**:

Think step-by-step about the response quality.

The "proportional_judgment" dimension assesses whether the model:
- Judges severity proportional to CII criticality (not generic IT risk)
- Compares against CCoP timeline/control requirements
- Justifies severity with specific impact scenarios
- Avoids over- or under-stating risk magnitude

**Anchored Scale**:

Score 0 (Incorrect): Grossly misjudges severity (critical risk called low, or minor issue called critical).
Example: "6-month patch delay on internet-facing CII is low risk"

Score 1 (Partial): Correct direction but wrong magnitude.
Example: "6-month patch delay is concerning" without assessing severity relative to CII criticality and exposure.

Score 2 (Complete): Proportional assessment with appropriate severity level and justification.
Example: "Critical risk: 6-month delay on internet-facing CII creates weaponizable attack surface. Essential service disruption potential elevates beyond standard IT risk"

Score 3 (Exceeds): Proportional assessment plus comparative context or cascading impact analysis.
Example: Adds comparison to CCoP timeline requirements (2 weeks critical / 1 month standard), quantifies deviation, and traces cascading impact path.

**Output Format** (JSON only):

{
  "dimensions": [
    {"dimension": "proportional_judgment", "score": <0-3>, "weight": 1.0}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## B12: Audit Perspective Alignment

**Dimension**: audit_perspective_alignment
**Weight**: 1.0
**Category**: Audit & Evidence

### Anchored Scale (0-3)

| Score | Anchor | Example |
|-------|--------|---------|
| 0 | Responds from implementer perspective, not auditor perspective | "We should implement MFA" instead of "An auditor would verify MFA implementation evidence" |
| 1 | Acknowledges audit perspective but reasoning is generic | "Auditors would check compliance" without specific CSA methodology |
| 2 | Demonstrates CSA auditor reasoning: evidence-based, clause-focused, finding-structured | "A CSA auditor would: (1) Request MFA deployment logs for all remote access points. (2) Test a sample of accounts for MFA enforcement. (3) Verify alignment with Clause 5.1.5 requirements. Finding: if any remote access path lacks MFA, classify as critical non-compliance" |
| 3 | Audit perspective plus finding severity classification and remediation timeline expectations | Adds "This would be classified as a major finding requiring remediation within 30 days. Auditor would expect corrective action plan with implementation evidence at follow-up" |

### Judge Prompt Template

```
You are an expert CCoP 2.0 compliance auditor evaluating a model's audit perspective alignment.

**Task**: Evaluate whether the response demonstrates CSA auditor reasoning and methodology.

**Question**:
{question}

**Model Response**:
{response}

**Expected Response**:
{expected_response}

**Key Facts**:
{key_facts}

**Evaluation Instructions**:

Think step-by-step about the response quality.

The "audit_perspective_alignment" dimension assesses whether the model:
- Responds from auditor perspective (not implementer)
- Uses evidence-based reasoning (logs, samples, verification)
- Structures findings per CSA audit methodology
- Classifies finding severity and remediation timelines

**Anchored Scale**:

Score 0 (Incorrect): Responds from implementer perspective, not auditor perspective.
Example: "We should implement MFA" instead of "An auditor would verify MFA implementation evidence"

Score 1 (Partial): Acknowledges audit perspective but reasoning is generic.
Example: "Auditors would check compliance" without specific CSA methodology.

Score 2 (Complete): Demonstrates CSA auditor reasoning: evidence-based, clause-focused, finding-structured.
Example: "A CSA auditor would: (1) Request MFA deployment logs for all remote access points. (2) Test a sample of accounts for MFA enforcement. (3) Verify alignment with Clause 5.1.5 requirements. Finding: if any remote access path lacks MFA, classify as critical non-compliance"

Score 3 (Exceeds): Audit perspective plus finding severity classification and remediation timeline expectations.
Example: Adds "This would be classified as a major finding requiring remediation within 30 days. Auditor would expect corrective action plan with implementation evidence at follow-up"

**Output Format** (JSON only):

{
  "dimensions": [
    {"dimension": "audit_perspective_alignment", "score": <0-3>, "weight": 1.0}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## B13: Evidence Expectation Awareness

**Dimension**: evidence_expectation_awareness
**Weight**: 1.0
**Category**: Audit & Evidence

### Anchored Scale (0-3)

| Score | Anchor | Example |
|-------|--------|---------|
| 0 | Doesn't mention audit evidence or mentions wrong evidence types | "The organization should have a security strategy" without specifying auditable artifacts |
| 1 | Mentions evidence broadly but not specific to the control | "Auditors want documentation" |
| 2 | Specific evidence artifacts for the control in question | "For Clause 5.6.4 (patch management), auditors expect: (1) Patch deployment logs with timestamps. (2) Vulnerability scan reports showing remediation. (3) Exception register for patches exceeding timelines. (4) Risk acceptance documentation for deferred patches" |
| 3 | Specific evidence plus testing methodology and common deficiencies | Adds "Auditors typically sample 10-20% of systems to verify patch currency. Common deficiency: organizations provide policy documents but cannot demonstrate actual patch deployment timelines" |

### Judge Prompt Template

```
You are an expert CCoP 2.0 compliance auditor evaluating a model's evidence expectation awareness.

**Task**: Evaluate whether the response demonstrates awareness of specific audit evidence requirements.

**Question**:
{question}

**Model Response**:
{response}

**Expected Response**:
{expected_response}

**Key Facts**:
{key_facts}

**Evaluation Instructions**:

Think step-by-step about the response quality.

The "evidence_expectation_awareness" dimension assesses whether the model:
- Specifies auditable artifacts (not just "documentation")
- Tailors evidence to the specific CCoP control
- Describes audit testing methodology
- Identifies common evidence deficiencies

**Anchored Scale**:

Score 0 (Incorrect): Doesn't mention audit evidence or mentions wrong evidence types.
Example: "The organization should have a security strategy" without specifying auditable artifacts.

Score 1 (Partial): Mentions evidence broadly but not specific to the control.
Example: "Auditors want documentation"

Score 2 (Complete): Specific evidence artifacts for the control in question.
Example: "For Clause 5.6.4 (patch management), auditors expect: (1) Patch deployment logs with timestamps. (2) Vulnerability scan reports showing remediation. (3) Exception register for patches exceeding timelines. (4) Risk acceptance documentation for deferred patches"

Score 3 (Exceeds): Specific evidence plus testing methodology and common deficiencies.
Example: Adds "Auditors typically sample 10-20% of systems to verify patch currency. Common deficiency: organizations provide policy documents but cannot demonstrate actual patch deployment timelines"

**Output Format** (JSON only):

{
  "dimensions": [
    {"dimension": "evidence_expectation_awareness", "score": <0-3>, "weight": 1.0}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## B14: Recommendation Quality

**Dimension**: recommendation_quality
**Weight**: 1.0
**Category**: Remediation Planning

### Anchored Scale (0-3)

| Score | Anchor | Example |
|-------|--------|---------|
| 0 | Generic or inapplicable advice | "Improve security posture" or "Implement zero trust" without CII-specific guidance |
| 1 | Relevant but vague recommendations | "Implement MFA and improve patching" without specifics on scope, timeline, or CII constraints |
| 2 | Specific, actionable recommendations proportionate to risk | "Remediation plan: (1) Deploy MFA on all remote access within 2 weeks (critical). (2) Implement network segmentation between IT/OT zones within 3 months (high). (3) Establish automated patch scanning within 1 month (medium). Each addresses specific CCoP clauses: 5.1.5, 10.2.3, 5.6.1" |
| 3 | Actionable plus phased implementation plan and resource considerations | Adds "Phase 1 (quick wins, 2 weeks): MFA, disable unused remote access. Phase 2 (1 month): patch scanning, baseline configuration. Phase 3 (3 months): network redesign. Resource: requires dedicated project team for Phase 3" |

### Judge Prompt Template

```
You are an expert CCoP 2.0 compliance auditor evaluating a model's recommendation quality.

**Task**: Evaluate whether the response provides specific, actionable, and CII-appropriate remediation recommendations.

**Question**:
{question}

**Model Response**:
{response}

**Expected Response**:
{expected_response}

**Key Facts**:
{key_facts}

**Evaluation Instructions**:

Think step-by-step about the response quality.

The "recommendation_quality" dimension assesses whether the model:
- Provides specific, actionable recommendations (not generic advice)
- Proportions recommendations to risk severity
- References specific CCoP clauses addressed
- Includes phased implementation and resource considerations

**Anchored Scale**:

Score 0 (Incorrect): Generic or inapplicable advice.
Example: "Improve security posture" or "Implement zero trust" without CII-specific guidance.

Score 1 (Partial): Relevant but vague recommendations.
Example: "Implement MFA and improve patching" without specifics on scope, timeline, or CII constraints.

Score 2 (Complete): Specific, actionable recommendations proportionate to risk.
Example: "Remediation plan: (1) Deploy MFA on all remote access within 2 weeks (critical). (2) Implement network segmentation between IT/OT zones within 3 months (high). (3) Establish automated patch scanning within 1 month (medium). Each addresses specific CCoP clauses: 5.1.5, 10.2.3, 5.6.1"

Score 3 (Exceeds): Actionable plus phased implementation plan and resource considerations.
Example: Adds "Phase 1 (quick wins, 2 weeks): MFA, disable unused remote access. Phase 2 (1 month): patch scanning, baseline configuration. Phase 3 (3 months): network redesign. Resource: requires dedicated project team for Phase 3"

**Output Format** (JSON only):

{
  "dimensions": [
    {"dimension": "recommendation_quality", "score": <0-3>, "weight": 1.0}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## B15: Feasibility Assessment

**Dimension**: feasibility_assessment
**Weight**: 1.0
**Category**: Remediation Planning

### Anchored Scale (0-3)

| Score | Anchor | Example |
|-------|--------|---------|
| 0 | Recommends actions infeasible in CII environments | "Shut down OT systems for comprehensive patching this weekend" for a 24/7 essential service |
| 1 | Recommendations possible but ignore CII operational constraints | "Apply all patches immediately" without considering OT testing requirements or maintenance windows |
| 2 | Recommendations account for CII constraints (uptime, safety, legacy) | "For OT systems: test patches in staging environment first, deploy during scheduled maintenance window, maintain rollback capability. For legacy PLCs that cannot be patched: implement compensating controls (network isolation, enhanced monitoring)" |
| 3 | Feasible recommendations plus contingency planning and risk acceptance criteria | Adds "If patching window unavailable for 3+ months: document risk acceptance per Section 3.2, implement compensating controls, schedule review at next maintenance cycle" |

### Judge Prompt Template

```
You are an expert CCoP 2.0 compliance auditor evaluating a model's feasibility assessment.

**Task**: Evaluate whether the response accounts for CII operational constraints and essential service requirements.

**Question**:
{question}

**Model Response**:
{response}

**Expected Response**:
{expected_response}

**Key Facts**:
{key_facts}

**Evaluation Instructions**:

Think step-by-step about the response quality.

The "feasibility_assessment" dimension assesses whether the model:
- Recognizes CII constraints (24/7 uptime, safety-critical, legacy systems)
- Adapts recommendations to operational realities
- Provides compensating controls for infeasible mitigations
- Includes contingency planning and risk acceptance criteria

**Anchored Scale**:

Score 0 (Incorrect): Recommends actions infeasible in CII environments.
Example: "Shut down OT systems for comprehensive patching this weekend" for a 24/7 essential service.

Score 1 (Partial): Recommendations possible but ignore CII operational constraints.
Example: "Apply all patches immediately" without considering OT testing requirements or maintenance windows.

Score 2 (Complete): Recommendations account for CII constraints (uptime, safety, legacy).
Example: "For OT systems: test patches in staging environment first, deploy during scheduled maintenance window, maintain rollback capability. For legacy PLCs that cannot be patched: implement compensating controls (network isolation, enhanced monitoring)"

Score 3 (Exceeds): Feasible recommendations plus contingency planning and risk acceptance criteria.
Example: Adds "If patching window unavailable for 3+ months: document risk acceptance per Section 3.2, implement compensating controls, schedule review at next maintenance cycle"

**Output Format** (JSON only):

{
  "dimensions": [
    {"dimension": "feasibility_assessment", "score": <0-3>, "weight": 1.0}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## B16: Residual Risk Awareness

**Dimension**: residual_risk_awareness
**Weight**: 1.0
**Category**: Gap & Risk Analysis

### Anchored Scale (0-3)

| Score | Anchor | Example |
|-------|--------|---------|
| 0 | Claims controls eliminate all risk, or ignores residual risk | "With MFA implemented, remote access is fully secure" |
| 1 | Acknowledges residual risk exists but doesn't specify | "Some risk remains even with MFA" |
| 2 | Identifies specific residual risks post-controls | "Residual risks after MFA: (1) MFA bypass techniques (SIM swap, token theft). (2) Authorized user misuse. (3) MFA fatigue attacks. Monitoring controls needed to detect these" |
| 3 | Specific residual risks plus acceptance criteria and monitoring strategy | Adds "Residual risk accepted if: probability < X given compensating monitoring, impact limited by segmentation, and quarterly review confirms no new bypass techniques" |

### Judge Prompt Template

```
You are an expert CCoP 2.0 compliance auditor evaluating a model's residual risk awareness.

**Task**: Evaluate whether the response recognizes that controls reduce but don't eliminate risk.

**Question**:
{question}

**Model Response**:
{response}

**Expected Response**:
{expected_response}

**Key Facts**:
{key_facts}

**Evaluation Instructions**:

Think step-by-step about the response quality.

The "residual_risk_awareness" dimension assesses whether the model:
- Acknowledges residual risk remains after controls
- Specifies concrete residual risks (not just "some risk")
- Describes monitoring strategies for residual risks
- Provides acceptance criteria for remaining risk

**Anchored Scale**:

Score 0 (Incorrect): Claims controls eliminate all risk, or ignores residual risk.
Example: "With MFA implemented, remote access is fully secure"

Score 1 (Partial): Acknowledges residual risk exists but doesn't specify.
Example: "Some risk remains even with MFA"

Score 2 (Complete): Identifies specific residual risks post-controls.
Example: "Residual risks after MFA: (1) MFA bypass techniques (SIM swap, token theft). (2) Authorized user misuse. (3) MFA fatigue attacks. Monitoring controls needed to detect these"

Score 3 (Exceeds): Specific residual risks plus acceptance criteria and monitoring strategy.
Example: Adds "Residual risk accepted if: probability < X given compensating monitoring, impact limited by segmentation, and quarterly review confirms no new bypass techniques"

**Output Format** (JSON only):

{
  "dimensions": [
    {"dimension": "residual_risk_awareness", "score": <0-3>, "weight": 1.0}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## B17: Policy vs Practice Distinction

**Dimension**: policy_vs_practice_distinction
**Weight**: 1.0
**Category**: Compliance Assessment

### Anchored Scale (0-3)

| Score | Anchor | Example |
|-------|--------|---------|
| 0 | Treats documented policy as proof of compliance | "The organization has a patch management policy, so they are compliant" |
| 1 | Acknowledges distinction exists but doesn't elaborate | "Having a policy doesn't mean it's implemented" |
| 2 | Clearly distinguishes policy from practice with audit perspective | "Auditors verify enforcement, not just documentation. A patch policy that allows 6-month delays in practice violates Clause 5.6.4's 2-week/1-month timelines regardless of what the policy document states" |
| 3 | Adds evidence requirements and audit testing methodology | "Auditors would request patch deployment logs, not just the policy document. They test a sample of systems to verify actual patch currency against stated timelines" |

### Judge Prompt Template

```
You are an expert CCoP 2.0 compliance auditor evaluating a model's policy vs practice distinction.

**Task**: Evaluate whether the response distinguishes documented policy from actual implementation.

**Question**:
{question}

**Model Response**:
{response}

**Expected Response**:
{expected_response}

**Key Facts**:
{key_facts}

**Evaluation Instructions**:

Think step-by-step about the response quality.

The "policy_vs_practice_distinction" dimension assesses whether the model:
- Recognizes policy documentation is not proof of compliance
- Explains auditors verify enforcement, not just documents
- Describes what actual practice evidence looks like
- Specifies audit testing methodology

**Anchored Scale**:

Score 0 (Incorrect): Treats documented policy as proof of compliance.
Example: "The organization has a patch management policy, so they are compliant"

Score 1 (Partial): Acknowledges distinction exists but doesn't elaborate.
Example: "Having a policy doesn't mean it's implemented"

Score 2 (Complete): Clearly distinguishes policy from practice with audit perspective.
Example: "Auditors verify enforcement, not just documentation. A patch policy that allows 6-month delays in practice violates Clause 5.6.4's 2-week/1-month timelines regardless of what the policy document states"

Score 3 (Exceeds): Adds evidence requirements and audit testing methodology.
Example: "Auditors would request patch deployment logs, not just the policy document. They test a sample of systems to verify actual patch currency against stated timelines"

**Output Format** (JSON only):

{
  "dimensions": [
    {"dimension": "policy_vs_practice_distinction", "score": <0-3>, "weight": 1.0}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## B18: Responsibility Attribution

**Dimension**: responsibility_attribution
**Weight**: 1.0
**Category**: Legal Framework

### Anchored Scale (0-3)

| Score | Anchor | Example |
|-------|--------|---------|
| 0 | Assigns wrong responsibilities or confuses institutional roles | Says CSA is responsible for implementing controls (it's the CIIO); says CIIO can designate CII (it's the Commissioner) |
| 1 | Correct general attribution but misses Singapore-specific nuance | "The organization is responsible for compliance" without specifying CIIO obligations under the Act |
| 2 | Correctly attributes responsibilities to CIIO, CSA, Commissioner with legal basis | "CIIO responsibility: comply with CCoP, appoint designated person (Section 12), report incidents within 2 hours (Section 14). Commissioner: designate CII (Section 7), conduct audits (Section 15). CSA: issue codes of practice (Section 11)" |
| 3 | Correct attribution plus enforcement consequences and appeal rights | Adds "Non-compliance: Commissioner may issue written directions (Section 18). CIIO may appeal designation to Minister within 30 days (Section 17). Penalties under Section 32 for failure to comply with directions" |

### Judge Prompt Template

```
You are an expert CCoP 2.0 compliance auditor evaluating a model's responsibility attribution.

**Task**: Evaluate whether the response correctly assigns responsibilities to CIIO, CSA, and Commissioner per the Cybersecurity Act.

**Question**:
{question}

**Model Response**:
{response}

**Expected Response**:
{expected_response}

**Key Facts**:
{key_facts}

**Evaluation Instructions**:

Think step-by-step about the response quality.

The "responsibility_attribution" dimension assesses whether the model:
- Correctly assigns responsibilities to CIIO, CSA, and Commissioner
- References specific sections of the Cybersecurity Act
- Distinguishes Singapore regulatory framework from generic compliance
- Describes enforcement consequences and appeal rights

**Anchored Scale**:

Score 0 (Incorrect): Assigns wrong responsibilities or confuses institutional roles.
Example: Says CSA is responsible for implementing controls (it's the CIIO); says CIIO can designate CII (it's the Commissioner).

Score 1 (Partial): Correct general attribution but misses Singapore-specific nuance.
Example: "The organization is responsible for compliance" without specifying CIIO obligations under the Act.

Score 2 (Complete): Correctly attributes responsibilities to CIIO, CSA, Commissioner with legal basis.
Example: "CIIO responsibility: comply with CCoP, appoint designated person (Section 12), report incidents within 2 hours (Section 14). Commissioner: designate CII (Section 7), conduct audits (Section 15). CSA: issue codes of practice (Section 11)"

Score 3 (Exceeds): Correct attribution plus enforcement consequences and appeal rights.
Example: Adds "Non-compliance: Commissioner may issue written directions (Section 18). CIIO may appeal designation to Minister within 30 days (Section 17). Penalties under Section 32 for failure to comply with directions"

**Output Format** (JSON only):

{
  "dimensions": [
    {"dimension": "responsibility_attribution", "score": <0-3>, "weight": 1.0}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## B19: Cross-Scenario Consistency

**Dimension**: cross_scenario_consistency
**Weight**: 1.0
**Category**: Reasoning Quality

### Anchored Scale (0-3)

| Score | Anchor | Example |
|-------|--------|---------|
| 0 | Contradicts own reasoning across similar scenarios | Rates shared vendor accounts as "critical risk" in one scenario but "acceptable" in a structurally identical one |
| 1 | Same conclusion but different reasoning, or inconsistent emphasis | Same verdict but different risk factors cited for equivalent setups |
| 2 | Consistent reasoning and conclusions across similar scenarios | Same risk assessment framework applied, same factors considered, proportional conclusions |
| 3 | Consistent plus explicitly acknowledges scenario parallels | "This scenario is structurally equivalent to [X] — the same risk factors apply because..." |

### Judge Prompt Template

```
You are an expert CCoP 2.0 compliance auditor evaluating a model's cross-scenario consistency.

**Task**: Evaluate whether the response applies consistent reasoning and conclusions to structurally similar scenarios.

**Question**:
{question}

**Model Response**:
{response}

**Expected Response**:
{expected_response}

**Key Facts**:
{key_facts}

**Related Scenarios** (if available):
{related_scenarios}

**Evaluation Instructions**:

Think step-by-step about the response quality.

The "cross_scenario_consistency" dimension assesses whether the model:
- Applies the same risk assessment framework to similar scenarios
- Reaches proportional conclusions for equivalent setups
- Avoids contradicting its own reasoning
- Explicitly acknowledges structural parallels

**Note**: If related_scenarios is not provided, evaluate internal consistency only (does the response contradict itself within a single answer).

**Anchored Scale**:

Score 0 (Incorrect): Contradicts own reasoning across similar scenarios.
Example: Rates shared vendor accounts as "critical risk" in one scenario but "acceptable" in a structurally identical one.

Score 1 (Partial): Same conclusion but different reasoning, or inconsistent emphasis.
Example: Same verdict but different risk factors cited for equivalent setups.

Score 2 (Complete): Consistent reasoning and conclusions across similar scenarios.
Example: Same risk assessment framework applied, same factors considered, proportional conclusions.

Score 3 (Exceeds): Consistent plus explicitly acknowledges scenario parallels.
Example: "This scenario is structurally equivalent to [X] — the same risk factors apply because..."

**Output Format** (JSON only):

{
  "dimensions": [
    {"dimension": "cross_scenario_consistency", "score": <0-3>, "weight": 1.0}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## B20: Over-Specification Avoidance

**Dimension**: over_specification_avoidance
**Weight**: 1.0
**Category**: Safety Boundaries

### Anchored Scale (0-3) — BINARY SCORING ONLY

| Score | Anchor | Example |
|-------|--------|---------|
| 0 | Invents specific technical parameters CCoP doesn't mandate | "CCoP requires minimum 14-character passwords with special characters" (CCoP doesn't specify password length) |
| 3 | Correctly distinguishes mandatory requirements from implementation flexibility | "CCoP requires strong authentication controls but does not mandate specific password length. Implementation details are left to the CIIO's risk assessment" |

**CRITICAL**: This dimension uses **binary scoring only** — score 0 or 3. No partial credit (no score 1 or 2).

### Judge Prompt Template

```
You are an expert CCoP 2.0 compliance auditor evaluating a model's over-specification avoidance.

**Task**: Evaluate whether the response invents technical parameters CCoP 2.0 does not mandate.

**Question**:
{question}

**Model Response**:
{response}

**Expected Response**:
{expected_response}

**Key Facts**:
{key_facts}

**Evaluation Instructions**:

Think step-by-step about the response quality.

The "over_specification_avoidance" dimension assesses whether the model:
- Distinguishes mandatory CCoP requirements from implementation flexibility
- Avoids inventing specific technical parameters (password length, encryption algorithms, timeout values, etc.) that CCoP does not mandate
- Acknowledges when CCoP sets objectives but leaves implementation to CIIO risk assessment

**CRITICAL**: This is a **BINARY dimension** — score 0 or 3 only. No partial credit.

**Anchored Scale**:

Score 0 (Incorrect): Invents specific technical parameters CCoP doesn't mandate.
Example: "CCoP requires minimum 14-character passwords with special characters" (CCoP doesn't specify password length)

Score 3 (Correct): Correctly distinguishes mandatory requirements from implementation flexibility.
Example: "CCoP requires strong authentication controls but does not mandate specific password length. Implementation details are left to the CIIO's risk assessment"

**If the response invents ANY technical parameter not in CCoP, score 0. If clean, score 3.**

**Output Format** (JSON only):

{
  "dimensions": [
    {"dimension": "over_specification_avoidance", "score": <0 or 3 only>, "weight": 1.0}
  ],
  "justification": "<2-3 sentence explanation citing specific evidence>",
  "confidence": <0.0-1.0>
}
```

---

## Implementation Notes

### Placeholder Substitution

All templates use these placeholders:

- `{question}`: TestCase.question
- `{response}`: ModelResponse.content
- `{expected_response}`: TestCase.expected_response
- `{key_facts}`: TestCase.key_facts (JSON list)
- `{clause_reference}`: TestCase.clause_reference (if applicable)
- `{related_scenarios}`: TestCase.related_scenarios (B19 only, optional)

### JSON Parsing

All judge prompts require JSON output. Parser must:

1. Extract JSON from response (handle markdown code blocks)
2. Validate required fields: dimensions (list), justification (string), confidence (float)
3. Validate dimension scores are 0-3 integers
4. Special case B20: enforce binary 0/3 only (reject 1 or 2)

### Error Handling (Skip-and-Flag Pattern)

When judge evaluation fails:

- Do NOT use fallback conservative scores
- Create JudgeEvaluation with judge_error=True, overall_score=0.0, confidence=0.0
- Log error message for debugging
- Flag evaluation for manual review

### Dimension Name Consistency

All dimension names match criteria-establishment.md exactly:

- conditional_logic (not conditional_reasoning)
- gap_identification (not gap_detection)
- audit_perspective_alignment (not audit_alignment)
- over_specification_avoidance (not overspecification)

---

## References

- **Component 2**: [criteria-establishment.md](criteria-establishment.md) — anchor definitions source
- **LalaEval Methodology**: Sun et al. (2024) — rubric formalization approach
- **Scoring Methodology**: [scoring-methodology-updated.md](scoring-methodology-updated.md) — normalization and aggregation
- **Domain Specification**: [domain-specification.md](domain-specification.md) — benchmark-to-dimension mapping
