"""Spec lifecycle management — archiving completed/abandoned specs.

Moves specs from specs/changes/ to specs/archive/ to reduce noise in
MCP tools, CLI output, and evospec check. Archived specs remain accessible
via include_archived flags but are hidden by default.
"""

import shutil
from pathlib import Path

import yaml
from rich.console import Console

from evospec.core.config import find_project_root, get_paths, load_config

console = Console()


def run_archive(
    *,
    spec_id: str | None = None,
    status_filter: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Archive completed/abandoned specs to specs/archive/.

    Args:
        spec_id: Archive a specific spec by id or directory name.
        status_filter: Archive all specs with this status (e.g., 'completed', 'abandoned').
                       If neither spec_id nor status_filter is given, defaults to
                       archiving all completed + abandoned specs.
        dry_run: If True, show what would be archived without moving anything.

    Returns:
        Dict with archived spec paths and count.
    """
    root = find_project_root()
    if root is None:
        console.print("[red]ERROR:[/] No evospec.yaml found. Run `evospec init` first.")
        return {"archived": [], "count": 0}

    config = load_config(root)
    paths_cfg = get_paths(config)
    specs_dir = root / paths_cfg["specs"]
    archive_dir = root / "specs" / "archive"

    if not specs_dir.exists():
        console.print("[yellow]No specs directory found.[/]")
        return {"archived": [], "count": 0}

    # Determine which statuses to archive
    if status_filter:
        target_statuses = {status_filter.lower()}
    elif spec_id is None:
        target_statuses = {"completed", "abandoned", "superseded"}
    else:
        target_statuses = None  # Archive by id regardless of status

    to_archive: list[tuple[Path, dict]] = []

    for spec_dir in sorted(specs_dir.iterdir()):
        spec_yaml = spec_dir / "spec.yaml"
        if not spec_yaml.exists():
            continue
        spec = yaml.safe_load(spec_yaml.read_text()) or {}

        if spec_id:
            sid = spec.get("id", "")
            if sid != spec_id and spec_dir.name != spec_id:
                continue

        if target_statuses:
            spec_status = (spec.get("status") or "draft").lower()
            if spec_status not in target_statuses:
                continue

        to_archive.append((spec_dir, spec))

    if not to_archive:
        console.print("[yellow]No specs match the archive criteria.[/]")
        return {"archived": [], "count": 0}

    # Preview
    console.print(f"[bold]{'Would archive' if dry_run else 'Archiving'} {len(to_archive)} spec(s):[/]")
    console.print()

    archived_paths: list[str] = []
    for spec_dir, spec in to_archive:
        title = spec.get("title", spec_dir.name)
        status = spec.get("status", "?")
        rel_path = spec_dir.relative_to(root)
        console.print(f"  {'[dim]DRY RUN[/] ' if dry_run else ''}[cyan]{rel_path}[/] ({status})")
        console.print(f"    {title}")

        if not dry_run:
            dest = archive_dir / spec_dir.name
            archive_dir.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(spec_dir), str(dest))
            archived_paths.append(str(dest.relative_to(root)))
        else:
            archived_paths.append(str(rel_path))

    console.print()
    if dry_run:
        console.print(f"[dim]Dry run — no files moved. Run without --dry-run to archive.[/]")
    else:
        console.print(f"[bold green]Archived {len(archived_paths)} spec(s) to specs/archive/[/]")
        console.print("[dim]Archived specs are hidden from MCP tools by default.[/]")
        console.print("[dim]Use include_archived=True or --include-archived to see them.[/]")

    return {"archived": archived_paths, "count": len(archived_paths)}
