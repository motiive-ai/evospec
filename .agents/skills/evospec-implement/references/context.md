# EvoSpec — Agent Context

> Progressive specs at the edge. Contracts in the core.

A spec-driven delivery toolkit that classifies changes as edge/hybrid/core and applies proportional governance.

## Layers

- **Discovery Layer** (edge): Mystery → Heuristic — Design Thinking + Continuous Discovery → `discovery-spec.md`
- **Core Engine** (core): Heuristic → Algorithm — DDD + Evolutionary Architecture → `domain-contract.md`

## Zone Classification

| Zone | Required Artifacts | Guardrails |
|------|-------------------|------------|
| **edge** | discovery-spec.md, spec.yaml with discovery section | Metrics + kill criteria |
| **hybrid** | discovery-spec.md + domain-contract.md (minimal) | Contract tests at boundaries |
| **core** | domain-contract.md, spec.yaml with invariants + fitness_functions | Fitness functions + CI gates |

## Entry Points

- **Experiment**: Unknown if users want it → discovery-spec.md, spec.yaml
- **Improvement**: Known need, known solution → improvement-scope.md, spec.yaml, tasks.md
- **Bug fix**: Something is broken → bugfix-report.md, spec.yaml, tasks.md

## Invariant Resolutions

- **exempt** — Experiment behind a feature flag, don't touch the invariant
- **evolve** — Propose INV-001-v2 with migration path + new fitness function
- **shadow** — Validate need via interviews/analytics BEFORE touching schema
- **redesign** — Change approach to avoid the conflict

## MCP Server

Start: `evospec serve`

**Tools** (model-invoked actions):
- `evospec:list_specs`
- `evospec:read_spec`
- `evospec:check_spec`
- `evospec:classify_change`
- `evospec:check_invariant_impact`
- `evospec:get_tasks`
- `evospec:update_task`
- `evospec:list_features`
- `evospec:get_discovery_status`
- `evospec:record_experiment`
- `evospec:update_assumption`
- `evospec:run_fitness_functions`
- `evospec:get_entities`
- `evospec:get_invariants`
- `evospec:get_upstream_apis`
- `evospec:parse_contract_file`
- `evospec:get_api_contract`
- `evospec:get_file_schema`
- `evospec:get_consumer_context`

**Resources** (ambient context):
- `evospec://bootstrap`
- `evospec://project`
- `evospec://glossary`
- `evospec://context-map`
- `evospec://skills`
- `evospec://api-catalog`
- `evospec://config`
- `evospec://entities`
- `evospec://invariants`

## Implementation Rules

### Before any change:
- Determine the change type: experiment, improvement, or bugfix
- Run invariant impact check (MCP check_invariant_impact or manual scan)
- Check if a spec exists in specs/changes/
- Read spec.yaml to understand the zone and classification
- Read the appropriate artifact (discovery-spec.md, improvement-scope.md, or bugfix-report.md)
- Read tasks.md if it exists — it's your implementation plan

### Core zone:
- Invariants are non-negotiable — every invariant in spec.yaml must be enforced
- Write fitness functions FIRST (TDD for core)
- Check authorization rules in domain-contract.md before implementing endpoints
- Respect state machine transitions — forbidden transitions must raise errors
- Tenant isolation: every query on tenant-scoped entities must filter by tenant_id

### Edge zone:
- Prototype quality is acceptable — focus on validating the hypothesis
- Instrument metrics to test assumptions listed in discovery-spec.md
- Respect kill criteria — don't over-invest before validation
- Keep it reversible — edge changes should be easy to remove

## Knowledge Funnel

- **Mystery** (edge): Prototype and learn, don't codify yet
- **Heuristic** (hybrid): Document as invariant candidate, test it
- **Algorithm** (core): Enforce with a fitness function
