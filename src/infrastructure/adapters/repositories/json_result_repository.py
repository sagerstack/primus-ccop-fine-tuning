"""
JSON Result Repository

Saves evaluation results to JSON files.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from application.ports.output.i_logger import ILogger
from application.ports.output.i_result_repository import IResultRepository
from domain.entities.evaluation_result import EvaluationResult
from domain.value_objects.quality_group import QualityGroup


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
        """
        Deprecated no-op in schema v6.

        Per-run writes happen via save_evaluation_run. This method is retained
        to avoid breaking any callers that still reference it, but produces no
        file output.
        """
        self._logger.debug(
            "save_batch is a no-op in schema v6; per-run writes happen via save_evaluation_run"
        )

    async def save_evaluation_run(
        self,
        results: List[EvaluationResult],
        metadata: Dict[str, any],
        contexts_by_test_id: Optional[Dict[str, List[Dict[str, any]]]] = None,
    ) -> str:
        """
        Save evaluation run results as per-run file under monthly subdirectory.

        Writes:
          - {run_id}-{model}.json  — main result file
          - {run_id}-contexts.json — sidecar (only when contexts_by_test_id is provided)

        Both files land under src/results/evaluations/{yyyy-MM}/.
        """
        if not results:
            return ""

        month_dir = self._monthly_dir(metadata.get("evaluated_at", ""))
        filename = self._generate_filename_v6(metadata)
        filepath = month_dir / filename

        enriched_metadata = self._enrich_quality_categories_metadata(metadata)
        output = {
            "metadata": enriched_metadata,
            "test_results": [self._serialize_with_question(result) for result in results],
        }

        with open(filepath, "w") as f:
            json.dump(output, f, indent=2, default=str)
        self._logger.info(f"Saved evaluation run to: {filepath}")

        if contexts_by_test_id:
            run_id = metadata["run_id"]
            sidecar_path = month_dir / f"{run_id}-contexts.json"
            with open(sidecar_path, "w") as f:
                json.dump(contexts_by_test_id, f, indent=2, default=str)
            self._logger.info(f"Saved retrieved contexts sidecar to: {sidecar_path}")

        return str(filepath)

    async def save_query_run(
        self,
        metadata: Dict[str, any],
        test_results: List[Dict[str, any]],
        contexts_by_test_id: Optional[Dict[str, List[Dict[str, any]]]] = None,
    ) -> str:
        """
        Save a single ad-hoc query result as a per-run JSON file.

        Writes:
          - {run_id}-{model}.json  — main result file
          - {run_id}-contexts.json — sidecar (only when contexts_by_test_id is provided)

        Both files land under src/results/evaluations/{yyyy-MM}/.
        """
        month_dir = self._monthly_dir(metadata.get("evaluated_at", ""))
        filename = self._generate_filename_v6(metadata)
        filepath = month_dir / filename
        output = {"metadata": metadata, "test_results": test_results}

        with open(filepath, "w") as f:
            json.dump(output, f, indent=2, default=str)
        self._logger.info(f"Saved query run to: {filepath}")

        if contexts_by_test_id:
            run_id = metadata["run_id"]
            sidecar_path = month_dir / f"{run_id}-contexts.json"
            with open(sidecar_path, "w") as f:
                json.dump(contexts_by_test_id, f, indent=2, default=str)
            self._logger.info(f"Saved query contexts sidecar to: {sidecar_path}")

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

    def _generate_filename_v6(self, metadata: Dict[str, any]) -> str:
        """
        Generate schema-v6 filename from run_id.

        Format: {run_id}-{model_name}.json

        Args:
            metadata: Evaluation metadata containing run_id and model_name.

        Returns:
            Generated filename.

        Raises:
            ValueError: If metadata.run_id is missing (required for schema v6).
        """
        run_id = metadata.get("run_id")
        model_name = metadata.get("model_name", "unknown")
        if not run_id:
            raise ValueError("metadata.run_id is required for schema v6")
        return f"{run_id}-{model_name}.json"

    def _generate_filename_legacy(self, metadata: Dict[str, any]) -> str:
        """
        Legacy filename generator (pre-v6). Retained for reference; not called on hot path.

        Format: result-{model}-[phase-{phase}]-[mode-{mode}]-...-{timestamp}.json
        """
        return self._generate_filename(metadata)

    def _monthly_dir(self, timestamp_iso: str) -> Path:
        """
        Return (and create) the monthly subdirectory for the given ISO timestamp.

        Args:
            timestamp_iso: ISO-formatted datetime string (e.g. "2026-04-21T14:30:00").
                Falls back to utcnow() if empty or unparseable.

        Returns:
            Path to the yyyy-MM directory under self._results_dir.
        """
        try:
            if timestamp_iso:
                dt = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
            else:
                dt = datetime.utcnow()
        except (ValueError, AttributeError):
            dt = datetime.utcnow()

        month_dir = self._results_dir / dt.strftime("%Y-%m")
        month_dir.mkdir(parents=True, exist_ok=True)
        return month_dir

    def _serialize(self, result: EvaluationResult) -> dict:
        """Serialize result to dict."""
        # Get RAGAs composite score from domain entity (multiplicative penalty formula)
        ragas_score = result.ragas_composite_score

        serialized = {
            "result_id": str(result.result_id),
            "test_id": result.test_case.test_id,
            "benchmark": result.test_case.benchmark_type.value,
            "model": result.model_response.model_name,
            "response": result.model_response.content,
            "score": result.overall_score,
            "ragas_score": ragas_score,
            "passed": result.passed,
            "metrics": [
                {"name": m.name, "value": m.value, "weight": m.weight}
                for m in result.metrics
            ],
            "tokens": result.model_response.tokens_used,
            "latency_ms": result.model_response.latency_ms,
            "evaluated_at": result.evaluated_at.isoformat(),
        }

        # Add RAGAs section if evaluation was performed
        ragas_eval = result.ragas_evaluation
        if ragas_eval is not None:
            if ragas_eval.evaluation_error:
                serialized["ragas"] = {
                    "schema_version": 5,
                    "error": True,
                    "error_message": ragas_eval.error_message,
                }
            else:
                # Build grouped structure
                serialized["ragas"] = self._build_grouped_ragas_structure(ragas_eval)

        # I/O capture fields (schema v6 — traceability)
        serialized["system_prompt"] = result.system_prompt
        serialized["user_prompt"] = result.user_prompt
        serialized["prompt_tokens"] = result.model_response.prompt_tokens
        serialized["completion_tokens"] = result.model_response.completion_tokens
        serialized["total_tokens"] = result.model_response.total_tokens

        # RAG evaluation metadata
        if result.evaluation_mode is not None:
            serialized["evaluation_mode"] = result.evaluation_mode
        if result.retrieved_chunk_ids is not None:
            serialized["retrieved_chunk_ids"] = result.retrieved_chunk_ids
            serialized["chunk_count"] = result.chunk_count or 0

        # Judge evaluation metadata (schema v5)
        # Detect judge mode from metrics
        judge_mode = None
        for metric in result.metrics:
            if metric.name == "universal_judge":
                judge_mode = "universal"
                # Parse judge metadata from description
                try:
                    import json as json_module
                    judge_data = json_module.loads(metric.description)
                    serialized["judge_mode"] = "universal"
                    serialized["judge_evaluation"] = {
                        "hallucination_detected": judge_data.get("hallucination_detected"),
                        "unsupported_count": judge_data.get("unsupported_count"),
                        "contradicted_count": judge_data.get("contradicted_count"),
                        "reasoning_depth_score": round(metric.value * 3),  # Denormalize to 0-3 scale
                        "reasoning_criteria_met": judge_data.get("reasoning_criteria_met"),
                        "claims": judge_data.get("claims"),
                        "justification": judge_data.get("justification"),
                    }
                except (json_module.JSONDecodeError, AttributeError):
                    pass
                break
            elif metric.name in ["accuracy", "completeness", "alignment"]:
                judge_mode = "rubric"
                break

        if judge_mode == "rubric":
            serialized["judge_mode"] = "rubric"

        return serialized

    def _serialize_with_question(self, result: EvaluationResult) -> dict:
        """Serialize result with question included."""
        serialized = self._serialize(result)
        # Add question field
        serialized["question"] = result.test_case.question
        return serialized

    def _build_grouped_ragas_structure(self, ragas_eval) -> dict:
        """
        Build grouped ragas structure from flat metrics.

        Converts flat metrics array into 3 diagnostic groups:
        - retrieval_quality: context_recall, context_precision
        - grounding: context_faithfulness
        - response_quality: factual_precision, factual_recall, answer_relevancy, semantic_similarity

        Note: schema_version 3 files use "answer_correctness" and "hallucination" instead of
        factual_precision/factual_recall/semantic_similarity. Version 2 uses "faithfulness"
        instead of "context_faithfulness".

        Args:
            ragas_eval: RagasEvaluation object

        Returns:
            Grouped structure with schema_version 4
        """
        # Build group definitions
        group_definitions = {}
        for group in QualityGroup.get_all_groups():
            # Map group name to JSON key
            if group.name == "Retrieval Quality":
                key = "retrieval_quality"
            elif group.name == "Model-RAG Grounding":
                key = "grounding"
            elif group.name == "Model Response Quality":
                key = "response_quality"
            else:
                continue

            # Filter to only RAGAs metrics (exclude llm_judge)
            ragas_metrics = [m for m in group.metrics if m != "llm_judge"]

            group_definitions[key] = {
                "display_name": group.name,
                "metrics": ragas_metrics,
            }

        # Add note for response_quality about llm_judge
        group_definitions["response_quality"]["note"] = (
            "llm_judge is part of this logical group but stored in the separate "
            "'metrics' array (benchmark scoring layer, not RAGAs)"
        )

        # Build metrics by group
        retrieval_quality = {}
        grounding = {}
        response_quality = {}

        for metric in ragas_eval.metrics:
            metric_data = {
                "score": metric.score,
                "applicable": metric.applicable,
            }

            if metric.name in ["context_recall", "context_precision"]:
                retrieval_quality[metric.name] = metric_data
            elif metric.name == "context_faithfulness":
                grounding[metric.name] = metric_data
            elif metric.name in ["factual_recall", "answer_relevancy", "semantic_similarity"]:
                response_quality[metric.name] = metric_data

        return {
            "schema_version": 5,
            "error": False,
            "is_rag_response": ragas_eval.is_rag_response,
            "group_definitions": group_definitions,
            "retrieval_quality": retrieval_quality,
            "grounding": grounding,
            "response_quality": response_quality,
            "schema_notes": "v5: factual_precision removed, judge_evaluation added. v4: factual_precision/recall/semantic_similarity replace answer_correctness/hallucination. v3: context_faithfulness, hallucination added. v2: grouped structure."
        }

    def _enrich_quality_categories_metadata(self, metadata: Dict[str, any]) -> Dict[str, any]:
        """
        Enrich metadata with group definitions in quality_categories.

        Adds group_definitions to quality_categories if quality_categories exists.
        This makes the JSON self-describing about which metrics belong to which groups.

        Args:
            metadata: Original metadata dict

        Returns:
            Enriched metadata dict (new copy, original unchanged)
        """
        enriched = metadata.copy()

        # Only enrich if quality_categories exists
        if "quality_categories" not in enriched:
            return enriched

        # Build group definitions
        group_definitions = {}
        for group in QualityGroup.get_all_groups():
            # Map group name to JSON key
            if group.name == "Retrieval Quality":
                key = "retrieval_quality"
            elif group.name == "Model-RAG Grounding":
                key = "grounding"
            elif group.name == "Model Response Quality":
                key = "response_quality"
            else:
                continue

            # Filter to only RAGAs metrics (exclude llm_judge which is in metrics array)
            ragas_metrics = [m for m in group.metrics if m != "llm_judge"]

            group_definitions[key] = {
                "display_name": group.name,
                "metrics": ragas_metrics,
            }

        # Add note for response_quality
        group_definitions["response_quality"]["note"] = (
            "llm_judge is part of this logical group but stored in the separate "
            "'metrics' array (benchmark scoring layer, not RAGAs)"
        )

        # Add group_definitions to quality_categories
        enriched["quality_categories"]["group_definitions"] = group_definitions

        return enriched

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

        if metadata.get("evaluation_mode"):
            parts.append(f"mode-{metadata['evaluation_mode']}")

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
