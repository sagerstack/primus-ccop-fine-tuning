"""
Rescore Evaluation Use Case

Re-runs the LLM judge on frozen Primus responses from a prior evaluation
run. Skips Primus inference + RAG retrieval entirely — those artifacts are
loaded from the source run's persisted output. Saves ~24 hours of compute
per cycle of full 435-case re-measurement (vs running fresh evaluations
after every judge / rubric / GT change).

Workflow:
  1. Locate source run's consolidated JSON file by run_id (glob across
     monthly subdirs).
  2. Load source results + retrieved-contexts sidecar (for hybrid runs).
  3. For each entry:
       a. Load fresh TestCase from test-suite JSONL — picks up any GT
          enrichments applied since the source run.
       b. Reconstruct ModelResponse from the frozen response bytes.
       c. Score via ScoringService (now uniformly through the LLM judge).
       d. Append to per-case partial JSONL for crash recovery.
  4. Save consolidated output with metadata.source_run_id linking back to
     the source run for provenance.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from application.dtos.evaluation_result_dto import EvaluationSummaryDTO
from application.ports.output.i_logger import ILogger
from application.ports.output.i_result_repository import IResultRepository
from application.ports.output.i_test_case_repository import ITestCaseRepository
from domain.entities.evaluation_result import EvaluationResult
from domain.entities.model_response import ModelResponse
from domain.entities.test_case import TestCase
from domain.services.scoring_service import ScoringService


class RescoreEvaluationUseCase:
    """Re-judge a prior run's frozen Primus responses with the current scoring config."""

    def __init__(
        self,
        test_case_repository: ITestCaseRepository,
        result_repository: IResultRepository,
        results_dir: Path,
        logger: ILogger,
    ) -> None:
        self._test_case_repository = test_case_repository
        self._result_repository = result_repository
        self._results_dir = Path(results_dir)
        self._logger = logger

    async def execute(
        self,
        source_run_id: str,
        judge_mode: str = "rubric",
        save_results: bool = True,
        resume: bool = False,
    ) -> EvaluationSummaryDTO:
        """
        Rescore a prior evaluation run's frozen responses.

        Args:
            source_run_id: Run identifier of the source run (without the
                model suffix), e.g. "eval-run-llm-only-tests-30-abc12345-20260425-0458".
            judge_mode: "rubric" (universal 5-dim) or "universal" (hallucination
                + reasoning depth). Both now route through the LLM judge.
            save_results: Persist the rescored consolidated output.
            resume: When True, skip already-completed cases via the partial JSONL.

        Returns:
            EvaluationSummaryDTO of the rescored run.

        Raises:
            FileNotFoundError: If no source result file matches source_run_id.
            ValueError: If multiple source files match (ambiguous) or the
                source file is malformed.
        """
        start_time = datetime.utcnow()
        source_path = self._find_source_file(source_run_id)
        contexts_path = self._find_contexts_sidecar(source_run_id)

        with open(source_path) as f:
            source_data = json.load(f)
        source_metadata = source_data.get("metadata", {})
        source_results = source_data.get("test_results", [])
        if not source_results:
            raise ValueError(f"Source run has no test_results: {source_path}")

        contexts_by_test_id: Dict[str, List[Any]] = {}
        if contexts_path is not None and contexts_path.exists():
            with open(contexts_path) as f:
                contexts_by_test_id = json.load(f)

        self._logger.info(
            f"Rescoring source run {source_run_id}: "
            f"{len(source_results)} cases, mode={source_metadata.get('evaluation_mode')}"
        )

        # Build a NEW run_id for the rescored output (timestamp-different from source)
        new_run_id = self._build_rescore_run_id(source_run_id, start_time)
        model_name = source_metadata.get("model_name", "unknown")
        evaluation_mode = source_metadata.get("evaluation_mode")

        # Build partial-write metadata prelude
        partial_metadata = {
            "run_id": new_run_id,
            "schema_version": 6,
            "model_name": model_name,
            "evaluation_mode": evaluation_mode,
            "scope": self._extract_scope_from_run_id(source_run_id, evaluation_mode),
            "judge_config": {
                "judge_mode": judge_mode,
                "evaluation_mode": evaluation_mode,
                "rescore_source": source_run_id,
            },
            "evaluated_at": start_time.isoformat(),
        }

        # Load existing partial results on resume
        results: List[EvaluationResult] = []
        completed_test_ids: set = set()
        if resume and save_results:
            partial = await self._result_repository.load_partial(partial_metadata)
            if partial is not None:
                completed_test_ids = partial["completed_test_ids"]
                results.extend(partial["completed_results"])
                self._logger.info(
                    f"Resuming rescore: skipping {len(completed_test_ids)} completed cases"
                )

        # Load all source test_ids in one batch
        source_test_ids = [entry["test_id"] for entry in source_results]
        full_test_cases = await self._test_case_repository.load_by_ids(source_test_ids)
        test_case_index = {tc.test_id: tc for tc in full_test_cases}

        # Re-score each case
        for i, entry in enumerate(source_results, 1):
            test_id = entry.get("test_id")
            if not test_id:
                self._logger.warning(f"Skipping source entry without test_id: {entry}")
                continue
            if test_id in completed_test_ids:
                self._logger.info(
                    f"Skipping already-rescored case {i}/{len(source_results)}: {test_id}"
                )
                continue

            test_case = test_case_index.get(test_id)
            if test_case is None:
                self._logger.warning(
                    f"Test case {test_id} from source run not found in current "
                    f"test-suite — may have been deprecated. Skipping."
                )
                continue

            self._logger.info(
                f"Rescoring case {i}/{len(source_results)}: {test_id}"
            )

            model_response = self._reconstruct_model_response(entry)
            retrieved_contexts = self._extract_retrieved_contexts(
                contexts_by_test_id.get(test_id)
            )

            try:
                metrics = ScoringService.score_response(
                    test_case,
                    model_response,
                    judge_mode=judge_mode,
                    retrieved_contexts=retrieved_contexts,
                )
            except Exception as exc:  # noqa: BLE001
                self._logger.error(
                    f"Rescore failed for {test_id}: {exc}. Marking judge_error."
                )
                from domain.value_objects.evaluation_metric import EvaluationMetric
                metrics = [
                    EvaluationMetric(name="judge_error", value=0.0, weight=1.0)
                ]

            result = EvaluationResult(
                test_case=test_case,
                model_response=model_response,
                metrics=metrics,
                evaluation_mode=evaluation_mode,
                evaluated_at=datetime.utcnow(),
                system_prompt=entry.get("system_prompt", ""),
                user_prompt=entry.get("user_prompt", ""),
            )
            # Compute composite score + pass/fail using the source run's
            # phase-specific threshold (preserves the same pass-bar as the
            # original run for comparability).
            threshold = self._derive_threshold(source_metadata)
            result.finalize(threshold=threshold)
            results.append(result)

            if save_results:
                try:
                    await self._result_repository.append_partial(result, partial_metadata)
                except Exception as exc:  # noqa: BLE001
                    self._logger.warning(
                        f"Failed to append partial rescore result for {test_id}: {exc}"
                    )

        # Build summary + save consolidated
        end_time = datetime.utcnow()
        summary = self._build_summary(model_name, results, start_time, end_time)

        if save_results:
            metadata = self._build_consolidated_metadata(
                source_run_id=source_run_id,
                source_metadata=source_metadata,
                new_run_id=new_run_id,
                evaluation_mode=evaluation_mode,
                model_name=model_name,
                judge_mode=judge_mode,
                summary=summary,
                start_time=start_time,
                end_time=end_time,
            )
            filepath = await self._result_repository.save_evaluation_run(
                results, metadata, contexts_by_test_id=contexts_by_test_id or None
            )
            self._logger.info(f"Saved rescored run to {filepath}")

        return summary

    def _derive_threshold(self, source_metadata: Dict[str, Any]) -> Optional[float]:
        """Pull the source run's pass threshold so rescored pass/fail uses the same bar.

        Falls back to phase-specific default when the source has no explicit
        threshold; falls back to baseline (0.15) when phase is also missing.
        """
        explicit = source_metadata.get("pass_threshold")
        if explicit is not None:
            try:
                return float(explicit)
            except (TypeError, ValueError):
                pass
        phase = source_metadata.get("evaluation_phase", "baseline")
        return {"baseline": 0.15, "finetuned": 0.50, "deployment": 0.85}.get(phase, 0.15)

    def _find_source_file(self, source_run_id: str) -> Path:
        """Glob across monthly subdirs for the source run's consolidated JSON."""
        # Pattern: {run_id}-{model}.json (excluding -contexts.json sidecars)
        candidates = [
            p for p in self._results_dir.rglob(f"{source_run_id}-*.json")
            if not p.name.endswith("-contexts.json")
            and not p.name.endswith(".partial.jsonl")
        ]
        if not candidates:
            raise FileNotFoundError(
                f"No source result file found for run_id={source_run_id} "
                f"under {self._results_dir}"
            )
        if len(candidates) > 1:
            names = [p.name for p in candidates]
            raise ValueError(
                f"Ambiguous source run_id — multiple files match: {names}. "
                f"Specify a more precise run_id."
            )
        return candidates[0]

    def _find_contexts_sidecar(self, source_run_id: str) -> Optional[Path]:
        """Locate the retrieved-contexts sidecar if present (hybrid runs)."""
        candidates = list(
            self._results_dir.rglob(f"{source_run_id}-contexts.json")
        )
        if not candidates:
            return None
        return candidates[0]

    def _build_rescore_run_id(self, source_run_id: str, now: datetime) -> str:
        """Construct the new run_id for the rescored output.

        Replaces the source run_id's timestamp suffix with the current one.
        Format: eval-run-{mode}-{scope}-{yyyyMMdd}-{HHmm}
        """
        # Source run_id format: eval-run-{mode}-{scope}-{yyyyMMdd}-{HHmm}
        # Replace last two dash-segments (date + time) with current values
        parts = source_run_id.rsplit("-", 2)
        if len(parts) == 3:
            base, _date, _time = parts
            return f"{base}-{now.strftime('%Y%m%d-%H%M')}"
        # Fallback if format unexpected — append current timestamp
        return f"{source_run_id}-rescored-{now.strftime('%Y%m%d-%H%M')}"

    def _extract_scope_from_run_id(
        self, run_id: str, mode: Optional[str]
    ) -> str:
        """Pull the scope segment out of an eval-run-{mode}-{scope}-{ts} run_id."""
        prefix = f"eval-run-{mode}-" if mode else "eval-run-"
        if run_id.startswith(prefix):
            tail = run_id[len(prefix):]
            # Strip the trailing -yyyyMMdd-HHmm
            parts = tail.rsplit("-", 2)
            if len(parts) == 3:
                return parts[0]
        return "unknown"

    def _reconstruct_model_response(self, entry: Dict[str, Any]) -> ModelResponse:
        """Reconstruct a ModelResponse from a persisted source-run entry."""
        return ModelResponse(
            content=entry.get("response", ""),
            model_name=entry.get("model", "unknown"),
            tokens_used=entry.get("tokens", 0),
            latency_ms=entry.get("latency_ms", 0),
            prompt_tokens=entry.get("prompt_tokens", 0),
            completion_tokens=entry.get("completion_tokens", 0),
            total_tokens=entry.get("total_tokens", 0),
        )

    def _extract_retrieved_contexts(
        self, sidecar_entry: Optional[Any]
    ) -> Optional[List[str]]:
        """Pull retrieved contexts (list of strings) out of the sidecar entry.

        The sidecar stores either a list of dicts (full chunk metadata) or a
        list of strings. Normalises to list[str] for the judge.
        """
        if not sidecar_entry:
            return None
        if isinstance(sidecar_entry, list):
            if not sidecar_entry:
                return None
            if isinstance(sidecar_entry[0], dict):
                return [
                    str(c.get("text") or c.get("content") or "")
                    for c in sidecar_entry
                ]
            return [str(c) for c in sidecar_entry]
        return None

    def _build_summary(
        self,
        model_name: str,
        results: List[EvaluationResult],
        start_time: datetime,
        end_time: datetime,
    ) -> EvaluationSummaryDTO:
        """Build a minimal EvaluationSummaryDTO from rescored results.

        Reuses the same structure as EvaluateModelUseCase._generate_summary
        but doesn't compute category-weighted scores — those flow from the
        consolidated metadata builder. Provides headline pass/fail and overall
        averages so the CLI can report progress on completion.
        """
        # EvaluationSummaryDTO is dataclass-shaped; import here to avoid cycle.
        from application.dtos.evaluation_result_dto import EvaluationResultDTO

        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        scores = [r.overall_score for r in results if r.overall_score is not None]
        overall = sum(scores) / len(scores) if scores else 0.0
        duration = (end_time - start_time).total_seconds()

        result_dtos = [self._result_to_dto(r) for r in results]

        return EvaluationSummaryDTO(
            model_name=model_name,
            total_tests=len(results),
            passed_tests=passed,
            failed_tests=failed,
            overall_score=overall,
            ragas_overall_score=None,
            results=result_dtos,
            by_benchmark={},
            by_difficulty={},
            quality_categories=None,
            total_duration_seconds=duration,
        )

    def _result_to_dto(self, result: EvaluationResult) -> Any:
        """Lightweight result-to-DTO conversion (mirrors EvaluateModelUseCase)."""
        from application.dtos.evaluation_result_dto import EvaluationResultDTO
        return EvaluationResultDTO(
            test_id=result.test_case.test_id,
            benchmark=result.test_case.benchmark_type.value,
            score=result.overall_score or 0.0,
            passed=result.passed if result.passed is not None else False,
            metrics={m.name: m.value for m in result.metrics},
        )

    def _build_consolidated_metadata(
        self,
        source_run_id: str,
        source_metadata: Dict[str, Any],
        new_run_id: str,
        evaluation_mode: Optional[str],
        model_name: str,
        judge_mode: str,
        summary: EvaluationSummaryDTO,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """Build consolidated metadata for the rescored output file."""
        return {
            "run_id": new_run_id,
            "schema_version": 6,
            "model_name": model_name,
            "evaluation_phase": source_metadata.get("evaluation_phase", "baseline"),
            "evaluation_mode": evaluation_mode,
            "judge_config": {
                "judge_mode": judge_mode,
                "evaluation_mode": evaluation_mode,
            },
            "rescore": {
                "source_run_id": source_run_id,
                "source_evaluated_at": source_metadata.get("evaluated_at"),
                "rescored_at": start_time.isoformat(),
            },
            "benchmarks": source_metadata.get("benchmarks", []),
            "total_tests": summary.total_tests,
            "passed_tests": summary.passed_tests,
            "failed_tests": summary.failed_tests,
            "overall_score": summary.overall_score,
            "evaluated_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "duration_seconds": summary.total_duration_seconds,
        }
