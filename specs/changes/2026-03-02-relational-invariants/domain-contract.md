# Domain Contract: Relational Invariants (cardinality + state transitions)

> Zone: **core** | Bounded Context: **spec-engine** | Status: **draft**

---

## 1. Context & Purpose

**Bounded Context**: spec-engine

**Context Map Position**: shared kernel (invariant schema used by spec-engine, domain-management, and agent-integration)

**Ubiquitous Language**:

| Term | Definition | Not to be confused with |
|------|-----------|------------------------|
| Relationship invariant | A rule constraining cardinality between two entities | Entity-scoped invariant (single entity) |
| Transition invariant | A rule constraining allowed state changes on an enum field | Relationship invariant (between entities) |
| Cardinality | Notation expressing min..max count of a relationship (e.g., `1..*`) | Database cardinality (FK multiplicity) |
| Forbidden transition | A state change that must never occur | Missing transition (not yet implemented) |
| Scope | The type of invariant: `entity` (default), `relationship`, or `transition` | Bounded context scope |

---

## 2. Strategic Classification

**Domain Type**: core — invariants are the foundation of the safety net

**Investment Level**: high — this is a core differentiator

**Rationale**: The invariant system is what makes EvoSpec more than a documentation tool. Extending it to cover relationship and transition rules completes the safety net's coverage of the most common business rule categories.

---

## 3. Aggregates & Entities

### Aggregate: Invariant

**Root Entity**: Invariant (extended)

**Entities**:

| Entity | Key Fields | Description |
|--------|-----------|-------------|
| Invariant | id, statement, enforcement, scope | Base invariant (existing + extended with scope) |
| RelationshipInvariant | source, target, cardinality | Invariant with scope=relationship |
| TransitionInvariant | entity, field, transitions, forbidden | Invariant with scope=transition |

**Value Objects**:

| Value Object | Fields | Constraints |
|-------------|--------|-------------|
| Cardinality | min, max | Notation: `0..1`, `1..1`, `1..*`, `0..*`, `N..M` |
| Transition | from, to | `to` is a list of valid target states |
| ForbiddenTransition | from, to, reason | `to` can be `*` (any state) |

---

## 4. Invariants

| ID | Invariant Statement | Enforcement | Fitness Function |
|----|-------------------|-------------|-----------------|
| REL-INV-SCHEMA-001 | Relationship-scoped invariants MUST have source, target, and cardinality fields | schema-validation | `tests/test_relational_invariants.py` |
| REL-INV-SCHEMA-002 | Transition-scoped invariants MUST have entity, field, and transitions fields | schema-validation | `tests/test_relational_invariants.py` |
| REL-INV-COMPAT-001 | Existing entity-scoped invariants MUST remain valid without modification | test | `tests/test_check.py` |

---

## 5. State Machine & Transitions

N/A — this change extends the invariant schema, it does not introduce its own state machine.

---

## 6. Domain Events

N/A

---

## 7. Authorization & Policies

N/A — invariant schema is not auth-gated.

---

## 8. Backwards Compatibility & Migration

**Breaking changes**: None — fully additive
- [ ] Schema migration required — No
- [ ] API contract change — No (MCP tools return extended data)
- [ ] Event schema change — No
- [ ] Data backfill needed — No

**Migration strategy**: Existing invariants without `scope` field are implicitly `scope: entity` (default). No migration needed.

**Rollback plan**: Remove scope field handling from check engine and config loader. Existing invariants unaffected.

**Reversibility**: moderate

---

## 9. Fitness Functions

| Name | Type | Dimension | Implementation |
|------|------|-----------|---------------|
| Relational invariant schema validation | unit-test | schema-integrity | `tests/test_relational_invariants.py` |
| Cardinality validation against entities.yaml | integration-test | data-integrity | `tests/test_relational_invariants.py` |
| Transition validation against entity enum fields | integration-test | data-integrity | `tests/test_relational_invariants.py` |
| Backwards compatibility with existing invariants | regression-test | backwards-compatibility | `tests/test_check.py` |

---

## 10. Team Ownership

**Owning Team**: evospec-core

**Team Type**: platform

**Cross-Team Dependencies**: None

**Cognitive Load Assessment**: Low — extends existing invariant schema with two new optional fields.

---

## 11. Traceability

**Endpoints**: None

**Tables**: None

**Modules**:
- `evospec.core.check` — validate relational/transition invariants
- `evospec.core.config` — load and merge new invariant scopes
- `evospec.mcp.server` — serve relational invariants

**Related ADRs**:
- Use cardinality notation (`N..M`) for programmatic validation

---

## 12. Anti-Requirements

1. **No graph-specific YAML syntax** — EvoSpec stays domain-agnostic. AI interprets graph semantics from entity descriptions.
2. **No temporal constraint syntax** — Describe temporal rules in plain language.
3. **No auto-detection of relational invariants** — That's the deep-reverse-engineering change.
4. **No runtime enforcement** — Invariants are checked at spec-time by `evospec check`, not at application runtime.
