# Ontology Design — Phase 1a: Entities (E)

**Status:** DRAFT for approval. Hand-identified by reading the corpus (not scripted).
**Sources read:** CCoP 2.0 (full body + §1.2.1 glossary [56] + §10.1.2 OT glossary [8]),
Auditing Guidelines (glossary [10] + §2), Threat Modelling Guide, Risk Assessment Guide,
Cybersecurity Act 2018 (sections + First Schedule sectors), Security By Design (structure +
Annex B roles + Annex C glossary), Response-to-Feedback clarifications, and the OMD POC schemas.

**Method:** top-down from the CCoP domain structure (§1 scope, §2 audit, §3 governance,
§4 identification, §5 protection, §6 detection, §7 response, §8 resilience, §9 training,
§10 OT, §11 domain-specific) + the 18 benchmark distinctions; bottom-up from every glossary
term and clause subject/object. Entities are the "things" that appear as **subjects or objects
of obligations** — the nouns the graph must link.

Design choice: **types, not instances.** A domain controller, DNS server, and OT historian are
all `Server ⊑ ComputerSystem` — the specific make is a node property, not a new type. Hierarchy
(`⊑`) and disjointness (`⊥`) are declared so Phase 1c (OWL/SHACL) can reason over them.

Model: strictly the **OMD-GraphRAG paper §3.1** + the POC — **NOT** the Phase-11 Compliance-Unit
approach. The ontology is `S = (E, R, Φ)`: entity types `E`, relation types `R`, and a
type-constraint function `Φ(r) = (dom(r), range(r))`. Knowledge = flat typed triples
`(head, relation, tail)`, both ends entity types, post-hoc type-checked against Φ (POC `type_ok`).
`Obligation` is a **plain entity type** (as in the POC `omd_b01` schema), reached via
`CIIO –HAS_OBLIGATION→ Obligation`. There are no reified obligations, modality nodes, or CUs.

---

## Category 1 — Regulatory & legal (the compliance frame)

| Entity type | Notes / instances | Benchmarks |
|---|---|---|
| `Regulator` | CSA, Commissioner (+ Deputy/Assistant), Sector Lead, licensing officer | B18, B23 |
| `Legislation` | Cybersecurity Act 2018; CII Regulations 2018 | B01, B22, B23 |
| `CodeOfPractice` | CCoP 2.0 (this Code); Standards of Performance | B02, B23 |
| `Provision` | a clause/section — the regulatory unit itself | all |
| `Obligation` | a duty a clause imposes (plain entity, as in POC `omd_b01`); reached via `CIIO –HAS_OBLIGATION→ Obligation` | B02, B06 |
| `Waiver` | §11(7) waiver — a granted instrument (entity); connects via `Commissioner–GRANTS→Waiver`, `Waiver–WAIVES→Provision`, `Waiver–APPLIES_TO→CIIO` | **B22** |
| `Direction` | written direction under §12(1) | B22 |
| `Designation` | §7 CII designation act | **B01** |
| `Exemption` | Act §46 exemption | B22 |
| `ExternalStandard` | reference *frameworks*: NIST, ISO/IEC 27001, OWASP, MITRE ATT&CK, Purdue Model | B05, B21, B23 |
| `Certification` | professional/accreditation *credentials*: CISA, CRISC, CREST (split from ExternalStandard) | **B12**, B05 |
| `RegulatoryFramework` | MAS-TRM, IM8 (for multi-regulator overlap) | **B23** |

## Category 2 — Actors & roles (who bears duties)

All types below are `⊑ Actor` (abstract superclass, for typing obligations' subjects).
`Person` is dropped as too vague — the duty-bearing thing is always the **role**; a
person/employee/individual is a *filler* of an `OrganisationalRole`, not its own type.

| Entity type | Notes / instances | Benchmarks |
|---|---|---|
| `CIIO` | owner of the CII (the primary duty-holder) | all |
| `Board` | board of directors / equivalent body | B18 |
| `SeniorManagement` | incl. accountable management | B18 |
| `OrganisationalRole` | a named role with assigned responsibility (replaces vague `Person`; fillers = personnel/employee) | B18 |
| `CISO` | Chief Information Security Officer | B18 |
| `IncidentResponseTeam` | CIRT | **B24** |
| `CrisisTeam` | crisis communication / crisis management team | B24 |
| `AttackSimTeam` | red team, blue team, purple team | B05 |
| `ThirdParty` | vendor, external party, service provider, outsourced provider | B18 |
| `CloudServiceProvider` | cloud computing service provider | B18 |
| `Auditor` | cybersecurity auditor (CSA-approved) | **B12, B13** |
| `PenetrationTester` | certified pen-tester / accredited provider | B05 |
| `SystemActor` | System Owner, System Administrator, Database Administrator, System Custodian | B18 |
| `ProjectRole` | SBD roles: Steering Committee, Project Manager, Developer, Security Officer (Annex B) | B18 |
| `RiskRole` | Head of Organisation, Business Owner, Risk Management Function, Risk Owner, Cybersecurity Function | B08, B18 |
| `LawEnforcement` | law enforcement agency (incident engagement) | B24 |
| `CyberThreatActor` | adversary / attacker | B09, B24 |

## Category 3 — Systems, assets & boundaries

| Entity type | Notes / instances | Benchmarks |
|---|---|---|
| `CII` | the critical information infrastructure | all |
| `CIIAsset` | components: hardware, software, network infra | B01, B05 |
| `ITSystem` | `⊑ ComputerSystem` | **B04** |
| `OTSystem` | `⊑ ComputerSystem`; OT CII; **`ITSystem ⊥ OTSystem`** | **B04** |
| `ComputerSystem` | generic computer/computer system | B01, B04 |
| `Network` | network / network segment | B05 |
| `EnterpriseNetwork` | the shared corporate network (**not** in-scope by default) | **B01, B04** |
| `CloudSystem` | cloud computing system (public/private/hybrid) | B01 |
| `Database` | database, database tier | B05 |
| `Application` | software application, web application, firmware, programme code | B05 |
| `Server` | domain controller, DNS server, alarm server, OT historian, management server | B05 |
| `Endpoint` | workstation, console, HMI, portable computing device, removable storage media | B05 |
| `NetworkDevice` | appliance, field device, network device | B05 |
| `FieldController` | PLC, RTU (OT); `⊑ NetworkDevice` | B04, B05 |
| `ControlSystem` | SCADA, DCS, Safety Instrumented System (SIS) | B04 |
| `PhysicalProcess` | the physical process an OT CII monitors/controls (§10.1.2) | B04 |
| `DigitalBoundary` | cyber operating environment; perimeter/trust boundary; DMZ | **B01** |
| `PhysicalSite` | primary/secondary hosting locations | B01 |
| `EssentialService` | the service the CII delivers (Act §2) | **B01** |
| `Sector` | `⊑ EssentialService` — the 11 Act First-Schedule sectors (each also typed `EssentialService`): Energy, Info-comms, Water, Healthcare, Banking & Finance, Security & Emergency, Aviation, Land Transport, Maritime, Government, Media. `CII –DELIVERS→ EssentialService –IN_SECTOR→ Sector` | B01, B23 |

## Category 4 — Security controls & mechanisms

| Entity type | Notes / instances | Benchmarks |
|---|---|---|
| `SecurityControl` | generic control/measure/mechanism | B05, B07 |
| `MitigatingControl` | risk-mitigating / engineering (non-digital) control | B08, B09 |
| `CompensatingControl` | alternative control (audit) | B12, B22 |
| `AccessControlMechanism` | authentication, authorisation, MFA, privileged access | B05 |
| `SecurityConfigurationBaseline` | system hardening baseline (§5.9.2) | **B05** |
| `NetworkControl` | segmentation, firewall, WAF, IDS/IPS, data-flow control | B05 |
| `Cryptography` | encryption, cryptographic key, DNSSEC, hashing | B05 |
| `MalwareProtection` | anti-malware / signatures | B05 |
| `Patch` | security patch / update | B05 |
| `Backup` | backup copy / restoration | B24 |
| `Log` | logs, log retention (firewall/DNS/proxy/NIDS) | B05, B13 |
| `SecurityArchitecture` | multi-tier architecture, defence-in-depth layering | B05 |
| `SafetyMechanism` | fail-safe, interlock (OT) | B04, B05 |

## Category 5 — Processes & activities

| Entity type | Notes / instances | Benchmarks |
|---|---|---|
| `RiskManagement` | framework; risk identification / analysis / evaluation / response | B08, B09, B10 |
| `RiskAssessment` | the assessment activity (`⊑ RiskManagement`) | B08–B10 |
| `ThreatModelling` | scope → decompose → identify → attack-model | B07, B09 |
| `ThreatHunting` | proactive search | B07 |
| `ThreatIntelligence` | intel gathering + information sharing | B07, B23 |
| `VulnerabilityAssessment` | identify/track/remediate vulnerabilities | B07 |
| `PenetrationTesting` | authorised intrusion test | B05 |
| `AttackSimulation` | red/purple teaming exercise | B05 |
| `Audit` | cybersecurity audit (§15) | **B12, B13** |
| `AuditScope` | the defined scope an audit must cover (§15; Auditing §6.3) | **B12, B13** |
| `Remediation` | audit-finding remediation | **B14** |
| `ChangeManagement` | change identification/authorisation/validation | B05 |
| `IncidentManagement` | detection → containment → recovery → post-incident review | **B24** |
| `Monitoring` | monitoring & detection, logging | B05, B24 |
| `CybersecurityExercise` | scenario-based exercise | B24 |
| `SecurityByDesign` | SDLC-integrated security (SBD phases: Initiation…Disposal) | B05 |
| `Training` | awareness programme + skills training | B18 |

## Category 6 — Artifacts, documents & plans

| Entity type | Notes / instances | Benchmarks |
|---|---|---|
| `Policy` | policy / standard / guideline / procedure | B02 |
| `Contract` | outsourcing agreement / terms with a third party (§3.8) | B18 |
| `RiskRegister` | risk register (§3.2.4) | B08, B09 |
| `RiskAssessmentReport` | + cybersecurity risk profile | B08 |
| `AssetInventory` | CII asset inventory + network topology diagram | B01 |
| `IncidentResponsePlan` | Cybersecurity Incident Response Plan | **B24** |
| `CrisisCommunicationPlan` | (§7.2) | B24 |
| `BusinessContinuityPlan` | BCP | B24 |
| `DisasterRecoveryPlan` | DRP (+ RTO/RPO) | B24 |
| `RemediationPlan` | audit finding remediation plan | **B14** |
| `AuditReport` | audit report / evidence | **B13** |
| `ThreatModel` | the threat-model artifact | B07 |
| `AttackSimulationPlan` | red/purple team plan | B05 |
| `RiskAppetite` | risk appetite / risk tolerance / thresholds | B08 |

## Category 7 — Risk & threat concepts

| Entity type | Notes / instances | Benchmarks |
|---|---|---|
| `CybersecurityRisk` | risk = f(Likelihood, Impact) | B08–B10 |
| `ResidualRisk` | risk after controls | **B09** |
| `RiskScenario` | scenario in the risk register | B09, B10 |
| `Likelihood` | discoverability/exploitability/reproducibility | B10 |
| `Impact` | magnitude of harm (nation/org/individual) | B10 |
| `CybersecurityThreat` | threat / threat event / threat vector | B07, B09 |
| `TTP` | tactics, techniques & procedures | B07 |
| `Vulnerability` | weakness in design/implementation/operation | B07 |
| `CybersecurityIncident` | incident / cybersecurity event | B24 |
| `AttackConcept` | attack surface, attack vector, kill-chain, crown jewels, lateral movement | B07 |
| `Malware` | malware, IOC (indicator of compromise) | B05, B24 |

## Category 8 — Governance & compliance concepts

| Entity type | Notes / instances | Benchmarks |
|---|---|---|
| `DesignPrinciple` | defence-in-depth, least privilege, segregation of duties, defence-by-diversity, zero-trust | B05, B06 |
| `ComplianceStatus` | compliant / non-compliant / not-applicable / insufficient | **B02, B03** |
| `Condition` | the "if/where necessary…" qualifier on an obligation | **B03** |
| `ComplianceGap` | a gap / area of non-compliance | **B07, B14** |
| `Deadline` | recurring-requirement interval; Compliance/Effective/Designation Date | B03 |
| `OrganisationalStructure` | roles + authority + reporting lines | B18 |

---

## Benchmark coverage check (every distinction must be expressible)

- **B01 applicability** → `CII / DigitalBoundary / EnterpriseNetwork / EssentialService / Designation / Sector` ✅
- **B04 IT/OT** → `ITSystem ⊥ OTSystem` disjointness ✅
- **B22 waiver** → `Waiver / Exemption / Direction / CompensatingControl` ✅
- **B23 multi-regulator** → `Regulator / RegulatoryFramework / ExternalStandard` ✅
- **B24 incident** → `IncidentResponsePlan / CIRT / CybersecurityIncident / CrisisTeam` ✅
- **B12/B13 audit** → `Audit / Auditor / AuditReport / AuditEvidence` ✅
- **B14 remediation** → `RemediationPlan / ComplianceGap / Remediation` ✅
- **B18 responsibility** → `OrganisationalRole / CIIO / SystemActor / RiskRole` (accountability is a *relation*, 1b) ✅
- **B21 over-specification** → needs a `DOES_NOT_SPECIFY` *predicate* over `Provision`/`SecurityControl` (a relation, 1b) ⚠️
- **B02/B03 classification/conditional** → `Obligation / ComplianceStatus / Condition` ✅

## Open questions for you
1. **Granularity** — is ~65 typed entities across 8 categories the right altitude, or do you want it coarser (merge, e.g., all Category-4 controls into `SecurityControl`) or finer (split, e.g., every §5 control family as its own type)?
2. **IT ⊥ OT** is the one hard disjointness the benchmarks demand (B04). Any others to lock (e.g., `Waiver ⊥ Obligation`)?
3. **Sector as entity vs property** — keep the 11 essential-service sectors as a `Sector` type, or as an enum property on `EssentialService`?
4. Anything you expected to see that's missing before I move to **Relations (R)**.
