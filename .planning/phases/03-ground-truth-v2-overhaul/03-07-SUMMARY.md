# Plan 03-07 Summary: Gap/Risk Justification Test Cases Generation

## Status: COMPLETE

## Deliverables

### 1. B07 Gap Identification Quality (30 test cases)
**File:** `ground-truth/test-suite/b07_gap_identification_quality.jsonl`

Test scenarios covering:
- **Asset inventory gaps (5)**: Incomplete CII asset inventory, shadow IT, outdated inventory, third-party assets, missing data flow mapping
- **Privileged access gaps (5)**: Shared admin accounts, no access review, over-privileged service accounts, contractor permanent access, undefined break-glass procedures
- **Logging and monitoring gaps (5)**: Insufficient log collection, reactive-only review, log tampering risks, incomplete SIEM coverage, over-tuned alerting
- **OT security gaps (5)**: Unpatched OT systems, flat OT network, unprotected remote OT access, legacy OT protocols, unmanaged IT/OT convergence
- **Incident response gaps (5)**: Untested IR plan, outdated contact list, no forensic capability, undefined CSA reporting, no incident classification
- **Policy-vs-practice gaps (5, absorbed from B17)**:
  - B07-026: Policy requires complex passwords / Practice: default passwords in use
  - B07-027: Policy requires MFA / Practice: 40% exemptions granted
  - B07-028: Policy requires quarterly pen tests / Practice: last test 18 months ago
  - B07-029: Policy requires vendor due diligence / Practice: sole-source bypass review
  - B07-030: Policy requires daily backups / Practice: restoration never tested

### 2. B10 Risk Justification Coherence (20 test cases)
**File:** `ground-truth/test-suite/b10_risk_justification_coherence.jsonl`

Test scenarios covering board-level risk articulation across sectors:
- **Banking (3)**: Asset inventory prioritization, unprotected log storage, unverified backup restoration
- **Healthcare (3)**: Privileged access review, shared admin accounts, emergency access documentation
- **Energy (3)**: OT patching gap, over-privileged service accounts, partial SIEM coverage
- **Government (3)**: MFA exemptions, shadow IT, outdated IR contacts
- **Transportation (3)**: Incident classification, OT flat network, IT/OT convergence
- **Water (2)**: Vendor remote access, security awareness training, pen testing overdue
- **Telecommunications (2)**: Untested IR plan, forensic capability

## Validation Results

```
B07: 30 valid JSONL entries (including 5 B17-absorbed policy-practice gaps)
B10: 20 valid JSONL entries
Total: 50 gap/risk justification test cases
```

**Sector Diversity:**
- B07: 7 sectors (banking, energy, government, healthcare, telecommunications, transportation, water)
- B10: 7 sectors (banking, energy, government, healthcare, telecommunications, transportation, water)

All test cases conform to v2 schema with:
- `reasoning_chain` for gap identification and risk articulation logic
- `acceptable_variations` for different valid framings
- `key_facts` with tier ratings (critical/important/supporting)
- `fail_conditions` with missing_elements, incorrect_claims, hallucination_patterns
- `metadata` with section, clause_reference, domain, difficulty, scenario_type, test_category, created_date

## Notes

B07 tests the core audit capability of identifying compliance gaps. The inclusion of B17-absorbed policy-vs-practice scenarios ensures the model can detect when written policy doesn't match actual implementation—a common finding in CCoP audits.

B10 tests translate technical gaps into business risk language appropriate for board reporting. This bridges the gap between technical compliance findings and executive decision-making, a critical capability for CISOs and security managers communicating with senior leadership.
