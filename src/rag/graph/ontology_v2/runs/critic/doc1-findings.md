# CCoP 2.0 — KG Extraction Critic Findings (Doc 1)

**Reviewer:** independent QA critic (OMD-GraphRAG ontology v1.1)
**Scope reviewed:** all 385 clauses in `reextract/01-ccop-2-0/clauses.clean.json` vs `runs/extract/CCoP_2_0__*.json` (733 triples total).
**Ontology:** `corpus_ontology.json` v1.1 (72 relations, 122 entity types).

---

## 1. Summary

Overall the extraction is **type-clean and broadly faithful** — I found **no Φ (domain/range) violations** and few outright fabrications. The dominant relations (IMPLEMENTS 103, PROTECTS 98, DETECTS 45, MITIGATES 30) are used consistently and mostly correctly. The substantive protection/detection/response sections (§5–§8, §10) are well covered.

However there are **five systemic issues**, three of them serious:

- **RECOMMENDS is never used — 0 times across the whole corpus** (20 clauses contain "should"). Combined with MANDATES being used only 17×, the **shall/should modality split (B02) is effectively not encoded** in the graph. Most "shall implement" obligations are captured as the modality-neutral `CIIO IMPLEMENTS X` (actor→control) rather than `Provision MANDATES X`, so the graph cannot distinguish a mandatory control from a recommended one.
- **Annex A is mis-encoded as binding.** §11.2.2 and its three `::table::*` children are Annex A guidance — explicitly *"CIIOs are highly encouraged to implement these measures"* and *"need not be included in the scope of cybersecurity audits"* — every line reading "The CIIO **should** adopt/ensure/conduct". They are extracted with the same mandatory-flavoured relations (IMPLEMENTS, APPLIES_PRINCIPLE, CONDUCTS, PROTECTS) as the binding §3–§10 clauses. The non-binding + out-of-audit-scope character is erased.
- **citation_id collision silently drops the 6 reference footnotes.** Footnote clauses `CCoP 2.0::1..6` share their citation_id with the section headers `1..6` (verified: each ID appears twice). Because the cache is keyed by citation_id, the footnotes are not independently represented — the dump shows the *section header's* triples duplicated onto them. As a result the external-standard pointers in those footnotes (CSA Risk-Assessment Guide, CSA Threat-Modelling Guide, CSA Security-by-Design Framework, NIST Zero-Trust white paper, CREST, Purdue/PERA) are **never captured**. This is a pipeline keying bug **and** a silent-drop of ~6 legitimate `DEFERS_TO ExternalStandard` edges.
- **DEFERS_TO is under-used (2×)** — only §5.12.5 (OWASP) and the §5.12 preamble. The many "may refer to / shall refer to / take reference from" external-standard references (§3.4.1 SBD Framework, the 6 footnotes above) are not encoded as DEFERS_TO.
- **Entity endpoints are bare type-names (leaf concepts flattened).** Every `DesignPrinciple` node is literally "DesignPrinciple", so defence-in-depth / least-privilege / segregation-of-duties / defence-by-diversity / zero-trust all collapse into one node; likewise MFA, WAF, DNSSEC, Kerberos-reset, SIS lose their identity under generic type labels. For a KG whose cross-clause bridge *is* the shared canonical entity, this reduces resolution to type-granularity and loses distinctions several benchmarks need (B05, B04). **Flagging to confirm whether this is intended POC canonicalization** — if intended, ignore; if not, leaf concept names should be specialised.

**RECOMMENDS-usage verdict:** the suspicion is confirmed and is worse than "under-used" — it is **entirely unused (0×)**. The author correctly avoided false positives (e.g. §3.8.3(c)'s "should" is a conditional, not a recommendation — rightly skipped), but never captured the genuine recommendations. The clearest true-positives are **Annex A (§11.2.2 tables)** and **§3.3** ("mandatory standards … as well as recommended guidelines for best practice").

**Findings by category:** Systemic 6 · Missed (incl. RECOMMENDS/DEFERS_TO) 14 · Wrong-relation/modality 5 · Over-extraction/noise 3 · Thin 2.

---

## 2. Systemic findings (fix once, applies broadly)

| # | Category | Issue | Suggested fix |
|---|---|---|---|
| S1 | Missed / Wrong-modality | RECOMMENDS never used; MANDATES only 17×. shall/should split not in graph. | Add `Provision RECOMMENDS <SecurityControl\|RiskManagement\|Policy>` for genuine "should" recommendations (see M1–M4). Optionally also add `Provision MANDATES <control>` alongside `CIIO IMPLEMENTS` for "shall implement" clauses so modality is queryable. |
| S2 | Wrong-modality | Annex A (§11.2.2, `::table::0/1/2`) encoded as binding. | Replace/augment the mandatory relations with `Provision RECOMMENDS …`; add `ComputerSystem EXCLUDED_FROM_SCOPE Audit` (Annex A "need not be included in the scope of cybersecurity audits"). |
| S3 | Missed / pipeline | citation_id collision `::1..::6` (footnote vs section header) → footnote refs silently dropped. | Re-key footnotes (e.g. `CCoP 2.0::fn-3`) and extract them; add the `DEFERS_TO` edges in S4. Pipeline-level fix. |
| S4 | Missed | DEFERS_TO under-used (2×). | Add `CIIO DEFERS_TO ExternalStandard` (or `CodeOfPractice DEFERS_TO ExternalStandard`) for: §3.4.1 (CSA SBD Framework), fn-1 (CSA RA Guide), fn-2 (CSA TM Guide), fn-3 (SBD Framework), fn-4 (NIST Zero-Trust), fn-6 (Purdue/PERA). CREST (fn-5 / §5.15.3) → Certification, already partly covered. |
| S5 | Mis-typed (leaf) | Entity names == type names; leaf concepts flattened. | If not intended: give distinct canonical names under the same type (e.g. name="defence-in-depth" type=DesignPrinciple; name="MFA" type=AccessControlMechanism; name="DNSSEC" type=Cryptography). Confirm design intent first. |
| S6 | Missed (subtype under-use) | `PrivilegedAccount` (0×) though §5.3 is entirely about it; `Server` (0×) though §5.4 is about the domain controller. | Add `AccessControlMechanism PROTECTS CII` is present but add subtype nodes: §5.3 → involve PrivilegedAccount; §5.4 → domain controller as Server. |

---

## 3. Per-clause findings (ranked by value)

Legend: **MISS**=missed triple, **REC**=RECOMMENDS missed, **WRONG**=wrong relation, **OVER**=over-extraction, **THIN**=under-extracted.

| # | citation_id | Cat | Issue | Suggested fix (concrete triple) |
|---|---|---|---|---|
| M1 | `::11.2.2::table::0` | REC | "The CIIO **should** adopt the SBD Framework / defence-in-depth / least-privilege / segregation" — Annex A guidance encoded as binding `CIIO IMPLEMENTS SecurityControl`. | Replace with `Provision RECOMMENDS SecurityControl` + `Provision RECOMMENDS Policy`; add `CIIO DEFERS_TO ExternalStandard` (SBD Framework). |
| M2 | `::11.2.2::table::1` | REC | "should also adopt … defence-by-diversity … zero-trust … wireless LAN" as `APPLIES_PRINCIPLE`/`PROTECTS` (binding). | Add `Provision RECOMMENDS SecurityControl`; keep principle content but as recommendation, not `APPLIES_PRINCIPLE` (which reads as adopted). |
| M3 | `::11.2.2::table::2` | REC | "The CIIO **should** conduct threat hunting … should include … should analyse" encoded as `CIIO CONDUCTS ThreatHunting` (binding). | Add `Provision RECOMMENDS RiskManagement` / recommendation framing; distinguish from the identical binding §6.3.x clauses. |
| M4 | `::3.3` | REC | Text explicitly splits *"mandatory standards for compliance, as well as **recommended guidelines** for best practice"* — only `Provision MANDATES Policy` captured. | Add `Provision RECOMMENDS Policy` (the recommended-guidelines half). |
| M5 | `::11.2.2` | MISS/OVER | w=709 block swallowed all of Annex A but yields only 2 generic `SecurityControl/Cryptography PROTECTS CII`. Both the binding DNSSEC-signing shall and the Annex A guidance are thin. | Add `ComputerSystem EXCLUDED_FROM_SCOPE Audit` (Annex A not in audit scope); the DNSSEC-signing shall → `Cryptography PROTECTS CII` ok; consider `Provision MANDATES` for the signing requirement. |
| M6 | `::3` (fn-3, w=13) | MISS/OVER | "For Security-by-Design Framework, the CIIO **shall refer to** CSA's website" — collision hides it; shown triple `CIIO IMPLEMENTS RiskManagement` is actually the §3 header's, not the footnote's. | Re-key footnote; add `CIIO DEFERS_TO ExternalStandard` (SBD Framework). |
| M7 | `::4` (fn-4, w=21) | MISS/OVER | "For … NIST: Planning for a Zero Trust Architecture, the CIIO can refer to …" — footnote unextracted (collision with §4 header's `HAS_ASSET`/`DELIVERS`). | Re-key; add `CIIO DEFERS_TO ExternalStandard` (NIST). |
| M8 | `::1`,`::2` (fn-1/2) | MISS | fn-1 "CSA's Guide to Conducting Risk Assessment", fn-2 "CSA's Guide to Cyber Threat Modelling" — both unrepresented. | Re-key; add `CIIO DEFERS_TO ExternalStandard` for each. |
| M9 | `::6` (fn-6, w=25) | MISS/OVER | "Field devices include … refer to level 0 of the Purdue Enterprise Reference Architecture (PERA)" — footnote unextracted (collision with §6 header's Monitoring/DETECTS/TARGETS). | Re-key; add `CIIO DEFERS_TO ExternalStandard` (Purdue/PERA). |
| M10 | `::3.4.1` | MISS | "The CIIO **shall adopt** the Security-by-Design Framework established by CSA" — only `CIIO IMPLEMENTS SecurityByDesign`. | Add `CIIO DEFERS_TO ExternalStandard` (SBD Framework). |
| M11 | `::5.3` (+5.3.1) | MISS | Whole subsection is about **privileged accounts**; `PrivilegedAccount` subtype never used. Also "move about in the network" = lateral movement (AttackConcept). | Add a triple involving `PrivilegedAccount` (e.g. `AccessControlMechanism PROTECTS CII` is generic; better: keep but ensure PrivilegedAccount appears as a concept). Consider `SecurityControl REDUCES AttackConcept` for lateral movement. |
| M12 | `::5.4` | MISS | Clause is about the **domain controller** (a Server per ontology) as "primary target"; `Server` never captured. | Add `CyberThreatActor TARGETS CII` is present; add domain-controller as `Server` concept (subtype). |
| M13 | `::5.16` / `5.16.1(c)` | MISS | Attack-simulation plan artifact (`AttackSimulationPlan`) and blue/red/purple teams present; plan artifact not linked. | Optional: the ontology marks `AttackSimulationPlan` an intentional orphan — acceptable to skip. Verify intent. |
| M14 | `::6.4` | MISS | "share … information … **within the sector and with the Commissioner**" — sector information-sharing; only `CIIO REPORTS Regulator`. | Acceptable; optionally `CodeOfPractice OVERLAPS_WITH RegulatoryFramework` is not right here — leave as is. (low) |
| W1 | `::3` header (w=39) | WRONG | `CIIO IMPLEMENTS RiskManagement` for the GOVERNANCE section intro is a fine generic, but note it is duplicated onto fn-3 via the collision (S3). | No change to the header triple; fix via S3 re-keying. |
| W2 | `::3.2.1(f)` | WRONG | "Process hazard analysis methodology to reduce … impact on safety" → `SafetyMechanism MITIGATES CybersecurityRisk`. Process hazard analysis is a risk-assessment activity, not a SafetyMechanism. | Prefer `CIIO IMPLEMENTS RiskAssessment` (already present) + drop or re-scope the SafetyMechanism triple; SafetyMechanism belongs in §10.2.4. |
| W3 | `::8.1.1` | WRONG | Clause establishes a **backup/restoration** plan; extra `DisasterRecoveryPlan RECOVERS CII` over-reaches (DRP is §8.2). | Drop `DisasterRecoveryPlan RECOVERS CII`; keep `Backup RECOVERS CII`. |
| W4 | `::3.1.1` | WRONG (minor) | `OrganisationalRole ASSIGNED_TO CIIO` — text says responsibility assigned to *a person*, not to the CIIO org. Type-valid (CIIO is Actor) but semantically the filler should be a generic Actor/personnel. | Low priority; acceptable given no generic "Person" entity. |
| W5 | `::10.2` preamble | WRONG (minor) | `SafetyMechanism MITIGATES CybersecurityRisk` from "fail-safe mechanisms" is fine; but `ControlSystem DEPENDS_ON FieldController` reads backwards-ish (DCS/SCADA *control* field controllers). DEPENDS_ON is defensible (control loop). | Acceptable; note for review. |
| O1 | `::5` (fn-5, CREST) | OVER | Shown triples `CIIO IMPLEMENTS SecurityControl` + `PROTECTS CII` are the §5 header's (collision). The CREST footnote itself only describes the accreditation body. | Re-key; footnote legitimately near-empty, or `PenetrationTester HAS_CERTIFICATION Certification` (CREST). |
| O2 | `::4` header | OVER (none) | `CII HAS_ASSET CIIAsset` + `CII DELIVERS EssentialService` are correct for the Identification intro — flagged only because they are duplicated onto fn-4. | No change; fix via S3. |
| O3 | `::10.1.2::table::0` | OVER (dup) | The four `Provision DEFINES …` triples are duplicated verbatim on both `::10.1.2` and `::10.1.2::table::0`. | De-dup: keep DEFINES on the parent clause only, or split definitions per row. |
| T1 | `::3.2.4(f)` | THIN | "Progress status of the treatment plan" → 0 triples. The ontology has `HAS_STATUS` (used 0× corpus-wide) and `ComplianceStatus`. | Marginal — status of a treatment plan ≠ CII compliance status; acceptable to leave empty. Note HAS_STATUS is unused corpus-wide. |
| T2 | `::2.1.2(b)` | THIN | "Set out the timeline(s) for implementing the actions" → 0 triples. | Optional `Provision HAS_DEADLINE Deadline`. Low. |

---

## 4. Lower-priority "should" clauses (RECOMMENDS candidates, section preambles)

These carry "should" but each has a binding `shall` sub-clause, so encoding RECOMMENDS is optional (do only if modality completeness is wanted): §2.1, §5.2, §5.6, §5.10, §5.12, §5.13, §5.14, §6.4, §7.1, §7.2, §8.1, §10.2. **Do NOT** add RECOMMENDS to §3.8.3(c) — its "should" is a conditional ("should the external party commission its own audit"), not a recommendation.

---

## 5. What is NOT a defect (checked, do not re-flag)

- No Φ / domain-range violations found. Subtype-based fillers (SystemActor SEGREGATES SystemActor §5.13.2; OrganisationalRole SUPERVISES RiskAssessment §9.2.3; OTSystem CONNECTED_TO EnterpriseNetwork §10.2) are all valid and are actually *better* than generic parents.
- Zero-triple clauses in §1.2.x (legal interpretation), section headers, and boilerplate (§1.1.1, §1.4.2/4/6) are legitimately empty.
- The heavy use of `SecurityControl/AccessControlMechanism PROTECTS CII` is correct per the ontology's PROTECTS(→asset) vs MITIGATES(→risk/threat) split.
