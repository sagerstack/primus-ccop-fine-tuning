# Plan 03-09 Summary: Audit/Governance Test Cases Generation

## Status: COMPLETE

## Deliverables

### 1. B12 Audit Perspective Alignment (20 test cases)
**File:** `ground-truth/test-suite/b12_audit_perspective_alignment.jsonl`

Dual perspective testing:
- **CSA Auditor Viewpoint**: What auditors examine for each control
- **Risk Manager Audit Prep**: How to prepare for audit of each domain
- Covers: MFA, training, incident reporting, log retention, asset inventory, pen testing, third-party risk, BCP, segmentation, board governance, vulnerability management, data classification, IR planning, access reviews, OT security, supply chain, Forms A1/A2, cloud security, enforcement history, risk-based methodology

### 2. B13 Evidence Expectation Awareness (20 test cases)
**File:** `ground-truth/test-suite/b13_evidence_expectation_awareness.jsonl`

Evidence preparation across all 7 CCoP domains:
- **Governance** (3): Board oversight, third-party risk, CII designation documentation
- **Identification** (3): Asset inventory, risk assessment, regulatory tracking
- **Protection** (4): Access control, segmentation, data protection, physical security
- **Detection** (3): Monitoring/logging, vulnerability management, threat intelligence
- **Response** (3): IR preparedness, incident handling, forensic capability
- **Resilience** (2): Business continuity, backup/recovery
- **Training** (2): Awareness program, role-specific training

### 3. B18 Responsibility Attribution Singapore (25 test cases)
**File:** `ground-truth/test-suite/b18_responsibility_attribution_sg.jsonl`

Extended role hierarchy under Singapore's legal framework:
- **Core roles**: Board, CIIO, CISO, Risk Manager
- **Extended roles**: Vendors, Employees, Service providers, Subcontractors
- **Complex scenarios**: Joint CII arrangements, CSP breaches, M&A due diligence, supply chain vulnerabilities, scope changes
- **Legal framework**: Cybersecurity Act 2018, CCoP 2.0, PDPA

## Validation Results

```
B12: 20 valid JSONL entries
B13: 20 valid JSONL entries (7/7 domains covered)
B18: 25 valid JSONL entries
Total: 65 audit and governance test cases
```

**B13 Domain Coverage:** All 7 CCoP auditable domains covered
**B18 Roles Coverage:** Full hierarchy from Board to individual employees

All test cases conform to v2 schema with:
- `reasoning_chain` for audit preparation and responsibility mapping
- `acceptable_variations` for organizational context variations
- `key_facts` with tier ratings (critical/important/supporting)
- `fail_conditions` with missing_elements, incorrect_claims, hallucination_patterns
- `metadata` with section, clause_reference, domain, difficulty, scenario_type, test_category, created_date

## Notes

B12's dual perspective approach tests both understanding of auditor expectations and practical audit preparation—critical for CII organizations facing CSA audits.

B13 ensures comprehensive evidence awareness across all control domains, helping Risk Managers prepare thorough evidence packages.

B18 incorporates Singapore-specific legal and regulatory context, including CIIO personal liability under the Cybersecurity Act 2018—a critical distinction from generic governance benchmarks.
