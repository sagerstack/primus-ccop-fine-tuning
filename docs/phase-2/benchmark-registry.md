# V2 Benchmark Registry

> Implements benchmark audit decisions from spec Section 2 of `docs/superpowers/specs/2026-04-01-ground-truth-v2-design.md`

**Status:** V2 — approved post-audit  
**Last updated:** 2026-04-01  
**Scoring infrastructure reference:** Phase 02.4 LLM Judge Redesign (universal 2-dimension system)

---

## Overview

18 benchmarks targeting Risk Managers in CII organizations, reduced from 21 through structured audit. All questions must be scenario-grounded and practitioner-framed.

| Total benchmarks | Rule-based | LLM-judge | Target test cases |
|------------------|------------|-----------|-------------------|
| 18 | 4 (B1, B2, B4, B21) | 14 (all others) | ~435 |

---

## V1 Audit: Summary Findings

All 21 v1 benchmarks evaluated against 5 criteria: CIIO Relevance, Distinctiveness, Scorer Alignment, Question Feasibility, Evaluation Clarity.

### V1 Quality Assessment

| Benchmark | Cases | kf_issues | Abstract Qs | Decision | Key Finding |
|-----------|-------|-----------|-------------|----------|-------------|
| B1 — CCoP Applicability | 8 | 3/8 | 5/8 | Keep + Refocus | Too many definitional Qs; extend with CCoP 1.0 evolution, IM8, ESCI/FDI |
| B2 — Compliance Classification | 7 | 1/7 | 0/7 | Keep + Refocus | Good base; needs sector-specific IT/OT nuance |
| B3 — Conditional Compliance | 7 | 0/7 | 0/7 | Keep | Strongest v1 benchmark — all scenario-grounded, zero kf issues |
| B4 — IT/OT Classification | 7 | 0/7 | 1/7 | Keep + Refocus | Needs boundary reasoning across sectors, not just definitional distinctions |
| B5 — Control Requirement | 7 | 0/7 | 7/7 | Keep + Refocus | All abstract "explain Clause X" format — practitioner reframing required |
| B6 — Control Intent | 7 | 4/7 | 7/7 | Keep + Refocus | Weakest question quality; kf placeholders and no scenario grounding |
| B7 — Gap Identification | 8 | 0/8 | 0/8 | Keep | Strong; all scenario-grounded; absorbs B17 as scenario type |
| B8 — Gap Prioritisation | 7 | 4/7 | 0/7 | Merge into B8 | Scenario grounding good; kf quality gaps; natural merge with B11 |
| B9 — Risk Identification | 7 | 2/7 | 6/7 | Merge + Keep | Short/abstract Qs; merge with B16 (residual risk) |
| B10 — Risk Justification | 7 | 1/7 | 7/7 | Keep + Refocus | All justification Qs too abstract ("explain why X is a risk") |
| B11 — Risk Severity | 7 | 2/7 | 2/7 | Merge into B8 | Overlaps B8 prioritization logic; combined creates richer scoring target |
| B12 — Audit Perspective | 4 | 1/4 | 0/4 | Keep + Refocus | Too few cases; dual auditor+RM perspective needed |
| B13 — Evidence Expectation | 3 | 0/3 | 3/3 | Keep + Refocus | Critically underpopulated; needs sector-specific grounding |
| B14 — Remediation Quality | 3 | 3/3 | 3/3 | Merge + Keep | All key_facts placeholders; critical gap; absorbs B15 |
| B15 — Remediation Feasibility | 3 | 1/3 | 1/3 | Merge into B14 | Feasibility is a sub-dimension of recommendation quality |
| B16 — Residual Risk | 3 | 0/3 | 3/3 | Merge into B9 | Too few, too abstract; residual risk is extension of risk identification |
| B17 — Policy vs Practice | 3 | 3/3 | 0/3 | Absorb into B7 | All kf placeholders; thin concept testable as B7 scenario type |
| B18 — Responsibility Attribution | 7 | 1/7 | 1/7 | Keep + Refocus | Good base; extend to BoD, CISO, RM, vendor hierarchy |
| B19 — Cross-Scenario Consistency | 3 | 0/3 | 0/3 | Remove | Meta-benchmark; not a compliance reasoning capability |
| B20 — Over-Specification | 3 | 0/3 | 2/3 | Absorb into B21 | Over-specification is a form of fabrication; logically part of B21 |
| B21 — Hallucination Rate | 7 | 0/7 | 7/7 | Keep + Extend | Strong adversarial pattern; absorb B20 scenario type |

---

## Changes from V1

### Merges

| From | Into | New Name | Rationale |
|------|------|----------|-----------|
| B8 (Gap Prioritisation) + B11 (Risk Severity) | **B8** | Risk-Based Prioritization | Both test prioritization/severity reasoning — natural combination with richer scoring target |
| B14 (Remediation Quality) + B15 (Feasibility) | **B14** | Remediation Quality & Feasibility | Feasibility is a required sub-dimension of good remediation advice, not a separate benchmark |
| B9 (Risk Identification) + B16 (Residual Risk) | **B9** | Risk Identification & Residual Risk | Residual risk assessment is the natural extension of identifying risks |

### Removed / Absorbed

| Benchmark | Absorbed Into | Rationale |
|-----------|---------------|-----------|
| B17 — Policy vs Practice Distinction | B7 Gap Identification | Thin concept fully captured as a policy-evidence gap scenario type within B7 |
| B19 — Cross-Scenario Consistency | Quality check across benchmarks | Meta-benchmark testing consistency, not a compliance reasoning capability. Addressed via coverage analysis at dataset level |
| B20 — Over-Specification Avoidance | B21 Hallucination Rate | Over-specification (fabricating requirements beyond what CCoP mandates) is a form of hallucination — same detection mechanism applies |

### New Benchmarks

| Benchmark | ID | Rationale | Source |
|-----------|-----|-----------|--------|
| Waiver & Exception Reasoning | B22 | Risk Managers navigate the Section 11(7) waiver process regularly — identifying qualifying conditions, preparing submissions, managing compensating controls. No v1 benchmark tests this | CIIO research: waiver process is the top identified pain point |
| Multi-Regulator Coordination | B23 | CIIOs face overlapping requirements (CCoP + MAS-TRM, CCoP + IM8). No benchmark tests how to navigate regulatory overlap or identify conflicts | CIIO research: regulatory overlap is a top-3 challenge |
| Incident Response Guidance | B24 | 2-hour CSA notification, multi-regulator reporting (CSA + MAS + PDPC), crisis communication. High-stakes scenario directly relevant to Risk Managers | CIIO research: incident response coordination is a critical gap |

---

## Benchmark Definitions

### B1 — CCoP Applicability & Scope

**Scoring path:** Rule-based (`expected_label` match)  
**Description:** Tests whether the model correctly determines whether the CCoP applies to a given system, organization, or scenario — including scope boundaries, digital boundary definitions, CCoP 1.0 vs 2.0 evolution, IM8/CCoP overlap for government sector, and new entity classifications (ESCI, STCC, FDI) under the 2024 Cybersecurity Amendment Act.

**V2 changes:** Refocused from pure designation criteria to include CCoP 1.0 evolution questions, sector-specific applicability nuance (government IM8 overlap), and new entity types. Short definitional questions (5/8 v1 cases) replaced with scenario-based applicability judgements.

**Target count:** 25  
**Key CCoP sections:** Cybersecurity Act Section 7-8 (designation), CCoP 2.0 Scope section, Amendment Act 2024 (ESCI, STCC, FDI classifications)  
**Question design guidance:** Frame as "does CCoP apply in this situation?" with concrete organizational contexts. Vary across: new ESCI/STCC/FDI entities, government IM8 dual-compliance situations, scope boundary edge cases (third-party systems partially within CII), CCoP 1.0 vs 2.0 applicability gaps.

---

### B2 — Compliance Classification

**Scoring path:** Rule-based (`expected_label`: compliant / non-compliant / partial)  
**Description:** Tests whether the model correctly classifies a described control implementation as compliant, non-compliant, or partially compliant against CCoP 2.0 requirements. Sector-specific context (IT-heavy vs OT-heavy) affects classification.

**V2 changes:** Refocused from generic classification to sector-specific scenarios with IT/OT nuance. Each question must include a concrete organizational scenario with sector context. OT sector cases must reflect that some controls have OT-specific implementation variants.

**Target count:** 25  
**Key CCoP sections:** Section 5 (Protection: access control, MFA, network segmentation), Section 4 (Identification), Section 7 (Cyber Resilience), OT Addendum  
**Question design guidance:** Describe a specific control implementation at a named sector CIIO. Ask: "Does this satisfy CCoP 2.0 Clause X?" Vary sector (energy/banking/healthcare/transport), control type, and compliance status. Include edge cases where sector context changes the verdict (OT legacy system compensating controls, cloud-hosted CII).

---

### B3 — Conditional Compliance Reasoning

**Scoring path:** LLM-judge  
**Description:** Tests the model's ability to evaluate compliance when compensating controls, partial implementations, or conditional factors are present. The strongest v1 benchmark — scenario-grounded, rich key_facts, zero quality gaps. Core Risk Manager capability: "is this approach compliant IF we have X?"

**V2 changes:** Minimal structural change. Expand from 7 to 30 cases with broader sector diversity and more IT/OT boundary scenarios. Add waiver-adjacent scenarios (compensating controls that should trigger waiver vs those that are sufficient).

**Target count:** 30  
**Key CCoP sections:** Section 5 (Protection), OT Addendum, Cybersecurity Act Section 11(7) (waiver conditions)  
**Question design guidance:** Present a scenario where an organization has implemented something different from the literal CCoP requirement. Ask whether it complies. Good cases include: shared accounts with logging (does not comply), legacy OT system with compensating controls (may qualify for waiver), cloud-hosted CII with vendor SLA (complies with conditions). Always include compensating control details.

---

### B4 — IT/OT Classification & Boundary

**Scoring path:** Rule-based (`expected_label`: IT / OT / IT-OT-boundary / hybrid)  
**Description:** Tests whether the model correctly classifies systems and scenarios as IT, OT, or boundary/hybrid, with reasoning grounded in sector-specific architecture. The critical question is the IT/OT boundary — scenarios that could be either, or where the boundary is contested.

**V2 changes:** Refocused from definitional "explain IT vs OT differences" to scenario-based boundary judgements across sectors. Each question presents a specific system/component and asks for classification with rationale. Adds IT/OT convergence scenarios (historian servers, DMZ components, cloud-connected OT).

**Target count:** 25  
**Key CCoP sections:** OT Addendum (scope definition), CCoP 2.0 scope boundary guidance  
**Question design guidance:** Present a specific component (e.g., "SCADA historian server with database backup to cloud") and ask IT/OT classification. Vary sector: energy SCADA, hospital MRI controllers, port vessel traffic systems, financial market surveillance. Include convergence scenarios that sit at the boundary.

---

### B5 — Control Requirement Comprehension

**Scoring path:** LLM-judge  
**Description:** Tests whether the model can explain what a CCoP requirement actually mandates in practical terms a Risk Manager can act on. NOT definitional explanation — the question must be "what does this mean for my org in practice?"

**V2 changes:** Major refocus. All 7 v1 cases were abstract "explain Clause X in plain language" — replaced entirely. V2 questions frame as "we're in [sector] and have [situation]; what does Clause X actually require us to do?" Requires practical interpretation, not recitation.

**Target count:** 25  
**Key CCoP sections:** Section 5 (Protection clauses), Section 3 (Governance), Section 6 (Detection), OT Addendum  
**Question design guidance:** Frame as a Risk Manager asking "what does [specific clause] actually require us to do given our [sector/architecture/situation]?" Good cases: MFA requirements for OT legacy systems, threat modelling requirements for small healthcare CII, supply chain risk management for a water utility with single SCADA vendor.

---

### B6 — Control Intent Understanding

**Scoring path:** LLM-judge  
**Description:** Tests whether the model understands why a control exists — the security objective behind the requirement — and can apply that intent to evaluate non-obvious implementations. Requires connecting CCoP requirements to underlying security principles.

**V2 changes:** Complete rewrite. 6/7 v1 cases had abstract questions with zero scenario grounding; 4/7 had placeholder key_facts. All replaced with scenario-applied intent questions: "We want to achieve [objective] using [approach] — does this satisfy the intent of Clause X?"

**Target count:** 20  
**Key CCoP sections:** Section 5 (Protection), Section 4 (Identification), Security-by-Design principles  
**Question design guidance:** Frame as "the underlying intent of Clause X is [Y]; does our proposed approach of [Z] satisfy that intent?" Good cases: session logging as compensating control for individual accountability, defense-in-depth interpretation when perimeter controls are strong, zero trust principles applied to legacy OT.

---

### B7 — Gap Identification Quality

**Scoring path:** LLM-judge  
**Description:** Tests whether the model correctly identifies compliance gaps in a described organizational situation, including policy-vs-practice gaps (B17 absorbed). A gap must be specific, cite a clause, and not include false positives. Key Risk Manager capability: audit preparation.

**V2 changes:** Absorbs B17 (policy vs practice distinction) as a scenario subtype. Expands from 8 to 30 cases. Adds multi-domain scenarios (gaps across governance + protection + OT addendum simultaneously), sector-specific gap profiles.

**Target count:** 30  
**Key CCoP sections:** All CCoP sections (B7 tests gap identification across the full CCoP scope)  
**Question design guidance:** Describe an organization's current state — include deliberate gaps, partial implementations, and policy-practice inconsistencies. Ask the model to identify all compliance gaps. Include B17-type scenarios: "our policy says X but our evidence shows Y." Good cases: organization claims MFA implemented but audit evidence shows exceptions for legacy systems; board cybersecurity training described as "planned" but not executed.

---

### B8 — Risk-Based Prioritization

**Scoring path:** LLM-judge  
**Description:** Tests whether the model can prioritize a set of identified compliance gaps or risks in order of urgency, with sound reasoning grounded in threat severity, regulatory exposure, operational impact, and likelihood. Merged from B8 (gap prioritization) and B11 (risk severity assessment).

**V2 changes:** Merged B8 + B11. B8 was gap prioritization; B11 was severity classification — the scoring target (should gap A be addressed before gap B, and why?) is richer when both dimensions are combined. Key_facts quality gaps in B8 (4/7 placeholders) addressed in V2 regeneration.

**Target count:** 25  
**Key CCoP sections:** Section 3 (Governance: risk management), Section 4 (Identification: risk assessment methodology)  
**Question design guidance:** Present 3-5 identified gaps or risks and ask for prioritized remediation order with rationale. Good cases: MFA gap vs patch management backlog vs OT network segmentation gap — which first and why? Include sector-specific risk context (energy OT downtime cost, healthcare patient safety).

---

### B9 — Risk Identification & Residual Risk

**Scoring path:** LLM-judge  
**Description:** Tests whether the model identifies the full set of risks arising from a described situation AND correctly characterizes what residual risk remains after a control is implemented. Merged from B9 (risk identification) and B16 (residual risk awareness).

**V2 changes:** Merged B9 + B16. Risk identification and residual risk are two parts of the same risk assessment cycle. B9 v1 had 6/7 short/abstract questions — all replaced with scenario-grounded cases. B16 had 3 underpopulated cases — absorbed as the second half of each test case (identify risks, then what remains after mitigation).

**Target count:** 25  
**Key CCoP sections:** Section 4 (Identification: risk assessment, threat modelling), Section 3 (Governance: risk treatment)  
**Question design guidance:** Each case has two parts: (1) identify all risks from a described scenario, (2) after a stated mitigation is applied, what residual risk remains? Good cases: vendor access controls mitigated with MFA — what residual risk from insider threat, SIM swapping, session hijacking? OT air-gap with data diode — what residual risk from removable media, supply chain?

---

### B10 — Risk Justification Coherence

**Scoring path:** LLM-judge  
**Description:** Tests whether the model can construct a coherent, well-structured risk justification that links threat, vulnerability, likelihood, impact, and regulatory consequence. Used for board reporting and waiver request contexts.

**V2 changes:** Refocused from abstract "explain why X is a risk" (7/7 abstract v1 cases) to practitioner-framed "justify this risk for a board presentation / waiver submission." Adds sector-specific impact framing (financial sector = customer impact + MAS consequences; energy sector = public safety + national security).

**Target count:** 20  
**Key CCoP sections:** Section 3 (Governance: risk reporting), Section 4 (Identification: risk assessment)  
**Question design guidance:** Ask the model to produce a risk justification suitable for a specific audience (BoD, CSA audit, waiver submission). Scenario includes the threat actor, the vulnerability, and the organizational context. Good cases: justify OT patching backlog risk to a board that wants to defer it; justify a waiver request for legacy SCADA with no MFA capability.

---

### B12 — Audit Perspective Alignment

**Scoring path:** LLM-judge  
**Description:** Tests whether the model correctly evaluates a compliance claim from both the CSA auditor's perspective (what will fail an audit) AND the Risk Manager's audit preparation perspective (what evidence is needed). Dual-perspective benchmark.

**V2 changes:** Refocused from purely CSA auditor perspective to dual perspective. Added Risk Manager audit prep framing. Expanded from 4 to 20 cases with sector-specific audit scenarios (OT addendum audit evidence, governance clause audit requirements).

**Target count:** 20  
**Key CCoP sections:** Section 2 (biennial audit requirements), all auditable clauses (1, 2, 4, 5, 6, 7, OT addendum)  
**Question design guidance:** Present a compliance claim and ask: (1) would a CSA auditor accept this? (2) what evidence would the Risk Manager need to prepare? Good cases: "we train staff on cybersecurity annually" — what does an auditor expect vs what should RM prepare? Claims about MFA implementation that rely on incomplete evidence.

---

### B13 — Evidence Expectation Awareness

**Scoring path:** LLM-judge  
**Description:** Tests whether the model knows what specific types of audit evidence CII organizations must prepare and maintain for CCoP compliance audits — from the Risk Manager's perspective of audit preparation, not just what an auditor wants.

**V2 changes:** Refocused to Risk Manager preparation framing. Expanded from 3 to 20 cases. Added sector-specific evidence requirements (OT evidence challenges, cloud-hosted CII evidence in shared-responsibility models).

**Target count:** 20  
**Key CCoP sections:** Section 2 (audit requirements), Section 5 (Protection evidence), Section 6 (Detection: logging evidence), OT Addendum  
**Question design guidance:** Ask "what evidence should [type of RM] prepare to demonstrate compliance with [specific clause]?" Good cases: evidence for MFA on OT systems with no standard audit logging; evidence for board cybersecurity training requirement; evidence for threat modelling completion.

---

### B14 — Remediation Quality & Feasibility

**Scoring path:** LLM-judge  
**Description:** Tests whether the model produces high-quality, actionable remediation recommendations that are feasible for the specific organizational context — considering budget, operational constraints, sector-specific limitations, and CCoP requirements. Merged from B14 (remediation quality) and B15 (feasibility).

**V2 changes:** Merged B14 + B15. B14 v1 had 3/3 placeholder key_facts — completely unusable, full regeneration required. B15 feasibility testing absorbed as a required dimension: every good remediation answer must address feasibility, not just what to do. Critical benchmark: remediation guidance is the primary Risk Manager use case.

**Target count:** 30  
**Key CCoP sections:** All protection clauses, OT Addendum (OT-specific remediation constraints), Section 3 (risk treatment plans)  
**Question design guidance:** Describe a specific gap and organizational constraints (budget, operations, legacy systems, sector). Ask for practical remediation recommendations. Good cases: OT network segmentation where production shutdown is not acceptable; MFA implementation where legacy SCADA HMIs cannot support individual authentication; supply chain risk management for a water utility with a single source SCADA vendor.

---

### B18 — Responsibility Attribution (SG)

**Scoring path:** LLM-judge  
**Description:** Tests whether the model correctly attributes cybersecurity responsibilities across the CII governance hierarchy: Board of Directors, CIIO (legal entity), CISO, Risk Manager, OT team, IT team, vendors. Specifically the Singapore CCoP/Cybersecurity Act framework.

**V2 changes:** Extended from CIIO/CSA focus to the full governance hierarchy. Added BoD responsibility scenarios (new 2026 BoD training requirements), vendor responsibility attribution (on-site access requirements), CISO vs Risk Manager responsibility boundaries, and multi-organization scenarios (shared services, outsourced CII operations).

**Target count:** 25  
**Key CCoP sections:** Section 3 (Governance: roles and responsibilities), Cybersecurity Act Section 12 (designated person), CCoP 2.0 supply chain requirements  
**Question design guidance:** Present a scenario with a specific incident or compliance situation and ask who is responsible for what. Good cases: vendor causes breach — what is CIIO's vs vendor's regulatory liability? Board member lacks cybersecurity awareness — who is accountable under CCoP? CISO vs RM responsibility for waiver submission.

---

### B21 — Hallucination & Over-Specification

**Scoring path:** Rule-based (primary: `expected_label` pass/fail) + LLM-judge (secondary: for complex fabrication patterns)  
**Description:** Tests whether the model avoids fabricating non-existent CCoP clauses, inventing requirements beyond what CCoP mandates (over-specification), or attributing requirements from other frameworks (ISO 27001, NIST) as CCoP mandates. Safety-critical benchmark. Absorbs B20 (over-specification).

**V2 changes:** Absorbs B20. Over-specification (claiming CCoP mandates specific technologies or implementation details it does not) is a form of hallucination — same detection mechanism, same scoring. Adds adversarial patterns: questions that invite hallucination by asking about plausible-sounding clauses that do not exist, technology-specific requirements CCoP does not impose, and sector-specific mandates CCoP does not include.

**Target count:** 25  
**Key CCoP sections:** All (adversarial test for any section)  
**Question design guidance:** Design questions that tempt the model to fabricate. Types: (1) ask about a specific clause number that does not exist (e.g., "what does 5.9.7 say?"), (2) ask for a specific technology mandate (e.g., "does CCoP require RSA SecurID?"), (3) ask about requirements from other frameworks as if they are in CCoP, (4) ask about sector-specific requirements CCoP does not include. Expected response: acknowledge clause/requirement does not exist, point to related real requirements.

---

### B22 — Waiver & Exception Reasoning

**Scoring path:** LLM-judge  
**Description:** (New in V2) Tests whether the model correctly reasons about the waiver and exception process under Section 11(7) of the Cybersecurity Act — identifying qualifying conditions, advising on compensating controls, explaining process requirements (4-week timeline, time-bound waivers, monitoring obligations), and distinguishing situations that warrant a waiver from those that require full remediation.

**Target count:** 20  
**Key CCoP sections:** Cybersecurity Act Section 11(7), CCoP 2.0 waiver guidance, OT Addendum (legacy system waivers)  
**Question design guidance:** Design questions around genuine waiver scenarios from CIIO research: legacy OT systems that cannot support MFA, air-gapped systems where patch management is operationally infeasible, small-sector CIIOs with budget constraints. Ask: does this qualify for a waiver? What compensating controls are needed? What is the submission process? What monitoring obligations apply during the waiver period? Include trap cases where full remediation is required (no valid waiver ground).

---

### B23 — Multi-Regulator Coordination

**Scoring path:** LLM-judge  
**Description:** (New in V2) Tests whether the model can navigate scenarios where a CII organization faces overlapping regulatory requirements from multiple frameworks — CCoP + MAS-TRM (banking/finance), CCoP + IM8 (government), CCoP + PDPC (personal data), CCoP + CAAS regulations (aviation). Key Risk Manager challenge identified in CIIO research.

**Target count:** 20  
**Key CCoP sections:** Cross-regulatory (CCoP 2.0, MAS-TRM, IM8, PDPC, Singapore Cybersecurity Act)  
**Question design guidance:** Frame as "we must comply with both [regulator A] and [regulator B]; in this situation, what do we do?" Good cases: banking sector MFA requirement under MAS-TRM vs CCoP (different specificity levels), government sector audit mutual recognition between IM8 and CCoP, incident reporting to both CSA (2-hour window) and MAS (separate timeline and format), PDPC breach notification vs CSA cybersecurity incident notification for the same event.

---

### B24 — Incident Response Guidance

**Scoring path:** LLM-judge  
**Description:** (New in V2) Tests whether the model provides correct, actionable incident response guidance grounded in Singapore's CCoP 2.0 requirements — specifically the 2-hour notification window to CSA, multi-regulator reporting obligations, crisis communication requirements, evidence preservation, and BCP/DR activation. High-stakes Risk Manager scenario.

**Target count:** 25  
**Key CCoP sections:** Section 8 (Response & Recovery), Cybersecurity Act Section 14 (incident notification), Section 9 (Cyber Resilience)  
**Question design guidance:** Present a concrete incident scenario and ask for the correct response protocol. Good cases: ransomware detected on CII at 2am on a Sunday — what are the notification obligations and timeline? Data breach involving both CII and personal data — what are the overlapping notification obligations to CSA, MAS, PDPC? Major incident with media inquiries — what does crisis communication guidance require? Include sector-specific details (banking customer impact, healthcare patient data, energy operational disruption).

---

## Scoring Path Reference

| Path | Benchmarks | Infrastructure |
|------|------------|---------------|
| Rule-based | B1, B2, B4, B21 | `expected_label` match (exact or in allowed set) |
| LLM-judge | B3, B5, B6, B7, B8, B9, B10, B12, B13, B14, B18, B22, B23, B24 | Universal 2-dimension judge: reasoning depth (0-3) + hallucination gate (binary) |

B21 uses rule-based as primary and LLM-judge as secondary for complex fabrication patterns that regex cannot catch.

---

## Target Counts by Benchmark

| Benchmark | Target | Notes |
|-----------|--------|-------|
| B1 | 25 | CCoP evolution, IM8, ESCI/FDI additions |
| B2 | 25 | Sector variance across 11 sectors |
| B3 | 30 | Many conditional reasoning patterns |
| B4 | 25 | 11 sectors x IT/OT/hybrid/boundary profiles |
| B5 | 25 | Practical interpretation spans many CCoP sections |
| B6 | 20 | Refocused from v1, controlled scope |
| B7 | 30 | Complex reasoning, many failure modes, absorbs B17 |
| B8 | 25 | Merged B8+B11: severity + prioritization combined |
| B9 | 25 | Merged B9+B16: identification + residual combined |
| B10 | 20 | Board/audit justification framing |
| B12 | 20 | Dual perspective (expanded from 4 v1 cases) |
| B13 | 20 | Evidence prep (expanded from 3 v1 cases) |
| B14 | 30 | Merged B14+B15: quality + feasibility; critical gap fixed |
| B18 | 25 | Extended role hierarchy |
| B21 | 25 | Adversarial variety, absorbs B20 |
| B22 | 20 | New: waiver process scenarios |
| B23 | 20 | New: multi-regulator overlap |
| B24 | 25 | New: incident response protocols |
| **Total** | **~435** | |
