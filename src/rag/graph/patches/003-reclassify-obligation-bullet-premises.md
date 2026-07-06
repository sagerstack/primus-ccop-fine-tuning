# Patch 003 — reclassify obligation-bullet premises (de-premise)

**Depends on:** patch 001 (premises are `:Premise` clauses).

**Problem:** the Stage-1 classifier mis-tagged enumeration sub-items of obligation
clauses as `premise/definition|scope`. They are the *fields an obligation requires*
(e.g. `CCoP-4.1.1(b)` "Name and description of each CII asset" is a field of the
CIIO's inventory obligation), not definitions. As `:Premise` they pollute the
STRONG-support pool and mint **false STRONG** hypernym mappings (the wrong
hospital-admin → CII result in B01-001).

**Fix (Option A):** de-premise them — remove the `:Premise` label + `premise_kind`
+ `premise_cu_id`. No CU is touched. The bullet reverts to a plain structural
`:Clause` under its parent obligation (exactly like `CCoP-4.1.1(i)`, which the
classifier already left un-marked). The obligation itself is represented by the
parent's actor-CU, so nothing needs to be minted.

**Rule (deterministic, structural):** a `:Premise` clause that is `HAS_CHILD` of a
clause bearing an `actor-CU`/`meta-CU` → de-premise.

## Target set — 74 clauses (verified, 0 false positives)

- All 74 are lettered enumeration bullets `(a)`,`(b)`,… (0 non-bullet entries).
- premise_kind: 44 `definition`, 29 `scope`, 1 `interpretation`.
- doc: 73 CCoP + 1 SBD.
- By parent obligation: `CCoP-3.2.1/3.2.2/3.2.4` (risk register fields), `3.5.1/3.5.2`,
  `3.8.3`, `4.1.1` (CII-asset inventory), `5.1.3/5.9.1/5.13.3/5.16.1`,
  `6.1.1/6.1.2/6.2.2` (cyber-operating-environment / logging), `7.1.1/7.1.4/7.2.2/7.3.1/7.3.3/7.3.4`,
  `SBD-5.7.2`. Full list: run the target query in 003 or the vetting script.

## Before → After manifest

| | Before | After |
|---|---|---|
| `:Premise` clauses | 430 | **356** (−74) |
| the 74 bullet clauses | `:Clause:Premise` | `:Clause` |
| hypernym fragment pool | 811 | **737** (356 premise + 381 CU) |
| ComplianceUnit nodes / edges | unchanged | unchanged |

## Post-conditions (self-checked in the .cypher)

- 0 `:Premise` clauses remain with an obligation-bearing parent
- 356 `:Premise` clauses total
- `CCoP-4.1.1(b)` is no longer `:Premise`
