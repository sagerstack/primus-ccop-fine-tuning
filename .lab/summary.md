# Research Summary — Maximize CCoP Retrieval Quality

**Period**: 2026-04-25 → 2026-04-26
**Branches**: `research/maximize-rag-vs-llm-only` (#0-#25, plateaued) → `research/no-reranker-stack` (#26-#41)
**Total experiments**: 41 (real + thought + re-scores)
**Active branch**: `research/no-reranker-stack` (Exp #41 best correctness-preserving result)

## Headline Metric

**Primary metric (v3): mean_recall_at_C** — strict citation match against agent-team-corrected ground truth, where N = case-specific GT cardinality (cardinality-fair retrieval metric).

```
Baseline (Exp #0v2):                            0.1417
Best correctness-preserving (Exp #41):          0.5484
Lift:                                           +0.4067 absolute, +287% relative
Distance to 0.8 target:                         0.2516
```

## Important Methodological Note

Exp #33 scored higher (R@C = 0.6534) but used gpt-4o-mini-generated contexts that contained 86 chunks (17%) with hallucinated acronym expansions ("Chief Information and Innovation Officer" instead of the correct "Critical Information Infrastructure Owner"). These cosmetic hallucinations accidentally increased retrieval performance through expansion *variety* across chunks. Disqualified for production/dissertation purposes — methodology cannot rely on factual errors.

Exp #41 (acronyms-only contexts) eliminates hallucinations while preserving loose synonym-heavy style. Score is lower (~ -0.10) but methodology is defensible.

## Best Configuration (Exp #41)

```
Pipeline:
  Query (user)
  → HyDE rewrite via gpt-4o-mini → hypothetical CCoP-style clause
  → BGE-large-en-v1.5 dense embed of HyDE output
  → Qdrant dense-only retrieval, top_k=50
        (against ccop_clauses_contextual_v3:
         each chunk has breadcrumb + LLM-generated context line + original text;
         contexts use acronyms verbatim, no expansion)
  → bge-reranker-large cross-encoder
        (scores against ORIGINAL clause text, not augmented)
  → RRF ensemble of dense rank + cross-encoder rank
        (RRF: K=60, dense_weight=1.0, ce_weight=1.5)
  → Parent-child auto-merge of sibling clauses
        (window=40, min_siblings=2)
  → top-N delivered to LLM
```

## Multi-N Performance (Exp #41)

| N | Recall | F1 |
|---|--------|-----|
| 3 | 0.456 | 0.32 |
| 5 | 0.548 | — |
| 8 | 0.647 | — |
| C (cardinality, primary) | **0.5484** | 0.312 |
| K (full pool, k=50) | 0.752 | — |

## Top Most-Impactful Changes (correctness-preserving)

1. **+0.108** Exp #7 — BAAI/bge-reranker-large (vs ms-marco) — domain-tuned cross-encoder
2. **+0.064** Exp #16 — Parent-child auto-merging (window=10) — addresses cardinality
3. **+0.057** Exp #19 — Merge window 10→15 — wider sibling capture
4. **+0.058** Exp #28 — RRF CE-favored weighting (1.5 vs 1.0) — recovers CE-strong cases
5. **+0.052** Exp #31 — Merge window 15→30 — catches mid-rank clusters
6. **+0.029** Exp #33 — Merge window 30/50→40 — final sweet spot
7. **−0.105** Exp #41 — eliminating hallucinations (correctness adjustment, accepted)

Plus foundational: contextual chunking (Anthropic-style), HyDE query rewriting, agent-team-corrected GT.

## Branch Genealogy

```
Baseline (#0v2)
   |
   +─ research/maximize-rag-vs-llm-only (#0-#25)
   |    Best: 0.4874 (Exp #19)
   |    Plateaued — 6 discards in row (#20-25)
   |
   +─ research/no-reranker-stack (forked from #0)
        Inverted assumption: "reranker is necessary" → "reranker is harmful when retriever is rich"
        Discovery (Exp #26): NO-rerank shown complementary to CE
        Solution (Exp #27+): RRF ensemble of dense + CE ranks
        Local optimum (Exp #33): 0.6534 (HALLUCINATION-DEPENDENT — disqualified)
        Defensible best (Exp #41): 0.5484 — acronyms-only contextualization
```

## Cumulative Progression (correctness-preserving track)

```
0.142 → Exp #0v2 baseline (corrected GT, original pipeline)
0.250 → Exp #7  bge-reranker-large
0.283 → Exp #11 dense-only retrieval (vs hybrid RRF)
0.310 → Exp #14 contextual chunking
0.355 → Exp #15 decoupled reranker text
0.419 → Exp #16 parent-child merging w=10
0.430 → Exp #17 HyDE
0.487 → Exp #19 merge window=15
0.500 → Exp #27 RRF dense+CE ensemble (fork)
0.558 → Exp #28 RRF CE=1.5
0.609 → Exp #31 window=30
0.625 → Exp #32 window=50
0.6534 → Exp #33 window=40 (hallucination-dependent — DISQUALIFIED)
0.5484 → Exp #41 acronyms-only contexts (CORRECTNESS-PRESERVING BEST)
```

## Key Insights

### Architectural

1. **Cross-encoder rerankers are double-edged on regulatory text**: bge-reranker-large helps half our cases and hurts the other half (Exp #26). It's complementary to dense retrieval, not strictly better.

2. **RRF ensemble of dense + CE ranks** captures both signals' strengths. CE-favored weighting (1.5x) recovers the best of both worlds.

3. **Parent-child auto-merging is essential for high-cardinality GT**: When 4-8 expected clauses share a section, merging siblings into a single result captures cardinality without bloating top-N.

4. **Anthropic-style contextual chunking** lifted R@K substantially. The mechanism is **vocabulary diversity** in the indexed text — the ability to bridge user queries to formal clause language.

5. **HyDE query rewriting** addresses vocabulary mismatch between conversational queries and formal regulatory text.

6. **Decouple embedder text from reranker text**: When chunks have augmented prefixes (breadcrumb + context), the reranker should still score against the *original* clause text. Cross-encoders aren't trained on doc-prefix metadata.

### Methodological — Counterintuitive but Important

7. **Hallucinated contexts can accidentally improve retrieval scores** (Exp #33 vs #39/#40/#41). The mechanism is *expansion variety*: when an LLM doesn't know a domain acronym, it invents different expansions across chunks, which broadens the embedding-space coverage. **This is not a defensible engineering pattern** — it's a fluke that disappears with better-trained models. Production systems must use correctness-preserving contextualization even at lower retrieval scores.

8. **Three independent attempts to fix hallucinations all hurt retrieval** (Exp #39 grounded Claude, Exp #40 dictionary constraint, Exp #41 no-expansion instruction). The mechanism is the same: any constraint on the LLM produces more *uniform* contexts, which clusters embeddings and reduces vocabulary-bridging surface area. Best balance: Exp #41 (just instruct "use acronyms verbatim").

9. **Ground truth correction via agent-team is foundational**: 24 of 30 original test cases had wrong/incomplete clause references. Re-measuring against corrected GT lifted apparent retrieval performance dramatically.

10. **Cardinality-fair metric (recall@C) > fixed N=3** when GT cardinality varies (avg 4.7 in our sample). Production should also bump top_n=8 for the LLM (recall@8 = 0.65 in best config).

### Failed Approaches

- ms-marco-MiniLM cross-encoder (Exp #6)
- bge-reranker-v2-m3 (Exp #9)
- Static query suffix (Exp #10)
- Multi-query RRF dilutes HyDE wins (Exp #18)
- BGE-M3 embedder (Exp #38)
- Doc2Query collection with RRF (Exp #30, #35)
- top_k=100 with any stack (Exp #8, #23, #37)
- Merge window outside 30-50 (Exp #20, #34)
- Hallucination-fix attempts at contextualization (Exp #39, #40)

## Why Plateau at 0.55 (Correctness-Preserving)

Local-parameter sweeps and major architectural axes all explored. Remaining lift to 0.8 (~+0.25) requires structural changes outside autonomous-research scope:

1. **External reranker APIs** (Cohere/Jina/Voyage) — different model class
2. **LLM-as-reranker** (high cost, slow)
3. **Embedder fine-tuning** (excluded by user direction)
4. **Domain-tuned cross-encoder fine-tuning** (excluded by user direction)
5. **Different chunking strategies** (multiple variants tested, marginal impact)

## Production Recommendations

1. **Use Exp #41's pipeline** as the production retrieval methodology. Production-defensible (no hallucinations) with R@C = 0.55.

2. **Set production top_n=8**: practical recall jumps from 0.46 (top_n=3) to 0.65 (top_n=8) with manageable LLM context cost.

3. **Use the agent-team-corrected GT** as the test suite reference (24 of 30 cases updated).

4. **Track recall@C, not recall@3** as the primary retrieval metric in dissertation; report multi-N curve alongside.

5. **In dissertation, report Exp #41 as best result**, with a section discussing the Exp #33 vs Exp #41 finding (hallucination accidentally helping retrieval — counterintuitive but not exploitable as methodology).

## Code State

Active branch `research/no-reranker-stack` contains all experiment scripts in `.lab/`.

Reproduction command for Exp #41 (production-defensible best):
```bash
cd src && poetry run python ../.lab/workspace/retrieval_eval.py \
  --sample-file ../research/human-kappa-seed/00-sample-selection.json \
  --rerank-enabled true --top-k 50 --top-n 3 \
  --ce-model BAAI/bge-reranker-large \
  --retrieval-mode dense \
  --collection ccop_clauses_contextual_v3 \
  --corrected-gt ../.lab/workspace/agents/corrected-gt.json \
  --corrected-gt-field recommended_ccop_only \
  --merge-parents --merge-window 40 --merge-min-siblings 2 \
  --hyde \
  --reranker-text rrf_dense_ce \
  --rrf-dense-weight 1.0 --rrf-ce-weight 1.5 \
  --label "best_exp41" \
  --output ../.lab/workspace/best_exp41.json
```

## Final Numbers

| Metric | Exp #41 (production) | Comparison: Exp #33 (hallucinated) |
|--------|----------------------|-------------------------------------|
| recall@C (primary) | **0.5484** | 0.6534 |
| recall@3 | 0.4558 | 0.5470 |
| recall@5 | 0.5484 | 0.6238 |
| recall@8 | 0.6465 | 0.7103 |
| recall@K (k=50) | 0.7516 | 0.7764 |
| F1@C | 0.312 | 0.379 |
| Methodology defensible | ✓ | ✗ (hallucination-dependent) |

Final answer: **R@C = 0.5484, +287% over baseline, hallucination-free retrieval.**
