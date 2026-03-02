# EvoSpec — AI Agent Context

> This file is read automatically by Claude Code. It provides project context for AI-assisted development.

## Framework

This project uses **EvoSpec** — a spec-driven delivery toolkit.

**Core principle**: Progressive specs at the edge. Contracts in the core.

## Two Layers

### Discovery Layer (edge)
- Fast, iterative, experimental
- Specs are hypotheses (discovery-spec.md)
- Governed by metrics + kill criteria
- Knowledge stage: Mystery → Heuristic
- Design Thinking drives exploration

### Core Engine (center)
- Deliberate, versioned, audited
- Specs are contracts (domain-contract.md)
- Governed by invariants + fitness functions + CI gates
- Knowledge stage: Heuristic → Algorithm
- DDD drives codification

## Spec Structure

```
specs/
├── changes/                    # Change specifications
│   └── YYYY-MM-DD-<slug>/
│       ├── spec.yaml           # Machine-readable classification + metadata
│       ├── discovery-spec.md   # Hypothesis, experiments, learning (edge/hybrid)
│       ├── domain-contract.md  # Entities, invariants, fitness functions (core/hybrid)
│       ├── tasks.md            # Implementation tasks (AI work queue)
│       └── checks/             # Executable guardrails
├── domain/
│   ├── glossary.md             # Ubiquitous language
│   └── context-map.md          # Bounded context relationships
docs/
└── adr/                        # Architecture Decision Records
```

## Zone Classification

| Zone | Required Artifacts | Guardrails |
|------|-------------------|------------|
| **edge** | discovery-spec.md, spec.yaml with discovery section | Metrics + kill criteria |
| **hybrid** | discovery-spec.md + domain-contract.md (minimal) | Contract tests at boundaries |
| **core** | domain-contract.md, spec.yaml with invariants + fitness_functions | Fitness functions + CI gates |

## Three Entry Points

Not every change needs discovery. Choose the right entry point:

| Type | When | Workflow | Artifacts |
|------|------|----------|-----------|
| **Experiment** | Unknown if users want it | `/evospec.discover` → `/evospec.learn` | discovery-spec.md, spec.yaml |
| **Improvement** | Known need, known solution | `/evospec.improve` | improvement-scope.md, spec.yaml, tasks.md |
| **Bug fix** | Something is broken | `/evospec.fix` | bugfix-report.md, spec.yaml, tasks.md |

All three entry points run the **invariant impact check** before proceeding.

## Invariant Safety Net

The Core Engine publishes invariants. The Discovery Layer (and improvements/bugfixes) read them before making changes.

```
Core Engine (stable)                 Any Change (experiment/improve/fix)
┌──────────────────┐                ┌────────────────────────────┐
│ INV-001: Order   │──publishes──→  │ check_invariant_impact()   │
│ must have ≥ 1    │                │   conflicts: [INV-001]     │
│ LineItem         │                │   resolution: exempt /     │
│                  │                │     evolve / shadow /      │
│ Fitness function:│                │     redesign               │
│ test_order.py    │                └────────────────────────────┘
└──────────────────┘
```

**Resolution options** for invariant conflicts:
- **exempt** — Experiment behind a feature flag, don't touch the invariant
- **evolve** — Propose INV-001-v2 with migration path + new fitness function
- **shadow** — Validate need via interviews/analytics BEFORE touching schema
- **redesign** — Change approach to avoid the conflict

MCP tool: `check_invariant_impact(entities=[...], contexts=[...], description="...")`
Resource: `evospec://invariants` — returns all invariants from all core/hybrid specs

## Working with Specs

### Before implementing ANY change:
1. Determine the change type: experiment, improvement, or bugfix
2. Run invariant impact check (MCP `check_invariant_impact` or manual scan)
3. Check if a spec exists in `specs/changes/`
4. Read `spec.yaml` to understand the zone and classification
5. Read the appropriate artifact (discovery-spec.md, improvement-scope.md, or bugfix-report.md)
6. Read `tasks.md` if it exists — it's your implementation plan

### When implementing Core zone changes:
- **Invariants are non-negotiable** — every invariant in spec.yaml must be enforced
- **Write fitness functions FIRST** (TDD for core)
- **Check authorization rules** in domain-contract.md before implementing endpoints
- **Respect state machine transitions** — forbidden transitions must raise errors
- **Tenant isolation**: every query on tenant-scoped entities must filter by tenant_id

### When implementing Edge zone changes:
- **Prototype quality is acceptable** — focus on validating the hypothesis
- **Instrument metrics** to test assumptions listed in discovery-spec.md
- **Respect kill criteria** — don't over-invest before validation
- **Keep it reversible** — edge changes should be easy to remove

### When creating ADRs:
- Use the template in `specs/_templates/adr.md`
- Include "What would have to be true" section (Roger Martin)
- Include reversibility assessment
- Link to related specs

## MCP Server (Programmatic Access)

EvoSpec exposes an MCP server that AI agents can call as structured tools:

**Tools** (actions):
- `list_specs()` — list all specs with zone, status, artifacts
- `read_spec(spec_path)` — read a spec with all artifacts
- `check_spec(spec_path?)` — run validation checks
- `classify_change(...)` — classify a change into edge/hybrid/core
- `check_invariant_impact(entities, contexts, description)` — **safety net**: check what invariants a change affects
- `get_tasks(spec_path)` — parse tasks.md into structured data
- `update_task(spec_path, task_id, done)` — mark tasks complete
- `list_features()` — list registered features with lifecycle status
- `get_discovery_status(spec_path)` — assumptions, experiments, health, deadlines
- `record_experiment(spec_path, assumption_id, ...)` — log experiment results
- `update_assumption(spec_path, assumption_id, ...)` — update assumption status
- `run_fitness_functions(spec_path?)` — execute fitness function tests

**Resources** (context):
- `evospec://config` — project configuration
- `evospec://glossary` — ubiquitous language
- `evospec://context-map` — bounded context relationships
- `evospec://invariants` — **all invariants from all core/hybrid specs** (the safety net)

**Prompts** (templates):
- `discover_feature(description)` — discovery spec generation prompt
- `domain_contract(bounded_context)` — domain contract generation prompt

To start: `evospec serve` or `evospec-mcp`

## Features Registry

Features are tracked in `evospec.yaml` with lifecycle status:

```
discovery → specifying → implementing → validating → shipped
                                                   → killed
```

Each feature maps to a knowledge stage:
- **discovery** = mystery (Design Thinking explores)
- **specifying/implementing** = heuristic (patterns emerging)
- **shipped** = algorithm (codified, enforced)

CLI: `evospec feature list`, `evospec feature add "title"`, `evospec feature update feat-001 --status implementing`

## Continuous Discovery Loop

The Discovery Layer is **not a one-shot document**. It's a learning system with weekly cycles:

```
Hypothesize → Experiment → Learn → Decide → (repeat or promote)
```

### Assumption Lifecycle
```
untested → testing → validated    → promote-to-core (becomes invariant)
                   → invalidated  → pivot or kill
                   → pivoted      → new iteration
```

### Key MCP Tools for Discovery
- `get_discovery_status(path)` — dashboard: assumptions, experiments, health, deadline warnings
- `record_experiment(path, assumption_id, ...)` — log results, update assumption, log learning
- `update_assumption(path, id, status, pivot_to)` — manual status update

### CLI
- `evospec learn` — interactive experiment recording
- `/evospec.learn` — Windsurf workflow for the feedback loop

### Rules for Edge Zone
- Every assumption needs a **category**: desirability, feasibility, viability, usability
- Every experiment must end with a **decision**: continue, pivot, kill, promote-to-core
- Pivots **increment the iteration counter** in spec.yaml
- **Kill deadlines are enforced** — MCP warns when approaching
- When all high-risk assumptions are resolved → move to `/evospec.tasks`

## Validation

Run `evospec check` to validate all specs. For core zone, this checks:
- Schema validation against JSON Schema
- Invariants have enforcement mechanisms
- Fitness functions are defined
- Required artifacts exist for the zone

Run `evospec check --run-fitness` to also **execute** fitness function tests.

Run `evospec fitness` to run fitness functions independently.

## Knowledge Funnel (Roger Martin)

```
Mystery  → use Design Thinking to explore    → Discovery Layer (edge)
Heuristic → patterns emerging, judgment needed → Hybrid zone
Algorithm → codified, enforceable, automated  → Core Engine (core)
```

When you encounter ambiguity about how to implement something:
- If it's a Mystery: don't codify it yet. Prototype and learn.
- If it's a Heuristic: document as an invariant candidate. Test it.
- If it's an Algorithm: enforce it with a fitness function.
