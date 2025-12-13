"""
Test Case Data Transfer Object

Pydantic model for transferring test case data across application boundaries.
"""

from typing import Any, Dict

from pydantic import BaseModel, Field


class TestCaseDTO(BaseModel):
    """
    DTO for test case data transfer.

    Used to pass test case data between layers without exposing
    domain entities outside the application core.
    """

    test_id: str = Field(..., description="Unique test identifier (e.g., B1-001)")
    benchmark_type: str = Field(..., description="Benchmark category (B1-B6)")
    section: str = Field(..., description="CCoP 2.0 section")
    clause_reference: str = Field(..., description="CCoP clause reference")
    difficulty: str = Field(..., description="Difficulty level (low/medium/high/critical)")
    question: str = Field(..., description="Test question")
    expected_response: str = Field(..., description="Expected answer")
    evaluation_criteria: Dict[str, Any] = Field(
        default_factory=dict,
        description="Evaluation criteria"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "test_id": "B1-001",
                "benchmark_type": "B1",
                "section": "Governance",
                "clause_reference": "5.1.2",
                "difficulty": "medium",
                "question": "What are the governance requirements for CIIOs under CCoP 2.0?",
                "expected_response": "CCoP 2.0 requires CIIOs to establish...",
                "evaluation_criteria": {
                    "accuracy": 0.8,
                    "completeness": 0.7
                },
                "metadata": {
                    "domain": "IT/OT",
                    "tags": ["governance", "compliance"]
                }
            }
        }
    }
