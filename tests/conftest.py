"""
Pytest configuration and shared fixtures.
"""
import sys
from pathlib import Path

# Add src to path so tests can import modules
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
from datetime import datetime
from typing import Dict, Any, List

from domain.entities.test_case import TestCase
from domain.entities.model_response import ModelResponse
from domain.entities.evaluation_result import EvaluationResult
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.difficulty_level import DifficultyLevel
from domain.value_objects.ccop_section import CCoPSection
from domain.value_objects.evaluation_metric import EvaluationMetric


@pytest.fixture
def sample_b1_test_case() -> TestCase:
    """Create a sample B1 test case for testing."""
    return TestCase(
        test_id="B1-001",
        benchmark_type=BenchmarkType("B1_CCoP_Applicability_Scope"),
        section=CCoPSection("Cybersecurity Act 2018 Part 3"),
        clause_reference="Section 7(1)",
        difficulty=DifficultyLevel.MEDIUM,
        question="What are the criteria that the Commissioner uses to designate a computer or computer system as Critical Information Infrastructure (CII) under the Cybersecurity Act 2018?",
        expected_response="According to Section 7(1) of the Cybersecurity Act 2018, the Commissioner may designate a computer or computer system as CII if two criteria are satisfied: (a) the computer or computer system is necessary for the continuous delivery of an essential service, and the loss or compromise of the computer or computer system will have a debilitating effect on the availability of the essential service in Singapore; and (b) the computer or computer system is located wholly or partly in Singapore.",
        evaluation_criteria={
            "accuracy": "Must correctly identify both criteria",
            "completeness": "Should mention written notice requirement",
        },
        metadata={
            "domain": "IT/OT",
            "criticality": "critical",
        }
    )


@pytest.fixture
def sample_b2_test_case() -> TestCase:
    """Create a sample B2 test case with citation."""
    return TestCase(
        test_id="B2-001",
        benchmark_type=BenchmarkType("B2_Compliance_Classification_Accuracy"),
        section=CCoPSection("Section 3: Risk Management"),
        clause_reference="3.1.1",
        difficulty=DifficultyLevel.HIGH,
        question="Which section addresses cybersecurity risk management?",
        expected_response="Risk Management section addresses cybersecurity risk management",
        evaluation_criteria={
            "accuracy_threshold": 0.8,
            "requires_citation": True,
        },
        metadata={
            "domain": "IT/OT",
        }
    )


@pytest.fixture
def sample_b3_test_case() -> TestCase:
    """Create a sample B3 test case for hallucination detection."""
    return TestCase(
        test_id="B3-001",
        benchmark_type=BenchmarkType("B3_Conditional_Compliance_Reasoning"),
        section=CCoPSection("Section 6: Detection"),
        clause_reference="6.1.1",
        difficulty=DifficultyLevel.CRITICAL,
        question="What are the requirements for incident response?",
        expected_response="Organizations must establish incident response procedures",
        evaluation_criteria={
            "accuracy_threshold": 0.9,
        },
        metadata={
            "domain": "IT/OT",
        }
    )


@pytest.fixture
def sample_model_response() -> ModelResponse:
    """Create a sample model response."""
    return ModelResponse(
        content="The primary objective of CCoP 2.0 is to provide cybersecurity standards for Critical Information Infrastructure.",
        model_name="primus-reasoning",
        tokens_used=25,
        latency_ms=1500,
        metadata={
            "temperature": 0.7,
            "timestamp": datetime.now().isoformat(),
        }
    )


@pytest.fixture
def sample_evaluation_metrics() -> List[EvaluationMetric]:
    """Create sample evaluation metrics."""
    return [
        EvaluationMetric(
            name="accuracy",
            description="Answer correctness",
            value=0.95,
            weight=0.5,
        ),
        EvaluationMetric(
            name="completeness",
            description="Response completeness",
            value=0.85,
            weight=0.3,
        ),
        EvaluationMetric(
            name="relevance",
            description="Answer relevance",
            value=0.90,
            weight=0.2,
        ),
    ]
