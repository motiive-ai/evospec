"""Spec validation and fitness function checks."""

from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, ValidationError
from rich.console import Console

from evospec.core.config import find_project_root, load_config, get_paths

console = Console()

_PACKAGE_SCHEMA = Path(__file__).parent.parent / "schemas" / "spec.schema.json"


def _load_schema() -> dict | None:
    """Load the spec JSON schema.

    Looks in two places:
    1. The project root (schemas/spec.schema.json) — for local overrides
    2. The installed package (evospec/schemas/) — for pipx installs
    """
    import json

    # Try project root first (allows local overrides)
    root = find_project_root()
    if root:
        local_schema = root / "schemas" / "spec.schema.json"
        if local_schema.exists():
            with open(local_schema) as f:
                return json.load(f)

    # Fall back to package-bundled schema
    if _PACKAGE_SCHEMA.exists():
        with open(_PACKAGE_SCHEMA) as f:
            return json.load(f)

    return None


def run_checks(strict: bool = False) -> None:
    """Run all spec validations and fitness function checks."""
    root = find_project_root()
    if root is None:
        console.print("[red]✗ No evospec.yaml found. Run `evospec init` first.[/red]")
        return

    config = load_config(root)
    paths = get_paths(config)
    specs_root = root / paths["specs"]

    if not specs_root.exists():
        console.print("[yellow]No specs directory found.[/yellow]")
        return

    schema = _load_schema()
    errors = 0
    warnings = 0
    checked = 0

    spec_dirs = sorted(
        [d for d in specs_root.iterdir() if d.is_dir() and (d / "spec.yaml").exists()]
    )

    if not spec_dirs:
        console.print("[yellow]No specs found to check.[/yellow]")
        return

    console.print(f"[bold]Checking {len(spec_dirs)} spec(s)...[/bold]")
    console.print()

    for spec_dir in spec_dirs:
        spec_yaml_path = spec_dir / "spec.yaml"
        with open(spec_yaml_path) as f:
            spec = yaml.safe_load(f) or {}

        title = spec.get("title", spec_dir.name)
        zone = spec.get("zone", "unknown")
        checked += 1

        console.print(f"[bold]{title}[/bold] [dim]({zone})[/dim]")

        # Schema validation
        if schema:
            validator = Draft202012Validator(schema)
            spec_errors = list(validator.iter_errors(spec))
            for err in spec_errors:
                console.print(f"  [red]✗ Schema: {err.message}[/red]")
                errors += 1
            if not spec_errors:
                console.print(f"  [green]✓[/green] Schema valid")

        # Zone-specific checks
        if zone == "core":
            e, w = _check_core(spec, spec_dir)
            errors += e
            warnings += w
        elif zone == "hybrid":
            e, w = _check_hybrid(spec, spec_dir)
            errors += e
            warnings += w
        elif zone == "edge":
            e, w = _check_edge(spec, spec_dir)
            errors += e
            warnings += w

        # General checks
        e, w = _check_general(spec, spec_dir)
        errors += e
        warnings += w

        console.print()

    # Summary
    console.print("─" * 50)
    console.print(f"[bold]Checked {checked} spec(s)[/bold]")

    if errors:
        console.print(f"[red]✗ {errors} error(s)[/red]")
    if warnings:
        console.print(f"[yellow]⚠ {warnings} warning(s)[/yellow]")
    if not errors and not warnings:
        console.print("[bold green]✓ All checks passed[/bold green]")

    if strict and (errors or warnings):
        raise SystemExit(1)
    elif errors:
        raise SystemExit(1)


def _check_core(spec: dict, spec_dir: Path) -> tuple[int, int]:
    """Check core zone requirements."""
    errors = 0
    warnings = 0

    if not spec.get("bounded_context"):
        console.print("  [red]✗ Core zone requires bounded_context[/red]")
        errors += 1

    invariants = spec.get("invariants", [])
    if not invariants:
        console.print("  [red]✗ Core zone requires at least one invariant[/red]")
        errors += 1
    else:
        console.print(f"  [green]✓[/green] {len(invariants)} invariant(s) defined")
        for inv in invariants:
            if not inv.get("enforcement"):
                console.print(
                    f"  [yellow]⚠ Invariant {inv.get('id', '?')} has no enforcement mechanism[/yellow]"
                )
                warnings += 1

    fitness = spec.get("fitness_functions", [])
    if not fitness:
        console.print("  [red]✗ Core zone requires at least one fitness function[/red]")
        errors += 1
    else:
        console.print(f"  [green]✓[/green] {len(fitness)} fitness function(s) defined")

    if not (spec_dir / "domain-contract.md").exists():
        console.print("  [red]✗ Core zone requires domain-contract.md[/red]")
        errors += 1
    else:
        console.print("  [green]✓[/green] domain-contract.md exists")

    return errors, warnings


def _check_hybrid(spec: dict, spec_dir: Path) -> tuple[int, int]:
    """Check hybrid zone requirements."""
    errors = 0
    warnings = 0

    if not (spec_dir / "discovery-spec.md").exists():
        console.print("  [yellow]⚠ Hybrid zone should have discovery-spec.md[/yellow]")
        warnings += 1
    else:
        console.print("  [green]✓[/green] discovery-spec.md exists")

    if not (spec_dir / "domain-contract.md").exists():
        console.print("  [yellow]⚠ Hybrid zone should have domain-contract.md[/yellow]")
        warnings += 1
    else:
        console.print("  [green]✓[/green] domain-contract.md exists")

    if not spec.get("invariants"):
        console.print("  [yellow]⚠ Hybrid zone: consider defining invariants[/yellow]")
        warnings += 1

    return errors, warnings


def _check_edge(spec: dict, spec_dir: Path) -> tuple[int, int]:
    """Check edge zone requirements."""
    errors = 0
    warnings = 0

    discovery = spec.get("discovery", {})
    if not discovery.get("outcome"):
        console.print("  [yellow]⚠ Edge zone: discovery.outcome not set[/yellow]")
        warnings += 1

    if not discovery.get("kill_criteria"):
        console.print("  [yellow]⚠ Edge zone: discovery.kill_criteria not set[/yellow]")
        warnings += 1

    if not (spec_dir / "discovery-spec.md").exists():
        console.print("  [red]✗ Edge zone requires discovery-spec.md[/red]")
        errors += 1
    else:
        console.print("  [green]✓[/green] discovery-spec.md exists")

    return errors, warnings


def _check_general(spec: dict, spec_dir: Path) -> tuple[int, int]:
    """General checks applicable to all zones."""
    warnings = 0

    if not spec.get("ownership", {}).get("team"):
        console.print("  [yellow]⚠ No owning team specified[/yellow]")
        warnings += 1

    classification = spec.get("classification", {})
    if not classification:
        console.print("  [yellow]⚠ Not classified yet. Run `evospec classify`[/yellow]")
        warnings += 1

    return 0, warnings


def run_fitness_functions(spec_path: str | None = None) -> tuple[int, int, int]:
    """Execute fitness functions defined in spec.yaml files.

    Returns:
        Tuple of (passed, failed, skipped) counts.
    """
    import subprocess

    root = find_project_root()
    if root is None:
        console.print("[red]✗ No evospec.yaml found. Run `evospec init` first.[/red]")
        return 0, 0, 0

    config = load_config(root)
    specs_root = root / get_paths(config)["specs"]

    if spec_path:
        spec_dirs = [root / spec_path]
    else:
        spec_dirs = sorted(
            d for d in specs_root.iterdir()
            if d.is_dir() and (d / "spec.yaml").exists()
        ) if specs_root.exists() else []

    passed = 0
    failed = 0
    skipped = 0

    for spec_dir in spec_dirs:
        spec_yaml_path = spec_dir / "spec.yaml"
        if not spec_yaml_path.exists():
            continue

        with open(spec_yaml_path) as f:
            spec = yaml.safe_load(f) or {}

        fitness_fns = spec.get("fitness_functions", [])
        if not fitness_fns:
            continue

        title = spec.get("title", spec_dir.name)
        console.print(f"\n[bold]Running fitness functions for: {title}[/bold]")

        for ff in fitness_fns:
            ff_id = ff.get("id", "?")
            ff_path = ff.get("path", "")
            ff_type = ff.get("type", "unknown")
            ff_dim = ff.get("dimension", "")

            if not ff_path:
                console.print(f"  [dim]⊘ {ff_id}: no path defined (skipped)[/dim]")
                skipped += 1
                continue

            full_path = root / ff_path
            if not full_path.exists():
                console.print(f"  [yellow]⊘ {ff_id}: file not found — {ff_path}[/yellow]")
                skipped += 1
                continue

            if ff_type in ("unit-test", "integration-test", "contract-test"):
                try:
                    result = subprocess.run(
                        ["python", "-m", "pytest", str(full_path), "-v", "--tb=short", "-q"],
                        capture_output=True,
                        text=True,
                        cwd=str(root),
                        timeout=120,
                    )
                    if result.returncode == 0:
                        console.print(f"  [green]✓[/green] {ff_id} ({ff_dim}) — PASS")
                        passed += 1
                    else:
                        console.print(f"  [red]✗[/red] {ff_id} ({ff_dim}) — FAIL")
                        if result.stdout:
                            for line in result.stdout.strip().split("\n")[-5:]:
                                console.print(f"    [dim]{line}[/dim]")
                        failed += 1
                except subprocess.TimeoutExpired:
                    console.print(f"  [red]✗[/red] {ff_id} — TIMEOUT (>120s)")
                    failed += 1
                except FileNotFoundError:
                    console.print(f"  [yellow]⊘ {ff_id}: test runner not found[/yellow]")
                    skipped += 1
            else:
                console.print(f"  [dim]⊘ {ff_id}: type '{ff_type}' not executable (skipped)[/dim]")
                skipped += 1

    # Summary
    console.print()
    console.print("─" * 50)
    total = passed + failed + skipped
    console.print(f"[bold]Fitness functions: {total} total[/bold]")
    if passed:
        console.print(f"  [green]✓ {passed} passed[/green]")
    if failed:
        console.print(f"  [red]✗ {failed} failed[/red]")
    if skipped:
        console.print(f"  [dim]⊘ {skipped} skipped[/dim]")

    return passed, failed, skipped
