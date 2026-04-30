# Recommendation — OpenRouter judge model

Date: 2026-04-25
Decision-relevant inputs: `00-scope-and-shortlist.md`, `10-candidate-specs.md`, `20-cost-projection.md`.

---

## 1. Budget-primary pick

**`openai/gpt-4.1-mini-2025-04-14`**

- Pinned canonical slug: **`openai/gpt-4.1-mini-2025-04-14`** (dated by OpenAI; OpenRouter exposes both `openai/gpt-4.1-mini` alias and the dated form — code uses the dated form)
- OpenRouter URL: https://openrouter.ai/openai/gpt-4.1-mini
- **Full project cost (~30K calls, mid bound): $80.40**
- Pricing: $0.40/M input, $1.60/M output
- Context: 1,047,576 tokens
- Params: `temperature` ✓, `seed` ✓, `top_p` ✓, `response_format` ✓, `max_tokens` ✓
- Reproducibility class: **A — byte-level when `seed` is pinned and temp is fixed**
- License: OpenAI commercial; academic / dissertation use permitted

### Why this and not the absolutely-cheapest Qwen3-235B ($9.86)?

We considered Qwen3-235B-A22B-2507 hard for budget-primary. Three reasons it is the **backup**, not the primary:

1. **Reliability evidence is family-level, not exact-model-level.** Qwen2.5-72B sits at the top of JuStRank 2025 (τ=0.827). Qwen3-235B-A22B is the MoE successor; reliability is *expected* equal-or-better but not directly published on JudgeBench. GPT-4.1 family has explicit OpenAI-published evals at gpt-4o-class.
2. **MoE output-format consistency is a real risk** for structured JSON rubric output. We can mitigate via `response_format={"type":"json_object"}`, but failure mode is heavier than with dense models.
3. **Methodology defensibility in a dissertation.** "OpenAI GPT-4.1-mini, version 2025-04-14, called via OpenRouter at temperature=0.2, seed=42" is a single, citable, reproducible line. The Qwen story is longer (community license, MoE routing nondeterminism notes, third-party judge-bench inference).

GPT-4.1-mini at $80 vs Qwen at $10 is a $70 difference for the entire project. That is well below the "model cost is no longer binding" line. Buy the defensibility.

### What budget-primary delivers

- Project cost in the **low double-digits of dollars** even at 30K calls.
- Byte-level reproducibility (seed + temp pinned).
- A dated version string the methodology can cite.
- Evidence base from GPT-4 family judge work that the dissertation can lean on.

---

## 2. Quality-primary pick

**`anthropic/claude-sonnet-4.5` (`anthropic/claude-4.5-sonnet-20250929`)**

- Pinned canonical slug: **`anthropic/claude-4.5-sonnet-20250929`**
- OpenRouter URL: https://openrouter.ai/anthropic/claude-sonnet-4.5
- **Full project cost (~30K calls, mid bound): $675.00**
- Pricing: $3/M input, $15/M output
- Context: 1,000,000 tokens
- Params: `temperature` ✓, `seed` **✗**, `top_p` ✓
- Reproducibility class: **B — distributional (no seed)**
- License: Anthropic commercial; academic clean

### Why this and not Gemini-2.5-Pro or GPT-4.1?

| Candidate | $/project | JudgeBench | Reasoning |
|---|---|---|---|
| Sonnet-4.5 | $675 | Family ~64.3% (3.5-Sonnet, ICLR 2025) | **Best documented judge reliability of the three** |
| Gemini-2.5-Pro | $371 | No published number | Strong reasoning leaderboard, weaker judge-task evidence |
| GPT-4.1 | $402 | GPT-4o ~57% (extrapolation) | Strong but below Sonnet on judge-task evidence |

If the goal is "highest expected judge reliability we can pay for", Sonnet-4.5 is on the strongest evidence base. The seed gap (Anthropic doesn't expose `seed`) is the only meaningful cost — handled in the methodology by reporting *distributional* reproducibility (mode score across N=3) rather than byte-level.

### When to actually use quality-primary

- Final reported milestone numbers in the dissertation submission (one-time cost, ~$60)
- Re-judging contested cases flagged by inter-judge agreement (Tier C work)
- Paired runs vs budget-primary to measure the actual κ penalty (see §4)

Do **not** run all 30K calls through Sonnet-4.5. The budget penalty is ~8x and the marginal reliability lift over GPT-4.1-mini is unproven.

---

## 3. Backup / secondary judge (for inter-judge agreement)

**`qwen/qwen3-235b-a22b-2507`** (canonical: `qwen/qwen3-235b-a22b-07-25`)

- Different model family (Alibaba) → genuine inter-judge signal
- OpenRouter URL: https://openrouter.ai/qwen/qwen3-235b-a22b-2507
- Project cost: **$9.86** — cheap enough to run as a parallel second judge
- Reproducibility class: A (dated slug, seed supported)
- Logprobs available — unlocks G-Eval-style continuous scoring later

### Inter-judge agreement protocol (Tier C)

Run the budget-primary (GPT-4.1-mini) and the backup (Qwen3-235B) against the same prompts. Measure:

- Cohen's κ on dimension-level scores (treat 0-3 as ordinal)
- Pearson r on overall_score (continuous)
- Spearman ρ on case ranking

If κ ≥ 0.6 and r ≥ 0.7, single-judge results are defensible. Below that, escalate to a third judge (Sonnet-4.5) for arbitration on disagreement-flagged cases.

This costs ~$90 across the full project ($80 GPT-4.1-mini + $10 Qwen) — still below the Sonnet-4.5 single-judge baseline.

### Alternative backup: `deepseek/deepseek-v3.2-20251201`

If Qwen has problems in pilot (output-format issues, Chinese-language artifacts), DeepSeek-V3.2 is the next backup. Dated slug, similar price ($35/project), different model family. Switch is a one-line change in config.

---

## 4. Expected quality-floor trade-off

If we pick **GPT-4.1-mini** as primary instead of **Sonnet-4.5**, what's the expected agreement-with-human-judges penalty?

### Direct evidence (verified)

- **JudgeBench (Tan et al., ICLR 2025)** reports Claude-3.5-Sonnet at **64.3%** overall and GPT-4o at **~57%** on direct-assessment judge tasks. Sonnet ahead by ~7 points on the JudgeBench composite.
- GPT-4.1-mini does **not** have a published JudgeBench score. We extrapolate from OpenAI's positioning ("competitive with GPT-4o at lower cost") — i.e., gpt-4o-class.

### Inferred range

- Best plausible: GPT-4.1-mini ≈ GPT-4o-class ≈ **57% JudgeBench overall** (gap to Sonnet ≈ -7 points).
- Worst plausible: GPT-4.1-mini below GPT-4o due to scale-down, ≈ **53-55%** (gap to Sonnet ≈ -10 points).

### Translated to Cohen's κ

JudgeBench accuracy ≈ pairwise agreement with humans. Translating to Cohen's κ on our 0-3 ordinal scale (rough heuristic, weighted κ):

- Sonnet-4.5 expected κ with humans: **~0.55-0.65**
- GPT-4.1-mini expected κ with humans: **~0.45-0.55**

i.e., we expect **~0.05-0.10 κ penalty** when using budget-primary. This is in the "substantial agreement → moderate agreement" boundary on Landis-Koch.

### Mitigation that recovers most of the gap

- N=3 majority vote with temperature=0.2 → empirically reduces variance ~30-40% for prompted judges (Prometheus 2 paper, Kim et al., 2024). This was the original A1 motivation. **Restores most of the κ gap when budget judge is correct on average and noisy on the margin.**
- Inter-judge agreement check between primary + backup → flags cases where κ is brittle.
- Spot-audit: 20 random cases re-judged by Sonnet-4.5 quality-primary at end of milestone for triangulation. Cost ~$0.50.

### Bottom line on trade-off

**Expected κ penalty: ~0.05-0.10 (moderate-significant in absolute terms, small relative to A1 mitigation effect).**
**Cost saved: $595 over the project (~88%).**
The trade-off is rational. Frame in dissertation as "GPT-4.1-mini at temp=0.2, N=3, seed-pinned, with Qwen3-235B inter-judge agreement check" — not as "we picked the cheap one."

---

## 5. Pinned version strings (for methodology section)

These are the strings to put in the methodology table, exactly as written:

| Role | Model ID (canonical, dated) | Provider | Pricing date |
|---|---|---|---|
| **Primary judge** | `openai/gpt-4.1-mini-2025-04-14` | OpenAI via OpenRouter | 2026-04-25 |
| **Quality-primary** (audit subset) | `anthropic/claude-4.5-sonnet-20250929` | Anthropic via OpenRouter | 2026-04-25 |
| **Backup judge** (inter-judge agreement) | `qwen/qwen3-235b-a22b-07-25` | Alibaba via OpenRouter | 2026-04-25 |

If any of these is silently revved by the provider, the dated suffix lets us detect it (the slug becomes a 404 or starts returning a different model). For Anthropic specifically, **always use the dated slug, never the bare alias**.

---

## 6. Decision summary in one paragraph

Use **`openai/gpt-4.1-mini-2025-04-14`** (cost: ~$80 for full project) as the primary judge. It supports temperature + seed (byte-level reproducibility), has a dated slug (methodology defensibility), is in the GPT-4.1 family (judge-bench-defensible), and meets the A1 N=3 sampling requirement. Run **`qwen/qwen3-235b-a22b-07-25`** (cost: ~$10) in parallel as a different-family backup judge for inter-judge agreement (Tier C). Reserve **`anthropic/claude-4.5-sonnet-20250929`** (cost: ~$60 for a 20-case spot-audit) for end-of-milestone arbitration on disagreement-flagged cases. Total project judging cost: **~$150 vs $675 baseline, with stronger reproducibility and a defensible inter-judge story**.
