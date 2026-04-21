# Ground Truth Citation Audit Report

**Generated:** 2026-04-21 16:34 UTC
**Semantic threshold (Pass 3):** 0.35

## Summary

| Metric | Count |
|--------|-------|
| Test cases audited | 435 |
| clause_reference values audited (Pass 1) | 493 |
| In-text citations extracted (Pass 2) | 396 |
| Clause references semantically checked (Pass 3) | 217 |
| **Pass 1 flags (invalid clause_reference ID)** | **190** |
| **Pass 2 flags (invalid in-text citation)** | **72** |
| **Pass 3 flags (semantic mismatch)** | **0** |
| **Total unique flags** | **223** |

### Recommended Actions

| Action | Count |
|--------|-------|
| CORRECT (clear nearest-neighbour mapping) | 0 |
| DEPRECATE (low confidence, no salvageable fix) | 0 |
| HUMAN_REVIEW (requires expert judgment) | 223 |

---

## Flagged Cases by Benchmark

### B05

- **B05-002** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.3` (source: CCoP 2.0)
  - **Reason:** clause_id='5.2.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.3.1` (nearest-neighbour confidence=0.717)

- **B05-013** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.3` (source: CCoP 2.0)
  - **Reason:** clause_id='4.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.630)

- **B05-015** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `9.3.1` (source: CCoP 2.0)
  - **Reason:** clause_id='9.3.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `9.2.3` (nearest-neighbour confidence=0.673)

- **B05-016** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.3.4` (source: CCoP 2.0)
  - **Reason:** clause_id='5.3.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `8.2.1` (nearest-neighbour confidence=0.635)

- **B05-018** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.5.5` (source: CCoP 2.0)
  - **Reason:** clause_id='5.5.5' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.656)

- **B05-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.3` (source: CCoP 2.0)
  - **Reason:** clause_id='5.2.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.8.1` (nearest-neighbour confidence=0.678)

### B06

- **B06-002** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.3` (source: CCoP 2.0)
  - **Reason:** clause_id='5.2.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.1` (nearest-neighbour confidence=0.617)

- **B06-013** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.5` (source: CCoP 2.0)
  - **Reason:** clause_id='5.2.5' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.3` (nearest-neighbour confidence=0.615)

- **B06-018** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `7.4.1` (source: CCoP 2.0)
  - **Reason:** clause_id='7.4.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `8.2.1` (nearest-neighbour confidence=0.721)

- **B06-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.655)

### B07

- **B07-001** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.2` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `4.1.1` (nearest-neighbour confidence=0.724)

- **B07-002** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.2` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.4` (nearest-neighbour confidence=0.655)

- **B07-003** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.2` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `4.1.1` (nearest-neighbour confidence=0.671)

- **B07-005** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.2` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.4` (nearest-neighbour confidence=0.643)

- **B07-006** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.4` (source: CCoP 2.0)
  - **Reason:** clause_id='5.2.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.4` (nearest-neighbour confidence=0.640)

- **B07-007** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.5` (source: CCoP 2.0)
  - **Reason:** clause_id='5.2.5' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.3.1` (nearest-neighbour confidence=0.630)

- **B07-008** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.4` (source: CCoP 2.0)
  - **Reason:** clause_id='5.2.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.9.2` (nearest-neighbour confidence=0.633)

- **B07-010** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.6` (source: CCoP 2.0)
  - **Reason:** clause_id='5.2.6' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.4` (nearest-neighbour confidence=0.633)

- **B07-015** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.3.4` (source: CCoP 2.0)
  - **Reason:** clause_id='6.3.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `10.4.4` (nearest-neighbour confidence=0.649)

- **B07-017** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.4.2` (source: CCoP 2.0)
  - **Reason:** clause_id='5.4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `10.2` (nearest-neighbour confidence=0.691)

- **B07-018** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.4.4` (source: CCoP 2.0)
  - **Reason:** clause_id='5.4.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `10` (nearest-neighbour confidence=0.688)

- **B07-027** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.3` (source: CCoP 2.0)
  - **Reason:** clause_id='5.2.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.4` (nearest-neighbour confidence=0.626)

### B08

- **B08-001** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.698)

- **B08-001** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.698)

- **B08-002** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.702)

- **B08-002** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.702)

- **B08-003** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.705)

- **B08-003** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.705)

- **B08-004** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.691)

- **B08-004** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.691)

- **B08-005** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.705)

- **B08-005** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.705)

- **B08-006** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.691)

- **B08-006** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.691)

- **B08-007** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.712)

- **B08-007** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.712)

- **B08-008** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.699)

- **B08-008** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.699)

- **B08-009** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.706)

- **B08-009** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.706)

- **B08-010** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.686)

- **B08-010** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.686)

- **B08-011** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.688)

- **B08-011** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.688)

- **B08-012** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.710)

- **B08-012** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.710)

- **B08-013** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.710)

- **B08-013** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.710)

- **B08-014** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.717)

- **B08-014** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.717)

- **B08-015** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.696)

- **B08-015** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.696)

- **B08-016** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.716)

- **B08-016** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.716)

- **B08-017** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.690)

- **B08-017** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.690)

- **B08-018** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.708)

- **B08-018** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.708)

- **B08-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.723)

- **B08-019** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.723)

- **B08-020** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `8.2` (nearest-neighbour confidence=0.705)

- **B08-020** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `8.2` (nearest-neighbour confidence=0.705)

- **B08-021** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.699)

- **B08-021** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.699)

- **B08-022** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.705)

- **B08-022** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.705)

- **B08-023** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.713)

- **B08-023** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.713)

- **B08-024** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.710)

- **B08-024** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.710)

- **B08-025** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.711)

- **B08-025** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.14.2` (nearest-neighbour confidence=0.711)

### B09

- **B09-001** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.683)

- **B09-002** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `10.2` (nearest-neighbour confidence=0.751)

- **B09-003** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.650)

- **B09-004** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `6.1` (nearest-neighbour confidence=0.716)

- **B09-005** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.696)

- **B09-006** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.671)

- **B09-007** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.10` (nearest-neighbour confidence=0.717)

- **B09-008** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.672)

- **B09-009** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.9.1` (nearest-neighbour confidence=0.684)

- **B09-010** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.3.3` (nearest-neighbour confidence=0.733)

- **B09-011** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `8.2` (nearest-neighbour confidence=0.758)

- **B09-012** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.685)

- **B09-013** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.711)

- **B09-014** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.663)

- **B09-015** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.5` (nearest-neighbour confidence=0.719)

- **B09-016** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.5` (nearest-neighbour confidence=0.669)

- **B09-017** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.5` (nearest-neighbour confidence=0.696)

- **B09-018** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.10.1` (nearest-neighbour confidence=0.677)

- **B09-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.5` (nearest-neighbour confidence=0.656)

- **B09-020** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.691)

- **B09-021** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `9` (nearest-neighbour confidence=0.685)

- **B09-022** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.659)

- **B09-023** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `8.2` (nearest-neighbour confidence=0.703)

- **B09-024** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.5` (nearest-neighbour confidence=0.646)

- **B09-025** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.2` (nearest-neighbour confidence=0.658)

### B1

- **B1-001** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `2.3` (source: CCoP 2.0)
  - **Reason:** In-text citation '2.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.12.1` (nearest-neighbour confidence=0.685)

- **B1-017** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `CCoP 2.0 Section 5.1.5` (source: CCoP 2.0)
  - **Reason:** clause_id='5.1.5' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.3.1` (nearest-neighbour confidence=0.661)

### B12

- **B12-001** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.3` (source: CCoP 2.0)
  - **Reason:** clause_id='5.2.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.686)

- **B12-005** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.2` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `4.1` (nearest-neighbour confidence=0.748)

- **B12-008** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `7.4.1` (source: CCoP 2.0)
  - **Reason:** clause_id='7.4.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `8.2.1` (nearest-neighbour confidence=0.706)

- **B12-014** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.2.5` (source: CCoP 2.0)
  - **Reason:** clause_id='5.2.5' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.6.1` (nearest-neighbour confidence=0.708)

- **B12-016** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `9.3.1` (source: CCoP 2.0)
  - **Reason:** clause_id='9.3.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.682)

- **B12-020** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2.1` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.741)

### B14

- **B14-001** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.9.2` (nearest-neighbour confidence=0.697)

- **B14-002** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.666)

- **B14-003** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.712)

- **B14-004** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.692)

- **B14-005** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.691)

- **B14-006** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.721)

- **B14-007** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `8.2.4` (nearest-neighbour confidence=0.656)

- **B14-008** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.9.2` (nearest-neighbour confidence=0.691)

- **B14-009** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.694)

- **B14-010** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.686)

- **B14-011** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.690)

- **B14-012** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.7.3` (nearest-neighbour confidence=0.692)

- **B14-013** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.3.1` (nearest-neighbour confidence=0.714)

- **B14-014** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.689)

- **B14-015** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.711)

- **B14-016** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `4.1.1` (nearest-neighbour confidence=0.696)

- **B14-017** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.692)

- **B14-018** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `8.1.4` (nearest-neighbour confidence=0.719)

- **B14-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.679)

- **B14-020** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.9.2` (nearest-neighbour confidence=0.658)

- **B14-021** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.671)

- **B14-022** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.699)

- **B14-023** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.685)

- **B14-024** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.695)

- **B14-025** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.704)

- **B14-026** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.684)

- **B14-027** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.699)

- **B14-028** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.7.3` (nearest-neighbour confidence=0.654)

- **B14-029** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `8.2.4` (nearest-neighbour confidence=0.678)

- **B14-030** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `6.1.1` (source: CCoP 2.0)
  - **Reason:** clause_id='6.1.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `2.1.4` (nearest-neighbour confidence=0.678)

### B2

- **B2-001** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.1.5` (source: CCoP 2.0)
  - **Reason:** clause_id='5.1.5' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `10.2.3` (nearest-neighbour confidence=0.673)

- **B2-003** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.6.4` (source: CCoP 2.0)
  - **Reason:** clause_id='5.6.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.681)

- **B2-010** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.6.4` (source: CCoP 2.0)
  - **Reason:** clause_id='5.6.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1.1.1` (nearest-neighbour confidence=0.667)

- **B2-014** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.6.4` (source: CCoP 2.0)
  - **Reason:** clause_id='5.6.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.708)

- **B2-024** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.6.4` (source: CCoP 2.0)
  - **Reason:** clause_id='5.6.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1.1.1` (nearest-neighbour confidence=0.654)

### B21

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
  - **Reason:** clause_id='9.4.1' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `8.2.4` (nearest-neighbour confidence=0.744)

- **B21-008** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `11.7.5` (source: CCoP 2.0)
  - **Reason:** In-text citation '11.7.5' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.646)

- **B21-009** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.7.3` (source: CCoP 2.0)
  - **Reason:** clause_id='5.7.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.15.2` (nearest-neighbour confidence=0.739)

- **B21-010** | Pass 2 | `ground_truth.expected_response` | [HUMAN_REVIEW]
  - **Original:** `4.2.6` (source: CCoP 2.0)
  - **Reason:** In-text citation '4.2.6' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.12.1` (nearest-neighbour confidence=0.714)

- **B21-012** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `5.3.2` (source: CCoP 2.0)
  - **Reason:** clause_id='5.3.2' not found in inventory for source_doc='CCoP 2.0'
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
  - **Reason:** clause_id='5.1.5' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `10.2.3` (nearest-neighbour confidence=0.660)

- **B21-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `9.3` (source: CCoP 2.0)
  - **Reason:** clause_id='9.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `8.2` (nearest-neighbour confidence=0.769)

- **B21-021** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `4.2` (source: CCoP 2.0)
  - **Reason:** clause_id='4.2' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.7` (nearest-neighbour confidence=0.737)

### B22

- **B22-001** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.714)

- **B22-002** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `6.1.4` (nearest-neighbour confidence=0.688)

- **B22-003** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `5.6.1` (nearest-neighbour confidence=0.673)

- **B22-004** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.718)

- **B22-005** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.8.1` (nearest-neighbour confidence=0.731)

- **B22-006** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.7.3` (nearest-neighbour confidence=0.681)

- **B22-007** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.7` (nearest-neighbour confidence=0.684)

- **B22-008** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.7.3` (nearest-neighbour confidence=0.707)

- **B22-009** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.7.3` (nearest-neighbour confidence=0.687)

- **B22-010** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.5` (nearest-neighbour confidence=0.667)

- **B22-011** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.667)

- **B22-012** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.4` (nearest-neighbour confidence=0.681)

- **B22-013** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.705)

- **B22-014** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.2.3` (nearest-neighbour confidence=0.672)

- **B22-015** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.7.3` (nearest-neighbour confidence=0.695)

- **B22-016** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1.2.1` (nearest-neighbour confidence=0.674)

- **B22-017** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.694)

- **B22-018** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `1` (nearest-neighbour confidence=0.671)

- **B22-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.7.3` (nearest-neighbour confidence=0.709)

- **B22-020** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `11.7` (source: CCoP 2.0)
  - **Reason:** clause_id='11.7' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `3.7.3` (nearest-neighbour confidence=0.655)

### B24

- **B24-001** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-001** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-002** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-002** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-003** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-003** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-004** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-004** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-005** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-005** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-006** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-006** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-007** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-007** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-008** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-008** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-009** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-009** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-010** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-010** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-011** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-011** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-012** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-012** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-013** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-013** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-014** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-014** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-015** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-015** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-016** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-016** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-017** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-017** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-018** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-018** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-019** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-019** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-020** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-020** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-021** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-021** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-022** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-022** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-023** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-023** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-024** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-024** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-025** | Pass 1 | `metadata.clause_reference[0]` | [HUMAN_REVIEW]
  - **Original:** `8.3` (source: CCoP 2.0)
  - **Reason:** clause_id='8.3' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)

- **B24-025** | Pass 1 | `metadata.clause_reference[1]` | [HUMAN_REVIEW]
  - **Original:** `8.4` (source: CCoP 2.0)
  - **Reason:** clause_id='8.4' not found in inventory for source_doc='CCoP 2.0'
  - **Suggested correction:** `7.1.6` (nearest-neighbour confidence=0.692)
