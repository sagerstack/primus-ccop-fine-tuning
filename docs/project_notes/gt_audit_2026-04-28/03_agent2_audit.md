# GT Audit — Agent 2 (Independent Auditor)

Independent verification of Agent 1's 98 proposed edits across 33 REAL_INCONSISTENCY cases
(plus a confirmation pass on the 24 AMBIGUOUS B18 cases). Cross-checked against:

- The actual JSONL records under `ground-truth/test-suite/`
- The CCoP 2.0 source PDF (`ccop-official/CCoP---Second-Edition_Revision-One.pdf`,
  pdftotext-extracted to `/tmp/ccop20.txt`)
- The clause inventory at `src/rag/ingestion/fixtures/clause_inventory.json`

---

## Summary

| Verdict | Count |
|---|---:|
| APPROVE | 86 |
| REJECT | 0 |
| NEEDS_REVISION | 12 |
| **Total proposed edits audited** | **98** |

Plus AMBIGUOUS-block confirmation: **24 B18 cases (B18-002..B18-025) — confirmed AMBIGUOUS,
NOT safe for mechanical correction.**

**Overall verdict — partial APPROVE.**

The B22 phantom-§11 batch (60 edits) and the §3.2 / §3.8 / §8.2 / §1.6 alignments in
B05/B06/B12/B13 (23 edits) and B01-001 (3 edits) are safe and should be applied. The B07
batch (12 edits) is **NEEDS_REVISION** — the underlying issue is real but Agent 1's proposed
target clause (`§3.2.2`) is topically wrong; the canonical asset-inventory clause is `§4.1.1`,
not `§3.2.2`. Agent 1's mapping was based on a faulty section map (see "Critical correction"
below).

### Critical correction to Agent 1's domain priors

Agent 1's stated CCoP 2.0 section map contains several **factual errors**, verified against
the actual PDF table-of-contents and body text:

| Topic | Agent 1 said | Verified actual |
|---|---|---|
| Asset inventory | §3.2.2 | **§4.1.1** (Asset Management) |
| Section 11 of CCoP 2.0 | "does not exist" | **EXISTS** — §11 is "Domain-Specific Practices" (DNSSEC); §11.1, §11.1.1, §11.2, §11.2.1, §11.2.2 all exist |
| §8.3 reporting timelines | claimed §8.3 holds 2h/24h timelines | **§8.3 does not exist** — §8 has only §8.1 (Backup) and §8.2 (BCP/DRP). 2h/24h timelines come from the Cybersecurity Act, not CCoP §8.3 |
| §9 | "Resilience / BCP" | **§9 = Cybersecurity Training & Awareness**; resiliency is §8 |
| §1.2 | "Scope / digital boundary" | §1.2 = "Glossary and Interpretation" (defines terms incl. CII). No clause is titled "Scope" or "Digital Boundary" in CCoP 2.0 |
| §5.3.1 MFA / access control | "MFA, access control 5.3.1" | §5.1 = Access Control; §5.2 = Account Management; §5.3 = Privileged Access Management. No explicit MFA clause exists at §5.3.1 — §5.3.1 is privileged-access scope |
| §3.8 | "supply chain" | Correct (§3.8 = Outsourcing and Vendor Management) |
| §1.6 | "Waiver" | Correct |
| §3.1 | "governance roles" | Correct (§3.1 = Leadership and Oversight) |
| §3.2 | "Risk Management" | Correct |
| §7.1.1 | "incident-handling subclauses" | Correct |
| §10 | "OT security" | Correct |

The **B22 fix is still correct** despite the flawed reasoning: §1.6 IS the CCoP waiver clause,
and §11 in CCoP 2.0 is DNSSEC (definitely not waiver). The fix produces the right anchor.

The **B07 fix is wrong** because §3.2.2 is "risk assessment methodology steps" (risk analysis,
evaluation, response), not asset inventory. The B07 questions are explicitly about CII asset
inventory gaps — those belong at §4.1.1.

The reviewer should also note that **B07's existing `clause_reference: ['3.2.2(b)', '3.2.2(c)']`
is itself topically wrong** for the asset-inventory questions. A proper fix needs both
`clause_reference` and `key_facts[*].source` rewritten to §4.1.1, which is outside Agent 1's
scope (they preserved clause_reference per task rules). Flagging for human review.

---

## APPROVED EDITS (86)

These are safe to apply mechanically.

### B01-001 (b01_ccop_applicability_scope.jsonl)
- key_facts[0].source: `"CCoP 2.0 Section 2, Cybersecurity Act Section 11"` → `"CCoP 2.0 Section 1.2, Cybersecurity Act Section 11"`
- key_facts[1].source: `"CCoP 2.0 Scope section, RESPONSE-TO-FEEDBACK Q2.2-2.3"` → `"CCoP 2.0 Section 1.2, RESPONSE-TO-FEEDBACK Q2.2-2.3"`
- key_facts[3].source: `"CCoP 2.0 Section 2"` → `"CCoP 2.0 Section 1.2"`

(Note: §1.2 is "Glossary and Interpretation"; §1.4 is "Legal Effect / applicability". Aligning to
existing `clause_reference: ['1.2.1', '1.4.1']` — `Section 1.2` matches `1.2.1` in clause_reference.
The original "Section 2" is unambiguously wrong since CCoP §2 is "AUDIT REQUIREMENTS".)

### B05-013 (b05_control_comprehension.jsonl)
- key_facts[0].source: `"CCoP 2.0 4.3"` → `"CCoP 2.0 1.6.1"`
- key_facts[1].source: `"CCoP 2.0 4.3"` → `"CCoP 2.0 1.6.2"`
- key_facts[2].source: `"CCoP 2.0 4.3"` → `"CCoP 2.0 1.6.3"`

(Verified: §4.3 does not exist in CCoP 2.0. §4 has only §4.1 Asset Management.
§1.6.1/1.6.2/1.6.3 exist and are the Waiver clauses. Question is about legacy-system
exemptions = waiver. expected_response explicitly cites "CCoP 2.0 Section 1.6 (Waiver)".)

### B05-015 (b05_control_comprehension.jsonl)
- key_facts[0].source: `"CCoP 2.0 9.3.1"` → `"CCoP 2.0 3.8.1"`
- key_facts[1].source: `"CCoP 2.0 9.3.1"` → `"CCoP 2.0 3.8.2"`
- key_facts[2].source: `"CCoP 2.0 9.3.1"` → `"CCoP 2.0 3.8.3"`

(Verified: §9 is "Cybersecurity Training & Awareness" — no §9.3.x exists in inventory.
§3.8 is "Outsourcing and Vendor Management" = supply chain. §3.8.1, §3.8.2, §3.8.3 all exist.
Question is about hardware/software supply chain controls.)

### B06-018 (b06_intent_understanding.jsonl)
- key_facts[0].source: `"CCoP 2.0 7.4.1"` → `"CCoP 2.0 8.2.1"`
- key_facts[1].source: `"CCoP 2.0 7.4.1"` → `"CCoP 2.0 8.2.1"`
- key_facts[2].source: `"CCoP 2.0 7.4.1"` → `"CCoP 2.0 8.2.2"`

(Verified: §7.4 does not exist. §7 has §7.1 Incident, §7.2 Crisis Comms, §7.3 Cyber Exercise.
§8.2.1 and §8.2.2 are the BCP/DRP clauses. expected_response cites §8.2 explicitly.)

### B06-019 (b06_intent_understanding.jsonl)
- key_facts[0].source: `"CCoP 2.0 4.2.1"` → `"CCoP 2.0 3.2.1"`
- key_facts[1].source: `"CCoP 2.0 4.2.1"` → `"CCoP 2.0 3.2.1"`
- key_facts[2].source: `"CCoP 2.0 4.2.1"` → `"CCoP 2.0 3.2.1"`

(Verified: §4.2 does not exist. §3.2.1 is the cybersecurity risk management framework clause.
Question is about formal risk assessment intent. expected_response cites §3.2.)

### B12-016 (b12_audit_perspective_alignment.jsonl)
- key_facts[0].source: `"CCoP 2.0 9.3.1"` → `"CCoP 2.0 3.8.1"`
- key_facts[1].source: `"CCoP 2.0 9.3.1"` → `"CCoP 2.0 3.8.1"`
- key_facts[2].source: `"CCoP 2.0 9.3.1"` → `"CCoP 2.0 3.8.1"`

(Same §9.3.1 ↔ §3.8 confusion as B05-015. Supply chain audit → §3.8.)

### B12-020 (b12_audit_perspective_alignment.jsonl)
- key_facts[0].source: `"CCoP 2.0 4.2.1"` → `"CCoP 2.0 3.2.1"`
- key_facts[1].source: `"CCoP 2.0 4.2.1"` → `"CCoP 2.0 3.2.1"`
- key_facts[2].source: `"CCoP 2.0 4.2.1"` → `"CCoP 2.0 3.2.1"`

(Same §4.2.1 ↔ §3.2.1 confusion as B06-019. Risk-based audit methodology → §3.2.)

### B13-003 (b13_evidence_expectation_awareness.jsonl)
- key_facts[0].source: `"CCoP 2.0 Section 4"` → `"CCoP 2.0 Section 3.2"`
- key_facts[1].source: `"CCoP 2.0 Section 4"` → `"CCoP 2.0 Section 3.2"`
- key_facts[2].source: `"CCoP 2.0 Section 4"` → `"CCoP 2.0 Section 3.2"`

(Verified: clause_reference is `['3.2.4', '3.2.2', '3.2.1', '3.2.5']` — risk register
and risk methodology — all under §3.2. The expected_response self-mislabels as "Identification
(Section 4)" but the actual content is risk register / methodology / acceptance documentation,
which lives at §3.2. Note for human reviewer: the expected_response domain label "Section 4"
also needs correcting in a future pass — but that is out of scope per task rules.)

### B18-001 (b18_responsibility_attribution_sg.jsonl)
- key_facts[1].source: `"CCoP 2.0 Section 1"` → `"CCoP 2.0 Section 3.1"`
- key_facts[2].source: `"CCoP 2.0 Section 1"` → `"CCoP 2.0 Section 3.1"`

(Verified: clause_reference is `['3.1.2', '3.1.3', '3.1.1']` (Leadership and Oversight).
§3.1 contains BoD / senior management / CISO requirements. The original "Section 1" was
loosely defensible (governance lives in §1 and §3) but §3.1 is the precise anchor. The
Cybersecurity Act §11 ref in key_facts[0] is preserved as a valid cross-doc reference.)

### B22-001 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-002 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-003 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-004 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-005 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-006 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-007 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-008 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-009 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-010 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-011 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-012 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-013 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-014 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-015 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-016 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-017 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-018 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-019 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

### B22-020 (b22_waiver_exception_reasoning.jsonl)
- key_facts[0].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[1].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`
- key_facts[2].source: `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11"` → `"Cybersecurity Act Section 11(7) and CCoP 2.0 Section 1.6"`

(B22 group rationale: All 20 records share clause_reference rooted at §1.6.x (Waiver) and a
key_facts[*].source string with the literal `"CCoP 2.0 Section 11"`. CCoP 2.0 §11 is
"Domain-Specific Practices" (DNSSEC) — definitely NOT the waiver clause. CCoP §1.6 IS the
Waiver clause. The Cybersecurity Act §11(7) prefix is preserved as a valid cross-doc
statutory reference. 60 mechanical edits, all safe.)

---

## REJECTED EDITS (0)

None. No proposed edit points to a clause that does not exist or is flatly wrong topically
in a way that would propagate confidently-wrong information *worse* than the current state.

The closest call is B07 (see NEEDS_REVISION) — the proposed §3.2.2 anchor is technically
in the corpus and topically adjacent (risk methodology mentions asset identification at
§3.2.2(a)) but is not the canonical asset-inventory clause; that's §4.1.1.

---

## NEEDS_REVISION (12 edits across 4 cases)

The B07 batch — issue is real, but Agent 1's proposed clause `§3.2.2` is the wrong topical
anchor. The B07 questions are all about CII **asset inventory** scenarios (OT systems,
shadow IT, outdated inventory, data flow mapping). The canonical asset-inventory clause in
CCoP 2.0 is **§4.1.1** ("The CIIO shall establish mechanisms and processes to identify all
CII assets and maintain an inventory of the assets") with sub-items (a) through (j) covering
owner, name, dependencies, location, etc. §3.2.2 is the risk-assessment-methodology clause
(risk identification / analysis / evaluation / response).

Agent 1's mapping is consistent with the existing `clause_reference: ['3.2.2(b)', '3.2.2(c)']`
in each B07 record — but **that clause_reference is itself topically wrong** for the
asset-inventory scenarios. A correct fix needs to rewrite both `clause_reference` and
`key_facts[*].source` to §4.1.1 — which is outside Agent 1's stated scope.

### B07-001 (b07_gap_identification_quality.jsonl) — NEEDS_REVISION
- Proposed: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"` (×3)
- Recommended: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 4.1.1"` (×3), AND rewrite
  `metadata.clause_reference` from `['3.2.2(b)', '3.2.2(c)']` to `['4.1.1']`.
- Reason: scenario is "Incomplete CII asset inventory" — §4.1.1(a-j) is the canonical inventory clause.

### B07-002 (b07_gap_identification_quality.jsonl) — NEEDS_REVISION
- Proposed: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"` (×3)
- Recommended: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 4.1.1"` (×3), AND rewrite clause_reference to `['4.1.1']`.
- Reason: shadow-IT inventory gap — §4.1.1.

### B07-003 (b07_gap_identification_quality.jsonl) — NEEDS_REVISION
- Proposed: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"` (×3)
- Recommended: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 4.1.2"` (×3), AND rewrite clause_reference to `['4.1.2']`.
- Reason: scenario is "outdated inventory" — §4.1.2 specifically requires "The CIIO shall
  update the inventory whenever there is any change to any CII asset or to the information
  to be recorded in the inventory."

### B07-005 (b07_gap_identification_quality.jsonl) — NEEDS_REVISION
- Proposed: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 3.2.2"` (×3)
- Recommended: `"CCoP 2.0 4.2.2"` → `"CCoP 2.0 4.1.1"` (×3), AND rewrite clause_reference to `['4.1.1']`.
- Reason: data-flow mapping in inventory — §4.1.1(e) requires "The dependencies of each CII
  asset and the connections between each CII asset and any systems or networks (whether
  internal or external to the CII)"; §4.1.1(j) requires "CII network topology diagram, including
  the CII network perimeter, and all external computers and computer systems that the CII
  interfaces with." This is exactly the data-flow mapping requirement.

**Recommendation for the application step:** Hold the B07 batch (12 edits) for a human pass
that also corrects `metadata.clause_reference`. Apply the other 86 approved edits (B22 ×60,
B05/B06/B12/B13 ×24, B01-001 ×2... I mean ×3, B18-001 ×2, totalling 60+9+9+3+2 = 86)
mechanically.

(Edit-count reconciliation: 60 + 6 (B05) + 6 (B06) + 6 (B12) + 3 (B13) + 3 (B01-001) + 2 (B18-001) = 86 approved; 12 needs-revision (B07-001/002/003/005, 3 edits each); 86 + 12 = 98 ✓.)

---

## AMBIGUOUS confirmation

### B18-002 .. B18-025 — confirmed AMBIGUOUS (24 cases)

Independently verified Agent 1's flag. The 25 B18 records (B18-001..B18-025) share an
identical top-level `input.question` ("Under Singapore's Cybersecurity Act 2018 and CCoP 2.0,
who is personally liable for CII compliance violations? What are the responsibilities of
the Board, CIIO, and CISO?") but each record's `expected_response` embeds a *different*
sub-question:

| test_id | sub-question topic | likely correct CCoP anchor |
|---|---|---|
| B18-002 | training | §9.1 / §9.2 |
| B18-003 | incident reporting to CSA | §7.1.1(b) + Cybersecurity Act §14 |
| B18-004 | vendor breach | §3.8.x |
| B18-005 | risk acceptance approver | §3.2.4(g) / §3.1 |
| B18-006 | employee compliance responsibilities | §9 / §3.1 |
| B18-007 | CISO vs Risk Manager | §3.1.3 |
| B18-008 | outsourced CII operations | §3.7 / §3.8 |
| B18-009 | OT security ownership | §10 + §3.1 |
| B18-010 | critical-incident classification | §7.1.1(d) |
| B18-011 | asset inventory ownership | §4.1.1(a) |
| B18-012 | budget/resource authorization | §3.1 |
| B18-013 | controls vs operations conflict | §3.2 / §1.6 |
| B18-014 | vendor security assessments | §3.8.3 |
| B18-015 | CSA audit representation | §3.1 / §2.1 |
| B18-016 | employee background screening | (no direct CCoP clause; Annex A) |
| B18-017 | control failure despite implementation | §3.2 / §7.1.4 |
| B18-018 | joint CII arrangement | §1.4 / §3.1 |
| B18-019 | CSP breach affecting CII | §3.7 / §3.8 |
| B18-020 | M&A due diligence | (no direct CCoP clause; Annex A) |
| B18-021 | deliberate employee policy violation | §9.1 / Annex A |
| B18-022 | supply-chain SW vulnerabilities | §3.8 |
| B18-023 | unauthorised subcontracting | §3.8 / §1.4 |
| B18-024 | CII designation transition | §1.4.4 / §1.4.5 |
| B18-025 | CII scope changes | §1.4 (no specific scope clause) |

Every single one of the 24 records has `metadata.section: "8"` and
`metadata.clause_reference: ['8.1.1']` — i.e., the clause_reference was set once for B18-002
("training") and copy-pasted across all 24 sub-questions. §8.1.1 is the **backup and
restoration plan** clause — totally unrelated to any of the 24 sub-questions.

The boilerplate `key_facts` are also identical across all 24 records and don't specifically
support any per-case expected_response.

This is not a single-field-disagreement bug; it's a benchmark-templating issue that needs a
domain-aware human pass to:
1. Rewrite `metadata.clause_reference` per case to the correct CCoP anchor
2. Rewrite `key_facts` per case (both `fact` text and `source`) to support the specific
   expected_response sub-question
3. Decide whether B18-016, B18-020 should be removed entirely (no direct CCoP clause covers
   employee background screening or M&A diligence — Annex A is non-mandatory guidance only)

**These 24 cases must NOT be touched mechanically.** Confirmed AMBIGUOUS.

---

## Notes / open items for the human reviewer (out-of-scope for this audit, but should be
recorded)

1. **B07's `clause_reference` is wrong, not just key_facts.source.** All four B07 cases cite
   §3.2.2(b)/(c) (risk analysis/evaluation) for asset-inventory questions; the canonical
   anchor is §4.1.1 / §4.1.2. Both fields need rewriting together.

2. **B13-003's expected_response mislabels the CCoP domain.** Says "Identification (Section
   4)" but the content (risk register, risk methodology, risk acceptance) lives at §3.2 /
   §3.2.4. Out of scope to edit expected_response per task rules — but flag for future pass.

3. **Agent 1's domain priors should be corrected** in any downstream documentation. The
   "CCoP 2.0 has no Section 11" claim is false (Section 11 = DNSSEC). The "asset inventory
   in §3.2.2" claim is false (it's §4.1). The "§8.3 reporting timelines" claim is false (no
   §8.3 in CCoP 2.0; reporting timelines are in the Cybersecurity Act). These misstatements
   did not, in this batch, produce wrong fixes for B22 / B05 / B06 / B12 / B13 / B01 / B18-001
   because the *target* clauses Agent 1 selected (§1.6, §3.2, §3.8, §8.2, §3.1) are correct
   regardless. But they did produce a wrong target for B07 (§3.2.2 instead of §4.1.1), and
   could mislead future audit work.

4. **B22-015's clause_reference contains `1.4.7` in addition to §1.6.x.** §1.4.7 is "the
   Commissioner may issue a direction... for compliance" — i.e., the enforcement / denial
   pathway. For a "denial / enforcement" waiver scenario this is a defensible secondary
   anchor. The §1.4.7 element is preserved untouched by the proposed edit, which is correct.
