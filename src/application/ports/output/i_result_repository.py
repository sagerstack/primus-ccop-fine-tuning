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
    async def append_partial(
        self,
        result: EvaluationResult,
        run_metadata: Dict[str, Any],
    ) -> str:
        """
        Append a single completed test-case result to the per-run partial JSONL.

        Called once per test case as it completes, so that a crash mid-run
        preserves all completed results. The first call writes a header line
        with run-level metadata; subsequent calls append one JSON-encoded
        result per line. Each line is flushed and fsynced before returning.

        Args:
            result: Completed evaluation result for one test case.
            run_metadata: Run-level metadata used to derive the partial-file
                path AND to record the invocation's intent in the header.
                Required keys: run_id, model_name, evaluation_mode, judge_config.

        Returns:
            Path to the partial file the line was written to.

        Raises:
            RepositoryError: If write fails.
        """
        pass

    @abstractmethod
    async def load_partial(
        self,
        run_metadata: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Load completed test-case results from a prior run's partial JSONL.

        Used on `--resume` to skip already-completed cases. Matches by glob
        pattern on (mode, scope, model_name); when multiple partial files
        match, picks the most-recent by mtime. Validates the header's
        judge_config matches `run_metadata["judge_config"]`; bails out
        otherwise to prevent mixed-config result sets.

        Args:
            run_metadata: Current invocation's metadata. Must include the
                same keys as `append_partial`.

        Returns:
            None when no matching partial file exists. Otherwise a dict:
                {
                    "partial_path": str,
                    "header": {...original run metadata...},
                    "completed_test_ids": set[str],
                    "completed_results": list[EvaluationResult],
                }

        Raises:
            ValueError: If the partial file's header is incompatible with
                the current invocation (e.g., judge_config drift).
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
