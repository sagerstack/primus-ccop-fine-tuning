<research_objective>
Research the landmark LLM-as-Judge evaluation methodologies for scoring cybersecurity question-answering systems **and** the ground-truth schema designs that enable reliable judge scoring. Then produce an engineering-focused gap analysis comparing both to our current implementation.

The output is **not** a literature review for a dissertation. It is **engineering input** for redesigning (a) our LLM judge (`src/domain/services/llm_judge_service.py`), (b) our rubric (`docs/phase-2/evaluation-rubrics.md`), and (c) our ground-truth schema (`ground-truth/test-suite/*.jsonl`). The judge and the ground truth are a coupled system — a better judge cannot overcome weak ground truth, and richer ground truth is wasted if the judge cannot consume it. Every finding must translate into a concrete keep/change/add recommendation for either the judge, the rubric, or the ground-truth schema.

Thoroughly analyze each method. Explore multiple perspectives — academic, industry-practical, and cybersecurity-domain-specific. Consider tradeoffs deeply before recommending changes. Go beyond surface summaries: for each landmark method, extract the specific scoring mechanics, prompt scaffolding, **ground-truth schema requirements**, and failure modes that would inform our implementation.
</research_objective>

<scope>
## Domain focus
Cybersecurity compliance QA under the Singapore CCoP 2.0 standard. Our judge scores LLM answers to questions like "What are the MFA requirements for CII?" against a ground truth that includes an expected verdict, expected justification, expected citations (clause IDs like 5.3.1), key facts, and a way-forward.

## Dimensions we currently score
1. **D1 verdict_accuracy** — is the compliance verdict (compliant/non-compliant/partial) correct?
2. **D2 justification_quality** — is the reasoning sound and complete?
3. **D3 factual_grounding** — are citations accurate and claims anchored to real CCoP clauses? (weighted 2×)
4. **D4 scope_appropriateness** — does the answer respect stated constraints (e.g., CII-only, Singapore-only)?
5. **D5 actionable_way_forward** — does it provide feasible next steps for a non-compliant organization?

## Our current ground-truth schema (one JSONL row per test case)
Each test case under `ground-truth/test-suite/b{NN}_*.jsonl` carries approximately:
- `test_id`, `benchmark_id`
- `question` — the prompt sent to the model under test
- `expected_response` — free-text reference answer
- `clause_reference` — list of CCoP clause IDs (e.g., `["5.3.1", "5.3.2(c)"]`)
- `expected_verdict` — compliant / non-compliant / partial (benchmark-dependent)
- `key_facts` — list of facts the answer must contain, tiered CRITICAL / IMPORTANT
- `way_forward` — expected remediation steps (free-text or list, benchmark-dependent)
- `forbidden_claims` / `hallucination_patterns` — assertions that should NOT appear
- `audit_exempt`, `notes` — provenance and audit flags

Sample file to examine: `ground-truth/test-suite/b05_control_comprehension.jsonl`

## Methods in scope (landmark only, 7-9 total across all categories)
Cover at least one method from each category below, including the ground-truth design category. Prioritize methods that are (a) highly cited, (b) actively maintained, or (c) uniquely applicable to cybersecurity/compliance QA.

### Academic papers (2023-2026)
- **G-Eval** (Liu et al., 2023) — NLG evaluation using GPT-4 with chain-of-thought and form-filling
- **Prometheus / Prometheus 2** (Kim et al., 2023/2024) — fine-tuned open-source judges with fine-grained rubrics
- **JudgeLM** or **PandaLM** — open-source judge models trained on preference data
- **MT-Bench / Chatbot Arena** (Zheng et al., 2023) — pairwise LLM-as-judge evaluation
- **FActScore** (Min et al., 2023) — atomic fact decomposition for factuality scoring
- **LLM-as-Judge survey** (e.g., "A Survey on LLM-as-a-Judge" 2024-2025) — meta-analysis of bias, reliability, calibration

### Industry frameworks
- **RAGAS** — faithfulness, answer_relevancy, context_precision/recall, answer_similarity
- **DeepEval** (Confident AI) — GEval, hallucination, bias, toxicity metrics
- **LangSmith / LangChain evals** — trajectory evals, custom evaluators
- **OpenAI evals** or **Anthropic evals patterns**
- **TruLens** — feedback functions, groundedness, context_relevance
- **Promptfoo** — assertion-based evaluation

### Cybersecurity-specific benchmarks
- **CyberSecEval / CyberSecEval 2/3** (Meta) — security-focused evaluation suites
- **CyberMetric** — MCQ cybersecurity knowledge benchmark
- **SecLLM / CyberLLMInstruct** — cybersecurity fine-tuning/evaluation methods (`docs/phase1/domain-specific-compliance-models-analysis.md` has prior analysis)
- **LalaEval** — human evaluation framework for domain-specific LLMs (already cited in CLAUDE.md)
- **RegBERT** or similar regulatory-NLP evaluation

### Hallucination detection methods
- **SelfCheckGPT** (Manakul et al., 2023) — sampling-based consistency checking
- **FActScore** (covered above) — atomic fact verification
- **Citation verification / attribution evaluation** — e.g., AttributionBench, ExpertQA methods
- **HHEM** (Vectara Hallucination Evaluation Model) or **Patronus Lynx**
- **Chain-of-Verification (CoVe)** (Dhuliawala et al., 2023)

### Ground-truth design / schema methods
These are orthogonal to the judge and address **how the reference data is structured**. Cover at least 2 of:
- **FActScore atomic-fact decomposition** — reference broken into verifiable atomic claims
- **CheckList** (Ribeiro et al., 2020 and successors) — capability-tagged test cases with MFT/INV/DIR templates
- **ExpertQA / AttributionBench** — multi-reference, per-claim citation ground truth
- **Prometheus-style instance-specific rubrics** — ground truth includes a case-specific rubric, not just a reference answer
- **RAGAS reference requirements** — what fields `answer_similarity`, `context_recall`, `faithfulness` actually need
- **HELM scenario format** or **MMLU-style structured references** — adjudication-friendly schema design
- **Checklist-annotated references** (e.g., key-point matching in ROSCOE, QAGS) — bullet lists of must-contain / must-not-contain facts
- **Domain-specific regulatory QA schemas** — any CUAD, LegalBench, SARA, or compliance-QA ground truth format that handles clause-level reasoning

## What is out of scope
- Pre-2023 methods (BLEU, ROUGE, BERTScore) unless used as a component
- Human-only evaluation frameworks (expert panels) — we want automated judges
- Pure classification benchmarks without QA reasoning
- Dissertation-style literature framing — this is an engineering artifact
</scope>

<context>
## Our current implementation (read these first)
Before starting external research, read:
- `docs/phase-2/evaluation-rubrics.md` — the UNIVERSAL 5-dim rubric specification
- `src/domain/services/llm_judge_service.py` — judge orchestration, prompt construction, citation verification, ground-truth injection
- `src/domain/entities/evaluation_metric.py` — weight constraints (0.0-1.0 per dimension)
- `src/domain/entities/test_case.py` — the ground-truth entity (fields, validators, invariants)
- `ground-truth/test-suite/b05_control_comprehension.jsonl` — sample ground-truth rows with all fields populated
- `ground-truth/test-suite/b03_conditional_compliance_reasoning.jsonl` — second sample, different benchmark shape
- `ground-truth/test-suite/b21_hallucination_over_specification.jsonl` — ground truth for the hallucination benchmark
- `docs/phase1/domain-specific-compliance-models-analysis.md` — prior analysis of cyber-LLM evaluation methods

## Known observations on our current rubric (starting hypotheses, not directives — the research may confirm, refute, or reprioritize)
- **Single-sample noise** — temperature=0.7 causes sample variance > treatment effect; no N-sample averaging or seed strategy
- **Binary verdict scoring** — D1 penalizes partially-correct verdicts the same as fully wrong
- **Citation verification is lexical** — we check if clause IDs exist in the Qdrant store but don't semantically verify the claim matches the clause
- **No calibration / self-consistency** — single judge pass, no cross-check
- **No positional / length / verbosity bias controls** — known LLM-as-judge biases uncontrolled
- **Way-forward (D5) has weak anchoring** — no structured checklist of expected steps in ground truth
- **Hallucination detection is coarse** — we detect fabricated clause IDs but not fabricated facts within real clauses
- **Safety dimension absent** — no scoring for harmful advice (e.g., "disable logging to avoid audit failures")

## Known observations on our current ground-truth schema (starting hypotheses)
- **`expected_response` is free-text** — no atomic-fact decomposition; judge must decide what counts as "the answer"
- **`key_facts` tiers exist but are underused** — CRITICAL vs IMPORTANT distinction is not mapped to dimension scoring
- **`clause_reference` is ID-only** — no expected quote, paraphrase, or role (supports-verdict vs context-only)
- **`way_forward` structure varies** — sometimes a list, sometimes prose; not adjudicable as a checklist
- **`forbidden_claims` is rarely populated** — most rows leave it empty; hallucination benchmark (B21) is the exception
- **No per-case rubric overrides** — rubric is universal, but some benchmarks may need per-case scoring anchors
- **No inter-annotator agreement data** — we don't know how reliable our expert validation actually is
- **No negative examples** — no "an answer that would score 1 looks like X" in the ground-truth schema

## Non-negotiable constraints
- Benchmark-agnostic rubric (must work for all 21 benchmarks B1-B24)
- Weights must stay in [0.0, 1.0] per EvaluationMetric invariant
- Target: dissertation Phase 3.2 evaluation already in progress — changes must be defensible, not trend-chasing

## Flexible constraints (open to change based on research)
- **Judge model choice is open** — current implementation uses Claude API, but open-source judges (Prometheus 2, JudgeLM, Llama-3.1-70B-Instruct, Qwen2.5 judges) and commercial alternatives (GPT-4o, Gemini) are all in scope. Evaluate by accuracy, cost, reproducibility, and inter-judge agreement — not vendor preference.
- **Judge deployment is open** — local (Ollama, vLLM) vs API vs hybrid are all viable. Consider reproducibility for dissertation defense (local + pinned model > API with silent updates).
- **Ground-truth schema is open to extension** — current fields (`clause_reference`, `expected_response`, `key_facts`, `way_forward`, `forbidden_claims`) can be extended or restructured. Migration cost is a factor but not a blocker.
- **Scoring scale is open** — 0-3 anchored is current; continuous (0.0-1.0), pairwise, or likert-7 are all candidates if evidence supports the change.
- **Fine-tuning a judge is in scope** — if evidence shows a fine-tuned small judge (Prometheus-style) beats a prompted frontier model on cost/agreement, include that recommendation with training-data requirements.
</context>

<research_process>

## Phase 1 — Internal baseline (do this first, 30 min)
1. Read all files listed under "Our current implementation"
2. Extract and summarize in `./research/llm-judge-cybersec/00-current-rubric-summary.md`:
   - Each dimension's exact scoring anchors (0/1/2/3 descriptors)
   - The prompt scaffolding (what ground-truth artifacts are injected)
   - The composite score formula
   - Known failure modes we've observed
3. Extract and summarize in `./research/llm-judge-cybersec/01-current-ground-truth-schema.md`:
   - Full field inventory of `test_case` with types and whether each is used by the judge
   - Field population rates across the three sample JSONL files (which fields are consistently filled vs sparse)
   - Which judge dimensions each field feeds (e.g., `key_facts[tier=CRITICAL]` → D2, D3)
   - Failure modes caused by ground-truth gaps (e.g., judge cannot verify a claim because `clause_reference` has no expected quote)
   - Sample row(s) quoted verbatim so the research can reason over concrete shape

## Phase 2 — External landmark research (parallel, use WebSearch + WebFetch + mcp__exa__web_search_exa)

For maximum efficiency, whenever you need to fetch multiple papers or framework docs, invoke all relevant tool calls simultaneously rather than sequentially.

For each landmark method (7-9 total across all categories including ground-truth design):
1. Find the canonical source (paper PDF, GitHub README, or official docs)
2. Extract:
   - **Scoring mechanics** — formula, scale, dimensions, weights (judge methods) OR schema shape (ground-truth methods)
   - **Prompt scaffolding** — what the judge sees (question, reference, answer, rubric)
   - **Ground-truth schema requirements** — exact fields/structure the method expects in the reference (be concrete: field names, types, granularity)
   - **Annotation cost & process** — how the ground truth is produced (expert, crowd, LLM-assisted); inter-annotator agreement reported
   - **Bias/reliability controls** — position swap, multi-sample, self-consistency, CoT
   - **Reported limitations** — what the authors admit doesn't work
   - **Citation/fact grounding approach** — if applicable
   - **Domain fit for cybersecurity compliance QA** — would this work for our use case?
3. Save each method summary to `./research/llm-judge-cybersec/1{N}-{method-slug}.md` (e.g., `11-g-eval.md`, `12-prometheus-2.md`, `16-factscore.md`, `17-checklist.md`)

After receiving each fetch result, carefully reflect on quality and relevance before moving on. If a source is thin or tangential, discard and pick the next-most-cited method in that category.

## Phase 3 — Cross-cutting synthesis
Write `./research/llm-judge-cybersec/20-synthesis.md` organized by theme, not by method:
- **Scoring scale design** — discrete anchored (G-Eval) vs continuous (RAGAS) vs pairwise (MT-Bench). Tradeoffs for compliance QA.
- **Grounding and citation verification** — FActScore's atomic decomposition vs RAGAS faithfulness vs our lexical clause-ID check
- **Hallucination detection** — SelfCheckGPT consistency vs CoVe verification vs expected-claim matching
- **Bias mitigation** — which biases each method controls for, which remain
- **Cybersecurity domain adaptation** — what changes when the domain is regulatory/safety-critical
- **Reliability / agreement with human judgment** — reported κ or correlation numbers per method
- **Ground-truth schema design patterns** — atomic facts vs key-points vs instance-rubrics vs multi-reference. Which judge dimensions each pattern unlocks. Annotation cost tradeoffs.
- **Judge-GT coupling** — for each scoring dimension, what is the minimum GT structure required for reliable scoring? Where does our GT under-serve our judge, and where does it over-specify fields the judge ignores?

## Phase 4 — Gap analysis (the deliverable that matters)
Write `./research/llm-judge-cybersec/30-gap-analysis.md` covering BOTH judge and ground-truth gaps:

### Judge comparison matrix (required)
Rows = our 5 dimensions + proposed new dimensions. Columns = landmark methods + our current rubric. Cells = how each method scores that dimension (or "N/A"). Makes gaps visually obvious.

### Ground-truth schema comparison matrix (required)
Rows = schema fields (ours + those introduced by landmark methods: atomic_facts, key_points, instance_rubric, expected_quotes, negative_examples, etc.). Columns = methods (our current schema, FActScore, Prometheus instance-rubric, CheckList, RAGAS requirements, ExpertQA, legal/regulatory QA schemas). Cells = present/absent/partial, with a brief note on role. Makes GT gaps visually obvious.

### Per-dimension recommendations (required)
For D1-D5 and any proposed new dimension:
- **Current state** — what we do now (judge AND ground truth side)
- **State of the art** — best method found
- **Recommendation** — keep / change / add, with justification
- **Ground-truth dependency** — what ground-truth fields must exist/change for this judge change to work
- **Implementation cost** — LOW/MED/HIGH (judge lines changed, new deps, new prompt tokens, GT migration effort)
- **Risk if not done** — what failure modes persist

### Ground-truth schema recommendations (required)
A dedicated section proposing the target GT schema:
- **Fields to add** — with type, example, which dimension it serves, annotation effort
- **Fields to change** — e.g., `clause_reference: list[str]` → `clause_reference: list[{id, expected_quote, role}]`
- **Fields to deprecate** — unused or redundant
- **Migration plan** — can this be done in-place, or does it require a v2 schema and parallel test suites?
- **Annotation burden** — rough hours per test case for expert re-annotation of all 118 rows

### Judge model recommendation (required)
Explicit recommendation on which judge model(s) to use:
- Claude API (current) vs GPT-4o vs Prometheus 2 vs Llama-3.1-70B judge vs ensemble
- Decision axes: reported human-agreement numbers, cost per test case, reproducibility, domain fit for regulatory QA
- If fine-tuning is warranted, specify training-data requirements and expected gain over prompted baseline

### Priority-ranked changes (required)
A table of recommended changes ordered by (impact × feasibility) / cost, covering BOTH judge and GT changes:
| Rank | Change | Type (Judge/GT/Both) | Affects | Impact | Cost | Evidence source |

### Safety dimension decision (required)
Explicit recommendation: should we add a D6 safety/harm dimension? If yes, propose scoring anchors AND the ground-truth fields needed to support it. If no, justify.

### Calibration & reliability decision (required)
Explicit recommendation on N-sample averaging, temperature, seed, self-consistency. Cite which landmark method's approach we'd adopt.

### Phased migration roadmap (required)
Separate "ship this week" (prompt-only changes) from "Phase 4 work" (schema migration, judge swap, fine-tuning). Each phase lists: scope, effort estimate, risk, expected score-reliability gain.

</research_process>

<deliverables>
Save all outputs under `./research/llm-judge-cybersec/`:

```
./research/llm-judge-cybersec/
  00-current-rubric-summary.md           # Phase 1 baseline (judge)
  01-current-ground-truth-schema.md      # Phase 1 baseline (ground truth)
  11-{judge-method-1-slug}.md            # Phase 2 judge method summaries
  12-{judge-method-2-slug}.md
  13-{judge-method-3-slug}.md
  14-{judge-method-4-slug}.md
  15-{judge-method-5-slug}.md
  16-{gt-method-1-slug}.md               # Phase 2 ground-truth design summaries
  17-{gt-method-2-slug}.md
  18-{gt-method-3-slug}.md               # (optional)
  20-synthesis.md                        # Phase 3 cross-cutting themes
  30-gap-analysis.md                     # Phase 4 THE DELIVERABLE
  90-sources.md                          # Bibliography with URLs, access dates
```

## Style requirements
- Markdown, no LaTeX (renders in terminal)
- Every claim backed by a source (paper link, GitHub URL, framework doc). No uncited claims.
- Tables for comparisons, not prose walls
- Inline citations in format `[Author Year](url)` — verified URLs only
- Flag uncertainty explicitly: "Confidence: LOW — only found one 2024 blog post supporting this"
- No generic LLM-slop filler ("In conclusion, LLM evaluation is an important area...")
</deliverables>

<evaluation_criteria>
The research is complete when a reader can answer all of these from `30-gap-analysis.md` alone:

1. Which specific method (by name and citation) should inform a change to each of our 5 dimensions?
2. Do we add a safety/harm dimension? What anchors? What ground-truth fields support it?
3. Do we change our scoring scale (keep 0-3 anchored, or move to continuous/pairwise)?
4. What's the single highest-ROI change we could ship this week (prompt-only, no GT migration)?
5. What's the highest-ROI change that needs Phase 4+ budget (includes GT migration or judge swap)?
6. What bias controls are we missing vs state of the art?
7. How does our citation verification compare to FActScore and RAGAS faithfulness?
8. What reported human-agreement numbers should we target?
9. What is the target ground-truth schema — which fields to add, change, deprecate?
10. What is the annotation burden of migrating our 118 test cases to the target schema?
11. Which judge model(s) should we use going forward, and why (cost / agreement / reproducibility tradeoffs)?
12. Where does our current ground truth under-serve the judge, and where does it over-specify fields the judge ignores?

## Source quality bar
- Academic claims → peer-reviewed paper or arXiv preprint with >50 citations preferred; flag preprints
- Industry framework claims → official docs or GitHub README, dated; no Medium/blog posts unless authoritative
- Cybersecurity benchmark claims → official paper or benchmark release
- Verify every URL before citing. Dead links are disqualifying.
</evaluation_criteria>

<verification>
Before declaring the research complete:

1. **Coverage check** — did you cover at least one method from each of the five source categories (academic judges, industry frameworks, cyber-specific, hallucination detection, ground-truth design)?
2. **Gap analysis test** — does `30-gap-analysis.md` answer all 12 questions in evaluation_criteria?
3. **Source audit** — open `90-sources.md`. Are all URLs live? Are all access dates present?
4. **Judge actionability test** — can a reader list 3 concrete code changes to `llm_judge_service.py` after reading only `30-gap-analysis.md`? If no, the deliverable fails.
5. **Ground-truth actionability test** — can a reader list 3 concrete schema changes to `ground-truth/test-suite/*.jsonl` (field add/change/remove) after reading only `30-gap-analysis.md`? If no, the deliverable fails.
6. **Coupling check** — for each judge recommendation, is the required ground-truth support explicitly stated? (No orphaned judge changes that assume GT fields we don't have.)
7. **Bias check on your own output** — did you over-recommend trendy 2025 methods? Did you dismiss simpler approaches (anchored rubrics, expert-written references) because they're older? Did you anchor too hard to Claude because it's our current judge? Flag any such bias explicitly in the synthesis.
8. **Length check** — gap analysis should be 3000-5000 words (expanded from 2500-4000 to accommodate GT section). Synthesis 1500-2500. Method summaries 400-800 each. If any file is outside these ranges, trim or expand.
</verification>

<success_criteria>
- All files in `./research/llm-judge-cybersec/` present and non-empty
- 7-9 landmark methods covered with named attribution (including at least 2 ground-truth design methods)
- Judge comparison matrix covers all 5 current dimensions + safety proposal
- Ground-truth schema comparison matrix covers current fields + fields introduced by landmark methods
- Priority-ranked change list covers BOTH judge and ground-truth changes with impact/cost estimates
- Every citation has a live, verified URL
- Explicit go/no-go recommendations on: safety dimension, scoring scale change, calibration strategy, judge model choice, ground-truth migration
- Phased migration roadmap separates "ship this week" from "Phase 4 work"
- Reader can derive concrete PRs for `llm_judge_service.py` AND a concrete schema migration plan for `ground-truth/test-suite/*.jsonl` from `30-gap-analysis.md` alone
</success_criteria>
