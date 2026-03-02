# Improvement Scope: evospec-core-domain

> Zone: **core** | Type: **improvement** | Status: **draft**

---

## What Needs to Change

EvoSpec should dogfood itself — its own domain model, bounded contexts, invariants, and fitness functions should be formally specified using its own spec artifacts. Additionally, the `reverse` command needs a `cli` subcommand that can introspect Click CLI applications and Python module structures, since the existing `api` and `db` reverse engineers only work for web frameworks and databases.

## Why Now

Without self-specification, EvoSpec's own domain knowledge lives only in code — invisible to the spec engine it provides to others. Dogfooding validates the framework, exposes gaps, and produces a living reference implementation. The `reverse cli` command fills a gap: evospec cannot introspect itself or any CLI/library project.

## Scope

### In Scope

- Domain contract describing evospec's Spec Engine bounded context
- `evospec reverse cli` command: introspect Click commands, Python modules, classes, and functions
- Fitness functions that enforce evospec's own invariants
- Discovery spec for future evospec features

### Out of Scope

- Changes to existing `reverse api` or `reverse db` commands
- MCP server modifications
- Template redesign

## Affected Areas

**Endpoints**: N/A (CLI tool)

**Tables**: N/A (file-based)

**Modules**:
- `evospec.reverse.cli` (new)
- `evospec.cli.main` (add `reverse cli` subcommand)

**Bounded Contexts**:
- Spec Engine (core)
- Reverse Engineering (supporting)

## Invariant Impact

No conflicts — this is additive. No existing invariants are affected.

## Acceptance Criteria

- [x] Domain contract describes evospec's bounded contexts, entities, invariants, and state machines
- [ ] `evospec reverse cli` introspects Click commands from a Python source directory
- [ ] `evospec reverse cli` introspects Python modules, classes, and functions
- [ ] Running `evospec reverse cli --source src` on evospec itself produces meaningful output
- [ ] Existing tests still pass

## Risks & Rollback

**Risk level**: low

**Rollback plan**: Delete new files (`reverse/cli.py`), revert CLI registration. Spec artifacts are just markdown.

**Reversibility**: trivial

## ADRs

- docs/adr/0001-adopt-evospec.md
