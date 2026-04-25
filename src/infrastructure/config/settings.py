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

    # Claude CLI Configuration
    claude_cli_timeout: int = Field(
        default=120,
        description="Claude CLI request timeout in seconds"
    )

    # LLM Judge Configuration
    llm_judge_model: str = Field(
        default="sonnet",
        description="DEPRECATED: legacy Claude CLI judge model (superseded by openrouter_* fields below)"
    )
    judge_mode: str = Field(
        default="rubric",
        description="Judge mode: rubric (per-benchmark rubrics) or universal (reasoning depth + hallucination)"
    )

    # OpenRouter Judge Configuration (Path B 2-judge methodology)
    openrouter_api_key: Optional[str] = Field(
        default=None,
        description="OpenRouter API key (required for judge calls; set in .env.local)"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter OpenAI-compatible API base URL"
    )
    judge_primary_model: str = Field(
        default="qwen/qwen3-235b-a22b-07-25",
        description="Primary judge model ID on OpenRouter (runs on every eval)"
    )
    judge_secondary_model: str = Field(
        default="openai/gpt-4o-mini-2024-07-18",
        description="Secondary judge model ID on OpenRouter (runs only for inter-judge kappa measurement snapshots)"
    )
    judge_temperature: float = Field(
        default=0.2,
        description="Judge sampling temperature (0.0-1.0); 0.2 is the variance-reduction sweet spot"
    )
    judge_max_retries: int = Field(
        default=3,
        description="Max retries on OpenRouter API failure before raising JudgeAPIError"
    )
    judge_timeout: int = Field(
        default=60,
        description="Per-call timeout in seconds for OpenRouter judge calls"
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
        default=Path("../ground-truth/test-suite"),
        description="Test cases directory (v2 ground truth)"
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
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Default temperature (0.3 balances reproducibility with reasoning depth)"
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

    # Databricks Configuration (RAG Infrastructure)
    databricks_host: Optional[str] = Field(
        default=None,
        description="Databricks workspace host URL"
    )
    databricks_token: Optional[str] = Field(
        default=None,
        description="Databricks access token"
    )
    databricks_catalog: Optional[str] = Field(
        default=None,
        description="Databricks Unity Catalog name"
    )
    databricks_schema: Optional[str] = Field(
        default=None,
        description="Databricks schema name"
    )
    databricks_vector_search_endpoint: Optional[str] = Field(
        default=None,
        description="Databricks Vector Search endpoint name"
    )
    databricks_embedding_endpoint: Optional[str] = Field(
        default=None,
        description="Databricks embedding model endpoint name"
    )
    databricks_warehouse_id: Optional[str] = Field(
        default=None,
        description="Databricks SQL Warehouse ID for statement execution"
    )

    # RAG Pipeline Configuration
    rag_grading_enabled: bool = Field(
        default=False,
        description="DEPRECATED: Grading is now measurement-only. This setting is ignored."
    )
    rag_retrieval_top_k: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Number of documents to retrieve before reranking"
    )

    # Ingestion Pipeline Configuration
    preamble_max_words: int = Field(
        default=500,
        ge=100,
        description="Max words for preamble chunks before paragraph-based splitting"
    )
    section_chunk_min_tokens: int = Field(
        default=200,
        ge=50,
        description="Merge threshold for section-based chunker (tokens)"
    )
    section_chunk_max_tokens: int = Field(
        default=1000,
        ge=200,
        description="Split threshold for section-based chunker (tokens)"
    )
    # Diagram Captioning (GLM-4V via ZhipuAI)
    diagram_captioning_enabled: bool = Field(
        default=False,
        description="Enable diagram captioning with GLM-4V vision model"
    )
    zhipuai_api_key: Optional[str] = Field(
        default=None,
        description="ZhipuAI API key for GLM-4V diagram captioning"
    )
    zhipuai_base_url: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4",
        description="ZhipuAI API base URL"
    )
    zhipuai_model: str = Field(
        default="glm-4.6v",
        description="ZhipuAI vision model name"
    )
    zhipuai_timeout: int = Field(
        default=60,
        ge=10,
        description="ZhipuAI request timeout in seconds"
    )
    zhipuai_max_tokens: int = Field(
        default=512,
        ge=64,
        description="Max tokens for diagram description"
    )
    diagram_captioning_prompt: str = Field(
        default="Describe this diagram from a cybersecurity regulatory document. Focus on the structure, relationships, and key information conveyed. Be concise and factual.",
        description="Prompt sent to vision model for diagram captioning"
    )
    garbled_text_repetition_threshold: int = Field(
        default=5,
        ge=2,
        description="N-gram repetition threshold for garbled text detection"
    )

    # Retrieval Funnel Configuration (Phase 1.3)
    rerank_top_n: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Number of documents to keep after cross-encoder reranking"
    )
    cross_encoder_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L12-v2",
        description="Cross-encoder model for reranking (HuggingFace model ID)"
    )

    # RAGAs Configuration
    ragas_enabled: bool = Field(
        default=True,
        description="Enable RAGAs evaluation alongside benchmark scoring"
    )
    ragas_evaluator_model: str = Field(
        default="mistral-small-latest",
        description="Model name for RAGAs evaluator LLM"
    )
    ragas_api_key: Optional[str] = Field(
        default=None,
        description="API key for RAGAs evaluator LLM provider (OpenAI-compatible)"
    )
    ragas_api_base_url: str = Field(
        default="https://api.mistral.ai/v1",
        description="API base URL for RAGAs evaluator LLM provider (OpenAI-compatible)"
    )
    ragas_embedding_model: str = Field(
        default="BAAI/bge-large-en-v1.5",
        description="HuggingFace embedding model for RAGAs semantic similarity"
    )

    # Qdrant Configuration (Local RAG)
    qdrant_url: Optional[str] = Field(
        default=None,
        description="Qdrant REST API URL (e.g., http://localhost:6333)"
    )
    qdrant_collection_name: Optional[str] = Field(
        default=None,
        description="Qdrant collection name for CCoP clauses (e.g., ccop_clauses_hybrid)"
    )
    qdrant_embedding_model: Optional[str] = Field(
        default=None,
        description="Dense embedding model name (e.g., BAAI/bge-large-en-v1.5)"
    )
    qdrant_sparse_model: Optional[str] = Field(
        default=None,
        description="Sparse embedding model name for BM25 (e.g., Qdrant/bm25)"
    )

    model_config = SettingsConfigDict(
        env_file=("config/.env.example", "config/.env.local"),
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
