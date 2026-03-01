"""Show status of all change specs."""

from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

from evospec.core.config import find_project_root, load_config, get_paths

console = Console()

ZONE_COLORS = {
    "edge": "green",
    "hybrid": "yellow",
    "core": "red",
}

STATUS_COLORS = {
    "draft": "dim",
    "proposed": "cyan",
    "accepted": "blue",
    "in-progress": "yellow",
    "completed": "green",
    "abandoned": "red",
    "superseded": "dim",
}


def show_status() -> None:
    """Display a summary table of all change specs."""
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

    spec_dirs = sorted(
        [d for d in specs_root.iterdir() if d.is_dir() and (d / "spec.yaml").exists()]
    )

    if not spec_dirs:
        console.print("[yellow]No specs found. Run `evospec new` to create one.[/yellow]")
        return

    table = Table(title="EvoSpec — Change Specifications")
    table.add_column("ID", style="dim", max_width=30)
    table.add_column("Title", style="bold")
    table.add_column("Zone", justify="center")
    table.add_column("Status", justify="center")
    table.add_column("Risk", justify="center")
    table.add_column("Owner", style="dim")
    table.add_column("Artifacts", style="dim")

    for spec_dir in spec_dirs:
        with open(spec_dir / "spec.yaml") as f:
            spec = yaml.safe_load(f) or {}

        spec_id = spec.get("id", spec_dir.name)
        title = spec.get("title", "Untitled")
        zone = spec.get("zone", "?")
        status = spec.get("status", "?")
        risk = spec.get("classification", {}).get("risk_level", "—")
        team = spec.get("ownership", {}).get("team", "—")

        # Check which artifacts exist
        artifacts = []
        if (spec_dir / "discovery-spec.md").exists():
            artifacts.append("D")
        if (spec_dir / "domain-contract.md").exists():
            artifacts.append("C")

        # Count linked ADRs
        adr_count = len(spec.get("adrs", []))
        if adr_count:
            artifacts.append(f"A×{adr_count}")

        # Count invariants
        inv_count = len(spec.get("invariants", []))
        if inv_count:
            artifacts.append(f"I×{inv_count}")

        # Count fitness functions
        ff_count = len(spec.get("fitness_functions", []))
        if ff_count:
            artifacts.append(f"F×{ff_count}")

        zone_color = ZONE_COLORS.get(zone, "white")
        status_color = STATUS_COLORS.get(status, "white")

        table.add_row(
            spec_id,
            title,
            f"[{zone_color}]{zone}[/{zone_color}]",
            f"[{status_color}]{status}[/{status_color}]",
            risk,
            team,
            " ".join(artifacts) if artifacts else "—",
        )

    console.print(table)
    console.print()
    console.print("[dim]Artifacts: D=Discovery Spec, C=Domain Contract, A=ADRs, I=Invariants, F=Fitness Functions[/dim]")
