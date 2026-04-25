# Scoring Protocol — Reference Card for B1 Labeling Session

Use this card during the labeling session to score each dimension on the **0-3 anchored scale**. These are the EXACT anchors the LLM judge uses — apples-to-apples comparison requires you and the judge to apply the same rubric.

---

## The 5 dimensions at a glance

| Dim | Name | Weight | Measures |
|-----|------|--------|----------|
| D1 | verdict_accuracy | 0.5 | Is the final verdict / conclusion correct? |
| D2 | justification_quality | 0.5 | Is the reasoning logically sound and on-topic? |
| D3 | factual_grounding | **1.0** (2×) | Are citations real + correctly attributed? No fabrications? |
| D4 | scope_appropriateness | 0.5 | Does the response stay focused and respect stated constraints? |
| D5 | actionable_way_forward | 0.5 | Are the next steps concrete, feasible, and specific? |

D3 is weighted double — it's the hallucination penalty.

---

## D1 — verdict_accuracy

**Ask yourself**: Does the response's final verdict/conclusion match the expected answer?

| Score | Anchor |
|-------|--------|
| **0** | Verdict contradicts the expected answer (says "compliant" when expected is "non-compliant", etc.) |
| **1** | Directionally right but misses key qualifications, conditions, or secondary conclusions |
| **2** | Correct main verdict; misses one or more secondary aspects (e.g., forgets to note waiver applies) |
| **3** | Fully matches including all qualifications and secondary conclusions |

---

## D2 — justification_quality

**Ask yourself**: Is the reasoning logically sound and internally consistent? Does each inference follow from stated premises?

| Score | Anchor |
|-------|--------|
| **0** | No justification OR internally contradictory reasoning |
| **1** | Reasoning drifts from the actual question; partially off-target |
| **2** | Sound reasoning chain addressing the core issue; minor gaps in inferential links |
| **3** | Tight logical chain; every inference traceable to premises |

---

## D3 — factual_grounding (weight 2×)

**Ask yourself**: Are all factual claims — citations, regulatory assertions — verifiable against the ground truth? Any fabrications?

**Two-step check:**

1. **Are the cited clauses REAL?** Check the `clause_reference` ground truth + your own CCoP knowledge. If the response cites a non-existent clause → **automatic 0**.
2. **Are REAL citations CORRECTLY attributed?** Does the response's description of the clause match what the clause actually says?

| Score | Anchor |
|-------|--------|
| **0** | Fabricated citations (clauses that don't exist) OR no citations anywhere |
| **1** | Real citations but significant misattribution (cites correct clause for wrong claim) |
| **2** | Real citations, mostly correct interpretation; one loose attribution or imprecise claim |
| **3** | All citations real, correctly interpreted; every claim traceable |

**Watch for hallucination patterns**: clause IDs with wrong section numbers, invented sub-letters (e.g., `5.3.1(z)`), regulatory body confusion (CSA ≠ MAS ≠ MOH).

---

## D4 — scope_appropriateness

**Ask yourself**: Does the response stay on-topic, without drifting or contradicting scenario constraints?

Look at `input.scenario_sector`, `input.scenario_role`, and any stated constraints in the question. Does the response respect them?

| Score | Anchor |
|-------|--------|
| **0** | Substantially off-topic OR proposes actions that contradict stated scenario constraints |
| **1** | Verbose with tangential sections; core answer diluted |
| **2** | Mostly on-topic with minor drift; longer than needed but doesn't mislead |
| **3** | Focused response directly addressing what was asked; no drift, no bloat |

---

## D5 — actionable_way_forward

**Ask yourself**: Does the response translate analysis into concrete, feasible next steps?

| Score | Anchor |
|-------|--------|
| **0** | No next steps OR suggested steps contradict scenario constraints (infeasible given stated facts) |
| **1** | Vague direction only; no specific mechanism, instrument, or action named |
| **2** | Names a specific action or mechanism but lacks detail, specificity, or feasibility awareness |
| **3** | Specific action + correct mechanism/instrument + feasibility-aware given stated constraints |

**Note**: Not all benchmarks require a way-forward. For benchmarks that are pure classification (e.g., B02) or hallucination-check (B21), use **N/A** — don't force a score.

---

## General labeling rules

1. **Blind to judge scores** — do NOT look at the judge's scores before labeling. Anchoring bias inflates κ dishonestly.
2. **Score from ground truth only** — don't use your own CCoP expertise to fill gaps. If the response claims something not in GT and not traceable, it's ungrounded (regardless of whether it's *actually* true).
3. **Score dimensions independently** — a response can be 0 on D3 (fabricated) but 3 on D2 (well-reasoned given the fabrication). Dimensions measure different things.
4. **Provide a 1-2 sentence justification** — this is the most valuable output. The justification is what reveals whether you and the judge disagree on *interpretation* vs. *rubric ambiguity* vs. *actual quality*.
5. **"Other" / free-text available** — if a case doesn't fit the 4-option MCQ cleanly, use "Other" to explain. These cases become rubric-refinement candidates.
6. **Flag GT defects** — if the expected answer itself looks wrong, call it out. These findings become dissertation appendix material.

---

## What the judge sees (so you can match)

The judge receives:
- The question
- The model's response
- The expected response
- Ground-truth key_facts (tier-tagged)
- Clause references + (when available) verbatim clause text
- Forbidden claims + hallucination patterns

You'll see the same artifacts in the labeling UI. Score using the same inputs the judge uses.
