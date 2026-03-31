## Deep Dive: Singapore CIIO & CCoP Practices

### Strategic Summary

Singapore's Critical Information Infrastructure (CII) regulatory regime -- anchored by the Cybersecurity Act 2018, the CCoP 2.0 (July 2022), and the Cybersecurity (Amendment) Act 2024 -- is among the most prescriptive critical infrastructure cybersecurity frameworks in Asia-Pacific. The regime designates 11 critical sectors, imposes ~220 compliance clauses on CII Owners (CIIOs), mandates biennial audits, and enforces 2-hour incident reporting. For Risk Managers operating within CII organizations, the day-to-day reality involves navigating overlapping regulatory requirements (CCoP, IM8, MAS-TRM), managing waiver processes, preparing for audits, and bridging the IT/OT security divide -- all while the regulatory landscape continues to expand with new entity classifications (ESCI, STCC, FDI) under the 2024 amendments.

### Key Questions

- What are Singapore's designated CII sectors and their typical IT/OT architectures?
- What are common CCoP 2.0 compliance challenges and audit findings?
- What does the CSA enforcement/audit process look like?
- How do CII organizations structure risk management? What role does the Risk Manager play vs CIIO vs CISO?
- What changed from CCoP 1.0 to 2.0? What was the transition experience?
- What is IM8? How does SII classification work?
- What are realistic day-to-day compliance questions a Risk Manager would face?
- What are sector-specific implementation challenges (IT-heavy vs OT-heavy)?

---

### CII Sector Landscape

#### Designated Sectors (11 Total)

Singapore's Cybersecurity Act designates 11 critical sectors. The list of specific CII systems and their owners is classified for national security reasons -- only the sectors are public:

1. **Energy** -- Power generation, transmission, distribution (SP Group, Senoko Energy, etc.)
2. **Water** -- PUB (Singapore's National Water Agency) water treatment and distribution
3. **Banking & Finance** -- MAS-regulated financial institutions (DBS, OCBC, UOB, SGX)
4. **Healthcare** -- Public health clusters (SingHealth, NHG), hospital IT systems
5. **Aviation** -- Changi Airport Group, CAAS air traffic management
6. **Land Transport** -- LTA, SMRT, SBS Transit rail and bus systems
7. **Maritime** -- MPA port operations, vessel traffic systems
8. **Info-communications** -- Singtel, StarHub, M1 telecommunications infrastructure
9. **Government** -- GovTech, government ICT systems
10. **Media** -- Mediacorp, broadcast infrastructure
11. **Security & Emergency** -- SPF, SCDF, MHA emergency services systems

#### Typical IT/OT Architectures by Sector Type

**OT-Heavy Sectors (Energy, Water, Maritime, Transport)**
- SCADA (Supervisory Control and Data Acquisition) systems controlling physical processes
- Programmable Logic Controllers (PLCs) managing actuators and sensors
- Safety Instrumented Systems (SIS) for fail-safe operations
- Distributed Control Systems (DCS) in power plants and water treatment
- Industrial Control Systems (ICS) with legacy protocols (Modbus, DNP3, OPC)
- Increasing IT/OT convergence via gateways and DMZs
- Air-gapped or semi-air-gapped OT networks with controlled connection points
- Typical architecture: Enterprise IT network -> DMZ -> OT network -> Field devices

**IT-Heavy Sectors (Banking, Info-comms, Government, Media)**
- Standard enterprise architecture: data centres, cloud services, web applications
- Core banking systems, payment gateways, SWIFT connectivity
- Cloud-native and hybrid cloud deployments (increasingly common)
- API-driven architectures with third-party integrations
- Mobile and internet banking platforms

**Hybrid Sectors (Healthcare, Aviation)**
- Medical devices and IoT sensors alongside hospital IT systems
- Clinical systems (EMR/EHR) with both IT and specialized medical device networks
- Aviation: air traffic management systems (OT) alongside passenger processing (IT)

#### Sector-Specific Cybersecurity Challenges

| Sector | Key Challenge | Architecture Complexity |
|--------|--------------|----------------------|
| Energy | Legacy SCADA systems not designed for security; patching disrupts operations | Very High (OT) |
| Water | 24/7 operations make maintenance windows rare; sensor networks exposed | High (OT) |
| Banking | Regulatory overlap (MAS-TRM + CCoP); cloud migration risks | High (IT) |
| Healthcare | Medical device vulnerabilities; post-SingHealth breach heightened scrutiny | High (Hybrid) |
| Transport | Real-time systems cannot tolerate latency from security controls | High (OT/IT) |
| Telecoms | Scale of infrastructure; 5G security implications | Very High (IT) |
| Government | IM8 + CCoP dual compliance burden; classified system constraints | High (IT) |

---

### CCoP 2.0 Implementation in Practice

#### Structure and Scope

CCoP 2.0 contains approximately 220 clauses across 11 requirement domains (a 116% increase from CCoP 1.0's ~102 clauses). The 7 auditable domains are:

1. **Governance** -- Cybersecurity leadership, roles, risk management framework
2. **Identification** -- Asset management, risk assessment, threat modelling
3. **Protection** -- Access control, network security, system hardening, patch management, cryptography, vulnerability assessment, penetration testing
4. **Detection** -- Logging, monitoring, threat hunting, threat intelligence sharing
5. **Response & Recovery** -- Incident management, crisis communication, BCP/DR, backup
6. **Cyber Resilience** -- Exercises, continuous improvement
7. **Cybersecurity Training & Awareness** -- Role-based training, awareness programmes
8. **OT Security** (Addendum) -- OT-specific architecture, secure coding, field controller security

The CCoP applies specifically to the CII system -- defined as computer systems, network components, and end-point devices within a digital boundary jointly defined by CSA, CIIOs, and Sector Leads. It does not formally apply to the entire CII organization, though CSA encourages extending capabilities organization-wide via Annex A (non-auditable).

#### Common Implementation Challenges

**1. Scale of New Requirements**
The jump from ~102 to ~220 clauses within a 12-month grace period created significant implementation pressure. Many CIIOs, particularly smaller ones in sectors like water and media, lacked the internal cybersecurity teams to address the expanded scope.

**2. OT Security Gap**
The OT addendum introduced mandatory OT-specific practices that many CIIOs had never formalized. Legacy ICS/SCADA systems were purpose-built for reliability, not security -- most lack basic controls like authentication and encryption. Patching OT systems risks operational disruption to essential services.

**3. IT/OT Convergence**
With increasing connectivity between IT and OT networks, threat actors can compromise internet-facing IT systems and pivot to OT environments. Implementing proper segmentation (DMZs, data diodes) between IT and OT while maintaining operational data flows is a major challenge.

**4. Supply Chain Risk Management**
CCoP 2.0 requires vendor risk management frameworks and mandates that all vendor access to CII be performed on-site. Managing cybersecurity requirements across multiple tiers of the supply chain is operationally complex.

**5. Regulatory Overlap**
Government sector CIIOs face dual compliance with IM8 and CCoP 2.0, particularly in access control management and system hardening. Financial sector CIIOs must satisfy both MAS-TRM guidelines and CCoP requirements. CSA acknowledged this concern and committed to harmonization efforts, including mutually recognized audits.

**6. Cloud Migration Uncertainty**
Moving CII workloads to the cloud raises questions about shared responsibility boundaries, data sovereignty, and how CCoP clauses apply in cloud-hosted environments. CSA addressed this by noting that CCoP requirements still apply regardless of hosting model.

**7. Recurring Requirements Scheduling**
CIIOs sought clarification on how recurring requirements (e.g., annual risk assessments, biennial VA/PT) interact with the CCoP 2.0 transition. CSA clarified that deadlines are based on when the previous instance was performed, even under the old CCoP version.

**8. Waiver Process Complexity**
CIIOs unable to comply with specific clauses must submit waiver requests under Section 11(7) of the Cybersecurity Act. Waivers are time-bound (never permanent), require compensating controls, and take approximately 4 weeks to process. During review, CIIOs must continue monitoring associated risks.

**9. Talent and Resource Constraints**
Cybersecurity talent shortage in Singapore means many CIIOs struggle to staff the specialized roles required by CCoP 2.0 (threat hunters, OT security specialists, incident response personnel).

**10. Definition Ambiguity**
Industry feedback highlighted unclear terms like "raw logs" and "baseline of normal operations." CSA updated the glossary but noted CIIOs should contact CSA directly for interpretation questions.

---

### Risk Manager's Perspective

#### Organizational Structure in CII Organizations

In a typical CII organization, the cybersecurity governance structure follows this hierarchy:

**Board of Directors (BoD)**
- CCoP 2.0 requires at least one BoD member with cybersecurity knowledge and awareness
- Provides oversight of cybersecurity risks and guides senior management on systemic risk management
- Sets "tone at the top," defines risk appetite, oversees CCoP compliance
- Board cybersecurity training requirement expected to be codified in regulations (announced for 2026)

**CIIO (Critical Information Infrastructure Owner)**
- The legal entity designated under the Cybersecurity Act
- Bears ultimate responsibility and accountability for CII cybersecurity, even when outsourcing functions
- Must notify CSA within 2 hours of becoming aware of a cybersecurity incident
- Submits audit reports, remediation plans, and waiver requests to the Commissioner

**CISO / Head of Cybersecurity**
- Leads the cybersecurity function operationally
- Drives CCoP 2.0 compliance programme implementation
- Reports to senior management and board on cybersecurity posture
- Manages relationships with CSA sector officers

**Risk Manager**
- Conducts and maintains cybersecurity risk assessments per CSA's risk assessment methodology
- Maintains the CII risk register
- Performs gap analyses against CCoP 2.0 clauses and sector-specific requirements
- Develops risk treatment plans and tracks remediation of audit findings
- Evaluates vendor/supply chain cybersecurity risks
- Engages with OT teams and IT teams to validate findings and gather evidence
- Prepares materials for board reporting on cybersecurity risk posture
- Coordinates with CSA sector officers on waiver requests and compliance queries

#### Day-to-Day Responsibilities

A Risk Manager in a CII organization typically handles:

- **Risk Assessment Cycles**: Conducting annual (or more frequent) cybersecurity risk assessments using CSA-aligned methodologies, maintaining the risk register, and updating threat models
- **Audit Preparation**: Gathering evidence for biennial CCoP compliance audits (7 auditable clauses), coordinating with auditors, and tracking remediation of findings within the 30-day submission window
- **Waiver Management**: Identifying clauses that cannot be met, preparing waiver submissions with compensating controls, monitoring waiver expiry dates
- **Incident Response Coordination**: Ensuring the 2-hour notification process is exercised and ready, maintaining incident response plans and crisis communication plans
- **Vendor Risk Assessments**: Evaluating third-party vendors' cybersecurity posture, ensuring on-site access requirements are enforced
- **Board Reporting**: Translating technical cybersecurity risks into business impact language for board consumption
- **Policy Maintenance**: Keeping cybersecurity policies aligned with CCoP 2.0 requirements and any sector-specific regulations
- **Exercise Participation**: Planning and participating in cybersecurity exercises (both internal and national exercises like Exercise Cyber Star)

---

### CCoP Evolution: 1.0 to 2.0

#### Timeline

| Version | Date | Key Milestone |
|---------|------|--------------|
| CCoP 1.0 (First Edition) | 2018 | Issued alongside the Cybersecurity Act |
| CCoP 1.1 | ~2019-2020 | Minor revisions, 4 auditable clauses |
| CCoP 2.0 Draft | February 2022 | Issued for industry consultation |
| Response to Feedback | July 2022 | CSA published responses to industry concerns |
| CCoP 2.0 (Second Edition) | July 4, 2022 | Effective date, superseding all previous versions |
| Compliance Date | July 2023 | 12-month grace period for all clauses |
| CCoP 2.0 Revision One | Later revision | Minor updates |

#### What Changed

**Structural Changes**
- Auditable clauses increased from 4 to 7
- Total requirements increased from ~102 to ~220 (116% increase)
- OT security elevated from an Annex to a dedicated section with mandatory practices
- New domains added: Cyber Resilience, enhanced Detection requirements

**Key New Requirements in CCoP 2.0**
- **Threat Modelling**: Mandatory cyber threat modelling as part of risk assessment (supported by CSA's Guide to Cyber Threat Modelling)
- **Zero Trust Principles**: Security-by-Design and Zero Trust architecture principles introduced
- **Defence-in-Depth and Defence-by-Diversity**: Explicit design principle requirements
- **Red/Purple Teaming**: Adversarial attack simulation requirements introduced
- **Threat Hunting**: Proactive threat hunting capabilities required
- **Cyber Threat Intelligence Sharing**: Information sharing with CSA and sector peers
- **Supply Chain Risk Assessment**: Formal vendor cybersecurity risk management
- **Cloud Security**: Requirements addressing cloud-hosted CII workloads
- **Active Directory/Domain Controller Security**: Specific controls for AD environments
- **Board-Level Oversight**: Formal governance requirements for BoD cybersecurity knowledge

**Motivation for Update**
- Post-SingHealth breach (2018) COI recommendations were incorporated
- Ransomware evolved into a systemic national security threat
- Evolving TTPs required moving beyond foundational cyber hygiene
- Emerging technology risks: Cloud, 5G, AI/ML adoption by CIIOs
- Need for coordinated government-private sector defense capability

#### Transition Experience

The initial CCoP 2.0 draft proposed immediate effect for existing clauses, 30-day grace for COI-formalized clauses, and 9-month grace for new clauses. After industry feedback highlighting the operational challenge (particularly for OT environments), CSA revised to a uniform 12-month grace period for all clauses.

CSA acknowledged in the Response to Feedback that "technical and/or operational challenges to implement the revised heightened cybersecurity requirements" exist, but emphasized that "impending cybersecurity threats have raised the need for more effective measures to be built-up expediently."

For CIIOs unable to meet specific requirements, the waiver mechanism under Section 11(7) provides relief with compensating controls, though waivers are never permanent.

---

### IM8 and SII Classification

#### What is IM8?

IM8 (Instruction Manual 8) is the Singapore Government's internal ICT security policy framework, now formally known as the "Instruction Manual for ICT & SS (Smart Systems) Management." Key characteristics:

- **Scope**: Applies to all Singapore Government agencies and their ICT systems
- **Governance**: Managed by the Smart Nation and Digital Government Group (SNDGG) / GovTech
- **Coverage**: Spans Digital Service Standards (DSS), Third-Party Management (TPM), data security, and cybersecurity controls
- **Purpose**: Safeguards government Infocomm Technology and Smart Systems assets
- **Reform**: IM8 underwent reform as part of Singapore's Smart Nation transformation to support digital government initiatives while maintaining security

#### IM8 and CCoP 2.0 Overlap

A significant practical challenge identified in industry feedback was the overlap between IM8 and CCoP 2.0, particularly in:
- Access control management
- System hardening requirements
- Security configuration standards

Government sector CIIOs raised concerns about needing to conduct two separate audits. CSA's response (paragraph 2.9 of the Response to Feedback):
- Harmonization of codes will be carried out to deconflict requirements
- Audits will be mutually recognized under both the Cybersecurity Act and IM8 requirements

#### SII (Systems/Services of Information Infrastructure) -- Clarification

The term "SII" does not appear as a formal classification in Singapore's current regulatory framework. The Cybersecurity (Amendment) Act 2024 instead introduced three new entity classifications beyond CII:

1. **Entities of Special Cybersecurity Interest (ESCI)** -- Organizations that hold sensitive information or perform a function of national interest (e.g., autonomous universities). Obligations are lighter than CII requirements.

2. **Systems of Temporary Cybersecurity Concern (STCC)** -- Computer systems facing heightened cybersecurity risks due to temporary events (e.g., systems supporting elections or pandemic vaccine distribution). Time-limited designations under Part 3B, effective 31 October 2025.

3. **Foundational Digital Infrastructure (FDI)** -- Major providers of digital infrastructure services foundational to the economy, starting with cloud computing services and data centre facility services. Part 3D (not yet commenced).

#### Pathway to CII Designation

Under Section 7 of the Cybersecurity Act:
1. The Commissioner of Cybersecurity identifies computer systems that are necessary for the continuous delivery of essential services listed in the First Schedule
2. The system must be located wholly or partly in Singapore
3. Loss or compromise of the system would have a debilitating effect on national security, economy, public health, safety, or order
4. The Commissioner designates specific computer systems (not entire organizations or sectors) as CII
5. The CII list is classified for national security reasons
6. Designation can be challenged but the process is confidential

The 2024 amendments expanded the definition of CII to include "virtual CII" (systems that may not be physically located in Singapore but are essential to Singapore's critical services), and "provider-owned CII" (where the CII is owned by a third party, such as a cloud service provider, rather than the CIIO directly).

---

### CSA Audit and Enforcement

#### Audit Process

**Frequency**: At least once every 2 years (Commissioner may direct higher frequency)

**Audit Period**: Must be at least 12 months; no gaps between consecutive audit periods

**Auditor Appointment**:
1. CIIO identifies a proposed auditor
2. Submits Forms A1 and A2 to CSA for Commissioner approval
3. Commissioner approves or appoints the auditor
4. Auditor must be independent and competent in cybersecurity

**Audit Approach** (dual methodology):
- **Compliance-based**: Testing adequacy and effectiveness of controls against CCoP 2.0 clauses
- **Risk-based**: Identifying risks and threats to ensure appropriate controls are in place

**Auditable Scope**: 7 domains under CCoP 2.0 (up from 4 under CCoP 1.1). Preamble paragraphs are NOT in audit scope. Annex A capabilities are NOT in audit scope.

**Post-Audit Process**:
1. Auditor submits report to CIIO
2. CIIO submits audit report to Commissioner within 30 days of receiving it
3. CIIO submits audit finding remediation plan within 30 days
4. CIIO provides updates on each non-compliance remediation as they are completed
5. CIIO can proceed with remediation unless CSA deems plans unsatisfactory
6. If Commissioner finds audit unsatisfactory, may direct a re-audit under Section 15(3)

#### Common Non-Compliance Areas (Based on Industry Reports and Consulting Assessments)

While specific audit findings are not publicly disclosed, industry reports and consulting firm assessments consistently identify these common gaps:

- **Incomplete asset inventories** -- CIIOs struggle to maintain comprehensive, up-to-date inventories of all CII components, particularly in OT environments with legacy devices
- **Inadequate privileged access management** -- Weak controls over privileged/administrator accounts, insufficient monitoring of privileged sessions (SingHealth COI specifically cited this)
- **Insufficient logging and monitoring** -- Gaps in security event logging, particularly for OT systems; lack of centralized log management and correlation
- **Weak incident response readiness** -- Incident response plans not exercised regularly; unclear escalation procedures for the 2-hour CSA notification
- **Patch management gaps** -- Particularly in OT environments where patching risks operational disruption; no formal risk-based patch prioritization
- **Vendor access controls** -- Third-party remote access not consistently restricted to on-site only; insufficient supply chain risk assessments
- **Network segmentation deficiencies** -- Inadequate separation between IT and OT networks; flat networks without proper micro-segmentation
- **Training and awareness gaps** -- Staff lacking cybersecurity awareness (the SingHealth COI found IHiS staff "did not have adequate cybersecurity awareness, training, and resources")
- **Board-level cybersecurity governance** -- BoD members lacking cybersecurity knowledge; cybersecurity not regularly discussed at board level

#### Enforcement Mechanisms

**Criminal Penalties**:
- Non-compliance with Commissioner's notice/direction: Fine up to SGD 100,000 and/or imprisonment up to 2 years, plus SGD 5,000/day for continuing offenses
- Failure to submit audit report within 30 days: Fine up to SGD 25,000 and/or imprisonment up to 12 months, plus SGD 2,500/day for continuing offenses

**Civil Penalties (new under 2024 Amendment)**:
- CSA may seek civil penalties with Public Prosecutor's consent (Section 37A)
- Maximum: SGD 500,000 or 10% of annual turnover of the entity's Singapore business

**Enforcement Approach**:
- CSA has historically favored a collaborative, education-first approach rather than punitive enforcement
- The Commissioner can issue directions requiring specific remedial steps
- Sector Leads (e.g., MAS for banking, EMA for energy) serve as Assistant Cyber Commissioners, maintaining continuity of existing regulatory relationships
- No publicly reported enforcement actions or fines against CIIOs as of the research date

#### Incident Reporting Requirements

| Timeframe | Requirement |
|-----------|-------------|
| Within 2 hours | Notify Commissioner by calling the NCIRF-specified telephone number upon awareness of a cybersecurity incident |
| Within 14 days | Submit supplementary details: cause, impact on CII and interconnected systems, remedial measures taken |

The 2024 amendments expanded reportable incidents to include:
- Incidents suspected of being caused by Advanced Persistent Threats (APTs)
- Incidents causing disruption to essential services from non-interconnected systems under the CIIO's control

---

### Sector-Specific Compliance Scenarios

#### Energy Sector

**Scenario 1: SCADA Patch Management Dilemma**
A power generation company discovers a critical vulnerability in its SCADA HMI software. The vendor patch requires a system restart, but the plant cannot schedule downtime without affecting grid stability. The Risk Manager must decide: apply for a CCoP waiver with compensating controls (enhanced monitoring, network isolation), or coordinate with EMA for a planned maintenance window.

**Scenario 2: IT/OT Convergence Risk**
An energy utility is deploying smart grid sensors that require cloud connectivity for analytics. This creates new pathways between IT and OT networks. The Risk Manager needs to assess whether the new architecture maintains CCoP 2.0 network segmentation requirements and whether the cloud component falls within CII scope.

**Scenario 3: Vendor Access to OT Systems**
A turbine manufacturer requires remote diagnostic access to control systems for maintenance. CCoP 2.0 mandates on-site vendor access for CII. The Risk Manager must evaluate whether a monitored, time-limited VPN with jump-server qualifies, or whether the vendor must physically be on-site.

#### Water Sector

**Scenario 4: Legacy PLC Security**
PUB's water treatment plants run PLCs from the early 2000s that cannot support modern authentication or encryption. The Risk Manager needs to determine compensating controls (network segmentation, monitoring, physical access controls) and prepare a waiver request for the relevant CCoP clause.

**Scenario 5: 24/7 Operations and Security Testing**
CCoP 2.0 requires vulnerability assessment and penetration testing of OT CII every 24 months. Water treatment cannot be interrupted. The Risk Manager must plan non-disruptive testing approaches (passive scanning, test environment replication) that satisfy the auditor.

#### Healthcare Sector

**Scenario 6: Post-SingHealth Lessons**
Following the 2018 SingHealth breach (1.5M patient records), healthcare CIIOs face heightened scrutiny. A hospital's Risk Manager discovers that privileged admin accounts on the clinical management system share credentials across IT support staff -- a direct echo of the COI findings. Remediation requires implementing individual privileged accounts with session recording.

**Scenario 7: Medical Device IoT Security**
A hospital deploys network-connected infusion pumps and patient monitoring devices. These devices run embedded firmware that cannot be patched frequently. The Risk Manager must assess whether these devices fall within the CII boundary and what CCoP clauses apply to them.

**Scenario 8: Third-Party System Dependency**
A healthcare cluster outsources its EMR system management to a vendor (similar to the SingHealth-IHiS model). CCoP 2.0 states the CIIO remains accountable even when outsourcing. The Risk Manager must ensure the vendor's cybersecurity practices meet CCoP requirements and establish clear accountability boundaries.

#### Banking & Finance Sector

**Scenario 9: MAS-TRM and CCoP Dual Compliance**
A bank's core banking system is designated as CII. The Risk Manager must map CCoP 2.0 requirements against MAS-TRM guidelines to identify overlaps and gaps, creating a unified control framework that satisfies both regulators without duplicating audit effort.

**Scenario 10: Cloud Migration of CII**
A bank plans to migrate its designated CII payment gateway to a cloud provider's Singapore region. The Risk Manager must assess: Does CCoP still apply? How does the shared responsibility model work? What constitutes "provider-owned CII" under the 2024 amendments? What additional controls are needed?

**Scenario 11: Incident Reporting Coordination**
A ransomware attack hits the bank's CII system. The Risk Manager must coordinate: 2-hour notification to CSA, separate notification to MAS under its own incident reporting requirements, and notification to PDPC if personal data is compromised. Three different regulators, three different timelines and formats.

#### Transport Sector

**Scenario 12: Real-Time Systems Security**
SMRT's signalling system is designated as CII. Security controls cannot introduce latency that could affect train operations. The Risk Manager must identify security measures that protect the system without impacting real-time performance requirements.

**Scenario 13: Converged IT/OT in Rail**
The fare collection system (IT) connects to operational rail systems (OT) for passenger flow management. A breach of the fare system could theoretically pivot to signalling systems. The Risk Manager must ensure proper network segmentation between these systems per CCoP requirements.

#### Telecommunications Sector

**Scenario 14: 5G Infrastructure Security**
A telco rolling out 5G infrastructure faces new attack surfaces. CCoP 2.0 explicitly recognizes 5G as an emerging risk domain. The Risk Manager must assess the cybersecurity implications of network slicing, edge computing, and the expanded attack surface of 5G infrastructure components.

**Scenario 15: Scale of CII Asset Inventory**
A major telco has thousands of network devices, servers, and systems that could be part of the CII boundary. Maintaining a complete, accurate, and up-to-date asset inventory as required by CCoP 2.0 is a massive operational challenge.

---

### Realistic Risk Manager Questions

#### Governance & Compliance

1. "Our board has no members with cybersecurity expertise. What is the minimum requirement under CCoP 2.0 for board-level cybersecurity knowledge, and what happens if we can't recruit someone with that background?"
2. "We received our CCoP audit report with 12 non-compliance findings. What is the deadline and process for submitting our remediation plan to the Commissioner?"
3. "Our last audit was conducted under CCoP 1.0. When does our next audit need to use CCoP 2.0 as the reference framework?"
4. "Can we use the same audit to satisfy both CCoP 2.0 and IM8 requirements, or do we need separate audits?"
5. "We cannot comply with a specific CCoP clause due to our legacy OT architecture. What is the process for submitting a waiver request, and how long are waivers granted for?"

#### Risk Assessment & Threat Modelling

6. "CCoP 2.0 requires cyber threat modelling as part of our risk assessment. What methodology does CSA recommend, and is there a specific guide we should follow?"
7. "How frequently must we update our CII cybersecurity risk assessment? Is annual sufficient, or does the Commissioner expect more frequent updates?"
8. "Our risk register currently covers IT risks only. What additional categories must we include now that CCoP 2.0 has OT-specific requirements?"
9. "How should we determine our organization's cybersecurity risk appetite as required by CCoP 2.0? Is there a CSA-recommended approach?"

#### Access Control & Identity

10. "What are the CCoP 2.0 requirements for privileged access management on our CII systems? Do we need to implement Privileged Access Management (PAM) tooling?"
11. "Our OT systems use shared accounts because the legacy HMIs don't support individual authentication. How do we comply with CCoP access control requirements?"
12. "Does CCoP 2.0 require multi-factor authentication for all access to CII, or only for specific types of access?"

#### OT Security

13. "Our SCADA vendor says patching will void the warranty. How do we handle the conflict between CCoP patch management requirements and vendor support terms?"
14. "What network segmentation controls does CCoP 2.0 require between our IT and OT networks? Is a firewall sufficient, or do we need a DMZ or data diode?"
15. "We need to conduct penetration testing of our OT CII within 24 months. How do we test without risking disruption to essential services?"

#### Incident Response

16. "What exactly constitutes a 'cybersecurity incident' that triggers the 2-hour notification requirement to CSA? Does a suspected APT without confirmed data exfiltration count?"
17. "We detected anomalous network activity on our CII at 2 AM. Our CISO is unavailable. Who in the organization can authorize the 2-hour notification to CSA?"
18. "After the initial 2-hour notification, what supplementary information must we provide within 14 days, and in what format?"
19. "Our CII was affected by a ransomware attack that also compromised personal data. Do we need to notify CSA, MAS, and PDPC separately? What are the different timelines?"

#### Supply Chain & Vendor Management

20. "A critical vendor needs remote access to our CII for emergency maintenance. CCoP 2.0 says vendor access must be on-site. Can we get an emergency exception?"
21. "How deep does our supply chain risk assessment need to go? Are we responsible for our vendor's sub-contractors' cybersecurity posture?"
22. "We're evaluating a new cloud service provider for a CII workload. What CCoP 2.0 requirements apply to the cloud provider vs. what remains our responsibility?"

#### Training & Awareness

23. "CCoP 2.0 requires cybersecurity training based on roles in the CII organization. What specific training is required for our board members vs. our OT operators?"
24. "What certifications does CSA expect our cybersecurity risk assessment and audit personnel to hold?"
25. "How do we measure the effectiveness of our cybersecurity awareness programme as required by CCoP 2.0?"

#### Detection & Monitoring

26. "What constitutes adequate security event logging for CII under CCoP 2.0? What is the minimum log retention period?"
27. "CCoP 2.0 introduces threat hunting requirements. Do we need a dedicated threat hunting team, or can this be outsourced to a managed security service provider?"
28. "What cyber threat intelligence sharing obligations do we have under CCoP 2.0? What information are we required to share with CSA?"

#### Architecture & Design

29. "We are redesigning our CII network architecture. What does CCoP 2.0 require regarding Zero Trust principles and Defence-in-Depth?"
30. "Our CII uses Active Directory for authentication. What specific AD/Domain Controller security controls does CCoP 2.0 mandate?"

#### Regulatory Landscape

31. "With the 2024 Cybersecurity Act amendments, could any of our non-CII systems be classified as ESCI? What obligations would that create?"
32. "We are a cloud service provider hosting CII for multiple clients. Under the new 'provider-owned CII' concept, what are our obligations?"
33. "Our organization is participating in Exercise Cyber Star. What are our obligations vs. voluntary participation elements?"

---

### Key Takeaways

1. **The compliance burden has more than doubled**: CCoP 2.0's 220 clauses (up from 102) across 7 auditable domains represent a fundamental step-change in requirements. Risk Managers must treat this as a multi-year compliance programme, not a one-off exercise, and leverage the waiver mechanism strategically for genuinely infeasible requirements.

2. **OT security is the most critical gap across sectors**: The majority of CII sectors operate OT systems that were designed for reliability, not security. Legacy SCADA/ICS systems lack basic security controls, cannot be easily patched, and require specialized approaches to vulnerability assessment and penetration testing. This is where most compliance challenges concentrate.

3. **The regulatory landscape is actively expanding**: The 2024 Cybersecurity Act amendments introduced ESCI, STCC, and FDI classifications that extend CSA's regulatory reach well beyond traditional CII. CII organizations should anticipate their broader ecosystem (cloud providers, data centres, vendors) coming under direct CSA regulation, changing the dynamics of shared responsibility and vendor management.

---

### Remaining Unknowns

- [ ] Specific audit findings data from CSA-published reports (CSA does not publicly release audit findings at the CIIO level for national security reasons)
- [ ] Exact number of designated CII systems across all 11 sectors (classified information)
- [ ] Detailed IM8 requirements for comparison against CCoP 2.0 (IM8 is not publicly available in full)
- [ ] Enforcement action statistics -- whether CSA has issued any fines or directions under the Cybersecurity Act (no publicly reported enforcement actions found)
- [ ] Commencement dates for Part 3C (ESCI) and Part 3D (FDI) of the 2024 amendments (not yet announced)
- [ ] Board cybersecurity training regulation details expected in Q1 2026 (announced by CSA but details not yet published as of research date)
- [ ] Sector-specific addenda or guidelines beyond the OT addendum (some sectors may have additional sector-specific guidance not publicly documented)
- [ ] CCoP 2.0 Revision Two or future updates in response to the 2024 Act amendments

---

### Sources

- [CSA - Cybersecurity Act FAQ](https://www.csa.gov.sg/faqs/cybersecurity-act/) - accessed 2026-04-01
- [CSA - CII Sectors](https://www.csa.gov.sg/information-for/cii-sectors/) - accessed 2026-04-01
- [CSA - Codes of Practice](https://www.csa.gov.sg/legislation/codes-of-practice/) - accessed 2026-04-01
- [CSA - Cybersecurity Audit for CII FAQ](https://www.csa.gov.sg/faqs/cybersecurity-audit-cii/) - accessed 2026-04-01
- [CSA - Review of Cybersecurity Act and CCoP Update](https://www.csa.gov.sg/news-events/press-releases/review-of-the-cybersecurity-act-and-update-to-the-cybersecurity-code-of-practice-for-ciis/) - accessed 2026-04-01
- [CSA - Raise Cybersecurity Standards for CII Owners](https://www.csa.gov.sg/news-events/press-releases/csa-to-raise-cybersecurity-standards-for-critical-information-infrastructure-owners/) - accessed 2026-04-01
- [CSA - Exercise Cyber Star 2025](https://www.csa.gov.sg/news-events/press-releases/11-critical-sectors-come-together-to-tackle-complex-cyber-threat-scenarios-in-national-cyber-crisis-management-exercise/) - accessed 2026-04-01
- [CSA - OT Cybersecurity Masterplan 2024](https://www.csa.gov.sg/resources/publications/singapore-s-operational-technology-cybersecurity-masterplan-2024/) - accessed 2026-04-01
- [CSA - Provisions in Cybersecurity Amendment Act](https://www.csa.gov.sg/news-events/press-releases/provisions-in-the-cybersecurity--amendment--act-to-come-into-force-on-31-october-2025/) - accessed 2026-04-01
- [CSA - First Reading of Cybersecurity Amendment Bill](https://www.csa.gov.sg/news-events/press-releases/csa-first-reading-of-the-cybersecurity-(amendment)-bill/) - accessed 2026-04-01
- [CSA - Singapore Cyber Landscape 2024/2025 (PDF)](https://isomer-user-content.by.gov.sg/36/995dbbd7-a1de-4edb-b731-8fa36eb5546e/Singapore+Cyber+Landscape+2024_2025.pdf) - accessed 2026-04-01
- [CSA - OT Resilience Careers](https://www.csa.gov.sg/Explore/careers/working-in-csa/workingincsa-strengthening-the-cybersecurity-resilience-of-operational-technology-(ot)-systems) - accessed 2026-04-01
- [CSA - Response to Feedback (PDF)](https://isomer-user-content.by.gov.sg/36/0fd48037-f5eb-478a-bcbe-15f1a945d721/RESPONSE-TO-FEEDBACK.pdf) - accessed 2026-04-01 (also available locally: ccop-official/RESPONSE-TO-FEEDBACK.pdf)
- [CCoP 2.0 Second Edition Revision One (PDF)](https://isomer-user-content.by.gov.sg/36/2df750a7-a3bc-4d77-a492-d64f0ff4db5a/CCoP---Second-Edition_Revision-One.pdf) - accessed 2026-04-01
- [Cybersecurity (Amendment) Act 2024 - Singapore Statutes](https://sso.agc.gov.sg/Acts-Supp/19-2024/Published/20240704?DocDate=20240704) - accessed 2026-04-01
- [Hogan Lovells - Cybersecurity Amendment Act Provisions](https://www.hoganlovells.com/en/publications/provisions-in-singapores-cybersecurity-amendment-act-came-into-force-on-31-october-2025) - accessed 2026-04-01
- [CMS Law-Now - Key Amendments to Singapore Cybersecurity Regime](https://cms-lawnow.com/en/ealerts/2025/10/key-amendments-to-singapore-s-cybersecurity-regime-to-come-into-effect-on-31-october-2025) - accessed 2026-04-01
- [DLA Piper - Singapore Key Amendments to Cybersecurity Act](https://privacymatters.dlapiper.com/2025/12/singapore-key-amendments-to-the-cybersecurity-act-now-in-force/) - accessed 2026-04-01
- [Allen & Gledhill - Amendments to Cybersecurity Act](https://www.allenandgledhill.com/sg/perspectives/articles/31414/) - accessed 2026-04-01
- [Reed Smith - Singapore Passes Cybersecurity Amendment Bill](https://www.reedsmith.com/articles/singapore-passes-cybersecurity-amendment-bill/) - accessed 2026-04-01
- [Clifford Chance - Singapore Cybersecurity Act Extends Reach](https://www.cliffordchance.com/insights/resources/blogs/talking-tech/en/articles/2024/05/cybersecurity-update-singapore-cybersecurity-act-extends-its-reach.html) - accessed 2026-04-01
- [FTI Cybersecurity - 5 Key Takeaways from Amendment](https://fticybersecurity.com/2024-05/5-key-takeaways-from-the-singapore-cybersecurity-act-amendment/) - accessed 2026-04-01
- [Norton Rose Fulbright - Singapore Expands Cybersecurity Law](https://www.nortonrosefulbright.com/en/knowledge/publications/95489007/singapore-expands-scope-of-cybersecurity-law-to-address-evolving-risks) - accessed 2026-04-01
- [Thales - Singapore CCoP 2.0](https://cpl.thalesgroup.com/compliance/apac/singapore-ccop-2-critical-information-infrastructure) - accessed 2026-04-01
- [CyberSierra - Proactive CISO's Guide to CCoP 2.0](https://cybersierra.co/blog/ccop-2-regulations/) - accessed 2026-04-01
- [Industrial Cyber - CSA Publishes CCoP 2.0](https://industrialcyber.co/critical-infrastructure/cyber-security-agency-of-singapore-publishes-ccop-2-0-with-regulations-for-owners-of-critical-information-infrastructure/) - accessed 2026-04-01
- [ICLG - Cybersecurity Laws Singapore 2026](https://iclg.com/practice-areas/cybersecurity-laws-and-regulations/singapore) - accessed 2026-04-01
- [Baker McKenzie - Singapore Enforcement Priorities and Penalties](https://resourcehub.bakermckenzie.com/en/resources/global-data-and-cyber-handbook/asia-pacific/singapore/topics/regulators-enforcement-priorities-and-penalties) - accessed 2026-04-01
- [PwC - Navigating New CSA CII Requirements for Board of Directors](https://www.pwc.com/sg/en/services/risk/digital-solutions/navigating-new-csa-cii-requirements-for-board-of-directors.html) - accessed 2026-04-01
- [KPMG - CCoP 2.0 CII Programme Management (PDF)](https://assets.kpmg.com/content/dam/kpmg/sg/pdf/2023/10/ccop2.0-critical-information-infrastructure-programme-management.pdf) - accessed 2026-04-01
- [HashiCorp - Complying with CCoP 2.0](https://www.hashicorp.com/en/resources/complying-with-the-cybersecurity-code-of-practice-for-critical-information-infras) - accessed 2026-04-01
- [Picus Security - Practical Guide to CCoP 2.0 Compliance](https://www.picussecurity.com/resource/a-practical-guide-to-ccop-2.0-compliance-using-picus) - accessed 2026-04-01
- [InsiderSecurity - CCoP 2.0 Compliance](https://insidersecurity.co/cybersecurity-code-of-practice-ccop-2-0-complying-with-insidersecurity/) - accessed 2026-04-01
- [Sapience Consulting - Demystifying CCoP](https://www.sapience-consulting.com/know-your-ccop/) - accessed 2026-04-01
- [GICG - CCoP Compliance Audit](https://gicgrp.com/sg/cyber-security-code-of-practice-ccop-compliance-audit/) - accessed 2026-04-01
- [TUV SUD - CCoP Compliance Audit](https://www.tuvsud.com/en-sg/services/cyber-security/cyber-security-code-of-practice-ccop-compliance-audit) - accessed 2026-04-01
- [Right-Hand - Singapore CCoP 2.0 Security Awareness](https://right-hand.ai/blog/singapore-ccop-20-security-awareness/) - accessed 2026-04-01
- [IriusRisk - Singapore CSA Mandates Threat Modeling](https://www.iriusrisk.com/resources-blog/singapores-cybersecurity-agency-mandates) - accessed 2026-04-01
- [MAS - Cyber Security](https://www.mas.gov.sg/regulation/cyber-security) - accessed 2026-04-01
- [RSIS - SingHealth Cyber Attack Learning from COI Findings](https://rsis.edu.sg/rsis-publication/cens/singhealth-cyber-attack-learning-from-coi-findings/) - accessed 2026-04-01
- [Singapore Government - SingHealth COI Public Report (PDF)](https://file.go.gov.sg/singhealthcoi.pdf) - accessed 2026-04-01
- [MOH - Ministerial Statement on SingHealth COI](https://www.moh.gov.sg/newsroom/ministerial-statement-on-the-committee-of-inquiry-into-the-cyber-attack-on-singhealth-s-it-system) - accessed 2026-04-01
- [GovTech - IM8 Agile Playbook](https://docs.developer.tech.gov.sg/docs/agile-playbook/agile-instruction-manual-8) - accessed 2026-04-01
- [MINDEF - CIDeX 2024](https://www.mindef.gov.sg/news-and-events/latest-releases/15nov24_nr/) - accessed 2026-04-01
- [MINDEF - CIDeX 2025](https://www.mindef.gov.sg/news-and-events/latest-releases/12nov25-nr2/) - accessed 2026-04-01
- [AmCham Singapore - Response to CCoP Industry Consultation (PDF)](https://amcham.com.sg/wp-content/uploads/2022/05/AmCham-Feedback-on-Proposed-Updates-on-Cybersecurity-Code-of-Practice.pdf) - accessed 2026-04-01
- Local: `ccop-official/RESPONSE-TO-FEEDBACK.pdf` - CSA Response to Feedback, July 2022
- Local: `ccop-official/CCoP---Second-Edition_Revision-One.pdf` - CCoP 2.0 full document
