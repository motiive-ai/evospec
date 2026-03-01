"""Initialize EvoSpec in a project."""

import shutil
from datetime import date
from pathlib import Path

from rich.console import Console

from evospec.core.config import get_paths

console = Console()

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def init_project(name: str, description: str = "") -> None:
    """Initialize EvoSpec directory structure and config in the current directory."""
    project_root = Path.cwd()
    config_path = project_root / "evospec.yaml"

    if config_path.exists():
        console.print("[yellow]⚠ evospec.yaml already exists. Skipping init.[/yellow]")
        return

    # Load template and render config
    template_config = TEMPLATE_DIR / "evospec.yaml"
    with open(template_config) as f:
        config_content = f.read()

    config_content = config_content.replace(
        'name: ""', f'name: "{name}"'
    ).replace(
        'description: ""', f'description: "{description}"', 1
    )

    with open(config_path, "w") as f:
        f.write(config_content)

    console.print(f"[green]✓[/green] Created evospec.yaml")

    # Create directory structure
    default_paths = get_paths({})
    dirs_to_create = [
        default_paths["specs"],
        default_paths["templates"],
        default_paths["adrs"],
        default_paths["domain"],
        default_paths["checks"],
    ]

    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓[/green] Created {dir_path}/")

    # Copy templates to project
    templates_dest = project_root / default_paths["templates"]
    for template_file in TEMPLATE_DIR.glob("*.md"):
        dest = templates_dest / template_file.name
        if not dest.exists():
            shutil.copy2(template_file, dest)
            console.print(f"[green]✓[/green] Copied template {template_file.name}")

    # Create glossary stub
    glossary_path = project_root / default_paths["domain"] / "glossary.md"
    if not glossary_path.exists():
        glossary_path.write_text(
            "# Ubiquitous Language — Glossary\n\n"
            "> Define domain terms once, use them everywhere.\n\n"
            "| Term | Definition | Context | Not to be confused with |\n"
            "|------|-----------|---------|------------------------|\n"
            "| | | | |\n"
        )
        console.print("[green]✓[/green] Created domain glossary stub")

    # Create context map stub
    context_map_path = project_root / default_paths["domain"] / "context-map.md"
    if not context_map_path.exists():
        context_map_path.write_text(
            "# Context Map\n\n"
            "> How bounded contexts relate to each other (DDD strategic design).\n\n"
            "## Contexts\n\n"
            "| Context | Type | Owner | Description |\n"
            "|---------|------|-------|-------------|\n"
            "| | core / supporting / generic | | |\n\n"
            "## Relationships\n\n"
            "| Upstream | Downstream | Relationship |\n"
            "|----------|-----------|-------------|\n"
            "| | | conformist / ACL / shared-kernel / open-host / published-language |\n"
        )
        console.print("[green]✓[/green] Created context map stub")

    # Copy AI agent integration files
    _setup_ai_agents(project_root)

    # Create first ADR
    adr_path = project_root / default_paths["adrs"] / "0001-adopt-evospec.md"
    if not adr_path.exists():
        adr_path.write_text(
            f"# ADR-0001: Adopt EvoSpec for spec-driven delivery\n\n"
            f"> Status: **accepted** | Date: {date.today().isoformat()} | Zone: core\n\n"
            f"---\n\n"
            f"## Context\n\n"
            f"We need a structured approach to specification that adapts rigor to risk.\n"
            f"Exploratory work needs speed; core domain work needs contracts and guardrails.\n\n"
            f"## Decision\n\n"
            f"Adopt EvoSpec as our spec-driven delivery framework.\n"
            f"Classify changes as edge/hybrid/core and apply appropriate artifacts.\n\n"
            f"## Consequences\n\n"
            f"### Positive\n"
            f"- Proportional specification (no over-specifying edge, no under-specifying core)\n"
            f"- Executable guardrails via fitness functions\n"
            f"- ADR trail for architectural decisions\n\n"
            f"### Negative\n"
            f"- Learning curve for the team\n"
            f"- Initial overhead to classify and document\n\n"
            f"## Reversibility\n\n"
            f"**Assessment**: trivial — specs are markdown files, easy to remove or migrate.\n"
        )
        console.print("[green]✓[/green] Created ADR-0001: Adopt EvoSpec")

    console.print()
    console.print("[bold green]EvoSpec initialized successfully![/bold green]")
    console.print()
    console.print("Next steps:")
    console.print("  evospec new \"my-first-change\"    Create your first change spec")
    console.print("  evospec classify                  Classify a change by zone")
    console.print("  evospec adr new \"decision-title\"  Record an architectural decision")
    console.print()
    console.print("[dim]AI agent integration:[/dim]")
    console.print("  [dim]Windsurf: /evospec.discover, /evospec.contract, /evospec.tasks, /evospec.implement, /evospec.check[/dim]")
    console.print("  [dim]Claude Code: reads CLAUDE.md automatically[/dim]")


def _setup_ai_agents(project_root: Path) -> None:
    """Copy AI agent integration files (Windsurf workflows, CLAUDE.md)."""
    # Windsurf workflows
    windsurf_src = TEMPLATE_DIR / ".windsurf" / "workflows"
    windsurf_dest = project_root / ".windsurf" / "workflows"

    if windsurf_src.exists():
        windsurf_dest.mkdir(parents=True, exist_ok=True)
        for wf_file in windsurf_src.glob("*.md"):
            dest = windsurf_dest / wf_file.name
            if not dest.exists():
                shutil.copy2(wf_file, dest)
        console.print("[green]✓[/green] Created .windsurf/workflows/ (Cascade integration)")

    # CLAUDE.md
    claude_src = TEMPLATE_DIR / "CLAUDE.md"
    claude_dest = project_root / "CLAUDE.md"
    if claude_src.exists() and not claude_dest.exists():
        shutil.copy2(claude_src, claude_dest)
        console.print("[green]✓[/green] Created CLAUDE.md (Claude Code integration)")
