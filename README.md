# Fine-Tuning Language Model on CCoP 2.0 Standards

## Project Overview

This project focuses on fine-tuning Llama-Primus-Reasoning on Singapore's Cybersecurity Code of Practice (CCoP 2.0) standards to automate compliance violation detection for Critical Information Infrastructure organizations.

## Key Objectives

1. **Baseline Evaluation**: Benchmark Llama-Primus-Reasoning against CCoP 2.0 standards
2. **Fine-Tuning**: Use QLoRA to achieve 85% accuracy in compliance violation detection
3. **Integration**: Deploy model to CI/CD pipelines for automated code and infrastructure analysis
4. **Validation**: Test in isolated CII environment mimicking real-world deployment

## Project Structure

```
studio-ssdlc/
├── src/                    # Core source code for Colab execution
├── colab/                  # Google Colab notebooks
├── data/                   # Benchmark datasets
├── models/                 # Model artifacts and checkpoints
├── benchmarks/             # Benchmark execution and results
├── config/                 # Configuration files
├── deployment/             # Deployment configurations
├── tests/                  # Unit and integration tests
├── notebooks/              # Research and development notebooks
├── docs/                   # Documentation
└── references/             # External references and citations
```

## Development Workflow

This project uses a **GitHub + Google Colab** workflow:

1. **Code Development**: Local development with Git version control
2. **Execution**: All heavy computation in Google Colab
3. **Deployment**: Automated scripts sync code to Colab environment
4. **Results**: Auto-save results back to repository

## Current Status

### Phase 1: Foundation & Setup (In Progress)
- [x] Project repository initialization
- [x] Implementation plan documentation
- [ ] Poetry configuration setup
- [ ] Project structure creation
- [ ] Colab environment setup
- [ ] Benchmark dataset creation

### Upcoming Phases
- **Phase 2**: Baseline screening (>15% accuracy target)
- **Phase 3**: Comprehensive benchmarking (170 test cases)
- **Phase 4**: Small-scale fine-tuning test
- **Phase 5**: Full dataset creation (5,270 examples)
- **Phase 6**: Comprehensive fine-tuning
- **Phase 7**: Production validation

## Key Technologies

- **Base Model**: Llama-Primus-Reasoning (8B parameters)
- **Fine-Tuning**: QLoRA (Quantized Low-Rank Adaptation)
- **Evaluation**: 19-benchmark system (B1-B19)
- **Infrastructure**: Google Colab + Google Cloud Storage
- **Version Control**: Git + GitHub

## References

See [CLAUDE.md](./CLAUDE.md) for comprehensive project references and instructions.

## Getting Started

1. Clone the repository
2. Set up Poetry environment (for dependency management)
3. Open Google Colab notebooks for execution
4. Follow the Phase 1 implementation plan in `docs/phase-1/`

## License

This project is part of academic research on cybersecurity compliance automation.