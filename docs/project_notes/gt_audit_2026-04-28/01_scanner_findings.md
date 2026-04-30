# GT Consistency Audit Report

Scanned **435 test cases** across **18 benchmark files**.
Flagged **90 test cases** with potential inconsistencies.

---

## Flagged test cases

### `b01_ccop_applicability_scope.jsonl` — 2 flagged

#### `B01-001`

**Reasons:**
- key_facts.source family ['2'] disjoint from clause_reference family ['1']
- expected_response family ['2'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> CCoP 2.0 mandatory compliance applies only to systems within the digital boundary of the designated CII — in this case, the patient monitoring systems and MRI machines. The hospital administration system (patient records, billing, appointments) falls outside mandatory CCoP scope unless it is also de

**clause_reference:** `['1.2.1', '1.4.1']`
**Clauses extracted from expected_response:** `['2.3']`
**Section families across all GT fields:** `['1', '2']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 2, Cybersecurity Act Section 11` → clauses=`['2']` — fact: "CCoP 2.0 mandatory compliance applies only to systems within the digital boundary of the designated CII, not all systems"
- [critical] source=`CCoP 2.0 Scope section, RESPONSE-TO-FEEDBACK Q2.2-2.3` → clauses=`['2.3']` — fact: "The digital boundary is jointly determined by CSA, the CIIO, and the Sector Lead — it is not the enterprise network peri"
- [important] source=`RESPONSE-TO-FEEDBACK Q2.2-2.3` → clauses=`['2.3']` — fact: "CSA recommends extending CCoP cybersecurity capabilities organization-wide even beyond mandatory scope"
- [supporting] source=`CCoP 2.0 Section 2` → clauses=`['2']` — fact: "Systems outside the digital boundary are not subject to mandatory CCoP 2.0 cybersecurity audits"

#### `B01-012`

**Reasons:**
- key_facts.source family ['5'] disjoint from clause_reference family ['11']

**Expected response excerpt:**
> CCoP 2.0 compliance obligations rest with the Singapore subsidiary as the designated CIIO, but those obligations extend to how the CII is managed regardless of where management occurs. The US parent company's security operations — to the extent they affect the Singapore CII — must comply with CCoP 2

**clause_reference:** `['Section 11 Cybersecurity Act', 'CCoP 2.0 supply chain clauses']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['11', '5']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11, Regulatory interpretation` → clauses=`[]` — fact: "CCoP 2.0 obligations rest with the Singapore subsidiary as the designated CIIO — accountability cannot be delegated to a"
- [critical] source=`CCoP 2.0 supply chain requirements` → clauses=`[]` — fact: "CCoP 2.0 requires vendor and third-party access to CII to be performed on-site in Singapore unless explicitly approved"
- [important] source=`CCoP 2.0 Section 5 Protection` → clauses=`['5']` — fact: "Remote access by US parent security operations must satisfy CCoP 2.0 access control, MFA, and monitoring requirements"
- [supporting] source=`Cybersecurity Act Section 11` → clauses=`[]` — fact: "The Singapore CIIO must maintain oversight and accountability for security operations affecting the CII regardless of wh"

### `b03_conditional_compliance_reasoning.jsonl` — 3 flagged

#### `B03-004`

**Reasons:**
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> Legacy systems without MFA support require a waiver under Section 11(7). Isolation on a separate VLAN is an appropriate compensating control, but does not exempt the organization from pursuing the waiver. The waiver application must document genuine technical infeasibility and include a migration pl

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11(7)']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`CCoP 2.0` → clauses=`[]` — fact: "CCoP 2.0 requirements are mandatory for CII organizations"
- [important] source=`CCoP 2.0 principles` → clauses=`[]` — fact: "Compliance requires meeting all specified controls"

#### `B03-011`

**Reasons:**
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> Regulatory postponement is not a CCoP exemption. Section 11(7) requires a formal waiver application with documented technical constraints. COVID-19 urgency does not automatically exempt compliance. Compensating controls must be implemented during any grace period.

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11(7)']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`CCoP 2.0` → clauses=`[]` — fact: "CCoP 2.0 requirements are mandatory for CII organizations"
- [important] source=`CCoP 2.0 principles` → clauses=`[]` — fact: "Compliance requires meeting all specified controls"

#### `B03-023`

**Reasons:**
- expected_response family ['11'] disjoint from clause_reference family ['5']

**Expected response excerpt:**
> Permanent MFA exemptions for executives do not comply with CCoP 5.3.1. MFA is mandatory for CII systems. Executive convenience is not a valid exemption criterion. If technical barriers genuinely exist, a Section 11(7) waiver is required. Usability complaints do not justify exemption.

**clause_reference:** `['5.3.1(c)']`
**Clauses extracted from expected_response:** `['11(7)']`
**Section families across all GT fields:** `['11', '5']`

**key_facts:**
- [critical] source=`CCoP 2.0` → clauses=`[]` — fact: "CCoP 2.0 requirements are mandatory for CII organizations"
- [important] source=`CCoP 2.0 principles` → clauses=`[]` — fact: "Compliance requires meeting all specified controls"

### `b04_it_ot_classification_boundary.jsonl` — 2 flagged

#### `B04-008`

**Reasons:**
- expected_response family ['10'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> CCoP 2.0 applies to computer systems and digital security. A purely mechanical floodgate control system with no digital or electronic components falls outside CCoP 2.0 scope entirely. CCoP 2.0 Section 10 addresses OT security for computer-based systems that monitor and control physical processes - S

**clause_reference:** `['Section 1', 'Scope definition']`
**Clauses extracted from expected_response:** `['10']`
**Section families across all GT fields:** `['1', '10']`

**key_facts:**
- [critical] source=`CCoP 2.0 Scope, Section 1` → clauses=`['1']` — fact: "CCoP 2.0 applies to computer systems and digital security, not purely mechanical systems"
- [critical] source=`CCoP 2.0 Section 10.1` → clauses=`['10.1']` — fact: "Section 10 OT security covers computer-based industrial control systems"
- [important] source=`CCoP 2.0 Scope definition` → clauses=`[]` — fact: "Purely mechanical controls without digital components are outside CCoP 2.0 scope"
- [supporting] source=`CCoP 2.0 Scope definition` → clauses=`[]` — fact: "Digital systems supporting physical operations would still be in scope"

#### `B04-018`

**Reasons:**
- key_facts.source family ['10'] disjoint from clause_reference family ['6']

**Expected response excerpt:**
> The SIEM (Security Information and Event Management) system is classified as IT under CCoP 2.0. While it collects logs from both IT and OT sources, the SIEM itself performs data management and analysis functions - it is not directly controlling physical processes. CCoP 2.0 Section 10 applies to syst

**clause_reference:** `['6.2.1', '6.1.3']`
**Clauses extracted from expected_response:** `['10', '6']`
**Section families across all GT fields:** `['10', '6']`

**key_facts:**
- [critical] source=`CCoP 2.0 Sections 5, 6` → clauses=`[]` — fact: "SIEM performs data management and analysis - IT classification regardless of data sources"
- [critical] source=`CCoP 2.0 Sections 6, 10` → clauses=`[]` — fact: "Monitoring security events (information about systems) vs monitoring physical processes"
- [important] source=`CCoP 2.0 Section 10.2.3` → clauses=`['10.2.3']` — fact: "OT data sources create IT/OT boundary considerations but don't change SIEM classification"
- [supporting] source=`CCoP 2.0 Section 10.2, Regulatory interpretation` → clauses=`['10.2']` — fact: "SIEM could be used as pivot to attack OT - boundary protection required"

### `b05_control_comprehension.jsonl` — 2 flagged

#### `B05-013`

**Reasons:**
- key_facts.source family ['4'] disjoint from clause_reference family ['1', '10']

**Expected response excerpt:**
> According to CCoP 2.0 Section 1.6 (Waiver), legacy system exemptions requirements are as follows:

No blanket exemptions for legacy (critical) Compensating controls required if not compliant (critical) Must document risk and mitigation plan (important).

The intent of this control is to ensure adequ

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3', '10.2.7']`
**Clauses extracted from expected_response:** `['1.6']`
**Section families across all GT fields:** `['1', '10', '4']`

**key_facts:**
- [critical] source=`CCoP 2.0 4.3` → clauses=`['4.3']` — fact: "No blanket exemptions for legacy"
- [critical] source=`CCoP 2.0 4.3` → clauses=`['4.3']` — fact: "Compensating controls required if not compliant"
- [important] source=`CCoP 2.0 4.3` → clauses=`['4.3']` — fact: "Must document risk and mitigation plan"

#### `B05-015`

**Reasons:**
- key_facts.source family ['9'] disjoint from clause_reference family ['3']

**Expected response excerpt:**
> According to CCoP 2.0 Section 3.8, supply chain control verification requirements are as follows:

Verify software authenticity and integrity (critical) Source code escrow for critical vendors (important) Vendor security assessment required (critical).

The intent of this control is to ensure adequa

**clause_reference:** `['3.8.1', '3.8.2', '3.8.3']`
**Clauses extracted from expected_response:** `['3.8']`
**Section families across all GT fields:** `['3', '9']`

**key_facts:**
- [critical] source=`CCoP 2.0 9.3.1` → clauses=`['9.3.1']` — fact: "Verify software authenticity and integrity"
- [important] source=`CCoP 2.0 9.3.1` → clauses=`['9.3.1']` — fact: "Source code escrow for critical vendors"
- [critical] source=`CCoP 2.0 9.3.1` → clauses=`['9.3.1']` — fact: "Vendor security assessment required"

### `b06_intent_understanding.jsonl` — 2 flagged

#### `B06-018`

**Reasons:**
- key_facts.source family ['7'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> The primary security intent of CCoP 2.0 Section 8.2 regarding business continuity - resilience is: Ensure essential functions despite successful cyber attacks.

This intent is achieved through:
- Controls may fail despite best efforts (critical)
- BCP provides recovery path when prevention fails (cr

**clause_reference:** `['8.2.1', '8.2.2']`
**Clauses extracted from expected_response:** `['8.2']`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 7.4.1` → clauses=`['7.4.1']` — fact: "Controls may fail despite best efforts"
- [critical] source=`CCoP 2.0 7.4.1` → clauses=`['7.4.1']` — fact: "BCP provides recovery path when prevention fails"
- [important] source=`CCoP 2.0 7.4.1` → clauses=`['7.4.1']` — fact: "Addresses availability impact of incidents"

#### `B06-019`

**Reasons:**
- key_facts.source family ['4'] disjoint from clause_reference family ['3']

**Expected response excerpt:**
> The primary security intent of CCoP 2.0 Section 3.2 regarding risk assessment - informed decision making is: Enable security investment decisions based on measured risk.

This intent is achieved through:
- Resources are finite and must be allocated efficiently (critical)
- Risk assessment identifies

**clause_reference:** `['3.2.1', '3.2.2']`
**Clauses extracted from expected_response:** `['3.2']`
**Section families across all GT fields:** `['3', '4']`

**key_facts:**
- [critical] source=`CCoP 2.0 4.2.1` → clauses=`['4.2.1']` — fact: "Resources are finite and must be allocated efficiently"
- [critical] source=`CCoP 2.0 4.2.1` → clauses=`['4.2.1']` — fact: "Risk assessment identifies highest-priority vulnerabilities"
- [important] source=`CCoP 2.0 4.2.1` → clauses=`['4.2.1']` — fact: "Provides basis for control selection and justification"

### `b07_gap_identification_quality.jsonl` — 4 flagged

#### `B07-001`

**Reasons:**
- key_facts.source family ['4'] disjoint from clause_reference family ['3']

**Expected response excerpt:**
> Based on the scenario 'Incomplete CII asset inventory', the following compliance gaps are identified:

**Gap Type:** Missing Control

**CCoP Reference:** Section 3.2.2(b) / 3.2.2(c)

**Key Gaps:**
- OT systems within CII scope must be inventoried (critical priority)
- Incomplete inventory prevents c

**clause_reference:** `['3.2.2(b)', '3.2.2(c)']`
**Clauses extracted from expected_response:** `['3.2.2(b)', '3.2.2']`
**Section families across all GT fields:** `['3', '4']`

**key_facts:**
- [critical] source=`CCoP 2.0 4.2.2` → clauses=`['4.2.2']` — fact: "OT systems within CII scope must be inventoried"
- [critical] source=`CCoP 2.0 4.2.2` → clauses=`['4.2.2']` — fact: "Incomplete inventory prevents comprehensive risk assessment"
- [important] source=`CCoP 2.0 4.2.2` → clauses=`['4.2.2']` — fact: "Departmental silos create inventory blind spots"

#### `B07-002`

**Reasons:**
- key_facts.source family ['4'] disjoint from clause_reference family ['3']

**Expected response excerpt:**
> Based on the scenario 'Missing shadow IT inventory', the following compliance gaps are identified:

**Gap Type:** Missing Control

**CCoP Reference:** Section 3.2.2(b) / 3.2.2(c)

**Key Gaps:**
- Shadow IT creates unmonitored attack surface (critical priority)
- Data exposure risk outside approved c

**clause_reference:** `['3.2.2(b)', '3.2.2(c)']`
**Clauses extracted from expected_response:** `['3.2.2(b)', '3.2.2']`
**Section families across all GT fields:** `['3', '4']`

**key_facts:**
- [critical] source=`CCoP 2.0 4.2.2` → clauses=`['4.2.2']` — fact: "Shadow IT creates unmonitored attack surface"
- [critical] source=`CCoP 2.0 4.2.2` → clauses=`['4.2.2']` — fact: "Data exposure risk outside approved controls"
- [important] source=`CCoP 2.0 4.2.2` → clauses=`['4.2.2']` — fact: "Cloud procurement without security review violates governance"

#### `B07-003`

**Reasons:**
- key_facts.source family ['4'] disjoint from clause_reference family ['3']

**Expected response excerpt:**
> Based on the scenario 'Outdated asset inventory', the following compliance gaps are identified:

**Gap Type:** Inadequate Implementation

**CCoP Reference:** Section 3.2.2(b) / 3.2.2(c)

**Key Gaps:**
- Inventory must reflect current operational state (critical priority)
- Decommissioned systems sho

**clause_reference:** `['3.2.2(b)', '3.2.2(c)']`
**Clauses extracted from expected_response:** `['3.2.2(b)', '3.2.2']`
**Section families across all GT fields:** `['3', '4']`

**key_facts:**
- [critical] source=`CCoP 2.0 4.2.2` → clauses=`['4.2.2']` — fact: "Inventory must reflect current operational state"
- [important] source=`CCoP 2.0 4.2.2` → clauses=`['4.2.2']` — fact: "Decommissioned systems shouldn't be monitored as active"
- [critical] source=`CCoP 2.0 4.2.2` → clauses=`['4.2.2']` — fact: "New systems without inventory review are unassessed for risk"

#### `B07-005`

**Reasons:**
- key_facts.source family ['4'] disjoint from clause_reference family ['3']

**Expected response excerpt:**
> Based on the scenario 'Data flow mapping incomplete', the following compliance gaps are identified:

**Gap Type:** Inadequate Implementation

**CCoP Reference:** Section 3.2.2(b) / 3.2.2(c)

**Key Gaps:**
- Data flow maps required for boundary definition (critical priority)
- Undocumented flows crea

**clause_reference:** `['3.2.2(b)', '3.2.2(c)']`
**Clauses extracted from expected_response:** `['3.2.2(b)', '3.2.2']`
**Section families across all GT fields:** `['3', '4']`

**key_facts:**
- [critical] source=`CCoP 2.0 4.2.2` → clauses=`['4.2.2']` — fact: "Data flow maps required for boundary definition"
- [critical] source=`CCoP 2.0 4.2.2` → clauses=`['4.2.2']` — fact: "Undocumented flows create unprotected data paths"
- [important] source=`CCoP 2.0 4.2.2` → clauses=`['4.2.2']` — fact: "Asset inventory alone insufficient for scope understanding"

### `b09_risk_identification_residual_risk.jsonl` — 1 flagged

#### `B09-016`

**Reasons:**
- expected_response family ['1'] disjoint from clause_reference family ['3']

**Expected response excerpt:**
> **Residual Risk Assessment for Residual risk after encryption implementation:**

**Controls Implemented:**
AES-256 encryption at rest, TLS 1.3 for data in transit, Database encryption, Backup encryption

**Remaining Risks:**
Key management vulnerabilities, Memory decryption attacks, Quantum computin

**clause_reference:** `['3.2.2(a)', '3.2.4', '3.2.5']`
**Clauses extracted from expected_response:** `['1.3']`
**Section families across all GT fields:** `['1', '3']`

**key_facts:**
- [critical] source=`Residual risk assessment for government` → clauses=`[]` — fact: "Encryption protects data but key management remains critical"
- [important] source=`Residual risk assessment for government` → clauses=`[]` — fact: "Decryption must happen in memory for use, creating exposure window"
- [critical] source=`Residual risk assessment for government` → clauses=`[]` — fact: "Compromised encryption implementation undermines protection"

### `b12_audit_perspective_alignment.jsonl` — 2 flagged

#### `B12-016`

**Reasons:**
- key_facts.source family ['9'] disjoint from clause_reference family ['3', '6']

**Expected response excerpt:**
> **Audit Perspective: Supply chain security management**

**CSA Auditor Viewpoint:**
When assessing supply chain security management under CCoP 2.0 §3.8, a CSA auditor would examine:
- Control implementation against the clause requirements
- Evidence of effective operation, not just documentation
- C

**clause_reference:** `['3.8.1', '3.8.2', '3.8.3', '3.8.4', '3.8.5', '3.2.2', '6.4']`
**Clauses extracted from expected_response:** `['3.8']`
**Section families across all GT fields:** `['3', '6', '9']`

**key_facts:**
- [critical] source=`CCoP 2.0 9.3.1` → clauses=`['9.3.1']` — fact: "Auditor examines procurement security review and software verification processes"
- [critical] source=`CCoP 2.0 9.3.1` → clauses=`['9.3.1']` — fact: "Evidence: procurement policy, SBOM documentation, vendor security reviews, source code escrow"
- [important] source=`CCoP 2.0 9.3.1` → clauses=`['9.3.1']` — fact: "Risk Manager: ensure all software and hardware procurement includes security assessment"

#### `B12-020`

**Reasons:**
- key_facts.source family ['4'] disjoint from clause_reference family ['3']

**Expected response excerpt:**
> **Audit Perspective: Risk-based vs compliance-based methodology**

**CSA Auditor Viewpoint:**
When assessing risk-based vs compliance-based methodology under CCoP 2.0 §3.2, a CSA auditor would examine:
- Control implementation against the clause requirements
- Evidence of effective operation, not ju

**clause_reference:** `['3.2.1', '3.2.2']`
**Clauses extracted from expected_response:** `['3.2']`
**Section families across all GT fields:** `['3', '4']`

**key_facts:**
- [critical] source=`CCoP 2.0 4.2.1` → clauses=`['4.2.1']` — fact: "Auditor looks for evidence that risk assessments drive security priorities and spending"
- [critical] source=`CCoP 2.0 4.2.1` → clauses=`['4.2.1']` — fact: "Evidence: risk register, risk assessment methodology, control selection justification"
- [critical] source=`CCoP 2.0 4.2.1` → clauses=`['4.2.1']` — fact: "Risk Manager: demonstrate clear link between risk assessment and control implementation"

### `b13_evidence_expectation_awareness.jsonl` — 1 flagged

#### `B13-003`

**Reasons:**
- key_facts.source family ['4'] disjoint from clause_reference family ['3']
- expected_response family ['4'] disjoint from clause_reference family ['3']

**Expected response excerpt:**
> **Evidence Requirements for: Risk assessment documentation**

**CCoP Domain:** Identification (Section 4)

**Required Evidence Types:**
- Risk register
- Risk assessment methodology
- Risk assessment reports
- Control selection justification
- Residual risk acceptance


**Evidence Quality Dimensions

**clause_reference:** `['3.2.4', '3.2.2', '3.2.1', '3.2.5']`
**Clauses extracted from expected_response:** `['4']`
**Section families across all GT fields:** `['3', '4']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 4` → clauses=`['4']` — fact: "Risk register must be current and dated"
- [critical] source=`CCoP 2.0 Section 4` → clauses=`['4']` — fact: "Methodology should show systematic risk evaluation process"
- [important] source=`CCoP 2.0 Section 4` → clauses=`['4']` — fact: "Risk acceptance decisions must be formally documented"

### `b18_responsibility_attribution_sg.jsonl` — 25 flagged

#### `B18-001`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['3']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible for CCoP compliance in a CII-designated organization?

**Roles Involved:** BoD, CIIO, CISO, Risk Manager

**Answer:**
Board of Directors has ultimate accountability, CIIO has personal legal responsibility, CISO h

**clause_reference:** `['3.1.2', '3.1.3', '3.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '3']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-002`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who must receive cybersecurity training under CCoP 2.0?

**Roles Involved:** Board, CIIO, CISO, Risk Manager, All employees

**Answer:**
All staff must receive annual security awareness training. Board and senior management require

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `['8.1.1']`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-003`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who reports cybersecurity incidents to CSA?

**Roles Involved:** CIIO, CISO, Risk Manager

**Answer:**
CIIO is responsible for ensuring incident reports to CSA. CISO typically manages incident response and may submit reports. Risk 

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-004`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible when a vendor breach exposes CII data?

**Roles Involved:** CIIO, CISO, Vendor, Risk Manager

**Answer:**
CII operator (CIIO) remains responsible for CII data regardless of vendor breach. Vendor may have contract

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-005`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who approves risk acceptance for controls that cannot be implemented?

**Roles Involved:** Board, CIIO, CISO, Risk Manager

**Answer:**
Board of Directors must formally accept significant risks. CIIO should present risk acceptance 

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-006`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** What are the employee responsibilities for CCoP compliance?

**Roles Involved:** All employees, CISO, Risk Manager

**Answer:**
All employees must complete security training, follow security policies, report suspicious activities, 

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-007`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** What is the difference between CISO and Risk Manager roles under CCoP?

**Roles Involved:** CISO, Risk Manager

**Answer:**
CISO has technical responsibility for security operations and control implementation. Risk Manager has func

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-008`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible for cybersecurity in outsourced CII operations (e.g., SingHealth-IHiS model)?

**Roles Involved:** CIIO, Service provider, Vendor, Board

**Answer:**
CII operator's CIIO retains responsibility regardless of outso

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-009`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible for OT security when OT is managed separately from IT?

**Roles Involved:** CIIO, CISO, OT manager, Risk Manager

**Answer:**
CIIO is responsible for all CII security including OT. CISO should coordinate with OT 

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-010`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who determines what constitutes a critical incident for CSA reporting?

**Roles Involved:** CIIO, CISO, Risk Manager

**Answer:**
CIIO approves incident classification framework. CISO and Risk Manager apply framework to incidents. 

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-011`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible for maintaining the CII asset inventory?

**Roles Involved:** Risk Manager, CISO, Asset owners, CIIO

**Answer:**
Risk Manager typically maintains inventory process. Asset owners provide system information. CISO 

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-012`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who authorizes cybersecurity budget and resource allocation?

**Roles Involved:** Board, CIIO, CISO, Risk Manager

**Answer:**
Board of Directors approves budget and resources. CIIO presents business case for security investments. 

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-013`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible when security controls conflict with operational requirements?

**Roles Involved:** Board, CIIO, CISO, Operations

**Answer:**
Board decides on risk acceptance when controls conflict with operations. CIIO present

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-014`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible for vendor security assessments?

**Roles Involved:** Risk Manager, CISO, Procurement, CIIO

**Answer:**
Risk Manager typically conducts vendor security assessments. CISO provides technical requirements. Procurem

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-015`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who represents the organization during CSA audits?

**Roles Involved:** CIIO, CISO, Risk Manager, Legal

**Answer:**
CIIO is primary contact for CSA audits. CISO provides technical expertise. Risk Manager provides evidence and docu

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-016`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible for employee background screening?

**Roles Involved:** HR, CISO, Risk Manager, CIIO

**Answer:**
HR conducts background screening. CISO defines security screening requirements for sensitive roles. Risk Manager e

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-017`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible when a security control fails despite proper implementation?

**Roles Involved:** CISO, CIIO, Vendor, Board

**Answer:**
CISO is responsible for technical response and remediation. CIIO reports to CSA if required

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-018`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** How is responsibility attributed in a joint CII arrangement (multiple operators sharing infrastructure)?

**Roles Involved:** Multiple CIIOs, CISOs, CSA

**Answer:**
Each CII operator's CIIO is responsible for their own organizatio

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-019`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible when cloud service provider breach affects CII data?

**Roles Involved:** CIIO, CISO, CSP, Risk Manager

**Answer:**
CII operator's CIIO must report breach to CSA. CISO manages technical response. CSP addresses b

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-020`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible for cybersecurity during M&A due diligence?

**Roles Involved:** Board, CIIO, CISO, Risk Manager

**Answer:**
Board oversees cybersecurity due diligence in M&A. CIIO must ensure target CII compliance is assessed.

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-021`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible when an employee deliberately violates security policies causing a breach?

**Roles Involved:** Employee, Manager, CISO, CIIO, Board

**Answer:**
Employee is personally responsible for malicious actions and may f

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-022`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible for supply chain security vulnerabilities in purchased software?

**Roles Involved:** CIIO, CISO, Procurement, Vendor, Risk Manager

**Answer:**
CII operator's CIIO is responsible for CII security including purch

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-023`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible when delegated CII functions are subcontracted without permission?

**Roles Involved:** Primary CIIO, Subcontractor, CSA

**Answer:**
Primary CIIO is responsible for unauthorized subcontracting. Subcontractor mus

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-024`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible for cybersecurity during CII designation transition (newly designated)?

**Roles Involved:** Board, CIIO, CISO, CSA

**Answer:**
Board must appoint CIIO within designated timeframe. CISO must implement CCoP contr

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

#### `B18-025`

**Reasons:**
- key_facts.source family ['1'] disjoint from clause_reference family ['8']

**Expected response excerpt:**
> **Responsibility Attribution: Singapore CII Context**

**Question:** Who is responsible when CII scope changes (expansion or reduction)?

**Roles Involved:** CIIO, CSA, Board, CISO

**Answer:**
CIIO must notify CSA of material CII scope changes. CSA confirms new scope. Board must resource expanded s

**clause_reference:** `['8.1.1']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['1', '8']`

**key_facts:**
- [critical] source=`Cybersecurity Act 2018 Section 11` → clauses=`[]` — fact: "CIIO is personally liable for CII compliance under Cybersecurity Act 2018 Section 11"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "Board is responsible for CII governance and oversight"
- [important] source=`CCoP 2.0 Section 1` → clauses=`['1']` — fact: "CISO is responsible for operational security implementation"

### `b21_hallucination_over_specification.jsonl` — 2 flagged

#### `B21-008`

**Reasons:**
- expected_response cites clauses ['11.7.5', '11'] but clause_reference is empty

**Expected response excerpt:**
> CCoP 2.0 does not contain a Clause 11.7.5. More importantly, CCoP 2.0 does not specify penalty amounts for non-compliance. CCoP 2.0 is a code of practice that specifies cybersecurity requirements for CII, but it does not contain enforcement provisions or specify fines. Penalties for non-compliance w

**clause_reference:** `['N/A']`
**Clauses extracted from expected_response:** `['11.7.5', '11']`
**Section families across all GT fields:** `['11']`

**key_facts:**
- [critical] source=`CCoP 2.0 structure` → clauses=`[]` — fact: "CCoP 2.0 does not contain a Clause 11.7.5"
- [critical] source=`CCoP 2.0 scope` → clauses=`[]` — fact: "CCoP 2.0 does not specify penalty amounts for non-compliance"
- [important] source=`Cybersecurity Act Section 11` → clauses=`[]` — fact: "Penalties are determined by the Cybersecurity Act, not CCoP 2.0 itself"

#### `B21-010`

**Reasons:**
- expected_response cites clauses ['4.2.6'] but clause_reference is empty

**Expected response excerpt:**
> CCoP 2.0 does not contain a Clause 4.2.6. More broadly, CCoP 2.0 does not specify what percentage of CII budget must be allocated to cybersecurity. The standard requires CIIOs to implement cybersecurity measures and maintain adequate resources, but it does not prescribe specific budget allocations s

**clause_reference:** `['N/A']`
**Clauses extracted from expected_response:** `['4.2.6']`
**Section families across all GT fields:** `['4']`

**key_facts:**
- [critical] source=`CCoP 2.0 structure` → clauses=`[]` — fact: "CCoP 2.0 does not contain a Clause 4.2.6"
- [critical] source=`CCoP 2.0 scope` → clauses=`[]` — fact: "CCoP 2.0 does not specify cybersecurity budget percentages"
- [important] source=`CCoP 2.0 risk-based approach` → clauses=`[]` — fact: "Resource requirements are based on risk assessment and operational needs"

### `b22_waiver_exception_reasoning.jsonl` — 20 flagged

#### `B22-001`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Legacy SCADA cannot support MFA**

**Sector Context:** Energy CII

**Decision:** Yes, with compensating controls

**Reasoning:**
OT systems cannot always support modern authentication. Compensating controls required: network isolation, monitoring, strong authentication at networ

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Waiver application must include strong compensating controls"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Network isolation and monitoring can provide equivalent protection"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Waiver is temporary and must include transition planning"

#### `B22-002`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: 12-month log retention storage cost**

**Sector Context:** Healthcare CII

**Decision:** No, waiver not appropriate

**Reasoning:**
Cost alone is not sufficient grounds for waiver under Section 11(7). Organizational measures must be taken to meet requirements, including log comp

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11(7)', '11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Cost constraints do not exempt CCoP compliance"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Log compression and tiered storage can manage costs effectively"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Waiver may be considered only if requirement is technically infeasible"

#### `B22-003`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Small team cannot manage quarterly access reviews**

**Sector Context:** Banking CII

**Decision:** No, but modified approach may work

**Reasoning:**
Staffing constraints are not grounds for waiver. However, automation can reduce manual effort. Semi-annual reviews with automate

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Resource constraints do not exempt compliance obligations"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Automation can reduce manual review burden while maintaining control"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Modified approach still requires CSA approval"

#### `B22-004`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: OT system cannot be patched during operations**

**Sector Context:** Government CII

**Decision:** Yes, with time limit

**Reasoning:**
OT patching during operations creates safety risk. Time-limited waiver for patching during scheduled maintenance windows. Compensating controls

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Safety-critical operations may justify delayed patching"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Compensating controls must be documented and implemented"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Planned maintenance windows must be used for patching"

#### `B22-005`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: No local CISO expertise available**

**Sector Context:** Telecommunications CII

**Decision:** Yes, role can be outsourced

**Reasoning:**
CISO role can be fulfilled by qualified third-party or shared service. However, accountability remains with CIIO. Service level agreements m

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "CISO role can be outsourced but accountability cannot be delegated"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Third-party CISO must have appropriate qualifications and experience"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Service provider must meet CCoP compliance requirements themselves"

#### `B22-006`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Encryption incompatible with legacy system**

**Sector Context:** Water CII

**Decision:** Yes, with transition plan

**Reasoning:**
Encryption incompatibility may justify waiver with transition plan. Must demonstrate: incompatibility evidence, compensating controls (network iso

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Technical incompatibility must be documented with evidence"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Compensating controls must provide equivalent protection"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Transition plan must have specific timeline and milestones"

#### `B22-007`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Conflicting regulatory requirements**

**Sector Context:** Transportation CII

**Decision:** Consult CSA for guidance

**Reasoning:**
Regulatory conflicts require CSA consultation. CCoP 2.0 Section 11 states CII obligations prevail over conflicting requirements. Document conflic

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "CCoP obligations prevail in regulatory conflicts under Section 11"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Must document the conflict and seek CSA guidance formally"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Other regulator may be consulted during resolution process"

#### `B22-008`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Partial waiver for subsystem**

**Sector Context:** Energy CII

**Decision:** Yes, partial waiver possible

**Reasoning:**
Partial waivers may be granted for specific subsystems that cannot comply while rest of system complies. Must clearly define scope and implement controls fo

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Partial waiver must have clearly defined system boundaries"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Rest of system must achieve full CCoP compliance"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Boundary controls must protect compliant portions from non-compliant subsystem"

#### `B22-009`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Vendor refuses to implement security controls**

**Sector Context:** Healthcare CII

**Decision:** Risk acceptance or contract termination

**Reasoning:**
If vendor absolutely cannot implement required controls, options include: 1) terminate contract and find new vendor, 2) impl

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Vendor non-compliance does not exempt operator responsibility"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Contract termination may be necessary for critical controls"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Risk acceptance requires formal documentation and CSA notification"

#### `B22-010`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Waiver renewal approaching**

**Sector Context:** Banking CII

**Decision:** Waiver renewal requires continued justification

**Reasoning:**
Waiver renewal requires: demonstration of continued infeasibility, effectiveness of compensating controls, progress on transition plan, al

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Waiver renewal requires showing continued infeasibility"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Compensating control effectiveness must be demonstrated with evidence"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "CSA may tighten requirements or reduce waiver scope on renewal"

#### `B22-011`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Emergency bypass of security controls**

**Sector Context:** Government CII

**Decision:** Not a waiver, but must be documented

**Reasoning:**
Emergency control bypass is not a waiver but must be documented. Emergency procedures should define when bypass is permitted, who autho

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Emergency bypass is procedural, not a regulatory waiver"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Documented procedures must include authorization and restoration"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Incident report should document any emergency bypass usage"

#### `B22-012`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Multiple non-compliant areas**

**Sector Context:** Telecommunications CII

**Decision:** Case-by-case determination

**Reasoning:**
Separate waivers for each area with distinct justifications are preferred. However, if non-compliance stems from single root cause (e.g., legacy p

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Separate waivers allow targeted compensating controls for each gap"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Common root cause may justify comprehensive waiver approach"
- [supporting] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "CSA guidance should be sought on preferred approach"

#### `B22-013`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: OT protocol cannot be secured**

**Sector Context:** Water CII

**Decision:** Yes, with strong compensating controls

**Reasoning:**
Legacy OT protocols (Modbus, DNP3 without security) cannot be patched. Waiver required with strong compensating: network isolation, protocol gatew

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Legacy OT protocols have inherent security limitations"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Network isolation is primary compensating control for OT"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Protocol gateways enable monitoring at boundary"

#### `B22-014`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Building cannot accommodate additional security equipment**

**Sector Context:** Transportation CII

**Decision:** Maybe, if alternatives explored and ineffective

**Reasoning:**
Physical constraints may be waivable if genuinely infeasible. Must explore all alternatives first. C

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Physical infeasibility requires demonstration of all alternatives explored"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Compensating controls must provide equivalent protection"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "CSA may request site inspection to verify constraints"

#### `B22-015`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Waiver denial and enforcement**

**Sector Context:** Energy CII

**Decision:** Denial triggers enforcement process

**Reasoning:**
Waiver denial triggers enforcement process. CSA may issue compliance directive with timeline for implementation. Organization must demonstrate progr

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3', '1.4.7']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Waiver denial results in compliance directive with timeline"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Enforcement actions escalate for continued non-compliance"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Organization must implement control regardless of challenges when waiver denied"

#### `B22-016`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Conditional waiver with milestones**

**Sector Context:** Healthcare CII

**Decision:** CSA may impose conditions

**Reasoning:**
CSA may grant conditional waiver with: 1) strict compensating control requirements, 2) periodic progress reports, 3) sunset clause with review date, 

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Conditional waivers have specific compliance requirements attached"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Periodic reporting demonstrates ongoing compliance efforts"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Sunset clause forces re-evaluation at specified date"

#### `B22-017`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Emergency equipment replacement**

**Sector Context:** Banking CII

**Decision:** Temporary risk acceptance, not waiver

**Reasoning:**
This is not a waiver but temporary risk acceptance. Document interim controls, budget request for next year, contingency planning. May require 

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Budget constraints are managed through risk acceptance, not waiver"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Interim controls must reduce risk during budget gap period"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "CSA notification required if interim controls don't meet standards"

#### `B22-018`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Conflicting expert opinions**

**Sector Context:** Government CII

**Decision:** Evidence-based approach required

**Reasoning:**
Present all expert opinions with evidence. Acknowledge differing recommendations. Explain chosen approach with technical justification. CSA will eval

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "All expert opinions should be disclosed with reasoning"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Evidence-based justification preferred over authority-based arguments"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "CSA evaluates technical merits of competing approaches"

#### `B22-019`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Supply chain prevents implementation**

**Sector Context:** Telecommunications CII

**Decision:** Timeline extension may be requested

**Reasoning:**
Request timeline extension from CSA citing supply chain constraints. Document: vendor communications, alternative approaches expl

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Timeline extension may be granted with documented justification"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Supply chain documentation must show mitigation efforts"
- [supporting] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Partial waiver may cover extension period gap"

#### `B22-020`

**Reasons:**
- key_facts.source family ['11'] disjoint from clause_reference family ['1']
- expected_response family ['11'] disjoint from clause_reference family ['1']

**Expected response excerpt:**
> **Waiver Assessment: Waiver for 2-hour notification due to limited staff**

**Sector Context:** Water CII

**Decision:** No, alternative process required

**Reasoning:**
2-hour notification is mandatory for critical incidents. Limited staff is not grounds for waiver. Must establish alternative proce

**clause_reference:** `['1.6.1', '1.6.2', '1.6.3']`
**Clauses extracted from expected_response:** `['11']`
**Section families across all GT fields:** `['1', '11']`

**key_facts:**
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "2-hour critical notification is not waivable for staff constraints"
- [critical] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Alternative processes must ensure notification within timeline"
- [important] source=`Cybersecurity Act Section 11(7) and CCoP 2.0 Section 11` → clauses=`['11']` — fact: "Third-party monitoring services can provide 24/7 coverage"

### `b24_incident_response_guidance.jsonl` — 24 flagged

#### `B24-001`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Immediately classify as serious incident (data breach affecting critical services). Report to CSA within 2 hours via Form A2. Activate incident response plan. Preserve forensic evidence. Do not pay ransom without explicit legal and regulatory guidance. Isolate affected systems.

**clause_reference:** `['7.1.1(b)', '7.1.1(g)', '7.1.1(h)']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-002`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Classify as substantial incident if operational control remains intact. Report to CSA within 24 hours via Form A1. However: if encryption affects real-time monitoring or safety systems, reclassify as serious (2-hour reporting). The distinction depends on operational impact, not just data loss.

**clause_reference:** `['7.1.1(b)', '7.1.1(g)', '7.1.1(h)']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-004`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> If no impact on operational technology systems: substantial incident at minimum, may qualify as non-reportable if purely administrative with no CII impact. However: conduct full assessment to confirm no lateral movement. Document risk assessment. If any CII systems or data affected, report per subst

**clause_reference:** `['7.1.1(d)', '7.1.1(g)']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-005`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']
- expected_response family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> CCoP 2.0 does not explicitly prohibit ransom payment but: (1) Classify and report incident first before any payment decision, (2) Activate incident response plan regardless of timing, (3) Preserve forensic evidence, (4) Payment does not exempt reporting requirements, (5) Engage legal/compliance befo

**clause_reference:** `['7.1.1(c)', '7.1.1(d)', '7.1.1(e)']`
**Clauses extracted from expected_response:** `['8']`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-006`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Classify as serious incident (large-scale data breach). Report to CSA within 2 hours via Form A2. Also notify PDPC (Personal Data Protection Commission) per PDPA requirements. Activate forensic investigation. Assess whether data includes CII-specific sensitive information. Prepare customer notificat

**clause_reference:** `['7.1.1(b)', '7.1.1(f)', '7.1.1(h)']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-007`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Classify as substantial incident (limited data exposure, no classified compromise). Report to CSA within 24 hours via Form A1. Government sector: also report to GovTech Singapore and agency's CISO. Assess whether accessed information could be used for phishing. Implement monitoring for follow-on att

**clause_reference:** `['7.1.1(b)', '7.1.1(g)', '7.1.1(h)']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-008`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Classify as serious incident despite no operational disruption. SCADA configuration exposure reveals infrastructure details that could enable future attacks. Report to CSA within 2 hours via Form A2. Assume attacker may use information for follow-on attacks. Rotate credentials, review access logs, e

**clause_reference:** `['7.1.1(b)', '7.1.1(g)', '7.1.4']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-009`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Classify as serious incident (confirmed data exfiltration of patient records). Report to CSA within 2 hours via Form A2. Healthcare: notify Ministry of Health. Assess scope of affected patients. Prepare breach notification. Review backup storage security. Root cause analysis required. Determine if 1

**clause_reference:** `['7.1.1(b)', '7.1.1(h)', '7.1.1(i)', '7.1.4']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-010`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']
- expected_response family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Report as serious incident (assume exfiltration occurred when uncertain). CSA prefers over-reporting to under-reporting. Report what is known: unauthorized access confirmed, exfiltration unknown. Indicate investigation ongoing. Update CSA when forensic analysis completes. Section 8.6 requires forens

**clause_reference:** `['7.1.1(g)', '7.1.1(h)']`
**Clauses extracted from expected_response:** `['8.6']`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-011`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']
- expected_response family ['8', '9'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> CCoP 2.0 Section 8 covers cyber incidents. Equipment failure = business continuity (Section 9) not incident response. However: confirm not cyber-induced. Conduct preliminary cyber assessment. If confirmed non-cyber: activate BCP, document for Section 9.5. If any indication of cyber involvement: swit

**clause_reference:** `['7.1.1(i)', '7.1.4']`
**Clauses extracted from expected_response:** `['8', '9', '9.5']`
**Section families across all GT fields:** `['7', '8', '9']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-012`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Classify as substantial incident (disruption to communications but core ATC operational). Report to CSA within 24 hours via Form A1. However: if DDoS affected safety-critical communications, upgrade to serious. Aviation sector may have additional CAAS reporting. Implement DDoS mitigation. Assess att

**clause_reference:** `['7.1.1(d)', '7.1.1(g)']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-013`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']
- expected_response family ['8', '9'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Software bug causing outage = business continuity issue (Section 9), not cyber incident (Section 8). No CSA reporting required unless investigation reveals security component. However: document per BCP, review software deployment process. If bug was exploited or security-related, reclassify as cyber

**clause_reference:** `['7.1.1(i)', '7.1.4']`
**Clauses extracted from expected_response:** `['9', '8']`
**Section families across all GT fields:** `['7', '8', '9']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-014`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']
- expected_response family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Classify as serious incident despite uncertain cause. Loss of control/monitoring for CII = serious by operational impact. Report to CSA within 2 hours via Form A2. Assume cyber until proven otherwise. Categorize as 'suspected cyber incident' in initial report. Update when root cause confirmed. Secti

**clause_reference:** `['7.1.1(d)', '7.1.1(g)']`
**Clauses extracted from expected_response:** `['8.6']`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-015`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Classify as serious incident. Loss of monitoring for CII operational systems = serious, even with manual workarounds. Report to CSA within 2 hours via Form A2. Manual operations are compensating control but represent degraded capability. Assess root cause: cyber attack vs equipment failure vs commun

**clause_reference:** `['7.1.1(d)', '7.1.1(g)']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-016`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Classify as serious incident (data exfiltration by insider). Report to CSA within 2 hours via Form A2. Include: insider threat, data type (security-sensitive), status of external sharing unknown. Legal action may be considered. Preserve forensic evidence. Section 7.3 (terminated access) should have 

**clause_reference:** `['7.1.1(g)', '7.1.1(h)']`
**Clauses extracted from expected_response:** `['7.3']`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-017`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Classify as serious incident (third-party breach with potential CII impact). Report to CSA within 2 hours via Form A2. Assume CII systems compromised until forensic investigation proves otherwise. Section 7.2 (third-party security) applies - vendor due diligence failure. Immediate actions: revoke ve

**clause_reference:** `['7.1.1(e)', '7.1.1(g)']`
**Clauses extracted from expected_response:** `['7.2']`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-018`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Classify as serious incident (unauthorized access via active credentials). Report to CSA within 2 hours via Form A2. Immediate revocation required. Investigate: what was accessed, any data exfiltration, extent of unauthorized activity. Section 7.3 violation - access not terminated. Root cause: proce

**clause_reference:** `['7.1.1(g)', '7.1.4']`
**Clauses extracted from expected_response:** `['7.3']`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-019`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']
- expected_response family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Classify as substantial incident (potential phishing with unknown impact). Report to CSA within 24 hours via Form A1. However: if investigation reveals credentials stolen or malware installed, upgrade to serious. Immediate actions: identify all who clicked, scan for malware, password resets, enhance

**clause_reference:** `['7.1.1(d)', '7.1.1(f)']`
**Clauses extracted from expected_response:** `['8.6']`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-020`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']
- expected_response family ['6', '8', '9'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Classify as substantial incident (service disruption and data loss due to human error). Report to CSA within 24 hours via Form A1. CCoP Section 8 covers incidents regardless of intent (accidental vs malicious). Key issues: no backup (Section 9.4 violation), human error (Section 6 training), 6-hour d

**clause_reference:** `['7.1.1(g)']`
**Clauses extracted from expected_response:** `['8', '9.4', '6']`
**Section families across all GT fields:** `['6', '7', '8', '9']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-021`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Classify as serious incident (data exposure via supply chain deception). Report to CSA within 2 hours via Form A2. Even without exploitation: the information shared enables targeted attacks. Consider this a pre-positioning threat actor. Actions: assume systems are compromised, hunt for indicators, r

**clause_reference:** `['7.1.1(g)', '7.1.4']`
**Clauses extracted from expected_response:** `['7.2']`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-022`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['6', '7']

**Expected response excerpt:**
> Not immediately reportable as incident (no attack occurred). However: Section 7.1 requires incident management to include threat-intelligence consumption (see Section 6.4). Actions: enhance monitoring, review for indicators of compromise, prepare incident response team. If attack materializes: immed

**clause_reference:** `['7.1.1(d)', '7.1.1(b)', '7.1.1(a)', '6.4.1', '6.4.3']`
**Clauses extracted from expected_response:** `['7.1', '6.4']`
**Section families across all GT fields:** `['6', '7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-023`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']
- expected_response family ['5', '8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Authorized penetration testing = not a CCoP incident. No reporting required. However: Section 8.5 requires IR plan be tested - this is the purpose. Document findings, remediate vulnerability, update risk assessment (Section 5). Consider retesting. The finding validates IR testing program. Reporting 

**clause_reference:** `['7.1.1(g)']`
**Clauses extracted from expected_response:** `['8.5', '5']`
**Section families across all GT fields:** `['5', '7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-024`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Multiple simultaneous incidents: each classified separately, but overall response coordinated. Ransomware on internal systems = serious (2-hour reporting). DDoS = substantial if web systems non-essential, serious if CII-related. Vendor breach = serious (potential CII impact). Report all to CSA in co

**clause_reference:** `['7.1.1(c)', '7.1.1(d)', '7.1.1(g)']`
**Clauses extracted from expected_response:** `[]`
**Section families across all GT fields:** `['7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

#### `B24-025`

**Reasons:**
- key_facts.source family ['8'] disjoint from clause_reference family ['7']
- expected_response family ['5', '8'] disjoint from clause_reference family ['7']

**Expected response excerpt:**
> Classify based on original impact, not discovery time. If data exfiltration occurred: serious incident. Report to CSA immediately upon discovery. Late reporting explanation included. Section 8.6 forensic investigation: determine full scope, extract attacker TTPs, ensure eradication. Section 8.7: roo

**clause_reference:** `['7.1.1(b)', '7.1.1(h)', '7.1.1(i)', '7.1.4']`
**Clauses extracted from expected_response:** `['8.6', '8.7', '5.2']`
**Section families across all GT fields:** `['5', '7', '8']`

**key_facts:**
- [critical] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Serious incident = 2-hour CSA reporting (Form A2)"
- [important] source=`CCoP 2.0 Section 8.3` → clauses=`['8.3']` — fact: "Substantial incident = 24-hour CSA reporting (Form A1)"

