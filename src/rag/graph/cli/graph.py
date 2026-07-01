"""
GraphRAG CLI Commands

`ccop-eval graph build` constructs the emergent CCoP knowledge graph in Neo4j
as a first-class, repeatable command (D-17) — not a throwaway spike.
"""

import asyncio
import logging

import neo4j
import typer
from rich.console import Console
from rich.table import Table

from infrastructure.config.settings import get_settings
from rag.graph.build.corpus_source import DEFAULT_CCOP_DIR, load_ccop_corpus_texts
from rag.graph.build.kg_builder import BuildStats, EmergentKGBuilder

graph_app = typer.Typer(help="Build and inspect the GraphRAG knowledge graph")

console = Console()
logger = logging.getLogger(__name__)


@graph_app.command(name="build")
def build_command(
    ccop_dir: str = typer.Option(
        DEFAULT_CCOP_DIR,
        "--ccop-dir",
        help="Path to the ccop-official directory containing CCoP PDFs",
    ),
    drop: bool = typer.Option(
        False,
        "--drop/--no-drop",
        help=(
            "Wipe the existing graph before building (clean rebuild for "
            "iteration, D-19). Default: off — the destructive path is "
            "explicit opt-in."
        ),
    ),
) -> None:
    """
    Build the emergent CCoP knowledge graph in Neo4j.

    Extraction = openai/gpt-4o-mini via OpenRouter (D-06a). Embeddings =
    BAAI/bge-large-en-v1.5, in-process (D-07). NO schema constraint — this is
    the un-governed emergent baseline (D-03/D-08). Input is the same
    Docling-parsed CCoP markdown the hybrid Qdrant index consumes (D-04/D-05).

    Examples:
        ccop-eval graph build
        ccop-eval graph build --drop
    """
    try:
        asyncio.run(_run_build(ccop_dir, drop))
    except Exception as e:
        console.print(f"[red]Graph build failed:[/red] {e}")
        raise typer.Exit(code=1) from e


async def _run_build(ccop_dir: str, drop: bool) -> None:
    settings = get_settings()

    driver = neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )

    try:
        if drop:
            console.print(
                "[yellow]--drop set: wiping existing graph before build...[/yellow]"
            )
            with driver.session(database=settings.neo4j_database) as session:
                session.run("MATCH (n) DETACH DELETE n")

        with console.status("[bold green]Loading CCoP corpus (Docling markdown)..."):
            texts = load_ccop_corpus_texts(settings, ccop_dir=ccop_dir)

        console.print(f"[bold]Loaded {len(texts)} document(s) from {ccop_dir}[/bold]")

        builder = EmergentKGBuilder(settings=settings, driver=driver)

        with console.status(
            "[bold green]Building emergent KG (gpt-4o-mini extraction)..."
        ):
            stats = await builder.build(texts)

        _print_summary(stats)
    finally:
        driver.close()


def _print_summary(stats: BuildStats) -> None:
    table = Table(title="GraphRAG Build Summary", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="bold")
    table.add_row("Documents processed", str(stats.docs_processed))
    table.add_row("Chunks written", str(stats.chunks_written))
    table.add_row("Nodes created", str(stats.nodes_created))
    table.add_row("Relationships created", str(stats.relationships_created))
    table.add_row("Failures", str(len(stats.failures)))
    console.print(table)

    if stats.failures:
        console.print("[red]Failures:[/red]")
        for failure in stats.failures:
            console.print(f"  - {failure}")
