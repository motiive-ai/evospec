"""Interactive classification of changes by zone."""

from pathlib import Path

import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt

from evospec.core.config import find_project_root, load_config, get_paths

console = Console()

CLASSIFICATION_QUESTIONS = [
    ("touches_persistence", "Does this change alter database schema, state storage, or data models?"),
    ("touches_auth", "Does this change affect authentication, authorization, or identity?"),
    ("touches_billing", "Does this change affect billing, plans, subscriptions, or pricing?"),
    ("touches_audit", "Does this change affect audit trails, compliance, or regulatory requirements?"),
    ("touches_multi_tenancy", "Does this change affect tenant isolation or multi-tenancy boundaries?"),
    ("crosses_context_boundary", "Does this change span multiple bounded contexts?"),
    ("is_hypothesis", "Is this change driven by a hypothesis that needs validation?"),
]

CORE_TRIGGERS = {
    "touches_persistence",
    "touches_auth",
    "touches_billing",
    "touches_audit",
    "touches_multi_tenancy",
}


def classify_change(spec_path: str | None = None) -> None:
    """Interactively classify a change and update its spec.yaml."""
    root = find_project_root()
    if root is None:
        console.print("[red]✗ No evospec.yaml found. Run `evospec init` first.[/red]")
        return

    config = load_config(root)
    paths = get_paths(config)

    # Find spec
    if spec_path:
        spec_dir = root / spec_path
    else:
        specs_root = root / paths["specs"]
        if not specs_root.exists():
            console.print("[red]✗ No specs directory found.[/red]")
            return

        spec_dirs = sorted(
            [d for d in specs_root.iterdir() if d.is_dir() and (d / "spec.yaml").exists()],
            key=lambda d: d.name,
            reverse=True,
        )

        if not spec_dirs:
            console.print("[red]✗ No specs found. Run `evospec new` first.[/red]")
            return

        console.print("[bold]Available specs:[/bold]")
        for i, d in enumerate(spec_dirs, 1):
            with open(d / "spec.yaml") as f:
                spec = yaml.safe_load(f)
            title = spec.get("title", d.name)
            zone = spec.get("zone", "?")
            status = spec.get("status", "?")
            console.print(f"  {i}. {title} [dim]({zone}/{status})[/dim]")

        choice = Prompt.ask("Select spec", choices=[str(i) for i in range(1, len(spec_dirs) + 1)])
        spec_dir = spec_dirs[int(choice) - 1]

    spec_yaml_path = spec_dir / "spec.yaml"
    if not spec_yaml_path.exists():
        console.print(f"[red]✗ No spec.yaml found in {spec_dir}[/red]")
        return

    with open(spec_yaml_path) as f:
        spec = yaml.safe_load(f)

    console.print()
    console.print(f"[bold]Classifying:[/bold] {spec.get('title', spec_dir.name)}")
    console.print()

    # Ask classification questions
    answers: dict[str, bool] = {}
    for key, question in CLASSIFICATION_QUESTIONS:
        answers[key] = Confirm.ask(f"  {question}", default=False)

    # Determine reversibility
    console.print()
    reversibility = Prompt.ask(
        "  How hard is it to undo this change?",
        choices=["trivial", "moderate", "difficult", "irreversible"],
        default="moderate",
    )

    # Auto-determine zone
    core_hits = sum(1 for key in CORE_TRIGGERS if answers.get(key, False))
    is_hypothesis = answers.get("is_hypothesis", False)

    if core_hits >= 2 or reversibility == "irreversible":
        suggested_zone = "core"
    elif core_hits == 1 or answers.get("crosses_context_boundary", False):
        suggested_zone = "hybrid"
    else:
        suggested_zone = "edge"

    # Risk level
    if core_hits >= 3 or reversibility == "irreversible":
        risk_level = "critical"
    elif core_hits >= 2:
        risk_level = "high"
    elif core_hits >= 1:
        risk_level = "medium"
    else:
        risk_level = "low"

    console.print()
    console.print(f"[bold]Suggested zone:[/bold] [cyan]{suggested_zone}[/cyan]")
    console.print(f"[bold]Risk level:[/bold] [cyan]{risk_level}[/cyan]")
    console.print()

    zone = Prompt.ask(
        "  Accept zone or override?",
        choices=["edge", "hybrid", "core"],
        default=suggested_zone,
    )

    rationale = Prompt.ask("  Rationale (why this zone?)", default="")

    # Update spec.yaml
    spec["zone"] = zone
    spec["classification"] = {
        **answers,
        "reversibility": reversibility,
        "risk_level": risk_level,
        "rationale": rationale,
    }

    with open(spec_yaml_path, "w") as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    console.print()
    console.print(f"[bold green]✓ Classified as {zone} (risk: {risk_level})[/bold green]")

    # Generate missing artifacts
    template_dir = Path(__file__).parent.parent / "templates"

    if zone in ("edge", "hybrid") and not (spec_dir / "discovery-spec.md").exists():
        _copy_template(template_dir / "discovery-spec.md", spec_dir / "discovery-spec.md", spec)
        console.print("[green]✓[/green] Generated discovery-spec.md")

    if zone in ("core", "hybrid") and not (spec_dir / "domain-contract.md").exists():
        _copy_template(template_dir / "domain-contract.md", spec_dir / "domain-contract.md", spec)
        console.print("[green]✓[/green] Generated domain-contract.md")

    if zone == "core":
        console.print()
        console.print(
            "[yellow]⚠ Core zone requires:[/yellow]"
        )
        console.print("  • Bounded context in spec.yaml")
        console.print("  • Invariants with enforcement mechanisms")
        console.print("  • At least one fitness function")


def _copy_template(template_path: Path, output_path: Path, spec: dict) -> None:
    """Copy template with basic variable substitution."""
    with open(template_path) as f:
        content = f.read()

    content = (
        content
        .replace("{{ title }}", spec.get("title", ""))
        .replace("{{ zone }}", spec.get("zone", ""))
        .replace("{{ status }}", spec.get("status", "draft"))
        .replace("{{ bounded_context }}", spec.get("bounded_context", ""))
        .replace("{{ created_at }}", spec.get("created_at", ""))
    )

    output_path.write_text(content)
