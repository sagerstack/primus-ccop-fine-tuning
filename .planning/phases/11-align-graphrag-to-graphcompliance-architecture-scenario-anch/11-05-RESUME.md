# 11-05 Resume Notes (2026-07-06)

## Status
- **11-04b COMPLETE** — 802 CUs (362 actor / 16 meta / 424 premise), 0 empty tuples, 0 subjectless actor-CUs, Act text-alignment fixed. SUMMARY + inventory written. Committed.
- **11-05 Tasks 1–3 built + committed:**
  - `refers_to_linker.py` (Task 1) — REFERS_TO edges (explicit regex + gated implicit LLM), obligation-source only, over-linking guard. Live-verified: 144 edges.
  - `policy_graph_builder.py` (Task 2) — orchestrator: scoped teardown → classify → extract → `_finalize` (ancestor-subject inheritance + doc-default actor + **subject canonicalization**) → link. Source-layer precondition (tolerance 10 textless).
  - `graph build-compliance` CLI (Task 3).
- **A rebuild via `build-compliance --drop` was running in the background** to verify reproducibility. It may or may not have finished — CHECK the graph state.

## Backup (compare target)
`.../snapshots/graph-backup-20260706.json` — 883 clauses, 802 CUs, 144 REFERS_TO. This is the pre-rebuild reference.

## NEXT STEPS on resume
1. **Check rebuild state:** `docker exec neo4j-local cypher-shell -u neo4j -p test12345 "MATCH (cu:ComplianceUnit) RETURN cu.cu_type, count(*)"` + REFERS_TO count. If partial/incomplete → resume: `cd src && poetry run ccop-eval graph build-compliance --no-drop`.
2. **Apply subject normalization** (the running build used pre-normalization code): the `_finalize` normalization is committed; re-run finalize OR run the `_NORMALIZE_SUBJECT_QUERY` map once on the graph. (Or a fresh `build-compliance --no-drop` picks it up.)
3. **Compare vs backup:** `cd src && poetry run python <scratchpad>/compare_rebuild.py <backup.json>` — check clauses=883, REFERS_TO≈144, no subject losses, type-flip count small. Categorize: minor LLM-variance = OK; disruptive shift = fix.
4. **Then 11-06** (Context Graph) is the next plan in Phase 11: 11-06 → 11-07 (Compliance Gate/retrieval) → 11-08 (reasoning) → 11-09 (mode wiring) → 11-10 (A/B eval).

## Scratchpad helpers (session-specific dir, may not persist)
compare_rebuild.py, backup_graph.py, run_link.py, dump_cus.py — reproduce trivially if gone.

## Open items
- Cross-doc REFERS_TO (deterministic doc-cue + LLM implicit) — deferred, discussed, not built.
- ~dozen object-as-subject slips (subject = "licence"/"CII"/"audit finding remediation plan") — minor, not fixed.
- Fold cross-doc + semantic `CLARIFIES` edges — deliberately deferred (user said ignore for now).
