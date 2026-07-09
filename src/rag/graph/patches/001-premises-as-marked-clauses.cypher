// Patch 001 — premises become marked clauses (GraphCompliance Alg. 1 alignment)
// Idempotent: after it runs there are no premise CUs, so a re-run matches nothing.
// See 001-premises-as-marked-clauses.md for rationale + manifest.

// 1) stamp each premise's clause with the mark, then remove the separate premise CU
MATCH (p:ComplianceUnit {cu_type:'premise'})-[:FROM_CLAUSE]->(c:Clause)
SET c:Premise,
    c.premise_kind  = p.premise_kind,
    c.premise_cu_id = p.cu_id
DETACH DELETE p;

// 2) post-conditions (each RETURN should show the expected value)
MATCH (p:ComplianceUnit {cu_type:'premise'})            RETURN 'premise_cus_remaining' AS check, count(p) AS value   // expect 0
UNION ALL
MATCH (c:Clause:Premise)                                RETURN 'premise_marked_clauses' AS check, count(c) AS value  // expect 423
UNION ALL
MATCH (c:Clause:Premise) WHERE c.premise_kind IS NULL   RETURN 'marked_missing_kind'   AS check, count(c) AS value   // expect 0
UNION ALL
MATCH (cu:ComplianceUnit)                               RETURN 'compliance_units_total' AS check, count(cu) AS value // expect 381
;
