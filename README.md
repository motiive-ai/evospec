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
# AI bootstrap: give any AI agent instant EvoSpec context (works pre-init)
evospec prompt --detect

# Initialize EvoSpec in your project (--detect pre-fills reverse config)
evospec init
evospec init --detect

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
evospec reverse db --framework sqlalchemy
evospec reverse api --framework fastapi --deep  # schema extraction + invariant detection

# Detect spec drift (what changed in code but not in specs?)
evospec sync --since HEAD~10
evospec sync --generate  # auto-create draft specs for detected drift
evospec sync --ci         # JSON output for CI pipelines

# Verify spec accuracy against implementation
evospec verify
evospec verify --strict   # exit non-zero if score below threshold (CI gate)
evospec verify --format markdown

# Generate retroactive specs from git history
evospec capture --from-history
evospec capture --from-history --since v1.0 --min-cluster-size 3
```

> **See [`examples/`](examples/) for worked projects:**
> - [`evospec-structure/`](examples/evospec-structure/) — complete EvoSpec project structure with core + edge specs, domain glossary, context map, ADRs, and fitness functions
> - [`multi-system-ux-discovery/`](examples/multi-system-ux-discovery/) — two backends (Java/Spring Boot + Python/FastAPI) + UX prototype (React/TS) with cross-spec invariant checking
> - [`orders-system/`](examples/orders-system/) — domain exploration with MCP consumer discovery, API contracts, file schemas, and implementation skills

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
| `get_entities(context?, upstream?)` | Get entity registry, optionally filtered |
| `get_invariants(context?)` | Get all invariants, optionally by context |
| `get_api_contract(endpoint?, tag?)` | Get API contracts from api-contracts.yaml |
| `get_file_schema(name?, fmt?)` | Get file schemas from file-schemas.yaml |
| `get_consumer_context(intent)` | Combined context for external consumers |
| `get_upstream_apis(upstream?)` | API endpoints from upstream services |
| `parse_contract_file(file_path)` | Parse OpenAPI/JSON Schema files into entities |
| `check_drift(since?)` | Detect spec drift from git changes |
| `verify_spec(strict?)` | Verify spec accuracy against code (5 levels) |

**Resources**:

| Resource | Description |
|----------|-------------|
| `evospec://bootstrap` | AI bootstrap prompt (works pre-init) |
| `evospec://project` | Lean project metadata |
| `evospec://glossary` | Domain glossary (ubiquitous language) |
| `evospec://context-map` | Bounded context relationships |
| `evospec://skills` | Project-specific implementation skills |
| `evospec://api-catalog` | Browsable API endpoint catalog |
| `evospec://drift-report` | Current spec drift analysis |
| `evospec://verification` | Spec verification report |

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

## Spec Drift Detection

Code evolves. Specs don't always keep up. `evospec sync` detects the gap:

```bash
# What changed in code that isn't reflected in specs?
evospec sync

# Analyze only recent changes
evospec sync --since HEAD~20

# Auto-generate draft specs for detected drift
evospec sync --generate

# CI-friendly JSON output
evospec sync --ci
```

**What it detects:**
- **Entity field changes** — new/modified/removed fields in model classes (Python, Java, Go, TS)
- **API endpoint changes** — new/removed routes in FastAPI, Express, Spring Boot, etc.
- **Invariant impact** — changes touching files near invariant enforcement code

**Drift score**: 0–100% (0% = specs perfectly match code, 100% = massive untracked drift). Use `--ci` to fail CI pipelines when drift exceeds a threshold.

## Spec Verification

`evospec verify` goes deeper — it checks whether your specs are *accurate*, not just *present*:

```bash
# Full 5-level verification
evospec verify

# CI gate: exit non-zero if verification fails
evospec verify --strict

# Markdown report for documentation
evospec verify --format markdown
```

**Five verification levels:**

| Level | What it checks | Example |
|-------|---------------|---------|
| **1. Entities** | Do spec entities match code classes/fields? | `Order.status` in spec → `status = Column(String)` in code |
| **2. API endpoints** | Do documented endpoints exist in code? | `POST /api/orders` in spec → `@router.post("/api/orders")` |
| **3. Invariants** | Are invariants enforced in code + tested? | `INV-001` → validation function + test case |
| **4. Bounded contexts** | Do spec contexts match code structure? | `orders` context → `src/orders/` directory |
| **5. Consistency** | Do specs reference each other correctly? | Entity names match across specs |

**Overall score**: Weighted average across all 5 levels (0–100%).

## Retroactive Spec Generation

The biggest adoption barrier: *"We have 500K lines of code and no specs."*

`evospec capture --from-history` solves the cold start problem:

```bash
# Analyze full git history → detect feature clusters → generate specs
evospec capture --from-history

# Start from a specific point
evospec capture --from-history --since v2.0

# Tune clustering
evospec capture --from-history --min-cluster-size 3 --max-clusters 10
```

**How it works:**

1. **Parse git log** — extracts commits and files changed together
2. **Build co-change graph** — files that change in the same commit get weighted edges
3. **Community detection** — label propagation algorithm finds natural clusters (no ML, no external deps)
4. **Auto-label** — clusters named from conventional commit scopes (`feat(auth):`), directory structure, or commit message topics
5. **Generate specs** — each cluster becomes a `specs/changes/retroactive-*/` with spec.yaml + discovery-spec.md
6. **Extract entities** — scans code for class definitions, appends to `entities.yaml`
7. **Update features** — adds feature entries to `features.yaml`

Generated specs are drafts — review, rename, and promote to hybrid/core as needed.

## Deep Reverse Engineering

Standard `evospec reverse` does surface-level code scanning. Add `--deep` for richer analysis:

```bash
# Standard: extract API routes
evospec reverse api --framework fastapi

# Deep: extract API routes + request/response schemas + suggested invariants
evospec reverse api --framework fastapi --deep

# Deep DB: extract models + column types + relationships + suggested invariants
evospec reverse db --framework sqlalchemy --deep

# Deep dependencies: extract imports + call graphs + coupling metrics
evospec reverse deps --deep
```

**Deep mode adds:**
- **Schema extraction** — request/response models, field types, validation rules
- **Invariant detection** — suggests invariants from validation code, constraints, guards
- **Relationship mapping** — foreign keys, association tables, entity relationships
- **Confidence levels** — each suggestion tagged high/medium/low confidence

**Supported frameworks:**

| Language | API | DB | CLI |
|----------|-----|-----|-----|
| **Python** | FastAPI, Django, Flask | SQLAlchemy, Django ORM | Click |
| **Go** | gin, echo, fiber, chi, gorilla, net-http | GORM | Cobra |
| **Java/Kotlin** | Spring Boot | JPA/Hibernate | Picocli, Spring Shell |
| **JS/TS** | Express, Next.js, NestJS, Hono, Fastify | Prisma, TypeORM, Sequelize | — |

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

## CLI Reference

| Command | Description |
|---------|-------------|
| `evospec init` | Initialize EvoSpec in the current project. Options: `--name`, `--detect`, `--specs-dir` |
| `evospec new <slug>` | Create a new change spec. Options: `--zone edge\|hybrid\|core` |
| `evospec classify <path>` | Interactively classify a change by zone |
| `evospec check` | Run spec validations + invariant impact checks. Options: `--run-fitness` |
| `evospec fitness` | Run all fitness functions defined in spec.yaml files |
| `evospec sync` | Detect spec drift from git changes. Options: `--since`, `--generate`, `--ci` |
| `evospec verify` | Verify spec accuracy against code (5 levels). Options: `--strict`, `--format` |
| `evospec capture` | Generate retroactive specs. Options: `--from-history`, `--since`, `--min-cluster-size`, `--max-clusters` |
| `evospec reverse api` | Reverse-engineer API routes. Options: `--framework`, `--deep` |
| `evospec reverse db` | Reverse-engineer DB models. Options: `--framework`, `--deep` |
| `evospec reverse deps` | Reverse-engineer dependencies. Options: `--deep` |
| `evospec reverse cli` | Reverse-engineer CLI structure |
| `evospec adr new <title>` | Create an ADR. `evospec adr list` to list all |
| `evospec feature add <title>` | Add a feature. `evospec feature list`, `evospec feature update` |
| `evospec learn` | Record experiment results and update discovery assumptions |
| `evospec prompt` | Emit AI bootstrap prompt. Options: `--detect`, `--format json` |
| `evospec status` | Show status of all change specs |
| `evospec render` | Render all specs into consolidated markdown |
| `evospec generate agents` | Regenerate AI agent files. Options: `--platform windsurf\|claude\|cursor` |
| `evospec serve` | Start the MCP server for AI agent integration |

## Getting Started

See [docs/getting-started.md](docs/getting-started.md) for a step-by-step guide.

## License

MIT

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
