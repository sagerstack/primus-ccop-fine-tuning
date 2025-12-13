"""
Application Layer

Contains use cases, DTOs, and port definitions (interfaces).
Depends only on the domain layer.
"""

from application.dtos.evaluation_request_dto import EvaluationRequestDTO
from application.dtos.evaluation_result_dto import (
    EvaluationResultDTO,
    EvaluationSummaryDTO,
    MetricDTO,
)
from application.dtos.test_case_dto import TestCaseDTO
from application.use_cases.evaluate_model import EvaluateModelUseCase
from application.use_cases.generate_report import GenerateReportUseCase
from application.use_cases.setup_model import SetupModelUseCase

__all__ = [
    # DTOs
    "TestCaseDTO",
    "EvaluationRequestDTO",
    "EvaluationResultDTO",
    "EvaluationSummaryDTO",
    "MetricDTO",
    # Use Cases
    "EvaluateModelUseCase",
    "SetupModelUseCase",
    "GenerateReportUseCase",
]
