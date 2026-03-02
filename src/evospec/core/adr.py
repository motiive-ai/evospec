"""Architecture Decision Records management."""

import re
from datetime import date
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

from evospec.core.config import find_project_root, load_config, get_paths

console = Console()

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def _next_adr_number(adr_dir: Path) -> int:
    """Find the next ADR number by scanning existing files."""
    if not adr_dir.exists():
        return 1
    existing = []
    for f in adr_dir.glob("*.md"):
        match = re.match(r"^(\d+)-", f.name)
        if match:
            existing.append(int(match.group(1)))
    return max(existing, default=0) + 1


def create_adr(title: str) -> None:
    """Create a new Architecture Decision Record."""
    root = find_project_root()
    if root is None:
        console.print("[red]✗ No evospec.yaml found. Run `evospec init` first.[/red]")
        return

    config = load_config(root)
    paths = get_paths(config)
    adr_dir = root / paths["adrs"]
    adr_dir.mkdir(parents=True, exist_ok=True)

    number = _next_adr_number(adr_dir)
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower().strip()).strip("-")
    filename = f"{number:04d}-{slug}.md"
    adr_path = adr_dir / filename

    # Render template
    template_path = TEMPLATE_DIR / "adr.md"
    with open(template_path) as f:
        content = f.read()

    content = (
        content
        .replace("{{ number }}", f"{number:04d}")
        .replace("{{ title }}", title)
        .replace("{{ status }}", "proposed")
        .replace("{{ date }}", date.today().isoformat())
        .replace("{{ zone }}", "")
        .replace("{{ option_1 }}", "Option A")
        .replace("{{ option_2 }}", "Option B")
        .replace("{{ option_3 }}", "Option C")
    )

    adr_path.write_text(content)

    console.print(f"[green]✓[/green] Created ADR-{number:04d}: {title}")
    console.print(f"  [dim]{adr_path.relative_to(root)}[/dim]")


def list_adrs() -> None:
    """List all Architecture Decision Records."""
    root = find_project_root()
    if root is None:
        console.print("[red]✗ No evospec.yaml found. Run `evospec init` first.[/red]")
        return

    config = load_config(root)
    paths = get_paths(config)
    adr_dir = root / paths["adrs"]

    if not adr_dir.exists():
        console.print("[yellow]No ADR directory found.[/yellow]")
        return

    adr_files = sorted(adr_dir.glob("*.md"))
    if not adr_files:
        console.print("[yellow]No ADRs found.[/yellow]")
        return

    table = Table(title="Architecture Decision Records")
    table.add_column("#", style="cyan", width=6)
    table.add_column("Title", style="bold")
    table.add_column("Status", style="green")
    table.add_column("Date", style="dim")

    for adr_file in adr_files:
        content = adr_file.read_text()
        # Parse title from first heading
        title_match = re.search(r"^#\s+ADR-(\d+):\s+(.+)$", content, re.MULTILINE)
        # Parse status
        status_match = re.search(r"Status:\s+\*\*(\w+)\*\*", content)
        # Parse date
        date_match = re.search(r"Date:\s+(\S+)", content)

        number = title_match.group(1) if title_match else "?"
        title = title_match.group(2) if title_match else adr_file.stem
        status = status_match.group(1) if status_match else "?"
        adr_date = date_match.group(1) if date_match else "?"

        table.add_row(number, title, status, adr_date)

    console.print(table)
