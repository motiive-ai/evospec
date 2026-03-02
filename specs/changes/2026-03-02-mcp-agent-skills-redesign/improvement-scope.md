# Improvement Scope: MCP + Agent Skills Redesign

> Zone: **hybrid** | Type: **improvement** | Status: **draft**

---

## What Needs to Change

EvoSpec currently generates 22 platform-specific files across 3 AI platforms (Windsurf, Claude Code, Cursor) and exposes an MCP server that overexposes internal project data while missing critical cross-system capabilities. In 2025-2026, **Agent Skills** emerged as an open standard (agentskills.io) supported natively by all three platforms. This improvement:

1. Adopts Agent Skills as the primary cross-platform workflow format
2. Trims the MCP surface to expose only domain context that agents actually need
3. Adds new MCP tools for cross-system use cases (upstream API discovery, contract file parsing)
4. Makes Skills explicitly reference MCP tools so agents know what to call

### Two Personas

| Persona | Example | How they use EvoSpec |
|---------|---------|---------------------|
| **Internal** — developer using EvoSpec on their own codebase | Backend engineer maintaining Order Service | Skills for workflow, MCP for spec management |
| **External** — designer/dev consuming upstream contracts | Product designer building Smart Cart UI that calls Order + Inventory APIs | Skills for discovery, MCP for entity/invariant/API visibility across system boundaries |

The **external persona** is currently underserved. They can check invariant impact but can't:
- See what upstream API endpoints are available
- Parse an API response/contract file to understand entities
- Filter entities or invariants by context or upstream

## Why Now

1. **Agent Skills is now supported by Claude Code, Cursor, and Windsurf** — EvoSpec can generate one set of skill files instead of maintaining three platform-specific emitters.
2. **MCP best practices** (2025-06 spec) make clear that Resources should be lean ambient context, not full config dumps. `evospec://config` currently exposes the entire `evospec.yaml` including internal team/strategy data.
3. **Skills use progressive disclosure** — only name+description loaded at startup (~100 tokens), full instructions on activation. This is more efficient than platform-specific workflow files loaded at conversation start.
4. **Cross-system use cases are real** — a designer building a UI card that depends on another team's API needs to see the contract (entities, invariants, endpoints). If the API contract is a file (OpenAPI, JSON response example), the AI agent needs to parse it.
5. **The multi-system-ux-discovery example** needs to clearly demonstrate how MCP + Skills work together for both internal and external personas.

## Scope

### In Scope

- **Skills emitter**: Add `_emit_skills()` to `agents.py` that generates `.agents/skills/evospec-*/SKILL.md` from canonical workflow YAMLs
- **Skills-MCP explicit references**: Each Skill's steps must reference MCP tools by fully-qualified name (e.g., `evospec:check_invariant_impact`) so agents know what to call
- **MCP resource trimming**: Replace `evospec://config` with lean `evospec://project` (name, description, zone defaults only); keep `evospec://glossary` and `evospec://context-map`; move `evospec://entities` and `evospec://invariants` from resources to on-demand tools
- **MCP tool: `get_entities(context?, upstream?)`**: Filtered entity registry — filter by bounded context or upstream name
- **MCP tool: `get_invariants(context?)`**: Filtered invariants — filter by bounded context
- **MCP tool: `get_upstream_apis(upstream_name?)`**: List API endpoints from upstream services' traceability data
- **MCP tool: `parse_contract_file(file_path)`**: Parse an API contract/response file (OpenAPI, JSON Schema, JSON example, GraphQL, Protobuf) and extract entities/fields/relationships
- **_context.yaml update**: Add `skills` section documenting the new format; update `mcp` section to reflect trimmed resources and new tools
- **Example update**: Revise `examples/multi-system-ux-discovery/README.md` and `WALKTHROUGH.md` to demonstrate both personas using MCP tools + Skills
- **CLI update**: Add `skills` to `--platform` choices in `evospec generate agents`
- **Test coverage**: Ensure existing tests pass with the new emitter and MCP changes

### Out of Scope

- Removing existing Windsurf/Claude/Cursor emitters (kept as fallback)
- Changing canonical workflow YAML format
- The `evospec prompt` bootstrap command (separate change)
- MCP authentication/authorization changes
- Full OpenAPI spec import (parse_contract_file extracts entities, doesn't import the full spec)

## Affected Areas

**Endpoints**: None (MCP resources are not REST endpoints)

**Tables**: None

**Modules**:
- `src/evospec/core/agents.py` — add Skills emitter, update PLATFORMS, Skills-MCP tool references
- `src/evospec/mcp/server.py` — replace `evospec://config` resource, move entities/invariants to tools, add `get_upstream_apis`, `parse_contract_file`
- `src/evospec/mcp/contract_parser.py` — new module for parsing API contract/response files (OpenAPI, JSON Schema, JSON examples)
- `src/evospec/templates/workflows/_context.yaml` — update MCP section, add Skills section
- `src/evospec/cli/main.py` — add `skills` to platform choices
- `examples/multi-system-ux-discovery/README.md` — add two-persona model (internal + external), Skills + MCP actor model
- `examples/multi-system-ux-discovery/WALKTHROUGH.md` — show Skills invocation + new tools in walkthrough

**Bounded Contexts**:
- `agent-integration` — Skills generation, workflow format, Skills-MCP references
- `mcp-server` — resource/tool surface redesign, new cross-system tools

## Invariant Impact

No invariant conflicts detected. This change does not touch persistence, auth, billing, or existing domain invariants. The MCP surface changes are additive (new tools) and subtractive (removing overexposed resources) — no existing invariant enforcement is affected.

## Acceptance Criteria

### Skills
- [ ] `evospec generate agents --platform skills` produces `.agents/skills/evospec-*/SKILL.md` for all 10 workflows
- [ ] Each SKILL.md has valid frontmatter (name, description) and references shared `context.md`
- [ ] Skills reference MCP tools by fully-qualified name (e.g., `evospec:check_invariant_impact`)
- [ ] `evospec generate agents` (no platform flag) generates Skills + all 3 legacy platforms

### MCP Resources
- [ ] `evospec://project` resource returns lean project metadata (no teams, strategy, reverse config)
- [ ] `evospec://config` resource is removed
- [ ] `evospec://glossary` and `evospec://context-map` resources unchanged

### MCP Tools (existing, moved)
- [ ] `get_entities(context?, upstream?)` tool returns filtered entity registry (by context and/or upstream name)
- [ ] `get_invariants(context?)` tool returns filtered invariants (by bounded context)

### MCP Tools (new, cross-system)
- [ ] `get_upstream_apis(upstream_name?)` tool returns endpoint list from upstream traceability data
- [ ] `parse_contract_file(file_path)` tool parses OpenAPI/JSON Schema/JSON example files and extracts entities/fields/relationships

### Context & Documentation
- [ ] `_context.yaml` documents Skills format, updated MCP surface, and new tools
- [ ] `examples/multi-system-ux-discovery/` clearly shows both personas (internal dev + external designer) using MCP + Skills

### Quality
- [ ] All existing tests pass
- [ ] New tests cover Skills emitter, new MCP tools, and contract file parsing

## Risks & Rollback

**Risk level**: medium

**Rollback plan**: Revert the branch. Existing platform-specific emitters are unchanged, so users who don't use Skills see no difference.

**Reversibility**: moderate — Skills files are additive (new directory). MCP resource removal could break MCP clients that read `evospec://config` or `evospec://entities` as resources, but these are internal and undocumented to external users.

## ADRs

- Consider ADR: "Adopt Agent Skills as primary cross-platform workflow format"
