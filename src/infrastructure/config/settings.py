"""
Application Settings

Pydantic settings for configuration management.
Reads from environment variables and .env files.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings.

    All settings can be overridden via environment variables with CCOP_ prefix.
    """

    # Ollama Configuration
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Ollama API endpoint"
    )
    ollama_timeout: int = Field(
        default=300,
        description="Ollama request timeout in seconds"
    )

    # Model Configuration
    model_name: str = Field(
        default="primus-reasoning",
        description="Default model name"
    )
    model_hf_repo: str = Field(
        default="trendmicro-ailab/Llama-Primus-Reasoning",
        description="HuggingFace repository"
    )
    model_quantization: str = Field(
        default="Q5_K_M",
        description="Default quantization (Q4_K_M, Q5_K_M, Q6_K, Q8_0)"
    )
    model_cache_dir: Path = Field(
        default=Path.home() / ".cache" / "ccop-models",
        description="Model cache directory"
    )

    # Evaluation Configuration
    test_cases_dir: Path = Field(
        default=Path("../ground-truth/phase-2/test-suite"),
        description="Test cases directory (Phase 2 ground truth)"
    )
    results_dir: Path = Field(
        default=Path("results/evaluations"),
        description="Evaluation results directory"
    )
    max_concurrent_evaluations: int = Field(
        default=3,
        description="Maximum concurrent test evaluations"
    )

    # Evaluation Phase Configuration (Phase 2)
    evaluation_phase: str = Field(
        default="baseline",
        description="Evaluation phase: baseline, finetuned, deployment"
    )

    # Phase-Specific Pass Thresholds (Phase 2)
    baseline_threshold: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Pass threshold for baseline evaluation (15%)"
    )
    finetuned_threshold: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="Pass threshold for fine-tuned evaluation (50%)"
    )
    deployment_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Pass threshold for deployment evaluation (85%)"
    )

    # LLM Inference Parameters
    default_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Default temperature"
    )
    default_top_p: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Default top-p"
    )
    default_top_k: int = Field(
        default=40,
        ge=1,
        description="Default top-k"
    )
    default_max_tokens: int = Field(
        default=1024,
        ge=1,
        description="Default max tokens"
    )
    context_length: int = Field(
        default=4096,
        ge=512,
        description="Context window size"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_format: str = Field(
        default="json",
        description="Log format (json, console)"
    )
    log_file: Optional[Path] = Field(
        default=Path("logs/ccop-eval.log"),
        description="Log file path"
    )

    # Development/Debug
    debug: bool = Field(default=False, description="Debug mode")
    mock_mode: bool = Field(
        default=False,
        description="Use mock model gateway instead of real Ollama"
    )

    model_config = SettingsConfigDict(
        env_file="../config/.env.example",
        env_file_encoding="utf-8",
        env_prefix="CCOP_",
        case_sensitive=False,
        extra="ignore",
    )

    def __init__(self, **kwargs: any) -> None:
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.model_cache_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)


# Global settings instance (singleton pattern)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get global settings instance.

    Returns:
        Settings instance (singleton)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
