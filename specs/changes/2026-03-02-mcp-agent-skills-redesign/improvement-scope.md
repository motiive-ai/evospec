# Improvement Scope: MCP + Agent Skills Redesign

> Zone: **hybrid** | Type: **improvement** | Status: **draft**

---

## What Needs to Change

EvoSpec currently generates 22 platform-specific files across 3 AI platforms (Windsurf, Claude Code, Cursor) and exposes an MCP server that overexposes internal project data. In 2025-2026, **Agent Skills** emerged as an open standard (agentskills.io) supported natively by all three platforms. This improvement adopts Agent Skills as the primary cross-platform workflow format and trims the MCP surface to expose only domain context that agents actually need.

## Why Now

1. **Agent Skills is now supported by Claude Code, Cursor, and Windsurf** — EvoSpec can generate one set of skill files instead of maintaining three platform-specific emitters.
2. **MCP best practices** (2025-06 spec) make clear that Resources should be lean ambient context, not full config dumps. `evospec://config` currently exposes the entire `evospec.yaml` including internal team/strategy data.
3. **Skills use progressive disclosure** — only name+description loaded at startup (~100 tokens), full instructions on activation. This is more efficient than platform-specific workflow files loaded at conversation start.
4. **The multi-system-ux-discovery example** needs to clearly demonstrate how MCP + Skills work together so users understand the interaction model.

## Scope

### In Scope

- **Skills emitter**: Add `_emit_skills()` to `agents.py` that generates `.agents/skills/evospec-*/SKILL.md` from canonical workflow YAMLs
- **MCP resource trimming**: Replace `evospec://config` with lean `evospec://project` (name, description, zone defaults only); keep `evospec://glossary` and `evospec://context-map`; move `evospec://entities` and `evospec://invariants` from resources to on-demand tools
- **_context.yaml update**: Add `skills` section documenting the new format; update `mcp` section to reflect trimmed resources
- **Example update**: Revise `examples/multi-system-ux-discovery/README.md` and `WALKTHROUGH.md` to demonstrate MCP tools + Skills invocation clearly
- **CLI update**: Add `skills` to `--platform` choices in `evospec generate agents`
- **Test coverage**: Ensure existing tests pass with the new emitter and MCP changes

### Out of Scope

- Removing existing Windsurf/Claude/Cursor emitters (kept as fallback)
- Changing canonical workflow YAML format
- Adding new MCP tools beyond moving entities/invariants
- The `evospec prompt` bootstrap command (separate change)
- MCP authentication/authorization changes

## Affected Areas

**Endpoints**: None (MCP resources are not REST endpoints)

**Tables**: None

**Modules**:
- `src/evospec/core/agents.py` — add Skills emitter, update PLATFORMS
- `src/evospec/mcp/server.py` — replace `evospec://config` resource, move entities/invariants to tools
- `src/evospec/templates/workflows/_context.yaml` — update MCP section, add Skills section
- `src/evospec/cli/main.py` — add `skills` to platform choices
- `examples/multi-system-ux-discovery/README.md` — add Skills + MCP actor model
- `examples/multi-system-ux-discovery/WALKTHROUGH.md` — show Skills invocation in walkthrough

**Bounded Contexts**:
- `agent-integration` — Skills generation, workflow format
- `mcp-server` — resource/tool surface redesign

## Invariant Impact

No invariant conflicts detected. This change does not touch persistence, auth, billing, or existing domain invariants. The MCP surface changes are additive (new tools) and subtractive (removing overexposed resources) — no existing invariant enforcement is affected.

## Acceptance Criteria

- [ ] `evospec generate agents --platform skills` produces `.agents/skills/evospec-*/SKILL.md` for all 10 workflows
- [ ] Each SKILL.md has valid frontmatter (name, description) and references shared `context.md`
- [ ] `evospec://project` resource returns lean project metadata (no teams, strategy, reverse config)
- [ ] `evospec://config` resource is removed
- [ ] `get_entities()` and `get_invariants()` are available as MCP tools (not resources)
- [ ] `evospec://glossary` and `evospec://context-map` resources unchanged
- [ ] `_context.yaml` documents Skills format and updated MCP surface
- [ ] `examples/multi-system-ux-discovery/` clearly shows MCP + Skills actor model
- [ ] All existing tests pass
- [ ] `evospec generate agents` (no platform flag) generates Skills + all 3 legacy platforms

## Risks & Rollback

**Risk level**: medium

**Rollback plan**: Revert the branch. Existing platform-specific emitters are unchanged, so users who don't use Skills see no difference.

**Reversibility**: moderate — Skills files are additive (new directory). MCP resource removal could break MCP clients that read `evospec://config` or `evospec://entities` as resources, but these are internal and undocumented to external users.

## ADRs

- Consider ADR: "Adopt Agent Skills as primary cross-platform workflow format"
