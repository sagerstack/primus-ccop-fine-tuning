"""
CLI Main Entry Point

Typer-based CLI application for CCoP 2.0 evaluation framework.
"""

import typer
from rich.console import Console

from infrastructure.config.container import get_container
from presentation.cli.commands.evaluate import evaluate_app
from presentation.cli.commands.report import report_app
from presentation.cli.commands.setup import setup_app

# Create main Typer app
app = typer.Typer(
    name="ccop-eval",
    help="CCoP 2.0 Model Evaluation Framework",
    add_completion=False,
)

# Add subcommands
app.add_typer(setup_app, name="setup", help="Setup models for evaluation")
app.add_typer(evaluate_app, name="evaluate", help="Evaluate models on test cases")
app.add_typer(report_app, name="report", help="Generate evaluation reports")

console = Console()


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, help="Enable verbose output"),
    debug: bool = typer.Option(False, help="Enable debug mode"),
) -> None:
    """CCoP 2.0 Model Evaluation Framework."""
    # Initialize container
    container = get_container()

    # Store in context for commands to access
    ctx.obj = {"container": container, "verbose": verbose, "debug": debug}

    if debug:
        console.print("[yellow]Debug mode enabled[/yellow]")


if __name__ == "__main__":
    app()
