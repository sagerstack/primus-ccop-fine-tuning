# GT Stage-1 Defect Ledger (deterministic)

Generated: 2026-06-29T00:51:48.913225+00:00  |  Records scanned: **435**  |  Defects: **942**

Read-only, LLM-free, reproducible. Catches mechanically-decidable defects only;
citation relevance/hallucination is deferred to Stage 2.

## By detector

| Detector | Count | What it means |
|---|---:|---|
| D-CITE-KF | 138 | clause cited in key_facts/support_citations does not exist |
| D-FAMILY | 98 | key_facts.source families disjoint from clause_reference |
| D-FORBIDDEN | 706 | required element contaminating forbidden_claims (heuristic) |
| D-LEAK | 0 | expected_response duplicates the question |

## By benchmark

| Benchmark | Defects |
|---|---:|
| B01 | 3 |
| B02 | 13 |
| B04 | 26 |
| B05 | 101 |
| B06 | 72 |
| B07 | 127 |
| B08 | 75 |
| B09 | 75 |
| B10 | 60 |
| B12 | 60 |
| B13 | 40 |
| B14 | 90 |
| B21 | 25 |
| B22 | 40 |
| B23 | 60 |
| B24 | 75 |

## Defects

- **B01-016** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['2'] vs clause_reference families ['9']`
- **B01-017** `D-CITE-KF` (high) — CCoP clause '5.1.5' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.1.5`
- **B01-020** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['2'] vs clause_reference families ['1']`
- **B02-001** `D-CITE-KF` (high) — CCoP clause '5.1.5' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.1.5`
- **B02-001** `D-CITE-KF` (high) — CCoP clause '5.1.5' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.1.5`
- **B02-003** `D-CITE-KF` (high) — CCoP clause '5.6.4' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.6.4`
- **B02-003** `D-CITE-KF` (high) — CCoP clause '5.6.4' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.6.4`
- **B02-003** `D-CITE-KF` (high) — CCoP clause '5.6.4' cited in ground_truth.key_facts[3].source but absent from clause inventory  
  · `ground_truth.key_facts[3].source` → `5.6.4`
- **B02-010** `D-CITE-KF` (high) — CCoP clause '5.6.4' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.6.4`
- **B02-010** `D-CITE-KF` (high) — CCoP clause '5.6.4' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.6.4`
- **B02-010** `D-CITE-KF` (high) — CCoP clause '5.6.4' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.6.4`
- **B02-010** `D-CITE-KF` (high) — CCoP clause '5.6.4' cited in ground_truth.key_facts[3].source but absent from clause inventory  
  · `ground_truth.key_facts[3].source` → `5.6.4`
- **B02-014** `D-CITE-KF` (high) — CCoP clause '5.6.4' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.6.4`
- **B02-024** `D-CITE-KF` (high) — CCoP clause '5.6.4' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.6.4`
- **B02-024** `D-CITE-KF` (high) — CCoP clause '5.6.4' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.6.4`
- **B02-024** `D-CITE-KF` (high) — CCoP clause '5.6.4' cited in ground_truth.key_facts[3].source but absent from clause inventory  
  · `ground_truth.key_facts[3].source` → `5.6.4`
- **B04-001** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[1]` → `Historian databases are pure IT systems with no OT considerations`
- **B04-002** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-003** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-004** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-005** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-006** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-007** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-008** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-009** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-010** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-011** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-012** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-013** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-014** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-015** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-016** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-017** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-018** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['6']`
- **B04-019** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-020** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-021** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-022** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-023** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-024** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B04-025** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['1']`
- **B05-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-002** `D-CITE-KF` (high) — CCoP clause '5.2.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.2.3`
- **B05-002** `D-CITE-KF` (high) — CCoP clause '5.2.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.2.3`
- **B05-002** `D-CITE-KF` (high) — CCoP clause '5.2.3' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.2.3`
- **B05-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-006** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['6'] vs clause_reference families ['5']`
- **B05-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-007** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['6'] vs clause_reference families ['5']`
- **B05-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-008** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['5'] vs clause_reference families ['8']`
- **B05-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-010** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['9']`
- **B05-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-011** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['9'] vs clause_reference families ['3']`
- **B05-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-012** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['5'] vs clause_reference families ['3']`
- **B05-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-014** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['3'] vs clause_reference families ['1']`
- **B05-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-016** `D-CITE-KF` (high) — CCoP clause '5.3.4' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.3.4`
- **B05-016** `D-CITE-KF` (high) — CCoP clause '5.3.4' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.3.4`
- **B05-016** `D-CITE-KF` (high) — CCoP clause '5.3.4' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.3.4`
- **B05-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-017** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['6'] vs clause_reference families ['5']`
- **B05-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-018** `D-CITE-KF` (high) — CCoP clause '5.5.5' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.5.5`
- **B05-018** `D-CITE-KF` (high) — CCoP clause '5.5.5' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.5.5`
- **B05-018** `D-CITE-KF` (high) — CCoP clause '5.5.5' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.5.5`
- **B05-018** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['5'] vs clause_reference families ['3']`
- **B05-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-019** `D-CITE-KF` (high) — CCoP clause '5.2.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.2.3`
- **B05-019** `D-CITE-KF` (high) — CCoP clause '5.2.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.2.3`
- **B05-019** `D-CITE-KF` (high) — CCoP clause '5.2.3' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.2.3`
- **B05-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-020** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['6'] vs clause_reference families ['5']`
- **B05-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-021** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['5'] vs clause_reference families ['3']`
- **B05-021** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-021** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-021** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-022** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['9']`
- **B05-022** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-022** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-022** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-023** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-023** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-023** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-024** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['3'] vs clause_reference families ['1']`
- **B05-024** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-024** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-024** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B05-025** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['2'] vs clause_reference families ['1']`
- **B05-025** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific control requirements from the cited clause`
- **B05-025** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Mandatory elements marked as critical in key_facts`
- **B05-025** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to the applicable CCoP clause`
- **B06-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-002** `D-CITE-KF` (high) — CCoP clause '5.2.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.2.3`
- **B06-002** `D-CITE-KF` (high) — CCoP clause '5.2.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.2.3`
- **B06-002** `D-CITE-KF` (high) — CCoP clause '5.2.3' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.2.3`
- **B06-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-006** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['6'] vs clause_reference families ['5']`
- **B06-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-007** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['6'] vs clause_reference families ['5']`
- **B06-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-008** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['5'] vs clause_reference families ['8']`
- **B06-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-010** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['9']`
- **B06-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-012** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['6'] vs clause_reference families ['5']`
- **B06-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-013** `D-CITE-KF` (high) — CCoP clause '5.2.5' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.2.5`
- **B06-013** `D-CITE-KF` (high) — CCoP clause '5.2.5' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.2.5`
- **B06-013** `D-CITE-KF` (high) — CCoP clause '5.2.5' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.2.5`
- **B06-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B06-020** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['3']`
- **B06-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `The security intent or objective of the control`
- **B06-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `How the control achieves its security purpose`
- **B06-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `The threat or risk the control addresses`
- **B07-001** `D-CITE-KF` (high) — CCoP clause '4.2.2' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `4.2.2`
- **B07-001** `D-CITE-KF` (high) — CCoP clause '4.2.2' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `4.2.2`
- **B07-001** `D-CITE-KF` (high) — CCoP clause '4.2.2' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `4.2.2`
- **B07-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-002** `D-CITE-KF` (high) — CCoP clause '4.2.2' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `4.2.2`
- **B07-002** `D-CITE-KF` (high) — CCoP clause '4.2.2' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `4.2.2`
- **B07-002** `D-CITE-KF` (high) — CCoP clause '4.2.2' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `4.2.2`
- **B07-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-003** `D-CITE-KF` (high) — CCoP clause '4.2.2' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `4.2.2`
- **B07-003** `D-CITE-KF` (high) — CCoP clause '4.2.2' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `4.2.2`
- **B07-003** `D-CITE-KF` (high) — CCoP clause '4.2.2' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `4.2.2`
- **B07-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-004** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['9'] vs clause_reference families ['4']`
- **B07-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-005** `D-CITE-KF` (high) — CCoP clause '4.2.2' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `4.2.2`
- **B07-005** `D-CITE-KF` (high) — CCoP clause '4.2.2' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `4.2.2`
- **B07-005** `D-CITE-KF` (high) — CCoP clause '4.2.2' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `4.2.2`
- **B07-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-006** `D-CITE-KF` (high) — CCoP clause '5.2.4' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.2.4`
- **B07-006** `D-CITE-KF` (high) — CCoP clause '5.2.4' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.2.4`
- **B07-006** `D-CITE-KF` (high) — CCoP clause '5.2.4' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.2.4`
- **B07-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-008** `D-CITE-KF` (high) — CCoP clause '5.2.4' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.2.4`
- **B07-008** `D-CITE-KF` (high) — CCoP clause '5.2.4' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.2.4`
- **B07-008** `D-CITE-KF` (high) — CCoP clause '5.2.4' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.2.4`
- **B07-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-009** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['9'] vs clause_reference families ['5']`
- **B07-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-010** `D-CITE-KF` (high) — CCoP clause '5.2.6' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.2.6`
- **B07-010** `D-CITE-KF` (high) — CCoP clause '5.2.6' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.2.6`
- **B07-010** `D-CITE-KF` (high) — CCoP clause '5.2.6' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.2.6`
- **B07-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-015** `D-CITE-KF` (high) — CCoP clause '6.3.4' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `6.3.4`
- **B07-015** `D-CITE-KF` (high) — CCoP clause '6.3.4' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `6.3.4`
- **B07-015** `D-CITE-KF` (high) — CCoP clause '6.3.4' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `6.3.4`
- **B07-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-016** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['6'] vs clause_reference families ['5']`
- **B07-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-017** `D-CITE-KF` (high) — CCoP clause '5.4.2' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.4.2`
- **B07-017** `D-CITE-KF` (high) — CCoP clause '5.4.2' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.4.2`
- **B07-017** `D-CITE-KF` (high) — CCoP clause '5.4.2' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.4.2`
- **B07-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-019** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['10'] vs clause_reference families ['5']`
- **B07-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-021** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-021** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-021** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-022** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-022** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-022** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-023** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-023** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-023** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-024** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-024** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-024** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-025** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-025** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-025** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-026** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-026** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-026** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-027** `D-CITE-KF` (high) — CCoP clause '5.2.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.2.3`
- **B07-027** `D-CITE-KF` (high) — CCoP clause '5.2.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.2.3`
- **B07-027** `D-CITE-KF` (high) — CCoP clause '5.2.3' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.2.3`
- **B07-027** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-027** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-027** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-028** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['6'] vs clause_reference families ['5']`
- **B07-028** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-028** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-028** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-029** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['9'] vs clause_reference families ['3']`
- **B07-029** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-029** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-029** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B07-030** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['5'] vs clause_reference families ['8']`
- **B07-030** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Identification of specific compliance gaps`
- **B07-030** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Reference to applicable CCoP clause`
- **B07-030** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of gap severity or risk level`
- **B08-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-021** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-021** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-021** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-022** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-022** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-022** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-023** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-023** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-023** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-024** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-024** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-024** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B08-025** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear prioritization sequence`
- **B08-025** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk-based justification for priorities`
- **B08-025** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Consideration of given constraints`
- **B09-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-021** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-021** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-021** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-022** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-022** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-022** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-023** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-023** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-023** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-024** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-024** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-024** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B09-025** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear identification of security risks or residual risks`
- **B09-025** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific context consideration`
- **B09-025** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Assessment of risk severity or implications`
- **B10-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B10-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of business risk`
- **B10-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Sector-specific impact considerations`
- **B10-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Regulatory consequence awareness`
- **B12-001** `D-CITE-KF` (high) — CCoP clause '5.2.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.2.3`
- **B12-001** `D-CITE-KF` (high) — CCoP clause '5.2.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.2.3`
- **B12-001** `D-CITE-KF` (high) — CCoP clause '5.2.3' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.2.3`
- **B12-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-002** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['9']`
- **B12-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-005** `D-CITE-KF` (high) — CCoP clause '4.2.2' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `4.2.2`
- **B12-005** `D-CITE-KF` (high) — CCoP clause '4.2.2' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `4.2.2`
- **B12-005** `D-CITE-KF` (high) — CCoP clause '4.2.2' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `4.2.2`
- **B12-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-006** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['6'] vs clause_reference families ['5']`
- **B12-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-007** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['9'] vs clause_reference families ['3']`
- **B12-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-008** `D-CITE-KF` (high) — CCoP clause '7.4.1' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `7.4.1`
- **B12-008** `D-CITE-KF` (high) — CCoP clause '7.4.1' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `7.4.1`
- **B12-008** `D-CITE-KF` (high) — CCoP clause '7.4.1' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `7.4.1`
- **B12-008** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['7'] vs clause_reference families ['8']`
- **B12-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-010** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['3']`
- **B12-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-011** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['6'] vs clause_reference families ['5']`
- **B12-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-012** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['5'] vs clause_reference families ['3']`
- **B12-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-014** `D-CITE-KF` (high) — CCoP clause '5.2.5' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.2.5`
- **B12-014** `D-CITE-KF` (high) — CCoP clause '5.2.5' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.2.5`
- **B12-014** `D-CITE-KF` (high) — CCoP clause '5.2.5' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.2.5`
- **B12-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-018** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['5'] vs clause_reference families ['3']`
- **B12-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B12-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Risk Manager preparation recommendations`
- **B12-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Evidence requirements`
- **B13-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B13-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Specific evidence types required`
- **B13-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Evidence quality considerations`
- **B14-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-021** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-021** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-021** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-022** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-022** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-022** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-023** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-023** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-023** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-024** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-024** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-024** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-025** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-025** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-025** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-026** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-026** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-026** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-027** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-027** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-027** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-028** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-028** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-028** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-029** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-029** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-029** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B14-030** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Missing: Specific remediation actions`
- **B14-030** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Missing: Feasibility assessment`
- **B14-030** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Missing: Practical implementation considerations`
- **B21-001** `D-CITE-KF` (high) — CCoP clause '5.3.2' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.3.2`
- **B21-001** `D-CITE-KF` (high) — CCoP clause '5.3.2' cited in ground_truth.key_facts[3].source but absent from clause inventory  
  · `ground_truth.key_facts[3].source` → `5.3.2`
- **B21-004** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['7'] vs clause_reference families ['9']`
- **B21-005** `D-CITE-KF` (high) — CCoP clause '9.4.1' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `9.4.1`
- **B21-005** `D-CITE-KF` (high) — CCoP clause '9.4.1' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `9.4.1`
- **B21-005** `D-CITE-KF` (high) — CCoP clause '9.4.1' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `9.4.1`
- **B21-005** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['9'] vs clause_reference families ['8']`
- **B21-009** `D-CITE-KF` (high) — CCoP clause '5.7.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.7.3`
- **B21-009** `D-CITE-KF` (high) — CCoP clause '5.7.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.7.3`
- **B21-011** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['7'] vs clause_reference families ['3']`
- **B21-012** `D-CITE-KF` (high) — CCoP clause '5.3.2' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.3.2`
- **B21-012** `D-CITE-KF` (high) — CCoP clause '5.3.2' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `5.3.2`
- **B21-013** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['6'] vs clause_reference families ['7']`
- **B21-014** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['9'] vs clause_reference families ['8']`
- **B21-016** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['7'] vs clause_reference families ['3']`
- **B21-018** `D-CITE-KF` (high) — CCoP clause '5.1.5' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `5.1.5`
- **B21-018** `D-CITE-KF` (high) — CCoP clause '5.1.5' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `5.1.5`
- **B21-019** `D-CITE-KF` (high) — CCoP clause '9.3' cited in ground_truth.key_facts[2].source but absent from clause inventory  
  · `ground_truth.key_facts[2].source` → `9.3`
- **B21-019** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['9'] vs clause_reference families ['8']`
- **B21-020** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['5'] vs clause_reference families ['3']`
- **B21-021** `D-CITE-KF` (high) — CCoP clause '4.2' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `4.2`
- **B21-021** `D-CITE-KF` (high) — CCoP clause '4.2' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `4.2`
- **B21-021** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['4'] vs clause_reference families ['3']`
- **B21-024** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['6'] vs clause_reference families ['7']`
- **B21-025** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['5'] vs clause_reference families ['3']`
- **B22-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B22-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear waiver decision (yes/no/alternative)`
- **B22-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Justification for the decision`
- **B23-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-001** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-002** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-003** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-004** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-005** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-006** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-007** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-008** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-009** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-010** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-011** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-012** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-013** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-014** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-015** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-016** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-017** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-018** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-019** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B23-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[3]` → `Clear articulation of regulatory alignment or conflict`
- **B23-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[4]` → `Coordination strategy for overlapping requirements`
- **B23-020** `D-FORBIDDEN` (heuristic) — forbidden_claims entry reads as a REQUIRED element, not a prohibited claim  
  · `fail_conditions.forbidden_claims[5]` → `Reference to specific regulatory frameworks`
- **B24-001** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-001** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-001** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-002** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-002** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-002** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-003** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-003** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-003** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-004** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-004** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-004** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-005** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-005** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-005** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-006** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-006** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-006** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-007** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-007** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-007** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-008** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-008** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-008** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-009** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-009** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-009** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-010** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-010** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-010** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-011** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-011** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-011** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-012** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-012** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-012** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-013** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-013** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-013** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-014** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-014** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-014** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-015** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-015** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-015** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-016** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-016** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-016** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-017** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-017** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-017** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-018** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-018** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-018** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-019** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-019** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-019** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-020** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-020** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-020** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-021** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-021** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-021** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-022** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-022** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-022** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['6']`
- **B24-023** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-023** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-023** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-024** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-024** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-024** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
- **B24-025** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[0].source but absent from clause inventory  
  · `ground_truth.key_facts[0].source` → `8.3`
- **B24-025** `D-CITE-KF` (high) — CCoP clause '8.3' cited in ground_truth.key_facts[1].source but absent from clause inventory  
  · `ground_truth.key_facts[1].source` → `8.3`
- **B24-025** `D-FAMILY` (high) — key_facts.source clause families are disjoint from clause_reference families  
  · `ground_truth.key_facts[*].source vs metadata.clause_reference` → `key_facts families ['8'] vs clause_reference families ['7']`
