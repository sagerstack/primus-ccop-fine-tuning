"""
Setup Command

CLI command for setting up models.
"""

import asyncio

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from application.ports.output.i_model_converter import QuantizationType

setup_app = typer.Typer()
console = Console()


@setup_app.command()
def model(
    ctx: typer.Context,
    hf_repo: str = typer.Option(
        "trendmicro-ailab/Llama-Primus-Reasoning", help="HuggingFace repository"
    ),
    model_name: str = typer.Option(
        "primus-reasoning", help="Model name for Ollama"
    ),
    quantization: str = typer.Option(
        "Q5_K_M", help="Quantization type (Q4_K_M, Q5_K_M, Q6_K, Q8_0)"
    ),
    force: bool = typer.Option(
        False, help="Force reconversion"
    ),
) -> None:
    """Set up model for evaluation."""
    container = ctx.obj["container"]
    use_case = container.setup_model_use_case()

    console.print(f"[bold]Setting up model:[/bold] {hf_repo}")
    console.print(f"[bold]Model name:[/bold] {model_name}")
    console.print(f"[bold]Quantization:[/bold] {quantization}")

    try:
        quant_type = QuantizationType(quantization)
    except ValueError:
        console.print(f"[red]Invalid quantization: {quantization}[/red]")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Setting up model...", total=None)

        result = asyncio.run(
            use_case.execute(
                hf_model_repo=hf_repo,
                model_name=model_name,
                quantization=quant_type,
                force_reconvert=force,
            )
        )

        progress.update(task, completed=True)

    if result["status"] == "success":
        console.print(f"[green]✓[/green] {result['message']}")
    else:
        console.print(f"[red]✗ Setup failed[/red]")
        raise typer.Exit(1)


@setup_app.command()
def check(ctx: typer.Context) -> None:
    """Check prerequisites (Ollama, etc.)."""
    container = ctx.obj["container"]
    use_case = container.setup_model_use_case()

    console.print("[bold]Checking prerequisites...[/bold]")

    checks = asyncio.run(use_case.check_prerequisites())

    if checks.get("ollama_running"):
        console.print(f"[green]✓[/green] Ollama is running")
        console.print(f"  Models: {checks.get('ollama_models_count', 0)}")
    else:
        console.print("[red]✗[/red] Ollama is not running")
        if "error" in checks:
            console.print(f"  Error: {checks['error']}")
        console.print("\n[yellow]Please install and start Ollama:[/yellow]")
        console.print("  Run: ./scripts/setup_ollama.sh")
