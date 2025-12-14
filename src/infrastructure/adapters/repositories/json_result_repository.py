"""
JSON Result Repository

Saves evaluation results to JSON files.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
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

    async def save_evaluation_run(
        self,
        results: List[EvaluationResult],
        metadata: Dict[str, any]
    ) -> str:
        """Save evaluation run with metadata in separate file."""
        if not results:
            return ""

        # Generate filename from parameters
        filename = self._generate_filename(metadata)
        filepath = self._results_dir / filename

        # Build output structure with metadata first, then results
        output = {
            "metadata": metadata,
            "test_results": [self._serialize_with_question(result) for result in results]
        }

        # Save to file
        with open(filepath, "w") as f:
            json.dump(output, f, indent=2, default=str)

        self._logger.info(f"Saved evaluation run to: {filepath}")
        return str(filepath)

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

    def _serialize_with_question(self, result: EvaluationResult) -> dict:
        """Serialize result with question included."""
        serialized = self._serialize(result)
        # Add question field
        serialized["question"] = result.test_case.question
        return serialized

    def _generate_filename(self, metadata: Dict[str, any]) -> str:
        """
        Generate filename from evaluation parameters.

        Format: result-{model}-[phase-{phase}]-[tier-{tier}]-[benchmark-{benchmark}]-{timestamp}.json
        Omit optional parts if not available.

        Args:
            metadata: Evaluation metadata containing parameters

        Returns:
            Generated filename
        """
        # Start with required parts
        parts = ["result", metadata.get("model_name", "unknown")]

        # Add optional parts if present
        if metadata.get("evaluation_phase"):
            parts.append(f"phase-{metadata['evaluation_phase']}")

        if metadata.get("tier"):
            parts.append(f"tier-{metadata['tier']}")

        if metadata.get("benchmarks"):
            # If single benchmark, add it; if multiple, add "multi"
            benchmarks = metadata["benchmarks"]
            if len(benchmarks) == 1:
                parts.append(f"benchmark-{benchmarks[0]}")
            elif len(benchmarks) > 1:
                parts.append(f"benchmarks-{len(benchmarks)}")

        # Add timestamp
        timestamp = metadata.get("evaluated_at")
        if timestamp:
            # Format: yyyymmdd-HHMM
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp
            timestamp_str = dt.strftime("%Y%m%d-%H%M")
        else:
            timestamp_str = datetime.utcnow().strftime("%Y%m%d-%H%M")
        parts.append(timestamp_str)

        # Join with dashes and add .json extension
        return "-".join(parts) + ".json"
