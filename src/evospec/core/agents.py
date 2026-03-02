"""Generate AI agent integration files from canonical workflow specs.

Reads platform-agnostic workflow YAMLs and emits platform-specific files:
- Windsurf: .windsurf/workflows/evospec.*.md
- Claude Code: CLAUDE.md
- Cursor: .cursor/rules/evospec.mdc
- Skills: .agents/skills/evospec-*/SKILL.md (Agent Skills open standard)
"""

import re
from pathlib import Path

import yaml
from rich.console import Console

console = Console()

WORKFLOWS_DIR = Path(__file__).parent.parent / "templates" / "workflows"

PLATFORMS = ("windsurf", "claude", "cursor", "skills")


def _load_context() -> dict:
    """Load the shared _context.yaml."""
    ctx_path = WORKFLOWS_DIR / "_context.yaml"
    return yaml.safe_load(ctx_path.read_text()) or {}


def _load_workflows() -> list[dict]:
    """Load all canonical workflow YAMLs (excluding _context.yaml)."""
    workflows = []
    for path in sorted(WORKFLOWS_DIR.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        wf = yaml.safe_load(path.read_text()) or {}
        wf["_source"] = path.name
        workflows.append(wf)
    return workflows


# ---------------------------------------------------------------------------
# Windsurf emitter
# ---------------------------------------------------------------------------

def _emit_windsurf(workflows: list[dict], ctx: dict, dest: Path) -> list[Path]:
    """Emit .windsurf/workflows/evospec.*.md files."""
    out_dir = dest / ".windsurf" / "workflows"
    out_dir.mkdir(parents=True, exist_ok=True)
    created = []

    for wf in workflows:
        lines: list[str] = []

        # YAML frontmatter
        lines.append("---")
        lines.append(f"description: {wf['description']}")
        if wf.get("handoffs"):
            lines.append("handoffs:")
            for ho in wf["handoffs"]:
                lines.append(f"  - label: {ho['label']}")
                lines.append(f"    agent: evospec.{ho['workflow']}")
                lines.append(f"    prompt: {ho['prompt']}")
                # First handoff gets send: true
                if ho == wf["handoffs"][0]:
                    lines.append("    send: true")
        lines.append("---")
        lines.append("")

        # User input block
        lines.append("## User Input")
        lines.append("")
        lines.append("```text")
        lines.append("$ARGUMENTS")
        lines.append("```")
        lines.append("")
        lines.append("You **MUST** consider the user input before proceeding (if not empty).")
        lines.append("")

        # Context
        if wf.get("context"):
            lines.append("## Context")
            lines.append("")
            lines.append(wf["context"].rstrip())
            lines.append("")

        # When to use
        if wf.get("when_to_use"):
            lines.append("## When to Use This vs Other Workflows")
            lines.append("")
            lines.append(wf["when_to_use"].rstrip())
            lines.append("")

        # Steps → Outline
        if wf.get("steps"):
            lines.append("## Outline")
            lines.append("")
            for step in wf["steps"]:
                title = step["title"]
                if step.get("interactive"):
                    title += " (interactive)"
                lines.append(f"{step['id']}. **{title}**:")
                lines.append(step["instructions"].rstrip())
                lines.append("")

        # Extra sections
        for key in ("knowledge_funnel_guidance", "invariant_quality",
                     "bug_fix_discipline", "task_generation_from_contract",
                     "task_generation_from_discovery", "error_handling",
                     "teresa_torres_principles"):
            val = wf.get(key)
            if val:
                heading = key.replace("_", " ").title()
                if isinstance(val, str):
                    lines.append(f"## {heading}")
                    lines.append("")
                    lines.append(val.rstrip())
                    lines.append("")
                elif isinstance(val, list):
                    lines.append(f"## {heading}")
                    lines.append("")
                    for item in val:
                        lines.append(f"- {item}")
                    lines.append("")

        # Rules
        if wf.get("rules"):
            lines.append("## Rules")
            lines.append("")
            for rule in wf["rules"]:
                lines.append(f"- {rule}")
            lines.append("")

        filename = f"evospec.{wf['id']}.md"
        out_path = out_dir / filename
        out_path.write_text("\n".join(lines))
        created.append(out_path)

    return created


# ---------------------------------------------------------------------------
# Claude Code emitter
# ---------------------------------------------------------------------------

def _emit_claude(workflows: list[dict], ctx: dict, dest: Path) -> list[Path]:
    """Emit CLAUDE.md — single file with framework context + all workflow procedures."""
    lines: list[str] = []

    # Header
    lines.append("# EvoSpec — AI Agent Context")
    lines.append("")
    lines.append("> This file is auto-generated from canonical workflow specs.")
    lines.append("> Edit the source in `src/evospec/templates/workflows/` and run `evospec generate agents`.")
    lines.append("> These instructions ensure Claude Code produces the **same artifacts** as")
    lines.append("> Windsurf `/evospec.*` workflows and Cursor rules.")
    lines.append("")

    # Framework
    lines.append("## Framework")
    lines.append("")
    lines.append(f"This project uses **{ctx['framework']['name']}** — a spec-driven delivery toolkit.")
    lines.append("")
    lines.append(f"**Core principle**: {ctx['framework']['principle']}")
    lines.append("")

    # Two Layers
    lines.append("## Two Layers")
    lines.append("")
    lines.append("| Layer | Knowledge Stage | Approach | Artifacts |")
    lines.append("|-------|----------------|----------|-----------|")
    for layer in ctx["layers"]:
        lines.append(
            f"| **{layer['name']}** ({layer['zone']}) "
            f"| {layer['knowledge_stage']} "
            f"| {layer['approach']} "
            f"| {layer['artifact']} |"
        )
    lines.append("")

    # Spec structure
    lines.append("## Spec Structure")
    lines.append("")
    lines.append("```")
    lines.append(ctx["spec_structure"].rstrip())
    lines.append("```")
    lines.append("")

    # Zones
    lines.append("## Zone Classification")
    lines.append("")
    lines.append("| Zone | Required Artifacts | Guardrails |")
    lines.append("|------|-------------------|------------|")
    for zone in ctx["zones"]:
        lines.append(f"| **{zone['name']}** | {zone['required_artifacts']} | {zone['guardrails']} |")
    lines.append("")

    # Entry points
    lines.append("## Three Entry Points")
    lines.append("")
    lines.append("| Type | When | Artifacts |")
    lines.append("|------|------|-----------|")
    for ep in ctx["entry_points"]:
        lines.append(f"| **{ep['type']}** | {ep['when']} | {ep['artifacts']} |")
    lines.append("")
    lines.append("All three entry points **MUST** run the invariant impact check before proceeding.")
    lines.append("")

    # Invariant safety net
    lines.append("## Invariant Safety Net")
    lines.append("")
    lines.append("**Resolution options** for invariant conflicts:")
    for res in ctx["invariant_resolutions"]:
        lines.append(f"- **{res['id']}** — {res['description']}")
    lines.append("")
    lines.append("MCP tool: `evospec:check_invariant_impact(entities=[...], contexts=[...], description=\"...\")`")
    lines.append("MCP tool: `evospec:get_invariants(context?)` — all invariants from core/hybrid specs")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Workflow Procedures
    lines.append("# Workflow Procedures")
    lines.append("")
    lines.append("These procedures define exactly what artifacts to produce and how.")
    lines.append("Follow them step by step to ensure output is compatible across all AI platforms.")
    lines.append("")

    for wf in workflows:
        lines.append(f"## Procedure: {wf['name']}")
        lines.append("")
        lines.append(f"Equivalent to Windsurf `/{wf['slash_command']}`.")
        lines.append("")

        # Steps as numbered list — concise
        for step in wf.get("steps", []):
            title = step["title"]
            critical = " (CRITICAL)" if step.get("critical") else ""
            lines.append(f"{step['id']}. **{title}**{critical}:")

            # Compress instructions to key bullets
            instr = step["instructions"].strip()
            # Indent sub-content
            for iline in instr.split("\n"):
                lines.append(f"   {iline}")
            lines.append("")

        # Rules inline
        if wf.get("rules"):
            lines.append(f"**Rules**: " + " ".join(wf["rules"][:3]))
            if len(wf["rules"]) > 3:
                for rule in wf["rules"][3:]:
                    lines.append(f"- {rule}")
            lines.append("")

    lines.append("---")
    lines.append("")

    # Implementation rules
    lines.append("## Working with Specs")
    lines.append("")
    lines.append("### Before implementing ANY change:")
    for rule in ctx["implementation_rules"]["before_any_change"]:
        lines.append(f"- {rule}")
    lines.append("")
    lines.append("### When implementing Core zone changes:")
    for rule in ctx["implementation_rules"]["core_zone"]:
        lines.append(f"- **{rule}**")
    lines.append("")
    lines.append("### When implementing Edge zone changes:")
    for rule in ctx["implementation_rules"]["edge_zone"]:
        lines.append(f"- **{rule}**")
    lines.append("")

    # Entity registry
    er = ctx["entity_registry"]
    lines.append("## Domain Entity Registry")
    lines.append("")
    lines.append(f"`evospec.yaml` has a `domain.entities` section — {er['description'].lower()}")
    lines.append("")
    lines.append(f"Each entity defines: {er['fields']}")
    lines.append("")
    lines.append(f"- MCP tool: `{er['mcp_tool']}`")
    lines.append(f"- `{er['populate_command']}` generates copy-pasteable YAML for this section")
    lines.append(f"- {er['validation']}")
    lines.append("")
    lines.append("When creating specs, call `evospec:get_entities()` to use canonical entity names.")
    lines.append("")

    # MCP
    lines.append("## MCP Server (Programmatic Access)")
    lines.append("")
    lines.append(f"Start with: `{ctx['mcp']['start_command']}`")
    lines.append("")
    lines.append("**Tools** (actions):")
    for tool in ctx["mcp"]["tools"]:
        lines.append(f"- `{tool}`")
    lines.append("")
    lines.append("**Resources** (context):")
    for res in ctx["mcp"]["resources"]:
        lines.append(f"- `{res}`")
    lines.append("")

    # CLI
    lines.append("## CLI Commands")
    lines.append("")
    lines.append("```bash")
    for cmd in ctx["cli_commands"]:
        lines.append(cmd)
    lines.append("```")
    lines.append("")

    # Reverse engineering
    lines.append("## Reverse Engineering")
    lines.append("")
    for item in ctx["reverse_engineering"]:
        lines.append(f"- `{item}`")
    lines.append("")

    # Features
    lines.append("## Features Registry")
    lines.append("")
    lines.append(f"Features in `evospec.yaml` track lifecycle: `{ctx['features_lifecycle']}`")
    lines.append("")

    # Discovery loop
    dl = ctx["discovery_loop"]
    lines.append("## Continuous Discovery Loop")
    lines.append("")
    lines.append(f"```\n{dl['cycle']}\n```")
    lines.append("")
    lines.append(f"Assumption lifecycle: `{dl['assumption_lifecycle']}`")
    lines.append("")
    lines.append("Rules:")
    for rule in dl["rules"]:
        lines.append(f"- {rule}")
    lines.append("")

    # Knowledge funnel
    lines.append("## Knowledge Funnel (Roger Martin)")
    lines.append("")
    lines.append("| Stage | Action | Zone |")
    lines.append("|-------|--------|------|")
    for kf in ctx["knowledge_funnel"]:
        lines.append(f"| {kf['stage']} | {kf['action']} | {kf['zone']} |")
    lines.append("")
    lines.append("When you encounter ambiguity:")
    for kf in ctx["knowledge_funnel"]:
        lines.append(f"- {kf['stage']} → {kf['guidance']}")
    lines.append("")

    out_path = dest / "CLAUDE.md"
    out_path.write_text("\n".join(lines))
    return [out_path]


# ---------------------------------------------------------------------------
# Cursor emitter
# ---------------------------------------------------------------------------

def _emit_cursor(workflows: list[dict], ctx: dict, dest: Path) -> list[Path]:
    """Emit .cursor/rules/evospec.mdc — Cursor uses MDC format with frontmatter."""
    out_dir = dest / ".cursor" / "rules"
    out_dir.mkdir(parents=True, exist_ok=True)
    created = []

    # 1. Context rule — always-on project context
    context_lines: list[str] = []
    context_lines.append("---")
    context_lines.append("description: EvoSpec framework context — spec-driven delivery with zones, invariants, and fitness functions")
    context_lines.append("globs:")
    context_lines.append("alwaysApply: true")
    context_lines.append("---")
    context_lines.append("")
    context_lines.append(f"# {ctx['framework']['name']}")
    context_lines.append("")
    context_lines.append(f"**Core principle**: {ctx['framework']['principle']}")
    context_lines.append("")

    # Layers
    context_lines.append("## Two Layers")
    context_lines.append("")
    for layer in ctx["layers"]:
        context_lines.append(
            f"- **{layer['name']}** ({layer['zone']}): {layer['knowledge_stage']} — {layer['approach']}"
        )
    context_lines.append("")

    # Zones
    context_lines.append("## Zones")
    context_lines.append("")
    for zone in ctx["zones"]:
        context_lines.append(f"- **{zone['name']}**: {zone['required_artifacts']} | {zone['guardrails']}")
    context_lines.append("")

    # Entry points
    context_lines.append("## Entry Points")
    context_lines.append("")
    for ep in ctx["entry_points"]:
        context_lines.append(f"- **{ep['type']}**: {ep['when']} → {ep['artifacts']}")
    context_lines.append("")
    context_lines.append("All entry points MUST run invariant impact check before proceeding.")
    context_lines.append("")

    # Invariant resolutions
    context_lines.append("## Invariant Resolutions")
    context_lines.append("")
    for res in ctx["invariant_resolutions"]:
        context_lines.append(f"- **{res['id']}** — {res['description']}")
    context_lines.append("")

    # Implementation rules
    context_lines.append("## Implementation Rules")
    context_lines.append("")
    context_lines.append("### Core zone:")
    for rule in ctx["implementation_rules"]["core_zone"]:
        context_lines.append(f"- {rule}")
    context_lines.append("")
    context_lines.append("### Edge zone:")
    for rule in ctx["implementation_rules"]["edge_zone"]:
        context_lines.append(f"- {rule}")
    context_lines.append("")

    # Entity registry
    er = ctx["entity_registry"]
    context_lines.append("## Entity Registry")
    context_lines.append("")
    context_lines.append(f"Call `evospec:get_entities()` for canonical entity names. {er['validation']}.")
    context_lines.append("")

    # MCP
    context_lines.append("## MCP Server")
    context_lines.append("")
    context_lines.append(f"Start: `{ctx['mcp']['start_command']}`")
    context_lines.append("")
    context_lines.append("Resources: " + ", ".join(
        r.split(" — ")[0] for r in ctx["mcp"]["resources"]
    ))
    context_lines.append("")

    # Knowledge funnel
    context_lines.append("## Knowledge Funnel")
    context_lines.append("")
    for kf in ctx["knowledge_funnel"]:
        context_lines.append(f"- {kf['stage']} → {kf['guidance']}")
    context_lines.append("")

    ctx_path = out_dir / "evospec.mdc"
    ctx_path.write_text("\n".join(context_lines))
    created.append(ctx_path)

    # 2. One rule file per workflow
    for wf in workflows:
        wf_lines: list[str] = []

        # Glob pattern: apply when user is working in spec directories
        wf_lines.append("---")
        wf_lines.append(f"description: {wf['description']}")
        wf_lines.append("globs:")
        wf_lines.append("  - specs/**")
        wf_lines.append("  - evospec.yaml")
        wf_lines.append("alwaysApply: false")
        wf_lines.append("---")
        wf_lines.append("")
        wf_lines.append(f"# Procedure: {wf['name']}")
        wf_lines.append("")

        if wf.get("context"):
            wf_lines.append(wf["context"].rstrip())
            wf_lines.append("")

        if wf.get("when_to_use"):
            wf_lines.append("## When to Use")
            wf_lines.append("")
            wf_lines.append(wf["when_to_use"].rstrip())
            wf_lines.append("")

        # Steps
        wf_lines.append("## Steps")
        wf_lines.append("")
        for step in wf.get("steps", []):
            critical = " (CRITICAL)" if step.get("critical") else ""
            wf_lines.append(f"{step['id']}. **{step['title']}**{critical}")
            for iline in step["instructions"].strip().split("\n"):
                wf_lines.append(f"   {iline}")
            wf_lines.append("")

        # Rules
        if wf.get("rules"):
            wf_lines.append("## Rules")
            wf_lines.append("")
            for rule in wf["rules"]:
                wf_lines.append(f"- {rule}")
            wf_lines.append("")

        wf_path = out_dir / f"evospec-{wf['id']}.mdc"
        wf_path.write_text("\n".join(wf_lines))
        created.append(wf_path)

    return created


# ---------------------------------------------------------------------------
# Skills emitter (Agent Skills open standard — agentskills.io)
# ---------------------------------------------------------------------------

# MCP tools exposed by the EvoSpec server — used for fully-qualified references
_MCP_TOOLS = {
    "list_specs", "read_spec", "check_spec", "classify_change",
    "check_invariant_impact", "get_tasks", "update_task", "list_features",
    "get_discovery_status", "record_experiment", "update_assumption",
    "run_fitness_functions", "get_entities", "get_invariants",
    "get_upstream_apis", "parse_contract_file",
}


def _add_mcp_tool_refs(text: str) -> str:
    """Replace bare MCP tool names with fully-qualified evospec:tool_name references."""
    result = text
    for tool in sorted(_MCP_TOOLS, key=len, reverse=True):
        # Replace tool_name( with evospec:tool_name( — but not if already prefixed
        result = re.sub(
            rf'(?<!evospec:)(?<!\w){re.escape(tool)}(?=\()',
            f'evospec:{tool}',
            result,
        )
    return result


def _build_skills_context_md(ctx: dict) -> str:
    """Generate shared references/context.md content from _context.yaml."""
    lines: list[str] = []

    lines.append(f"# {ctx['framework']['name']} — Agent Context")
    lines.append("")
    lines.append(f"> {ctx['framework']['principle']}")
    lines.append("")
    lines.append(f"{ctx['framework']['description']}")
    lines.append("")

    # Layers
    lines.append("## Layers")
    lines.append("")
    for layer in ctx["layers"]:
        lines.append(
            f"- **{layer['name']}** ({layer['zone']}): "
            f"{layer['knowledge_stage']} — {layer['approach']} → `{layer['artifact']}`"
        )
    lines.append("")

    # Zones
    lines.append("## Zone Classification")
    lines.append("")
    lines.append("| Zone | Required Artifacts | Guardrails |")
    lines.append("|------|-------------------|------------|")
    for zone in ctx["zones"]:
        lines.append(f"| **{zone['name']}** | {zone['required_artifacts']} | {zone['guardrails']} |")
    lines.append("")

    # Entry points
    lines.append("## Entry Points")
    lines.append("")
    for ep in ctx["entry_points"]:
        lines.append(f"- **{ep['type']}**: {ep['when']} → {ep['artifacts']}")
    lines.append("")

    # Invariant resolutions
    lines.append("## Invariant Resolutions")
    lines.append("")
    for res in ctx["invariant_resolutions"]:
        lines.append(f"- **{res['id']}** — {res['description']}")
    lines.append("")

    # MCP surface
    lines.append("## MCP Server")
    lines.append("")
    lines.append(f"Start: `{ctx['mcp']['start_command']}`")
    lines.append("")
    lines.append("**Tools** (model-invoked actions):")
    for tool in ctx["mcp"]["tools"]:
        lines.append(f"- `evospec:{tool.split('(')[0].split(' —')[0].strip()}`")
    lines.append("")
    lines.append("**Resources** (ambient context):")
    for res in ctx["mcp"]["resources"]:
        lines.append(f"- `{res.split(' —')[0].strip()}`")
    lines.append("")

    # Implementation rules
    lines.append("## Implementation Rules")
    lines.append("")
    lines.append("### Before any change:")
    for rule in ctx["implementation_rules"]["before_any_change"]:
        lines.append(f"- {rule}")
    lines.append("")
    lines.append("### Core zone:")
    for rule in ctx["implementation_rules"]["core_zone"]:
        lines.append(f"- {rule}")
    lines.append("")
    lines.append("### Edge zone:")
    for rule in ctx["implementation_rules"]["edge_zone"]:
        lines.append(f"- {rule}")
    lines.append("")

    # Knowledge funnel
    lines.append("## Knowledge Funnel")
    lines.append("")
    for kf in ctx["knowledge_funnel"]:
        lines.append(f"- **{kf['stage']}** ({kf['zone']}): {kf['guidance']}")
    lines.append("")

    return "\n".join(lines)


def _emit_skills(workflows: list[dict], ctx: dict, dest: Path) -> list[Path]:
    """Emit .agents/skills/evospec-*/SKILL.md + shared references/context.md."""
    skills_root = dest / ".agents" / "skills"
    skills_root.mkdir(parents=True, exist_ok=True)
    created = []

    # Build shared context once
    context_content = _build_skills_context_md(ctx)

    for wf in workflows:
        skill_id = f"evospec-{wf['id']}"
        skill_dir = skills_root / skill_id
        skill_dir.mkdir(parents=True, exist_ok=True)

        # --- SKILL.md ---
        lines: list[str] = []

        # Frontmatter
        lines.append("---")
        lines.append(f"name: {skill_id}")
        lines.append(f"description: {wf['description']}")
        lines.append("---")
        lines.append("")

        # Title
        lines.append(f"# {wf['name']}")
        lines.append("")

        # Context (brief)
        if wf.get("context"):
            # Take first paragraph only for brevity
            ctx_text = wf["context"].strip()
            first_para = ctx_text.split("\n\n")[0]
            lines.append("## Context")
            lines.append("")
            lines.append(first_para.strip())
            lines.append("")
            lines.append("See [references/context.md](references/context.md) for full framework context.")
            lines.append("")

        # When to use
        if wf.get("when_to_use"):
            lines.append("## When to Use")
            lines.append("")
            lines.append(wf["when_to_use"].rstrip())
            lines.append("")

        # Steps (compact, with MCP tool references)
        if wf.get("steps"):
            lines.append("## Steps")
            lines.append("")
            for step in wf["steps"]:
                title = step["title"]
                if step.get("interactive"):
                    title += " *(interactive)*"
                if step.get("critical"):
                    title += " *(CRITICAL)*"
                lines.append(f"{step['id']}. **{title}**")

                # Add MCP tool fully-qualified references to instructions
                instructions = _add_mcp_tool_refs(step["instructions"].rstrip())
                for iline in instructions.split("\n"):
                    lines.append(f"   {iline}")
                lines.append("")

        # Rules
        if wf.get("rules"):
            lines.append("## Rules")
            lines.append("")
            for rule in wf["rules"]:
                lines.append(f"- {rule}")
            lines.append("")

        # Reference link
        lines.append("---")
        lines.append("")
        lines.append("*Full framework context: [references/context.md](references/context.md)*")
        lines.append("")

        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text("\n".join(lines))
        created.append(skill_path)

        # --- references/context.md ---
        ref_dir = skill_dir / "references"
        ref_dir.mkdir(parents=True, exist_ok=True)
        ref_path = ref_dir / "context.md"
        ref_path.write_text(context_content)
        created.append(ref_path)

    return created


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

EMITTERS = {
    "windsurf": _emit_windsurf,
    "claude": _emit_claude,
    "cursor": _emit_cursor,
    "skills": _emit_skills,
}


def generate_agents(dest: Path, platforms: list[str] | None = None) -> dict[str, list[Path]]:
    """Generate AI agent integration files for the specified platforms.

    Args:
        dest: Project root directory where files are written.
        platforms: List of platforms to generate for. None = all.

    Returns:
        Dict mapping platform name to list of created file paths.
    """
    platforms = platforms or list(PLATFORMS)
    ctx = _load_context()
    workflows = _load_workflows()

    results: dict[str, list[Path]] = {}
    for platform in platforms:
        emitter = EMITTERS.get(platform)
        if emitter is None:
            console.print(f"[yellow]⚠ Unknown platform: {platform}[/yellow]")
            continue
        created = emitter(workflows, ctx, dest)
        results[platform] = created

    return results
