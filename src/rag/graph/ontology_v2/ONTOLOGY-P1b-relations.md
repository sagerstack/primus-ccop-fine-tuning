# Ontology Design — Phase 1b: Relations (R)

**Status:** DRAFT for approval. Derived by reading the clauses (same corpus as 1a).
Model: strictly OMD-GraphRAG §3.1 + the POC — **no Compliance Units**. Every relation is a
**typed edge between two entity types** `(head_type –REL→ tail_type)`; its `(dom, range)` is the
Φ entry checked post-hoc at extraction (`type(h)∈dom(r) ∧ type(t)∈range(r)`, else discarded).
Knowledge is flat typed triples — the cross-document bridge is shared canonical entities
resolving to the same node (the POC `canon`/`SYN` mechanism), not any reified obligation layer.

---

## 1. Applicability & scope  (B01, B03)

| Relation | domain → range | Reading / source |
|---|---|---|
| `APPLIES_TO` | Provision/CodeOfPractice → CII, CIIO, ITSystem, OTSystem | "this Code shall apply to all CII" (§1.2.5, §10.1.1, §11.1.1) |
| `DELIVERS` | CII → EssentialService | Act §2 essential-service delivery |
| `IN_SECTOR` | EssentialService → Sector | Act First Schedule sectors |
| `WITHIN_BOUNDARY` | CIIAsset, ComputerSystem → DigitalBoundary | RtF-2.2 "within the digital boundary" |
| `DETERMINED_BY` | DigitalBoundary → Regulator | RtF-2.2 "jointly determined between CSA, CIIOs, Sector Leads" |
| `DESIGNATES` | Regulator → CII | Act §7 designation |
| `CONNECTED_TO` | CII ↔ EnterpriseNetwork, Network | §5.6, §10.2 connectivity |
| `EXCLUDED_FROM_SCOPE` | EnterpriseNetwork, ComputerSystem → Audit, CII | Annex A / §15 "need not be in audit scope" |
| `CONDITIONED_ON` | Obligation, Provision → Condition | §5.6.2 "where necessary for operating the CII" |

## 2. Classification  (B04)

| Relation | domain → range | Reading |
|---|---|---|
| `CLASSIFIED_AS` | CII → ITSystem, OTSystem | §5.12.4 "a CII which is an IT system", §10.1.1 "OT CII" |
| `HAS_ASSET` | CII → CIIAsset | §4.1 asset inventory |
| `DEPENDS_ON` | CIIAsset → CIIAsset, ComputerSystem | §4.1.1(e) dependencies |

## 3. Duty, responsibility & obligation  (B02, B06, B18)

| Relation | domain → range | Reading |
|---|---|---|
| `HAS_OBLIGATION` | Actor (CIIO…) → Obligation | POC `omd_b01` relation; a duty-bearer has a duty |
| `RESPONSIBLE_FOR` | Actor, OrganisationalRole → Process, CIIAsset, CII | §3.1.1 roles assigned responsibility |
| `ACCOUNTABLE_FOR` | CIIO, SeniorManagement, Board → CII, CybersecurityRisk | §3.7.1/§3.8.1 "remain responsible and accountable" |
| `ASSIGNED_TO` | OrganisationalRole → Actor | §3.1.1 responsibility assigned to a person |
| `OVERSEES` | Board, SeniorManagement → CybersecurityRisk, CII | §3.1.2/§3.1.3 oversight |
| `SEGREGATES` | OrganisationalRole ↔ OrganisationalRole | §3.5.1(c)/§5.13.2 segregation of duties |
| `DELEGATES_TO` | CIIO → ThirdParty, CloudServiceProvider | §3.8 outsourcing (duty stays with CIIO) |
| `SUPERVISES` | OrganisationalRole, CIIO → Process, OrganisationalRole, ThirdParty | §9.2.3/9.2.4 certified individual supervises the group; §5.15.4 vendor supervision |
| `HAS_CERTIFICATION` | OrganisationalRole, Auditor, PenetrationTester, ThirdParty → Certification | §9.2.4 CISA, §5.15.3 CREST |

## 4. Requirements & controls  (B05, B07, B21)

| Relation | domain → range | Reading |
|---|---|---|
| `MANDATES` | Provision → SecurityControl, Process, Artifact | **`shall`** requirement (§ glossary: mandatory) — the modality split, B02 |
| `RECOMMENDS` | Provision → SecurityControl, Process, Artifact | **`should`** requirement (§ glossary: recommended) — B02 |
| `IMPLEMENTS` | CIIO → SecurityControl, Process | §5.x "the CIIO shall implement…" |
| `PROTECTS` | SecurityControl → CII, CIIAsset | protect an *asset* (Φ-distinct by range) |
| `MITIGATES` | SecurityControl, MitigatingControl → CybersecurityRisk, CybersecurityThreat | mitigate a *risk/threat* |
| `ADDRESSES` | SecurityControl → Vulnerability | address a *weakness* (§5.14) |
| `APPLIES_BASELINE` | SecurityConfigurationBaseline → CIIAsset | §5.9.1 hardening baseline |
| `DEFERS_TO` | Provision, CodeOfPractice → ExternalStandard, RegulatoryFramework | **RtF-11.28** "may take reference from NIST"; §5.12.5 OWASP |
| `DOES_NOT_SPECIFY` | Provision → literal value/attribute | **B21** guard — the one relation with a literal range; the Code is silent on a specific (e.g. password length) |

## 5. Risk  (B08, B09, B10)

| Relation | domain → range | Reading |
|---|---|---|
| `IDENTIFIES` | RiskAssessment, ThreatModelling → CybersecurityRisk, CybersecurityThreat, Vulnerability | §3.2.2 risk identification |
| `HAS_LIKELIHOOD` | CybersecurityRisk → Likelihood | RA §3.1 Risk = f(Likelihood, Impact) |
| `HAS_IMPACT` | CybersecurityRisk → Impact | RA §3.1 |
| `EXPLOITS` | CybersecurityThreat, CyberThreatActor → Vulnerability | RA/TM threat event exploits vulnerability |
| `TARGETS` | CyberThreatActor → CIIAsset, CII | TM crown-jewels/kill-chain |
| `MITIGATED_BY` | CybersecurityRisk → SecurityControl | §3.2.4(c) existing measures |
| `LEAVES_RESIDUAL` | SecurityControl → ResidualRisk | §3.2.1(e) residual-risk thresholds |
| `RECORDED_IN` | CybersecurityRisk, RiskScenario → RiskRegister | §3.2.4 |
| `ACCEPTED_BY` | ResidualRisk → SeniorManagement, RiskRole | §3.2 "accepted at appropriate level" |

## 6. Detection, response & recovery  (B24)

| Relation | domain → range | Reading |
|---|---|---|
| `DETECTS` | Monitoring, Log → CybersecurityEvent, CybersecurityIncident | §6.2 monitoring & detection |
| `RESPONDS_TO` | IncidentResponsePlan, CIRT → CybersecurityIncident | §7.1 |
| `ACTIVATES` | CybersecurityIncident → IncidentResponsePlan, CIRT, CrisisCommunicationPlan | §7.1 thresholds trigger |
| `RECOVERS` | DisasterRecoveryPlan, BusinessContinuityPlan, Backup → CII, EssentialService | §8 resilience |
| `REPORTS` | CIIO → Regulator | §6.4.2 / Act §14 incident reporting |
| `VALIDATES` | CybersecurityExercise → IncidentResponsePlan, BCP, DRP, CrisisCommunicationPlan | §7.3.1 |

## 7. Audit, remediation & waiver  (B12, B13, B14, B22)

| Relation | domain → range | Reading |
|---|---|---|
| `AUDITS` | Auditor → CII | §15 audit; Auditing Guidelines |
| `PRODUCES` | Audit → AuditFinding, AuditReport | Auditing §6 |
| `COVERS` | Audit → AuditScope, Provision | Auditing §6.3 "the audit shall cover…" |
| `CONTAINS` | AuditReport, Artifact → (element/topic) | Auditing §6.7 report format |
| `REQUIRES_EVIDENCE` | Audit, AuditCriteria → AuditEvidence | **B13** audit evidence |
| `ISSUES` | Regulator → CodeOfPractice, StandardOfPerformance, Direction | Act §11 "Commissioner may issue…" |
| `APPROVES` | Regulator → Auditor, RiskAssessmentReport, Waiver | §5 auditor approval; §3.7 RA review |
| `APPOINTS` | Regulator → Auditor, OrganisationalRole | Act §22 appoint technical expert; §5 |
| `REMEDIATED_BY` | ComplianceGap, AuditFinding → RemediationPlan | **B14** §2.1 |
| `COMPENSATED_BY` | Provision/Requirement → CompensatingControl | audit compensating control |
| `GRANTS` | Regulator → Waiver | §1.6.1 |
| `WAIVES` | Waiver → Provision, Obligation | §11(7) |
| `EXEMPTS` | Legislation → Actor, ComputerSystem | Act §46 exemption |

## 8. Structural / cross-reference (concept-mediated — no clause→clause edges)

Relatedness between clauses is handled entirely by the concept graph (shared/1-hop
concepts + `INVOKES`); there are **no clause→clause edges**. `DEFINES` is a clause→concept
edge (glossary); `OVERLAPS_WITH` is concept→concept.

| Relation | domain → range | Reading |
|---|---|---|
| `DEFINES` | Provision → (any entity) | §1.2.1 glossary defines an entity |
| `OVERLAPS_WITH` | CodeOfPractice → RegulatoryFramework | **B23** CCoP + MAS-TRM/IM8 overlap |

> **Deferred (2026-07-08):** `REFERS_TO` / `CLARIFIES` (explicit clause→clause citation +
> RtF→CCoP clarification) were **dropped for now**. They don't affect POC Channel-I retrieval
> (which scores on concept overlap, never clause edges); their value is post-retrieval citation
> following / answer grounding. To revisit as an optional generation-time overlay later.

---

## Benchmark coverage (relations that carry each distinction)

- **B01** `APPLIES_TO`, `WITHIN_BOUNDARY`, `DETERMINED_BY`, `EXCLUDED_FROM_SCOPE`, `DELIVERS`, `IN_SECTOR` ✅
- **B02** `MANDATES` vs `RECOMMENDS` (the shall/should split) ✅
- **B03** `CONDITIONED_ON` ✅
- **B04** `CLASSIFIED_AS` over `ITSystem ⊥ OTSystem` ✅
- **B05** `MANDATES`/`RECOMMENDS`, `IMPLEMENTS`, `APPLIES_BASELINE`, `DEFERS_TO` ✅
- **B18** `RESPONSIBLE_FOR`, `ACCOUNTABLE_FOR`, `ASSIGNED_TO`, `SEGREGATES` ✅
- **B21** `DOES_NOT_SPECIFY` + `DEFERS_TO` (silent → defers to external) ✅
- **B22** `GRANTS`, `WAIVES`, `EXEMPTS`, `COMPENSATED_BY` ✅
- **B23** `OVERLAPS_WITH`, `DEFERS_TO` ✅
- **B24** `RESPONDS_TO`, `ACTIVATES`, `RECOVERS`, `REPORTS` ✅
- **B08–B10** `IDENTIFIES`, `HAS_LIKELIHOOD/IMPACT`, `MITIGATED_BY`, `LEAVES_RESIDUAL`, `ACCEPTED_BY` ✅
- **B12–B14** `AUDITS`, `PRODUCES`, `REQUIRES_EVIDENCE`, `REMEDIATED_BY` ✅

## Resolutions (approved 2026-07-08)
1. **Keep `PROTECTS`/`MITIGATES`/`ADDRESSES` distinct** — Φ-separated by object type (asset / risk-threat / vulnerability). No retrieval impact: the POC scores on shared *entities* and traverses edges relation-agnostically; the labels add precision for the judge/generation step and typed queries.
2. **`DOES_NOT_SPECIFY` allowed** — the single relation with a literal range, for the B21 over-specification guard.
3. **Modality split into `MANDATES` (shall) / `RECOMMENDS` (should)** relations — no `modality` property, no CU.
4. **`CLARIFIES` kept distinct** from `REFERS_TO`.
