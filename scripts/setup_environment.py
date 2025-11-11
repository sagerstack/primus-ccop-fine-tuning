#!/usr/bin/env python3
"""
Environment Setup Script

This script sets up the development environment for the CCoP 2.0 fine-tuning project.
It handles dependency installation, configuration setup, and initial environment validation.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

def run_command(command: str, cwd: Optional[Path] = None) -> bool:
    """Run a shell command and return success status."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ Success: {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {command}")
        print(f"Error output: {e.stderr}")
        return False

def setup_poetry_environment():
    """Set up Poetry environment and install dependencies."""
    print("🔧 Setting up Poetry environment...")

    # Check if Poetry is installed
    if not run_command("poetry --version"):
        print("❌ Poetry is not installed. Please install Poetry first.")
        print("Visit: https://python-poetry.org/docs/#installation")
        return False

    # Install dependencies
    if not run_command("poetry install"):
        print("❌ Failed to install dependencies")
        return False

    print("✅ Poetry environment setup complete")
    return True

def create_directories():
    """Create necessary directories if they don't exist."""
    print("📁 Creating project directories...")

    directories = [
        "data/benchmark",
        "models/checkpoints",
        "benchmarks/results",
        "logs",
        "config/secrets"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

    return True

def setup_environment_variables():
    """Set up environment variables."""
    print("🔐 Setting up environment variables...")

    env_file = Path(".env")
    if env_file.exists():
        print("⚠️  .env file already exists")
        return True

    env_content = """# Environment Variables for CCoP Fine-tuning Project

# API Keys (replace with your actual keys)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=config/service-account.json
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_BUCKET=your-bucket-name

# Hugging Face Configuration
HUGGINGFACE_HUB_TOKEN=your_huggingface_token_here

# Colab Configuration
COLAB_DRIVE_FOLDER_ID=your_google_drive_folder_id

# Environment
ENVIRONMENT=development
"""

    env_file.write_text(env_content)
    print("✅ Created .env file")
    return True

def validate_setup():
    """Validate the setup by checking key components."""
    print("🔍 Validating setup...")

    # Check Poetry environment
    if not run_command("poetry run python --version"):
        print("❌ Poetry environment validation failed")
        return False

    # Check key directories
    required_dirs = ["src", "data", "models", "benchmarks", "config"]
    for directory in required_dirs:
        if not Path(directory).exists():
            print(f"❌ Required directory missing: {directory}")
            return False

    # Check configuration files
    required_files = ["pyproject.toml", "CLAUDE.md", "README.md"]
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ Required file missing: {file}")
            return False

    print("✅ Setup validation complete")
    return True

def main():
    """Main setup function."""
    print("🚀 Starting CCoP 2.0 Fine-tuning Environment Setup")
    print("=" * 60)

    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Setup steps
    steps = [
        ("Poetry Environment", setup_poetry_environment),
        ("Directory Structure", create_directories),
        ("Environment Variables", setup_environment_variables),
        ("Setup Validation", validate_setup),
    ]

    for step_name, step_func in steps:
        print(f"\n📋 {step_name}")
        print("-" * 40)

        if not step_func():
            print(f"\n❌ Setup failed at {step_name}")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("🎉 Environment setup complete!")
    print("\nNext steps:")
    print("1. Update .env file with your API keys")
    print("2. Run 'poetry shell' to activate the environment")
    print("3. Start with the Colab notebooks in the colab/ directory")

if __name__ == "__main__":
    main()