"""EvoSpec CLI — Progressive specs at the edge. Contracts in the core."""

from pathlib import Path

import click

from evospec import __version__


@click.group()
@click.version_option(version=__version__, prog_name="evospec")
def cli() -> None:
    """EvoSpec: Progressive specs at the edge. Contracts in the core.

    A spec-driven delivery toolkit that adapts specification rigor to change risk.
    """


@cli.command()
@click.option("--name", prompt="Project name", help="Name of the project.")
@click.option("--description", default="", help="Short project description.")
@click.option("--detect", is_flag=True, help="Auto-detect project stack and pre-fill reverse config.")
@click.option("--specs-dir", default=None, help="Custom spec folder path (e.g., 'evospec' or '.evospec'). Sets paths.specs and paths.domain.")
def init(name: str, description: str, detect: bool, specs_dir: str | None) -> None:
    """Initialize EvoSpec in the current project."""
    from evospec.core.init import init_project

    detection = None
    if detect:
        from evospec.core.prompt import detect_project_stack

        detection = detect_project_stack(Path.cwd())

    init_project(name=name, description=description, detection=detection, specs_dir=specs_dir)


@cli.command()
@click.argument("title")
@click.option("--zone", type=click.Choice(["edge", "hybrid", "core"]), default=None)
@click.option(
    "--type", "change_type",
    type=click.Choice(["experiment", "improvement", "bugfix"]),
    default=None,
    help="Type of change (experiment/improvement/bugfix). Defaults based on zone.",
)
def new(title: str, zone: str | None, change_type: str | None) -> None:
    """Create a new change spec."""
    from evospec.core.new_spec import create_spec

    create_spec(title=title, zone=zone, change_type=change_type)


@cli.command()
@click.argument("spec_path", required=False)
def classify(spec_path: str | None) -> None:
    """Interactively classify a change by zone (edge/hybrid/core)."""
    from evospec.core.classify import classify_change

    classify_change(spec_path=spec_path)


@cli.group()
def adr() -> None:
    """Manage Architecture Decision Records."""


@adr.command("new")
@click.argument("title")
def adr_new(title: str) -> None:
    """Create a new ADR."""
    from evospec.core.adr import create_adr

    create_adr(title=title)


@adr.command("list")
def adr_list() -> None:
    """List all ADRs."""
    from evospec.core.adr import list_adrs

    list_adrs()


@cli.command()
@click.option("--strict", is_flag=True, help="Fail on warnings (for CI).")
@click.option("--run-fitness", is_flag=True, help="Also execute fitness function tests.")
def check(strict: bool, run_fitness: bool) -> None:
    """Run fitness function checks and spec validations."""
    from evospec.core.check import run_checks, run_fitness_functions

    run_checks(strict=strict)

    if run_fitness:
        passed, failed, skipped = run_fitness_functions()
        if failed and strict:
            raise SystemExit(1)


@cli.command()
@click.option("--since", default=None, help="Git ref (commit, tag, branch) to compare from.")
@click.option("--generate", is_flag=True, help="Create draft change specs from detected drift.")
@click.option("--ci", is_flag=True, help="Machine-readable JSON output for CI pipelines.")
def sync(since: str | None, generate: bool, ci: bool) -> None:
    """Detect spec drift by analyzing git diffs against domain specs."""
    from evospec.core.sync import run_sync

    run_sync(since=since, generate=generate, ci=ci)


@cli.command()
@click.option("--strict", is_flag=True, help="Exit non-zero on failures (for CI gates).")
@click.option("--format", "output_format", type=click.Choice(["text", "json", "markdown"]),
              default="text", help="Output format.")
def verify(strict: bool, output_format: str) -> None:
    """Verify spec accuracy against implementation code."""
    from evospec.core.verify import run_verify

    run_verify(strict=strict, output_format=output_format)


@cli.command()
@click.option("--from-history", "from_history", is_flag=True, required=True,
              help="Analyze git history to detect feature clusters and generate retroactive specs.")
@click.option("--since", default=None, help="Git ref (commit, tag, branch) to start analysis from.")
@click.option("--min-cluster-size", default=2, type=int, help="Minimum files per cluster (default: 2).")
@click.option("--max-clusters", default=20, type=int, help="Maximum clusters to generate (default: 20).")
def capture(from_history: bool, since: str | None, min_cluster_size: int, max_clusters: int) -> None:
    """Generate retroactive specs from existing codebase."""
    if from_history:
        from evospec.core.capture import run_capture_from_history

        run_capture_from_history(
            since=since,
            min_cluster_size=min_cluster_size,
            max_clusters=max_clusters,
        )


@cli.group()
def reverse() -> None:
    """Reverse-engineer domain contracts from code."""


@reverse.command("api")
@click.option(
    "--framework",
    type=click.Choice([
        "fastapi", "django", "flask",
        "gin", "echo", "fiber", "chi", "gorilla", "net-http",
        "spring",
        "express", "nextjs", "nestjs", "hono", "fastify",
    ]),
)
@click.option("--source", default=None, help="Source directory to scan.")
@click.option("--deep", is_flag=True, help="Deep extraction: DTO fields, validation, auth, error responses.")
@click.option("--write", is_flag=True, help="Write deep output to specs/domain/api-contracts.yaml (requires --deep).")
def reverse_api(framework: str | None, source: str | None, deep: bool, write: bool) -> None:
    """Reverse-engineer API endpoints into spec stubs."""
    from evospec.reverse.api import reverse_engineer_api

    reverse_engineer_api(framework=framework, source=source, deep=deep, write=write)


@reverse.command("db")
@click.option("--source", default=None, help="Migrations or models directory.")
@click.option("--deep", is_flag=True, help="Deep extraction: invariant detection, state machine detection.")
@click.option("--write", is_flag=True, help="Write deep output to specs/domain/ files (requires --deep).")
def reverse_db(source: str | None, deep: bool, write: bool) -> None:
    """Reverse-engineer database schema into domain contract stubs."""
    from evospec.reverse.db import reverse_engineer_db

    reverse_engineer_db(source=source, deep=deep, write=write)


@reverse.command("cli")
@click.option("--source", default=None, help="Source directory to scan.")
def reverse_cli(source: str | None) -> None:
    """Reverse-engineer CLI commands and Python module structure into spec stubs."""
    from evospec.reverse.cli import reverse_engineer_cli

    reverse_engineer_cli(source=source)


@reverse.command("deps")
@click.option("--source", default=None, help="Source directory to scan for API calls.")
@click.option("--deep", is_flag=True, help="Deep extraction: payload schemas, message queues, storage ops.")
@click.option("--write", is_flag=True, help="Write deep output to specs/domain/ files (requires --deep).")
def reverse_deps(source: str | None, deep: bool, write: bool) -> None:
    """Reverse-engineer cross-system API dependencies from source code.

    Scans source files for HTTP calls (fetch, axios, requests, etc.) and maps
    them to known backend endpoints declared in core/hybrid spec traceability.
    """
    from evospec.reverse.deps import reverse_engineer_deps

    reverse_engineer_deps(source=source, deep=deep, write=write)


@cli.command()
def render() -> None:
    """Render all specs into a consolidated markdown document."""
    from evospec.core.render import render_specs

    render_specs()


@cli.command()
def status() -> None:
    """Show the status of all change specs."""
    from evospec.core.status import show_status

    show_status()


@cli.group()
def feature() -> None:
    """Manage the features registry."""


@feature.command("list")
def feature_list() -> None:
    """List all registered features and their lifecycle status."""
    from evospec.core.features import list_features

    list_features()


@feature.command("add")
@click.argument("title")
@click.option("--zone", type=click.Choice(["edge", "hybrid", "core"]), default="edge")
@click.option("--owner", default="")
def feature_add(title: str, zone: str, owner: str) -> None:
    """Register a new feature in the features registry."""
    from evospec.core.features import add_feature

    add_feature(title=title, zone=zone, owner=owner)


@feature.command("update")
@click.argument("feature_id")
@click.option("--status", type=click.Choice(
    ["discovery", "specifying", "implementing", "validating", "shipped", "killed"]
))
@click.option("--zone", type=click.Choice(["edge", "hybrid", "core"]))
@click.option("--knowledge-stage", type=click.Choice(["mystery", "heuristic", "algorithm"]))
def feature_update(
    feature_id: str,
    status: str | None,
    zone: str | None,
    knowledge_stage: str | None,
) -> None:
    """Update a feature's status, zone, or knowledge stage."""
    from evospec.core.features import update_feature

    update_feature(
        feature_id=feature_id,
        status=status,
        zone=zone,
        knowledge_stage=knowledge_stage,
    )


@cli.command()
@click.argument("spec_path", required=False)
def learn(spec_path: str | None) -> None:
    """Record experiment results and update discovery assumptions."""
    from evospec.core.discovery import record_learning

    record_learning(spec_path=spec_path)


@cli.command()
def fitness() -> None:
    """Run all fitness functions defined in spec.yaml files."""
    from evospec.core.check import run_fitness_functions

    passed, failed, skipped = run_fitness_functions()
    if failed:
        raise SystemExit(1)


@cli.command()
@click.option("--detect", is_flag=True, help="Auto-detect project language, framework, ORM, and source dirs.")
@click.option(
    "--format", "fmt",
    type=click.Choice(["markdown", "json"]),
    default="markdown",
    help="Output format (default: markdown).",
)
def prompt(detect: bool, fmt: str) -> None:
    """Emit an AI bootstrap prompt with EvoSpec context.

    Gives any AI agent everything it needs to configure EvoSpec on a project
    without reading EvoSpec source code. Works without evospec.yaml (pre-init).
    """
    from evospec.core.prompt import generate_bootstrap_json, generate_bootstrap_prompt

    if fmt == "json":
        output = generate_bootstrap_json(detect=detect)
    else:
        output = generate_bootstrap_prompt(detect=detect)

    click.echo(output)


@cli.command()
def serve() -> None:
    """Start the EvoSpec MCP server (for AI agent integration)."""
    from evospec.mcp.server import main as mcp_main

    mcp_main()


@cli.group()
def generate() -> None:
    """Generate project artifacts from canonical sources."""


@generate.command("agents")
@click.option(
    "--platform",
    type=click.Choice(["windsurf", "claude", "cursor", "skills", "all"]),
    default="all",
    help="Target platform (default: all).",
)
def generate_agents_cmd(platform: str) -> None:
    """Generate AI agent integration files from canonical workflow specs.

    Reads platform-agnostic workflow YAMLs and emits platform-specific files:
    Windsurf (.windsurf/workflows/), Claude Code (CLAUDE.md), Cursor (.cursor/rules/),
    Skills (.agents/skills/).
    """
    from pathlib import Path

    from rich.console import Console

    from evospec.core.agents import generate_agents

    console = Console()
    dest = Path.cwd()
    platforms = None if platform == "all" else [platform]

    results = generate_agents(dest=dest, platforms=platforms)

    for plat, files in results.items():
        console.print(f"\n[bold]{plat}[/bold]: {len(files)} file(s)")
        for f in files:
            console.print(f"  [green]✓[/green] {f.relative_to(dest)}")

    total = sum(len(f) for f in results.values())
    console.print(f"\n[bold green]Generated {total} file(s) across {len(results)} platform(s).[/bold green]")


if __name__ == "__main__":
    cli()
