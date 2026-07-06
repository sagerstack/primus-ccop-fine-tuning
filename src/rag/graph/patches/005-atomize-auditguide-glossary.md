# Patch 005 — atomize Auditing Guidelines glossary + de-dup its copies

**Depends on:** patch 001. Atomize the 10 audit glossary terms (section 8) under
`AuditGuide-8`, de-premise that parent, and de-premise the 5 duplicate copies
(`AuditGuide-1..5`) that the chunking bug filled with the same glossary text.

## Editorial notes (fidelity — more judgment here than the CCoP tables)

- `'term' means …` reframing (patch-002 style).
- **Dropped internal cross-ref markers** `(SN 8.2)` / `(SN 8.3)` from the definitions.
- **Stripped redundant term-repetition** where a cell restated the term
  (e.g. "Audit evidence refers to records…" → "'Audit evidence' means records…";
  "Adequacy refers to whether…" → "'Adequacy of control' means whether…").
- `Compensating control` sub-points (a)/(b)/(c) kept inline; "rigor"→"rigour",
  and "Commensurate…" → "be commensurate…" for grammaticality.

## Duplication note

`AuditGuide-1..5` are sections 1–5 whose real content was overwritten with the
section-8 glossary (chunking bug). This patch **de-premises** them (removes the
duplicate glossary from the retrieval pool); their **real content is lost** and
awaits the source re-chunk (#1). Only their labels change here — nodes/edges kept.

## Before → After manifest

| | Before | After |
|---|---|---|
| `:Premise` clauses | 363 | **367** (+10 terms, −1 parent, −5 dup copies) |
| new `AuditGuide-8#<slug>` nodes | 0 | 10 |
| `AuditGuide-8` label | `:Clause:Premise` blob | `:Clause` |
| `AuditGuide-1..5` labels | `:Clause:Premise` (dup blob) | `:Clause` |
| fragment pool | 744 | **748** (367 premise + 381 CU) |

## Post-conditions (self-checked)

- 10 `:Premise` children under `AuditGuide-8`
- `AuditGuide-8` and `AuditGuide-1..5` are no longer `:Premise`
