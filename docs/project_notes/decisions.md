# Architectural Decisions

This file logs architectural decisions (ADRs) with context and trade-offs. Use bullet lists for clarity.

## Format

Each decision should include:
- Date and ADR number
- Context (why the decision was needed)
- Decision (what was chosen)
- Alternatives considered
- Consequences (trade-offs, implications)

---

## Decisions

### ADR-001: Clean Architecture / Hexagonal Pattern (2026-02-04)

**Context:**
- Need strict separation between domain logic and infrastructure concerns
- Want to enable testing without external dependencies (Ollama, file system)
- Framework-agnostic design for potential future changes

**Decision:**
- Use Clean Architecture with Ports & Adapters pattern
- Domain layer has zero dependencies on application/infrastructure
- Dependency injection via `dependency-injector` library
- All I/O operations through abstract ports

**Alternatives Considered:**
- Layered architecture (traditional) -> Rejected: less testability, implicit coupling
- Single-module script -> Rejected: doesn't scale with complexity
- Django/Flask built-in patterns -> Rejected: want framework independence

**Consequences:**
- More boilerplate (interfaces, adapters, DTOs)
- Excellent testability (mock any port)
- Clear boundaries between concerns
- Easy to swap implementations (e.g., Ollama -> HuggingFace API)

### ADR-002: Tiered Evaluation Strategy (2026-02-04)

**Context:**
- Different benchmarks require different scoring approaches
- Some benchmarks need exact matching, others need semantic similarity, others need LLM judges
- Want to minimize compute cost while maintaining accuracy

**Decision:**
- Tier 1 (B1-B6): Label-based and Jaccard scoring (fast, deterministic)
- Tier 2 (B8, B9, B11, B15, B17-B19): Semantic similarity with sentence-transformers
- Tier 3 (B7, B10, B12-B14, B16, B20-B21): LLM-as-judge for subjective evaluation

**Alternatives Considered:**
- All LLM-as-judge -> Rejected: expensive, slow, non-deterministic
- All exact matching -> Rejected: too strict, misses semantic equivalence
- Human review only -> Rejected: doesn't scale

**Consequences:**
- Efficient resource usage (fast tiers run first)
- Appropriate precision for each benchmark type
- Tier 3 requires external LLM calls (cost consideration)
- Clear separation of evaluation complexity

### ADR-003: Ollama for Local Inference (2026-02-04)

**Context:**
- Need to run inference on Llama-Primus-Reasoning model
- Want local development without API costs
- Need to support quantized models (GGUF)

**Decision:**
- Use Ollama as the primary inference engine
- Custom `OllamaClient` for HTTP API communication
- Support for model quantization via GGUF conversion

**Alternatives Considered:**
- HuggingFace Inference API -> Rejected: API costs, network dependency
- vLLM -> Rejected: more complex setup for local dev
- Direct transformers loading -> Rejected: memory requirements too high

**Consequences:**
- Easy local development setup
- Support for quantized models (Q4_K_M to Q8_0)
- Requires Ollama server running locally
- HTTP overhead vs in-process inference

### ADR-004: RAG First, Fine-Tuning on Remaining Gaps (2026-02-04)

**Context:**
- Baseline evaluation revealed clear split: reasoning benchmarks (59% avg) vs factual benchmarks (39% avg)
- Hallucination rate (B21) at 22% is a critical safety issue
- Fine-tuning alone cannot fix factual knowledge gaps (B4, B6 at 21%)
- Need to determine which gaps are retrieval problems vs reasoning problems

**Decision:**
- Implement RAG first using CCoP 2.0 document corpus
- Re-evaluate model against all 21 benchmarks with RAG
- Identify remaining gaps that RAG doesn't address
- Fine-tune only on benchmarks where reasoning (not retrieval) is the bottleneck

**Alternatives Considered:**
- Fine-tuning first, RAG later → Rejected: risk of reinforcing hallucination patterns
- Fine-tuning only → Rejected: can't fix factual gaps, regulatory updates require retraining
- Parallel implementation → Rejected: harder to isolate which approach fixes which gaps

**Consequences:**
- ✅ Hallucination addressed from day one (safety)
- ✅ Clear diagnosis: if RAG doesn't fix it, it's a reasoning problem
- ✅ Fine-tuning dataset becomes smaller and focused
- ✅ Regulatory updates handled by document refresh, not retraining
- ❌ Requires RAG infrastructure before seeing fine-tuning benefits
- ❌ Delays fine-tuning phase until RAG baseline established

**Expected Benchmark Impact:**
- RAG should improve: B1, B4, B5, B6, B18, B20, B21 (factual/grounding)
- RAG may not improve: B3, B8, B9, B11, B12, B15 (reasoning/judgment)
- Fine-tuning targets: benchmarks that remain low after RAG

### ADR-005: Default Evaluation Temperature 0.0 (2026-03-20)

**Context:**
- Default temperature was 0.7, causing different model responses on every run of the same test case
- Benchmark scores fluctuated between runs due to sampling randomness, not model capability
- Impossible to reliably measure whether code changes improved or degraded performance

**Decision:**
- Change default evaluation temperature from 0.7 to 0.3
- Low temperature reduces variance while preserving reasoning elaboration

**Alternatives Considered:**
- Keep 0.7 → Rejected: too much variance between runs for benchmarking
- 0.0 (fully deterministic) → Rejected: greedy decoding produced terse responses that scored poorly on reasoning rubrics (B3 dropped from 1/3 to 0/3)
- 0.1-0.2 → Not tested, 0.3 chosen as known middle ground

**Consequences:**
- More consistent evaluation results across runs (less variance than 0.7)
- Preserves reasoning depth in model responses (avoids greedy truncation at 0.0)
- Still not fully deterministic — slight variation between runs expected

---

### ADR-006: Deprecate `forbidden_claims` from Ground Truth & Scoring (2026-06-29)

**Context:**
- `fail_conditions.forbidden_claims` is model-generated and fed to the LLM judge as scoring priors.
- Stage-1 scan found contamination in 256/435 records — required-element descriptors
  ("Reference to applicable CCoP clause", "Evidence quality considerations") wrongly placed in the
  forbidden list (see `gt_audit_2026-04-28/stage1_defect_ledger.*`).
- The judge cites these entries in its rationale, so a model-hallucinated "prohibition" becomes a
  scoring criterion — a hallucination-amplification loop. Live example: B23 was penalised for
  "violating" `"Clear articulation of regulatory alignment"`, which is actually a *required* element.
- Negative space ("what a correct answer must NOT say") is unbounded and unverifiable — the
  highest-hallucination-risk, lowest-marginal-value part of the GT, and largely redundant with the
  judge's `factual_grounding` + `hallucination` dimensions and `expected_response`.

**Decision:**
- Deprecate `forbidden_claims` as a scoring input. Stop feeding it to the LLM judge; rely on the
  judge's grounding/hallucination dimensions + `expected_response`.
- Do NOT re-home entries into a `required_elements` field — that would only relocate the
  model-generated hallucination, not remove it.

**Alternatives Considered:**
- Shrink to curated red-lines → Rejected: curation needs human/expert authorship these don't have.
- Re-home contaminated entries to a rubric field → Rejected: relocates hallucination risk.

**Consequences:**
- Removes the judge-corruption / amplification loop; some previously-penalised cases may score higher.
- Stage-1 D-FORBIDDEN's 706 flags become moot (field removed, not fixed).
- Consumers to update: `domain/services/llm_judge_service.py`, `domain/services/scoring_service.py`,
  `rag/retrieval/nodes/generation.py`, `domain/entities/test_case.py`, JSONL repository/parsers.
- `fail_conditions.hallucination_patterns` is the same model-generated negative-space pattern and is
  a candidate for the same treatment — flagged for review.

---

### ADR-007: Phase 9 GraphRAG reports coarse chunking as an intrinsic OOTB limitation (2026-07-02)

**Context:**
- Phase 9 `--mode graphrag` scored judge 0.06 vs hybrid 0.44 on B01-001. One confound axis is
  chunk granularity: the graph uses neo4j-graphrag's default `FixedSizeSplitter` (4000 char /
  200 overlap, single-pass, no gleaning), while hybrid uses our clause-level Docling chunks.
- Question raised before Wave 6: is coarse chunking a fixable confound (re-chunk to clause units)
  or an intrinsic characteristic to report? Settled with a deep-research pass (see
  `docs/project_notes/research/2026-07-02-graphrag-chunking-regulatory.md`; mirrors Phase 9
  decisions D-20 / D-16a in `.planning/phases/09-.../09-CONTEXT.md`).

**Decision:**
- Phase 9 keeps the default coarse splitter and **reports coarse chunking as an intrinsic
  out-of-the-box limitation of the emergent baseline — not patched by re-chunking.**
- Wave-6 retrieval parity (rerank + sparse + `top_n` funnel cap to 3) proceeds — those are harness
  concerns, orthogonal to chunking.
- The clause-granularity fix is architectural and deferred to Phase 10 (clause-node seeding +
  clause-anchored fine retrieval + section-level extraction chunks, ideally with a gleaning/
  multi-pass step).

**Alternatives Considered:**
- Re-chunk the graph to clause units → Rejected ✗: verified to *starve relationship extraction*
  (both endpoints must co-occur in one chunk; arXiv 2605.28004) and adds a second variable to the
  P9→P10 ablation (breaks D-01). Also "bigger is simply better" is false — smaller chunks recover
  ~2× entities (arXiv 2404.16130v2), which the field fixes with gleaning that neo4j-graphrag lacks.
- Defer entire chunk decision to Phase 10 without recording rationale → Rejected ✗: leaves the
  Wave-6 confound narrative undocumented.

**Consequences:**
- Wave-6 graphrag-vs-hybrid comparison must explicitly caveat coarse chunking as a reported OOTB
  characteristic, with citations — a defensible dissertation narrative, not an excuse.
- ⚠️ Phase 10 risk carried forward: clause-node seeding alone is insufficient — retrieval must be
  re-anchored on clause nodes, else the 4000-char return-unit confound rides into Phase 10.

---

### ADR-008: Backward compatibility MUST be maintained per pipeline `mode` (2026-07-04)

**Context:**
- The RAG pipeline exposes multiple `mode`s that grow over time: `llm-only`, `hybrid`,
  `rag-only`, `graphrag`, `graphrag-retrieval`, `graphrag-ontology`, and the incoming
  `graph-compliance` (Phase 11-09). Modes share downstream LangGraph nodes (retrieval →
  reranking → grade → generate) and shared config/DI/allowlists.
- This creates a standing regression risk: wiring a NEW mode can silently alter an EXISTING
  mode's behavior. This is the exact "multi-allowlist" class the project keeps re-hitting
  (see D-16/D-19/D-20 decision tokens; the `~/.claude/rules/e2e-testing.md` Phase 9 example
  where a new `graphrag` mode passed mocked tests but a second `RunId._VALID_MODES` allowlist
  was missed).
- User directive (2026-07-04): each mode must stay backward-compatible going forward.

**Decision:**
- Any change that adds or modifies a `mode` MUST be **strictly additive** with respect to every
  other mode. Existing modes' routing outcomes, retrieval semantics, node behavior, and output
  contracts must be preserved unchanged.
- New behavior lives behind the new mode's own routing branch (mirroring `route_by_mode`'s
  additive `graphrag`/`graphrag-ontology` branches, where `hybrid` falls through to the
  unchanged default `retrieval` node). Shared nodes may only be changed in ways that are
  provably behavior-preserving for pre-existing modes.
- Every mode-touching change carries a backward-compat verification: diff the shared-path files
  and confirm pre-existing modes are behavior-identical, plus a smallest-slice E2E per affected
  mode. Reference precedent: the Phase 11 Wave-1 audit confirmed phases 9/10/11 left the shared
  hybrid code path byte-identical to pre-phase-9 (only additive early-return branches added).

**Alternatives Considered:**
- Refactor the shared retrieval path per-mode as needed → Rejected ✗: reintroduces exactly the
  silent cross-mode regression class this ADR exists to prevent.
- Rely on tests without a formal rule → Rejected ✗: mocked unit tests already missed a second
  allowlist once (the e2e-testing rule's own cautionary example).

**Consequences:**
- Mode wiring must update ALL allowlist/gating sites in one change (routing, `RunId._VALID_MODES`,
  DI container, settings, CLI, adapter validation) — never a subset.
- ⚠️ **Data caveat (separate compat surface):** shared retrieval indices (e.g. the
  `ccop_clauses_hybrid` Qdrant collection) are NOT covered by code-level backward compat. Every
  mode reading a collection is affected when that collection is re-ingested (e.g. Phase 11 Wave 0
  rebuilt `ccop_clauses_hybrid`, changing hybrid retrieval vs the frozen canonical baseline).
  Corpus/index changes must be treated as explicit, announced decisions — not silent — and any
  frozen baseline they invalidate must be re-noted or regenerated.

**Scope note (2026-07-04) — retired modes are an explicit exception:** `graphrag`,
`graphrag-retrieval`, and `graphrag-ontology` (Phase 9/10) are **retired**, superseded by
`graph-compliance` (Phase 11). Their Neo4j substrate (the emergent entity graph) was deleted and
will not be maintained or rebuilt. Their breakage is therefore **not** a backward-compat
regression under this ADR — the compat guarantee applies to *live* modes (`llm-only`, `hybrid`,
`rag-only`, `graph-compliance`). Do not "fix" a non-functional graphrag mode; if fully removing
its code/allowlist entries, do so as a deliberate deprecation, not a silent edit.

---

### ADR-009: Phase 12 `graphont-agentic` revised to rev 02 after peer-reviewed research critique (2026-07-13)

**Context:**
- Phase 12 (`12-01-PLAN.md`) proposed a bounded agentic retrieval-quality loop on `graphont`.
- A two-model research team (Roberto/Robin) produced a peer-reviewed critique:
  `research/20260713-agentic-rag-critique/FINAL-agentic-rag-critique.md`. It affirmed the
  strategy/architecture but flagged concentrated weaknesses.

**Decision:**
- Adopt `12-02-PLAN.md` (supersedes `12-01`). Key revisions:
  - **Detector = two-tier deterministic gate** (hard-failure OR sentinels + calibrated soft
    consensus/AND over rank-normalized pre-generation features) instead of a wide OR of soft
    thresholds (reranker scores certify topicality, not answer support; wide OR over-fires).
  - **Action routing derived from an offline action-oracle**, not intuition.
  - **Removed the post-generation "citation-present-in-context" signal from the runtime detector**
    (offline diagnostic only) — it is not knowable pre-generation.
  - **Graph expansion must be typed, hub-safe, provenance-first** (guards the `CII` hub ≈⅓ of the
    graph against Static-Graph-Fallacy / hub-drift).
  - **Evaluation requires disjoint calibration/held-out/test splits**, pooled expert adjudication,
    full-chain retrieval metric, and retry-ablation + action-oracle counterfactuals.
  - **Retrieval recall vs GT is the PRIMARY success metric; D6 is secondary/observational** —
    improved clause recall with flat D6 is still a Phase 12 success (citation behavior is out of
    scope; Slice 1.5 remains excluded).
- All `12-01` locked decisions, the additive/backward-compatible mode (per ADR-008), GT-offline-only,
  and the RoG/ReAct/query-reformulation deferrals are retained unchanged.
- **`graphont` parity is a HARD, BLOCKING acceptance gate (applies ADR-008 to Phase 12):** `graphont`
  must remain usable and behavior-identical for future evaluation/comparison after `graphont-agentic`
  ships. Before the new mode is activated, `graphont` is verified **byte/structure-identical**
  (candidate order → packed context → generation prompt) via golden traces captured *before* the Slice B
  node split; a parity failure **blocks the phase**. All new behavior is gated on
  `mode == "graphont-agentic"` only, behind a feature flag that can be disabled without reverting the
  refactor.
- **Phase 12 MUST NOT modify the shared corpus/index** (`ccop_clauses_hybrid`). Per ADR-008's
  data-surface caveat, re-ingesting/changing the index shifts `graphont` retrieval even with identical
  code and invalidates the frozen baseline — explicitly out of scope; Phase 12 only adds retry logic
  over the existing collection.

**Alternatives Considered:**
- Keep `12-01` as-is → Rejected ✗: leaves the over-firing detector, intuition-based routing, and a
  calibration set that both tunes and validates (overfit risk).
- Rewrite scope toward full 2026 agentic RAG (RoG/reformulation/answer-verification) → Rejected ✗:
  breaks the clean deterministic causal experiment; deferral judged justified.

**Consequences:**
- New nodes/state fields (`assess_retrieval_quality` two-tier, `plan_requery`, traversal provenance).
- Added labeling cost (pooled adjudication + action-oracle over the calibration set).
- Phase 12 is judged on retrieval recall, not D6 — update any dashboard/report that assumed D6 as the
  Phase 12 pass bar.
- References: `12-02-PLAN.md`; `research/20260713-agentic-rag-critique/FINAL-agentic-rag-critique.md`.

---

### ADR-010: Contextual Retrieval is opt-in; default hybrid uses the base collection (2026-07-27)

**Context:**
- `--mode hybrid` routed to the Contextual-Retrieval collection (`ccop_clauses_contextual_v3`) whenever `rag_contextualization_enabled=True` (the old default).
- That collection is built only by uncommitted lab scripts (`.lab/workspace/contextualize_corpus*.py`) and persisted to gitignored `qdrant_storage/`. In any environment where it wasn't rebuilt, hybrid retrieval 404'd and silently fell back to parametric LLM-only — an invalid, misleading "hybrid" result.
- The base collection `ccop_clauses_hybrid` (303 pts) is always present.

**Decision:**
- Flip the global default `rag_contextualization_enabled` from `True` → `False`. Contextual Retrieval is now **opt-in**.
- Add an `evaluate run --contextual/--no-contextual` flag (mirrors `--hyde`) that overrides per run; default OFF.
- Default hybrid now retrieves from the base `ccop_clauses_hybrid` collection — no dependency on a collection that can't be rebuilt from the repo.

**Alternatives Considered:**
- Keep default ON → Rejected: assumes a collection that isn't reproducible from version control; fails opaquely.
- Default-off only in the eval command, leave global `True` → Rejected: `query ask` and other readers would still fail opaquely; global honesty preferred.

**Consequences:**
- ✅ Fresh environments get a working `--mode hybrid` with no hidden dependency.
- ⚠️ Behavior change: the canonical hybrid baseline (`eval-run-hybrid-tests-18-bdc4927d`, 2026-04-30) was produced with contextualization **ON**. Plain `--mode hybrid` is no longer directly comparable to it — use `--contextual` (with the collection rebuilt) to reproduce that config.
- Productionization debt remains: the contextual-collection build should become a real `ccop-eval ingest` step and the lab scripts committed (tracked separately in `gt-improvements`/project notes).

---

### ADR-011: HyDE is opt-in; default OFF across all retrieval modes (2026-07-28)

**Context:**
- HyDE was default ON for `hybrid`/`rag-only` (`rag_hyde_enabled=true` in `.env.example`) but default OFF for `graphont` and `graphont-agentic`.
- That asymmetry confounds cross-mode comparison: a hybrid-vs-graphont delta partly reflects HyDE on-vs-off, not just retrieval architecture.

**Decision:**
- Flip `rag_hyde_enabled` default `True` → `False` (code + `config/.env.example`). All modes now default HyDE **off**.
- Opt in per run with `evaluate run --hyde` (sets the rag/graphont/graphont-agentic HyDE env vars together).

**Consequences:**
- ✅ All four report modes share the same HyDE state by default — cleaner comparison.
- ⚠️ Diverges from the canonical hybrid baseline (`bdc4927d`, built with HyDE ON) and from the two already-captured hybrid report runs (both `hyde_rag=true`) — re-run those with the new default (or `--hyde`) for a consistent dataset.
- Provenance (`retrieval_config.hyde_rag` / `hyde_graphont_agentic`) records the actual per-run state either way.

---

## Tips

- Number decisions sequentially (ADR-001, ADR-002, etc.)
- Always include date for context
- Be honest about trade-offs (use checkmarks and crosses)
- Keep alternatives brief but clear
- Update decisions if they're revisited/changed
