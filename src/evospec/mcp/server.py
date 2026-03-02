"""EvoSpec MCP Server — exposes EvoSpec tools to AI agents via Model Context Protocol."""

from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "EvoSpec",
    json_response=True,
    instructions=(
        "EvoSpec is a spec-driven delivery toolkit. "
        "It classifies changes as edge/hybrid/core and applies proportional governance. "
        "Use these tools to manage specs, run checks, and track features."
    ),
)


# ---------------------------------------------------------------------------
# Resources — static context for agents
# ---------------------------------------------------------------------------


@mcp.resource("evospec://project")
def get_project() -> str:
    """Return lean project metadata — name, description, zone defaults.

    Does NOT expose internal config (teams, strategy, reverse settings).
    """
    import yaml

    root = _find_root()
    if root is None:
        return "ERROR: No evospec.yaml found. Run `evospec init` first."
    config = yaml.safe_load((root / "evospec.yaml").read_text()) or {}
    project = config.get("project", {})
    lean = {
        "project": {
            "name": project.get("name", ""),
            "description": project.get("description", ""),
        },
        "schema": config.get("schema", {}),
        "paths": config.get("paths", {}),
    }
    return yaml.dump(lean, default_flow_style=False, sort_keys=False)


@mcp.resource("evospec://config")
def get_config() -> str:
    """[DEPRECATED — use evospec://project] Return lean project metadata."""
    import yaml

    root = _find_root()
    if root is None:
        return "ERROR: No evospec.yaml found. Run `evospec init` first."
    config = yaml.safe_load((root / "evospec.yaml").read_text()) or {}
    project = config.get("project", {})
    lean = {
        "_deprecated": "Use evospec://project instead. This resource will be removed in the next major version.",
        "project": {
            "name": project.get("name", ""),
            "description": project.get("description", ""),
        },
        "schema": config.get("schema", {}),
        "paths": config.get("paths", {}),
    }
    return yaml.dump(lean, default_flow_style=False, sort_keys=False)


@mcp.resource("evospec://glossary")
def get_glossary() -> str:
    """Return the domain glossary (ubiquitous language)."""
    root = _find_root()
    if root is None:
        return "ERROR: No evospec.yaml found."
    glossary = root / "specs" / "domain" / "glossary.md"
    if glossary.exists():
        return glossary.read_text()
    return "No glossary found."


@mcp.resource("evospec://bootstrap")
def get_bootstrap() -> str:
    """Return an AI bootstrap prompt with EvoSpec context and auto-detected project stack.

    Works without evospec.yaml — designed for pre-init agent discovery.
    """
    from evospec.core.prompt import generate_bootstrap_prompt

    return generate_bootstrap_prompt(detect=True)


@mcp.resource("evospec://context-map")
def get_context_map() -> str:
    """Return the bounded context map."""
    root = _find_root()
    if root is None:
        return "ERROR: No evospec.yaml found."
    ctx_map = root / "specs" / "domain" / "context-map.md"
    if ctx_map.exists():
        return ctx_map.read_text()
    return "No context map found."


@mcp.resource("evospec://skills")
def get_skills() -> str:
    """Return project-specific implementation skills that AI agents should follow.

    Skills are project-specific coding rules organized by category
    (error-handling, testing, architecture, naming, dependencies, security).
    Defined in specs/domain/skills.yaml.
    """
    from evospec.core.config import load_skills

    root = _find_root()
    if root is None:
        return "ERROR: No evospec.yaml found."

    skills = load_skills(project_root=root)
    if not skills:
        return "No implementation skills defined. Add skills to specs/domain/skills.yaml."

    import yaml
    return yaml.dump({"skills": skills}, default_flow_style=False, sort_keys=False)


@mcp.resource("evospec://api-catalog")
def get_api_catalog() -> str:
    """Return a browsable API endpoint catalog grouped by tag.

    Lists all API contracts from specs/domain/api-contracts.yaml,
    organized by tags for easy browsing by external consumers.
    """
    from evospec.core.config import load_config

    root = _find_root()
    if root is None:
        return "ERROR: No evospec.yaml found."

    config = load_config(root)
    contracts_data = config.get("api_contracts", {})
    contracts = contracts_data.get("contracts", []) if isinstance(contracts_data, dict) else []

    if not contracts:
        return "No API contracts defined. Add them to specs/domain/api-contracts.yaml."

    # Group by tag
    by_tag: dict[str, list[dict]] = {}
    for c in contracts:
        tags = c.get("tags", ["untagged"])
        for tag in tags:
            by_tag.setdefault(tag, []).append(c)

    lines = ["# API Catalog", ""]
    lines.append(f"Total: {len(contracts)} endpoint(s) across {len(by_tag)} tag(s).")
    lines.append("")

    for tag, tag_contracts in sorted(by_tag.items()):
        lines.append(f"## {tag}")
        lines.append("")
        for c in tag_contracts:
            ep = c.get("endpoint", "?")
            desc = c.get("description", "")
            auth = c.get("auth", "")
            lines.append(f"- **{ep}** — {desc}")
            if auth:
                lines.append(f"  - Auth: {auth}")
        lines.append("")

    return "\n".join(lines)


@mcp.resource("evospec://entities")
def get_entity_registry() -> str:
    """[DEPRECATED — use evospec:get_entities tool] Return the domain entity registry."""
    result = _build_entity_registry()
    return (
        "# ⚠ DEPRECATED: Use the `get_entities()` MCP tool instead of this resource.\n"
        "# This resource will be removed in the next major version.\n\n"
        + result
    )


@mcp.resource("evospec://invariants")
def get_all_invariants() -> str:
    """[DEPRECATED — use evospec:get_invariants tool] Return all invariants."""
    result = _build_invariants_text()
    return (
        "# ⚠ DEPRECATED: Use the `get_invariants()` MCP tool instead of this resource.\n"
        "# This resource will be removed in the next major version.\n\n"
        + result
    )


# ---------------------------------------------------------------------------
# Tools — actions agents can perform
# ---------------------------------------------------------------------------


@mcp.tool()
def list_specs() -> dict:
    """List all change specs with their zone, status, and available artifacts."""
    import yaml

    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found. Run `evospec init` first."}

    specs_dir = root / "specs" / "changes"
    if not specs_dir.exists():
        return {"specs": [], "count": 0}

    results = []
    for spec_dir in sorted(specs_dir.iterdir()):
        spec_yaml = spec_dir / "spec.yaml"
        if not spec_yaml.exists():
            continue
        spec = yaml.safe_load(spec_yaml.read_text()) or {}
        artifacts = []
        for artifact in ["discovery-spec.md", "domain-contract.md", "tasks.md"]:
            if (spec_dir / artifact).exists():
                artifacts.append(artifact)
        results.append({
            "id": spec.get("id", spec_dir.name),
            "title": spec.get("title", spec_dir.name),
            "zone": spec.get("zone", "unknown"),
            "status": spec.get("status", "draft"),
            "risk": spec.get("classification", {}).get("risk", "unknown"),
            "artifacts": artifacts,
            "path": str(spec_dir.relative_to(root)),
        })

    return {"specs": results, "count": len(results)}


@mcp.tool()
def read_spec(spec_path: str) -> dict:
    """Read a complete spec with all its artifacts.

    Args:
        spec_path: Relative path to the spec directory (e.g., 'specs/changes/2026-03-01-my-feature')
    """
    import yaml

    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found."}

    spec_dir = root / spec_path
    if not spec_dir.exists():
        return {"error": f"Spec directory not found: {spec_path}"}

    result: dict = {"path": spec_path, "artifacts": {}}

    spec_yaml = spec_dir / "spec.yaml"
    if spec_yaml.exists():
        result["spec"] = yaml.safe_load(spec_yaml.read_text()) or {}

    for artifact in ["discovery-spec.md", "domain-contract.md", "tasks.md"]:
        artifact_path = spec_dir / artifact
        if artifact_path.exists():
            result["artifacts"][artifact] = artifact_path.read_text()

    return result


@mcp.tool()
def check_spec(spec_path: str | None = None) -> dict:
    """Run validation checks on specs.

    Args:
        spec_path: Optional path to a specific spec. If None, checks all specs.
    """
    import json
    import yaml
    from jsonschema import Draft202012Validator

    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found."}

    # Look for schema: project root first, then package-bundled
    schema = None
    schema_path = root / "schemas" / "spec.schema.json"
    if schema_path.exists():
        schema = json.loads(schema_path.read_text())
    else:
        pkg_schema = Path(__file__).parent.parent / "schemas" / "spec.schema.json"
        if pkg_schema.exists():
            schema = json.loads(pkg_schema.read_text())

    specs_dir = root / "specs" / "changes"
    if not specs_dir.exists():
        return {"error": "No specs directory found."}

    if spec_path:
        spec_dirs = [root / spec_path]
    else:
        spec_dirs = sorted(
            d for d in specs_dir.iterdir() if d.is_dir() and (d / "spec.yaml").exists()
        )

    results = []
    total_errors = 0
    total_warnings = 0

    for spec_dir in spec_dirs:
        spec_yaml = spec_dir / "spec.yaml"
        if not spec_yaml.exists():
            continue

        spec = yaml.safe_load(spec_yaml.read_text()) or {}
        zone = spec.get("zone", "unknown")
        errors: list[str] = []
        warnings: list[str] = []

        # Schema validation
        if schema:
            validator = Draft202012Validator(schema)
            for err in validator.iter_errors(spec):
                errors.append(f"Schema: {err.message}")

        # Zone-specific checks
        if zone == "core":
            if not spec.get("bounded_context"):
                errors.append("Core zone requires bounded_context")
            if not spec.get("invariants"):
                errors.append("Core zone requires at least one invariant")
            else:
                for inv in spec["invariants"]:
                    if not inv.get("enforcement"):
                        warnings.append(f"Invariant {inv.get('id', '?')} has no enforcement")
            if not spec.get("fitness_functions"):
                errors.append("Core zone requires at least one fitness function")
            if not (spec_dir / "domain-contract.md").exists():
                errors.append("Core zone requires domain-contract.md")

        elif zone == "hybrid":
            if not (spec_dir / "discovery-spec.md").exists():
                warnings.append("Hybrid zone should have discovery-spec.md")
            if not (spec_dir / "domain-contract.md").exists():
                warnings.append("Hybrid zone should have domain-contract.md")

        elif zone == "edge":
            discovery = spec.get("discovery", {})
            if not discovery.get("outcome"):
                warnings.append("Edge zone: discovery.outcome not set")
            if not discovery.get("kill_criteria"):
                warnings.append("Edge zone: discovery.kill_criteria not set")
            if not (spec_dir / "discovery-spec.md").exists():
                errors.append("Edge zone requires discovery-spec.md")

        # Tasks coverage check
        if (spec_dir / "tasks.md").exists():
            tasks_content = (spec_dir / "tasks.md").read_text()
            tasks_meta = _parse_tasks_frontmatter(tasks_content)
            invariants = spec.get("invariants", [])
            for inv in invariants:
                inv_id = inv.get("id", "")
                if inv_id and inv_id not in tasks_content:
                    warnings.append(f"Invariant {inv_id} not referenced in tasks.md")

        # Fitness function execution check
        fitness_fns = spec.get("fitness_functions", [])
        for ff in fitness_fns:
            ff_path = ff.get("path", "")
            if ff_path and not (root / ff_path).exists():
                warnings.append(f"Fitness function file not found: {ff_path}")

        total_errors += len(errors)
        total_warnings += len(warnings)

        results.append({
            "spec": spec.get("title", spec_dir.name),
            "zone": zone,
            "errors": errors,
            "warnings": warnings,
            "status": "FAIL" if errors else ("WARN" if warnings else "PASS"),
        })

    return {
        "results": results,
        "summary": {
            "checked": len(results),
            "errors": total_errors,
            "warnings": total_warnings,
            "overall": "FAIL" if total_errors else ("WARN" if total_warnings else "PASS"),
        },
    }


@mcp.tool()
def classify_change(
    touches_persistence: bool = False,
    touches_auth: bool = False,
    touches_billing: bool = False,
    touches_multi_tenancy: bool = False,
    hypothesis_driven: bool = False,
    reversibility: str = "moderate",
) -> dict:
    """Classify a change into edge/hybrid/core zone based on risk signals.

    Args:
        touches_persistence: Change affects database schema or persistent state
        touches_auth: Change affects authentication or authorization
        touches_billing: Change affects billing, plans, or subscriptions
        touches_multi_tenancy: Change affects tenant isolation
        hypothesis_driven: Change is driven by a hypothesis that needs validation
        reversibility: How hard to undo (trivial/moderate/difficult/irreversible)
    """
    core_signals = sum([
        touches_persistence,
        touches_auth,
        touches_billing,
        touches_multi_tenancy,
    ])

    if core_signals >= 2 or reversibility == "irreversible":
        zone = "core"
        risk = "high"
    elif core_signals == 1:
        zone = "hybrid"
        risk = "medium"
    elif hypothesis_driven:
        zone = "edge"
        risk = "low"
    else:
        zone = "hybrid"
        risk = "medium"

    knowledge_stage = {
        "edge": "mystery",
        "hybrid": "heuristic",
        "core": "algorithm",
    }

    return {
        "zone": zone,
        "risk": risk,
        "knowledge_stage": knowledge_stage[zone],
        "classification": {
            "touches_persistence": touches_persistence,
            "touches_auth": touches_auth,
            "touches_billing": touches_billing,
            "touches_multi_tenancy": touches_multi_tenancy,
            "hypothesis_driven": hypothesis_driven,
            "reversibility": reversibility,
            "core_signals": core_signals,
        },
        "required_artifacts": _required_artifacts(zone),
    }


@mcp.tool()
def check_invariant_impact(
    entities: list[str] | None = None,
    contexts: list[str] | None = None,
    description: str = "",
) -> dict:
    """Check which existing core invariants a proposed change may affect.

    Call this BEFORE creating a discovery/improvement/bugfix spec to understand
    what guardrails exist. This is the safety net between the exploratory layer
    and the core engine.

    Args:
        entities: Domain entities this change touches (e.g., ['Order', 'LineItem'])
        contexts: Bounded contexts this change crosses (e.g., ['orders', 'catalog'])
        description: Free-text description of what the change does
    """
    import yaml

    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found."}

    entities = [e.lower() for e in (entities or [])]
    contexts = [c.lower() for c in (contexts or [])]
    desc_lower = description.lower()

    specs_dir = root / "specs" / "changes"
    if not specs_dir.exists():
        return {"conflicts": [], "all_invariants": 0, "safe": True}

    all_invariants = []
    conflicts = []

    for spec_dir in sorted(specs_dir.iterdir()):
        spec_yaml = spec_dir / "spec.yaml"
        if not spec_yaml.exists():
            continue
        spec = yaml.safe_load(spec_yaml.read_text()) or {}
        zone = spec.get("zone", "")
        if zone not in ("core", "hybrid"):
            continue

        bc = (spec.get("bounded_context") or "").lower()
        title = spec.get("title", spec_dir.name)
        spec_path_rel = str(spec_dir.relative_to(root))

        # Collect entities from traceability
        spec_entities = [
            t.lower() for t in spec.get("traceability", {}).get("tables", [])
        ]
        spec_entities += [
            m.lower() for m in spec.get("traceability", {}).get("modules", [])
        ]

        for inv in spec.get("invariants", []):
            inv_id = inv.get("id", "?")
            statement = inv.get("statement", "")
            statement_lower = statement.lower()

            all_invariants.append({
                "id": inv_id,
                "statement": statement,
                "spec": title,
                "spec_path": spec_path_rel,
                "context": bc,
            })

            # Check for conflict: entity overlap, context overlap, or keyword match
            reasons = []
            scope = inv.get("scope", "entity")

            for entity in entities:
                if entity in statement_lower:
                    reasons.append(f"touches entity '{entity}' mentioned in invariant")
                if entity in spec_entities:
                    reasons.append(f"touches entity '{entity}' in same spec")

                # Relationship invariant: check source/target
                if scope == "relationship":
                    inv_source = (inv.get("source") or "").lower()
                    inv_target = (inv.get("target") or "").lower()
                    card = inv.get("cardinality", "")
                    if entity == inv_source:
                        reasons.append(
                            f"touches source entity of cardinality constraint "
                            f"({inv_source} → {inv_target}: {card})"
                        )
                    if entity == inv_target:
                        reasons.append(
                            f"touches target entity of cardinality constraint "
                            f"({inv_source} → {inv_target}: {card})"
                        )

                # Transition invariant: check entity
                if scope == "transition":
                    inv_entity = (inv.get("entity") or "").lower()
                    inv_field = inv.get("field", "")
                    if entity == inv_entity:
                        reasons.append(
                            f"touches entity with state machine constraint "
                            f"({inv_entity}.{inv_field})"
                        )

            for ctx in contexts:
                if ctx == bc:
                    reasons.append(f"same bounded context '{ctx}'")

            # Keyword matching from description
            if desc_lower:
                inv_keywords = set(statement_lower.split())
                desc_keywords = set(desc_lower.split())
                # Common domain words that are too generic to match on
                stop_words = {"the", "a", "an", "is", "must", "be", "to", "in", "of",
                              "for", "and", "or", "not", "every", "all", "each", "by",
                              "with", "from", "that", "this", "should", "can", "will"}
                meaningful_overlap = (inv_keywords & desc_keywords) - stop_words
                if len(meaningful_overlap) >= 2:
                    reasons.append(
                        f"description shares keywords: {', '.join(sorted(meaningful_overlap)[:5])}"
                    )

            if reasons:
                conflicts.append({
                    "invariant_id": inv_id,
                    "statement": statement,
                    "spec": title,
                    "spec_path": spec_path_rel,
                    "context": bc,
                    "enforcement": inv.get("enforcement", ""),
                    "fitness_function": inv.get("fitness_function", ""),
                    "reasons": reasons,
                })

    # Determine safety guidance
    safe = len(conflicts) == 0
    guidance = []
    if conflicts:
        guidance.append("⚠ This change may affect existing core invariants.")
        guidance.append("Options for each conflict:")
        guidance.append("  - exempt: Experiment behind a feature flag, don't touch the invariant")
        guidance.append("  - evolve: Propose a new version of the invariant (INV-001-v2)")
        guidance.append("  - shadow: Run analytics/interviews first, don't touch schema")
        guidance.append("  - redesign: Change the approach to avoid the conflict")
    else:
        guidance.append("✓ No invariant conflicts detected. Safe to experiment.")

    return {
        "conflicts": conflicts,
        "all_invariants_count": len(all_invariants),
        "safe": safe,
        "guidance": guidance,
        "entities_checked": entities,
        "contexts_checked": contexts,
    }


@mcp.tool()
def get_tasks(spec_path: str) -> dict:
    """Parse tasks.md for a spec and return structured task data.

    Args:
        spec_path: Relative path to the spec directory
    """
    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found."}

    tasks_path = root / spec_path / "tasks.md"
    if not tasks_path.exists():
        return {"error": f"No tasks.md found at {spec_path}/tasks.md"}

    content = tasks_path.read_text()
    meta = _parse_tasks_frontmatter(content)
    tasks = _parse_task_lines(content)

    total = len(tasks)
    completed = sum(1 for t in tasks if t["done"])
    pending = total - completed

    return {
        "metadata": meta,
        "tasks": tasks,
        "summary": {
            "total": total,
            "completed": completed,
            "pending": pending,
            "progress_pct": round((completed / total * 100) if total else 0, 1),
        },
    }


@mcp.tool()
def update_task(spec_path: str, task_id: str, done: bool) -> dict:
    """Mark a task as done or not done in tasks.md.

    Args:
        spec_path: Relative path to the spec directory
        task_id: Task identifier (e.g., 'T001')
        done: Whether the task is completed
    """
    import re

    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found."}

    tasks_path = root / spec_path / "tasks.md"
    if not tasks_path.exists():
        return {"error": f"No tasks.md found at {spec_path}/tasks.md"}

    content = tasks_path.read_text()
    old_mark = "[ ]" if done else "[X]"
    new_mark = "[X]" if done else "[ ]"

    pattern = rf"(- \[)({old_mark[1]})(] {re.escape(task_id)}\b)"
    new_content, count = re.subn(
        rf"(- \[)({'  ' if not done else 'X'})(] {re.escape(task_id)}\b)",
        rf"\g<1>{'X' if done else ' '}\g<3>",
        content,
    )

    if content == new_content:
        return {"error": f"Task {task_id} not found or already in desired state."}

    tasks_path.write_text(new_content)
    return {"success": True, "task_id": task_id, "done": done}


@mcp.tool()
def list_features() -> dict:
    """List all registered features with their lifecycle status."""
    from evospec.core.config import load_config

    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found."}

    config = load_config(root)
    features = config.get("features", []) or []

    return {
        "features": features,
        "count": len(features),
        "by_status": _count_by_key(features, "status"),
        "by_zone": _count_by_key(features, "zone"),
    }


@mcp.tool()
def get_discovery_status(spec_path: str) -> dict:
    """Get the discovery status of a spec: assumptions, experiments, learnings, progress.

    Args:
        spec_path: Relative path to the spec directory
    """
    import yaml

    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found."}

    spec_yaml = root / spec_path / "spec.yaml"
    if not spec_yaml.exists():
        return {"error": f"No spec.yaml found at {spec_path}"}

    spec = yaml.safe_load(spec_yaml.read_text()) or {}
    discovery = spec.get("discovery", {})
    assumptions = discovery.get("assumptions", [])
    experiments = discovery.get("experiments", [])
    learnings = discovery.get("learnings", [])

    # Count assumption statuses
    by_status: dict[str, int] = {}
    for a in assumptions:
        s = a.get("status", "untested")
        by_status[s] = by_status.get(s, 0) + 1

    total = len(assumptions)
    validated = by_status.get("validated", 0)
    invalidated = by_status.get("invalidated", 0)
    untested = by_status.get("untested", 0)
    testing = by_status.get("testing", 0)

    # Determine discovery health
    if total == 0:
        health = "no-assumptions"
    elif untested == total:
        health = "not-started"
    elif invalidated > total / 2:
        health = "at-risk"
    elif validated == total:
        health = "ready-to-promote"
    elif validated + invalidated == total:
        health = "complete"
    else:
        health = "in-progress"

    # Check kill deadline
    kill_deadline = discovery.get("kill_deadline", "")
    deadline_warning = ""
    if kill_deadline:
        from datetime import date
        try:
            dl = date.fromisoformat(kill_deadline)
            if dl <= date.today():
                deadline_warning = "KILL DEADLINE REACHED — decision required"
            elif (dl - date.today()).days <= 7:
                deadline_warning = f"Kill deadline in {(dl - date.today()).days} days"
        except ValueError:
            pass

    return {
        "title": spec.get("title", ""),
        "zone": spec.get("zone", ""),
        "iteration": discovery.get("iteration", 1),
        "cadence": discovery.get("cadence", ""),
        "next_checkpoint": discovery.get("next_checkpoint", ""),
        "kill_criteria": discovery.get("kill_criteria", ""),
        "kill_deadline": kill_deadline,
        "deadline_warning": deadline_warning,
        "assumptions": {
            "total": total,
            "by_status": by_status,
            "items": assumptions,
        },
        "experiments": {
            "total": len(experiments),
            "items": experiments,
        },
        "learnings": {
            "total": len(learnings),
            "latest": learnings[-1] if learnings else None,
        },
        "health": health,
        "ready_to_promote": [
            a for a in assumptions if a.get("status") == "validated"
        ],
    }


@mcp.tool()
def record_experiment(
    spec_path: str,
    assumption_id: str,
    experiment_type: str,
    description: str,
    result: str,
    sample_size: int = 0,
    confidence: str = "medium",
    decision: str = "continue",
    learning: str = "",
) -> dict:
    """Record an experiment result and update the corresponding assumption.

    Args:
        spec_path: Relative path to the spec directory
        assumption_id: ID of the assumption tested (e.g., 'A-001')
        experiment_type: Type of experiment (prototype/interview/survey/A-B-test/wizard-of-oz/analytics/spike)
        description: What was done
        result: Qualitative or quantitative result
        sample_size: Number of users or data points
        confidence: Confidence in the result (high/medium/low)
        decision: Next step (continue/pivot/kill/promote-to-core)
        learning: One-sentence summary of what was learned
    """
    import yaml
    from datetime import date

    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found."}

    spec_yaml_path = root / spec_path / "spec.yaml"
    if not spec_yaml_path.exists():
        return {"error": f"No spec.yaml found at {spec_path}"}

    spec = yaml.safe_load(spec_yaml_path.read_text()) or {}
    discovery = spec.setdefault("discovery", {})
    assumptions = discovery.setdefault("assumptions", [])
    experiments = discovery.setdefault("experiments", [])
    learnings_list = discovery.setdefault("learnings", [])

    # Find the assumption
    target_assumption = None
    for a in assumptions:
        if a.get("id") == assumption_id:
            target_assumption = a
            break

    if target_assumption is None:
        return {"error": f"Assumption {assumption_id} not found in {spec_path}/spec.yaml"}

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

    # Create experiment record
    experiment = {
        "id": exp_id,
        "assumption_id": assumption_id,
        "type": experiment_type,
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

    # Update assumption status based on decision
    new_status = target_assumption.get("status", "untested")
    if decision == "promote-to-core":
        new_status = "validated"
    elif decision == "kill":
        new_status = "invalidated"
    elif decision == "pivot":
        new_status = "pivoted"
    elif confidence == "high" and "positive" in result.lower():
        new_status = "validated"
    elif confidence == "high" and "negative" in result.lower():
        new_status = "invalidated"
    else:
        new_status = "testing"

    target_assumption["status"] = new_status
    target_assumption["result"] = result
    target_assumption["result_date"] = today
    target_assumption["learning"] = learning

    # Handle pivot
    if decision == "pivot":
        iteration = discovery.get("iteration", 1)
        discovery["iteration"] = iteration + 1

    # Log learning
    learning_entry = {
        "date": today,
        "iteration": discovery.get("iteration", 1),
        "experiment_id": exp_id,
        "learning": learning or f"Experiment on {assumption_id}: {result}",
        "impact": f"Decision: {decision}",
        "spec_changed": decision in ("pivot", "kill", "promote-to-core"),
    }
    learnings_list.append(learning_entry)

    # Update spec.yaml
    spec["updated_at"] = today
    with open(spec_yaml_path, "w") as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return {
        "success": True,
        "experiment_id": exp_id,
        "assumption_id": assumption_id,
        "assumption_new_status": new_status,
        "decision": decision,
        "iteration": discovery.get("iteration", 1),
        "learning": learning_entry,
    }


@mcp.tool()
def update_assumption(
    spec_path: str,
    assumption_id: str,
    status: str | None = None,
    pivot_to: str | None = None,
    learning: str | None = None,
) -> dict:
    """Update an assumption's status, pivot direction, or learning.

    Args:
        spec_path: Relative path to the spec directory
        assumption_id: ID of the assumption (e.g., 'A-001')
        status: New status (untested/testing/validated/invalidated/pivoted)
        pivot_to: If pivoting, the new direction
        learning: Updated learning text
    """
    import yaml
    from datetime import date

    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found."}

    spec_yaml_path = root / spec_path / "spec.yaml"
    if not spec_yaml_path.exists():
        return {"error": f"No spec.yaml found at {spec_path}"}

    spec = yaml.safe_load(spec_yaml_path.read_text()) or {}
    assumptions = spec.get("discovery", {}).get("assumptions", [])

    target = None
    for a in assumptions:
        if a.get("id") == assumption_id:
            target = a
            break

    if target is None:
        return {"error": f"Assumption {assumption_id} not found"}

    changes = []
    if status:
        target["status"] = status
        target["result_date"] = date.today().isoformat()
        changes.append(f"status → {status}")

    if pivot_to:
        target["pivot_to"] = pivot_to
        changes.append(f"pivot_to → {pivot_to}")

    if learning:
        target["learning"] = learning
        changes.append(f"learning updated")

    if not changes:
        return {"error": "No changes specified"}

    spec["updated_at"] = date.today().isoformat()
    with open(spec_yaml_path, "w") as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return {
        "success": True,
        "assumption_id": assumption_id,
        "changes": changes,
    }


@mcp.tool()
def run_fitness_functions(spec_path: str | None = None) -> dict:
    """Execute fitness functions defined in spec.yaml and return results.

    Args:
        spec_path: Optional path to a specific spec. If None, runs all.
    """
    import subprocess
    import yaml

    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found."}

    config = yaml.safe_load((root / "evospec.yaml").read_text()) or {}
    global_command = config.get("fitness_functions", {}).get("run_command", "")

    specs_dir = root / "specs" / "changes"
    if not specs_dir.exists():
        return {"error": "No specs directory found."}

    if spec_path:
        spec_dirs = [root / spec_path]
    else:
        spec_dirs = sorted(
            d for d in specs_dir.iterdir() if d.is_dir() and (d / "spec.yaml").exists()
        )

    results = []

    for spec_dir in spec_dirs:
        spec_yaml = spec_dir / "spec.yaml"
        if not spec_yaml.exists():
            continue

        spec = yaml.safe_load(spec_yaml.read_text()) or {}
        fitness_fns = spec.get("fitness_functions", [])

        for ff in fitness_fns:
            ff_path = ff.get("path", "")
            ff_type = ff.get("type", "unknown")
            ff_dim = ff.get("dimension", "unknown")

            if not ff_path:
                results.append({
                    "spec": spec.get("title", spec_dir.name),
                    "function": ff.get("id", "?"),
                    "status": "SKIP",
                    "reason": "No path defined",
                })
                continue

            full_path = root / ff_path
            if not full_path.exists():
                results.append({
                    "spec": spec.get("title", spec_dir.name),
                    "function": ff.get("id", "?"),
                    "status": "SKIP",
                    "reason": f"File not found: {ff_path}",
                })
                continue

            # Execute based on type
            if ff_type in ("unit-test", "integration-test", "contract-test"):
                try:
                    result = subprocess.run(
                        ["python", "-m", "pytest", str(full_path), "-v", "--tb=short"],
                        capture_output=True,
                        text=True,
                        cwd=str(root),
                        timeout=120,
                    )
                    results.append({
                        "spec": spec.get("title", spec_dir.name),
                        "function": ff.get("id", "?"),
                        "dimension": ff_dim,
                        "status": "PASS" if result.returncode == 0 else "FAIL",
                        "output": result.stdout[-500:] if result.stdout else "",
                        "errors": result.stderr[-500:] if result.stderr else "",
                    })
                except subprocess.TimeoutExpired:
                    results.append({
                        "spec": spec.get("title", spec_dir.name),
                        "function": ff.get("id", "?"),
                        "status": "TIMEOUT",
                    })
            elif ff_type == "schema-check":
                results.append({
                    "spec": spec.get("title", spec_dir.name),
                    "function": ff.get("id", "?"),
                    "status": "PASS",
                    "reason": "Schema check handled by spec validation",
                })
            else:
                results.append({
                    "spec": spec.get("title", spec_dir.name),
                    "function": ff.get("id", "?"),
                    "status": "SKIP",
                    "reason": f"Unknown type: {ff_type}",
                })

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")

    return {
        "results": results,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "overall": "FAIL" if failed else "PASS",
        },
    }


@mcp.tool()
def get_upstream_apis(upstream_name: str | None = None) -> dict:
    """List API endpoints from upstream services' traceability data.

    Reads upstream repos' spec.yaml traceability.endpoints and returns the
    aggregated API surface. Only returns data from upstream services declared
    in evospec.yaml — never exposes local project internals.

    Args:
        upstream_name: Filter by a specific upstream service name. If None, returns all.
    """
    from evospec.core.config import load_config
    import yaml

    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found."}

    config = load_config(root)
    upstreams_cfg = config.get("_upstreams", {})
    if not upstreams_cfg:
        return {"error": "No upstreams configured in evospec.yaml.", "apis": []}

    results: dict[str, list[str]] = {}

    for name, up_data in upstreams_cfg.items():
        if upstream_name and name != upstream_name:
            continue

        upstream_root = Path(up_data.get("root", ""))
        if not upstream_root.exists():
            continue

        # Collect endpoints from all specs in the upstream
        from evospec.core.config import get_paths
        upstream_config_path = upstream_root / "evospec.yaml"
        if not upstream_config_path.exists():
            continue
        upstream_cfg = yaml.safe_load(upstream_config_path.read_text()) or {}
        specs_dir = upstream_root / get_paths(upstream_cfg).get("specs", "specs/changes")
        endpoints: list[str] = []

        if specs_dir.exists():
            for spec_dir in sorted(specs_dir.iterdir()):
                spec_yaml = spec_dir / "spec.yaml"
                if not spec_yaml.exists():
                    continue
                spec = yaml.safe_load(spec_yaml.read_text()) or {}
                for ep in spec.get("traceability", {}).get("endpoints", []):
                    if ep not in endpoints:
                        endpoints.append(ep)

        if endpoints:
            results[name] = endpoints

    if upstream_name and upstream_name not in results:
        return {
            "error": f"Upstream '{upstream_name}' not found or has no endpoints.",
            "apis": {},
        }

    return {
        "apis": results,
        "total_endpoints": sum(len(eps) for eps in results.values()),
        "filter": {"upstream_name": upstream_name},
    }


@mcp.tool()
def parse_contract_file(file_path: str) -> dict:
    """Parse an API contract or response file and extract entities/fields/relationships.

    Supports OpenAPI/Swagger, JSON Schema, and JSON example files.
    Use this when a UX or frontend team needs to understand entities from
    an API response or contract file.

    Args:
        file_path: Path to the contract file (absolute or relative to project root)
    """
    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found."}

    target = Path(file_path)
    if not target.is_absolute():
        target = root / target

    if not target.exists():
        return {"error": f"File not found: {file_path}"}

    suffix = target.suffix.lower()
    if suffix not in (".json", ".yaml", ".yml"):
        return {"error": f"Unsupported file format: {suffix}. Supported: .json, .yaml, .yml"}

    from evospec.mcp.contract_parser import parse_contract

    try:
        return parse_contract(target)
    except Exception as e:
        return {"error": f"Failed to parse contract file: {e}"}


@mcp.tool()
def get_entities(
    context: str | None = None,
    upstream: str | None = None,
) -> dict:
    """Get domain entities, optionally filtered by bounded context or upstream.

    Returns the entity registry as structured data. Use this instead of the
    deprecated evospec://entities resource.

    Args:
        context: Filter by bounded context name (case-insensitive)
        upstream: Filter by upstream service name (e.g., 'order-service')
    """
    text = _build_entity_registry(context=context, upstream=upstream)
    return {
        "text": text,
        "filters": {"context": context, "upstream": upstream},
    }


@mcp.tool()
def get_invariants(context: str | None = None) -> dict:
    """Get all invariants from core/hybrid specs, optionally filtered by bounded context.

    Returns invariants as structured data. Use this instead of the
    deprecated evospec://invariants resource.

    Args:
        context: Filter by bounded context name (case-insensitive)
    """
    text = _build_invariants_text(context=context)
    return {
        "text": text,
        "filter": {"context": context},
    }


# ---------------------------------------------------------------------------
# Consumer-facing tools — API contracts, file schemas, consumer context
# ---------------------------------------------------------------------------


@mcp.tool()
def get_api_contract(
    endpoint: str | None = None,
    tag: str | None = None,
) -> dict:
    """Get API contracts from specs/domain/api-contracts.yaml.

    Returns structured API contracts with endpoint, params, request/response
    schemas, auth, and tags. Use this when building integrations against
    a team's API.

    Args:
        endpoint: Filter by endpoint path (substring match, case-insensitive)
        tag: Filter by tag (e.g., 'orders', 'read')
    """
    from evospec.core.config import load_config

    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found."}

    config = load_config(root)
    contracts_data = config.get("api_contracts", {})
    contracts = contracts_data.get("contracts", []) if isinstance(contracts_data, dict) else []
    if isinstance(contracts_data, list):
        contracts = contracts_data

    if not contracts:
        return {"contracts": [], "count": 0, "note": "No API contracts defined. Add them to specs/domain/api-contracts.yaml."}

    # Filter
    results = contracts
    if endpoint:
        ep_lower = endpoint.lower()
        results = [c for c in results if ep_lower in (c.get("endpoint") or "").lower()]
    if tag:
        tag_lower = tag.lower()
        results = [c for c in results if tag_lower in [t.lower() for t in c.get("tags", [])]]

    return {
        "contracts": results,
        "count": len(results),
        "total": len(contracts),
        "filters": {"endpoint": endpoint, "tag": tag},
    }


@mcp.tool()
def get_file_schema(
    name: str | None = None,
    fmt: str | None = None,
) -> dict:
    """Get file/response schemas from specs/domain/file-schemas.yaml.

    Returns structured file schemas with name, format, structure, and examples.
    Use this when parsing files or API responses from a service.

    Args:
        name: Filter by schema name (substring match, case-insensitive)
        fmt: Filter by format (e.g., 'json', 'csv', 'xml')
    """
    from evospec.core.config import load_config

    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found."}

    config = load_config(root)
    schemas_data = config.get("file_schemas", {})
    schemas = schemas_data.get("schemas", []) if isinstance(schemas_data, dict) else []
    if isinstance(schemas_data, list):
        schemas = schemas_data

    if not schemas:
        return {"schemas": [], "count": 0, "note": "No file schemas defined. Add them to specs/domain/file-schemas.yaml."}

    results = schemas
    if name:
        name_lower = name.lower()
        results = [s for s in results if name_lower in (s.get("name") or "").lower()]
    if fmt:
        fmt_lower = fmt.lower()
        results = [s for s in results if fmt_lower == (s.get("format") or "").lower()]

    return {
        "schemas": results,
        "count": len(results),
        "total": len(schemas),
        "filters": {"name": name, "format": fmt},
    }


@mcp.tool()
def get_consumer_context(intent: str) -> dict:
    """Get combined context for an external consumer based on their intent.

    Combines API contracts, file schemas, domain entities, and glossary
    to give an AI agent everything it needs to generate correct integration
    code on the first try.

    Args:
        intent: Natural language description of what the consumer wants to do
                (e.g., 'download and parse order exports', 'create a new order')
    """
    from evospec.core.config import load_config

    root = _find_root()
    if root is None:
        return {"error": "No evospec.yaml found."}

    config = load_config(root)
    intent_lower = intent.lower()
    intent_words = set(intent_lower.split())

    # Search API contracts by keyword overlap
    contracts_data = config.get("api_contracts", {})
    all_contracts = contracts_data.get("contracts", []) if isinstance(contracts_data, dict) else []
    matching_contracts = []
    for c in all_contracts:
        score = 0
        ep = (c.get("endpoint") or "").lower()
        desc = (c.get("description") or "").lower()
        tags = [t.lower() for t in c.get("tags", [])]
        # Score: endpoint keyword match, description match, tag match
        for word in intent_words:
            if word in ep:
                score += 2
            if word in desc:
                score += 2
            if word in tags:
                score += 3
        if score > 0:
            matching_contracts.append({"contract": c, "relevance": score})
    matching_contracts.sort(key=lambda x: x["relevance"], reverse=True)

    # Search file schemas by keyword overlap
    schemas_data = config.get("file_schemas", {})
    all_schemas = schemas_data.get("schemas", []) if isinstance(schemas_data, dict) else []
    matching_schemas = []
    for s in all_schemas:
        score = 0
        name = (s.get("name") or "").lower()
        desc = (s.get("description") or "").lower()
        fmt = (s.get("format") or "").lower()
        for word in intent_words:
            if word in name:
                score += 2
            if word in desc:
                score += 2
            if word in fmt:
                score += 1
        if score > 0:
            matching_schemas.append({"schema": s, "relevance": score})
    matching_schemas.sort(key=lambda x: x["relevance"], reverse=True)

    # Find relevant entities
    entities = config.get("domain", {}).get("entities", [])
    matching_entities = []
    for e in entities:
        name = (e.get("name") or "").lower()
        ctx = (e.get("context") or "").lower()
        desc = (e.get("description") or "").lower()
        for word in intent_words:
            if word in name or word in ctx or word in desc:
                matching_entities.append(e.get("name"))
                break

    # Get glossary terms
    glossary_path = root / "specs" / "domain" / "glossary.md"
    glossary_excerpt = ""
    if glossary_path.exists():
        glossary_text = glossary_path.read_text()
        # Extract rows that match intent keywords
        relevant_lines = []
        for line in glossary_text.split("\n"):
            line_lower = line.lower()
            for word in intent_words:
                if len(word) > 3 and word in line_lower:
                    relevant_lines.append(line)
                    break
        if relevant_lines:
            glossary_excerpt = "\n".join(relevant_lines[:10])

    return {
        "intent": intent,
        "api_contracts": [m["contract"] for m in matching_contracts[:5]],
        "file_schemas": [m["schema"] for m in matching_schemas[:5]],
        "related_entities": matching_entities[:10],
        "glossary_excerpt": glossary_excerpt,
        "guidance": (
            "Use the API contracts for endpoint details, params, and response schemas. "
            "Use file schemas for parsing downloaded files or structured responses. "
            "Cross-reference entity names with the domain glossary for correct terminology."
        ),
    }


# ---------------------------------------------------------------------------
# Prompts — removed (replaced by Skills)
# ---------------------------------------------------------------------------
# discover_feature and domain_contract prompts have been removed.
# Use Agent Skills (evospec-discover, evospec-contract) instead.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_entity_registry(
    context: str | None = None,
    upstream: str | None = None,
) -> str:
    """Build entity registry text, optionally filtered by context or upstream."""
    from evospec.core.config import load_config

    root = _find_root()
    if root is None:
        return "ERROR: No evospec.yaml found."

    config = load_config(root)
    entities: list[dict] = []

    # Local entities (skip if filtering by upstream only)
    if upstream is None:
        for ent in config.get("domain", {}).get("entities", []):
            if context and ent.get("context", "").lower() != context.lower():
                continue
            entities.append(ent)
    elif upstream is not None:
        # Only include entities from a specific upstream
        up_data = config.get("_upstreams", {}).get(upstream, {})
        for ent in up_data.get("entities", []):
            ent_copy = dict(ent)
            ent_copy["_upstream"] = upstream
            if context and ent_copy.get("context", "").lower() != context.lower():
                continue
            entities.append(ent_copy)
    # If no upstream filter, also include all upstream entities
    if upstream is None:
        for name, up_data in config.get("_upstreams", {}).items():
            for ent in up_data.get("entities", []):
                ent_copy = dict(ent)
                ent_copy["_upstream"] = name
                if context and ent_copy.get("context", "").lower() != context.lower():
                    continue
                entities.append(ent_copy)

    if not entities:
        return "No entities found matching the filter."

    lines = ["# Domain Entity Registry", ""]
    lines.append(f"Total: {len(entities)} entities.\n")

    by_context: dict[str, list[dict]] = {}
    for ent in entities:
        ctx = ent.get("context", "unassigned")
        by_context.setdefault(ctx, []).append(ent)

    for ctx, ctx_entities in sorted(by_context.items()):
        lines.append(f"## Context: {ctx}")
        lines.append("")
        for ent in ctx_entities:
            name = ent.get("name", "?")
            table = ent.get("table", "")
            agg = " (aggregate root)" if ent.get("aggregate_root") else ""
            upstream_tag = f" [upstream: {ent['_upstream']}]" if "_upstream" in ent else ""
            lines.append(f"### {name}{agg}{upstream_tag}")
            if table:
                lines.append(f"Table: `{table}`")

            fields = ent.get("fields", [])
            if fields:
                lines.append("")
                lines.append("| Field | Type | Constraints |")
                lines.append("|-------|------|-------------|")
                for f in fields:
                    constraints = f.get("constraints", "")
                    lines.append(f"| {f.get('name', '?')} | {f.get('type', '?')} | {constraints} |")

            rels = ent.get("relationships", [])
            if rels:
                lines.append("")
                lines.append("Relationships:")
                for r in rels:
                    lines.append(f"- \u2192 {r.get('target', '?')} ({r.get('type', '?')})")

            inv_refs = ent.get("invariants", [])
            if inv_refs:
                lines.append("")
                lines.append(f"Invariants: {', '.join(inv_refs)}")

            lines.append("")

    return "\n".join(lines)


def _build_invariants_text(context: str | None = None) -> str:
    """Build invariants text, optionally filtered by bounded context."""
    import yaml

    root = _find_root()
    if root is None:
        return "ERROR: No evospec.yaml found."

    specs_dir = root / "specs" / "changes"
    if not specs_dir.exists():
        return "No specs directory found."

    lines = ["# All Invariants (Core Safety Net)", ""]
    count = 0

    for spec_dir in sorted(specs_dir.iterdir()):
        spec_yaml = spec_dir / "spec.yaml"
        if not spec_yaml.exists():
            continue
        spec = yaml.safe_load(spec_yaml.read_text()) or {}
        zone = spec.get("zone", "")
        if zone not in ("core", "hybrid"):
            continue

        bc = spec.get("bounded_context", "")
        if context and bc.lower() != context.lower():
            continue

        invariants = spec.get("invariants", [])
        if not invariants:
            continue

        title = spec.get("title", spec_dir.name)
        lines.append(f"## {title} ({zone}, context: {bc or 'unspecified'})")
        lines.append(f"Spec: `{spec_dir.relative_to(root)}`")
        lines.append("")

        for inv in invariants:
            inv_id = inv.get("id", "?")
            statement = inv.get("statement", "")
            enforcement = inv.get("enforcement", "")
            ff = inv.get("fitness_function", "")
            scope = inv.get("scope", "entity")
            lines.append(f"- **{inv_id}** [scope: {scope}]: {statement}")
            if enforcement:
                lines.append(f"  - Enforcement: {enforcement}")
            if ff:
                lines.append(f"  - Fitness function: `{ff}`")
            # Relationship-specific fields
            if scope == "relationship":
                source = inv.get("source", "")
                target = inv.get("target", "")
                card = inv.get("cardinality", "")
                lines.append(f"  - Relationship: {source} → {target} ({card})")
            # Transition-specific fields
            elif scope == "transition":
                entity = inv.get("entity", "")
                field = inv.get("field", "")
                lines.append(f"  - State machine: {entity}.{field}")
                for t in inv.get("transitions", []):
                    to_states = ", ".join(t["to"]) if isinstance(t.get("to"), list) else t.get("to", "")
                    lines.append(f"    - {t.get('from', '?')} → [{to_states}]")
                for f in inv.get("forbidden", []):
                    to_val = f.get("to", "?")
                    reason = f.get("reason", "")
                    lines.append(f"    - ✗ {f.get('from', '?')} → {to_val} (forbidden: {reason})")
            count += 1

        lines.append("")

    if count == 0:
        return "No invariants defined yet. Core specs have no invariants."

    lines.insert(1, f"Total: {count} invariants across core/hybrid specs.")
    return "\n".join(lines)


def _find_root() -> Path | None:
    """Find the project root by walking up from cwd looking for evospec.yaml."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "evospec.yaml").exists():
            return parent
    return None


def _required_artifacts(zone: str) -> dict:
    """Return required and optional artifacts for a zone."""
    if zone == "core":
        return {
            "required": ["spec.yaml", "domain-contract.md"],
            "optional": ["tasks.md"],
            "guardrails": ["fitness_functions", "invariants"],
        }
    elif zone == "hybrid":
        return {
            "required": ["spec.yaml", "discovery-spec.md", "domain-contract.md"],
            "optional": ["tasks.md"],
            "guardrails": ["contract_tests", "invariants (minimal)"],
        }
    else:  # edge
        return {
            "required": ["spec.yaml", "discovery-spec.md"],
            "optional": ["tasks.md"],
            "guardrails": ["metrics", "kill_criteria"],
        }


def _parse_tasks_frontmatter(content: str) -> dict:
    """Parse YAML front matter from tasks.md if present."""
    import yaml

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                return yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                pass
    return {}


def _parse_task_lines(content: str) -> list[dict]:
    """Parse task lines from tasks.md into structured data."""
    import re

    tasks = []
    pattern = re.compile(
        r"^- \[([ Xx])\] (T\d+)\s*(\[P\])?\s*\[([^\]]+)\]\s*(.+)$",
        re.MULTILINE,
    )

    for match in pattern.finditer(content):
        done_char, task_id, parallel, phase, description = match.groups()
        tasks.append({
            "id": task_id,
            "done": done_char.upper() == "X",
            "parallel": parallel is not None,
            "phase": phase,
            "description": description.strip(),
        })

    return tasks


def _count_by_key(items: list[dict], key: str) -> dict:
    """Count items grouped by a key."""
    counts: dict[str, int] = {}
    for item in items:
        val = item.get(key, "unknown")
        counts[val] = counts.get(val, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the EvoSpec MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
