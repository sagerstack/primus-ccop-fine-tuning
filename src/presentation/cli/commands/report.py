"""
Report Command

CLI command for generating reports.
"""

import asyncio
from typing import Optional

import typer
from rich.console import Console

from application.ports.input.i_generate_report_use_case import ReportFormat

report_app = typer.Typer()
console = Console()


@report_app.command()
def generate(
    ctx: typer.Context,
    model: str = typer.Option(..., help="Model name"),
    format: str = typer.Option("json", help="Report format (json/markdown/html/csv)"),
    output: Optional[str] = typer.Option(None, help="Output file path"),
    details: bool = typer.Option(True, help="Include detailed results"),
) -> None:
    """Generate evaluation report."""
    container = ctx.obj["container"]
    use_case = container.generate_report_use_case()

    try:
        report_format = ReportFormat(format.lower())
    except ValueError:
        console.print(f"[red]Invalid format: {format}[/red]")
        console.print("Valid formats: json, markdown, html, csv")
        raise typer.Exit(1)

    console.print(f"[bold]Generating {format} report for:[/bold] {model}")

    try:
        result = asyncio.run(
            use_case.execute(
                model_name=model,
                format=report_format,
                output_path=output,
                include_details=details,
            )
        )

        if output:
            console.print(f"[green]✓[/green] Report saved to: {result}")
        else:
            console.print("\n[bold]Report:[/bold]")
            console.print(result)

    except Exception as e:
        console.print(f"[red]Report generation failed: {e}[/red]")
        if ctx.obj.get("debug"):
            raise
        raise typer.Exit(1)


@report_app.command()
def summary(
    ctx: typer.Context,
    model: str = typer.Option(..., help="Model name"),
) -> None:
    """Show evaluation summary."""
    container = ctx.obj["container"]
    use_case = container.generate_report_use_case()

    try:
        summary = asyncio.run(use_case.get_summary(model))

        console.print(f"\n[bold]Evaluation Summary: {model}[/bold]\n")
        console.print(f"Total Tests: {summary.total_tests}")
        console.print(f"Passed: {summary.passed_tests} ({summary.passed_tests/summary.total_tests*100:.1f}%)")
        console.print(f"Failed: {summary.failed_tests}")
        console.print(f"Overall Score: {summary.overall_score:.2%}")

    except Exception as e:
        console.print(f"[red]Failed to get summary: {e}[/red]")
        if ctx.obj.get("debug"):
            raise
        raise typer.Exit(1)
