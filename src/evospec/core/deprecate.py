"""Deprecate API contracts or entities via CLI."""

from datetime import date
from pathlib import Path

import yaml
from rich.console import Console

from evospec.core.config import find_project_root, get_paths, load_config

console = Console()


def deprecate_item(
    *,
    kind: str,
    name: str,
    replacement: str | None = None,
    sunset_date: str | None = None,
) -> dict:
    """Mark an API contract endpoint or entity as deprecated.

    Args:
        kind: 'contract' or 'entity'
        name: Endpoint path (for contracts) or entity name (for entities)
        replacement: Replacement endpoint/entity name
        sunset_date: ISO date when the item will be removed

    Returns:
        Dict with status and details.
    """
    root = find_project_root()
    if root is None:
        console.print("[red]ERROR:[/] No evospec.yaml found. Run `evospec init` first.")
        return {"error": "No evospec.yaml found."}

    config = load_config(root)
    paths_cfg = get_paths(config)
    domain_dir = root / paths_cfg["domain"]
    today = date.today().isoformat()

    if kind == "contract":
        return _deprecate_contract(domain_dir, name, replacement, sunset_date, today)
    elif kind == "entity":
        return _deprecate_entity(domain_dir, name, replacement, today)
    else:
        console.print(f"[red]Unknown kind: {kind}. Use 'contract' or 'entity'.[/red]")
        return {"error": f"Unknown kind: {kind}"}


def _deprecate_contract(
    domain_dir: Path, endpoint: str, replacement: str | None, sunset_date: str | None, today: str,
) -> dict:
    """Mark an API contract as deprecated."""
    contracts_path = domain_dir / "api-contracts.yaml"
    if not contracts_path.exists():
        console.print("[red]No api-contracts.yaml found.[/red]")
        return {"error": "No api-contracts.yaml found."}

    data = yaml.safe_load(contracts_path.read_text()) or {}
    contracts = data.get("contracts", [])

    found = False
    for c in contracts:
        ep = c.get("endpoint", "")
        if ep.lower() == endpoint.lower() or endpoint.lower() in ep.lower():
            c["status"] = "deprecated"
            c["deprecated_at"] = today
            if replacement:
                c["replacement"] = replacement
            if sunset_date:
                c["sunset_date"] = sunset_date
            found = True
            console.print(f"[green]✓[/green] Deprecated: [cyan]{ep}[/cyan]")
            if replacement:
                console.print(f"  Replacement: {replacement}")
            if sunset_date:
                console.print(f"  Sunset date: {sunset_date}")
            break

    if not found:
        console.print(f"[red]No contract matching '{endpoint}' found.[/red]")
        return {"error": f"No contract matching '{endpoint}' found."}

    contracts_path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True))
    return {"status": "deprecated", "endpoint": endpoint}


def _deprecate_entity(
    domain_dir: Path, name: str, replacement: str | None, today: str,
) -> dict:
    """Mark an entity as deprecated."""
    entities_path = domain_dir / "entities.yaml"
    if not entities_path.exists():
        console.print("[red]No entities.yaml found.[/red]")
        return {"error": "No entities.yaml found."}

    entities = yaml.safe_load(entities_path.read_text()) or []
    if not isinstance(entities, list):
        console.print("[red]entities.yaml has unexpected format.[/red]")
        return {"error": "entities.yaml has unexpected format."}

    found = False
    for e in entities:
        ent_name = e.get("name", "")
        if ent_name.lower() == name.lower():
            e["status"] = "deprecated"
            e["deprecated_at"] = today
            if replacement:
                e["replacement"] = replacement
            found = True
            console.print(f"[green]✓[/green] Deprecated entity: [cyan]{ent_name}[/cyan]")
            if replacement:
                console.print(f"  Replacement: {replacement}")
            break

    if not found:
        console.print(f"[red]No entity named '{name}' found.[/red]")
        return {"error": f"No entity named '{name}' found."}

    entities_path.write_text(yaml.dump(entities, default_flow_style=False, sort_keys=False, allow_unicode=True))
    return {"status": "deprecated", "entity": name}
