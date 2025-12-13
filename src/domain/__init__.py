"""
Domain Layer

Pure business logic with no external dependencies.
Contains entities, value objects, domain services, and exceptions.
"""

from domain.entities.benchmark import Benchmark
from domain.entities.evaluation_result import EvaluationResult
from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.exceptions.evaluation_error import EvaluationError
from domain.exceptions.validation_error import ValidationError
from domain.services.benchmark_validator import BenchmarkValidator
from domain.services.scoring_service import ScoringService
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.ccop_section import CCoPSection
from domain.value_objects.difficulty_level import DifficultyLevel
from domain.value_objects.evaluation_metric import EvaluationMetric

__all__ = [
    # Entities
    "TestCase",
    "ModelResponse",
    "EvaluationResult",
    "Benchmark",
    # Value Objects
    "BenchmarkType",
    "DifficultyLevel",
    "CCoPSection",
    "EvaluationMetric",
    # Exceptions
    "ValidationError",
    "EvaluationError",
    # Services
    "ScoringService",
    "BenchmarkValidator",
]
