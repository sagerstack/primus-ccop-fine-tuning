# Parking Lot — Deferred Ideas

Ideas surfaced during experimentation that aren't being tested right now but might be worth revisiting.

## Pre-experiment ideas (from baseline analysis)

- **Re-ingestion with smaller chunks** — current chunks may be too large; smaller might improve retrieval recall.
- **Re-ingestion with larger chunks** — opposite hypothesis; current chunks may be too small to give the model useful context.
- **BGE-M3 instead of bge-large-en-v1.5** — newer multilingual model might be better.
- **Increase rerank_top_n from 3 to 5/8** — model gets more retrieved context.
- **Lower grading score threshold** — maybe filtering out useful borderline-relevance docs.
- **Disable the docs grading step entirely** — pass all reranked top-N to the model.
- **Hybrid scoring weight tuning** — currently equal RRF, try dense-favored or sparse-favored.
- **Query rewriting** — generate multiple query variants for better retrieval.
- **Improve generation prompt** — be more explicit about "use ONLY retrieved context" + "cite clauses by ID".
- **Penalize judge for unjustified uncited assertions** — make judge stricter on D3 when context is provided.
- **Add D6 safety dim** — out of scope for this research, but could affect composite.

## Mid-experiment additions

### After Exp 1 diagnostic

- **Top-k=40+** — ✅ TESTED Exp #5/#5b/#6/#7. k=50 gives recall_topk=0.50; k=100 gives 0.62 (embedder ceiling).
- **rerank_top_n=5 or 8** — pass more retrieved chunks to LLM so a relevant one is more likely included.
- **Domain-tuned reranker** — ✅ TESTED Exp #7. BAAI/bge-reranker-large gave +0.097 recall_topn over no-reranker. BAAI/bge-reranker-v2-m3 still untested.
- **Generation prompt: force clause citation** — current generation prompt doesn't strongly require "cite by clause ID". Adding: "Every assertion about CCoP must reference the clause ID in the form X.Y.Z(letter) directly from the retrieved context." Could lift D3 score independent of retrieval.
- **Ban invented frameworks** — model invented "Risk Priority Number" framework with weights 0.8/0.9/0.2. Add to system prompt: "Do NOT invent risk frameworks or numerical weights not present in retrieved context."
- **Score sidecar bug** — saved similarity_score is 0.000 for all retrieved chunks. Either reranker overwrites with 0 or serialization clobbers. Fix would help debugging.

### After Exp 7 (bge-reranker breakthrough)

- **bge-reranker-v2-m3** — newer multilingual variant, possibly better than bge-reranker-large for technical text. Lighter/faster too.
- **Query rewriting** — Address R@K ceiling (0.62 at k=100). Augment query with regulatory keywords ("shall include", "CII", "the audit shall", clause-pattern hints) so embedder's nearest-neighbor retrieval is closer to ground truth.
- **BGE-M3 embedder** — multilingual, dense+sparse+colbert all-in-one. Could surface CCoP clauses better than BGE-large-en-v1.5 (English-only, general purpose).
- **Re-chunking** — current chunks may split sub-clauses across boundaries. Test smaller (sentence-level) and larger (full-section) chunks.
- **Hybrid weight tuning** — currently equal RRF (k=60). Could tune dense vs sparse weighting.
- **Investigate B08-001 reranker failure** — clauses 3.2.2(b)/(c) ARE in candidate set at k=50, bge-reranker still doesn't pick them. Why? Inspect cross-encoder scores per case.
