# Domain Contract: auto-spec-sync-and-verification

> Zone: **hybrid** | Bounded Context: **** | Status: **draft**

---

## 1. Context & Purpose

**Bounded Context**: 

**Context Map Position**: <!-- conformist / anti-corruption layer / shared kernel / open-host / published language -->

**Ubiquitous Language** (terms specific to this context):

| Term | Definition | Not to be confused with |
|------|-----------|------------------------|
| | | |

---

## 2. Strategic Classification (Evans — Strategic Design)

**Domain Type**: <!-- core / supporting / generic -->

**Investment Level**: <!-- high (core differentiator) / medium (important but not unique) / low (commodity) -->

**Rationale**: <!-- Why this classification? What makes this core vs. supporting? -->

---

## 3. Aggregates & Entities

### Aggregate: {{ aggregate_name }}

**Root Entity**: {{ entity_name }}

**Entities**:

| Entity | Key Fields | Description |
|--------|-----------|-------------|
| | | |

**Value Objects**:

| Value Object | Fields | Constraints |
|-------------|--------|-------------|
| | | |

---

## 4. Invariants (DDD + Evolutionary Architecture)

> Invariants are testable propositions that must ALWAYS hold true within this bounded context.
> Every invariant should have an enforcement mechanism. Text alone is not a guardrail.

| ID | Invariant Statement | Enforcement | Fitness Function |
|----|-------------------|-------------|-----------------|
| INV-001 | | test / ci-check / schema / policy | |
| INV-002 | | | |
| INV-003 | | | |

---

## 5. State Machine & Transitions

**States**:
```
[state_1] --> [state_2] --> [state_3]
     |                         |
     +-----> [state_4] <------+
```

**Transition Rules**:

| From | To | Trigger | Guard Condition | Side Effects |
|------|----|---------|----------------|-------------|
| | | | | |

**Forbidden Transitions** (anti-requirements):

| From | To | Why |
|------|----|-----|
| | | |

---

## 6. Domain Events

| Event | Produced By | Payload | Consumers |
|-------|------------|---------|-----------|
| | | | |

**Event Ordering Guarantees**: <!-- none / per-aggregate / total -->

**Idempotency**: <!-- Are consumers expected to be idempotent? -->

---

## 7. Authorization & Policies

**Access Rules**:

| Operation | Allowed Roles | Additional Conditions |
|-----------|--------------|----------------------|
| | | |

**Tenant Isolation**: <!-- How is multi-tenancy enforced? -->

**Data Sensitivity**: <!-- PII? PHI? Financial? What classification? -->

---

## 8. Backwards Compatibility & Migration

**Breaking changes**: <!-- Does this change break existing clients? -->
- [ ] Schema migration required
- [ ] API contract change
- [ ] Event schema change
- [ ] Data backfill needed

**Migration strategy**: <!-- How will existing data be migrated? -->

**Rollback plan**: <!-- If this goes wrong, how do we revert? -->

**Reversibility**: <!-- trivial / moderate / difficult / irreversible -->

---

## 9. Fitness Functions (Neal Ford — Evolutionary Architecture)

> Every core change must have at least one automated fitness function.

| Name | Type | Dimension | Implementation |
|------|------|-----------|---------------|
| | unit-test / integration-test / contract-test / schema-check / lint-rule / ci-gate | security / data-integrity / performance / operability | path or description |

---

## 10. Team Ownership (Team Topologies)

**Owning Team**: {{ team_name }}

**Team Type**: <!-- stream-aligned / platform / enabling / complicated-subsystem -->

**Cross-Team Dependencies**:

| Team | Interaction Mode | What's Needed |
|------|-----------------|--------------|
| | collaboration / x-as-a-service / facilitating | |

**Cognitive Load Assessment**: <!-- Is this adding significant complexity to the owning team? -->

---

## 11. Traceability

**Endpoints**: <!-- API routes affected -->
- ...

**Tables**: <!-- Database tables affected -->
- ...

**Modules**: <!-- Code packages affected -->
- ...

**Related ADRs**:
- ...

---

## 12. Anti-Requirements (What This Is NOT)

<!-- Explicit boundaries. What is out of scope? What should NOT be built? -->
1. ...
2. ...
