"""
Evaluate Command

CLI command for evaluating models.
"""

import asyncio
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from application.dtos.evaluation_request_dto import EvaluationRequestDTO
from domain.value_objects.evaluation_tier import EvaluationTier
from domain.value_objects.quality_group import QualityGroup

evaluate_app = typer.Typer()
console = Console()

VALID_EVAL_MODES = ["hybrid", "llm-only"]


@evaluate_app.command()
def run(
    ctx: typer.Context,
    model: str = typer.Option(..., help="Model name"),
    benchmarks: Optional[List[str]] = typer.Option(
        None, help="Benchmarks to run (can specify multiple times, e.g., --benchmarks B1 --benchmarks B2)"
    ),
    tier: Optional[int] = typer.Option(
        None, help="Evaluation tier (1, 2, or 3). Overrides --benchmarks if specified."
    ),
    test_ids: Optional[List[str]] = typer.Option(
        None, help="Specific test IDs (can specify multiple times)"
    ),
    temperature: float = typer.Option(0.7, help="Temperature"),
    save: bool = typer.Option(True, help="Save results"),
    phase: str = typer.Option(
        "baseline",
        help="Evaluation phase: baseline (15%), finetuned (50%), deployment (85%)"
    ),
    threshold: Optional[float] = typer.Option(
        None,
        min=0.0,
        max=1.0,
        help="Pass threshold override (0.0-1.0). Overrides phase-specific threshold."
    ),
    mode: str = typer.Option(
        "hybrid",
        "--mode",
        "-m",
        help="Evaluation mode: hybrid (RAG-augmented) or llm-only"
    ),
) -> None:
    """Run model evaluation."""
    container = ctx.obj["container"]
    use_case = container.evaluate_model_use_case()

    # Validate mode parameter
    if mode not in VALID_EVAL_MODES:
        console.print(f"[red]Invalid mode: {mode}. Must be one of: {', '.join(VALID_EVAL_MODES)}[/red]")
        raise typer.Exit(1)

    # Handle --tier argument (takes precedence over --benchmarks)
    if tier is not None:
        if tier not in [1, 2, 3]:
            console.print(f"[red]Invalid tier: {tier}. Must be 1, 2, or 3.[/red]")
            raise typer.Exit(1)

        benchmarks = EvaluationTier.get_benchmarks_for_tier(tier)
        tier_name = EvaluationTier.get_tier_name(tier)
        console.print(f"[cyan]Running Tier {tier} evaluation ({tier_name})[/cyan]")

    # Default to all benchmarks if none specified
    # Query available benchmarks from repository
    if not benchmarks:
        # Get repository to discover available benchmarks
        repo = container.test_case_repository()
        # Use discovered benchmark files
        if hasattr(repo, '_benchmark_files') and repo._benchmark_files:
            # Extract unique benchmark numbers (B1, B2, B3, etc.)
            benchmark_numbers = set()
            for bt_str in repo._benchmark_files.keys():
                # Extract Bxx from strings like "B1_CCoP_Applicability_Scope"
                if bt_str.startswith('B'):
                    # Get just the Bxx part
                    parts = bt_str.split('_')
                    if parts:
                        benchmark_numbers.add(parts[0])
            benchmarks = sorted(list(benchmark_numbers), key=lambda x: int(x[1:]))
        else:
            # Fallback: use B1-B21 as default
            benchmarks = [f"B{i}" for i in range(1, 22)]

    console.print(f"[bold]Evaluating model:[/bold] {model}")
    console.print(f"[bold]Benchmarks:[/bold] {', '.join(benchmarks)}")
    console.print(f"[bold]Evaluation Phase:[/bold] {phase}")
    console.print(f"[bold]Evaluation Mode:[/bold] {mode}")

    # Display threshold being used
    if threshold is not None:
        console.print(f"[bold]Pass Threshold:[/bold] {threshold:.0%} (override)")
    else:
        phase_thresholds = {"baseline": 0.15, "finetuned": 0.50, "deployment": 0.85}
        default_threshold = phase_thresholds.get(phase, 0.70)
        console.print(f"[bold]Pass Threshold:[/bold] {default_threshold:.0%} (phase default)")

    request = EvaluationRequestDTO(
        model_name=model,
        benchmark_types=benchmarks,
        test_case_ids=test_ids,
        temperature=temperature,
        save_results=save,
        evaluation_phase=phase,
        pass_threshold=threshold,
        evaluation_mode=mode,
    )

    try:
        console.print("\n[yellow]Running evaluation...[/yellow]\n")
        summary = asyncio.run(use_case.execute(request))

        # Per-test-case detail output
        console.print("\n[bold]Per-Test-Case Results[/bold]\n")
        for r in summary.results:
            status_label = "[bold green]PASS[/bold green]" if r.passed else "[bold red]FAIL[/bold red]"
            score_str = f"{r.overall_score:.2f}" if r.overall_score is not None else "N/A"
            border_style = "green" if r.passed else "red"

            mode_suffix = f" | {r.evaluation_mode}" if r.evaluation_mode else ""
            title = f"{r.test_id} | {r.benchmark_type} | {'PASS' if r.passed else 'FAIL'} | Score: {score_str}{mode_suffix}"

            lines = []

            # Question
            lines.append(f"[bold]Question:[/bold]\n  {r.question}")

            # Response
            lines.append(f"\n[bold]Response[/bold] ({r.tokens_used} tokens, {r.latency_ms}ms):\n  {r.response_content}")

            # REORGANIZED INTO 3 DIAGNOSTIC GROUPS

            # Group 1: Model Response Quality (LLM Judge + answer metrics)
            lines.append("\n[bold cyan]─── Model Response Quality ───[/bold cyan]")

            # LLM Judge Dimensions
            judge_metrics = [m for m in r.metrics if m.name != "judge_error"]
            judge_errors = [m for m in r.metrics if m.name == "judge_error"]

            if judge_metrics:
                lines.append("[bold]LLM Judge:[/bold]")
                for m in judge_metrics:
                    raw_score = round(m.value * 3)
                    lines.append(f"  {m.name:<30s} {raw_score}/3  (weight: {m.weight:.2f})")
            if judge_errors:
                lines.append("[bold]LLM Judge:[/bold] [yellow]⚠ Judge Error[/yellow]")

            # RAGAs answer metrics (answer_correctness, answer_relevancy)
            if r.ragas_metrics:
                answer_metrics = [rm for rm in r.ragas_metrics if rm.name in ["answer_correctness", "answer_relevancy"]]
                for rm in answer_metrics:
                    metric_display = QualityGroup.get_display_name(rm.name)
                    if rm.applicable:
                        lines.append(f"[bold]{metric_display}:[/bold] {rm.score:.2f}")
                    else:
                        lines.append(f"[bold]{metric_display}:[/bold] N/A (not applicable)")
            elif r.ragas_error:
                lines.append(f"[bold]RAGAs answer metrics:[/bold] [yellow]⚠ {r.ragas_error}[/yellow]")

            # Group 2: Model-RAG Grounding (faithfulness)
            lines.append("\n[bold magenta]─── Model-RAG Grounding ───[/bold magenta]")

            if r.evaluation_mode == "llm-only":
                lines.append("[dim]N/A (llm-only mode)[/dim]")
            elif r.ragas_metrics:
                faithfulness_metrics = [rm for rm in r.ragas_metrics if rm.name == "faithfulness"]
                if faithfulness_metrics:
                    for rm in faithfulness_metrics:
                        metric_display = QualityGroup.get_display_name(rm.name)
                        if rm.applicable:
                            lines.append(f"[bold]{metric_display}:[/bold] {rm.score:.2f}")
                        else:
                            lines.append(f"[bold]{metric_display}:[/bold] N/A (not applicable)")
                else:
                    lines.append("[dim]No faithfulness metric available[/dim]")
            elif r.ragas_error:
                lines.append(f"[bold]RAGAs faithfulness:[/bold] [yellow]⚠ {r.ragas_error}[/yellow]")
            else:
                lines.append("[dim]No RAGAs metrics available[/dim]")

            # Group 3: Retrieval Quality (context metrics)
            lines.append("\n[bold yellow]─── Retrieval Quality ───[/bold yellow]")

            if r.evaluation_mode == "llm-only":
                lines.append("[dim]N/A (llm-only mode)[/dim]")
            elif r.ragas_metrics:
                context_metrics = [rm for rm in r.ragas_metrics if rm.name in ["context_recall", "context_precision"]]
                if context_metrics:
                    for rm in context_metrics:
                        metric_display = QualityGroup.get_display_name(rm.name)
                        if rm.applicable:
                            lines.append(f"[bold]{metric_display}:[/bold] {rm.score:.2f}")
                        else:
                            lines.append(f"[bold]{metric_display}:[/bold] N/A (not applicable)")
                else:
                    lines.append("[dim]No context metrics available[/dim]")
            elif r.ragas_error:
                lines.append(f"[bold]RAGAs context metrics:[/bold] [yellow]⚠ {r.ragas_error}[/yellow]")
            else:
                lines.append("[dim]No RAGAs metrics available[/dim]")

            # RAG response detection note
            if r.ragas_is_rag_response:
                lines.append("\n[dim]RAG response detected — context metrics evaluated[/dim]")

            # RAG Context info (hybrid mode)
            if r.evaluation_mode and r.chunk_count is not None:
                if r.chunk_count > 0 and r.retrieved_chunk_ids:
                    # Format chunk IDs for display (truncate if too many)
                    chunk_display = ", ".join(r.retrieved_chunk_ids[:5])
                    if len(r.retrieved_chunk_ids) > 5:
                        chunk_display += f", ... ({len(r.retrieved_chunk_ids)} total)"
                    lines.append(f"\n[bold]RAG Context:[/bold] {r.chunk_count} chunks ({chunk_display})")
                elif r.evaluation_mode == "hybrid":
                    lines.append(f"\n[bold]RAG Context:[/bold] No chunks retrieved")
                # For llm-only mode, don't show RAG Context line

            panel_content = "\n".join(lines)
            console.print(Panel(panel_content, title=title, border_style=border_style))

        # Display results
        console.print("\n[bold green]Evaluation Complete![/bold green]\n")

        # Determine evaluation mode
        eval_mode = summary.results[0].evaluation_mode if summary.results else "hybrid"

        # Check if quality_categories is available (new format)
        if summary.quality_categories:
            # NEW CATEGORIZED QUALITY DISPLAY

            # Run info header
            console.print(f"[bold]Model:[/bold] {summary.model_name}")
            console.print(f"[bold]Tests:[/bold] {summary.total_tests} total | {summary.passed_tests} passed | {summary.failed_tests} failed")
            console.print(f"[bold]Duration:[/bold] {summary.total_duration_seconds:.1f}s")
            console.print(f"[bold]Mode:[/bold] {eval_mode}\n")

            # Overall Quality Summary table
            overall_table = Table(title="Overall Quality Summary", show_header=True)
            overall_table.add_column("Quality Group", style="cyan", no_wrap=True)
            overall_table.add_column("LLM Judge", justify="center")
            overall_table.add_column("RAGAs: answer_correctness", justify="center")
            overall_table.add_column("RAGAs: answer_relevancy", justify="center")
            overall_table.add_column("RAGAs: faithfulness", justify="center")
            overall_table.add_column("RAGAs: context_recall", justify="center")
            overall_table.add_column("RAGAs: context_precision", justify="center")
            overall_table.add_column("Group Avg", justify="center", style="bold")

            # Helper to format metric value with color
            def format_metric(value: Optional[float]) -> str:
                if value is None:
                    return "[dim]N/A[/dim]"
                if value >= 0.7:
                    return f"[green]{value:.2f}[/green]"
                elif value >= 0.4:
                    return f"[yellow]{value:.2f}[/yellow]"
                else:
                    return f"[red]{value:.2f}[/red]"

            # Extract overall quality categories
            overall_groups = summary.quality_categories.get("overall", {}).get("groups", [])

            # Build rows for each quality group
            for group_data in overall_groups:
                group_name = group_data["name"]
                metrics_data = {m["name"]: m["value"] for m in group_data["metrics"]}
                group_avg = group_data["average"]

                # Map metric display names to values
                llm_judge = metrics_data.get("LLM Judge")
                answer_correctness = metrics_data.get("RAGAs: answer_correctness")
                answer_relevancy = metrics_data.get("RAGAs: answer_relevancy")
                faithfulness = metrics_data.get("RAGAs: faithfulness")
                context_recall = metrics_data.get("RAGAs: context_recall")
                context_precision = metrics_data.get("RAGAs: context_precision")

                overall_table.add_row(
                    group_name,
                    format_metric(llm_judge),
                    format_metric(answer_correctness),
                    format_metric(answer_relevancy),
                    format_metric(faithfulness),
                    format_metric(context_recall),
                    format_metric(context_precision),
                    format_metric(group_avg)
                )

            # Overall Score row
            overall_table.add_section()
            overall_table.add_row(
                "[bold]Overall Score[/bold]",
                "", "", "", "", "", "",
                f"[bold]{format_metric(summary.overall_score)}[/bold]"
            )

            console.print(overall_table)

            # Per-Benchmark Quality Breakdown
            if summary.by_benchmark:
                console.print("\n[bold]Quality Breakdown by Benchmark:[/bold]\n")

                by_benchmark_data = summary.quality_categories.get("by_benchmark", {})

                # Create table with group header rows
                bench_table = Table(show_header=True)
                bench_table.add_column("Benchmark", style="cyan", no_wrap=True)
                bench_table.add_column("LLM Judge", justify="center")
                bench_table.add_column("RAGAs: answer_correctness", justify="center")
                bench_table.add_column("RAGAs: answer_relevancy", justify="center")
                bench_table.add_column("RAGAs: faithfulness", justify="center")
                bench_table.add_column("RAGAs: context_recall", justify="center")
                bench_table.add_column("RAGAs: context_precision", justify="center")

                # Sort benchmarks (B1, B2, ..., B21) — extract short name for sorting
                def _bench_sort_key(full_name: str) -> int:
                    short = full_name.split("_")[0]
                    num = short[1:] if short.startswith("B") else short
                    return int(num) if num.isdigit() else 0

                sorted_benchmarks = sorted(summary.by_benchmark.keys(), key=_bench_sort_key)

                for benchmark in sorted_benchmarks:
                    # quality_categories uses short names (B1), by_benchmark uses full names
                    short_name = benchmark.split("_")[0]
                    bench_groups = by_benchmark_data.get(short_name, {}).get("groups", [])

                    # Reorder: Model Response Quality first (shows benchmark name), then sub-groups
                    ordered_groups = sorted(
                        bench_groups,
                        key=lambda g: 0 if g["name"] == "Model Response Quality" else 1
                    )

                    for i, group_data in enumerate(ordered_groups):
                        group_name = group_data["name"]
                        metrics_data = {m["name"]: m["value"] for m in group_data["metrics"]}

                        llm_judge = metrics_data.get("LLM Judge")
                        answer_correctness = metrics_data.get("RAGAs: answer_correctness")
                        answer_relevancy = metrics_data.get("RAGAs: answer_relevancy")
                        faithfulness = metrics_data.get("RAGAs: faithfulness")
                        context_recall = metrics_data.get("RAGAs: context_recall")
                        context_precision = metrics_data.get("RAGAs: context_precision")

                        # First row shows benchmark name, subsequent rows show group name
                        display_name = f"{short_name}" if i == 0 else f"  └─ {group_name}"

                        bench_table.add_row(
                            display_name,
                            format_metric(llm_judge),
                            format_metric(answer_correctness),
                            format_metric(answer_relevancy),
                            format_metric(faithfulness),
                            format_metric(context_recall),
                            format_metric(context_precision)
                        )

                console.print(bench_table)

        else:
            # FALLBACK: OLD FORMAT (if quality_categories is None)
            console.print("[yellow]Note: Using legacy display format (quality_categories not available)[/yellow]\n")

            # Summary table
            table = Table(title="Evaluation Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")

            table.add_row("Model", summary.model_name)
            table.add_row("Total Tests", str(summary.total_tests))
            table.add_row("Passed", str(summary.passed_tests))
            table.add_row("Failed", str(summary.failed_tests))
            table.add_row("Overall Score", f"{summary.overall_score:.2%}")
            table.add_row("Duration", f"{summary.total_duration_seconds:.1f}s")

            # Add evaluation mode if available
            if summary.results and summary.results[0].evaluation_mode:
                table.add_row("Evaluation Mode", summary.results[0].evaluation_mode)

            console.print(table)

            # Benchmark breakdown
            if summary.by_benchmark:
                console.print("\n[bold]Results by Benchmark:[/bold]")
                bench_table = Table()
                bench_table.add_column("Benchmark")
                bench_table.add_column("Total")
                bench_table.add_column("Passed")
                bench_table.add_column("Score")

                for benchmark, stats in summary.by_benchmark.items():
                    bench_table.add_row(
                        benchmark,
                        str(stats["total"]),
                        str(stats["passed"]),
                        f"{stats['score']:.2%}"
                    )

                console.print(bench_table)

    except Exception as e:
        console.print(f"[red]Evaluation failed: {e}[/red]")
        if ctx.obj.get("debug"):
            raise
        raise typer.Exit(1)
