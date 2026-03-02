---
spec_id: "order-management"
title: "Order Management CRUD API"
zone: "core"
status: "in-progress"
created_at: "2025-06-01"
total_tasks: 18
completed_tasks: 8
phases:
  - name: Setup
    tasks: ["T001", "T002"]
  - name: Foundation
    tasks: ["T003", "T004", "T005"]
  - name: Core Implementation
    tasks: ["T006", "T007", "T008", "T009", "T010"]
  - name: Integration
    tasks: ["T011", "T012", "T013"]
  - name: Guardrails
    tasks: ["T014", "T015", "T016"]
  - name: Polish
    tasks: ["T017", "T018"]
invariant_coverage:
  INV-001: "T014"
  INV-002: "T015"
  INV-003: "T016"
---

# Implementation Tasks: Order Management CRUD API

> Zone: **core** | Status: **in-progress** | Generated: 2025-06-01

---

## Context

- **Spec**: specs/changes/2025-06-01-order-management/spec.yaml
- **Domain Contract**: specs/changes/2025-06-01-order-management/domain-contract.md
- **ADRs**: docs/adr/0002-use-event-sourcing.md, docs/adr/0003-tenant-isolation-strategy.md

## Implementation Strategy

- **MVP first**: Ship basic CRUD with tenant isolation before adding event sourcing
- **Incremental delivery**: Each phase should be independently testable
- **Parallel where possible**: Tasks marked [P] can run concurrently

## Task Format

```
- [X] T001 [P] [Phase] Description with exact file path
```

- **Checkbox**: `- [ ]` (mark `[X]` when complete)
- **Task ID**: Sequential (T001, T002, ...)
- **[P]**: Parallelizable (different files, no dependency on incomplete tasks)
- **[Phase]**: Phase label for grouping

---

## Phase 1: Setup

- [X] T001 [Setup] Verify Python 3.11+, FastAPI, SQLAlchemy, Alembic dependencies
- [X] T002 [Setup] Add `pytest-asyncio` and `httpx` to dev dependencies for fitness functions

## Phase 2: Foundation

- [X] T003 [Foundation] Create Alembic migration `alembic/versions/001_create_orders.py` — orders table with tenant_id, status, total_amount, currency, timestamps
- [X] T004 [P] [Foundation] Create Alembic migration `alembic/versions/002_create_line_items.py` — line_items table with order_id FK, product_id, quantity, unit_price
- [X] T005 [Foundation] Create SQLAlchemy models `app/models/order.py` and `app/models/line_item.py`

## Phase 3: Core Implementation

- [X] T006 [Core] Create Pydantic schemas `app/schemas/order.py` — OrderCreate, OrderUpdate, OrderResponse, LineItemCreate
- [X] T007 [Core] Implement `POST /v1/orders/` endpoint in `app/api/v1/endpoints/orders.py` — create order with line items, enforce INV-001 (at least one line item)
- [X] T008 [P] [Core] Implement `GET /v1/orders/` and `GET /v1/orders/{id}` — list and detail with tenant_id filtering (INV-002)
- [ ] T009 [Core] Implement `PUT /v1/orders/{id}` — update order, revalidate line items
- [ ] T010 [Core] Implement `POST /v1/orders/{id}/submit` — state transition with state machine validation (INV-003)

## Phase 4: Integration & Wiring

- [ ] T011 [Integration] Wire order endpoints to FastAPI router with JWT authentication middleware
- [ ] T012 [P] [Integration] Emit domain events (`order.created`, `order.submitted`, `order.shipped`) after state transitions
- [ ] T013 [Integration] Add tenant_id extraction from JWT token to all order queries

## Phase 5: Guardrails

- [ ] T014 [Guardrails] Write fitness function `tests/fitness/test_order_integrity.py` — every order has ≥ 1 line item, total matches sum (INV-001, INV-005)
- [ ] T015 [Guardrails] Write fitness function `tests/fitness/test_tenant_isolation.py` — scan all query builders for tenant_id filter (INV-002)
- [ ] T016 [Guardrails] Write fitness function `tests/fitness/test_order_state_machine.py` — only valid transitions allowed (INV-003)

## Phase 6: Polish

- [ ] T017 [Polish] Add structured logging for order operations (create, submit, ship, deliver)
- [ ] T018 [Polish] Update spec.yaml traceability with actual file paths and run `evospec check`

---

## Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundation) → Phase 3 (Core) → Phase 4 (Integration) → Phase 5 (Guardrails) → Phase 6 (Polish)
```

## Parallel Opportunities

- T003 and T004 can run in parallel (separate migration files)
- T007 and T008 can run in parallel (separate endpoints, same model)
- T011 and T012 can run in parallel (routing vs. event emission)

## Completion Criteria

- [ ] All tasks marked [X]
- [ ] Fitness functions pass (`evospec check --run-fitness`)
- [ ] Spec.yaml traceability updated with actual file paths
- [ ] ADRs created for significant decisions made during implementation
- [ ] Domain contract invariants all have corresponding fitness functions
