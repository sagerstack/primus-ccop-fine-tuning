# Auto-J (Li et al., ICLR 2024)

**Category**: Academic fine-tuned generative judge, Llama-2-based, scenario-oriented
**Canonical sources**:
- Paper: [arXiv:2310.05470](https://arxiv.org/abs/2310.05470) (v2 December 2023, ICLR 2024 accepted)
- GitHub: [GAIR-NLP/auto-j](https://github.com/GAIR-NLP/auto-j)
- Project page: [gair-nlp.github.io/auto-j](https://gair-nlp.github.io/auto-j/)
- HF: [GAIR/autoj-13b](https://huggingface.co/GAIR/autoj-13b)

## Base model + size

| Variant | Base | Parameters |
|---------|------|-----------|
| Auto-J | LLaMA-2-13B-Chat | 13B |
| Auto-J-Bilingual | Yi-6B | 6B (EN + ZH) |
| Scenario Classifier | LLaMA-2-13B | 13B |

## Training data / method

**Distinctive feature: 58 predefined scenarios**, condensed into 8 major groups. Each scenario has **hand-designed criteria** written by the paper's authors — this is conceptually closest to our "CCoP compliance rubric" design.

- Data collection: real-world user queries + responses from various chatbots (Chatbot Arena Conversations). Queries categorized by the scenario classifier into one of 58 scenarios.
- Training: GPT-4 generates judgments using the scenario-specific criteria as context. Output is a natural-language critique + final verdict (pairwise) or rating (single-response).
- Pairwise training size: 3,436 samples. Single-response training size: 960 samples.
- Training stack: DeepSpeed ZeRO; fine-tuned from LLaMA-2-13B-Chat.

## License

- Auto-J (13B): **LLaMA-2 Community License** per GitHub README table. Commercial-use permitted under 700M MAU and Llama-2's use-case restrictions. [Source: github.com/GAIR-NLP/auto-j README].
- Auto-J-Bilingual (6B): **Yi License** (research-only as of the release date).
- Scenario Classifier (13B): LLaMA-2 Community License.
- Training data: subject to Chatbot Arena Conversations dataset terms.

**License confidence: HIGH** — GitHub README explicitly lists the license per checkpoint.

## Deployment profile

| Variant | FP16 VRAM | Q4 VRAM (GPTQ-4bits released by authors) | Fits 24 GB? |
|---------|-----------|------------------------------------------|-------------|
| Auto-J | ~26 GB | ~8 GB | Yes at Q4 (authors publish [GAIR/autoj-13b-GPTQ-4bits](https://huggingface.co/GAIR/autoj-13b-GPTQ-4bits)) |

**The authors ship a GPTQ-4bit quantization officially**. This is a plus — no community-uploaded quantization risk.

Integration: HF transformers + vLLM. The repo uses vllm-project/vllm for inference.

## Reported reliability numbers

**Primary paper (Table in project page):** Single-response rating on Auto-J's 58-scenario testbed:

| Model | Ranking | Agreement |
|-------|---------|-----------|
| **Auto-J** | 1 | 73.7 |
| GPT-4 | 2 | 58.2 |
| ChatGPT | 3 | 50.0 (reference) |
| LLaMA-2-13B-Chat | 4 | 47.0 |

On this in-distribution benchmark, Auto-J dramatically beats GPT-4 (+15.5 pp). **Confidence: MEDIUM — authors' own benchmark, no cross-replication.** The paper's primary contribution is on pairwise evaluation where gains are smaller.

**Prometheus 2 paper (arXiv:2405.01535 v2, Table 2):** Auto-J (13B) on direct-assessment across 4 benchmarks:

| Benchmark | Auto-J Pearson | Prometheus-2-7B | Prometheus-2-8x7B |
|-----------|---------------|-----------------|-------------------|
| VicunaBench | 0.282 | 0.543 | 0.559 |
| MT-Bench | 0.242 | 0.476 | 0.515 |
| Feedback-Bench | 0.515 | 0.784 | 0.800 |

**Auto-J is meaningfully weaker than Prometheus 2** on direct-assessment benchmarks. The authors' own testbed results (agreement 73.7%) do not translate to better Pearson correlation on external benchmarks. **Confidence: HIGH** on the Prometheus-2 comparison — peer-reviewed paper, independently measured.

**JudgeBench (arXiv:2410.12784) result**:

| Knowledge | Reasoning | Math | Coding | Overall |
|-----------|-----------|------|--------|---------|
| 40.26 | 29.59 | 44.64 | 28.57 | 36.57 |

Better than JudgeLM-7B/13B but below Prometheus-2-BGB-8x7B. **Confidence: HIGH** — JudgeBench paper Table 4.

## Reference-aware scoring support

**Partial.** The single-response prompt (Tab 15 in Auto-J paper) accepts a query and the response-to-evaluate, but does NOT have a dedicated reference-answer slot. You can inject the reference into the query or a system prompt, but Auto-J was not explicitly trained on reference-anchored data.

**This is a meaningful limitation for us.**

## Instance-rubric support

**No per-case anchored descriptors**, but **yes for scenario-level criteria**. Auto-J supports 58 pre-baked scenarios, each with hand-written criteria. If our 24 CCoP benchmarks map to "compliance classification" or "gap identification" etc., we could adopt Auto-J's scenario framing. But we'd need to either:
(a) pick the closest Auto-J scenario and accept its criteria, or
(b) retrain Auto-J with CCoP-specific scenarios (significant work).

For our use case — per-case instance rubrics — **Auto-J does NOT support this natively**.

## Cybersecurity / regulatory / compliance fit

- None of the 58 scenarios are explicitly cybersecurity or regulatory compliance.
- The closest scenarios are "writing_general" and "exam_question" categories (per `other_resources/scenario_classifier_data/`).
- Base model Llama-2-13B-Chat has MMLU ~55% — below Llama-3-8B-Instruct's 68% and well below Qwen2.5-14B's 80%.
- **No cybersecurity benchmarking** in the Auto-J paper.

## Known failure modes

- **Position bias**: "lessened" per paper's analysis but not eliminated.
- **Scenario misclassification**: if the scenario classifier mis-categorizes a query, the rubric is wrong. The paper provides a scenario classifier at 13B, which adds overhead.
- **Weaker on direct-assessment vs pairwise** (see Prometheus 2 comparison above).
- **Base model age**: Llama-2 (2023) is now 2+ generations behind frontier open models.

## Ease of integration

- HuggingFace transformers: straightforward.
- GPTQ-4bits: authors publish ready-to-use 4-bit version — plug-and-play on a 24 GB GPU.
- Python library: repo ships inference scripts, no pip package.
- Ollama: community GGUFs exist; not first-party.

**Integration effort: ~1 day** to wire up, but another ~3-5 days to figure out the right scenario mapping for CCoP — which defeats the point of a "drop-in rubric-aware judge."

## Recommendation summary

- **Strength**: Scenario-oriented design conceptually maps to domain-specific evaluation; authors ship quantization.
- **Weakness for us**: Older Llama-2 base; weaker on direct-assessment Pearson than Prometheus 2; no first-class reference-answer slot; no instance rubric.
- **Verdict**: Not a primary candidate. The scenario-criteria pattern is interesting methodologically (we could borrow the "per-scenario criteria authored by hand" approach for our own benchmark design), but as a deployable judge it's dominated by Prometheus 2 and M-Prometheus.

## Sources used (all verified accessible 2026-04-24)

- [arXiv:2310.05470](https://arxiv.org/abs/2310.05470)
- [github.com/GAIR-NLP/auto-j](https://github.com/GAIR-NLP/auto-j)
- [gair-nlp.github.io/auto-j](https://gair-nlp.github.io/auto-j/)
- [huggingface.co/GAIR/autoj-13b](https://huggingface.co/GAIR/autoj-13b)
- [huggingface.co/GAIR/autoj-13b-GPTQ-4bits](https://huggingface.co/GAIR/autoj-13b-GPTQ-4bits)
- [Prometheus 2 paper (arXiv:2405.01535)](https://arxiv.org/abs/2405.01535) v2 Table 2 for cross-benchmarking
- [JudgeBench paper (arXiv:2410.12784)](https://arxiv.org/abs/2410.12784) Table 4
