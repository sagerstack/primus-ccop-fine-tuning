"""
Evaluation Result Data Transfer Object

Pydantic model for evaluation results.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MetricDTO(BaseModel):
    """DTO for individual metric."""
    name: str
    value: float = Field(..., ge=0.0, le=1.0)
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    description: Optional[str] = None


class EvaluationResultDTO(BaseModel):
    """
    DTO for evaluation result.

    Represents the outcome of evaluating a single test case.
    """

    result_id: UUID = Field(..., description="Unique result identifier")
    test_id: str = Field(..., description="Test case ID")
    benchmark_type: str = Field(..., description="Benchmark category")
    model_name: str = Field(..., description="Model name")
    response_content: str = Field(..., description="Model's response")
    metrics: List[MetricDTO] = Field(default_factory=list, description="Evaluation metrics")
    overall_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall score")
    passed: Optional[bool] = Field(None, description="Pass/fail status")
    threshold: float = Field(..., ge=0.0, le=1.0, description="Passing threshold")
    evaluator_notes: str = Field(default="", description="Additional notes")
    tokens_used: int = Field(default=0, description="Tokens in response")
    latency_ms: int = Field(default=0, description="Response latency")
    evaluated_at: datetime = Field(default_factory=datetime.utcnow, description="Evaluation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "result_id": "123e4567-e89b-12d3-a456-426614174000",
                "test_id": "B1-001",
                "benchmark_type": "B1",
                "model_name": "primus-reasoning",
                "response_content": "CCoP 2.0 requires...",
                "metrics": [
                    {"name": "accuracy", "value": 0.85, "weight": 1.0},
                    {"name": "completeness", "value": 0.78, "weight": 0.8}
                ],
                "overall_score": 0.82,
                "passed": True,
                "threshold": 0.70,
                "evaluator_notes": "",
                "tokens_used": 256,
                "latency_ms": 1234,
                "evaluated_at": "2025-01-01T00:00:00",
                "metadata": {}
            }
        }
    }


class EvaluationSummaryDTO(BaseModel):
    """
    DTO for overall evaluation summary across multiple test cases.
    """

    model_name: str = Field(..., description="Model name")
    total_tests: int = Field(..., ge=0, description="Total number of tests")
    passed_tests: int = Field(..., ge=0, description="Number of passed tests")
    failed_tests: int = Field(..., ge=0, description="Number of failed tests")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall score")
    by_benchmark: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Results grouped by benchmark"
    )
    by_difficulty: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Results grouped by difficulty"
    )
    evaluation_started_at: datetime
    evaluation_completed_at: datetime
    total_duration_seconds: float = Field(..., ge=0.0, description="Total evaluation duration")
    results: List[EvaluationResultDTO] = Field(default_factory=list, description="Individual results")

    model_config = {
        "json_schema_extra": {
            "example": {
                "model_name": "primus-reasoning",
                "total_tests": 40,
                "passed_tests": 32,
                "failed_tests": 8,
                "overall_score": 0.78,
                "by_benchmark": {
                    "B1": {"total": 10, "passed": 8, "score": 0.82},
                    "B2": {"total": 5, "passed": 4, "score": 0.75}
                },
                "by_difficulty": {
                    "low": {"total": 10, "passed": 10, "score": 0.95},
                    "medium": {"total": 15, "passed": 12, "score": 0.80}
                },
                "evaluation_started_at": "2025-01-01T00:00:00",
                "evaluation_completed_at": "2025-01-01T01:00:00",
                "total_duration_seconds": 3600.0,
                "results": []
            }
        }
    }
