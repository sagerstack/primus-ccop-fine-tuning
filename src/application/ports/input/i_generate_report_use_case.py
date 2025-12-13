"""
Generate Report Use Case Port (Interface)

Abstract interface for report generation use case.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional

from application.dtos.evaluation_result_dto import EvaluationSummaryDTO


class ReportFormat(str, Enum):
    """Supported report formats."""
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    CSV = "csv"


class IGenerateReportUseCase(ABC):
    """
    Port (interface) for report generation use case.

    Generates evaluation reports in various formats.
    """

    @abstractmethod
    async def execute(
        self,
        model_name: str,
        format: ReportFormat = ReportFormat.JSON,
        output_path: Optional[str] = None,
        include_details: bool = True,
    ) -> str:
        """
        Generate evaluation report.

        Args:
            model_name: Model to generate report for
            format: Report format
            output_path: Optional output file path
            include_details: Include individual test results

        Returns:
            Path to generated report (or report content if output_path is None)

        Raises:
            ReportError: If report generation fails
        """
        pass

    @abstractmethod
    async def get_summary(self, model_name: str) -> EvaluationSummaryDTO:
        """
        Get evaluation summary for a model.

        Args:
            model_name: Model name

        Returns:
            Evaluation summary

        Raises:
            ReportError: If summary generation fails
        """
        pass
