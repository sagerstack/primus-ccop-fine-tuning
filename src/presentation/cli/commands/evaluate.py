"""
Evaluate Command

CLI command for evaluating models.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from application.dtos.evaluation_request_dto import EvaluationRequestDTO
from domain.value_objects.evaluation_tier import EvaluationTier
from domain.value_objects.quality_group import QualityGroup
from domain.value_objects.run_id import RunId
from presentation.cli.formatters import build_per_result_panel

evaluate_app = typer.Typer()
console = Console()

VALID_EVAL_MODES = ["hybrid", "llm-only", "graphrag", "graphrag-ontology"]


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
    temperature: Optional[float] = typer.Option(None, help="Temperature override (default from CCOP_DEFAULT_TEMPERATURE)"),
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
        help="Evaluation mode: hybrid (RAG-augmented), llm-only, graphrag (emergent-KG graph retrieval -> primus generation, scored), or graphrag-ontology (Phase 10 ontology-grounded graph retrieval -> primus generation, scored; no retrieval-only mode on evaluate)"
    ),
    judge_mode: str = typer.Option(
        "rubric",
        "--judge-mode",
        help="Judge mode: rubric (per-benchmark rubrics) or universal (reasoning depth + hallucination)"
    ),
    verbose_io: bool = typer.Option(
        False,
        "--verbose-io",
        help="Show captured system/user prompts and retrieved contexts per test case"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Raise pipeline log level to INFO (surfaces TOC filter, RRF ensemble, parent-merge diagnostics from rag.retrieval.* loggers). Same semantics as `query ask --verbose`."
    ),
    resume: bool = typer.Option(
        False,
        "--resume",
        help=(
            "Resume from a prior partial run with the same (mode, scope, model). "
            "Skips already-completed test cases. Bails out if judge_config or "
            "model has drifted vs the partial file."
        ),
    ),
) -> None:
    """Run model evaluation."""
    from infrastructure.config.settings import get_settings

    # Verbose log routing — match `query ask --verbose` behaviour so rag.retrieval.*
    # diagnostics (TOC filter, RRF ensemble, parent-merge) surface in eval runs too.
    if verbose:
        logging.basicConfig(
            level=logging.INFO,
            format="%(name)s | %(message)s",
            stream=sys.stderr,
            force=True,
        )
        # Suppress noisy third-party loggers
        for noisy in ("httpx", "httpcore", "urllib3", "databricks", "mlflow"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    container = ctx.obj["container"]
    use_case = container.evaluate_model_use_case()

    # Resolve temperature from settings if not provided via CLI
    if temperature is None:
        temperature = get_settings().default_temperature

    # Validate mode parameter
    if mode not in VALID_EVAL_MODES:
        console.print(f"[red]Invalid mode: {mode}. Must be one of: {', '.join(VALID_EVAL_MODES)}[/red]")
        raise typer.Exit(1)

    # Validate judge_mode parameter
    if judge_mode not in ["rubric", "universal"]:
        console.print(f"[red]Invalid judge_mode: {judge_mode}. Must be 'rubric' or 'universal'.[/red]")
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
            # Fallback: use B1-B24 as default (excluding any deprecated)
            benchmarks = [f"B{i}" for i in range(1, 25)]

    console.print(f"[bold]Evaluating model:[/bold] {model}")
    console.print(f"[bold]Benchmarks:[/bold] {', '.join(benchmarks)}")
    console.print(f"[bold]Evaluation Phase:[/bold] {phase}")
    console.print(f"[bold]Evaluation Mode:[/bold] {mode}")
    console.print(f"[bold]Judge Mode:[/bold] {judge_mode}")

    # Display threshold being used
    if threshold is not None:
        console.print(f"[bold]Pass Threshold:[/bold] {threshold:.0%} (override)")
    else:
        phase_thresholds = {"baseline": 0.15, "finetuned": 0.50, "deployment": 0.85}
        default_threshold = phase_thresholds.get(phase, 0.70)
        console.print(f"[bold]Pass Threshold:[/bold] {default_threshold:.0%} (phase default)")

    # Generate RunId — encodes scope deterministically before executing
    total_benchmarks_available = len(benchmarks)
    scope = RunId.build_scope(
        tier=tier,
        benchmarks=benchmarks if tier is None else None,
        test_ids=test_ids,
        total_benchmarks_available=total_benchmarks_available,
    )
    run_id = RunId(mode=mode, scope=scope, timestamp=datetime.utcnow())
    console.print(f"[bold]Run ID:[/bold] {run_id.value}")

    request = EvaluationRequestDTO(
        model_name=model,
        benchmark_types=benchmarks,
        test_case_ids=test_ids,
        temperature=temperature,
        save_results=save,
        evaluation_phase=phase,
        pass_threshold=threshold,
        evaluation_mode=mode,
        judge_mode=judge_mode,
        run_id=run_id.value,
        resume=resume,
    )

    try:
        console.print("\n[yellow]Running evaluation...[/yellow]\n")
        summary = asyncio.run(use_case.execute(request))

        # Load sidecar for verbose-io display
        sidecar: dict = {}
        if verbose_io:
            from infrastructure.config.settings import get_settings
            results_dir = Path(get_settings().results_dir)
            month_dir = results_dir / datetime.utcnow().strftime("%Y-%m")
            sidecar_path = month_dir / f"{run_id.value}-contexts.json"
            if sidecar_path.exists():
                with open(sidecar_path) as _f:
                    sidecar = json.load(_f)

        # Per-test-case detail output — uses shared renderer (presentation.cli.formatters)
        # so that `query ask` produces an equivalent panel for ad-hoc queries.
        console.print("\n[bold]Per-Test-Case Results[/bold]\n")
        for r in summary.results:
            score_str = f"{r.overall_score:.2f}" if r.overall_score is not None else "N/A"
            ragas_str = f"{r.ragas_score:.2f}" if r.ragas_score is not None else "N/A"
            mode_suffix = f" | {r.evaluation_mode}" if r.evaluation_mode else ""
            title = (
                f"{r.test_id} | {r.benchmark_type} | "
                f"{'PASS' if r.passed else 'FAIL'} | Bench: {score_str} | RAGAs: {ragas_str}"
                f"{mode_suffix}"
            )
            border_style = "green" if r.passed else "red"

            # Extract metrics from DTO into the formatter's named inputs
            ragas_by_name = {rm.name: rm for rm in (r.ragas_metrics or []) if rm.applicable}

            def _ragas(name):
                rm = ragas_by_name.get(name)
                return rm.score if rm is not None else None

            # Judge dimensions (rubric mode): exclude judge_error, universal_judge,
            # and any sentinel metrics (names starting with "_" are metadata, not
            # score dimensions — e.g. _judge_raw which carries the raw judge JSON).
            judge_dims = [
                {"name": m.name, "value": m.value, "weight": m.weight}
                for m in r.metrics
                if m.name not in ("judge_error", "universal_judge")
                and not m.name.startswith("_")
            ]
            has_judge_error = any(m.name == "judge_error" for m in r.metrics)
            has_universal_judge = any(m.name == "universal_judge" for m in r.metrics)

            # Universal-judge specific fields (Path B)
            universal_overall = (
                r.overall_score if (has_universal_judge and r.judge_mode == "universal") else None
            )
            claims_count = len(r.claims) if getattr(r, "claims", None) else 0

            # Verbose I/O: pull retrieved-contexts from sidecar (loaded above)
            test_sidecar_ctx = sidecar.get(r.test_id) if verbose_io else None

            panel = build_per_result_panel(
                title=title,
                border_style=border_style,
                question=r.question,
                response=r.response_content,
                evaluation_mode=r.evaluation_mode,
                chunk_count=r.chunk_count,
                retrieved_citations=r.retrieved_chunk_ids,
                # Verbose I/O
                system_prompt=getattr(r, "system_prompt", None),
                user_prompt=getattr(r, "user_prompt", None),
                retrieved_contexts_detailed=test_sidecar_ctx,
                prompt_tokens=getattr(r, "prompt_tokens", 0) or 0,
                completion_tokens=getattr(r, "completion_tokens", 0) or 0,
                total_tokens=getattr(r, "total_tokens", 0) or 0,
                tokens_used_legacy=r.tokens_used,
                latency_ms=r.latency_ms,
                # RAGAs metrics (None if not applicable / not present)
                ragas_context_recall=_ragas("context_recall"),
                ragas_context_precision=_ragas("context_precision"),
                ragas_context_faithfulness=_ragas("context_faithfulness"),
                ragas_factual_recall=_ragas("factual_recall"),
                ragas_answer_relevancy=_ragas("answer_relevancy"),
                ragas_semantic_similarity=_ragas("semantic_similarity"),
                ragas_error=r.ragas_error,
                ragas_is_rag_response=r.ragas_is_rag_response,
                # Judge — rubric or universal
                judge_dimensions=judge_dims if not has_universal_judge else None,
                judge_overall=r.overall_score,
                judge_error=has_judge_error,
                universal_judge_overall=universal_overall,
                reasoning_criteria_met=r.reasoning_criteria_met,
                hallucination_detected=r.hallucination_detected,
                unsupported_count=r.unsupported_count,
                contradicted_count=r.contradicted_count,
                claims_count=claims_count,
                # Mode flags — eval has GT, so show everything
                show_judge=True,
                show_gt_comparisons=True,
                verbose_io=verbose_io,
            )
            console.print(panel)

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

            # Overall Quality Summary table (parent-child layout)
            overall_table = Table(title="Overall Quality Summary", show_header=True)
            overall_table.add_column("Quality Group / Metric", style="cyan", no_wrap=True)
            overall_table.add_column("Score", justify="center", style="bold")

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

            overall_groups = summary.quality_categories.get("overall", {}).get("groups", [])

            for group_data in overall_groups:
                group_name = group_data["name"]
                group_avg = group_data["average"]

                # Parent row (quality group)
                overall_table.add_row(
                    f"[bold]{group_name}[/bold]",
                    format_metric(group_avg)
                )

                # Child rows (individual metrics) - indented
                for metric_data in group_data["metrics"]:
                    metric_name = metric_data["name"]
                    metric_value = metric_data["value"]
                    overall_table.add_row(
                        f"  {metric_name}",
                        format_metric(metric_value)
                    )

                # Visual separator between groups
                overall_table.add_section()

            # Overall score rows (triple)
            overall_table.add_row(
                "[bold]Benchmark Score[/bold]",
                f"[bold]{format_metric(summary.overall_score)}[/bold]"
            )
            overall_table.add_row(
                "[bold]RAGAs Score[/bold]",
                f"[bold]{format_metric(summary.ragas_overall_score)}[/bold]"
            )

            console.print(overall_table)

            # Per-Benchmark Quality Breakdown
            if summary.by_benchmark:
                console.print("\n[bold]Quality Breakdown by Benchmark:[/bold]\n")

                by_benchmark_data = summary.quality_categories.get("by_benchmark", {})

                # Quality group legend
                console.print(
                    "  [yellow]■ Retrieval Quality[/yellow]  "
                    "[magenta]■ Model-RAG Grounding[/magenta]  "
                    "[cyan]■ Model Response Quality[/cyan]\n"
                )

                # Flat benchmark table with columns in information flow order
                bench_table = Table(title="Quality Breakdown by Benchmark", show_header=True)
                bench_table.add_column("Benchmark", style="cyan", no_wrap=True)

                # Columns: Yellow = Retrieval | Magenta = Grounding | Cyan = Response
                bench_table.add_column("ctx_recall", justify="center", header_style="yellow")
                bench_table.add_column("ctx_precision", justify="center", header_style="yellow")
                bench_table.add_column("ctx_faith", justify="center", header_style="magenta")
                bench_table.add_column("fct_recl", justify="center", header_style="cyan")
                bench_table.add_column("ans_relev", justify="center", header_style="cyan")
                bench_table.add_column("sem_sim", justify="center", header_style="cyan")
                bench_table.add_column("LLM Judge", justify="center", header_style="cyan")

                # Sort benchmarks (B1, B2, ..., B21) — extract short name for sorting
                def _bench_sort_key(full_name: str) -> int:
                    short = full_name.split("_")[0]
                    num = short[1:] if short.startswith("B") else short
                    return int(num) if num.isdigit() else 0

                sorted_benchmarks = sorted(summary.by_benchmark.keys(), key=_bench_sort_key)

                for benchmark in sorted_benchmarks:
                    short_name = benchmark.split("_")[0]
                    bench_label = benchmark.replace("_", " ").replace(short_name + " ", "")
                    display_name = f"{short_name}: {bench_label}" if bench_label else short_name

                    bench_groups = by_benchmark_data.get(short_name, {}).get("groups", [])

                    # Extract all metrics across groups into flat dict
                    metrics_flat = {}
                    for group_data in bench_groups:
                        for metric_data in group_data["metrics"]:
                            metrics_flat[metric_data["name"]] = metric_data["value"]

                    bench_table.add_row(
                        display_name,
                        format_metric(metrics_flat.get("RAGAs: context_recall")),
                        format_metric(metrics_flat.get("RAGAs: context_precision")),
                        format_metric(metrics_flat.get("RAGAs: context_faithfulness")),
                        format_metric(metrics_flat.get("RAGAs: factual_recall")),
                        format_metric(metrics_flat.get("RAGAs: answer_relevancy")),
                        format_metric(metrics_flat.get("RAGAs: semantic_similarity")),
                        format_metric(metrics_flat.get("LLM Judge")),
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


@evaluate_app.command()
def rescore(
    ctx: typer.Context,
    source_run_id: str = typer.Option(
        ...,
        "--source-run-id",
        help=(
            "Run ID of the source evaluation to rescore (format: "
            "eval-run-{mode}-{scope}-{yyyyMMdd}-{HHmm}, no model suffix). "
            "Loads frozen Primus responses + retrieved contexts and re-runs "
            "the LLM judge without re-running model inference."
        ),
    ),
    judge_mode: str = typer.Option(
        "rubric",
        "--judge-mode",
        help="Judge mode: rubric (universal 5-dim) or universal (hallucination + reasoning)",
    ),
    save: bool = typer.Option(True, "--save/--no-save", help="Save rescored results"),
    resume: bool = typer.Option(
        False,
        "--resume",
        help="Resume from a prior partial rescore run with the same source",
    ),
) -> None:
    """Re-run the LLM judge on a prior run's frozen responses (no Primus inference)."""
    from infrastructure.config.settings import get_settings
    from application.use_cases.rescore_evaluation import RescoreEvaluationUseCase

    if judge_mode not in ["rubric", "universal"]:
        console.print(
            f"[red]Invalid judge_mode: {judge_mode}. Must be 'rubric' or 'universal'.[/red]"
        )
        raise typer.Exit(1)

    container = ctx.obj["container"]
    settings = get_settings()

    use_case = RescoreEvaluationUseCase(
        test_case_repository=container.test_case_repository(),
        result_repository=container.result_repository(),
        results_dir=Path(settings.results_dir),
        logger=container.logger(),
    )

    console.print(f"[bold]Source run:[/bold] {source_run_id}")
    console.print(f"[bold]Judge mode:[/bold] {judge_mode}")
    console.print(f"[bold]Resume:[/bold] {resume}")

    try:
        console.print("\n[yellow]Rescoring frozen responses...[/yellow]\n")
        summary = asyncio.run(
            use_case.execute(
                source_run_id=source_run_id,
                judge_mode=judge_mode,
                save_results=save,
                resume=resume,
            )
        )

        console.print("\n[green]Rescore complete[/green]")
        console.print(f"  Total cases: {summary.total_tests}")
        console.print(f"  Passed:      {summary.passed_tests}")
        console.print(f"  Failed:      {summary.failed_tests}")
        console.print(f"  Overall:     {summary.overall_score:.2%}")

    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Rescore failed: {e}[/red]")
        if ctx.obj.get("debug"):
            raise
        raise typer.Exit(1)
