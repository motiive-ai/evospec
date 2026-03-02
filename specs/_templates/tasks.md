---
spec_id: "{{ id }}"
title: "{{ title }}"
zone: "{{ zone }}"
status: "{{ status }}"
created_at: "{{ created_at }}"
total_tasks: 0
completed_tasks: 0
phases:
  - name: Setup
    tasks: []
  - name: Foundation
    tasks: []
  - name: Core Implementation
    tasks: []
  - name: Integration
    tasks: []
  - name: Guardrails
    tasks: []
  - name: Polish
    tasks: []
invariant_coverage: {}
---

# Implementation Tasks: {{ title }}

> Zone: **{{ zone }}** | Status: **{{ status }}** | Generated: {{ created_at }}

---

## Context

- **Spec**: specs/changes/{{ id }}/spec.yaml
- **Discovery Spec**: specs/changes/{{ id }}/discovery-spec.md
- **Domain Contract**: specs/changes/{{ id }}/domain-contract.md

## Implementation Strategy

- **MVP first**: Ship the smallest increment that validates the hypothesis (edge) or establishes the contract (core)
- **Incremental delivery**: Each phase should be independently testable
- **Parallel where possible**: Tasks marked [P] can run concurrently

## Task Format

```
- [ ] T001 [P] [Phase] Description with exact file path
```

- **Checkbox**: `- [ ]` (mark `[X]` when complete)
- **Task ID**: Sequential (T001, T002, ...)
- **[P]**: Parallelizable (different files, no dependency on incomplete tasks)
- **[Phase]**: Phase label for grouping

---

## Phase 1: Setup

<!-- Project initialization, dependencies, configuration -->

- [ ] T001 Verify project dependencies and environment setup
- [ ] T002 Create/update configuration files as needed

## Phase 2: Foundation

<!-- Blocking prerequisites that all subsequent phases depend on -->
<!-- For core: schema migrations, base models, auth setup -->
<!-- For edge: API stubs, feature flags, experiment infrastructure -->

## Phase 3: Core Implementation

<!-- Main implementation tasks, organized by user story or domain entity -->
<!-- Each task should reference exact file paths -->

## Phase 4: Integration & Wiring

<!-- Connect components, add middleware, wire endpoints -->

## Phase 5: Guardrails

<!-- For core: fitness functions, contract tests, invariant checks -->
<!-- For edge: metrics instrumentation, kill criteria checks -->
<!-- For hybrid: boundary contract tests -->

## Phase 6: Polish

<!-- Documentation, logging, error handling, edge cases -->

---

## Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundation) → Phase 3 (Core) → Phase 4 (Integration) → Phase 5 (Guardrails) → Phase 6 (Polish)
```

## Parallel Opportunities

<!-- List tasks that can run in parallel within each phase -->

## Completion Criteria

- [ ] All tasks marked [X]
- [ ] Fitness functions pass (`evospec check`)
- [ ] Spec.yaml traceability updated with actual file paths
- [ ] ADRs created for significant decisions made during implementation
