# Plan 03-06 Summary: Core Reasoning Test Cases Generation

## Status: COMPLETE

## Deliverables

### 1. B05 Control Requirement Comprehension (25 test cases)
**File:** `ground-truth/test-suite/b05_control_comprehension.jsonl`

Test scenarios covering:
- Positive cases: straightforward control understanding (10 cases)
  - Password complexity, MFA, incident reporting, data retention
  - Network segmentation, vulnerability scanning, penetration testing
  - Backup requirements, encryption, security training
- Edge cases: complex/ambiguous scenarios (8 cases)
  - Third-party control allocation, cloud shared responsibility
  - Legacy system exemptions, subsidiary scope
  - Supply chain verification, mobile device management, OT patching
- Negative cases: common misunderstandings (7 cases)
  - Isolated network MFA exemptions, pen testing vs scanning
  - Cloud provider responsibility, training requirements
  - Log retention costs, small operator exemptions, grandfathered controls

### 2. B06 Control Intent Understanding (20 test cases)
**File:** `ground-truth/test-suite/b06_intent_understanding.jsonl`

Test scenarios covering control intent and security objectives:
- Password complexity → preventing brute force attacks
- MFA → limiting impact of credential theft
- Incident reporting timelines → enabling national response
- Log retention → forensic investigation capability
- Network segmentation → blast radius reduction
- Vulnerability scanning → exposure reduction
- Penetration testing → control validation
- Backup testing → recovery assurance
- Encryption in transit → eavesdropping protection
- Security training → human firewall
- Vendor due diligence → supply chain risk
- Change management → preventing security degradation
- Access review → privilege creep prevention
- Security monitoring → threat detection
- Data classification → protection proportional to sensitivity
- Physical security → preventing physical compromise
- Incident response plan → organized response
- Business continuity → resilience despite attacks
- Risk assessment → informed security decisions
- Management accountability → organizational commitment

## Validation Results

```
B05: 25 valid JSONL entries
B06: 20 valid JSONL entries
Total: 45 core reasoning test cases
```

All test cases conform to v2 schema with:
- `reasoning_chain` for LLM-judge evaluation
- `acceptable_variations` for response flexibility
- `key_facts` with tier ratings (critical/important/supporting)
- `fail_conditions` with missing_elements, incorrect_claims, hallucination_patterns
- `metadata` with section, clause_reference, domain, difficulty, scenario_type, test_category, created_date

## Notes

B05 tests focus on WHAT the requirements are - comprehension of specific control details. B06 tests focus on WHY the controls exist - understanding security intent and objectives. Together they evaluate the model's ability to both recall requirements accurately and explain their security rationale.

B05 negative cases specifically test common misconceptions and "loophole" thinking that organizations often use to avoid controls. B06 intent-based tests evaluate whether the model understands security principles that can be applied to novel situations beyond explicit requirements.
