"""
Evaluate Model Use Case

Orchestrates model evaluation across test cases.
"""

from datetime import datetime
from typing import Dict, List

from application.dtos.evaluation_request_dto import EvaluationRequestDTO
from application.dtos.evaluation_result_dto import (
    EvaluationResultDTO,
    EvaluationSummaryDTO,
    MetricDTO,
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
    ) -> None:
        self._model_gateway = model_gateway
        self._test_case_repository = test_case_repository
        self._result_repository = result_repository
        self._logger = logger

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

        # Save results if requested
        if request.save_results:
            await self._result_repository.save_batch(results)
            self._logger.info(f"Saved {len(results)} results")

        # Generate summary
        end_time = datetime.utcnow()
        summary = self._generate_summary(
            request.model_name,
            results,
            start_time,
            end_time
        )

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

    async def _evaluate_test_case(
        self,
        test_case: TestCase,
        request: EvaluationRequestDTO
    ) -> EvaluationResult:
        """Evaluate a single test case."""
        # Determine max tokens
        max_tokens = request.max_tokens or test_case.get_max_tokens_for_response()

        # Generate response
        model_response = await self._model_gateway.generate_response(
            prompt=test_case.question,
            model_name=request.model_name,
            temperature=request.temperature,
            max_tokens=max_tokens,
            top_p=request.top_p,
            top_k=request.top_k,
            system_prompt="You are a cybersecurity compliance expert specializing in Singapore's CCoP 2.0.",
        )

        # Score response
        metrics = ScoringService.score_response(test_case, model_response)

        # Create evaluation result
        result = EvaluationResult(
            test_case=test_case,
            model_response=model_response,
            metrics=metrics,
        )

        # Finalize (calculate score and pass/fail)
        result.finalize()

        return result

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

        # Calculate overall score
        overall_score = (
            sum(r.overall_score for r in results if r.overall_score is not None) / total_tests
            if total_tests > 0 else 0.0
        )

        # Group by benchmark
        by_benchmark = self._group_by_benchmark(results)

        # Group by difficulty
        by_difficulty = self._group_by_difficulty(results)

        # Convert results to DTOs
        result_dtos = [self._result_to_dto(r) for r in results]

        duration = (end_time - start_time).total_seconds()

        return EvaluationSummaryDTO(
            model_name=model_name,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            overall_score=overall_score,
            by_benchmark=by_benchmark,
            by_difficulty=by_difficulty,
            evaluation_started_at=start_time,
            evaluation_completed_at=end_time,
            total_duration_seconds=duration,
            results=result_dtos,
        )

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

        return EvaluationResultDTO(
            result_id=result.result_id,
            test_id=result.test_case.test_id,
            benchmark_type=result.test_case.benchmark_type.value,
            model_name=result.model_response.model_name,
            response_content=result.model_response.content,
            metrics=metrics_dtos,
            overall_score=result.overall_score,
            passed=result.passed,
            threshold=result.test_case.get_passing_threshold(),
            evaluator_notes=result.evaluator_notes,
            tokens_used=result.model_response.tokens_used,
            latency_ms=result.model_response.latency_ms,
            evaluated_at=result.evaluated_at,
            metadata=result.metadata,
        )
