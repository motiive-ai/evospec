# Getting Started with EvoSpec

This guide walks you through setting up EvoSpec in your project and running your first spec-driven workflow.

## Prerequisites

- Python 3.10+
- [pipx](https://pypa.github.io/pipx/) (recommended) or pip

## Installation

```bash
# Recommended: install globally with pipx
pipx install evospec

# Or with pip
pip install evospec
```

Verify the installation:

```bash
evospec --version
```

## Initialize Your Project

Navigate to your project root and run:

```bash
evospec init
```

This creates:

```
your-project/
├── specs/
│   ├── changes/              # Where change specs live
│   └── domain/
│       ├── glossary.md       # Ubiquitous language (DDD)
│       └── context-map.md    # Bounded context relationships
├── docs/
│   └── adr/                  # Architecture Decision Records
├── evospec.yaml              # Project configuration
├── CLAUDE.md                 # AI agent context (for Claude Code)
└── .windsurf/
    └── workflows/            # Slash commands (for Windsurf/Cascade)
```

## Your First Change Spec

### Option A: Using an AI agent (recommended)

If you're using **Windsurf/Cascade**, type a slash command:

```
/evospec.discover "smart product recommendations"
```

The AI will:
1. Ask classification questions to determine the zone (edge/hybrid/core)
2. Check for invariant conflicts with existing core specs
3. Generate a complete `discovery-spec.md` with all sections filled in
4. Generate `spec.yaml` with structured metadata

If you're using **Claude Code**, it reads `CLAUDE.md` automatically and understands the EvoSpec workflow.

### Option B: Using the CLI

```bash
# Create a new change spec
evospec new "smart-recommendations"

# Interactively classify the change
evospec classify specs/changes/smart-recommendations
```

This creates:

```
specs/changes/2026-03-01-smart-recommendations/
├── spec.yaml              # Classification + metadata
├── discovery-spec.md      # Hypothesis, experiments, learning (edge/hybrid)
└── tasks.md               # Implementation tasks (generated later)
```

## Understanding Zones

EvoSpec classifies every change into one of three zones:

| Zone | When | What you need |
|------|------|--------------|
| **Edge** | Experimenting, hypothesis-driven | discovery-spec.md + kill criteria |
| **Hybrid** | Crosses into core domain territory | discovery-spec.md + light domain contract |
| **Core** | Touches persistence, auth, billing, multi-tenancy | domain-contract.md + invariants + fitness functions |

The classification is based on **risk signals**:
- 0 core signals + hypothesis → **edge**
- 1 core signal → **hybrid**
- 2+ core signals or irreversible → **core**

## Three Entry Points

Not every change needs full discovery. Choose the right entry point:

### Experiment (unknown outcome)

```bash
# "We don't know if users want this"
/evospec.discover "smart recommendations"

# Later, record experiment results
/evospec.learn
```

### Improvement (known need)

```bash
# "We know we need pagination on the product list"
/evospec.improve "add pagination to product list"
```

Skips discovery. Generates a brief scope document and goes straight to tasks.

### Bug fix (something is broken)

```bash
# "Orders are missing line items after checkout"
/evospec.fix "orders missing line items after checkout"
```

Skips discovery. Focuses on root cause analysis, fix, and regression test.

## The Discovery Loop

For experiments (edge zone), EvoSpec supports continuous discovery:

```
Hypothesize → Experiment → Learn → Decide → (repeat or promote to core)
```

### 1. Define assumptions

When you create a discovery spec, the AI generates **riskiest assumptions**:

```yaml
# In spec.yaml
discovery:
  assumptions:
    - id: "A-001"
      statement: "Users prefer personalized recommendations over generic ones"
      category: "desirability"
      risk: "high"
      status: "untested"
```

### 2. Run experiments

After testing an assumption, record the results:

```bash
evospec learn
```

Or with Windsurf:

```
/evospec.learn
```

The tool asks: what was tested, what happened, how confident are you, and what's the decision — **continue**, **pivot**, **kill**, or **promote-to-core**.

### 3. Promote to core

When an assumption is validated with high confidence, it becomes an invariant:

```
/evospec.contract
```

This is how knowledge flows through the funnel: Mystery → Heuristic → Algorithm.

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

This works for all three entry points (experiment, improvement, bug fix).

## Working with Tasks

Once your spec is ready, generate tasks:

```
/evospec.tasks
```

Tasks are phased, dependency-ordered, and machine-parseable:

```markdown
## Phase 1: Setup
- [ ] T001 [P] [Setup] Create feature flag for smart-recs in `config/features.yaml`
- [ ] T002 [P] [Setup] Add recommendation service skeleton in `src/services/recommendations.py`

## Phase 2: Core
- [ ] T003 [Core] Implement scoring algorithm in `src/services/recommendations.py`
- [ ] T004 [Core] Add API endpoint `GET /v1/recommendations` in `src/api/recommendations.py`
```

Execute tasks with the AI:

```
/evospec.implement
```

## Fitness Functions

Core zone specs define **executable guardrails**:

```yaml
# In spec.yaml
fitness_functions:
  - id: "FF-001"
    type: "integration-test"
    dimension: "data-integrity"
    path: "tests/fitness/test_order_integrity.py"
```

Run them:

```bash
# Validate specs + run fitness tests
evospec check --run-fitness

# Run fitness functions only
evospec fitness
```

## Feature Lifecycle

Track features across the knowledge funnel:

```bash
# Register a feature
evospec feature add "smart recommendations" --zone edge

# List all features
evospec feature list

# Update status
evospec feature update feat-001 --status implementing --knowledge-stage heuristic
```

Lifecycle: `discovery → specifying → implementing → validating → shipped | killed`

## MCP Server (for AI agents)

EvoSpec exposes a Model Context Protocol server that any AI agent can use:

```bash
# Start the MCP server
evospec serve
```

Agents can call tools like `list_specs()`, `check_invariant_impact()`, `record_experiment()`, and `run_fitness_functions()` programmatically.

See the [README](../README.md) for the full tools/resources/prompts list.

## Configuration

Edit `evospec.yaml` to configure:

- **Classification signals** — what triggers core classification
- **Team topologies** — team types and bounded context ownership
- **Bounded contexts** — your domain model registry
- **Features** — feature lifecycle tracking
- **Fitness functions** — test runner configuration

## Next Steps

- Read the [MANIFESTO.md](../MANIFESTO.md) for the intellectual foundations
- Read [COMPARISON.md](COMPARISON.md) to understand how EvoSpec differs from other frameworks
- Explore the workflow files in `.windsurf/workflows/` to see what each slash command does
- Set up your bounded contexts in `specs/domain/context-map.md`
- Define your first invariants in a core spec
