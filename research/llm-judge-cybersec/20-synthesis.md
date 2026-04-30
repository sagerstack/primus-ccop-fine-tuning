# Cross-Cutting Synthesis — Themes Across the 9 Landmark Methods

Organized by theme, not by method. Each theme integrates what different methods reveal about one engineering question.

## Theme 1 — Scoring-scale design: anchored vs continuous vs pairwise

| Approach | Exemplar | Scale | Strengths | Weaknesses |
|----------|----------|-------|-----------|------------|
| Discrete anchored | G-Eval, Prometheus, ours | Integer 1-5 (G-Eval, Prometheus) or 0-3 (ours) with per-level descriptors | Interpretable, defensible to reviewers, aligns with expert rubrics | Tie-heavy integer output has coarse resolution; scoring-level boundaries are judgment calls |
| Continuous 0-1 | RAGAS, G-Eval logprob variant | Real-valued 0.0-1.0 | High resolution, smooth for correlation analysis | Loses interpretability; "0.73 faithfulness" is opaque without calibration |
| Pairwise | MT-Bench | A / B / Tie | Humans do this naturally; strong inter-judge agreement | Doesn't give per-dimension breakdown; O(n²) cost |

**Verdict for compliance QA**: Our anchored 0-3 is the right primary scale. For a dissertation, anchored scales are defensible and map to expert rubrics. G-Eval's logprob-weighted continuous score is a nice-to-have for variance reduction but requires logprob access (we use Claude API via subprocess — no direct logprob exposure). Pairwise is a useful supplementary mode when comparing two model versions (e.g., fine-tuned vs baseline).

**Don't do**: Move to continuous 0-1 as primary — loses the anchored-descriptor defensibility we need for expert validation.

## Theme 2 — Grounding and citation verification

Three increasingly rigorous patterns exist:

1. **Lexical ID check** (our current D3 first stage) — does the cited clause exist in the corpus?
2. **Text-match misattribution check** (our current D3 second stage) — does the cited clause's actual text support the claim?
3. **Atomic-claim decomposition + retrieval verification** (FActScore, RAGAS Faithfulness) — decompose the response into atomic claims; verify each against retrieved context.

We do (1) and partially (2). We do NOT do (3). The consequence: our D3 catches **fabricated clause IDs** and **clearly misattributed** references but misses **fabricated facts that sit inside real clauses** (e.g., "Clause 5.2.1 requires 14-character passwords" when 5.2.1 exists but says nothing about length).

**What FActScore + RAGAS prescribe**: separate the response into atomic claims, retrieve the relevant CCoP passage for each claim, run a per-claim SUPPORTED/UNSUPPORTED check. This is the pipeline RAGAS Faithfulness runs. Our `UNIVERSAL_JUDGE_PROMPT` does this partially but it's a SECONDARY path — the primary 5-dim judge doesn't decompose.

**Concrete convergence**: our judge should run per-claim verification as a PRE-PROCESSING step (before rubric scoring), surface the results as `{claim_verifications}` in the prompt (like `{citation_verifications}`), and let D3 score based on verified claims rather than implicit decomposition.

## Theme 3 — Hallucination detection: consistency, atomic-facts, and expected-claim matching

Three orthogonal approaches:

| Method | Signal | Requires GT? | Catches |
|--------|--------|--------------|---------|
| SelfCheckGPT | Model self-consistency across N samples | No | Knowledge-uncertainty hallucination |
| FActScore | Atomic-claim retrieval verification | Atomic-fact GT + knowledge source | All fabricated claims verifiable against knowledge source |
| Expected-claim matching (our forbidden_claims, hallucination_patterns) | Presence of pre-enumerated bad patterns | Per-case GT enumeration | Known failure modes (e.g., "CCoP 2.0 does NOT mandate X" cases in B21) |

These are complementary. FActScore has the highest ceiling (catches any unsupported claim) but highest GT cost. Our expected-claim matching has moderate ceiling and is already in place. SelfCheckGPT has zero GT cost but catches only a subset and misses systematic errors.

**For our use case**, adopting all three layered would produce:
- Model self-consistency as a confidence signal (cheap, optional).
- Per-atomic-claim retrieval verification for the main hallucination check (FActScore-style).
- Forbidden-claim / hallucination-pattern matching for benchmark-specific known failures (our current approach).

The layering cost is primarily on the FActScore layer. B21 is already hand-crafted for forbidden-claims; adding atomic-claim GT to the other 20 benchmarks is the real work.

## Theme 4 — Bias mitigation coverage

What's in scope for each method:

| Bias | G-Eval | Prometheus | MT-Bench | RAGAS | SelfCheckGPT | Ours |
|------|--------|------------|----------|-------|--------------|------|
| Position | N/A (single) | Via swap (pairwise mode) | Swap mitigation validated | N/A (per-claim) | N/A | **Not measured** |
| Verbosity | Partial (form-filling) | Not addressed explicitly | Explicitly studied | N/A | N/A | **Not addressed** |
| Self-enhancement | Flagged but not fixed | Mitigated by open weights | Mitigated by cross-family judge | N/A | N/A | **Claude judging Primus is cross-family — OK** |
| Single-sample noise | Fixed via logprob averaging | Not fixed | N/A | Not fixed | Fixed by N samples | **Not fixed** |
| Temperature effect | Not addressed | Low temp default | Low temp default | Low temp default | Adjustable | temperature=0.7 — **high, noisy** |
| Self-consistency | Not addressed | Single pass | Single pass | Single pass | Central | **Not addressed** |

Our judge has **no implemented bias controls**. Lowest-hanging fruit: N-sample majority vote (Theme 6) and lowering evaluator temperature.

## Theme 5 — Cybersecurity domain adaptation

CyberSecEval is the only cybersec-specific work in the set, and it informs us about what works in safety-critical eval:

- **Deterministic-first scoring** where possible (static analysis, MCQ keys, differential testing) — LLM-judging is the fallback, not the default.
- **Framework-grounded GT** (MITRE ATT&CK, CWE) — taxonomies are first-class, not prose references. Our `clause_reference` already follows this pattern.
- **Refusal is a scored behavior**, not a failure. FRR tests explicitly score over-refusal. Our current rubric does not reward "I cannot answer because Clause 5.9.7 does not exist" (correct B21 behavior) as a first-class outcome — it falls out implicitly from D3/forbidden_claims.
- **No reference to citation-fidelity** as a concept in CyberSecEval — their tasks don't require clause-level reasoning. **This is where CCoP evaluation is genuinely novel** and not covered by existing benchmarks.

The regulatory/compliance-QA niche is thinly populated: CyberSecEval doesn't cover it; LegalBench and CUAD are the nearest analogues. This is a dissertation contribution opportunity (claim: our rubric + schema combination is a novel artifact for regulatory-QA evaluation of LLMs).

## Theme 6 — Reliability and agreement numbers: targets and measurement

Best-in-class numbers reported by methods in our set:

| Method | Metric | Number | Context |
|--------|--------|--------|---------|
| GPT-4 vs human (MT-Bench) | Pairwise agreement | ~85% | General-purpose chat eval |
| Prometheus 1 vs human | Pearson | 0.897 | 45 custom rubrics |
| FActScore auto vs human | Error rate | <2% | Biographies, Wikipedia-grounded |
| G-Eval GPT-4 | Spearman | 0.514 | SummEval coherence |
| RAGAS faithfulness vs human | Pearson | 0.80-0.85 | WikiEval |

Our judge has **no reported number** against human judgment. This is the biggest credibility gap in the dissertation: without a judge-human agreement measurement, reviewers cannot distinguish "the model improved" from "the judge got inconsistent across runs."

**Target**: collect human labels on ~20 cases (at least 10 min per case for careful labeling = ~3-4 hours of expert time), compute Pearson or Cohen's κ between our judge and human labels, aim for ≥0.80 Pearson / ≥0.70 κ. This is the LLM-as-judge reliability bar the field uses.

## Theme 7 — Ground-truth schema design patterns

Four schema archetypes, each with distinct implications:

| Pattern | Exemplar | GT shape | What the judge gets to use |
|---------|----------|----------|---------------------------|
| **Free-text reference** | Our `expected_response`, MT-Bench | One passage per case | Implicit decomposition by judge |
| **Atomic-fact list** | FActScore, our `key_facts` partial | List of independent claims with source links | Per-claim SUPPORTED check |
| **Instance-specific rubric** | Prometheus Feedback Collection | Per-case 5-level score descriptors | Rubric-anchored judging with concrete level anchors |
| **Capability × test-type matrix** | CheckList | Template + perturbations + type tags | Expected behavior by test type (MFT pass-label, INV invariance, DIR direction) |
| **Multi-reference + citation roles** | ExpertQA, AttributionBench | Multiple valid references + per-citation role tags | Attribution check by citation role |

Our schema is **mostly free-text** (expected_response) + **partially atomic-fact** (key_facts with tiers) + **lexical-ID-only** (clause_reference). We lack per-case instance rubrics (Prometheus), lack capability×test-type tags (CheckList), and lack per-citation role metadata (ExpertQA/AttributionBench).

The schema's richness determines the judge's ceiling. **Rich GT is the primary lever** — no judge model swap compensates for thin GT.

## Theme 8 — Judge-GT coupling: what the judge needs from the GT

For each dimension in our rubric, what GT structure unlocks reliable scoring:

| Dimension | Minimum viable GT | What's missing today | Cost of adding |
|-----------|-------------------|----------------------|----------------|
| D1 verdict_accuracy | `expected_label` with typed values (compliant / non-compliant / partial / no-clause-exists) | `expected_label` exists for B02/B03 only; not consumed by 5-dim judge path | LOW — already present in data, wire into judge |
| D2 justification_quality | Reasoning-chain checklist + key-point list | `reasoning_chain` exists for B05 only; not consumed | MEDIUM — populate and wire |
| D3 factual_grounding | Atomic-claim list with per-claim source clause + role | Only partial via `key_facts`; no per-claim role ("supports-verdict" vs "context") | HIGH — atomic-claim annotation for 118 cases |
| D4 scope_appropriateness | Stated constraints list (explicit, not embedded in question) | Currently embedded in question text; judge re-extracts each time | MEDIUM — extract once into GT |
| D5 actionable_way_forward | Structured checklist of expected steps | `way_forward` embedded in `expected_response` free-text; not separated | MEDIUM — extract into `expected_way_forward: list[step]` |

Our current GT **over-serves D3** (rich ground-truth infrastructure: inventory, clause-text cache, forbidden-claims, hallucination-patterns) and **under-serves D1/D5** (structured fields exist but aren't consumed or aren't populated). This is an imbalance to correct.

## Bias check on this synthesis

Things I've flagged to avoid anchoring:

- **Trendy-method bias**: I did NOT recommend "just use GPT-5 as judge" or "fine-tune a Llama-4 judge" because evidence for dissertation use says reproducibility > SOTA. Prometheus 2 is recommended for local deployment; Claude is acceptable for primary use with the proviso that API drift is a risk.
- **Dismissal of simple approaches**: Our current anchored 0-3 rubric is a strong primary scoring scale — I didn't recommend replacing it with continuous scoring. Human-anchored rubrics outperformed continuous for our use case across the evidence (CyberSecEval prefers deterministic, Prometheus prefers anchored, the survey flags continuous as harder to calibrate).
- **Claude anchoring**: I've explicitly raised Prometheus 2 local deployment as superior for reproducibility (dissertation defense). If Claude is recommended, it's on cost/quality grounds, not familiarity.
- **Over-recommendation of 2025 methods**: the method set deliberately anchors to pre-2025 landmark work (G-Eval 2023, Prometheus 2 2024, FActScore 2023, CheckList 2020). The 2025 survey is used only for bias taxonomy, not method recommendations.

## Summary — what changes are implied by the evidence

Five evidence-backed pivots emerge:

1. **Per-claim verification step before D3 scoring** (FActScore + RAGAS convergence).
2. **N-sample majority vote with lower temperature** (MT-Bench + survey).
3. **Measure judge-human agreement on a seed set** (all methods — establishes reliability floor).
4. **Enrich GT with structured fields** (Prometheus instance-rubrics, FActScore atomic facts, CheckList test-type tags).
5. **Surface refusal-correctness as a first-class outcome** (CyberSecEval-style explicit behavior scoring — relevant to B21).

All five translate to concrete changes in the gap analysis.
