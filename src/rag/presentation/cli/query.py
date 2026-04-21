"""
RAG Query CLI Command

Command-line interface for querying CCoP compliance via RAG pipeline.
"""

import asyncio
import logging
import sys
from datetime import datetime

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from domain.value_objects.run_id import RunId
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
    no_score: bool = typer.Option(False, "--no-score", help="Skip quality scoring (hybrid mode)"),
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

    asyncio.run(_execute_query(question, mode, verbose, no_score))


async def _execute_query(question: str, mode: str, verbose: bool, no_score: bool = False) -> None:
    """Execute query and display formatted response."""
    try:
        container = get_container()
        use_case = container.query_compliance_use_case()

        spinner_label = {
            "hybrid": "Querying RAG pipeline...",
            "llm-only": "Querying LLM (no RAG)...",
            "rag-only": "Retrieving documents (no LLM)...",
        }

        ts = datetime.utcnow()
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
        console.print(f"\n[bold yellow]Question:[/bold yellow] {response.query}\n")
        console.print(f"[bold blue]{mode_label.get(mode, 'Response')}:[/bold blue]\n")
        console.print(Markdown(response.response))

        # Quality scoring (hybrid mode only, requires retrieved contexts)
        if mode == "hybrid" and not no_score and response.retrieved_contexts:
            try:
                ragas_service = container.ragas_service()
                if ragas_service is not None:
                    with console.status("[bold green]Computing quality scores..."):
                        from domain.value_objects.quality_group import QualityGroup
                        ragas_eval = ragas_service.evaluate_response(
                            question=response.query,
                            response=response.response,
                            reference="",
                            retrieved_contexts=response.retrieved_contexts,
                            key_facts=None,
                        )

                    if not ragas_eval.evaluation_error:
                        console.print("\n[bold]Quality Scores:[/bold]")
                        for metric in ragas_eval.metrics:
                            if metric.name in ["context_faithfulness", "answer_relevancy"] and metric.applicable:
                                display_name = QualityGroup.get_display_name(metric.name)
                                if metric.score >= 0.7:
                                    score_str = f"[green]{metric.score:.2f}[/green]"
                                elif metric.score >= 0.4:
                                    score_str = f"[yellow]{metric.score:.2f}[/yellow]"
                                else:
                                    score_str = f"[red]{metric.score:.2f}[/red]"
                                console.print(f"  {display_name}: {score_str}")
                    else:
                        if verbose:
                            console.print(f"\n[yellow]Quality scoring failed: {ragas_eval.error_message}[/yellow]")
            except Exception as e:
                if verbose:
                    console.print(f"\n[yellow]Quality scoring error: {e}[/yellow]")
                logging.getLogger(__name__).warning(f"Quality scoring failed: {e}")

        # Persist query as auditable artifact (scope=query, schema v6)
        run_id = RunId(mode=mode, scope="query", timestamp=ts)
        console.print(f"\n[dim]Run ID: {run_id.value}[/dim]")

        try:
            query_test_id = f"query-{run_id.value}"
            test_results = [{
                "test_id": query_test_id,
                "question": question,
                "response": response.response,
                "raw_response": response.raw_response,
                "is_rag_augmented": response.is_rag_augmented,
                "citations": response.citations,
                "system_prompt": response.system_prompt,
                "user_prompt": response.user_prompt,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "total_tokens": response.total_tokens,
                "latency_ms": response.latency_ms,
                "evaluation_mode": mode,
                "evaluated_at": ts.isoformat(),
            }]
            contexts_by_test_id = {}
            if response.retrieved_contexts_detailed:
                contexts_by_test_id[query_test_id] = response.retrieved_contexts_detailed

            settings = container.config()
            metadata = {
                "run_id": run_id.value,
                "schema_version": 6,
                "model_name": settings.model_name,
                "evaluation_mode": mode,
                "evaluated_at": ts.isoformat(),
                "question": question,
                "is_rag_augmented": response.is_rag_augmented,
            }

            repo = container.result_repository()
            await repo.save_query_run(
                metadata=metadata,
                test_results=test_results,
                contexts_by_test_id=contexts_by_test_id or None,
            )
        except Exception as persist_err:
            logging.getLogger(__name__).warning(f"Query persistence failed (non-fatal): {persist_err}")

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
