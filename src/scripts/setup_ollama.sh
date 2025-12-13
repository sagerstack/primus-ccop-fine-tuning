#!/usr/bin/env bash
#
# CCoP 2.0 Evaluation Framework - Ollama Setup Script
#
# This script installs Ollama on macOS and verifies the installation
#
# Usage:
#   ./scripts/setup_ollama.sh
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Main installation function
main() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  CCoP 2.0 - Ollama Setup${NC}"
    echo -e "${BLUE}========================================${NC}\n"

    # Check if Ollama is already installed
    if command_exists ollama; then
        print_success "Ollama is already installed"
        ollama --version

        print_info "Checking if Ollama service is running..."
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            print_success "Ollama service is running"
        else
            print_warning "Ollama is installed but not running"
            print_info "Starting Ollama service..."
            ollama serve &
            sleep 3
            print_success "Ollama service started"
        fi
    else
        print_info "Ollama not found. Installing..."

        # Detect OS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            print_info "Detected macOS"

            # Check if Homebrew is installed
            if command_exists brew; then
                print_info "Installing Ollama via Homebrew..."
                brew install ollama
            else
                print_warning "Homebrew not found. Downloading installer from ollama.com..."
                curl -fsSL https://ollama.com/install.sh | sh
            fi
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            print_info "Detected Linux"
            print_info "Installing Ollama..."
            curl -fsSL https://ollama.com/install.sh | sh
        else
            print_error "Unsupported operating system: $OSTYPE"
            print_info "Please visit https://ollama.com/download for manual installation"
            exit 1
        fi

        print_success "Ollama installed successfully"
        ollama --version
    fi

    # Start Ollama service if not running
    print_info "Ensuring Ollama service is running..."
    if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_info "Starting Ollama service in background..."
        nohup ollama serve > /tmp/ollama.log 2>&1 &
        sleep 3
    fi

    # Verify Ollama is accessible
    print_info "Verifying Ollama API accessibility..."
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_success "Ollama API is accessible at http://localhost:11434"
    else
        print_error "Failed to connect to Ollama API"
        print_info "Please check logs: tail -f /tmp/ollama.log"
        exit 1
    fi

    # List installed models
    print_info "Checking installed models..."
    ollama list

    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}  Ollama Setup Complete!${NC}"
    echo -e "${GREEN}========================================${NC}\n"

    print_info "Next steps:"
    echo "  1. Convert Llama-Primus-Reasoning to GGUF: ./scripts/convert_to_gguf.sh"
    echo "  2. Or use the CLI: poetry run ccop-eval setup"
    echo ""
}

# Run main function
main "$@"
