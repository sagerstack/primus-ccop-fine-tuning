---
phase: 09-basic-graphrag-reference-baseline-microsoft-graphrag-package
plan: 01
subsystem: infra
tags: [neo4j, neo4j-graphrag, graphrag, docker, apoc, pydantic-settings, openrouter, bge-large-en-v1.5, gpt-4o-mini]

# Dependency graph
requires:
  - phase: 01.2-local-rag-migration
    provides: "docker-compose qdrant service pattern + BAAI/bge-large-en-v1.5 embedder (CCOP_QDRANT_EMBEDDING_MODEL)"
  - phase: 01.3-rag-quality-chunking
    provides: "OpenRouter gpt-4o-mini as configured RAG-infra LLM (rag_contextualization_model precedent)"
provides:
  - "Local Neo4j Docker service (5.26 LTS, APOC, localhost-bound 7474/7687, persistent volume)"
  - "neo4j-graphrag + neo4j Poetry dependencies (installed, importable)"
  - "Pydantic Neo4j connection settings (neo4j_uri/user/password/database)"
  - "Interceptable GraphRAG model settings: graph_extraction_model (gpt-4o-mini, D-06a), graph_embedding_model (bge-large-en-v1.5, D-07), graph_embedding_dimensions (1024), graph_vector_index_name"
  - "CCOP_NEO4J_* env documentation (placeholder-only, no secrets)"
affects: [09-02-graph-build, 09-03-graph-retrieval-provider, 09-04-graph-cli-inspect, 10-ontology-grounded-kg]

# Tech tracking
tech-stack:
  added: [neo4j-graphrag ^1.18.0, neo4j ^6.2.0, "neo4j:5.26-community docker image"]
  patterns: ["Interceptable model-config seam (standalone graph_extraction_model/graph_embedding_model fields held constant across Phase 9/10 for the D-16 additivity ablation)", "Per-dependency python marker to scope a package that caps below the project's declared range", "Secret via ${CCOP_NEO4J_PASSWORD} env only; placeholder in .env.example, key in gitignored .env.local"]

key-files:
  created:
    - tests/infrastructure/config/test_neo4j_settings.py
    - .planning/phases/09-basic-graphrag-reference-baseline-microsoft-graphrag-package/deferred-items.md
  modified:
    - docker-compose.yml
    - .gitignore
    - src/pyproject.toml
    - src/infrastructure/config/settings.py
    - src/config/.env.example

key-decisions:
  - "neo4j-graphrag carries an explicit python marker (>=3.10,<3.15) — Poetry's recommended fix for the project's ^3.10 (>=3.10,<4.0) range vs the package's <3.15 cap; avoids narrowing the root python constraint and re-locking unrelated packages"
  - "poetry.lock left uncommitted — repo gitignores it (.gitignore line 86); regenerable via poetry install"
  - "graph_vector_index_name uses alias=CCOP_GRAPH_VECTOR_INDEX so the env var is CCOP_GRAPH_VECTOR_INDEX (not the auto-derived ..._NAME)"
  - "Extraction + embedding kept as standalone interceptable fields (not folded into a dict) so Phase 10 can layer ontology governance additively (D-16)"

patterns-established:
  - "Interceptable GraphRAG model seam: graph_extraction_model / graph_embedding_model are explicit fields documented as held constant across Phase 9 and Phase 10"
  - "Neo4j service mirrors the qdrant docker-compose shape (localhost-bound ports, persistent volume, healthcheck, restart: unless-stopped)"

requirements-completed: [D-01, D-06a, D-07, D-12]

# Metrics
duration: 109min
completed: 2026-07-01
---

# Phase 9 Plan 01: Neo4j GraphRAG Foundation Summary

**Local Neo4j 5.26 (APOC) Docker service + neo4j-graphrag/neo4j Poetry deps + Pydantic Neo4j connection settings and interceptable gpt-4o-mini extraction / bge-large-en-v1.5 (1024-dim) embedding model config — pure infra/config, no graph built, no credential committed.**

## Performance

- **Duration:** 109 min wall (includes a blocking package-legitimacy checkpoint pause for human approval; active execution was a small fraction of this)
- **Started:** 2026-07-01T11:16:52Z
- **Completed:** 2026-07-01T13:06:25Z
- **Tasks:** 3 (Task 1 = human-verify gate, approved; Tasks 2–3 executed)
- **Files modified:** 5 modified + 2 created (7 total)

## Accomplishments
- Verified both packages as official Neo4j, Inc. publications via live PyPI metadata, then passed the blocking-human legitimacy gate on approval.
- Stood up a local `neo4j` Docker service (5.26-community LTS, APOC plugin, ports bound to 127.0.0.1 only, persistent `./neo4j_storage` volume, healthcheck) alongside the existing qdrant service — container NOT started (deferred to Wave 2 pending the real password).
- Installed `neo4j-graphrag ^1.18.0` + `neo4j ^6.2.0`; both import cleanly (`neo4j 6.2.0`, `neo4j_graphrag 1.18.0`).
- Added Neo4j connection settings and the two interceptable GraphRAG infrastructure-model settings (extraction gpt-4o-mini via OpenRouter D-06a; embeddings bge-large-en-v1.5 @ 1024-dim D-07), all with no committed secret.

## Task Commits

1. **Task 1: Package legitimacy gate** — no commit (checkpoint; human approved packages before install)
2. **Task 2: Neo4j Docker service + Poetry deps** — `2f095cc` (feat)
3. **Task 3: Neo4j + graph-model settings + env docs** — `e80def2` (test, RED) → `ec94bdc` (feat, GREEN)

_TDD: Task 3 followed RED (9 failing) → GREEN (9 passing). No REFACTOR commit needed._

## Files Created/Modified
- `docker-compose.yml` — added `neo4j` service (5.26-community, APOC, localhost-bound 7474/7687, `NEO4J_AUTH=neo4j/${CCOP_NEO4J_PASSWORD}`, persistent volume, healthcheck)
- `.gitignore` — ignore `neo4j_storage/` (mirrors `qdrant_storage/`)
- `src/pyproject.toml` — `neo4j-graphrag ^1.18.0` (python `>=3.10,<3.15` marker) + `neo4j ^6.2.0`
- `src/infrastructure/config/settings.py` — Neo4j connection fields + interceptable graph extraction/embedding/vector-index settings
- `src/config/.env.example` — documented `CCOP_NEO4J_*` block (password placeholder only)
- `src/config/.env.local` (gitignored, not committed) — `CCOP_NEO4J_PASSWORD=` key placeholder for local setup
- `tests/infrastructure/config/test_neo4j_settings.py` — 9 tests pinning connection + model defaults (env-file-independent)

## Decisions Made
- **python marker on neo4j-graphrag** — the package caps at `<3.15` while the project declares `^3.10` (`>=3.10,<4.0`), so Poetry refused across the `[3.15,4.0)` sub-range. Applied Poetry's own recommended fix: a per-dependency `python = ">=3.10,<3.15"` marker. Surgical — no change to the root python constraint, no re-lock of unrelated packages. Runtime is 3.13.
- **poetry.lock not committed** — repo intentionally gitignores it (`.gitignore` line 86). Respected the existing convention over the plan's `files_modified` list (CLAUDE.md precedence). Lock is regenerable from pyproject via `poetry install`.
- **alias for CCOP_GRAPH_VECTOR_INDEX** — field `graph_vector_index_name` with `alias="CCOP_GRAPH_VECTOR_INDEX"` yields the exact env var the plan specifies (not the auto-derived `CCOP_GRAPH_VECTOR_INDEX_NAME`). Verified override + full env-file load both work.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] neo4j-graphrag python-range conflict blocked `poetry add`**
- **Found during:** Task 2 (poetry add)
- **Issue:** `poetry add neo4j-graphrag neo4j` failed — project's `^3.10` range includes 3.15+, but neo4j-graphrag requires `<3.15`, so version solving failed.
- **Fix:** Added a scoped `python = ">=3.10,<3.15"` marker on the `neo4j-graphrag` dependency in `pyproject.toml` (Poetry's recommended resolution), then `poetry lock` + `poetry install` succeeded.
- **Files modified:** `src/pyproject.toml`
- **Verification:** `poetry run python -c "import neo4j, neo4j_graphrag"` exits 0; both versions print.
- **Committed in:** `2f095cc` (Task 2 commit)

**2. [Scope boundary - not fixed] poetry.lock gitignored — deviated from plan `files_modified`**
- **Found during:** Task 2 (commit)
- **Issue:** Plan lists `src/poetry.lock` in `files_modified`, but the repo gitignores `poetry.lock` (`.gitignore` line 86).
- **Resolution:** Respected the repo convention — did not force-commit the lock. Documented here. Lock regenerable via `poetry install`.

---

**Total deviations:** 1 auto-fixed (Rule 3 blocking) + 1 convention-driven omission (poetry.lock).
**Impact on plan:** Both necessary to complete the install correctly and honor repo conventions. No scope creep.

## Issues Encountered

**Pre-existing test failures (out of scope, NOT fixed):** The full `poetry run pytest -m "not integration"` run surfaced 9 failures in `tests/domain/services/test_llm_judge_service.py` (`TypeError: unhashable type: 'dict'`). Confirmed **pre-existing and unrelated to 09-01**: commit `a34c18c` ("migrate LLMJudgeService from Claude CLI to OpenRouter") changed `_build_judge_prompt`'s third argument from a rubric dict to `benchmark_id: str`, but the test file (last touched in `6b134e3`, which predates the migration) still passes a dict. `git merge-base --is-ancestor a34c18c 4efc77e` = YES (migration predates the 09-01 base). A `dict`-unhashable Python error cannot originate from the neo4j-graphrag transitive dependency downgrades. Logged to `deferred-items.md`. This plan's own tests (9/9) and all other collected tests pass (40 passed).

## User Setup Required

**Neo4j requires one manual step before the container can start:**
- Set a value for `CCOP_NEO4J_PASSWORD` in `src/config/.env.local` (gitignored). The key placeholder is already present. It must match `docker-compose` `NEO4J_AUTH`.
- Then start the service (Wave 2): `docker compose up -d neo4j` (from repo root). Browser at `http://localhost:7474`, Bolt at `bolt://localhost:7687`.
- Per coordinator instruction, the container was NOT started in this plan.

## Next Phase Readiness
- Neo4j service is defined and startable; deps installed and importable; settings expose connection + interceptable extraction/embedding models. Ready for 09-02 (graph build) once the password is keyed in and the container is up.
- **Blocker for Wave 2:** `CCOP_NEO4J_PASSWORD` still empty — user must set it before `docker compose up neo4j`.
- **Carry-forward:** transitive downgrades from neo4j-graphrag (torch 2.12→2.7.1, numpy, matplotlib, etc.) — existing suite otherwise unaffected; watch for any embedder/RAGAs behavior changes in later plans.

## Self-Check: PASSED

All created/modified files exist on disk; all three task commits (`2f095cc`, `e80def2`, `ec94bdc`) present in git history.

---
*Phase: 09-basic-graphrag-reference-baseline-microsoft-graphrag-package*
*Completed: 2026-07-01*
