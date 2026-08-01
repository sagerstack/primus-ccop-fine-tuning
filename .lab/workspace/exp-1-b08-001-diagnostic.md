# Experiment 1 — B08-001 Full Diagnostic Evidence

## Question
"Given the following compliance gaps in a banking CII environment:
1. Shared admin accounts (likelihood: high, impact: high, effort: low)
2. Missing security awareness training records (likelihood: medium, impact: low, effort: medium)
3. Outdated asset inventory (likelihood: medium, impact: medium, effort: high)

Constraints: None

Which gap should be prioritized for remediation first, and what should the prioritization sequence be?"

## Expected
- Priority 1: Shared admin accounts (high likelihood × high impact, low effort)
- Reasoning: risk-based prioritization framework (CCoP 3.2.2(b)/(c))

## Top 30 hybrid-retrieved chunks (BGE dense + BM25 sparse RRF)

```
rank   score  citation_id                              snippet
   1  0.5233  Risk Assessment Guide::Task A: Determi…  Determine and Prioritise Risk          ← MOST RELEVANT
   2  0.5000  CCoP 2.0::5.14.2                         shall remediate all cybersecurity vuln
   3  0.3656  CCoP Response to Feedback::11            ACCESS CONTROL MANAGEMENT              ← used in eval
   4  0.3333  CCoP 2.0::2.1.2                          audit finding remediation plan
   5  0.2700  CCoP Response to Feedback::3             link/reference
   6  0.2667  Risk Assessment Guide::1.2 Common Probl  Common Problems in Risk Assessment     ← relevant
   7  0.2500  Risk Assessment Guide::Task A: Likeliho  Determine Likelihood
   8  0.2000  CCoP 2.0::1.2.1::table::5                glossary
   9  0.1875  CCoP 2.0::4.1.1                          asset management
  10  0.1773  CCoP 2.0::7.1.4                          incident processes
  …
  18  0.1181  CCoP Response to Feedback::6             POLICIES, STANDARDS, GUIDELINES         ← used in eval
  20  0.1111  CCoP 2.0::5.14.3                         vulnerability assessment frequency      ← used in eval
  …
  30  0.0683  CCoP 2.0::3.2.2                          risk assessment methodology steps      ← TARGET (b)/(c)
```

## What the eval actually used
- Reranker chose ranks #3, #18, #20 from the above list
- Despite #1 (Risk Assessment Guide Task A on prioritization) being the most semantically relevant

## Cross-encoder model: cross-encoder/ms-marco-MiniLM-L12-v2
Trained on web QA. Not domain-tuned for regulatory text. Likely the root cause.

## Hybrid model response (full text)
[See full output captured in shell history — 35+ lines, invented RPN formulas with weights 0.8/0.9/0.2, miscited retrieved sources, no clause-ID citations]

## Saved similarity scores
All `score=0.000` in contexts sidecar. Suggests reranker overwrites with 0, or score field gets clobbered in serialization. Separate cosmetic bug.

## Diagnosis summary

| Layer | State | Verdict |
|-------|-------|---------|
| Hybrid retrieval (BGE+BM25) | Top-1 result is genuinely relevant | OK |
| Cross-encoder rerank | Demotes #1 #2 #6, promotes #3 #18 #20 | **BROKEN for regulatory** |
| top_k=20 | Excludes target chunk (rank 30) | Too small for some queries |
| top_n=3 final | Reasonable count | Adequate IF reranker ordering is right |
| Model attention to context | Invents RPN formulas; name-drops citations | **HONESTY ISSUE** |
| Judge | Correctly penalised D3=0 | Working as intended |

## Recommended Experiment 2
Bypass the cross-encoder. Use top-N straight from hybrid RRF.

Expected effect: B08-001 should now see {Risk Assessment Guide Task A, CCoP 5.14.2, CCoP Response 11} as its top 3 — these are at least *related* to risk prioritization, even if 3.2.2 is still missing.

For 3.2.2 specifically, also need top_k≥30 OR query rewriting. But Experiment 2 first, layered increments.
