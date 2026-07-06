# Patch 006 — backfill + atomize Cybersecurity Act 2018 s.2(1) definitions

**Depends on:** patch 001. The graph's `Act-2` node is a **truncated blob** with only
3 of the ~27 s.2 defined terms; the rest were **missing from the graph**. This
backfills all 27 as `:Clause:Premise` children of `Act-2` (sourced from the Act PDF,
extracted programmatically — not hand-typed), then de-premises the `Act-2` blob.

The 27 terms are the Act **s.2(1)** interpretation set (the earlier "35" count
included terms defined in *later* Act sections, not s.2).

## Scope decision (user chose "all")

All 27 s.2(1) definitions, including admin/role terms. `computer service` uses
"includes" (kept verbatim); `owner` keeps its ", in relation to a CII," qualifier.
Curly quotes/apostrophes normalized to straight.

## Dedup note

`Act-2#critical-information-infrastructure` is the **authoritative thin s.2 wording**
("a computer or computer system in respect of which a designation under s.7(1) is in
effect"). It **coexists** with `CCoP-1.2.1#CII` (the resolved s.2+s.7(1) version from
patch 002). Both are legitimate (different provenance); the resolved one is richer for
retrieval, the s.2 one is the exact statutory text.

## Before → After manifest

| | Before | After |
|---|---|---|
| `:Premise` clauses | 367 | **393** (+27 terms, −1 parent) |
| new `Act-2#<slug>` nodes | 0 | 27 |
| `Act-2` label | `:Clause:Premise` (truncated blob) | `:Clause` |
| `HAS_CHILD` under Act-2 | (existing) | +27 |
| fragment pool | 748 | **775** |
| ComplianceUnit / clauses count | unchanged | unchanged |

## Post-conditions (self-checked)

- 27 `:Premise` children under `Act-2`, each `premise_kind='definition'`
- `Act-2` no longer `:Premise`
- `Act-2#essential-service` present (the term the CII definition hinges on)
