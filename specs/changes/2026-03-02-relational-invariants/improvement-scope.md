# Improvement Scope: Relational Invariants (cardinality + state transitions)

> Zone: **core** | Type: **improvement** | Status: **draft**

---

## What Needs to Change

Current invariants are entity-scoped only — you can say "field X must not be null" but you can't express "entity A must relate to exactly 1 entity B and at least 1 entity C." Relationship rules and state machine transitions are universal patterns that the safety net currently can't enforce. This change adds two new invariant scopes: **relationship** (cardinality between entities) and **transition** (state machine rules on enum fields).

## Why Now

The invariant safety net has blind spots on relationship rules. When an AI agent checks `check_invariant_impact`, it can't see cardinality violations or illegal state transitions. This means the most common business rule failures — empty collections, orphaned records, forbidden state changes — are invisible to the governance system.

## Scope

### In Scope

- **Relationship-scoped invariants** with `source`, `target`, and `cardinality` fields
- **Transition-scoped invariants** with `entity`, `field`, `transitions`, and `forbidden` sections
- **Cardinality notation**: `1..1` (exactly one), `0..1` (optional), `1..*` (one or more), `0..*` (any), `N..M` (range)
- **`evospec check` validation** of relational invariants against entities.yaml relationships
- **MCP serving** of relational and transition invariants via existing `get_invariants()` tool
- **Schema extension** to spec.yaml invariants section

### Out of Scope

- Graph-specific YAML syntax (EvoSpec stays domain-agnostic — AI interprets)
- Temporal constraint syntax (describe in plain language)
- Hierarchy-specific syntax (same reasoning)
- Auto-detection of relational invariants from code (that's the deep-reverse-engineering change)

## Affected Areas

**Endpoints**: None (schema-only change)

**Tables**: None

**Modules**:
- `evospec.core.check` — validate relational/transition invariant structure and cross-reference with entities.yaml
- `evospec.core.config` — load and merge new invariant scopes
- `evospec.mcp.server` — serve relational invariants in `get_invariants()` and `check_invariant_impact()`

**Bounded Contexts**:
- `spec-engine` — invariant schema extension
- `domain-management` — entity relationship validation

## Invariant Impact

No conflicts with existing invariants. This is an additive schema extension — existing entity-scoped invariants remain valid without modification.

## Acceptance Criteria

- [ ] Invariants support `scope: relationship` with `source`, `target`, and `cardinality`
- [ ] Invariants support `scope: transition` with `entity`, `field`, `transitions`, `forbidden`
- [ ] Cardinality notation: `1..1`, `0..1`, `1..*`, `0..*`, `N..M`
- [ ] `evospec check` validates relational invariants against entities.yaml relationships
- [ ] `evospec check` validates transition invariants against entity enum fields
- [ ] MCP `get_invariants()` returns relational and transition invariants
- [ ] MCP `check_invariant_impact()` detects cardinality and transition conflicts
- [ ] Existing entity-scoped invariants continue to work without changes

### Example: Relationship Invariant

```yaml
invariants:
  # Existing entity-scoped (unchanged)
  - id: "INV-001"
    entity: "Order"
    statement: "Order total must be > 0"
    enforcement: "domain-logic"

  # NEW: Relationship-scoped
  - id: "REL-INV-001"
    scope: "relationship"
    source: "Order"
    target: "LineItem"
    cardinality: "1..*"
    statement: "An Order MUST have at least 1 LineItem before checkout"
    enforcement: "api-validation"

  # NEW: Transition-scoped
  - id: "TRANS-INV-001"
    scope: "transition"
    entity: "Order"
    field: "status"
    statement: "Order status transitions must follow the state machine"
    transitions:
      - from: "draft"
        to: ["pending_payment", "cancelled"]
      - from: "pending_payment"
        to: ["confirmed", "cancelled"]
      - from: "confirmed"
        to: ["shipped", "cancelled"]
      - from: "shipped"
        to: ["delivered"]
    forbidden:
      - from: "delivered"
        to: "*"
        reason: "terminal state"
    enforcement: "domain-logic"
```

## Risks & Rollback

**Risk level**: medium — schema extension touches the core invariant system

**Rollback plan**: Remove the new `scope` field handling; existing invariants without `scope` are unaffected

**Reversibility**: moderate — additive but touches the validation pipeline

## ADRs

- ADR: Use cardinality notation (`N..M`) rather than natural language for relationship constraints — enables programmatic validation
