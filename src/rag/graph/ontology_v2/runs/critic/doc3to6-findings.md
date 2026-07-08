# CCoP Supplementary Guides — KG Extraction Critic Findings (Docs 3–6)

**Reviewer:** independent QA critic (OMD-GraphRAG ontology v1.1)
**Docs reviewed:**
- **D3 Auditing Guidelines** — 17 clauses, 36 triples
- **D4 Threat Modelling Guide** — 12 clauses, 29 triples
- **D5 Risk Assessment Guide** — 15 clauses, 35 triples
- **D6 Security-by-Design** — 98 clauses, 178 triples

**Ontology:** `corpus_ontology.json` v1.1 (unchanged). Deferred forks (systematic shall/should modality; umbrella-type leaf granularity) **not re-raised**.

---

## 1. Summary

**All four docs are clean and faithful.** No Φ (domain/range) violations, no fabricated triples, and — importantly — **no citation_id collisions**: the doc-1 footnote-vs-header collision bug does **not** recur. Footnote records (SBD `::1 ::2 ::5`, D6 `::5` = IM8, etc.) are their own separate records and receive sensible topic-invoking triples (`CodeOfPractice OVERLAPS_WITH RegulatoryFramework` for IM8/DCM), not clobbered/fabricated content. These are guide/framework docs and the extractor correctly gives descriptive clauses light topic-invoking triples — I did **not** over-flag thin.

**Per-doc one-liners:**
- **D3 Auditing** — solid; audit machinery (`AUDITS`/`COVERS`/`PRODUCES`/`APPROVES`/`APPOINTS`) well captured. One B22-relevant miss at §6.3 (waiver still in audit scope + compensating-control check).
- **D4 Threat Modelling** — consistent and correct (`ThreatModelling IDENTIFIES CybersecurityThreat` dominant; `DEFERS_TO` for STRIDE/NIST/OWASP/MITRE). One high-value under-extraction: the STRIDE-LM control→threat table (§3.4) drops ~7 explicit control-mitigation pairs.
- **D5 Risk Assessment** — the cleanest of the four; risk vocabulary (`HAS_LIKELIHOOD`/`HAS_IMPACT`/`EXPLOITS`/`BOUNDED_BY`/`ACCEPTED_BY`/`MITIGATED_BY`) applied precisely. Only trivial misses (AttackConcept, a couple of DEFERS_TO).
- **D6 Security-by-Design** — §1–5 lean on `CIIO IMPLEMENTS SecurityByDesign` (by nature, not flagged); §6.x security-process/testing clauses are well covered (`VulnerabilityAssessment IDENTIFIES`, `CONDUCTS PenetrationTesting`, `ADDRESSES Vulnerability`, `Auditor AUDITS`, `IMPLEMENTS Monitoring/ChangeManagement`). Two clear `DEFERS_TO` misses where ISO/NIST standards are explicitly named.

**One recurring minor pattern (across D5/D6):** a few clauses that explicitly name an external standard are not encoded as `DEFERS_TO ExternalStandard`, even though `DEFERS_TO` is used correctly elsewhere in the same docs — inconsistent application, not absence.

**Findings by category:** Missed (incl. DEFERS_TO / STRIDE controls) 9 · Under-extraction (thin-with-content) 2 · all Low–Medium. No wrong-relation-direction or over-extraction defects found.

---

## 2. Per-clause findings (ranked by value)

Legend: **MISS**=missed typed triple, **THIN**=content-rich clause under-extracted, **CONS**=consistency.

### D3 — Auditing Guidelines
| # | citation_id | Cat | Issue | Suggested fix |
|---|---|---|---|---|
| 1 | `::6.3` | MISS | Audit Criteria row: "If a waiver is granted, the CoP clause **remains subjected for cybersecurity audit**… the auditor should check the validity of the justification, the waiver condition and the **effectiveness of the compensating controls**." Only `COVERS AuditScope/Provision` captured — the waiver + compensating-control facts (B22-relevant) are missed. | Add `Waiver WAIVES Provision` and `Provision COMPENSATED_BY CompensatingControl` (and optionally `CompensatingControl MITIGATES CybersecurityRisk`). |
| 2 | `::5` | MISS | Auditor approval "two main criteria: independence and **competency (professional qualifications/certifications)**" — competency/certification not captured (though §6.1 has `HAS_CERTIFICATION`). | Optional add `Auditor HAS_CERTIFICATION Certification`. Low. |

### D4 — Threat Modelling Guide
| # | citation_id | Cat | Issue | Suggested fix |
|---|---|---|---|---|
| 3 | `::3.4` | THIN | The STRIDE-LM section (w=1318) explicitly pairs controls to threats — strong authentication↔spoofing, encryption/access-checks↔tampering, logging/digital-signatures↔repudiation, encryption↔information-disclosure, redundancy↔DoS, least-privilege↔elevation-of-privilege, segmentation/firewall↔lateral-movement — yet only 3 generic triples captured. | Add representative `SecurityControl MITIGATES CybersecurityThreat` (a few of the above); `CIIO APPLIES_PRINCIPLE DesignPrinciple` (least privilege); optionally `SecurityControl REDUCES AttackConcept` (lateral movement). Measured — huge descriptive block, so a handful suffices. |
| 4 | `::1.1` / `::3.5` | MISS | Kill-chain / crown jewels / lateral movement (AttackConcept) described but not captured. | Optional `SecurityControl REDUCES AttackConcept`. Low. |

### D5 — Risk Assessment Guide
| # | citation_id | Cat | Issue | Suggested fix |
|---|---|---|---|---|
| 5 | `::4.1` | MISS | Task A "crown jewels" and "stepping stones" (AttackConcept), and Task B "refer to the **Guide to Cyber Threat Modelling**" (external ref) not captured. | Optional `CyberThreatActor` already `TARGETS CIIAsset`; add `SecurityControl REDUCES AttackConcept` and/or `CIIO DEFERS_TO ExternalStandard`. Low. |
| 6 | `::4.2` | CONS | Likelihood factors "adapted from **Microsoft's DREAD model**" and "**NIST SP 800-30**" explicitly named; no `DEFERS_TO`. | Optional `CIIO DEFERS_TO ExternalStandard`. Low. |
| 7 | `::3.3` | MISS | "Cybersecurity Function … responsible for the **implementation and maintenance of cybersecurity controls**" — only `RiskRole RESPONSIBLE_FOR RiskManagement` captured. | Optional `RiskRole RESPONSIBLE_FOR SecurityControl`. Low. |

### D6 — Security-by-Design
| # | citation_id | Cat | Issue | Suggested fix |
|---|---|---|---|---|
| 8 | `::6.2.1.1` | MISS | "Security requirements should also include … **references from International Standards (e.g. ISO2700X standards)**" — explicit external-standard ref not encoded. | Add `CIIO DEFERS_TO ExternalStandard` (ISO 27000). Medium. |
| 9 | `::6.6.1.2` | MISS | "**NIST SP 800-88 r1, Guidelines for Media Sanitisation** provides details on media sanitisation best practices." — explicit external-standard ref not encoded. | Add `CIIO DEFERS_TO ExternalStandard` (NIST SP 800-88). Medium. |
| 10 | `::6.3.1.1` | MISS | Security architecture review includes "**design vulnerability assessments**"; `VulnerabilityAssessment` not captured (only `IMPLEMENTS SecurityArchitecture` + `WITHIN_BOUNDARY`). | Optional `VulnerabilityAssessment IDENTIFIES Vulnerability`. Low. |
| 11 | `::6.4.1.1` | MISS | Source-code review examines for "**Backdoors, logic bombs, and malware**"; Malware/detection not captured (only `ADDRESSES Vulnerability` + `EXPLOITS`). | Optional `Monitoring DETECTS Malware` or `MalwareProtection MITIGATES Malware`. Low. |

---

## 3. What is NOT a defect (checked, do not re-flag)

- **No citation_id collisions** in any of the four docs (verified programmatically). Footnote records (SBD `::1 ::2 ::5`, D6 `::5` IM8) are separate and carry sensible `OVERLAPS_WITH` topic triples — not fabricated, not clobbering headers. The doc-1 collision defect is resolved.
- **D6 §1–5 `CIIO IMPLEMENTS SecurityByDesign` repetition** is inherent to the intro/overview sections and is correct — not flagged.
- Guide-doc descriptive clauses with a single topic-invoking triple are appropriate, not thin.
- `DEFERS_TO ExternalStandard` **is** used correctly in many places (D4 §3.4/§3.5 STRIDE/NIST/OWASP/MITRE/Kill-Chain; D6 §3.4 NIST/ISO/IEEE) — findings 6/8/9 are consistency gaps, not systemic absence.
- No wrong-relation-direction and no over-extraction/fabrication found in any doc.
