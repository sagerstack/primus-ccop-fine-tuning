# MCQ Labeling Session Playbook

Protocol for the B1 κ labeling session. I (Claude) am the orchestrator using `AskUserQuestion`; you (user) provide the labels.

**Do NOT start labeling until**: A1 has shipped AND post-A1 judge has scored the 30 hybrid responses. We need judge scores frozen *before* labeling to preserve blinding.

---

## Pre-session setup (me, ~15 min)

Artifacts I must have ready:
- `00-sample-selection.json` — the 30 cases to label ✓
- `01-scoring-protocol.md` — rubric anchor reference card ✓
- Frozen `pre_a1_snapshot.json` — judge scores (pre-A1) for the 30 hybrid responses, kept hidden
- Frozen `post_a1_snapshot.json` — judge scores (post-A1) for the 30 hybrid responses, kept hidden
- Primus hybrid responses (from task #42) — the actual text user will score
- Clean `human-labels.jsonl` ready to append to

---

## Calibration warm-up (user + me, ~45 min, runs once before the 30)

Purpose: align on rubric interpretation before real labeling starts. Catches anchor drift.

**Cases**: 3 non-sample cases hand-picked to hit easy / medium / hard rubric edges:
- 1 clearly-wrong response (should be unanimous 0s) — tests that we both flag obvious failures
- 1 clearly-right response (should be unanimous 3s) — tests that we don't over-penalize good answers
- 1 borderline response — where the rubric anchors are hardest to apply

**Protocol**:
1. I show you the case (question + expected + response)
2. We BOTH label independently (you via MCQ, I use my own judge run)
3. We compare and discuss any disagreement
4. If the rubric anchor is ambiguous → edit `evaluation-rubrics.md` BEFORE the real session starts (this is allowed; we haven't started measuring yet)

Calibration labels are NOT recorded to `human-labels.jsonl`. They're throwaway.

---

## Main session — per-case flow

For each of the 30 cases, I follow this exact pattern. Target: ~5 min per case × 30 = ~2.5 hrs total.

### Step 1 — Present case (text message, not MCQ)

```
Case N of 30 — {test_id}
Benchmark: {benchmark_id}  |  Domain: {domain}  |  Difficulty: {difficulty}
Clauses: {clause_reference}

=== QUESTION ===
{input.question}

Scenario: sector={input.scenario_sector}, role={input.scenario_role}

=== EXPECTED RESPONSE ===
{ground_truth.expected_response}

=== KEY FACTS ===
{ground_truth.key_facts}

=== MODEL RESPONSE (Primus, hybrid mode) ===
{model_response}
```

No scores shown yet. You have the context needed to label.

### Step 2 — D1 MCQ

Question: `D1 verdict_accuracy — Does the response's verdict match the expected answer?`

Options (per `01-scoring-protocol.md` anchors):
- `(3) Fully matches including all qualifications and secondary conclusions`
- `(2) Correct main verdict; misses one or more secondary aspects`
- `(1) Directionally right but misses key qualifications, conditions, or secondary conclusions`
- `(0) Verdict contradicts the expected answer`

User picks; optionally adds text feedback via "Other".

### Step 3 — D2 MCQ

Question: `D2 justification_quality — Is the reasoning logically sound and internally consistent?`

Options:
- `(3) Tight logical chain; every inference traceable to premises`
- `(2) Sound reasoning chain; minor gaps in inferential links`
- `(1) Reasoning drifts from the actual question; partially off-target`
- `(0) No justification OR internally contradictory`

### Step 4 — D3 MCQ (the weighted one)

Question: `D3 factual_grounding — Are citations real and correctly attributed?`

Options:
- `(3) All citations real, correctly interpreted; every claim traceable`
- `(2) Real citations, mostly correct; one loose attribution or imprecise claim`
- `(1) Real citations but significant misattribution (right clause, wrong claim)`
- `(0) Fabricated citations OR no citations at all`

### Step 5 — D4 MCQ

Question: `D4 scope_appropriateness — Does the response stay on-topic and respect scenario constraints?`

Options:
- `(3) Focused; directly addresses what was asked; no drift, no bloat`
- `(2) Mostly on-topic with minor drift; longer than needed but doesn't mislead`
- `(1) Verbose with tangential sections; core answer diluted`
- `(0) Substantially off-topic OR contradicts stated scenario constraints`

### Step 6 — D5 MCQ

Question: `D5 actionable_way_forward — Are the next steps concrete, specific, and feasible?`

Options:
- `(3) Specific action + correct mechanism + feasibility-aware`
- `(2) Names a specific action or mechanism but lacks detail or feasibility awareness`
- `(1) Vague direction only; no specific mechanism or instrument`
- `(0) No next steps OR steps contradict scenario constraints`
- `(N/A) Not applicable for this benchmark (e.g., pure classification or hallucination-check)`

### Step 7 — Case-level flags (one final MCQ, multiSelect)

Question: `Any issues with this case?`

Options (multiSelect true):
- `Expected response looks wrong or incomplete` — GT defect candidate
- `Rubric anchor was ambiguous` — rubric refinement candidate
- `Case was much harder than its difficulty tier suggests` — sampling/difficulty calibration
- `Model response had a pattern worth flagging` — interesting finding
- `None of the above`

### Step 8 — I append to human-labels.jsonl

One row per (case, dim):

```json
{
  "session": "b1-post-a1",
  "test_id": "B01-007",
  "mode": "hybrid",
  "dim": "verdict_accuracy",
  "score": 2,
  "justification": "Correct that this is non-compliant, but the response misses the waiver path under Section 11(7) that the expected answer covers.",
  "labeled_at": "2026-04-25T..."
}
```

Five rows per case × 30 cases = 150 label rows.

### Step 9 — Progress ping every 5 cases

"Case N/30 complete. D1 mean so far: X.X, D3 mean so far: X.X. Estimated time remaining: Y min."

Lets you track pace; catches if dimension scores are drifting uniformly (signal of fatigue or rubric drift).

---

## Edge cases

### Case where user wants to see the judge's score mid-session

**Don't show.** Explain: anchoring bias. You can see all judge scores after all 30 are labeled. Hard rule.

### Case where user wants to revise a prior label

**Allow, but flag.** Note the revision in the JSONL as `revised: true` with original + new score. Keeps methodology audit trail honest.

### Case where N/A is selected for D5

Store as `score: null` in JSONL (not 0). κ computation skips null entries for that dim. Don't force a score on a dimension that doesn't apply.

### Case where user gets tired mid-session

**Pause.** After any case, user can say "pausing" and I save state. Resume later with "resume case N". No pressure to finish in one sitting — fatigue-driven scoring is worse than paused-then-resumed scoring.

### Case where MCQ options don't fit what user wants to say

Use `Other` free-text. I parse the free-text, map to the closest integer score if possible, note the user's exact words as `justification`. These cases become rubric-refinement signals after the session.

---

## Post-session — what I compute

Once all 30 cases are labeled (150 rows in `human-labels.jsonl`):

1. **Three κ runs** (same human labels, different judge files):
   ```
   python3 kappa_compute.py --human human-labels.jsonl --judge pre_a1_snapshot.json --label pre_a1 --output 20-kappa-pre-a1.md
   python3 kappa_compute.py --human human-labels.jsonl --judge post_a1_snapshot.json --label post_a1 --output 21-kappa-post-a1.md
   python3 kappa_compute.py --human human-labels.jsonl --judge post_enrichment_snapshot.json --label post_enrichment --output 22-kappa-post-enrichment.md
   ```

2. **Disagreement deep-dive**: for each dim where κ < 0.60, pull the specific cases where judge and human disagreed most. Write to `23-disagreement-deep-dive.md`. These drive rubric anchor refinements.

3. **Mode-discrimination check**: run judge on llm-only responses. Compare mean(judge_hybrid) vs mean(judge_llm-only). Expect hybrid > llm-only systematically (your earlier finding).

4. **Calibration correction fit** (optional): if judge has systematic bias (e.g., judge_mean − human_mean is consistently positive on D3), fit a linear correction and apply to all 435 judge scores in future evals.

---

## Commit after session

```
git add research/human-kappa-seed/
git commit -m "feat(b1): human-labeled κ seed session N=30; κ_post_A1=X.XX"
```

No PR needed — this is dissertation research data, not shipped code.

---

## If something goes wrong

- **Judge snapshots not frozen yet** → stop, don't start labeling. Go back to task #42/#48.
- **User unsure about a case** → allow text feedback on "Other"; don't force a score.
- **Rubric anchor seems wrong mid-session** → finish the session on the existing anchors (consistency > perfection for THIS measurement). Log the anchor concern. Fix the rubric for the NEXT measurement cycle.
- **Pace is slower than expected** → that's fine. Target is quality, not throughput. 30 carefully-labeled cases beat 50 rushed ones.
