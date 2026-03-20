# Fine-Tuning Language Model on CCoP 2.0 Standards

## Project Objective
Read the project paper [Primus-Fine-Tuning-CCOP2-SG-v2.0-SagarPratapSingh-1010736.md](report/term1-mid/Primus-Fine-Tuning-CCOP2-SG-v2.0-SagarPratapSingh-1010736.md)

## Project References

### Regulatory & Standards References
- [Cyber Security Agency of Singapore - Codes of Practice](https://www.csa.gov.sg/legislation/codes-of-practice) - Official CCoP 2.0 standards and documentation
- [CCoP Second Edition Revision One PDF](https://isomer-user-content.by.gov.sg/36/2df750a7-a3bc-4d77-a492-d64f0ff4db5a/CCoP---SecondEdition_Revision-One.pdf) - Complete CCoP 2.0 regulatory document
- Local: `ccop-official/CCoP---Second-Edition_Revision-One.pdf` - Official CCoP 2.0 document (local copy)

### Supplementary CCoP 2.0 Documents (Local Repository)
- `ccop-official/supplementary/Guidelines_for_Auditing_Critical_Information_Infrastructure.pdf` - Auditing guidelines for CII
- `ccop-official/supplementary/Guide-to-Cyber-Threat-Modelling.pdf` - Threat modelling framework
- `ccop-official/supplementary/Guide-to-Conducting-Cybersecurity-Risk-Assessment-for-CII.pdf` - Risk assessment methodology
- `ccop-official/supplementary/Security_By_Design_Framework.pdf` - Security by design principles
- `ccop-official/references/Ensign's_Cybersecurity_Guide_on_CCoP_2_0_for_CII_Sep_2022.pdf` - Implementation guide for CCoP 2.0

### Model & Framework References
- [Llama-Primus-Reasoning on Hugging Face](https://huggingface.co/trendmicro-ailab/Llama-Primus-Reasoning) - Base cybersecurity-specialized reasoning model
- [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314) - Parameter-efficient fine-tuning methodology

### Research & Analysis References
- [Primus: A Pioneering Collection of Open-Source Datasets for Cybersecurity LLM Training](https://arxiv.org/html/2502.11191v1) - Primus: A Pioneering Collection of Open-Source Datasets for Cybersecurity LLM Training
- [Learning and Forgetting Unsafe Examples in Large Language Models](https://arxiv.org/abs/2312.12736) - Research on catastrophic forgetting in sequential fine-tuning
- [Chained Tuning Leads to Biased Forgetting](https://arxiv.org/abs/2412.16469) - Research on sequential training challenges
- [The Ultimate Guide to Fine-Tuning LLMs](https://arxiv.org/pdf/2408.13296) - Comprehensive fine-tuning methodology reference
- [LalaEval: Human Evaluation Framework for Domain-Specific LLMs](https://arxiv.org/abs/2408.13338) - Evaluation framework for specialized language models
- [CyberLLMInstruct Dataset Analysis](https://arxiv.org/html/2503.09334v2) - Cybersecurity fine-tuning dataset research

### Industry & Implementation References
- [CyberSierra CCoP 2.0 Analysis](https://cybersierra.co/blog/ccop-2-regulations/) - Industry commentary on CCoP 2.0 implementation challenges
- [Thomson Reuters AI Compliance Research](https://www.thomsonreuters.com/en-us/posts/technology/expert-ai-automating-compliance-tasks) - Enterprise AI accuracy requirements
- [US GSA CUI Protection Guide](https://www.gsa.gov/system/files/Protecting-CUI-Nonfederal-Systems-%5BCIO-IT-Security-21-112-Initial-Release%5D-05-27-2022.pdf) - Reference for 85% accuracy threshold

### Project Planning Documents (Local Repository)
- `docs/phase1/phase1-user-story.md` - Phase 1 baseline evaluation infrastructure user story and functional requirements
- `docs/phase1/domain-specific-compliance-models-analysis.md` - Analysis of CyberLLM, SecLLM, RegBERT evaluation methodologies
- `docs/phase1/related-works-literature-review.md` - Literature review of LLM-based compliance checking models
- `ccop-official/RESPONSE-TO-FEEDBACK.pdf` - Official clarifications and responses on CCoP 2.0 requirements

### Repository Structure Guidance
- 1. SKIP files under research/archived* folder. They are not relevant to the context

## CLI Reference (ccop-eval)

All commands run from `src/` directory using `poetry run ccop-eval`.

### Evaluate — Run model evaluation

```bash
# Full batch: all 21 benchmarks (118 test cases), hybrid mode (default)
cd src && poetry run ccop-eval evaluate run --model primus-reasoning

# Full batch: llm-only mode (no RAG)
cd src && poetry run ccop-eval evaluate run --model primus-reasoning --mode llm-only

# Single benchmark
cd src && poetry run ccop-eval evaluate run --model primus-reasoning --benchmarks B3

# Multiple benchmarks (repeat --benchmarks flag)
cd src && poetry run ccop-eval evaluate run --model primus-reasoning --benchmarks B1 --benchmarks B3 --benchmarks B21

# By tier (overrides --benchmarks)
cd src && poetry run ccop-eval evaluate run --model primus-reasoning --tier 1
cd src && poetry run ccop-eval evaluate run --model primus-reasoning --tier 3

# Specific test cases
cd src && poetry run ccop-eval evaluate run --model primus-reasoning --test-ids B3-001 --test-ids B3-002

# Custom temperature
cd src && poetry run ccop-eval evaluate run --model primus-reasoning --benchmarks B1 --temperature 0.3

# Skip saving results
cd src && poetry run ccop-eval evaluate run --model primus-reasoning --benchmarks B1 --no-save

# Custom pass threshold (0.0-1.0, overrides phase default)
cd src && poetry run ccop-eval evaluate run --model primus-reasoning --threshold 0.5

# Evaluation phase (sets pass threshold: baseline=15%, finetuned=50%, deployment=85%)
cd src && poetry run ccop-eval evaluate run --model primus-reasoning --phase finetuned
```

### Query — Ask CCoP compliance questions via RAG

```bash
# Hybrid mode (default): RAG retrieval + LLM generation
cd src && poetry run ccop-eval query ask "What are the access control requirements?"

# LLM-only mode
cd src && poetry run ccop-eval query ask "What are the MFA requirements?" --mode llm-only

# RAG-only mode
cd src && poetry run ccop-eval query ask "What does clause 5.2.1 say?" --mode rag-only

# Verbose (show metadata)
cd src && poetry run ccop-eval query ask "How should CII organizations implement MFA?" --verbose
```

### Report — Generate evaluation reports

```bash
# Generate JSON report (default)
cd src && poetry run ccop-eval report generate --model primus-reasoning

# Generate markdown report
cd src && poetry run ccop-eval report generate --model primus-reasoning --format markdown

# Generate to specific file
cd src && poetry run ccop-eval report generate --model primus-reasoning --format html --output report.html

# Show evaluation summary
cd src && poetry run ccop-eval report summary --model primus-reasoning
```

### Setup — Model setup and prerequisites

```bash
# Check prerequisites (Ollama, etc.)
cd src && poetry run ccop-eval setup check

# Set up model (default: primus-reasoning with Q5_K_M quantization)
cd src && poetry run ccop-eval setup model

# Custom model setup
cd src && poetry run ccop-eval setup model --hf-repo trendmicro-ailab/Llama-Primus-Reasoning --model-name primus-reasoning --quantization Q8_0

# Force reconversion
cd src && poetry run ccop-eval setup model --force
```

### Benchmark Reference

| Benchmarks | Type | Description |
|------------|------|-------------|
| B1, B2, B4, B5, B6 | Rule-based | Keyword matching, Jaccard word overlap |
| B21 | Rule-based | Regex hallucination detection (binary pass/fail) |
| B3, B7-B20 | LLM-as-Judge | Rubric-based evaluation via Claude (0-3 anchored scale) |

### Global Options

```bash
# Verbose output
cd src && poetry run ccop-eval --verbose evaluate run --model primus-reasoning

# Debug mode
cd src && poetry run ccop-eval --debug evaluate run --model primus-reasoning
```

## Project Memory System

This project maintains institutional knowledge in `docs/project_notes/` for consistency across sessions.

### Memory Files

- **bugs.md** - Bug log with dates, solutions, and prevention notes
- **decisions.md** - Architectural Decision Records (ADRs) with context and trade-offs
- **key_facts.md** - Project configuration, credentials, ports, important URLs
- **issues.md** - Work log with ticket IDs, descriptions, and URLs

### Memory-Aware Protocols

**Before proposing architectural changes:**
- Check `docs/project_notes/decisions.md` for existing decisions
- Verify the proposed approach doesn't conflict with past choices
- If it does conflict, acknowledge the existing decision and explain why a change is warranted

**When encountering errors or bugs:**
- Search `docs/project_notes/bugs.md` for similar issues
- Apply known solutions if found
- Document new bugs and solutions when resolved

**When looking up project configuration:**
- Check `docs/project_notes/key_facts.md` for credentials, ports, URLs, service accounts
- Prefer documented facts over assumptions

**When completing work on tickets:**
- Log completed work in `docs/project_notes/issues.md`
- Include ticket ID, date, brief description, and URL

**When user requests memory updates:**
- Update the appropriate memory file (bugs, decisions, key_facts, or issues)
- Follow the established format and style (bullet lists, dates, concise entries)

### Style Guidelines for Memory Files

- **Prefer bullet lists over tables** for simplicity and ease of editing
- **Keep entries concise** (1-3 lines for descriptions)
- **Always include dates** for temporal context
- **Include URLs** for tickets, documentation, monitoring dashboards
- **Manual cleanup** of old entries is expected (not automated)
