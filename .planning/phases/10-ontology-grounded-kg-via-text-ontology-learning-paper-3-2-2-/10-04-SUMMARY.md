---
phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2
plan: 04
subsystem: rag
tags: [ontology, graphrag, discovery, method-b, clustering, affinity-propagation, curation-gate, lock, scikit-learn, coverage-check]

# Dependency graph
requires:
  - phase: 10-03
    provides: "Approved Method-C draft (ontology_draft.json: 20 node types + 47 relations) + D-14/D-17 coverage tooling + gate_b_reconciliation_candidates"
provides:
  - "LOCKED ontology_config.json: 24 node types + 48 relationship types + 9 patterns + function-type tags, vocabulary CLOSED (additional_*_types=false)"
  - "Method B clustering cross-check (method_b_clustering.py): fresh-corpus term extraction -> reused bge embeddings -> AffinityPropagation -> LLM-named clusters -> b_only diff vs Method C"
  - "method_b_reconcile.json: real cross-check artifact (599 terms -> 87 clusters, 71 B-only candidates, 16 corroborating clusters, 10 C types not corroborated)"
  - "lock_ontology.py: reproducible LOCK builder that re-runs D-14+D-17 coverage and refuses to lock unless both pass (Pitfall 1)"
affects: [10-05, 10-06, 10-07, clause-seeding, schema-constrained-extraction, shacl-validation]

# Tech tracking
tech-stack:
  added:
    - "scikit-learn ~1.7 (AffinityPropagation clustering; pinned to hold the Python 3.10 floor — 1.9+ requires >=3.11)"
  patterns:
    - "Method B = independent structural cross-check (clustering) against Method C (grounded synthesis), NOT a replacement — D-05"
    - "Injectable LLM seams (term extraction + cluster naming) + injectable embedder → deterministic offline unit tests over a real ML clustering pipeline"
    - "Lock-only-after-coverage-passes: the LOCK builder re-runs D-14+D-17 and SystemExits rather than lock if coverage regresses (RESEARCH Pitfall 1)"

key-files:
  created:
    - src/rag/graph/ontology/discovery/method_b_clustering.py
    - src/rag/graph/ontology/discovery/lock_ontology.py
    - src/rag/graph/ontology/method_b_reconcile.json
    - src/rag/graph/ontology/ontology_config.json
    - tests/rag/graph/ontology/test_method_b_clustering.py
  modified:
    - src/pyproject.toml  # scikit-learn dep + sklearn.* mypy ignore_missing_imports
    - src/rag/graph/ontology/discovery/coverage_check.py  # VIOLATES removed from gold-verb collapse map (gate-b SPLIT)
    - .gitignore  # committed-fixture exceptions for method_b_reconcile.json + ontology_config.json

key-decisions:
  - "Curation gate (b) resolved approve-reconciled: +4 Method-B-only node types (OperationalTechnology/ThirdParty/EssentialService/BusinessEntity) -> 24; SPLIT VIOLATES from CANNOT_SATISFY -> 48 relations; confirm 2 remaining collapses; LOCK vocabulary"
  - "Of 71 B-only candidates only 4 cleared the 'a fixed GT case structurally needs this type' bar — the rest are Control/Obligation instances or synonyms (schema-lean principle from gate a); OperationalTechnology (B04 IT/OT) was the one clear coverage gap"
  - "VIOLATES (active breach) is now DISTINCT from CANNOT_SATISFY (structural inability) — compliance-critical for B07/B03/B21; removed from the synonym collapse map so D-17 counts it honestly"
  - "10 C types not independently corroborated by B are KEPT: 7 are D-08/D-09 hand-seeded structural/function-tag abstractions that clustering cannot surface by construction; ComplianceGap/IncidentResponsePlan/MFA are genuine GT-grounded keeps"

patterns-established:
  - "Clustering cross-check as a governed second discovery lens: embed reuse (one model, D-07) + no-preset-k AffinityPropagation + per-cluster LLM naming + label/member-term overlap diff against the curated draft"
  - "Reproducible LOCK step with a coverage gate baked into the builder — the ontology cannot be locked with a coverage regression"

requirements-completed: [RAG-06, D-01, D-02, D-05, D-14, D-17]

# Metrics
duration: ~80min
completed: 2026-07-03
---

# Phase 10 Plan 04: Method-B Clustering Cross-Check → Reconcile → LOCK Ontology Summary

**A structurally-different second discovery lens (AffinityPropagation clustering over 599 fresh-extracted corpus terms) independently corroborated 10 of Method C's types and surfaced 71 B-only candidates; the human curation gate (b) reconciled these to +4 genuine additions and one VIOLATES/CANNOT_SATISFY relation split, then LOCKED a 24-node-type / 48-relation `ontology_config.json` — vocabulary closed only after re-running and passing both the D-14 benchmark-coverage and D-17 gold-relation-coverage checks.**

## Performance

- **Duration:** ~80 min (incl. a real Docling parse of 7 PDFs + a live 599-term extraction / 87-cluster-naming OpenRouter run + two human curation-gate pauses)
- **Tasks:** 3/3 (Task 1 = package-legitimacy gate; Task 3 = curation gate (b), both human-resolved)
- **Files created:** 5; modified: 4

## Accomplishments

- **Method B (clustering cross-check, D-05):** `method_b_clustering.py` extracts candidate domain terms FRESH from corpus prose (D-02 — reads only `load_ccop_corpus_texts`, never the Phase 9 emergent graph; asserted in tests), embeds each term with the SAME `SentenceTransformerEmbeddings(bge-large-en-v1.5)` used for chunk embeddings (D-07 — one embedding model, not a second), clusters with `AffinityPropagation` (no pre-set k), and LLM-names each cluster. The two LLM seams + the embedder are injectable, so the ML pipeline is unit-tested deterministically offline.
- **Real cross-check run:** 599 unique terms → 87 clusters (80 named) → **71 B-only candidates, 16 clusters corroborating 10 Method-C types, 10 C types not corroborated**. Committed as `method_b_reconcile.json` for the gate.
- **Curation gate (b) resolved (approve-reconciled)** and fully applied:
  - **+4 node types** (20 → 24): `OperationalTechnology` (B04 IT/OT boundary — the one clear coverage gap; ICS/SCADA/PLC/DCS terms), `ThirdParty` (B18 outsourcing/non-delegable responsibility), `EssentialService` (B01 scope), `BusinessEntity` (B18 legal-entity attribution).
  - **VIOLATES split** (47 → 48 relations): active breach now DISTINCT from `CANNOT_SATISFY` structural inability; removed from the gold-verb collapse map so D-17 counts it honestly. Confirmed the two remaining collapses (`MAY_REQUEST`→`APPLIES_FOR_WAIVER`, `ADDRESSES`→`MITIGATES`).
  - **Kept** `MultiFactorAuthentication` as its own type + all 10 not-corroborated C types.
- **LOCK (D-14/D-17 gated):** `lock_ontology.py` applies the gate-(b) decisions, RE-RUNS both coverage checks on the reconciled set, and writes `ontology_config.json` with `additional_node_types=false` + `additional_relationship_types=false` ONLY after both pass — it `SystemExit`s rather than lock on any regression (RESEARCH Pitfall 1).

## Coverage Re-Check (before LOCK)

| Check | Result |
|---|---|
| D-14 benchmark coverage | **18/18 benchmarks mapped**, `unmapped = []` |
| D-17 gold-relation coverage | **`unresolved_missing = []`** (9 intentionally-excluded hierarchy/junk verbs remain, as at gate a) |
| VIOLATES | present in ontology relations AND in gold_relation_types (no longer collapsed) — covered |
| Vocabulary lock | `additional_node_types=false`, `additional_relationship_types=false` |

Final locked schema: **24 node types, 48 relationship types, 9 patterns, 3 function-type tags.**

## Task Commits

1. **Task 1: scikit-learn ~1.7 (package-legitimacy gate approved)** — `e3b5392` (chore)
2. **Task 2 (RED): failing Method B tests** — `e633f1f` (test)
3. **Task 2 (GREEN): Method B clustering cross-check** — `8cf08c3` (feat)
4. **Task 2 (run): real cross-check + committed reconcile report** — `4dd21fd` (feat)
5. **Gate (b) pause marker** — `ece6752` (docs)
6. **Task 3: LOCK reconciled ontology_config.json (gate b applied)** — `4992ae6` (feat)

**Plan metadata:** (this SUMMARY + STATE/ROADMAP/REQUIREMENTS) — see final docs commit.

## Deviations from Plan

**1. [Rule 2 - Missing critical functionality] Added `lock_ontology.py` reproducible LOCK builder**
- **Found during:** Task 3.
- **Issue:** The plan named `ontology_config.json` as the artifact but no committed mechanism to produce it reproducibly with the coverage gate enforced. Hand-writing the locked JSON would lose provenance and the Pitfall-1 guard.
- **Fix:** Added `lock_ontology.py` (sibling to `method_c_synthesis.py` / `method_b_clustering.py`) that transforms draft + reconcile-report → config, re-runs D-14+D-17, and refuses to lock on coverage regression.
- **Commit:** `4992ae6`.

**2. [Rule 3 - Blocking] `*.json` gitignore blocked committing the reconcile report and the locked config**
- **Found during:** Task 2 (reconcile report) and Task 3 (config).
- **Issue:** The project-wide `*.json` ignore silently excluded both plan-mandated output artifacts (same class as the 10-03 `ontology_draft.json` issue).
- **Fix:** Added explicit `!` un-ignore exceptions for `method_b_reconcile.json` and `ontology_config.json`, matching the `ontology_draft.json` committed-fixture precedent.
- **Commits:** `4dd21fd`, `4992ae6`.

**3. Install correction (coordinator-directed):** plain `poetry add scikit-learn` resolves ^1.9.0 which requires Python >=3.11, breaking the project's 3.10 floor. Pinned `~1.7` (1.7.2 already resolved transitively); poetry.lock unchanged.

Otherwise the plan executed as written.

## Known Stubs

None. `method_b_clustering.py` ran a real pipeline (Docling parse + 599-term live extraction + AffinityPropagation + live cluster naming); `ontology_config.json` is a real locked artifact whose coverage was re-verified. `additional_*_types` are now `false` (locked, no longer permissive) — the intended terminal state after the C→curate→B→reconcile→lock sequence.

## Threat Flags

None new. The plan's two trust boundaries are handled: (1) `poetry add scikit-learn` gated behind the blocking-human legitimacy checkpoint (Task 1, T-10-04-SC); (2) corpus prose → term-extraction/cluster-naming LLM (T-10-04-01) is mitigated by curation gate (b), which reviewed every B-only candidate before any could enter the locked ontology — only 4 of 71 were admitted. Premature-lock (T-10-04-02) is mitigated by the LOCK builder's coverage gate (locks only after D-14+D-17 pass).

## For the Next Wave (10-05 clause seeder ‖ 10-06 splitter+gleaning)

- **Input:** `src/rag/graph/ontology/ontology_config.json` is the authoritative, LOCKED build-time schema. Consume `node_types` + `relationship_types` via the `schema=` kwarg, `function_type_tags` for D-09 routing, and honor `additional_*_types=false` (reject out-of-schema facts).
- **Reproducibility:** `lock_ontology.py` regenerates the config deterministically from the draft + reconcile report if the ontology ever needs re-locking.
- **The D-01 sequence (C → curate → B → reconcile → LOCK) is COMPLETE.**

## Self-Check: PASSED

- All 5 created files verified present on disk (`method_b_clustering.py`, `lock_ontology.py`, `method_b_reconcile.json`, `ontology_config.json`, `test_method_b_clustering.py`).
- All 6 task commits verified in git history (`e3b5392`, `e633f1f`, `8cf08c3`, `4dd21fd`, `ece6752`, `4992ae6`).
- 36/36 ontology unit tests pass (`pytest ../tests/rag/graph/ontology/ -m "not integration" -q`).
- Locked config re-verified: 24 node types, 48 relations, D-14 18/18, D-17 unresolved_missing=[], additional_*_types=false.

*Phase: 10-ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2*
