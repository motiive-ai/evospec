# EvoSpec

**Progressive specs at the edge. Contracts in the core.**

EvoSpec is a spec-driven delivery toolkit that adapts specification rigor to change risk. It combines Continuous Discovery, Domain-Driven Design, Evolutionary Architecture, Design Thinking, Team Topologies, and Architecture Decision Records into a single, coherent workflow.

## Not just code specs. The whole business.

Most spec frameworks stop at technical requirements. EvoSpec doesn't.

A single EvoSpec change spec captures **everything that matters** — from boardroom strategy to database migration:

| Layer | What EvoSpec captures | Framework |
|-------|----------------------|-----------|
| **Strategy** | Why this matters. Where we play. How we win. | Roger Martin — Playing to Win |
| **Discovery** | What we don't know yet. Assumptions. Experiments. Kill criteria. | Teresa Torres — Continuous Discovery |
| **Domain** | What must always be true. Invariants. State machines. Events. | Evans/Vernon — Domain-Driven Design |
| **Architecture** | Why we chose X over Y. Reversibility. Migration paths. | Nygard — ADRs + Neal Ford — Fitness Functions |
| **Team** | Who owns this. Cognitive load. Interaction modes. | Skelton/Pais — Team Topologies |
| **Risk** | Leadership derailers. Cultural constraints. Organizational blind spots. | Hogan — Organizational Personality |
| **Implementation** | Phased tasks. Parallel opportunities. Exact file paths. AI-executable. | EvoSpec — AI Agent Integration |

**One spec. Seven dimensions. Zero gaps between "what the business wants" and "what gets built."**

Other frameworks give you a template and wish you luck. EvoSpec gives you executable guardrails — fitness functions that run in CI, invariant safety nets that prevent experiments from breaking core domain logic, and kill criteria that stop you from over-investing in ideas that don't work.

## Manifesto

Most spec frameworks assume you know what you're building before you build it. EvoSpec doesn't.

### Discovery is messy. Let it be messy. Capture when it crystallizes.

A UX designer exploring a smart cart prototype doesn't need a domain contract. A developer refactoring a payment state machine doesn't need a discovery spec. Forcing the wrong artifact at the wrong time produces shelfware — documents nobody reads because they were written to satisfy a process, not to solve a problem.

EvoSpec adapts to how work actually happens:

**Principle 1: Never force documentation before the user is ready.**
Experimental work starts with a conversation, not a template. The AI helps you model entities, explore design options, and iterate. You build a prototype. You test it. Only when you're confident do you formalize — and even then, the AI does the writing by scanning your code (`/evospec.capture`).

**Principle 2: Rigor follows risk, not ritual.**
An edge experiment behind a feature flag needs kill criteria and metrics. A core domain change touching the order state machine needs invariants, fitness functions, and a migration plan. Same framework, different rigor — automatically matched to the zone.

**Principle 3: Specs are for humans and machines.**
Every artifact is designed to be read by humans and parsed by AI agents. The AI doesn't just help you write specs — it enforces them. Fitness functions run in CI. Invariant checks run before every change. Kill criteria trigger before you over-invest.

**Principle 4: One source of truth, every platform.**
Workflows are defined once in canonical YAML and auto-generated for Windsurf, Claude Code, Cursor, and any future platform. The result is identical regardless of which AI tool you use.

**Principle 5: Knowledge flows across boundaries.**
Each service owns its domain. Downstream teams see upstream entities and invariants automatically. When a UX team's experiment touches a core entity, the AI flags the conflict before a single line of code is written.

---

## Why

Modern software teams face a paradox:
- **Product discovery** demands speed, iteration, and tolerance for ambiguity.
- **Core domain logic** demands stability, invariants, and executable guardrails.

Most teams treat everything the same — either over-specifying exploratory work or under-specifying structural changes. Both fail.

**EvoSpec classifies every change by zone, then applies the right level of specification and governance.**

## The Two Layers

EvoSpec makes an explicit separation that most frameworks leave implicit:

### Discovery Layer (the edge)

Fast, iterative, experimental. Knowledge is in the **Mystery → Heuristic** stage.
Design Thinking drives exploration. Specs are hypotheses. The goal is learning.

### Core Engine (the center)

Deliberate, versioned, audited. Knowledge is in the **Heuristic → Algorithm** stage.
DDD drives codification. Specs are contracts. The goal is stability and correctness.

### The Knowledge Funnel (Roger Martin)

```
Mystery   → "We don't know what users need"           → Edge zone (Design Thinking)
Heuristic → "Users with guided onboarding retain 2x"  → Hybrid zone (emerging patterns)
Algorithm → "Every Order MUST have at least one LineItem" → Core zone (DDD + fitness functions)
```

## The Model

### Three Zones

| Zone | Layer | Artifacts | Guardrails |
|------|-------|-----------|------------|
| **Edge** | Discovery | Discovery Spec | Metrics + kill criteria |
| **Hybrid** | Boundary | Discovery Spec + Domain Contract (light) | Contract tests |
| **Core** | Engine | Domain Contract (full) | Fitness functions + CI gates |

### Three Artifacts

- **Discovery Spec** — What we're learning, why, and how we'll know (Teresa Torres + Design Thinking)
- **Domain Contract** — What must remain true, always (Evans/Vernon DDD)
- **ADR** — Why we chose X over Y, and what it costs (Nygard)

### The Loop

```
Classify → Specify → Decide → Implement → Guard → Learn → (repeat)
```

## Installation

```bash
pipx install evospec
```

For development:

```bash
git clone https://github.com/evospec/evospec.git
cd evospec
pipx install -e ".[dev]"
```

## Quick Start

```bash
# Initialize EvoSpec in your project
evospec init

# Create a new change spec
evospec new "user-onboarding-redesign"

# Interactively classify the change (edge/hybrid/core)
evospec classify specs/changes/user-onboarding-redesign

# Create an architecture decision record
evospec adr new "use-event-sourcing-for-orders"

# Run fitness function checks
evospec check

# Reverse-engineer domain contracts from code
evospec reverse api --framework fastapi
```

> **See [`examples/`](examples/) for worked projects:**
> - [`evospec-structure/`](examples/evospec-structure/) — complete EvoSpec project structure with core + edge specs, domain glossary, context map, ADRs, and fitness functions
> - [`multi-system-ux-discovery/`](examples/multi-system-ux-discovery/) — two backends (Java/Spring Boot + Python/FastAPI) + UX prototype (React/TS) with cross-spec invariant checking

## Project Structure (after `evospec init`)

```
your-project/
├── .windsurf/workflows/     # Windsurf/Cascade slash commands (auto-generated)
│   ├── evospec.discover.md  #   /evospec.discover — create discovery spec
│   ├── evospec.learn.md     #   /evospec.learn — record experiment results
│   ├── evospec.improve.md   #   /evospec.improve — plan a known improvement
│   ├── evospec.fix.md       #   /evospec.fix — diagnose and fix a bug
│   ├── evospec.contract.md  #   /evospec.contract — create domain contract
│   ├── evospec.tasks.md     #   /evospec.tasks — generate implementation tasks
│   ├── evospec.implement.md #   /evospec.implement — execute tasks
│   ├── evospec.check.md     #   /evospec.check — validate & run fitness functions
│   └── evospec.adr.md       #   /evospec.adr — create architecture decision record
├── .cursor/rules/           # Cursor rules (auto-generated)
│   ├── evospec.mdc          #   Always-on project context
│   └── evospec-*.mdc        #   Per-workflow rules (activated on spec files)
├── CLAUDE.md                # Claude Code project context (auto-generated)
├── specs/
│   ├── _templates/          # Customizable templates
│   ├── changes/             # Change specs (organized by date/name)
│   │   └── 2026-03-01-user-onboarding/
│   │       ├── spec.yaml           # Machine-readable metadata (JSON Schema validated)
│   │       ├── discovery-spec.md   # Hypothesis, experiments, learning (edge/hybrid)
│   │       ├── domain-contract.md  # Entities, invariants, fitness functions (core/hybrid)
│   │       ├── tasks.md            # AI-executable implementation tasks
│   │       ├── implementation-spec.md # As-built blueprint (for reproduction)
│   │       └── checks/             # Executable guardrails
│   └── domain/              # Living domain model
│       ├── entities.yaml    # Domain entity registry (fields, relationships, invariants)
│       ├── contexts.yaml    # Bounded contexts (owner, type, description)
│       ├── features.yaml    # Feature lifecycle registry
│       ├── glossary.md      # Ubiquitous language (DDD)
│       └── context-map.md   # Bounded context relationships
├── docs/
│   └── adr/                 # Architecture Decision Records
│       ├── 0001-adopt-evospec.md
│       └── ...
└── evospec.yaml             # Project configuration (lean — domain data in specs/domain/)
```

## Three Entry Points

Not every change needs discovery. Choose the right entry point:

| Type | When to Use | Workflow | Skips Discovery? |
|------|------------|----------|------------------|
| **Experiment** | Unknown if users want it | `/evospec.discover` → `/evospec.learn` | No — full discovery cycle |
| **Improvement** | Known need, known solution | `/evospec.improve` | Yes — straight to tasks |
| **Bug fix** | Something is broken | `/evospec.fix` | Yes — diagnose, fix, test |

All three entry points run the **invariant impact check** automatically.

## Invariant Safety Net

The Core Engine publishes invariants (e.g., "Every Order must have at least one LineItem"). Before **any** change — experiment, improvement, or bugfix — EvoSpec checks which invariants would be affected:

```bash
# Via MCP (agents call this automatically)
check_invariant_impact(entities=["Order", "LineItem"], description="allow orders without line items")

# Returns:
# conflicts: [INV-001: "Order must have ≥ 1 LineItem"]
# resolution options: exempt | evolve | shadow | redesign
```

**Resolution options** when a change conflicts with an invariant:
- **exempt** — Experiment behind a feature flag, don't touch the invariant
- **evolve** — Propose INV-001-v2 with a migration path + new fitness function
- **shadow** — Validate the need via interviews/analytics BEFORE touching schema
- **redesign** — Change the approach to avoid the conflict

This is how someone on the exploratory side knows what's safe and what breaks the core.

## AI Agent Integration

EvoSpec is designed to work **with** AI coding agents, not replace them.

### Windsurf (Cascade)

Slash commands for the full delivery loop:

```
/evospec.discover "smart recommendations" → AI drafts discovery-spec.md (experiment)
/evospec.learn                         → Record experiment results, update assumptions
/evospec.improve "add pagination"      → Skip discovery, go straight to tasks (improvement)
/evospec.fix "broken tenant filter"    → Root cause + regression test (bugfix)
/evospec.contract                      → AI drafts domain-contract.md
/evospec.tasks                         → AI generates tasks.md
/evospec.implement                     → AI executes tasks phase by phase
/evospec.check                         → AI validates specs + fitness functions
```

### Claude Code

Reads `CLAUDE.md` automatically. Contains all workflow procedures, MCP tools/resources, implementation rules — identical behavior to Windsurf workflows.

### Cursor

Reads `.cursor/rules/evospec.mdc` (always-on project context) + per-workflow rules in `.cursor/rules/evospec-*.mdc` (activated when editing spec files).

### Platform-Agnostic: Canonical Workflow Specs

All AI agent integration files are **auto-generated** from a single source of truth:

```
src/evospec/templates/workflows/    ← canonical YAML specs (edit here)
├── _context.yaml                   ← shared: framework, zones, MCP, CLI, entities
├── discover.yaml                   ← 9 workflow definitions
├── improve.yaml
├── fix.yaml
├── contract.yaml
├── tasks.yaml
├── implement.yaml
├── learn.yaml
├── check.yaml
└── adr.yaml

evospec generate agents             ← generates all platforms at once

.windsurf/workflows/evospec.*.md    ← Windsurf output (9 files)
CLAUDE.md                           ← Claude Code output (1 file)
.cursor/rules/evospec*.mdc          ← Cursor output (10 files)
```

To regenerate after editing canonical specs: `evospec generate agents`
To generate for a single platform: `evospec generate agents --platform cursor`

### MCP Server (Any Agent)

EvoSpec exposes a **Model Context Protocol server** for programmatic access:

```bash
# Start the MCP server
evospec serve
# Or directly
evospec-mcp
```

**Tools** agents can call:

| Tool | Description |
|------|-------------|
| `list_specs()` | List all specs with zone, status, artifacts |
| `read_spec(path)` | Read a spec with all artifacts |
| `check_spec(path?)` | Run validation checks |
| `classify_change(...)` | Classify a change into edge/hybrid/core |
| `check_invariant_impact(entities, contexts, desc)` | **Safety net**: check what invariants a change affects |
| `get_tasks(path)` | Parse tasks.md into structured data |
| `update_task(path, id, done)` | Mark tasks complete |
| `list_features()` | List features with lifecycle status |
| `get_discovery_status(path)` | Assumptions, experiments, health, deadlines |
| `record_experiment(path, ...)` | Log results, update assumption, log learning |
| `update_assumption(path, id, ...)` | Update assumption status or pivot direction |
| `run_fitness_functions(path?)` | Execute fitness function tests |

**Resources**: `evospec://config`, `evospec://glossary`, `evospec://context-map`, `evospec://invariants`, `evospec://entities`

Any MCP-compatible agent (Claude Code, Cursor, custom agents) can connect to the server and use these tools directly.

## Cross-Repo Sharing

In real-world systems, each service lives in its own repository with its own `evospec.yaml`. Downstream repos (e.g., a UX prototype) reference upstream repos to see their entities and invariants:

```yaml
# In smart-cart-ui/evospec.yaml:
upstreams:
  - name: "order-service"
    path: "../order-service"       # relative path to sibling repo
  - name: "inventory-service"
    path: "../inventory-service"
```

This enables:
- `evospec check` includes upstream invariants in cross-spec checks
- `evospec://entities` MCP resource includes upstream entities
- `check_invariant_impact()` checks upstream invariants too
- AI agents see the full domain picture across repos

> See [`examples/multi-system-ux-discovery/`](examples/multi-system-ux-discovery/) for a worked example with 3 separate services.

## Changes vs Features

A **change** is the unit of work — it lives in `specs/changes/YYYY-MM-DD-slug/`. A **feature** is a product capability tracked across its lifecycle in `specs/domain/features.yaml`.

- A change can **create** a feature (experiment discovers something worth building)
- A change can **advance** a feature (improvement or implementation)
- A change can **fix** a feature (bugfix)
- A change can have **nothing to do with features** (e.g., tech debt, infra, refactoring)

Not every change is a feature. Features are optional — changes are always tracked.

## Continuous Discovery Loop

The Discovery Layer is not a one-shot planning document. It's a **learning system** inspired by Teresa Torres' Continuous Discovery Habits:

```
Hypothesize → Experiment → Learn → Decide → (repeat or promote to core)
```

### Assumption Lifecycle

```
untested → testing → validated    → promote-to-core (becomes an invariant)
                   → invalidated  → pivot (new iteration) or kill
```

Each assumption is categorized: **desirability** (do users want it?), **feasibility** (can we build it?), **viability** (should we build it?), **usability** (can they use it?)

### Recording Experiments

```bash
# Interactive CLI
evospec learn

# Or via Windsurf
/evospec.learn
```

Every experiment records: what was tested, the result, confidence level, and a **decision** — `continue`, `pivot`, `kill`, or `promote-to-core`.

Pivots increment the **iteration counter**. Kill deadlines are enforced. When all high-risk assumptions are resolved, you're ready for `/evospec.tasks`.

### The Bridge: Discovery → Core

When an edge assumption is validated with high confidence, it becomes a **promotion candidate**. Run `/evospec.contract` to codify it as an invariant with fitness functions — this is how knowledge flows from Mystery → Algorithm.

## Intellectual Foundations

EvoSpec synthesizes:

- **Domain-Driven Design** (Evans, Vernon) — Bounded contexts, ubiquitous language, invariants
- **Continuous Discovery** (Teresa Torres) — Opportunity trees, assumption testing, learning loops
- **Design Thinking** (IDEO, d.school) — Empathize → Define → Ideate → Prototype → Test
- **The Knowledge Funnel** (Roger Martin) — Mystery → Heuristic → Algorithm
- **Evolutionary Architecture** (Neal Ford et al.) — Fitness functions, incremental change
- **Team Topologies** (Skelton, Pais) — Cognitive load, team ownership, interaction modes
- **Strategy as Choice** (Roger Martin) — Playing to Win cascade, integrated choices
- **ADRs** (Michael Nygard) — Lightweight decision governance
- **Organizational Personality** (Robert Hogan) — Leadership risk, dark-side derailers

Read the full [MANIFESTO.md](MANIFESTO.md) for the deep synthesis.

## How EvoSpec Compares

See [docs/COMPARISON.md](docs/COMPARISON.md) for an honest comparison with:
- **Spec Kit** (GitHub) — Linear spec pipeline, broad agent support
- **OpenSpec** (Fission AI) — Lightweight proposal flow, 20+ tools
- **Agent OS** (Builder Methods) — Codebase standards injection

**TL;DR**: Other frameworks treat all changes the same. EvoSpec classifies by zone and applies proportional governance — lightweight for experiments, strict for core domain.

## Feature Lifecycle & Fitness Functions

### Features Registry

Track features across the Knowledge Funnel:

```bash
evospec feature add "smart recommendations" --zone edge
evospec feature list
evospec feature update feat-001 --status implementing --knowledge-stage heuristic
```

Lifecycle: `discovery → specifying → implementing → validating → shipped | killed`

### Fitness Functions (Executable Guardrails)

Core zone specs define fitness functions in `spec.yaml`. EvoSpec **actually runs them**:

```bash
# Validate specs + run fitness function tests
evospec check --run-fitness

# Run fitness functions independently
evospec fitness
```

Fitness functions are pytest (or jest/go test) files referenced in `spec.yaml`:

```yaml
fitness_functions:
  - id: "FF-001"
    type: "integration-test"
    dimension: "data-integrity"
    path: "tests/fitness/test_order_integrity.py"
```

## Guiding Principles

1. **Specs are proportional to risk.** Edge gets a hypothesis. Core gets invariants + fitness functions.
2. **Invariants are testable propositions.** Not prose.
3. **Decisions are logged.** ADRs explain *why*, which code never can.
4. **Discovery is continuous.** Specs evolve. This is not waterfall.
5. **Teams own contexts.** Specs map to bounded contexts, contexts map to teams.
6. **AI accelerates, humans decide.** AI generates and reverse-engineers. Humans review and own.
7. **Guardrails are executable.** If it's not automated, it's a suggestion.

## Getting Started

See [docs/getting-started.md](docs/getting-started.md) for a step-by-step guide.

## License

MIT

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
