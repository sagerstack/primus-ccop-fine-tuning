# CCoP 2.0 Clause Breakdown by Infrastructure Type

## Overview Statistics

| Infrastructure Type | Applicable Clauses | Percentage | Source Code Detectable |
|---------------------|-------------------|------------|------------------------|
| **Cross-Cutting (Both IT & OT)** | ~120-130 clauses | ~55-60% | ~35-40 clauses (30%) |
| **IT-Specific** | ~50-60 clauses | ~23-27% | ~40-45 clauses (80%) |
| **OT/ICS-Specific** | ~35-40 clauses | ~16-18% | ~15-20 clauses (45%) |
| **TOTAL** | ~220 clauses | 100% | **~90-100 clauses (40-45%)** |

---

## Section-by-Section Breakdown

### Section 1: Audit (4 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 1.1 - Audit Programme | | | ✅ | ❌ | Organizational process, not code-detectable |
| 1.2 - Audit Scope | | | ✅ | ❌ | Organizational process, not code-detectable |
| 1.3 - Audit Frequency | | | ✅ | ❌ | Organizational process, not code-detectable |
| 1.4 - Audit Findings | | | ✅ | ❌ | Organizational process, not code-detectable |

**Applicability:** 100% Cross-Cutting (4/4)  
**Source Code Detectable:** 0/4 (0%)

---

### Section 2: Governance (~15-20 clauses)

| Clause Category | IT | OT | Both | Source Code | Notes |
|-----------------|----|----|------|-------------|-------|
| 2.1 - Cybersecurity Governance Framework | | | ✅ | ❌ | Board/management oversight |
| 2.2 - Roles & Responsibilities | | | ✅ | ❌ | Organizational structure |
| 2.3 - Board Oversight | | | ✅ | ❌ | Governance process |
| 2.4 - Policies & Standards | | | ✅ | ❌ | Policy documentation |
| 2.5 - Resources & Budget | | | ✅ | ❌ | Budget allocation |
| 2.6 - Performance Measurement | | | ✅ | ❌ | KPI tracking |
| 2.7 - Compliance Management | | | ✅ | ❌ | Compliance tracking |

**Applicability:** 100% Cross-Cutting (15-20/15-20)  
**Source Code Detectable:** 0/15-20 (0%)

---

### Section 3: Risk Management & Resilience (~25-30 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 3.1 - Cybersecurity Risk Assessment | | | ✅ | ❌ | Risk assessment process |
| 3.2 - Risk Treatment | | | ✅ | ❌ | Risk management documentation |
| 3.3 - Business Continuity | | | ✅ | ⚠️ | Partial: DR configs in IaC, backups |
| 3.4.1 - Security by Design Framework | | | ✅ | ⚠️ | Partial: Secure SDLC implementation |
| 3.4.2 - Threat Modeling | | | ✅ | ❌ | Design documentation |
| 3.5 - Cyber Resilience | | | ✅ | ⚠️ | Partial: Redundancy in IaC |
| 3.6.1 - Change Management Process | | | ✅ | ❌ | Process documentation |
| 3.6.2 - Change Approval | | | ✅ | ❌ | Approval workflow |
| 3.6.3 - Change Testing | | | ✅ | ⚠️ | Partial: Test configs in IaC |
| 3.6.4 - Rollback Procedures | | | ✅ | ⚠️ | Partial: IaC version control |
| 3.7.1 - Cloud Risk Assessment | ✅ | | | ❌ | Risk assessment documentation |
| 3.7.2 - Cloud Commissioner Notification | ✅ | | | ❌ | Regulatory notification process |
| 3.7.3 - Cloud Service Provider Selection | ✅ | | | ⚠️ | Partial: Provider configs in IaC |
| 3.7.4 - Cloud Security Controls | ✅ | | | ✅ | **IaC scanning: Cloud configs, IAM policies** |

**Applicability:**  
- Cross-Cutting: ~20-22 clauses  
- IT-Specific (Cloud): ~4 clauses  

**Source Code Detectable:** ~4-6/25-30 (16-20%)

---

### Section 4: Asset Management (~8-10 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 4.1.1 - Asset Inventory | | | ✅ | ⚠️ | Partial: IaC inventory, SBOM generation |
| 4.1.2 - Asset Classification | | | ✅ | ❌ | Manual classification process |
| 4.2 - Asset Owner Accountability | | | ✅ | ❌ | Organizational assignment |
| 4.3 - Acceptable Use Policy | | | ✅ | ❌ | Policy documentation |
| 4.4 - Media Handling | | | ✅ | ❌ | Physical/operational controls |
| 4.5 - Asset Disposal | | | ✅ | ❌ | Decommissioning process |

**Applicability:** 100% Cross-Cutting (8-10/8-10)  
**Source Code Detectable:** ~1-2/8-10 (10-20%)

---

### Section 5: Protect (~80-90 clauses) - LARGEST SECTION

#### 5.1 - Access Control (~6 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.1.1 - Access Control Policy | | | ✅ | ❌ | Policy documentation |
| 5.1.2 - Authentication Mechanisms | | | ✅ | ✅ | **SAST: Auth implementation, IAM in IaC** |
| 5.1.3 - Authorization Controls | | | ✅ | ✅ | **SAST: RBAC implementation, IAM policies** |
| 5.1.4 - Least Privilege | | | ✅ | ✅ | **SAST: Permission checks, IaC IAM roles** |
| 5.1.5 - Segregation of Duties | | | ✅ | ⚠️ | Partial: Code-level SoD, IAM policies |
| 5.1.6 - Access Reviews | | | ✅ | ❌ | Periodic review process |

**Source Code Detectable:** ~3-4/6 (50-67%)

#### 5.2 - Account Management (~4 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.2.1 - User Account Provisioning | ✅ | | | ⚠️ | Partial: IaC user provisioning scripts |
| 5.2.2 - Account Deprovisioning | ✅ | | | ❌ | Operational process |
| 5.2.3 - Account Monitoring | ✅ | | | ❌ | Runtime monitoring |
| 5.2.4 - Dormant Account Management | ✅ | | | ❌ | Operational process |

**Source Code Detectable:** ~0-1/4 (0-25%)

#### 5.3 - Privileged Access Management (~3 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.3.1 - Privileged Account Controls | ✅ | | | ⚠️ | Partial: Admin role configs in IaC |
| 5.3.2 - Privileged Session Management | ✅ | | | ❌ | PAM solution configuration |
| 5.3.3 - Privileged Access Monitoring | ✅ | | | ❌ | Runtime monitoring |

**Source Code Detectable:** ~0-1/3 (0-33%)

#### 5.4 - Identity & Access Management (~4 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.4.1 - Identity Lifecycle Management | ✅ | | | ⚠️ | Partial: IAM configs in IaC |
| 5.4.2 - Federation & SSO | ✅ | | | ✅ | **IaC: IdP configurations, SAML/OAuth** |
| 5.4.3 - Multi-Factor Authentication | ✅ | | | ✅ | **SAST: MFA enforcement, IaC MFA policies** |
| 5.4.4 - Password Management | ✅ | | | ✅ | **SAST: Password policies, hardcoded passwords** |

**Source Code Detectable:** ~3/4 (75%)

#### 5.5 - Network Segmentation (~3 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.5.1 - Network Architecture Design | | | ✅ | ✅ | **IaC: VPC design, subnet configs** |
| 5.5.2 - Segmentation Implementation | | | ✅ | ✅ | **IaC: Security groups, NACLs, NSGs** |
| 5.5.3 - Inter-Segment Controls | | | ✅ | ✅ | **IaC: Firewall rules, routing tables** |

**Source Code Detectable:** 3/3 (100%)

#### 5.6 - Network Security (~3 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.6.1 - Network Access Controls | | | ✅ | ✅ | **IaC: Firewall rules, WAF configs** |
| 5.6.2 - External Network Connections | | | ✅ | ✅ | **IaC: Internet gateway configs, NAT** |
| 5.6.3 - Internet Connectivity Controls | | | ✅ | ✅ | **IaC: Public/private subnet design** |

**Source Code Detectable:** 3/3 (100%)

#### 5.7 - Remote Access (~4 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.7.1 - Remote Access Policy | | | ✅ | ❌ | Policy documentation |
| 5.7.2 - VPN Implementation | | | ✅ | ✅ | **IaC: VPN gateway configs** |
| 5.7.3 - Remote Access Authentication | | | ✅ | ✅ | **IaC: VPN authentication configs** |
| 5.7.4 - Remote Access Monitoring | | | ✅ | ⚠️ | Partial: Logging configs in IaC |

**Source Code Detectable:** ~2-3/4 (50-75%)

#### 5.8 - Wireless Security (~3 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.8.1 - Wireless Network Segmentation | ✅ | | | ✅ | **IaC: WiFi VLAN configs** |
| 5.8.2 - Wireless Encryption | ✅ | | | ✅ | **IaC: WPA3/802.1X configs** |
| 5.8.3 - Wireless Access Controls | ✅ | | | ⚠️ | Partial: Network configs |

**Source Code Detectable:** ~2-3/3 (67-100%)

#### 5.9 - System Hardening (~4 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.9.1 - Operating System Hardening | ✅ | | | ✅ | **IaC: OS configs, CIS benchmarks** |
| 5.9.2 - Application Hardening | ✅ | | | ✅ | **IaC: App server configs** |
| 5.9.3 - Network Device Hardening | ✅ | | | ✅ | **IaC: Router/switch configs** |
| 5.9.4 - Server Hardening | ✅ | | | ✅ | **IaC: Server baseline configs** |

**Source Code Detectable:** 4/4 (100%)

#### 5.10 - Removable Media (~2 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.10.1 - Removable Media Controls | | | ✅ | ⚠️ | Partial: USB blocking in OS configs |
| 5.10.2 - Media Encryption | | | ✅ | ❌ | Operational/policy control |

**Source Code Detectable:** ~0-1/2 (0-50%)

#### 5.11 - Configuration Management (~3 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.11.1 - Configuration Baselines | | | ✅ | ✅ | **IaC: Infrastructure baselines** |
| 5.11.2 - Configuration Change Control | | | ✅ | ✅ | **IaC: Version control, change tracking** |
| 5.11.3 - Configuration Auditing | | | ✅ | ⚠️ | Partial: IaC drift detection |

**Source Code Detectable:** ~2-3/3 (67-100%)

#### 5.12 - Application Security (~7 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.12.1 - Application Whitelisting | ✅ | | | ⚠️ | Partial: Container image whitelisting |
| 5.12.2 - Secure SDLC | ✅ | | | ✅ | **SAST: Security testing in pipelines** |
| 5.12.3 - OWASP Top 10 Compliance | ✅ | | | ✅ | **SAST: Injection, XSS, auth flaws** |
| 5.12.4 - Input Validation | ✅ | | | ✅ | **SAST: Input sanitization** |
| 5.12.5 - Output Encoding | ✅ | | | ✅ | **SAST: XSS prevention** |
| 5.12.6 - Web Application Firewall | ✅ | | | ✅ | **IaC: WAF rules, CloudFront configs** |
| 5.12.7 - Application Integrity | ✅ | | | ✅ | **SAST: Code signing, integrity checks** |

**Source Code Detectable:** 6-7/7 (86-100%)**

#### 5.13 - Database Security (~5 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.13.1 - Database Access Controls | ✅ | | | ✅ | **SAST: SQL query permissions** |
| 5.13.2 - Query Access Control | ✅ | | | ✅ | **SAST: SQL injection prevention** |
| 5.13.3 - Segregation of Duties (DB) | ✅ | | | ⚠️ | Partial: DB role configs |
| 5.13.4 - Data-at-Rest Encryption | ✅ | | | ✅ | **IaC: DB encryption configs** |
| 5.13.5 - Database Activity Monitoring | ✅ | | | ⚠️ | Partial: Logging configs |

**Source Code Detectable:** ~4/5 (80%)

#### 5.14 - Cryptography (~4 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.14.1 - Cryptographic Standards | | | ✅ | ✅ | **SAST: Weak crypto detection (MD5, SHA1)** |
| 5.14.2 - Key Management | | | ✅ | ✅ | **SAST: Hardcoded keys, IaC KMS configs** |
| 5.14.3 - Data in Transit Encryption | | | ✅ | ✅ | **SAST: TLS/SSL implementation** |
| 5.14.4 - Data at Rest Encryption | | | ✅ | ✅ | **IaC: Encryption configs** |

**Source Code Detectable:** 4/4 (100%)

#### 5.15 - Data Protection (~5 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.15.1 - Data Classification | | | ✅ | ⚠️ | Partial: Data tagging in code |
| 5.15.2 - Data Handling Procedures | | | ✅ | ⚠️ | Partial: DLP configs |
| 5.15.3 - Data Loss Prevention | | | ✅ | ❌ | DLP solution configuration |
| 5.15.4 - Data Retention | | | ✅ | ⚠️ | Partial: Retention policies in IaC |
| 5.15.5 - Data Disposal | | | ✅ | ❌ | Operational process |

**Source Code Detectable:** ~1-2/5 (20-40%)

#### 5.16 - Backup & Recovery (~4 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.16.1 - Backup Strategy | | | ✅ | ⚠️ | Partial: Backup configs in IaC |
| 5.16.2 - Backup Testing | | | ✅ | ❌ | Operational testing process |
| 5.16.3 - Backup Security | | | ✅ | ✅ | **IaC: Backup encryption, access controls** |
| 5.16.4 - Recovery Procedures | | | ✅ | ⚠️ | Partial: DR configs in IaC |

**Source Code Detectable:** ~1-2/4 (25-50%)

#### 5.17 - Logging & Monitoring (~4 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.17.1 - Security Event Logging | | | ✅ | ✅ | **SAST: Logging implementation** |
| 5.17.2 - Log Protection | | | ✅ | ✅ | **IaC: Log storage configs, encryption** |
| 5.17.3 - Log Retention | | | ✅ | ✅ | **IaC: Log retention policies** |
| 5.17.4 - Log Monitoring | | | ✅ | ⚠️ | Partial: SIEM configs in IaC |

**Source Code Detectable:** ~3-4/4 (75-100%)

#### 5.18 - Vulnerability Management (~5 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.18.1 - Vulnerability Assessment | ✅ | | | ✅ | **SCA: Dependency scanning** |
| 5.18.2 - Patch Management | ✅ | | | ✅ | **SCA: Outdated library detection** |
| 5.18.3 - Vulnerability Prioritization | ✅ | | | ⚠️ | Partial: CVSS scoring in SCA |
| 5.18.4 - Remediation Tracking | ✅ | | | ❌ | Project management process |
| 5.18.5 - Emergency Patching | ✅ | | | ❌ | Operational process |

**Source Code Detectable:** ~2-3/5 (40-60%)

#### 5.19 - Malware Protection (~3 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.19.1 - Antivirus Deployment | ✅ | | | ⚠️ | Partial: AV configs in IaC |
| 5.19.2 - Malware Scanning | ✅ | | | ❌ | Runtime scanning |
| 5.19.3 - Malware Response | ✅ | | | ❌ | Incident response process |

**Source Code Detectable:** ~0-1/3 (0-33%)

#### 5.20 - Email Security (~3 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.20.1 - Email Gateway Protection | ✅ | | | ⚠️ | Partial: Email gateway configs |
| 5.20.2 - Email Encryption | ✅ | | | ⚠️ | Partial: Email security policies |
| 5.20.3 - Phishing Protection | ✅ | | | ❌ | User awareness + filtering |

**Source Code Detectable:** ~0-1/3 (0-33%)

#### 5.21 - Web Security (~3 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 5.21.1 - Web Filtering | ✅ | | | ⚠️ | Partial: Proxy configs |
| 5.21.2 - Web Content Inspection | ✅ | | | ❌ | Runtime inspection |
| 5.21.3 - Safe Browsing Policies | ✅ | | | ❌ | Policy enforcement |

**Source Code Detectable:** ~0-1/3 (0-33%)

---

**Section 5 Summary:**

| Category | Total Clauses | Source Code Detectable | Percentage |
|----------|---------------|------------------------|------------|
| **IT-Specific Controls** | ~45-50 | ~35-40 | **75-80%** |
| **Cross-Cutting Controls** | ~30-35 | ~10-15 | **30-45%** |
| **Section 5 Total** | ~80-90 | ~45-55 | **55-65%** |

**Highest Code-Scannable Subsections:**
- 5.5 Network Segmentation (100%)
- 5.6 Network Security (100%)
- 5.9 System Hardening (100%)
- 5.12 Application Security (86-100%)
- 5.13 Database Security (80%)
- 5.14 Cryptography (100%)

---

### Section 6: Detect, Respond & Recover (~25-30 clauses)

| Subsection | Clauses | IT | OT | Both | Source Code | Notes |
|------------|---------|----|----|------|-------------|-------|
| **6.1 - Security Monitoring** | ~5 | | | ✅ | ⚠️ | Partial: SIEM/logging configs in IaC |
| **6.2 - Anomaly Detection** | ~3 | | | ✅ | ❌ | Runtime behavior analysis |
| **6.3 - Incident Detection** | ~3 | | | ✅ | ⚠️ | Partial: Alert configs in IaC |
| **6.4 - Incident Classification** | ~2 | | | ✅ | ❌ | Operational process |
| **6.5 - Incident Response** | ~4 | | | ✅ | ❌ | IR playbook execution |
| **6.6 - Incident Reporting** | ~3 | | | ✅ | ❌ | Regulatory reporting process |
| **6.7 - Forensics** | ~2 | ✅ | | | ❌ | Forensic investigation |
| **6.8 - Recovery** | ~4 | | | ✅ | ⚠️ | Partial: DR automation configs |
| **6.9 - Lessons Learned** | ~2 | | | ✅ | ❌ | Post-incident review |

**Applicability:**  
- Cross-Cutting: ~23-25 clauses  
- IT-Specific: ~2-3 clauses (forensics)  

**Source Code Detectable:** ~3-5/25-30 (10-20%)

---

### Section 7: Cybersecurity Awareness (~8-10 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 7.1 - Awareness Programme | | | ✅ | ❌ | Training program delivery |
| 7.2 - Role-Based Training | | | ✅ | ❌ | Training content development |
| 7.3 - Phishing Awareness | ✅ | | | ❌ | User training + simulations |
| 7.4 - Social Engineering | | | ✅ | ❌ | User training |
| 7.5 - Security Culture | | | ✅ | ❌ | Organizational culture |
| 7.6 - Training Effectiveness | | | ✅ | ❌ | Training metrics |

**Applicability:**  
- Cross-Cutting: ~7-8 clauses  
- IT-Specific: ~1-2 clauses (phishing)  

**Source Code Detectable:** 0/8-10 (0%)

---

### Section 8: Supply Chain Cybersecurity (~10-12 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 8.1 - Supply Chain Risk Assessment | | | ✅ | ❌ | Vendor assessment process |
| 8.2 - Supplier Security Requirements | | | ✅ | ❌ | Contract requirements |
| 8.3.1 - Software Integrity | | | ✅ | ✅ | **SAST: Code signing, checksums** |
| 8.3.2 - Hardware Integrity | | | ✅ | ❌ | Physical verification |
| 8.4 - Supply Chain Monitoring | | | ✅ | ⚠️ | Partial: SBOM generation |
| 8.5 - Counterfeit Prevention | | ✅ | | ❌ | Physical verification (OT focus) |
| 8.6 - End-of-Life Management | | | ✅ | ❌ | Asset lifecycle management |

**Applicability:**  
- Cross-Cutting: ~9-10 clauses  
- OT-Emphasis: ~1-2 clauses  

**Source Code Detectable:** ~1-2/10-12 (8-20%)

---

### Section 9: Third Party Cybersecurity (~12-15 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 9.1 - Third Party Risk Assessment | | | ✅ | ❌ | Vendor evaluation process |
| 9.2 - Contractual Requirements | | | ✅ | ❌ | Contract negotiations |
| 9.3 - Vendor Security Evaluation | | | ✅ | ❌ | Vendor audits |
| 9.4 - Access Control for Third Parties | | | ✅ | ⚠️ | Partial: IAM policies for vendors |
| 9.5 - Third Party Monitoring | | | ✅ | ❌ | Ongoing vendor oversight |
| 9.6 - Incident Response Coordination | | | ✅ | ❌ | Incident communication |
| 9.7 - Service Level Agreements | | | ✅ | ❌ | SLA documentation |

**Applicability:** 100% Cross-Cutting (12-15/12-15)  
**Source Code Detectable:** ~0-1/12-15 (0-7%)

---

### Section 10: OT/ICS-Specific Controls (~35-40 clauses) - OT ONLY

#### 10.1 - OT Access Control (~5 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 10.1.1 - Physical + Logical Access | | ✅ | | ⚠️ | Partial: IaC access policies |
| 10.1.2 - Role-Based Access (OT) | | ✅ | | ⚠️ | Partial: OT user configs |
| 10.1.3 - Emergency Access | | ✅ | | ❌ | Operational procedure |
| 10.1.4 - OT User Management | | ✅ | | ❌ | Operational process |
| 10.1.5 - OT Access Monitoring | | ✅ | | ⚠️ | Partial: Log configs |

**Source Code Detectable:** ~1-2/5 (20-40%)

#### 10.2 - OT Architecture (~7 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 10.2.1 - Purdue Model Compliance | | ✅ | | ✅ | **IaC: Network zone separation** |
| 10.2.2 - IT/OT DMZ | | ✅ | | ✅ | **IaC: DMZ network configs** |
| 10.2.3 - OT Network Segmentation | | ✅ | | ✅ | **IaC: VLAN, firewall rules** |
| 10.2.4 - Zones and Conduits | | ✅ | | ✅ | **IaC: Network architecture** |
| 10.2.5 - Safety System Isolation | | ✅ | | ✅ | **IaC: SIS network isolation** |
| 10.2.6 - Remote Access to OT | | ✅ | | ✅ | **IaC: Jump box configs** |
| 10.2.7 - Wireless in OT | | ✅ | | ⚠️ | Partial: WiFi configs |

**Source Code Detectable:** ~5-6/7 (71-86%)

#### 10.3 - OT Secure Coding (~7 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 10.3.1 - Firmware Integrity | | ✅ | | ✅ | **SAST: Firmware signing, checksums** |
| 10.3.2 - PLC Program Validation | | ✅ | | ✅ | **SAST: PLC code review (ladder logic)** |
| 10.3.3 - Interlocks & Failsafes | | ✅ | | ✅ | **SAST: Safety logic validation** |
| 10.3.4 - Input Validation (OT) | | ✅ | | ✅ | **SAST: Industrial protocol validation** |
| 10.3.5 - Unauthorized Change Prevention | | ✅ | | ✅ | **SAST: Code signing, version control** |
| 10.3.6 - Register Block Separation | | ✅ | | ✅ | **SAST: Memory protection in PLC code** |
| 10.3.7 - Code Modularization | | ✅ | | ✅ | **SAST: Code structure analysis** |

**Source Code Detectable:** 7/7 (100%)**

#### 10.4 - OT Change Management (~4 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 10.4.1 - Maintenance Windows | | ✅ | | ❌ | Operational scheduling |
| 10.4.2 - OT Change Testing | | ✅ | | ⚠️ | Partial: Test configs |
| 10.4.3 - Rollback Procedures (OT) | | ✅ | | ⚠️ | Partial: Backup configs |
| 10.4.4 - Change Coordination | | ✅ | | ❌ | Operational coordination |

**Source Code Detectable:** ~0-1/4 (0-25%)

#### 10.5 - OT Vulnerability Management (~5 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 10.5.1 - OT Vulnerability Assessment | | ✅ | | ⚠️ | Partial: Passive scanning configs |
| 10.5.2 - Virtual Patching | | ✅ | | ✅ | **IaC: Network-based mitigation** |
| 10.5.3 - Vendor Coordination | | ✅ | | ❌ | Vendor communication |
| 10.5.4 - Risk-Based Prioritization | | ✅ | | ❌ | Risk assessment process |
| 10.5.5 - Compensating Controls | | ✅ | | ✅ | **IaC: Alternative security controls** |

**Source Code Detectable:** ~2/5 (40%)

#### 10.6 - OT Incident Management (~4 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 10.6.1 - Safety vs Security Incident | | ✅ | | ❌ | Incident classification |
| 10.6.2 - Operational Continuity Priority | | ✅ | | ❌ | Response procedure |
| 10.6.3 - OT Incident Response | | ✅ | | ❌ | IR playbook execution |
| 10.6.4 - Safety Team Coordination | | ✅ | | ❌ | Cross-team collaboration |

**Source Code Detectable:** 0/4 (0%)

#### 10.7 - OT Supply Chain (~4 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 10.7.1 - Legacy System Management | | ✅ | | ❌ | Asset lifecycle management |
| 10.7.2 - End-of-Life Equipment | | ✅ | | ❌ | Operational risk acceptance |
| 10.7.3 - Vendor Support Requirements | | ✅ | | ❌ | Contract requirements |
| 10.7.4 - Industrial Procurement | | ✅ | | ❌ | Procurement process |

**Source Code Detectable:** 0/4 (0%)

---

**Section 10 Summary:**

| Subsection | Clauses | Source Code Detectable | Percentage |
|------------|---------|------------------------|------------|
| 10.1 - Access Control | ~5 | ~1-2 | 20-40% |
| 10.2 - Architecture | ~7 | ~5-6 | 71-86% |
| 10.3 - Secure Coding | ~7 | 7 | **100%** |
| 10.4 - Change Mgmt | ~4 | ~0-1 | 0-25% |
| 10.5 - Vulnerability Mgmt | ~5 | ~2 | 40% |
| 10.6 - Incident Mgmt | ~4 | 0 | 0% |
| 10.7 - Supply Chain | ~4 | 0 | 0% |
| **Section 10 Total** | ~35-40 | ~15-18 | **40-45%** |

**Highest Code-Scannable OT Subsections:**
- 10.3 Secure Coding (100%) - **Critical for OT security**
- 10.2 Architecture (71-86%) - **Network design validation**
- 10.5 Vulnerability Management (40%) - **Virtual patching configs**

---

### Section 11: Assurance (~8-10 clauses)

| Clause | IT | OT | Both | Source Code | Notes |
|--------|----|----|------|-------------|-------|
| 11.1 - Security Testing Programme | | | ✅ | ❌ | Testing strategy documentation |
| 11.2.1 - Vulnerability Scanning (IT) | ✅ | | | ⚠️ | Partial: Scan configs |
| 11.2.2 - Passive Scanning (OT) | | ✅ | | ❌ | Passive monitoring only |
| 11.3 - Penetration Testing | | | ✅ | ❌ | Manual pentesting |
| 11.4 - Red Team Exercises | | | ✅ | ❌ | Attack simulation |
| 11.5 - Independent Audits | | | ✅ | ❌ | Third-party audit |
| 11.6 - Continuous Assurance | | | ✅ | ⚠️ | Partial: Automated testing configs |

**Applicability:**  
- Cross-Cutting: ~7-8 clauses  
- IT-Specific: ~1-2 clauses (active scanning)  

**Source Code Detectable:** ~1-2/8-10 (10-20%)

---

## COMPREHENSIVE SUMMARY TABLE

### Overall Source Code Applicability

| Section | Total Clauses | Source Code Detectable | Percentage | Primary Detection Methods |
|---------|---------------|------------------------|------------|---------------------------|
| **1. Audit** | 4 | 0 | 0% | N/A - Organizational |
| **2. Governance** | 15-20 | 0 | 0% | N/A - Organizational |
| **3. Risk & Resilience** | 25-30 | 4-6 | 16-20% | IaC (Cloud configs) |
| **4. Asset Management** | 8-10 | 1-2 | 10-20% | IaC (Inventory), SBOM |
| **5. Protect** | 80-90 | 45-55 | 55-65% | **SAST, SCA, IaC, Secrets** |
| **6. Detect/Respond/Recover** | 25-30 | 3-5 | 10-20% | IaC (SIEM configs) |
| **7. Awareness** | 8-10 | 0 | 0% | N/A - Training |
| **8. Supply Chain** | 10-12 | 1-2 | 8-20% | SAST (Code signing), SBOM |
| **9. Third Party** | 12-15 | 0-1 | 0-7% | IaC (Vendor IAM) |
| **10. OT/ICS** | 35-40 | 15-18 | 40-45% | **SAST (PLC), IaC (OT network)** |
| **11. Assurance** | 8-10 | 1-2 | 10-20% | IaC (Test configs) |
| **TOTAL** | **~220** | **~90-100** | **40-45%** | Multiple tools required |

---

### Source Code Detection Tools Required

| Tool Category | CCoP Sections Covered | Clause Count | Key Capabilities |
|---------------|----------------------|--------------|------------------|
| **SAST (Static Application Security Testing)** | 5.1, 5.4, 5.12, 5.13, 5.14, 5.17, 5.18, 8.3, 10.3 | ~30-35 | Code vulnerabilities, OWASP Top 10, secure coding |
| **SCA (Software Composition Analysis)** | 5.18, 8.4 | ~5-8 | Dependency scanning, license compliance, SBOM |
| **IaC Scanning** | 3.7, 5.5, 5.6, 5.7, 5.8, 5.9, 5.11, 5.13, 5.14, 5.16, 5.17, 10.2, 10.5 | ~35-40 | Cloud configs, network security, infrastructure baselines |
| **Secret Scanning** | 5.4, 5.14 | ~3-5 | Hardcoded credentials, API keys, certificates |
| **Container Scanning** | 3.7, 5.9, 5.18 | ~5-8 | Image vulnerabilities, misconfigurations |
| **Policy-as-Code** | 3.7, 5.1, 5.5, 5.6, 10.2 | ~8-10 | Compliance enforcement, architectural validation |

---

## Key Insights for Your LLM Project

### 1. Section 5 (Protect) is Most Code-Scannable
- **55-65% of Section 5 clauses are code-detectable** (~45-55 clauses)
- Highest ROI for automated scanning
- Covers SAST, SCA, IaC, and Secret Scanning

### 2. Section 10.3 (OT Secure Coding) is 100% Scannable
- **All 7 clauses can be validated via code analysis**
- Unique differentiator - most tools ignore OT/PLC code
- Critical for CII organizations with industrial systems

### 3. IaC Scanning Covers ~35-40 Clauses
- Network segmentation (5.5, 10.2)
- Cloud security (3.7)
- System hardening (5.9)
- Configuration management (5.11)

### 4. ~60% of CCoP Requires Non-Code Controls
- Governance, training, incident response
- Your LLM can still add value here through:
  - Policy generation
  - Gap analysis
  - Documentation automation
  - Incident report generation

### 5. Hybrid IT/OT Organizations Need Both
- IT scanning: Sections 3-9 (~50-60 code-scannable clauses)
- OT scanning: Section 10 (~15-18 code-scannable clauses)
- Cross-cutting: IaC applies to both domains

---

## Recommendations for Phase 1A Validation

### Test These Code-Scannable Sections First:

**High Priority (Most Scannable):**
1. **Section 5.12** - Application Security (86-100% scannable)
2. **Section 5.14** - Cryptography (100% scannable)
3. **Section 5.5** - Network Segmentation (100% scannable)
4. **Section 10.3** - OT Secure Coding (100% scannable)
5. **Section 5.9** - System Hardening (100% scannable)

**Medium Priority:**
6. **Section 5.13** - Database Security (80% scannable)
7. **Section 10.2** - OT Architecture (71-86% scannable)
8. **Section 5.18** - Vulnerability Management (40-60% scannable)

**Lower Priority (Less Scannable):**
9. **Section 3.7** - Cloud Computing (partial)
10. **Section 5.1** - Access Control (50-67% scannable)

### Create 50-100 Test Examples Covering:
- **30 examples:** Section 5 IT controls (SAST/IaC)
- **15 examples:** Section 10 OT controls (SAST for PLC, IaC for networks)
- **10 examples:** Cross-cutting (incident classification, gap analysis)
- **5 examples:** Non-scannable controls (to test model's ability to recognize limitations)

This ensures comprehensive validation of both code scanning AND broader compliance capabilities.</parameter>