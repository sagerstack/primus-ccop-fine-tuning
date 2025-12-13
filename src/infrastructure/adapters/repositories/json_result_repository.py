"""
JSON Result Repository

Saves evaluation results to JSON files.
"""

import json
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from application.ports.output.i_logger import ILogger
from application.ports.output.i_result_repository import IResultRepository
from domain.entities.evaluation_result import EvaluationResult


class JSONResultRepository(IResultRepository):
    """Repository for saving evaluation results to JSON."""

    def __init__(self, results_dir: Path, logger: ILogger) -> None:
        self._results_dir = Path(results_dir)
        self._results_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logger

    async def save(self, result: EvaluationResult) -> None:
        """Save single result."""
        await self.save_batch([result])

    async def save_batch(self, results: List[EvaluationResult]) -> None:
        """Save multiple results."""
        if not results:
            return

        # Group by model name
        by_model = {}
        for result in results:
            model = result.model_response.model_name
            if model not in by_model:
                by_model[model] = []
            by_model[model].append(result)

        # Save each model's results
        for model_name, model_results in by_model.items():
            filepath = self._results_dir / f"{model_name}_results.json"

            # Load existing if any
            existing = []
            if filepath.exists():
                with open(filepath, "r") as f:
                    existing = json.load(f)

            # Append new results
            for result in model_results:
                existing.append(self._serialize(result))

            # Save
            with open(filepath, "w") as f:
                json.dump(existing, f, indent=2, default=str)

    async def load_by_id(self, result_id: UUID) -> Optional[EvaluationResult]:
        """Load result by ID (not implemented - stub)."""
        return None

    async def load_by_test_id(self, test_id: str) -> List[EvaluationResult]:
        """Load results by test ID (not implemented - stub)."""
        return []

    async def load_by_model(self, model_name: str) -> List[EvaluationResult]:
        """Load results by model (not implemented - stub)."""
        return []

    async def load_all(self) -> List[EvaluationResult]:
        """Load all results (not implemented - stub)."""
        return []

    async def delete_by_id(self, result_id: UUID) -> bool:
        """Delete result (not implemented - stub)."""
        return False

    async def clear_all(self) -> int:
        """Clear all results (not implemented - stub)."""
        return 0

    def _serialize(self, result: EvaluationResult) -> dict:
        """Serialize result to dict."""
        return {
            "result_id": str(result.result_id),
            "test_id": result.test_case.test_id,
            "benchmark": result.test_case.benchmark_type.value,
            "model": result.model_response.model_name,
            "response": result.model_response.content,
            "score": result.overall_score,
            "passed": result.passed,
            "metrics": [
                {"name": m.name, "value": m.value, "weight": m.weight}
                for m in result.metrics
            ],
            "tokens": result.model_response.tokens_used,
            "latency_ms": result.model_response.latency_ms,
            "evaluated_at": result.evaluated_at.isoformat(),
        }
