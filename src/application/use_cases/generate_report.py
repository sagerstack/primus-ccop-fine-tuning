"""
Generate Report Use Case

Generates evaluation reports in various formats.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from application.dtos.evaluation_result_dto import EvaluationSummaryDTO, MetricDTO
from application.ports.input.i_generate_report_use_case import IGenerateReportUseCase, ReportFormat
from application.ports.output.i_logger import ILogger
from application.ports.output.i_result_repository import IResultRepository
from domain.entities.evaluation_result import EvaluationResult


class GenerateReportUseCase(IGenerateReportUseCase):
    """
    Use case for generating evaluation reports.

    Supports multiple formats: JSON, Markdown, HTML, CSV.
    """

    def __init__(
        self,
        result_repository: IResultRepository,
        logger: ILogger,
    ) -> None:
        self._result_repository = result_repository
        self._logger = logger

    async def execute(
        self,
        model_name: str,
        format: ReportFormat = ReportFormat.JSON,
        output_path: Optional[str] = None,
        include_details: bool = True,
    ) -> str:
        """Generate evaluation report."""
        self._logger.info(
            f"Generating {format.value} report for model: {model_name}",
            include_details=include_details
        )

        # Get summary
        summary = await self.get_summary(model_name)

        # Generate report content based on format
        if format == ReportFormat.JSON:
            content = self._generate_json_report(summary, include_details)
        elif format == ReportFormat.MARKDOWN:
            content = self._generate_markdown_report(summary, include_details)
        elif format == ReportFormat.HTML:
            content = self._generate_html_report(summary, include_details)
        elif format == ReportFormat.CSV:
            content = self._generate_csv_report(summary)
        else:
            raise ValueError(f"Unsupported report format: {format}")

        # Save to file if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(content)
            self._logger.info(f"Report saved to: {output_path}")
            return str(output_file)

        return content

    async def get_summary(self, model_name: str) -> EvaluationSummaryDTO:
        """Get evaluation summary for a model."""
        # Load all results for the model
        results = await self._result_repository.load_by_model(model_name)

        if not results:
            raise ValueError(f"No evaluation results found for model: {model_name}")

        # Calculate summary
        return self._calculate_summary(model_name, results)

    def _calculate_summary(
        self,
        model_name: str,
        results: List[EvaluationResult]
    ) -> EvaluationSummaryDTO:
        """Calculate summary from results."""
        from application.dtos.evaluation_result_dto import EvaluationResultDTO

        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = total_tests - passed_tests

        overall_score = (
            sum(r.overall_score for r in results if r.overall_score) / total_tests
            if total_tests > 0 else 0.0
        )

        # Group by benchmark
        by_benchmark = {}
        benchmarks = {}
        for r in results:
            b = r.test_case.benchmark_type.value
            if b not in benchmarks:
                benchmarks[b] = []
            benchmarks[b].append(r)

        for b, b_results in benchmarks.items():
            total = len(b_results)
            passed = sum(1 for r in b_results if r.passed)
            score = sum(r.overall_score for r in b_results if r.overall_score) / total
            by_benchmark[b] = {"total": total, "passed": passed, "score": score}

        # Group by difficulty
        by_difficulty = {}
        difficulties = {}
        for r in results:
            d = r.test_case.difficulty.value
            if d not in difficulties:
                difficulties[d] = []
            difficulties[d].append(r)

        for d, d_results in difficulties.items():
            total = len(d_results)
            passed = sum(1 for r in d_results if r.passed)
            score = sum(r.overall_score for r in d_results if r.overall_score) / total
            by_difficulty[d] = {"total": total, "passed": passed, "score": score}

        # Get time range
        start_time = min(r.evaluated_at for r in results)
        end_time = max(r.evaluated_at for r in results)
        duration = (end_time - start_time).total_seconds()

        # Convert results to DTOs
        result_dtos = []
        for r in results:
            metrics_dtos = [
                MetricDTO(name=m.name, value=m.value, weight=m.weight, description=m.description)
                for m in r.metrics
            ]
            result_dtos.append(EvaluationResultDTO(
                result_id=r.result_id,
                test_id=r.test_case.test_id,
                benchmark_type=r.test_case.benchmark_type.value,
                model_name=r.model_response.model_name,
                response_content=r.model_response.content,
                metrics=metrics_dtos,
                overall_score=r.overall_score,
                passed=r.passed,
                threshold=r.test_case.get_passing_threshold(),
                evaluator_notes=r.evaluator_notes,
                tokens_used=r.model_response.tokens_used,
                latency_ms=r.model_response.latency_ms,
                evaluated_at=r.evaluated_at,
                metadata=r.metadata,
            ))

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

    def _generate_json_report(
        self,
        summary: EvaluationSummaryDTO,
        include_details: bool
    ) -> str:
        """Generate JSON report."""
        data = summary.model_dump()
        if not include_details:
            data.pop("results", None)
        return json.dumps(data, indent=2, default=str)

    def _generate_markdown_report(
        self,
        summary: EvaluationSummaryDTO,
        include_details: bool
    ) -> str:
        """Generate Markdown report."""
        lines = [
            f"# CCoP 2.0 Evaluation Report: {summary.model_name}",
            "",
            f"**Generated**: {datetime.utcnow().isoformat()}",
            "",
            "## Summary",
            "",
            f"- **Total Tests**: {summary.total_tests}",
            f"- **Passed**: {summary.passed_tests} ({summary.passed_tests/summary.total_tests*100:.1f}%)",
            f"- **Failed**: {summary.failed_tests} ({summary.failed_tests/summary.total_tests*100:.1f}%)",
            f"- **Overall Score**: {summary.overall_score:.2%}",
            f"- **Duration**: {summary.total_duration_seconds:.1f}s",
            "",
            "## Results by Benchmark",
            "",
            "| Benchmark | Total | Passed | Failed | Score |",
            "|-----------|-------|--------|--------|-------|",
        ]

        for benchmark, stats in summary.by_benchmark.items():
            lines.append(
                f"| {benchmark} | {stats['total']} | {stats['passed']} | "
                f"{stats['total'] - stats['passed']} | {stats['score']:.2%} |"
            )

        lines.extend([
            "",
            "## Results by Difficulty",
            "",
            "| Difficulty | Total | Passed | Failed | Score |",
            "|------------|-------|--------|--------|-------|",
        ])

        for difficulty, stats in summary.by_difficulty.items():
            lines.append(
                f"| {difficulty} | {stats['total']} | {stats['passed']} | "
                f"{stats['total'] - stats['passed']} | {stats['score']:.2%} |"
            )

        if include_details:
            lines.extend([
                "",
                "## Detailed Results",
                "",
            ])
            for result in summary.results:
                status = "✓ PASSED" if result.passed else "✗ FAILED"
                lines.extend([
                    f"### {result.test_id} - {status}",
                    "",
                    f"- **Benchmark**: {result.benchmark_type}",
                    f"- **Score**: {result.overall_score:.2%} (threshold: {result.threshold:.2%})",
                    f"- **Tokens**: {result.tokens_used}",
                    f"- **Latency**: {result.latency_ms}ms",
                    "",
                ])

        return "\n".join(lines)

    def _generate_html_report(
        self,
        summary: EvaluationSummaryDTO,
        include_details: bool
    ) -> str:
        """Generate HTML report."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>CCoP 2.0 Evaluation Report: {summary.model_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
    </style>
</head>
<body>
    <h1>CCoP 2.0 Evaluation Report: {summary.model_name}</h1>
    <p><strong>Overall Score:</strong> {summary.overall_score:.2%}</p>
    <p><strong>Passed:</strong> {summary.passed_tests}/{summary.total_tests}</p>
    <h2>Results by Benchmark</h2>
    <table>
        <tr><th>Benchmark</th><th>Total</th><th>Passed</th><th>Failed</th><th>Score</th></tr>
"""
        for benchmark, stats in summary.by_benchmark.items():
            html += f"""        <tr>
            <td>{benchmark}</td>
            <td>{stats['total']}</td>
            <td>{stats['passed']}</td>
            <td>{stats['total'] - stats['passed']}</td>
            <td>{stats['score']:.2%}</td>
        </tr>
"""
        html += """    </table>
</body>
</html>"""
        return html

    def _generate_csv_report(self, summary: EvaluationSummaryDTO) -> str:
        """Generate CSV report."""
        lines = [
            "test_id,benchmark,score,passed,tokens,latency_ms"
        ]
        for result in summary.results:
            lines.append(
                f"{result.test_id},{result.benchmark_type},"
                f"{result.overall_score:.3f},{result.passed},"
                f"{result.tokens_used},{result.latency_ms}"
            )
        return "\n".join(lines)
