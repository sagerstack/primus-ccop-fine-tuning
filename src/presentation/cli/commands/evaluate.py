"""
Evaluate Command

CLI command for evaluating models.
"""

import asyncio
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from application.dtos.evaluation_request_dto import EvaluationRequestDTO
from domain.value_objects.evaluation_tier import EvaluationTier

evaluate_app = typer.Typer()
console = Console()


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
) -> None:
    """Run model evaluation."""
    container = ctx.obj["container"]
    use_case = container.evaluate_model_use_case()

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
    )

    try:
        console.print("\n[yellow]Running evaluation...[/yellow]\n")
        summary = asyncio.run(use_case.execute(request))

        # Display results
        console.print("\n[bold green]Evaluation Complete![/bold green]\n")

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
