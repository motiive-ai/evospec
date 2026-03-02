# Tasks: MCP + Agent Skills Redesign

> Zone: **hybrid** | Spec: `specs/changes/2026-03-02-mcp-agent-skills-redesign`
> Generated from: improvement-scope.md + domain-contract.md

---

## Phase 1: Setup

- [ ] T001 [Setup] Add `skills` to `PLATFORMS` tuple and `EMITTERS` dict in `src/evospec/core/agents.py`
- [ ] T002 [Setup] Add `skills` to `--platform` CLI choices in `src/evospec/cli/main.py`

## Phase 2: Skills Emitter (Core Implementation)

- [ ] T003 [Core] Implement `_build_skills_context_md(ctx)` helper in `src/evospec/core/agents.py` — generates shared `references/context.md` content from `_context.yaml`
- [ ] T004 [Core] Implement `_emit_skills(workflows, ctx, dest)` emitter in `src/evospec/core/agents.py` — generates `.agents/skills/evospec-{id}/SKILL.md` + `references/context.md` for each canonical workflow
- [ ] T005 [Core] SKILL.md frontmatter must include `name` (matching directory name) and `description` per agentskills.io spec
- [ ] T006 [Core] SKILL.md body: title, context (brief), when_to_use, steps (compact), rules, reference link to `references/context.md`
- [ ] T007 [Core] Each skill directory structure: `evospec-{id}/SKILL.md` + `evospec-{id}/references/context.md`

## Phase 3: MCP Resource Trimming

- [ ] T008 [Core] Replace `evospec://config` resource with `evospec://project` in `src/evospec/mcp/server.py` — expose only project name, description, and zone defaults
- [ ] T009 [Core] Convert `evospec://entities` resource to `get_entities()` MCP tool in `src/evospec/mcp/server.py` — same logic, different primitive (model-controlled, on-demand)
- [ ] T010 [Core] Convert `evospec://invariants` resource to `get_invariants()` MCP tool in `src/evospec/mcp/server.py` — same logic, different primitive
- [ ] T011 [Core] Keep `evospec://glossary` and `evospec://context-map` resources unchanged in `src/evospec/mcp/server.py`
- [ ] T012 [Core] Remove MCP prompts `discover_feature` and `domain_contract` from `src/evospec/mcp/server.py` — these are now served by Skills

## Phase 4: Context & Metadata Update

- [ ] T013 [Core] Update `mcp.resources` list in `src/evospec/templates/workflows/_context.yaml` — replace `evospec://config` with `evospec://project`, remove `evospec://entities` and `evospec://invariants` from resources
- [ ] T014 [Core] Update `mcp.tools` list in `src/evospec/templates/workflows/_context.yaml` — add `get_entities()` and `get_invariants()` tools
- [ ] T015 [Core] Remove `mcp.prompts` section from `src/evospec/templates/workflows/_context.yaml` (Skills replace MCP prompts)
- [ ] T016 [Core] Add `skills` section to `src/evospec/templates/workflows/_context.yaml` documenting the Agent Skills format, directory structure, and progressive disclosure pattern

## Phase 5: Example Update

- [ ] T017 [Core] Update `examples/multi-system-ux-discovery/README.md` — add section explaining the MCP + Skills actor model (who controls what: User → Skills, Agent → MCP Tools, Host → MCP Resources)
- [ ] T018 [Core] Update `examples/multi-system-ux-discovery/README.md` — replace references to `evospec://invariants` resource with `get_invariants()` tool, replace `evospec://config` with `evospec://project`
- [ ] T019 [Core] Update `examples/multi-system-ux-discovery/WALKTHROUGH.md` — show how AI agent uses Skills (`/evospec-discover`) to start discovery workflow + MCP tools for invariant checks
- [ ] T020 [Core] Update `examples/multi-system-ux-discovery/WALKTHROUGH.md` — update "What EvoSpec Supports Today" table with Skills and updated MCP surface

## Phase 6: Regenerate Agent Files

- [ ] T021 [Core] Run `evospec generate agents` to regenerate all platform files including new Skills output
- [ ] T022 [Core] Verify generated `.agents/skills/` contains 10 skill directories with valid SKILL.md files
- [ ] T023 [Core] Verify generated CLAUDE.md, `.windsurf/workflows/`, `.cursor/rules/` reflect updated MCP surface

## Phase 7: Guardrails & Testing

- [ ] T024 [Guardrails] Verify existing tests pass: `poetry run pytest tests/`
- [ ] T025 [Guardrails] Add test for Skills emitter in `tests/test_agents.py` — verify 10 skills generated with correct frontmatter and references
- [ ] T026 [Guardrails] Add test verifying `evospec://project` resource returns lean metadata (no teams, strategy, reverse config)
- [ ] T027 [Guardrails] Add test verifying `get_entities()` and `get_invariants()` are registered as MCP tools
- [ ] T028 [Guardrails] Run `evospec check` to validate all specs

## Phase 8: Polish

- [ ] T029 [Polish] Update `examples/multi-system-ux-discovery/WALKTHROUGH.md` "Gaps Identified" section to remove gaps now addressed by Skills
- [ ] T030 [Polish] Review all generated SKILL.md files are under 500 lines (progressive disclosure best practice)

---

## Invariant-to-Task Mapping

| Invariant | Tasks |
|-----------|-------|
| AGT-INV-001: Every workflow YAML → valid Skill with name `evospec-{id}` | T004, T005, T025 |
| AGT-INV-002: MCP Resources MUST NOT expose internal config | T008, T026 |
| AGT-INV-003: MCP write tools annotated as destructive | T009, T010 (docstrings) |
| AGT-INV-004: Skills reference shared context.md | T006, T007, T025 |
| AGT-INV-005: Default generate emits Skills + 3 legacy formats | T001, T005, T025 |

---

## Dependency Graph

```
Phase 1 (Setup) → Phase 2 (Skills Emitter) → Phase 4 (Context Update) → Phase 6 (Regenerate)
                                             ↗
Phase 3 (MCP Trimming) ────────────────────→ Phase 4
                                               ↓
Phase 5 (Example Update) ←─────────────────── Phase 4
                                               ↓
Phase 6 → Phase 7 (Guardrails) → Phase 8 (Polish)
```

Within phases: T001 || T002 (parallel), T003 → T004 → T005 → T006 → T007 (sequential),
T008 || T009 || T010 (parallel), T013 || T014 || T015 || T016 (parallel)

---

## Summary

- **Total tasks**: 30
- **Phases**: 8
- **Parallel opportunities**: T001/T002, T008/T009/T010, T013-T016, T017/T018, T019/T020
- **Invariant coverage**: 5/5 (100%)
- **Suggested MVP**: Phases 1-4 (Skills emitter + MCP trimming + context update)
- **Estimated effort**: ~3 implementation sessions
