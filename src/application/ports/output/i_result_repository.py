"""
Result Repository Port (Interface)

Abstract interface for evaluation result persistence.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID

from domain.entities.evaluation_result import EvaluationResult


class IResultRepository(ABC):
    """
    Port (interface) for evaluation result storage operations.

    This is an output port defining how the application persists results.
    """

    @abstractmethod
    async def save(self, result: EvaluationResult) -> None:
        """
        Save an evaluation result.

        Args:
            result: Evaluation result to save

        Raises:
            RepositoryError: If saving fails
        """
        pass

    @abstractmethod
    async def save_batch(self, results: List[EvaluationResult]) -> None:
        """
        Save multiple evaluation results efficiently.

        Args:
            results: List of evaluation results

        Raises:
            RepositoryError: If saving fails
        """
        pass

    @abstractmethod
    async def save_evaluation_run(
        self,
        results: List[EvaluationResult],
        metadata: Dict[str, Any],
        contexts_by_test_id: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> str:
        """
        Save evaluation results for a complete run with metadata.

        Args:
            results: List of evaluation results
            metadata: Evaluation run metadata (model, phase, tier, benchmarks, scores, etc.)
            contexts_by_test_id: Optional mapping of test_id to list of retrieved context dicts.
                When provided, written as a sidecar {run_id}-contexts.json file.

        Returns:
            Filepath of saved results

        Raises:
            RepositoryError: If saving fails
        """
        pass

    @abstractmethod
    async def save_query_run(
        self,
        metadata: Dict[str, Any],
        test_results: List[Dict[str, Any]],
        contexts_by_test_id: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> str:
        """
        Save a single ad-hoc query result as a per-run JSON file.

        Args:
            metadata: Run metadata including run_id, model_name, evaluated_at, etc.
            test_results: List of result dicts (typically a single entry for query runs).
            contexts_by_test_id: Optional mapping of test_id to retrieved context dicts.
                Written as sidecar {run_id}-contexts.json when provided.

        Returns:
            Filepath of saved result

        Raises:
            RepositoryError: If saving fails
        """
        pass

    @abstractmethod
    async def load_by_id(self, result_id: UUID) -> Optional[EvaluationResult]:
        """
        Load a specific result by ID.

        Args:
            result_id: Result identifier

        Returns:
            Evaluation result if found, None otherwise

        Raises:
            RepositoryError: If loading fails
        """
        pass

    @abstractmethod
    async def load_by_test_id(self, test_id: str) -> List[EvaluationResult]:
        """
        Load all results for a specific test case.

        Args:
            test_id: Test case identifier

        Returns:
            List of evaluation results

        Raises:
            RepositoryError: If loading fails
        """
        pass

    @abstractmethod
    async def load_by_model(self, model_name: str) -> List[EvaluationResult]:
        """
        Load all results for a specific model.

        Args:
            model_name: Model name

        Returns:
            List of evaluation results

        Raises:
            RepositoryError: If loading fails
        """
        pass

    @abstractmethod
    async def load_all(self) -> List[EvaluationResult]:
        """
        Load all evaluation results.

        Returns:
            List of all results

        Raises:
            RepositoryError: If loading fails
        """
        pass

    @abstractmethod
    async def delete_by_id(self, result_id: UUID) -> bool:
        """
        Delete a specific result.

        Args:
            result_id: Result identifier

        Returns:
            True if deleted, False if not found

        Raises:
            RepositoryError: If operation fails
        """
        pass

    @abstractmethod
    async def clear_all(self) -> int:
        """
        Clear all evaluation results (use with caution).

        Returns:
            Number of results deleted

        Raises:
            RepositoryError: If operation fails
        """
        pass
