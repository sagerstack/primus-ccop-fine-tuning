# POC reference — OMD-GraphRAG (the thing ontology_v2 scales corpus-wide)

These three scripts are the **proof-of-concept** that justified the corpus-wide
ontology build. They are **reference only** — recovered on 2026-07-08 from session
transcripts (the originals lived in a scratchpad that did not persist). Do not
wire them into the pipeline; mirror their *patterns* (`extract`, `canon`, the
typed schema, Channel-I overlap) in the `ontology_v2` build modules.

## Files
- `omd_b01.py` — B01 applicability run (is a shared-network admin system in CCoP scope?).
- `omd_b05.py` — B05 password-requirements run (extends the schema with password/config entities).
- `omd_e2e.py` — feeds the OMD top-K clauses to primus (real `generate` node) for B01-001.

## Method (blind — extractor never sees GT labels)
1. **Pool** — hand-picked per question: GT answer clauses + real retrieval distractors. Labels used only at grading.
2. **Typed schema `S=(E,R,Φ)`** — `ENTITY_TYPES` + `RELATIONS` + `PHI` (allowed object-type per relation).
3. **Blind extraction** — per clause → LLM (`ontology_discovery_model`, OpenRouter, temp 0, `fix_invalid_json`), cached to `omd_*_ex_<cid>.json` → resumable.
4. **Entity resolution** — `canon(name,type)` folds surface forms to canonical hubs via a `SYN` map; `type_ok` enforces Φ.
5. **Entity KG** — `clause_entities[cid]` (canonical entity set) + global `rel_edges` `(subjE, rel, objE)`.
6. **Query side** — extract question entities with the same schema → `Q`; expand `Q+ = Q ∪ 1-hop(rel_edges)`.
7. **Retrieval = Channel-I overlap** — `score(cid) = 1.0·|Q∩E| + 0.5·|(Q+−Q)∩E|`. No per-question hand weights.

## Results
- **B01:** `RtF-2.2` unreachable (plain retrieval) → **rank 1** — cross-doc bridge (CCoP↔RtF↔Act via `CII`/`DigitalBoundary` hubs).
- **B05:** answers **top-3**; `CCoP-5.9.2(b)` ↔ `RtF-11.28` bridged via `Password`/`PasswordLength`/`ExternalStandard` hubs.

## The two circularities scaled away (see ../.. plan)
| POC (proven, circular) | Corpus-wide (ontology_v2) |
|---|---|
| Per-question hand-built schema (B01 ≠ B05) | One unified ontology (Phase 1, entities-first, OWL+SHACL) |
| Hand-picked 16–18-clause in-memory pools | All clauses extracted + persisted as `:Concept` layer in Neo4j (Phases 2/5) |
| Retrieval over the curated pool | Blind retrieval over the full graph (Phase 6) |
| Bridge shown for 2 questions | Coverage + linkage measured across all benchmarks |

## Note on clause text
The POC fetched clause text from the **old** `:Clause{citation_id}` nodes. ontology_v2
does NOT reuse existing Neo4j — it re-extracts every doc fresh from source PDFs
(RtF sub-clauses are re-segmented at `N.N` with role/subsection tags). The POC's
`RtF-2.2`/`RtF-11.28` were atomic answer sub-clauses linked by shared entities —
never Q&A grouping.
