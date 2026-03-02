# Domain Contract: MCP + Agent Skills Redesign

> Zone: **hybrid** | Bounded Context: **agent-integration** | Status: **draft**
>
> *Light hybrid contract — Sections 1, 3, 4, 7 populated per EvoSpec hybrid zone rules.*

---

## 1. Context & Purpose

**Bounded Context**: agent-integration

**Context Map Position**: open-host / published language — EvoSpec's agent integration layer publishes Skills and MCP tools as a service consumed by external AI agents (Claude Code, Cursor, Windsurf).

**Ubiquitous Language** (terms specific to this context):

| Term | Definition | Not to be confused with |
|------|-----------|------------------------|
| Skill | A directory with SKILL.md + optional supporting files that teaches an AI agent how to execute a multi-step workflow. Follows the agentskills.io open standard. | Windsurf Workflow or Cursor Rule (platform-specific formats) |
| MCP Resource | Read-only ambient context injected by the host application at conversation start. Application-controlled. | MCP Tool (model-controlled action) |
| MCP Tool | An action the AI model can invoke autonomously during a conversation. Model-controlled. | MCP Resource (ambient context) |
| Progressive Disclosure | Skills pattern: name+description loaded at startup (~100 tokens), full SKILL.md on activation, supporting files on demand. | Eager loading (all context at once) |
| Canonical Workflow | Platform-agnostic YAML definition in `src/evospec/templates/workflows/`. Source of truth for all emitted formats. | Generated output files |

---

## 2. Strategic Classification (Evans — Strategic Design)

**Domain Type**: supporting

**Investment Level**: medium — important for adoption but not the core differentiator (the spec-driven governance model is core)

**Rationale**: Agent integration is the delivery channel. The domain model (zones, invariants, fitness functions) is core; how agents access it is supporting.

---

## 3. Aggregates & Entities

### Aggregate: WorkflowSpec

**Root Entity**: WorkflowSpec (canonical YAML in `src/evospec/templates/workflows/`)

**Entities**:

| Entity | Key Fields | Description |
|--------|-----------|-------------|
| WorkflowSpec | id, name, slash_command, description, steps[], rules[] | Canonical workflow definition. Source of truth. |
| Skill | name, description, SKILL.md body, references/ | Generated output: cross-platform Agent Skills format |
| AgentFile | platform, path, content | Generated output: platform-specific file (Windsurf .md, Claude CLAUDE.md, Cursor .mdc) |
| MCPResource | uri, description, handler | Read-only context exposed to agents via MCP |
| MCPTool | name, description, parameters, handler | Model-controlled action exposed to agents via MCP |
| ContractFile | file_path, format, extracted_entities[] | API contract/response file parsed to extract entities |
| UpstreamAPI | upstream_name, endpoints[], source_spec | API surface from an upstream service's traceability data |

**Value Objects**:

| Value Object | Fields | Constraints |
|-------------|--------|-------------|
| SkillFrontmatter | name, description | name: 1-64 chars, lowercase+hyphens, must match directory name |
| StepInstruction | id, title, instructions, interactive?, critical? | id must be sequential integer |
| MCPToolReference | server_name, tool_name | Fully-qualified reference in Skills: `evospec:tool_name` |
| ExtractedEntity | name, fields[], relationships[] | Entity parsed from a contract file (not persisted) |

---

## 4. Invariants (DDD + Evolutionary Architecture)

> Invariants are testable propositions that must ALWAYS hold true within this bounded context.

| ID | Invariant Statement | Enforcement | Fitness Function |
|----|-------------------|-------------|-----------------|
| AGT-INV-001 | Every canonical workflow YAML MUST produce a valid Skill with name matching `evospec-{id}` | test | `tests/test_agents.py` |
| AGT-INV-002 | MCP Resources MUST NOT expose internal project config (teams, strategy, reverse settings) | code-review | Manual review of `server.py` resources |
| AGT-INV-003 | MCP Tools that mutate state (write files, execute commands) MUST be clearly annotated as destructive | code-review | Manual review of tool docstrings |
| AGT-INV-004 | Skills MUST reference shared context via `references/context.md`, not inline the full framework description | test | `tests/test_agents.py` |
| AGT-INV-005 | `evospec generate agents` with no platform flag MUST generate Skills + all 3 legacy platform formats | test | `tests/test_agents.py` |
| AGT-INV-006 | Skills MUST reference MCP tools by fully-qualified name (`evospec:tool_name`) in step instructions | test | `tests/test_agents.py` |
| AGT-INV-007 | `get_entities()` and `get_invariants()` tools MUST support filtering by bounded context | test | `tests/test_mcp.py` |
| AGT-INV-008 | `get_upstream_apis()` MUST return only data from upstream services' published traceability, never local project internals | test | `tests/test_mcp.py` |
| AGT-INV-009 | `parse_contract_file()` MUST validate file exists and is a supported format before parsing | test | `tests/test_mcp.py` |
| AGT-INV-010 | New fields in spec.schema.json MUST be optional — no new entries in `required` arrays — so specs created with older EvoSpec versions pass validation | test | `tests/test_check.py` |
| AGT-INV-011 | Deprecated MCP resources (`evospec://config`, `evospec://entities`, `evospec://invariants`) MUST return data (not errors) with a deprecation notice until next major version | test | `tests/test_mcp.py` |

---

## 5–6. State Machine & Domain Events

*Not applicable for this hybrid change — no state transitions or domain events.*

---

## 7. Authorization & Policies

**Access Rules**:

| Operation | Allowed Roles | Additional Conditions |
|-----------|--------------|----------------------|
| Read MCP resources | Any AI agent with MCP connection | Local filesystem access only (stdio transport) |
| Call MCP read tools | Any AI agent | No side effects |
| Call MCP write tools | Any AI agent | Agent client SHOULD prompt user for confirmation |
| Execute fitness functions | Any AI agent | Subprocess timeout enforced (120s) |

**Tenant Isolation**: N/A — EvoSpec is a local CLI tool, not multi-tenant.

**Data Sensitivity**: Low — spec metadata is project-internal. No PII, PHI, or financial data.

---

## 8–10. Migration, Fitness Functions, Team Ownership

*See improvement-scope.md for rollback plan and acceptance criteria.*

---

## 11. Traceability

**Modules**:
- `src/evospec/core/agents.py` — Skills emitter + PLATFORMS update
- `src/evospec/mcp/server.py` — resource trimming + new tools
- `src/evospec/templates/workflows/_context.yaml` — MCP + Skills metadata
- `src/evospec/cli/main.py` — platform choices
- `examples/multi-system-ux-discovery/README.md`
- `examples/multi-system-ux-discovery/WALKTHROUGH.md`

---

## 12. Anti-Requirements (What This Is NOT)

1. This is NOT a replacement for platform-specific emitters — Windsurf, Claude, and Cursor formats are kept as fallback.
2. This is NOT an MCP authentication/authorization system — security is out of scope.
3. This is NOT the `evospec prompt` bootstrap command — that is a separate change.
4. This does NOT change the canonical workflow YAML format — Skills are generated FROM existing YAMLs.
