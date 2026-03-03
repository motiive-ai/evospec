"""Initialize EvoSpec in a project."""

import shutil
from datetime import date
from pathlib import Path

from rich.console import Console

from evospec.core.config import get_paths

console = Console()

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def init_project(
    name: str,
    description: str = "",
    detection: "ProjectDetection | None" = None,
    specs_dir: str | None = None,
) -> None:
    """Initialize EvoSpec directory structure and config in the current directory.

    Args:
        name: Project name.
        description: Short project description.
        detection: Optional auto-detected project stack (from ``evospec prompt --detect``).
        specs_dir: Optional custom spec folder prefix (e.g., 'evospec' or '.evospec').
                   Sets paths.specs to '{specs_dir}/changes' and paths.domain to '{specs_dir}/domain'.
    """
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

    # Apply custom spec folder if provided
    if specs_dir or detection:
        import yaml as _yaml

        config_data = _yaml.safe_load(config_content) or {}

        # Custom spec folder paths
        if specs_dir:
            specs_dir = specs_dir.rstrip("/")
            paths = config_data.get("paths", {})
            paths["specs"] = f"{specs_dir}/changes"
            paths["domain"] = f"{specs_dir}/domain"
            paths["templates"] = f"{specs_dir}/_templates"
            paths["checks"] = f"{specs_dir}/checks"
            config_data["paths"] = paths

        # Pre-fill reverse config from detection results
        if detection:
            reverse = config_data.get("reverse", {})
            if detection.framework and not reverse.get("framework"):
                reverse["framework"] = detection.framework
            if detection.source_dirs and not reverse.get("source_dirs"):
                reverse["source_dirs"] = detection.source_dirs
            config_data["reverse"] = reverse

        config_content = _yaml.dump(config_data, default_flow_style=False, sort_keys=False)

    with open(config_path, "w") as f:
        f.write(config_content)

    console.print(f"[green]✓[/green] Created evospec.yaml")

    # Create directory structure (use configured paths, not defaults)
    import yaml as _yaml

    _config_data = _yaml.safe_load(config_content) or {}
    configured_paths = get_paths(_config_data)
    dirs_to_create = [
        configured_paths["specs"],
        configured_paths["templates"],
        configured_paths["adrs"],
        configured_paths["domain"],
        configured_paths["checks"],
    ]

    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓[/green] Created {dir_path}/")

    # Copy templates to project
    templates_dest = project_root / configured_paths["templates"]
    for template_file in TEMPLATE_DIR.glob("*.md"):
        dest = templates_dest / template_file.name
        if not dest.exists():
            shutil.copy2(template_file, dest)
            console.print(f"[green]✓[/green] Copied template {template_file.name}")

    # Create domain file stubs (entities, contexts, features, skills)
    domain_dir = project_root / configured_paths["domain"]
    _create_domain_stubs(domain_dir)

    # Create glossary stub
    glossary_path = project_root / configured_paths["domain"] / "glossary.md"
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
    context_map_path = project_root / configured_paths["domain"] / "context-map.md"
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
    adr_path = project_root / configured_paths["adrs"] / "0001-adopt-evospec.md"
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
    console.print("[dim]AI agent integration (generated from canonical workflow specs):[/dim]")
    console.print("  [dim]Windsurf: /evospec.discover, /evospec.contract, /evospec.tasks, /evospec.implement, /evospec.check[/dim]")
    console.print("  [dim]Claude Code: reads CLAUDE.md automatically[/dim]")
    console.print("  [dim]Cursor: reads .cursor/rules/ automatically[/dim]")
    console.print("  [dim]Regenerate: evospec generate agents[/dim]")


def _create_domain_stubs(domain_dir: Path) -> None:
    """Create stub domain files (entities.yaml, contexts.yaml, features.yaml)."""
    domain_dir.mkdir(parents=True, exist_ok=True)

    entities_path = domain_dir / "entities.yaml"
    if not entities_path.exists():
        entities_path.write_text(
            "# Domain Entity Registry\n"
            "# Canonical source of truth for domain entities.\n"
            "# Populated manually or via `evospec reverse db`.\n"
            "#\n"
            "# Each entity belongs to a bounded context and describes:\n"
            "# - fields (name, type, constraints)\n"
            "# - relationships to other entities\n"
            "# - invariants that reference this entity\n"
            "#\n"
            "# Example:\n"
            "# - name: \"Order\"\n"
            "#   context: \"orders\"\n"
            "#   table: \"orders\"\n"
            "#   aggregate_root: true\n"
            "#   description: \"Represents a customer purchase with line items and payment.\"\n"
            "#   fields:\n"
            "#     - name: \"id\"\n"
            "#       type: \"UUID\"\n"
            "#     - name: \"status\"\n"
            "#       type: \"String\"\n"
            "#       constraints: \"draft | submitted | shipped | delivered | cancelled\"\n"
            "#   relationships:\n"
            "#     - target: \"LineItem\"\n"
            "#       type: \"one-to-many\"\n"
            "#   invariants:\n"
            "#     - \"ORD-INV-001\"\n"
            "[]\n"
        )
        console.print(f"[green]✓[/green] Created {entities_path.relative_to(Path.cwd())}")

    contexts_path = domain_dir / "contexts.yaml"
    if not contexts_path.exists():
        contexts_path.write_text(
            "# Bounded Contexts Registry\n"
            "# Defines the bounded contexts in your domain (DDD strategic design).\n"
            "#\n"
            "# Example:\n"
            "# - name: \"orders\"\n"
            "#   owner: \"commerce-team\"\n"
            "#   type: \"core\"           # core | supporting | generic\n"
            "#   description: \"Order lifecycle from cart to delivery.\"\n"
            "[]\n"
        )
        console.print(f"[green]✓[/green] Created {contexts_path.relative_to(Path.cwd())}")

    features_path = domain_dir / "features.yaml"
    if not features_path.exists():
        features_path.write_text(
            "# Features Registry\n"
            "# Tracks feature lifecycle across the Knowledge Funnel.\n"
            "# Managed via `evospec feature add/update/list`.\n"
            "#\n"
            "# Lifecycle: discovery → specifying → implementing → validating → shipped / killed\n"
            "# Knowledge: mystery → heuristic → algorithm\n"
            "#\n"
            "# A change (specs/changes/) may create a feature, advance it, or have nothing\n"
            "# to do with features (e.g. a bugfix). Not every change is a feature.\n"
            "[]\n"
        )
        console.print(f"[green]✓[/green] Created {features_path.relative_to(Path.cwd())}")

    api_contracts_path = domain_dir / "api-contracts.yaml"
    if not api_contracts_path.exists():
        api_contracts_path.write_text(
            "# API Contracts\n"
            "# Structured API contracts for external consumers and AI agents.\n"
            "# Served via MCP as evospec://api-catalog and get_api_contract() tool.\n"
            "#\n"
            "# Example:\n"
            "# contracts:\n"
            "#   - endpoint: \"GET /api/orders/{orderId}\"\n"
            "#     description: \"Get order details\"\n"
            "#     params:\n"
            "#       - name: orderId\n"
            "#         in: path\n"
            "#         type: String\n"
            "#         format: UUID\n"
            "#         required: true\n"
            "#     response:\n"
            "#       200:\n"
            "#         fields:\n"
            "#           - name: orderId\n"
            "#             type: String\n"
            "#           - name: status\n"
            "#             type: OrderStatus\n"
            "#     auth: \"bearer token\"\n"
            "#     tags: [\"orders\", \"read\"]\n"
            "contracts: []\n"
        )
        console.print(f"[green]✓[/green] Created {api_contracts_path.relative_to(Path.cwd())}")

    file_schemas_path = domain_dir / "file-schemas.yaml"
    if not file_schemas_path.exists():
        file_schemas_path.write_text(
            "# File Schemas\n"
            "# Describes file formats and response structures for external consumers.\n"
            "# Served via MCP as get_file_schema() tool.\n"
            "#\n"
            "# Example:\n"
            "# schemas:\n"
            "#   - name: \"OrderExport\"\n"
            "#     format: json\n"
            "#     description: \"JSON export of order data\"\n"
            "#     version: \"v1\"\n"
            "#     structure:\n"
            "#       - name: orderId\n"
            "#         type: String\n"
            "#       - name: items\n"
            "#         type: List<LineItem>\n"
            "#     example: |\n"
            "#       { \"orderId\": \"a1b2c3d4\", \"items\": [...] }\n"
            "schemas: []\n"
        )
        console.print(f"[green]✓[/green] Created {file_schemas_path.relative_to(Path.cwd())}")

    skills_path = domain_dir / "skills.yaml"
    if not skills_path.exists():
        skills_path.write_text(
            "# Implementation Skills\n"
            "# Project-specific coding rules that AI agents should follow.\n"
            "# These are injected into generated agent files (CLAUDE.md, .windsurf/, .cursor/).\n"
            "# Served via MCP as evospec://skills.\n"
            "#\n"
            "# Categories: error-handling, testing, architecture, naming, dependencies, security\n"
            "# (you can add your own categories)\n"
            "#\n"
            "# Example:\n"
            "# skills:\n"
            "#   - category: \"error-handling\"\n"
            "#     rules:\n"
            "#       - \"Use Result<T, E> pattern for domain operations\"\n"
            "#       - \"Map all external API errors to domain-specific error types\"\n"
            "#   - category: \"testing\"\n"
            "#     rules:\n"
            "#       - \"Write integration tests for every API endpoint\"\n"
            "#       - \"Use factory functions (not fixtures) for test data\"\n"
            "skills: []\n"
        )
        console.print("[green]✓[/green] Created skills.yaml (implementation skills for AI agents)")


def _setup_ai_agents(project_root: Path) -> None:
    """Generate AI agent integration files from canonical workflow specs."""
    from evospec.core.agents import generate_agents

    results = generate_agents(dest=project_root)
    for platform, files in results.items():
        if files:
            if platform == "windsurf":
                console.print("[green]✓[/green] Generated .windsurf/workflows/ (Cascade integration)")
            elif platform == "claude":
                console.print("[green]✓[/green] Generated CLAUDE.md (Claude Code integration)")
            elif platform == "cursor":
                console.print("[green]✓[/green] Generated .cursor/rules/ (Cursor integration)")
