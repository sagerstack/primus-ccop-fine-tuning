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
    cu_extraction_model: str = Field(
        default="anthropic/claude-sonnet-4",
        description=(
            "OpenRouter model id for Phase-11 Compliance-Unit classification "
            "(Stage 1, `cu_classifier.py`) and 4-tuple extraction (Stage 2, "
            "`cu_extractor.py`), routed through `OpenRouterGateway` "
            "(OpenRouter credits, decoupled from the `claude -p` Claude "
            "subscription that hit daily token limits mid-build, 2026-07-05). "
            "Must be an OpenRouter model id (verify on openrouter.ai/models). "
            "Override via CCOP_CU_EXTRACTION_MODEL. Reuses `claude_cli_timeout` "
            "as the per-call timeout bound and `judge_max_retries` for retries."
        )
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
    judge_seed: Optional[int] = Field(
        default=None,
        description="Fixed seed for LLM-Judge calls (passed to OpenRouterClient). None = default. Set an int with judge_temperature=0 for more reproducible judging (note: qwen3-235b is MoE/OpenRouter so residual nondeterminism remains). Env: CCOP_JUDGE_SEED",
    )
    judge_max_retries: int = Field(
        default=3,
        description="Max retries on OpenRouter API failure before raising JudgeAPIError"
    )
    judge_json_retry_attempts: int = Field(
        default=3,
        description=(
            "Max attempts for the rubric/universal judge to return parseable JSON. "
            "Separate from judge_max_retries: this catches successful API responses "
            "that contain malformed JSON (e.g., Qwen truncating mid-thought). Each "
            "attempt re-calls the judge for a fresh response."
        )
    )
    judge_timeout: int = Field(
        default=60,
        description="Per-call timeout in seconds for OpenRouter judge calls"
    )
    retrieval_evaluator_model: str = Field(
        default="qwen/qwen3-235b-a22b-07-25",
        description="OpenRouter model id for the retrieval evaluator (per-clause relevance/answer-support scoring for filtering). Env: CCOP_RETRIEVAL_EVALUATOR_MODEL",
    )
    retrieval_evaluator_temperature: float = Field(
        default=0.0,
        description="Sampling temperature for the retrieval evaluator (0 for near-deterministic). Env: CCOP_RETRIEVAL_EVALUATOR_TEMPERATURE",
    )
    graphont_pool_k: int = Field(
        default=8,
        ge=1,
        le=50,
        description="Number of internally ranked graphont candidates retained before the final primary-context cap. Env: CCOP_GRAPHONT_POOL_K",
    )
    graphont_top_k: int = Field(
        default=8,
        ge=1,
        le=20,
        description="Top-k retrieved candidates for --mode graphont (default 8 = paper baseline; configurable for recall@k experiments). Env: CCOP_GRAPHONT_TOP_K",
    )
    graphont_agentic_pool_k: int = Field(
        default=8,
        ge=1,
        le=50,
        description="Number of retrieved candidates the retrieval evaluator scores in graphont-agentic mode (default 8 = same pool as graphont). Env: CCOP_GRAPHONT_AGENTIC_POOL_K",
    )
    graphont_agentic_top_k: int = Field(
        default=8,
        ge=1,
        le=20,
        description="Maximum primary clause contexts retained after graphont-agentic evaluator filtering. Definitions do not consume this budget. Env: CCOP_GRAPHONT_AGENTIC_TOP_K",
    )
    graphont_agentic_filter_min_score: int = Field(
        default=1,
        description="Keep clauses whose retrieval-evaluator score >= this in graphont-agentic mode (1 = retention-safe; 2 = aggressive). Env: CCOP_GRAPHONT_AGENTIC_FILTER_MIN_SCORE",
    )
    graphont_hyde_enabled: bool = Field(
        default=False,
        description="Enable HyDE hypothetical-clause dense retrieval in plain graphont mode. Default False preserves the graphont baseline. Env: CCOP_GRAPHONT_HYDE_ENABLED",
    )
    graphont_agentic_hyde_enabled: bool = Field(
        default=False,
        description="Enable HyDE (hypothetical-clause dense retrieval) in graphont-agentic mode. Default False = agentic baseline unchanged. Env: CCOP_GRAPHONT_AGENTIC_HYDE_ENABLED",
    )
    hyde_cache_enabled: bool = Field(
        default=True,
        description="Cache HyDE generations for deterministic comparisons. Env: CCOP_HYDE_CACHE_ENABLED",
    )
    graphont_agentic_corrective_enabled: bool = Field(
        default=False,
        description="Enable CRAG-style corrective retrieval (Round-2 rewrite+retrieve when Round-1 is Incorrect/Ambiguous) in graphont-agentic mode. Default False = corrective OFF until calibrated. Env: CCOP_GRAPHONT_AGENTIC_CORRECTIVE_ENABLED",
    )
    graphont_agentic_corrective_rewrite_model: str = Field(
        default="openai/gpt-4o-mini-2024-07-18",
        description="OpenRouter model id for corrective query rewrite (canonical vocabulary, neutral). Env: CCOP_GRAPHONT_AGENTIC_CORRECTIVE_REWRITE_MODEL",
    )
    graphont_agentic_corrective_max_retries: int = Field(
        default=1,
        ge=0,
        le=2,
        description="Maximum corrective retrieval attempts in graphont-agentic mode (0 = corrective OFF even if enabled; 1 = one Round-2 attempt; 2 = two attempts max). Env: CCOP_GRAPHONT_AGENTIC_CORRECTIVE_MAX_RETRIES",
    )
    query_concepts_cache_enabled: bool = Field(
        default=True,
        description="Cache query_to_concepts LLM extraction (keyed by model|build_id|question) for deterministic/reproducible retrieval pools. Env: CCOP_QUERY_CONCEPTS_CACHE_ENABLED",
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
    generation_seed: Optional[int] = Field(
        default=None,
        description="Fixed seed for Primus (Ollama) generation. None = nondeterministic (default). Set an int (e.g. 0) with temperature 0 for fully reproducible generation. Env: CCOP_GENERATION_SEED",
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
        default=3,  # 8→3 (2026-04-27): too much context confused the model (44K-char prompts); short queries had reranker scores clustered at logits 0.000–0.080 with no clear winner, so 8 chunks brought verbosity without precision gain. Lab Exp #41 retrieval recall metric was at top_n=C cardinality not top_n=8.
        ge=1,
        le=20,
        description="Number of documents to keep after cross-encoder reranking"
    )
    cross_encoder_model: str = Field(
        default="BAAI/bge-reranker-large",  # Per Exp #7
        description="Cross-encoder model for reranking (HuggingFace model ID)"
    )

    # Production retrieval architecture (per lab research, Exp #41)
    rag_retrieval_mode: str = Field(
        default="dense",  # vs "hybrid"; per Exp #11 — dense-only beats hybrid+RRF
        description="Retrieval mode: 'dense' (pure cosine), 'hybrid' (RRF dense+sparse), or 'sparse'"
    )
    rag_contextualization_enabled: bool = Field(
        default=False,
        description="Whether to route retrieval to the Contextual-Retrieval collection (breadcrumb + LLM-generated context per chunk, Exp #14/#41). Default False = opt-in: the contextual collection must be built first (.lab/workspace/contextualize_corpus*.py) or retrieval 404s. See ADR-010. Env: CCOP_RAG_CONTEXTUALIZATION_ENABLED; CLI: --contextual"
    )
    rag_contextualization_model: str = Field(
        default="openai/gpt-4o-mini",
        description="OpenRouter model for context generation (acronyms-only prompt per Exp #41)"
    )
    rag_hyde_enabled: bool = Field(
        default=False,
        description="Whether to apply HyDE query rewriting before retrieval in hybrid/rag-only (Exp #17). Default OFF (ADR-011): opt in per run with `--hyde`. Held off so all modes share the same HyDE state by default (graphont/graphont-agentic default off too). Env: CCOP_RAG_HYDE_ENABLED"
    )
    rag_hyde_model: str = Field(
        default="openai/gpt-4o-mini",
        description="OpenRouter model for HyDE hypothetical-clause generation"
    )
    rag_rrf_dense_weight: float = Field(
        default=1.0,
        description="RRF weight on dense rank (Exp #28 found CE-favored 1:1.5 best)"
    )
    rag_rrf_ce_weight: float = Field(
        default=1.5,
        description="RRF weight on cross-encoder rank (Exp #28)"
    )
    rag_merge_parent_enabled: bool = Field(
        default=True,
        description="Whether to merge sibling chunks into parent groups after reranking (Exp #16)"
    )
    rag_merge_window: int = Field(
        default=40,
        description="Top-K reranked window size for parent-child sibling detection (Exp #33)"
    )
    rag_merge_min_siblings: int = Field(
        default=2,
        description="Minimum sibling clauses required to trigger parent merge"
    )
    rag_merge_min_score_ratio: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description=(
            "Relevance gate for parent-child merge: only include sibling members "
            "whose cross-encoder score is at least this fraction of the anchor's score. "
            "Prevents weak siblings (e.g., adjacent clauses on different sub-topics) "
            "from being bundled into a slot just because they share a parent. "
            "Set to 0.0 to disable the gate (legacy behaviour: all in-window siblings merge)."
        ),
    )
    rag_merge_max_members: int = Field(
        default=4,
        ge=2,
        le=10,
        description=(
            "Hard cap on members in a single merged group, taken from the highest-scoring "
            "siblings. Prevents one slot from dominating the LLM context budget when a "
            "section has many siblings (e.g., chapter 11 with 50+ sub-clauses)."
        ),
    )
    rag_collection_name_contextual: str = Field(
        default="ccop_clauses_contextual_v3",
        description="Production Qdrant collection with contextual augmentation (Exp #41)"
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

    # ------------------------------------------------------------------
    # Neo4j GraphRAG Configuration (Phase 9 — emergent-KG baseline)
    # ------------------------------------------------------------------
    # Connection (D-01/D-12): local Docker Neo4j alongside qdrant.
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j Bolt URI (local Docker service)"
    )
    neo4j_user: str = Field(
        default="neo4j",
        description="Neo4j username"
    )
    neo4j_password: Optional[str] = Field(
        default=None,
        description=(
            "Neo4j password. No insecure default — supply via CCOP_NEO4J_PASSWORD "
            "in config/.env.local (must match docker-compose NEO4J_AUTH). Never a "
            "committed literal."
        )
    )
    neo4j_database: str = Field(
        default="neo4j",
        description="Neo4j database name"
    )
    graph_vector_index_name: str = Field(
        default="ccop_chunk_embeddings",
        description="Neo4j vector index name for chunk embeddings (CCOP_GRAPH_VECTOR_INDEX)",
        alias="CCOP_GRAPH_VECTOR_INDEX",
    )
    graph_fulltext_index_name: str = Field(
        default="ccop_chunk_fulltext",
        description=(
            "Neo4j fulltext (Lucene) index name over Chunk.text — the sparse leg of "
            "the graph HybridCypherRetriever (Wave-6 retrieval parity: dense + sparse, "
            "mirroring hybrid's dense+BM25 RRF). NOTE: Lucene BM25 is an approximate, "
            "not bit-identical, parity to hybrid's fastembed BM25 (CCOP_GRAPH_FULLTEXT_INDEX)."
        ),
        alias="CCOP_GRAPH_FULLTEXT_INDEX",
    )

    # GraphRAG infrastructure models — held constant across Phase 9 and Phase 10
    # (D-16 additivity). Kept as explicit standalone fields so they remain an
    # interceptable seam for ontology-governed extraction in Phase 10.
    graph_extraction_model: str = Field(
        default="openai/gpt-4o-mini",
        description=(
            "KG entity/relationship extraction LLM (D-06a) — runs via OpenRouter "
            "(reuses openrouter_api_key / openrouter_base_url). Held constant across "
            "Phase 9 and Phase 10 so the ablation isolates the ontology, not the model."
        )
    )
    graph_embedding_model: str = Field(
        default="BAAI/bge-large-en-v1.5",
        description=(
            "GraphRAG embedding model (D-07) — in-process SentenceTransformer, exact "
            "parity with hybrid's CCOP_QDRANT_EMBEDDING_MODEL. Held constant across "
            "Phase 9 and Phase 10."
        )
    )
    graph_embedding_dimensions: int = Field(
        default=1024,
        ge=1,
        description="Embedding vector dimensionality for the Neo4j vector index (bge-large-en-v1.5 = 1024, D-07)"
    )

    # ------------------------------------------------------------------
    # Neo4j GraphRAG Ontology Configuration (Phase 10 — ontology-grounded KG)
    # ------------------------------------------------------------------
    # Front-loaded here (plan 10-02) so NO other Phase 10 plan needs to touch
    # settings.py — single-owner seam, avoids same-wave write conflicts in
    # Waves 3 and 5 (10-08/10-09 both read settings in the same wave).
    ontology_config_path: str = Field(
        default="src/rag/graph/ontology/ontology_config.json",
        description=(
            "Path to the Phase 10 ontology config (entity/relation/function-type "
            "schema, D-01). File is created by a later Phase 10 plan."
        )
    )
    shacl_shapes_path: str = Field(
        default="src/rag/graph/ontology/shapes.ttl",
        description=(
            "Path to the SHACL shapes file used to validate ontology-grounded "
            "extraction (D-02/D-03). File is created by a later Phase 10 plan."
        )
    )
    ontology_discovery_model: str = Field(
        default="openai/gpt-4o-mini",
        description=(
            "LLM used for ontology-guided discovery/extraction passes (Phase 10, "
            "D-06a parity with graph_extraction_model) — runs via OpenRouter."
        )
    )
    function_type_boost: float = Field(
        default=1.5,
        gt=0,
        description=(
            "Retrieval-time score boost applied to nodes matching the query's "
            "inferred function-type (D-12). Applied by the real clause-anchored "
            "retrieval query landing in plan 10-09."
        )
    )
    gleaning_max_gleanings: int = Field(
        default=1,
        ge=0,
        description="Maximum number of additional 'gleaning' extraction passes per chunk (D-11)"
    )
    graphrag_ontology_enabled: bool = Field(
        default=True,
        description="Feature flag gating the Phase 10 `graphrag-ontology` mode and its DI provider"
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
