# B1 Stratified Sample — 30 cases for human labeling

Source: `ground-truth/test-suite/` (435 total cases)

Selected: **30 cases** across 18 benchmarks

Clauses covered: **73**
 / 415 in clause inventory (17.6%)


## Selection

| # | test_id | benchmark | section | difficulty | domain | scenario | clauses |
|---|---------|-----------|---------|------------|--------|----------|---------|
| 1 | `B01-007` | B01 | CCoP 2.0 Scope, Supply Chain | medium | OT | outsourced_cii_accountability | CCoP 2.0 supply chain clauses,CCoP Section 5.5,Section 11 Cybersecurity Act,Section 14 Cybersecurity Act |
| 2 | `B01-009` | B01 | CCoP 2.0 OT Addendum | high | IT/OT | ot_addendum_scope | CCoP 2.0 OT Addendum,CCoP 2.0 Scope section,Section 10 OT Security |
| 3 | `B02-012` | B02 | Section 6: Detection | medium | OT | log_integrity_compliance | 6.1,6.1.3,6.2 |
| 4 | `B02-014` | B02 | 5 | high | OT | legacy_ot_patching_waiver | 5.10.1(e),Section 10 OT Addendum,Section 11(7) Cybersecurity Act |
| 5 | `B03-002` | B03 | 5 | medium | OT | conditional_compliance | 10.2.1,5.5.1,5.5.2 |
| 6 | `B03-030` | B03 | 1 | medium | OT | conditional_compliance | 1.4.1,1.4.5,1.5.1 |
| 7 | `B04-001` | B04 | Section 10: Operational Technology Security | medium | IT/OT | multi_system_classification | 10.1,10.1.1,5.1 |
| 8 | `B04-005` | B04 | Section 10: Operational Technology Security | medium | IT/OT | industrial_control_classification | 10.1,10.2.3,10.3.2,5.4.1 |
| 9 | `B05-013` | B05 | 1 | medium | IT | edge_case | 1.6.1,1.6.2,1.6.3,3.2.1 |
| 10 | `B05-016` | B05 | 5 | medium | IT | edge_case | 5.11.1,5.11.2,5.11.3,5.11.4 |
| 11 | `B06-002` | B06 | 5 | medium | IT | intent_analysis | 5.1.2,5.3.1,5.7.2 |
| 12 | `B06-013` | B06 | 5 | medium | IT | intent_analysis | 5.2.1,5.2.2 |
| 13 | `B07-015` | B07 | 6 | medium | IT | inadequate_implementation | 6.2.1,6.2.2,6.2.3 |
| 14 | `B07-022` | B07 | 7 | high | IT | inadequate_implementation | 7.2.3 |
| 15 | `B08-001` | B08 | 3 | low | IT | prioritization | 3.2.2(b),3.2.2(c) |
| 16 | `B08-018` | B08 | 3 | high | IT | prioritization | 3.2.2(b),3.2.2(c) |
| 17 | `B09-019` | B09 | 3 | high | IT | residual_risk | 3.2.2(a),3.2.4,3.2.5 |
| 18 | `B10-015` | B10 | 8 | high | IT | risk_articulation | 8.1 |
| 19 | `B12-008` | B12 | 8 | medium | IT | audit_preparation | 8.2.1,8.2.2,8.2.3,8.2.4 |
| 20 | `B12-016` | B12 | 3 | high | IT | audit_preparation | 3.8.1,3.8.2,3.8.3,3.8.4,3.8.5 |
| 21 | `B13-003` | B13 | 4 | high | IT | evidence_preparation | 4.1 |
| 22 | `B13-009` | B13 | 7 | high | IT | evidence_preparation | 7.1 |
| 23 | `B14-001` | B14 | 6 | medium | IT | remediation_scenario | 6.1.1 |
| 24 | `B18-001` | B18 | 8 | medium | IT | responsibility_attribution | 8.1.1 |
| 25 | `B21-001` | B21 | Non-existent Clause | high | IT | non_existent_clause | N/A |
| 26 | `B21-022` | B21 | CCoP 2.0 Scope | high | IT | non_existent_designation_period | Cybersecurity Act Section 11,Section 2 |
| 27 | `B22-015` | B22 | 1 | high | IT | waiver_reasoning | 1.6.1,1.6.2,1.6.3 |
| 28 | `B23-001` | B23 | 11 | medium | IT | regulatory_coordination | 11.1 |
| 29 | `B24-003` | B24 | 7 | medium | IT | incident_guidance | 7.1.1(b),7.1.1(g),7.1.1(i),7.1.4 |
| 30 | `B24-022` | B24 | 7 | medium | IT | incident_guidance | 6.4.1,6.4.3,7.1.1(a),7.1.1(d) |

## Per-benchmark count

| benchmark | cases |
|-----------|-------|
| B01 | 2 |
| B02 | 2 |
| B03 | 2 |
| B04 | 2 |
| B05 | 2 |
| B06 | 2 |
| B07 | 2 |
| B08 | 2 |
| B09 | 1 |
| B10 | 1 |
| B12 | 2 |
| B13 | 2 |
| B14 | 1 |
| B18 | 1 |
| B21 | 2 |
| B22 | 1 |
| B23 | 1 |
| B24 | 2 |

## Difficulty distribution

| difficulty | count |
|------------|-------|
| high | 12 |
| low | 1 |
| medium | 17 |

## Domain distribution

| domain | count |
|--------|-------|
| IT | 22 |
| IT/OT | 3 |
| OT | 5 |

## Scenario type distribution

| scenario | count |
|----------|-------|
| audit_preparation | 2 |
| conditional_compliance | 2 |
| edge_case | 2 |
| evidence_preparation | 2 |
| inadequate_implementation | 2 |
| incident_guidance | 2 |
| industrial_control_classification | 1 |
| intent_analysis | 2 |
| legacy_ot_patching_waiver | 1 |
| log_integrity_compliance | 1 |
| multi_system_classification | 1 |
| non_existent_clause | 1 |
| non_existent_designation_period | 1 |
| ot_addendum_scope | 1 |
| outsourced_cii_accountability | 1 |
| prioritization | 2 |
| regulatory_coordination | 1 |
| remediation_scenario | 1 |
| residual_risk | 1 |
| responsibility_attribution | 1 |
| risk_articulation | 1 |
| waiver_reasoning | 1 |

## Clauses covered

```
1.4.1, 1.4.5, 1.5.1, 1.6.1, 1.6.2, 1.6.3, 10.1, 10.1.1, 10.2.1, 10.2.3, 10.3.2, 11.1, 3.2.1, 3.2.2(a), 3.2.2(b), 3.2.2(c), 3.2.4, 3.2.5, 3.8.1, 3.8.2, 3.8.3, 3.8.4, 3.8.5, 4.1, 5.1, 5.1.2, 5.10.1(e), 5.11.1, 5.11.2, 5.11.3, 5.11.4, 5.2.1, 5.2.2, 5.3.1, 5.4.1, 5.5.1, 5.5.2, 5.7.2, 6.1, 6.1.1, 6.1.3, 6.2, 6.2.1, 6.2.2, 6.2.3, 6.4.1, 6.4.3, 7.1, 7.1.1(a), 7.1.1(b), 7.1.1(d), 7.1.1(g), 7.1.1(i), 7.1.4, 7.2.3, 8.1, 8.1.1, 8.2.1, 8.2.2, 8.2.3, 8.2.4, CCoP 2.0 OT Addendum, CCoP 2.0 Scope section, CCoP 2.0 supply chain clauses, CCoP Section 5.5, Cybersecurity Act Section 11, N/A, Section 10 OT Addendum, Section 10 OT Security, Section 11 Cybersecurity Act, Section 11(7) Cybersecurity Act, Section 14 Cybersecurity Act, Section 2
```