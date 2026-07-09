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
| **1.1 — ontology extension** | ✅ APPLIED (2026-07-08) | `corpus_ontology.json` **v1.1** — additive: 8 reparents + 8 new relations (CONDUCTS, APPLIES_PRINCIPLE, USES_TECHNIQUE, REDUCES, HAS_DEADLINE, HAS_STATUS, BOUNDED_BY, BINDS) + 6 relation dom/range extensions. Removed 26 orphan entity types (6 intentional orphans left). Approved after self-critique. `.pre-extend-*.bak` backup kept. |
| **2 — extraction (Opus, by hand)** | ✅ **ALL 7 DOCS DONE** | **869/869 clauses, 1672 triples, 0 Φ-fails, 107 concepts, 71/72 relations used, 69% ≥2 triples, 2% empty.** Per-doc: d1 385/729, d2 280/564, d3 17/36, d4 12/29, d5 15/35, d6 98/178, d7 62/92. Method: hand-author → `apply_extract.py` Φ-validates + caches tagged `claude-opus`. |
| **3 — per-doc critic** | ✅ d1–d6 done+fixed, d7 running | Critic subagent reviewed each doc (`runs/critic/doc{1,2,3to6,7}-findings.md`). All type-clean, no fabrications. Fixes applied: d1 (Annex A modality+scope, DEFERS_TO, W2/W3/O3), d2 (6 fixes: inverted COVERS, clause-merge, DISABLES mis-reads), d3–d6 (5 fixes: waiver/compensating in audit scope, STRIDE-LM mitigations, DEFERS_TO). |
| **4 — entity resolution** | ✅ DONE (2026-07-09) | Verify+register pass (hand-authoring already canonical): 0 multi-type nodes, 0 dupes, cross-doc bridges confirmed (7-doc hubs), wrong-merge guard clean (IT⊥OT, Malware≠MalwareProtection, Password family, Cryptography≠DNSSEC). `concept_aliases.json` = 137 canonical nodes + surface forms for retrieval query→concept mapping. |
| **5 — Neo4j persist** | ✅ DONE (2026-07-09) | Loaded `build_id=omd-v1-20260709`: **863 :Clause** (869 records − 6 footnote citation_id collisions) + **122 :Concept** + **3135 :INVOKES** (Clause→Concept) + **1935 :REL** (Concept→Concept). Loader `build_omd_graph.py`. **Old Phase-11 CU graph (1320 nodes) was backed up to `../complianceunit/cu_graph_backup.json` (+`restore.py`), then DETACH DELETE'd** (per user; it backed live graphcpl retrieval — REWIRE those 7 retrieval nodes or `restore.py` before using graphcpl). |
| **6 — coverage/linkage** | 🟡 bridges verified | POC bridges reproduce in Neo4j: B05 5.9.2(b)↔11.28 via Password/PasswordLength ✓; B01 CII hub spans 7 docs (296 clauses) ✓; leaf bridge defence-in-depth spans CCoP↔RtF ✓. TODO: full coverage report + close residual gaps (footnote re-key, REQUIRES_EVIDENCE). |
| **7 — retrieval (`graphont`)** | 🟡 core built, 2 issues | `omd_retrieval.py` = new POC Channel-I retrieval (query→concepts→1-hop `:REL` expand→INVOKES-overlap score) over the Neo4j `build_id` layer. Standalone, touches no existing code. **E2E proven on B05 password bridge.** **2 issues to fix before wiring (see module docstring):** (1) mega-hub over-expansion → needs concept-IDF weighting; (2) thin query→concept mapping (PenetrationTesting etc. unmapped) → auto-derive surface forms + embedding/LLM fallback. |

## RETRIEVAL DEBRIEF (2026-07-09) — B01-001 investigation

### What we're trying to accomplish
Turn the persisted KG into working retrieval: a NEW mode `graphont` that runs the OMD-GraphRAG
POC methodology (concept-based retrieval) so it can be benchmarked vs `hybrid`/`graphcpl`. New
code only; do NOT touch graphcpl or existing retrieval nodes. `omd_retrieval.py` is that code.

### Steps taken (this session, after the KG build)
1. Built `omd_retrieval.py` = POC **Channel-I** (query→concepts Q → Q⁺=1-hop over `:REL` →
   score `|Q∩INVOKES| + 0.5·|(Q⁺−Q)∩INVOKES|` → top-K). Ran it corpus-wide (all 863 clauses).
2. **Found: hub flooding.** `CII` is in 296 clauses; scoring the whole corpus lets every CII
   clause tie, so B01-001 returned generic OT/access clauses, not scope answers.
3. **Read the POC** (`poc_reference/omd_b01.py`, `omd_e2e.py`) to see why it "worked":
   - it scored a **hand-picked ~18-clause pool** (answers + real distractors), not the corpus;
   - `omd_b01.py` = same concept-overlap formula as ours; `omd_e2e.py` = a **hand-tuned
     relation-weight table** (APPLIES_TO +2, EXCLUDED_FROM_AUDIT +2, IN_AUDIT_SCOPE −1.5…) — B01-specific.
   - the POC is **dual-channel** (Ch-I structural + **Ch-II dense + β-fusion + rerank**); we'd
     ported Ch-I ONLY, and pointed a *re-ranker* at the whole corpus.
4. **Fixed query→Q (issue #2):** replaced substring matching with **schema-guided LLM extraction**
   (POC design). Killed the false hit ("patient monitoring"→Monitoring). Q now clean/semantic.
5. **Built the dual-channel cascade (issue partially):** added **Channel-II = BM25 sparse recall**
   over all 863 clause texts → top-k1=40 candidates → Channel-I re-ranks only those → light fusion
   (`ch1 + 0.5·bm25_norm`). Added 3-stage CLI output (Ch-II list / Q,Q⁺ / Ch-I final).

### What we've been EVALUATING for B01-001
Query = the healthcare scenario (patient-monitoring/MRI = CII; hospital admin on shared enterprise
network — does mandatory compliance extend?). GT `expected_label = not-applicable`.
- **GT reference clauses:** CCoP §1.2.1, §1.4.1; Act §7.
- **GT key_facts → decisive clause = RtF §2.2** (digital boundary jointly determined by
  CSA/CIIO/Sector-Lead, ≠ enterprise-network perimeter) + RtF §2.3 (recommend org-wide) + Annex-A exclusion.
- **Result:** pipeline surfaced NONE of §1.2.1/§1.4.1/Act§7 at top; **RtF §2.2 WAS recalled by
  BM25 (#3) but Channel-I DEMOTED it to #8** (equal-weighting rewards concept-count, so OT-architecture
  §10.2 with many common concepts beat the focused answer).

### Root causes (evidence-backed) + NEXT STEPS
1. **Equal-weight Channel-I buries the decisive clause** → **add concept-IDF weighting**
   (weight ∝ log(N/df): `CII` df=296→idf≈1.1; `DigitalBoundary`/`EnterpriseNetwork` rare→idf≈4.3).
   Precompute `df` per concept, store `idf` on `:Concept`, multiply into the score. **Biggest lever.**
2. **Cascade (BM25→Ch-I) gates concept-retrieval behind lexical recall** → §1.4.1/Act§7 (abstract,
   lexically dissimilar) never enter the pool. **Switch to FUSION:** run IDF-weighted Channel-I as
   its own recall channel over the FULL corpus (IDF stops the flooding) **in parallel** with BM25,
   then fuse. This is the paper's real design; cascade was my wrong turn.
3. **`DigitalBoundary` missing from Q** though the question is entirely about scope/boundary →
   improve the query→concept prompt to surface *implicit* scope concepts.
4. **§1.2.1 not in the graph** — definitions were pulled to a separate `definitions/` layer in
   Phase 0, never loaded as `:Clause`. Decide: load definitions as clauses (or a `:Definition` node)
   so glossary-referenced answers are reachable.
5. Then wire `graphont` (seams below), benchmark vs hybrid/graphcpl.

### Files (retrieval)
- `omd_retrieval.py` — Channel-I + Channel-II(BM25) + LLM query→concept + 3-stage output. WORKS,
  but ranking needs #1/#2 above. Known issues in its docstring.
- `poc_reference/omd_b01.py` / `omd_e2e.py` — the reference (pool + relation-weights + dual-channel).

## `graphont` — new additive retrieval mode (planned, NOT wired yet)
User decision (2026-07-09): create a NEW mode `graphont` that routes to `omd_retrieval.py`; do NOT
touch graphcpl or existing retrieval nodes. Wiring seams (all additive):
1. `presentation/cli/query.py` → `VALID_MODES` += "graphont"
2. `presentation/cli/commands/evaluate.py` → `VALID_EVAL_MODES` += "graphont"
3. `application/use_cases/evaluate_model.py` → `_RETRIEVAL_EVAL_MODES` += "graphont" (also check for a
   RunId mode allowlist — the Phase-9 graphrag bug was a 2nd allowlist; grep before wiring)
4. `rag/retrieval/edges/routing.py` `route_by_mode` → return a "graphont" key
5. `rag/retrieval/graph.py` → add one node (calls `omd_retrieval.retrieve()`, assembles
   `filtered_documents`) + conditional-edge key + edge to `generate`. Mirror `compliance_context_assembly`
   output shape so primus reasons+cites (comparable to hybrid/graphcpl).
- **Prereq: fix the 2 `omd_retrieval` issues + re-run E2E on B01/B05/B12 (GT clauses top-K) FIRST.**

### Both design forks RESOLVED (2026-07-09, see memory `ontology-v2-pending-critic-forks`)
1. **Modality (B02)** ✅ — ontology **v1.2** broadened MANDATES/RECOMMENDS range; `modality_pass.py`
   added 187 MANDATES + 62 RECOMMENDS (248 clauses carry shall/should modality).
2. **Umbrella leaf granularity** ✅ — `specialize_leaves.py` split 4 umbrella types into distinct
   leaf nodes (defence-in-depth, zero-trust, MFA, DNSSEC, network-segmentation, …); 95 clauses.
- **FINAL corpus: 1935 triples, 0 Φ-invalid, 122 concept nodes, 869/869 clauses.**
- New helpers: `apply_extract.py` (author→validate→cache), `modality_pass.py`, `specialize_leaves.py`.
- Backups: `corpus_ontology.json.{pre-extend,pre-modality}-*.bak`.

### Residual gaps for Phase 6
- **Phase-0 footnote-collision bug** (doc 1 `::1..::6` share ids with §1..6 headers): re-key footnotes; only doc 1 affected (docs 3–7 footnotes clean per critics).
- **Unused relation:** `REQUIRES_EVIDENCE` (B13 AuditEvidence never a triple endpoint) — minor.

## Extraction workflow (LOCKED this session)
- **Opus authors every triple by hand, per clause** (NO gpt-4o-mini `_call_llm`, NO subagent/script doing the reasoning). Code only Φ-validates + caches.
- Batch ~30 clauses/turn: read clauses → write `batch.json` (list of `{citation_id, triples:[{subject,subject_type,relation,object,object_type,[proposed]}]}`) → `poetry run python -m rag.graph.ontology_v2.apply_extract --file batch.json` → review PROPOSED/dropped, fix, continue.
- Empty administrative/interpretation/header clauses are cached with `triples:[]` (marks them done; Phase-6 flags thin clauses) — never force noise.
- **Per-doc critic gate** (user instruction): finish a doc → spawn critic subagent (background) → move to next doc → fold critic findings back when it returns. See memory `ontology-v2-per-doc-critic-gate`.
- Remaining worklist / stale (gpt-4o-mini) recompute: a clause is "done" only if its cache has `extractor=="claude-opus"`. Stale to redo: `CCoP 2.0::1.2.5` ✅done, `CCoP 2.0::3.2.4` ✅done, `CCoP Response to Feedback::11.28` ⬜.

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
