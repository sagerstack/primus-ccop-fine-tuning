# ontology_v2 — RESUME (2026-07-08)

Corpus-wide OMD-GraphRAG KG build. **Strictly the POC (`poc_reference/omd_b01.py`,
`omd_b05.py`) + the OMD-GraphRAG paper (`../../../../research/graphcompliance/omd-graphrag.pdf`,
§3.1). NO Compliance Units** (that was the Phase-11 approach — explicitly out).

## Where we are

| Phase | Status | Artifact |
|---|---|---|
| **0 — corpus re-extraction** | ✅ DONE | `reextract/<doc>/clauses.clean.json` — **869 clauses**, 7 docs, fresh from source PDFs (nothing reused from old Neo4j) |
| **0 — definitions** | ✅ DONE | `definitions/*.json` — **68 terms** (CCoP glossary, Auditing §8, SBD Annex C) |
| **1 — ontology S=(E,R,Φ)** | ✅ LOCKED | `corpus_ontology.json` — **~123 entity types, ~64 relations, Φ domain/range, 30 subsumptions, IT⊥OT** + `ONTOLOGY-P1a-entities.md`, `ONTOLOGY-P1b-relations.md` |
| **2 — extraction** | 🟡 VALIDATED + 18 benchmark clauses done | `runs/extract/*.json` per-clause cache |
| 3 critic / 4 resolution / 5 Neo4j / 6 coverage | ⬜ not started | — |

## The KEY decision (this session): Opus does the extraction, not gpt-4o-mini

Phase 2 = turn each clause into typed triples. The plan used `settings.ontology_discovery_model`
= **`gpt-4o-mini`** — validated on B01/B05, but the 15-benchmark sweep showed it's **too weak**:
dumps whole clause sentences as free-text nodes on list-heavy clauses, mis-types entities,
varies run-to-run. **The ontology was designed by Opus (high quality); the graph must be built to
the same standard.** So: **Claude Opus reads each clause and emits the triples; `extract.py` only
validates against Φ (`type_ok`) + caches.** No API/gpt-4o-mini for the reasoning.

Proven: all 4 clauses gpt-4o-mini failed (5.2.1, 2.1.2, 7.1.1, 7.1.2) → clean, 100% Φ-valid when
Opus extracts. **All 18 benchmark clauses extracted at Opus quality, 0 Φ-failures** (cached with
`"extractor": "claude-opus"`).

Extraction is **one-time** (build graph once → retrieval reuses forever). Per-clause cache =
resumable/incremental. Worth Opus quality because amortized over all future queries.

## NEXT (new session)

1. **Extract the remaining ~850 non-benchmark clauses at Opus quality** — batched (~20–40/turn),
   Opus authors triples, `type_ok` validates, write to `runs/extract/`. Resumable via cache.
   Method demonstrated in the 2026-07-08 transcript (author triples dict → validate → cache).
2. **Phase 3 — critic pass**: re-check each clause for missed triples (Opus).
3. **Phase 4 — entity resolution**: canon/alias fold surface forms → canonical concepts.
4. **Phase 5 — Neo4j persist**: seed `:Clause` (from `clauses.clean.json`) + `:Concept` +
   `:Clause-[:INVOKES]->:Concept` + `:Concept-[:REL]->:Concept`, tagged `build_id` (droppable).
5. **Phase 6 — coverage/linkage measurement** + iterate.

## How retrieval will work (POC Channel-I)
Query → concepts Q → Q⁺ = Q ∪ 1-hop over `:REL` → score clauses by
`|Q ∩ INVOKES(clause)| + 0.5·|(Q⁺−Q) ∩ INVOKES(clause)|`. Cross-doc bridge = shared concept hubs
(e.g. B01 via CII/DigitalBoundary; B05 via Password/PasswordLength `ATTRIBUTE_OF`).

## Files
- **Code:** `reextract_doc.py` (P0 parse), `apply_clean.py` (P0 clean rules per doc),
  `rtf_segmenter.py` / `heading_segmenter.py` / `act_segmenter.py` / `sbd_clean.py` (doc-specific
  segmenters), `extract.py` (P2 extractor: schema-inject + `type_ok` + `canon` + free-text guard),
  `_neo.py`.
- **Schema:** `corpus_ontology.json` (LOCKED), `ONTOLOGY-P1a/1b-*.md`.
- **Corpus:** `reextract/<doc>/clauses.clean.json`; **Defs:** `definitions/*.json`.
- **Cache:** `runs/extract/*.json` (per-clause; 18 benchmark clauses = Opus, others = gpt-4o-mini test runs — re-do those as Opus).
- **POC reference:** `poc_reference/` (omd_b01/b05/e2e + README).

## Gotchas
- Run Python via `poetry run` from `src/` (Poetry only). `uv run` wipes `.venv`.
- `*.json` is globally gitignored — ontology_v2 artifacts were force-added (`git add -f`).
- Neo4j: local docker `neo4j-local`, password in `src/config/.env.local` (`CCOP_NEO4J_PASSWORD`).
- gpt-4o-mini test extractions in `runs/extract/` for the 15 non-anchor benchmarks were the WEAK
  ones; the 18-benchmark Opus re-do overwrote the anchors. Treat non-benchmark cache as TODO.
