# Patch 004 — atomize CCoP-10.1.2 OT/ICS definitions

**Depends on:** patch 001. **Same operation as patch 002**, applied to the second
CCoP definitions blob (`CCoP-10.1.2`, the OT/ICS glossary).

Split the fused 8-term blob into 8 atomic `:Clause:Premise` term children of
`CCoP-10.1.2`, then de-premise the parent. All 8 are verbatim from the table,
reframed as `'term' means …` sentences (the framing approved for patch 002).

Terms: alert suppression, fail-safe, field controller, interlock, physical process,
programme code, register block, Safety Instrumented System.

## Editorial notes (fidelity)

- `'term' means …` reframing (as in patch 002).
- **Articles added** to 2 bare-noun cells for grammaticality: `field controller`
  (+"an"), `interlock` (+"a").
- **Source typo fixed:** `register block` cell reads "Atemporary" → "a temporary".

## Before → After manifest

| | Before | After |
|---|---|---|
| `:Premise` clauses | 356 | **363** (+8 terms, −1 parent de-premised) |
| new `CCoP-10.1.2#<slug>` nodes | 0 | 8 |
| `CCoP-10.1.2` label | `:Clause:Premise` (blob) | `:Clause` (de-premised) |
| `HAS_CHILD` under CCoP-10.1.2 | (existing) | +8 |
| hypernym fragment pool | 737 | **744** |
| ComplianceUnit / clauses count | unchanged | unchanged |

## Post-conditions (self-checked by the .py)

- 8 `:Premise` children under `CCoP-10.1.2`, each `premise_kind='definition'`
- `CCoP-10.1.2` is no longer `:Premise`
