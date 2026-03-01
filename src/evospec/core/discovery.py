"""Continuous Discovery loop — record experiments, update assumptions, log learnings."""

import re
from datetime import date
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.table import Table

from evospec.core.config import find_project_root, load_config, get_paths

console = Console()


def _find_edge_specs(root: Path, config: dict) -> list[Path]:
    """Find all edge/hybrid specs that have discovery sections."""
    paths = get_paths(config)
    specs_dir = root / paths["specs"]
    if not specs_dir.exists():
        return []

    results = []
    for spec_dir in sorted(specs_dir.iterdir()):
        spec_yaml = spec_dir / "spec.yaml"
        if not spec_yaml.exists():
            continue
        spec = yaml.safe_load(spec_yaml.read_text()) or {}
        if spec.get("zone") in ("edge", "hybrid"):
            results.append(spec_dir)
    return results


def _show_discovery_dashboard(spec: dict, spec_dir: Path) -> None:
    """Display the discovery status dashboard."""
    discovery = spec.get("discovery", {})
    assumptions = discovery.get("assumptions", [])
    experiments = discovery.get("experiments", [])
    learnings = discovery.get("learnings", [])

    title = spec.get("title", spec_dir.name)
    iteration = discovery.get("iteration", 1)
    zone = spec.get("zone", "?")

    console.print(f"\n[bold]{title}[/bold] [dim](iteration {iteration}, {zone})[/dim]")
    console.print()

    # Assumptions table
    if assumptions:
        table = Table(title="Assumptions")
        table.add_column("ID", style="cyan")
        table.add_column("Statement")
        table.add_column("Category", style="dim")
        table.add_column("Risk")
        table.add_column("Status")

        status_styles = {
            "untested": "[dim]○ untested[/dim]",
            "testing": "[yellow]⟳ testing[/yellow]",
            "validated": "[green]✓ validated[/green]",
            "invalidated": "[red]✗ invalidated[/red]",
            "pivoted": "[magenta]↻ pivoted[/magenta]",
        }

        for a in assumptions:
            status = a.get("status", "untested")
            table.add_row(
                a.get("id", "?"),
                a.get("statement", "")[:60],
                a.get("category", ""),
                a.get("risk", ""),
                status_styles.get(status, status),
            )
        console.print(table)
    else:
        console.print("[yellow]No assumptions defined yet.[/yellow]")

    # Summary
    total = len(assumptions)
    by_status: dict[str, int] = {}
    for a in assumptions:
        s = a.get("status", "untested")
        by_status[s] = by_status.get(s, 0) + 1

    if total:
        parts = [f"{v} {k}" for k, v in sorted(by_status.items())]
        console.print(f"\n[dim]Assumptions: {', '.join(parts)}[/dim]")

    console.print(f"[dim]Experiments run: {len(experiments)}[/dim]")
    console.print(f"[dim]Learnings logged: {len(learnings)}[/dim]")

    if learnings:
        latest = learnings[-1]
        console.print(f"[dim]Latest learning: \"{latest.get('learning', '')}\"[/dim]")

    # Kill deadline warning
    kill_deadline = discovery.get("kill_deadline", "")
    if kill_deadline:
        try:
            dl = date.fromisoformat(kill_deadline)
            days_left = (dl - date.today()).days
            if days_left <= 0:
                console.print(f"\n[bold red]⚠ KILL DEADLINE REACHED — decision required[/bold red]")
            elif days_left <= 7:
                console.print(f"\n[yellow]⚠ Kill deadline in {days_left} day(s)[/yellow]")
        except ValueError:
            pass

    # Next checkpoint
    next_cp = discovery.get("next_checkpoint", "")
    if next_cp:
        console.print(f"[dim]Next checkpoint: {next_cp}[/dim]")

    console.print()


def record_learning(spec_path: str | None = None) -> None:
    """Interactive flow to record experiment results and update assumptions."""
    root = find_project_root()
    if root is None:
        console.print("[red]✗ No evospec.yaml found. Run `evospec init` first.[/red]")
        return

    config = load_config(root)

    # Find the spec
    if spec_path:
        spec_dir = root / spec_path
    else:
        edge_specs = _find_edge_specs(root, config)
        if not edge_specs:
            console.print("[yellow]No edge/hybrid specs found.[/yellow]")
            return

        if len(edge_specs) == 1:
            spec_dir = edge_specs[0]
        else:
            console.print("[bold]Available discovery specs:[/bold]")
            for i, sd in enumerate(edge_specs, 1):
                spec = yaml.safe_load((sd / "spec.yaml").read_text()) or {}
                console.print(f"  {i}. {spec.get('title', sd.name)} ({spec.get('zone', '?')})")

            choice = click.prompt("Choose a spec", type=int, default=1)
            if choice < 1 or choice > len(edge_specs):
                console.print("[red]Invalid choice.[/red]")
                return
            spec_dir = edge_specs[choice - 1]

    spec_yaml_path = spec_dir / "spec.yaml"
    if not spec_yaml_path.exists():
        console.print(f"[red]✗ No spec.yaml at {spec_dir}[/red]")
        return

    spec = yaml.safe_load(spec_yaml_path.read_text()) or {}
    discovery = spec.setdefault("discovery", {})
    assumptions = discovery.setdefault("assumptions", [])
    experiments = discovery.setdefault("experiments", [])
    learnings_list = discovery.setdefault("learnings", [])

    # Show dashboard
    _show_discovery_dashboard(spec, spec_dir)

    if not assumptions:
        console.print("[yellow]Add assumptions to spec.yaml first (discovery.assumptions[]).[/yellow]")
        return

    # Select assumption
    assumption_id = click.prompt(
        "Which assumption was tested?",
        type=str,
        default=assumptions[0].get("id", "A-001"),
    )

    target = None
    for a in assumptions:
        if a.get("id") == assumption_id:
            target = a
            break

    if target is None:
        console.print(f"[red]✗ Assumption {assumption_id} not found.[/red]")
        return

    console.print(f"\n[bold]Testing: {target.get('statement', assumption_id)}[/bold]")

    # Collect experiment data
    exp_type = click.prompt(
        "Experiment type",
        type=click.Choice(["prototype", "interview", "survey", "A-B-test", "wizard-of-oz", "analytics", "spike"]),
    )
    description = click.prompt("What did you do?")
    sample_size = click.prompt("Sample size (N)", type=int, default=0)
    result = click.prompt("Result (what happened?)")
    confidence = click.prompt(
        "Confidence",
        type=click.Choice(["high", "medium", "low"]),
        default="medium",
    )
    decision = click.prompt(
        "Decision",
        type=click.Choice(["continue", "pivot", "kill", "promote-to-core"]),
        default="continue",
    )
    learning_text = click.prompt("What did you learn? (one sentence)")

    # Generate experiment ID
    max_exp = 0
    for e in experiments:
        eid = e.get("id", "")
        if eid.startswith("EXP-"):
            try:
                max_exp = max(max_exp, int(eid.split("-")[1]))
            except (ValueError, IndexError):
                pass
    exp_id = f"EXP-{max_exp + 1:03d}"

    today = date.today().isoformat()

    # Create experiment
    experiment = {
        "id": exp_id,
        "assumption_id": assumption_id,
        "type": exp_type,
        "description": description,
        "started_at": today,
        "completed_at": today,
        "sample_size": sample_size,
        "result": result,
        "confidence": confidence,
        "decision": decision,
        "next_experiment": "",
    }
    experiments.append(experiment)

    # Update assumption status
    if decision == "promote-to-core":
        target["status"] = "validated"
    elif decision == "kill":
        target["status"] = "invalidated"
    elif decision == "pivot":
        target["status"] = "pivoted"
        pivot_to = click.prompt("Pivot to what?", default="")
        target["pivot_to"] = pivot_to
        discovery["iteration"] = discovery.get("iteration", 1) + 1
    elif confidence == "high":
        if "positive" in result.lower() or "success" in result.lower() or "yes" in result.lower():
            target["status"] = "validated"
        elif "negative" in result.lower() or "fail" in result.lower() or "no" in result.lower():
            target["status"] = "invalidated"
        else:
            target["status"] = "testing"
    else:
        target["status"] = "testing"

    target["result"] = result
    target["result_date"] = today
    target["learning"] = learning_text

    # Log learning
    learning_entry = {
        "date": today,
        "iteration": discovery.get("iteration", 1),
        "experiment_id": exp_id,
        "learning": learning_text,
        "impact": f"Decision: {decision}",
        "spec_changed": decision in ("pivot", "kill", "promote-to-core"),
    }
    learnings_list.append(learning_entry)

    # Save
    spec["updated_at"] = today
    with open(spec_yaml_path, "w") as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # Report
    console.print()
    console.print(f"[green]✓[/green] Recorded experiment [cyan]{exp_id}[/cyan]")
    console.print(f"  Assumption {assumption_id}: {target['status']}")
    console.print(f"  Decision: [bold]{decision}[/bold]")
    console.print(f"  Iteration: {discovery.get('iteration', 1)}")

    # Suggest next action
    console.print()
    if decision == "continue":
        console.print("[dim]Next: design follow-up experiment for this assumption.[/dim]")
    elif decision == "pivot":
        console.print("[dim]Next: update discovery-spec.md with new direction. Run `/evospec.discover` to iterate.[/dim]")
    elif decision == "kill":
        console.print("[dim]Next: run `evospec feature update <id> --status killed` to close the feature.[/dim]")
    elif decision == "promote-to-core":
        console.print("[dim]Next: run `/evospec.contract` to codify this as an invariant in a domain contract.[/dim]")

    # Check if all high-risk assumptions are resolved
    high_risk = [a for a in assumptions if a.get("risk") == "high"]
    high_resolved = [a for a in high_risk if a.get("status") in ("validated", "invalidated", "pivoted")]
    if high_risk and len(high_resolved) == len(high_risk):
        console.print()
        console.print("[bold green]All high-risk assumptions resolved![/bold green]")
        console.print("[dim]Consider moving to implementation: `/evospec.tasks`[/dim]")
