"""Create a new change spec."""

import re
from datetime import date
from pathlib import Path

from rich.console import Console

from evospec.core.config import find_project_root, load_config, get_paths

console = Console()

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def slugify(title: str) -> str:
    """Convert a title to a slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def create_spec(title: str, zone: str | None = None) -> None:
    """Create a new change spec with appropriate templates."""
    root = find_project_root()
    if root is None:
        console.print("[red]✗ No evospec.yaml found. Run `evospec init` first.[/red]")
        return

    config = load_config(root)
    paths = get_paths(config)

    today = date.today().isoformat()
    slug = slugify(title)
    spec_id = f"{today}-{slug}"
    spec_dir = root / paths["specs"] / spec_id

    if spec_dir.exists():
        console.print(f"[red]✗ Spec directory already exists: {spec_dir}[/red]")
        return

    spec_dir.mkdir(parents=True)
    (spec_dir / "checks").mkdir()

    # Render spec.yaml
    spec_yaml_template = TEMPLATE_DIR / "spec.yaml"
    with open(spec_yaml_template) as f:
        spec_content = f.read()

    spec_content = (
        spec_content
        .replace("{{ id }}", slug)
        .replace("{{ title }}", title)
        .replace("{{ zone }}", zone or "edge")
        .replace("{{ created_at }}", today)
    )

    (spec_dir / "spec.yaml").write_text(spec_content)
    console.print(f"[green]✓[/green] Created spec.yaml")

    # Always create discovery spec for edge/hybrid
    if zone in (None, "edge", "hybrid"):
        _render_template(
            TEMPLATE_DIR / "discovery-spec.md",
            spec_dir / "discovery-spec.md",
            title=title,
            zone=zone or "edge",
            status="draft",
            created_at=today,
        )
        console.print(f"[green]✓[/green] Created discovery-spec.md")

    # Create domain contract for core/hybrid
    if zone in ("core", "hybrid"):
        _render_template(
            TEMPLATE_DIR / "domain-contract.md",
            spec_dir / "domain-contract.md",
            title=title,
            zone=zone,
            status="draft",
            bounded_context="",
        )
        console.print(f"[green]✓[/green] Created domain-contract.md")

    # Always create domain contract for core
    if zone == "core":
        console.print()
        console.print(
            "[yellow]⚠ Core zone: domain-contract.md requires invariants and fitness functions.[/yellow]"
        )

    console.print()
    console.print(f"[bold green]Created spec:[/bold green] {spec_dir.relative_to(root)}")

    if zone is None:
        console.print()
        console.print("Next: run [bold]evospec classify[/bold] to set the zone.")


def _render_template(
    template_path: Path,
    output_path: Path,
    **variables: str,
) -> None:
    """Render a template file with variable substitution."""
    with open(template_path) as f:
        content = f.read()

    for key, value in variables.items():
        content = content.replace("{{ " + key + " }}", value)

    output_path.write_text(content)
