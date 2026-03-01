"""Feature registry management — tracks feature lifecycle across the Knowledge Funnel."""

import re
from datetime import date
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

from evospec.core.config import find_project_root, load_config

console = Console()


def _load_config_with_features(root: Path) -> tuple[dict, list[dict], Path]:
    """Load config and return (config, features_list, config_path)."""
    config_path = root / "evospec.yaml"
    config = load_config(root)
    features = config.get("features", []) or []
    return config, features, config_path


def _save_features(root: Path, config: dict, features: list[dict]) -> None:
    """Write updated features list back to evospec.yaml."""
    config_path = root / "evospec.yaml"
    config["features"] = features
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def _next_feature_id(features: list[dict]) -> str:
    """Generate the next feature ID (feat-001, feat-002, etc.)."""
    max_num = 0
    for feat in features:
        match = re.match(r"feat-(\d+)", feat.get("id", ""))
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"feat-{max_num + 1:03d}"


def _knowledge_stage_for_zone(zone: str) -> str:
    """Default knowledge stage based on zone."""
    return {"edge": "mystery", "hybrid": "heuristic", "core": "algorithm"}.get(zone, "mystery")


def list_features() -> None:
    """Display all registered features in a table."""
    root = find_project_root()
    if root is None:
        console.print("[red]✗ No evospec.yaml found. Run `evospec init` first.[/red]")
        return

    _, features, _ = _load_config_with_features(root)

    if not features:
        console.print("[yellow]No features registered. Use `evospec feature add` to register one.[/yellow]")
        return

    table = Table(title="Features Registry")
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Zone", style="magenta")
    table.add_column("Status")
    table.add_column("Knowledge", style="dim")
    table.add_column("Owner", style="dim")
    table.add_column("Created")

    status_colors = {
        "discovery": "blue",
        "specifying": "yellow",
        "implementing": "cyan",
        "validating": "magenta",
        "shipped": "green",
        "killed": "red",
    }

    for feat in features:
        status = feat.get("status", "?")
        color = status_colors.get(status, "white")
        table.add_row(
            feat.get("id", "?"),
            feat.get("title", "?"),
            feat.get("zone", "?"),
            f"[{color}]{status}[/{color}]",
            feat.get("knowledge_stage", "?"),
            feat.get("owner", ""),
            feat.get("created_at", ""),
        )

    console.print(table)

    # Summary
    by_status: dict[str, int] = {}
    for feat in features:
        s = feat.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1

    parts = [f"{v} {k}" for k, v in sorted(by_status.items())]
    console.print(f"\n[dim]{len(features)} feature(s): {', '.join(parts)}[/dim]")


def add_feature(title: str, zone: str = "edge", owner: str = "") -> None:
    """Register a new feature in the features registry."""
    root = find_project_root()
    if root is None:
        console.print("[red]✗ No evospec.yaml found. Run `evospec init` first.[/red]")
        return

    config, features, _ = _load_config_with_features(root)
    feature_id = _next_feature_id(features)

    new_feature = {
        "id": feature_id,
        "title": title,
        "zone": zone,
        "status": "discovery",
        "knowledge_stage": _knowledge_stage_for_zone(zone),
        "spec_path": "",
        "owner": owner,
        "created_at": date.today().isoformat(),
        "shipped_at": "",
        "kill_reason": "",
    }

    features.append(new_feature)
    _save_features(root, config, features)

    console.print(f"[green]✓[/green] Registered feature [cyan]{feature_id}[/cyan]: {title}")
    console.print(f"  Zone: [magenta]{zone}[/magenta] | Knowledge stage: {_knowledge_stage_for_zone(zone)}")
    console.print(f"\n  Next: `evospec new \"{title}\"` to create the spec, then link it with:")
    console.print(f"  `evospec feature update {feature_id} --spec-path specs/changes/...`")


def update_feature(
    feature_id: str,
    status: str | None = None,
    zone: str | None = None,
    knowledge_stage: str | None = None,
) -> None:
    """Update a feature's status, zone, or knowledge stage."""
    root = find_project_root()
    if root is None:
        console.print("[red]✗ No evospec.yaml found. Run `evospec init` first.[/red]")
        return

    config, features, _ = _load_config_with_features(root)

    target = None
    for feat in features:
        if feat.get("id") == feature_id:
            target = feat
            break

    if target is None:
        console.print(f"[red]✗ Feature {feature_id} not found.[/red]")
        return

    changes = []

    if status:
        old_status = target.get("status", "?")
        target["status"] = status
        changes.append(f"status: {old_status} → {status}")
        if status == "shipped":
            target["shipped_at"] = date.today().isoformat()

    if zone:
        old_zone = target.get("zone", "?")
        target["zone"] = zone
        changes.append(f"zone: {old_zone} → {zone}")

    if knowledge_stage:
        old_ks = target.get("knowledge_stage", "?")
        target["knowledge_stage"] = knowledge_stage
        changes.append(f"knowledge_stage: {old_ks} → {knowledge_stage}")

    if not changes:
        console.print("[yellow]No changes specified.[/yellow]")
        return

    _save_features(root, config, features)

    console.print(f"[green]✓[/green] Updated [cyan]{feature_id}[/cyan]:")
    for change in changes:
        console.print(f"  {change}")
