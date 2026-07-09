---
description: Audit CCoP ground-truth records against the official CCoP source documents using grounded subagents (verify → fix-check → critic → batch-critic). Produces a fixed GT and a per-record status report under gt-audit/.
arguments:
  - name: scope
    description: "'--pilot' (the 18 stratified records), '--all' (all 435), or a single test_id like 'B07-006'"
    required: false
---

Orchestrate a grounded, multi-agent audit of CCoP ground-truth records. You are the conductor: you loop over records, spawn the subagents to do the judgment, and write the deliverables. Subagents judge; you write files. Never modify anything under `ground-truth/test-suite/` — all output goes to a new tree under `gt-audit/`.

## 0. Resolve scope (from `$ARGUMENTS`, default `--pilot`)

- `--pilot` → the 18 test_ids in `gt-audit/inputs/pilot_18.txt`.
- `<test_id>` (e.g. `B07-006`) → just that one.
- `--all` → every record in `ground-truth/test-suite/*.jsonl`. **Prerequisite:** an input file `gt-audit/inputs/<id>.json` must exist for each (record + Stage-1 `deterministic_flags`). If missing, generate them first from `ground-truth/test-suite/` + `docs/project_notes/gt_audit_2026-04-28/stage1_defect_ledger.json`, then proceed.

**Run output directory (self-contained, fresh per run):** each invocation creates its OWN new timestamped tree `ground-truth/test-suite/audit-<YYYYMMDD-HHMM>/` (use `date +%Y%m%d-%H%M`) and writes EVERYTHING for the run inside it:
```
audit-<ts>/
├── <benchmark>.jsonl              # fixed GT
├── <benchmark>.needs-review.jsonl
├── reports/<id>.json             # per-record status
└── audit_summary.json            # roll-up
```
Do NOT reuse a previous run's dir. **The original `ground-truth/test-suite/*.jsonl` files are never modified.**

**Resume:** to continue an interrupted run instead of starting fresh, pass `--resume <audit-dir>`; write into that existing dir and skip any `<id>` that already has `<audit-dir>/reports/<id>.json`. Report how many were skipped. Without `--resume`, always mint a new dir.

**Output filename convention:** a record's output file uses the **same basename as the source test-suite file that contains its `test_id`** (e.g. `B07-006` → `b07_gap_identification_quality.jsonl`). Determine it by finding which `ground-truth/test-suite/*.jsonl` holds the `test_id`.

## 1. Per record (process in small parallel batches, e.g. 4–6 at a time)

For each `<id>`:

1. **Verify** — spawn the `gt-verifier` subagent (Task tool, `subagent_type: gt-verifier`) with the `test_id`. Parse its JSON report.
2. **Fix-check** — for every attribute whose `status == "fail"`, spawn `gt-fix-checker` with the `test_id`, the `attribute` name, and the `issue` text **only** — do NOT pass the verifier's `proposed_fix` (the checker must be blind). Collect each verdict and compare its `independently_derived_value` to the verifier's `proposed_fix` → mark `agree` / `disagree`.
3. **Critic** — spawn `gt-critic` with the original record, the verifier report, and the fix-checker verdicts. Parse its JSON critique (per-attribute `attribute_decisions` + `record_status`).
4. **Apply fixes per attribute (partial-fix):** build the output record by starting from the original and, for each `attribute_decisions` entry with `resolution == "apply"`, applying its `final_value`. Entries with `resolution == "review"` are **left at their original value** and recorded for human review. The record's status is the critic's `record_status` (`pass | fixed | partial | needs_human`).
5. **Write the per-record status report** → `gt-audit/reports/<id>.json`:
   ```json
   {
     "test_id": "...", "benchmark": "...",
     "check_status": "pass|fixed|partial|needs_human",
     "attributes": { "<name>": {"status": "...", "issue": "...", "resolution": "apply|review", "fix": "..."}, ... },
     "fix_checks": [{"attribute": "...", "agree": true, "derived": "..."}],
     "remarks": "..."
   }
   ```
6. **Write the new GT** into the run's timestamped dir, filename = the source basename (see Output filename convention). **Append** each record to its benchmark file (a benchmark accumulates all its audited records):
   - **`audit-<ts>/<benchmark_file>.jsonl`** — every audited record with all `apply` fixes applied. This is the new, corrected GT. (`pass` records are copied verbatim.)
   - **`audit-<ts>/<benchmark_file>.needs-review.jsonl`** — ALSO write the record here **iff** `record_status` is `partial` or `needs_human`. Same record format, plus one extra attribute:
     ```json
     "audit_review": {
       "status": "partial|needs_human",
       "unresolved_attributes": [
         {"attribute": "key_facts", "options": ["5.2.1(c)", "5.2.1(d)"], "recommendation": "5.2.1(d)", "reason": "..."}
       ],
       "commentary": "what a human needs to decide and why"
     }
     ```
   So a `partial` record appears in **both** files: the main file carries the confident fixes; the needs-review file carries the same record plus the `audit_review` commentary for the unresolved attributes.

## 2. After all records — batch critic

Spawn `gt-batch-critic` once. Then write `gt-audit/audit_summary.json`:

```json
{
  "generated_at": "...", "scope": "...", "output_dir": "ground-truth/test-suite/audit-<ts>/", "records_audited": 0,
  "by_status": {"pass": 0, "fixed": 0, "partial": 0, "needs_human": 0},
  "attribute_fail_counts": {"clause_reference": 0, "expected_response": 0, "key_facts": 0, "reasoning_chain": 0, "question": 0},
  "needs_review": ["<id>", ...],
  "batch_critique": { }
}
```

## 3. Validate against known truths (pilot only)

After a `--pilot` run, sanity-check the output against facts we already established, and flag any miss prominently:
- **B07-006** → clause anchor should resolve to **§4.1.1** (Asset Management), not §3.2.2/§4.2.2.
- **B21-001** → the `5.9.7` mention is a hallucination TRAP; the expected_response *correctly* says it does not exist — must NOT be "fixed" into existence.
- **B24-001** → `§8.3` does not exist; the reporting-timeline content is in the Cybersecurity Act, not CCoP §8.3.
- **B05-001 vs B06-001** → the batch critic should surface their password-complexity contradiction.

## 4. Final report to the user

Print: records audited / skipped, the `by_status` counts (pass/fixed/partial/needs_human), the list of records needing review, the path to the new GT dir `ground-truth/test-suite/audit-<ts>/`, any known-truth validation misses, and the path to `gt-audit/audit_summary.json`. Do not claim a record is fully fixed if any of its attributes were routed to `review`.

## Guardrails

- Subagents are grounded in the CCoP documents and must quote clause text; if a subagent returns an ungrounded verdict, treat it as `needs_human`.
- Originals in `ground-truth/test-suite/` are read-only. All writes go under `gt-audit/`.
- Resumable and idempotent: re-running continues where it stopped and never overwrites an existing report unless explicitly asked.
