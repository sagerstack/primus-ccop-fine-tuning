"""
GraphRAG CLI Commands

`ccop-eval graph build` constructs the emergent CCoP knowledge graph in Neo4j
as a first-class, repeatable command (D-17) — not a throwaway spike.

`ccop-eval graph build-ontology` constructs the SCHEMA-CONSTRAINED
(ontology-governed) CCoP knowledge graph (Phase 10, D-06/D-07 fix), then
LINKs extracted entities to the seeded :Clause backbone (D-10/D-11).

`ccop-eval graph inspect` / `graph stats` surface the D-18 KG-quality metrics
(KGInspector) so the emergent graph is seen and measured before it is ever
scored — the quantitative half of the D-19 iterate-and-improve loop
(inspect -> adjust -> rebuild -> re-inspect). The interactive/visual half is
docs/phase-2/neo4j-browser-workflow.md.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional

import neo4j
import typer
from rich.console import Console
from rich.table import Table

from infrastructure.config.settings import get_settings
from rag.graph.build.corpus_source import DEFAULT_CCOP_DIR, load_ccop_corpus_texts
from rag.graph.build.kg_builder import BuildStats, EmergentKGBuilder
from rag.graph.build.ontology_kg_builder import (
    BuildStats as OntologyBuildStats,
)
from rag.graph.build.ontology_kg_builder import OntologyKGBuilder
from rag.graph.inspect.metrics import DEFAULT_CLAUSE_INVENTORY_PATH, KGInspector
from rag.graph.ontology.clause_linker import ClauseLinker, LinkStats
from rag.graph.ontology.clause_seeder import (
    DEFAULT_CLAUSE_INVENTORY_PATH as DEFAULT_SEED_INVENTORY_PATH,
)
from rag.graph.ontology.clause_seeder import ClauseSeeder, SeedStats

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


@graph_app.command(name="build-ontology")
def build_ontology_command(
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
    permissive: bool = typer.Option(
        False,
        "--permissive/--strict",
        help=(
            "Flip additional_node_types/additional_relationship_types to "
            "True for iteration (RESEARCH.md Pitfall 1 escape hatch — the "
            "locked vocabulary can silently drop out-of-schema entities). "
            "Default: --strict (the locked ontology_config.json vocabulary)."
        ),
    ),
    sample: bool = typer.Option(
        False,
        "--sample/--full",
        help=(
            "Build on ONLY the first loaded document (cheap iteration / "
            "smoke-test). Default: --full (the entire CCoP corpus)."
        ),
    ),
    link: bool = typer.Option(
        True,
        "--link/--no-link",
        help=(
            "Run the deterministic clause_linker pass after the build "
            "(D-10/D-11 entity->:Clause LINKED_TO). Default: on."
        ),
    ),
) -> None:
    """
    Build the SCHEMA-CONSTRAINED (ontology-governed) CCoP knowledge graph in
    Neo4j (Phase 10, D-06/D-07 anti-pattern fix), then LINK extracted
    entities to the seeded :Clause backbone (D-10/D-11).

    Extraction = openai/gpt-4o-mini via OpenRouter (D-06a, held constant with
    Phase 9). Embeddings = BAAI/bge-large-en-v1.5, in-process (D-07). Schema
    = the LOCKED ontology_config.json (24 node types, 48 relationship types,
    additional_node_types=false) unless --permissive is set. Extraction unit
    = SectionAlignedSplitter + gleaning (D-11, 10-06).

    Run `ccop-eval graph seed-clauses` FIRST so extracted entities have a
    seeded :Clause backbone to link to.

    Examples:
        ccop-eval graph seed-clauses
        ccop-eval graph build-ontology
        ccop-eval graph build-ontology --sample --permissive
        ccop-eval graph build-ontology --drop
    """
    try:
        asyncio.run(_run_build_ontology(ccop_dir, drop, permissive, sample, link))
    except Exception as e:
        console.print(f"[red]Ontology KG build failed:[/red] {e}")
        raise typer.Exit(code=1) from e


async def _run_build_ontology(
    ccop_dir: str, drop: bool, permissive: bool, sample: bool, link: bool
) -> None:
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

        if sample:
            first_doc_name, first_doc_text = next(iter(texts.items()))
            texts = {first_doc_name: first_doc_text}
            console.print(
                f"[yellow]--sample set: building on 1 document only "
                f"({first_doc_name})[/yellow]"
            )

        console.print(f"[bold]Loaded {len(texts)} document(s) from {ccop_dir}[/bold]")

        builder = OntologyKGBuilder(settings=settings, driver=driver, permissive=permissive)

        mode_label = "PERMISSIVE" if permissive else "STRICT (locked schema)"
        with console.status(
            f"[bold green]Building ontology-constrained KG "
            f"({mode_label}, gpt-4o-mini extraction + gleaning)..."
        ):
            stats = await builder.build(texts)

        _print_ontology_build_summary(stats, permissive)

        if link:
            with console.status(
                "[bold green]Linking extracted entities to seeded :Clause backbone..."
            ):
                linker = ClauseLinker(settings=settings, driver=driver)
                link_stats = linker.link()
            _print_link_summary(link_stats)
    finally:
        driver.close()


def _print_ontology_build_summary(stats: OntologyBuildStats, permissive: bool) -> None:
    mode = "permissive" if permissive else "strict (locked schema)"
    table = Table(title=f"Ontology KG Build Summary ({mode})", show_header=True)
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


def _print_link_summary(stats: LinkStats) -> None:
    table = Table(title="Clause Linking Summary (D-10/D-11)", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="bold")
    table.add_row("Chunks scanned", str(stats.chunks_scanned))
    table.add_row("Clauses scanned", str(stats.clauses_scanned))
    table.add_row("Chunk-clause matches", str(stats.chunk_clause_pairs))
    table.add_row("LINKED_TO edges (total)", str(stats.linked_to_edges_total))
    console.print(table)


def _open_driver(settings) -> neo4j.Driver:
    return neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )


@graph_app.command(name="seed-clauses")
def seed_clauses_command(
    inventory_path: str = typer.Option(
        str(DEFAULT_SEED_INVENTORY_PATH),
        "--inventory-path",
        help="Path to clause_inventory.json (D-10 deterministic seed source)",
    ),
) -> None:
    """
    Seed (or re-seed) the deterministic clause backbone (D-10).

    MERGEs :Clause nodes from clause_inventory.json with Title -> Chapter ->
    Article -> Item parent-child edges and function_type tags (D-09) from
    the locked ontology. No LLM call -- deterministic and idempotent;
    re-running never creates duplicates. These real-ID clause nodes become
    the fine-grained retrieval unit (D-11) that extracted entities LINK to.

    Example:
        ccop-eval graph seed-clauses
    """
    settings = get_settings()
    driver = _open_driver(settings)
    try:
        seeder = ClauseSeeder(settings=settings, driver=driver, inventory_path=inventory_path)
        with console.status("[bold green]Seeding clause backbone (deterministic, no LLM)..."):
            stats = seeder.seed()
        _print_seed_summary(stats)
    except Exception as e:
        console.print(f"[red]Clause seeding failed:[/red] {e}")
        raise typer.Exit(code=1) from e
    finally:
        driver.close()


def _print_seed_summary(stats: SeedStats) -> None:
    table = Table(title="Clause Backbone Seed Summary", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="bold")
    table.add_row("Entries in fixture", str(stats.entries_total))
    table.add_row("Clause nodes (post-seed)", str(stats.nodes_seeded))
    table.add_row("Parent-child edges", str(stats.edges_created))
    console.print(table)

    dist_table = Table(title="function_type Distribution (D-09)", show_header=True)
    dist_table.add_column("function_type", style="cyan")
    dist_table.add_column("Count", justify="right", style="bold")
    for function_type, count in stats.function_type_distribution.items():
        dist_table.add_row(function_type, str(count))
    console.print(dist_table)


@graph_app.command(name="inspect")
def inspect_command(
    inventory_path: str = typer.Option(
        str(DEFAULT_CLAUSE_INVENTORY_PATH),
        "--inventory-path",
        help="Path to clause_inventory.json (D-18 clause-coverage source)",
    ),
) -> None:
    """
    Print a human-readable KG-quality report (D-18).

    Node/edge counts, entity-type distribution, degree summary, orphan
    count, clause coverage vs clause_inventory.json, duplicate-entity
    groups, and extraction failure rate. Complements the interactive Neo4j
    Browser workflow (docs/phase-2/neo4j-browser-workflow.md) — this is the
    quantitative half of the D-19 inspect -> adjust -> rebuild -> re-inspect
    loop, run BEFORE the graph is ever scored.

    Honesty guardrail (D-19): these metrics measure structural/extraction
    functionality. They are not a knob for chasing B01/B03/B04 scores.

    Example:
        ccop-eval graph inspect
    """
    settings = get_settings()
    driver = _open_driver(settings)
    try:
        inspector = KGInspector(driver=driver, database=settings.neo4j_database)
        summary = inspector.summary(inventory_path=inventory_path)
        _print_inspect_report(summary)
    except Exception as e:
        console.print(f"[red]Graph inspect failed:[/red] {e}")
        raise typer.Exit(code=1) from e
    finally:
        driver.close()


@graph_app.command(name="stats")
def stats_command(
    inventory_path: str = typer.Option(
        str(DEFAULT_CLAUSE_INVENTORY_PATH),
        "--inventory-path",
        help="Path to clause_inventory.json (D-18 clause-coverage source)",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        help="Write JSON stats to this path instead of stdout (feeds the Plan 06 comparison report)",
    ),
) -> None:
    """
    Print (or write) the D-18 KG-quality summary as machine-readable JSON.

    Same metrics as `graph inspect`, JSON-encoded for programmatic
    consumption (e.g. the Plan 06 graphrag-vs-hybrid comparison report's
    KG-quality section, D-15).

    Example:
        ccop-eval graph stats --output kg-stats.json
    """
    settings = get_settings()
    driver = _open_driver(settings)
    try:
        inspector = KGInspector(driver=driver, database=settings.neo4j_database)
        summary = inspector.summary(inventory_path=inventory_path)
        payload = json.dumps(summary, indent=2, default=str)

        if output:
            Path(output).write_text(payload)
            console.print(f"[green]Stats written to {output}[/green]")
        else:
            console.print(payload)
    except Exception as e:
        console.print(f"[red]Graph stats failed:[/red] {e}")
        raise typer.Exit(code=1) from e
    finally:
        driver.close()


def _print_inspect_report(summary: dict[str, Any]) -> None:
    coverage = summary["clause_coverage"]
    console.print(
        f"[bold]clause_coverage:[/bold] {coverage['covered']}/{coverage['total']} "
        f"({coverage['coverage_ratio']:.1%})"
    )

    counts_table = Table(title="KG Structure", show_header=True)
    counts_table.add_column("Metric", style="cyan")
    counts_table.add_column("Value", justify="right", style="bold")
    counts_table.add_row("Nodes", str(summary["node_count"]))
    counts_table.add_row("Edges", str(summary["edge_count"]))
    counts_table.add_row("Orphan nodes", str(summary["orphan_nodes"]))
    console.print(counts_table)

    entity_table = Table(title="Entity-Type Distribution", show_header=True)
    entity_table.add_column("Type", style="cyan")
    entity_table.add_column("Count", justify="right", style="bold")
    for label, count in summary["entity_type_distribution"].items():
        entity_table.add_row(label, str(count))
    console.print(entity_table)

    degree = summary["degree_distribution"]
    console.print(
        f"[bold]Degree:[/bold] min={degree['min']} max={degree['max']} "
        f"avg={degree['avg']} buckets={degree.get('buckets', {})}"
    )

    duplicates = summary["duplicate_entities"]
    console.print(f"[bold]Duplicate-entity groups:[/bold] {len(duplicates)}")
    if duplicates:
        dup_table = Table(title="Duplicate Entities (top 10 by group size)")
        dup_table.add_column("Name", style="yellow")
        dup_table.add_column("Labels")
        dup_table.add_column("Count", justify="right")
        for group in sorted(duplicates, key=len, reverse=True)[:10]:
            dup_table.add_row(
                group[0]["name"], ", ".join(group[0]["labels"]), str(len(group))
            )
        console.print(dup_table)

    failure = summary["extraction_failure_rate"]
    console.print(
        f"[bold]Extraction failure rate:[/bold] {failure['rate']} — {failure['note']}"
    )
