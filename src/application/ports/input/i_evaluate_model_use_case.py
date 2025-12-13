"""
Evaluate Model Use Case Port (Interface)

Abstract interface for model evaluation use case.
"""

from abc import ABC, abstractmethod

from application.dtos.evaluation_request_dto import EvaluationRequestDTO
from application.dtos.evaluation_result_dto import EvaluationSummaryDTO


class IEvaluateModelUseCase(ABC):
    """
    Port (interface) for model evaluation use case.

    This is an input port (primary port) - defines what the application can do.
    """

    @abstractmethod
    async def execute(self, request: EvaluationRequestDTO) -> EvaluationSummaryDTO:
        """
        Execute model evaluation.

        Args:
            request: Evaluation request parameters

        Returns:
            Evaluation summary with results

        Raises:
            EvaluationError: If evaluation fails
        """
        pass
