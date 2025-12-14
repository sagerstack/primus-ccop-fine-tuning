# Phase 1: Infrastructure Setup and Baseline Testing Approach

## Overview

Phase 1 focused on establishing a cost-effective, local evaluation infrastructure for baseline testing of the Llama-Primus-Reasoning model against CCoP 2.0 standards. Our approach leveraged local compute resources to validate the evaluation methodology before scaling to cloud infrastructure, enabling rapid iteration while maintaining zero infrastructure costs during the critical methodology validation phase.

## Infrastructure Setup

### Hardware Environment

The baseline evaluation infrastructure was deployed on an Apple MacBook equipped with the M3 chip, utilizing Apple Silicon's ARM64 architecture with unified memory architecture. This platform provides a shared CPU/GPU memory pool that enables efficient inference for quantized models without requiring dedicated GPU hardware [32]. The selection of local development infrastructure was driven by four key considerations. First, cost efficiency was paramount, as local deployment eliminated cloud compute costs entirely during methodology validation, allowing resources to be preserved for later phases requiring extensive GPU compute. Second, rapid iteration was essential for developing and refining the evaluation pipeline, with local deployment providing immediate feedback without the latency and complexity of cloud-based workflows. Third, data privacy considerations favored local infrastructure, ensuring that CCoP 2.0 test cases containing sensitive regulatory interpretations remained within controlled local infrastructure rather than being transmitted to cloud services. Fourth, methodology validation required proving the evaluation approach before committing significant investment to cloud resources, with local deployment serving as a low-risk proof-of-concept environment.

### Model Configuration

The evaluation infrastructure utilized a quantized version of the Llama-Primus-Reasoning model (8B parameters) developed by Trend Micro AILab [33]. During infrastructure planning, we evaluated multiple quantization approaches to determine the optimal balance between memory efficiency and model performance for baseline evaluation. Table 1 summarizes the quantization methods considered, their performance characteristics, and the rationale for selection or rejection.

**Table 1: Quantization Method Evaluation for Phase 1 Infrastructure**

| Quantization Method | Technique | Memory Footprint (8B Model) | Memory Reduction | Performance Retention | Accuracy Degradation | Selected | Rationale | Reference |
|---------------------|-----------|----------------------------|------------------|----------------------|---------------------|----------|-----------|-----------|
| **Full Precision (FP16)** | 16-bit floating point | ~16 GB | Baseline | 100% | 0% | ❌ | Exceeds M3 hardware memory capacity; not viable for local deployment | - |
| **8-bit Quantization** | LLM.int8() | ~8 GB | 2x | 99.9% | <0.1% | ❌ | Limited memory advantage; still requires significant memory headroom; minimal benefit over full precision for baseline testing | [35] |
| **4-bit Quantization** | QLoRA (NF4) | ~5-6 GB | 3-4x | 97-99% | 1-3% | ✅ | **Optimal balance**: Sufficient memory reduction for M3 deployment, minimal performance loss, maintains >90% accuracy for valid baseline metrics | [34] |
| **3-bit Quantization** | GPTQ | ~4 GB | 4-5x | 90-95% | 5-10% | ❌ | Excessive accuracy degradation introduces confounding variables; compromises baseline validity | [36] |
| **2-bit Quantization** | GPTQ | ~3 GB | 5-8x | 85-90% | 10-15% | ❌ | Unacceptable performance loss; baseline metrics would not reflect true model capabilities | [36] |

The evaluation revealed that 4-bit quantization using QLoRA emerged as the optimal choice for Phase 1 infrastructure [34]. This approach reduces memory requirements from approximately 16GB for full precision to 5-6GB for 4-bit quantized inference, representing a 3-4x memory reduction that makes deployment viable on consumer hardware (M3 chip with 16GB unified memory) while maintaining model performance within 1-3% of full precision accuracy across diverse benchmarks. The model was converted to GGUF (GPT-Generated Unified Format) specifically optimized for Apple Silicon, enabling Metal acceleration for efficient inference on the M3 chip's neural engine. The inference framework utilized llama.cpp with Metal backend support, providing hardware-accelerated inference capabilities specifically optimized for Apple Silicon architecture [37].

The selected 4-bit quantization approach provides several critical advantages for baseline evaluation. First, the 3-4x memory reduction enables deployment on consumer hardware while preserving sufficient memory headroom for concurrent processes and evaluation framework execution. Second, the minimal performance degradation (1-3%) ensures that baseline metrics accurately reflect model capabilities rather than quantization artifacts, critical for establishing valid performance benchmarks. Third, 4-bit quantization maintains over 90% of full-precision performance, providing a reliable foundation for methodology validation before scaling to cloud infrastructure [34]. Additionally, the unified memory architecture of Apple Silicon provides faster inference compared to discrete GPU configurations for models of this size, as it eliminates PCIe transfer overhead between CPU and GPU memory spaces. This configuration validated that baseline performance assessment could be conducted effectively on consumer hardware before committing to cloud GPU infrastructure for comprehensive evaluation.

### References (Infrastructure Setup)

[32] Apple Inc., "Apple M3 Chip: Technical Overview," Apple Platform Architecture, 2023. [Online]. Available: https://www.apple.com/mac/m3/

[33] Trend Micro AILab, "Llama-Primus-Reasoning," Hugging Face Model Repository, 2025. [Online]. Available: https://huggingface.co/trendmicro-ailab/Llama-Primus-Reasoning

[34] T. Dettmers, A. Pagnoni, A. Holtzman, and L. Zettlemoyer, "QLoRA: Efficient Finetuning of Quantized LLMs," arXiv preprint arXiv:2305.14314, 2023. [Online]. Available: https://arxiv.org/abs/2305.14314

[35] T. Dettmers, M. Lewis, Y. Belkada, and L. Zettlemoyer, "LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale," in Proceedings of the 36th Conference on Neural Information Processing Systems (NeurIPS), 2022. [Online]. Available: https://arxiv.org/abs/2208.07339

[36] E. Frantar, S. Ashkboos, T. Hoefler, and D. Alistarh, "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers," arXiv preprint arXiv:2210.17323, 2022. [Online]. Available: https://arxiv.org/abs/2210.17323

[37] G. Gerganov, "llama.cpp: Inference of LLaMA model in pure C/C++," GitHub Repository, 2024. [Online]. Available: https://github.com/ggerganov/llama.cpp

---

## Key Learnings and Future Directions

Phase 1 infrastructure deployment validated several critical technical and methodological assumptions that inform subsequent project phases. The quantized model approach proved viable for local evaluation on consumer hardware, with Apple Silicon (M3) providing a cost-effective alternative to cloud GPUs during methodology validation and iterative refinement. The 4-bit quantization maintained over 90% of full-precision performance while reducing memory requirements by 3-4x, confirming that baseline assessment could proceed on local infrastructure before committing to cloud GPU investment. This hybrid infrastructure strategy—where local development handles methodology validation while cloud resources are reserved for computationally intensive workloads—optimizes cost efficiency without compromising evaluation rigor.

The infrastructure validation confirmed that llama.cpp with Metal acceleration provided sufficient performance for baseline screening, achieving 2-5 second inference latency per test case well within acceptable bounds for diagnostic evaluation. Memory footprint remained within consumer hardware limits at 5-6GB, preserving adequate headroom for concurrent evaluation framework processes and dataset curation workflows. The modular pipeline architecture designed during Phase 1 proved extensible for scaling to larger test datasets and more sophisticated evaluation methodologies implemented in Phase 2, validating the architectural approach for production-scale deployment.

Future work will leverage the Phase 1 infrastructure foundation for cloud-based comprehensive baseline evaluation in Phase 3, expanding test coverage to 170+ cases across all CCoP 2.0 sections and implementing comparative evaluation against state-of-the-art language models (GPT-5, DeepSeek-V3). Phase 4 will utilize the validated quantization approach for QLoRA-based fine-tuning, with Phase 1 infrastructure continuing to support dataset curation, ground truth annotation, evaluation script development, and result analysis workflows. The Phase 1 architecture diagram (see phase1-architecture-diagram.html) provides visual reference for the infrastructure configuration and component interactions.
