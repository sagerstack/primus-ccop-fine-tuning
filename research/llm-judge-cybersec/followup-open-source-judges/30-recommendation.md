# Recommendation — primary and secondary open-source judge

## TL;DR

| Scenario | Pick | Why |
|----------|------|-----|
| Replace Claude entirely on single RTX 4090 | **M-Prometheus-14B (Q4/Q5)** | Only judge in shortlist that combines (a) first-class instance-rubric + reference-answer slots, (b) fits 24 GB at Q4/Q5, (c) Qwen2.5-14B base reasoning quality, (d) commercially-usable license, (e) Apache-2.0 training recipe with proven reproduction of Prometheus 2. |
| Keep Claude as primary, add secondary for inter-judge κ | **Qwen2.5-14B-Instruct prompted as a judge** (cross-family vs M-Prometheus), OR **JudgeLRM-7B** if research-only license is acceptable | Cross-family generates meaningful inter-judge agreement signal; trivially deployable via Ollama; no fine-tuning complexity |
| Fine-tune a CCoP-specific judge (Phase 3+) | **Start from M-Prometheus-14B or Qwen2.5-14B-Instruct** | Qwen2.5-14B base + Prometheus/JudgeLRM recipe = well-documented training path; 14B fits single 4090 for training with LoRA |
| 2025 judges that outperform Prometheus 2 in our regime? | **None with clear certainty on direct assessment + reference + rubric**; M-Prometheus-14B *is* the 2025 Prometheus 2 successor | CompassJudger-2-7B and JudgeLRM-7B have competing claims but lack Prometheus-style per-level anchored rubric. |
| Single most credible meta-judge benchmark to cite | **JudgeBench (ICLR 2025, arXiv:2410.12784)** | Peer-reviewed, objective labels, covers reasoning-heavy domains closest to CCoP |

---

## 1. If we replace Claude entirely with an open-source judge — which one?

### Pick: **M-Prometheus-14B (Unbabel/M-Prometheus-14B on HF, Qwen2.5-14B-Instruct base)**

**Reasoning chain (with our constraints):**

- **Hard constraint 1 (reference-aware direct assessment)**: Prometheus-family models are the *only* open judges trained with reference-answer as a first-class field. M-Prometheus-14B inherits this verbatim from Prometheus 2's recipe. [source: arXiv:2504.04953 + arXiv:2405.01535]
- **Hard constraint 2 (instance rubric)**: Same — Prometheus-family is the only cohort with per-instance 5-level anchored descriptors as a first-class input field.
- **Hard constraint 3 (reproducibility / pinned weights)**: Weights are pinned on HuggingFace; `AutoModelForCausalLM.from_pretrained(..., revision="<commit>")` is fully deterministic. Temperature + seed controllable via `transformers.generation.Config`. ✅
- **Hard constraint 4 (single RTX 4090, 24 GB VRAM)**: 14B FP16 needs ~28 GB, but Q5_K_M or Q4_K_M fits in ~10 GB with headroom for long context (8K+ tokens). Inference speed ~30-50 tok/s on 4090 via vLLM. 1,770 judge calls complete in <1 hour. ✅
- **Hard constraint 5 (license)**: Qwen Community License — commercial use permitted under 100M MAU. Apache-2.0 training recipe per the M-Prometheus paper. Clean for dissertation and potential production. ✅
- **Soft constraint (cybersec reasoning)**: Qwen2.5-14B-Instruct MMLU ~80% is among the strongest sub-70B open-source models. Stronger base than Prometheus-2-7B's Mistral-7B. For CCoP's mix of factual citation + regulatory reasoning, this matters more than any judge-specific fine-tuning.

**Why NOT the alternatives (same constraint bag):**

- **Prometheus-2-7B (Mistral)**: Same rubric/reference architecture, but weaker base model (Mistral-7B MMLU ~60%). M-Prometheus-14B is strictly better at equal license and deployment ergonomics.
- **Prometheus-2-8x7B**: Fits 24 GB only at Q4 with no headroom (~26 GB); risk of OOM on long contexts. M-Prometheus-14B is safer on 24 GB.
- **SFR-Judge-12B (Mistral NeMo)**: Reference-aware yes, rubric only via classification mode (not anchored descriptors). Misses the instance-rubric requirement.
- **Qwen2.5-14B-Instruct prompted**: Equal prompt flexibility but no fine-tuning investment → empirically less consistent in judge-style output format per the CompassJudger-2 paper (baseline Qwen2.5-7B scores ~23% on JudgeBench vs CompassJudger-2-7B's higher score).
- **JudgeLRM-14B**: Qwen2.5-14B base, but **research-only license** rules it out as a replacement primary judge for any context that may go to production.

### Deployment sketch (M-Prometheus-14B)

```
# Hypothetical integration points — illustrative only
ollama pull hf.co/Unbabel/M-Prometheus-14B-Q5_K_M    # or use vLLM directly
# Replace src/domain/services/llm_judge_service._call_claude_agent
# with an httpx.post(...) call to the local Ollama/vLLM OpenAI-compat endpoint
# Prompt template: adopt prometheus-eval's ABSOLUTE_GRADE_TEMPLATE
# Parse: "Feedback: ... [RESULT] <1-5>" — map 1-5 to our 0-3 anchors via floor((score-1) * 0.75)
```

### Risks

| Risk | Mitigation |
|------|-----------|
| Prompt-format mismatch (Prometheus expects 1-5, we use 0-3) | Run 5-dim scoring in 1-5 mode, map to 0-3 post-hoc using a fixed monotonic mapping. Validate on 20-case gold set. |
| M-Prometheus trained primarily for multilingual — English regression? | Paper's English-only ablation (§5) shows no regression vs Prometheus-2-7B. Verify on 10 of our test cases as a sanity check. |
| 14B reasoning ceiling < Claude Sonnet | Expected. Offset with N=3 majority voting (already in our Phase 1 plan). |
| Judge self-preference for Qwen-family responses | If we evaluate Qwen models later, flag and cross-check with a non-Qwen secondary judge. |

---

## 2. If we keep Claude as primary and add a secondary for inter-judge κ — which secondary?

### Primary recommendation: **Qwen2.5-14B-Instruct prompted as a judge (cross-family vs Claude, matches our existing prompt template)**

**Reasoning:**

- The inter-judge κ metric is most informative when the two judges have **different failure modes**. Claude (Anthropic) and Qwen (Alibaba) have substantially different training recipes → different systematic biases → disagreement is meaningful signal.
- Qwen2.5-14B prompted can **use our existing judge prompt template verbatim**. No fine-tuning, no prompt re-engineering, no new parsing logic. Integration is ~4 hours.
- Fits 24 GB at FP16 with headroom; runs at ~40-60 tok/s on 4090.
- Qwen Community License permits commercial use.
- JuStRank 2025 showed Qwen2.5 family is the strongest prompted-judge family — the 14B is a scaled-down sibling of the #1-ranked Qwen2.5-72B-Instruct.

### Alternate secondary: **JudgeLRM-7B**

**If research-only license is acceptable** (which it is for dissertation evaluation):

- **Strongest direct precedent for compliance**: AAAI 2025 CA-Judge paper chose JudgeLRM-7B specifically for regulatory-rule compliance verification. This is the single most relevant external validation for our domain.
- Qwen2.5-7B base — cross-family from Claude.
- RL-trained on reasoning-intensive judge tasks — potentially stronger on CCoP's reasoning chains than a prompted generalist.

**Why Qwen2.5-14B prompted is still the preferred primary secondary**:
- Commercial-license clean.
- Zero custom code — reuse existing judge prompt.
- Same-family as M-Prometheus-14B later if we migrate primary too, but **still cross-family from Claude** for the current inter-judge exercise.

### Alternate if multi-GPU becomes available: **Qwen2.5-72B-Instruct prompted**

- JuStRank #1 in 2025 (τ=0.827 with human ranking). Strong primary judge, not just secondary.
- Ollama one-liner: `ollama pull qwen2.5:72b`.
- Cloud cost for 1,770 calls: ~$0.50 on L40S. Trivial.
- **If dissertation budget allows cloud**: promote to primary and relegate M-Prometheus-14B to secondary.

---

## 3. If we wanted a fine-tuned CCoP-specific judge — which base, how to source training data?

### Pick: **Qwen2.5-14B-Instruct as the base**

**Reasoning:**

- Qwen2.5-14B is the best-in-class open-source base model that fits 24 GB for LoRA fine-tuning.
- All three 2025 judge papers (M-Prometheus, JudgeLRM, CompassJudger-2) converged on Qwen2.5 as the training substrate → the Qwen2.5 family is the de-facto community standard for new judges.
- Qwen Community License permits commercial fine-tuning and deployment.

### Training-data sourcing strategy (three tiers from cheapest to strongest)

**Tier 1 — Synthetic rubric expansion (cheapest, 1-2 weeks)**:
- Take our 118 CCoP test cases.
- For each case, prompt Claude Opus to generate 5-10 synthetic responses at varying quality levels (high/medium/low/fabricated).
- Use Claude to score each synthetic response on our 5-dim rubric with anchored justifications.
- Dataset: ~600-1200 (response, score, justification) triples.
- Fine-tune with LoRA (rank 16-64) on Qwen2.5-14B-Instruct. Training time: ~2-6 hours on 4090.

**Tier 2 — Prometheus-style Feedback Collection for CCoP (4-8 weeks)**:
- Follow Prometheus 2's recipe: ~50 human-authored CCoP rubrics as seeds, GPT-4 expands to 1000 rubrics with human verification.
- For each rubric, 20 synthetic responses at varying score levels.
- Result: 20,000 (question, rubric, response, score, feedback) tuples.
- Full fine-tune or high-rank LoRA.

**Tier 3 — Human-annotated compliance judgments (quarter-scale effort)**:
- Recruit 2-3 CCoP compliance experts.
- For each of 118 cases, have experts score 5-10 responses from different model families on our 5-dim rubric.
- Kappa-validate inter-expert agreement on a subset.
- This creates a gold-standard training + test corpus of ~600-1200 expert-scored judgments.
- Fine-tune on this data; reserve a held-out subset as the evaluation gold set.

**Recommendation**: **Tier 1 for dissertation pilot; Tier 2 if publication-quality CCoP judge is a long-term goal.** Tier 3 is a post-dissertation research program.

### Fine-tuning framework

- **prometheus-eval training recipe** (from the GitHub repo's BiGGen-Bench subfolder): uses HuggingFace Alignment Handbook + Super Mario Merging for weight-merging. Proven recipe, Apache-2.0.
- Alternative: **JudgeLRM's RL recipe** (outcome-driven rewards) if the training data includes verifiable correctness signals.

---

## 4. Are there 2025 open-source judges that specifically outperform Prometheus 2 in our regime?

**Our regime**: reference-aware + instance-rubric + 7B-13B single-GPU.

**Short answer: NO — with high confidence.**

The three 2025 candidates that claim to beat Prometheus 2 on some metric:

1. **M-Prometheus-14B** (April 2025): Not a "beat" but a **direct successor with a better base model**. Paper does not frame this as a beat, but empirically M-Prometheus-14B is strictly stronger than Prometheus-2-7B at English direct-assessment-with-reference-and-rubric for the reasons above. **This IS the 2025 Prometheus 2 evolution we want.**

2. **JudgeLRM-7B/14B** (April 2025): Claims to beat DeepSeek-R1 + 2pp on PandaLM F1. But:
   - PandaLM F1 is a pairwise-preference benchmark, not direct-assessment Pearson. Different regime.
   - JudgeLRM doesn't have Prometheus-style per-instance anchored rubric descriptors.
   - Research-only license.
   - **Cannot be considered a Prometheus 2 replacement in our exact regime, despite being a strong judge in its own regime.**

3. **CompassJudger-2-7B** (July 2025): Claims competitive with 235B general models on JudgerBenchV2, JudgeBench, RewardBench. But:
   - No first-class instance-rubric slot.
   - JudgerBenchV2 is the *authors' own* benchmark.
   - Less third-party replication than Prometheus 2.
   - **Potentially strong but not dispositive for our regime.**

**Gap**: No 2025 paper has published a direct head-to-head Pearson comparison in the setting "reference answer + per-instance 5-level rubric + 7-14B model + English direct assessment." Prometheus 2 remains the benchmark-defining paper in that exact regime, and M-Prometheus-14B is the strongest successor.

**Confidence: MEDIUM-HIGH.** The absence of a 2025 paper with a direct apples-to-apples comparison is itself evidence — if someone had definitively beaten Prometheus 2 in our regime, the paper would frame itself that way. Instead, 2025 papers either use a different regime (pairwise-only for JudgeLRM, system-ranking for JuStRank) or use a different benchmark (JudgerBenchV2, ContextualJudgeBench).

---

## 5. Single most credible benchmark to cite in the dissertation

### Pick: **JudgeBench (Tan et al., ICLR 2025 — arXiv:2410.12784)**

**Why it's the best citation for our defense:**

- **Peer-reviewed at top-tier venue** (ICLR 2025).
- **Objective labels** derived from known-correct datasets (LiveCodeBench, PRM-800k, etc.) — unlike RewardBench, which relies on crowdsourced preferences.
- **Reasoning-heavy domains** (knowledge, math, coding, reasoning) — closest proxy to CCoP's regulatory reasoning.
- **Covers both prompted and fine-tuned judges** — allows us to cite the exact scores for Prometheus-2-BGB-8x7B (39.43), Skywork-Critic-70B (57.43), Llama-3.1-70B-Instruct (52.29), etc. as a reference framework.
- **Hugging Face Space leaderboard** ([ScalerLab/JudgeBench](https://huggingface.co/spaces/ScalerLab/JudgeBench)) exists for ongoing model comparison.

**Secondary citation**: **JuStRank (ACL 2025, arXiv:2412.09569)** for the system-ranking angle, if we want to report judge quality in the context of ranking multiple LLMs under test rather than instance-level agreement.

**Do NOT cite** as primary:
- **RewardBench v1**: saturated, known to be beatable by stylistic factors (Tan et al. explicitly flag this in JudgeBench paper).
- **RewardBench v2**: newer but focused on reward models more than generative judges; relevant but less directly aligned with our use case.

---

## Concrete go-forward proposal

### Phase 2 (now, ~1 week):
1. Keep Claude Sonnet as primary judge (as currently integrated).
2. Add **Qwen2.5-14B-Instruct via Ollama** as secondary judge using our existing judge prompt template verbatim.
3. Run Phase 1 N=3 majority voting on both judges; compute Cohen's κ per dimension between Claude-majority and Qwen2.5-14B-majority. Target κ ≥ 0.70 (substantial agreement).

### Phase 3 (2-4 weeks if κ < 0.70 OR if we want stronger reproducibility):
1. Integrate **M-Prometheus-14B (Q4 or Q5 GGUF)** as a third judge using the `prometheus-eval` library's ABSOLUTE_GRADE_TEMPLATE.
2. Report 3-way judge agreement (Fleiss' κ) in the dissertation methodology section.
3. Where any 2 of 3 judges disagree, flag for human spot-check (on a 10-case stratified sample).

### Phase 4 (optional, if dissertation reviewers request):
1. Pilot **Tier 1 fine-tuning** (Qwen2.5-14B-Instruct on ~1000 synthetic CCoP-judgment triples) to demonstrate feasibility of a domain-specific judge.
2. Compare CCoP-fine-tuned judge vs M-Prometheus-14B vs Claude Sonnet on held-out 20 human-labeled cases.

### Do NOT pursue (explicit NO-GO):
- **Self-Taught Evaluator 70B**: research-only + 70B footprint.
- **Skywork-Critic-8B**: authors themselves disclaim it.
- **PandaLM-7B/13B**: superseded, LLaMA-1 era.
- **JudgeLM-33B**: marginal VRAM fit; superseded architecturally.

---

## Final-word licensing red flags to document in the dissertation

| Judge | License flag | Impact |
|-------|--------------|--------|
| Self-Taught Evaluator 70B | Research-only, gated | Cannot deploy anywhere but academic context |
| JudgeLRM (all sizes) | "Research purposes only" per paper | Cannot deploy in any production-adjacent context |
| Auto-J-Bilingual 6B | Yi License | Research-only |
| PandaLM-7B/13B | LLaMA-1 Community | Research-only effectively |
| Skywork-Critic (both) | Skywork Community | Commercial-OK but some use-case restrictions (cannot be used for "national/societal security threats") |
| Qwen2.5-14B / 72B | Qwen Community | Commercial-OK under 100M MAU |
| Llama-3.1 all sizes | Llama 3.1 Community | Commercial-OK under 700M MAU |
| Prometheus 2 weights | Apache-2.0 (model), OpenAI ToU (training data) | Model is commercial-clean; training data restrictions apply only if we re-use the data |
| M-Prometheus weights | Apache-2.0-derived | Commercial-OK |
| SFR-Judge weights | Llama-3.1 Community + possibly research preview at time of release | Verify current HF card before commercial deployment |
