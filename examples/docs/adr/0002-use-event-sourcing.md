# ADR-0002: Use Event Sourcing for Order State Transitions

> Status: **accepted** | Date: 2025-06-01 | Zone: core

---

## Context

Orders have a strict state machine (draft → submitted → processing → shipped → delivered).
We need an audit trail of every state transition for compliance and debugging.
Traditional CRUD updates would lose the history of transitions.

## Decision

Use event sourcing for order state transitions:
- Every state change produces a domain event (`order.created`, `order.submitted`, etc.)
- Events are persisted in an append-only event store
- Current state is derived from replaying events
- Events are published to downstream consumers (notifications, analytics)

## Consequences

### Positive
- Complete audit trail of every order state change
- Downstream consumers can react to events asynchronously
- Enables future features like order timeline, undo operations
- Natural fit for the Order state machine invariant (INV-003)

### Negative
- More complex than simple CRUD updates
- Event schema must be versioned carefully
- Eventual consistency for read models

## Alternatives Considered

1. **CRUD with audit log table**: Simpler but audit log is a separate concern, easy to forget
2. **CDC (Change Data Capture)**: Infrastructure-heavy, depends on database vendor

## Reversibility

**Assessment**: moderate — would require migrating from event store back to CRUD, but domain events can continue to be published either way.
