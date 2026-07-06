// Patch 003 — reclassify obligation-bullet premises (Option A: de-premise only)
//
// Rule: a :Premise clause that is HAS_CHILD of a clause bearing an obligation CU
// (actor-CU/meta-CU) is a mis-tagged enumeration sub-item of that obligation,
// NOT a definition. Remove the :Premise mark (+ premise_kind, premise_cu_id).
// No CU is created, modified, or deleted; only the bullet clause's labels change.
// Verified: 74 clauses, all lettered bullets, 0 non-bullet false positives.
//
// Idempotent: after running, no :Premise clause has an obligation-bearing parent,
// so a re-run matches nothing.

MATCH (parent:Clause)-[:HAS_CHILD]->(c:Clause:Premise)
MATCH (parent)<-[:FROM_CLAUSE]-(pcu:ComplianceUnit)
WHERE pcu.cu_type IN ['actor-CU', 'meta-CU']
REMOVE c:Premise, c.premise_kind, c.premise_cu_id;

// post-conditions
MATCH (parent:Clause)-[:HAS_CHILD]->(c:Clause:Premise)
MATCH (parent)<-[:FROM_CLAUSE]-(pcu:ComplianceUnit) WHERE pcu.cu_type IN ['actor-CU','meta-CU']
RETURN 'obligation_bullet_premises_remaining' AS check, count(DISTINCT c) AS value  // expect 0
UNION ALL
MATCH (c:Clause:Premise) RETURN 'premise_clauses_total' AS check, count(c) AS value // expect 356
UNION ALL
MATCH (c:Clause {citation_id:'CCoP-4.1.1(b)'}) RETURN 'sample_4_1_1_b_still_premise' AS check,
  CASE WHEN c:Premise THEN 1 ELSE 0 END AS value                                    // expect 0
;
