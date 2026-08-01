# Term-3 Final Report, New Sections (19 to 23), DRAFT

> **Placement note.** These sections are inserted after the current Section 18 (Research Arc), numbered 19 to 23. The current Section 19 (Next Steps) and Section 20 (Appendix) shift to the end and are renumbered (TBD, provisionally Section 30 onward). Section 23 (Conclusion) absorbs the old Next Steps content. When the document is reassembled, either fold the old Next Steps into Section 23 or keep it as a short forward-looking coda.
>
> **Figures.** Placeholders are marked `[FIGURE: ...]` where a diagram would help. These cover the agentic and corrective flow (Section 19), the ablation results (Section 20), and the B07-006 retrieval contrast (Section 21). They can be produced separately.
>
> **Status of numbers.** All results are the corrected figures from the completed 18-case ablation campaign, computed after the category-matching fix. Three of the ladder composites were independently re-verified against the run JSON files (hybrid 0.441, graphont 0.546, graphont-agentic with corrective 0.550). The graphont-agentic no-corrective figure of 0.560 is taken from the campaign log and should be re-verified before final submission.

---

# Agentic RAG

Sections 13 to 16 described the base ontology-guided retriever, graphont. A query is translated into graph concepts, expanded across the graph, recalled through three channels (graph, keyword, and semantic), fused by weighted reciprocal rank fusion, and reranked by a cross-encoder. Section 16.5 closed with two honest limitations of that design. Rank fusion can dilute a result that is strong in one channel but weak in the others. More importantly, the cross-encoder returns weak, tightly clustered scores on very short factoid questions. On exactly the clause-lookup queries the benchmarks stress, the reranker has little signal to separate a decisive clause from a merely on-topic one.

The graphont-agentic mode is the response to those two limitations. It is a bounded control loop wrapped around the same graphont retriever. The base mode is left unchanged, byte for byte, under the parity gate of ADR-008 and ADR-009, and every new behaviour is switched on only when the mode is graphont-agentic. It adds two capabilities. A relevance filter re-judges the retrieved pool by answer support rather than textual similarity. An optional corrective retrieval loop, a CRAG-style second round, fires only when the first pass looks weak.

## The Agentic Relevance Filter

A similarity or cross-encoder score certifies topicality, that a clause is about the same subject as the query. It does not certify answer support, whether the clause actually contains the rule, obligation, or definition the question needs. A terse governing clause and a verbose but useless on-topic clause can score almost identically, which is the reranker limitation Section 16.5 named. Calibrating a threshold on the cross-encoder score, its confidence, or the top-1 margin confirmed the problem directly. None of those scalar signals separated the cases that recalled the gold clause from the cases that missed it, so a threshold gate was left inert. The filter therefore judges answer support directly, by meaning, rather than trusting a similarity score.

After graphont retrieval assembles its candidate pool, each candidate clause is scored by a retrieval evaluator. This is an LLM (Qwen3-235B via OpenRouter, temperature 0) prompted to rate, for the question and that single clause, how much the clause helps answer the question on a three-point scale. Using the model itself to judge whether retrieved evidence supports the answer, rather than trusting a similarity score, follows the self-reflective retrieval pattern of Self-RAG [5].

| Score | Label | Meaning |
|---|---|---|
| **2** | ESSENTIAL | The clause states a rule, obligation, definition, or fact directly needed to answer the question |
| **1** | RELATED | The clause is contextually relevant but does not itself provide what is needed |
| **0** | IRRELEVANT | The clause does not help answer the question |

The prompt instructs the evaluator to judge by meaning rather than word overlap. A terse obligation can be ESSENTIAL even if it shares few words with the question, and an on-topic clause can be merely RELATED. The evaluator considers only the question and that one clause.

Clauses scoring at or above a retention threshold survive into the packed context, capped at the top-k primary clauses. The threshold (min_score) defaults to 1, which keeps RELATED and ESSENTIAL clauses and drops IRRELEVANT ones. Two safety behaviours keep the filter from ever starving generation.

- **Fail-open.** If the evaluator errors or returns unparseable output for a clause, that clause is kept. Its score is treated as unknown and it is never dropped on an infrastructure failure.
- **Empty-guard.** If the filter would eliminate every candidate, the single highest-scoring candidate is retained, so the model is never handed an empty context.

The three model roles are distinct. The retrieval evaluator (Qwen3-235B) scores clauses on the retrieval side. The independent LLM-Judge (also Qwen3-235B) scores the model's response on the evaluation side. The model under test is Llama-Primus-Reasoning. The model being evaluated never scores its own retrieval or its own answer.

The default configuration retrieves and scores 8 candidates (pool_k), retains up to 8 primary clauses (top_k), keeps clauses at score 1 or above (min_score), runs the evaluator at temperature 0, and caches evaluator results by the tuple of model, temperature, prompt version, question, and clause text so the pipeline is reproducible across runs.

## The Corrective Retrieval Loop (CRAG-lite)

The per-clause scores also drive an optional second retrieval round, adapted at the pattern level from Corrective RAG (CRAG) [4]. The idea is to assess the first retrieval and, if it looks weak, take one bounded corrective action before generating, so that only the weak cases pay the retry cost, in the spirit of Adaptive-RAG [6]. The loop borrows CRAG's shape but none of its machinery. There is no trained evaluator and no web search. The assessment is a deterministic aggregation of the answer-support scores already computed, and the whole loop is capped at one retry. Ground truth is never consulted at runtime.

**Step 1, grade the first round.** The pool's answer-support scores aggregate into one of four grades, each with a recommended action.

| Round-1 grade | Condition | Action |
|---|---|---|
| **Correct** | at least one ESSENTIAL (score 2) clause retrieved | refine, the first pass is good enough, no Round-2 |
| **Incorrect** | every scored clause is IRRELEVANT (all 0, no eval failures) | replace, discard Round-1 and retrieve afresh |
| **Ambiguous** | mixed RELATED, IRRELEVANT, or eval failures, no ESSENTIAL | supplement, keep the good Round-1 clauses and add more |
| **Empty** | no candidates at all | none, nothing to correct |

The verdict is deliberately conservative. Incorrect is claimed only when all signal is negative. Any evaluator failure pulls the case to Ambiguous rather than asserting a strong verdict from incomplete data. If the grade is Correct or Empty, the loop stops and packs the Round-1 context directly.

**Step 2, rewrite the query in neutral canonical vocabulary.** For Incorrect and Ambiguous cases under the retry cap, a lightweight rewriter (GPT-4o-mini, temperature 0) restates the question in the corpus's canonical regulatory vocabulary. This is the same acronym expansion and formal phrasing shift that HyDE performs, applied here to recover recall after a weak first pass. A neutrality post-check rejects any rewrite that leaks a verdict, using tokens such as "must comply", "exempt", or "mandatory". On rejection or any error the loop falls back to the original question, so the rewrite can only help and never bias the answer.

**Step 3, retrieve and re-score Round-2.** The rewritten query retrieves a fresh pool through the same graphont retriever. Each new candidate is re-scored by the retrieval evaluator against the original question, so answer support is always judged by the user's real intent, never by the rewrite.

**Step 4, merge.** Round-1 and Round-2 are combined according to the Step-1 action. Under replace (Incorrect), only Round-2 is kept, because the first pass had nothing worth retaining. Under supplement (Ambiguous), the Round-1 clauses that scored RELATED or better are kept, then the Round-2 clauses not already present are added, de-duplicating by clause identifier and keeping the higher score on any collision.

**Step 5, essential-first selection.** The merged pool is ordered by answer support. All ESSENTIAL (score 2) clauses come first, then RELATED (score 1) clauses fill the remaining top-k slots, with a section-diversity preference that avoids stacking sibling sub-clauses from the same parent section when alternatives exist. The selection is packed into the identical context shape every other mode uses, so generation and citation behaviour are held constant across modes. The ablation isolates retrieval alone.

`[FIGURE: graphont-agentic control flow. Query, then HyDE (off), then graphont retrieve, then per-clause answer-support scoring, then filter. Correct or Empty routes to pack. Incorrect or Ambiguous routes to rewrite, then Round-2 retrieve, then re-score, then merge (replace or supplement), then essential-first select, then pack. One bounded retry, ground truth never used at runtime.]`

**Design properties.** The loop is agentic in the workflow sense. It observes retrieval outcomes, decides whether they are adequate, chooses a corrective action, and terminates. But the decision policy is deterministic rather than an autonomous planner. It is additive (base graphont untouched), bounded (one retry), and fail-safe (every LLM step falls back to a working default). It is also clean for evaluation, because ground truth is used only offline for calibration and never in the runtime decision. Corrective retrieval is opt-in and defaults to off until the calibration evidence justifies turning it on.

## The Complete Retrieval Flow

The diagram below places the two agentic components from Sections 19.1 and 19.2 in the full pipeline. A query runs through the shared graphont backbone (concept analysis, the three retrieval channels, weighted fusion, and cross-encoder reranking), and the reranked pool then enters the agentic layer, where the answer-support filter and CRAG grade either pack the clauses directly (Correct or Empty) or run one corrective round (Incorrect or Ambiguous) first. Both paths converge at the same context-assembly and generation steps every mode shares, which is what keeps the retrieval-only ablation fair.

`[FIGURE: graphont-agentic retrieval methodology. The shared graphont backbone across the top (query analysis, tri-channel recall, weighted RRF fusion, cross-encoder rerank), the additive agentic layer below (answer-support filter, CRAG grade, and the conditional corrective sub-lane of rewrite, round-2 retrieve, round-2 eval, merge, and essential-first select), both feeding back into context assembly and the LLM.]`

---

# GraphRAG Ablation, Graph-Family Studies

Section 17 validated the graph end to end on two anchor cases and deferred the full comparison to the real test. This section reports the graph-family half of that test, the sequence of ablation studies that built the retrieval mode up from the plain ontology graph to the agentic and corrective variants. Section 21 then sets the best graph configuration against the hybrid baselines. Every study holds the model (Llama-Primus-Reasoning), the judge (Qwen3-235B), the six-dimension rubric, and the 18-case stratified sample (hash bdc4927d) fixed, keeps HyDE off throughout (ADR-011), and changes only the graph retrieval layer, so any difference is attributable to that layer alone. A control run with HyDE turned on over the best corrective configuration confirmed that choice, lowering its composite from 0.550 to 0.511 and hitting citation correctness hardest (0.69 down to 0.47 out of 3).

The five studies are listed in the order they were run, each built on the one before it, rather than sorted by score. The composite is the category-weighted Tier-3 score, and Pool over Top is candidates-scored over clauses-retained.

| # | Study (each builds on the previous) | Change introduced | Pool / Top | Composite Score | Pass / Fail Verdict |
|---|---|---|---|---:|---:|
| 1 | Ontology concept graph (graphont) | tri-channel graph retrieval, weighted fusion, rerank | 8 / 8 | 0.546 | 18 / 0 |
| 2 | + agentic answer-support filter | LLM re-scores each clause 0 / 1 / 2, drops the irrelevant | 8 / 8 | 0.560 | 18 / 0 |
| 3 | + CRAG corrective retrieval | one Round-2 rewrite and retrieve on weak grades | 8 / 8 | 0.540 | 18 / 0 |
| 4 | + wider scored pool | evaluator scores 16 candidates, keeps 8 | 16 / 8 | 0.550 | 18 / 0 |
| 5 | + wider retained context | scores and keeps 16 | 16 / 16 | 0.493 | 16 / 2 |

Read down the composite column and the story is not a climb. The plain graph already scores 0.546. The answer-support filter nudges it to 0.560, within the judge's noise. Adding corrective retrieval at the base width dips to 0.540, then widening the scored pool recovers it to 0.550. Widening the retained context as well drops it to 0.493 with two outright failures. Once the graph is in place, none of the agentic refinements moves the aggregate outside a 0.54 to 0.56 band. They reshuffle rather than lift. Two findings are worth drawing out, the dimensional trade between the filter and the corrective loop, and the clean negative from widening context.

## Filter versus Corrective, the Dimensional Trade

Studies 2 and 4 are the two strongest agentic configurations, and they are effectively tied on the aggregate (0.560 for the filter alone, 0.550 for the filter plus corrective). What the aggregate hides is that they are strong on different dimensions.

| Dimension (0 to 3) | graphont | Agentic filter (no corrective) | Filter + corrective |
|---|---:|---:|---:|
| D1 verdict | 1.22 | **1.50** | 1.44 |
| D2 justification | 2.06 | 2.28 | **2.39** |
| D3 grounding | 1.56 | **1.72** | 1.44 |
| D4 scope | 2.72 | **2.61** | 2.50 |
| D5 actionable | 1.11 | 0.89 | **1.06** |
| D6 citation | 0.61 | 0.58 | **0.69** |

The filter-only configuration wins on grounding (D3) and scope (D4), the dimensions retrieval already handled well. The corrective configuration wins on justification (D2), actionable next steps (D5), and, most importantly, citation correctness (D6 at 0.69, the highest of any mode in the whole study). Citation correctness is the exact residual Term 2 left open, and the corrective loop, which re-retrieves to recover the governing clause, is the one lever that moves it. That is why the corrective configuration, not the marginally higher filter-only one, is carried into the headline comparison of Section 21. It trades a hair of aggregate score for a real gain on the two dimensions the study identifies as the ceiling.

## A Clean Negative, Wider Context Hurts

The 16/16 corrective configuration widens not just the scored pool (from 8 to 16) but the retained context (also from 8 to 16). It drops to 0.493 with two failures, below every other graph configuration and below the noise floor. Widening the pool while holding selection at 8 was marginally positive. Widening the selection to 16 clearly degraded. The bottleneck is therefore clause precision, not context quantity. Handing the model more clauses dilutes the decisive ones rather than helping. This is reported as a deliberate negative control, not omitted.

## Confidence and the Honest Small-Sample Caveat

At eighteen cases, no configuration within this graph family separates from the others above the judge's noise. The judge is non-deterministic. Repeat scoring drifts by roughly 0.05 on the composite, with swings up to about 0.25 seen on individual cases. The entire 0.54 to 0.56 cluster (graphont, the agentic filter, and the corrective variants) is a statistical tie, and the ordering within it must not be read as a ranking. Corrective retrieval, moreover, changed retrieval or response on only 14 of the 18 cases. On the other four the packed context was identical to graphont, so any composite difference there is judge variance rather than a retrieval effect. Before publishing any ranking within the graph cluster, the top two or three configurations should be re-run on a substantially larger sample, either the full 435 cases or a 50 to 90 case stratified draw, to lift the intra-cluster differences above the noise floor.

---

# Overall Evaluation, Hybrid versus Graph Retrieval

This section sets the graph retrieval modes against the Term-2 hybrid baselines on the same fixed model, judge, rubric, and 18-case sample. Four configurations anchor the comparison: naive hybrid (the Term-2 production pipeline), hybrid with HyDE query rewriting, the plain ontology graph (graphont), and the best graph-agentic configuration (the answer-support filter plus corrective retrieval, at pool 16 and top 8). The corrective configuration is chosen over the marginally higher filter-only run because it wins the citation and actionability dimensions that matter most here, as Section 20 showed.

## Overall Composite

| Configuration | Retrieval structure | Composite Score | Pass / Fail Verdict |
|---|---|---:|---:|
| Naive hybrid | flat RAG (Term-2 baseline) | 0.441 | 13 / 5 |
| Hybrid + HyDE | flat RAG plus query rewrite | 0.484 | 16 / 2 |
| Ontology graph (graphont) | concept-graph retrieval | 0.546 | 18 / 0 |
| Graph-agentic + corrective | graph, filter, Round-2 (16 / 8) | 0.550 | 18 / 0 |

The decisive result of the term is the step from hybrid to graph. Naive hybrid scores 0.441 and fails 5 of the 18 cases. Adding HyDE lifts it to 0.484, a real but modest gain. Moving to the ontology graph lifts the composite to 0.546 and passes all 18 cases, a jump of 0.10 over naive hybrid and 0.06 over the best hybrid. This is the one comparison in the study that clears the judge's noise floor. The graph-agentic corrective configuration adds a further 0.004, which is within noise on the aggregate but, as the per-dimension table below shows, concentrates on citation correctness.

## Per-Category Breakdown

The eighteen benchmarks group into five scoring categories with weights summing to 1.0. Categories are rows and the four modes are columns, so each row shows how one category responds as retrieval moves from hybrid to graph.

| Category (weight) | Naive hybrid | Hybrid + HyDE | Graphont | Graph-agentic + corrective |
|---|---:|---:|---:|---:|
| Regulatory Applicability (0.25) | 0.367 | 0.417 | **0.556** | 0.478 |
| Compliance and Risk (0.25) | 0.384 | 0.505 | 0.481 | **0.634** |
| Remediation and Audit (0.20) | 0.352 | 0.296 | **0.556** | 0.500 |
| Governance, SG context (0.10) | 0.278 | 0.389 | **0.426** | 0.389 |
| Safety and Grounding (0.20) | **0.778** | **0.778** | 0.667 | 0.667 |

Graph retrieval wins the three categories that turn on getting the right regulatory clause, namely Regulatory Applicability, Remediation and Audit, and, with corrective, Compliance and Risk at 0.634. The corrective loop's extra retrieval pass is a targeted recall tool, and Compliance and Risk is the category where it pays off. The hybrid modes win only Safety, where the answer is that the Code does not specify something and is carried by absence rather than by retrieving a clause, so a concept graph offers no advantage. Governance is a floor for every mode.

## Per-Dimension Ceiling

Every response is scored on six dimensions, each on an anchored 0 to 3 scale (0 incorrect, 1 partial, 2 complete, 3 exceeds). For a single case the composite is the mean of the six dimension scores divided by 3, and the overall figures above additionally weight cases by category, so they do not reduce to a flat average of the columns below. The table gives the mean raw dimension score across the 18 cases.

| Configuration | D1 verdict | D2 justification | D3 grounding | D4 scope | D5 actionable | D6 citation |
|---|---:|---:|---:|---:|---:|---:|
| Naive hybrid | 0.89 | 1.50 | 1.11 | 1.94 | **0.78** | **0.58** |
| Hybrid + HyDE | 1.00 | 1.89 | 1.33 | 2.33 | **1.00** | **0.39** |
| Graphont | 1.22 | 2.06 | 1.56 | 2.72 | **1.11** | **0.61** |
| Graph-agentic + corrective | 1.44 | 2.39 | 1.44 | 2.50 | **1.06** | **0.69** |

The dimensions that depend on external regulatory fact, verdict (D1), grounding (D3), and scope (D4), climb from hybrid to graph, which is exactly where retrieval structure helps. The dimensions that depend on the model's own output discipline do not. D6 citation and D5 actionable are the floors.

- **Citation correctness (D6) never clears 0.69 out of 3, roughly a fifth to a quarter of the maximum.** The graph-agentic corrective configuration posts the best D6 (0.69), the mechanism Section 22 illustrates, but even that is capped because the model attaches loosely supported secondary citations. HyDE moves D6 the wrong way (0.58 down to 0.39), inflating fluent but unverifiable citations. Getting the right clause into context is necessary but not sufficient. Whether the model cites only what it needs is a property of the model, not of retrieval.
- **Actionable next steps (D5) sit between 0.78 and 1.11 out of 3, roughly a third of the maximum.** The model tends to stop at analysis. In the B10-001 case (Section 22) D5 is 0 across all graph modes even as verdict and grounding recover.
- **Verdict (D1) is a softer floor**, reaching only around 1.4 to 1.5 out of 3 even in the strongest modes, which means the model states the fully correct final verdict about half the time. This one does respond to retrieval, so it reads as a fine-tuning opportunity rather than a hard ceiling.

The pattern is the study's most consequential finding for what comes next in Section 23. The remaining ceiling is not in what is retrieved but in the model's citation discipline and actionability, which retrieval architecture cannot fix.

---

# Qualitative Contrast

Two worked examples make the mechanism concrete, laid out in the same side-by-side form as the Term-2 worked example in Section 9.3. Each holds the model, judge, and rubric fixed and varies only retrieval. B10-001 shows the cleanest incremental improvement up the ladder, where each retrieval step produces a visibly better answer. B07-006 shows the sharper mechanism underneath, a single governing clause that only corrective retrieval recovers.

## Incremental Improvement, B10-001 (Asset Inventory Prioritization)

**Question.** "Why should the board prioritize completing the CII asset inventory over other security initiatives?"

**Ground truth.** The answer must justify the asset inventory as a mandatory CCoP 2.0 requirement (clauses 4.1.1 and 4.1.2, Asset Management), on the grounds that unknown assets cannot be protected or monitored and that dependencies, including operational-technology links, cannot be mapped without it. The expected board action is to allocate resources and require progress reporting.

| | Hybrid (naive RAG) | Graphont | Graphont-agentic + corrective |
|---|---|---|---|
| Clauses retrieved | 3.8.5, RtF 3, **4.1.1** | AnnexC (SBD), 4.1, RtF 5.6, **4.1.1**, RtF 10.2, 3.1, 3.1.2, RtF 10.5, RtF 10.1 | AnnexC (SBD), 4.1, RtF 5.6, **4.1.1**, RtF 10.2, 3.1, RtF 10.5, RtF 10.6, **4.1.1(d)** |
| Gold clauses 4.1.1 / 4.1.2 present | 4.1.1 yes, 4.1.2 no | 4.1.1 yes, 4.1.2 no | 4.1.1 and 4.1.1(d) yes, 4.1.2 no |
| Verdict | Off-topic. Answers access control instead of asset inventory | On-topic but thin. No business-risk justification | On-topic and grounded. Adds a regulatory anchor |
| Citations used correctly? | No, none given | Partially. 4.1 correct but generic | Partially. 4.1 and 4.1.1 correct |
| Scores D1 to D6 (0 to 3) | 0, 0, 0, 1, 0, 1 | 1, 2, 2, 3, 0, 0 | 2, 3, 2, 3, 0, 1 |
| LLM Judge composite | 0.111 | 0.444 | **0.583** |

The ladder climbs in strict order and each step is a real change in the answer. Clause 4.1.1 is in context for all three modes, so the improvement is not clause recovery. It is the model progressively using what it has. Flat retrieval also hands the model the off-topic clause 3.8.5, and the model derails into a generic access-control essay that scores straight zeros. Graph retrieval anchors the answer to Section 4 (Asset Management), and verdict, justification, and scope all recover at once. The corrective round adds the granular clause 4.1.1(d) and a Cybersecurity Act anchor, lifting verdict from 1 to 2 and justification from 2 to 3. The floors from Section 21 are visible even here. Actionability (D5) stays at 0 across all three modes because none gives the board concrete next steps, and citation (D6) never exceeds 1.

## Decisive-Clause Recovery, B07-006 (Shared Administrator Credentials)

**Question.** "Identify the compliance gaps based on the following scenario. An IT team uses shared administrator credentials for emergency access, claiming individual accountability is maintained through logs."

**Ground truth.** The gap is Missing Control. The governing clause is CCoP 2.0 clause 5.2.1(c), that shared user accounts are not to be created unless necessary for operating the CII, with clause 5.2.1(d) on per-account monitoring. The critical facts are that shared accounts prevent individual accountability and that logs cannot definitively attribute actions to individuals.

| | Hybrid (naive RAG) | Graphont | Graphont-agentic + corrective |
|---|---|---|---|
| Clauses retrieved | Risk-Assessment-Guide 1.2, 7.1.4, 5.2.2 | Auditing-Guidelines 8, 7.1.4(a to c), RtF 11.10, RtF 11.1, 6.1.2(d) | Auditing-Guidelines 8, **5.2.1**, 5.2, 5.3.1(a to c), RtF 11.10, 11.23, 11.43 |
| Gold clause 5.2.1 present | No | No | **Yes, recovered** |
| Verdict | Plausible but misattributed to the wrong real clause | On-topic but grounded in the wrong section, hallucinated citations | Correct, grounded in the governing clause |
| Citations used correctly? | No, 5.3.1(a) is privileged-access authorization, not the shared-account rule | No, 7.1.4 and 11.10 are audit-process clauses | Yes, quotes 5.2.1(c) and 5.2.1(d) |
| Judge grounding note | 5.3.1(a) misattribution flagged as 1 CONTRADICTED | "1 SUPPORTED, 4 CONTRADICTED, ratio 0.2, D3 equals 0" | "4 SUPPORTED, 1 UNSUPPORTED, 0 CONTRADICTED, ratio 0.8, D3 equals 2" |
| Scores D1 to D6 (0 to 3) | 1, 2, 1, 2, 0, 1 | 1, 2, 0, 2, 1, 0 | 2, 3, 2, 2, 2, 1 |
| LLM Judge composite | 0.361 | 0.333 | **0.667** |

**Full model responses (verbatim).**

*Hybrid (naive RAG):*

> **Compliance Gap Identification:**
>
> The use of shared administrator credentials by the IT team for emergency access, with individual accountability maintained through logs, presents several compliance gaps based on CCoP 2.0 requirements:
>
> 1. **Lack of Unique Credentials**:
>    - **CCoP 2.0 Clause 5.3.1(a)** mandates that privileged access should be granted only to selected accounts authorized for such access. Using shared credentials violates this requirement as it does not ensure unique accountability.
>
> 2. **Insufficient Logging and Monitoring**:
>    - While logs are used to maintain accountability, relying solely on logs without individualized credentials may not provide sufficient granularity in identifying the specific actions performed by each user during an incident. This could hinder effective investigation and response efforts.
>
> 3. **Potential for Unauthorized Access**:
>    - Shared credentials increase the risk of unauthorized access as multiple individuals have the same set of privileges, potentially leading to misuse or compromise.
>
> 4. **Non-Compliance with Privileged Account Management**:
>    - The practice does not adhere to best practices outlined in CCoP 2.0 for managing privileged accounts, which emphasizes strict control and monitoring over such accesses.
>
> 5. **Risk of Anomalous Activity Going Undetected**:
>    - Without unique credentials, it may be challenging to detect anomalies or unauthorized activities within the logs, as all actions are attributed to a single account.
>
> 6. **Non-Compliance with Regular Review Requirements**:
>    - Clause 5.2.2 mandates a review of accounts with access every 12 months. Shared credentials might not undergo this periodic evaluation, potentially leading to outdated privileges and increased risk over time.
>
> **Actionable Steps:**
>
> 1. **Implement Unique Credentials**: Assign unique privileged accounts to each IT team member.
> 2. **Enforce Multi-Factor Authentication (MFA)**: Ensure MFA is mandatory for all privileged access to enhance security.
> 3. **Regular Account Reviews**: Conduct bi-annual reviews of all accounts, including those with shared credentials, to assess their necessity and privileges.
> 4. **Enhance Logging and Monitoring**: Implement detailed logging mechanisms that track individual actions taken by each user, facilitating better incident response and accountability.
>
> **Sources:**
> CCoP 2.0: 5.3.1(a), 5.2.2
> CCoP Response to Feedback: Not applicable
> Cybersecurity Act 2018: Section 11(7) - Not directly referenced
> Guidelines for Auditing CII: Not applicable
> Guide to Cyber Threat Modelling: Not applicable
> Guide to Conducting Cybersecurity Risk Assessment: Not applicable
> Security By Design Framework: Not applicable

*Graphont:*

> **Compliance Gap Identification**
>
> The use of shared administrator credentials for emergency access by the IT team raises several compliance concerns under CCoP 2.0:
>
> 1. **Lack of Accountability**: Shared accounts undermine individual accountability, as it is challenging to attribute actions to specific individuals. This contradicts the principle of maintaining clear audit trails and accountability for administrative activities.
>
> 2. **Non-Compliance with Access Management Requirements**: The practice violates best practices in user access management by not adhering to the requirement to maintain an inventory of privileged accounts, permissions, and privileges. CCoP 2.0 emphasizes the need for strict control over who has elevated access.
>
> 3. **Insufficient Logging and Monitoring**: Without individual credentials, it is difficult to log and monitor activities effectively. This gap aligns with the lack of logging requirements for all privileged access and activities as mandated by CCoP 2.0.
>
> 4. **Potential Anomaly Detection Challenges**: Shared accounts can mask anomalous behavior, making it harder to detect unauthorized or suspicious activities that could indicate security incidents.
>
> 5. **Risk of Unauthorized Access**: The use of shared credentials increases the risk of unauthorized access during emergencies, as there is no way to ensure that only authorized personnel are using these accounts.
>
> **Actionable Steps for Compliance**
>
> - **Implement Unique Credentials**: Assign unique administrator accounts to each IT team member to maintain accountability and enable proper logging.
>
> - **Regular Access Reviews**: Conduct regular reviews of user permissions and privileges to ensure they align with job roles and responsibilities.
>
> - **Enhance Logging Capabilities**: Ensure that all administrative activities are logged, including those performed using shared accounts during emergencies. This may involve implementing additional logging mechanisms or revising existing ones.
>
> **Sources:**
> CCoP 2.0: 7.1.4(a), (b), (c)
> CCoP Response to Feedback: 11.10(a), (b), (c)
> Risk Assessment Guide: 1.2 (Common Problems Observed)

*Graphont-agentic + corrective:*

> **Compliance Gap Identification:**
>
> The IT team's use of shared administrator credentials for emergency access violates several key requirements in CCoP 2.0:
>
> 1. **Shared User Accounts:** The code explicitly states that "shared user accounts are not created unless necessary for operating the CII" (CCoP 2.0, Section 5.2.1(c)). Using shared administrator credentials implies the creation of a shared account, which is discouraged unless absolutely essential.
>
> 2. **Privileged Access Control:** The requirement to grant privileged access only to selected accounts authorized to have such access is emphasized in multiple sections (CCoP 2.0, Sections 5.2(a), 5.3.1(a)). Shared credentials undermine this principle by allowing multiple individuals to use the same account with elevated privileges.
>
> 3. **Account Monitoring and Logging:** The code mandates monitoring activities of each account for anomalies and logging privileged access (CCoP 2.0, Section 5.2.1(d) & 5.3.1(c)). With shared credentials, it becomes challenging to attribute actions to specific individuals, hindering effective monitoring and logging.
>
> 4. **Segregation of Duties:** The principle of segregation of duties is highlighted in the feedback response (CCoP Response to Feedback, Section 11.43), which suggests that having multiple roles combined can increase risk. Shared accounts blur role boundaries, potentially violating this principle.
>
> 5. **Lack of Accountability:** While logs may exist for login attempts and VPN connections, using shared credentials means individual accountability is compromised. It's unclear who performed specific actions with the shared account, making it difficult to investigate incidents or anomalies (CCoP Response to Feedback, Section 11.23).
>
> **Actionable Steps:**
>
> - **Immediate Action:** Discontinue the use of shared administrator credentials and replace them with unique accounts for each authorized user.
> - **Inventory Management:** Maintain an updated inventory of all privileged accounts, including details of permissions and privileges assigned to each individual account.
> - **Multi-factor Authentication (MFA):** Implement MFA for all privileged access to enhance security.
> - **Logging and Monitoring:** Ensure that all privileged activities are logged comprehensively, allowing for effective monitoring and anomaly detection.
>
> **Sources:**
> CCoP 2.0: Section 5.2.1(c), 5.3.1(a-c)
> CCoP Response to Feedback: Sections 11.23, 11.43


Here graphont scores below hybrid (0.333 against 0.361), because more structure without an answer-support check moved the answer to a different wrong anchor rather than the right one. This is the GraphCompliance caution from Section 12 in practice. Attaching a graph does not by itself guarantee the right clause surfaces. Only when the answer-support filter finds no essential clause in Round-1 does the corrective loop retrieve afresh, surface clause 5.2.1, and let the model ground correctly. The gain is caused by retrieval, since the same model and prompt produce a correct answer purely because the governing clause is now in context.

The two cases together make the point. Retrieval structure is what lets the model reach the right regulatory fact, whether by anchoring to the right section (B10-001) or by recovering a single decisive clause (B07-006). But even at the top of the ladder, citation discipline (D6 at 1 of 3 in both cases) and actionability (D5 at 0 in B10-001) stay capped, because they are properties of the model's output rather than of what it retrieves. This is the D6 and D5 floor of Section 21 seen case by case.

---

# Conclusion and Open Questions

This chapter closes the year. Rather than a plan of action, it leaves the questions the study has now made answerable.

**What the year settled.** Across three terms the work separated two things that are easy to conflate: how much of Llama-Primus-Reasoning's compliance-reasoning gap is a retrieval problem and how much is a model problem. Term 1 found strong reasoning behind weak factual recall. Term 2 showed that naive hybrid retrieval recovers part of the grounding gap but leaves citation correctness and cross-clause answers open. Term 3 showed that ontology-guided graph retrieval is the decisive retrieval lever, beating naive hybrid by 0.10. Layering an agentic answer-support filter and a corrective retrieval loop on top of the graph then advanced the specific dimensions those refinements were built for, with the corrective loop delivering the study's highest citation correctness and its strongest compliance-and-risk reasoning of any configuration. Because the ablation held everything but the retrieval layer fixed, the residual that remains belongs to the model, not the pipeline. Retrieval has done what retrieval can do.

**The gaps that remain.** The study's most useful output is not the winning configuration but the precise shape of what is left. Four residuals survived the best retrieval the project could build.

- **Citation discipline.** Citation correctness never cleared 0.69 out of 3 in any mode. Even when the corrective loop retrieved the governing clause and the model quoted it, the model still attached loosely supported secondary citations. Getting the right clause into context is necessary but not sufficient. Whether the model cites only what it used is a property of the model.
- **Actionability.** Actionable next steps stayed near a third of the maximum and, if anything, fell as retrieval tightened, because the model grew more conservative about prescribing action when constrained by retrieved text.
- **Verdict completeness.** Only two of eighteen verdicts were actually wrong. The rest were directionally correct but omitted qualifications and secondary conclusions, and none earned full marks. The gap is thoroughness of the stated answer, not access to the clause.
- **Corpus boundary.** Cases that reference material outside the seven-document corpus, such as MAS TRM alignment and the incident-reporting forms of the CII Regulations, cannot be helped by retrieving from a corpus that does not contain them.

One finding cuts the other way: reasoning quality was steady across every mode. The model constructs sound arguments over whatever facts it is given. That rules out a general capability intervention and points every remaining question at factual recall and output discipline.

**What this domain demands.** Compliance reasoning is not general question answering, and the residuals this study located are not generic retrieval metrics. In a regulatory setting what matters most is the exactness of authority and fidelity to what the regulation does and does not say. A citation that names a real clause but the wrong one, or a confidently asserted requirement the Code never states, is not a minor slip but a compliance hazard, because a fabricated clause or an invented threshold flows downstream into audit trails, remediation plans, and board reports as if it were law. That is why citation correctness and resistance to over-specification matter more here than the fluency and breadth that general retrieval optimizes, and why getting them exactly right, not merely plausibly right, is the property most worth closing. The same logic elevates the qualified verdict: compliance conclusions are conditional, and the qualification that a system is out of scope unless it joins the cyber operating environment, or that the Code defers password length to industry standards, is often what decides the real case. The residuals the study isolated, citation discipline, silence-awareness, and verdict completeness, are the aspects a cybersecurity-compliance model most needs to get right, which is what makes them the target for a learning intervention rather than a footnote.

**Open questions for further research.**

*1. Where does the residual live, and is it learnable?* Three of the four residuals, citation discipline, actionability, and verdict completeness, are behaviours of how the model uses and states what it already holds in context, not failures of reasoning or of retrieval. The open question is whether these can be taught from supervised examples of well-cited, fully-qualified, action-oriented answers, or whether they are structural limits of an eight-billion-parameter model. The study makes the target narrow and measurable, which is the precondition for answering it.

*2. Where would RAFT help, and where is QLoRA the better fit?* The two candidate fine-tuning approaches address different residuals. Retrieval-augmented fine-tuning [7] trains the model on questions paired with retrieved passages, including distracting ones, and a grounded answer that cites the relevant passage verbatim. That verbatim-citation objective is precisely the exact-attribution behaviour this domain rewards, so RAFT targets the in-corpus residuals the study exposed: using retrieved context faithfully, citing only the governing clause, and grounding each claim. Standard QLoRA [8] instead writes the regulation into the model's weights, which is the natural fit for the corpus-boundary cases where there is nothing to retrieve, but it re-opens the confident-fabrication failure mode that Term 1 identified as the model's original weakness. The open question is whether the residuals split cleanly along that line, RAFT for in-corpus discipline and QLoRA for out-of-corpus recall, whether one dominates, and whether the two compose without the fine-tune eroding the reasoning quality that is currently the model's strength. Any such study should hold retrieval fixed at the best graph configuration, mirroring how this year isolated retrieval.

*3. Can Google's Open Knowledge Format close the citation and hallucination residual?* In June 2026 Google Cloud published the Open Knowledge Format (OKF), an open, vendor-neutral specification that represents an organization's curated, authoritative knowledge as a version-controlled directory of Markdown files with lightweight metadata, consumed directly by AI agents rather than through an embedding pipeline [9]. The ontology-guided knowledge graph built this year is already most of the way to an OKF layer, holding verbatim clause text, typed facts, and glossary definitions that are human-reviewed and authoritative. Where probabilistic retrieval approximates, a curated layer of this kind supplies the exact, approved fact, which is the behaviour the citation-correctness and hallucination-resistance cases reward. This opens an ablation axis orthogonal to the one this year explored. The study varied the retrieval mechanism, whereas an OKF layer varies the knowledge representation, pairing an authoritative curated source of regulatory facts with graph retrieval as the fallback for reasoning-heavy queries. The open question is whether such a hybrid closes the citation and hallucination gap that even graph retrieval could not, and whether it does so more cheaply than a fine-tune, since it changes no model weights.

The through-line is a single discipline the project held for three years: prove one layer's contribution in a controlled comparison before adding the next. The year ends with retrieval understood and the residual located. The questions above are what a fourth cycle would isolate and answer.
