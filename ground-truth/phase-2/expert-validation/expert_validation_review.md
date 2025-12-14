# CCoP 2.0 Phase 2 Test Cases - Domain Expert Validation

## Instructions for Domain Expert Reviewer

This document contains 116 test cases for evaluating LLM baseline models against Singapore's CCoP 2.0 (Cybersecurity Code of Practice for Critical Information Infrastructure).

**Your Review Task**:
1. Verify that each **Question** accurately reflects CCoP 2.0 requirements
2. Validate that each **Expected Response** is technically accurate and compliant with CCoP 2.0
3. Verify **Key Facts** are atomic, verifiable, and extracted correctly from expected responses
4. For classification/safety benchmarks: Validate **Expected Label** is correct
5. For reasoning benchmarks: Review **Reasoning Dimensions** for appropriateness
6. For safety benchmarks: Verify **Safety Checks** identify correct hallucination/over-specification risks
7. Check that clause references are correct
8. Identify any inaccuracies, omissions, or misinterpretations
9. Provide feedback on clarity and completeness

**Review Checklist** (for each test case):
- [ ] Question is clear and unambiguous
- [ ] Clause reference is correct
- [ ] Expected response is technically accurate
- [ ] Expected response is complete and comprehensive
- [ ] Key facts (3-8) are atomic and verifiable
- [ ] Expected label (if applicable) is correct and concise
- [ ] Reasoning dimensions (if applicable) align with evaluation criteria
- [ ] Safety checks (if applicable) cover hallucination risks
- [ ] Answer correctly interprets CCoP 2.0 requirements
- [ ] Singapore-specific terminology is used correctly
- [ ] Benchmark category (classification/reasoning/safety) is appropriate

**Phase 2 Schema Structure**:
```json
{
  "benchmark_category": "classification | reasoning | safety",
  "key_facts": ["atomic fact 1", "atomic fact 2", ...],
  "expected_label": "..." (for classification/safety),
  "reasoning_dimensions": {...} (for reasoning),
  "safety_checks": [...] (for safety)
}
```

**How to Provide Feedback**:
- Add comments directly in this document using `<!-- EXPERT NOTE: your feedback -->`
- Mark approved test cases with `✅ APPROVED`
- Mark test cases needing revision with `❌ NEEDS REVISION: reason`

---

## Test Case Summary (Phase 2 - Updated Schema)
- **Total Test Cases**: 116
- **Benchmark Categories**: B1-B21 (21 benchmarks)
- **Category Distribution**:
  - Classification: 29 test cases (B1, B2, B4, B5)
  - Reasoning: 79 test cases (B3, B6-B19)
  - Safety: 8 test cases (B20, B21)
- **CCoP Sections Covered**: All 11 sections
- **Schema Version**: Phase 2 (with key_facts, expected_label, reasoning_dimensions, safety_checks)

---

## NOTE: Sample Test Cases Below

The detailed test cases shown below are from an earlier phase and serve as examples of the validation format. For complete Phase 2 validation with updated schema, please reference the JSONL files in `ground-truth/phase-2/test-suite/` containing all 116 test cases across B1-B21 benchmarks.

---

# B1: CCoP Interpretation Accuracy (7 test cases)

**Purpose**: Test model's ability to accurately interpret and explain CCoP 2.0 requirements in plain language.

---

## B1-001: Cybersecurity Risk Management Framework

**Section**: Section 3: Governance
**Clause Reference**: 3.2.2
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
Explain the requirement in CCoP 2.0 Clause 3.2.2 regarding cybersecurity risk management frameworks in plain language. What must CIIOs do according to this clause?

### Expected Answer:
According to Clause 3.2.2, Critical Information Infrastructure Owners (CIIOs) must establish and maintain a cybersecurity risk management framework. This framework should enable them to identify, assess, manage, and monitor cybersecurity risks to their CII. The framework must be appropriate to the nature, scale, and complexity of their operations. CIIOs should regularly review and update this framework to ensure it remains effective in addressing evolving cybersecurity threats and changes to their infrastructure.

### Expert Review:
<!-- Add your feedback here -->

---

## B1-002: Multi-Factor Authentication

**Section**: Section 5: Protection
**Clause Reference**: 5.1.5
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
What does CCoP 2.0 Clause 5.1.5 require regarding multi-factor authentication? Provide a plain language explanation suitable for a CIIO's management team.

### Expected Answer:
Clause 5.1.5 requires CIIOs to implement multi-factor authentication (MFA) for all access to CII systems. This means users must provide at least two different types of credentials before gaining access - typically something they know (like a password), something they have (like a security token or mobile device), or something they are (like a fingerprint). The clause specifically mandates MFA for remote access, privileged user access, and access to critical systems. This requirement significantly reduces the risk of unauthorized access even if passwords are compromised.

### Expert Review:
<!-- Add your feedback here -->

---

## B1-003: Patch Management Timelines

**Section**: Section 5: Protection
**Clause Reference**: 5.6.4
**Difficulty**: High
**Domain**: IT/OT

### Question:
Interpret CCoP 2.0 Clause 5.6.4 concerning patch management timelines. What are the specific time requirements CIIOs must meet for applying security patches?

### Expected Answer:
Clause 5.6.4 establishes specific timelines for patch application based on severity. For critical security patches addressing vulnerabilities being actively exploited or with publicly available exploit code, CIIOs must apply patches within 2 weeks of the patch being made available by the vendor. For other security patches, CIIOs must apply them within 1 month. The clause recognizes that CIIOs should conduct appropriate testing before deployment, but emphasizes that these timelines are maximum periods. CIIOs should prioritize patches based on risk assessment and may need to apply critical patches even more quickly if threats are imminent.

### Expert Review:
<!-- Add your feedback here -->

---

## B1-004: Security Event Logging

**Section**: Section 6: Detection
**Clause Reference**: 6.1.3
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
Explain what CCoP 2.0 Clause 6.1.3 requires regarding security event logging. What types of events must be logged and for how long?

### Expected Answer:
Clause 6.1.3 requires CIIOs to log security-relevant events for all CII systems. At minimum, logs must capture: user authentication and authorization events, privileged operations, system and application changes, security policy changes, network connections, and security alerts. The clause mandates that logs must be retained for at least 1 year, with the most recent 3 months of logs available for immediate review and analysis. Logs must be protected from unauthorized modification or deletion, and must include sufficient detail to support incident investigation and forensic analysis, including timestamps, user identities, and event outcomes.

### Expert Review:
<!-- Add your feedback here -->

---

## B1-005: Cybersecurity Incident Response Plans

**Section**: Section 7: Response and Recovery
**Clause Reference**: 7.1.2
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
What does CCoP 2.0 Clause 7.1.2 specify about cybersecurity incident response plans? What key elements must be included in such plans?

### Expected Answer:
Clause 7.1.2 requires CIIOs to develop, maintain, and regularly test a cybersecurity incident response plan. The plan must include: clear roles and responsibilities for incident response team members, procedures for detecting and reporting incidents, escalation protocols including criteria for notifying senior management and CSA, containment and eradication procedures, recovery and restoration processes, and communication plans for internal and external stakeholders. The clause emphasizes that plans must be tested at least annually through tabletop exercises or simulations, and updated based on lessons learned from tests and actual incidents.

### Expert Review:
<!-- Add your feedback here -->

---

## B1-006: OT Network Segmentation

**Section**: Section 10: Operational Technology Security
**Clause Reference**: 10.2.3
**Difficulty**: High
**Domain**: OT

### Question:
Explain CCoP 2.0 Clause 10.2.3 regarding network segmentation for OT systems. How does this requirement differ from general IT network segmentation?

### Expected Answer:
Clause 10.2.3 requires CIIOs to implement network segmentation that separates OT networks from IT networks and the internet. Specifically, OT systems must be isolated in dedicated network zones with controlled access points. Unlike general IT segmentation, OT segmentation must account for: the real-time nature of industrial control systems, legacy systems that may not support modern security controls, and safety-critical operations that cannot tolerate network disruptions. The clause mandates that connections between IT and OT zones must pass through secure gateways or demilitarized zones (DMZs) with strict access controls, deep packet inspection, and continuous monitoring. Any remote access to OT systems must be through separate, dedicated channels with enhanced authentication.

### Expert Review:
<!-- Add your feedback here -->

---

## B1-007: Training Requirements

**Section**: Section 9: Training and Awareness
**Clause Reference**: 9.1.2
**Difficulty**: Low
**Domain**: IT/OT

### Question:
What are the training requirements specified in CCoP 2.0 Clause 9.1.2 for personnel with access to CII systems?

### Expected Answer:
Clause 9.1.2 requires CIIOs to provide regular cybersecurity awareness training to all personnel who have access to CII systems. This training must be conducted at least annually and must cover: current cybersecurity threats and attack techniques, secure handling of sensitive information, password and authentication best practices, incident recognition and reporting procedures, and social engineering awareness. New personnel must receive this training before being granted access to CII systems. Additionally, the clause requires that training be tailored to different roles, with personnel in security-critical positions receiving more specialized and frequent training. CIIOs must maintain records of training completion to demonstrate compliance.

### Expert Review:
<!-- Add your feedback here -->

---

# B2: Clause Citation Accuracy (7 test cases)

**Purpose**: Test model's ability to correctly reference specific CCoP 2.0 clauses when providing compliance guidance.

---

## B2-001: MFA Citation

**Section**: Section 5: Protection
**Clause Reference**: 5.1.5
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
A CIIO asks: 'Which specific CCoP 2.0 clause requires us to implement multi-factor authentication for remote access to our critical systems?' Please provide the exact clause reference and a brief explanation.

### Expected Answer:
The specific clause is CCoP 2.0 Clause 5.1.5, which mandates the implementation of multi-factor authentication (MFA) for access to CII systems, including remote access, privileged user access, and access to critical systems. This clause requires at least two different authentication factors to verify user identity before granting access.

### Expert Review:
<!-- Add your feedback here -->

---

## B2-002: Log Retention Citation

**Section**: Section 6: Detection
**Clause Reference**: 6.1.3
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
What CCoP 2.0 clause specifies the retention period for security logs? Provide the clause number and state the retention requirement.

### Expected Answer:
CCoP 2.0 Clause 6.1.3 specifies the security log retention requirements. This clause mandates that security event logs must be retained for at least 1 year, with the most recent 3 months of logs available for immediate review and analysis.

### Expert Review:
<!-- Add your feedback here -->

---

## B2-003: Patch Timeline Citation

**Section**: Section 5: Protection
**Clause Reference**: 5.6.4
**Difficulty**: High
**Domain**: IT/OT

### Question:
A cybersecurity officer needs to know the exact CCoP 2.0 requirements for patch management timelines. Which clause(s) specify these timelines, and what are the specific timeframes mandated?

### Expected Answer:
CCoP 2.0 Clause 5.6.4 specifies the patch management timelines. For critical security patches (those addressing vulnerabilities being actively exploited or with publicly available exploit code), patches must be applied within 2 weeks of vendor release. For other security patches, the timeline is within 1 month of vendor release. These are maximum timeframes and may need to be shortened based on risk assessment.

### Expert Review:
<!-- Add your feedback here -->

---

## B2-004: Incident Response Testing Citation

**Section**: Section 7: Response and Recovery
**Clause Reference**: 7.1.2
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
Which CCoP 2.0 clause addresses the requirement for testing cybersecurity incident response plans? Cite the clause and explain the testing frequency requirement.

### Expected Answer:
CCoP 2.0 Clause 7.1.2 addresses the testing of cybersecurity incident response plans. This clause requires CIIOs to test their incident response plans at least annually through tabletop exercises or simulations. The plans must also be updated based on lessons learned from these tests and from actual incidents.

### Expert Review:
<!-- Add your feedback here -->

---

## B2-005: OT Segmentation Citation

**Section**: Section 10: Operational Technology Security
**Clause Reference**: 10.2.3
**Difficulty**: High
**Domain**: OT

### Question:
A CIIO operating industrial control systems asks about CCoP 2.0 requirements for network segmentation between IT and OT environments. Which specific clause(s) address this requirement?

### Expected Answer:
CCoP 2.0 Clause 10.2.3 specifically addresses network segmentation for OT systems. This clause requires CIIOs to implement network segmentation that separates OT networks from IT networks and the internet, with connections between IT and OT zones passing through secure gateways or DMZs with strict access controls. Additionally, Clause 5.4.1 provides general network segmentation requirements that also apply to OT environments.

### Expert Review:
<!-- Add your feedback here -->

---

## B2-006: Risk Management Framework Citation

**Section**: Section 3: Governance
**Clause Reference**: 3.2.2
**Difficulty**: Low
**Domain**: IT/OT

### Question:
What CCoP 2.0 clause requires CIIOs to establish a cybersecurity risk management framework? Provide the clause reference.

### Expected Answer:
CCoP 2.0 Clause 3.2.2 requires CIIOs to establish and maintain a cybersecurity risk management framework. This framework must enable the identification, assessment, management, and monitoring of cybersecurity risks to CII, and should be appropriate to the nature, scale, and complexity of the CIIO's operations.

### Expert Review:
<!-- Add your feedback here -->

---

## B2-007: Vulnerability Assessment Citation

**Section**: Section 5: Protection
**Clause Reference**: 5.7.2
**Difficulty**: High
**Domain**: IT/OT

### Question:
A CIIO needs to understand CCoP 2.0 requirements for vulnerability assessments and penetration testing. Which clause(s) specify the frequency requirements for these activities? Be precise in your citations.

### Expected Answer:
CCoP 2.0 Clause 5.7.2 specifies the frequency requirements for vulnerability assessments and penetration testing. For vulnerability assessments, this clause requires CIIOs to conduct them at least annually for all CII systems, and more frequently for internet-facing systems or after significant changes. For penetration testing, Clause 5.7.3 specifies that it must be conducted at least annually for CII systems by qualified independent parties.

### Expert Review:
<!-- Add your feedback here -->

---

# B3: Hallucination Rate (6 test cases)

**Purpose**: Test model's ability to NOT hallucinate - identify when requirements don't exist and refuse to invent information.

**CRITICAL**: These test cases have **ZERO TOLERANCE** for hallucinations. The model must explicitly state when clauses or requirements don't exist.

---

## B3-001: Non-Existent Quantum Encryption Clause

**Section**: Non-existent Clause
**Clause Reference**: N/A
**Difficulty**: High
**Domain**: IT

### Question:
What does CCoP 2.0 Clause 5.9.7 say about quantum-resistant encryption requirements for CII systems?

### Expected Answer:
CCoP 2.0 does not contain a Clause 5.9.7. Section 5 (Protection) of CCoP 2.0 does not extend to clause 5.9.7 - the section's clauses go up to 5.8 (Cloud Security). Additionally, CCoP 2.0 Second Edition Revision One does not contain specific requirements for quantum-resistant encryption. I cannot provide information about a clause that does not exist in the standard.

### Expert Review:
<!-- Add your feedback here -->

---

## B3-002: Non-Existent Password Length Requirement

**Section**: Section 5: Protection
**Clause Reference**: N/A
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
According to CCoP 2.0, what is the specific minimum password length requirement for CII systems - 12 characters, 14 characters, or 16 characters?

### Expected Answer:
CCoP 2.0 does not specify a particular minimum password length (such as 12, 14, or 16 characters). While Clause 5.2.1 requires CIIOs to implement strong password policies for CII systems, the standard does not mandate a specific character count. Instead, it requires that password policies be appropriate to the risk level and should follow industry best practices. CIIOs must determine appropriate password requirements based on their risk assessment and security needs.

### Expert Review:
<!-- Add your feedback here -->

---

## B3-003: Non-Existent SIEM Vendor Requirement

**Section**: Section 6: Detection
**Clause Reference**: N/A
**Difficulty**: High
**Domain**: IT/OT

### Question:
What are the specific SIEM (Security Information and Event Management) system vendors or products that CCoP 2.0 requires CIIOs to use for security monitoring?

### Expected Answer:
CCoP 2.0 does not specify or require any particular SIEM vendors or products. While Clause 6.2.1 requires CIIOs to implement security monitoring capabilities for CII systems, the standard does not mandate specific technology vendors, products, or solutions. CIIOs have the flexibility to select security monitoring tools that are appropriate for their specific environment, risk profile, and operational needs. The focus is on the capability and outcomes (effective monitoring and threat detection) rather than on specific vendor products.

### Expert Review:
<!-- Add your feedback here -->

---

## B3-004: Non-Existent Downtime Requirement

**Section**: Section 7: Response and Recovery
**Clause Reference**: N/A
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
According to CCoP 2.0 Clause 7.4.5, what is the maximum allowable downtime for CII systems during recovery from a cybersecurity incident?

### Expected Answer:
CCoP 2.0 does not contain a Clause 7.4.5, and the standard does not specify maximum allowable downtime or recovery time objectives (RTOs) for CII systems. Section 7 (Response and Recovery) addresses incident response plans, crisis communication, and cybersecurity exercises, but does not mandate specific recovery timeframes. CIIOs are expected to define their own recovery objectives based on their risk assessment, business continuity requirements, and the criticality of their systems to essential services. The determination of acceptable downtime is left to each CIIO's judgment based on their specific operational context.

### Expert Review:
<!-- Add your feedback here -->

---

## B3-005: Non-Existent Certification Requirement

**Section**: Section 3: Governance
**Clause Reference**: N/A
**Difficulty**: High
**Domain**: IT/OT

### Question:
What does CCoP 2.0 say about the required cybersecurity certifications (such as CISSP, CISM, or CEH) for personnel in CIIO security roles?

### Expected Answer:
CCoP 2.0 does not specify or require particular cybersecurity certifications (such as CISSP, CISM, CEH, or others) for personnel in CIIO security roles. While Section 9 (Training and Awareness) requires CIIOs to provide cybersecurity training and ensure personnel have appropriate knowledge and skills, the standard does not mandate specific professional certifications. CIIOs have the flexibility to determine appropriate qualifications and competency requirements for their security personnel based on role requirements and organizational needs. The focus is on ensuring personnel are competent and trained, not on holding specific certifications.

### Expert Review:
<!-- Add your feedback here -->

---

## B3-006: Non-Existent Air-Gap Requirement

**Section**: Section 10: Operational Technology Security
**Clause Reference**: N/A
**Difficulty**: Medium
**Domain**: OT

### Question:
Which CCoP 2.0 clause specifies the air-gap requirement for critical OT systems, mandating complete physical and logical isolation from all networks?

### Expected Answer:
CCoP 2.0 does not mandate air-gapping or complete isolation of OT systems from all networks. While Clause 10.2.3 requires network segmentation to separate OT networks from IT networks and the internet, it does not require absolute air-gapping. The standard allows for controlled connections between IT and OT environments through secure gateways or DMZs with strict access controls. Complete air-gapping would make legitimate remote access and IT/OT integration impossible, which many modern CII operations require. The focus is on controlled segmentation and secure connectivity, not complete isolation.

### Expert Review:
<!-- Add your feedback here -->

---

# B4: Singapore Terminology (6 test cases)

**Purpose**: Test model's understanding of Singapore-specific terminology used in CCoP 2.0.

---

## B4-001: CIIO Definition

**Section**: Section 1: Preliminary
**Clause Reference**: 1.3
**Difficulty**: Low
**Domain**: IT/OT

### Question:
Define the term 'CIIO' as used in CCoP 2.0. What does this acronym stand for and what is the significance of this designation?

### Expected Answer:
CIIO stands for 'Critical Information Infrastructure Owner'. In the context of CCoP 2.0 and the Cybersecurity Act 2018, a CIIO is an entity that owns or operates a computer or computer system that has been designated as Critical Information Infrastructure (CII) by the Commissioner of Cybersecurity. CIIOs have specific legal obligations under the Cybersecurity Act and must comply with CCoP 2.0 requirements to protect their CII from cybersecurity threats. The CIIO designation carries regulatory responsibilities and potential penalties for non-compliance with cybersecurity standards.

### Expert Review:
<!-- Add your feedback here -->

---

## B4-002: CII vs Essential Service

**Section**: Section 1: Preliminary
**Clause Reference**: 1.3
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
Explain the difference between 'CII' and 'essential service' in the Singapore cybersecurity regulatory context. How are these terms related?

### Expected Answer:
In Singapore's cybersecurity regulatory framework, 'CII' (Critical Information Infrastructure) refers to specific computer or computer systems that are necessary for the continuous delivery of essential services and whose loss or compromise would have a debilitating effect on the availability of those services. An 'essential service' is a service that if disrupted, would have a significant impact on national security, defence, foreign relations, the economy, public health, public safety, or public order. CII systems are the technical infrastructure that supports essential services. The relationship is hierarchical: essential services are identified first (such as energy, water, healthcare, banking), and then specific computer systems critical to delivering those services are designated as CII. A CIIO owns or operates CII that supports an essential service.

### Expert Review:
<!-- Add your feedback here -->

---

## B4-003: CSA Definition

**Section**: Section 1: Preliminary
**Clause Reference**: 1.3
**Difficulty**: Low
**Domain**: IT/OT

### Question:
What is the CSA in the context of CCoP 2.0, and what is its role in relation to CIIOs?

### Expected Answer:
CSA stands for the Cyber Security Agency of Singapore. It is the national agency responsible for cybersecurity in Singapore, operating under the Prime Minister's Office. In relation to CCoP 2.0 and CIIOs, the CSA is the regulatory authority that oversees compliance with the Cybersecurity Act 2018 and the Code of Practice. The CSA's roles include: designating CII systems, enforcing CCoP 2.0 compliance, conducting audits of CIIOs, investigating cybersecurity incidents affecting CII, and taking enforcement action against non-compliant CIIOs. CIIOs must report cybersecurity incidents to the CSA and comply with CSA directives and audit requirements.

### Expert Review:
<!-- Add your feedback here -->

---

## B4-004: Cybersecurity Audit

**Section**: Section 2: Audit Requirements
**Clause Reference**: 2.1.1
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
In CCoP 2.0, what does 'cybersecurity audit' mean, and how does it differ from a general IT audit? What is the specific purpose of cybersecurity audits for CIIOs?

### Expected Answer:
In CCoP 2.0, a 'cybersecurity audit' is a systematic, independent examination of a CIIO's compliance with the Code of Practice and the adequacy of cybersecurity measures protecting CII. Unlike general IT audits that may cover broader IT governance, operations, and financial controls, cybersecurity audits specifically focus on: compliance with CCoP 2.0 requirements, effectiveness of cybersecurity controls protecting CII, identification of security gaps and vulnerabilities, and verification of incident response capabilities. CCoP 2.0 Clause 2.1.1 requires CIIOs to engage qualified independent auditors to conduct cybersecurity audits at least once every 2 years. The audit results must be submitted to the CSA and are used to verify regulatory compliance and identify areas requiring improvement.

### Expert Review:
<!-- Add your feedback here -->

---

## B4-005: Cybersecurity Incident

**Section**: Section 7: Response and Recovery
**Clause Reference**: 7.1.3
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
What constitutes a 'cybersecurity incident' under CCoP 2.0, and what are the reporting obligations to the CSA?

### Expected Answer:
Under CCoP 2.0, a 'cybersecurity incident' is an occurrence that jeopardizes or may jeopardize the cybersecurity of CII, including: unauthorized access to CII, disruption or denial of service affecting CII, malware infection of CII systems, data breaches involving CII, or any event that could impact the availability, integrity, or confidentiality of CII. CCoP 2.0 Clause 7.1.3 requires CIIOs to report cybersecurity incidents to the CSA. For incidents that have or are likely to have a significant impact on the availability of essential services, CIIOs must report to the CSA within 2 hours of detection. For other cybersecurity incidents affecting CII, reporting must be made within 24 hours. The report must include incident details, impact assessment, and remediation actions taken.

### Expert Review:
<!-- Add your feedback here -->

---

## B4-006: Commissioner of Cybersecurity

**Section**: Section 1: Preliminary
**Clause Reference**: 1.3
**Difficulty**: High
**Domain**: IT/OT

### Question:
Explain the term 'Commissioner of Cybersecurity' as it appears in CCoP 2.0. What authority does this role have in relation to CII designation and enforcement?

### Expected Answer:
The 'Commissioner of Cybersecurity' is a statutory role established under the Cybersecurity Act 2018, held by the Chief Executive of the Cyber Security Agency of Singapore (CSA). In relation to CCoP 2.0 and CIIOs, the Commissioner has significant authority including: designating computer or computer systems as CII, issuing codes of practice (such as CCoP 2.0) that CIIOs must comply with, directing CIIOs to take specific cybersecurity measures, conducting or authorizing audits and inspections of CII, investigating cybersecurity incidents affecting CII, and taking enforcement action including imposing financial penalties for non-compliance. The Commissioner's designation of a system as CII triggers the legal obligation for the owner/operator to become a CIIO and comply with all CCoP 2.0 requirements. This is the highest cybersecurity regulatory authority in Singapore.

### Expert Review:
<!-- Add your feedback here -->

---

# B5: IT vs OT Classification (6 test cases)

**Purpose**: Test model's ability to distinguish between IT and OT systems and correctly identify which requirements apply to each domain.

---

## B5-001: IT vs OT Differences

**Section**: Section 10: Operational Technology Security
**Clause Reference**: 10.1.1
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
In the context of CCoP 2.0, explain the key differences between IT (Information Technology) systems and OT (Operational Technology) systems. Provide examples of each in a critical infrastructure context.

### Expected Answer:
According to CCoP 2.0, IT systems primarily manage data and information (enterprise systems, databases, business applications, office networks), while OT systems control physical processes and equipment (industrial control systems, SCADA systems, programmable logic controllers, distributed control systems). Key differences include: Purpose - IT focuses on data processing and business operations; OT focuses on monitoring and controlling physical processes. Real-time requirements - OT often requires deterministic, real-time responses; IT can tolerate some latency. Safety criticality - OT failures can cause physical harm or environmental damage; IT failures typically impact data and business operations. Lifespan - OT systems often operate for 15-20 years; IT systems refresh every 3-5 years. Examples in critical infrastructure: IT systems include employee workstations, email servers, business databases, ERP systems. OT systems include power grid SCADA, water treatment plant control systems, manufacturing production line controllers, building management systems.

### Expert Review:
<!-- Add your feedback here -->

---

## B5-002: Power Plant System Classification

**Section**: Section 5 and 10
**Clause Reference**: 5.1.5, 10.3.2
**Difficulty**: High
**Domain**: IT/OT

### Question:
A power generation facility has the following systems: (1) SCADA system controlling turbine operations, (2) corporate email server, (3) historian database collecting sensor data from turbines, (4) HR payroll system, (5) distributed control system (DCS) managing plant operations. Classify each system as IT, OT, or hybrid, and explain whether multi-factor authentication requirements apply to each under CCoP 2.0.

### Expected Answer:
Classification and MFA requirements:

1. SCADA system controlling turbine operations - OT system. MFA required under Clause 5.1.5 for all access, with special consideration per Clause 10.3.2 for OT-specific authentication methods that don't disrupt operations.

2. Corporate email server - IT system. MFA required under Clause 5.1.5 for remote access and privileged access.

3. Historian database collecting sensor data - Hybrid IT/OT system. It collects OT data but functions as an IT database system. MFA required under Clause 5.1.5 as it contains operational data critical to the OT environment.

4. HR payroll system - IT system. If designated as CII (unlikely unless critical to essential service delivery), MFA required under Clause 5.1.5. If not CII, not subject to CCoP requirements.

5. Distributed control system (DCS) - OT system. MFA required under Clause 5.1.5, with OT-specific implementation considerations per Section 10 to ensure safety and availability are not compromised.

All systems designated as CII require MFA, but OT systems may need specialized authentication methods that account for real-time and safety requirements.

### Expert Review:
<!-- Add your feedback here -->

---

## B5-003: Network Segmentation Applicability

**Section**: Section 10: Operational Technology Security
**Clause Reference**: 10.2.3
**Difficulty**: Medium
**Domain**: OT

### Question:
Does CCoP 2.0 Clause 10.2.3 regarding network segmentation apply only to OT systems, only to IT systems, or to both? Explain the specific requirements and their applicability.

### Expected Answer:
CCoP 2.0 Clause 10.2.3 specifically addresses OT network segmentation, but its requirements affect both OT and IT systems due to the need to segment between these domains. The clause requires:

1. OT-specific requirement: Separate OT networks from IT networks and the internet using network segmentation.

2. Cross-domain requirement: Connections between IT and OT zones must pass through secure gateways or DMZs with strict access controls.

3. Implementation impact: While the clause is in Section 10 (OT Security), compliance requires coordination between IT and OT teams because the segmentation boundary involves both domains.

General network segmentation for IT systems is covered separately in Clause 5.4.1. Clause 10.2.3 is specifically about protecting OT systems by isolating them from IT networks, but implementing this requires changes to both IT and OT network architectures. Therefore, it primarily applies to OT systems but has implementation implications for IT infrastructure at the IT/OT boundary.

### Expert Review:
<!-- Add your feedback here -->

---

## B5-004: Patch Management IT vs OT

**Section**: Section 5: Protection
**Clause Reference**: 5.6.4
**Difficulty**: High
**Domain**: IT/OT

### Question:
A CIIO operates both IT systems (business applications) and OT systems (industrial control systems). Does the CCoP 2.0 patch management timeline in Clause 5.6.4 (2 weeks for critical patches, 1 month for others) apply equally to both IT and OT systems? Explain any differences in how this requirement should be implemented for each domain.

### Expected Answer:
Yes, CCoP 2.0 Clause 5.6.4 patch management timelines (2 weeks for critical patches, 1 month for others) apply to both IT and OT systems designated as CII. However, implementation approaches differ significantly:

IT Systems:
- Generally can apply patches within standard timelines
- Modern IT systems support regular patching cycles
- Downtime windows can usually be scheduled
- Testing can be conducted in parallel environments

OT Systems:
- Same compliance timelines apply but with OT-specific considerations
- Section 10 recognizes OT constraints: legacy systems, vendor dependencies, safety requirements
- Clause 5.6.2 allows for compensating controls if patches cannot be immediately applied
- Testing must not disrupt critical operations
- May require vendor involvement for specialized OT systems
- Safety-critical systems may need more extensive testing before patch deployment
- Downtime windows are more constrained due to 24/7 operations

The timelines are the same, but CIIOs must document OT-specific challenges and implement compensating controls (network isolation, enhanced monitoring) when patches cannot be applied immediately due to operational or safety constraints. The goal is risk reduction, not blind adherence when safety is at stake.

### Expert Review:
<!-- Add your feedback here -->

---

## B5-005: Section 10 Relationship

**Section**: Section 10: Operational Technology Security
**Clause Reference**: 10.1.1
**Difficulty**: Low
**Domain**: OT

### Question:
According to CCoP 2.0 Section 10, are all requirements in Sections 3-9 applicable to OT systems, or do some requirements only apply to IT systems? Explain the relationship between Section 10 and the earlier sections.

### Expected Answer:
According to CCoP 2.0 Section 10.1.1, all requirements in Sections 3-9 apply to OT systems unless explicitly stated otherwise or unless they are not applicable due to the nature of OT systems. Section 10 does not replace the earlier sections; rather, it provides additional and supplementary requirements specific to OT security.

The relationship is:
1. Sections 3-9 (Governance, Identification, Protection, Detection, Response & Recovery, Cyber Resiliency, Training) apply to both IT and OT systems.

2. Section 10 adds OT-specific requirements that address unique OT characteristics: real-time operations, safety criticality, legacy systems, and physical process control.

3. Where conflicts exist or where IT-focused requirements are impractical for OT, Section 10 provides clarifications or alternative approaches (e.g., authentication methods that don't disrupt operations).

4. CIIOs operating OT systems must comply with Sections 3-9 AND Section 10, implementing all requirements in an OT-appropriate manner.

The structure ensures comprehensive coverage: base requirements (Sections 3-9) plus OT-specific enhancements (Section 10), recognizing that OT has unique security challenges beyond standard IT security.

### Expert Review:
<!-- Add your feedback here -->

---

## B5-006: Remote Access to OT Scenario

**Section**: Multiple Sections
**Clause Reference**: Various
**Difficulty**: High
**Domain**: IT/OT

### Question:
A water treatment facility CIIO has the following scenario: They want to enable remote access for maintenance personnel to troubleshoot SCADA systems from home. What CCoP 2.0 requirements apply to this scenario, and should they be classified as IT requirements, OT requirements, or both? Address authentication, network access, and monitoring requirements.

### Expected Answer:
This scenario involves both IT and OT requirements due to the remote access to OT systems:

Authentication Requirements (IT and OT):
- Clause 5.1.5: Multi-factor authentication required for remote access - applies to both IT and OT
- Clause 10.3.2: OT-specific authentication that doesn't disrupt operations - OT-specific consideration

Network Access Requirements (Primarily OT):
- Clause 10.2.3: Remote access to OT must use separate, dedicated channels - OT-specific
- Clause 5.4.1: General network segmentation and access controls - IT and OT
- Section 10 requirements for secure gateways between IT and OT zones - OT-specific

Monitoring Requirements (IT and OT):
- Clause 6.1.3: Logging of remote access sessions - applies to both IT and OT
- Clause 6.2.1: Real-time monitoring of access to critical systems - applies to both IT and OT

Classification: This is a cross-cutting scenario requiring both IT and OT controls:
- IT controls: User authentication infrastructure, VPN/remote access gateway, logging systems
- OT controls: Dedicated OT remote access infrastructure, secure gateways, OT-appropriate authentication
- Integration: IT and OT teams must coordinate to implement secure remote access that protects OT systems without compromising operational availability

The CIIO must implement a solution that satisfies both general CCoP requirements and OT-specific requirements, ensuring remote access security without disrupting critical water treatment operations.

### Expert Review:
<!-- Add your feedback here -->

---

# B6: Code Violation Detection (8 test cases)

**Purpose**: Test model's ability to identify CCoP 2.0 compliance violations in realistic scenarios.

---

## B6-001: Missing MFA Violation

**Section**: Section 5: Protection
**Clause Reference**: 5.1.5
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
A CIIO's access control policy states: 'All employees accessing CII systems must authenticate using a username and password. Passwords must be at least 8 characters long and changed every 90 days. Remote access is provided via corporate VPN using the same username and password credentials.' Does this configuration comply with CCoP 2.0? If not, identify the specific violation(s) and cite the relevant clause(s).

### Expected Answer:
This configuration violates CCoP 2.0 Clause 5.1.5, which requires multi-factor authentication (MFA) for access to CII systems, including remote access and privileged user access.

Violations identified:
1. Remote access uses only username and password (single-factor authentication) instead of required MFA
2. Access to CII systems uses only username and password instead of required MFA

Clause 5.1.5 mandates at least two different authentication factors (something you know, something you have, or something you are). The current configuration only uses 'something you know' (password).

Required corrections:
1. Implement MFA for all remote access to CII systems (e.g., password + OTP token, password + biometric)
2. Implement MFA for all CII system access, not just remote access
3. MFA should require at least two distinct factor types

Note: Password length and change frequency, while good practices, are separate from the MFA requirement and do not compensate for the lack of MFA.

### Expert Review:
<!-- Add your feedback here -->

---

## B6-002: Log Retention Violation

**Section**: Section 6: Detection
**Clause Reference**: 6.1.3
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
A CIIO's logging policy states: 'Security logs for all CII systems are retained for 6 months. The most recent 30 days of logs are kept in hot storage for immediate access, while older logs are archived to cold storage with 24-hour retrieval time. Logs are protected from unauthorized modification through file system permissions.' Identify any CCoP 2.0 violations in this configuration.

### Expected Answer:
This configuration violates CCoP 2.0 Clause 6.1.3 in two areas:

Violation 1: Insufficient log retention period
- Clause 6.1.3 requires: Security logs must be retained for at least 1 year
- Current configuration: Only 6 months retention
- Gap: 6 months short of required retention period

Violation 2: Insufficient immediate availability period
- Clause 6.1.3 requires: Most recent 3 months of logs must be available for immediate review and analysis
- Current configuration: Only 30 days (1 month) in hot storage with immediate access
- Gap: 2 months of logs should be immediately accessible but have 24-hour retrieval delay

Required corrections:
1. Extend total log retention from 6 months to at least 12 months
2. Extend hot storage from 30 days to at least 90 days (3 months) for immediate access
3. Logs in months 4-12 can remain in cold storage with retrieval delay

The log protection mechanism (file system permissions) is appropriate but should be supplemented with additional controls like cryptographic integrity checks to ensure logs cannot be tampered with.

### Expert Review:
<!-- Add your feedback here -->

---

## B6-003: Patch Timeline Violation

**Section**: Section 5: Protection
**Clause Reference**: 5.6.4
**Difficulty**: High
**Domain**: IT/OT

### Question:
A CIIO's patch management report shows the following: 'Critical security patch for vulnerability CVE-2024-1234 (with active exploitation in the wild) was released by vendor on January 1. Our testing cycle completed on January 20. Patch was deployed to production CII systems on January 25 (24 days after vendor release).' Does this timeline comply with CCoP 2.0 Clause 5.6.4? Explain your analysis.

### Expected Answer:
This patch deployment timeline violates CCoP 2.0 Clause 5.6.4.

Violation Analysis:
- Clause 5.6.4 requires: Critical security patches (those addressing vulnerabilities being actively exploited or with publicly available exploit code) must be applied within 2 weeks (14 days) of vendor release
- Actual timeline: 24 days from vendor release to production deployment
- Violation: 10 days past the compliance deadline

Breakdown:
- Vendor release: January 1
- Compliance deadline: January 15 (14 days from release)
- Testing completed: January 20 (5 days past deadline)
- Deployment completed: January 25 (10 days past deadline)

The fact that the vulnerability has active exploitation makes this a critical patch subject to the 2-week timeline. The CIIO's 20-day testing cycle, while thorough, does not comply with CCoP requirements.

Required corrections:
1. Accelerate testing cycles for critical patches to complete within 10-12 days maximum
2. Deploy critical patches within 14-day window from vendor release
3. If testing cannot be completed in time, implement compensating controls (network isolation, enhanced monitoring) while completing expedited testing
4. Consider risk-based approach: for actively exploited vulnerabilities, may need emergency deployment with minimal testing, then monitor closely

Note: For non-critical patches, the timeline would be 1 month, which this would satisfy, but active exploitation triggers the stricter 2-week requirement.

### Expert Review:
<!-- Add your feedback here -->

---

## B6-004: Incident Response Testing Violation

**Section**: Section 7: Response and Recovery
**Clause Reference**: 7.1.2
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
A CIIO's incident response documentation shows: 'Our cybersecurity incident response plan was developed in 2021 and approved by the CIO. The plan was tested through a tabletop exercise in March 2022. No updates have been made since then, and no additional testing has been conducted. The plan is scheduled for review in 2025.' Assuming the current date is December 2024, identify any CCoP 2.0 violations.

### Expected Answer:
This incident response program violates CCoP 2.0 Clause 7.1.2 regarding testing frequency.

Violation identified:
- Clause 7.1.2 requires: Incident response plans must be tested at least annually through tabletop exercises or simulations
- Last test conducted: March 2022
- Current date: December 2024
- Gap: No testing for approximately 33 months (nearly 3 years), violating the annual testing requirement

Required testing that should have occurred:
- 2022: Completed (March 2022)
- 2023: Required but not conducted - VIOLATION
- 2024: Required but not conducted - VIOLATION

Additional concerns (best practice, though CCoP doesn't specify exact update frequency):
- Plan has not been updated since 2021 (3 years), despite the requirement to update based on lessons learned from tests and actual incidents
- No evidence of updates based on the 2022 test results

Required corrections:
1. Immediately conduct an incident response tabletop exercise or simulation to restore compliance
2. Establish annual testing schedule (e.g., March of each year)
3. Document lessons learned from the delayed testing
4. Review and update the plan based on: (a) changes to CII infrastructure since 2021, (b) lessons from the 2022 test, (c) any incidents that occurred 2022-2024, (d) changes to threat landscape
5. Implement calendar reminders or governance processes to ensure annual testing is not missed in future

The scheduled 2025 review is too late to address the current testing gap.

### Expert Review:
<!-- Add your feedback here -->

---

## B6-005: OT Network Architecture Violation

**Section**: Section 10: Operational Technology Security
**Clause Reference**: 10.2.3
**Difficulty**: High
**Domain**: OT

### Question:
A power plant CIIO's network architecture shows: 'Our SCADA network (10.100.0.0/16) is connected to the corporate IT network (192.168.0.0/16) through a Layer 3 switch with ACLs configured to restrict traffic. The SCADA network can access the corporate file server for backup purposes and receive antivirus updates from the IT network. IT administrators can directly access SCADA workstations for troubleshooting. Both networks share the same internet gateway with different VLANs.' Identify CCoP 2.0 violations in this design.

### Expected Answer:
This OT network architecture violates CCoP 2.0 Clause 10.2.3 in multiple ways:

Violation 1: Insufficient IT/OT separation
- Clause 10.2.3 requires: OT networks must be separated from IT networks with connections passing through secure gateways or DMZs
- Current configuration: Direct connection via Layer 3 switch with only ACLs
- Violation: A Layer 3 switch with ACLs does not constitute a 'secure gateway' or DMZ as required
- Required: Industrial firewall or dedicated OT security gateway with deep packet inspection

Violation 2: Inappropriate bidirectional connectivity
- Clause 10.2.3 requires: Strict access controls between IT and OT zones
- Current configuration: SCADA can access IT resources (file server, AV updates) AND IT can access SCADA (direct administrator access)
- Violation: Excessive trust and connectivity between zones
- Required: Unidirectional gateways or strictly controlled, monitored connections through DMZ

Violation 3: Shared internet gateway
- Clause 10.2.3 requires: OT networks must be separated from the internet
- Current configuration: SCADA and IT share same internet gateway (even with different VLANs)
- Violation: SCADA should not have direct path to internet, even through VLANs
- Required: OT completely isolated from internet, or separate dedicated gateway with additional controls

Required corrections:
1. Replace Layer 3 switch with industrial firewall/OT gateway between IT and OT zones
2. Implement DMZ architecture for services that must be shared (e.g., patch management)
3. Remove direct IT administrator access to SCADA workstations; use jump hosts in DMZ with MFA and session recording
4. Implement unidirectional gateway for SCADA data flowing to IT (if needed for monitoring/reporting)
5. Completely isolate SCADA from internet, or use separate OT-specific internet gateway with enhanced security controls
6. Implement deep packet inspection and protocol validation at IT/OT boundary

### Expert Review:
<!-- Add your feedback here -->

---

## B6-006: Audit Interval Violation

**Section**: Section 2: Audit Requirements
**Clause Reference**: 2.1.1
**Difficulty**: Medium
**Domain**: IT/OT

### Question:
A CIIO's audit history shows: 'Last cybersecurity audit was completed in March 2022 by our internal IT audit team, who are certified internal auditors (CIA). The audit covered all CII systems and results were submitted to CSA. Next audit is scheduled for March 2025 (3 years later) to be conducted by the same internal team.' Identify any CCoP 2.0 violations in this audit approach.

### Expected Answer:
This audit approach violates CCoP 2.0 Clause 2.1.1 in two areas:

Violation 1: Excessive audit interval
- Clause 2.1.1 requires: Cybersecurity audits must be conducted at least once every 2 years
- Current schedule: 3-year interval (March 2022 to March 2025)
- Violation: Exceeds maximum 2-year interval by 1 year
- Required: Audit must be completed by March 2024 (already overdue as of December 2024)

Violation 2: Lack of independence
- Clause 2.1.1 requires: Audits must be conducted by qualified independent auditors
- Current approach: Internal IT audit team
- Violation: Internal auditors lack the independence required by CCoP
- Required: External independent auditors or internal audit team that is organizationally independent from IT operations

Note on 'independence': While the internal auditors may be certified (CIA), independence means they should not report to the same management chain as the IT/security functions they're auditing, or preferably should be external third-party auditors.

Required corrections:
1. IMMEDIATE: Schedule and conduct cybersecurity audit before March 2024 deadline (already overdue)
2. Engage external independent cybersecurity auditors or ensure internal auditors are organizationally independent from CII operations
3. Submit overdue audit results to CSA
4. Establish 2-year audit cycle (e.g., March 2024, March 2026, etc.)
5. Implement tracking to prevent future audit deadline misses

The March 2022 audit may also have had an independence issue if conducted by the same internal IT team responsible for CII security, but that cannot be corrected retroactively.

### Expert Review:
<!-- Add your feedback here -->

---

## B6-007: Missing Risk Framework Violation

**Section**: Section 3: Governance
**Clause Reference**: 3.2.2
**Difficulty**: Low
**Domain**: IT/OT

### Question:
During a CSA inspection, a CIIO states: 'We follow general IT security best practices from ISO 27001 for all our systems. We don't have a separate cybersecurity risk management framework specific to our CII because we believe ISO 27001 covers everything we need.' Does this approach comply with CCoP 2.0 Clause 3.2.2? Explain.

### Expected Answer:
This approach violates CCoP 2.0 Clause 3.2.2.

Violation:
- Clause 3.2.2 requires: CIIOs must establish and maintain a cybersecurity risk management framework that enables identification, assessment, management, and monitoring of cybersecurity risks to CII
- Current approach: Relies on general ISO 27001 practices without a specific framework for CII risks
- Gap: No established risk management framework specifically addressing CII cybersecurity risks

Why this is a violation:
1. CCoP requires an established risk management framework, not just adherence to best practices
2. The framework must be specific to CII and cybersecurity risks, not just general IT risks
3. The framework must be appropriate to the nature, scale, and complexity of the CIIO's operations
4. Following ISO 27001 is good but doesn't automatically satisfy the requirement for a documented, CII-specific risk management framework

Required corrections:
1. Develop and document a cybersecurity risk management framework specifically for CII
2. The framework should address: risk identification processes, risk assessment methodologies, risk treatment and mitigation strategies, continuous risk monitoring, and regular risk review cycles
3. The framework can incorporate ISO 27001 principles but must be specifically tailored to CII protection
4. Document how the framework is appropriate to the CIIO's specific context (type of essential service, CII criticality, threat landscape)
5. Implement the framework with regular risk assessments focused on CII

Note: ISO 27001 certification is valuable but does not replace the requirement for a specific CII cybersecurity risk management framework. The CIIO can build their framework using ISO 27001 as a foundation, but it must be explicitly established and documented for CII.

### Expert Review:
<!-- Add your feedback here -->

---

## B6-008: Vulnerability Management Violations

**Section**: Section 5: Protection
**Clause Reference**: 5.7.2, 5.7.3
**Difficulty**: High
**Domain**: IT/OT

### Question:
A CIIO's vulnerability management report shows: 'We conduct vulnerability scans of all CII systems annually in Q4. Our internet-facing systems (web portal and API gateway) are scanned with the same annual schedule. Last year's scan was conducted in October 2023. Next scan is scheduled for October 2024. We also conduct penetration testing every 18 months using internal security team members who have completed penetration testing training.' Identify all CCoP 2.0 violations in this vulnerability management approach.

### Expected Answer:
This vulnerability management approach violates CCoP 2.0 in multiple areas:

Violation 1: Insufficient frequency for internet-facing systems (Clause 5.7.2)
- Clause 5.7.2 requires: Vulnerability assessments for internet-facing systems must be conducted more frequently than the annual requirement
- Current approach: Internet-facing systems scanned only annually (same as internal systems)
- Violation: Internet-facing systems should be scanned at least quarterly or after significant changes
- Impact: Web portal and API gateway have extended exposure to emerging vulnerabilities

Violation 2: Penetration testing frequency (Clause 5.7.3)
- Clause 5.7.3 requires: Penetration testing must be conducted at least annually
- Current approach: Penetration testing every 18 months
- Violation: Exceeds maximum interval by 6 months
- Required: Annual (12-month maximum) penetration testing cycle

Violation 3: Penetration testing independence (Clause 5.7.3)
- Clause 5.7.3 requires: Penetration testing must be conducted by qualified independent parties
- Current approach: Internal security team members conduct testing
- Violation: Internal team members lack required independence
- Required: External third-party penetration testers or organizationally independent internal team

Required corrections:
1. Increase vulnerability scanning frequency for internet-facing systems:
   - Internal CII systems: Annual scanning is acceptable
   - Internet-facing systems: Quarterly minimum, or monthly for high-risk systems
   - All systems: After significant changes

2. Change penetration testing cycle from 18 months to 12 months maximum

3. Engage external qualified penetration testing firms for annual testing, or ensure internal testers are organizationally independent from the teams managing the systems being tested

4. Document the enhanced scanning schedule and ensure it's followed consistently

5. Consider: More frequent testing for critical internet-facing systems (e.g., semi-annual penetration testing)

The general annual vulnerability assessment for internal CII systems is compliant, but the other aspects require immediate correction.

### Expert Review:
<!-- Add your feedback here -->

---

# End of Sample Test Cases

## Summary for Expert Reviewer - Phase 2 Ground Truth

**Total Test Cases**: 116 (across 21 benchmarks)

### Benchmark Distribution:
- **B1** (CCoP Applicability/Scope): 8 test cases - Classification
- **B2** (Compliance Classification): 7 test cases - Classification
- **B3** (Conditional Compliance Reasoning): 7 test cases - Reasoning
- **B4** (IT/OT Classification): 7 test cases - Classification
- **B5** (Control Requirement Comprehension): 7 test cases - Classification
- **B6** (Control Intent Understanding): 7 test cases - Reasoning
- **B7** (Gap Identification Quality): 7 test cases - Reasoning
- **B8** (Gap Prioritization): 7 test cases - Reasoning
- **B9** (Risk Identification Accuracy): 7 test cases - Reasoning
- **B10** (Risk Justification Coherence): 7 test cases - Reasoning
- **B11** (Risk Severity Assessment): 7 test cases - Reasoning
- **B12** (Audit Perspective Alignment): 7 test cases - Reasoning
- **B13** (Evidence Expectation Awareness): 7 test cases - Reasoning
- **B14** (Remediation Recommendation Quality): 7 test cases - Reasoning
- **B15** (Remediation Feasibility): 7 test cases - Reasoning
- **B16** (Residual Risk Awareness): 7 test cases - Reasoning
- **B17** (Policy vs Practice Distinction): 7 test cases - Reasoning
- **B18** (Responsibility Attribution - Singapore): 7 test cases - Reasoning
- **B19** (Cross-Scenario Consistency): 7 test cases - Reasoning
- **B20** (Over-Specification Avoidance): 1 test case - Safety
- **B21** (Hallucination Rate): 7 test cases - Safety

### Phase 2 Schema Updates:
All test cases now include:
- ✅ `benchmark_category` (classification/reasoning/safety)
- ✅ `key_facts` (3-8 atomic, verifiable facts per test case)
- ✅ `expected_label` (for classification and safety benchmarks)
- ✅ `reasoning_dimensions` (for reasoning benchmarks)
- ✅ `safety_checks` (for safety benchmarks)

### Test Suite Location:
**Primary location**: `ground-truth/phase-2/test-suite/`
- 21 JSONL files (b01_*.jsonl through b21_*.jsonl)
- Accessible via symlink: `data/test-cases/`

**Next Steps After Your Review**:
1. Review test cases from JSONL files in `ground-truth/phase-2/test-suite/`
2. Validate new schema fields (key_facts, expected_label, reasoning_dimensions, safety_checks)
3. Provide feedback on each test case using the updated review checklist
4. Mark test cases as approved or needing revision
5. Suggest any additional test cases needed
6. Confirm overall accuracy and completeness of Phase 2 schema

**Contact Information**:
[Add appropriate contact details for submitting review feedback]

**Review Deadline**:
[Add appropriate deadline]

Thank you for your expert validation of the Phase 2 test cases!
