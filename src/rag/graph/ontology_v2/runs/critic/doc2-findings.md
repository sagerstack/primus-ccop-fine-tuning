# CCoP 2.0 Response-to-Feedback — KG Extraction Critic Findings (Doc 2)

**Reviewer:** independent QA critic (OMD-GraphRAG ontology v1.1)
**Scope reviewed:** all 280 clauses in `reextract/02-ccop-response-to-feedback/clauses.clean.json` vs `runs/extract/CCoP_Response_to_Feedback__*.json` (566 triples).
**Ontology:** `corpus_ontology.json` v1.1 (unchanged).

---

## 1. Summary

**Doc 2 is markedly cleaner than doc 1.** The doc-1 learnings are visibly applied and the extractor now uses the full relation vocabulary correctly:

- **RECOMMENDS (2×)**, **DEFERS_TO (8×)**, **DOES_NOT_SPECIFY (1×)**, **EXCLUDED_FROM_SCOPE (1×)**, **HAS_STATUS (1×)**, **BOUNDED_BY**, **ATTRIBUTE_OF** — all used, and used aptly (e.g. §11.28 password-length↔NIST bridge is a textbook `DEFERS_TO ExternalStandard` + `DOES_NOT_SPECIFY PasswordLength` + `PasswordLength ATTRIBUTE_OF Password`; §11.25 corporate-network exclusion → `EnterpriseNetwork EXCLUDED_FROM_SCOPE CII`; §2.20 not-applicable clause → `CII HAS_STATUS ComplianceStatus`).
- **No Φ (domain/range) violations** found.
- **No citation_id collisions** (the doc-1 footnote-collision defect does not recur here).
- **No fabricated triples.** The 103 Q&A "Feedback" clauses ("Respondents sought clarification on X") correctly receive light topic-invoking triples — this is appropriate for the Q&A framing and I did **not** flag them as thin.

The defects that remain are **few, minor, and localized** — mostly one inverted relation, one clause-merge that drops a triple, and a couple of weak/mis-read triples. No systemic issue on the scale of doc 1's RECOMMENDS-gap or footnote collision.

**Deferred forks — not re-raised per instruction:** (a) systematic shall/should modality encoding (48 "should" clauses, 2 use RECOMMENDS — consistent with the still-open modality fork, mostly CSA soft-explaining a binding clause, so not new defects); (b) umbrella-type leaf granularity (e.g. emergency accounts / privileged accounts under generic `Account`/`AccessControlMechanism`). Both left untouched.

**Findings by category:** Wrong-relation / inverted 3 · Missed (incl. one clause-merge drop) 3 · Weak / mis-read triple 2 · Consistency 1. (9 total; all Low–Medium.)

---

## 2. Per-clause findings (ranked by value)

Legend: **WRONG**=wrong/inverted relation, **MISS**=missed triple, **SEG**=segmentation, **WEAK**=weak/mis-read triple, **CONS**=consistency.

| # | citation_id | Cat | Issue | Suggested fix |
|---|---|---|---|---|
| 1 | `::2.27` | WRONG | "The preamble is **not** in the cybersecurity audit." Extracted as `Audit COVERS AuditScope` — which asserts **inclusion**, the opposite of the clause's meaning. The exclusion fact is inverted/lost. | Drop `Audit COVERS AuditScope`. Ideal is an exclusion edge, but `EXCLUDED_FROM_SCOPE`'s domain is EnterpriseNetwork/ComputerSystem (a preamble isn't in-domain), so cleanest is to leave §2.27 with no audit-scope triple rather than assert the inverse. |
| 2 | `::13.32` | SEG/MISS | Clause body contains a **second merged clause 13.33** ("13.33. With the establishment of the recovery procedures for Kerberos Ticket Granting Ticket account, the CIIO is expected to exercise the procedures in cybersecurity exercise."). 13.33 has no standalone record; its content is dropped — only `DRP RECOVERS CII` + `ACM PROTECTS CII` captured. | Segmentation fix: split 13.33 into its own clause. Add the missed triple `CybersecurityExercise VALIDATES DisasterRecoveryPlan` (the Kerberos recovery exercise). |
| 3 | `::11.5` | WEAK | "only accounts authorised to install software are given the rights" → `SecurityConfigurationBaseline DISABLES Application`. This is an **access-control on install rights**, not a baseline disabling an application. `AccessControlMechanism PROTECTS CII` (also present) is the correct capture. | Drop `SecurityConfigurationBaseline DISABLES Application`; the ACM triple already covers it. |
| 4 | `::2.24` | WEAK | Feedback clause: "Respondents **requested** definitions to terms such as 'raw logs'…" → `Provision DEFINES Log`. The clause does **not** define anything — it asks for definitions. `DEFINES` misreads a request as a definition. | Drop `Provision DEFINES Log` (leave as a topic mention), or move a `DEFINES` to §2.25 (the CSA response that says the glossary was updated) if a definition edge is wanted. |
| 5 | `::2.3` | CONS | "The cybersecurity capabilities under Annex A … is **not to be included in the scope for the cybersecurity audit**." Captured only as `Provision RECOMMENDS SecurityControl`; the audit-exclusion is uncaptured, though §11.25 captures the analogous corporate-network exclusion. | For consistency with §11.25, optionally add `EnterpriseNetwork EXCLUDED_FROM_SCOPE Audit` (Annex A applies to the wider organisation/enterprise network, which is out of audit scope). |
| 6 | `::8.10` | MISS | "the approved auditor … should review and ascertain that the third-party audit report **covers the scope of the CCoP requirements**." Got `Auditor AUDITS CII` + `Audit PRODUCES AuditReport`; the scope-coverage idea is missed. | Optional add `Audit COVERS Provision` (the audit/report must cover the CCoP provisions). Low. |
| 7 | `::11.40` | WEAK | "approve only applications used for … operation and cybersecurity of the CII" → `SecurityConfigurationBaseline DISABLES Application`. Application whitelisting/approval, not baseline-disable; borderline but reads as a slight mis-map. `Provision MANDATES Policy` (also present) is the stronger capture. | Low priority — acceptable; note alongside #3 as a recurring "approval/whitelisting → DISABLES Application" habit (2 instances). |
| 8 | `::7.9` | — (no fix) | Source typo "should be adopt CSA's SBD framework"; extraction `CIIO IMPLEMENTS SecurityByDesign` is fine. Noted only for completeness. | None. |
| 9 | `::11.13` | WEAK (deferred-adjacent) | Emergency accounts clause → only `AccessControlMechanism PROTECTS CII`. Thin, but "emergency accounts ≈ privileged/emergency account" specificity falls under the **deferred leaf-granularity fork** — not raised as a new defect. | None (deferred). |

---

## 3. What is NOT a defect (checked, do not re-flag)

- The 103 "Feedback" clauses with light topic-invoking triples are **correct** for the Q&A framing — not thin.
- `DEFERS_TO ExternalStandard` uses (§5.3, §5.10 ISA/NIST, §11.22 NIST/ISO, §11.28 NIST, §11.30 CIS Benchmarks, §11.37/38 OWASP, §14.2 SANS/ISACA) are all apt.
- `Audit COVERS AuditScope/Provision` at §2.4, §2.5, §2.6, §2.9 is **correct** (these genuinely describe audit-scope inclusion) — only §2.27's use is inverted (see #1).
- Subtype fillers (`SystemActor SEGREGATES SystemActor` §11.42/43; `OTSystem CONNECTED_TO EnterpriseNetwork` §15.2/13) are valid and precise.
- The single zero-triple clause (§1.5 "CSA would like to thank all respondents") is legitimately empty.
- Modality/`RECOMMENDS` under-use is **consistent with the deferred modality fork** and is not counted as a new doc-2 defect.
