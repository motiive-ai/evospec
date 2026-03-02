# Implementation Spec: MCP + Agent Skills Redesign

> Zone: **hybrid** | Status: **draft** | Last updated: 2026-03-02
>
> This document is the **as-built blueprint** — it describes what was actually implemented,
> how the pieces connect, and everything needed to reproduce or maintain this component.
> Created as a skeleton by `/evospec.tasks`, filled in during `/evospec.implement`.

---

## 1. Overview

**What was built**: Agent Skills emitter for cross-platform AI workflow delivery + lean MCP resource surface that follows MCP best practices (resources = ambient context, tools = on-demand actions).

**Architecture style**: CLI tool + MCP server (local, stdio transport)

**Tech stack**:

| Layer | Technology | Version | Why |
|-------|-----------|---------|-----|
| Runtime | Python | 3.11+ | Existing stack |
| MCP | FastMCP | latest | Existing MCP server framework |
| Templates | YAML | - | Canonical workflow specs |
| Skills | Markdown (SKILL.md) | agentskills.io v1 | Cross-platform open standard |

**Key decisions**:
- Adopt Agent Skills as primary cross-platform format (additive, not replacing existing emitters)
- Trim MCP resources to lean domain context; move large data to on-demand tools
- Consider ADR: "Adopt Agent Skills as primary cross-platform workflow format"

---

## 2. Component Architecture

```
src/evospec/core/agents.py          ← Skills emitter + existing emitters
src/evospec/mcp/server.py           ← Trimmed resources + new/moved tools
src/evospec/mcp/contract_parser.py  ← NEW: Parse API contract files into entities
src/evospec/templates/workflows/    ← Canonical source (unchanged)
  _context.yaml                     ← Updated MCP + Skills metadata
```

### Components / Modules

| Component | Responsibility | File Path | Dependencies |
|-----------|---------------|-----------|-------------|
| Skills emitter | Generate .agents/skills/ from canonical YAMLs with MCP tool references | `src/evospec/core/agents.py` | `_context.yaml`, workflow YAMLs |
| MCP server | Expose domain context + tools to AI agents | `src/evospec/mcp/server.py` | `evospec.core.config`, `contract_parser` |
| Contract parser | Parse OpenAPI/JSON Schema/JSON example files → entities | `src/evospec/mcp/contract_parser.py` | - |
| Context metadata | Document MCP + Skills surface for generated files | `src/evospec/templates/workflows/_context.yaml` | - |
| CLI | Add `skills` platform choice | `src/evospec/cli/main.py` | `agents.py` |

### Data Flow

```
=== Skills Generation ===
Canonical YAML → _emit_skills() → .agents/skills/evospec-{id}/SKILL.md (with evospec:tool refs)
                                 → .agents/skills/evospec-{id}/references/context.md

=== Internal Persona (developer managing own codebase) ===
AI Agent → MCP Resources (ambient): evospec://project, glossary, context-map
AI Agent → MCP Tools (on-demand): list_specs(), read_spec(), update_task(), ...
User → Skills (/evospec-discover): Agent reads SKILL.md → follows workflow → calls MCP tools

=== External Persona (designer consuming upstream contracts) ===
AI Agent → evospec:get_entities(upstream="order-service") → upstream entity registry
AI Agent → evospec:get_upstream_apis(upstream="order-service") → upstream API endpoints
AI Agent → evospec:parse_contract_file("order-response.json") → entities from API contract
AI Agent → evospec:check_invariant_impact(entities, contexts, description) → safety net
User → Skills (/evospec-discover): workflow guides agent through the above sequence
```

---

## 3–8. Sections to fill during `/evospec.implement`

*Skeleton — will be populated as tasks are completed.*

---

## 9. Invariant Compliance

| Invariant | How Enforced | File:Line | Test |
|-----------|-------------|-----------|------|
| AGT-INV-001: workflow → valid Skill | _emit_skills() naming convention | TBD | TBD |
| AGT-INV-002: no internal config in resources | evospec://project returns lean data | TBD | TBD |
| AGT-INV-003: write tools annotated | Docstrings on update_task, record_experiment, etc. | TBD | TBD |
| AGT-INV-004: Skills reference context.md | _emit_skills() writes references/ | TBD | TBD |
| AGT-INV-005: default generates all formats | PLATFORMS tuple includes "skills" | TBD | TBD |
| AGT-INV-006: Skills reference MCP tools by FQ name | _emit_skills() writes `evospec:tool_name` in steps | TBD | TBD |
| AGT-INV-007: get_entities/get_invariants filter by context | Optional params in tool signature | TBD | TBD |
| AGT-INV-008: get_upstream_apis returns only upstream data | Reads only from `_upstreams` config | TBD | TBD |
| AGT-INV-009: parse_contract_file validates file/format | Validation before parsing | TBD | TBD |
| AGT-INV-010: new schema fields MUST be optional | No new `required` entries in spec.schema.json | TBD | TBD |
| AGT-INV-011: deprecated MCP resources return data + notice | Aliases delegate to new tools | TBD | TBD |

---

## 10. Reproduction Instructions

### Prerequisites

- Python 3.11+
- Poetry
- EvoSpec installed (`poetry install`)

### Build & Run

```bash
# Generate all agent files including Skills
poetry run evospec generate agents

# Generate Skills only
poetry run evospec generate agents --platform skills

# Start MCP server
poetry run evospec serve
```

### Verify

```bash
# Run tests
poetry run pytest tests/

# Validate specs
poetry run evospec check

# Check generated skills
ls .agents/skills/
```

---

## 11. Known Limitations & Tech Debt

| Item | Impact | Planned Fix | Priority |
|------|--------|------------|----------|
| Existing platform emitters kept as fallback | Maintenance burden of 4 formats | Deprecate after Skills adoption verified | Low |
| MCP prompts removed but not replaced by Skills MCP reference | Agents using MCP prompts directly will lose those | Skills are the replacement | Medium |

---

## 12. Changelog

| Date | Phase | What Changed |
|------|-------|-------------|
| 2026-03-02 | Skeleton | Created from `/evospec.tasks` |
