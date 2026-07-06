# 11-05 Resume Notes (2026-07-06)

## Status
- **11-04b COMPLETE** — 802 CUs (362 actor / 16 meta / 424 premise), 0 empty tuples, 0 subjectless actor-CUs, Act text-alignment fixed. SUMMARY + inventory written. Committed.
- **11-05 Tasks 1–3 built + committed:**
  - `refers_to_linker.py` (Task 1) — REFERS_TO edges (explicit regex + gated implicit LLM), obligation-source only, over-linking guard. Live-verified: 144 edges.
  - `policy_graph_builder.py` (Task 2) — orchestrator: scoped teardown → classify → extract → `_finalize` (ancestor-subject inheritance + doc-default actor + **subject canonicalization**) → link. Source-layer precondition (tolerance 10 textless).
  - `graph build-compliance` CLI (Task 3).
- **11-05 rebuild VERIFIED COMPLETE (2026-07-06).** Background `build-compliance` finished (exit 0). Steps 1–3 below all done — see "Rebuild verification result".

## Rebuild verification result (2026-07-06)
- **Live graph:** 883 clauses, **804 CUs** (365 actor / 16 meta / 423 premise), **172 REFERS_TO** (163 actor-CU src + 9 meta-CU src).
- **Gates:** 0 subjectless actor-CUs, 0 empty tuples. ✓
- **vs backup (802 CU / 144 edges):** deltas fully explained, NOT noise —
  - LLM re-decomposed 3 Act clauses: `Act-38` premise→2 actor-CU, `Act-43` premise→3 actor-CU, `Act-41` 2→1. Net +2 CU.
  - +31/−3 REFERS_TO edges all trace to those new/removed obligation CUs (e.g. each `Act-43#n`→Act-18/22/23/6).
  - 3 type flips (`Act-19`, `SBD-5.6.2`, `SBD-6.3.1.1`, actor-CU↔premise) — minor LLM variance, within OK band.
  - meta-CU sources = 9 in BOTH backup and live → stable, not a regression.
- **Subject normalization APPLIED to live graph** (the background build ran pre-normalization code): folded 8 CUs via the committed `_NORMALIZE_SUBJECT_QUERY` map (e.g. `owner of a critical information infrastructure`→`CIIO`, `organisations`→`the organisation`). 0 variants remain; CIIO bucket 258→266.

## Backup (compare target) — STALE, NOT re-snapshotted
`.../snapshots/graph-backup-20260706.json` — 883 clauses, 802 CUs, 144 REFERS_TO. This is the PRE-rebuild reference and was **deliberately NOT rebased** after the 2026-07-06 rebuild.
- ⚠️ The live graph legitimately advanced past it (+2 CU, +28 edges, normalization). A future `build-compliance` compare against this file will show that accepted delta as false "drift" — either regenerate the snapshot first (`backup_graph.py`) or mentally subtract the delta above.

## NEXT STEPS on resume
- Steps 1–3 (check rebuild / normalize / compare) are **DONE** — see verification result above.
- **NOW: 11-06** (Context Graph) is the next plan in Phase 11: 11-06 → 11-07 (Compliance Gate/retrieval) → 11-08 (reasoning) → 11-09 (mode wiring) → 11-10 (A/B eval).

## Scratchpad helpers (session-specific dir, may not persist)
compare_rebuild.py, backup_graph.py, run_link.py, dump_cus.py — reproduce trivially if gone.

## Subject cleanup (2026-07-06, follow-up after rebuild verify)
- **Object-as-subject slips FIXED** — new `_SUBJECT_OVERRIDE` (cu_id-keyed) in `_finalize_subjects`: `audit finding remediation plan`→CIIO (CCoP-2.1.2/2.1.2(a)), `CII`→CIIO (CCoP-3.8.3/3.8.3(c)), `licence`→licensing officer (Act-28). 5 CUs.
- **Near-dup subjects FOLDED** — extended `_SUBJECT_CANONICAL`: `auditor`/`auditors`→`the auditor`, `project steering committee`→`Steering Committee`. 5 CUs.
- Result: distinct actor-CU subjects 37→31; CIIO 261→265; verified idempotent (real `_finalize_subjects` re-run = 0 changes → rebuild-safe).
- Left alone (correctly distinct SBD roles): `System Owners`, `System Administrator`, `Security Officer`.

## Open items
- Cross-doc REFERS_TO (deterministic doc-cue + LLM implicit) — deferred, discussed, not built.
- Root-cause of object-slips = extractor puts grammatical subject ("The CII shall…") in the subject slot; overrides are a targeted patch, a doc-shall→actor extraction pass is the durable fix — deferred.
- Fold cross-doc + semantic `CLARIFIES` edges — deliberately deferred (user said ignore for now).
