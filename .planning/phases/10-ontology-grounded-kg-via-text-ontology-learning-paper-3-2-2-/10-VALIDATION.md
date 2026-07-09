---
phase: 10
slug: ontology-grounded-kg-via-text-ontology-learning-paper-3-2-2
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-02
approved: 2026-07-02
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Derived from the `## Validation Architecture` section of `10-RESEARCH.md` and the
> actual `<verify><automated>` blocks of the 11 committed plans.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (poetry-managed; run from `src/`) |
| **Config file** | `src/pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `cd src/ && poetry run pytest -m "not integration" -q` |
| **Full suite command** | `cd src/ && poetry run pytest` |
| **Estimated runtime (fast slice)** | < 30s (module-scoped unit tests) |
| **Estimated runtime (full incl. integration)** | ~2–5 min (live Neo4j fixtures) |
| **Headline acceptance runs (excluded from loop)** | 10-01-T1, 10-11-T1 — full 18-case LLM eval, minutes-long |

---

## Sampling Rate

- **After every task commit:** `cd src/ && poetry run pytest -m "not integration" -q` scoped to the touched module.
- **After every plan wave:** `cd src/ && poetry run pytest` (full suite including `-m integration` against live Neo4j).
- **Before `/gsd:verify-work`:** Full suite green + the smallest-slice E2E for the wave's vertical seam (10-02-T3 routing E2E; 10-07-T2 seed→build→link E2E; 10-11 A/B run).
- **Max feedback latency:** **30s** for the quick per-commit loop (`-m "not integration"`, module-scoped). EXCLUDES the two headline 18-case LLM eval acceptance runs (10-01-T1, 10-11-T1), which are minutes-long by design and are NOT per-commit gates.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-01-T1 | 10-01 | 1 | EVAL-02 / D-16 | T-10-01-01/02 | judge key env-only; rubric-parity judge | execution-acceptance (headline) | `ls results/evaluations/2026-07/eval-run-graphrag-tests-18-bdc4927d-*.json` + `python` assert `len(test_results)==18` | ❌ Wave 1 | ⬜ pending |
| 10-01-T2 | 10-01 | 1 | D-15 | — | — | artifact-assert (spike doc) | `test -f docs/project_notes/research/2026-07-02-neo4j-exact-vector-search-spike.md && grep -qiE "determinism (strategy\|decision)\|LOCKED"` | ❌ Wave 1 | ⬜ pending |
| 10-02-T1 | 10-02 | 1 | RAG-06 / D-16 | T-10-02-02/03 | static Cypher skeleton; no secret fields added | unit | `poetry run pytest ../tests/infrastructure/config/test_graph_provider_selection.py -x -q` | ❌ Wave 1 | ⬜ pending |
| 10-02-T2 | 10-02 | 1 | D-16 | T-10-02-01 | 4-allowlist membership; router explicit branches | unit | `poetry run pytest ../tests/rag/graph/retrieval/test_graphrag_ontology_routing.py -x -q` + allowlist grep gate (≥3, filtered) | ❌ Wave 1 | ⬜ pending |
| 10-02-T3 | 10-02 | 1 | D-16 | T-10-02-01 | provider-distinct routing; P9 untouched | e2e (integration) | `poetry run pytest ../tests/rag/graph/retrieval/test_graphrag_ontology_routing.py -k "e2e or provider_distinct" -q` | ❌ Wave 1 | ⬜ pending |
| 10-03-T1 | 10-03 | 1 | D-17 / D-14 / D-18 | T-10-03-03 | read-only regex parse, no eval | unit | `poetry run pytest ../tests/rag/graph/ontology/test_gold_relation_parser.py ../tests/rag/graph/ontology/test_coverage_check.py -x -q` | ❌ Wave 1 | ⬜ pending |
| 10-03-T2 | 10-03 | 1 | D-01/04/08/09/18 | T-10-03-01/02 | discovery LLM key env-only; no P9 graph input (D-02) | artifact-assert (draft schema) | `python` assert draft has D-08 layer + D-09 tags + all 14 D-18 relations | ❌ Wave 1 | ⬜ pending |
| 10-03-T3 | 10-03 | 1 | D-14 | T-10-03-01 | no unreviewed type reaches build | manual (checkpoint: curation gate a) | — (human approval; markup table + D-14/D-17 coverage report) | n/a | ⬜ pending |
| 10-04-T1 | 10-04 | 2 | D-05 (supply-chain) | T-10-04-SC | pypi legitimacy verified before install | manual (checkpoint: blocking-human pkg gate) | — (verify pypi.org/project/scikit-learn) | n/a | ⬜ pending |
| 10-04-T2 | 10-04 | 2 | D-05 | T-10-04-01 | cluster naming reviewed at gate b; no P9 graph input | unit | `poetry run pytest ../tests/rag/graph/ontology/test_method_b_clustering.py -x -q` | ❌ Wave 2 | ⬜ pending |
| 10-04-T3 | 10-04 | 2 | D-14 / D-01 / D-17 | T-10-04-02 | vocabulary lock only after coverage passes | manual (checkpoint: curation gate b + lock) | — (human approval; reconcile + coverage re-check) | n/a | ⬜ pending |
| 10-05-T1 | 10-05 | 3 | RAG-01/02 / D-10 / D-09 | T-10-05-01/02 | static parameterized Cypher; idempotent MERGE | integration (live Neo4j) | `poetry run pytest ../tests/rag/graph/ontology/test_clause_seeding.py -m integration -x -q` | ❌ Wave 3 | ⬜ pending |
| 10-05-T2 | 10-05 | 3 | D-10 | T-10-05-01 | — | cli-smoke | `poetry run ccop-eval graph seed-clauses --help` | ❌ Wave 3 | ⬜ pending |
| 10-06-T1 | 10-06 | 3 | D-11 | — | — | unit | `poetry run pytest ../tests/rag/graph/build/test_section_aligned_splitter.py -x -q` | ❌ Wave 3 | ⬜ pending |
| 10-06-T2 | 10-06 | 3 | D-11 | T-10-06-01/02 | schema-constrained downstream; reuse base JSON repair | unit | `poetry run pytest ../tests/rag/graph/build/test_gleaning_extractor.py -x -q` | ❌ Wave 3 | ⬜ pending |
| 10-07-T1 | 10-07 | 4 | D-06 / D-07 / D-11 | T-10-07-01/03 | locked vocab; ignore-illustrative prompt; key env-only | unit | `poetry run pytest ../tests/rag/graph/build/test_ontology_kg_builder.py -x -q` | ❌ Wave 4 | ⬜ pending |
| 10-07-T2 | 10-07 | 4 | D-10 / D-11 | T-10-07-02 | static parameterized linking Cypher | integration + e2e (seed→build→link) | `poetry run pytest ../tests/rag/graph/ontology/test_clause_linker.py -m integration -x -q` + `graph build-ontology --help` | ❌ Wave 4 | ⬜ pending |
| 10-08-T1 | 10-08 | 5 | D-13 (supply-chain) | T-10-08-SC | pypi legitimacy verified before install | manual (checkpoint: blocking-human pkg gate) | — (verify pypi.org rdflib + pyshacl) | n/a | ⬜ pending |
| 10-08-T2 | 10-08 | 5 | D-13 | T-10-08-01/02/03 | quarantine not delete; static export Cypher; trusted TTL | unit (in-memory rdflib) | `poetry run pytest ../tests/rag/graph/ontology/test_shacl_validation.py -x -q` | ❌ Wave 5 | ⬜ pending |
| 10-08-T3 | 10-08 | 5 | D-13 | — | gate on HIGH-severity conformance | cli-smoke | `poetry run ccop-eval graph validate --help` | ❌ Wave 5 | ⬜ pending |
| 10-09-T1 | 10-09 | 5 | D-12 / D-11 / D-15 | T-10-09-01 | static RETRIEVAL_QUERY; bound `$function_type`/`$boost` | unit | `poetry run pytest ../tests/rag/graph/retrieval/test_ontology_graph_retrieval_adapter.py -x -q` | ❌ Wave 5 | ⬜ pending |
| 10-09-T2 | 10-09 | 5 | D-12 | T-10-09-02/03 | classifier key env-only; enum-constrained output | unit | `poetry run pytest ../tests/rag/retrieval/nodes/test_function_type_routing.py -x -q` | ❌ Wave 5 | ⬜ pending |
| 10-10-T1 | 10-10 | 6 | D-15 | — | pure function, no external deps | unit | `poetry run pytest ../tests/domain/services/test_clause_hit_scoring_service.py -x -q` | ❌ Wave 6 | ⬜ pending |
| 10-10-T2 | 10-10 | 6 | D-15 / EVAL-03 | T-10-10-01/02 | deterministic; gold cross-checked vs D-17 xlsx | unit + integration + cli-smoke | `poetry run pytest ../tests/application/use_cases/test_clause_hit_harness.py -x -q` + `graph clause-hit --help` | ❌ Wave 6 | ⬜ pending |
| 10-11-T1 | 10-11 | 7 | EVAL-02 / D-16 | T-10-11-01/02 | judge key env-only; rubric parity; generator constant | execution-acceptance (headline) | `python` assert `len(test_results)==18` on graphrag-ontology run | ❌ Wave 7 | ⬜ pending |
| 10-11-T2 | 10-11 | 7 | EVAL-02 / EVAL-03 / D-16 | T-10-11-03 | no claim absent P9 baseline | unit + artifact-assert | `poetry run pytest ../tests/application/use_cases/test_ab_report.py -x -q` + `grep -qi "clause-hit@3" report` | ❌ Wave 7 | ⬜ pending |
| 10-11-T3 | 10-11 | 7 | D-16 | T-10-11-02 | parity + hedging confirmed | manual (checkpoint: A/B review) | — (human approval) | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*Every code-producing task has an `<automated>` verify. Checkpoint tasks (10-03-T3, 10-04-T1, 10-04-T3, 10-08-T1, 10-11-T3) are human gates with no automated command — see Manual-Only Verifications.*

---

## Wave 0 Requirements

Nyquist is satisfied per-task: every code task creates its own test file (RED) in the same task (tdd), so no `<automated>` block is MISSING at commit time. The only cross-task prerequisites (create before the first consuming test):

- [ ] **Shared Neo4j integration fixture/conftest** — reuse the Phase 9 pattern in `tests/rag/graph/retrieval/test_graph_retrieval_adapter_integration.py`'s `conftest.py` before the first integration test (10-05-T1 `test_clause_seeding.py`). Consumed by: 10-05-T1, 10-07-T2, 10-09 (live), 10-10-T2 (integration), 10-08 (live validate).
- [ ] **Gold-relation fixture cells** — a small fixture of `graph_relation` cell strings (incl. the `NOT DESIGNATED_AS` spacing case) for 10-03-T1 `test_gold_relation_parser.py`, so the parser test does not depend on the full live xlsx.
- [ ] **Scripted-LLM mock helper** — a reusable 2-call scripted-LLM mock for the mocked-extraction tests (10-03-T2, 10-04-T2, 10-06-T2, 10-07-T1, 10-09-T2). Establish in the first such test (10-03-T2) and reuse.

*New test directories created by this phase (mirror `src/`): `tests/rag/graph/ontology/`, `tests/rag/retrieval/nodes/` (if absent), plus additions under `tests/domain/services/`, `tests/application/use_cases/`, `tests/infrastructure/config/`.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Curation gate (a) — approve/amend Method-C draft | D-14 | Oversight-not-authoring human judgement | Present markup table (type \| definition \| example terms \| provenance \| flagged ambiguities) + D-14 benchmark-coverage + D-17 gold-relation coverage; capture approval (10-03-T3) |
| Curation gate (b) — reconcile B vs C, LOCK ontology | D-14 / D-01 / D-17 | Human keep/drop on B-only clusters; lock decision | Present reconcile report + re-run D-14/D-17 checks; approve; lock `ontology_config.json` with `additional_node_types=false` only after checks pass (10-04-T3) |
| Package legitimacy — scikit-learn | D-05 (supply chain) | `[ASSUMED]` pkg; slopcheck not run | Verify pypi.org/project/scikit-learn before `poetry add`; never auto-approve (10-04-T1, T-10-04-SC) |
| Package legitimacy — rdflib + pyshacl | D-13 (supply chain) | `[ASSUMED]` pkgs; slopcheck not run | Verify pypi.org for both before `poetry add`; never auto-approve (10-08-T1, T-10-08-SC) |
| A/B conclusions review | D-16 | Judgement on parity + hedging for n=18 | Confirm same 18 ids + rubric judge across 3 legs; confirm hedged claims; decide D-12 escalation (10-11-T3) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or are declared human gates (no MISSING blocks; checkpoints listed above)
- [x] Sampling continuity: no 3 consecutive code tasks without automated verify
- [x] Wave 0 covers all cross-task fixture prerequisites (shared Neo4j conftest, gold-relation fixture, scripted-LLM mock)
- [x] No watch-mode flags
- [x] Feedback latency < 30s for the per-commit loop (headline 18-case eval runs excluded by design)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-07-02
