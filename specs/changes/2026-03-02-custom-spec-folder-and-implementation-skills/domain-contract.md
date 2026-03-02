# Domain Contract: Custom Spec Folder + Implementation Skills

> Zone: **core** | Bounded Context: **domain-management** | Status: **draft**

---

## 1. Context & Purpose

**Bounded Context**: domain-management

**Context Map Position**: shared kernel (paths used by all contexts; skills consumed by agent-integration)

**Ubiquitous Language**:

| Term | Definition | Not to be confused with |
|------|-----------|------------------------|
| Custom spec folder | User-configured path for spec storage (default: `specs/`) | Spec template directory |
| Implementation skill | A project-specific coding rule or pattern that AI agents should follow | EvoSpec workflow (process, not code rule) |
| Skill category | Grouping for skills: error-handling, testing, architecture, naming, dependencies, security | Zone classification (edge/hybrid/core) |
| skills.yaml | Domain file defining project-specific implementation skills | workflows/*.yaml (agent workflow definitions) |

---

## 2. Strategic Classification

**Domain Type**: core — paths are foundational infrastructure; skills are a unique differentiator for AI code quality

**Investment Level**: high (skills) / medium (custom paths)

**Rationale**: Custom paths remove an adoption blocker. Skills are a unique value proposition — no other spec tool lets teams define project-specific coding rules that get injected into AI agent context.

---

## 3. Aggregates & Entities

### Aggregate: ProjectConfig (extended)

**Root Entity**: ProjectConfig

**Entities**:

| Entity | Key Fields | Description |
|--------|-----------|-------------|
| ProjectConfig | paths, project, reverse, strategy | Extended with custom paths |
| Skill | category, rules | Project-specific implementation rule |
| SkillRegistry | skills[] | Collection of all skills loaded from skills.yaml |

**Value Objects**:

| Value Object | Fields | Constraints |
|-------------|--------|-------------|
| PathConfig | specs, domain, templates, adrs, checks | All relative to project root |
| SkillCategory | category name | One of: error-handling, testing, architecture, naming, dependencies, security (extensible) |

---

## 4. Invariants

| ID | Invariant Statement | Enforcement | Fitness Function |
|----|-------------------|-------------|-----------------|
| CUSTOM-PATH-001 | All CLI commands and config loading MUST respect `paths.specs` from evospec.yaml | test | `tests/test_config.py` |
| CUSTOM-PATH-002 | Default spec folder MUST remain `specs/` for backward compatibility | test | `tests/test_config.py` |
| SKILLS-001 | Implementation skills MUST be included in generated agent files (CLAUDE.md, .windsurf/, .cursor/) | test | `tests/test_agents.py` |

---

## 5. State Machine & Transitions

N/A

---

## 6. Domain Events

N/A

---

## 7. Authorization & Policies

N/A

---

## 8. Backwards Compatibility & Migration

**Breaking changes**: None — both features are additive with clear defaults
- [ ] Schema migration required — No
- [ ] API contract change — No
- [ ] Event schema change — No
- [ ] Data backfill needed — No

**Migration strategy**: Existing projects without `paths.specs` in evospec.yaml default to `specs/`. Existing projects without `skills.yaml` simply don't have skills injected.

**Rollback plan**: Revert path resolution to hardcoded defaults; remove skills loading.

**Reversibility**: trivial

---

## 9. Fitness Functions

| Name | Type | Dimension | Implementation |
|------|------|-----------|---------------|
| Custom path resolution in all commands | unit-test | correctness | `tests/test_config.py` |
| Default path backward compatibility | unit-test | backwards-compatibility | `tests/test_config.py` |
| Skills injected into CLAUDE.md | integration-test | correctness | `tests/test_agents.py` |
| Skills injected into Windsurf files | integration-test | correctness | `tests/test_agents.py` |
| Skills injected into Cursor files | integration-test | correctness | `tests/test_agents.py` |
| Skills served via MCP evospec://skills | integration-test | correctness | `tests/test_mcp.py` |

---

## 10. Team Ownership

**Owning Team**: evospec-core

**Team Type**: platform

**Cross-Team Dependencies**: None

**Cognitive Load Assessment**: Low — path resolution is a simple config change; skills loading follows the existing domain file pattern.

---

## 11. Traceability

**Endpoints**: None

**Tables**: None

**Modules**:
- `evospec.core.config` — custom path resolution, skills loading
- `evospec.core.init` — `--specs-dir` flag, skills.yaml stub creation
- `evospec.core.agents` — inject skills into generated agent files
- `evospec.cli.main` — pass custom paths through commands
- `evospec.mcp.server` — `evospec://skills` resource

**Related ADRs**:
- Skills are project-wide, not per-change
- Custom paths via `paths.*` in evospec.yaml (single source of truth)

---

## 12. Anti-Requirements

1. **No per-change skills** — Skills are project-wide. Per-change overrides would create conflicting rules.
2. **No skill enforcement in `evospec check`** — Skills are guidance for AI agents, not linting rules. Future enhancement could add detection.
3. **No dynamic skill loading** — Skills come from skills.yaml only, not from external URLs or plugins.
4. **No path auto-migration** — Changing `paths.specs` doesn't move existing files. User must move them manually.
