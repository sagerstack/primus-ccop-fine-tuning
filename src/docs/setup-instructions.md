# Llama-Primus-Reasoning Model Setup Instructions

This document tracks the successful completion of setup steps for the Llama-Primus-Reasoning model.

## Completed Steps

### ✅ Step 1: Install Required Tools (Completed)

**Date:** 2025-12-14

**Tools Installed:**
```bash
# Install llama.cpp for model conversion
brew install llama.cpp

# Install huggingface-cli for model downloads
poetry run pip install huggingface-hub[cli]
poetry run pip install transformers sentencepiece protobuf
poetry run pip install torch
poetry run pip install gguf
```

**Verification:**
- llama.cpp installed at: `/opt/homebrew/Cellar/llama.cpp/7340`
- Conversion script available at: `/opt/homebrew/Cellar/llama.cpp/7340/bin/convert_hf_to_gguf.py`

---

### ✅ Step 2: Download Llama-Primus-Reasoning Model (Completed)

**Date:** 2025-12-14

**Command:**
```bash
poetry run huggingface-cli download trendmicro-ailab/Llama-Primus-Reasoning \
  --local-dir /Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/models/primus-reasoning-source
```

**Result:**
- Model downloaded successfully
- Location: `/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/models/primus-reasoning-source`
- Size: 16.1 GB
- Files downloaded:
  - 4 model weight files (model-00001 through model-00004.safetensors)
  - config.json
  - tokenizer.json
  - generation_config.json
  - tokenizer_config.json
  - special_tokens_map.json
  - README.md

---

### ✅ Step 3: Convert Model to GGUF F16 Format (Completed)

**Date:** 2025-12-14

**Command:**
```bash
cd /Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/src
poetry run python /tmp/llama.cpp/convert_hf_to_gguf.py \
  ../models/primus-reasoning-source \
  --outfile ../models/primus-reasoning-f16.gguf \
  --outtype f16
```

**Result:**
- Conversion completed successfully
- Output file: `/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/models/primus-reasoning-f16.gguf`
- Size: 15 GB
- Note: Used GitHub repo's latest conversion script due to version compatibility

---

### ✅ Step 4: Quantize GGUF to Q5_K_M (Completed)

**Date:** 2025-12-14

**Command:**
```bash
cd /Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/models
llama-quantize \
  ./primus-reasoning-f16.gguf \
  ./primus-reasoning-Q5_K_M.gguf \
  Q5_K_M
```

**Result:**
- Quantization completed in ~96 seconds
- Output file: `/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/models/primus-reasoning-Q5_K_M.gguf`
- Size: 5.3 GB (65% reduction from F16)
- 292 tensors quantized with mixed precision (q5_K and q6_K)

---

### ✅ Step 5: Create Ollama Modelfile (Completed)

**Date:** 2025-12-14

**Command:**
```bash
cd /Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/models

cat > Modelfile <<'EOF'
FROM ./primus-reasoning-Q5_K_M.gguf

SYSTEM """You are a cybersecurity compliance expert specializing in Singapore's CCoP 2.0 (Cybersecurity Code of Practice) standards for Critical Information Infrastructure."""

TEMPLATE """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{{ .System }}<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{{ .Prompt }}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""

PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_of_text|>"
EOF
```

**Result:**
- Modelfile created successfully with CCoP 2.0 system prompt

---

### ✅ Step 6: Import Model to Ollama (Completed)

**Date:** 2025-12-14

**Command:**
```bash
cd /Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/models
ollama create primus-reasoning -f Modelfile
```

**Result:**
- Model imported successfully
- Model name: `primus-reasoning:latest`
- Model ID: `f99d5577fc82`
- Size in Ollama: 5.7 GB

---

### ✅ Step 7: Verify Model (Completed)

**Date:** 2025-12-14

**Commands:**
```bash
# List models
ollama list

# Test inference
ollama run primus-reasoning "What is CCoP 2.0?"
```

**Result:**
- Model listed successfully in Ollama
- Test inference completed with accurate CCoP 2.0 response
- Performance metrics:
  - Prompt eval rate: 60.95 tokens/s
  - Generation rate: 13.33 tokens/s
  - Total duration: 41.3 seconds (includes 20.9s model load time)

---

## Understanding Ollama's Model Storage

### Two Different Locations

After completing the setup, the model exists in **two independent locations**:

#### 1. Your Project's `models/` Folder (Source Files)
```
/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/models/
├── primus-reasoning-source/        # 16.1 GB (original PyTorch weights)
├── primus-reasoning-f16.gguf       # 15 GB (intermediate GGUF)
├── primus-reasoning-Q5_K_M.gguf    # 5.3 GB (quantized GGUF - source file)
└── Modelfile                       # Configuration file
```

These are the **source files** used during conversion and import.

#### 2. Ollama's Internal Storage (Production Copy)
```
~/.ollama/models/
├── blobs/
│   └── sha256-007aebc855f2e10a... # 5.3 GB (model copy used for inference)
└── manifests/
    └── registry.ollama.ai/library/primus-reasoning/latest
```

Ollama maintains its **own copy** of the model in content-addressable storage.

### What Happens During `ollama create`

When you run `ollama create primus-reasoning -f Modelfile`:

1. **Reads the Modelfile** from your current directory
2. **Parses the `FROM` line**: sees `./primus-reasoning-Q5_K_M.gguf`
3. **Copies the GGUF file** to Ollama's blob storage:
   - Source: `/path/to/your/models/primus-reasoning-Q5_K_M.gguf`
   - Destination: `~/.ollama/models/blobs/sha256-007aebc...` (SHA256 hash)
4. **Creates configuration blobs**:
   - System prompt (162 bytes)
   - Template (195 bytes)
   - Parameters (62 bytes)
5. **Creates a manifest** at `~/.ollama/models/manifests/.../primus-reasoning/latest`
6. **Registers** the model as `primus-reasoning:latest` in Ollama's registry

### How Ollama References the Model

Ollama uses a **Docker-like layered storage system**:

```json
{
  "layers": [
    {
      "mediaType": "application/vnd.ollama.image.model",
      "digest": "sha256:007aebc855f2e10a...",
      "size": 5732989440,
      "from": "~/.ollama/models/blobs/sha256-007aebc..."
    },
    {
      "mediaType": "application/vnd.ollama.image.template",
      "digest": "sha256:3f1f8b411666..."
    },
    {
      "mediaType": "application/vnd.ollama.image.system",
      "digest": "sha256:dfbdaba60f65..."
    }
  ]
}
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EVALUATION RUNTIME FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  Your Terminal                                                               │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │ $ poetry run ccop-eval evaluate run --model primus-reasoning       │    │
│  │                                --benchmarks B1                      │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Evaluation Framework (Python Process)                                      │
│  /Users/.../studio-ssdlc/src/                                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  Application Layer (Use Cases)                                   │       │
│  │  • EvaluateModelUseCase                                          │       │
│  │    - Loads test cases from ground-truth/phase-2/test-suite/     │       │
│  │    - Iterates through each test case                             │       │
│  │    - Calls model gateway for each question                       │       │
│  └──────────────────────────┬───────────────────────────────────────┘       │
│                             │                                                │
│                             ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  Infrastructure Layer (Adapters)                                 │       │
│  │  • OllamaGateway (IModelGateway implementation)                  │       │
│  │    - Normalizes model name: "primus-reasoning" → ":latest"       │       │
│  │    - Creates HTTP payload with prompt + parameters               │       │
│  └──────────────────────────┬───────────────────────────────────────┘       │
└─────────────────────────────┼────────────────────────────────────────────────┘
                              │
                              │ HTTP POST
                              │ localhost:11434/api/generate
                              │ {
                              │   "model": "primus-reasoning:latest",
                              │   "prompt": "What is CCoP 2.0?",
                              │   "system": "You are a cybersecurity...",
                              │   "options": {"temperature": 0.7, ...}
                              │ }
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Ollama Service (Background Process)                                        │
│  http://localhost:11434                                                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  API Server                                                      │       │
│  │  1. Receives HTTP request                                        │       │
│  │  2. Parses model name: "primus-reasoning:latest"                 │       │
│  └──────────────────────────┬───────────────────────────────────────┘       │
│                             │                                                │
│                             ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  Model Registry Lookup                                           │       │
│  │  3. Reads manifest:                                              │       │
│  │     ~/.ollama/models/manifests/                                  │       │
│  │       registry.ollama.ai/library/primus-reasoning/latest         │       │
│  │                                                                   │       │
│  │  4. Manifest contains:                                           │       │
│  │     {                                                             │       │
│  │       "layers": [                                                 │       │
│  │         {                                                         │       │
│  │           "mediaType": "application/vnd.ollama.image.model",     │       │
│  │           "digest": "sha256:007aebc855f2e10a...",                │       │
│  │           "size": 5732989440                                     │       │
│  │         }                                                         │       │
│  │       ]                                                           │       │
│  │     }                                                             │       │
│  └──────────────────────────┬───────────────────────────────────────┘       │
│                             │                                                │
│                             ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  Blob Storage Access                                             │       │
│  │  5. Loads model from blob:                                       │       │
│  │     ~/.ollama/models/blobs/sha256-007aebc855f2e10a...            │       │
│  │     (5.3 GB GGUF file)                                           │       │
│  └──────────────────────────┬───────────────────────────────────────┘       │
│                             │                                                │
│                             ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  llama.cpp Inference Engine                                      │       │
│  │  6. Loads GGUF into RAM (if not already loaded)                  │       │
│  │  7. Applies system prompt from manifest                          │       │
│  │  8. Generates response using:                                    │       │
│  │     - Temperature: 0.7                                            │       │
│  │     - Template: Llama-3 chat format                              │       │
│  │     - Stop tokens: <|eot_id|>, <|end_of_text|>                   │       │
│  │  9. Returns response JSON:                                       │       │
│  │     {                                                             │       │
│  │       "response": "CCoP stands for...",                          │       │
│  │       "eval_count": 257,                                         │       │
│  │       "eval_duration": 19286739213                               │       │
│  │     }                                                             │       │
│  └──────────────────────────┬───────────────────────────────────────┘       │
└─────────────────────────────┼────────────────────────────────────────────────┘
                              │
                              │ HTTP 200 OK (JSON response)
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Evaluation Framework (continued)                                           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  OllamaGateway                                                   │       │
│  │  10. Parses response                                             │       │
│  │  11. Creates ModelResponse entity:                               │       │
│  │      - response_id: UUID                                         │       │
│  │      - content: "CCoP stands for..."                             │       │
│  │      - tokens_used: 257                                          │       │
│  │      - latency_ms: 19286                                         │       │
│  └──────────────────────────┬───────────────────────────────────────┘       │
│                             │                                                │
│                             ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  Domain Layer (Business Logic)                                   │       │
│  │  12. Evaluates response quality                                  │       │
│  │  13. Creates EvaluationResult entity                             │       │
│  │  14. Calculates scores                                           │       │
│  └──────────────────────────┬───────────────────────────────────────┘       │
│                             │                                                │
│                             ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │  Results Storage                                                 │       │
│  │  15. Saves to: results/evaluations/                              │       │
│  │      primus-reasoning_<timestamp>.json                           │       │
│  └─────────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                          STORAGE LAYOUT                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┐  ┌──────────────────────────────────┐
│  Your Project Directory          │  │  Ollama's Storage Directory      │
│  (Source Files - Can Delete)     │  │  (Production - Must Keep)        │
├──────────────────────────────────┤  ├──────────────────────────────────┤
│  models/                         │  │  ~/.ollama/models/               │
│  ├── primus-reasoning-source/    │  │  ├── blobs/                      │
│  │   └── *.safetensors (16.1GB) │  │  │   ├── sha256-007aebc... (5.3GB)│
│  ├── primus-reasoning-f16.gguf   │  │  │   ├── sha256-3f1f8b... (195B) │
│  │   (15 GB)                     │  │  │   ├── sha256-dfbdab... (162B) │
│  ├── primus-reasoning-Q5_K_M.gguf│  │  │   └── sha256-d2fe86... (62B)  │
│  │   (5.3 GB) ← Source           │  │  └── manifests/                  │
│  └── Modelfile                   │  │      └── registry.ollama.ai/     │
│                                  │  │          └── library/             │
│      ⚠️  NOT used during         │  │              └── primus-reasoning/│
│      evaluation - only           │  │                  └── latest       │
│      for building/import         │  │                                   │
│                                  │  │      ✅ Used during evaluation    │
└──────────────────────────────────┘  └──────────────────────────────────┘
                                              ▲
                                              │
                                              │ Ollama reads from here
                                              │ during inference
```

### How the Evaluation Framework Uses the Model

**Important:** The evaluation framework **never** accesses your local `models/` folder. It communicates with Ollama via HTTP API (localhost:11434), and Ollama serves the model from its own storage (`~/.ollama/models/`).

### Storage Implications

After `ollama create` completes:

| Location | Size | Purpose | Can Delete? |
|----------|------|---------|-------------|
| `models/primus-reasoning-source/` | 16.1 GB | Original PyTorch weights | ✅ Yes (after conversion) |
| `models/primus-reasoning-f16.gguf` | 15 GB | Intermediate GGUF | ✅ Yes (after quantization) |
| `models/primus-reasoning-Q5_K_M.gguf` | 5.3 GB | Source for Ollama import | ✅ Yes (after import to Ollama) |
| `~/.ollama/models/blobs/sha256-007aebc...` | 5.3 GB | Ollama's production copy | ❌ No (required for inference) |

You could delete the entire `models/` folder after import and Ollama would still work because it has its own independent copy.

### Why This Design?

Ollama uses content-addressable storage for:
- **Deduplication**: Multiple models can share common layers
- **Integrity**: SHA256 hashing prevents corruption
- **Versioning**: Support multiple versions (`:v1`, `:v2`, `:latest`)
- **Isolation**: Source files don't affect running models

---

## System Information

- **OS:** macOS (Darwin 25.1.0)
- **Architecture:** Apple Silicon (M3 Mac, 16GB RAM)
- **Python Version:** 3.13.5
- **Working Directory:** `/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/src`
- **Models Directory:** `/Users/sagarpratapsingh/dev/sagerstack/studio-ssdlc/models`

---

## Resources

- **Model Source:** https://huggingface.co/trendmicro-ailab/Llama-Primus-Reasoning
- **Documentation:** https://arxiv.org/html/2502.11191v1
- **Ollama:** Installed via Homebrew, running as service
