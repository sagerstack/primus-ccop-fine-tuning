"""
Validate Ground Truth Command

Thin Typer wrapper over `ground-truth/schema/validate.py`. Exposes the
ID-existence + semantic-mismatch validator as `ccop-eval validate-ground-truth`.

Manual-run only per CONTEXT.md — not wired into CI or pre-commit hooks.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import typer
from rich.console import Console

_CONSOLE = Console()

# Repo root resolved from this file: src/presentation/cli/commands/validate_ground_truth.py
#   parents[0] = commands/, parents[1] = cli/, parents[2] = presentation/,
#   parents[3] = src/, parents[4] = repo root.
_REPO_ROOT = Path(__file__).resolve().parents[4]
_VALIDATOR_SCRIPT = _REPO_ROOT / "ground-truth" / "schema" / "validate.py"
_DEFAULT_TEST_SUITE_DIR = _REPO_ROOT / "ground-truth" / "test-suite"
_DEFAULT_INVENTORY_PATH = (
    _REPO_ROOT / "src" / "rag" / "ingestion" / "fixtures" / "clause_inventory.json"
)

validate_app = typer.Typer(
    name="validate-ground-truth",
    help="Validate v2 ground-truth JSONL files against the clause inventory "
    "and (optionally) the semantic-mismatch gate. Manual-run only.",
    invoke_without_command=True,
    no_args_is_help=False,
)


def _load_validator_module():
    """Load ground-truth/schema/validate.py as a module.

    The validator lives outside the src/ package tree; importlib lets us reuse
    its functions programmatically without subprocess overhead.
    """
    if not _VALIDATOR_SCRIPT.exists():
        _CONSOLE.print(
            f"[red]Validator script missing: {_VALIDATOR_SCRIPT}[/red]"
        )
        raise typer.Exit(code=2)

    spec = importlib.util.spec_from_file_location(
        "_ccop_validate_ground_truth", _VALIDATOR_SCRIPT
    )
    if spec is None or spec.loader is None:
        _CONSOLE.print("[red]Could not load validator module[/red]")
        raise typer.Exit(code=2)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@validate_app.callback(invoke_without_command=True)
def validate(
    ctx: typer.Context,
    test_suite_dir: Path = typer.Option(
        _DEFAULT_TEST_SUITE_DIR,
        "--test-suite-dir",
        help="Directory containing b*.jsonl test-case files.",
    ),
    file: Path = typer.Option(
        None,
        "--file",
        help="Single JSONL file to validate (overrides --test-suite-dir).",
    ),
    inventory: Path = typer.Option(
        _DEFAULT_INVENTORY_PATH,
        "--inventory",
        help="Path to clause_inventory.json.",
    ),
    no_semantic: bool = typer.Option(
        False,
        "--no-semantic",
        help="Disable the Pass-3 semantic-mismatch gate (default: semantic ON).",
    ),
    semantic_threshold: float = typer.Option(
        0.35,
        "--semantic-threshold",
        help="Cosine similarity threshold for Pass-3 semantic check.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Treat warnings as errors.",
    ),
) -> None:
    """Run the v2 ground-truth validator. Exits 0 on clean ground truth."""
    if ctx.invoked_subcommand is not None:
        return

    validator = _load_validator_module()
    exit_code = validator.run_validation(
        test_suite_dir=test_suite_dir if file is None else None,
        file=file,
        inventory_path=inventory,
        use_inventory=True,
        semantic_check=not no_semantic,
        semantic_threshold=semantic_threshold,
        strict=strict,
    )
    raise typer.Exit(code=exit_code)
