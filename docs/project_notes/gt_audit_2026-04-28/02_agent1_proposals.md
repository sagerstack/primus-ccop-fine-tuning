# GT Audit Proposals — Agent 1

Triage of the 90 flagged test cases from `01_scanner_findings.md`. This document contains
proposals only; no GT files are modified by this agent.

## Summary

| Bucket | Count |
|---|---:|
| REAL_INCONSISTENCY | 33 |
| FALSE_POSITIVE | 33 |
| AMBIGUOUS | 24 |
| **Total** | **90** |

**Total individual edit proposals across REAL_INCONSISTENCY cases:** **98**
(all are `key_facts[*].source` updates; no `clause_reference` rewrites — every fix preserves
the existing canonical clause anchors).

Per-benchmark breakdown:

| Benchmark | Flagged | REAL | FALSE | AMBIG |
|---|---:|---:|---:|---:|
| B01 | 2 | 1 | 1 | 0 |
| B03 | 3 | 0 | 3 | 0 |
| B04 | 2 | 0 | 2 | 0 |
| B05 | 2 | 2 | 0 | 0 |
| B06 | 2 | 2 | 0 | 0 |
| B07 | 4 | 4 | 0 | 0 |
| B09 | 1 | 0 | 1 | 0 |
| B12 | 2 | 2 | 0 | 0 |
| B13 | 1 | 1 | 0 | 0 |
| B18 | 25 | 1 | 0 | 24 |
| B21 | 2 | 0 | 2 | 0 |
| B22 | 20 | 20 | 0 | 0 |
| B24 | 24 | 0 | 24 | 0 |
| **Total** | **90** | **33** | **33** | **24** |

---

## Domain priors used for triage

A quick anchor of CCoP 2.0 structure I relied on (verified by sampling JSONL records and the
`agent-team-2026-04-26` correction notes already embedded in B24-003):

- **§1** — Cybersecurity Governance. **§1.6 = Waiver** (the canonical CCoP waiver clause).
- **§3** — Identification (asset inventory in §3.2.2; risk assessment in §3.2; supply chain in §3.8).
- **§5 / §6** — Protection (incl. MFA, access control 5.3.1, network segmentation 6.x).
- **§7** — Detection. §7.1.1 holds the granular incident-handling subclauses (a..i).
- **§8** — Response & Recovery. §8.3 = reporting timelines (2 h serious / 24 h substantial); §8.6 forensic; §8.7 root-cause.
- **§9** — Resilience / BCP.
- **§10** — OT security.
- **CCoP 2.0 has no Section 11.** "Section 11" universally refers to the **Cybersecurity Act 2018**
  (§11(7) is the statutory waiver basis). Strings like `"CCoP 2.0 Section 11"` in `key_facts.source`
  are confirmed errors.

Cross-document references that the user said to leave alone:
- `"Cybersecurity Act 2018 Section 11"` / `"§11(7)"`
- `"RESPONSE-TO-FEEDBACK Q…"`
- `"IM8 framework"`, generic regulator names, and any non-clause-shaped string.

---

# 1. REAL_INCONSISTENCY — proposed edits

## B01

### B01-001 (b01_ccop_applicability_scope.jsonl)
- **Issue:** clause_reference is `['1.2.1', '1.4.1']` (CCoP §1.2 Scope / §1.4 Applicability).
  expected_response talks about the *digital boundary* (a §1.2 concept). But three of the four
  `key_facts.source` strings cite `"CCoP 2.0 Section 2"`, which in this corpus is a different
  topic (and conflicts with the §1 anchor of clause_reference). The "Cybersecurity Act Section 11"
  and "RESPONSE-TO-FEEDBACK Q2.2-2.3" parts of the source strings are valid cross-doc refs and
  must stay.
- **Decision:** key_facts.source cites of `"CCoP 2.0 Section 2"` are the outlier. clause_reference
  and expected_response agree on §1.2 / digital boundary scope.
- **Proposed edits:**
  - key_facts[0].source: `"CCoP 2.0 Section 2, Cybersecurity Act Section 11"` → `"CCoP 2.0 Section 1.2, Cybersecurity Act Section 11"`
  - key_facts[1].source: `"CCoP 2.0 Scope section, RESPONSE-TO-FEEDBACK Q2.2-2.3"` → `"CCoP 2.0 Section 1.2, RESPONSE-TO-FEEDBACK Q2.2-2.3"` *(makes "Scope section" explicit as §1.2 to match clause_reference)*
  - key_facts[3].source: `"CCoP 2.0 Section 2"` → `"CCoP 2.0 Section 1.2"`
- **Rationale:** The question is about which systems on a shared enterprise network fall inside CCoP scope. CCoP §1.2 is "Scope" / digital boundary, which clause_reference (§1.2.1) correctly anchors. "Section 2" appears to be a copy-paste error.

## B05

### B05-013 (b05_control_comprehension.jsonl)
- **Issue:** All three `key_facts[*].source` strings say `"CCoP 2.0 4.3"`, but clause_reference is
  `['1.6.1', '1.6.2', '1.6.3', '10.2.7']` and expected_response opens with
  *"According to CCoP 2.0 Section 1.6 (Waiver)…"*.
- **Decision:** clause_reference and expected_response agree on §1.6 (Waiver). key_facts.source is the outlier.
- **Proposed edits:**
  - key_facts[0].source: `"CCoP 2.0 4.3"` → `"CCoP 2.0 1.6.1"`
  - key_facts[1].source: `"CCoP 2.0 4.3"` → `"CCoP 2.0 1.6.2"`
  - key_facts[2].source: `"CCoP 2.0 4.3"` → `"CCoP 2.0 1.6.3"`
- **Rationale:** The question asks about legacy-system exemptions; CCoP §1.6 is the waiver clause. §4.3 is unrelated and is almost certainly a generator artifact.

### B05-015 (b05_control_comprehension.jsonl)
- **Issue:** All three `key_facts[*].source` say `"CCoP 2.0 9.3.1"`, but clause_reference is
  `['3.8.1', '3.8.2', '3.8.3']` and expected_response opens with *"According to CCoP 2.0 Section 3.8…"*.
- **Decision:** clause_reference and expected_response agree on §3.8 (Supply chain). key_facts.source is the outlier.
- **Proposed edits:**
  - key_facts[0].source: `"CCoP 2.0 9.3.1"` → `"CCoP 2.0 3.8.1"`
  - key_facts[1].source: `"CCoP 2.0 9.3.1"` → `"CCoP 2.0 3.8.2"`
  - key_facts[2].source: `"CCoP 2.0 9.3.1"` → `"CCoP 2.0 3.8.3"`
- **Rationale:** Question is about supply-chain control verification; §3.8 is supply-chain in CCoP 2.0. §9.3.1 does not exist as the supply-chain anchor.

## B06

### B06-018 (b06_intent_understanding.jsonl)
- **Issue:** All `key_facts[*].source` say `"CCoP 2.0 7.4.1"`, but clause_reference is `['8.2.1', '8.2.2']`
  and expected_response opens with *"…CCoP 2.0 Section 8.2 regarding business continuity…"*.
- **Decision:** clause_reference and expected_response agree on §8.2 (BCP / resilience). key_facts.source is the outlier.
- **Proposed edits:**
  - key_facts[0].source: `"CCoP 2.0 7.4.1"` → `"CCoP 2.0 8.2.1"`
  - key_facts[1].source: `"CCoP 2.0 7.4.1"` → `"CCoP 2.0 8.2.1"`
  - key_facts[2].source: `"CCoP 2.0 7.4.1"` → `"CCoP 2.0 8.2.2"`
- **Rationale:** Question is on business continuity intent; §8.2 is BCP. §7.4.1 is unrelated.

### B06-019 (b06_intent_understanding.jsonl)
- **Issue:** All `key_facts[*].source` say `"CCoP 2.0 4.2.1"`, but clause_reference is
  `['3.2.1', '3.2.2']` and expected_response opens with *"…CCoP 2.0 Section 3.2 regarding risk
  assessment…"*.
- **Decision:** clause_reference and expected_response agree on §3.2. key_facts.source is the outlier.
- **Proposed edits:**
  - key_facts[0].source: `"CCoP 2.0 4.2.1"` → `"CCoP 2.0 3.2.1"`
  - key_facts[1].source: `"CCoP 2.0 4.2.1"` → `"CCoP 2.0 3.2.1"`
  - key_facts[2].source: `"CCoP 2.0 4.2.1"` → `"CCoP 2.0 3.2.1"`
- **Rationale:** Question is about risk-assessment intent; §3.2 is risk assessment.

## B07

All four B07 cases share the same shape: clause_reference cites §3.2.2(b)/(c) (CCoP §3.2 Identification —
asset inventory), expected_response explicitly says *"CCoP Reference: Section 3.2.2(b) / 3.2.2(c)"*,
yet `key_facts[*].source` all read `"CCoP 2.0 4.2.2"`. §4.2.2 is not the asset-inventory clause.
This is the same boilerplate copy-paste error as B05/B06.

### B07-001 (b07_gap_identification_quality.jsonl)
- **Issue:** key_facts.source `"CCoP 2.0 4.2.2"` vs clause_reference `['3.2.2(b)', '3.2.2(c)']` and expected_response cites §3.2.2.
- **Decision:** key_facts.source is the outlier; §3.2.2 wins.
- **Proposed edits:**
  - key_facts[0].source: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"`
  - key_facts[1].source: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"`
  - key_facts[2].source: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"`
- **Rationale:** Scenario is incomplete CII asset inventory; §3.2.2 is asset-inventory.

### B07-002 (b07_gap_identification_quality.jsonl)
- **Issue:** Same as B07-001.
- **Proposed edits:**
  - key_facts[0].source: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"`
  - key_facts[1].source: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"`
  - key_facts[2].source: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"`
- **Rationale:** Shadow-IT inventory gap is still §3.2.2 territory.

### B07-003 (b07_gap_identification_quality.jsonl)
- **Issue:** Same as B07-001.
- **Proposed edits:**
  - key_facts[0].source: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"`
  - key_facts[1].source: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"`
  - key_facts[2].source: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"`
- **Rationale:** Outdated asset inventory gap; §3.2.2.

### B07-005 (b07_gap_identification_quality.jsonl)
- **Issue:** Same as B07-001.
- **Proposed edits:**
  - key_facts[0].source: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"`
  - key_facts[1].source: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"`
  - key_facts[2].source: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"`
- **Rationale:** Data-flow mapping is part of CII scope/inventory under §3.2.2.

## B12

### B12-016 (b12_audit_perspective_alignment.jsonl)
- **Issue:** All `key_facts[*].source` say `"CCoP 2.0 9.3.1"`. clause_reference is
  `['3.8.1', '3.8.2', '3.8.3', '3.8.4', '3.8.5', '3.2.2', '6.4']` and expected_response cites *"CCoP 2.0 §3.8"*.
  Same §9.3.1↔§3.8 confusion as B05-015.
- **Decision:** §3.8 wins (supply-chain anchor).
- **Proposed edits:**
  - key_facts[0].source: `"CCoP 2.0 9.3.1"` → `"CCoP 2.0 3.8.1"`
  - key_facts[1].source: `"CCoP 2.0 9.3.1"` → `"CCoP 2.0 3.8.1"`
  - key_facts[2].source: `"CCoP 2.0 9.3.1"` → `"CCoP 2.0 3.8.1"`
- **Rationale:** Supply-chain audit perspective belongs to §3.8.

### B12-020 (b12_audit_perspective_alignment.jsonl)
- **Issue:** All `key_facts[*].source` say `"CCoP 2.0 4.2.1"`. clause_reference is `['3.2.1', '3.2.2']`
  and expected_response cites *"CCoP 2.0 §3.2"*. Same §4.2.1↔§3.2 confusion as B06-019.
- **Decision:** §3.2 wins.
- **Proposed edits:**
  - key_facts[0].source: `"CCoP 2.0 4.2.1"` → `"CCoP 2.0 3.2.1"`
  - key_facts[1].source: `"CCoP 2.0 4.2.1"` → `"CCoP 2.0 3.2.1"`
  - key_facts[2].source: `"CCoP 2.0 4.2.1"` → `"CCoP 2.0 3.2.1"`
- **Rationale:** Risk-based audit methodology lives at §3.2.

## B13

### B13-003 (b13_evidence_expectation_awareness.jsonl)
- **Issue:** clause_reference is `['3.2.4', '3.2.2', '3.2.1', '3.2.5']` (CCoP §3.2). expected_response
  header says *"CCoP Domain: Identification (Section 4)"* and key_facts.source all say `"CCoP 2.0 Section 4"`.
  In CCoP 2.0, the "Identification" domain is **§3** (Identification) — calling it "Section 4" is an
  authoring slip.
- **Decision:** clause_reference is the canonical anchor; expected_response and key_facts both got
  the section number wrong. Fix the source strings; expected_response is out of scope per task rules.
- **Proposed edits:**
  - key_facts[0].source: `"CCoP 2.0 Section 4"` → `"CCoP 2.0 Section 3.2"`
  - key_facts[1].source: `"CCoP 2.0 Section 4"` → `"CCoP 2.0 Section 3.2"`
  - key_facts[2].source: `"CCoP 2.0 Section 4"` → `"CCoP 2.0 Section 3.2"`
- **Rationale:** Risk-assessment evidence requirements live in §3.2 (clause_reference is correct).
  Note for human reviewer: the expected_response *also* mislabels the domain as "Section 4"; that
  text remains untouched per scope.

## B18

### B18-001 (b18_responsibility_attribution_sg.jsonl)
- **Issue:** clause_reference is `['3.1.2', '3.1.3', '3.1.1']` (CCoP §3.1 governance roles —
  the canonical home for Board / CIIO / CISO accountability). The first key_fact source is
  `"Cybersecurity Act 2018 Section 11"` (valid cross-doc — keep). The other two cite
  `"CCoP 2.0 Section 1"` for governance/CISO, but §3.1 is the more precise CCoP location for those
  facts.
- **Decision:** Keep the cross-doc Cybersecurity Act ref. Tighten the CCoP §1 references to §3.1.
- **Proposed edits:**
  - key_facts[1].source: `"CCoP 2.0 Section 1"` → `"CCoP 2.0 Section 3.1"`
  - key_facts[2].source: `"CCoP 2.0 Section 1"` → `"CCoP 2.0 Section 3.1"`
- **Rationale:** clause_reference (§3.1.x) and the question (Board/CIIO/CISO responsibilities) both
  point to §3.1 governance roles. "CCoP 2.0 Section 1" is loosely correct (governance is in §1)
  but not aligned with clause_reference granularity.

*B18-002 through B18-025 are AMBIGUOUS — see that section.*

## B22

All 20 B22 cases share an identical defect: `key_facts[*].source = "Cybersecurity Act Section 11(7)
and CCoP 2.0 Section 11"`. The first half is a valid cross-document reference. The second half
("CCoP 2.0 Section 11") **does not exist in CCoP 2.0** — there is no §11. The waiver authority in
CCoP 2.0 is **§1.6**, which all 20 cases correctly cite in `clause_reference = ['1.6.1', '1.6.2',
'1.6.3'(, '1.4.7' for B22-015)]`.

The fix is mechanical and identical for all 20: replace the literal string `"CCoP 2.0 Section 11"`
with `"CCoP 2.0 Section 1.6"` in every key_facts.source. The Cybersecurity Act §11(7) cross-doc
ref is preserved.

For each test_id below, the proposed edit applies to **every** key_fact in that record:

> `key_facts[*].source: "Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"
> → "Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-001 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Waiver questions across all of B22 anchor on CCoP §1.6 (Waiver), which clause_reference correctly cites. CCoP 2.0 has no §11; that string is always a leftover from the Cybersecurity Act §11(7) phrase.

### B22-002 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — log-retention waiver still anchors on CCoP §1.6.

### B22-003 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — staffing-constraint waiver still anchors on CCoP §1.6.

### B22-004 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — OT patching waiver, CCoP §1.6.

### B22-005 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — outsourced CISO waiver, CCoP §1.6.

### B22-006 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — encryption-incompatibility waiver, CCoP §1.6.

### B22-007 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — regulatory-conflict waiver, CCoP §1.6.

### B22-008 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — partial waiver, CCoP §1.6.

### B22-009 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — vendor-non-compliance scenario, CCoP §1.6 waiver framework.

### B22-010 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — waiver renewal, CCoP §1.6.

### B22-011 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — emergency bypass vs waiver, CCoP §1.6.

### B22-012 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — multi-area waiver, CCoP §1.6.

### B22-013 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — OT-protocol waiver, CCoP §1.6.

### B22-014 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — physical-constraint waiver, CCoP §1.6.

### B22-015 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — denial/enforcement, CCoP §1.6 (note: this case's clause_reference also
  includes `1.4.7`; that's a related governance clause and is left untouched).

### B22-016 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — conditional waiver, CCoP §1.6.

### B22-017 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — temporary risk acceptance, CCoP §1.6.

### B22-018 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — conflicting-experts waiver, CCoP §1.6.

### B22-019 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — supply-chain timeline waiver, CCoP §1.6.

### B22-020 (b22_waiver_exception_reasoning.jsonl)
- **Issue / Decision / Proposed edits:** As above. 3 key_facts → 3 edits.
- **Rationale:** Same — 2-hour notification waiver request, CCoP §1.6.

## B24

In B24 the **questions explicitly invoke "CCoP 2.0 Section 8"** ("What CCoP 2.0 Section 8 actions
are required for classification and reporting?"). Per the user's rule, an `expected_response` /
`key_facts` family that legitimately spans two CCoP sections in answering one question is a
FALSE_POSITIVE. The §7 / §8 spread in B24 is genuine — §7.1.1(x) holds the granular
incident-handling subclauses (clause_reference) and §8.3 holds the reporting-timeline facts
(`Serious = 2 h Form A2`, `Substantial = 24 h Form A1`) carried in key_facts. Both are real
clauses; both belong in this answer. I am marking those FALSE_POSITIVE in the next section.

The B24 cases I am marking REAL are the ones that **also** have an additional family disagreement
beyond the standard §7/§8 split — i.e., where `expected_response` introduces a *third* section
that has no support in `clause_reference` or where the case looks miscategorised.

After re-reading the per-case excerpts in the scanner findings, none of the B24 expected_response
"extra families" actually contradict the clause_reference: §8.5 (B24-023), §8.6/§8.7 (B24-010, 14,
19, 25), §7.2 (B24-17, 21), §7.3 (B24-16, 18), §6 / §6.4 (B24-22), §9 / §9.4 / §9.5 (B24-11, 13,
20), §5 / §5.2 (B24-23, 25) are all legitimate cross-section pointers used to enrich the answer.

So **all 24 B24 cases are FALSE_POSITIVE** under the user's stated rules. They are listed in
the FALSE_POSITIVE section.

**Edit count check:** B22 = 20 × 3 = 60. Plus B01-001 (3), B05-013 (3), B05-015 (3), B06-018 (3),
B06-019 (3), B07-001..005 (4 × 3 = 12), B12-016 (3), B12-020 (3), B13-003 (3), B18-001 (2) =
**98 individual edits across 33 REAL_INCONSISTENCY cases**.

---

# 2. FALSE_POSITIVE

One line per case.

## B01
- **B01-012**: clause_reference is `['Section 11 Cybersecurity Act', 'CCoP 2.0 supply chain clauses']` — non-clause-shaped strings that mix two documents (Cybersecurity Act §11 + CCoP supply chain). Per user rules, cross-document references and non-clause-shaped strings are not to be changed.

## B03
- **B03-004**: expected_response cites "Section 11(7)" which is the **Cybersecurity Act** waiver clause; clause_reference correctly anchors CCoP at §1.6.x. The §11 family in expected_response is a cross-document reference, not a CCoP §11.
- **B03-011**: Same pattern as B03-004 — "Section 11(7)" = Cybersecurity Act, not CCoP §11. clause_reference §1.6.x is correct.
- **B03-023**: expected_response cites "5.3.1" (matches clause_reference) and "Section 11(7)" — the latter is again the Cybersecurity Act, not CCoP. Cross-document; no edit.

## B04
- **B04-008**: clause_reference is `['Section 1', 'Scope definition']` — non-clause-shaped strings. The §10 mention in expected_response is a legitimate counter-reference ("Section 10 OT security covers computer-based ICS — this floodgate is not"). Multi-section spread is intentional.
- **B04-018**: clause_reference (§6.2.1, §6.1.3 — network segmentation/protection) plus key_facts spanning §5/§6/§10 reflects a real SIEM IT/OT classification answer that genuinely spans Protection and OT chapters. No single-section anchor is correct here; spread is legitimate.

## B09
- **B09-016**: key_facts.source is the literal string `"Residual risk assessment for government"` — a label, not a CCoP clause citation. There is no CCoP family to compare against. clause_reference §3.2.x is correct on its own.

## B21
- **B21-008**: This is a **hallucination-detection** test case. The point of the test is that "Clause 11.7.5" does not exist; clause_reference is `['N/A']` by design. The §11 family in expected_response is the *hallucinated* clause being refuted, plus a correct reference to the Cybersecurity Act §11. By design, no internal CCoP-clause anchor exists.
- **B21-010**: Same pattern — the test refutes a hallucinated "Clause 4.2.6"; `clause_reference: ['N/A']` is intentional.

## B24

All 24 B24 cases are FALSE_POSITIVE — see the "B24" prose in the REAL section above for reasoning.
The §7 (detection / 7.1.1 incident-handling subclauses) vs §8 (response / 8.3 reporting timelines)
split is the legitimate cross-section structure of CCoP incident handling. Question text explicitly
asks about "Section 8 actions"; clause_reference picks the §7.1.1 anchors; key_facts cite §8.3
reporting timelines. Both are real CCoP clauses and both belong in the answer.

- **B24-001**: §7.1.1(b/g/h) clause_reference + §8.3 key_facts — legitimate detection/response spread.
- **B24-002**: Same as B24-001.
- **B24-004**: §7.1.1(d/g) + §8.3 — legitimate.
- **B24-005**: clause_reference §7.1.1(c/d/e); response cites §8 generically — legitimate.
- **B24-006**: §7.1.1(b/f/h) + §8.3 — legitimate.
- **B24-007**: §7.1.1(b/g/h) + §8.3 — legitimate.
- **B24-008**: §7.1.1(b/g) + §7.1.4 + §8.3 — legitimate.
- **B24-009**: §7.1.1(b/h/i) + §7.1.4 + §8.3 — legitimate.
- **B24-010**: clause_reference §7.1.1(g/h); response adds §8.6 (forensic) — legitimate cross-section.
- **B24-011**: clause_reference §7.1.1(i)/§7.1.4; response adds §8 + §9/§9.5 (BCP) — legitimate; the question explicitly contrasts incident vs business-continuity classification.
- **B24-012**: §7.1.1(d/g) + §8.3 — legitimate.
- **B24-013**: §7.1.1(i)/§7.1.4 + §8/§9 — legitimate; the question is "is this an incident or BCP issue".
- **B24-014**: §7.1.1(d/g) + response adds §8.6 — legitimate.
- **B24-015**: §7.1.1(d/g) + §8.3 — legitimate.
- **B24-016**: clause_reference §7.1.1(g/h); response adds §7.3 (terminated-access) — same-section enrichment, legitimate.
- **B24-017**: §7.1.1(e/g) + response §7.2 (third-party security) — same-section enrichment.
- **B24-018**: §7.1.1(g)/§7.1.4 + response §7.3 — same-section enrichment.
- **B24-019**: §7.1.1(d/f) + §8.6 — legitimate cross-section.
- **B24-020**: §7.1.1(g) + response §8/§9.4/§6 — legitimate; the answer explicitly invokes BCP backup (§9.4) and training (§6) gaps as part of root cause.
- **B24-021**: §7.1.1(g)/§7.1.4 + §7.2 — same-section.
- **B24-022**: clause_reference §7.1.1(d/b/a)/§6.4.1/§6.4.3; response cites §7.1/§6.4 — legitimate (threat intel under §6.4).
- **B24-023**: §7.1.1(g) + response §8.5 (IR-plan testing) + §5 (risk reassessment) — legitimate cross-section authorization (pen-test scenario).
- **B24-024**: §7.1.1(c/d/g) + §8.3 — legitimate.
- **B24-025**: §7.1.1(b/h/i)/§7.1.4 + response §8.6/§8.7 + §5.2 — legitimate cross-section root-cause/remediation chain.

---

# 3. AMBIGUOUS

## B18 — 24 cases (B18-002 through B18-025)

All 24 cases share the **same** problem shape, so I describe it once here:

**Shared shape.**
- `input.question` is *identical* across all 25 B18 cases:
  *"Under Singapore's Cybersecurity Act 2018 and CCoP 2.0, who is personally liable for CII
  compliance violations? What are the responsibilities of the Board, CIIO, and CISO?"*
- The expected_response then embeds a *different* sub-question per case (training, incident
  reporting, employee responsibilities, OT security ownership, audit rep, M&A due diligence, …).
- `metadata.section = "8"` and `metadata.clause_reference = ['8.1.1']` are *the same* in all 24
  cases — i.e., the clause_reference appears to have been set once for the training case
  (B18-002) and copy-pasted across the rest, even though their expected_response sub-questions
  cover wildly different CCoP sections (incident reporting → §7/§8.3, OT ownership → §10, audit
  representation → §1/§3.1, vendor/supply-chain → §3.8, etc.).
- `key_facts` are *also* identical boilerplate across all 25 cases (Cybersecurity Act §11,
  CCoP §1 governance × 2). They do not specifically support each per-case expected_response.

**Why AMBIGUOUS.**
A correct mechanical fix would require, per case, picking the right CCoP clause for that
particular sub-question. Doing that requires real CCoP domain mapping (e.g., "who reports to CSA"
→ §8 reporting; "who maintains asset inventory" → §3.2.2; "supply chain due diligence" → §3.8;
"OT ownership" → §10). That goes beyond mechanical alignment and risks introducing errors.

The fact that the boilerplate key_facts mismatch the per-case expected_responses is also a much
deeper authoring issue — it's not a single field-disagreement bug, it's "this benchmark file was
templated and never customised per case." That needs human review.

**Per-case AMBIGUOUS notes** (each is the same shape — listed for completeness):

- **B18-002**: Sub-question is *training* (Section 8.1.1 referenced in expected_response). clause_reference §8.1.1 actually matches this case correctly — but the boilerplate key_facts (Cybersecurity Act §11 + CCoP §1) don't specifically support training. Unclear whether to add a §8.1.1 source to key_facts or accept the loose match.
- **B18-003**: Sub-question is *who reports incidents to CSA*. Should likely point to §7 / §8.3 reporting clauses, not §8.1.1 training. clause_reference is wrong but the right value depends on which incident clause is canonical.
- **B18-004**: Sub-question is *vendor breach responsibility*. Correct anchor likely §3.8 (supply chain) — but unclear without deep mapping.
- **B18-005**: Sub-question is *risk acceptance approver*. Likely §3.2 risk assessment or §1.5 governance.
- **B18-006**: Sub-question is *employee responsibilities for CCoP compliance*. Could be §1 (governance) or §6 (training/awareness).
- **B18-007**: Sub-question is *CISO vs Risk Manager role distinction*. Likely §3.1 governance.
- **B18-008**: Sub-question is *outsourced CII operations*. Likely §3.8 (supply chain) or §1.4 (applicability).
- **B18-009**: Sub-question is *OT security ownership when OT is managed separately*. Likely §10 (OT) plus §3.1 (governance).
- **B18-010**: Sub-question is *who decides what constitutes critical incident*. Likely §8.3 classification / §3.1 governance.
- **B18-011**: Sub-question is *who maintains CII asset inventory*. Likely §3.2.2.
- **B18-012**: Sub-question is *who authorises cybersecurity budget*. Likely §1.4 / §3.1.
- **B18-013**: Sub-question is *control-vs-operations conflict*. Likely §3.2 risk acceptance.
- **B18-014**: Sub-question is *vendor security assessments*. Likely §3.8.
- **B18-015**: Sub-question is *who represents the org during CSA audits*. Likely §3.1 governance.
- **B18-016**: Sub-question is *employee background screening*. Likely §6 (HR / personnel security).
- **B18-017**: Sub-question is *who is responsible when a control fails despite proper implementation*. Likely §3.2 / §8 (incident).
- **B18-018**: Sub-question is *joint CII arrangement*. Likely §1.4 / §3.1 / §3.8.
- **B18-019**: Sub-question is *cloud service provider breach*. Likely §3.8 / §8.
- **B18-020**: Sub-question is *cybersecurity during M&A due diligence*. Not clearly covered by any single CCoP clause; likely §3.8 + §1.4.
- **B18-021**: Sub-question is *deliberate employee policy violation*. Likely §6 (training/discipline).
- **B18-022**: Sub-question is *supply-chain vulnerabilities in purchased software*. Likely §3.8.
- **B18-023**: Sub-question is *unauthorised subcontracting*. Likely §3.8 / §1.4.
- **B18-024**: Sub-question is *cybersecurity during CII designation transition*. Likely §1.4 + §3.1.
- **B18-025**: Sub-question is *CII scope changes*. Likely §1.2 (scope) / §1.4.

**Recommendation to human reviewer.** The B18-002+ block needs a domain pass that maps each
per-case sub-question to its canonical CCoP clause and replaces both `clause_reference` and the
boilerplate `key_facts` accordingly. A mechanical "string replace" cannot do this safely.
