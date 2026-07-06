# Patch 002 — atomize CCoP-1.2.1 definitions (incl. the resolved CII definition)

**Depends on:** patch 001 (premises are `:Premise` clauses).

**What:** split the fused 8-term `CCoP-1.2.1` definitions blob into 8 atomic
`:Clause:Premise` term nodes (children of `CCoP-1.2.1`), then de-premise the
parent blob so it stops competing in retrieval. Content: `002-*.json`.

- 6 terms verbatim from CCoP-1.2.1 (Act, BCP, Commissioner, CII asset, CII Designation Date, Code).
- **CII resolved** from Cybersecurity Act 2018 s.2 read with s.7(1) — the table only said
  "As defined in section 2 of the Act"; the operative test (necessary for an essential service;
  debilitating-if-lost; located in Singapore) is now inline.
- **CIIO enriched** with the Act s.2 "owner" definition.

## Why atomize all 8 (not just the 3 core)

You can't cleanly de-premise the parent blob while it still holds un-atomized terms — the
blob's CII row would keep competing with the atomized CII. So the whole table is atomized in
one patch to reach a clean state (no partial duplication).

## Before → After manifest

| | Before | After |
|---|---|---|
| `:Premise` clauses | 423 | **430** (+8 new terms, −1 parent de-premised) |
| new term nodes (`CCoP-1.2.1#<slug>`) | 0 | 8 |
| `CCoP-1.2.1` label | `:Clause:Premise` | `:Clause` (de-premised; keeps text + 8 children) |
| `HAS_CHILD` under CCoP-1.2.1 | 0 | 8 |
| hypernym fragment pool | 804 | **811** (430 premise + 381 CU) |
| ComplianceUnit / actor / meta / clauses | unchanged | unchanged |

New node shape (each term): `:Clause:Premise`, `premise_kind='definition'`,
`function_type='DefinitionClause'`, `doc_class='binding'`, `source_doc='CCoP 2.0'`,
`citation_id='CCoP-1.2.1#<slug>'`, `HAS_CHILD` from `CCoP-1.2.1`.

## Post-conditions (self-checked by the .py)

- 8 `:Premise` children under `CCoP-1.2.1`, each `premise_kind='definition'`
- `CCoP-1.2.1` is no longer `:Premise`
- `CCoP-1.2.1#CII` text contains "section 7(1)" (resolution landed)

## Note

Does NOT touch the OTHER definition blobs (`CCoP-10.1.2`, `Act-2`, AuditGuide glossary) or the
missing Act §2 terms — those are later patches (P2). This patch makes the CII/CIIO family clean,
which is what B01-001 needs.
