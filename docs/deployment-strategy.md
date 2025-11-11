# Llama-Primus CCoP Project Deployment Strategy

## Project Overview

This document outlines the deployment strategy for fine-tuning Llama-Primus-Reasoning model (8B parameters) on Singapore's Cybersecurity Code of Practice (CCoP 2.0) standards to automate compliance validation for Critical Information Infrastructure (CII) organizations.

## Phase-Based Deployment Approach

### Phase 1: Google Colab Initial Testing (Weeks 1-2)

#### Objectives
- Get Llama-Primus model running immediately
- Test basic CCoP compliance capabilities
- Validate model responses to cybersecurity prompts
- Create initial evaluation framework
- Establish baseline performance metrics

#### Technical Setup
- **Platform**: Google Colab with T4 GPU access
- **Storage**: Google Drive integration for persistence
- **Scope**: Small-scale experiments (100-200 examples)
- **Tools**: Basic inference scripts and prompt testing

#### Implementation Details

**1. Colab Environment Setup**
```python
# GPU Verification
!nvidia-smi
import torch
print(f"GPU Available: {torch.cuda.is_available()}")
print(f"GPU Name: {torch.cuda.get_device_name(0)}")
```

**2. Model Installation**
```python
# Core Dependencies
!pip install transformers accelerate bitsandbytes huggingface-hub
!pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Model Download
from transformers import AutoTokenizer, AutoModelForCausalLM
model_name = "trendmicro-ailab/Llama-Primus-Reasoning"
```

**3. Google Drive Persistence**
```python
from google.colab import drive
drive.mount('/content/drive')

# Create project directory structure
!mkdir -p "/content/drive/MyDrive/llama-primus-ccop/{models,data,results,checkpoints}"
```

#### Deliverables
- [ ] Working Llama-Primus inference notebook
- [ ] Basic CCoP prompt/response validation
- [ ] Initial baseline performance metrics
- [ ] Test dataset creation framework
- [ ] Model response quality assessment

#### Expected Timeline: 2 weeks
- **Week 1**: Model setup, basic inference, prompt testing
- **Week 2**: Evaluation framework, baseline metrics, documentation

### Phase 2: AWS Production Environment (Weeks 3-8)

#### Objectives
- Set up permanent development environment
- Handle full dataset (5,270 examples)
- Complete fine-tuning pipeline
- Production-ready deployment
- Full 19-benchmark evaluation framework

#### AWS Infrastructure Setup

**1. EC2 GPU Configuration**
```bash
# Recommended Instance Types
- g5.2xlarge (1 GPU, 24GB VRAM) - Primary choice
- g5.xlarge (1 GPU, 16GB VRAM) - Budget option
- p3.2xlarge (1 V100 GPU) - High performance

# Cost Optimization
- Use Spot Instances (90% cost reduction)
- g5.2xlarge spot: ~$0.36/hour vs $1.21/hour on-demand
```

**2. Storage Architecture**
```bash
# S3 Bucket Structure
s3://primus-ccop-project/
├── models/
│   ├── base-model/
│   ├── fine-tuned/
│   └── checkpoints/
├── data/
│   ├── training/
│   ├── validation/
│   └── test/
├── results/
│   ├── evaluations/
│   ├── benchmarks/
│   └── reports/
└── code/
    ├── scripts/
    ├── notebooks/
    └── configs/
```

**3. Security & Networking**
```bash
# VPC Configuration
- Private subnet for compute instances
- NAT gateway for internet access
- Security Group Rules:
  * SSH (22) from development IP
  * HTTPS (443) for API access
  * Custom ports for internal services
```

#### Implementation Pipeline

**1. Environment Setup**
```bash
# Deep Learning AMI or Ubuntu 22.04
conda create -n primus-ccop python=3.10 -y
conda activate primus-ccop

# Core Dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers accelerate peft bitsandbytes
pip install datasets wandb tensorboard
pip install fastapi uvicorn  # For API deployment
```

**2. Project Structure**
```bash
mkdir -p ~/primus-ccop/{src,data,models,configs,scripts,notebooks,tests}

# Key Directories
src/
├── data_processing/
├── training/
├── evaluation/
├── inference/
└── utils/

data/
├── raw/
├── processed/
├── training/
└── validation/

models/
├── base/
├── checkpoints/
└── fine_tuned/
```

**3. Fine-Tuning Pipeline**
```python
# LoRA Configuration
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=16,  # LoRA rank
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
```

#### Migration Strategy

**Phase 1 → Phase 2 Transition**
1. **Transfer Colab Successes**
   - Move validated prompts to AWS
   - Replicate successful inference patterns
   - Scale dataset creation based on Colab insights

2. **Scale Up Operations**
   - Expand from 200 → 5,270 examples
   - Implement full training pipeline
   - Set up automated evaluation

3. **Production Readiness**
   - CI/CD pipeline integration
   - Model versioning and monitoring
   - API endpoint deployment

#### Deliverables
- [ ] Complete fine-tuned Llama-Primus model
- [ ] Full dataset (4,850 training + 420 test examples)
- [ ] 19-benchmark evaluation framework
- [ ] Production inference API
- [ ] Performance monitoring and logging
- [ ] Documentation and deployment guides

#### Expected Timeline: 6 weeks
- **Week 3-4**: AWS setup, dataset creation, training pipeline
- **Week 5-6**: Fine-tuning, evaluation, optimization
- **Week 7-8**: Production deployment, testing, documentation

## Technical Requirements & Specifications

### Model Requirements
- **Base Model**: Llama-Primus-Reasoning (8B parameters)
- **Target Accuracy**: >85% across all 19 benchmarks
- **Inference Speed**: <5 seconds per response
- **Memory Usage**: <16GB GPU memory

### Dataset Specifications
- **Total Examples**: 5,270 (4,850 training + 420 test)
- **Coverage**: All 11 CCoP sections (220 clauses)
- **Format**: Instruction-following with context
- **Quality**: Zero hallucinations, 100% Singapore terminology

### Evaluation Benchmarks
| Category | Benchmarks | Focus Areas |
|----------|------------|-------------|
| Compliance | B1-B5 | CCoP interpretation, citations, terminology |
| Technical | B6-B8 | Code scanning, vulnerability detection |
| Advanced | B9-B12 | Incident response, gap analysis |
| Safety | B13-B14 | Prompt injection, jailbreak resistance |
| Training | B15-B17 | Loss, perplexity, learning metrics |
| Performance | B18-B19 | Inference speed, memory usage |

## Cost Analysis

### Phase 1: Google Colab (Student Enhanced)
- **Cost**: FREE + Student Benefits
- **Benefits**:
  - GitHub Student Pack → Colab Pro credits
  - Enhanced GPU access (longer sessions, better GPUs)
  - Google Drive integration (15GB free + 100GB through education)
- **Storage**: Google Drive (15GB free + educational storage)

### Phase 2: Cloud with Student Credits
**Available Student Resources:**
- **GitHub Student Developer Pack**:
  - Colab Pro credits ($50+ value)
  - Microsoft Azure credits ($100)
  - AWS Educate credits ($100+)
  - DigitalOcean credits ($200)
- **Google Cloud Platform Education**: $300 free credit
- **University Resources**: Potential free GPU clusters

**Optimized Cost Structure:**
- **Compute**: $50-150/month (after student credits)
- **Storage**: $20-50/month (educational discounts)
- **Data Transfer**: $10-25/month
- **Total**: $80-225/month during active development
- **Project Total**: $400-1,125 for 5-month duration

### Student Discount Application Steps
1. **GitHub Student Developer Pack** (education.github.com/pack)
2. **Google Cloud for Education** (cloud.google.com/edu)
3. **AWS Educate** (aws.amazon.com/education/awseducate)
4. **University IT Resources** (check with your institution)

### Cost Optimization Strategies
1. **Student Credits**: $600-800 in free cloud credits
2. **Spot Instances**: 90% cost reduction on remaining usage
3. **Educational Discounts**: 50-75% reduction on cloud services
4. **University Resources**: Free access to research computing clusters
5. **Multi-cloud Strategy**: Use different credits for different phases

## Risk Mitigation

### Technical Risks
1. **Model Performance**: Baseline testing in Phase 1
2. **Resource Limits**: Progressive scaling approach
3. **Data Quality**: Multi-stage validation process
4. **Deployment Complexity**: Phased rollout strategy

### Operational Risks
1. **Cost Overruns**: Spot instances + monitoring
2. **Timeline Delays**: Agile methodology with regular checkpoints
3. **Resource Availability**: Multi-cloud backup options
4. **Security Compliance**: AWS security best practices

## Success Criteria

### Phase 1 Success Metrics
- [ ] Model successfully loads and generates responses
- [ ] Basic CCoP prompts receive relevant answers
- [ ] Initial baseline metrics established
- [ ] Development workflow validated

### Phase 2 Success Metrics
- [ ] Fine-tuned model achieves >85% accuracy
- [ ] All 19 benchmarks implemented and passing
- [ ] Production API handles expected load
- [ ] Total project cost within budget ($400-1,125 with student discounts)

## Next Steps

### Immediate Actions (Week 1)
1. Set up Google Colab environment
2. Download and test Llama-Primus model
3. Create initial CCoP test prompts
4. Establish baseline performance metrics

### Medium-term Planning (Weeks 2-4)
1. Expand test dataset
2. Refine prompt engineering
3. Set up AWS environment
4. Begin full dataset creation

### Long-term Goals (Weeks 5-12)
1. Complete fine-tuning pipeline
2. Comprehensive evaluation
3. Production deployment
4. Documentation and knowledge transfer

## Conclusion

This student-optimized deployment strategy dramatically reduces costs while maintaining professional-grade capabilities for CCoP compliance automation. By leveraging educational resources and student discounts, we can achieve production-ready results at **70-80% cost reduction** compared to standard commercial pricing.

**Key Student Benefits:**
- **Phase 1**: Enhanced Colab Pro with better GPU access via GitHub Student Pack
- **Phase 2**: $600-800 in free cloud credits across multiple platforms
- **University Resources**: Potential access to research computing clusters
- **Total Savings**: $1,000-2,000+ compared to standard commercial rates

The strategy leverages educational resources for initial validation, then scales to professional cloud infrastructure using student credits, ensuring optimal use of available benefits while maintaining project quality and timeline.

**Estimated Student Cost:** $400-1,125 total (vs. $1,350-2,750 commercial)
**Timeline:** Maintained at 8-10 weeks
**Quality:** Production-ready standards maintained