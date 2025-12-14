"""
Evaluation Request Data Transfer Object

Pydantic model for evaluation request parameters.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class EvaluationRequestDTO(BaseModel):
    """
    DTO for evaluation request.

    Contains parameters for running model evaluation.
    """

    model_name: str = Field(..., description="Name of the model to evaluate")
    benchmark_types: List[str] = Field(
        default_factory=lambda: ["B1", "B2", "B3", "B4", "B5", "B6"],
        description="Benchmarks to evaluate (default: all)"
    )
    test_case_ids: Optional[List[str]] = Field(
        None,
        description="Specific test case IDs (if None, runs all for selected benchmarks)"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for model generation"
    )
    max_tokens: Optional[int] = Field(
        None,
        ge=1,
        description="Max tokens (if None, uses test case difficulty default)"
    )
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling")
    top_k: int = Field(default=40, ge=1, description="Top-k sampling")
    save_results: bool = Field(default=True, description="Save results to disk")
    results_dir: Optional[str] = Field(None, description="Results output directory")

    # Phase 2: Configurable evaluation phase and threshold
    evaluation_phase: str = Field(
        default="baseline",
        description="Evaluation phase: baseline, finetuned, deployment"
    )
    pass_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Pass threshold override (if None, uses phase-specific default)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "model_name": "primus-reasoning",
                "benchmark_types": ["B1", "B3"],
                "test_case_ids": None,
                "temperature": 0.7,
                "max_tokens": None,
                "top_p": 0.9,
                "top_k": 40,
                "save_results": True,
                "results_dir": "results/evaluations"
            }
        }
    }
