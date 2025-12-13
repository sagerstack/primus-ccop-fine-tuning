#!/usr/bin/env bash
#
# CCoP 2.0 Evaluation Framework - Model Conversion Script
#
# This script converts Llama-Primus-Reasoning from HuggingFace to GGUF format
# and imports it into Ollama
#
# Usage:
#   ./scripts/convert_to_gguf.sh [QUANTIZATION]
#
# Arguments:
#   QUANTIZATION: Q4_K_M, Q5_K_M (default), Q6_K, Q8_0
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MODEL_HF_REPO="trendmicro-ailab/Llama-Primus-Reasoning"
MODEL_NAME="primus-reasoning"
QUANTIZATION="${1:-Q5_K_M}"
WORK_DIR="$(pwd)/models/conversion"
LLAMA_CPP_DIR="$WORK_DIR/llama.cpp"
MODEL_DIR="$WORK_DIR/hf-model"
OUTPUT_DIR="$WORK_DIR/gguf"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Validate quantization level
validate_quantization() {
    case "$QUANTIZATION" in
        Q4_K_M|Q5_K_M|Q6_K|Q8_0)
            print_success "Using quantization: $QUANTIZATION"
            ;;
        *)
            print_error "Invalid quantization: $QUANTIZATION"
            echo "Valid options: Q4_K_M, Q5_K_M, Q6_K, Q8_0"
            exit 1
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check Python
    if ! command_exists python3; then
        print_error "Python 3 not found. Please install Python 3.10+"
        exit 1
    fi

    # Check git
    if ! command_exists git; then
        print_error "git not found. Please install git"
        exit 1
    fi

    # Check huggingface-cli
    if ! command_exists huggingface-cli; then
        print_warning "huggingface-cli not found. Installing..."
        pip install -U huggingface_hub
    fi

    # Check Ollama
    if ! command_exists ollama; then
        print_error "Ollama not found. Please run ./scripts/setup_ollama.sh first"
        exit 1
    fi

    print_success "All prerequisites satisfied"
}

# Create working directories
setup_directories() {
    print_info "Setting up working directories..."
    mkdir -p "$WORK_DIR" "$MODEL_DIR" "$OUTPUT_DIR"
    print_success "Working directory: $WORK_DIR"
}

# Clone or update llama.cpp
setup_llama_cpp() {
    print_info "Setting up llama.cpp..."

    if [ -d "$LLAMA_CPP_DIR" ]; then
        print_info "llama.cpp already exists, updating..."
        cd "$LLAMA_CPP_DIR"
        git pull
    else
        print_info "Cloning llama.cpp..."
        git clone https://github.com/ggerganov/llama.cpp.git "$LLAMA_CPP_DIR"
        cd "$LLAMA_CPP_DIR"
    fi

    # Build llama.cpp
    print_info "Building llama.cpp..."
    make clean
    make

    # Install Python dependencies
    print_info "Installing Python dependencies for conversion..."
    pip install -r requirements.txt

    print_success "llama.cpp setup complete"
    cd - > /dev/null
}

# Download model from HuggingFace
download_model() {
    print_info "Downloading $MODEL_HF_REPO from HuggingFace..."

    if [ -d "$MODEL_DIR" ] && [ "$(ls -A $MODEL_DIR)" ]; then
        print_warning "Model directory not empty. Skipping download."
        print_info "To re-download, delete: $MODEL_DIR"
    else
        huggingface-cli download "$MODEL_HF_REPO" \
            --local-dir "$MODEL_DIR" \
            --local-dir-use-symlinks False

        print_success "Model downloaded to $MODEL_DIR"
    fi
}

# Convert to GGUF
convert_to_gguf() {
    print_info "Converting model to GGUF (FP16)..."

    cd "$LLAMA_CPP_DIR"

    OUTPUT_F16="$OUTPUT_DIR/${MODEL_NAME}-f16.gguf"

    python convert_hf_to_gguf.py "$MODEL_DIR" \
        --outfile "$OUTPUT_F16" \
        --outtype f16

    print_success "FP16 GGUF created: $OUTPUT_F16"

    # Quantize
    print_info "Quantizing to $QUANTIZATION..."

    OUTPUT_QUANT="$OUTPUT_DIR/${MODEL_NAME}-${QUANTIZATION}.gguf"

    ./llama-quantize "$OUTPUT_F16" "$OUTPUT_QUANT" "$QUANTIZATION"

    print_success "Quantized GGUF created: $OUTPUT_QUANT"

    # Clean up FP16 version to save space
    print_info "Cleaning up intermediate FP16 file..."
    rm -f "$OUTPUT_F16"

    cd - > /dev/null

    echo "$OUTPUT_QUANT"
}

# Import to Ollama
import_to_ollama() {
    local gguf_file="$1"

    print_info "Creating Modelfile for Ollama..."

    MODELFILE="$OUTPUT_DIR/Modelfile"

    cat > "$MODELFILE" << EOF
FROM $gguf_file

TEMPLATE """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{{ .System }}<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{{ .Prompt }}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""

SYSTEM """You are a cybersecurity compliance expert specializing in Singapore's CCoP 2.0 (Cybersecurity Code of Practice) standards for Critical Information Infrastructure."""

PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_of_text|>"
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 4096
EOF

    print_success "Modelfile created"

    print_info "Importing model to Ollama as '$MODEL_NAME'..."
    ollama create "$MODEL_NAME" -f "$MODELFILE"

    print_success "Model imported to Ollama"
}

# Test the model
test_model() {
    print_info "Testing model with sample question..."

    echo -e "\n${YELLOW}Question:${NC} What is CCoP 2.0?\n"

    ollama run "$MODEL_NAME" "What is Singapore's CCoP 2.0 and why is it important for Critical Information Infrastructure?"

    echo ""
}

# Main execution
main() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  CCoP 2.0 - Model Conversion${NC}"
    echo -e "${BLUE}========================================${NC}\n"

    validate_quantization
    check_prerequisites
    setup_directories
    setup_llama_cpp
    download_model

    gguf_file=$(convert_to_gguf)

    import_to_ollama "$gguf_file"

    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}  Conversion Complete!${NC}"
    echo -e "${GREEN}========================================${NC}\n"

    print_info "Model details:"
    echo "  - Name: $MODEL_NAME"
    echo "  - Quantization: $QUANTIZATION"
    echo "  - GGUF file: $gguf_file"
    echo ""

    print_info "List installed models:"
    ollama list

    echo ""
    print_info "Would you like to test the model? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        test_model
    fi

    echo ""
    print_success "All done! Use 'ollama run $MODEL_NAME' to interact with the model"
    print_info "Or use the CLI: poetry run ccop-eval evaluate --model $MODEL_NAME"
}

# Run main function
main "$@"
