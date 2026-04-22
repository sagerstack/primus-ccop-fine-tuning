# Ground Truth Citation Audit Report

**Generated:** 2026-04-22 04:15 UTC
**Semantic threshold (Pass 3):** 0.35

## Summary

| Metric | Count |
|--------|-------|
| Test cases audited | 435 |
| clause_reference values audited (Pass 1) | 501 |
| In-text citations extracted (Pass 2) | 365 |
| Clause references semantically checked (Pass 3) | 317 |
| **Pass 1 flags (invalid clause_reference ID)** | **159** |
| **Pass 2 flags (invalid in-text citation)** | **85** |
| **Pass 3 flags (semantic mismatch)** | **0** |
| **Total unique flags** | **192** |

### Recommended Actions

| Action | Count |
|--------|-------|
| CORRECT (clear nearest-neighbour mapping) | 0 |
| DEPRECATE (low confidence, no salvageable fix) | 0 |
| HUMAN_REVIEW (requires expert judgment) | 192 |

---

## Flagged Cases by Benchmark

### B01_CCOP_APPLICABILITY_SCOPE

- **B1-001** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `2.3` (source: CCoP 2.0)
  - **Reason:** In-text citation '2.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.12.1` (nearest-neighbour confidence=0.685)

- **B1-017** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `CCoP 2.0 Section 5.1.5` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.1.5', 'CCoP 2.0')]
  - **Suggested correction:** `5.3.1` (nearest-neighbour confidence=0.661)

### B02_COMPLIANCE_CLASSIFICATION

- **B2-001** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.1.5` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.1.5', 'CCoP 2.0')]
  - **Suggested correction:** `10.2.3` (nearest-neighbour confidence=0.673)

- **B2-003** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.6.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.6.4', 'CCoP 2.0')]
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.681)

- **B2-010** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.6.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.6.4', 'CCoP 2.0')]
  - **Suggested correction:** `1.1.1` (nearest-neighbour confidence=0.667)

- **B2-014** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.6.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.6.4', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.708)

- **B2-024** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.6.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.6.4', 'CCoP 2.0')]
  - **Suggested correction:** `1.1.1` (nearest-neighbour confidence=0.654)

### B03_CONDITIONAL_COMPLIANCE_REASONING

- **B3-004** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `5.8.1` (nearest-neighbour confidence=0.637)

- **B3-005** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.3.2` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.3.2', 'CCoP 2.0')]
  - **Suggested correction:** `5.1.4` (nearest-neighbour confidence=0.639)

- **B3-006** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2', 'CCoP 2.0')]
  - **Suggested correction:** `5.10.1` (nearest-neighbour confidence=0.642)

- **B3-011** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `1.6.2` (nearest-neighbour confidence=0.621)

- **B3-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.5` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.5', 'CCoP 2.0')]
  - **Suggested correction:** `7.3.3` (nearest-neighbour confidence=0.724)

- **B3-021** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2', 'CCoP 2.0')]
  - **Suggested correction:** `8.2.1` (nearest-neighbour confidence=0.639)

- **B3-024** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `9.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('9.4', 'CCoP 2.0')]
  - **Suggested correction:** `8.1.4` (nearest-neighbour confidence=0.732)

### B05_CONTROL_COMPREHENSION

- **B05-002** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.2.3', 'CCoP 2.0')]
  - **Suggested correction:** `5.3.1` (nearest-neighbour confidence=0.717)

- **B05-013** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.3', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.630)

- **B05-015** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `9.3.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('9.3.1', 'CCoP 2.0')]
  - **Suggested correction:** `9.2.3` (nearest-neighbour confidence=0.673)

- **B05-016** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.3.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.3.4', 'CCoP 2.0')]
  - **Suggested correction:** `8.2.1` (nearest-neighbour confidence=0.635)

- **B05-018** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.5.5` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.5.5', 'CCoP 2.0')]
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.656)

- **B05-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.2.3', 'CCoP 2.0')]
  - **Suggested correction:** `5.8.1` (nearest-neighbour confidence=0.678)

### B06_INTENT_UNDERSTANDING

- **B06-002** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.2.3', 'CCoP 2.0')]
  - **Suggested correction:** `5.1` (nearest-neighbour confidence=0.617)

- **B06-013** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.5` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.2.5', 'CCoP 2.0')]
  - **Suggested correction:** `5.3` (nearest-neighbour confidence=0.615)

- **B06-018** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `7.4.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('7.4.1', 'CCoP 2.0')]
  - **Suggested correction:** `8.2.1` (nearest-neighbour confidence=0.721)

- **B06-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.655)

### B07_GAP_IDENTIFICATION_QUALITY

- **B07-001** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.2` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.2', 'CCoP 2.0')]
  - **Suggested correction:** `4.1.1` (nearest-neighbour confidence=0.724)

- **B07-002** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.2` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.2', 'CCoP 2.0')]
  - **Suggested correction:** `7.1.4` (nearest-neighbour confidence=0.655)

- **B07-003** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.2` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.2', 'CCoP 2.0')]
  - **Suggested correction:** `4.1.1` (nearest-neighbour confidence=0.671)

- **B07-005** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.2` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.2', 'CCoP 2.0')]
  - **Suggested correction:** `7.1.4` (nearest-neighbour confidence=0.643)

- **B07-006** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.2.4', 'CCoP 2.0')]
  - **Suggested correction:** `7.1.4` (nearest-neighbour confidence=0.640)

- **B07-007** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.5` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.2.5', 'CCoP 2.0')]
  - **Suggested correction:** `5.3.1` (nearest-neighbour confidence=0.630)

- **B07-008** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.2.4', 'CCoP 2.0')]
  - **Suggested correction:** `5.9.2` (nearest-neighbour confidence=0.633)

- **B07-010** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.6` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.2.6', 'CCoP 2.0')]
  - **Suggested correction:** `7.1.4` (nearest-neighbour confidence=0.633)

- **B07-015** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.3.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('6.3.4', 'CCoP 2.0')]
  - **Suggested correction:** `10.4.4` (nearest-neighbour confidence=0.649)

- **B07-017** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.4.2` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.4.2', 'CCoP 2.0')]
  - **Suggested correction:** `10.2` (nearest-neighbour confidence=0.691)

- **B07-018** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.4.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.4.4', 'CCoP 2.0')]
  - **Suggested correction:** `10` (nearest-neighbour confidence=0.688)

- **B07-027** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.2.3', 'CCoP 2.0')]
  - **Suggested correction:** `7.1.4` (nearest-neighbour confidence=0.626)

### B08_RISK_BASED_PRIORITIZATION

- **B08-001** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.698)

- **B08-001** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.698)

- **B08-002** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.702)

- **B08-002** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.702)

- **B08-003** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.705)

- **B08-003** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.705)

- **B08-004** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.691)

- **B08-004** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.691)

- **B08-005** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.705)

- **B08-005** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.705)

- **B08-006** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.691)

- **B08-006** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.691)

- **B08-007** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.712)

- **B08-007** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.712)

- **B08-008** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.699)

- **B08-008** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.699)

- **B08-009** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.706)

- **B08-009** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.706)

- **B08-010** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.686)

- **B08-010** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.686)

- **B08-011** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.688)

- **B08-011** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.688)

- **B08-012** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.710)

- **B08-012** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.710)

- **B08-013** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.710)

- **B08-013** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.710)

- **B08-014** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.717)

- **B08-014** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.717)

- **B08-015** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.696)

- **B08-015** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.696)

- **B08-016** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.716)

- **B08-016** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.716)

- **B08-017** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.690)

- **B08-017** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.690)

- **B08-018** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.708)

- **B08-018** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.708)

- **B08-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.723)

- **B08-019** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.723)

- **B08-020** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `8.2` (nearest-neighbour confidence=0.705)

- **B08-020** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `8.2` (nearest-neighbour confidence=0.705)

- **B08-021** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.699)

- **B08-021** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.699)

- **B08-022** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.705)

- **B08-022** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.705)

- **B08-023** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.713)

- **B08-023** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.713)

- **B08-024** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.710)

- **B08-024** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.710)

- **B08-025** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.711)

- **B08-025** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.711)

### B09_RISK_IDENTIFICATION_RESIDUAL_RISK

- **B09-001** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.683)

- **B09-002** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `10.2` (nearest-neighbour confidence=0.751)

- **B09-003** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.650)

- **B09-004** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.702)

- **B09-005** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.696)

- **B09-006** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.671)

- **B09-007** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.10` (nearest-neighbour confidence=0.717)

- **B09-008** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.672)

- **B09-009** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.9.1` (nearest-neighbour confidence=0.684)

- **B09-010** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `7.3.3` (nearest-neighbour confidence=0.733)

- **B09-011** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `8.2` (nearest-neighbour confidence=0.758)

- **B09-012** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.685)

- **B09-013** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.711)

- **B09-014** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.663)

- **B09-015** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.5` (nearest-neighbour confidence=0.719)

- **B09-016** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.5` (nearest-neighbour confidence=0.669)

- **B09-017** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.5` (nearest-neighbour confidence=0.696)

- **B09-018** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `5.10.1` (nearest-neighbour confidence=0.677)

- **B09-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.5` (nearest-neighbour confidence=0.656)

- **B09-020** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.691)

- **B09-021** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `9` (nearest-neighbour confidence=0.685)

- **B09-022** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.659)

- **B09-023** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `8.2` (nearest-neighbour confidence=0.703)

- **B09-024** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.5` (nearest-neighbour confidence=0.646)

- **B09-025** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.658)

### B12_AUDIT_PERSPECTIVE_ALIGNMENT

- **B12-001** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.2.3', 'CCoP 2.0')]
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.686)

- **B12-005** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.2` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.2', 'CCoP 2.0')]
  - **Suggested correction:** `4.1` (nearest-neighbour confidence=0.748)

- **B12-008** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `7.4.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('7.4.1', 'CCoP 2.0')]
  - **Suggested correction:** `8.2.1` (nearest-neighbour confidence=0.706)

- **B12-014** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.5` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.2.5', 'CCoP 2.0')]
  - **Suggested correction:** `5.6.1` (nearest-neighbour confidence=0.708)

- **B12-016** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `9.3.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('9.3.1', 'CCoP 2.0')]
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.682)

- **B12-020** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2.1', 'CCoP 2.0')]
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.741)

### B21_HALLUCINATION_OVER_SPECIFICATION

- **B21-001** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `5.9.7` (source: CCoP 2.0)
  - **Reason:** In-text citation '5.9.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.606)

- **B21-001** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `5.3.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '5.3.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.606)

- **B21-004** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `8.5.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '8.5.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.3.2` (nearest-neighbour confidence=0.757)

- **B21-005** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `9.4.1` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('9.4.1', 'CCoP 2.0')]
  - **Suggested correction:** `8.1.4` (nearest-neighbour confidence=0.737)

- **B21-008** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `11.7.5` (source: CCoP 2.0)
  - **Reason:** In-text citation '11.7.5' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.646)

- **B21-009** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.7.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.7.3', 'CCoP 2.0')]
  - **Suggested correction:** `5.15.2` (nearest-neighbour confidence=0.739)

- **B21-010** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2.6` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2.6' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.12.1` (nearest-neighbour confidence=0.714)

- **B21-012** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.3.2` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.3.2', 'CCoP 2.0')]
  - **Suggested correction:** `5.12.1` (nearest-neighbour confidence=0.693)

- **B21-012** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `5.3.5` (source: CCoP 2.0)
  - **Reason:** In-text citation '5.3.5' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.12.1` (nearest-neighbour confidence=0.693)

- **B21-016** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `7.4.3` (source: CCoP 2.0)
  - **Reason:** In-text citation '7.4.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `9.2.4` (nearest-neighbour confidence=0.768)

- **B21-018** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.1.5` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('5.1.5', 'CCoP 2.0')]
  - **Suggested correction:** `10.2.3` (nearest-neighbour confidence=0.660)

- **B21-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `9.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('9.3', 'CCoP 2.0')]
  - **Suggested correction:** `8.2` (nearest-neighbour confidence=0.769)

- **B21-021** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('4.2', 'CCoP 2.0')]
  - **Suggested correction:** `3.7` (nearest-neighbour confidence=0.737)

### B22_WAIVER_EXCEPTION_REASONING

- **B22-001** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.714)

- **B22-002** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `6.1.4` (nearest-neighbour confidence=0.688)

- **B22-003** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `5.6.1` (nearest-neighbour confidence=0.673)

- **B22-004** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.718)

- **B22-005** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `3.8.1` (nearest-neighbour confidence=0.731)

- **B22-006** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `3.7.3` (nearest-neighbour confidence=0.681)

- **B22-007** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `7.1.7` (nearest-neighbour confidence=0.684)

- **B22-008** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `3.7.3` (nearest-neighbour confidence=0.707)

- **B22-009** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `3.7.3` (nearest-neighbour confidence=0.687)

- **B22-010** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.5` (nearest-neighbour confidence=0.667)

- **B22-011** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.667)

- **B22-012** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `7.1.4` (nearest-neighbour confidence=0.681)

- **B22-013** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.705)

- **B22-014** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.672)

- **B22-015** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `3.7.3` (nearest-neighbour confidence=0.695)

- **B22-016** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.674)

- **B22-017** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.694)

- **B22-018** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.671)

- **B22-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `3.7.3` (nearest-neighbour confidence=0.709)

- **B22-020** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('11.7', 'CCoP 2.0')]
  - **Suggested correction:** `3.7.3` (nearest-neighbour confidence=0.655)

### B24_INCIDENT_RESPONSE_GUIDANCE

- **B24-001** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.4', 'CCoP 2.0')]
  - **Suggested correction:** `7.1.1` (nearest-neighbour confidence=0.661)

- **B24-002** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.4', 'CCoP 2.0')]
  - **Suggested correction:** `7.3.5` (nearest-neighbour confidence=0.696)

- **B24-003** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.3', 'CCoP 2.0')]
  - **Suggested correction:** `preamble` (nearest-neighbour confidence=0.673)

- **B24-003** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.4', 'CCoP 2.0')]
  - **Suggested correction:** `preamble` (nearest-neighbour confidence=0.673)

- **B24-003** | Pass 1 | `metadata.clause_reference[2]` | [HUMAN_REVIEW]
  - **Original:** `8.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.7', 'CCoP 2.0')]
  - **Suggested correction:** `preamble` (nearest-neighbour confidence=0.673)

- **B24-004** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.4', 'CCoP 2.0')]
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.682)

- **B24-005** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.3', 'CCoP 2.0')]
  - **Suggested correction:** `7.1.1` (nearest-neighbour confidence=0.584)

- **B24-006** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.3', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.5` (nearest-neighbour confidence=0.666)

- **B24-006** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.4', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.5` (nearest-neighbour confidence=0.666)

- **B24-006** | Pass 1 | `metadata.clause_reference[2]` | [HUMAN_REVIEW]
  - **Original:** `8.6` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.6', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.5` (nearest-neighbour confidence=0.666)

- **B24-007** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.3', 'CCoP 2.0')]
  - **Suggested correction:** `preamble` (nearest-neighbour confidence=0.689)

- **B24-007** | Pass 1 | `metadata.clause_reference[2]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.4', 'CCoP 2.0')]
  - **Suggested correction:** `preamble` (nearest-neighbour confidence=0.689)

- **B24-008** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.4', 'CCoP 2.0')]
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.659)

- **B24-009** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.4', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.5` (nearest-neighbour confidence=0.637)

- **B24-009** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.6` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.6', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.5` (nearest-neighbour confidence=0.637)

- **B24-009** | Pass 1 | `metadata.clause_reference[2]` | [HUMAN_REVIEW]
  - **Original:** `8.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.7', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.5` (nearest-neighbour confidence=0.637)

- **B24-010** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.4', 'CCoP 2.0')]
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.616)

- **B24-010** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.6` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.6', 'CCoP 2.0')]
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.616)

- **B24-011** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `9.5` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('9.5', 'CCoP 2.0')]
  - **Suggested correction:** `8.2.1` (nearest-neighbour confidence=0.729)

- **B24-012** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.3', 'CCoP 2.0')]
  - **Suggested correction:** `7.3.5` (nearest-neighbour confidence=0.658)

- **B24-012** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.4', 'CCoP 2.0')]
  - **Suggested correction:** `7.3.5` (nearest-neighbour confidence=0.658)

- **B24-013** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `9.5` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('9.5', 'CCoP 2.0')]
  - **Suggested correction:** `8.2.1` (nearest-neighbour confidence=0.666)

- **B24-014** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.4', 'CCoP 2.0')]
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.683)

- **B24-014** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.6` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.6', 'CCoP 2.0')]
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.683)

- **B24-015** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.4', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.3` (nearest-neighbour confidence=0.662)

- **B24-016** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.3', 'CCoP 2.0')]
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.645)

- **B24-016** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.6` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.6', 'CCoP 2.0')]
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.645)

- **B24-017** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.3', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.5` (nearest-neighbour confidence=0.667)

- **B24-017** | Pass 1 | `metadata.clause_reference[2]` | [HUMAN_REVIEW]
  - **Original:** `8.6` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.6', 'CCoP 2.0')]
  - **Suggested correction:** `5.14.5` (nearest-neighbour confidence=0.667)

- **B24-018** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.3', 'CCoP 2.0')]
  - **Suggested correction:** `5.16.3` (nearest-neighbour confidence=0.606)

- **B24-018** | Pass 1 | `metadata.clause_reference[2]` | [HUMAN_REVIEW]
  - **Original:** `8.6` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.6', 'CCoP 2.0')]
  - **Suggested correction:** `5.16.3` (nearest-neighbour confidence=0.606)

- **B24-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.4', 'CCoP 2.0')]
  - **Suggested correction:** `7.3.5` (nearest-neighbour confidence=0.643)

- **B24-019** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.6` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.6', 'CCoP 2.0')]
  - **Suggested correction:** `7.3.5` (nearest-neighbour confidence=0.643)

- **B24-020** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.4', 'CCoP 2.0')]
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.652)

- **B24-020** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `9.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('9.4', 'CCoP 2.0')]
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.652)

- **B24-021** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.3', 'CCoP 2.0')]
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.646)

- **B24-023** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.5` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.5', 'CCoP 2.0')]
  - **Suggested correction:** `5.15.3` (nearest-neighbour confidence=0.670)

- **B24-024** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.3', 'CCoP 2.0')]
  - **Suggested correction:** `6.3.3` (nearest-neighbour confidence=0.704)

- **B24-024** | Pass 1 | `metadata.clause_reference[2]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.4', 'CCoP 2.0')]
  - **Suggested correction:** `6.3.3` (nearest-neighbour confidence=0.704)

- **B24-025** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.3', 'CCoP 2.0')]
  - **Suggested correction:** `2.1` (nearest-neighbour confidence=0.619)

- **B24-025** | Pass 1 | `metadata.clause_reference[2]` | [HUMAN_REVIEW]
  - **Original:** `8.6` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.6', 'CCoP 2.0')]
  - **Suggested correction:** `2.1` (nearest-neighbour confidence=0.619)

- **B24-025** | Pass 1 | `metadata.clause_reference[3]` | [HUMAN_REVIEW]
  - **Original:** `8.7` (source: CCoP 2.0)
  - **Reason:** None of the candidates matched inventory: [('8.7', 'CCoP 2.0')]
  - **Suggested correction:** `2.1` (nearest-neighbour confidence=0.619)
