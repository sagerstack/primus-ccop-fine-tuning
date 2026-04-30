# RAGAS — Retrieval-Augmented Generation Assessment (Shahul et al., 2023; Explodinggradients)

**Category**: Industry framework — the dominant RAG evaluator library (2026)
**Canonical sources**:
- Paper: [Es et al., EACL 2024 — arXiv:2309.15217](https://arxiv.org/abs/2309.15217)
- Docs: [docs.ragas.io](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)
- Faithfulness: [docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/)
- Code: [explodinggradients/ragas](https://github.com/explodinggradients/ragas)

## Scoring mechanics

Per-metric, continuous 0.0-1.0 scale, no anchored levels. Metrics are composed of multiple LLM-based sub-steps. Primary metrics used in production:

| Metric | What it measures | Formula |
|--------|-----------------|---------|
| **Faithfulness** | Share of response claims supported by retrieved context | `|supported claims| / |total claims|` |
| **Answer Relevancy** | Does the answer address the question? | Cosine similarity between original question and LLM-reverse-engineered questions from the answer |
| **Context Precision** | Are retrieved chunks relevant and top-ranked? | Mean-average-precision-style ordering score |
| **Context Recall** | Did we retrieve all ground-truth-relevant chunks? | Share of ground-truth claims attributable to retrieved context |
| **Answer Similarity** | Semantic similarity to reference answer | Embedding cosine or LLM-rated similarity |
| **Answer Correctness** | Combined factual + semantic | Weighted combo of Faithfulness + Answer Similarity |

## Prompt scaffolding (Faithfulness example)

Two-stage LLM pipeline:

1. **Statement extraction**: decompose response into atomic claims.
   - Prompt: "Given the response, list each simple, standalone statement..."
2. **Verification**: for each claim, verify against retrieved context.
   - Prompt: "Does the following context support the claim? Respond YES/NO."
3. Score = YES count / total claims.

This is effectively **FActScore** applied to retrieved context instead of a knowledge base — RAGAS adopts FActScore's atomic-fact decomposition pattern and specializes it for RAG.

## Ground-truth requirements

- **Faithfulness** — requires ONLY `(question, answer, retrieved_contexts)`. No reference answer needed. Fully reference-free.
- **Answer Relevancy** — `(question, answer)` only.
- **Context Recall / Answer Similarity / Answer Correctness** — require `ground_truth` reference answer field.

### Schema RAGAS expects

Per-sample dict:
```python
{
  "user_input": str,          # the question
  "response": str,            # model output
  "retrieved_contexts": list[str],  # chunks pulled by retriever
  "reference": str,           # ground-truth answer (optional — required for recall/similarity)
  "reference_contexts": list[str]   # ideal retrieved set (optional — for context_recall)
}
```

RAGAS does NOT expect:
- Tiered key_facts
- Expected clause IDs
- Forbidden claims
- Per-case instance rubrics

It treats the ground-truth as a **single reference answer** and lets the LLM do the atomic-claim decomposition at eval time. Our schema is richer but misaligned with the RAGAS schema shape.

## Annotation cost

- Per test case: requires `(question, reference)` — same burden as our current `expected_response`.
- Optional `reference_contexts` (gold-retrieved chunks) adds 5-15 min per case of annotator effort.

## Bias / reliability controls

- **Reference-free faithfulness** → no annotator bias on the reference side; but high dependence on judge LLM quality.
- **HHEM-2.1-Open integration**: Vectara's open hallucination classifier (T5-based) can replace the LLM call in the Faithfulness verification step — fast, cheap, reproducible. Not as accurate as GPT-4 but deterministic.
- No explicit position-bias controls (faithfulness per-claim is independent; not pairwise).
- No N-sample averaging built-in.

## Reported reliability

- Es et al. EACL 2024 paper reports ~0.80-0.85 correlation with human judgment on WikiEval for faithfulness; slightly weaker for answer relevancy.
- Community benchmarks (Langfuse, Vectara) report faithfulness is the most stable RAGAS metric; answer_relevancy is noisier.

## Reported limitations

- Atomic-fact decomposition is LLM-dependent — different judge LLMs produce different claim granularity.
- Answer Relevancy's reverse-question generation is prone to verbosity artifacts.
- Context Precision / Recall require gold retrieval annotations that most projects don't have.
- Faithfulness can miss **implicit** hallucinations — claims that aren't explicitly stated but are presupposed.

## Domain fit for cybersecurity compliance QA

- **Directly applicable**: Faithfulness metric maps well to our D3 factual_grounding — it's essentially claim-level grounding against retrieved CCoP clauses.
- **Partially applicable**: our ground truth carries `clause_reference` which RAGAS doesn't use; we'd need to either (a) feed `expected_citations_text` as `reference_contexts` or (b) compute faithfulness against RAG-retrieved contexts (aligned with our hybrid mode).
- **Not applicable as-is**: RAGAS's continuous 0-1 scoring doesn't slot into our anchored 0-3 rubric without mapping. A common adaptation is to threshold continuous → discrete (e.g., <0.3 → 0, <0.6 → 1, <0.85 → 2, else 3).
- **Useful complement**: RAGAS as a secondary metric for validation — run it in parallel with our 5-dim judge and measure divergence as a confidence signal.

## Concrete borrowable patterns

1. **Atomic-claim decomposition** as a prerequisite step before D3 scoring — inherit from RAGAS's Faithfulness pipeline.
2. **HHEM-2.1-Open** as a deterministic fallback for claim verification when Claude/API access is rate-limited.
3. **Per-claim SUPPORTED/UNSUPPORTED binary** — our universal judge already does this in `UNIVERSAL_JUDGE_PROMPT`; the RAGAS formula validates it.
4. **Reference_contexts schema field** — add expected-relevant chunks to our ground truth, unlocking context_recall measurement.

## Sources used

- Paper: https://arxiv.org/abs/2309.15217 (accessed 2026-04-24)
- Docs root: https://docs.ragas.io/en/stable/concepts/metrics/overview/ (accessed 2026-04-24)
- Faithfulness: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/ (accessed 2026-04-24)
- GitHub: https://github.com/explodinggradients/ragas (accessed 2026-04-24)
