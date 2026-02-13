"""
RAG Query CLI Command

Command-line interface for querying CCoP compliance via RAG pipeline.
"""

import asyncio
import logging
import sys

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from infrastructure.config.container import get_container

# Create Typer app
query_app = typer.Typer(help="Query CCoP compliance information")

console = Console()

VALID_MODES = ["hybrid", "llm-only", "rag-only"]


@query_app.command(name="ask")
def query_command(
    question: str = typer.Argument(..., help="Question about CCoP compliance"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show metadata"),
    mode: str = typer.Option("hybrid", "--mode", "-m", help="Pipeline mode: hybrid, llm-only, rag-only"),
) -> None:
    """
    Query CCoP compliance information.

    Examples:
        ccop-eval query ask "What are the access control requirements?"
        ccop-eval query ask "What are the access control requirements?" --mode llm-only
        ccop-eval query ask "What are the access control requirements?" --mode rag-only
        ccop-eval query ask "How should CII organizations implement MFA?" --verbose
    """
    if mode not in VALID_MODES:
        console.print(f"[red]Invalid mode:[/red] {mode}. Must be one of: {', '.join(VALID_MODES)}")
        raise typer.Exit(code=1)

    # Configure Python logging for RAG pipeline nodes
    # Verbose: show all pipeline steps; Normal: show warnings only
    log_level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(name)s | %(message)s",
        stream=sys.stderr,
        force=True,
    )
    # Suppress noisy third-party loggers even in verbose mode
    for noisy in ("httpx", "httpcore", "urllib3", "databricks", "mlflow"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    asyncio.run(_execute_query(question, mode, verbose))


async def _execute_query(question: str, mode: str, verbose: bool) -> None:
    """Execute query and display formatted response."""
    try:
        container = get_container()
        use_case = container.query_compliance_use_case()

        spinner_label = {
            "hybrid": "Querying RAG pipeline...",
            "llm-only": "Querying LLM (no RAG)...",
            "rag-only": "Retrieving documents (no LLM)...",
        }

        with console.status(f"[bold green]{spinner_label.get(mode, 'Querying...')}"):
            response = await use_case.execute(question, mode)

        # Handle errors
        if response.error:
            console.print(
                Panel(
                    f"[red]Error:[/red] {response.error}",
                    title="Query Failed",
                    border_style="red",
                )
            )

            if "not available" in response.error or "not configured" in response.error:
                console.print("\n[yellow]Configuration Help:[/yellow]")
                if mode in ("hybrid", "rag-only"):
                    console.print("1. Ensure .env.local has Databricks settings:")
                    console.print("   - DATABRICKS_HOST")
                    console.print("   - DATABRICKS_TOKEN")
                    console.print("   - DATABRICKS_CATALOG")
                    console.print("   - DATABRICKS_SCHEMA")
                console.print("\n2. Ensure Ollama is running:")
                console.print("   - OLLAMA_HOST (default: http://localhost:11434)")

            return

        # Display response
        mode_label = {
            "hybrid": "Response",
            "llm-only": "Response (LLM-only, no RAG)",
            "rag-only": "Retrieved Documents (no LLM)",
        }
        console.print(f"\n[bold blue]{mode_label.get(mode, 'Response')}:[/bold blue]\n")
        console.print(Markdown(response.response))

        # Display metadata if verbose
        if verbose:
            console.print("\n[bold]Metadata:[/bold]")
            console.print(f"  Mode: {mode}")
            console.print(f"  RAG-augmented: {response.is_rag_augmented}")
            console.print(f"  Citations: {len(response.citations)}")
            console.print(f"  Retrieval attempts: {response.retrieval_attempts}")

            if response.grading_scores:
                avg_score = sum(response.grading_scores) / len(response.grading_scores)
                console.print(f"  Avg relevance score: {avg_score:.2f}")

            if response.citations:
                console.print("\n[bold]Citation Details:[/bold]")
                for idx, citation in enumerate(response.citations, start=1):
                    console.print(
                        f"  [{idx}] {citation.get('document', 'Unknown')} - "
                        f"{citation.get('section', 'N/A')} - "
                        f"Clause {citation.get('clause', 'N/A')}"
                    )

    except ValueError as e:
        console.print(f"[red]Invalid input:[/red] {e}")
        raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            raise
        raise typer.Exit(code=1)
