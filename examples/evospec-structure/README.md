# EvoSpec Worked Example — E-Commerce Platform

This directory is a **complete EvoSpec project** for a fictional e-commerce platform called **Acme Commerce**. It demonstrates every artifact that `evospec init` and `evospec new` create, fully filled in.

Use this as a reference when setting up EvoSpec in your own project.

## Project Structure

```
examples/
├── evospec.yaml                          # Project config (teams, contexts, features, strategy)
├── README.md                             # This file
│
├── specs/
│   ├── domain/
│   │   ├── glossary.md                   # Ubiquitous language definitions
│   │   └── context-map.md               # How bounded contexts relate
│   │
│   ├── changes/
│   │   ├── 2025-06-01-order-management/  # CORE zone example
│   │   │   ├── spec.yaml                # Full spec with invariants, fitness functions
│   │   │   ├── domain-contract.md       # Aggregates, state machine, events, auth
│   │   │   ├── tasks.md                 # Phased implementation plan
│   │   │   └── checks/                  # Fitness function implementations
│   │   │       ├── test_order_integrity.py
│   │   │       ├── test_tenant_isolation.py
│   │   │       └── test_order_state_machine.py
│   │   │
│   │   └── 2026-03-01-smart-recommendations/  # EDGE zone example
│   │       ├── spec.yaml                # Spec with discovery metadata
│   │       ├── discovery-spec.md        # Full discovery spec (Design Thinking + Continuous Discovery)
│   │       ├── tasks.md                 # Experiment implementation plan
│   │       └── checks/                  # Empty — edge zone has metrics, not fitness functions
│   │
│   ├── _templates/                      # Copied from evospec templates on init
│   └── checks/                          # Global fitness function config
│
└── docs/
    └── adr/
        ├── 0001-adopt-evospec.md        # Meta: why we use EvoSpec
        ├── 0002-use-event-sourcing.md   # Order state transitions
        └── 0003-tenant-isolation-strategy.md  # Multi-tenancy approach
```

## What Each Zone Looks Like

### Core Zone (Order Management)

Core specs have the **most artifacts** because they guard the most important domain logic:

| Artifact | Purpose |
|----------|---------|
| `spec.yaml` | Full specification with invariants, fitness functions, traceability |
| `domain-contract.md` | Aggregates, state machine, events, authorization, anti-requirements |
| `tasks.md` | Phased implementation plan with invariant coverage tracking |
| `checks/` | Executable fitness functions that run in CI |
| ADRs | Architectural decisions (event sourcing, tenant isolation) |

### Edge Zone (Smart Recommendations)

Edge specs are **lightweight** — focused on learning, not contracts:

| Artifact | Purpose |
|----------|---------|
| `spec.yaml` | Spec with rich discovery metadata (assumptions, experiments, learnings) |
| `discovery-spec.md` | Full discovery spec: empathy, ideation, kill criteria, learning log |
| `tasks.md` | Experiment plan with kill criteria checkpoints |
| `checks/` | Empty — edge zone uses metrics and A/B test results, not fitness functions |

### Hybrid Zone (not shown)

A hybrid spec would have **both** a discovery spec and a lightweight domain contract, representing a feature transitioning from edge to core.

## How to Explore

1. **Start with `evospec.yaml`** — see how teams, bounded contexts, features, and strategy are configured
2. **Read the glossary** — `specs/domain/glossary.md` defines the ubiquitous language
3. **Compare the two specs** — notice how core has invariants and fitness functions, while edge has assumptions and experiments
4. **Check the domain contract** — `order-management/domain-contract.md` is the most detailed artifact
5. **Look at the fitness functions** — `order-management/checks/` shows executable invariant guards
6. **Read the ADRs** — `docs/adr/` shows architectural decision records

## Recreating This

To create a similar structure from scratch:

```bash
# Initialize EvoSpec
evospec init "acme-commerce" --description "E-commerce platform for SMBs"

# Create a core zone spec
evospec new "Order Management CRUD API" --zone core --type improvement

# Create an edge zone spec
evospec new "Smart Product Recommendations" --zone edge --type experiment

# Classify a change interactively
evospec classify

# Check all specs
evospec check

# Run fitness functions
evospec fitness
```
