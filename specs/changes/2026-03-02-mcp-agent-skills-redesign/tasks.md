# Tasks: MCP + Agent Skills Redesign

> Zone: **hybrid** | Spec: `specs/changes/2026-03-02-mcp-agent-skills-redesign`
> Generated from: improvement-scope.md + domain-contract.md

---

## Phase 1: Setup

- [ ] T001 [Setup] Add `skills` to `PLATFORMS` tuple and `EMITTERS` dict in `src/evospec/core/agents.py`
- [ ] T002 [Setup] Add `skills` to `--platform` CLI choices in `src/evospec/cli/main.py`

## Phase 2: Skills Emitter

- [ ] T003 [Core] Implement `_build_skills_context_md(ctx)` helper in `src/evospec/core/agents.py` — generates shared `references/context.md` content from `_context.yaml`
- [ ] T004 [Core] Implement `_emit_skills(workflows, ctx, dest)` emitter in `src/evospec/core/agents.py` — generates `.agents/skills/evospec-{id}/SKILL.md` + `references/context.md` for each canonical workflow
- [ ] T005 [Core] SKILL.md frontmatter: `name` (matching directory name) and `description` per agentskills.io spec
- [ ] T006 [Core] SKILL.md body: title, context (brief), when_to_use, steps (compact), rules, reference link to `references/context.md`
- [ ] T007 [Core] Skills-MCP explicit references: each step that uses an MCP tool MUST reference it as `evospec:tool_name` (fully-qualified) in the step instructions

## Phase 3: MCP Resource Trimming + Deprecation Aliases

- [ ] T008 [Core] Add `evospec://project` resource in `src/evospec/mcp/server.py` — expose only project name, description, and zone defaults
- [ ] T009 [Core] Convert `evospec://entities` resource handler to use new `get_entities(context?, upstream?)` tool logic — add optional filters by bounded context and upstream name
- [ ] T010 [Core] Convert `evospec://invariants` resource handler to use new `get_invariants(context?)` tool logic — add optional filter by bounded context
- [ ] T011 [Core] Keep `evospec://glossary` and `evospec://context-map` resources unchanged
- [ ] T012 [Core] Remove MCP prompts `discover_feature` and `domain_contract` from `src/evospec/mcp/server.py` — replaced by Skills
- [ ] T012a [Core] **Deprecation alias**: Keep `evospec://config` resource — return same data as `evospec://project` + `"_deprecated": "Use evospec://project instead"` field
- [ ] T012b [Core] **Deprecation alias**: Keep `evospec://entities` resource — delegate to `get_entities()` internally + prepend deprecation notice in output
- [ ] T012c [Core] **Deprecation alias**: Keep `evospec://invariants` resource — delegate to `get_invariants()` internally + prepend deprecation notice in output
- [ ] T012d [Core] **Schema version gate**: In `check.py`, read `schema.version` from `evospec.yaml` — if version is newer than known, emit warning (not error). If missing, default to `"1.0.0"`
- [ ] T012e [Core] **Schema backwards compat**: Verify no new `required` entries added to spec.schema.json `required` array or `allOf` conditional `required` arrays

## Phase 4: New MCP Tools (Cross-System)

- [ ] T013 [Core] Implement `get_upstream_apis(upstream_name?)` tool in `src/evospec/mcp/server.py` — reads upstream repos' spec.yaml traceability.endpoints and returns aggregated API surface
- [ ] T014 [Core] Create `src/evospec/mcp/contract_parser.py` — module for parsing API contract files into entities
- [ ] T015 [Core] Implement OpenAPI/Swagger parser in `contract_parser.py` — extract entities from `definitions`/`components.schemas`, fields from properties, relationships from `$ref`
- [ ] T016 [Core] Implement JSON Schema parser in `contract_parser.py` — extract entities from top-level object properties
- [ ] T017 [Core] Implement JSON example parser in `contract_parser.py` — infer entity structure from a JSON response example file
- [ ] T018 [Core] Implement `parse_contract_file(file_path)` tool in `src/evospec/mcp/server.py` — delegates to `contract_parser.py`, validates file exists and format is supported

## Phase 5: Context & Metadata Update

- [ ] T019 [Core] Update `mcp.resources` in `src/evospec/templates/workflows/_context.yaml` — replace `evospec://config` with `evospec://project`, remove entities/invariants from resources
- [ ] T020 [Core] Update `mcp.tools` in `src/evospec/templates/workflows/_context.yaml` — add `get_entities`, `get_invariants`, `get_upstream_apis`, `parse_contract_file`
- [ ] T021 [Core] Remove `mcp.prompts` section from `_context.yaml` (Skills replace MCP prompts)
- [ ] T022 [Core] Add `skills` section to `_context.yaml` documenting Agent Skills format, directory structure, progressive disclosure, and Skills-MCP tool references

## Phase 6: Example Update (Two Personas)

- [ ] T023 [Core] Update `examples/multi-system-ux-discovery/README.md` — add two-persona model (internal dev + external designer), explain MCP + Skills actor model
- [ ] T024 [Core] Update `README.md` — replace `evospec://invariants` resource refs with `evospec:get_invariants` tool, replace `evospec://config` with `evospec://project`
- [ ] T025 [Core] Update `README.md` — add scenario showing designer's AI using `evospec:get_upstream_apis` and `evospec:parse_contract_file` to understand upstream API contract
- [ ] T026 [Core] Update `WALKTHROUGH.md` — show how AI agent activates `evospec-discover` skill → calls `evospec:get_entities`, `evospec:check_invariant_impact` MCP tools
- [ ] T027 [Core] Update `WALKTHROUGH.md` — add Act showing designer providing an API response file and agent using `evospec:parse_contract_file` to extract entities
- [ ] T028 [Core] Update `WALKTHROUGH.md` — update "What EvoSpec Supports Today" table with Skills, new MCP tools, and cross-system capabilities

## Phase 7: Regenerate Agent Files

- [ ] T029 [Core] Run `evospec generate agents` to regenerate all platform files including new Skills output
- [ ] T030 [Core] Verify generated `.agents/skills/` contains 10 skill directories with valid SKILL.md files
- [ ] T031 [Core] Verify generated CLAUDE.md, `.windsurf/workflows/`, `.cursor/rules/` reflect updated MCP surface

## Phase 8: Guardrails & Testing

- [ ] T032 [Guardrails] Verify existing tests pass: `poetry run pytest tests/`
- [ ] T033 [Guardrails] Add test for Skills emitter in `tests/test_agents.py` — verify 10 skills generated with correct frontmatter, MCP tool references, and `references/context.md`
- [ ] T034 [Guardrails] Add test verifying `evospec://project` resource returns lean metadata (no teams, strategy, reverse config)
- [ ] T035 [Guardrails] Add test for `get_entities(context?, upstream?)` tool — verify filtering works
- [ ] T036 [Guardrails] Add test for `get_invariants(context?)` tool — verify filtering works
- [ ] T037 [Guardrails] Add test for `get_upstream_apis()` tool — verify it reads upstream traceability
- [ ] T038 [Guardrails] Add test for `parse_contract_file()` — verify OpenAPI, JSON Schema, and JSON example parsing
- [ ] T038a [Guardrails] Add test: deprecated MCP resources (`evospec://config`, `evospec://entities`, `evospec://invariants`) return data + deprecation notice, not errors
- [ ] T038b [Guardrails] Add test: spec created with EvoSpec v1.0.0 (no new fields) passes `evospec check` without errors on new version
- [ ] T038c [Guardrails] Add test: spec.schema.json has no new entries in top-level `required` or `allOf` conditional `required`
- [ ] T039 [Guardrails] Run `evospec check` to validate all specs

## Phase 9: Polish

- [ ] T040 [Polish] Update `WALKTHROUGH.md` "Gaps Identified" section to remove gaps now addressed by Skills and new tools
- [ ] T041 [Polish] Review all generated SKILL.md files are under 500 lines (progressive disclosure best practice)

---

## Invariant-to-Task Mapping

| Invariant | Tasks |
|-----------|-------|
| AGT-INV-001: Every workflow YAML → valid Skill with name `evospec-{id}` | T004, T005, T033 |
| AGT-INV-002: MCP Resources MUST NOT expose internal config | T008, T034 |
| AGT-INV-003: MCP write tools annotated as destructive | T009, T010 (docstrings) |
| AGT-INV-004: Skills reference shared context.md | T006, T033 |
| AGT-INV-005: Default generate emits Skills + 3 legacy formats | T001, T033 |
| AGT-INV-006: Skills reference MCP tools by fully-qualified name | T007, T033 |
| AGT-INV-007: get_entities/get_invariants support context filtering | T009, T010, T035, T036 |
| AGT-INV-008: get_upstream_apis returns only upstream data | T013, T037 |
| AGT-INV-009: parse_contract_file validates file and format | T018, T038 |
| AGT-INV-010: New schema fields MUST be optional (no new required) | T012e, T038c |
| AGT-INV-011: Deprecated MCP resources return data + deprecation notice | T012a, T012b, T012c, T038a |

---

## Dependency Graph

```
Phase 1 (Setup) → Phase 2 (Skills Emitter) ───────────→ Phase 5 (Context Update) → Phase 7 (Regenerate)
                                                        ↗
Phase 3 (MCP Trimming) ──→ Phase 4 (New MCP Tools) ──→ Phase 5
                                                          ↓
Phase 6 (Example Update) ←────────────────────────────── Phase 5
                                                          ↓
Phase 7 → Phase 8 (Guardrails) → Phase 9 (Polish)
```

Within phases:
- T001 || T002 (parallel)
- T008 || T009 || T010 || T011 || T012 (parallel)
- T013 || T014 (parallel), T015 → T016 → T017 → T018 (sequential, same module)
- T019 || T020 || T021 || T022 (parallel)
- T023 || T024 || T025 (parallel), T026 || T027 || T028 (parallel)

---

## Summary

- **Total tasks**: 49
- **Phases**: 9
- **Parallel opportunities**: 6 parallel groups across phases
- **Invariant coverage**: 11/11 (100%)
- **Suggested MVP**: Phases 1-5 (Skills emitter + MCP trimming + deprecation aliases + new tools + context update)
- **Estimated effort**: ~4-5 implementation sessions
