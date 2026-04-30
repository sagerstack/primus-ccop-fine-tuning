"""
RAG Query CLI Command

Command-line interface for querying CCoP compliance via RAG pipeline.

Output format mirrors `evaluate run` per-test-case panels (via shared renderer
in src/presentation/cli/formatters/) so query results and eval results are
structurally identical. The only difference: ground-truth-dependent metrics
(context_recall, factual_recall, semantic_similarity) are omitted because
ad-hoc queries have no expected_label to score against. The LLM Judge runs
in *universal* mode (hallucination + reasoning depth — both GT-free) so it
behaves the same as `evaluate run --judge-mode universal`.
"""

import asyncio
import logging
import sys
from datetime import datetime

import typer
from rich.console import Console

from domain.value_objects.run_id import RunId
from infrastructure.config.container import get_container

# NOTE: `from presentation.cli.formatters import build_per_result_panel` would
# create a circular import — presentation/__init__.py eagerly loads main.py
# which imports query.py back. Lazy-import the formatter inside the function.

# Create Typer app
query_app = typer.Typer(help="Query CCoP compliance information")

console = Console()

VALID_MODES = ["hybrid", "llm-only", "rag-only"]


@query_app.command(name="ask")
def query_command(
    question: str = typer.Argument(..., help="Question about CCoP compliance"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Raise pipeline log level to INFO (TOC filter, RRF ensemble, parent-merge diagnostics from rag.retrieval.* loggers).",
    ),
    verbose_io: bool = typer.Option(
        False, "--verbose-io",
        help="Show full system/user prompts and detailed retrieved contexts in the result panel. Same semantics as `evaluate run --verbose-io`.",
    ),
    mode: str = typer.Option("hybrid", "--mode", "-m", help="Pipeline mode: hybrid, llm-only, rag-only"),
    no_score: bool = typer.Option(False, "--no-score", help="Skip quality scoring (hybrid mode)"),
    no_judge: bool = typer.Option(
        False, "--no-judge",
        help="Skip the universal LLM judge (saves ~10-20s per query). Judge runs by default.",
    ),
) -> None:
    """
    Query CCoP compliance information.

    Examples:
        ccop-eval query ask "What are the access control requirements?"
        ccop-eval query ask "What are the access control requirements?" --mode llm-only
        ccop-eval query ask "What are the access control requirements?" --mode rag-only
        ccop-eval query ask "How should CII organizations implement MFA?" --verbose
        ccop-eval query ask "How should CII organizations implement MFA?" --verbose-io
    """
    if mode not in VALID_MODES:
        console.print(f"[red]Invalid mode:[/red] {mode}. Must be one of: {', '.join(VALID_MODES)}")
        raise typer.Exit(code=1)

    # Verbose log routing — surfaces rag.retrieval.* INFO-level diagnostics
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

    asyncio.run(_execute_query(question, mode, verbose, verbose_io, no_score, no_judge))


async def _execute_query(
    question: str,
    mode: str,
    verbose: bool,
    verbose_io: bool,
    no_score: bool = False,
    no_judge: bool = False,
) -> None:
    """Execute query and display formatted Rich Panel result (matches evaluate run format)."""
    # Lazy import to avoid circular import chain via presentation/__init__.py
    from presentation.cli.formatters import build_per_result_panel

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

        # Handle errors with the original red-panel UX
        if response.error:
            from rich.panel import Panel
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

        # Compute GT-free RAGAs scores (hybrid mode, when retrieved contexts present)
        ragas_eval = None
        ragas_error_msg = None
        if mode == "hybrid" and not no_score and response.retrieved_contexts:
            try:
                ragas_service = container.ragas_service()
                if ragas_service is not None:
                    with console.status("[bold green]Computing quality scores..."):
                        ragas_eval = ragas_service.evaluate_response(
                            question=response.query,
                            response=response.response,
                            reference="",
                            retrieved_contexts=response.retrieved_contexts,
                            key_facts=None,
                        )
                    if ragas_eval and ragas_eval.evaluation_error:
                        ragas_error_msg = ragas_eval.error_message
                        ragas_eval = None
            except Exception as e:
                ragas_error_msg = str(e)
                logging.getLogger(__name__).warning(f"Quality scoring failed: {e}")

        # Map RAGAs metrics by name for quick lookup
        ragas_by_name = {}
        if ragas_eval is not None and not ragas_eval.evaluation_error:
            for m in ragas_eval.metrics:
                if m.applicable:
                    ragas_by_name[m.name] = m.score

        def _ragas(name):
            return ragas_by_name.get(name)

        # Universal LLM Judge (GT-free: hallucination + reasoning depth).
        # Mirrors `evaluate run --judge-mode universal`. Skipped when:
        #   * --no-judge passed
        #   * llm-only mode (no contexts) → still useful for hallucination but
        #     skipped for now to keep the no-RAG path fast
        #   * rag-only mode (no model response to judge)
        judge_eval = None
        judge_error_msg = None
        if (
            not no_judge
            and mode == "hybrid"
            and response.response
            and response.retrieved_contexts
        ):
            try:
                from domain.services.llm_judge_service import LLMJudgeService
                judge_service = LLMJudgeService()
                with console.status("[bold green]Running universal judge..."):
                    judge_eval = judge_service.universal_evaluate_raw(
                        question=response.query,
                        response_content=response.raw_response or response.response,
                        retrieved_contexts=response.retrieved_contexts,
                        label=f"query-{ts.isoformat()}",
                    )
                if judge_eval and judge_eval.judge_error:
                    judge_error_msg = judge_eval.error_message
                    judge_eval = None
            except Exception as e:
                judge_error_msg = str(e)
                logging.getLogger(__name__).warning(f"Universal judge failed: {e}")

        # GT-free metrics actually displayed in the panel — used for both
        # the title's RAGAs score and the Overall Quality Summary table so
        # that what the user sees and what the title averages are identical.
        # Pre-2026-04-27 bug: title averaged ALL 6 RAGAs metrics, including
        # GT-dependent ones (context_recall, factual_recall, semantic_similarity)
        # that compute to ~0 with empty reference and dragged the title down.
        # Note: context_precision was initially listed here but observed to
        # return 0.00 even with bullseye-relevant chunks; it actually requires
        # a reference (passing empty string makes RAGAs's LLM judge return 0).
        # Removed from query mode 2026-04-27.
        DISPLAYED_RAGAS_METRICS = [
            "context_faithfulness",
            "answer_relevancy",
        ]
        displayed_scores = {
            name: _ragas(name)
            for name in DISPLAYED_RAGAS_METRICS
            if _ragas(name) is not None
        }
        ragas_summary = (
            sum(displayed_scores.values()) / len(displayed_scores)
            if displayed_scores
            else None
        )

        run_id = RunId(mode=mode, scope="query", timestamp=ts)
        ragas_str = f"{ragas_summary:.2f}" if ragas_summary is not None else "N/A"
        judge_str = (
            f" | Judge: {judge_eval.overall_score:.2f}"
            if judge_eval is not None else ""
        )
        title = f"query-{run_id.value} | ad-hoc | {mode.upper()} | RAGAs: {ragas_str}{judge_str}"

        # Build the "Retrieved Citations" display directly from the RAG
        # retrieval output (top-N chunks fed to the model as context). This
        # is intentionally separate from response.citations, which under the
        # <Sources>-based design reflects what the MODEL declared it relied
        # on — a possibly-different list. Panel header = retrieved set;
        # response body's <Sources> block = model-declared subset.
        retrieved_cids = []
        for ctx in (response.retrieved_contexts_detailed or []):
            doc = ctx.get("document", "?") or "?"
            clause = (ctx.get("clause") or "").strip()
            section = (ctx.get("section") or "").strip()
            cid = ctx.get("citation_id") or ""
            if cid:
                primary = cid
            elif clause:
                primary = f"{doc}::{clause}"
            elif section:
                primary = f"{doc}::{section}"
            else:
                primary = doc

            # Surface parent-child merged siblings (set by reranking.py when merge fires)
            members = (ctx.get("metadata") or {}).get("merged_member_citation_ids") or []
            other_members = [m for m in members if m and m != primary]
            if other_members:
                primary = f"{primary} (+{len(other_members)} merged: {', '.join(other_members)})"
            retrieved_cids.append(primary)

        panel = build_per_result_panel(
            title=title,
            border_style="cyan",
            question=response.query,
            response=response.response,
            evaluation_mode=mode,
            chunk_count=len(response.retrieved_contexts) if response.retrieved_contexts else None,
            retrieved_citations=retrieved_cids if retrieved_cids else None,
            # Verbose I/O
            system_prompt=response.system_prompt if verbose_io else None,
            user_prompt=response.user_prompt if verbose_io else None,
            retrieved_contexts_detailed=(
                response.retrieved_contexts_detailed if verbose_io else None
            ),
            prompt_tokens=response.prompt_tokens or 0,
            completion_tokens=response.completion_tokens or 0,
            total_tokens=response.total_tokens or 0,
            latency_ms=response.latency_ms or 0,
            # RAGAs — only GT-FREE metrics are populated; rest stay None and the
            # renderer skips them. We deliberately omit the GT-dependent ones
            # (context_recall, context_precision, factual_recall, semantic_similarity)
            # because they require expected_label / reference to be meaningful;
            # without it RAGAs's internal LLM judge returns 0 across the board.
            ragas_context_faithfulness=_ragas("context_faithfulness"),
            ragas_answer_relevancy=_ragas("answer_relevancy"),
            ragas_error=ragas_error_msg,
            ragas_is_rag_response=response.is_rag_augmented,
            # Universal LLM Judge (GT-free) — populates the same panel rows as
            # `evaluate run --judge-mode universal`.
            universal_judge_overall=(
                judge_eval.overall_score if judge_eval is not None else None
            ),
            reasoning_criteria_met=(
                judge_eval.reasoning_criteria_met if judge_eval is not None else None
            ),
            hallucination_detected=(
                judge_eval.hallucination_detected if judge_eval is not None else None
            ),
            unsupported_count=(
                judge_eval.unsupported_count if judge_eval is not None else None
            ),
            contradicted_count=(
                judge_eval.contradicted_count if judge_eval is not None else None
            ),
            claims_count=(
                len(judge_eval.claims) if judge_eval is not None and judge_eval.claims else 0
            ),
            judge_error=bool(judge_error_msg),
            show_judge=True,
            show_gt_comparisons=False,
            verbose_io=verbose_io,
        )
        console.print(panel)

        # ── Query Complete banner + Overall Quality Summary table ─────────
        # Mirrors `evaluate run` output structure for visual parity.
        from rich.table import Table

        settings = container.config()
        duration_s = (datetime.utcnow() - ts).total_seconds()

        console.print("\n[bold green]Query Complete![/bold green]\n")
        console.print(f"[bold]Model:[/bold] {settings.model_name}")
        console.print(f"[bold]Duration:[/bold] {duration_s:.1f}s")
        console.print(f"[bold]Mode:[/bold] {mode}\n")

        # Color helper matching evaluate.py
        def _fmt(value):
            if value is None:
                return "[dim]N/A[/dim]"
            if value >= 0.7:
                return f"[green]{value:.2f}[/green]"
            if value >= 0.4:
                return f"[yellow]{value:.2f}[/yellow]"
            return f"[red]{value:.2f}[/red]"

        # Build the parent-child table over GT-free metric groups only.
        # GT-dependent rows (context_recall, factual_recall, semantic_similarity,
        # LLM Judge) are intentionally excluded — there is no expected_label for
        # an ad-hoc query.
        summary_table = Table(title="Overall Quality Summary", show_header=True)
        summary_table.add_column("Quality Group / Metric", style="cyan", no_wrap=True)
        summary_table.add_column("Score", justify="center", style="bold")

        cf = displayed_scores.get("context_faithfulness")
        ar = displayed_scores.get("answer_relevancy")

        # NOTE: "Retrieval Quality" group is intentionally omitted in query mode.
        # It contains context_recall + context_precision, both of which need a
        # reference answer to be meaningful. Ad-hoc queries have no GT, so this
        # group has nothing to display.

        # Group: Model-RAG Grounding (context_faithfulness — GT-free)
        summary_table.add_row("[bold]Model-RAG Grounding[/bold]", _fmt(cf))
        summary_table.add_row("  RAGAs: context_faithfulness", _fmt(cf))
        summary_table.add_section()

        # Group: Model Response Quality (answer_relevancy + universal judge —
        # both GT-free). Judge row mirrors the structure of `evaluate run
        # --judge-mode universal`. Group header score is the simple mean of
        # whichever sub-rows are populated.
        judge_overall_q = judge_eval.overall_score if judge_eval is not None else None
        rq_subscores = [s for s in (ar, judge_overall_q) if s is not None]
        rq_group = sum(rq_subscores) / len(rq_subscores) if rq_subscores else None

        summary_table.add_row("[bold]Model Response Quality[/bold]", _fmt(rq_group))
        summary_table.add_row("  RAGAs: answer_relevancy", _fmt(ar))
        if judge_eval is not None:
            summary_table.add_row("  LLM Judge (Universal): overall", _fmt(judge_overall_q))
            halluc_label = (
                "[red]YES[/red]" if judge_eval.hallucination_detected else "[green]NO[/green]"
            )
            summary_table.add_row("    hallucination_detected", halluc_label)
        elif judge_error_msg:
            summary_table.add_row(
                "  LLM Judge (Universal)", "[yellow]⚠ error[/yellow]"
            )
        elif no_judge:
            summary_table.add_row("  LLM Judge (Universal)", "[dim]skipped[/dim]")
        summary_table.add_section()

        summary_table.add_row("[bold]RAGAs Score[/bold]", _fmt(ragas_summary))
        if judge_eval is not None:
            summary_table.add_row("[bold]Judge Score[/bold]", _fmt(judge_overall_q))

        if displayed_scores or ragas_error_msg or judge_eval is not None:
            console.print(summary_table)
            if ragas_error_msg:
                console.print(f"\n[yellow]⚠ RAGAs error: {ragas_error_msg}[/yellow]")
            if judge_error_msg:
                console.print(f"\n[yellow]⚠ Judge error: {judge_error_msg}[/yellow]")
        elif mode != "hybrid":
            console.print(
                f"[dim]Quality scoring not applicable for mode={mode}[/dim]"
            )
        elif no_score:
            console.print("[dim]Quality scoring skipped (--no-score)[/dim]")
        else:
            console.print("[dim]No quality scores available[/dim]")

        console.print(f"\n[dim]Run ID: {run_id.value}[/dim]")

        # Persist query as auditable artifact (scope=query, schema v6)
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
                "judge_mode": "universal" if judge_eval is not None else None,
                "judge_overall_score": (
                    judge_eval.overall_score if judge_eval is not None else None
                ),
                "hallucination_detected": (
                    judge_eval.hallucination_detected if judge_eval is not None else None
                ),
                "unsupported_count": (
                    judge_eval.unsupported_count if judge_eval is not None else None
                ),
                "contradicted_count": (
                    judge_eval.contradicted_count if judge_eval is not None else None
                ),
                "claims": judge_eval.claims if judge_eval is not None else None,
                "reasoning_criteria_met": (
                    judge_eval.reasoning_criteria_met if judge_eval is not None else None
                ),
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

    except ValueError as e:
        console.print(f"[red]Invalid input:[/red] {e}")
        raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            raise
        raise typer.Exit(code=1)
