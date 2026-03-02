# Getting Started with EvoSpec

> *Discovery is messy. Let it be messy. Capture when it crystallizes.*

This guide walks you through EvoSpec from first install to running spec-driven workflows with AI agents. It covers both **experimental** (prototype first, document later) and **deliberate** (plan first, build after) modes.

## Prerequisites

- Python 3.10+
- [pipx](https://pypa.github.io/pipx/) (recommended) or pip
- An AI coding assistant: **Windsurf/Cascade**, **Claude Code**, or **Cursor**

## Installation

```bash
# Recommended: install globally with pipx
pipx install evospec

# Or with pip
pip install evospec
```

Verify:

```bash
evospec --version
```

## Initialize Your Project

```bash
cd your-project
evospec init
```

This creates:

```
your-project/
├── .windsurf/workflows/       # Windsurf/Cascade slash commands (auto-generated)
├── .cursor/rules/             # Cursor rules (auto-generated)
├── CLAUDE.md                  # Claude Code context (auto-generated)
├── evospec.yaml               # Project configuration (lean)
├── specs/
│   ├── changes/               # Change specifications
│   └── domain/                # Living domain model
│       ├── entities.yaml      # Domain entity registry
│       ├── contexts.yaml      # Bounded contexts
│       ├── features.yaml      # Feature lifecycle
│       ├── glossary.md        # Ubiquitous language (DDD)
│       └── context-map.md     # Bounded context relationships
└── docs/
    └── adr/                   # Architecture Decision Records
```

All AI agent files are auto-generated from canonical workflow specs. Regenerate anytime with `evospec generate agents`.

---

## Two Modes: Choose Your Path

EvoSpec never forces documentation before you're ready. Pick the mode that matches your confidence level.

### 🧪 Experimental Mode (explore first, document later)

For UX, product experiments, and prototyping. You don't know the solution yet.

```
/evospec.discover "smart cart with real-time availability"
```

**What happens:**
1. AI asks classification questions → determines the zone (edge/hybrid/core)
2. **Interactive domain modeling** — AI helps you understand entities, relationships, and boundaries:
   ```
   AI: "What are the main entities? I see your upstream Order Service has Order and LineItem..."
   You: "Cart, with items and a total. It references Products from inventory."
   AI: "Like this?
        Entity: CartView
        Fields: items[], recommendations[], total
        Relationships: CartView → Product (references), CartView → Order (creates)
        Does this look right?"
   ```
3. **Design exploration** — AI asks your confidence (1-10), sketches approaches, helps you choose
4. Generates `spec.yaml` + `discovery-spec.md` with everything filled in
5. Checks invariant conflicts with existing core specs

**Then you build.** Prototype with AI help, iterate, test with users.

**When you're ready to formalize:**
```
/evospec.capture
```

The AI scans your code and generates:
- `implementation-spec.md` — complete as-built blueprint (architecture, APIs, state, config, reproduction instructions)
- Updates `specs/domain/entities.yaml` if new entities were discovered
- Gap analysis: which invariants are enforced, which aren't

**Record what you learned:**
```
/evospec.learn
```

### 🏗️ Deliberate Mode (plan first, build after)

For developers, known improvements, and core domain changes. You know the solution.

```
/evospec.improve "add pagination to product list"
```

Or for experiments where you're already confident:
```
/evospec.discover "batch availability API"   # (AI detects high confidence, fast-tracks)
```

**The pipeline:**
```
/evospec.discover or /evospec.improve
  → /evospec.contract        (domain contract for core/hybrid)
  → /evospec.tasks            (task list + implementation-spec.md skeleton)
  → /evospec.implement        (execute tasks, update implementation-spec)
  → /evospec.check            (validate everything)
```

The `implementation-spec.md` grows with the code — skeleton at task generation, filled in during implementation, finalized post-completion.

### 🐛 Bug Fix Mode

```
/evospec.fix "orders missing line items after checkout"
```

Skips discovery entirely. Root cause analysis, minimal fix, regression test.

---

## Understanding Zones

Every change is classified by risk:

| Zone | When | Artifacts | Guardrails |
|------|------|-----------|------------|
| **Edge** | Experimenting, hypothesis-driven | discovery-spec.md | Kill criteria + metrics |
| **Hybrid** | Crosses into core territory | discovery-spec.md + light contract | Contract tests |
| **Core** | Persistence, auth, billing, multi-tenancy | domain-contract.md (full) | Fitness functions + CI gates |

**Auto-classification** based on risk signals:
- 0 core signals + hypothesis → **edge**
- 1 core signal or crosses context boundary → **hybrid**
- 2+ core signals or irreversible → **core**

---

## Domain Model (Split Files)

Domain data lives in dedicated files under `specs/domain/`, not in `evospec.yaml`:

| File | Contains | Populated by |
|------|----------|-------------|
| `entities.yaml` | Entity registry (fields, relationships, invariants) | `evospec reverse db` or manually |
| `contexts.yaml` | Bounded contexts (owner, type, description) | Manually |
| `features.yaml` | Feature lifecycle (status, knowledge stage) | `evospec feature add/update` |
| `glossary.md` | Ubiquitous language definitions | Manually |
| `context-map.md` | Context relationships | Manually |

Example entity in `specs/domain/entities.yaml`:

```yaml
- name: "Order"
  context: "orders"
  table: "orders"
  aggregate_root: true
  description: "A customer purchase with line items and payment."
  fields:
    - name: "id"
      type: "UUID"
    - name: "status"
      type: "String"
      constraints: "draft | submitted | shipped | delivered | cancelled"
  relationships:
    - target: "LineItem"
      type: "one-to-many"
  invariants:
    - "ORD-INV-001"
```

---

## Invariant Safety Net

Before any change, EvoSpec checks which core invariants might be affected:

```
/evospec.discover "allow empty orders"

⚠ INVARIANT CONFLICT DETECTED

INV-001: "Every Order must have at least one LineItem"
  Source: specs/changes/2025-06-01-order-rules/spec.yaml
  Enforced by: tests/fitness/test_order_integrity.py

Resolution options:
  1. exempt    — Experiment behind a feature flag
  2. evolve    — Propose INV-001-v2 with migration path
  3. shadow    — Validate need before touching schema
  4. redesign  — Change approach to avoid the conflict
```

This works across repos — if your UX project references backend services as upstreams, the AI sees their invariants too.

---

## Cross-Repo Sharing

In multi-service setups, each service has its own `evospec.yaml`. Downstream repos reference upstreams:

```yaml
# In smart-cart-ui/evospec.yaml
upstreams:
  - name: "order-service"
    path: "../order-service"
  - name: "inventory-service"
    path: "../inventory-service"
```

This enables:
- `evospec check` includes upstream invariants in cross-spec checks
- `evospec://entities` MCP resource includes upstream entities
- `/evospec.discover` shows upstream entities during interactive domain modeling
- AI agents see the full domain picture across repos

> See [`examples/multi-system-ux-discovery/`](../examples/multi-system-ux-discovery/) for a worked example with 3 services.

---

## The Discovery Loop

For experiments (edge zone), EvoSpec supports continuous discovery:

```
Hypothesize → Experiment → Learn → Decide → (repeat or promote to core)
```

### 1. Define assumptions

The AI generates riskiest assumptions when creating a discovery spec:

```yaml
# In spec.yaml
discovery:
  assumptions:
    - id: "A-001"
      statement: "Users abandon carts due to out-of-stock surprises"
      category: "desirability"
      risk: "high"
      status: "untested"
```

### 2. Run experiments and learn

```
/evospec.learn
```

Records: what was tested, the result, confidence level, and a decision — **continue**, **pivot**, **kill**, or **promote-to-core**.

### 3. Promote to core

When an assumption is validated with high confidence, it becomes an invariant:

```
/evospec.contract
```

This is how knowledge flows through the funnel: Mystery → Heuristic → Algorithm.

---

## Reverse Engineering

Bring EvoSpec into existing codebases:

```bash
# Scan API endpoints (FastAPI, Spring, Express, Go, NestJS, Next.js, ...)
evospec reverse api --framework fastapi

# Scan DB models → generate entity registry YAML
evospec reverse db

# Scan module/function structure
evospec reverse cli

# Detect cross-system API dependencies
evospec reverse deps --source src/
```

`reverse db` outputs copy-pasteable YAML for `specs/domain/entities.yaml`.

---

## Working with Tasks

Generate phased, dependency-ordered tasks:

```
/evospec.tasks
```

```markdown
## Phase 1: Setup
- [ ] T001 [P] [Setup] Create feature flag in `config/features.yaml`
- [ ] T002 [P] [Setup] Add service skeleton in `src/services/recommendations.py`

## Phase 2: Core
- [ ] T003 [Core] Implement scoring algorithm in `src/services/recommendations.py`
- [ ] T004 [Core] Add endpoint `GET /v1/recommendations` in `src/api/recommendations.py`
```

Execute with the AI:

```
/evospec.implement
```

The AI executes tasks phase by phase, marks them complete, and (for core/hybrid) updates `implementation-spec.md` as it goes.

---

## Implementation Spec (As-Built Blueprint)

The `implementation-spec.md` captures what was actually built — for reproduction, maintenance, and handoff:

| Section | What it captures |
|---------|-----------------|
| Overview | Tech stack, architecture style, key decisions |
| Component Architecture | Module tree, responsibilities, file paths |
| API Integration | Endpoints consumed, auth, error handling |
| State Management | State shape, transitions, side effects |
| Configuration | Env vars, feature flags |
| Invariant Compliance | Maps each invariant → code file:line |
| Reproduction Instructions | Setup, build, run, verify |
| Known Limitations | Tech debt, gaps, planned fixes |

**Two ways to create it:**
- **Deliberate**: skeleton created by `/evospec.tasks`, filled during `/evospec.implement`
- **Experimental**: created retroactively by `/evospec.capture` after prototyping

---

## Fitness Functions

Core zone specs define executable guardrails:

```yaml
# In spec.yaml
fitness_functions:
  - id: "FF-001"
    type: "integration-test"
    dimension: "data-integrity"
    path: "tests/fitness/test_order_integrity.py"
```

```bash
# Validate specs + run fitness tests
evospec check --run-fitness

# Run fitness functions only
evospec fitness
```

---

## Feature Lifecycle

Track features across the knowledge funnel:

```bash
evospec feature add "smart recommendations" --zone edge
evospec feature list
evospec feature update feat-001 --status implementing --knowledge-stage heuristic
```

Lifecycle: `discovery → specifying → implementing → validating → shipped | killed`

Features live in `specs/domain/features.yaml`. Not every change is a feature — a bugfix or tech debt refactor doesn't need one.

---

## AI Agent Integration

EvoSpec works with any AI coding assistant. All agent files are auto-generated from the same canonical workflow specs.

| Platform | Files | How it works |
|----------|-------|-------------|
| **Windsurf/Cascade** | `.windsurf/workflows/evospec.*.md` | Slash commands: `/evospec.discover`, `/evospec.capture`, etc. |
| **Claude Code** | `CLAUDE.md` | Auto-read on session start. All workflows documented inline. |
| **Cursor** | `.cursor/rules/evospec*.mdc` | Context rule + per-workflow rules activated on spec files. |

Regenerate for all platforms:

```bash
evospec generate agents
evospec generate agents --platform cursor  # single platform
```

### MCP Server (programmatic access)

```bash
evospec serve
```

Any MCP-compatible agent can call tools like `list_specs()`, `check_invariant_impact()`, `record_experiment()`, `run_fitness_functions()`, and access resources like `evospec://entities`, `evospec://config`, `evospec://invariants`.

---

## All 10 Workflows

| Workflow | Command | Purpose |
|----------|---------|---------|
| **Discover** | `/evospec.discover` | Interactive exploration, entity modeling, design thinking |
| **Improve** | `/evospec.improve` | Known improvement — skip discovery, straight to tasks |
| **Fix** | `/evospec.fix` | Bug fix — root cause, minimal fix, regression test |
| **Contract** | `/evospec.contract` | Domain contract (invariants, state machines, fitness functions) |
| **Tasks** | `/evospec.tasks` | Generate task list from spec artifacts |
| **Implement** | `/evospec.implement` | Execute tasks phase by phase |
| **Capture** | `/evospec.capture` | Retroactive formalization of experimental/undocumented work |
| **Learn** | `/evospec.learn` | Record experiment results, update assumptions |
| **Check** | `/evospec.check` | Validate specs, run fitness functions, cross-spec checks |
| **ADR** | `/evospec.adr` | Architecture Decision Record |

---

## Configuration

`evospec.yaml` is lean — it contains project metadata, not domain data:

```yaml
project:
  name: "my-service"
  description: "..."

paths:
  specs: "specs/changes"
  domain: "specs/domain"
  adrs: "docs/adr"

classification:
  core_triggers:
    - touches_persistence
    - touches_auth

teams:
  - name: "product-core"
    type: "stream-aligned"
    bounded_contexts: ["orders", "catalog"]

# Cross-repo dependencies
upstreams:
  - name: "order-service"
    path: "../order-service"

fitness_functions:
  run_command: "pytest tests/fitness/ -v"
  test_runner: "pytest"
```

Domain data lives in `specs/domain/*.yaml` files, not in `evospec.yaml`.

---

## Next Steps

- Read the [Manifesto](../README.md#manifesto) for the design principles
- Explore [`examples/evospec-structure/`](../examples/evospec-structure/) — complete single-repo example
- Explore [`examples/multi-system-ux-discovery/`](../examples/multi-system-ux-discovery/) — multi-repo with cross-spec invariant checking
- Try `/evospec.discover` with your next feature idea
- Run `evospec reverse db` to populate your entity registry from existing code
