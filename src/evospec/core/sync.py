"""Detect spec drift by analyzing git diffs against domain specs.

Compares what's declared in specs/domain/ (entities, API contracts, invariants)
against changes detected in the codebase via git diff. Produces a drift report
with a 0–100% score.

Key invariant: SYNC-001 — sync MUST NOT modify spec files without --generate flag.
"""

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

from evospec.core.config import find_project_root, get_paths, load_config

console = Console()


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class FieldChange:
    entity: str
    field_name: str
    change_type: str  # "added" | "removed" | "modified"
    detail: str = ""


@dataclass
class EndpointChange:
    endpoint: str
    change_type: str  # "added" | "removed" | "modified"
    detail: str = ""


@dataclass
class InvariantImpact:
    invariant_id: str
    statement: str
    reason: str


@dataclass
class DriftReport:
    entity_changes: list[FieldChange] = field(default_factory=list)
    endpoint_changes: list[EndpointChange] = field(default_factory=list)
    invariant_impacts: list[InvariantImpact] = field(default_factory=list)
    drift_score: float = 0.0
    commits_analyzed: int = 0
    since: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_changes": [
                {"entity": c.entity, "field": c.field_name, "type": c.change_type, "detail": c.detail}
                for c in self.entity_changes
            ],
            "endpoint_changes": [
                {"endpoint": c.endpoint, "type": c.change_type, "detail": c.detail}
                for c in self.endpoint_changes
            ],
            "invariant_impacts": [
                {"id": i.invariant_id, "statement": i.statement, "reason": i.reason}
                for i in self.invariant_impacts
            ],
            "drift_score": round(self.drift_score, 1),
            "commits_analyzed": self.commits_analyzed,
            "since": self.since,
        }


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def _run_git(args: list[str], cwd: Path) -> str:
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=str(cwd),
            timeout=30,
        )
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def _get_diff_files(root: Path, since: str | None) -> list[str]:
    """Get list of changed files from git diff."""
    args = ["diff", "--name-only"]
    if since:
        args.append(f"{since}..HEAD")
    else:
        # Default: compare working tree + staged changes against last commit
        args.append("HEAD")
    output = _run_git(args, root)
    if not output.strip():
        # Also check staged
        staged = _run_git(["diff", "--name-only", "--cached"], root)
        output = (output + "\n" + staged).strip()
    return [f for f in output.strip().split("\n") if f]


def _get_diff_content(root: Path, since: str | None) -> str:
    """Get unified diff content."""
    args = ["diff", "-U3"]
    if since:
        args.append(f"{since}..HEAD")
    else:
        args.append("HEAD")
    return _run_git(args, root)


def _count_commits(root: Path, since: str | None) -> int:
    """Count commits in the analysis window."""
    if not since:
        return 1
    output = _run_git(["rev-list", "--count", f"{since}..HEAD"], root)
    try:
        return int(output.strip())
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# Entity drift detection
# ---------------------------------------------------------------------------


# Patterns for detecting entity/model definitions across languages
_ENTITY_PATTERNS = [
    # Python: class Foo(Base/Model/db.Model)
    re.compile(r"class\s+(\w+)\s*\(.*(?:Base|Model|db\.Model)"),
    # Python dataclass / pydantic
    re.compile(r"class\s+(\w+)\s*\(.*(?:BaseModel|Schema)\)"),
    # Java/Kotlin: @Entity class Foo / data class Foo
    re.compile(r"@Entity[^}]*class\s+(\w+)"),
    re.compile(r"data\s+class\s+(\w+)"),
    # TypeScript: @Entity() class Foo
    re.compile(r"@Entity\(\)\s*(?:export\s+)?class\s+(\w+)"),
    # Go struct
    re.compile(r"type\s+(\w+)\s+struct\s*\{"),
]

# Patterns for detecting fields in diff hunks
_FIELD_PATTERNS = [
    # Python: field_name = Column(Type) or field_name: Type
    re.compile(r"^\+\s+(\w+)\s*[=:]\s*(?:Column|Field|mapped_column|db\.Column)\("),
    re.compile(r"^\+\s+(\w+)\s*:\s*(?:str|int|float|bool|Mapped|Optional|list|List|UUID|datetime)"),
    # Java: private Type fieldName;
    re.compile(r"^\+\s+(?:private|protected|public)\s+\S+\s+(\w+)\s*;"),
    # TS: fieldName: type
    re.compile(r"^\+\s+(?:readonly\s+)?(\w+)\s*[?]?\s*:\s*\w+"),
    # Go: FieldName Type `tag`
    re.compile(r'^\+\s+(\w+)\s+\w+\s+`'),
    # Removed fields (same patterns but with -)
    re.compile(r"^-\s+(\w+)\s*[=:]\s*(?:Column|Field|mapped_column|db\.Column)\("),
    re.compile(r"^-\s+(?:private|protected|public)\s+\S+\s+(\w+)\s*;"),
]

# Patterns for API endpoint definitions
_ENDPOINT_PATTERNS = [
    # Python decorators: @app.get("/path"), @router.post("/path")
    re.compile(r'@\w+\.(?:get|post|put|patch|delete)\(\s*["\']([^"\']+)["\']'),
    # Java Spring: @GetMapping("/path"), @PostMapping, @RequestMapping
    re.compile(r'@(?:Get|Post|Put|Patch|Delete|Request)Mapping\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'),
    # Express/Hono/Fastify: app.get("/path", ...), router.post("/path", ...)
    re.compile(r'\.(?:get|post|put|patch|delete)\(\s*["\']([^"\']+)["\']'),
    # Go: r.GET("/path", ...) or group.POST("/path", ...)
    re.compile(r'\.(?:GET|POST|PUT|PATCH|DELETE|Handle|HandleFunc)\(\s*["\']([^"\']+)["\']'),
]


def _detect_entity_changes(
    diff_content: str, spec_entities: list[dict],
) -> list[FieldChange]:
    """Detect entity field additions/removals from diff content."""
    changes: list[FieldChange] = []
    spec_field_map = _build_spec_field_map(spec_entities)

    current_entity = ""
    for line in diff_content.split("\n"):
        # Track which entity/class we're in
        for pattern in _ENTITY_PATTERNS:
            m = pattern.search(line)
            if m:
                current_entity = m.group(1)
                break

        if not current_entity:
            continue

        # Detect field additions
        if line.startswith("+") and not line.startswith("+++"):
            for pattern in _FIELD_PATTERNS[:5]:  # addition patterns
                m = pattern.match(line)
                if m:
                    field_name = m.group(1)
                    # Skip common non-field names
                    if field_name in ("self", "cls", "return", "class", "def", "import"):
                        continue
                    # Check if this field exists in spec
                    spec_fields = spec_field_map.get(current_entity.lower(), set())
                    if field_name.lower() not in spec_fields:
                        changes.append(FieldChange(
                            entity=current_entity,
                            field_name=field_name,
                            change_type="added",
                            detail=f"New field in code, not in spec",
                        ))
                    break

        # Detect field removals
        elif line.startswith("-") and not line.startswith("---"):
            for pattern in _FIELD_PATTERNS[5:]:  # removal patterns
                m = pattern.match(line)
                if m:
                    field_name = m.group(1)
                    if field_name in ("self", "cls", "return", "class", "def", "import"):
                        continue
                    spec_fields = spec_field_map.get(current_entity.lower(), set())
                    if field_name.lower() in spec_fields:
                        changes.append(FieldChange(
                            entity=current_entity,
                            field_name=field_name,
                            change_type="removed",
                            detail=f"Field removed from code, still in spec",
                        ))
                    break

    return changes


def _detect_endpoint_changes(
    diff_content: str, spec_endpoints: list[str],
) -> list[EndpointChange]:
    """Detect API endpoint additions/removals from diff content."""
    changes: list[EndpointChange] = []
    spec_paths = {_normalize_endpoint(ep) for ep in spec_endpoints}

    for line in diff_content.split("\n"):
        for pattern in _ENDPOINT_PATTERNS:
            m = pattern.search(line)
            if m:
                path = m.group(1)
                norm = _normalize_endpoint(path)
                if line.startswith("+") and norm not in spec_paths:
                    changes.append(EndpointChange(
                        endpoint=path,
                        change_type="added",
                        detail="New endpoint in code, not documented in spec",
                    ))
                elif line.startswith("-") and norm in spec_paths:
                    changes.append(EndpointChange(
                        endpoint=path,
                        change_type="removed",
                        detail="Endpoint removed from code, still documented in spec",
                    ))
                break

    return changes


def _detect_invariant_impacts(
    entity_changes: list[FieldChange],
    endpoint_changes: list[EndpointChange],
    invariants: list[dict],
) -> list[InvariantImpact]:
    """Check if detected changes may affect existing invariants."""
    impacts: list[InvariantImpact] = []
    changed_entities = {c.entity.lower() for c in entity_changes}
    changed_endpoints = {c.endpoint.lower() for c in endpoint_changes}

    for inv in invariants:
        inv_id = inv.get("id", "?")
        statement = inv.get("statement", "")
        stmt_lower = statement.lower()

        reasons = []
        for entity in changed_entities:
            if entity in stmt_lower:
                reasons.append(f"entity '{entity}' changed in code")

        if reasons:
            impacts.append(InvariantImpact(
                invariant_id=inv_id,
                statement=statement,
                reason="; ".join(reasons),
            ))

    return impacts


# ---------------------------------------------------------------------------
# Drift scoring
# ---------------------------------------------------------------------------


def _calculate_drift_score(
    entity_changes: list[FieldChange],
    endpoint_changes: list[EndpointChange],
    total_spec_fields: int,
    total_spec_endpoints: int,
) -> float:
    """Calculate a drift score (0–100%).

    0% = specs perfectly match code.
    100% = specs are completely outdated.
    """
    total_items = total_spec_fields + total_spec_endpoints
    if total_items == 0:
        return 0.0

    drift_items = len(entity_changes) + len(endpoint_changes)
    # Cap at 100%
    return min(100.0, (drift_items / total_items) * 100)


# ---------------------------------------------------------------------------
# Spec generation (--generate flag)
# ---------------------------------------------------------------------------


def _generate_draft_specs(
    report: DriftReport, root: Path, config: dict,
) -> list[Path]:
    """Generate draft change specs from detected drift. Only called with --generate flag."""
    if not report.entity_changes and not report.endpoint_changes:
        return []

    from datetime import date
    paths_cfg = get_paths(config)
    specs_dir = root / paths_cfg["specs"]

    today = date.today().isoformat()
    slug = f"{today}-auto-sync-drift"
    spec_dir = specs_dir / slug
    spec_dir.mkdir(parents=True, exist_ok=True)

    # Build description of changes
    desc_parts = []
    if report.entity_changes:
        entities_touched = sorted({c.entity for c in report.entity_changes})
        desc_parts.append(f"Entity changes: {', '.join(entities_touched)}")
    if report.endpoint_changes:
        eps = sorted({c.endpoint for c in report.endpoint_changes})
        desc_parts.append(f"Endpoint changes: {', '.join(eps[:5])}")

    spec_yaml = {
        "id": slug,
        "title": f"Spec Drift (auto-detected by evospec sync)",
        "zone": "hybrid",
        "change_type": "improvement",
        "status": "draft",
        "created_at": today,
        "updated_at": today,
        "classification": {
            "touches_persistence": any(c.change_type != "removed" for c in report.entity_changes),
            "touches_auth": False,
            "touches_billing": False,
            "touches_audit": False,
            "touches_multi_tenancy": False,
            "hypothesis_driven": False,
            "reversibility": "trivial",
            "risk_level": "low",
            "rationale": "Auto-generated from drift detection. Review and update specs to match implementation.",
        },
        "bounded_context": "",
        "traceability": {
            "endpoints": [c.endpoint for c in report.endpoint_changes],
            "tables": [],
            "modules": [],
        },
        "discovery": {
            "outcome": "; ".join(desc_parts),
            "opportunity": "Keep specs in sync with implementation",
            "kill_criteria": "",
            "assumptions": [],
        },
    }

    spec_path = spec_dir / "spec.yaml"
    spec_path.write_text(
        yaml.dump(spec_yaml, default_flow_style=False, sort_keys=False, allow_unicode=True)
    )

    # Generate a discovery-spec.md with the drift details
    lines = [
        "# Discovery Spec: Spec Drift (auto-generated)",
        "",
        f"> Generated by `evospec sync` on {today}",
        f"> Drift score: {report.drift_score:.1f}%",
        "",
        "## Entity Changes",
        "",
    ]
    if report.entity_changes:
        for c in report.entity_changes:
            symbol = {"added": "+", "removed": "-", "modified": "~"}[c.change_type]
            lines.append(f"  {symbol} {c.entity}.{c.field_name} — {c.detail}")
    else:
        lines.append("  (none)")

    lines += ["", "## Endpoint Changes", ""]
    if report.endpoint_changes:
        for c in report.endpoint_changes:
            symbol = {"added": "+", "removed": "-", "modified": "~"}[c.change_type]
            lines.append(f"  {symbol} {c.endpoint} — {c.detail}")
    else:
        lines.append("  (none)")

    if report.invariant_impacts:
        lines += ["", "## Invariant Impacts", ""]
        for i in report.invariant_impacts:
            lines.append(f"  ⚠ {i.invariant_id}: {i.statement}")
            lines.append(f"    Reason: {i.reason}")

    lines.append("")
    discovery_path = spec_dir / "discovery-spec.md"
    discovery_path.write_text("\n".join(lines))

    return [spec_path, discovery_path]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_spec_field_map(entities: list[dict]) -> dict[str, set[str]]:
    """Build a map of entity_name.lower() → set of field_name.lower()."""
    result: dict[str, set[str]] = {}
    for ent in entities:
        name = ent.get("name", "").lower()
        fields = {f.get("name", "").lower() for f in ent.get("fields", [])}
        result[name] = fields
    return result


def _normalize_endpoint(endpoint: str) -> str:
    """Normalize an endpoint for comparison (strip method prefix, lowercase)."""
    # Remove HTTP method prefix if present: "GET /api/orders" → "/api/orders"
    ep = re.sub(r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+", "", endpoint.strip())
    # Normalize path params: /orders/{id} → /orders/{*}
    ep = re.sub(r"\{[^}]+\}", "{*}", ep)
    return ep.lower().rstrip("/")


def _collect_all_invariants(root: Path, config: dict) -> list[dict]:
    """Collect all invariants from core/hybrid specs."""
    paths_cfg = get_paths(config)
    specs_dir = root / paths_cfg["specs"]
    if not specs_dir.exists():
        return []

    invariants: list[dict] = []
    for spec_dir in sorted(specs_dir.iterdir()):
        spec_yaml = spec_dir / "spec.yaml"
        if not spec_yaml.exists():
            continue
        spec = yaml.safe_load(spec_yaml.read_text()) or {}
        zone = spec.get("zone", "")
        if zone not in ("core", "hybrid"):
            continue
        for inv in spec.get("invariants", []):
            invariants.append(inv)

    return invariants


def _collect_spec_endpoints(config: dict) -> list[str]:
    """Collect all documented endpoints from API contracts + traceability."""
    endpoints: list[str] = []

    # From api-contracts.yaml
    contracts = config.get("api_contracts", {})
    if isinstance(contracts, dict):
        for c in contracts.get("contracts", []):
            ep = c.get("endpoint", "")
            if ep:
                endpoints.append(ep)

    return endpoints


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_sync(
    *,
    since: str | None = None,
    generate: bool = False,
    ci: bool = False,
) -> DriftReport:
    """Run drift detection: compare git changes against specs.

    Args:
        since: Git ref (commit, tag, branch) to compare from. If None, compares against HEAD.
        generate: If True, create draft change specs from detected drift.
        ci: If True, output machine-readable JSON instead of human-readable text.

    Returns:
        DriftReport with detected changes and drift score.
    """
    root = find_project_root()
    if root is None:
        console.print("[red]ERROR:[/] No evospec.yaml found. Run `evospec init` first.")
        return DriftReport()

    config = load_config(root)
    entities = config.get("domain", {}).get("entities", [])
    spec_endpoints = _collect_spec_endpoints(config)
    invariants = _collect_all_invariants(root, config)

    # Get git diff
    diff_files = _get_diff_files(root, since)
    diff_content = _get_diff_content(root, since)
    commits = _count_commits(root, since)

    # Filter to source files only (skip specs, configs, docs)
    source_extensions = {".py", ".java", ".kt", ".go", ".ts", ".tsx", ".js", ".jsx", ".rs"}
    source_files = [
        f for f in diff_files
        if Path(f).suffix in source_extensions
        and not f.startswith("specs/")
        and not f.startswith("tests/")
    ]

    if not source_files and not ci:
        console.print(f"[dim]No source file changes detected{' since ' + since if since else ''}.[/dim]")
        return DriftReport(since=since or "HEAD", commits_analyzed=commits)

    # Detect changes
    entity_changes = _detect_entity_changes(diff_content, entities)
    endpoint_changes = _detect_endpoint_changes(diff_content, spec_endpoints)
    invariant_impacts = _detect_invariant_impacts(entity_changes, endpoint_changes, invariants)

    # Calculate drift score
    total_fields = sum(len(e.get("fields", [])) for e in entities)
    total_endpoints = len(spec_endpoints)
    drift_score = _calculate_drift_score(
        entity_changes, endpoint_changes, total_fields, total_endpoints,
    )

    report = DriftReport(
        entity_changes=entity_changes,
        endpoint_changes=endpoint_changes,
        invariant_impacts=invariant_impacts,
        drift_score=drift_score,
        commits_analyzed=commits,
        since=since or "HEAD",
    )

    # Output
    if ci:
        console.print(json.dumps(report.to_dict(), indent=2))
    else:
        _print_report(report, source_files)

    # Generate draft specs if requested (SYNC-001: only with --generate)
    if generate:
        created = _generate_draft_specs(report, root, config)
        if created and not ci:
            console.print()
            console.print("[green]Generated draft spec:[/]")
            for p in created:
                console.print(f"  {p.relative_to(root)}")

    return report


def _print_report(report: DriftReport, source_files: list[str]) -> None:
    """Print human-readable drift report."""
    console.print(f"\nAnalyzing {report.commits_analyzed} commit(s) since {report.since}...")
    console.print(f"Source files changed: {len(source_files)}")
    console.print()

    if report.entity_changes:
        console.print("[bold]Entity changes detected:[/]")
        for c in report.entity_changes:
            symbol = {"added": "+", "removed": "-", "modified": "~"}[c.change_type]
            color = {"added": "green", "removed": "red", "modified": "yellow"}[c.change_type]
            console.print(f"  [{color}]{symbol} {c.change_type.upper()} FIELD:[/] {c.entity}.{c.field_name}")
            if c.detail:
                console.print(f"    {c.detail}")
        console.print()

    if report.endpoint_changes:
        console.print("[bold]API changes detected:[/]")
        for c in report.endpoint_changes:
            symbol = {"added": "+", "removed": "-", "modified": "~"}[c.change_type]
            color = {"added": "green", "removed": "red", "modified": "yellow"}[c.change_type]
            console.print(f"  [{color}]{symbol} {c.change_type.upper()} ENDPOINT:[/] {c.endpoint}")
            if c.detail:
                console.print(f"    {c.detail}")
        console.print()

    if report.invariant_impacts:
        console.print("[bold yellow]Invariant impact:[/]")
        for i in report.invariant_impacts:
            console.print(f"  ⚠ {i.invariant_id} may need update: {i.statement}")
            console.print(f"    Reason: {i.reason}")
        console.print()

    if not report.entity_changes and not report.endpoint_changes:
        console.print("[green]✓[/] No spec drift detected.")
    else:
        console.print(f"[bold]Drift score: {report.drift_score:.1f}%[/]")
