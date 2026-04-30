# Scope and Shortlist — Open-Source Judge Landscape Follow-up

**Purpose**: Expand the judge landscape beyond Prometheus 2 (the only open-source judge covered in the main research) so we can make an informed decision for the CCoP 2.0 cybersecurity compliance evaluation pipeline.

**Out-of-scope** (explicitly excluded):
- Closed-source API judges (Claude, GPT-4, Gemini) — already decided against per the task brief.
- Pure classifier reward models (Skywork-Reward non-critic, ArmoRM, InternLM2-Reward). These emit a scalar only, no rubric/justification → not compatible with our 5-dim + justification requirement. Noted in landscape table but not profiled.
- LLM-as-judge frameworks that are "orchestration wrappers" around external LLMs (microsoft/llm-as-judge, EvalSense). These are not themselves judges; they call other judges.
- Prometheus 1 — superseded by Prometheus 2; all facts already captured in the main research's `12-prometheus-2.md`.

## Our requirements (re-stated)

| Requirement | Hard / Soft |
|-------------|-------------|
| Reference-aware direct assessment (not only pairwise) | Hard |
| Instance-rubric support (user-specified score descriptors) | Hard |
| Reproducible (pinned weights OR temperature + seed controllable) | Hard |
| Local deployment on single RTX 4090-class GPU (24 GB VRAM) | Hard |
| Commercially-usable OR academic-research-usable license | Hard (research-only still OK for dissertation) |
| Cybersecurity / regulatory reasoning quality | Soft but important |
| Integrates cleanly with HF transformers / vLLM / Ollama | Soft |

**Scale budget**: ~1,770 judge calls per full eval (118 cases × 5 dims × 3 samples). A single 24 GB GPU must complete this in a reasonable window (hours, not days).

## Candidates covered

| # | Candidate | File | Why included |
|---|-----------|------|--------------|
| 1 | **Prometheus 2 ecosystem — 2025 updates & M-Prometheus** | `11-prometheus-2-2025-updates.md` | Most-cited open judge; 2025 updates include multilingual M-Prometheus (Qwen2.5-based). |
| 2 | **JudgeLM (7B / 13B / 33B)** | `12-judgelm.md` | Explicitly trained as judge; 90%+ teacher agreement; ICLR 2025 Spotlight. |
| 3 | **PandaLM (7B / 13B / 70B)** | `13-pandalm.md` | Earliest open judge; human-annotated test set; LLaMA-based. Still cited as baseline on JudgeBench. |
| 4 | **Auto-J (13B)** | `14-auto-j.md` | 58-scenario coverage; scenario-specific criteria are conceptually closest to our domain-specific rubric. Llama-2-13B. |
| 5 | **Self-Taught Evaluator (Llama-3.1-70B)** | `15-self-taught-evaluator.md` | Meta FAIR, no human annotations; 88.7% on RewardBench; research-license-only. |
| 6 | **Skywork-Critic (8B / 70B)** | `16-skywork-critic.md` | Top RewardBench generative judge as of Sep-2024; available in 8B. |
| 7 | **SFR-Judge (8B / 12B / 70B)** | `17-sfr-judge.md` | Salesforce; top-performing on 10/13 judge benchmarks; single-rating mode. |
| 8 | **Llama-3.1-70B / Qwen2.5-72B as prompted judges** | `18-prompted-generalist-judges.md` | JuStRank top performer; no fine-tuning; local-run demands 2× 4090 or 1× A100. |
| 9 | **JudgeLRM (3B / 7B / 14B)** | `19-judgelrm.md` | RL-trained reasoning judge; Qwen2.5-7B base; claims >GPT-4 at 3B. Used by the compliance-QA CA-Judge paper. |
| 10 | **CompassJudger-2 (7B / 32B)** | `20-compassjudger-2.md` | 2025 generalist judge; Qwen2.5-based; JudgerBenchV2 leader among 7B models. |
| 11 | **M-Prometheus (3B / 7B / 14B)** | Covered inside `11-prometheus-2-2025-updates.md` | Prometheus 2 recipe applied to Qwen2.5; Apache-2.0; 14B fits in 24 GB quantized. |

## Candidates dropped / out-of-scope

| Candidate | Why dropped |
|-----------|-------------|
| **Prometheus 3** (hypothetical) | No paper, no weights — not released as of 2026-04-24. M-Prometheus (2025) is the closest successor. |
| **Prometheus-Mini** (hypothetical) | Not a real model. The 7B Prometheus 2 IS the "mini" variant. |
| **Themis (8B, Xie et al. 2024)** | Reference-**free** by design (aclanthology.org/2024.emnlp-main.891). Our pipeline injects a reference answer → Themis's selling point is irrelevant to us. Noted only in landscape table. |
| **Themis (Baidu-internal, Wu et al. 2025, arXiv 2502.02988)** | Different paper, internal fine-tuned 8B. Not open-weighted on HF as of verification date. |
| **OffsetBias (8B)** | Bias-correction auxiliary; pairwise-only. Used inside SFR-Judge training data. Noted in table. |
| **Pure reward models** (Skywork-Reward, InternLM2-Reward, ArmoRM, URM, QRM) | Classifier head returns a scalar, no critique/justification → incompatible with our 5-dim output shape. |
| **Nemotron-4-340B-Reward** | 340B parameters; infeasible on 24 GB. |

## Methodology

- **URL verification**: every cited URL fetched via `mcp__exa__web_fetch_exa` or `WebSearch`; dead links removed.
- **Reliability claims**: only numbers sourced from primary paper, official HuggingFace model card, or Papers-with-Code entry. No "reportedly ~0.85" without citation.
- **License confidence**: license read from HuggingFace model-card YAML frontmatter or the repo LICENSE file.
- **Benchmark meta-evaluation landscape**: the credible meta-judge benchmarks in scope are **JudgeBench** (arXiv:2410.12784, ICLR 2025), **RewardBench v1 / v2** (Allen AI, arXiv:2506.01937), **JuStRank** (ACL 2025, arXiv:2412.09569), **JETTS** (ICML 2025, arXiv:2504.15253), and **ContextualJudgeBench** (ACL 2025, arXiv:2503.15620). Our recommendation file cites these as shared reference points.

## Final deliverables

| File | Content |
|------|---------|
| `00-scope-and-shortlist.md` | This file. |
| `11-prometheus-2-2025-updates.md` | Prometheus-eval ecosystem in 2025 + M-Prometheus deep-dive. |
| `12-judgelm.md` | JudgeLM 7B/13B/33B. |
| `13-pandalm.md` | PandaLM 7B/13B/70B. |
| `14-auto-j.md` | Auto-J 13B. |
| `15-self-taught-evaluator.md` | Meta FAIR Self-Taught Evaluator 70B. |
| `16-skywork-critic.md` | Skywork-Critic 8B / 70B. |
| `17-sfr-judge.md` | Salesforce SFR-Judge 8B / 12B / 70B. |
| `18-prompted-generalist-judges.md` | Llama-3.1-70B-Instruct + Qwen2.5-72B-Instruct as prompted judges. |
| `19-judgelrm.md` | JudgeLRM 3B / 7B / 14B. |
| `20-compassjudger-2.md` | CompassJudger-2 7B / 32B. |
| `20-landscape-comparison.md` | Side-by-side comparison table across 12 requirements. |
| `30-recommendation.md` | Concrete go-forward pick with reasoning. |
| `90-sources.md` | Every URL with access date. |
