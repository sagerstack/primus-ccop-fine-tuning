# PLAN — Corpus-wide ontology-guided KG (ontology_v2)

Durable copy of the plan-mode plan (originally 2026-07-08), **updated with this session's
locked decisions**. Model: **OMD-GraphRAG paper §3.1 + the POC** (`poc_reference/`). **NO
Compliance Units.** See `RESUME.md` for live status; this file is the full phase spec.

## Goal
Scale the OMD POC (B01: RtF-2.2 unreachable→rank 1; B05: 5.9.2(b)↔RtF-11.28) from hand-picked
per-question clause pools to a **blind, corpus-wide** KG: one ontology over ALL clauses,
persisted as a `:Concept` layer in Neo4j, with measured coverage + cross-doc linkage — so
retrieval works blind, corpus-wide, for every benchmark.

Two guarantees: **exhaustive coverage** (open-schema extraction + critic pass + coverage loop);
**cross-document linkage** (shared canonical `:Concept` hubs, the POC mechanism).

## Working principles (apply throughout)
- **Assume NO counts** — re-verify every number by query/measurement at runtime.
- **One document at a time**, PAUSE + report after each (no silent all-corpus batch).
- **Blind** — the extractor never sees benchmark/answer labels.

---

## Phase 0 — Data prep & cleansing  ✅ DONE
Re-extract every clause fresh from the source PDFs (nothing reused from old Neo4j). Per-doc
segmenters where the shared chunker failed (RtF `N.N`; heading-based for supplementary guides;
legal-section for the Act; SBD diagram/annex cleanup). Definitions pulled to a separate layer.
→ 869 clean clauses (`reextract/<doc>/clauses.clean.json`) + 68 definitions (`definitions/`).

## Phase 1 — Ontology S=(E,R,Φ), entities-first  ✅ LOCKED
Hand-designed by reading the whole corpus (Opus), not scripted. `corpus_ontology.json`.
- **1a Entities (E):** top-down seed (CCoP domains + 18 benchmark distinctions + glossaries)
  + bottom-up from every clause subject/object. ~123 typed entities, 8 categories, `⊑` hierarchy.
- **1b Relations (R):** ~64 typed edges, entity→entity.
- **1c Constraints (Φ):** per the paper, `Φ(r)=(dom(r),range(r))` + `IT⊥OT` disjointness +
  subsumptions. Checked post-hoc (`type_ok`). **NOT OWL/SHACL** (that was the plan's embellishment;
  dropped to stay POC/paper-faithful — can add cardinality/SHACL later if a benchmark needs it).
- Deferred: `REFERS_TO`/`CLARIFIES` clause→clause edges (no POC retrieval impact; revisit as a
  generation-time overlay).

## Phase 2 — Blind, ontology-guided extraction  🟡 IN PROGRESS
Per clause: inject S into the reader → typed triples → `type_ok` Φ-check → keep/`proposed`.
Open schema (`proposed:true` for out-of-schema = the coverage signal). Per-clause cache
(`runs/extract/`) = resumable. **DECISION: Claude Opus is the extractor** (gpt-4o-mini too weak —
free-text dumps, mis-typing, run variance); `extract.py` only validates + caches. Extraction is
**one-time**, amortized over all retrieval.
- ✅ 18 benchmark clauses extracted at Opus quality, 0 Φ-failures.
- ⬜ **Remaining ~850 clauses** — batched Opus extraction (author triples → validate → cache).

## Phase 3 — Critic pass (silent-drop defense)  ⬜
For each clause, re-read text + its extracted triples and ask "what obligation/concept/relation
did extraction MISS?" (Opus). Flag thin/zero-triple clauses with real content. Feeds Phase 6.

## Phase 4 — Hybrid entity resolution  ⬜
Fold surface forms to canonical concepts: curated synonym map (extend `extract.py` `canon`/aliases
+ POC `SYN`) for the ~50 core concepts; embedding clustering for the long tail (borderline merges
logged for review — guard IT/OT-style wrong merges).

## Phase 5 — Persist to Neo4j (additive, namespaced, droppable)  ⬜
- `(:Clause {citation_id, text, source_doc})` ← seed from `clauses.clean.json` (fresh; nothing reused).
- `(:Concept {name, type, build_id})` — one per resolved concept.
- `(:Clause)-[:INVOKES {build_id}]->(:Concept)` — the clause↔concept bridge.
- `(:Concept)-[:REL {type, build_id, citation_id}]->(:Concept)` — typed relations (tag source clause).
- Everything `build_id`-tagged → whole layer removable in one Cypher. Keep separate from any
  existing nodes.

## Phase 6 — Coverage + linkage measurement, then iterate  ⬜
- Coverage: % clauses with 0/1/≥2 valid triples; per-benchmark, do GT answer-clauses express the
  distinction? (the `proposed` rate is the direct signal.)
- Linkage: cross-doc concept bridges; verify POC bridges reproduce (CII across CCoP+Act+RtF;
  Password/PasswordLength across 5.9.2(b)↔RtF-11.28).
- Iterate: add missing E/R from critic + coverage gaps → re-extract affected clauses (cache makes
  it incremental) → repeat until ≥90% clauses ≥2 triples AND every benchmark's answer-clauses
  covered. Log residual gaps (no completeness claim).

## Verification (end state)
- Coverage report ≥90% clauses ≥2 triples; per-benchmark answer-clause coverage table.
- Linkage Cypher confirms CII/Password hubs span expected docs; POC bridges reproduce.
- E2E: honest `omd_run`-style retrieval for B01 AND B05 reading from Neo4j (not in-memory pool) —
  GT clauses still rank top-K blind, corpus-wide.
- `build_id` delete leaves the base graph intact.
