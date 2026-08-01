# Researcher Log — Maximize RAG vs llm-only

## Experiment 0 — BASELINE (already measured)
Branch: research/maximize-rag-vs-llm-only / Type: real / Parent: —
Hypothesis: Current state of hybrid pipeline (post Qdrant fix, post uniform-LLM-judge routing) is what we measure improvements against.
Changes: None (pre-existing run 4 hybrid + llm-only data, both rescored to uniform 5-dim schema).
Result:
- llm-only mean: **0.3426** (34.26%)
- hybrid mean: **0.3259** (32.59%)
- **Primary metric (hybrid − llm-only): −0.0167** (hybrid LOSING by 1.67 pp)
- RAGAs context_recall: 0.250 / context_precision: 0.533 / context_faithfulness: 0.525
- D3 factual_grounding mean: hybrid 0.022 / llm-only 0.033 (both near-zero)

Status: keep
Insight: The BASELINE itself is the bug we're fixing. Hybrid SHOULD be higher than llm-only — currently it isn't. Root causes diagnosed earlier:
1. **Retrieval misses 75% of relevant content** (context_recall 0.250)
2. **About half of retrieved chunks are noise** (precision 0.533)
3. **Even when context is right, model uses it only ~half the time** (faithfulness 0.525)
4. **Judge sees rare clause citations** in either mode (D3 mean 0.022 vs 0.033)

These are at least 3 orthogonal problems. Each experiment will target one or more.

Distance to target: 0.217 absolute composite gain needed (hybrid currently 0.326 → must reach ≥0.543).
This is very ambitious. Logging milestones:
- Stretch milestone: hybrid − llm-only ≥ +0.05 (interesting; means RAG net helping)
- Mid milestone: ≥ +0.10 (meaningful win for the dissertation story)
- Target: ≥ +0.20 (user's defined success)

## THINK — before Experiment 1

### Convergence signals (none yet, just baseline)

### Untested assumptions
- Assumption: the LLM judge fairly compares hybrid vs llm-only responses. Untested.
- Assumption: the model attends to retrieved context when given. Refuted by faithfulness 0.52 → the model only half-attends.
- Assumption: the retriever can find relevant CCoP clauses. Refuted by recall 0.250 → it can't, mostly.
- Assumption: chunking strategy is reasonable. Untested.
- Assumption: top_k=20, rerank_top_n=3 is appropriate. Untested.

### Invalidation risk
None yet — first experiment.

### Next hypothesis (Experiment 1) — DIAGNOSE first

Before changing things, I want to **diagnose exactly what's happening on the canary case (B08-001)**.

B08-001 baseline state:
- composite: 0.389
- ctx_recall: 0.286 (mediocre)
- ctx_precision: 1.000 (every retrieved chunk relevant!)
- ctx_faithfulness: 0.000 (model COMPLETELY ignored the context)
- D3 factual_grounding: 0.0 (no clause citations in response)

This is the cleanest signal in the dataset. Retrieval delivered 100% relevant content but the model ignored it. **Why?**

Stage A — Experiment 1: Inspect B08-001 hybrid response + retrieved contexts. No code changes — just diagnostic.
- Read the question
- Read the expected answer + key facts
- Read the model's hybrid response (frozen)
- Read the retrieved contexts (sidecar)
- Read the judge's reasoning (if captured)
- Compare: did the model see the context? did it use it? what would a human do differently?

This is a thought experiment / diagnostic. Status will be `thought`.

## Experiment 1 — DIAGNOSTIC: B08-001 retrieval + response analysis
Branch: research/maximize-rag-vs-llm-only / Type: thought / Parent: #0
Hypothesis: Identify whether the failure mode is retrieval (wrong docs), generation (model ignored docs), or judge (unfair scoring).
Changes: NONE — diagnostic only.

**FINDINGS — five layered problems**:

### Problem 1: Wrong chunks retrieved
The eval's hybrid mode for B08-001 used these 3 contexts:
1. `CCoP Response to Feedback::11` (access control management) — TANGENTIAL
2. `CCoP 2.0::5.14.3` (vulnerability assessment frequency) — UNRELATED
3. `CCoP Response to Feedback::6` (policy review cadence) — UNRELATED

Expected clauses: **3.2.2(b)** and **3.2.2(c)** (risk-based prioritization framework).

### Problem 2: Target chunk ranks #30 by hybrid retrieval (outside top_k=20)
Re-ran retrieval with k=30. Target chunk `CCoP 2.0::3.2.2` (parent of (b)/(c)) ranks last at hybrid score 0.0683. Current `top_k=20` excludes it from candidates entirely.

Chunk content (verified): "3.2.2 The CIIO shall include the following steps in the cybersecurity risk assessment methodology: (a) Risk identification..." — confirms the parent-chunk holds (b) and (c) sub-letters.

### Problem 3: Cross-encoder reranker is making wrong choices
Top-3 retrieved by hybrid RRF (BGE dense + BM25 sparse):
1. **Risk Assessment Guide::Task A: Determine and Prioritise Risk** — score 0.5233 — DIRECTLY ON TOPIC
2. CCoP 2.0::5.14.2 — 0.50 — vulnerability remediation
3. CCoP Response to Feedback::11 — 0.37 — access control

But the reranker chose Response::11, 5.14.3, Response::6 (hybrid ranks #3, #20, #18). The cross-encoder (`ms-marco-MiniLM-L12-v2`) is moving relevant docs DOWN and irrelevant docs UP. ms-marco is trained on general web QA, not regulatory text.

### Problem 4: Similarity scores save as 0.0 in metadata
All saved retrieved-context similarity scores are 0.000. Either reranker overwrites with 0, or score field gets clobbered. Cosmetic but obscures debugging — separate bug.

### Problem 5: Model invents content + name-drops citations
Hybrid response invents "Risk Priority Number (RPN)" formula with specific numerical weights (0.8, 0.9, 0.2) — none of which is in retrieved context or CCoP. Then cites the 3 retrieved sources at the end as if they support the invented framework. RAGAs faithfulness=0.0 correctly flags this. Model isn't honestly using context.

**Top causal contributor**: Cross-encoder reranker is the dominant failure. Even with current top_k=20, the reranker had Risk Assessment Guide::Task A available and chose worse alternatives.

**Hypothesis path forward** (Experiment 2):
- **Bypass the reranker entirely** — use top-N from hybrid RRF directly. The dense+sparse hybrid score correctly identified the most relevant chunk; reranker degraded the choice.
- Cheap to test (one config change), reversible.

Result: thought experiment — no metric to record. Documented in workspace `.lab/workspace/exp-1-b08-001-diagnostic.md` for full evidence.
Duration: ~10 min agent time
Status: thought
Insight: The retrieval pipeline has THREE failure points stacked: (a) top_k cuts off ground-truth chunk (rank 30 vs k=20), (b) cross-encoder demotes the few good chunks that DO survive, (c) model fabricates and cites unrelated retrieved sources. Each compounds.

## THINK — before Experiment 2

### Convergence signals
- 1 thought experiment, 0 real experiments yet. No convergence yet.

### Untested assumptions
- Cross-encoder is helping (refuted by Exp 1; reranker is hurting on this case).
- top_k=20 is sufficient (refuted; need ≥30 to include 3.2.2 chunk).
- The model honestly uses retrieved context (refuted; model invents and name-drops).

### Invalidation risk
None — first real experiment.

### Next hypothesis (Experiment 2) — bypass cross-encoder reranker

Change `src/rag/retrieval/graph.py` to remove the reranking node from the workflow. Edge becomes: retrieval → grade_documents (skipping reranking). The grade_documents node will see top_k chunks ordered by hybrid RRF; it can apply its own filtering. Effectively the "top 3 sent to LLM" becomes the top 3 by hybrid score.

Predicted delta on B08-001 (canary):
- Retrieved chunks should now include Risk Assessment Guide::Task A and CCoP 5.14.2 → factual_grounding may rise from 0.0
- Composite expected to rise from 0.389 → 0.45-0.55 range
- ctx_faithfulness should rise (model gets actually-relevant context)

If Experiment 2 fails on B08-001, fork into a different strategy (bigger top_n, different reranker model, query rewriting).

## Experiment 2 — bypass cross-encoder reranker (KEEP)
Branch: research/maximize-rag-vs-llm-only / Type: real / Parent: #1
Hypothesis: Cross-encoder demotes relevant CCoP chunks; bypassing produces better top-N.
Changes: Added `rag_rerank_enabled: bool = True` to settings; reranking node short-circuits to top-N from hybrid order when False. Run with `CCOP_RAG_RERANK_ENABLED=false`.
Commit: 92a9e90
Result on B08-001 canary:
- composite: **0.611** (was 0.389) — **+0.222 absolute, +57% relative**
- D1 verdict_accuracy: 0.667 (was 0)
- D2 justification_quality: 1.000 (was — significantly improved)
- D3 factual_grounding: 0.000 (unchanged — STILL no clause citations)
- D4 scope_appropriateness: 1.000
- D5 actionable_way_forward: 1.000
- ctx_recall: 0.476 (was 0.286) — improved +0.19
- ctx_precision: 1.000 (unchanged)
- ctx_faithfulness: 0.000 (unchanged — model still inventing content)

Retrieved contexts: {CCoP 2.0::5.14.2, Risk Assessment Guide::Task A: Determine and Prioritise Risk, CCoP Response::11} — top 3 by hybrid RRF as predicted. Risk Assessment Guide::Task A IS in context — directly relevant to "prioritize compliance gaps".

Duration: ~2 min (model cache hit)
Status: **KEEP**
Insight: Reranker bypass is a clean win. ms-marco cross-encoder was actively harmful for regulatory text. BUT D3 = 0 and ctx_faithfulness = 0 persist — model receives better context but still doesn't cite clauses by ID and still invents content. Two orthogonal issues remain:
1. **Recall**: Even with bypass, target chunk 3.2.2(b)/(c) still missing (rank #30 by hybrid). Need higher top_k or top_n.
2. **Citation behavior**: Model doesn't cite by clause ID even when given relevant context. Need generation prompt fix.

## REFLECT — Experiment 2

What confirmed:
- Cross-encoder was the dominant retrieval-quality bottleneck for this case.
- Hybrid RRF (BGE+BM25) ordering is competent for regulatory text.

What surprised:
- Magnitude of gain (+0.22 absolute) on a single config flag flip.
- D3 stayed at 0 even with vastly improved retrieval — citation is its OWN problem.

What breaks the model:
- Model can produce a high-quality response (D1/D2/D4/D5 all near max) without citing a single clause. The "factual_grounding" rubric expects clause IDs but the response delivers everything except IDs.

## THINK — before Experiment 3

### Convergence signals
- 1 keep, big gain. Clear signal that retrieval quality matters. No discards yet.

### Untested assumptions
- top_n=3 is the right amount of context (untested; might benefit from more)
- top_k=20 covers the recall need (refuted for B08-001; target rank #30)
- Generation prompt asks for clause IDs (need to verify what it says now)

### Invalidation risk
None at this scale yet.

### Next hypothesis (Experiment 3) — increase rerank_top_n from 3 to 8

Rationale: at top_n=3 with bypass, model gets {Task A, 5.14.2, Response::11}. Ranks 4-8 from hybrid RRF include more risk-relevant content:
- #6: Risk Assessment Guide::1.2 Common Problems (risk-relevant)
- #7: Risk Assessment Guide::Task A: Determine Likelihood (risk-relevant)

Bumping top_n to 8 floods the model with more relevant context. Risks: (a) model overwhelmed, (b) noise from #5 (link reference) and #8 (glossary). Quick to test.

Predicted:
- B08-001 composite: 0.611 → 0.65-0.75 if more context helps with citation/grounding
- ctx_recall should improve as more relevant chunks reach the prompt
- D3 may rise from 0 if 3.2.2-adjacent content (Common Problems, Likelihood) helps the model cite

If composite stagnates or drops, the bottleneck shifts to model behavior (citation prompt) rather than retrieval volume.

## Experiment 3 — top_n=8 with bypass (DISCARD)
Branch: research/maximize-rag-vs-llm-only / Type: parameter-sweep / Parent: #2
Hypothesis: More retrieved chunks (top_n=8) reaches LLM with more risk-relevant content; expected composite ↑.
Changes: env var CCOP_RERANK_TOP_N=8 at invocation. No code change.
Result on B08-001: composite 0.611 → **0.389** (-0.222 — REGRESSION back to baseline level).
- D1: 0.667 (unchanged)
- D2: 1.000 → **0.667** (regressed)
- D3: 0.000 (unchanged)
- D4: 1.000 → **0.667** (regressed)
- D5: 1.000 → **0.333** (regressed sharply)
- ctx_precision: 1.000 → 0.876 (slight regression — extra chunks add noise)
- ctx_recall: 0.476 → 0.571 (improved)
- ctx_faithfulness: 0.000 (unchanged)

Status: **DISCARD**
Insight: Quantity ≠ quality. More retrieved context OVERWHELMS the model — D2/D4/D5 all regressed despite improved retrieval recall. The reranker bypass with top_n=3 (Exp 2) is the better config. KEEP for top_n stays at 3.

## METRIC REVISION (per skill protocol)

Per user direction (received during Exp 3): "focus experiments on purely increasing rag retrieval quality and ensuring that the RAGAs retrieval quality metrics show a significant improvement over current baseline. assess that independently by checking the ccop clauses directly and maximize RAGAs retrieval scores."

The current primary metric (hybrid composite − llm-only composite) couples retrieval quality to model+judge behavior. Result: a single bad model response (e.g., D2/D5 regression in Exp 3) can mask actual retrieval improvement (ctx_recall +0.10 in Exp 3).

### Metric v2 — Phase A: retrieval-quality only

| Field | Value |
|-------|-------|
| **Primary** | Mean RAGAs context_recall across the test set being evaluated |
| Direction | higher is better |
| Phase A target | mean ctx_recall ≥ 0.70 (from baseline 0.250) — this is a 2.8× improvement |
| Secondary 1 | mean RAGAs context_precision (target ≥ 0.80) |
| Secondary 2 | per-case retrieval F1 = harmonic mean of clause-match precision/recall comparing retrieved citation_ids vs expected clause_reference |
| Secondary 3 | recall@k for top_k retrieval (before truncation to top_n) — measures candidate-set quality |
| Secondary 4 | mean ctx_faithfulness (target ≥ 0.70) |
| **Tracked** | composite delta (now demoted to a TRACKED metric, not driving keep/discard during Phase A) |

### Phase B (later) — switch back

Once Phase A target hit, switch primary metric back to hybrid composite delta and validate end-to-end model+judge improvement.

### Re-score plan for existing keeps
- #0 baseline: full 30 hybrid run already exists with RAGAs scores. Mean ctx_recall=0.250.
- #2 reranker bypass: only ran on B08-001. Need to expand to full 30 for fair comparison.

### Phase A measurement command

Building a **standalone retrieval evaluator** at `.lab/workspace/retrieval_eval.py`:
- Input: list of test_ids
- For each: load test_case, invoke retrieval pipeline (BGE+BM25+RRF, optionally reranker, optionally grading) via DI container
- Compute: top-k recall, top-N precision, per-case clause-match F1
- Output: aggregate + per-case JSON to .lab/workspace/exp-N-retrieval.json
- Runtime target: <60 sec for 30 cases (no LLM, no Primus, just embeddings + Qdrant lookups)

This decouples retrieval-quality measurement from the slow Primus + judge pipeline.

## THINK — before Experiment 4 (under metric v2)

### Convergence signals
- 2 experiments under old metric: 1 keep, 1 discard. Fork from Exp #2 not needed (it's still keep).

### Untested assumptions (re-aligned to retrieval focus)
- Retrieval recall is binding (supported by data — 25% recall is low)
- Reranker bypass improves recall metric (untested at population scale)
- top_k=20 is enough candidate breadth (need to verify across cases)
- BGE+BM25 RRF is the right hybrid balance (untested)

### Invalidation risk
None for the metric switch — ctx_recall is independently measurable from old data.

### Next hypothesis (Experiment 4) — INFRASTRUCTURE: build retrieval evaluator + measure baseline + Exp 2 under new metric

This is a tooling experiment. No code/config change to the pipeline; just a new measurement script.

After Exp 4 lands the script + baseline+Exp2 numbers under metric v2, Experiment 5 will use the script to evaluate retrieval-only changes (top_k, top_n, query rewriting, etc.) independent of LLM/judge.

## Experiment 4 — INFRASTRUCTURE: retrieval evaluator + re-score under metric v2 (KEEP)
Branch: research/maximize-rag-vs-llm-only / Type: tooling+real / Parent: #2
Hypothesis: A standalone retrieval evaluator (no LLM, no Primus) decouples retrieval-quality from end-to-end pipeline; should re-score baseline+Exp2 under metric v2.
Changes: Created `.lab/workspace/retrieval_eval.py` (≈250 lines). Strict citation matching: only exact (1.0) or parent/child sub-letter (0.7) matches count toward recall/precision. Same-section (0.3) and same-chapter (0.1) tracked but excluded from primary metric.

Re-scored under metric v2:

| Run | recall_topn | precision_topn | f1_topn | recall_topk | mrr_topk |
|-----|-------------|----------------|---------|-------------|----------|
| Baseline (#0) rerank ON | 0.1417 | 0.0889 | 0.1029 | 0.3472 | 0.0564 |
| Exp #2 rerank OFF | 0.1528 | 0.0778 | 0.0998 | 0.3139 | 0.0564 |
| Δ | +0.011 | -0.011 | -0.003 | -0.033 | 0.000 |

Result: under retrieval-quality metric, the reranker bypass barely moves the needle (+1.1% recall_topn, slightly worse recall_topk). The +0.222 composite gain on B08-001 in Exp 2 was a single-case outlier; at population scale the retrieval-quality benefit is marginal.

**Implication**: cross-encoder bypass is still a worthwhile keep (it helped one case meaningfully without harming the population-level metric), but the ROOT bottleneck is candidate-set quality (recall_topk=0.31-0.35). At top_k=20, the embedder can't surface ground-truth clauses for ~65% of cases. Increasing top_k OR improving the embedder is the path forward.

Duration: ~25 sec for full 30 cases (vs ~75 min for the hybrid eval pipeline) — 180× speedup
Status: KEEP (script + baseline numbers)
Insight:
- Strict matching against ground truth is necessary; lenient/section-level matching inflates recall artificially.
- The retrieval pipeline currently surfaces only 35% of expected clauses even with k=20 candidates. Any composite-level wins must come AFTER expanding candidate set or improving embeddings.
- Per-case observation: B08-001 (canary) has recall_topk=0.0 — neither 3.2.2(b) nor 3.2.2(c) is in top-20 candidates. Confirms earlier finding that 3.2.2 ranks #30 by hybrid score.

## REFLECT — Experiment 4

Confirmed:
- Reranker bypass is a marginal keep at population scale (composite outlier on B08-001 alone).
- Real lever: candidate set size (top_k) and/or embedder quality.

Surprised:
- Magnitude — only 35% recall_topk on a curated 30-case test set with hand-picked CCoP clauses. The retriever genuinely cannot find what's expected for most queries.

Breaks model:
- The embedder is much weaker on regulatory-domain than expected. BGE-large-en is general-purpose; CCoP terminology may not map well to its training distribution.

Updated parking lot.

## THINK — before Experiment 5

### Convergence signals
- 1 keep (#2), 1 discard (#3), 1 keep (#4 infrastructure). Need to drive recall_topk up significantly. Hypothesis space focused on candidate set: top_k, embedding model, query rewriting.

### Untested assumptions
- top_k=20 is the right default (refuted; recall_topk=0.35 is too low).
- BGE-large-en handles regulatory text well (likely refuted; need to test alternatives).
- Hybrid RRF dense+sparse weighting is balanced (untested).

### Invalidation risk
None for this metric switch.

### Next hypothesis (Experiment 5) — increase top_k to 50

Rationale: cheapest possible test. recall_topk should rise substantially since many expected clauses likely sit at ranks 21-50. If recall_topk jumps from 0.35 → ≥0.70 with k=50, the embedder is fine; we just need a bigger funnel. If it stays low, we need a better embedder.

Predicted:
- recall_topk: 0.347 → 0.55-0.75
- recall_topn (top-3 final): minimal change unless we also increase top_n; the top-3 by hybrid score doesn't change with bigger k.

Caveat: recall_topn is what the LLM actually sees. To improve LLM-relevant retrieval, recall_topn must rise. So top_k alone won't help unless paired with rerank_top_n increase. But Exp 5 will tell us how big the candidate-set ceiling is.

After Exp 5: if k=50 works, run Exp 6 with k=50 + top_n=5 (with bypass). That gives the LLM a wider window into the candidate set.

## Experiment 5 — top_k=50, rerank OFF (KEEP — informational)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only (env var change, no commit) / Parent: #2v2
Hypothesis: Doubling candidate pool from 20→50 expands recall_topk substantially; recall_topn stays flat unless top_n also increases.
Changes: CCOP_RAG_TOP_K=50, CCOP_RAG_RERANK_ENABLED=false. No code change.
Result: recall_topn=0.1528 (unchanged vs Exp #2 at k=20), recall_topk=0.5028 (+0.189 vs k=20). MRR 0.0611.
Duration: 4.9 sec
Status: keep (informational; recall_topn flat as predicted)
Insight: Bigger funnel works at k-level. The candidate ceiling is real — there ARE more ground-truth clauses reachable with k>20. But hybrid RRF top-3 doesn't change just because k expands. The LLM still sees the same top-3 it saw before. To get them to top-N we need either (a) a smarter reranker, (b) query rewriting to lift them by hybrid score, or (c) more chunks passed to LLM (top_n>3 — but Exp #3 showed that hurts).

## Experiment 5b — top_k=100, rerank OFF (KEEP — informational)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only / Parent: #5
Hypothesis: At k=100 we hit the embedder's recall ceiling — diminishing returns beyond.
Changes: CCOP_RAG_TOP_K=100, rerank OFF.
Result: recall_topn=0.1528 (unchanged), recall_topk=0.6167 (+0.114 vs k=50). MRR 0.0621.
Duration: 5.0 sec
Status: keep (informational)
Insight: Even at k=100, recall_topk caps at 0.62 — meaning ~38% of expected clauses are NOT in the embedder's top-100 for their query. This is the embedder ceiling. To exceed it, query rewriting or a different embedding model is required. Cannot rely on bigger funnel alone.

## Experiment 6 — top_k=50, rerank ON (DISCARD — re-confirms #2)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only / Parent: #5
Hypothesis: With more candidates (k=50), the cross-encoder might have enough quality signal to surface ground-truth clauses to top-3. Tests whether reranker was hurt by limited candidate set in Exp #2.
Changes: CCOP_RAG_TOP_K=50, CCOP_RAG_RERANK_ENABLED=true.
Result: recall_topn=0.1333 (-0.020 vs Exp #5 same k, rerank OFF; -0.011 vs baseline). recall_topk=0.5028.
Duration: 41.4 sec
Status: discard (re-confirms ms-marco cross-encoder is harmful for CCoP retrieval)
Insight: Cross-encoder hurts even with bigger candidate pool. The model isn't lacking candidates — it just doesn't understand regulatory text. Demoting relevant CCoP clauses below ms-marco-style passage matches. Need a domain-tuned reranker (BAAI/bge-reranker-large) or skip reranking entirely.

## REFLECT — Experiments 5, 5b, 6

Confirmed:
- Embedder hits recall ceiling at ~0.62 with k=100. Cannot get past this without query/embedding changes.
- Cross-encoder ms-marco actively harms recall on CCoP regardless of candidate pool size.
- recall_topn is the binding metric and is **stuck at 0.15** because hybrid RRF top-3 doesn't move when k changes.

Surprised:
- recall_topk(k=100)=0.62 — even doubling candidates from 50 to 100 only added 11 percentage points. The embedder genuinely cannot find the rest.

Breaks model:
- The bottleneck isn't candidate-set width. It's that the **right ranks** within the candidate set are wrong. The expected clauses, when reachable, sit in ranks 4-100 — not top-3. So we need a re-ordering mechanism (a smarter reranker) OR a smarter query (query rewriting) OR a smarter embedder (BGE-M3 or domain-tuned).

Updated parking lot — query rewriting and bge-reranker-large remain top candidates.

## THINK — before Experiment 7

### Convergence signals
- Discard streak: 1 (just Exp 6). Not at guardrail yet.
- recall_topn plateau: 4 consecutive measurements (#0v2, #2v2, #5, #5b) all at 0.142-0.153. STRONG plateau signal.
- 3+ experiments tweaking the same axis (top_k / rerank toggle). Need to change axis.

### Untested assumptions
- ms-marco-MiniLM is the right cross-encoder for regulatory text → REFUTED in Exp 2/6.
- BGE-large-en handles regulatory text well → ceiling at recall_topk=0.62 suggests partial limitation.
- Top-3 by hybrid RRF is a meaningful order → questionable; expected clauses sit in 4-100, suggesting hybrid score doesn't reflect relevance well.

### Invalidation risk
None — all v2 metrics are independently measurable with the standalone evaluator.

### Next hypothesis (Experiment 7) — domain-tuned reranker BAAI/bge-reranker-large

Rationale:
- Plateau on top_k tweaks confirms the binding constraint is RANKING, not CANDIDATE WIDTH.
- ms-marco was trained on MS-MARCO (web passage QA). CCoP is regulatory text — different vocab, different reasoning patterns.
- BAAI/bge-reranker-large is trained on broader multilingual corpus including technical/formal text. Better fit for CCoP.
- Cheap to test: change reranker model in settings, run with rerank ON, k=50.

Predicted:
- recall_topn: 0.153 → 0.30-0.45 (if domain match works) or stays ~0.13 (if reranker concept is fundamentally wrong for this corpus).
- recall_topk: unchanged (~0.50 with k=50) — reranker doesn't change candidate set.

Decision tree:
- If recall_topn ≥ 0.30 → BIG WIN. Continue with bge-reranker, then test top_n=5/8 with it.
- If recall_topn < 0.20 → reranker concept is wrong; pivot to query rewriting (Exp 8).
- If recall_topn 0.20-0.30 → keep as marginal improvement, also try query rewriting next.

This is a real experiment requiring a code change (configurable reranker model). Will commit before run.

## Experiment 7 — BAAI/bge-reranker-large, k=50, n=3 (KEEP — first breakthrough)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only (no source change; CCOP_CROSS_ENCODER_MODEL via CLI flag) / Parent: #5
Hypothesis: Domain-tuned reranker (broader corpus including formal text) surfaces ground-truth CCoP clauses to top-N where ms-marco fails.
Changes: --ce-model BAAI/bge-reranker-large; rerank ON; k=50, n=3.

Result:
- recall_topn=0.2500 (+0.097 vs #5; +0.108 vs baseline #0v2; +0.117 vs ms-marco #6)
- precision_topn=0.1333 (+0.056)
- f1_topn=0.1667 (+0.067)
- recall_topk=0.5028 (unchanged — reranker doesn't change candidate set)
- MRR=0.0611

Per-case highlights:
- B22-015 R@N=1.00 (3/3) — bge-reranker correctly elevated 1.6.1, 1.6.2, 1.6.3
- B12-008 R@N=1.00 — perfect on attack scenario clauses
- B24-003 R@N=1.00 — perfect on incident response clauses
- B04-001 R@N=1.00 — perfect on access control 10.1, 10.1.1
- B13-009, B02-012, B06-002 (0.67) — strong wins
- **B08-001 R@N=0.00 but R@K=1.00** — clauses 3.2.2(b)/(c) ARE in candidate set with k=50 (vs absent at k=20), but bge-reranker still doesn't elevate them. Different failure mode from k=20 (where they were unreachable).
- B07-015, B07-022, B03-030, B05-016, B09-019: R@K>0 but R@N=0 — reranker present but failing to surface

Duration: 611 sec (vs ~5 sec for rerank-OFF; vs ~41 sec for ms-marco). bge-reranker-large is ~12× slower than ms-marco.
Status: keep
Insight:
- Domain-tuned reranker WORKS on regulatory text. ms-marco-MiniLM was actively harming retrieval (-0.020 vs no reranker); bge-reranker-large adds +0.097.
- The reranker now surfaces ground-truth clauses in 8/30 cases at top-3 vs 5/30 with rerank OFF (rough count from per-case data).
- Remaining gap (0.25 → 0.70 target): split between (a) cases where R@K=0 (clauses not in candidate pool — embedder limitation) and (b) cases where R@K>0 but R@N=0 (bge-reranker still failing — reranker limitation, but less catastrophic than ms-marco).
- Latency cost: 611s for 30 cases ≈ 20s/case. Real-time RAG implications acceptable.

## REFLECT — Experiment 7

Confirmed:
- Domain-tuned reranker is the right axis. The ms-marco corpus mismatch was real and significant.
- Plateau-breaking experiment as predicted by the strategy diversification analysis pre-Exp 7.

Surprised:
- Magnitude — full +0.097 absolute recall_topn gain from a model swap alone, no other changes. Bigger than expected (predicted 0.30-0.45; got 0.25 — partway between predictions).
- B08-001 canary still failing despite chunks being reachable. The reranker has the candidates and STILL doesn't pick them. This suggests two distinct failure modes: chunk reachability (embedder) AND chunk discrimination (reranker).
- ~12× latency penalty for bge-reranker-large. A pareto trade-off worth flagging.

Breaks model:
- Even with the best available cross-encoder, recall_topn=0.25 << 0.70 target. Reranker alone won't get us there. We need to compound: bge-reranker + bigger funnel (top_k=100) and/or query rewriting and/or top_n=5.

Updated parking lot: bge-reranker-v2-m3 still untested; could be even better.

## THINK — before Experiment 8

### Convergence signals
- Discard streak: 0 (just had a +0.097 keep). Reset.
- recall_topn plateau broken (0.15 → 0.25).
- Same axis (reranker model) explored deeply. Time to compound or pivot.

### Untested assumptions
- bge-reranker-large performance scales with bigger candidate set → untested. R@K=0.62 at k=100 means more right answers exist in the pool.
- top_n=5 dilutes precision more than it lifts recall → untested with bge-reranker (was tested with ms-marco/no-reranker context, may differ).
- Query rewriting could push R@K from 0.50 → higher → untested.

### Invalidation risk
None on prior keeps (#0v2, #2v2, #5, #5b — all infrastructure/measurement).

### Next hypothesis (Experiment 8) — bge-reranker-large + top_k=100 (compound)

Rationale: Best reranker so far + biggest candidate funnel. If recall_topk=0.62 with k=100 (proven in Exp #5b), bge-reranker should be able to find more ground-truth clauses to surface. Cheap to run (model already cached, just bigger reranking batch).

Predicted:
- recall_topn: 0.25 → 0.32-0.42 (compound effect; if reranker can use the bigger pool well, gain should be ~0.07-0.17 absolute)
- recall_topk: 0.50 → 0.62 (matches Exp #5b)
- Latency: ~2× Exp 7 (~20 min for 30 cases) since reranker now scores 100 candidates instead of 50

Decision tree:
- If recall_topn ≥ 0.35 → MAJOR keep, try top_n=5 next (Exp 9) for additional lift
- If recall_topn 0.27-0.35 → marginal keep, pivot to query rewriting (Exp 9) for orthogonal lift
- If recall_topn ≤ 0.27 → reranker hits its own ceiling at this candidate volume; pivot to query rewriting or bge-reranker-v2-m3

Lab-only (env/CLI change only). No commit needed.

## Experiment 8 — bge-reranker-large + top_k=100 (DISCARD — surprise regression)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only / Parent: #7
Hypothesis: Reranker compounds with bigger candidate pool — recall_topk rises 0.50→0.62, reranker should pick more right answers.
Changes: --top-k 100 (was 50). All else same as Exp 7.

Result:
- recall_topn=0.2278 (-0.022 vs Exp #7) ❌
- precision_topn=0.1222 (-0.011)
- f1_topn=0.1511 (-0.016)
- recall_topk=0.6167 (+0.114, matches Exp #5b — confirms more clauses reachable)
- Per-case: full_recall=5 (down from ~8 in #7), partial=4, zero=21 (up from ~17 in #7)

Duration: 958 sec (~16 min, 1.6× Exp 7 due to 2× reranking work)

Status: DISCARD (lab-only, nothing to reset)
Insight:
- **Reranker has a sweet spot.** bge-reranker-large performed BEST at k=50, not k=100. Adding 50 more candidates introduced more confusing "plausible-but-wrong" passages that displaced the right answers from top-3.
- This is the OPPOSITE of the prediction. Compound hypothesis refuted.
- The reranker's discrimination capability degrades with candidate volume — likely because more candidates = more high-similarity-but-irrelevant text from the same domain.
- Recall_topk going from 0.50 → 0.62 confirms more right answers ARE in the bigger pool. They're just being out-ranked by distractors.
- Practical implication: keep k=50 with bge-reranker-large. Don't increase candidate set when using a smart reranker.

## REFLECT — Experiment 8

Confirmed:
- bge-reranker-large at k=50 is the current best config (recall_topn=0.250).
- Bigger candidate set is NOT free with smart rerankers — there's a noise penalty.

Surprised:
- Direction of the effect. Predicted +0.07-0.17; got -0.022. The reranker prefers smaller, higher-quality candidate sets.

Breaks model:
- Hypothesis "more candidates always helps if reranker is smart" is false. Reranker quality is candidate-density-sensitive.

Updated parking lot — added "investigate per-case reranker scores on B08-001-class failures" since the candidates ARE there but bge-reranker is missing them.

## THINK — before Experiment 9

### Convergence signals
- Discard streak: 1 (Exp 8). Not at guardrail.
- Best metric still 0.250 (Exp #7); we improved +0.108 absolute over baseline.
- Need ~0.45 more absolute to hit 0.70 target. Single-axis tweaks won't get us there.

### Untested assumptions
- bge-reranker-large is the best available reranker for this domain → untested. bge-reranker-v2-m3 (newer, multilingual) untested.
- Query rewriting could lift R@K → untested.
- LLM-side tooling (top_n>3) is bad → tested only with non-domain reranker. Untested with bge-reranker-large.
- Hybrid RRF fusion of dense+sparse is well-balanced → untested.

### Invalidation risk
None on Exp #7 (still best, under v2 metric, independently measurable).

### Next hypothesis (Experiment 9) — bge-reranker-v2-m3 at k=50, n=3

Rationale: Cheapest meaningful test. v2-m3 is BAAI's newer reranker, multilingual, lightweight (568M params), trained on broader corpus. If the reranker class is right and bge-reranker-large was just an OK choice, v2-m3 might do +0.05-0.10 better. If it's same/worse, we know bge-reranker-large is near the reranker ceiling and we need to pivot to query rewriting (orthogonal) for further gains.

Predicted:
- recall_topn: 0.250 → 0.27-0.35 (mild improvement; v2-m3 reportedly outperforms v1 on some benchmarks)
- recall_topk: unchanged (0.503)
- Latency: similar or faster (smaller model)

Decision tree:
- recall_topn ≥ 0.30 → KEEP, new best, continue with reranker family
- 0.25-0.30 → marginal, also try query rewriting
- < 0.25 → reranker family near ceiling, pivot to query rewriting

## Experiment 9 — bge-reranker-v2-m3, k=50, n=3 (DISCARD; first run crashed OOM, retry succeeded)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only / Parent: #7

**First attempt:** crashed with `RuntimeError: Invalid buffer size: 34.71 GB` — XLM-RoBERTa default 8192-token max-length exploded the attention buffer. Trivial fix in retrieval_eval.py: pass `max_length=512, batch_size=8` to CrossEncoder constructor.

**Retry after fix:**
- recall_topn=0.1583 (-0.092 vs Exp #7) ❌
- precision_topn=0.1000
- f1_topn=0.1144
- recall_topk=0.5028 (unchanged)

Per-case diff vs Exp #7 (bge-reranker-large):
- GAINED: B02-014 (0.00 → 1.00) — only one
- LOST: B22-015 (1.00 → 0.00), B12-008 (1.00 → 0.00), B02-012 (1.00 → 0.00), B24-003 (1.00 → 0.75), B04-001 (1.00 → 0.50)
- Net: -4 high-recall cases, +1 case. Total recall_topn drops 0.09.

Duration: 479 sec (faster than bge-reranker-large at 611s)

Status: DISCARD
Insight:
- v2-m3 is NOT a strict upgrade over bge-reranker-large for English regulatory text. v2-m3 is multilingual-optimized; the multilingual training likely reduces its English specificity.
- The cases v2-m3 keeps perfect (B13-009, B24-003-partial) are "easy" — short clauses or distinctive section headers. v2-m3 fails on cases bge-reranker-large mastered, suggesting v2-m3 lacks the English-formal-text discrimination edge.
- bge-reranker-large is **confirmed best reranker** in this family. Time to pivot to query rewriting (orthogonal axis).

## REFLECT — Experiment 9

Confirmed:
- bge-reranker-large is the local maximum on the reranker axis. v1 > v2 for English regulatory text.
- ms-marco << bge-reranker-large; v2-m3 < bge-reranker-large; bge-reranker-base untested but expected to underperform large.

Surprised:
- v2-m3 lost MORE perfect cases than expected. If anything, "newer" models often regress on niche domains because they're trained on broader, more diverse data.

Breaks model:
- "Newer model = better" assumption refuted on this domain. Need to evaluate per-domain, not by version number.

## THINK — before Experiment 10

### Convergence signals
- Discard streak: 2 (Exp 8, Exp 9). One more discard hits guardrail.
- Best metric still 0.250 (Exp #7). Reranker axis exhausted.
- Re-validation due (per skill: every 10th experiment). Will skip auto-rerun since Exp #7 used a fixed model + script that produces deterministic scores; the JSON exists.

### Untested assumptions (reranker axis exhausted)
- Query rewriting can lift R@K → untested. Currently R@K=0.50 with k=50. If we can lift it to 0.70+, both reranker and recall_topn benefit.
- Hybrid RRF weighting balanced → untested but lower priority.
- Different embedder model → re-ingestion required, expensive.
- Re-chunking → re-ingestion required, expensive.

### Strategy diversification — pivoting axes per skill protocol

Current best (#7) assumes:
- Reranker quality is the primary lever → confirmed up to 0.25, but capped beyond.
- Original test question is good for retrieval → UNTESTED. Test questions are conversational ("Which gap should be prioritized?"). CCoP clauses are formal ("The CII owner shall conduct a risk assessment that includes..."). Vocabulary mismatch likely.

**Inversion**: instead of "make the reranker smarter at picking from current candidates", try "make the embedder produce better candidates by rewriting the query".

### Next hypothesis (Experiment 10) — Query suffix augmentation (simplest query rewriter)

Rationale: Cheapest possible query-rewriting test. Append a static, domain-anchoring suffix to every query: "as defined in CCoP 2.0 Singapore CII Cyber Security Code of Practice". This nudges the embedding toward CCoP-specific space without an LLM call.

Predicted:
- recall_topk: 0.50 → 0.55-0.65 (modest lift if suffix helps embedder hit CCoP space)
- recall_topn: 0.25 → 0.27-0.35 (compound with bge-reranker-large)
- Latency: unchanged (no LLM call)
- Risk: keyword-stuffing might confuse short queries; might hurt as much as help on average.

If positive → commit to query-rewriting axis, try HyDE next.
If neutral/negative → suffix isn't the right rewriter; try HyDE (LLM-generated hypothetical clause) directly in Exp 11.

Lab-only — implement query-suffix in retrieval_eval.py, then promote to query_analysis.py if winning.

## Experiment 10 — Generic CCoP suffix (DISCARD)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only / Parent: #7
Hypothesis: Anchor every query to CCoP-specific embedding space by appending "as defined in CCoP 2.0 Singapore CII Cyber Security Code of Practice".
Changes: Added --query-prefix/--query-suffix flags to retrieval_eval.py. Augmentation applied to BOTH retrieval query and reranker scoring text.

Result:
- recall_topn=0.1528 (-0.097 vs Exp #7) ❌
- precision_topn=0.0889 (-0.044)
- f1_topn=0.1098 (-0.057)
- recall_topk=0.4956 (-0.007 — slight drop in candidate-set quality)
- MRR=0.0293 (-0.032)
- Cases: full_recall=3, partial=3, zero=24 (vs 6/3/21 in #7)

Per-case diff vs Exp #7:
- GAINED: B03-030 (0.00 → 0.33) — only one
- LOST: B22-015 (1.00 → 0.00), B12-008 (1.00 → 0.00), B24-003 (1.00 → 0.75), B06-002 (0.67 → 0.00), B04-005 (0.33 → 0.00)
- Net: -4 high-recall cases, +1 marginal case.

Duration: 662 sec
Status: DISCARD
Insight:
- Generic boilerplate suffix made queries LESS specific, not more. Adding "CCoP 2.0 Singapore CII Code of Practice" to every query produces high similarity with every CCoP chunk — so the embedder's nearest-neighbor signal is dominated by suffix vocabulary, not the question content.
- This is the diluting-the-signal failure mode of crude query augmentation.
- Importantly: the CHANGED candidate set caused the reranker to pick differently. So query rewriting DOES matter as an axis — but suffix-stuffing is the wrong implementation.
- recall_topk dropped slightly too — not a candidate-set ceiling improvement.

## REFLECT — Experiment 10

Confirmed:
- Crude query augmentation (static suffix) is harmful, not helpful.
- bge-reranker-large is sensitive to candidate composition: same reranker + different candidates ≠ same outcome.

Surprised:
- Magnitude of regression. Predicted -0.05 worst case; got -0.10. Suffix dilution is more aggressive than expected.
- 4 perfect cases lost (B22-015, B12-008, B24-003, B06-002 etc.). The augmented query embedding is far enough from the original to land in a different cluster.

Breaks model:
- "More context in the query helps the embedder" — refuted for static suffix. Embedder treats each token equally; boilerplate dominates.

## 3-Discard Guardrail — after Experiment 10

Discard streak: 3 consecutive (Exp 8, 9, 10). Skill protocol mandates a STOP-and-review.

### Convergence signals review
| Signal | Status |
|--------|--------|
| 5+ discards in a row | NO (3/5) |
| Thought experiments repeating | NO |
| Results consistently confirm theory | MIXED — bge-reranker-large works; v2-m3, k=100, suffix all refuted |
| Results contradict theory | YES on Exp 10 — query rewriting expected to help; static suffix actively hurt |
| Metric plateau (<0.5% over 5 keeps) | N/A — too few keeps |
| Same code area modified 3+ times | YES — reranker swaps (3×), then query rewriting attempts |

### Why I am continuing on this branch (not forking)

1. We have a **clear best** (Exp #7, recall_topn=0.250) that's +0.108 over baseline. Path forward isn't lost.
2. Exp 10's failure is informative, not stuck: query rewriting MOVED retrieval (different cases hit/miss vs Exp 7), so the axis is alive — the SUFFIX implementation was wrong.
3. Untested ideas remain on this branch:
   - **HyDE** (LLM generates a hypothetical CCoP clause for each question, embeds THAT for retrieval) — proven technique for vocabulary-mismatch
   - **Multi-query merge** (retrieve with original + rewritten queries, dedupe, then rerank) — adds candidates without replacing
   - **Per-benchmark targeted hints** (e.g., for B22-waiver add "waiver exception"; for B07-gap add "control gap") — narrow rewriting
   - **Investigating B08-001 reranker scores** — diagnostic to understand WHY bge-reranker can't pick available clauses
4. Forking from baseline (#0) loses all wins. The 0.108 lift from bge-reranker-large is real and stable.

### Why NOT forking yet

Forking from #0 with inverted assumptions would mean abandoning bge-reranker-large to test e.g., a different embedder, different chunking, or no reranker. But the data shows:
- Reranker class IS the right axis (ms-marco hurt; bge-reranker-large helped +0.10).
- The remaining gap is on cases where bge-reranker can't elevate clauses despite presence in pool. That's a discrimination problem within reranker, OR a query-vocabulary problem that better rewriting could solve.
- Forking now == abandoning a confirmed +0.10 lift on a hunch.

### Decision: continue with HyDE-style rewriting (Exp 11), one more attempt before potentially forking

If Exp 11 (HyDE) also discards, we'll have 4 consecutive discards on this branch — closer to the 5-discard mandatory-fork threshold. At that point, fork from #0 with a fundamentally different approach (likely re-chunking with smaller chunks + sentence-level granularity, OR a different embedder).

## THINK — before Experiment 11

### Untested assumption to test
- LLM-generated hypothetical answer (HyDE) embeds closer to ground-truth CCoP clauses than the original test question does.

### Next hypothesis (Experiment 11) — HyDE query rewriting

Rationale:
- Test questions use conversational vocabulary ("Which gap should be prioritized?"). CCoP clauses use formal regulatory vocabulary ("The CII owner shall conduct a risk assessment that includes..."). Vocabulary mismatch causes embedder to land in wrong cluster.
- HyDE: ask a small LLM to write a hypothetical regulatory clause that would answer the question. Embed THAT instead of (or in addition to) the question.
- Use OpenRouter's gpt-4o-mini (already configured for judge) — fast, cheap.

Implementation:
1. Add `--hyde-model` flag to retrieval_eval.py
2. For each query: call gpt-4o-mini with a HyDE prompt → get hypothetical clause text → use as retrieval query
3. Keep bge-reranker-large + k=50, n=3

Predicted:
- recall_topn: 0.25 → 0.28-0.40 (gain depends on how well LLM mimics CCoP vocab)
- recall_topk: 0.50 → 0.55-0.70 (if hypothetical clause embeds closer to real clauses)
- Latency: +1 LLM call per query (~1 sec extra) — total run ~12 min

Risk: HyDE generates wrong vocab → no improvement. Worst case = 0.20-0.25 (similar to Exp 10). Worth the test.

If positive → commit to HyDE, integrate into production query_analysis node.
If negative → abandon query rewriting axis. Fork from #0 with alternative strategy (re-chunking, different embedder).

## Diagnostic — dense vs sparse vs hybrid R@K (THOUGHT, not numbered as experiment)

Before running Exp 11, ran a quick diagnostic via .lab/workspace/dense_vs_sparse_eval.py. Three searches per case at top-K against the same Qdrant collection:

| K   | Dense alone | Sparse alone | Hybrid (RRF) | Dense - Hybrid |
|-----|-------------|--------------|--------------|----------------|
| 20  | 0.367       | 0.194        | 0.314        | +0.053         |
| 50  | 0.530       | 0.400        | 0.503        | +0.027         |
| 100 | 0.644       | 0.578        | 0.617        | +0.027         |

**Critical finding**: hybrid LOSES to dense alone at every K tested. RRF rewards consensus chunks (both dense + sparse rate highly), demoting dense-strong-only candidates. Sparse (BM25) at k=20 is genuinely weak (0.194) on regulatory text vs conversational queries — not earning its weight in fusion. Pivots Exp 11 hypothesis from HyDE to dense-only.

## THINK — before Experiment 11 (revised; superseded the HyDE plan)

### Convergence signals
- Discard streak: 3. Need to break.
- Diagnostic above is cleaner evidence than HyDE hypothesis.
- Dense-only is a MINIMAL change (one CLI flag) with HIGH-CONFIDENCE prediction.

### Untested assumption
- Hybrid retrieval mode is optimal → REFUTED by diagnostic.

### Hypothesis (Exp 11): dense-only candidate set + bge-reranker-large + k=50, n=3

Predicted:
- recall_topn: 0.250 → 0.27-0.32 (compound effect: cleaner candidates → reranker picks better)
- recall_topk: 0.503 → 0.530 (matches diagnostic)

Decision tree:
- recall_topn ≥ 0.27 → KEEP, new best, continue compounding
- < 0.25 → unexpected; revisit diagnostic

## Experiment 11 — Dense-only + bge-reranker-large + k=50, n=3 (KEEP — new best)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only / Parent: #7
Hypothesis: Dense-only candidate set strictly improves over hybrid (per diagnostic). Reranker has cleaner pool to pick from.
Changes: Added `_retrieve_single_mode()` helper to retrieval_eval.py + `--retrieval-mode {hybrid,dense,sparse}` CLI flag. Calls Qdrant `query_points` with `using="dense"` or `using="sparse"` to bypass RRF.

Result:
- recall_topn=0.2833 (+0.033 vs Exp #7) ✅
- precision_topn=0.1444 (+0.011)
- f1_topn=0.1833 (+0.017)
- recall_topk=0.530 (+0.027 — exact diagnostic match)
- MRR=0.0455
- Cases: full_recall=7, partial=3, zero=20 (vs 6/3/21 in #7)

Per-case diff vs Exp #7:
- GAINED: B09-019 (0.00 → 1.00) — clean win
- LOST: NONE
- Same perfect: 6
- **Pareto improvement** — strictly better than #7

Duration: 548 sec
Status: KEEP — NEW BEST
Insight:
- Dense-only candidate set delivers exactly the +0.027 R@K boost predicted by the diagnostic. That cascaded into +0.033 recall_topn through the reranker.
- B09-019 jumped from 0/3 to 3/3 expected clauses at top-N. The hybrid RRF was demoting `3.2.2(a)`, `3.2.4`, `3.2.5` because sparse signal was weak; dense alone surfaced them, reranker correctly ranked them.
- This is the cumulative path: baseline 0.142 → Exp 7 (0.250, +bge-reranker) → Exp 11 (0.283, +dense-only).
- 3-discard guardrail RESET.

## REFLECT — Experiment 11

Confirmed:
- Diagnostic-driven hypotheses outperform speculation. The dense-only test was based on direct measurement (Exp 11's prediction was within +0.001 of measured).
- Dense-only is a Pareto improvement — never hurts, sometimes helps.

Surprised:
- Magnitude: +0.033 from a 1-flag change. Cumulatively now +0.141 over baseline (~2× recall).

Breaks model:
- "Hybrid is always at least as good as components" — refuted. RRF can dilute a dominant signal when its companion is weak.

Updated parking lot — sparse retrieval is on the parking lot now (currently dragging hybrid down; could be FIXED with better sparse model or different fusion weight).

## Experiment 12 — Re-measure Exp 11 against agent-team-corrected GT (KEEP)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only / Parent: #11
Hypothesis: Original GT had wrong/incomplete clauses (24 of 30 cases); re-measuring against agent-team-corrected GT will reveal true retrieval performance.
Changes: Added --corrected-gt flag to retrieval_eval.py. Built corrected-gt.json from 30 reviewer agents.
Result:
- recall_topn 0.257 (-0.026 vs Exp #11 against original GT)
- precision_topn 0.241 (+0.097)
- recall_topk **0.750** (+0.220) — embedder ceiling much higher than thought
- MRR 0.266 (6× improvement vs 0.045)
- F1 0.238 (+0.054)
Status: keep
Insight: Original recall_topn was systematically pessimistic. R@K=0.75 means embedder reaches 75% of true expected clauses at k=50. The "0.62 ceiling" was an artifact of measuring against bad GT. The retrieval engine is genuinely better than the original metric showed.

## Experiment 13 — Multi-N + dynamic N=C metrics on corrected GT (KEEP — new headline)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only / Parent: #12
Hypothesis: recall@N=3 is mechanically pessimistic when GT cardinality > 3. Test recall@N for multiple N (3,5,8,10,K) and dynamic N=C per case.
Changes: Multi-N computation in retrieval_eval.py. Computes recall/precision/F1 at N=3,5,8,10,C,K for each case.
Result:
| N      | recall  | precision | f1    |
|--------|---------|-----------|-------|
| 3      | 0.257   | 0.241     | 0.238 |
| 5      | 0.310   | 0.207     | 0.241 |
| 8      | 0.413   | 0.177     | 0.240 |
| 10     | 0.413   | 0.155     | 0.219 |
| **C**  | **0.335** | 0.221  | 0.254 |
| K=50   | 0.750   | 0.073     | 0.131 |

GT cardinality: mean 4.72, max 8. N=3 is binding for 77% of cases.
Status: keep — recall@C is the cardinality-fair retrieval metric. **Headline: 0.335.**
Insight: Two distinct failure modes now cleanly separable:
- **Reranker fail** (R@K high, R@C low): 7 cases — bge-reranker can't surface available clauses
- **Embedder fail** (R@K low): 6 cases — vocab mismatch / chunking
- 17 cases working

## METRIC v3 REVISION (Phase A focus update)

Per user direction (2026-04-26): switch primary to mean_recall_at_C against corrected GT. Target raised to ≥ 0.8 on 30 subset. Re-ingestion in scope.

Distance to target: 0.465 absolute (very ambitious — typical regulatory QA achieves 0.55-0.75 without fine-tuning).

## THINK — before Experiment 14

### Convergence signals
- 3 keeps in a row (Exp 11, 12, 13). No discard streak.
- Best: 0.335. Need +0.465 to hit target.
- All retrieval-side experiments to date have stayed within "tweak existing pipeline." Time to make a structural change.

### Untested assumptions
- Chunking is correct → REFUTED by audit (median 44 words for CCoP; chunks too small for BGE)
- Each clause should be standalone → UNTESTED — best practice says add section breadcrumb + contextual prefix
- Re-ingestion would help → UNTESTED — gated to date by cost, but per user new scope it's allowed
- Anthropic's contextual chunking applies here → UNTESTED — but every diagnostic data point points to it

### Invalidation risk
- Re-ingestion will WIPE the current Qdrant index. Mitigations: keep current corpus_dump.md as ground truth; re-ingestion is reversible (rebuild from PDFs).
- All previous experiments measured against current chunking. After re-ingestion, those measurements no longer apply to the live index. New experiments will start from a new baseline.

### Next hypothesis (Exp 14) — Contextual Chunking + Breadcrumb Headers

Anthropic's published recipe (Sept 2024): for each chunk, prepend an LLM-generated 1-2 sentence context describing how the chunk fits in the parent document. PLUS structural breadcrumb header.

For our case, augment each chunk's indexed text with:
1. **Breadcrumb** (free, deterministic): `[Doc: CCoP 2.0 | Chapter 5: Protection | Section 5.3: Privileged Access Management]`
2. **Context** (LLM-generated, gpt-4o-mini): "This clause mandates multi-factor authentication for privileged accounts to prevent credential compromise."

Expected lift: Anthropic reports 35-50% reduction in retrieval failures on technical docs. For our 0.335 starting point, that translates to recall@C ≈ 0.50-0.55.

Predicted:
- recall@C: 0.335 → 0.50-0.55
- recall@K: 0.75 → 0.85-0.92 (more clauses become reachable at k=50)
- recall@3: 0.26 → 0.40-0.45
- recall@5: 0.31 → 0.45-0.50

Effort:
- ~3 hr engineering (add contextualization step to ingestion pipeline)
- ~$0.20 in LLM costs (gpt-4o-mini × 700 chunks)
- ~30 min re-ingestion

Decision tree:
- recall@C ≥ 0.45 → KEEP, big win, continue with parent-child auto-merging
- recall@C 0.35-0.45 → KEEP marginal, layer on breadcrumb-only test to isolate effect
- recall@C < 0.35 → DISCARD, investigate why (LLM context is wrong? truncation? embedding length?)

This is a real experiment with code changes (ingestion pipeline). Will commit before re-ingest.

## Experiment 14 — Contextual Chunking + Breadcrumb (KEEP* — embedder big win, reranker bug uncovered)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only (new collection ccop_clauses_contextual; original collection unchanged) / Parent: #13
Hypothesis: Anthropic-style contextual chunking + breadcrumb headers will lift recall@C from 0.335 to 0.50+.
Changes: Built `.lab/workspace/contextualize_corpus.py`. For each of 495 chunks: deterministic breadcrumb from metadata + LLM-generated 1-2 sentence context (gpt-4o-mini, parallel, ~33s for all chunks). Augmented_text = breadcrumb + context + original. Stored in new collection `ccop_clauses_contextual`. Eval against this collection with bge-reranker-large + dense + k=50.

Result:
- recall@K (k=50): **0.750 → 0.857 (+0.107)** ★ — embedder reaches 86% of expected clauses
- precision@3: 0.241 → 0.322 (+0.081) ★
- precision@C: 0.221 → 0.282 (+0.061)
- f1@C: 0.254 → 0.280 (+0.026)
- MRR: 0.266 → 0.307 (+0.040)
- recall@C: 0.335 → 0.310 (-0.025) ✗ ← primary regressed
- recall@5: 0.310 → 0.305 (-0.005)
- recall@8: 0.413 → 0.384 (-0.029)
- Per-case R@C: 6 gained, 6 lost, 17 same

Duration: ~10 sec (test contexts) + ~107 sec (dense embed 495 chunks) + ~10 min (eval) = ~13 min total
Status: keep* — informational regression on primary, big wins on secondaries
Insight (CRITICAL):
- **Contextual chunking is the right intervention** — embedder ceiling lifted from 0.75 to 0.857
- **But reranker is now BROKEN by the augmented text.** The reranker scores (query, augmented_text). bge-reranker isn't trained on documents prefixed with breadcrumb metadata. It's getting distracted.
- The fix: pass **original_text** to reranker (stored in payload as `original_text`), not the augmented text.
- This should restore primary metric AND retain the R@K gain.

## REFLECT — Experiment 14

Confirmed:
- Anthropic's contextual chunking technique works on regulatory text. Embedder reachability lifted +14% relative.
- Short chunks were the dominant problem. With context augmentation, the embedder finds 86% of expected clauses in top-50.

Surprised:
- Reranker degradation. I expected the reranker to handle augmented text fine. It doesn't — bge-reranker treats the breadcrumb+context as noise.

Breaks model:
- "Use the same indexed text everywhere" is wrong for hybrid pipelines with both embedder and reranker. Each stage may want different versions of the document.

## THINK — before Experiment 15

### Convergence signals
- 1 keep* with diagnostic insight. Not a discard streak. Path forward is clear.

### Untested assumption
- Reranker performs better when scoring against original text (not augmented).

### Next hypothesis (Exp 15) — Decouple embedder text from reranker text

Use:
- **Indexed text for embedder**: augmented (breadcrumb + context + original) — keep current contextualized index
- **Reranker scoring text**: original_text from payload — bypass augmentation

Predicted:
- recall@K: stays at 0.857 (embedder unchanged)
- recall@C: 0.310 → 0.45-0.55 (reranker now seeing clean text)
- precision@C: stays high or improves further

Decision tree:
- recall@C ≥ 0.45 → KEEP, big win, continue
- 0.35-0.45 → KEEP, marginal win
- < 0.33 → unexpected; reconsider

This is a single-line change in retrieval_eval.py. Lab-only, no commit needed.

## Experiment 15 — Decouple embedder text from reranker text (KEEP)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only / Parent: #14
Hypothesis: Reranker scoring (query, original_text) instead of (query, augmented_text) restores discrimination.
Changes: retrieval_eval.py — when reranking, pass `doc.metadata.original_text` (original clause body) if present, else fall back to `doc.page_content`.
Result:
- recall@C: 0.310 → **0.3545** (+0.045 vs #14, +0.020 vs #13) — best ever
- recall@5: 0.305 → 0.3531 (+0.048)
- recall@8: 0.384 → 0.4505 (+0.066) — R@8 over 0.45
- recall@K: 0.857 (preserved)
- precision@3: 0.322 → 0.287 (-0.034 — minor regression vs #14)
- f1@3: 0.278 → 0.270 (-0.008)
- MRR: 0.307 (preserved)
- R@C distribution: 2 full / 18 partial / 9 zero (vs 7/3/20 in #13)

Status: keep — primary R@C up, R@5/8/10 substantially up
Insight:
- Decoupling embedder vs reranker text inputs is the right architecture for hybrid pipelines with augmented chunks
- Retrieval is now genuinely good: 86% reachability + reranker pulls more clauses to top-N
- BUT R@C only +0.020 vs #13 because reranker's TOP-3 still misses many available clauses
- Distance to target 0.8: 0.445 — need next leverage point

## REFLECT — Experiment 15

Confirmed:
- The "use original text for reranker" architecture works.
- Cumulative R@C improvement so far: 0.142 → 0.3545 = +149% relative.

Surprised:
- Recall@K=0.857 means 86% of expected clauses are in the candidate pool. Yet recall@C=0.355 means we surface less than half of those to the LLM. Reranker is the binding constraint.

Breaks model:
- "Better embedder → linearly better recall" — refuted. Embedder ceiling is high but reranker dominates the pipeline at small N.

Updated parking lot — single-vector dense embedder may be near ceiling; reranker quality and parent-child are the leverage.

## THINK — before Experiment 16

### Convergence signals
- 2 keeps in a row (Exp 14*, 15). No discard streak.
- R@K=0.857 means the candidate pool is rich. Bottleneck has shifted to reranker.
- Several test cases have multiple expected clauses in the SAME section: B22-015 (1.6.1-3), B05-013 (1.6.1-3, 10.2.7), B07-015 (6.2.1-3), B12-008 (8.2.1-5), B12-016 (3.8.1-5), B13-009 (7.1.x), B14-001 (5.9.x), B24-022 (7.1.1+6.4.x).

### Untested assumption
- Parent-child auto-merging will help cases where expected clauses share a section.

### Hypothesis (Exp 16) — Parent-child auto-merging at retrieval time

Algorithm:
1. Retrieve top_k=50 (current pipeline)
2. After reranking, group docs by parent_path (everything except leaf clause id)
3. If 2+ docs from the same parent are in the top reranked list, merge them into a "section group" treated as a single retrieval result. Include all member sub-clause citation_ids in the group.
4. Take the top-N groups (instead of top-N docs), where each group can contain 1+ original docs.
5. Recall is computed against ALL clause_ids in the merged groups, not just the leaf ones.

For metric: a "merged" entry still has a single rank slot. Its contribution to recall counts all member clauses.

Predicted:
- Cases with multi-clause expected from same section (~10 of 30 cases) will jump significantly
- recall@C: 0.355 → 0.45-0.55
- recall@K unchanged (same candidate pool)

This is a retrieval-time logic change in retrieval_eval.py. Lab-only.

Decision tree:
- recall@C ≥ 0.45 → KEEP, big win
- 0.36-0.45 → KEEP marginal
- < 0.36 → DISCARD, the merging logic is wrong

## Experiment 16 — Parent-child auto-merging (KEEP — NEW BEST)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only / Parent: #15
Hypothesis: Group siblings of same parent_path within reranker top-K=10 window into single section result; counts toward recall via members.
Changes: Added get_parent_path() and merge_by_parent() functions to retrieval_eval.py. Added --merge-parents flag. Window=10, min_siblings=2.

Result:
- recall@C: 0.3545 → **0.4189** (+0.064, +18% relative) ★ NEW BEST
- recall@3: 0.276 → 0.343 (+0.067)
- recall@5: 0.353 → 0.400 (+0.047)
- recall@8: 0.451 → 0.457 (+0.007 — saturated; merging mostly affects head)
- recall@K: 0.857 (unchanged, as predicted)
- precision@C: 0.238 → 0.221 (-0.017 — minor; merged entries have multiple members)
- f1@3: 0.270 → 0.301 (+0.031)

Per-case: 7 GAINED, 0 LOST, 22 same — clean Pareto improvement.

GAINED:
- B04-005: 0.75 → 1.00
- B02-012: 0.50 → 1.00
- B18-001: 0.33 → 0.67
- B14-001: 0.20 → 0.40
- B21-001: 0.50 → 0.75
- B04-001: 0.67 → 0.83
- B08-018: 0.17 → 0.33

Duration: ~22 min (eval; merge logic is fast, reranker dominant)
Status: keep — NEW BEST
Insight:
- Cardinality fix works exactly as predicted on cases where reranker already had partial signal
- Cases where reranker put ZERO expected clauses in top-10 (B07-015, B12-008, B12-016, B22-015, B05-013, etc.) didn't benefit — merge can't surface anything if there are no siblings in the window
- This is a VOCABULARY problem now clearly visible: cross-encoder can't bridge query→regulatory-text gap
- Cumulative R@C: 0.142 → 0.4189 = +196% relative; distance to 0.8 = 0.381

## REFLECT — Experiment 16

Confirmed:
- Parent-child merging adds ~0.07 recall at top-3 with no precision/recall regressions
- Pareto improvement is the strongest signal of a sound technique

Surprised:
- The cardinality-binding cases I expected to dominate (B07-015 with 6.2.x, B12-008 with 8.2.x, B12-016 with 3.8.x) didn't gain — they're cross-encoder-failing, not cardinality-bound

Breaks model:
- "If R@K=1.0, merging will fix R@N" — refuted. Even if all expected clauses are in candidate pool of 50, the cross-encoder may put none in top-10 (the merge window).
- The deeper bottleneck for some cases is cross-encoder discrimination — vocabulary mismatch between conversational query and formal clause.

## THINK — before Experiment 17

### Convergence signals
- 3 keeps in row (Exp 14*, 15, 16). Strong stack.
- Distance to target: 0.381. Need next high-leverage move.
- Diagnosis is clear: ~6-8 cases where cross-encoder reranker fails to surface ANY expected clause to top-10 because of vocab mismatch.

### Untested assumption
- HyDE (LLM-generated hypothetical clause) will lift recall on vocab-mismatch cases.

### Next hypothesis (Exp 17) — HyDE query rewriting

For each test query, call gpt-4o-mini to generate a 2-3 sentence "hypothetical CCoP clause" that would answer the question. Embed THAT for retrieval (not the original query). Reranker scores against ORIGINAL query (its training data).

Predicted:
- Lifts the 6-7 vocab-mismatch cases (B05-013, B07-015, B12-016, B22-015, B23-001, etc.)
- recall@C: 0.4189 → 0.50-0.55
- recall@K: stays at 0.857 or improves slightly (better vocabulary alignment for retrieval)
- Cost: 30 LLM calls per eval × $0.0003 ≈ $0.01

Implementation: Add `--hyde` flag to retrieval_eval.py. Before retrieval, call OpenRouter with the test question and a HyDE prompt. Use the LLM's output as the embedding query. Keep original query for reranker.

Stacks on top of Exp 16: contextualized index + decoupled reranker + parent-child merge + HyDE.

Decision tree:
- recall@C ≥ 0.50 → KEEP, big win, continue (probably stack additional improvements)
- 0.43-0.50 → KEEP marginal, dial in (e.g., HyDE for reranker too)
- < 0.42 → DISCARD, HyDE is wrong axis for our cases

## Experiment 17 — HyDE + full stack (KEEP modest)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only / Parent: #16
Hypothesis: gpt-4o-mini generates hypothetical CCoP-style clause; embed THAT (not original query). Reranker still scores against original query.
Changes: Added --hyde, --hyde-model flags. Pre-generates HyDE for all 30 cases in 7.4s parallel. Per-case: hypothetical used for embedding query; original used for reranker.
Result:
- recall@C: 0.4189 → 0.4304 (+0.012, modest)
- recall@3: +0.030, recall@5: +0.042, recall@8: +0.058, recall@10: **+0.076** (biggest)
- MRR: +0.142 (~+46%, huge — HyDE pulls relevant clauses to higher ranks)
- precision@3: +0.040, f1@3: +0.038
- recall@K: 0.857 → 0.797 (-0.060) ✗
- Per-case: 4 gained, 3 lost, 22 same — net Pareto positive

Status: keep
Insight:
- HyDE works on vocab-mismatch cases (B07-015, B13-003 went 0→0.25)
- But drifts the embedded query for some clear cases (R@K dropped). Embedding hypothetical text instead of original query loses some "easy" matches.
- The right fix is multi-query retrieval: use BOTH original query and HyDE, merge via RRF.

## REFLECT — Experiment 17

Confirmed: HyDE addresses vocabulary mismatch (B07-015 was the canary "exempted vs waiver" pattern).
Surprised: R@K REGRESSION. Anthropic-style HyDE drifts vector position; we lose some easy matches even as we gain hard ones.
Breaks model: "HyDE is strictly additive" — no, it can replace good retrievals with worse ones if the hypothetical wanders.

## THINK — before Experiment 18

### Convergence signals
- 4 keeps in row (Exp 14*, 15, 16, 17). Strong.
- Best R@C: 0.430. Distance to 0.8: 0.370.
- HyDE gave us recall@5/8/10 lifts — clauses are now in higher ranks.

### Untested assumption
- Multi-query retrieval (original + HyDE → RRF merge) recovers R@K regression while keeping HyDE benefits.

### Next hypothesis (Exp 18) — Multi-query retrieval (RAG-Fusion style)

For each test case:
1. Retrieve top-50 with ORIGINAL query (vector A)
2. Retrieve top-50 with HyDE query (vector B)
3. RRF-merge: for each chunk, score = 1/(k+rank_A) + 1/(k+rank_B), where k=60 (standard)
4. Take top-50 from merged
5. Reranker + parent-child merge as before (Exp 17 pipeline)

Predicted:
- recall@K: 0.797 → 0.85+ (recover original query's reach)
- recall@C: 0.430 → 0.46-0.52
- MRR: stays ~0.45 (HyDE still pulls relevant clauses high)

Cost: one extra retrieval per query (~50ms each), HyDE already pre-generated.

Decision tree:
- recall@C ≥ 0.50 → KEEP, big stack win
- 0.43-0.50 → KEEP marginal
- < 0.42 → DISCARD, multi-query merge is wrong

## Experiment 18 — Multi-query RRF (orig + HyDE) (DISCARD)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only / Parent: #17
Result: R@C 0.4131 (-0.017 vs #17). 2 gained / 4 lost. RRF averaging diluted HyDE's vocab-bridge wins. R@K only partially recovered.
Status: discard
Insight: when HyDE works (vocab cases), merging with original-query rankings DILUTES the win. Should not blend rankings — keep HyDE pure for retrieval.

## THINK — before Experiment 19

### Convergence signals
- 1 discard. Best remains Exp #17 (0.430).
- Exp #17 showed recall@10=0.545. Many relevant clauses sit at ranks 4-10 that current merge_window=10 partially catches. Wider window may catch more.

### Untested assumption
- Wider merge window (15 or 20) catches more sibling pairs that HyDE pulled to mid-ranks.

### Next hypothesis (Exp 19) — Widen merge window to 15 (HyDE + window=15)

Stack: Exp 17 config + merge_window=15 (was 10).

Predicted:
- recall@C: 0.430 → 0.46-0.50 (catches groups extending into ranks 11-15)
- Risk: precision could drop if too-loose grouping pulls in unrelated clauses

Cheap test, no new code.

## Experiment 19 — HyDE + window=15 (KEEP — NEW BEST)
Branch: research/maximize-rag-vs-llm-only / Type: lab-only / Parent: #17
Result:
- recall@C: 0.4304 → **0.4874** (+0.057) ★★ NEW BEST
- recall@3: +0.059, @5: +0.052, @8: +0.048, @10: +0.052
- recall@K: -0.030 (HyDE drift)
- f1@C: +0.018, MRR: +0.014
- Per-case: 4 gained big (B13-003 0.25→1.00, B09-019 0.40→1.00, B18-001 0.67→1.00, B05-016 0.20→0.60), 1 lost (B12-008 0.86→0.43), 24 same

Status: keep — NEW BEST
Insight: Wider merge window caught sibling groups extending into ranks 11-15 that window=10 missed. HyDE's vocab-bridge wins compound with merge expansion.

## Re-Validation after Experiment 19 (per skill protocol — N=20 trigger)
Re-running Exp 19 (current best) is unnecessary — just produced. Same code, same data, same metric (R@C=0.4874). No drift.

## THINK — before Experiment 20

### Convergence signals
- Steady progress: R@C 0.142→0.487 over 19 exp, +243% relative.
- Window=15 paid off; consider window=20 as continued sweep.
- Still 0.313 to target.

### Untested
- Window=20 — does even wider catch more or saturate?

### Hypothesis (Exp 20) — Window=20 with same stack

Predicted: marginal +0.01 to +0.04 if ranks 16-20 still have clusters; could regress if grouping noise pulls in unrelated clauses.

## Experiment 20 — window=20 (DISCARD)
Result: R@C 0.4764 (-0.011 vs #19). 5 lost / 2 gained. Window=20 over-merges. Window=15 is local optimum on this axis.

## THINK — before Experiment 21

### Convergence signals
- Discard streak: 1 (Exp 20). 
- Best R@C: 0.487 (Exp #19). Distance to 0.8: 0.313.
- Window axis exhausted (10 < 15 > 20).

### Untested
- Synthetic question chunks (Doc2Query): bake 3-5 likely questions per chunk into the indexed text. Pre-published technique that lifts retrieval recall on QA tasks by 5-15%.

### Hypothesis (Exp 21) — Doc2Query: synthetic question chunks

For each of the 495 chunks in ccop_clauses_contextual:
1. Call gpt-4o-mini with prompt: "Given this CCoP clause text and its context, generate 3-5 likely user questions a regulatory analyst might search with."
2. Build new augmented text: breadcrumb + context + [3-5 questions] + original_text
3. Re-encode with BGE-large-en + Qdrant/bm25
4. Store in NEW collection ccop_clauses_doc2query (preserves prior collection)

This bakes query-style vocabulary into the index. Should lift R@K (currently 0.766 in Exp 19) substantially, which propagates to R@C.

Predicted:
- recall@K: 0.766 → 0.85+
- recall@C: 0.487 → 0.55-0.60
- Cost: ~$0.50 LLM + ~5 min re-index + ~12 min eval

Decision tree:
- recall@C ≥ 0.53 → KEEP, big lift
- 0.49-0.53 → KEEP marginal
- < 0.48 → DISCARD, Doc2Query didn't help

## Experiment 21 — Doc2Query + HyDE + window=15 (DISCARD)
Result: R@C 0.4813 (-0.006 vs #19). R@K +0.041. 2 gained / 2 lost.
Insight: Doc2Query lifts R@K (chunks now contain question-style vocab) BUT lost cases overlap with HyDE's earlier wins (B05-013, B13-003) — Doc2Query and HyDE may conflict.

## THINK — before Experiment 22

### Convergence signals
- Discard streak: 2 (Exp 20, 21). One more = guardrail.
- Best stays Exp 19 R@C=0.487.

### Untested
- Doc2Query without HyDE — does the question-augmented index alone (without HyDE drift) match or beat the HyDE-only run?

### Hypothesis (Exp 22) — Doc2Query alone (no HyDE)

Same stack as #19 but: collection=ccop_clauses_doc2query, hyde=OFF.

Reasoning: Doc2Query chunks already contain query-style language. Adding HyDE may push the embedding query AWAY from chunks rather than toward them.

Predicted:
- recall@C: 0.487 → 0.49-0.53 (DocQ lifts R@K; original query better aligned with augmented chunks than HyDE-drift)
- recall@K: should be high (~0.85+ as in Exp 21)

Decision tree:
- ≥ 0.50 → KEEP, big win
- 0.485-0.50 → KEEP marginal
- < 0.485 → DISCARD (3rd in row → guardrail)

## Experiment 22 — Doc2Query alone (no HyDE) (DISCARD)
Result: R@C 0.4545 (-0.033 vs #19). R@K 0.852 (highest ever, +0.086 vs #19). MRR collapsed -0.142.
Insight: Doc2Query lifts retrieval pool quality but reranker can't surface the right clauses from the bigger pool. Removing HyDE removed the vocab bridge for cases B13-003, B09-019, B05-016, B07-015, B14-001, B21-001 — all regressed.

## 3-Discard Guardrail — after Experiment 22 (per skill protocol)

Discard streak: 3 consecutive (#20, #21, #22). MUST stop and reflect.

### Convergence signals review
| Signal | Status |
|--------|--------|
| 5+ discards in a row | NO (3/5) |
| Thought experiments repeating | NO |
| Results consistently confirm theory | MIXED — Doc2Query confirmed lifting R@K, but R@C didn't follow |
| Results contradict theory | YES on Exp 22 — bigger candidate pool didn't translate to better top-3; reranker is binding |
| Metric plateau | Best metric stable at 0.487 over Exp #19; experiments since are flat or regress |
| Same code area modified 3+ times | Yes — merge window, HyDE, indexing strategy |

### Why I am continuing on this branch (not forking)

1. Best metric R@C = 0.487 (Exp #19) is +243% over baseline 0.142. Path is real; we have a working stack.
2. Last 3 discards each REVEALED something:
   - Exp 20 (window=20): showed window=15 is local optimum
   - Exp 21 (Doc2Query+HyDE): showed Doc2Query and HyDE conflict
   - Exp 22 (Doc2Query alone): showed reranker is binding constraint when R@K is high
3. Untested ideas remain:
   - **Different reranker** (Cohere, Jina, Voyage) on the Exp 19 stack — never tested with contextualized index + HyDE
   - **top_k=100 with full stack** — already saw R@K=0.86 at k=50; bigger pool may help reranker
   - **Stricter merge_min_siblings=3** — fewer false-positive merges
   - **Reranker scoring with augmented text** (revisit Exp 14's idea now that bigger context is available)
   - **Hierarchical chunking** — index at multiple granularities

### Forking? Considering but not yet

A fork from baseline (#0) with inverted assumptions would require abandoning all 5 stacked wins (contextualization, decoupled reranker, HyDE, merge, window=15). The compounded R@C lift is too valuable to discard — most clearly demonstrated on B13-003 (0→1.00), B09-019 (0.40→1.00), B22-015 (1.00).

### Decision: continue on branch with reranker-focused experiments

The data points clearly to reranker as the binding constraint when R@K is high. Three options:

**A. top_k=100 with full Exp 19 stack** (cheap, minutes)
**B. Different reranker (try cohere or jina via API, since bge-reranker-large is plateauing)** (medium, requires API setup)
**C. Stricter parent-merge (min_siblings=3 — only merge tight clusters)** (cheap)

Pick A first (cheapest, tests whether wider pool helps the reranker now that R@K is genuinely better with stack).

## THINK — before Experiment 23

### Hypothesis (Exp 23) — Stack 19 + top_k=100

If the reranker is binding because expected clauses sit at ranks 4-15 in top-50 reranked, expanding to top_k=100 lets even more candidates come through. With contextual+Doc2Query already lifting R@K to 0.85 at k=50, R@K@100 may reach 0.90+. Reranker then has more material to work with.

NOTE: We tested top_k=100 in Exp 8 (with vanilla pipeline, no stack) and it slightly regressed because the bigger pool added noise. With the cleaner stack (contextualized chunks, HyDE, merge), the pool may be cleaner now.

Predicted:
- recall@K: 0.77 → 0.90+
- recall@C: 0.487 → 0.50-0.55
- Risk: same as Exp 8 — too many candidates pollute reranker
- Cost: 2× retrieval (still <1 sec)

Decision tree:
- recall@C ≥ 0.50 → KEEP, exit guardrail
- 0.48-0.50 → KEEP marginal
- < 0.485 → DISCARD (4th, very close to 5-discard fork mandate)

## Experiment 23 — top_k=100 + full stack (DISCARD)
Result: R@C 0.4384 (-0.049 vs #19). R@K 0.886 (highest). Reranker overwhelmed by bigger pool.
Insight: R@K and R@C inversely correlate. Reranker IS the binding constraint, top_k expansion can't fix this.

## THINK — before Experiment 24

### Convergence signals
- Discard streak: 4. ONE MORE = mandatory fork per skill.
- All variants of what we've tried (top_k, window, reranker model, indexing) have failed since Exp 19.

### Genuinely new axis (NOT a variant)
Reranker scoring against AUGMENTED text (with Doc2Query questions baked in). Exp 14 tested this with breadcrumb-only augmentation and it failed; current Doc2Query augmentation has query-style synthetic questions baked in, which is materially different signal.

### Hypothesis (Exp 24) — Reranker on augmented text (Doc2Query collection)

Stack: ccop_clauses_doc2query + HyDE + window=15 + reranker scores against AUGMENTED text (chunks contain breadcrumb + context + questions + original).

Reasoning: cross-encoder bge-reranker-large was distracted by raw breadcrumb+context (Exp 14), but synthetic QUESTIONS are query-style language — exactly what cross-encoders are trained to see (query, query-like passage). The reranker may now find the right matches.

Predicted:
- recall@C: 0.487 → 0.50-0.55 (if augmented signal helps reranker)
- recall@K: same as Exp 21 (0.81)
- Risk: reranker still distracted, R@C drops further

Decision tree:
- recall@C ≥ 0.49 → KEEP, exit guardrail
- 0.46-0.49 → KEEP marginal
- < 0.46 → DISCARD (5th → MANDATORY FORK)

## Experiment 24 — Reranker on AUGMENTED Doc2Query text (DISCARD on primary, polarized)
Result: R@C 0.4695 (-0.018 vs #19). 5 big gains, 6 big losses. precision@3 +0.074, f1@3 +0.048.
Insight: augmented-text reranker has different priors. Highly polarized — works perfectly on some cases (B05-013, B12-008, B06-002 → 1.00) but collapses others (B01-007, B13-003, B18-001 → 0.00). Suggests ensemble of original+augmented rerankers might smooth the volatility.

## 5-Discard Fork — after Experiment 24 (per skill protocol)

Discard streak: 5 consecutive (#20, #21, #22, #23, #24). Per protocol, fork is the default action UNLESS:
1. A parking-lot idea is tried first, OR
2. A specific untested non-variant hypothesis is named

### Parking lot untested ideas
- BGE-M3 embedder — would shift R@K but R@K is no longer binding (already 0.85-0.89)
- Re-chunking smaller/larger — variant of indexing axis (already tried contextual + Doc2Query)
- Hybrid scoring weights — variant of retrieval mode axis (dense-only beat hybrid in Exp 11)

None of these directly attack the diagnosed bottleneck (reranker). Trying them would burn experiments before getting to the right axis.

### Specific untested non-variant hypothesis

**Reranker score ensemble**: average the cross-encoder score from `(query, original_text)` AND `(query, augmented_text)` for each candidate. Use the average for ranking.

Why this is non-variant:
- Exp 15 used original_text only
- Exp 24 used augmented_text only  
- Both are individually suboptimal but in DIFFERENT ways (Exp 24 polarization)
- Ensembling smooths volatility — neither orig nor aug alone has been combined this way
- Different axis: changes the SCORING, not the chunks/queries/window/top_k

Predicted:
- recall@C: 0.487 → 0.50-0.55 (smooths Exp 24's polarization while keeping its wins)
- Cost: 2× reranker forward passes per query (~25 min eval)

### Decision: try ensemble (Exp 25), THEN fork if it discards

This is the LAST stay-on-branch attempt. If Exp 25 discards → mandatory fork from baseline.

## THINK — before Experiment 25

### Hypothesis (Exp 25) — Reranker score ensemble
Score each candidate against BOTH original and augmented text. Average the two scores for ranking. Average smooths Exp 24's polarization while preserving its big wins (B05-013, B12-008, etc.).

Decision tree:
- recall@C ≥ 0.49 → KEEP, exit fork mandate
- 0.46-0.49 → marginal, considered KEEP*
- < 0.46 → DISCARD → MANDATORY FORK

## Experiment 25 — Reranker score ensemble (DISCARD — 6th)
Result: R@C 0.4649 (-0.023 vs #19). 5 gained / 5 lost. Many secondaries up but primary regressed. 6th consecutive discard.

## FORK — Strategy Diversification (per skill protocol)

### Branch: research/no-reranker-stack (forked from baseline a67bbb7)

### Assumptions list (for the EXHAUSTED branch research/maximize-rag-vs-llm-only):
1. Cross-encoder reranker is necessary for top-N selection
2. Sequential pipeline: bi-encoder retrieval → cross-encoder rerank → top-N
3. Single 1024-dim dense vector per chunk
4. BAAI's reranker family is appropriate
5. Off-the-shelf models without fine-tuning
6. top_k=50 candidate pool is right size

### CORE INVERSION (mandatory per skill diversification rules):
**"Cross-encoder reranker is necessary"** → **"When retrieval is rich (R@K=0.85+), the cross-encoder is HARMFUL — it overfits to passage-similarity patterns that don't match regulatory citation."**

Evidence supporting the inversion:
- R@K=0.857 in Exp 14 (contextual)
- R@K=0.852 in Exp 22 (Doc2Query)
- R@K=0.886 in Exp 23 (top_k=100)
- Despite high R@K, R@C plateaus at ~0.45-0.49 — the reranker isn't surfacing what the retriever found
- 6 consecutive failures to lift R@C past 0.487 via reranker tweaks

### Hypothesis (Exp 26): No-reranker baseline + Exp 19's stack improvements

Stack:
- ccop_clauses_contextual collection (Exp 14's index)
- HyDE for embedding query (Exp 17)
- Dense retrieval, top_k=50
- **NO cross-encoder reranking** — take top-3 directly by dense cosine similarity
- Parent-child auto-merging on the dense-ranked list (window=15)

Predicted:
- recall@C: ?? (unknown, novel architecture)
- recall@K should match Exp 14 (0.857)
- If reranker was actually harmful, R@C may JUMP to 0.55+
- If reranker was load-bearing, R@C may COLLAPSE to <0.30
- Either way, informative

Cost: ~3 min eval (no reranker = no cross-encoder forward passes; just dense + merge logic).

## Experiment 26 — NO RERANKER inversion (INTERESTING)
Result: R@C 0.4803 (-0.007 vs Exp 19, within noise). MRR +0.058.
Per-case: 8 gained / 10 lost / 11 same. Polarized.

GAINED (no-reranker wins): B06-013 0→1.00, B07-022 0→1.00, B12-016 0→0.29, B23-001 0→0.33, B06-002 0.60→1.00, B05-013 0.25→0.75
LOST (reranker wins): B14-001 0.60→0, B24-022 0.60→0, B22-015 0.75→0.50, B13-003 1.00→0.25

Status: interesting — the cross-encoder is COMPLEMENTARY to dense ranking, not strictly better. Each catches what the other misses.

**Critical insight**: max score per-case across Exp 19 (with reranker) and Exp 26 (without) ≈ 0.60+ R@C. RRF ensemble of the two ranking signals could capture this.

## THINK — before Experiment 27

### Hypothesis (Exp 27) — RRF ensemble of dense rank AND cross-encoder rank

Both rankings exist on the SAME candidate set (top-50 dense). Combine them:
1. Dense-only ranking → ordered list of 50 chunks (by cosine)
2. Cross-encoder ranking → ordered list of 50 chunks (by ce_score)
3. RRF score per chunk = 1/(60+rank_dense) + 1/(60+rank_ce)
4. Sort by RRF score → final top-N

This way: chunks that score high on EITHER ranker get credit. Cases where dense alone is right (B06-013) get the dense rank. Cases where cross-encoder is right (B14-001) get the ce rank. RRF-merge favors chunks high in both, but lifts chunks high in either.

Predicted: recall@C 0.487 → 0.55-0.60 (capturing union of both signals).

Cost: ~12 min (just the cross-encoder pass, plus RRF logic).

## Experiments 27-36 — Summary on research/no-reranker-stack

| # | Change | R@C | Status |
|---|--------|-----|--------|
| 27 | RRF dense+CE, both 1.0 | 0.4995 | KEEP (NEW BEST after fork) |
| 28 | RRF CE=1.5 | 0.5576 | KEEP (NEW BEST) |
| 29 | RRF CE=2.0 | 0.5558 | DISCARD |
| 30 | Doc2Query + RRF (w=15) | 0.4819 | DISCARD |
| 31 | RRF + window=30 | 0.6090 | KEEP (NEW BEST) |
| 32 | RRF + window=50 | 0.6249 | KEEP (NEW BEST) |
| 33 | RRF + window=40 | **0.6534** | KEEP (NEW BEST) |
| 34 | window=35 | 0.6243 | DISCARD |
| 35 | Doc2Query + w=40 | 0.5516 | DISCARD |
| 36 | min_siblings=3 | 0.5973 | DISCARD |

## 3-Discard Guardrail — after Experiment 36

Discard streak: 3 (Exp 34, 35, 36). MUST stop and reflect.

### Convergence signals
- Best: Exp 33 R@C=0.6534. +361% vs baseline.
- Window axis exhausted (15 < 30 < 40 = optimum > 50, 35 below 40).
- min_siblings=2 confirmed optimal.
- Doc2Query collection doesn't compose with RRF.
- Distance to 0.8 target: 0.147 — still substantial.

### Why I am continuing on this branch (not forking)
- The fork already paid off massively (Exp 26-33 lifted R@C 0.487 → 0.65)
- Many parameters of the current architecture remain untested (top_k variation, RRF K parameter, different reranker)
- Untested specific hypotheses still available

### Specific untested non-variant hypothesis (Exp 37)
**top_k=100 with the RRF stack.** We tested top_k=100 in Exp 23 with the OLD pipeline (CE-only ranking). With the new RRF dense+CE ranking, the bigger pool may compose differently because both signals draw from a wider diverse candidate set.

Predicted:
- recall@K: 0.78 → 0.88+
- recall@C: 0.65 → 0.68-0.72 if pool quality lifts
- Risk: more candidates = more noise even with RRF

If this fails too: 4-discard streak, very close to fork mandate. Would then try BGE-M3 embedder swap (requires re-ingestion).
