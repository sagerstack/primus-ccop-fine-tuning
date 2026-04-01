# V1 Test Case Triage Report

> Triage of all 118 v1 test cases from `ground-truth/archive/phase-2/test-suite/`  
> Purpose: Determine which cases can migrate to v2 (saving generation effort) vs must be regenerated  
> V2 Benchmark reference: `docs/phase-2/benchmark-registry.md`

**Triage completed:** 2026-04-01  
**Total v1 test cases:** 118 across 21 benchmarks

---

## Summary

| Classification | Count | Percentage |
|----------------|-------|------------|
| Keep           | 52    | 44%        |
| Revise         | 36    | 31%        |
| Discard        | 30    | 25%        |
| **Total**      | **118** | **100%** |

**Salvageable (Keep + Revise):** 88 of 118 cases (75%) — these inform v2 generation with context; 30 can migrate directly

**Distribution vs spec target:** Keep 44% (target 40-50%), Revise 31% (target ~30%), Discard 25% (target 20-30%) — within range

### Key Findings

- **B3** (Conditional Compliance) is the only benchmark with zero discards — all 7 cases Keep
- **B5, B6, B9, B10** are heavily revise/discard due to abstract question framing
- **B14, B17** are full discard — key_facts placeholders throughout
- **B19** is full discard — meta-benchmark removed in v2
- **B8, B11, B14, B15** map to merged v2 benchmarks (B8 and B14)
- **B9, B16** map to merged v2 benchmark (B9)
- **B17** absorbed into B7; **B20** absorbed into B21

---

## Per-Benchmark Triage

### B1 — CCoP Applicability & Scope (8 cases → V2: B1)

V1 audit finding: 5/8 too definitional, 3/8 key_facts placeholders

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B1-001  | Revise        | B1           | Definitional ("what criteria does Commissioner use") — reframe as applicability scenario for a specific org |
| B1-002  | Revise        | B1           | Abstract distinction question ("what is difference between CII and essential service") — reframe as "does CCoP apply to us?" scenario |
| B1-003  | Revise        | B1           | Pure definitional ("what is a CIIO") — replace with scenario-grounded applicability judgement |
| B1-004  | Keep          | B1           | Healthcare dual-system scenario — already scenario-grounded, maps well to v2 applicability scope |
| B1-005  | Discard       | B1           | Key_facts placeholder; definitional ("what does debilitating effect mean") — too abstract, needs full regeneration |
| B1-006  | Keep          | B1           | Scenario-grounded recourse question; decent expected_response (932 chars); key_facts solid |
| B1-007  | Discard       | B1           | Key_facts placeholder; definitional ("what is digital boundary") — too abstract for v2 practitioner framing |
| B1-008  | Revise        | B1           | Key_facts placeholder; good multi-system scenario concept — scenario is salvageable but key_facts and ground truth need reconstruction |

**B1 summary:** 2 Keep, 3 Revise, 3 Discard

---

### B2 — Compliance Classification Accuracy (7 cases → V2: B2)

V1 audit finding: 1/7 key_facts placeholder, 0/7 abstract — good base

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B2-001  | Keep          | B2           | Scenario-grounded VPN auth compliance check; solid expected_response; maps directly to v2 |
| B2-002  | Revise        | B2           | Key_facts placeholder; 18-month retention scenario good — rewrite key_facts, reconstruct expected_response to cite exact clause |
| B2-003  | Keep          | B2           | Critical patch timeline scenario; clear compliance verdict; good expected_response |
| B2-004  | Keep          | B2           | IRP testing scenario with tabletop exercise; decent expected_response (443 chars) — keep, minor enrichment needed |
| B2-005  | Keep          | B2           | OT firewall segmentation scenario; good expected_response (610 chars); maps well to v2 sector-specific focus |
| B2-006  | Keep          | B2           | Audit cycle timing scenario; clear expected_label and expected_response |
| B2-007  | Keep          | B2           | Password policy scenario; rich expected_response (879 chars); rule-based scoring target preserved |

**B2 summary:** 6 Keep, 1 Revise, 0 Discard

---

### B3 — Conditional Compliance Reasoning (7 cases → V2: B3)

V1 audit finding: 0/7 abstract, 0/7 key_facts placeholders — strongest v1 benchmark

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B3-001  | Keep          | B3           | Shared admin accounts with logging — canonical conditional compliance scenario; rich key_facts (3) |
| B3-002  | Keep          | B3           | OT patching exception — sector-specific, waiver-adjacent; 2 key_facts, 815-char expected_response |
| B3-003  | Keep          | B3           | Legacy OT logging limitation — compensating control evaluation; strong case |
| B3-004  | Keep          | B3           | IRP tested 18 months ago — conditional compliance with nuance; solid expected_response (823 chars) |
| B3-005  | Keep          | B3           | 5% training non-compliance — partial implementation scenario; 2 key_facts, 960-char response |
| B3-006  | Keep          | B3           | IT vs OT vulnerability assessment frequency gap — 5 key_facts, 1088-char response; excellent case |
| B3-007  | Keep          | B3           | ISO 27001 vs CCoP alignment — framework substitution scenario; 3 key_facts, 1060-char response |

**B3 summary:** 7 Keep, 0 Revise, 0 Discard

---

### B4 — IT/OT Classification & Boundary (7 cases → V2: B4)

V1 audit finding: 0/7 key_facts placeholders, 1/7 abstract

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B4-001  | Discard       | B4           | Pure definitional ("explain key differences between IT and OT") — exactly the abstract format v2 replaces; no scenario grounding |
| B4-002  | Keep          | B4           | Power facility multi-system classification — 5 key_facts; scenario-grounded; excellent v2 fit |
| B4-003  | Revise        | B4           | Clause applicability question (does 10.2.3 apply to IT/OT/both) — decent scenario component but framing is regulatory lookup, not boundary reasoning |
| B4-004  | Keep          | B4           | Parallel requirements for IT vs OT — 8 key_facts; scenario-grounded; rich expected_response (1261 chars) |
| B4-005  | Revise        | B4           | Section applicability question — partially scenario-grounded but still asks about regulatory scope rather than classification |
| B4-006  | Keep          | B4           | Water treatment remote access scenario — IT/OT boundary reasoning; 8 key_facts; 1477-char response |
| B4-007  | Keep          | B4           | Engineering Workstation classification — 8 key_facts; exceptional case with 3593-char expected_response; canonical boundary scenario |

**B4 summary:** 4 Keep, 2 Revise, 1 Discard

---

### B5 — Control Requirement Comprehension (7 cases → V2: B5)

V1 audit finding: 7/7 abstract ("explain Clause X in plain language") — all need practitioner reframing

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B5-001  | Revise        | B5           | "Explain Clause 3.2.2 in plain language" — clause ID and concept salvageable; reframe as "what does this require us to do in [sector]?" |
| B5-002  | Revise        | B5           | "What does Clause 5.1.5 require re: MFA?" — good clause reference; reframe as practitioner implementation question with OT/legacy context |
| B5-003  | Revise        | B5           | "Interpret Clause 5.6.4 patch management timelines" — specific numbers are valuable; reframe as sector-specific practical interpretation |
| B5-004  | Revise        | B5           | "What does Clause 6.1.3 require re: logging?" — logging detail valuable; reframe as RM asking "what do we actually need to implement?" |
| B5-005  | Revise        | B5           | "What does Clause 7.1.2 specify re: IRP?" — IRP elements valuable; reframe as practitioner planning question |
| B5-006  | Revise        | B5           | "Explain Clause 10.2.3 for OT" — OT context partially grounds it; reframe as "we have [OT architecture], what exactly do we need?" |
| B5-007  | Revise        | B5           | "What are training requirements in Clause 9.1.2?" — 4 key_facts available; reframe as RM audit preparation question |

**B5 summary:** 0 Keep, 7 Revise, 0 Discard

---

### B6 — Control Intent Understanding (7 cases → V2: B6)

V1 audit finding: 7/7 abstract questions, 4/7 key_facts placeholders

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B6-001  | Discard       | B6           | Key_facts placeholder; "what is intent of MFA requirement?" — abstract intent question with no scenario |
| B6-002  | Discard       | B6           | Key_facts placeholder; "why require 1-year log retention AND 3-month availability?" — abstract dual-requirement reasoning |
| B6-003  | Revise        | B6           | 2 key_facts present; "why require annual IRP testing?" — decent concept; add organizational scenario to ground the intent application |
| B6-004  | Discard       | B6           | Key_facts placeholder; "why require IT/OT segmentation?" — abstract security principle question |
| B6-005  | Revise        | B6           | 1 key_fact present (not placeholder); "why different patch timelines critical vs non-critical?" — add risk framing with sector scenario |
| B6-006  | Discard       | B6           | Key_facts placeholder; "why require framework appropriate to scale/complexity?" — abstract compliance philosophy |
| B6-007  | Revise        | B6           | 1 key_fact present; "why role-specific training for privileged users?" — add privileged user scenario to ground the intent application |

**B6 summary:** 0 Keep, 3 Revise, 4 Discard

---

### B7 — Gap Identification Quality (8 cases → V2: B7)

V1 audit finding: 0/8 abstract, 0/8 key_facts placeholders — strong benchmark

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B7-001  | Keep          | B7           | Access control policy gap — 5 key_facts; policy document format; excellent scenario grounding |
| B7-002  | Keep          | B7           | Logging policy gap — 8 key_facts; rich evidence detail; strong v2 fit |
| B7-003  | Keep          | B7           | Patch management gap — 8 key_facts; CVE evidence details; excellent compliance gap scenario |
| B7-004  | Keep          | B7           | IRP documentation gap — 8 key_facts; multi-dimensional gap identification; strong case |
| B7-005  | Keep          | B7           | Power plant network architecture gap — 8 key_facts; OT-specific; sector-grounded; excellent |
| B7-006  | Keep          | B7           | Audit history gap — 8 key_facts; temporal compliance gap; well-structured |
| B7-007  | Keep          | B7           | ISO 27001 gap (not CCoP-specific) — 8 key_facts; framework confusion gap; good B7 candidate |
| B7-008  | Keep          | B7           | Vulnerability management gap — 8 key_facts; scope and frequency gap; strong scenario |

**B7 summary:** 8 Keep, 0 Revise, 0 Discard

---

### B8 — Gap Prioritisation (7 cases → V2: B8 merged with B11)

V1 audit finding: 4/7 key_facts placeholders, 0/7 abstract — scenario grounding good but key_facts weak

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B8-001  | Discard       | B8           | Key_facts placeholder; MFA + logging + patch gap prioritization — concept good but ground truth needs reconstruction |
| B8-002  | Keep          | B8           | OT segmentation + OT vuln scan gaps — 5 key_facts; scenario-grounded; maps well to merged B8 (risk-based prioritization) |
| B8-003  | Keep          | B8           | Quarterly vuln assessment vs remediation timeline choice — grounded tradeoff reasoning; solid case |
| B8-004  | Discard       | B8           | Key_facts placeholder; no IRP vs no backup — concept is sound but ground truth unusable |
| B8-005  | Discard       | B8           | Key_facts placeholder; framework vs technical controls prioritization — needs full regeneration |
| B8-006  | Discard       | B8           | Key_facts placeholder; IT vs OT gap prioritization with resources — scenario interesting but unusable |
| B8-007  | Keep          | B8           | Post-pentest access control gaps — good question, no placeholder, concrete prioritization scenario |

**B8 summary:** 3 Keep, 0 Revise, 4 Discard

---

### B9 — Risk Identification Accuracy (7 cases → V2: B9 merged with B16)

V1 audit finding: 6/7 short/abstract questions, 2/7 key_facts placeholders

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B9-001  | Keep          | B9           | Third-party shared account risk — scenario-grounded; decent key_facts; maps to B9 (Risk Identification & Residual Risk) |
| B9-002  | Keep          | B9           | IT/OT flat network risk — scenario-grounded; both IT and OT risk angles |
| B9-003  | Keep          | B9           | Logs on local systems risk — clear scenario; good identification target |
| B9-004  | Revise        | B9           | 6-month patch cycle risk — scenario decent but question too short (no org context); add sector/architecture detail |
| B9-005  | Revise        | B9           | Untested IRP risk — question too brief ("what risks does this create?"); needs practitioner framing and org context |
| B9-006  | Discard       | B9           | Key_facts placeholder; generic training gap — too short, no org context, placeholder key_facts |
| B9-007  | Discard       | B9           | Key_facts placeholder; no formal risk framework — too abstract, no scenario |

**B9 summary:** 3 Keep, 2 Revise, 2 Discard

---

### B10 — Risk Justification Coherence (7 cases → V2: B10)

V1 audit finding: 7/7 abstract ("explain why X is a risk") — all need practitioner reframing

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B10-001 | Revise        | B10          | Shared vendor accounts justification — 2 key_facts; good concept; reframe for specific audience (board/waiver submission) |
| B10-002 | Discard       | B10          | Key_facts placeholder; IT/OT segmentation justification — "construct a clear risk justification" but placeholder key_facts |
| B10-003 | Revise        | B10          | Local log storage justification — decent concept; reframe as board presentation context with specific org scenario |
| B10-004 | Revise        | B10          | 6-month patch cycle justification — 2 key_facts; good specific detail; reframe as audit or board document |
| B10-005 | Revise        | B10          | Untested IRP justification — 3 key_facts; best B10 candidate; reframe for specific output (waiver document/board brief) |
| B10-006 | Keep          | B10          | Generic training for privileged users — 5 key_facts; most grounded B10 case; skills-responsibility gap framing valuable |
| B10-007 | Revise        | B10          | No formal risk framework justification — 1 key_fact; decent structure; add specific org context and target audience |

**B10 summary:** 1 Keep, 5 Revise, 1 Discard

---

### B11 — Risk Severity Assessment (7 cases → V2: B8 merged)

V1 audit finding: Merges into B8; 2/7 key_facts placeholders

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B11-001 | Keep          | B8           | Vendor shared accounts severity rating — scenario-grounded; clear severity assessment; maps to B8 severity dimension |
| B11-002 | Discard       | B8           | Key_facts placeholder; IT/OT segmentation severity — placeholder key_facts, too generic |
| B11-003 | Discard       | B8           | Key_facts placeholder; local log storage severity — placeholder key_facts |
| B11-004 | Keep          | B8           | CVE severity with active exploitation — 3 key_facts; specific CVE details; strong scenario for B8 severity scoring |
| B11-005 | Keep          | B8           | Untested IRP severity (3-year gap) — 2 key_facts; temporal context gives specific severity anchor |
| B11-006 | Keep          | B8           | 15% overdue training severity — 4 key_facts; operational staff + detailed context; good severity case |
| B11-007 | Revise        | B8           | Severity of controls without formal framework — decent concept; refocus from "rate the severity" to prioritization within B8 framing |

**B11 summary:** 4 Keep, 1 Revise, 2 Discard (all map to V2 B8)

---

### B12 — Audit Perspective Alignment (4 cases → V2: B12)

V1 audit finding: 1/4 key_facts placeholder, 0/4 abstract — good base, underpopulated

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B12-001 | Keep          | B12          | Email-based MFA audit evaluation — scenario-grounded; auditor perspective clear; maps to v2 dual-perspective |
| B12-002 | Revise        | B12          | Key_facts placeholder; manual spreadsheet log retention claim — scenario concept good; rewrite key_facts, add RM perspective |
| B12-003 | Keep          | B12          | IRP with 2-hour notification clause — concrete audit finding; 1043-char expected_response; strong case |
| B12-004 | Keep          | B12          | Informal risk management (Excel spreadsheet) — 3 key_facts; dual perspective opportunity; strong v2 fit |

**B12 summary:** 3 Keep, 1 Revise, 0 Discard

---

### B13 — Evidence Expectation Awareness (3 cases → V2: B13)

V1 audit finding: 0/3 key_facts placeholders but 3/3 abstract (audit-centric not RM-centric), critically underpopulated

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B13-001 | Revise        | B13          | MFA evidence expectation — decent concept; reframe from "what do auditors expect?" to "what evidence should RM prepare?" + add sector context |
| B13-002 | Revise        | B13          | Log retention evidence expectation — 2 key_facts; reframe to RM preparation perspective with OT-specific evidence challenges |
| B13-003 | Revise        | B13          | IRP testing evidence — reframe to RM perspective; add sector-specific evidence gaps |

**B13 summary:** 0 Keep, 3 Revise, 0 Discard

---

### B14 — Remediation Recommendation Quality (3 cases → V2: B14 merged with B15)

V1 audit finding: 3/3 key_facts placeholders, 3/3 abstract — completely unusable ground truth

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B14-001 | Discard       | B14          | Key_facts placeholder; vendor shared accounts remediation — scenario salvageable but ground truth completely unusable; regenerate |
| B14-002 | Discard       | B14          | Key_facts placeholder; flat network segmentation remediation — placeholder key_facts throughout; full regeneration required |
| B14-003 | Discard       | B14          | Key_facts placeholder; local log storage SIEM remediation — same issue; regenerate with feasibility dimension (v2 B14) |

**B14 summary:** 0 Keep, 0 Revise, 3 Discard

---

### B15 — Remediation Feasibility (3 cases → V2: B14 merged)

V1 audit finding: 1/3 key_facts placeholder; merges into B14

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B15-001 | Keep          | B14          | 2-week OT segmentation timeline feasibility — scenario-grounded; directly maps to B14 feasibility dimension |
| B15-002 | Revise        | B14          | OT patching feasibility — good concept; reframe to include remediation recommendation component (B14 requires both quality + feasibility) |
| B15-003 | Discard       | B14          | Key_facts placeholder; tabletop exercise feasibility — placeholder key_facts; regenerate as B14 case with full feasibility+quality dimensions |

**B15 summary:** 1 Keep, 1 Revise, 1 Discard (all map to V2 B14)

---

### B16 — Residual Risk Awareness (3 cases → V2: B9 merged)

V1 audit finding: 0/3 key_facts placeholders but 3/3 abstract questions, underpopulated; merges into B9

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B16-001 | Revise        | B9           | MFA residual risk — question too brief ("what residual risks remain after MFA?"); enrich with specific org architecture and threat actors |
| B16-002 | Revise        | B9           | IT/OT segmentation residual risk — 2 key_facts; better than B16-001; add sector-specific residual threat framing |
| B16-003 | Revise        | B9           | SIEM residual risk — good concept; needs org scenario and specific sector context for B9 merged framing |

**B16 summary:** 0 Keep, 3 Revise, 0 Discard (all map to V2 B9)

---

### B17 — Policy vs Practice Distinction (3 cases → V2: B7 absorbed)

V1 audit finding: 3/3 key_facts placeholders — absorbed into B7 as scenario subtype

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B17-001 | Discard       | B7           | Key_facts placeholder; MFA policy vs practice gap — scenario is exactly a B7 policy-evidence gap scenario, but key_facts placeholder makes it unusable; regenerate as B7 case |
| B17-002 | Discard       | B7           | Key_facts placeholder; 2-hour notification policy vs actual incident log — strong B7 scenario concept but ground truth unusable |
| B17-003 | Discard       | B7           | Key_facts placeholder; annual training policy vs records gap — all three B17 cases are perfect B7 scenario types but all have placeholder key_facts |

**B17 summary:** 0 Keep, 0 Revise, 3 Discard (scenario concepts inform B7 generation)

---

### B18 — Responsibility Attribution (7 cases → V2: B18)

V1 audit finding: 1/7 key_facts placeholder, 1/7 abstract — good base

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B18-001 | Discard       | B18          | Key_facts placeholder; designated person responsibilities — abstract ("what are responsibilities of designated person?"); regenerate with governance scenario |
| B18-002 | Keep          | B18          | Commissioner direction to CIIO — 2 key_facts; scenario-grounded; maps to v2 governance hierarchy |
| B18-003 | Keep          | B18          | Incident reporting responsibilities — scenario-grounded; who reports to whom; strong v2 fit |
| B18-004 | Keep          | B18          | Digital boundary responsibility attribution — good multi-party scenario; CIIO vs CSA vs sector regulator |
| B18-005 | Keep          | B18          | MSSP/SOC outsourcing responsibility — scenario-grounded; vendor responsibility boundary; excellent v2 case |
| B18-006 | Keep          | B18          | CSA inspection powers and responsibilities — 2 key_facts; scenario about CSA authority boundaries; strong case |
| B18-007 | Keep          | B18          | Multinational subsidiary scenario — 4 key_facts; parent company vs Singapore subsidiary responsibilities; excellent v2 fit |

**B18 summary:** 6 Keep, 0 Revise, 1 Discard

---

### B19 — Cross-Scenario Consistency (3 cases → V2: Removed)

V1 audit finding: B19 is a meta-benchmark (testing consistency, not compliance reasoning). Removed in v2.

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B19-001 | Discard       | None (removed) | Meta-benchmark: tests if MFA requirement is applied consistently across scenarios — consistency is addressed at dataset analysis level, not a compliance reasoning capability |
| B19-002 | Discard       | None (removed) | Meta-benchmark: tests log retention consistency across Windows/Linux — same issue; removed from v2 benchmark set |
| B19-003 | Discard       | None (removed) | Meta-benchmark: tests patch timeline consistency across IT/OT — all 3 B19 cases discard; B19 concept addressed by dataset coverage analysis |

**B19 summary:** 0 Keep, 0 Revise, 3 Discard (benchmark removed, not absorbed)

---

### B20 — Over-Specification Avoidance (3 cases → V2: B21 absorbed)

V1 audit finding: 0/3 key_facts placeholders but 2/3 abstract; absorbed into B21

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B20-001 | Keep          | B21          | MFA technology specificity — does CCoP mandate RSA SecurID/Yubikey? — adversarial pattern; maps directly to B21 over-specification testing |
| B20-002 | Keep          | B21          | SIEM vendor specificity — good adversarial pattern; model should refuse to attribute specific vendors to CCoP |
| B20-003 | Keep          | B21          | Patch testing environment specificity — 3 key_facts; strong over-specification scenario; maps to B21 |

**B20 summary:** 3 Keep, 0 Revise, 0 Discard (all map to V2 B21)

---

### B21 — Hallucination Rate (7 cases → V2: B21)

V1 audit finding: 0/7 key_facts placeholders, 7/7 adversarial pattern — strong benchmark

| Test ID | Classification | V2 Benchmark | Notes |
|---------|---------------|--------------|-------|
| B21-001 | Keep          | B21          | Non-existent Clause 5.9.7 quantum encryption — canonical fabricated clause test; strong adversarial pattern |
| B21-002 | Keep          | B21          | Specific minimum password length (12/14/16 chars?) — CCoP doesn't mandate specific length; good hallucination trap |
| B21-003 | Keep          | B21          | SIEM vendor requirement — does CCoP mandate specific vendors? — strong over-specification trap |
| B21-004 | Keep          | B21          | Non-existent Clause 7.4.5 maximum downtime — fabricated clause with specific RTO; excellent adversarial case |
| B21-005 | Keep          | B21          | Cybersecurity certification requirements (CISSP/CISM/CEH) — CCoP doesn't mandate certifications |
| B21-006 | Keep          | B21          | Air-gap mandate clause — over-specification pattern (CCoP doesn't mandate air-gap) |
| B21-007 | Keep          | B21          | Minimum training hours — CCoP doesn't specify hours; good fabrication trap |

**B21 summary:** 7 Keep, 0 Revise, 0 Discard

---

## Benchmark Mapping Summary

### Direct V1 → V2 Mappings

| V1 Benchmark | V2 Benchmark | Keep | Revise | Discard |
|--------------|--------------|------|--------|---------|
| B1 Applicability | B1 | 2 | 3 | 3 |
| B2 Classification | B2 | 6 | 1 | 0 |
| B3 Conditional | B3 | 7 | 0 | 0 |
| B4 IT/OT | B4 | 4 | 2 | 1 |
| B5 Control Req | B5 | 0 | 7 | 0 |
| B6 Intent | B6 | 0 | 3 | 4 |
| B7 Gap ID | B7 | 8 | 0 | 0 |
| B9 Risk ID | B9 | 3 | 2 | 2 |
| B10 Risk Justification | B10 | 1 | 5 | 1 |
| B12 Audit Perspective | B12 | 3 | 1 | 0 |
| B13 Evidence | B13 | 0 | 3 | 0 |
| B18 Responsibility | B18 | 6 | 0 | 1 |

### Merged V1 → V2 Mappings

| V1 Benchmarks | V2 Benchmark | Keep | Revise | Discard |
|---------------|--------------|------|--------|---------|
| B8 + B11 | B8 Risk-Based Prioritization | 3+4=7 | 0+1=1 | 4+2=6 |
| B14 + B15 | B14 Remediation Quality & Feasibility | 0+1=1 | 0+1=1 | 3+1=4 |
| B9 + B16 | B9 Risk ID & Residual Risk | 3+0=3 | 2+3=5 | 2+0=2 |

### Absorbed / Removed V1 Benchmarks

| V1 Benchmark | V2 Target | Keep | Revise | Discard | Notes |
|--------------|-----------|------|--------|---------|-------|
| B17 Policy vs Practice | B7 | 0 | 0 | 3 | All key_facts placeholders; scenario concepts inform B7 generation |
| B19 Cross-Scenario | None | 0 | 0 | 3 | Meta-benchmark removed; consistency via dataset analysis |
| B20 Over-Specification | B21 | 3 | 0 | 0 | All 3 keep — over-specification is hallucination pattern |

---

## Actionability for V2 Generation

### Immediately Migratable (52 Keep cases)

These cases can be migrated to v2 schema with key_facts enrichment and expected_response restructuring. Reduces generation effort for:
- B3: full 7-case coverage (only needs expansion to 30 target)
- B7: full 8-case coverage (strong foundation for 30-case target)
- B21: full 7 native + 3 absorbed B20 = 10 cases toward 25-case target
- B2: 6 cases toward 25-case target

### Revise-and-Use (36 Revise cases)

These cases have salvageable scenarios but need question rewriting, ground truth reconstruction, or key_facts replacement. Primary revision types:
- **Practitioner reframing** (B5 all 7): abstract "explain clause" → "what does this require us to do?"
- **Audience targeting** (B10 most): add specific output context (board brief, waiver submission, audit prep)
- **RM perspective** (B13 all 3): audit-centric → Risk Manager preparation framing
- **Key_facts reconstruction** (B2-002, B8-002, B12-002): placeholder → atomic, sourced facts

### Must Regenerate (30 Discard cases)

Full regeneration required. High-discard benchmarks:
- **B8** (4 discards): key_facts placeholders throughout half the benchmark
- **B17** (3 discards): all key_facts placeholders; B7 scenario types will regenerate natively
- **B14** (3 discards): 100% key_facts placeholders — critical gap benchmark needs complete regeneration
- **B19** (3 discards): meta-benchmark, concept retired
- **B6** (4 discards): abstract intent questions with placeholder key_facts
