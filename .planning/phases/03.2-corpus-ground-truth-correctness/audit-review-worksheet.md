# Ground-Truth Citation Audit — Flag Clusters for Review

**Total flags:** 192 across 55 unique (benchmark, citation) pairs

**All flags are HUMAN_REVIEW** — nearest-neighbour confidences too low (0.58-0.76) for auto-accept

## Executive Summary

| Cluster | Flags | Nature | Likely Decision |
|---------|-------|--------|-----------------|
| B08 `4.2.1` + `4.2` (Pass 1+2 on same 25 cases) | 50 | Entire benchmark cites non-existent clause; topic is "risk-based prioritization" — not in CCoP 2.0, lives in *Risk Assessment Guide* | **Deprecate OR re-anchor to Risk Assessment Guide** |
| B09 `4.2.1` | 25 | Same systemic issue as B08 | **Deprecate OR re-anchor** |
| B22 `11.7` | 20 | Ch 11 has only 11.1–11.2; topic is waiver/exception reasoning | **Deprecate OR re-anchor** |
| B24 `8.3`–`8.7` | 38 | Ch 8 has only 8.1–8.2; topic is incident response (actually CCoP Ch 7) | **Re-anchor to Chapter 7** |
| **B21 `*` (all 13 flags)** | 13 | **FALSE POSITIVES** — B21 is the hallucination-detection benchmark; its test cases intentionally cite non-existent clauses (col 7 = "Non-existent Clause") | **Mark audit-exempt; do NOT correct** |
| B07 misc, B02/B03/B05/B12 misc | 46 | Mix of real errors + audit parser edge cases | **Walk through per-case** |

### Critical: B21 is a designed hallucination benchmark, not broken data

13 flags in B21_HALLUCINATION_OVER_SPECIFICATION are by design — the benchmark's purpose is to verify the model refuses to answer invented clauses. These must NOT be "corrected". Recommend tagging B21 test cases with `audit_exempt: true` (or similar) so future audit runs skip them.

**Affected B21 flags:** B21-001, B21-004, B21-005, B21-008, B21-009, B21-010, B21-012, B21-016, B21-018, B21-019, B21-021 (+2 dupes via Pass 1/2)

Net real flags after excluding B21: **179**

---

## B08_RISK_BASED_PRIORITIZATION — citation `4.2.1` × 25

**NN suggestions:** `5.14.2`×17, `3.2.3`×5, `1`×2, `8.2`×1  
**Confidence:** 0.69–0.72

| Test ID | Pass | CCoP Section (col 7) | Clause Refs (col 8) | Question |
|---------|------|----------------------|---------------------|----------|
| B08-001 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a banking CII environment:  1. Shared admin accounts (likelihood: high, impact: h… |
| B08-002 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a energy CII environment:  1. MFA not enabled for vendor portal (likelihood: high… |
| B08-003 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a government CII environment:  1. Pen testing 6 months overdue (likelihood: mediu… |
| B08-004 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a healthcare CII environment:  1. Service accounts over-privileged (likelihood: m… |
| B08-005 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a telecommunications CII environment:  1. Emergency access undocumented (likeliho… |
| B08-006 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a transportation CII environment:  1. CSA reporting channel undefined (likelihood… |
| B08-007 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a energy CII environment:  1. OT systems unpatched 2 years (likelihood: high, imp… |
| B08-008 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a banking CII environment:  1. No privileged access review 3 years (likelihood: h… |
| B08-009 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a water CII environment:  1. SIEM excludes OT network (likelihood: high, impact: … |
| B08-010 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a transportation CII environment:  1. IT/OT convergence unmanaged (likelihood: hi… |
| B08-011 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a healthcare CII environment:  1. Incident response plan never tested (likelihood… |
| B08-012 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a government CII environment:  1. Data flow mapping incomplete (likelihood: mediu… |
| B08-013 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a telecommunications CII environment:  1. Encryption not implemented for internal… |
| B08-014 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a banking CII environment:  1. No network segmentation between zones (likelihood:… |
| B08-015 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a energy CII environment:  1. Physical access controls weak (likelihood: medium, … |
| B08-016 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a healthcare CII environment:  1. Vendor security assessments not performed (like… |
| B08-017 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a government CII environment:  1. No intrusion detection system (likelihood: medi… |
| B08-018 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a energy CII environment:  1. OT systems unpatched 2 years (likelihood: high, imp… |
| B08-019 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a banking CII environment:  1. No intrusion prevention on critical network (likel… |
| B08-020 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a telecommunications CII environment:  1. Business continuity plan untested (like… |
| B08-021 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a government CII environment:  1. Multiple shared admin accounts across departmen… |
| B08-022 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a water CII environment:  1. OT SCADA system end-of-life (likelihood: high, impac… |
| B08-023 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a healthcare CII environment:  1. Database encryption not implemented (likelihood… |
| B08-024 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a transportation CII environment:  1. No vulnerability management process (likeli… |
| B08-025 | Pass 1 | 4 | 4.2.1 | Given the following compliance gaps in a banking CII environment:  1. Board reporting on security gaps absent (likelihoo… |

**Decision per cluster:**
- [ ] REMAP all to `___` (provide single correct clause if there's a consistent right answer)
- [ ] REMAP per-case (multiple correct answers — walk through row-by-row)
- [ ] DEPRECATE all (test cases not supported by CCoP 2.0; remove from benchmark)
- [ ] Other: _______

---

## B08_RISK_BASED_PRIORITIZATION — citation `4.2` × 25

**NN suggestions:** `5.14.2`×17, `3.2.3`×5, `1`×2, `8.2`×1  
**Confidence:** 0.69–0.72

| Test ID | Pass | CCoP Section (col 7) | Clause Refs (col 8) | Question |
|---------|------|----------------------|---------------------|----------|
| B08-001 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a banking CII environment:  1. Shared admin accounts (likelihood: high, impact: h… |
| B08-002 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a energy CII environment:  1. MFA not enabled for vendor portal (likelihood: high… |
| B08-003 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a government CII environment:  1. Pen testing 6 months overdue (likelihood: mediu… |
| B08-004 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a healthcare CII environment:  1. Service accounts over-privileged (likelihood: m… |
| B08-005 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a telecommunications CII environment:  1. Emergency access undocumented (likeliho… |
| B08-006 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a transportation CII environment:  1. CSA reporting channel undefined (likelihood… |
| B08-007 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a energy CII environment:  1. OT systems unpatched 2 years (likelihood: high, imp… |
| B08-008 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a banking CII environment:  1. No privileged access review 3 years (likelihood: h… |
| B08-009 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a water CII environment:  1. SIEM excludes OT network (likelihood: high, impact: … |
| B08-010 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a transportation CII environment:  1. IT/OT convergence unmanaged (likelihood: hi… |
| B08-011 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a healthcare CII environment:  1. Incident response plan never tested (likelihood… |
| B08-012 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a government CII environment:  1. Data flow mapping incomplete (likelihood: mediu… |
| B08-013 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a telecommunications CII environment:  1. Encryption not implemented for internal… |
| B08-014 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a banking CII environment:  1. No network segmentation between zones (likelihood:… |
| B08-015 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a energy CII environment:  1. Physical access controls weak (likelihood: medium, … |
| B08-016 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a healthcare CII environment:  1. Vendor security assessments not performed (like… |
| B08-017 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a government CII environment:  1. No intrusion detection system (likelihood: medi… |
| B08-018 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a energy CII environment:  1. OT systems unpatched 2 years (likelihood: high, imp… |
| B08-019 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a banking CII environment:  1. No intrusion prevention on critical network (likel… |
| B08-020 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a telecommunications CII environment:  1. Business continuity plan untested (like… |
| B08-021 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a government CII environment:  1. Multiple shared admin accounts across departmen… |
| B08-022 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a water CII environment:  1. OT SCADA system end-of-life (likelihood: high, impac… |
| B08-023 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a healthcare CII environment:  1. Database encryption not implemented (likelihood… |
| B08-024 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a transportation CII environment:  1. No vulnerability management process (likeli… |
| B08-025 | Pass 2 | 4 | 4.2.1 | Given the following compliance gaps in a banking CII environment:  1. Board reporting on security gaps absent (likelihoo… |

**Decision per cluster:**
- [ ] REMAP all to `___` (provide single correct clause if there's a consistent right answer)
- [ ] REMAP per-case (multiple correct answers — walk through row-by-row)
- [ ] DEPRECATE all (test cases not supported by CCoP 2.0; remove from benchmark)
- [ ] Other: _______

---

## B09_RISK_IDENTIFICATION_RESIDUAL_RISK — citation `4.2.1` × 25

**NN suggestions:** `3.2.2`×8, `3.2.5`×4, `1`×3, `8.2`×2, `10.2`×1, `5.10`×1, `5.9.1`×1, `7.3.3`×1, `5.5`×1, `5.10.1`×1, `9`×1, `3.2.3`×1  
**Confidence:** 0.65–0.76

| Test ID | Pass | CCoP Section (col 7) | Clause Refs (col 8) | Question |
|---------|------|----------------------|---------------------|----------|
| B09-001 | Pass 1 | 4 | 4.2.1 | **Risk Identification for Config analysis - missing MFA:**  **Configuration Analysis:** Critical systems: Database serve… |
| B09-002 | Pass 1 | 4 | 4.2.1 | **Risk Identification for Config analysis - OT flat network:**  **Configuration Analysis:** OT network: Single broadcast… |
| B09-003 | Pass 1 | 4 | 4.2.1 | **Risk Identification for Config analysis - excessive privileges:**  **Configuration Analysis:** Service account 'svc_ap… |
| B09-004 | Pass 1 | 4 | 4.2.1 | **Risk Identification for Config analysis - logging gaps:**  **Configuration Analysis:** Security devices: Firewall (log… |
| B09-005 | Pass 1 | 4 | 4.2.1 | **Risk Identification for Config analysis - vendor access:**  **Configuration Analysis:** Third-party access: Vendor A (… |
| B09-006 | Pass 1 | 4 | 4.2.1 | **Risk Identification for Config analysis - encryption gaps:**  **Configuration Analysis:** Data flows: Database to App … |
| B09-007 | Pass 1 | 4 | 4.2.1 | **Risk Identification for Config analysis - patch management:**  **Configuration Analysis:** Patch status: Critical vuln… |
| B09-008 | Pass 1 | 4 | 4.2.1 | **Risk Identification for Config analysis - network exposure:**  **Configuration Analysis:** Internet-facing services: R… |
| B09-009 | Pass 1 | 4 | 4.2.1 | **Risk Identification for Config analysis - physical security:**  **Configuration Analysis:** Data center access: Badge … |
| B09-010 | Pass 1 | 4 | 4.2.1 | **Risk Identification for Config analysis - incident response:**  **Configuration Analysis:** IR capabilities: Plan docu… |
| B09-011 | Pass 1 | 4 | 4.2.1 | **Risk Identification for Config analysis - business continuity:**  **Configuration Analysis:** BCP status: Plan exists,… |
| B09-012 | Pass 1 | 4 | 4.2.1 | **Risk Identification for Config analysis - data classification:**  **Configuration Analysis:** Data handling: All data … |
| B09-013 | Pass 1 | 4 | 4.2.1 | **Risk Identification for Config analysis - change management:**  **Configuration Analysis:** Change process: No approva… |
| B09-014 | Pass 1 | 4 | 4.2.1 | **Residual Risk Assessment for Residual risk after MFA implementation:**  **Controls Implemented:** MFA enabled for all … |
| B09-015 | Pass 1 | 4 | 4.2.1 | **Residual Risk Assessment for Residual risk after network segmentation:**  **Controls Implemented:** VLANs implemented,… |
| B09-016 | Pass 1 | 4 | 4.2.1 | **Residual Risk Assessment for Residual risk after encryption implementation:**  **Controls Implemented:** AES-256 encry… |
| B09-017 | Pass 1 | 4 | 4.2.1 | **Residual Risk Assessment for Residual risk after SIEM deployment:**  **Controls Implemented:** Comprehensive log colle… |
| B09-018 | Pass 1 | 4 | 4.2.1 | **Residual Risk Assessment for Residual risk after patching program:**  **Controls Implemented:** Monthly vulnerability … |
| B09-019 | Pass 1 | 4 | 4.2.1 | **Residual Risk Assessment for Residual risk after vendor management:**  **Controls Implemented:** Vendor security asses… |
| B09-020 | Pass 1 | 4 | 4.2.1 | **Residual Risk Assessment for Residual risk after incident response preparation:**  **Controls Implemented:** Documente… |
| B09-021 | Pass 1 | 4 | 4.2.1 | **Residual Risk Assessment for Residual risk after security awareness training:**  **Controls Implemented:** Annual trai… |
| B09-022 | Pass 1 | 4 | 4.2.1 | **Residual Risk Assessment for Residual risk after physical security upgrades:**  **Controls Implemented:** Badge access… |
| B09-023 | Pass 1 | 4 | 4.2.1 | **Residual Risk Assessment for Residual risk after backup implementation:**  **Controls Implemented:** Daily automated b… |
| B09-024 | Pass 1 | 4 | 4.2.1 | **Residual Risk Assessment for Residual risk after access control implementation:**  **Controls Implemented:** Least pri… |
| B09-025 | Pass 1 | 4 | 4.2.1 | **Residual Risk Assessment for Residual risk after penetration testing and remediation:**  **Controls Implemented:** Ann… |

**Decision per cluster:**
- [ ] REMAP all to `___` (provide single correct clause if there's a consistent right answer)
- [ ] REMAP per-case (multiple correct answers — walk through row-by-row)
- [ ] DEPRECATE all (test cases not supported by CCoP 2.0; remove from benchmark)
- [ ] Other: _______

---

## B22_WAIVER_EXCEPTION_REASONING — citation `11.7` × 20

**NN suggestions:** `3.7.3`×6, `3.2.3`×4, `1.2.1`×2, `1`×2, `6.1.4`×1, `5.6.1`×1, `3.8.1`×1, `7.1.7`×1, `3.2.5`×1, `7.1.4`×1  
**Confidence:** 0.65–0.73

| Test ID | Pass | CCoP Section (col 7) | Clause Refs (col 8) | Question |
|---------|------|----------------------|---------------------|----------|
| B22-001 | Pass 1 | 11 | 11.7 | Can a CII operator apply for a waiver for MFA requirements on legacy SCADA systems? |
| B22-002 | Pass 1 | 11 | 11.7 | Is cost a valid justification for a waiver from log retention requirements? |
| B22-003 | Pass 1 | 11 | 11.7 | Can limited staff justify a waiver from quarterly access review requirements? |
| B22-004 | Pass 1 | 11 | 11.7 | What is the waiver process for OT systems that cannot be patched during active operations? |
| B22-005 | Pass 1 | 11 | 11.7 | Can lack of in-house CISO expertise justify outsourcing the CISO role? |
| B22-006 | Pass 1 | 11 | 11.7 | How should a waiver request be structured when encryption breaks legacy systems? |
| B22-007 | Pass 1 | 11 | 11.7 | What happens when CCoP requirements conflict with another regulator's requirements? |
| B22-008 | Pass 1 | 11 | 11.7 | Can a waiver apply to only part of a system rather than the entire CII system? |
| B22-009 | Pass 1 | 11 | 11.7 | What options exist when vendor contract prevents CCoP-required controls? |
| B22-010 | Pass 1 | 11 | 11.7 | What is required for waiver renewal and how does it differ from initial application? |
| B22-011 | Pass 1 | 11 | 11.7 | Does bypassing security controls during emergency constitute a waiver? |
| B22-012 | Pass 1 | 11 | 11.7 | Should separate waivers be filed for each non-compliant area or one comprehensive waiver? |
| B22-013 | Pass 1 | 11 | 11.7 | What waiver approach works for legacy OT protocols with no security features? |
| B22-014 | Pass 1 | 11 | 11.7 | Physical constraints preventing security equipment installation - is this waivable? |
| B22-015 | Pass 1 | 11 | 11.7 | What happens when CSA denies a waiver application? |
| B22-016 | Pass 1 | 11 | 11.7 | What conditions might CSA attach to granting a waiver? |
| B22-017 | Pass 1 | 11 | 11.7 | CII system needs immediate replacement for security reasons but budget not available until next fiscal year - can waiver… |
| B22-018 | Pass 1 | 11 | 11.7 | How should a waiver application address conflicting consultant recommendations? |
| B22-019 | Pass 1 | 11 | 11.7 | What if vendor supply chain issues prevent implementing required controls within CSA timeline? |
| B22-020 | Pass 1 | 11 | 11.7 | Can limited overnight staff justify waiving the 2-hour critical incident notification requirement? |

**Decision per cluster:**
- [ ] REMAP all to `___` (provide single correct clause if there's a consistent right answer)
- [ ] REMAP per-case (multiple correct answers — walk through row-by-row)
- [ ] DEPRECATE all (test cases not supported by CCoP 2.0; remove from benchmark)
- [ ] Other: _______

---

## B24_INCIDENT_RESPONSE_GUIDANCE — citation `8.4` × 15

**NN suggestions:** `7.3.5`×3, `preamble`×2, `5.14.5`×2, `7.1.6`×2, `7.1.1`×1, `3.2.3`×1, `1`×1, `1.2.1`×1, `5.14.3`×1, `6.3.3`×1  
**Confidence:** 0.62–0.70

| Test ID | Pass | CCoP Section (col 7) | Clause Refs (col 8) | Question |
|---------|------|----------------------|---------------------|----------|
| B24-001 | Pass 1 | CCoP 2.0 Section 8 | 8.2,8.4 | Our healthcare CII has detected a ransomware attack on patient record systems. Data is encrypted and a ransom note deman… |
| B24-002 | Pass 1 | CCoP 2.0 Section 8 | 8.2,8.4 | A water utility CII discovered ransomware on SCADA systems controlling water distribution. The attack encrypted historic… |
| B24-003 | Pass 1 | CCoP 2.0 Section 8 | 8.3,8.4,8.7 | Our bank's payment processing system is hit by ransomware. Transaction processing halted for 30 minutes before failover … |
| B24-004 | Pass 1 | CCoP 2.0 Section 8 | 8.2,8.4 | A transportation CII discovers ransomware on administrative systems only. Operational systems (train control, signaling)… |
| B24-006 | Pass 1 | CCoP 2.0 Section 8 | 8.3,8.4,8.6 | A telecom CII discovers customer data exfiltration: 50,000 records including names, addresses, phone numbers accessed. N… |
| B24-007 | Pass 1 | CCoP 2.0 Section 8 | 8.2,8.3,8.4 | Government CII agency discovers unauthorized access to employee directory: names, positions, email addresses of 500 empl… |
| B24-008 | Pass 1 | CCoP 2.0 Section 8 | 8.4 | Energy CII discovers SCADA system configuration files were accessed remotely. No operational disruption occurred, no cha… |
| B24-009 | Pass 1 | CCoP 2.0 Section 8 | 8.4,8.6,8.7 | Healthcare CII discovers a database backup was exposed on internet for 48 hours before being secured. The backup contain… |
| B24-010 | Pass 1 | CCoP 2.0 Section 8 | 8.4,8.6 | A CII organization discovers data breach but cannot determine if data was exfiltrated. Logs show unauthorized access but… |
| B24-012 | Pass 1 | CCoP 2.0 Section 8 | 8.3,8.4 | Air traffic control system experiences intermittent disruptions: 30-minute outages 3 times in one day. Investigation rev… |
| B24-014 | Pass 1 | CCoP 2.0 Section 8 | 8.4,8.6 | Energy CII's SCADA system loses visibility into 20% of substations due to network failure. Operators cannot monitor or c… |
| B24-015 | Pass 1 | CCoP 2.0 Section 8 | 8.2,8.4 | Water utility's remote telemetry systems stop sending data from 15 pumping stations. Central control can no longer monit… |
| B24-019 | Pass 1 | CCoP 2.0 Section 8 | 8.4,8.6 | CII staff member reports receiving targeted phishing emails that appear to be from internal IT department. Several staff… |
| B24-020 | Pass 1 | CCoP 2.0 Section 8 | 8.4,9.4 | A CII system administrator accidentally deletes production database during maintenance. No backup available. 48 hours of… |
| B24-024 | Pass 1 | CCoP 2.0 Section 8 | 8.2,8.3,8.4 | CII organization experiences simultaneous incidents: DDoS attack on web systems AND ransomware on internal systems AND t… |

**Decision per cluster:**
- [ ] REMAP all to `___` (provide single correct clause if there's a consistent right answer)
- [ ] REMAP per-case (multiple correct answers — walk through row-by-row)
- [ ] DEPRECATE all (test cases not supported by CCoP 2.0; remove from benchmark)
- [ ] Other: _______

---

## B24_INCIDENT_RESPONSE_GUIDANCE — citation `8.3` × 11

**NN suggestions:** `preamble`×2, `5.14.5`×2, `1.2.1`×2, `7.1.1`×1, `7.3.5`×1, `5.16.3`×1, `6.3.3`×1, `2.1`×1  
**Confidence:** 0.58–0.70

| Test ID | Pass | CCoP Section (col 7) | Clause Refs (col 8) | Question |
|---------|------|----------------------|---------------------|----------|
| B24-003 | Pass 1 | CCoP 2.0 Section 8 | 8.3,8.4,8.7 | Our bank's payment processing system is hit by ransomware. Transaction processing halted for 30 minutes before failover … |
| B24-005 | Pass 1 | CCoP 2.0 Section 8 | 8.2,8.3 | Ransomware attack detected during weekend. IR team is unavailable. System admin wants to pay ransom quickly to restore o… |
| B24-006 | Pass 1 | CCoP 2.0 Section 8 | 8.3,8.4,8.6 | A telecom CII discovers customer data exfiltration: 50,000 records including names, addresses, phone numbers accessed. N… |
| B24-007 | Pass 1 | CCoP 2.0 Section 8 | 8.2,8.3,8.4 | Government CII agency discovers unauthorized access to employee directory: names, positions, email addresses of 500 empl… |
| B24-012 | Pass 1 | CCoP 2.0 Section 8 | 8.3,8.4 | Air traffic control system experiences intermittent disruptions: 30-minute outages 3 times in one day. Investigation rev… |
| B24-016 | Pass 1 | CCoP 2.0 Section 8 | 8.3,8.6 | A CII employee is found to have exported proprietary system designs to personal cloud storage before resigning. No evide… |
| B24-017 | Pass 1 | CCoP 2.0 Section 8 | 7.2,8.3,8.6 | A third-party vendor with remote access to CII systems experiences their own security breach. Attacker may have used ven… |
| B24-018 | Pass 1 | CCoP 2.0 Section 8 | 7.3,8.3,8.6 | A former contractor's credentials were still active 3 months after contract ended. Recent log analysis shows those crede… |
| B24-021 | Pass 1 | CCoP 2.0 Section 8 | 7.2,8.3 | CII organization discovers they've been communicating with a fake vendor for 6 months. Sensitive system diagrams and sec… |
| B24-024 | Pass 1 | CCoP 2.0 Section 8 | 8.2,8.3,8.4 | CII organization experiences simultaneous incidents: DDoS attack on web systems AND ransomware on internal systems AND t… |
| B24-025 | Pass 1 | CCoP 2.0 Section 8 | 5.2,8.3,8.6,8.7 | CII organization discovers incident that occurred 6 months ago, undetected at time. Logs show attacker had persistent ac… |

**Decision per cluster:**
- [ ] REMAP all to `___` (provide single correct clause if there's a consistent right answer)
- [ ] REMAP per-case (multiple correct answers — walk through row-by-row)
- [ ] DEPRECATE all (test cases not supported by CCoP 2.0; remove from benchmark)
- [ ] Other: _______

---

## B24_INCIDENT_RESPONSE_GUIDANCE — citation `8.6` × 9

**NN suggestions:** `5.14.5`×3, `1.2.1`×2, `1`×1, `5.16.3`×1, `7.3.5`×1, `2.1`×1  
**Confidence:** 0.61–0.68

| Test ID | Pass | CCoP Section (col 7) | Clause Refs (col 8) | Question |
|---------|------|----------------------|---------------------|----------|
| B24-006 | Pass 1 | CCoP 2.0 Section 8 | 8.3,8.4,8.6 | A telecom CII discovers customer data exfiltration: 50,000 records including names, addresses, phone numbers accessed. N… |
| B24-009 | Pass 1 | CCoP 2.0 Section 8 | 8.4,8.6,8.7 | Healthcare CII discovers a database backup was exposed on internet for 48 hours before being secured. The backup contain… |
| B24-010 | Pass 1 | CCoP 2.0 Section 8 | 8.4,8.6 | A CII organization discovers data breach but cannot determine if data was exfiltrated. Logs show unauthorized access but… |
| B24-014 | Pass 1 | CCoP 2.0 Section 8 | 8.4,8.6 | Energy CII's SCADA system loses visibility into 20% of substations due to network failure. Operators cannot monitor or c… |
| B24-016 | Pass 1 | CCoP 2.0 Section 8 | 8.3,8.6 | A CII employee is found to have exported proprietary system designs to personal cloud storage before resigning. No evide… |
| B24-017 | Pass 1 | CCoP 2.0 Section 8 | 7.2,8.3,8.6 | A third-party vendor with remote access to CII systems experiences their own security breach. Attacker may have used ven… |
| B24-018 | Pass 1 | CCoP 2.0 Section 8 | 7.3,8.3,8.6 | A former contractor's credentials were still active 3 months after contract ended. Recent log analysis shows those crede… |
| B24-019 | Pass 1 | CCoP 2.0 Section 8 | 8.4,8.6 | CII staff member reports receiving targeted phishing emails that appear to be from internal IT department. Several staff… |
| B24-025 | Pass 1 | CCoP 2.0 Section 8 | 5.2,8.3,8.6,8.7 | CII organization discovers incident that occurred 6 months ago, undetected at time. Logs show attacker had persistent ac… |

**Decision per cluster:**
- [ ] REMAP all to `___` (provide single correct clause if there's a consistent right answer)
- [ ] REMAP per-case (multiple correct answers — walk through row-by-row)
- [ ] DEPRECATE all (test cases not supported by CCoP 2.0; remove from benchmark)
- [ ] Other: _______

---

## Medium clusters (2–8 flags each, 23 total)

| Benchmark | Citation | Count | NN range | Test IDs |
|-----------|----------|-------|----------|----------|
| B02_COMPLIANCE_CLASSIFICATION | `5.6.4` | 4 | 1.1.1 … 3.2.3 (0.65–0.71) | B2-003, B2-010, B2-014, B2-024 |
| B07_GAP_IDENTIFICATION_QUALITY | `4.2.2` | 4 | 4.1.1 … 7.1.4 (0.64–0.72) | B07-001, B07-002, B07-003, B07-005 |
| B24_INCIDENT_RESPONSE_GUIDANCE | `8.7` | 3 | 2.1 … preamble (0.62–0.67) | B24-003, B24-009, B24-025 |
| B03_CONDITIONAL_COMPLIANCE_REASONING | `11.7` | 2 | 1.6.2 … 5.8.1 (0.62–0.64) | B3-004, B3-011 |
| B03_CONDITIONAL_COMPLIANCE_REASONING | `4.2` | 2 | 5.10.1 … 8.2.1 (0.64–0.64) | B3-006, B3-021 |
| B05_CONTROL_COMPREHENSION | `5.2.3` | 2 | 5.3.1 … 5.8.1 (0.68–0.72) | B05-002, B05-019 |
| B07_GAP_IDENTIFICATION_QUALITY | `5.2.4` | 2 | 5.9.2 … 7.1.4 (0.63–0.64) | B07-006, B07-008 |
| B21_HALLUCINATION_OVER_SPECIFICATION | `5.3.2` | 2 | 1.2.1 … 5.12.1 (0.61–0.69) | B21-001, B21-012 |
| B24_INCIDENT_RESPONSE_GUIDANCE | `9.5` | 2 | 8.2.1 … 8.2.1 (0.67–0.73) | B24-011, B24-013 |

## Singletons (39 unique flags)

| Test ID | Benchmark | Pass | Citation | Suggested NN | Conf | CCoP Section | Clause Refs |
|---------|-----------|------|----------|--------------|------|--------------|-------------|
| B1-001 | B01_CCOP_APPLICABILITY_SCOPE | Pass 2 | `2.3` | `5.12.1` | 0.69 | CCoP 2.0 Scope | Section 11 Cybersecurity Act, RESPONSE-T |
| B1-017 | B01_CCOP_APPLICABILITY_SCOPE | Pass 1 | `CCoP 2.0 Section 5.1.5` | `5.3.1` | 0.66 | Section 5: Protection | CCoP 2.0 Section 5.1.5, CCoP 2.0 Section |
| B2-001 | B02_COMPLIANCE_CLASSIFICATION | Pass 1 | `5.1.5` | `10.2.3` | 0.67 | Section 5: Protection | 5.1.5 |
| B3-005 | B03_CONDITIONAL_COMPLIANCE_REASONING | Pass 1 | `5.3.2` | `5.1.4` | 0.64 | 5 | 5.3.2 |
| B3-019 | B03_CONDITIONAL_COMPLIANCE_REASONING | Pass 1 | `8.5` | `7.3.3` | 0.72 | 8 | 8.5 |
| B3-024 | B03_CONDITIONAL_COMPLIANCE_REASONING | Pass 1 | `9.4` | `8.1.4` | 0.73 | 9 | 9.4 |
| B05-013 | B05_CONTROL_COMPREHENSION | Pass 1 | `4.3` | `3.2.3` | 0.63 | 4 | 4.3 |
| B05-016 | B05_CONTROL_COMPREHENSION | Pass 1 | `5.3.4` | `8.2.1` | 0.63 | 5 | 5.3.4 |
| B05-018 | B05_CONTROL_COMPREHENSION | Pass 1 | `5.5.5` | `1.2.1` | 0.66 | 5 | 5.5.5 |
| B05-015 | B05_CONTROL_COMPREHENSION | Pass 1 | `9.3.1` | `9.2.3` | 0.67 | 9 | 9.3.1 |
| B06-019 | B06_INTENT_UNDERSTANDING | Pass 1 | `4.2.1` | `3.2.2` | 0.66 | 4 | 4.2.1 |
| B06-002 | B06_INTENT_UNDERSTANDING | Pass 1 | `5.2.3` | `5.1` | 0.62 | 5 | 5.2.3 |
| B06-013 | B06_INTENT_UNDERSTANDING | Pass 1 | `5.2.5` | `5.3` | 0.61 | 5 | 5.2.5 |
| B06-018 | B06_INTENT_UNDERSTANDING | Pass 1 | `7.4.1` | `8.2.1` | 0.72 | 7 | 7.4.1 |
| B07-027 | B07_GAP_IDENTIFICATION_QUALITY | Pass 1 | `5.2.3` | `7.1.4` | 0.63 | 5 | 5.2.3 |
| B07-007 | B07_GAP_IDENTIFICATION_QUALITY | Pass 1 | `5.2.5` | `5.3.1` | 0.63 | 5 | 5.2.5 |
| B07-010 | B07_GAP_IDENTIFICATION_QUALITY | Pass 1 | `5.2.6` | `7.1.4` | 0.63 | 5 | 5.2.6 |
| B07-017 | B07_GAP_IDENTIFICATION_QUALITY | Pass 1 | `5.4.2` | `10.2` | 0.69 | 5 | 5.4.2 |
| B07-018 | B07_GAP_IDENTIFICATION_QUALITY | Pass 1 | `5.4.4` | `10` | 0.69 | 5 | 5.4.4 |
| B07-015 | B07_GAP_IDENTIFICATION_QUALITY | Pass 1 | `6.3.4` | `10.4.4` | 0.65 | 6 | 6.3.4 |
| B12-020 | B12_AUDIT_PERSPECTIVE_ALIGNMENT | Pass 1 | `4.2.1` | `1` | 0.74 | 4 | 4.2.1 |
| B12-005 | B12_AUDIT_PERSPECTIVE_ALIGNMENT | Pass 1 | `4.2.2` | `4.1` | 0.75 | 4 | 4.2.2 |
| B12-001 | B12_AUDIT_PERSPECTIVE_ALIGNMENT | Pass 1 | `5.2.3` | `1` | 0.69 | 5 | 5.2.3 |
| B12-014 | B12_AUDIT_PERSPECTIVE_ALIGNMENT | Pass 1 | `5.2.5` | `5.6.1` | 0.71 | 5 | 5.2.5 |
| B12-008 | B12_AUDIT_PERSPECTIVE_ALIGNMENT | Pass 1 | `7.4.1` | `8.2.1` | 0.71 | 7 | 7.4.1 |
| B12-016 | B12_AUDIT_PERSPECTIVE_ALIGNMENT | Pass 1 | `9.3.1` | `1` | 0.68 | 9 | 9.3.1 |
| B21-008 | B21_HALLUCINATION_OVER_SPECIFICATION | Pass 2 | `11.7.5` | `1.2.1` | 0.65 | Non-existent Clause | N/A |
| B21-021 | B21_HALLUCINATION_OVER_SPECIFICATION | Pass 1 | `4.2` | `3.7` | 0.74 | Section 4: Governance | 4.2 |
| B21-010 | B21_HALLUCINATION_OVER_SPECIFICATION | Pass 2 | `4.2.6` | `5.12.1` | 0.71 | Non-existent Clause | N/A |
| B21-018 | B21_HALLUCINATION_OVER_SPECIFICATION | Pass 1 | `5.1.5` | `10.2.3` | 0.66 | Section 5: Protection | 5.1.5 |
| B21-012 | B21_HALLUCINATION_OVER_SPECIFICATION | Pass 2 | `5.3.5` | `5.12.1` | 0.69 | Section 5: Protection | 5.3.2 |
| B21-009 | B21_HALLUCINATION_OVER_SPECIFICATION | Pass 1 | `5.7.3` | `5.15.2` | 0.74 | Section 5: Protection | 5.7.3 |
| B21-001 | B21_HALLUCINATION_OVER_SPECIFICATION | Pass 2 | `5.9.7` | `1.2.1` | 0.61 | Non-existent Clause | N/A |
| B21-016 | B21_HALLUCINATION_OVER_SPECIFICATION | Pass 2 | `7.4.3` | `9.2.4` | 0.77 | Section 7: People | 7.2 |
| B21-004 | B21_HALLUCINATION_OVER_SPECIFICATION | Pass 2 | `8.5.2` | `7.3.2` | 0.76 | Section 7: People | 7.3 |
| B21-019 | B21_HALLUCINATION_OVER_SPECIFICATION | Pass 1 | `9.3` | `8.2` | 0.77 | Section 9: Recovery | 9.3 |
| B21-005 | B21_HALLUCINATION_OVER_SPECIFICATION | Pass 1 | `9.4.1` | `8.1.4` | 0.74 | Section 9: Recovery | 9.4.1 |
| B24-023 | B24_INCIDENT_RESPONSE_GUIDANCE | Pass 1 | `8.5` | `5.15.3` | 0.67 | CCoP 2.0 Section 8 | 8.5 |
| B24-020 | B24_INCIDENT_RESPONSE_GUIDANCE | Pass 1 | `9.4` | `7.1.6` | 0.65 | CCoP 2.0 Section 8 | 8.4,9.4 |