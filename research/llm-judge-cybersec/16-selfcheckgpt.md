# SelfCheckGPT (Manakul et al., EMNLP 2023)

**Category**: Hallucination detection — sampling-based consistency check
**Canonical sources**:
- Paper: [Manakul et al., EMNLP 2023 — arXiv:2303.08896](https://arxiv.org/abs/2303.08896)
- Code: [potsawee/selfcheckgpt](https://github.com/potsawee/selfcheckgpt)

## Scoring mechanics

Core idea: **if the model really knows, its samples agree; if it hallucinates, its samples diverge.** Zero-resource, black-box — no external knowledge base, no token logprobs needed.

### Pipeline

1. Generate the original response R₀ (typically temperature=0 or low).
2. Generate N additional samples S₁...Sₙ (typically N=5-20, temperature=1.0).
3. For each sentence in R₀, measure its consistency with S₁...Sₙ.
4. Per-sentence hallucination score = inconsistency measure; higher → more likely hallucinated.

### Five variants for the consistency measure

| Variant | Method | Cost | Reported AUC-PR |
|---------|--------|------|-----------------|
| BERTScore | Sentence-level embedding similarity between R₀ sentence and each Sᵢ | Low | Baseline |
| Question-Answering | Generate QA pairs from R₀, check if Sᵢ answers match | Medium | Strong |
| n-gram | Token-level probability under n-gram model over samples | Low | Weak |
| NLI | Run NLI model (e.g., DeBERTa) between R₀ sentence and each Sᵢ | Medium | Strong |
| LLM-Prompting | Ask a judge LLM if R₀ sentence is supported by S₁...Sₙ | High | Strongest |

Final score = mean (or max) of inconsistency across the N samples.

## Prompt scaffolding (LLM-Prompting variant)

```
Context: {concat(S_1..S_N)}
Sentence: {R_0 sentence i}
Is the sentence supported by the context above? Answer: YES or NO.
```

Applied per-sentence of R₀. Hallucination score = fraction of NO.

## Ground-truth requirements

**Reference-free.** SelfCheckGPT is zero-resource — no reference answer, no knowledge base, no gold retrieval. It relies solely on sampling distribution of the model under test.

This is a **profound GT cost advantage** — no annotation needed. But it has a matching limitation: the method detects knowledge-uncertainty-driven hallucination, not belief-coherent systematic errors (if the model confidently and repeatedly makes the same wrong claim, SelfCheckGPT will rate it as SUPPORTED).

## Annotation cost

Zero — the method is ground-truth-free.

## Bias / reliability controls

- **Sampling-based**: inherent robustness to single-sample noise (this is SelfCheckGPT's mechanism, not a side-effect).
- **Black-box**: works without access to logprobs — applicable to closed APIs.
- **Multi-variant**: can ensemble BERTScore + NLI + LLM-Prompting for higher AUC.

## Reported reliability

On WikiBio-GPT3 dataset:
- Sentence-level AUC-PR: 0.76 (LLM-Prompting variant) vs grey-box baseline ~0.56
- Passage-level factuality ranking: Spearman ~0.78

Higher AUC than grey-box methods (which need logprobs) — remarkable given zero external info.

## Reported limitations

- **Systematic errors escape**: if the model is confidently wrong across samples, SelfCheckGPT rates as SUPPORTED. For cybersecurity compliance, a model that consistently fabricates "CCoP Clause 5.9.7" across 20 samples would pass.
- **Sample cost**: N=20 samples × 118 test cases = 2,360 generations just for the model under test, before any judging. For a slow local Ollama model this is non-trivial; for API it's cost.
- **Temperature dependence**: sampling temperature affects the diversity of samples; low temperature → under-detection, high → false-positive hallucinations on correct-but-phrased-differently output.

## Citation / fact grounding

Implicit — the method doesn't check citations against a source of truth. It checks that the MODEL is consistent with itself. For regulatory citations (like "Clause 5.3.1(c)"), SelfCheckGPT would only detect hallucination if the model sometimes cites different clauses for the same answer.

## Domain fit for cybersecurity compliance QA

- **Partially applicable**: as a **complementary hallucination signal**, not a replacement for ground-truth citation verification. We could run SelfCheckGPT on the model's `{clause_reference}` mentions — if the model sometimes cites 5.3.1 and sometimes 5.2.1 for the same question, that's diagnostic.
- **Calibration value**: our current judge uses N=1 temperature=0.7; SelfCheckGPT's N-sample idea directly motivates multi-sample averaging for our overall scoring (not just hallucination detection).
- **Not applicable as-is**: for B21 (hallucination benchmark), we have ground-truth forbidden-claim lists — SelfCheckGPT would be redundant with our deterministic check. SelfCheckGPT's strength is for benchmarks where GT is absent or hard to construct.
- **Useful for dissertation**: reporting SelfCheckGPT hallucination-rate ALONGSIDE our judge-D3 score gives two independent signals on factual grounding — strong methodology story.

## Concrete borrowable patterns

1. **N-sample self-consistency** at the MODEL level — run the model under test 3-5 times and compute verdict agreement rate as a confidence signal.
2. **NLI variant** using DeBERTa-mnli (free, local, <1GB model) as a cheap reference-free hallucination screen.
3. **Per-sentence hallucination granularity** — our current D3 is a single dimension score; SelfCheckGPT validates per-claim scoring as the right granularity.

## Sources used

- Paper: https://arxiv.org/abs/2303.08896 (accessed 2026-04-24)
- Code: https://github.com/potsawee/selfcheckgpt (accessed 2026-04-24)
- ACL Anthology: https://aclanthology.org/2023.emnlp-main.557.pdf (accessed 2026-04-24)
