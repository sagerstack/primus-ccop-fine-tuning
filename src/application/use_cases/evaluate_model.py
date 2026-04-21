"""
Evaluate Model Use Case

Orchestrates model evaluation across test cases.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from rag.application.ports.i_rag_pipeline import IRagPipeline

from application.dtos.evaluation_request_dto import EvaluationRequestDTO
from application.dtos.evaluation_result_dto import (
    EvaluationResultDTO,
    EvaluationSummaryDTO,
    MetricDTO,
    RagasMetricDTO,
)
from application.ports.input.i_evaluate_model_use_case import IEvaluateModelUseCase
from application.ports.output.i_logger import ILogger
from application.ports.output.i_model_gateway import IModelGateway
from application.ports.output.i_result_repository import IResultRepository
from application.ports.output.i_test_case_repository import ITestCaseRepository
from domain.entities.evaluation_result import EvaluationResult
from domain.entities.test_case import TestCase
from domain.services.scoring_service import ScoringService
from domain.value_objects.benchmark_type import BenchmarkType
from domain.value_objects.evaluation_category import EvaluationCategory
from domain.value_objects.quality_group import QualityGroup


class EvaluateModelUseCase(IEvaluateModelUseCase):
    """
    Use case for evaluating a model on CCoP 2.0 test cases.

    Orchestrates:
    1. Loading test cases
    2. Generating model responses
    3. Scoring responses
    4. Saving results
    """

    def __init__(
        self,
        model_gateway: IModelGateway,
        test_case_repository: ITestCaseRepository,
        result_repository: IResultRepository,
        logger: ILogger,
        ragas_service=None,
        rag_pipeline: Optional["IRagPipeline"] = None,
    ) -> None:
        self._model_gateway = model_gateway
        self._test_case_repository = test_case_repository
        self._result_repository = result_repository
        self._logger = logger
        self._ragas_service = ragas_service
        self._rag_pipeline = rag_pipeline

    async def execute(self, request: EvaluationRequestDTO) -> EvaluationSummaryDTO:
        """Execute model evaluation."""
        start_time = datetime.utcnow()
        self._logger.info(
            f"Starting evaluation for model: {request.model_name}",
            benchmarks=request.benchmark_types
        )

        # Load test cases
        test_cases = await self._load_test_cases(request)
        self._logger.info(f"Loaded {len(test_cases)} test cases")

        # Verify model is available
        is_available = await self._model_gateway.is_model_available(request.model_name)
        if not is_available:
            raise ValueError(f"Model '{request.model_name}' is not available")

        # Evaluate each test case
        results: List[EvaluationResult] = []
        for i, test_case in enumerate(test_cases, 1):
            self._logger.info(
                f"Evaluating test case {i}/{len(test_cases)}: {test_case.test_id}"
            )
            result = await self._evaluate_test_case(test_case, request)
            results.append(result)

        # Generate summary
        end_time = datetime.utcnow()
        summary = self._generate_summary(
            request.model_name,
            results,
            start_time,
            end_time
        )

        # Save results if requested (with metadata)
        if request.save_results:
            metadata = self._build_evaluation_metadata(request, summary, start_time, end_time)
            contexts_by_test_id = {
                r.test_case.test_id: r.retrieved_contexts_detailed
                for r in results
                if r.retrieved_contexts_detailed
            }
            filepath = await self._result_repository.save_evaluation_run(
                results, metadata, contexts_by_test_id=contexts_by_test_id or None
            )
            self._logger.info(f"Saved {len(results)} results to {filepath}")

        self._logger.info(
            f"Evaluation complete. Overall score: {summary.overall_score:.2%}",
            passed=summary.passed_tests,
            failed=summary.failed_tests
        )

        return summary

    async def _load_test_cases(
        self,
        request: EvaluationRequestDTO
    ) -> List[TestCase]:
        """Load test cases based on request parameters."""
        if request.test_case_ids:
            # Load specific test cases
            return await self._test_case_repository.load_by_ids(request.test_case_ids)
        else:
            # Load by benchmarks
            test_cases = []
            for benchmark_str in request.benchmark_types:
                benchmark_type = BenchmarkType.from_string(benchmark_str)
                cases = await self._test_case_repository.load_by_benchmark(benchmark_type)
                test_cases.extend(cases)
            return test_cases

    def _get_threshold(self, request: EvaluationRequestDTO) -> Optional[float]:
        """
        Get the pass threshold based on evaluation phase and request override.

        Phase 2: Returns threshold in priority order:
        1. Explicit threshold from request.pass_threshold
        2. Phase-specific threshold based on request.evaluation_phase
        3. None (use test case default)

        Args:
            request: Evaluation request

        Returns:
            Pass threshold (0.0-1.0) or None
        """
        # Priority 1: Explicit override from CLI/request
        if request.pass_threshold is not None:
            return request.pass_threshold

        # Priority 2: Phase-specific thresholds
        phase_thresholds = {
            "baseline": 0.15,
            "finetuned": 0.50,
            "deployment": 0.85,
        }

        return phase_thresholds.get(request.evaluation_phase, None)

    async def _evaluate_test_case(
        self,
        test_case: TestCase,
        request: EvaluationRequestDTO
    ) -> EvaluationResult:
        """Evaluate a single test case."""
        # Determine max tokens
        max_tokens = request.max_tokens or test_case.get_max_tokens_for_response()

        # Route through RAG pipeline if available, otherwise use direct model gateway
        retrieved_chunk_ids = None
        chunk_count = None
        retrieved_contexts = None
        system_prompt_captured = ""
        user_prompt_captured = ""
        retrieved_contexts_detailed_captured = None

        if self._rag_pipeline is not None and request.evaluation_mode:
            # RAG pipeline path
            mode = request.evaluation_mode

            # Check RAG pipeline availability for requested mode
            is_rag_available = await self._rag_pipeline.is_available(mode)
            if mode == "hybrid" and not is_rag_available:
                raise ValueError(
                    f"RAG pipeline not available for hybrid mode. "
                    f"Ensure Qdrant is running and configured. "
                    f"Use --mode llm-only to evaluate without RAG."
                )

            # Query RAG pipeline
            rag_response = await self._rag_pipeline.query(
                question=test_case.question,
                mode=mode,
            )

            # Build ModelResponse from RagResponse with full token/latency tracking
            from domain.entities.model_response import ModelResponse
            model_response = ModelResponse(
                content=rag_response.response,
                model_name=request.model_name,
                tokens_used=rag_response.total_tokens,  # back-compat display
                prompt_tokens=rag_response.prompt_tokens,
                completion_tokens=rag_response.completion_tokens,
                total_tokens=rag_response.total_tokens,
                latency_ms=rag_response.latency_ms,
                temperature=request.temperature,
            )

            # Capture full I/O for traceability
            system_prompt_captured = rag_response.system_prompt
            user_prompt_captured = rag_response.user_prompt
            retrieved_contexts_detailed_captured = rag_response.retrieved_contexts_detailed or None

            # Extract retrieved chunk IDs from citations
            if rag_response.citations:
                retrieved_chunk_ids = []
                for citation in rag_response.citations:
                    chunk_id = f"{citation.get('document', 'Unknown')}::{citation.get('clause', citation.get('section', 'N/A'))}"
                    retrieved_chunk_ids.append(chunk_id)
                chunk_count = len(retrieved_chunk_ids)

            # Extract retrieved contexts for RAGAs
            if rag_response.is_rag_augmented:
                retrieved_contexts = rag_response.retrieved_contexts

        else:
            # Direct model gateway path (backward compatibility)
            _direct_system_prompt = "You are a cybersecurity compliance expert specializing in Singapore's CCoP 2.0."
            model_response = await self._model_gateway.generate_response(
                prompt=test_case.question,
                model_name=request.model_name,
                temperature=request.temperature,
                max_tokens=max_tokens,
                top_p=request.top_p,
                top_k=request.top_k,
                system_prompt=_direct_system_prompt,
            )

            # Capture I/O for direct path
            system_prompt_captured = _direct_system_prompt
            user_prompt_captured = test_case.question
            retrieved_contexts_detailed_captured = None

        # Shadow retrieval: retrieve contexts for universal judge (not passed to model)
        if (
            getattr(request, 'judge_mode', 'rubric') == "universal"
            and request.evaluation_mode == "llm-only"
            and self._rag_pipeline is not None
            and retrieved_contexts is None
        ):
            try:
                shadow_response = await self._rag_pipeline.query(
                    question=test_case.question, mode="hybrid"
                )
                if shadow_response.is_rag_augmented:
                    retrieved_contexts = shadow_response.retrieved_contexts
                    self._logger.info(
                        f"Shadow retrieval for universal judge: "
                        f"{len(retrieved_contexts)} contexts retrieved"
                    )
            except Exception as e:
                self._logger.warning(
                    f"Shadow retrieval failed for {test_case.test_id}: {e}"
                )
                # retrieved_contexts stays None — judge skips hallucination check

        # Score response (Layer 1: Benchmark scoring)
        metrics = ScoringService.score_response(
            test_case,
            model_response,
            judge_mode=getattr(request, 'judge_mode', 'rubric'),
            retrieved_contexts=retrieved_contexts,
        )

        # Evaluate with RAGAs (Layer 2: Quality metrics)
        ragas_evaluation = None
        if self._ragas_service is not None:
            try:
                reference = test_case.expected_response or ""
                key_facts = test_case.key_facts

                ragas_evaluation = self._ragas_service.evaluate_response(
                    question=test_case.question,
                    response=model_response.content,
                    reference=reference,
                    retrieved_contexts=retrieved_contexts,
                    key_facts=key_facts if isinstance(key_facts, list) and len(key_facts) > 0 else None,
                )

                if ragas_evaluation.evaluation_error:
                    self._logger.warning(
                        f"RAGAs evaluation error for {test_case.test_id}: {ragas_evaluation.error_message}"
                    )
            except Exception as e:
                self._logger.warning(
                    f"RAGAs evaluation failed for {test_case.test_id}: {str(e)}"
                )

        # Create evaluation result
        result = EvaluationResult(
            test_case=test_case,
            model_response=model_response,
            metrics=metrics,
            ragas_evaluation=ragas_evaluation,
            retrieved_chunk_ids=retrieved_chunk_ids,
            chunk_count=chunk_count,
            evaluation_mode=request.evaluation_mode if self._rag_pipeline else None,
            system_prompt=system_prompt_captured,
            user_prompt=user_prompt_captured,
            retrieved_contexts_detailed=retrieved_contexts_detailed_captured,
        )

        # Finalize (calculate score and pass/fail with configurable threshold)
        # Phase 2: Use threshold from request if provided, otherwise use phase-specific default
        threshold = self._get_threshold(request)
        result.finalize(threshold=threshold)

        return result

    def _extract_ragas_score(self, result: EvaluationResult) -> Optional[float]:
        """Extract RAGAs composite score from domain entity."""
        return result.ragas_composite_score

    def _calculate_category_weighted_ragas_score(
        self,
        results: List[EvaluationResult]
    ) -> Optional[float]:
        """
        Calculate category-weighted RAGAs composite score.

        Uses same category weighting as _calculate_category_weighted_score
        but with per-test ragas_composite_score instead of overall_score.

        Returns None if no results have RAGAs scores.
        """
        if not results:
            return None

        categories = EvaluationCategory.get_all_categories()

        category_scores = {}
        for category in categories:
            category_ragas = []
            for r in results:
                if r.test_case.benchmark_type.short_name in category.benchmarks:
                    ragas_score = self._extract_ragas_score(r)
                    if ragas_score is not None:
                        category_ragas.append(ragas_score)

            if category_ragas:
                category_avg = sum(category_ragas) / len(category_ragas)
                category_scores[category.name] = {
                    "average": category_avg,
                    "weight": category.weight,
                }

        if not category_scores:
            return None

        weighted_sum = sum(
            cat["average"] * cat["weight"]
            for cat in category_scores.values()
        )
        total_weight = sum(cat["weight"] for cat in category_scores.values())
        return weighted_sum / total_weight if total_weight > 0 else None

    def _generate_summary(
        self,
        model_name: str,
        results: List[EvaluationResult],
        start_time: datetime,
        end_time: datetime
    ) -> EvaluationSummaryDTO:
        """Generate evaluation summary from results."""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = total_tests - passed_tests

        # Calculate overall score using category-level weighting
        overall_score = self._calculate_category_weighted_score(results)

        # Group by benchmark
        by_benchmark = self._group_by_benchmark(results)

        # Group by difficulty
        by_difficulty = self._group_by_difficulty(results)

        # Aggregate quality categories
        quality_categories = self._aggregate_quality_categories(results)

        # Calculate summary-level RAGAs score
        ragas_overall_score = self._calculate_category_weighted_ragas_score(results)

        # Convert results to DTOs
        result_dtos = [self._result_to_dto(r) for r in results]

        duration = (end_time - start_time).total_seconds()

        return EvaluationSummaryDTO(
            model_name=model_name,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            overall_score=overall_score,
            ragas_overall_score=ragas_overall_score,
            by_benchmark=by_benchmark,
            by_difficulty=by_difficulty,
            evaluation_started_at=start_time,
            evaluation_completed_at=end_time,
            total_duration_seconds=duration,
            results=result_dtos,
            quality_categories=quality_categories,
        )

    def _calculate_category_weighted_score(
        self,
        results: List[EvaluationResult]
    ) -> float:
        """
        Calculate overall score using category-level weighting.

        Categories and weights:
        - Regulatory Applicability & Interpretation (B1-B5): 25%
        - Compliance & Risk Reasoning (B6-B12): 35%
        - Remediation & Audit Reasoning (B13-B16): 20%
        - Governance & Consistency (B17-B19): 10%
        - Safety & Regulatory Grounding (B20-B21): 10%

        Args:
            results: List of evaluation results

        Returns:
            Category-weighted overall score (0.0-1.0)
        """
        if not results:
            return 0.0

        # Get all evaluation categories
        categories = EvaluationCategory.get_all_categories()

        # Group results by category
        category_scores = {}
        for category in categories:
            # Find all results for benchmarks in this category
            category_results = [
                r for r in results
                if r.test_case.benchmark_type.short_name in category.benchmarks
                and r.overall_score is not None
            ]

            if category_results:
                # Calculate average score for this category
                category_avg = sum(r.overall_score for r in category_results) / len(category_results)
                category_scores[category.name] = {
                    "average": category_avg,
                    "weight": category.weight,
                    "count": len(category_results)
                }

                self._logger.info(
                    f"Category '{category.name}': {category_avg:.2%} (weight: {category.weight:.0%}, tests: {len(category_results)})"
                )

        # Calculate weighted overall score, normalized by total weight of present categories
        if not category_scores:
            # Fallback to simple average if no category matches
            return sum(r.overall_score for r in results if r.overall_score is not None) / len(results)

        weighted_sum = sum(
            cat["average"] * cat["weight"]
            for cat in category_scores.values()
        )
        total_weight = sum(cat["weight"] for cat in category_scores.values())
        normalized_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        self._logger.info(
            f"Category-weighted overall score: {normalized_score:.2%} "
            f"(weighted_sum={weighted_sum:.4f}, total_weight={total_weight:.2f})"
        )

        return normalized_score

    def _aggregate_quality_categories(
        self,
        results: List[EvaluationResult]
    ) -> Dict[str, any]:
        """
        Aggregate quality metrics into categorized groups at per-benchmark and overall levels.

        Computes:
        1. Per-benchmark group scores (simple average across test cases)
        2. Overall group scores (weighted average using category weights)

        Handles:
        - llm-only mode: Retrieval Quality and Model-RAG Grounding show N/A
        - RAGAs errors: count as 0 in averages
        - LLM Judge normalization: already 0-1 from scoring service

        Args:
            results: List of evaluation results

        Returns:
            Dict with structure: {"overall": {"groups": [...]}, "by_benchmark": {"B1": {"groups": [...]}, ...}}
        """
        if not results:
            return {"overall": {"groups": []}, "by_benchmark": {}}

        # Determine evaluation mode from first result (all share same mode in a run)
        evaluation_mode = results[0].evaluation_mode if results[0].evaluation_mode else "llm-only"
        rag_only_groups = QualityGroup.get_rag_only_groups()

        # Group results by benchmark
        benchmark_groups = {}
        for result in results:
            benchmark_key = result.test_case.benchmark_type.short_name
            if benchmark_key not in benchmark_groups:
                benchmark_groups[benchmark_key] = []
            benchmark_groups[benchmark_key].append(result)

        # Process each benchmark
        by_benchmark = {}
        for benchmark_key, bench_results in benchmark_groups.items():
            benchmark_data = {"groups": []}

            for quality_group in QualityGroup.get_all_groups():
                group_dict = {
                    "name": quality_group.name,
                    "metrics": [],
                    "average": None
                }

                # Check if this group should show N/A in llm-only mode
                if quality_group.name in rag_only_groups and evaluation_mode != "hybrid":
                    # Mark all metrics as N/A
                    for metric_name in quality_group.metrics:
                        group_dict["metrics"].append({
                            "name": QualityGroup.get_display_name(metric_name),
                            "value": None
                        })
                    group_dict["average"] = None
                else:
                    # Compute metrics for this group
                    metric_values = []
                    for metric_name in quality_group.metrics:
                        if metric_name == "llm_judge":
                            # LLM Judge: use overall_score (already 0-1 normalized)
                            scores = [r.overall_score for r in bench_results if r.overall_score is not None]
                            if scores:
                                metric_avg = sum(scores) / len(scores)
                                metric_values.append(metric_avg)
                                group_dict["metrics"].append({
                                    "name": QualityGroup.get_display_name(metric_name),
                                    "value": metric_avg
                                })
                            else:
                                group_dict["metrics"].append({
                                    "name": QualityGroup.get_display_name(metric_name),
                                    "value": None
                                })
                        else:
                            # RAGAs metric
                            scores = []
                            for result in bench_results:
                                if result.ragas_evaluation is None:
                                    continue
                                if result.ragas_evaluation.evaluation_error:
                                    # Error: count as 0
                                    scores.append(0.0)
                                else:
                                    # Find matching metric
                                    for ragas_metric in result.ragas_evaluation.metrics:
                                        if ragas_metric.name == metric_name:
                                            if ragas_metric.applicable:
                                                scores.append(ragas_metric.score)
                                            # If not applicable, skip (don't count toward average)
                                            break

                            if scores:
                                metric_avg = sum(scores) / len(scores)
                                metric_values.append(metric_avg)
                                group_dict["metrics"].append({
                                    "name": QualityGroup.get_display_name(metric_name),
                                    "value": metric_avg
                                })
                            else:
                                group_dict["metrics"].append({
                                    "name": QualityGroup.get_display_name(metric_name),
                                    "value": None
                                })

                    # Calculate group average from non-None metric values
                    if metric_values:
                        group_dict["average"] = sum(metric_values) / len(metric_values)

                benchmark_data["groups"].append(group_dict)

            by_benchmark[benchmark_key] = benchmark_data

        # Compute overall scores using category-level weighting
        categories = EvaluationCategory.get_all_categories()
        overall_groups = []

        for quality_group in QualityGroup.get_all_groups():
            group_dict = {
                "name": quality_group.name,
                "metrics": [],
                "average": None
            }

            # Check if this group should show N/A in llm-only mode
            if quality_group.name in rag_only_groups and evaluation_mode != "hybrid":
                # Mark all metrics as N/A at overall level
                for metric_name in quality_group.metrics:
                    group_dict["metrics"].append({
                        "name": QualityGroup.get_display_name(metric_name),
                        "value": None
                    })
                group_dict["average"] = None
            else:
                # Compute category-weighted average for this group
                # Step 1: Compute category-level group averages
                category_group_scores = {}
                total_weight = 0.0

                for category in categories:
                    # Find benchmarks in this category that we have results for
                    category_benchmark_avgs = []
                    for benchmark_key in category.benchmarks:
                        if benchmark_key in by_benchmark:
                            # Find this group's average in the benchmark data
                            for group_data in by_benchmark[benchmark_key]["groups"]:
                                if group_data["name"] == quality_group.name:
                                    if group_data["average"] is not None:
                                        category_benchmark_avgs.append(group_data["average"])
                                    break

                    # Category-level average for this group
                    if category_benchmark_avgs:
                        category_avg = sum(category_benchmark_avgs) / len(category_benchmark_avgs)
                        category_group_scores[category.name] = category_avg
                        total_weight += category.weight

                # Step 2: Compute weighted overall group score
                if category_group_scores and total_weight > 0:
                    weighted_sum = sum(
                        score * categories[i].weight
                        for i, (cat_name, score) in enumerate(category_group_scores.items())
                        for category in categories if category.name == cat_name
                    )
                    # Normalize by actual weight used
                    group_dict["average"] = weighted_sum / total_weight
                else:
                    group_dict["average"] = None

                # Populate per-metric values at overall level (category-weighted per metric)
                for metric_name in quality_group.metrics:
                    # Compute category-weighted average for this individual metric
                    metric_category_scores = {}
                    metric_total_weight = 0.0

                    for category in categories:
                        category_metric_values = []
                        for benchmark_key in category.benchmarks:
                            if benchmark_key in by_benchmark:
                                for group_data in by_benchmark[benchmark_key]["groups"]:
                                    if group_data["name"] == quality_group.name:
                                        for m in group_data["metrics"]:
                                            if m["name"] == QualityGroup.get_display_name(metric_name):
                                                if m["value"] is not None:
                                                    category_metric_values.append(m["value"])
                                        break

                        if category_metric_values:
                            cat_avg = sum(category_metric_values) / len(category_metric_values)
                            metric_category_scores[category.name] = cat_avg
                            metric_total_weight += category.weight

                    if metric_category_scores and metric_total_weight > 0:
                        weighted_sum = sum(
                            score * cat.weight
                            for cat_name, score in metric_category_scores.items()
                            for cat in categories if cat.name == cat_name
                        )
                        metric_overall = weighted_sum / metric_total_weight
                    else:
                        metric_overall = None

                    group_dict["metrics"].append({
                        "name": QualityGroup.get_display_name(metric_name),
                        "value": metric_overall
                    })

            overall_groups.append(group_dict)

        return {
            "overall": {"groups": overall_groups},
            "by_benchmark": by_benchmark
        }

    def _build_evaluation_metadata(
        self,
        request: EvaluationRequestDTO,
        summary: 'EvaluationSummaryDTO',
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, any]:
        """
        Build metadata for evaluation run.

        Includes model parameters, benchmark scores, category weights, and tier information.

        Args:
            request: Evaluation request
            summary: Evaluation summary
            start_time: Evaluation start time
            end_time: Evaluation end time

        Returns:
            Metadata dictionary
        """
        metadata = {
            "run_id": request.run_id,
            "schema_version": 6,
            "model_name": request.model_name,
            "evaluation_phase": request.evaluation_phase,
            "evaluation_mode": request.evaluation_mode,
            "pass_threshold": request.pass_threshold or self._get_threshold(request),
            "benchmarks": request.benchmark_types,
            "total_tests": summary.total_tests,
            "passed_tests": summary.passed_tests,
            "failed_tests": summary.failed_tests,
            "overall_score": summary.overall_score,
            "ragas_overall_score": summary.ragas_overall_score,
            "evaluated_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "duration_seconds": summary.total_duration_seconds,
            "temperature": request.temperature,
        }

        # Add tier if used
        from domain.value_objects.evaluation_tier import EvaluationTier
        for tier in EvaluationTier.get_all_tiers():
            if set(tier.benchmarks) == set(request.benchmark_types):
                metadata["tier"] = tier.tier_number
                metadata["tier_name"] = tier.name
                break

        # Add benchmark scores
        metadata["benchmark_scores"] = summary.by_benchmark

        # Add category scores
        metadata["category_scores"] = self._calculate_category_scores(summary.results)

        # Add quality categories
        if summary.quality_categories:
            metadata["quality_categories"] = summary.quality_categories

        return metadata

    def _calculate_category_scores(
        self,
        results: List['EvaluationResultDTO']
    ) -> Dict[str, Dict[str, any]]:
        """
        Calculate scores per evaluation category.

        Args:
            results: List of evaluation result DTOs

        Returns:
            Dictionary mapping category names to their scores and weights
        """
        from domain.value_objects.evaluation_category import EvaluationCategory

        categories = EvaluationCategory.get_all_categories()
        category_scores = {}

        for category in categories:
            # Find results for benchmarks in this category
            # Use underscore delimiter to prevent prefix collisions (e.g., B2 matching B21)
            category_results = [
                r for r in results
                if any(
                    r.benchmark_type.startswith(b + "_") or r.benchmark_type == b
                    for b in category.benchmarks
                )
            ]

            if category_results:
                avg_score = sum(r.overall_score for r in category_results if r.overall_score is not None) / len(category_results)
                category_scores[category.name] = {
                    "average_score": avg_score,
                    "weight": category.weight,
                    "weighted_contribution": avg_score * category.weight,
                    "test_count": len(category_results),
                    "benchmarks": category.benchmarks
                }

        return category_scores

    def _group_by_benchmark(
        self,
        results: List[EvaluationResult]
    ) -> Dict[str, Dict[str, any]]:
        """Group results by benchmark type."""
        grouped: Dict[str, List[EvaluationResult]] = {}

        for result in results:
            benchmark = result.test_case.benchmark_type.value
            if benchmark not in grouped:
                grouped[benchmark] = []
            grouped[benchmark].append(result)

        summary = {}
        for benchmark, bench_results in grouped.items():
            total = len(bench_results)
            passed = sum(1 for r in bench_results if r.passed)
            score = sum(r.overall_score for r in bench_results if r.overall_score) / total

            summary[benchmark] = {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "score": score,
            }

        return summary

    def _group_by_difficulty(
        self,
        results: List[EvaluationResult]
    ) -> Dict[str, Dict[str, any]]:
        """Group results by difficulty level."""
        grouped: Dict[str, List[EvaluationResult]] = {}

        for result in results:
            difficulty = result.test_case.difficulty.value
            if difficulty not in grouped:
                grouped[difficulty] = []
            grouped[difficulty].append(result)

        summary = {}
        for difficulty, diff_results in grouped.items():
            total = len(diff_results)
            passed = sum(1 for r in diff_results if r.passed)
            score = sum(r.overall_score for r in diff_results if r.overall_score) / total

            summary[difficulty] = {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "score": score,
            }

        return summary

    def _result_to_dto(self, result: EvaluationResult) -> EvaluationResultDTO:
        """Convert domain EvaluationResult to DTO."""
        metrics_dtos = [
            MetricDTO(
                name=m.name,
                value=m.value,
                weight=m.weight,
                description=m.description,
            )
            for m in result.metrics
        ]

        # Build RAGAs DTO fields
        ragas_metrics = None
        ragas_is_rag_response = None
        ragas_error = None

        if result.ragas_evaluation is not None:
            ragas_eval = result.ragas_evaluation
            ragas_is_rag_response = ragas_eval.is_rag_response

            if ragas_eval.evaluation_error:
                ragas_error = ragas_eval.error_message
            else:
                ragas_metrics = [
                    RagasMetricDTO(
                        name=m.name,
                        score=m.score,
                        applicable=m.applicable,
                    )
                    for m in ragas_eval.metrics
                ]

        # Compute per-test RAGAs score
        ragas_score = self._extract_ragas_score(result)

        # Extract judge metadata if universal judge was used
        judge_mode = None
        hallucination_detected = None
        unsupported_count = None
        contradicted_count = None
        reasoning_criteria_met = None
        claims = None

        for metric in result.metrics:
            if metric.name == "universal_judge":
                judge_mode = "universal"
                try:
                    import json
                    judge_data = json.loads(metric.description)
                    hallucination_detected = judge_data.get("hallucination_detected")
                    unsupported_count = judge_data.get("unsupported_count")
                    contradicted_count = judge_data.get("contradicted_count")
                    reasoning_criteria_met = judge_data.get("reasoning_criteria_met")
                    claims = judge_data.get("claims")
                except (json.JSONDecodeError, AttributeError):
                    # If description is not JSON or missing, skip
                    pass
                break
            elif metric.name in ["accuracy", "completeness", "alignment"]:
                # Rubric-based dimensions indicate rubric mode
                judge_mode = "rubric"
                break

        return EvaluationResultDTO(
            result_id=result.result_id,
            test_id=result.test_case.test_id,
            benchmark_type=result.test_case.benchmark_type.value,
            question=result.test_case.question,
            model_name=result.model_response.model_name,
            response_content=result.model_response.content,
            metrics=metrics_dtos,
            overall_score=result.overall_score,
            ragas_score=ragas_score,
            passed=result.passed,
            threshold=result.test_case.get_passing_threshold(),
            evaluator_notes=result.evaluator_notes,
            tokens_used=result.model_response.tokens_used,
            latency_ms=result.model_response.latency_ms,
            evaluated_at=result.evaluated_at,
            metadata=result.metadata,
            ragas_metrics=ragas_metrics,
            ragas_is_rag_response=ragas_is_rag_response,
            ragas_error=ragas_error,
            evaluation_mode=result.evaluation_mode,
            retrieved_chunk_ids=result.retrieved_chunk_ids,
            chunk_count=result.chunk_count,
            judge_mode=judge_mode,
            hallucination_detected=hallucination_detected,
            unsupported_count=unsupported_count,
            contradicted_count=contradicted_count,
            reasoning_criteria_met=reasoning_criteria_met,
            claims=claims,
            # I/O capture fields (Phase 3.1 — traceability)
            system_prompt=result.system_prompt,
            user_prompt=result.user_prompt,
            prompt_tokens=result.model_response.prompt_tokens,
            completion_tokens=result.model_response.completion_tokens,
            total_tokens=result.model_response.total_tokens,
            retrieved_contexts_detailed=result.retrieved_contexts_detailed,
        )
