---
phase: 11-align-graphrag-to-graphcompliance-architecture-scenario-anch
plan: 04b
type: execute
wave: 3
supersedes: "04"
depends_on: ["11-02"]
blocks: ["11-05"]
files_modified:
  - src/rag/graph/ontology/cu_teardown.py
  - src/rag/graph/ontology/cu_classifier.py
  - src/rag/graph/ontology/cu_extractor.py
  - src/rag/graph/ontology/cu_candidate_gate.py
  - src/presentation/cli/graph.py
  - tests/rag/graph/ontology/test_cu_teardown.py
  - tests/rag/graph/ontology/test_cu_candidate_gate.py
  - tests/rag/graph/ontology/test_cu_classifier.py
  - tests/rag/graph/ontology/test_cu_extractor.py
autonomous: false
requirements: [R11-2, R11-4]
must_haves:
  truths:
    - "This plan SUPERSEDES 11-04. The 11-04 CU layer is torn down and regenerated. The 883-node :Clause backbone (11-01/11-02) is NEVER touched."
    - "CU typing is a PER-UNIT LLM SEMANTIC JUDGMENT (D-30), not a predetermined table. The `function_type`/`doc_class` tags are passed as SOFT HINTS only; the classifier decides. Supersedes D-03's warm-start-as-decider."
    - "Two-level classification per the paper (D-31): premise vs CU, then within CU actor-CU vs meta-CU; deontic MODALITY (obligation/prohibition/permission) captured on every actor-CU (carried in constraint + a `modality` facet)."
    - "Candidate gating (D-32): structural headers (ToC) stay pure hierarchy, never CUs (unchanged). Response-to-Feedback (doc_class=guidance, consultation-response) → premise(kind=interpretation), NEVER an obligation CU. The four guidance docs (SBD/Threat/Risk/Audit) are classified PER-CONTENT by the LLM (not wholesale premise)."
    - "premise_kind facet (D-33): every premise carries premise_kind ∈ {definition, scope, purpose, interpretation}. Glossary → definition; RtF → interpretation. Premises are retained (D-09) and never judged."
    - "Subject inheritance (D-34): a lettered sub-clause inherits its operative parent's subject; NO obligation CU is minted subjectless when the actor is recoverable from the parent stem."
    - "Regulator-facing units (D-35): minted as actor-CU with modality=permission (Commissioner/Minister/licensing powers) — kept, not excluded (user directive)."
    - "Real quality gate (D-36): an obligation CU whose 4-tuple is ALL-EMPTY is a FAILURE, not a pass. Extraction RETRIES on empty; the acceptance gate counts empty-string tuples, not just NULL. Replaces 11-04's NULL-only gate that masked 325 hollow CUs."
    - "Full-scope 4-tuple (D-37): subject normalized to a role/hypernym form for downstream anchor alignment; `conditions` supports the paper's structured disjunction (any/all) serialized as JSON-in-string, not a flat coercion."
    - "Delete-and-rebuild (D-38): all :ComplianceUnit nodes + relationships are snapshotted then DETACH DELETEd before regen; a before/after diff vs the snapshot is part of acceptance."
    - "Pure LLM path runs on `claude-opus-4-8` via the local ClaudeCliGateway (NOT OpenRouter), per the 2026-07-05 user directive. Classification is now ~770 real Opus calls (no warm-start short-circuit) — a one-time offline build cost, paid once, reused across all cases."
    - "D-07 (emergent count), D-09 (premise retrievable), D-13 (text = citation payload, never mutated by extraction), D-26 (human approval gate ends the wave) all still hold."
  artifacts:
    - path: "src/rag/graph/ontology/cu_teardown.py"
      provides: "Snapshot current :ComplianceUnit layer to JSON, then DETACH DELETE all CU nodes+rels (Clause backbone untouched)"
      contains: "DETACH DELETE"
    - path: "src/rag/graph/ontology/cu_candidate_gate.py"
      provides: "Candidate selection + doc-type routing: exclude structural headers; RtF→forced premise(interpretation); guidance docs→LLM-decides; carry doc_class/function_type as hints"
      contains: "premise_kind"
    - path: "src/rag/graph/ontology/cu_classifier.py"
      provides: "Stage 1 REWRITE: per-unit pure-LLM two-level classification (premise/meta-CU/actor-CU) + modality + premise_kind; mint typed :ComplianceUnit; subject inheritance"
      contains: "modality"
    - path: "src/rag/graph/ontology/cu_extractor.py"
      provides: "Stage 2 REWRITE: 4-tuple extraction with retry-on-empty, subject normalization, structured conditions; empty-tuple = failure"
      contains: "retry"
  key_links:
    - from: "src/rag/graph/ontology/cu_classifier.py"
      to: ":ComplianceUnit (cu_type, modality, premise_kind) -> source clause"
      via: "per-unit LLM classification + mint, MERGE link to source clause"
      pattern: "cu_type"
    - from: "src/rag/graph/ontology/cu_extractor.py"
      to: ":ComplianceUnit 4-tuple properties (normalized subject, structured conditions)"
      via: "schema-constrained LLM extraction with retry-on-empty"
      pattern: "constraint"
---

<objective>
Regenerate the Policy Graph CU layer from scratch, correcting the six defects found in the 11-04 audit (2026-07-05):
1. Typing was a CCoP-chapter-1 lookup table with `actor-CU` as the catch-all default (744/770 actor-CUs) — not a semantic judgment. Replace with per-unit pure-LLM classification (D-30/D-31).
2. Response-to-Feedback (235 clauses, doc_class=guidance) minted as obligation actor-CUs — a category error (consultation Q&A, 64% empty tuples, 84 duplicating existing CCoP obligations). Route to premise(interpretation) (D-32).
3. 325/764 obligation CUs (43%) carried an ALL-EMPTY 4-tuple despite real source text, hidden by a NULL-only acceptance gate. Add retry-on-empty + an empty-string-aware gate (D-36).
4. 61 subjectless obligation fragments (lettered sub-clauses split from their "The CIIO shall:" stem). Add subject inheritance (D-34).
5. Definitions mistyped (glossary rows as meta/actor-CU, e.g. CCoP-10.1.2). Fixed by semantic typing + premise_kind (D-33).
6. Simplified tuple (flat conditions, un-normalized subject). Full-scope tuple with structured conditions + role-normalized subject (D-37).

Delete-and-rebuild: snapshot + DETACH DELETE the 770 existing CUs (D-38), then regenerate. The :Clause backbone (883 nodes) and its 11-02 text/citation/doc_class annotations are the untouched input.
Output: a semantically-typed :ComplianceUnit layer — premise/meta-CU/actor-CU by LLM judgment, modality + premise_kind facets, obligation CUs carrying a non-empty validated 4-tuple, subjects inherited/normalized, RtF as linked interpretive context — ready for 11-05 reference-building.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/11-align-graphrag-to-graphcompliance-architecture-scenario-anch/11-CONTEXT.md
@.planning/phases/11-align-graphrag-to-graphcompliance-architecture-scenario-anch/11-04-cu-inventory.md
@research/graphcompliance/2510.26309v1.pdf
@src/rag/graph/ontology/cu_classifier.py
@src/rag/graph/ontology/cu_extractor.py
@src/rag/graph/ontology/clause_seeder.py
@src/rag/graph/ontology/clause_source_annotator.py
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 0 (W0): Teardown + baseline snapshot</name>
  <read_first>
    - src/rag/graph/ontology/cu_classifier.py (current mint/constraint discipline + CUMintStats — the layer being deleted)
    - src/rag/graph/ontology/clause_seeder.py lines 190-211 (uniqueness-constraint idempotency pattern — keep the (cu_id, source_doc) constraint across teardown)
    - .planning/phases/.../11-04-cu-inventory.md (the 770-CU baseline this snapshot must reproduce for the before/after diff)
  </read_first>
  <behavior>
    - Snapshot every :ComplianceUnit (all properties + FROM_CLAUSE target clause_id) to a timestamped JSON before deleting, so the regen has a diffable baseline (770 CUs; 744 actor / 20 meta / 6 premise; 325 empty tuples).
    - DETACH DELETE all :ComplianceUnit nodes and their relationships. The :Clause backbone (883) and the (cu_id, source_doc) uniqueness constraint are preserved.
    - Idempotent + safe: re-running on an already-empty CU layer is a no-op that still writes a (0-CU) snapshot.
  </behavior>
  <action>Create `src/rag/graph/ontology/cu_teardown.py` with a `CUTeardown` class: `snapshot(path)` runs `MATCH (cu:ComplianceUnit) OPTIONAL MATCH (cu)-[:FROM_CLAUSE]->(c:Clause) RETURN cu{.*} , c.clause_id` and writes JSON; `teardown()` runs `MATCH (cu:ComplianceUnit) DETACH DELETE cu` (static Cypher, T-09-12). Guard: assert `:Clause` count is unchanged (883) after teardown. Add a `ccop-eval graph reset-cus` CLI subcommand in `src/presentation/cli/graph.py` that snapshots-then-tears-down. Add `tests/rag/graph/ontology/test_cu_teardown.py`: snapshot round-trips CU props; teardown removes all CUs; Clause count unchanged; re-run is a no-op.</action>
  <acceptance_criteria>
    - After teardown: `MATCH (cu:ComplianceUnit) RETURN count(cu)` = 0; `MATCH (c:Clause) RETURN count(c)` = 883 (unchanged); the (cu_id, source_doc) constraint still exists.
    - A snapshot JSON exists capturing the pre-teardown 770 CUs for the acceptance diff.
    - `poetry run pytest ../tests/rag/graph/ontology/test_cu_teardown.py -x` passes.
  </acceptance_criteria>
  <verify>
    <automated>cd src && poetry run pytest ../tests/rag/graph/ontology/test_cu_teardown.py -x</automated>
  </verify>
  <done>CU layer snapshotted + deleted; Clause backbone intact; regen has a clean slate + a diff baseline.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 1 (W1): Candidate gate — doc-type routing (structural / RtF / guidance)</name>
  <read_first>
    - src/rag/graph/ontology/clause_source_annotator.py (source of `doc_class` binding/guidance + `is_structural_header` + namespaced citation on every :Clause)
    - src/rag/graph/ontology/clause_seeder.py lines 76-152 (function_type tags — now a HINT, not a decider)
    - .planning/.../11-04-cu-inventory.md (RtF = 235 clauses all doc_class=guidance; the 4 guidance docs = SBD/Threat/Risk/Audit)
  </read_first>
  <behavior>
    - Fetch candidate clauses (non-structural-header) and attach routing metadata: `source_doc`, `doc_class`, `function_type` (hint), and a `route` ∈ {llm_classify, force_premise_interpretation}.
    - Structural headers (is_structural_header=true) are excluded entirely (never a CU; ToC stays pure hierarchy).
    - Response-to-Feedback source_doc → route=`force_premise_interpretation` (D-32): never an obligation CU; will mint as premise(kind=interpretation).
    - All other docs (CCoP, Act, SBD, Threat, Risk, Audit) → route=`llm_classify` (the LLM decides premise/meta/actor per-content — guidance docs are NOT wholesale-premised).
  </behavior>
  <action>Create `src/rag/graph/ontology/cu_candidate_gate.py`: a pure function `route_candidates(clauses) -> list[Candidate]` where `Candidate` carries clause fields + `route` + hint tags. Encode the RtF source_doc string as a module constant (mirror `clause_source_annotator`'s registered-source-doc discipline; fail-loud on an unregistered doc rather than silently defaulting). No LLM here — pure routing. Add `tests/rag/graph/ontology/test_cu_candidate_gate.py`: structural headers dropped; RtF → force_premise_interpretation; a SBD "should" clause → llm_classify (not forced premise); an unregistered source_doc raises.</action>
  <acceptance_criteria>
    - RtF clauses (235) all route to force_premise_interpretation; zero route to llm_classify.
    - Guidance docs (SBD/Threat/Risk/Audit) route to llm_classify (LLM decides), NOT force_premise.
    - Structural headers excluded (candidate count = 883 − structural-header count).
    - `poetry run pytest ../tests/rag/graph/ontology/test_cu_candidate_gate.py -x` passes.
  </acceptance_criteria>
  <verify>
    <automated>cd src && poetry run pytest ../tests/rag/graph/ontology/test_cu_candidate_gate.py -x</automated>
  </verify>
  <done>Candidate set routed: ToC excluded, RtF forced to interpretive premise, everything else to per-content LLM classification.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2 (W2): Classifier REWRITE — per-unit pure-LLM two-level typing + modality + premise_kind + subject inheritance</name>
  <read_first>
    - src/rag/graph/ontology/cu_classifier.py (current file — REMOVE the FUNCTION_TYPE_TO_CU_TYPE warm-start short-circuit as the decider; keep the mint/MERGE/CUMintStats/Cypher discipline)
    - research/graphcompliance/2510.26309v1.pdf §3.1 (VERBATIM definitions to embed in the prompt: premise = non-deontic definitional/interpretive/scope/purpose material, NOT judged; actor-CU = obligation/prohibition/permission addressed to a role-bearing actor, the unit judged; meta-CU = applicability gate — temporal/territorial scope, role qualification, covered processing — evaluated first, never a standalone violation)
    - src/infrastructure/adapters/models/claude_cli_gateway.py (ClaudeCliGateway — the pure-LLM path, settings.cu_extraction_model=claude-opus-4-8)
    - src/rag/graph/ontology/clause_seeder.py lines 108-152 (`_derive_parent` — the parent-stem resolution reused for subject inheritance)
  </read_first>
  <behavior>
    - Every candidate routed `llm_classify` gets a REAL Opus classification call (no warm-start short-circuit — D-30). The prompt carries the paper's verbatim premise/meta-CU/actor-CU definitions and asks for: (a) type, (b) for actor-CU, modality ∈ {obligation, prohibition, permission}, (c) for premise, premise_kind ∈ {definition, scope, purpose, interpretation}. `function_type`/`doc_class` appear in the prompt as SOFT HINTS ("prior signal, may be wrong").
    - Candidates routed `force_premise_interpretation` (RtF) skip the LLM and mint directly as premise, premise_kind=interpretation (D-32/D-33).
    - Multi-obligation clauses may mint >1 CU (D-07 preserved); the ordinal-suffix cu_id scheme is retained.
    - Regulator-facing obligations mint as actor-CU modality=permission (D-35) — no exclusion.
    - Subject inheritance (D-34): when a candidate is a lettered sub-clause (citation ends in `(a)`/`(b)`/…) and its own text has no explicit actor, the operative parent's subject is carried onto the child CU (resolved via `_derive_parent` + the parent's text) so no obligation CU is minted subjectless when the actor is recoverable.
    - Degrade-safe: malformed LLM output → log + default to premise(kind=definition) (inert — never a false obligation); never raise (T-11-08).
  </behavior>
  <action>Rewrite `src/rag/graph/ontology/cu_classifier.py`: delete `FUNCTION_TYPE_TO_CU_TYPE` as the decision path; keep `VALID_CU_TYPES`. New `CU_CLASSIFICATION_PROMPT` embedding the paper's verbatim definitions and requesting a small JSON `{"type": "...", "modality": "...", "premise_kind": "..."}` (modality only for actor-CU, premise_kind only for premise). Parse via the `fix_invalid_json`/Pydantic degrade shape (reuse from cu_extractor). Consume `cu_candidate_gate.route_candidates` output: force_premise_interpretation candidates bypass the LLM. Mint typed :ComplianceUnit with `cu_type`, plus `modality` (actor-CU) / `premise_kind` (premise) properties. Implement subject inheritance as a pre-mint enrichment: for a lettered-suffix candidate with no actor token in its own text, look up the parent clause text + resolved subject and stamp an `inherited_subject` hint onto the CU for Stage 2 to consume. Extend `CUMintStats` with per-modality and per-premise_kind counts (re-queried from Neo4j). Update `tests/rag/graph/ontology/test_cu_classifier.py`: a definitional clause → premise(definition) with NO obligation minted; an RtF clause → premise(interpretation) with no LLM call; a "the CIIO shall…" clause → actor-CU(obligation); a "the Commissioner may…" clause → actor-CU(permission); an OT-applicability clause → meta-CU; a lettered sub-clause with no actor inherits the parent subject; malformed output degrades to premise; multi-obligation spawns >1 CU.</action>
  <acceptance_criteria>
    - Zero classifications use a predetermined type table as the decider — every `llm_classify` candidate has a real Opus call (assert llm_classification_calls == count(llm_classify candidates)).
    - Type distribution is emergent and plausible: NO single catch-all bucket ≈ total; premise count ≫ 6 (glossary + RtF + definitional Act/guide rows); meta-CU count > 20 (all applicability gates, not just CCoP §1); actor-CU count ≪ 744.
    - Every actor-CU carries modality ∈ {obligation, prohibition, permission}; every premise carries premise_kind ∈ {definition, scope, purpose, interpretation}.
    - Zero obligation CUs are minted subjectless when the actor is recoverable from the parent stem (spot-check the former 61 lettered-fragment cases).
    - `poetry run pytest ../tests/rag/graph/ontology/test_cu_classifier.py -x` passes (all cases above).
  </acceptance_criteria>
  <verify>
    <automated>cd src && poetry run pytest ../tests/rag/graph/ontology/test_cu_classifier.py -x</automated>
  </verify>
  <done>CUs typed by LLM semantic judgment; RtF is interpretive premise; regulator powers are permission actor-CUs; definitions are premises; sub-clauses inherit their actor.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3 (W3): Extractor REWRITE — root-cause the empties, then 4-tuple with retry-on-empty + normalized subject + structured conditions</name>
  <read_first>
    - src/rag/graph/ontology/cu_extractor.py (current file — keep the fix_invalid_json/Pydantic/parameterized-Cypher discipline; REPLACE degrade-and-pass with retry-on-empty; the `subject IS NULL` resume marker still works)
    - research/graphcompliance/2510.26309v1.pdf §3.1 + Appendix C.1 Listing 1 (the GDPR Art.37 worked CU: subject="controller and processor", constraint=["shall designate…"], condition={"any":[…three triggers…]}, context=null — the structured-condition + normalized-subject target shape)
    - .planning/.../11-04-cu-inventory.md (the 139 CCoP + 151 RtF + 35 other empty-tuple CUs — the failures this task must not reproduce)
  </read_first>
  <behavior>
    - ROOT-CAUSE FIRST (blocking sub-step): re-extract ~10 known-empty CCoP obligations (5.6.1, 5.7.1, 5.7.2, 5.13.x…) with the current prompt, capture the raw Opus responses, and classify the failure (prompt shape / CLI truncation at max_tokens / item-letter text shape). Record the finding in the SUMMARY; let it drive the new prompt.
    - Every obligation CU (actor-CU + meta-CU) gets a 4-tuple. `subject` is normalized to a role/hypernym form (e.g. "the owner of a CII ('CIIO')" → "CIIO"); the classifier's `inherited_subject` hint seeds sub-clause subjects. `conditions` may be a structured disjunction/conjunction (paper's any/all) serialized as JSON-in-string; `context` may be genuinely empty.
    - RETRY-ON-EMPTY (D-36): if extraction returns an all-empty tuple for a CU whose source text is non-trivial, retry once with a repair prompt before persisting. Persisting an all-empty tuple for a non-trivial obligation is a recorded failure, not a silent pass.
    - Premises are never fetched (structurally excluded). Source `text` is never mutated (D-13).
  </behavior>
  <action>Rewrite `src/rag/graph/ontology/cu_extractor.py`: new `CU_TUPLE_EXTRACTION_PROMPT` incorporating the root-cause finding + the paper's worked-example shape (normalized subject, structured conditions, nullable context, deontic force inside constraint). Add subject-normalization guidance + consume the `inherited_subject` hint from Stage 1. Add a single retry: if `CUTuple.is_empty()` and source text length > a small threshold, re-call with a terser repair instruction; count `cus_retried` and `cus_still_empty_after_retry`. Extend `ExtractionStats` with `obligation_cu_all_empty_count` (empty-STRING aware, not NULL-only). Keep incremental batched writes + resume. Update `tests/rag/graph/ontology/test_cu_extractor.py`: a well-formed obligation → complete non-empty tuple; an empty first response triggers a retry; a normalized subject is produced for a verbose actor phrase; a structured `conditions` disjunction round-trips; premises are skipped; source text untouched.</action>
  <acceptance_criteria>
    - Root-cause of the 11-04 empty-tuple failure is documented in the SUMMARY with a representative raw response.
    - `obligation_cu_all_empty_count` (empty-string-aware) is ~0 — any residual all-empty obligation CUs are enumerated with a reason (genuinely non-obligation text), NOT silently passed. This is the HARD gate replacing 11-04's NULL-only check.
    - Spot-check: the former 139 empty CCoP obligations (5.6.1, 5.7.x, 5.13.x…) now carry a populated ⟨subject, constraint, context, conditions⟩.
    - Subjects for the former 61 lettered fragments are populated (inherited) and normalized.
    - `poetry run pytest ../tests/rag/graph/ontology/test_cu_extractor.py -x` passes.
  </acceptance_criteria>
  <verify>
    <automated>cd src && poetry run pytest ../tests/rag/graph/ontology/test_cu_extractor.py -x</automated>
  </verify>
  <done>Obligation CUs carry non-empty, role-normalized, structured 4-tuples; the empty-tuple failure is root-caused and gated; text preserved.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 4 (W4): Full regen run + acceptance diff vs the W0 snapshot</name>
  <read_first>
    - src/rag/graph/ontology/cu_teardown.py (the W0 snapshot to diff against)
    - src/presentation/cli/graph.py (the build orchestration entry point — wire reset → gate → classify → extract)
  </read_first>
  <behavior>
    - Run the full pipeline on the live graph: reset-cus (W0) → route (W1) → classify+mint (W2) → 4-tuple extract (W3), on claude-opus-4-8 via the local CLI (one-time offline build).
    - Produce a regenerated `11-04b-cu-inventory.md` (same shape as 11-04's) AND a diff summary vs the W0 snapshot: net change per type, RtF reclassified to premise, empty-tuple delta (325 → ~0), subjectless-fragment delta (61 → ~0).
  </behavior>
  <action>Run `poetry run ccop-eval graph reset-cus` then the CU build orchestration (classify + extract) end-to-end against live Neo4j (the mandated smallest-real-slice first: one benchmark's worth of clauses to prove wiring, then the full ~770-candidate run). Regenerate the inventory + write the before/after diff into the SUMMARY.</action>
  <acceptance_criteria>
    - Live counts: :ComplianceUnit regenerated; type distribution emergent + plausible (no catch-all bucket); every obligation CU has a non-empty 4-tuple + modality; every premise has premise_kind; RtF (235) all premise(interpretation); 0 CUs without source-text link; :Clause still 883.
    - Before/after diff vs W0 snapshot is written to the SUMMARY (empty-tuple 325→~0; RtF 235 actor→premise; subjectless 61→~0).
  </acceptance_criteria>
  <verify>
    <automated>cd src && poetry run ccop-eval graph reset-cus --help</automated>
  </verify>
  <done>The corrected CU layer is live on the graph with a documented before/after diff; ready for 11-05 reference-building.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>The regenerated Policy-Graph CU layer (this plan, superseding 11-04): LLM-typed :ComplianceUnit nodes (emergent premise/meta-CU/actor-CU) with modality + premise_kind facets, non-empty role-normalized 4-tuples on obligation CUs, RtF as linked interpretive premise, subject-inherited sub-clauses — each linked to its source clause's verbatim text.</what-built>
  <how-to-verify>
    1. Review the emergent type distribution + the before/after diff vs the 11-04 snapshot (RtF reclassified; no catch-all actor bucket; premise/meta counts sane).
    2. Spot-check the former failure cases: 5.6.1/5.7.x now have real 4-tuples; a former lettered fragment (e.g. 5.6.2(a)) now carries an inherited subject; a "Commissioner may…" unit is actor-CU(permission); CCoP-10.1.2 is now premise(definition).
    3. Confirm the hard gate: obligation CUs with an all-empty tuple ≈ 0, and any residual are enumerated-with-reason, not silent.
  </how-to-verify>
  <resume-signal>Type "approved" to let 11-05 build REFERS_TO edges (incl. RtF→CCoP clarification links) on these CUs, or list the CUs/tuples needing rework.</resume-signal>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| corpus text -> LLM classifier/extractor | Untrusted-shaped provision text prompts Opus; malformed output must degrade, never crash the ~770-candidate batch |
| Claude CLI (local subprocess) | Pure-LLM classify + 4-tuple extract via local `claude -p --model claude-opus-4-8`; no external API key; subprocess failure/timeout degrades per-unit |
| teardown DETACH DELETE | A destructive CU-layer delete; must be snapshot-guarded + backbone-preserving |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-11b-01 | Tampering/Destruction | teardown DETACH DELETE | mitigate | Snapshot-before-delete (D-38); post-delete assert :Clause count == 883; static parameterized Cypher (T-09-12) |
| T-11b-02 | Denial of Service | ~770 real Opus classify calls (no warm-start) + retry-on-empty extract | mitigate | Per-unit try/except degrade; `claude_cli_timeout` per call; incremental batched writes + resume; one-time offline build |
| T-11b-03 | Info Disclosure | local Claude CLI subprocess | mitigate | No external API key on this path; corpus is public CCoP; secrets never logged |
| T-11b-04 | Tampering | Cypher writes of cu_type/modality/premise_kind/tuple | mitigate | Parameterized Cypher only (T-09-12) |
| T-11b-SC | Tampering | package installs | accept | No new installs (reuses neo4j-graphrag, pydantic, typer) |
</threat_model>

<verification>
- CU layer torn down (snapshot kept) + regenerated; :Clause backbone intact (883); typing is per-unit LLM; RtF is interpretive premise; guidance docs classified per-content; regulator powers are permission actor-CUs; every obligation CU has a non-empty role-normalized 4-tuple with modality; premises carry premise_kind; empty-tuple gate is empty-string-aware and ≈0; before/after diff documented.
</verification>

<success_criteria>
- D-30: typing is per-unit LLM judgment, not a table (warm-start-as-decider removed).
- D-31: two-level classification + modality captured.
- D-32: RtF → premise(interpretation); guidance docs LLM-decided; ToC excluded.
- D-33: premise_kind facet on every premise.
- D-34: no recoverable-subject obligation CU minted subjectless.
- D-35: regulator powers minted as actor-CU(permission).
- D-36: empty-string-aware quality gate; obligation all-empty ≈ 0; root-cause documented.
- D-37: normalized subject + structured conditions.
- D-38: snapshot + delete-and-rebuild; before/after diff.
- D-07/D-09/D-13/D-26 preserved: emergent count; premise retrievable; text never mutated; human gate ends the wave.
</success_criteria>

<output>
Create `.planning/phases/11-align-graphrag-to-graphcompliance-architecture-scenario-anch/11-04b-SUMMARY.md` when done (include the empty-tuple root-cause finding + the before/after diff vs the 11-04 snapshot).
Regenerate `.planning/phases/11-align-graphrag-to-graphcompliance-architecture-scenario-anch/11-04b-cu-inventory.md`.
</output>
