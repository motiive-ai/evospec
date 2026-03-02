# Domain Contract: Order Management

> Bounded Context: **orders** | Classification: **core** | Owner: **commerce-core**

---

## 1. Context & Purpose

**Bounded Context**: Orders

**Context Map Position**: Downstream of `catalog` (Conformist), upstream of `shipping` (Published Language).

**Ubiquitous Language**:
- **Order**: A customer's intent to purchase one or more products
- **LineItem**: A single product entry within an order, with quantity and price
- **Order Status**: The lifecycle state of an order (draft, submitted, processing, shipped, delivered)
- **Tenant**: An isolated business entity; all orders belong to exactly one tenant

---

## 2. Strategic Classification (Evans)

- **Domain Type**: Core
- **Investment Level**: High — this is the primary revenue-generating domain
- **Competitive Differentiation**: Reliability and speed of order processing

---

## 3. Aggregates & Entities

### Order (Aggregate Root)

| Field | Type | Constraints |
|-------|------|------------|
| id | UUID | PK, auto-generated |
| tenant_id | string | Required, indexed, from auth context |
| user_id | UUID | Required, from auth token |
| status | enum | draft / submitted / processing / shipped / delivered |
| total_amount | decimal | Computed from line items, ≥ 0 |
| currency | string | ISO 4217, required |
| created_at | datetime | Auto-set |
| updated_at | datetime | Auto-updated |

### LineItem (Entity, owned by Order)

| Field | Type | Constraints |
|-------|------|------------|
| id | UUID | PK, auto-generated |
| order_id | UUID | FK → Order, required |
| product_id | UUID | Required |
| quantity | integer | ≥ 1 |
| unit_price | decimal | ≥ 0 |
| subtotal | decimal | Computed: quantity × unit_price |

---

## 4. Invariants

| ID | Statement | Enforcement | Fitness Function |
|----|----------|-------------|-----------------|
| INV-001 | Every Order must have at least one LineItem | integration-test | `tests/fitness/test_order_integrity.py` |
| INV-002 | Every query on orders must filter by tenant_id | integration-test | `tests/fitness/test_tenant_isolation.py` |
| INV-003 | Order status transitions follow: draft → submitted → processing → shipped → delivered (no reverse) | unit-test | `tests/fitness/test_order_state_machine.py` |
| INV-004 | LineItem quantity must be ≥ 1 | schema | Database constraint + API validation |
| INV-005 | Order total_amount must equal sum of line item subtotals | unit-test | `tests/fitness/test_order_integrity.py` |

---

## 5. State Machine

```
     ┌─────────┐
     │  draft   │
     └────┬─────┘
          │ submit()
          ▼
     ┌──────────┐
     │ submitted │
     └────┬──────┘
          │ process()
          ▼
     ┌────────────┐
     │ processing  │
     └────┬────────┘
          │ ship()
          ▼
     ┌──────────┐
     │ shipped   │
     └────┬──────┘
          │ deliver()
          ▼
     ┌───────────┐
     │ delivered  │
     └───────────┘
```

**Forbidden transitions**:
- delivered → any (terminal state)
- shipped → draft (no going back)
- Any state → draft (draft is initial only)

**Cancellation**: An order can be cancelled from `draft` or `submitted` only. Cancelled is a terminal state.

---

## 6. Domain Events

| Event | Produced When | Consumers |
|-------|--------------|-----------|
| `order.created` | New order saved | Analytics, Notifications |
| `order.submitted` | Order submitted for processing | Inventory, Payment |
| `order.shipped` | Order marked as shipped | Notifications, Shipping |
| `order.delivered` | Order confirmed delivered | Analytics, Reviews |

**Ordering guarantee**: Events for a single order are published in order.
**Idempotency**: Consumers must handle duplicate events (at-least-once delivery).

---

## 7. Authorization & Policies

| Operation | Allowed Roles | Additional Rules |
|-----------|--------------|-----------------|
| Create order | user, admin | Must be authenticated |
| View order | user, admin | Must be owner or admin |
| Submit order | user, admin | Must be owner |
| Process order | admin | Admin only |
| Cancel order | user, admin | Must be owner, only from draft/submitted |

**Data isolation**: Every query must filter by `tenant_id` from the auth context. No cross-tenant data access is permitted.

---

## 8. Backwards Compatibility & Migration

**Migration strategy**: Schema migration creates `orders` and `line_items` tables with required fields.

**Breaking changes**: None (new domain).

**Rollback plan**: Drop tables, no data dependencies from other contexts.

---

## 9. Fitness Functions

| Function | Type | Dimension | What it checks |
|----------|------|-----------|---------------|
| Order integrity | integration-test | data-integrity | Orders must have ≥ 1 line item, totals must match |
| Tenant isolation | integration-test | security | All queries scoped to tenant_id |
| State machine | unit-test | data-integrity | Only valid transitions allowed |

---

## 10. Team Ownership

| Team | Type | Interaction |
|------|------|------------|
| commerce-core | stream-aligned | Owns this context end-to-end |
| platform | platform | x-as-a-service: auth, database, infrastructure |

---

## 11. Traceability

**Endpoints**:
- GET /v1/orders/
- POST /v1/orders/
- GET /v1/orders/{id}
- PUT /v1/orders/{id}
- POST /v1/orders/{id}/submit

**Tables**: orders, line_items

**Modules**:
- app/api/v1/endpoints/orders.py
- app/models/order.py
- app/models/line_item.py
- app/schemas/order.py

**ADRs**:
- ADR-0001: Use event sourcing for order state transitions
- ADR-0002: Tenant isolation strategy

---

## 12. Anti-Requirements

1. This does NOT support cross-tenant order visibility.
2. This does NOT implement order splitting or merging.
3. This does NOT handle payment processing (separate bounded context).
4. This does NOT implement soft-delete — cancellation is the only removal mechanism.
