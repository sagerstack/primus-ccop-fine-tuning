# Audit Verifier Summary

_Generated: 2026-04-30_

## Scope

This verifier pass is now exhaustive for the **582 audited defects** in `audit_defects.json`.

It also retains the previously identified **8 additional `MISSED_BY_AUDITOR`** findings from the NO_DEFECT sample review.

## §11 Conflict Resolution

Resolved from the authoritative CCoP PDF table of contents and body text: **§11 does exist**. Its title is **Domain-Specific Practices**, and page 61 contains `11.1 Application of this Section`, `11.1.1` (scope limited to internet-facing DNS servers), `11.2 Domain Name System Security Extension (DNSSEC)`, `11.2.1`, and `11.2.2`.

Verifier conclusion:
- Auditor E was wrong to say CCoP 2.0 ends at Chapter 10.
- Auditor F was right that §11 is DNSSEC/domain-specific practice content, so using “CCoP Section 11” as the waiver chapter in B22 is still wrong.

## Exhaustive Decision Totals

- Audited defects reviewed: 582
- `APPROVED`: 442
- `REJECTED_FALSE_POSITIVE`: 62
- `REJECTED_BAD_FIX`: 78
- Extra `MISSED_BY_AUDITOR` findings retained: 8

### Per-Benchmark Totals

| Benchmark | Approved | False Positive | Bad Fix | Total |
|---|---:|---:|---:|---:|
| B01 | 12 | 4 | 3 | 19 |
| B02 | 27 | 0 | 1 | 28 |
| B03 | 8 | 10 | 1 | 19 |
| B04 | 24 | 0 | 0 | 24 |
| B05 | 18 | 0 | 8 | 26 |
| B06 | 19 | 0 | 0 | 19 |
| B07 | 22 | 2 | 0 | 24 |
| B08 | 25 | 0 | 0 | 25 |
| B10 | 40 | 0 | 0 | 40 |
| B12 | 18 | 1 | 4 | 23 |
| B13 | 55 | 0 | 0 | 55 |
| B14 | 56 | 0 | 4 | 60 |
| B18 | 51 | 0 | 1 | 52 |
| B21 | 21 | 0 | 1 | 22 |
| B22 | 21 | 20 | 0 | 41 |
| B23 | 20 | 0 | 20 | 40 |
| B24 | 5 | 25 | 35 | 65 |

## Exhaustive Findings

- `B10`: The systemic wrong-chapter claim holds across the benchmark. Rows currently anchored to §8 / §8.1 for non-resiliency topics should be updated.
- `B13`: The fabricated source title `CIIO Audit Evidence Requirements` and the fabricated `30 days before audit submission` rule are systemic GT defects. The approved auditor replacements are broadly safe to apply.
- `B14`: The current GT repeatedly uses §6.1.1 / section 6 for remediation rows. Most auditor corrections are directionally right, but a small subset still needs rewrite before apply.
- `B18`: The current GT repeatedly uses §8.1.1 / section 8 for governance and responsibility-attribution rows. Most clause/section corrections are safe to apply.
- `B22`: The real defect is the Expected Response misattribution to `CCoP Section 11`, not the legal citation `Cybersecurity Act §11(7)` itself. The D1 format-mismatch family should not be applied as GT defect corrections.
- `B23`: The benchmark genuinely contains out-of-scope cross-regulator synthesis, but the auditor's D2 fix family is not applyable as written. Those rows need rewritten replacement text, not meta guidance.
- `B24`: The benchmark genuinely contains fabricated Chapter 8/9 references and out-of-corpus incident-form/timing claims, but much of the auditor output is still only a mapping memo or editorial note. Those rows need rewritten final values.

## Action Items For GT Update

### 1. Safe To Apply As-Is

- Apply the `442` rows marked `APPROVED` in `audit_verifier_decisions.json`.
- Highest-volume safe families are B10 wrong-chapter fixes, B13 fabricated-source/timeline removals, most B14 section fixes, and most B18 governance/responsibility fixes.
- The B08 incident-classification-reference cleanup remains safe to apply across the family.

### 2. Rewrite Before Apply

- `78` rows are real defects but need rewritten GT values before any apply step.
- Rewrite concentrations:
- `B23 D2 family`: 20
- `B24 D4 family`: 20
- `B24 D2 family`: 15
- `B05`: 8
- `B12`: 4
- `B14`: 4
- `B01`: 3
- `B02`: 1
- `B03`: 1
- `B18`: 1
- `B21`: 1

- Use the concrete sampled replacement patterns already recorded in `audit_verifier_decisions.json` for B23, B24, B05, B14, and B18. Extend those patterns to the same family members rather than auto-applying the current auditor text.

### 3. Do Not Apply

- `62` rows should not be applied as defect corrections.
- These are primarily index-granularity or citation-format complaints where the underlying GT statement is still substantively accurate in the authoritative PDF/Act.
- Main false-positive concentrations:
- `B24 D1 family`: 25
- `B22 D1 family`: 20
- `B03`: 10
- `B01`: 4
- `B07`: 2
- `B12`: 1

### 4. Additional GT Work Outside Auditor Inventory

- Preserve and fix the `8` extra `MISSED_BY_AUDITOR` findings already recorded in the decisions file.
- The biggest non-auditor issue remains sector-metadata inconsistency in B09 plus a few missed clause/reference defects in B03 and B07.

## Highest-Risk Rewrite Families

- `B23 D2 family`: Replace editorial “either/or” guidance with direct CCoP-grounded responses that explicitly state multi-regulator coordination is outside the current CCoP corpus and use §1.6 / §3.2.1 only for conflict handling.
- `B24 D2 family`: Replace fabricated `8.3-8.7` / `9.4-9.5` references with final Chapter 7/8 grounded answers, not mapping notes.
- `B24 D4 family`: Remove unsupported Form A1/A2 labels and hour-count reporting timelines; use Act §14 + CCoP §7.1.1(b) prescribed-form/prescribed-period wording only.
- `B05` row-specific bad fixes: Re-ground vulnerability, penetration-testing, and compliance-date rows to the verified Chapter 5 clause family already used elsewhere in the audit.
- `B12` row-specific bad fixes: Remove placeholder clause numbers such as `5.10.x`, `11.x`, and `2.x` before applying any fix.

## Extra Missed Defects Retained

- `B03-030-M1` (B03-030, auditor_B03): Expected Response asserts that CCoP itself contains CSA-specific incident-reporting forms and timelines. Those specifics are not in CCoP 2.0; §7.1.1(b) only requires the IR plan to comply with reporting obligations under the Act and other laws.
- `B07-007-M1` (B07-007, auditor_B07): Key facts cite a non-existent clause (5.2.5), and the expected response contains a text artifact (review周期). The real review cadence clause is §5.2.2.
- `B07-018-M1` (B07-018, auditor_B07): Key facts cite a non-existent clause (5.4.4). The actual remote-access requirements are in §5.7.1, §5.7.2, and OT credential separation is in §10.2.3.
- `B09-001-M1` (B09-001, auditor_B09): Row is not internally consistent. The question and reasoning use a banking context, but input.scenario_sector is set to energy.
- `B09-003-M1` (B09-003, auditor_B09): Row is not internally consistent. The question/reasoning/key-fact sources are healthcare-specific, but input.scenario_sector is set to energy.
- `B09-009-M1` (B09-009, auditor_B09): Row is not internally consistent. The question/reasoning/key-fact sources are healthcare-specific, but input.scenario_sector is set to energy.
- `B09-010-M1` (B09-010, auditor_B09): Row is not internally consistent. The reasoning chain and key-fact sources use a water-sector context, but input.scenario_sector is set to energy.
- `B09-020-M1` (B09-020, auditor_B09): Row is not internally consistent. The reasoning chain and key-fact sources use a transportation context, but input.scenario_sector is set to energy.

## Final Recommendation

- Update GT in three passes: first apply all `APPROVED` rows, then rewrite and apply the `REJECTED_BAD_FIX` rows by family, then leave `REJECTED_FALSE_POSITIVE` rows untouched.
- Keep the 8 `MISSED_BY_AUDITOR` items in the GT backlog even though they were outside the 582-defect auditor inventory.
- Use `audit_verifier_decisions.json` as the row-level action ledger. It is now exhaustive for the audited defect set plus the retained extra misses.
