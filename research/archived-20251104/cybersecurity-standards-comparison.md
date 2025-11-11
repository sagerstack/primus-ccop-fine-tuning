# Cybersecurity Standards Comparison - Primary Objectives

## 1. SINGAPORE MANDATORY/ENFORCED STANDARDS

| Standard | Primary Objective | Key Differentiator |
|----------|------------------|-------------------|
| **CCoP 2.0** | Protect Critical Information Infrastructure (CII) from sophisticated attacks | Mandatory for CII sectors with OT-specific requirements |
| **Cybersecurity Act** | Legal framework for national cybersecurity oversight and incident response | Provides enforcement powers and penalties |
| **PDPA** | Protect personal data privacy and regulate data collection/use/disclosure | Focus on individual privacy rights, not security |
| **MAS TRM Guidelines** | Ensure technology risk management in financial institutions | Financial sector-specific with board accountability |
| **SS 712:2025 (Cyber Essentials)** | Establish basic cybersecurity hygiene for SMEs | Entry-level certification for small businesses |
| **SS 712:2025 (Cyber Trust/CTM)** | Risk-based cybersecurity for mature organizations including AI/Cloud/OT | Advanced cert with emerging tech pillars |
| **MTCS SS 584** | Multi-tier cloud security for cloud service providers | Singapore's cloud-specific standard with 3 tiers |
| **DPTM SS 714:2025** | Demonstrate accountable data protection practices beyond PDPA | Enterprise-wide privacy management certification |
| **IMDA Telecom Codes** | Secure telecommunications infrastructure and services | Telco-specific network security |
| **IM8 Reform** | Govern ICT adoption in government with risk-based controls | Government-only ICT policy framework |

## 2. VULNERABILITY & THREAT FRAMEWORKS

| Standard | Primary Objective | Key Differentiator |
|----------|------------------|-------------------|
| **OWASP Top 10** | Identify the 10 most critical web application security risks | Web app vulnerabilities ranked by prevalence |
| **OWASP ASVS** | Provide comprehensive security verification requirements for applications | 286 detailed testable requirements in 3 levels |
| **OWASP API Top 10** | Address API-specific security risks distinct from web apps | API-focused (different from web vulnerabilities) |
| **CWE** | Catalog software weaknesses that lead to vulnerabilities | Weakness types (root causes) not vulnerabilities |
| **CVE** | Uniquely identify and track specific discovered vulnerabilities | Individual vulnerability naming/tracking system |
| **MITRE ATT&CK** | Describe adversary tactics, techniques, and procedures (behaviors) | How attackers operate, not what to defend |
| **MITRE D3FEND** | Map defensive countermeasures to offensive techniques | Defensive techniques to counter ATT&CK |

## 3. COMPREHENSIVE SECURITY FRAMEWORKS

| Standard | Primary Objective | Key Differentiator |
|----------|------------------|-------------------|
| **ISO/IEC 27001** | Establish an Information Security Management System (ISMS) | Management system with 93 controls, certifiable |
| **ISO/IEC 27002** | Provide detailed implementation guidance for security controls | How-to guide for 27001 controls (not certifiable) |
| **ISO/IEC 27005** | Guide information security risk assessment and treatment | Risk management methodology |
| **ISO/IEC 27017** | Add cloud-specific security controls to ISO 27001 | Cloud extension (37 additional controls) |
| **ISO/IEC 27018** | Protect Personally Identifiable Information in public clouds | Cloud privacy controls for PII processors |
| **ISO/IEC 27701** | Extend ISMS to include privacy information management (PIMS) | Privacy extension to 27001/27002 |
| **ISO/IEC 27032** | Provide cybersecurity guidelines beyond information security | Internet/cyberspace security (broader than infosec) |
| **ISO/IEC 27035** | Manage information security incidents effectively | Incident response planning and operations |
| **NIST CSF 2.0** | Provide flexible framework to manage cybersecurity risks | 6 functions (Govern, Identify, Protect, Detect, Respond, Recover) |
| **NIST SP 800-53** | Catalog security and privacy controls for federal systems | 1000+ detailed controls for US government |
| **NIST SP 800-171** | Protect Controlled Unclassified Information in non-federal systems | CUI protection for contractors |

## 4. INDUSTRY/SECTOR-SPECIFIC STANDARDS

| Standard | Primary Objective | Key Differentiator |
|----------|------------------|-------------------|
| **PCI DSS** | Secure payment card data throughout transaction lifecycle | Payment card industry mandatory requirements |
| **SWIFT CSP** | Secure SWIFT financial messaging infrastructure | SWIFT network-specific controls |
| **SOC 2 Type II** | Demonstrate service organization controls over time | Third-party assurance for service providers |
| **HIPAA** | Protect healthcare information privacy and security | US healthcare-specific regulations |
| **IEC 62443** | Secure industrial automation and control systems (OT/ICS) | Industrial/OT specific with 4 security levels |
| **NERC CIP** | Protect electric grid critical infrastructure | Power sector reliability standards |
| **Basel III** | Manage operational risk in banking including cyber | Banking operational risk framework |
| **GxP** | Ensure quality and integrity in pharma/life sciences | Good practices for regulated life sciences |

## 5. OPERATIONAL & GOVERNANCE FRAMEWORKS

| Standard | Primary Objective | Key Differentiator |
|----------|------------------|-------------------|
| **COBIT 2019** | Govern and manage enterprise IT including security | IT governance (broader than security) |
| **ITIL v4** | Manage IT services throughout their lifecycle | Service management, not security-focused |
| **CIS Controls v8** | Provide prioritized set of actions to defend against attacks | 18 actionable controls with implementation groups |
| **CSA CCM** | Provide cloud security controls matrix for all cloud models | Cloud-specific control framework (197 controls) |

## 6. SINGAPORE GOVERNMENT FRAMEWORKS

| Standard | Primary Objective | Key Differentiator |
|----------|------------------|-------------------|
| **GovZTA** | Implement Zero Trust Architecture in government systems | Singapore's Zero Trust adoption framework |
| **SHIP-HATS** | Integrate DevSecOps into government development pipelines | Government CI/CD platform with security built-in |
| **GCC/GCC+** | Provide secure government cloud with compliance built-in | Pre-configured cloud with government controls |
| **AIAS** | Define application infrastructure architecture standards | Government app architecture requirements |

## 7. EMERGING TECHNOLOGY STANDARDS

| Standard | Primary Objective | Key Differentiator |
|----------|------------------|-------------------|
| **NIST AI RMF** | Manage risks in AI system development and deployment | AI-specific risk management |
| **Singapore Model AI Governance** | Ensure ethical and explainable AI deployment | Singapore's AI ethics framework |
| **NIST Post-Quantum Crypto** | Prepare cryptography for quantum computing threats | Quantum-resistant algorithms |
| **SBOM Requirements** | Track software supply chain components for security | Software component transparency |

## KEY INSIGHTS:

### Why So Many Standards?

1. **Different Scopes:**
   - **Organizational**: ISO 27001 (management system)
   - **Technical**: OWASP (specific vulnerabilities)
   - **Behavioral**: MITRE ATT&CK (threat actors)

2. **Different Industries:**
   - **Finance**: MAS TRM, PCI DSS, SWIFT
   - **Healthcare**: HIPAA, ISO 27799
   - **Industrial**: IEC 62443, NERC CIP
   - **Government**: IM8, GovZTA

3. **Different Purposes:**
   - **Compliance**: PDPA, PCI DSS (mandatory)
   - **Certification**: ISO 27001, SOC 2 (voluntary)
   - **Guidance**: NIST CSF, CIS Controls (best practices)
   - **Intelligence**: MITRE ATT&CK, CVE (threat info)

4. **Different Maturity Levels:**
   - **Basic**: Cyber Essentials (SMEs)
   - **Intermediate**: ISO 27001
   - **Advanced**: CCoP 2.0, IEC 62443 Level 3-4

5. **Different Technology Domains:**
   - **Traditional IT**: ISO 27001
   - **Cloud**: MTCS, CSA CCM, ISO 27017
   - **OT/ICS**: IEC 62443
   - **AI**: NIST AI RMF, CTM AI pillar
   - **APIs**: OWASP API Top 10

## FOR YOUR SCANNING MODEL:

### Core Security (Must Have):
- **CWE/CVE** - Identify vulnerabilities
- **OWASP** - Web/API security patterns
- **MITRE ATT&CK** - Map to real threats

### Compliance Mapping (Must Have):
- **CCoP 2.0** - Singapore CII requirements
- **PDPA** - Privacy requirements
- **MAS TRM** - Financial requirements
- **ISO 27001/27002** - General security controls

### Context-Specific (Add Based on Client):
- **PCI DSS** - If handling payments
- **IEC 62443** - If OT/ICS systems
- **SWIFT CSP** - If using SWIFT
- **IM8** - If government agency
- **CTM** - For AI/Cloud/OT security

This differentiation shows why a hybrid RAG + fine-tuning approach makes sense: standards change frequently (RAG for updates) but vulnerability patterns remain consistent (fine-tuning for detection).