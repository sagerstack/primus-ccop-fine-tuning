---
description: Apply human review decisions to GT records that /gt-audit flagged as partial or needs_human. Reads the *.needs-review.jsonl files in an audit run, asks you to resolve each unresolved attribute (accept the recommendation, pick an option, or enter a custom value), writes the chosen value into the main fixed GT file, and clears the resolved review entry.
arguments:
  - name: scope
    description: "Path to an audit run dir (e.g. ground-truth/test-suite/audit-20260629-1245), 'latest' (default), or a specific test_id."
    required: false
---

You are the interactive review resolver. For records `/gt-audit` flagged `partial` or `needs_human`, you surface each unresolved attribute with its options + recommendation, take the user's decision, write the chosen value into the main GT file, and remove the resolved entry from the needs-review file. **Never invent a value — only apply what the user explicitly chooses.**

## 0. Resolve scope (from `$ARGUMENTS`, default `latest`)

- `latest` / empty → the most recent `ground-truth/test-suite/audit-*/` directory (sort by name).
- a path → that audit dir.
- a `test_id` → find the audit dir + the record containing it; resolve only that record.

## 1. Collect open reviews

Find every `*.needs-review.jsonl` in the audit dir. For each record, read `audit_review.unresolved_attributes`. If there are none open, tell the user and exit.

## 2. Present each unresolved attribute, then confirm (yes/no)

For each unresolved attribute, FIRST print a context block so the reviewer decides on the evidence, not a bare label. Show, in order:

1. **Question** — the record's `input.question`, verbatim.
2. **Answer** — the record's `ground_truth.expected_response`, verbatim (a faithful excerpt if very long).
3. **Contentious attribute** — the attribute path, its `current` (invalid) value, and a plain-English explanation of **why** it is contested (from `reason`): what is wrong and what the disagreement is.
4. **Proposed resolution** — the `recommendation`. If it points to a clause, **cite it: quote the clause's verbatim text** from `gt-audit/context/*.txt` (or the CCoP PDF) so the reviewer sees exactly what they are endorsing.

THEN ask with **AskUserQuestion** a simple confirmation:
- `header`: the attribute label (e.g. `key_facts[1]`).
- `question`: "Apply the recommended fix — set `<attribute>` to `<recommendation>`?"
- `options`: **"Yes — apply `<recommendation>`"** and **"No"**. (The harness adds an "Other" choice for a custom value.)
- If the user picks **No**, follow up by offering the remaining `options` (plus "Other"); if they still decline, leave the attribute **open (deferred)** — do not write anything.

Present one attribute's context block, then its confirmation, before moving to the next (do not bury the evidence under a batch of questions).

## 3. Apply decisions (deterministic — no loose hand-editing)

Map the confirmation to a value:
- **Yes** → the `recommendation`.
- A chosen alternative `option` → that option's value.
- **Other** → the user's exact text, verbatim.
- **No / deferred** → apply nothing; leave the attribute open.

For each value to apply, set it at its path (e.g. `key_facts[1].source`, or `metadata.clause_reference`) for that `test_id` in the **main** file `<benchmark>.jsonl`. Apply with a precise Python step: read the jsonl, locate the line whose `test_id` matches, set the field by its path, rewrite that line.

## 4. Clean up the review file

- Remove the resolved attribute from that record's `audit_review.unresolved_attributes` in the `.needs-review.jsonl`.
- If a record has **no remaining** unresolved attributes, remove the whole record from the needs-review file.
- If the `.needs-review.jsonl` becomes empty, delete it.

## 5. Update status

- In `gt-audit/reports/<id>.json`, flip `check_status` `partial → fixed` once a record's reviews are all resolved (leave `needs_human` if the user explicitly defers).
- Refresh `by_status` counts in `gt-audit/audit_summary.json`.

## 6. Report

Print: attributes resolved this session, records now **fully fixed**, records with reviews **still open** (deferred), and the path to the updated GT dir.

## Guardrails

- Only the **main** `<benchmark>.jsonl` in the audit dir is edited with chosen values. The pristine originals under `ground-truth/test-suite/*.jsonl` (non-audit) are **never** touched.
- Apply only user-confirmed values; if the user skips/defers an attribute, leave it open.
- Idempotent: re-running surfaces only still-open reviews.
