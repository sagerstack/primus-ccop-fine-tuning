# Fine-Tuning Language Model on CCoP 2.0 Standards

## Project Objective
Read the project paper [Primus-Fine-Tuning-CCOP2-SG-v2.0-SagarPratapSingh-1010736.md](report/term1-mid/Primus-Fine-Tuning-CCOP2-SG-v2.0-SagarPratapSingh-1010736.md)

## Project References

### Regulatory & Standards References
- [Cyber Security Agency of Singapore - Codes of Practice](https://www.csa.gov.sg/legislation/codes-of-practice) - Official CCoP 2.0 standards and documentation
- [CCoP Second Edition Revision One PDF](https://isomer-user-content.by.gov.sg/36/2df750a7-a3bc-4d77-a492-d64f0ff4db5a/CCoP---SecondEdition_Revision-One.pdf) - Complete CCoP 2.0 regulatory document

### Model & Framework References
- [Llama-Primus-Reasoning on Hugging Face](https://huggingface.co/trendmicro-ailab/Llama-Primus-Reasoning) - Base cybersecurity-specialized reasoning model
- [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314) - Parameter-efficient fine-tuning methodology

### Research & Analysis References
- [Learning and Forgetting Unsafe Examples in Large Language Models](https://arxiv.org/abs/2312.12736) - Research on catastrophic forgetting in sequential fine-tuning
- [Chained Tuning Leads to Biased Forgetting](https://arxiv.org/abs/2412.16469) - Research on sequential training challenges
- [The Ultimate Guide to Fine-Tuning LLMs](https://arxiv.org/pdf/2408.13296) - Comprehensive fine-tuning methodology reference
- [LalaEval: Human Evaluation Framework for Domain-Specific LLMs](https://arxiv.org/abs/2408.13338) - Evaluation framework for specialized language models
- [CyberLLMInstruct Dataset Analysis](https://arxiv.org/html/2503.09334v2) - Cybersecurity fine-tuning dataset research

### Industry & Implementation References
- [CyberSierra CCoP 2.0 Analysis](https://cybersierra.co/blog/ccop-2-regulations/) - Industry commentary on CCoP 2.0 implementation challenges
- [Thomson Reuters AI Compliance Research](https://www.thomsonreuters.com/en-us/posts/technology/expert-ai-automating-compliance-tasks) - Enterprise AI accuracy requirements
- [US GSA CUI Protection Guide](https://www.gsa.gov/system/files/Protecting-CUI-Nonfederal-Systems-%5BCIO-IT-Security-21-112-Initial-Release%5D-05-27-2022.pdf) - Reference for 85% accuracy threshold

### Repository Structure Guidance
- 1. SKIP files under research/archived* folder. They are not relevant to the context 

```
studio-ssdlc/
├── README.md                          # Project overview and setup instructions
├── pyproject.toml                     # Poetry configuration for dependencies
├── .gitignore                         # Git ignore patterns
├── CLAUDE.md                          # This file - project instructions and references
│
├── docs/                              # Documentation and research references
│   ├── ccop-standards/                # CCoP 2.0 standards documentation
│   ├── methodology/                   # Fine-tuning methodology documentation
│   └── evaluation/                    # Benchmark evaluation procedures
│
├── src/                               # Core source code
│   ├── __init__.py
│   ├── model/                         # Model handling and fine-tuning
│   │   ├── __init__.py
│   │   ├── base_model.py              # Llama-Primus-Reasoning model loading
│   │   ├── fine_tuning.py             # QLoRA fine-tuning implementation
│   │   └── inference.py               # Model inference and prediction
│   │
│   ├── data/                          # Data processing and management
│   │   ├── __init__.py
│   │   ├── dataset_creation.py        # Training dataset generation
│   │   ├── preprocessing.py           # Data cleaning and preparation
│   │   └── augmentation.py            # Data augmentation techniques
│   │
│   ├── evaluation/                    # Benchmark and evaluation system
│   │   ├── __init__.py
│   │   ├── benchmarks.py              # B1-B19 benchmark implementation
│   │   ├── scoring.py                 # Evaluation scoring algorithms
│   │   └── human_eval.py              # Human-in-the-loop evaluation
│   │
│   ├── integration/                   # CI/CD pipeline integration
│   │   ├── __init__.py
│   │   ├── github_actions.py          # GitHub Actions integration
│   │   ├── gitlab_ci.py               # GitLab CI integration
│   │   └── scanners/                  # Code scanning integrations
│   │       ├── __init__.py
│   │       ├── sast_scanner.py        # Static Application Security Testing
│   │       ├── sca_scanner.py         # Software Composition Analysis
│   │       └── iac_scanner.py         # Infrastructure as Code scanning
│   │
│   └── utils/                         # Utility functions
│       ├── __init__.py
│       ├── config.py                  # Configuration management
│       ├── logging.py                 # Logging utilities
│       └── metrics.py                 # Performance metrics collection
│
├── data/                              # Training and test datasets
│   ├── raw/                           # Raw collected data
│   │   ├── ccop_clauses/              # CCoP 2.0 clause text
│   │   ├── vulnerable_code/           # Security vulnerability examples
│   │   ├── infrastructure_configs/    # IaC configuration examples
│   │   └── ot_ics_examples/           # OT/ICS specific examples
│   │
│   ├── processed/                     # Cleaned and processed datasets
│   │   ├── training/                  # Training datasets (4,850 examples)
│   │   ├── test/                      # Test datasets (420 examples)
│   │   └── validation/                # Validation datasets for hyperparameter tuning
│   │
│   └── synthetic/                     # Generated synthetic data for augmentation
│
├── models/                            # Model artifacts and checkpoints
│   ├── base/                          # Base Llama-Primus-Reasoning model
│   ├── checkpoints/                   # Fine-tuning checkpoints
│   ├── final/                         # Final production models
│   └── evaluation/                    # Models for evaluation phases
│
├── benchmarks/                        # Benchmark execution and results
│   ├── baseline/                      # Phase 2-3 baseline benchmarking
│   ├── small_finetune/                # Phase 4 small-scale testing
│   ├── production/                    # Phase 7 production validation
│   └── results/                       # Benchmark results and analysis
│
├── scripts/                           # Utility and execution scripts
│   ├── setup_environment.py           # Environment setup and dependency installation
│   ├── download_models.py             # Base model download and setup
│   ├── run_benchmarks.py              # Benchmark execution script
│   ├── fine_tune.py                   # Fine-tuning execution script
│   └── deploy_model.py                # Model deployment script
│
├── tests/                             # Unit and integration tests
│   ├── __init__.py
│   ├── test_model/                    # Model component tests
│   ├── test_data/                     # Data processing tests
│   ├── test_evaluation/               # Evaluation system tests
│   └── test_integration/              # CI/CD integration tests
│
├── config/                            # Configuration files
│   ├── training_config.yaml           # Fine-tuning hyperparameters
│   ├── benchmark_config.yaml          # Benchmark configuration
│   ├── deployment_config.yaml         # Deployment settings
│   └── environment/                   # Environment-specific configurations
│       ├── development.yaml
│   ├── staging.yaml
│   └── production.yaml
│
├── notebooks/                         # Research and development notebooks
│   ├── 01_exploratory_analysis.ipynb  # Initial data exploration
│   ├── 02_baseline_evaluation.ipynb   # Base model evaluation
│   ├── 03_data_preprocessing.ipynb    # Data cleaning and preparation
│   ├── 04_fine_tuning_experiments.ipynb # Fine-tuning experimentation
│   └── 05_results_analysis.ipynb      # Final results and analysis
│
├── deployment/                        # Deployment configurations
│   ├── docker/                        # Docker configurations
│   │   ├── Dockerfile                 # Main application Dockerfile
│   │   ├── Dockerfile.gpu             # GPU-enabled Dockerfile
│   │   └── docker-compose.yml         # Multi-service deployment
│   │
│   ├── kubernetes/                    # Kubernetes deployment manifests
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   │
│   └── api/                           # API endpoints for model serving
│       ├── app.py                     # FastAPI application
│       ├── requirements.txt           # API dependencies
│       └── endpoints/                 # API endpoint definitions
│
├── report/                            # Project reports and documentation
│   ├── term1-mid/                     # Mid-term 1 report
│   ├── term1-final/                   # Final term 1 report
│   ├── term2-mid/                     # Mid-term 2 report
│   ├── term2-final/                   # Final term 2 report
│   ├── term3-mid/                     # Mid-term 3 report
│   └── term3-final/                   # Final project report
│
└── references/                        # External references and citations
    ├── papers/                        # Research papers and articles
    ├── standards/                     # Standards and regulations
    └── tools/                         # Tool documentation and references
```

### Key Directory Purposes:

- **`src/`**: Core application code organized by functional areas
- **`data/`**: Training datasets organized by processing stage (raw → processed → synthetic)
- **`models/`**: Model artifacts organized by training phase
- **`benchmarks/`**: Benchmark execution tracking for each project phase
- **`deployment/`**: Production deployment configurations for air-gapped CIIO environments
- **`notebooks/`**: Research notebooks for iterative development and analysis
- **`config/`**: Environment-specific configurations for different deployment scenarios


