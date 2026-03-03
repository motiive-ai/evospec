# Improvement Scope: Custom Spec Folder + Implementation Skills

> Zone: **core** | Type: **improvement** | Status: **draft**

---

## What Needs to Change

Two adoption friction points: (1) **Custom spec folder** — many projects already have a `specs/` directory for other purposes (API specs, test specs, infrastructure specs). EvoSpec should allow configuring a custom path (e.g., `evospec/`, `.evospec/`, `docs/specs/`) so it doesn't collide with existing directories. (2) **Implementation skills** — teams have project-specific coding rules, patterns, and tech stack conventions that AI agents should follow when implementing changes. Currently there's no way to define these; AI agents follow only the generic EvoSpec workflow rules.

## Why Now

The custom spec folder is an **immediate adoption blocker** — teams with existing `specs/` directories can't use EvoSpec without renaming their existing directory. Implementation skills improve AI code quality for every team, turning project-specific knowledge (error handling patterns, logging conventions, testing strategies, architectural patterns) into enforceable guidance for AI agents.

## Scope

### In Scope

**Sub-feature A: Custom Spec Folder**
- `paths.specs` in `evospec.yaml` configurable to any relative path
- `paths.domain` configurable independently from `paths.specs`
- All CLI commands respect configured paths
- `evospec init` accepts `--specs-dir <path>` to set during initialization
- Default remains `specs/` for backward compatibility

**Sub-feature B: Implementation Skills**
- New `specs/domain/skills.yaml` (or custom domain path) defining project-specific implementation rules
- Skills organized by category: error-handling, testing, architecture, naming, dependencies, security
- Skills injected into generated agent files (CLAUDE.md, .windsurf/, .cursor/)
- Skills served via MCP as `evospec://skills` resource
- `evospec init` creates stub skills.yaml with common categories

### Out of Scope

- Per-change-spec skills (skills are project-wide, not per-change)
- Skill enforcement at code level (skills are guidance, not linting rules)
- Dynamic skill loading from external sources

## Affected Areas

**Endpoints**: None

**Tables**: None

**Modules**:
- `evospec.core.config` — resolve custom paths, load skills.yaml
- `evospec.core.init` — `--specs-dir` flag, create skills.yaml stub
- `evospec.core.agents` — inject skills into generated agent files
- `evospec.cli.main` — pass custom paths through all commands
- `evospec.mcp.server` — `evospec://skills` resource

**Bounded Contexts**:
- `domain-management` — custom paths, skills registry
- `agent-integration` — skills in agent files and MCP
- `cli` — path resolution

## Invariant Impact

No conflicts with existing invariants. Default paths remain `specs/` — fully backward compatible.

## Acceptance Criteria

### Custom Spec Folder
- [ ] `paths.specs` in evospec.yaml respected by all CLI commands (`new`, `check`, `status`, `classify`, etc.)
- [ ] `paths.domain` independently configurable
- [ ] `evospec init --specs-dir evospec/` creates project with custom spec folder
- [ ] Default remains `specs/` when not specified
- [ ] `evospec.yaml` template updated with documentation for custom paths
- [ ] All existing tests pass with both default and custom paths

### Implementation Skills
- [ ] `specs/domain/skills.yaml` loaded by config alongside other domain files
- [ ] Skills injected into CLAUDE.md generation
- [ ] Skills injected into .windsurf/ workflow files
- [ ] Skills injected into .cursor/ rules files
- [ ] Skills served via `evospec://skills` MCP resource
- [ ] `evospec init` creates stub skills.yaml with example categories
- [ ] `evospec generate agents` includes skills in output
- [ ] Skills support categories: error-handling, testing, architecture, naming, dependencies, security

### Example: Custom Spec Folder

```yaml
# evospec.yaml
paths:
  specs: "evospec/changes"      # Custom: avoids collision with existing specs/
  domain: "evospec/domain"      # Custom: follows the same prefix
  templates: "evospec/_templates"
  adrs: "docs/adr"
  checks: "evospec/checks"
```

```bash
# Initialize with custom path
evospec init "my-project" --specs-dir evospec

# All commands respect the configured path
evospec new "add-search" --zone edge
# Creates: evospec/changes/2026-03-02-add-search/spec.yaml

evospec check
# Checks: evospec/changes/*/spec.yaml
```

### Example: Implementation Skills

```yaml
# specs/domain/skills.yaml (or evospec/domain/skills.yaml)
skills:
  - category: "error-handling"
    rules:
      - "Use Result<T, E> pattern for domain operations — never throw exceptions from service layer"
      - "Map all external API errors to domain-specific error types"
      - "Include correlation ID in all error responses"

  - category: "testing"
    rules:
      - "Write integration tests for every API endpoint"
      - "Use factory functions (not fixtures) for test data — factories in tests/factories/"
      - "Assert on behavior, not implementation — mock external services only"

  - category: "architecture"
    rules:
      - "Hexagonal architecture: domain layer has no framework imports"
      - "Repository pattern for all persistence — no direct DB access from services"
      - "Events over direct coupling between bounded contexts"

  - category: "naming"
    rules:
      - "Use ubiquitous language from glossary.md in all class and method names"
      - "Suffix command handlers with 'Handler', query handlers with 'Query'"
      - "Prefix interfaces with 'I' only for ports (e.g., IOrderRepository)"

  - category: "dependencies"
    rules:
      - "No new dependencies without ADR"
      - "Pin all dependency versions in lock file"
      - "Prefer standard library over third-party when functionality is equivalent"

  - category: "security"
    rules:
      - "All endpoints require authentication unless explicitly marked public"
      - "Validate all input at API boundary — never trust client data"
      - "Use parameterized queries only — no string concatenation for SQL"
```

### How Skills Appear in Generated Agent Files

**CLAUDE.md** (excerpt):
```markdown
## Implementation Skills

These are project-specific rules. Follow them when implementing changes.

### Error Handling
- Use Result<T, E> pattern for domain operations — never throw exceptions from service layer
- Map all external API errors to domain-specific error types
- Include correlation ID in all error responses

### Testing
- Write integration tests for every API endpoint
- Use factory functions (not fixtures) for test data — factories in tests/factories/
- Assert on behavior, not implementation — mock external services only

### Architecture
- Hexagonal architecture: domain layer has no framework imports
- Repository pattern for all persistence — no direct DB access from services
...
```

## Risks & Rollback

**Risk level**: low — both sub-features are additive with clear defaults

**Rollback plan**: Revert path resolution to hardcoded `specs/`; remove skills loading. Existing projects unaffected.

**Reversibility**: trivial

## ADRs

- ADR: Skills are project-wide, not per-change — keeps the skill registry simple and avoids conflicting rules between changes
- ADR: Skills are guidance, not enforcement — AI agents should follow them but they don't fail `evospec check`. Future enhancement could add skill-violation detection.
- ADR: Custom paths use `paths.*` in evospec.yaml rather than CLI flags — single source of truth after init
