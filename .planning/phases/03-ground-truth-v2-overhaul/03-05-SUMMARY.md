# Plan 03-05 Summary: Rule-Based Test Cases Generation

## Status: COMPLETE

## Deliverables

### 1. B04 IT/OT Classification Boundary (25 test cases)
**File:** `ground-truth/test-suite/b04_it_ot_classification_boundary.jsonl`

Test scenarios covering:
- Multi-system classification (power generation, maritime port)
- Hybrid system identification (BMS, IoT medical devices)
- Hardware platform classification (Windows-based OT controllers)
- Monitoring systems (SIEM, MES, LIMS)
- Boundary devices (industrial firewalls)
- Infrastructure systems (data center power management)
- Operator interfaces (ATC workstations, CTC workstations)
- Classification principles (function vs OS vs location)

### 2. B21 Hallucination Over Specification (25 test cases)
**File:** `ground-truth/test-suite/b21_hallucination_over_specification.jsonl`

Test scenarios covering:
- Non-existent clauses (5.9.7, 8.5.2, 11.7.5, 4.2.6, 7.4.3, etc.)
- Non-existent requirement details (password length, encryption key length, training frequency)
- Non-existent vendor approvals (SIEM, firewall, backup software, cloud providers)
- Non-existent technical specifications (RTO, retention periods, response times)
- Non-existent certifications and qualifications
- Non-existent performance metrics (false positive rates, MFA latency)
- Non-existent budget percentages and staffing ratios

### 3. Existing Files Verified
- B01: 25 entries (already existed)
- B02: 25 entries (already existed)

## Validation Results

```
B04: 25 valid JSONL entries
B21: 25 valid JSONL entries
Total: 100 rule-based test cases
```

All test cases conform to v2 schema with:
- `expected_label` for rule-based classification
- `expected_response` (100-250 words)
- `key_facts` with tier ratings (critical/important/supporting)
- `fail_conditions` with forbidden_claims and hallucination_patterns
- `metadata` with section, clause_reference, domain, difficulty, scenario_type, test_category, created_date

## Notes

B21 test cases are adversarial by design - they ask about non-existent CCoP requirements to test whether the model correctly identifies hallucination vs. factual content. Each test requires the model to:
1. Acknowledge the clause/requirement does not exist
2. Not invent content for non-existent clauses
3. Reference the actual CCoP clause that addresses the general topic area

B04 test cases cover the IT/OT classification boundary per CCoP 2.0 Section 10, emphasizing that classification is based on function (controlling physical processes) not platform, location, or user base.
