# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Objective

Fine-tune and evaluate an LLM (`Llama-Primus-Reasoning`) on Singapore's Cybersecurity Code of Practice (CCoP 2.0) for Critical Information Infrastructure. The repository hosts the **evaluation framework** (test suite + scoring + RAG-augmented inference) used to measure baseline and improved model performance.

Read the project paper: [Primus-Fine-Tuning-CCOP2-SG-v2.0-SagarPratapSingh-1010736.md](report/term1-mid/Primus-Fine-Tuning-CCOP2-SG-v2.0-SagarPratapSingh-1010736.md)

## High-Level Architecture

The codebase is a Python application split into two collaborating bounded contexts under `src/`:

1. **Evaluation engine** (`src/{domain,application,infrastructure,presentation}/`) — Clean Architecture / Ports & Adapters
   - `domain/` — pure entities, value objects, scoring services (no external deps)
   - `application/` — use cases, DTOs, ports (depends on domain only)
   - `infrastructure/` — adapters (Ollama client, JSON repository, settings, DI container)
   - `presentation/cli/` — Typer-based CLI; entry point `ccop-eval` → `presentation.cli.main:app`

2. **RAG subsystem** (`src/rag/`) — its own DDD slice (`domain/`, `application/`, `infrastructure/`, `ingestion/`, `retrieval/`, `citations/`, `presentation/cli/`)
   - LangGraph-orchestrated retrieval pipeline (`rag/retrieval/graph.py` builds the graph; nodes in `rag/retrieval/nodes/`)
   - Qdrant local vector store (hybrid dense + BM25 sparse via fastembed)
   - Citation resolver/formatter for clause-grounded answers
   - Exposed to the evaluator via `--mode hybrid` (RAG-augmented) vs `--mode llm-only`

**Dependency rule:** `domain` imports nothing project-specific; `application` imports `domain`; `infrastructure` and `presentation` import via DI container (`infrastructure/config/container.py`). The RAG slice mirrors this.

**Test suite location:** `ground-truth/test-suite/` (one JSONL per benchmark). The `Settings.test_cases_dir` default is `../ground-truth/test-suite` (relative to `src/`).

**Results location:** `src/results/evaluations/` (one JSON per run, plus `.partial.jsonl` rolling log and optional `-contexts.json` sidecar for retrieved-context audit).

## Benchmarks (Active Set)

**18 active benchmarks, 435 test cases total** (as of 2026-04-30). Benchmark IDs are non-contiguous because some originally-planned benchmarks (B11, B15, B16, B17, B19, B20) have no JSONL test files in the active suite.

| ID | File | n |
|---|---|---|
| B01 | `b01_ccop_applicability_scope` | 25 |
| B02 | `b02_compliance_classification` | 25 |
| B03 | `b03_conditional_compliance_reasoning` | 30 |
| B04 | `b04_it_ot_classification_boundary` | 25 |
| B05 | `b05_control_comprehension` | 25 |
| B06 | `b06_intent_understanding` | 20 |
| B07 | `b07_gap_identification_quality` | 30 |
| B08 | `b08_risk_based_prioritization` | 25 |
| B09 | `b09_risk_identification_residual_risk` | 25 |
| B10 | `b10_risk_justification_coherence` | 20 |
| B12 | `b12_audit_perspective_alignment` | 20 |
| B13 | `b13_evidence_expectation_awareness` | 20 |
| B14 | `b14_remediation_quality_feasibility` | 30 |
| B18 | `b18_responsibility_attribution_sg` | 25 |
| B21 | `b21_hallucination_over_specification` | 25 |
| B22 | `b22_waiver_exception_reasoning` | 20 |
| B23 | `b23_multi_regulator_coordination` | 20 |
| B24 | `b24_incident_response_guidance` | 25 |

**Internal inconsistency to be aware of:** `src/domain/value_objects/evaluation_tier.py` and `evaluation_category.py` still reference benchmark IDs (B11, B15-B17, B19, B20) that don't exist as active JSONL files. When working with tier/category lookups, verify against the file system before acting on the code's static lists.

**Stratified validation sample:** 18-case subset (`bdc4927d` hash) — one test case per active benchmark, used as the test bed for LLM-Judge κ validation. Latest results in `src/results/evaluations/2026-04/eval-run-{hybrid,llm-only}-tests-18-bdc4927d-*.json`.

## Build, Run, Test

All commands run from `src/`. Poetry is the only supported package manager.

```bash
# Install
cd src/ && poetry install

# Prereqs check (Ollama, Qdrant, model availability)
poetry run ccop-eval setup check

# Setup model (downloads from HF, converts to GGUF, registers with Ollama)
poetry run ccop-eval setup model
poetry run ccop-eval setup model --hf-repo trendmicro-ailab/Llama-Primus-Reasoning \
    --model-name primus-reasoning --quantization Q5_K_M

# Local Qdrant (vector store for RAG)
docker compose up -d qdrant   # from repo root; persists to ./qdrant_storage
```

### Evaluation

```bash
# Default: hybrid mode (RAG), all 18 benchmarks, baseline phase (15% threshold)
poetry run ccop-eval evaluate run --model primus-reasoning

# Mode toggle
poetry run ccop-eval evaluate run --model primus-reasoning --mode llm-only
poetry run ccop-eval evaluate run --model primus-reasoning --mode hybrid

# Scoping (combinable as flags; --tier overrides --benchmarks)
--benchmarks B1 --benchmarks B3 --benchmarks B21    # specific benchmarks
--tier 1                                            # tier-based selection
--test-ids B3-001 --test-ids B3-002                 # specific cases

# Phase / threshold
--phase baseline   # 15% pass threshold (default)
--phase finetuned  # 50%
--phase deployment # 85%
--threshold 0.5    # explicit override (0.0-1.0)

# Judge config
--judge-mode rubric     # per-benchmark rubrics (default)
--judge-mode universal  # universal reasoning-depth + hallucination judge

# Diagnostics
--verbose      # surface rag.retrieval.* logs (TOC filter, RRF, parent-merge)
--verbose-io   # capture system/user prompts and retrieved contexts per case

# Resume a partial run (skips completed cases; bails if config has drifted)
poetry run ccop-eval evaluate run --model primus-reasoning --mode hybrid --resume

# Re-score an existing run with a new judge config (no model re-inference)
poetry run ccop-eval evaluate rescore --run-id <run-id>
```

### Reporting

```bash
poetry run ccop-eval report summary --model primus-reasoning
poetry run ccop-eval report generate --model primus-reasoning --format markdown --output report.md
# Formats: json (default), markdown, html, csv
```

### Query (interactive RAG)

```bash
poetry run ccop-eval query ask "What are the access control requirements?"
poetry run ccop-eval query ask "..." --mode rag-only      # retrieval only, no LLM generation
poetry run ccop-eval query ask "..." --mode llm-only      # LLM, no retrieval
poetry run ccop-eval query ask "..." --verbose            # surface retrieval diagnostics
```

### Ground-Truth Validation

```bash
poetry run ccop-eval validate-ground-truth   # validates all v2 JSONL files against the clause inventory
```

### Tests

```bash
cd src/ && poetry run pytest                                    # all tests + coverage report (term + html + xml)
poetry run pytest ../tests/domain/                              # one layer
poetry run pytest ../tests/rag/retrieval/test_citation_resolver.py  # one file
poetry run pytest -k "citation"                                 # by name
poetry run pytest -m integration                                # integration-marked only (require Databricks etc.)
poetry run pytest -m "not integration"                          # exclude integration

# Coverage outputs: src/htmlcov/index.html, src/coverage.xml
```

Coverage targets are configured in `src/pyproject.toml` (`[tool.pytest.ini_options]`) covering `domain`, `application`, `infrastructure`, `presentation`, `rag`.

## Configuration

Environment variables, prefix `CCOP_`. Loaded by `src/infrastructure/config/settings.py` (Pydantic Settings). Important keys:

- **Ollama:** `CCOP_OLLAMA_HOST` (default `http://localhost:11434`), `CCOP_OLLAMA_TIMEOUT`
- **Model:** `CCOP_MODEL_NAME`, `CCOP_MODEL_HF_REPO`, `CCOP_MODEL_QUANTIZATION` (default `Q5_K_M`)
- **Judge:** `CCOP_JUDGE_PRIMARY_MODEL`, `CCOP_JUDGE_SECONDARY_MODEL`, `CCOP_JUDGE_TEMPERATURE`, `CCOP_JUDGE_MAX_RETRIES`, `CCOP_JUDGE_JSON_RETRY_ATTEMPTS`, `CCOP_OPENROUTER_API_KEY` (judge runs via OpenRouter)
- **Phases:** `CCOP_BASELINE_THRESHOLD` (0.15), `CCOP_FINETUNED_THRESHOLD` (0.50), `CCOP_DEPLOYMENT_THRESHOLD` (0.85)
- **Generation defaults:** `CCOP_DEFAULT_TEMPERATURE`, `CCOP_DEFAULT_TOP_P`, `CCOP_DEFAULT_TOP_K`, `CCOP_DEFAULT_MAX_TOKENS`, `CCOP_CONTEXT_LENGTH`
- **RAG:** `CCOP_RAG_GRADING_ENABLED`, `CCOP_RAG_RETRIEVAL_TOP_K`, `CCOP_PREAMBLE_MAX_WORDS`, `CCOP_SECTION_CHUNK_MIN_TOKENS`, `CCOP_SECTION_CHUNK_MAX_TOKENS`, `CCOP_DIAGRAM_CAPTIONING_ENABLED`
- **Databricks (optional):** `CCOP_DATABRICKS_*` for the alternative vector-search adapter

## Project Memory System

Institutional knowledge lives in `docs/project_notes/`. **Read these before proposing changes that overlap with prior work.**

- `bugs.md` — bug log with dates, solutions, prevention notes
- `decisions.md` — Architectural Decision Records (ADRs)
- `key_facts.md` — project configuration, ports, URLs (note: some benchmark assertions in this file are stale; trust the file system + this CLAUDE.md for benchmark IDs)
- `issues.md` — work log with ticket IDs and URLs
- `gt_audit_2026-04-28/` — in-progress ground-truth audit findings

### Memory-Aware Protocols

- **Before proposing architectural changes** — check `decisions.md`; if proposal conflicts with an ADR, acknowledge it and explain why a change is warranted.
- **When debugging** — search `bugs.md` for similar issues; document new bug+fix when resolved.
- **When constructing CLI commands** — check the `Build, Run, Test` section above (or `key_facts.md`'s "CLI Commands" section) before inferring command syntax from filesystem exploration.
- **When closing a ticket** — append to `issues.md` with date, ticket ID, brief description, URL.

### Memory Style

Bullet lists over tables, 1–3 line entries, dates always, URLs included for tickets/dashboards. Manual cleanup of old entries is expected.

## Repository Layout

```
studio-ssdlc/
├── src/                          # All source code; CLI runs from here
│   ├── pyproject.toml
│   ├── domain/ application/ infrastructure/ presentation/
│   ├── rag/                      # RAG subsystem (its own DDD slice)
│   ├── results/evaluations/      # Run outputs
│   └── scripts/                  # setup_ollama.sh, convert_to_gguf.sh, etc.
├── tests/                        # pytest suite (mirrors src/ layers)
├── ground-truth/
│   └── test-suite/               # JSONL test cases (active benchmarks)
├── ccop-official/                # Official CCoP 2.0 PDFs + supplementary docs
├── docs/
│   ├── phase-1/                  # Original term-1 design docs
│   ├── phase-2/                  # Term-2 evaluation rubrics, expansion plans
│   └── project_notes/            # Memory system (see above)
├── prompts/                      # System/user prompt templates
├── notebooks/                    # Experimental Jupyter notebooks
├── report/                       # Term submissions (term1-mid/end, term2-mid/end)
├── docker-compose.yml            # Qdrant local
└── qdrant_storage/               # Qdrant persisted data (gitignored)
```

**Skip:** `research/archived*` folders — not relevant to current context.

## Project References

### Regulatory & Standards
- [CSA Singapore — Codes of Practice](https://www.csa.gov.sg/legislation/codes-of-practice)
- [CCoP Second Edition Revision One PDF](https://isomer-user-content.by.gov.sg/36/2df750a7-a3bc-4d77-a492-d64f0ff4db5a/CCoP---SecondEdition_Revision-One.pdf)
- Local: `ccop-official/CCoP---Second-Edition_Revision-One.pdf`
- `ccop-official/RESPONSE-TO-FEEDBACK.pdf` — official clarifications
- `ccop-official/supplementary/` — auditing guidelines, threat modelling, risk assessment, security-by-design
- `ccop-official/references/Ensign's_Cybersecurity_Guide_on_CCoP_2_0_for_CII_Sep_2022.pdf`

### Model & Methodology
- [Llama-Primus-Reasoning (HF)](https://huggingface.co/trendmicro-ailab/Llama-Primus-Reasoning) — base cybersecurity reasoning model
- [QLoRA: Efficient Finetuning of Quantized LLMs (arXiv 2305.14314)](https://arxiv.org/abs/2305.14314)
- [Primus dataset paper (arXiv 2502.11191)](https://arxiv.org/html/2502.11191v1)
- [Learning and Forgetting Unsafe Examples in LLMs (arXiv 2312.12736)](https://arxiv.org/abs/2312.12736)
- [Chained Tuning Leads to Biased Forgetting (arXiv 2412.16469)](https://arxiv.org/abs/2412.16469)
- [The Ultimate Guide to Fine-Tuning LLMs (arXiv 2408.13296)](https://arxiv.org/pdf/2408.13296)
- [LalaEval — Human Evaluation for Domain LLMs (arXiv 2408.13338)](https://arxiv.org/abs/2408.13338)
- [CyberLLMInstruct (arXiv 2503.09334v2)](https://arxiv.org/html/2503.09334v2)

### Industry & Threshold References
- [CyberSierra — CCoP 2.0 Analysis](https://cybersierra.co/blog/ccop-2-regulations/)
- [Thomson Reuters — AI Compliance Research](https://www.thomsonreuters.com/en-us/posts/technology/expert-ai-automating-compliance-tasks)
- [US GSA — CUI Protection (85% accuracy threshold reference)](https://www.gsa.gov/system/files/Protecting-CUI-Nonfederal-Systems-%5BCIO-IT-Security-21-112-Initial-Release%5D-05-27-2022.pdf)

### Project Planning Documents
- `docs/phase-1/phase1-user-story.md`, `domain-specific-compliance-models-analysis.md`, `related-works-literature-review.md`
- `docs/phase-2/evaluation-rubrics.md`
