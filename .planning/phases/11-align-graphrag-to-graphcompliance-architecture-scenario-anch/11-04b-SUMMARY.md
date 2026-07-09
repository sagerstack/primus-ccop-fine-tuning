---
phase: 11-align-graphrag-to-graphcompliance-architecture-scenario-anch
plan: 04b
supersedes: "04"
subsystem: rag-graph-ontology
tags: [graphcompliance, compliance-unit, openrouter, claude-sonnet-4, 4-tuple, policy-graph, neo4j, text-alignment]
requirements-completed: [R11-2, R11-4]
completed: 2026-07-06
---

# Phase 11 Plan 04b: Regenerate Compliance Units (supersedes 11-04) Summary

**Deleted the defective 11-04 CU layer and regenerated it with per-unit LLM typing, a fixed Cybersecurity Act text layer, and death-resilient extraction — 802 semantically-typed `:ComplianceUnit` nodes, 0 empty obligation tuples, 0 subjectless actor-CUs — built on `anthropic/claude-sonnet-4` via OpenRouter (off the `claude -p` subscription that was hitting daily limits).**

## Why 11-04 was regenerated (audit findings, 2026-07-05)

| Defect | 11-04 | Root cause |
|---|---|---|
| Typing was a lookup table | 744/770 actor-CU catch-all | `function_type` CCoP-§1 table + `ControlClause` default; LLM classifier never ran |
| Empty 4-tuples | 325/764 obligation CUs empty (masked by NULL-only gate) | extraction prompt/run artifact |
| RtF miscast | 235 Q&A clauses as obligation actor-CUs | no doc-type gating |
| Subjectless fragments | 61 lettered sub-clauses | no subject inheritance |
| Act text corruption | 13 Act clauses shared identical wrong text | 11-02 aligner stripped the heading line carrying the section number → longest-bare-match collision |

## What was built (W0–W4 + fixes)

- **W0 Teardown** (`cu_teardown.py`, `graph reset-cus`): snapshot + DETACH DELETE the CU layer, `:Clause` backbone guard (883 unchanged).
- **W1 Candidate gate** (`cu_candidate_gate.py`): ToC excluded, RtF → forced interpretive premise, guidance docs → LLM-decided, textless clauses skipped.
- **W2 Classifier rewrite** (`cu_classifier.py`): per-unit **pure-LLM two-level typing** (premise/meta-CU/actor-CU) + `modality` (obligation/prohibition/permission) + `premise_kind` (definition/scope/purpose/interpretation) facets; dedup + premise-XOR-obligation + 3-unit cap guards.
- **W3 Extractor rewrite** (`cu_extractor.py`): retry-on-empty + empty-string-aware gate, parent-stem subject inheritance, normalized subject, structured `conditions` (`{"any":[…]}`).
- **Act text-alignment fix** (`clause_text_aligner.py`, 11-02): two-pass per-section slicer (strict `##`-headed, then relaxed `(1)`-opener fallback) + isolated Act path that never uses the colliding longest-bare fallback; clear stale text on unaligned clauses. 49/53 Act clauses now resolve to correct distinct bodies, **0 text collisions** (was 13), CCoP untouched.
- **Death-resilient pipeline** (`GatewayUnavailableError`): a gateway/CLI failure SKIPS the unit (leaves it un-minted / subject NULL) for a resume pass instead of writing a wrong value; aborts a pass after N consecutive infra errors. Both stages resumable.
- **OpenRouter migration** (`openrouter_gateway.py`, `_default_cu_gateway`): CU build routed through OpenRouter (credits, decoupled from the `claude -p` Claude-subscription daily limit). `settings.cu_extraction_model = anthropic/claude-sonnet-4`.

## Result (live, Neo4j bolt://localhost:7687)

| Metric | 11-04 | **11-04b** |
|---|---|---|
| Total CUs | 770 | **802** |
| actor-CU / meta-CU / premise | 744 / 20 / 6 | **362 / 16 / 424** |
| modality (obligation/permission/prohibition) | — | 313 / 37 / 12 |
| premise_kind (interp/def/scope/purpose) | — | 281 / 70 / 48 / 25 |
| **All-empty obligation tuples** | 325 | **0** |
| **Subjectless actor-CUs** | 61 | **0** |
| RtF as obligations | 235 | **0** (all → premise/interpretation) |
| CUs without source text / link | 0 / 0 | 0 / 0 |
| `:Clause` backbone | 883 | 883 (unchanged) |

Extraction: 378/378 obligation CUs extracted (2 retried-and-recovered, 0 still-empty). Premises carry no tuple (0). Unit tests: 71 pass (fake gateways).

## Model & cost

- **`anthropic/claude-sonnet-4`** via OpenRouter. Measured per-call token usage → full build ≈ **$3.09**, within the available $3.82 credits. (Sonnet 4.5 / GPT-4.1 / DeepSeek V3 all wired-compatible; override via `CCOP_CU_EXTRACTION_MODEL`.)
- ~531 classify calls (235 RtF forced, no LLM) + 378 extract calls + 10 cleanup re-extractions.

## Deviations from plan

1. **[Rule 1 — infra] Opus `claude -p` hit the daily spend limit mid-run (twice).** The first full regen corrupted ~400 clauses (silent degrade-on-infra-error). Recovery: hardened both stages to skip-on-infra-error + resume (never write a wrong value), then migrated the CU build to OpenRouter/Sonnet-4 entirely.
2. **[Root-cause detour] Act text alignment (11-02).** The CU over-generation (multi-CU ratio 1.6) traced to 13 Act clauses sharing wrong text — a foundational-layer + citation-payload correctness bug. Fixed at source rather than worked around (user directive: "why not fix the text alignment first").
3. **[Orchestration] Completion-check false negative.** The resumable orchestrator counted the 4 textless Act Parts as "unclassified" and stalled before extraction; fixed the query to exclude textless (gate-skipped) clauses.
4. **[Cleanup] 17 subjectless actor-CUs** post-build → 7 inherited subject from parent CU (CCoP-5.9.2 → CIIO), 10 re-extracted with a doc-default-actor hint (SBD → the organisation, Audit → the auditor, Act-44 → protected official). Now 0.

## Commits

- `149be32` feat: regenerate CU pipeline — pure-LLM typing + retry/inheritance extractor
- `755c4d2` docs: CU-regeneration phase plan
- `afc6a6d` fix: death-resilient CU pipeline — skip-on-infra-error + resume
- `e5f691d` fix(11-02): Act clause-text alignment — section slicing, no shared blobs
- `6dba693` fix: premise-XOR-obligation + units-per-clause cap
- `2a57c72` feat: route CU build through OpenRouter (off claude -p)
- `e104d9a` chore: default CU model → anthropic/claude-sonnet-4

## Follow-ups / notes for 11-05

- Fold **ancestor-subject inheritance** (the parent-CU-subject propagation used in cleanup) into the `build-compliance` orchestrator so a future rebuild is subjectless-free without a manual pass.
- The 3 subjectless meta-CUs (Act-3, CCoP-1.5.2, CCoP-10.1.1) are applicability gates — subject legitimately empty (not a defect).
- The regenerated CUs are the nodes 11-05's `REFERS_TO` edges will connect; the Act text fix makes reference extraction (regex over clause text) correct.

## Self-Check: PASSED
- FOUND: cu_teardown.py, cu_candidate_gate.py, cu_classifier.py (rewrite), cu_extractor.py (rewrite), openrouter_gateway.py, clause_text_aligner.py (Act fix); tests updated (71 pass).
- CONFIRMED (live): 802 CUs (362 actor / 16 meta / 424 premise); 0 all-empty obligation tuples; 0 subjectless actor-CUs; 0 Act text collisions; 883 clauses intact.
