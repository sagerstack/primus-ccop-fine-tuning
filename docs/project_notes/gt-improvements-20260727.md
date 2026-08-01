# Ground-Truth Improvements — 2026-07-27

Running log of ground-truth (GT) gold-set improvements surfaced during Phase 12
corrective-retrieval work. These are **data / gold-set** issues (as opposed to
code bugs, which are fixed in place and noted in `bugs.md`).

---

## GT-1: Gold clause sets are narrower than the set of legitimately-citable clauses

**Date:** 2026-07-27
**Surfaced by:** D6 (citation_correctness) investigation on B07-006 (graphont-agentic corrective run).
**Severity:** Medium — systematically penalizes thorough, correct answers on multi-clause benchmarks.

### What happened
D6 is computed as **precision** of the model's in-corpus citations against the
GT gold set `G` (built from `metadata.clause_reference` + `ground_truth.key_facts[].source`):

```
precision = |C ∩ G| / |C|      # C = model's in-corpus citations
```

On **B07-006** (gap identification — shared admin credentials scenario), the model
produced a strong answer citing four real, in-corpus, decision-relevant clauses:

- `5.2.1(c)` — shared user accounts not created unless necessary  ✅ (the exact obligation)
- `5.2.1(d)` — monitor account activity for anomalies             ✅ (relevant)
- `6.1.1(a)` — log all access to the CII                          ✅ (relevant)
- `11.12`    — log privileged-account activity                   ✅ (relevant)

But the gold set `G` for B07-006 is narrow (`clause_reference = ["5.2.1"]` plus a
few key_facts sources). Three of the four correct, relevant citations are **not in
`G`**, so precision drops and D6 is penalized — even though a good gap-identification
answer *should* cite multiple relevant clauses. **Thoroughness is punished.**

### Why this is a GT (data) issue, not just a metric issue
For multi-gap / gap-identification benchmarks (B07, and likely B08/B12/B14/B23),
the gold set should enumerate the **full set of legitimately-citable clauses** for
the scenario — not just the single primary anchor. When the GT under-lists the
relevant clauses, any precision-based citation metric will unfairly punish correct
breadth.

### Proposed improvement
- Review the gold sets (`clause_reference` + `key_facts` sources) for the
  gap-identification and multi-clause benchmarks and **expand them to include all
  clauses a correct answer may legitimately cite** for each scenario.
- Alternatively/additionally, distinguish **required** gold clauses (must cite) from
  **acceptable-additional** clauses (citing them should not reduce precision).
  This is a schema decision — see the related metric-design question below.

### Related (metric side, tracked separately — not this doc)
- D6 precision-vs-narrow-GT design and parent↔subclause granularity are metric-design
  questions for an ADR. The multi-clause **parser under-count** bug (GT sources like
  `"CCoP 2.0 5.2.1(c), 5.2.1(d)"` dropping the 2nd clause) was a code bug and is
  **fixed** (see `_extract_clause_ids` in `llm_judge_service.py` + D6 tests).

### Evidence
- Run: `results/evaluations/2026-07/eval-run-graphont-agentic-test-B07-006-20260727-1009-*.json`
- Record: `ground-truth/test-suite/audit-20260629-1245/b07_gap_identification_quality.jsonl` (B07-006)
