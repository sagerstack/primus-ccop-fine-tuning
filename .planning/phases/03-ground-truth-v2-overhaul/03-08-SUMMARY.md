# Plan 03-08 Summary: Risk/Remediation Test Cases Generation

## Status: COMPLETE

## Deliverables

### 1. B08 Risk-Based Prioritization (25 test cases, merged B8+B11)
**File:** `ground-truth/test-suite/b08_risk_based_prioritization.jsonl`

Test scenarios covering gap prioritization:
- **Low difficulty (6)**: Straightforward likelihood x impact prioritization
- **Medium difficulty (11)**: Prioritization with constraints (limited staff, audit timeline, safety-critical, limited budget)
- **High difficulty (8)**: Complex OT vs IT prioritization, multiple critical gaps, zero budget scenarios

### 2. B09 Risk Identification and Residual Risk (25 test cases, merged B9+B16)
**File:** `ground-truth/test-suite/b09_risk_identification_residual_risk.jsonl`

Test scenarios covering:
- **Risk identification (13)**: Configuration analysis revealing compliance risks
  - Missing MFA, OT flat network, excessive privileges, logging gaps, vendor access
  - Encryption gaps, patch management, network exposure, physical security
  - Incident response, business continuity, data classification, change management
- **Residual risk (12)**: Remaining risks after implementing controls
  - After MFA, segmentation, encryption, SIEM, patching, vendor management
  - After IR preparation, training, physical security, backups, access controls, pen testing

### 3. B14 Remediation Quality and Feasibility (30 test cases, merged B14+B15)
**File:** `ground-truth/test-suite/b14_remediation_quality_feasibility.jsonl`

Test scenarios covering practical remediation:
- **Low difficulty (8)**: Straightforward fixes with minimal disruption
  - Default passwords, undocumented procedures, outdated contacts, alert tuning
- **Medium difficulty (13)**: Require planning or operational coordination
  - OT patching, access reviews, SIEM expansion, shadow IT, IR testing
  - Forensic capability, data flow mapping, third-party assets, IT/OT convergence
  - Backup testing, service accounts, physical security, network segmentation
- **High difficulty (9)**: Complex trade-offs or severe constraints
  - End-of-life systems, unsupported vendors, zero budget, small teams
  - Legacy protocols, safety-critical operations, high-volume encryption

## Validation Results

```
B08: 25 valid JSONL entries
B09: 25 valid JSONL entries
B14: 30 valid JSONL entries
Total: 80 risk and remediation test cases
```

**Sector Diversity (all benchmarks):**
- All 3 benchmarks: 7 sectors (banking, energy, government, healthcare, telecommunications, transportation, water)

All test cases conform to v2 schema with:
- `reasoning_chain` for risk analysis and remediation planning
- `acceptable_variations` for alternative valid approaches
- `key_facts` with tier ratings (critical/important/supporting)
- `fail_conditions` with missing_elements, incorrect_claims, hallucination_patterns
- `metadata` with section, clause_reference, domain, difficulty, scenario_type, test_category, created_date

## Notes

B08 merged B8 (prioritization) and B11 (severity assessment) - testing the ability to sequence remediation work based on risk, constraints, and sector-specific priorities.

B09 merged B9 (risk identification) and B16 (residual risk) - testing both finding risks in configurations and understanding that controls reduce but don't eliminate risk.

B14 merged B14 (remediation quality) and B15 (feasibility) - testing practical recommendations that consider real-world constraints like budget, timeline, operational disruption, and team capability.
