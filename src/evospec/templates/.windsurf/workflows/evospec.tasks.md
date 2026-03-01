---
description: Generate an actionable, dependency-ordered tasks.md for AI-driven implementation based on the spec artifacts.
handoffs:
  - label: Implement Tasks
    agent: evospec.implement
    prompt: Execute the implementation tasks
    send: true
  - label: Run Checks
    agent: evospec.check
    prompt: Validate spec and run fitness function checks
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Context

This workflow generates a **machine-parseable, dependency-ordered task list** that AI agents can execute. Tasks are the bridge between specification and implementation.

## Outline

1. **Find the spec directory**:
   - Check `evospec.yaml` exists. If not: instruct user to run `evospec init`.
   - If `$ARGUMENTS` contains a spec path, use it.
   - Otherwise, list available specs and let user choose.
   - Read `spec.yaml`, `discovery-spec.md`, `domain-contract.md` (whichever exist).

2. **Load implementation context**:
   - From `spec.yaml`: zone, classification, invariants, fitness_functions, traceability
   - From `discovery-spec.md`: selected solution approach, prototype plan
   - From `domain-contract.md`: entities, state machines, authorization rules, events
   - From `evospec.yaml`: project tech stack, team topology, bounded contexts

3. **Determine task generation strategy by zone**:

   ### Edge Zone (Discovery Layer)
   - Focus on **prototyping speed** and **learning instrumentation**
   - Phase structure:
     1. Setup: feature flag, experiment infrastructure
     2. Prototype: minimal UI/API to test hypothesis
     3. Instrumentation: metrics, analytics, A/B test setup
     4. Validation: smoke tests, user test scripts
   - Mark most tasks as [P] (parallelizable) — edge work is loosely coupled

   ### Hybrid Zone
   - Focus on **boundary protection** while allowing iteration
   - Phase structure:
     1. Setup: dependencies, configuration
     2. Foundation: schema migrations, base models (from domain contract)
     3. Contract Tests: boundary tests between discovery and core
     4. Core Implementation: entities, services matching domain contract
     5. Edge Implementation: UX, experimental features
     6. Guardrails: fitness functions for invariants
   - Sequential for core tasks, parallel for edge tasks

   ### Core Zone (Core Engine)
   - Focus on **correctness, invariants, and fitness functions**
   - Phase structure:
     1. Setup: dependencies, configuration
     2. Foundation: schema migrations, base models
     3. Fitness Functions: write tests FIRST (TDD for core)
     4. Core Implementation: entities, aggregates, services
     5. Authorization: role checks, tenant isolation
     6. Integration: wire endpoints, middleware
     7. Guardrails: run all fitness functions, contract tests
     8. Polish: logging, error handling, documentation
   - Strictly sequential — core changes must be verified at each step

4. **Generate tasks.md**:
   Use the tasks template. For each task:

   **Task Format** (REQUIRED):
   ```
   - [ ] T001 [P] [Phase] Description with exact file path
   ```

   **Format Rules**:
   - `- [ ]`: Checkbox (mark `[X]` when complete)
   - `T001`: Sequential task ID
   - `[P]`: Only if parallelizable (different files, no dependency on incomplete tasks)
   - `[Phase]`: Phase label (Setup, Foundation, Core, Integration, Guardrails, Polish)
   - Description: Clear action verb + exact file path

   **Task Quality Rules**:
   - Every task must reference an exact file path
   - Every task must be completable by an AI agent without additional context
   - Every task should be independently verifiable
   - Tasks affecting the same file must be sequential (not [P])

5. **Generate invariant-to-task mapping** (for core/hybrid):
   - Every invariant in spec.yaml must have at least one corresponding task
   - Every fitness function must have a task to implement it
   - Include this mapping in the tasks.md as a traceability section

6. **Generate dependency graph**:
   ```
   Phase 1 → Phase 2 → Phase 3 → ...
   Within phases: T001 → T003 (sequential), T002 || T004 (parallel)
   ```

7. **Report**:
   - Total task count
   - Tasks per phase
   - Parallel opportunities
   - Invariant coverage (% of invariants with tasks)
   - Suggested MVP scope
   - Estimated implementation phases

## Task Generation from Domain Contract

When a domain-contract.md exists, generate tasks for:

| Contract Section | Generated Tasks |
|-----------------|----------------|
| Entities | Create model files, define fields, add constraints |
| Invariants | Write fitness function tests (TDD-first for core) |
| State Machine | Implement state transitions, add guards |
| Domain Events | Create event classes, implement handlers |
| Authorization | Add role checks, tenant isolation queries |
| Fitness Functions | Implement each listed fitness function |
| Migration | Create schema migration files |

## Task Generation from Discovery Spec

When a discovery-spec.md exists, generate tasks for:

| Spec Section | Generated Tasks |
|-------------|----------------|
| Selected Solution | Implement the chosen approach |
| Prototype Plan | Create prototype artifacts |
| Assumptions | Instrument metrics to test assumptions |
| Kill Criteria | Add monitoring/alerting for kill criteria |

## Rules

- **NEVER generate tasks without reading the spec artifacts first**
- **Core zone: fitness function tasks BEFORE implementation tasks** (TDD)
- **Edge zone: prototype tasks BEFORE instrumentation tasks**
- **Every invariant must map to at least one task**
- **Every task must have an exact file path**
- Tasks must be specific enough for an AI agent to execute without asking questions
- Maximum 50 tasks per spec (break into sub-specs if larger)
