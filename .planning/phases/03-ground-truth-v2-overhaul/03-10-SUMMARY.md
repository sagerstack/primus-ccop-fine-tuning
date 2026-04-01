# Plan 03-10 Summary: Singapore-Specific and Advanced Scenarios

## Status: COMPLETE

## Deliverables

### 1. B22 Waiver Exception Reasoning (20 test cases)
**File:** `ground-truth/test-suite/b22_waiver_exception_reasoning.jsonl`

Test scenarios covering Section 11(7) waiver process:
- **Section 11(7) Waiver Scenarios (6)**: Flat network OT waiver, MFA exemption for isolated systems, encryption performance waiver, patch deferral for safety-critical, legacy system exception, encryption in transit waiver
- **Waiver Application Process (5)**: Documentation requirements, timeline (60 days), information needed, gap closure plan, alternative measures
- **Waiver Decision Factors (5)**: Technical infeasibility assessments, cost-benefit analysis, sector-specific considerations, risk-based methodology, independent assessment requirements
- **Waiver Compliance Management (4)**: Conditional approvals, monitoring requirements, expiry dates, gap closure planning

### 2. B23 Multi-Regulator Coordination (20 test cases)
**File:** `ground-truth/test-suite/b23_multi_regulator_coordination.jsonl`

Test scenarios covering regulatory overlap between CSA, MAS, PDPC, IM8:
- **Banking (MAS) + CCoP (5)**: Encryption requirements alignment, incident reporting dual obligations, audit coordination, risk assessment harmonization, BCP testing requirements
- **Personal Data (PDPC) + CCoP (5)**: Data breach notification, encryption alignment, access control harmonization, data retention policies, cross-border data transfers
- **Sector-Specific Regulations + CCoP (5)**: IM8 (healthcare), CAAS (aviation), LTA/PSA (transport), EMA (energy), PUB (water)
- **Conflict Resolution (5)**: Stricter requirement dominance, conflicting timelines, documentation burden, assessment methodologies, enforcement coordination

### 3. B24 Incident Response Guidance (25 test cases)
**File:** `ground-truth/test-suite/b24_incident_response_guidance.jsonl`

Test scenarios covering CCoP 2.0 Section 8 (Response) incident management:
- **Ransomware Incidents (5)**: Healthcare patient records, SCADA water utility, banking payment systems, administrative vs operational systems, weekend response constraints
- **Data Breaches (5)**: Telecom customer data (50k records), government employee directory, SCADA configuration exposure, backup exfiltration, uncertain exfiltration
- **Service Disruptions (5)**: Equipment failure (non-cyber), DDoS attacks, software bugs, SCADA visibility loss, telemetry failures
- **Insider/Third-Party (5)**: Insider exfiltration, vendor breach, orphaned credentials, phishing campaigns, accidental deletion
- **Complex Scenarios (5)**: Supply chain deception, threat intelligence (pre-incident), pen test findings, simultaneous incidents, undetected long-term breach

## Validation Results

```
B22: 20 valid JSONL entries
B23: 20 valid JSONL entries
B24: 25 valid JSONL entries
Total: 65 Singapore-specific and advanced scenario test cases
```

**Sector Diversity:**
- B22: 6 sectors (banking, energy, government, healthcare, transportation, water)
- B23: 7 sectors (banking, healthcare, aviation, transportation, energy, water, government)
- B24: 7 sectors (healthcare, water, banking, telecom, government, energy, transportation)

All test cases conform to v2 schema with:
- `reasoning_chain` for waiver applications, regulatory coordination, and incident response logic
- `acceptable_variations` for alternative valid approaches
- `key_facts` with tier ratings (critical/important/supporting)
- `fail_conditions` with missing_elements, incorrect_claims, hallucination_patterns
- `metadata` with section, clause_reference, domain, difficulty, scenario_type, test_category, created_date

## Notes

B22 tests Section 11(7) waiver reasoning—the process by which CII organizations can request exemptions from specific controls when compliance is technically infeasible or disproportionately costly. This is a Singapore-specific regulatory mechanism.

B23 addresses the reality that Singapore CII organizations operate under multiple regulatory frameworks. The test scenarios evaluate the model's ability to identify when different regulators' requirements overlap, conflict, or complement each other.

B24 provides actionable incident response guidance for CII organizations facing real-world security incidents. The scenarios cover classification, reporting, containment, and recovery across all major incident types affecting critical infrastructure.

## Wave 3 Completion

This completes **Wave 3** of Phase 3. All plans 03-05 through 03-10 are complete with 435 test cases generated across 18 v2 benchmarks.
