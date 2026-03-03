# Domain Contract: Deep Reverse Engineering

> Zone: **core** | Bounded Context: **reverse-engineering** | Status: **draft**

---

## 1. Context & Purpose

**Bounded Context**: reverse-engineering

**Context Map Position**: open-host (produces structured data consumed by domain-management and agent-integration)

**Ubiquitous Language**:

| Term | Definition | Not to be confused with |
|------|-----------|------------------------|
| Deep reverse | Semantic code analysis beyond structural scanning (`--deep` flag) | Shallow reverse (existing, structure-only) |
| Suggested invariant | An invariant inferred from code with a confidence level — not confirmed until human reviews | Confirmed invariant (in spec.yaml) |
| Confidence level | How certain the detection is: high (DB constraint), medium (code pattern), low (heuristic) | Risk level (spec classification) |
| DTO walker | Recursive field resolution of request/response data transfer objects | Entity scanner (DB models) |
| State machine detection | Building transition graphs from enum fields + service code analysis | State machine definition (in spec) |

---

## 2. Strategic Classification

**Domain Type**: core — reverse engineering quality directly determines MCP context quality

**Investment Level**: high — this is what makes specs self-populating

**Rationale**: Without deep reverse, teams must manually curate every API schema, invariant, and state machine. Deep reverse automates the most tedious part of spec creation.

---

## 3. Aggregates & Entities

### Aggregate: DeepReverseResult

**Root Entity**: DeepReverseResult

**Entities**:

| Entity | Key Fields | Description |
|--------|-----------|-------------|
| DeepEndpoint | method, path, handler, request, response, annotations | API endpoint with full schema |
| SuggestedInvariant | id, entity, rule, source, confidence, enforcement | Auto-detected invariant candidate |
| DetectedStateMachine | entity, field, states, transitions, forbidden, diagram | State machine from enum analysis |
| ExternalDependency | name, type, operations, client_class | Service call with payload |
| DomainEvent | name, producer, trigger, payload_fields, consumers | Event publishing pattern |

**Value Objects**:

| Value Object | Fields | Constraints |
|-------------|--------|-------------|
| RequestSchema | content_type, body_class, fields | Recursive field structure |
| ResponseSchema | success, errors | Status-keyed responses |
| SchemaField | name, type, required, constraints | Single field definition |

---

## 4. Invariants

| ID | Invariant Statement | Enforcement | Fitness Function |
|----|-------------------|-------------|-----------------|
| DEEP-REV-001 | Deep reverse MUST NOT overwrite existing manually-curated spec data without `--force` flag | api-validation | `tests/test_deep_reverse.py` |
| DEEP-REV-002 | Suggested invariants MUST have confidence level (high/medium/low) and source code reference | schema-validation | `tests/test_deep_reverse.py` |
| DEEP-REV-003 | Existing shallow reverse (without `--deep`) MUST continue to work unchanged | test | `tests/test_reverse.py` |

---

## 5. State Machine & Transitions

N/A — this change detects state machines in user code, it does not introduce its own.

---

## 6. Domain Events

N/A

---

## 7. Authorization & Policies

N/A — CLI command, no auth.

---

## 8. Backwards Compatibility & Migration

**Breaking changes**: None — `--deep` is an additive flag
- [ ] Schema migration required — No
- [ ] API contract change — No
- [ ] Event schema change — No
- [ ] Data backfill needed — No

**Migration strategy**: N/A — existing shallow reverse unmodified.

**Rollback plan**: Remove `--deep` flag handling. Shallow reverse unaffected.

**Reversibility**: trivial

---

## 9. Fitness Functions

| Name | Type | Dimension | Implementation |
|------|------|-----------|---------------|
| Deep API schema extraction (Spring Boot) | integration-test | correctness | `tests/test_deep_reverse.py` |
| Deep API schema extraction (FastAPI) | integration-test | correctness | `tests/test_deep_reverse.py` |
| Invariant detection from annotations | integration-test | correctness | `tests/test_deep_reverse.py` |
| State machine detection from enums | integration-test | correctness | `tests/test_deep_reverse.py` |
| Shallow reverse regression | regression-test | backwards-compatibility | `tests/test_reverse.py` |

---

## 10. Team Ownership

**Owning Team**: evospec-core

**Team Type**: platform

**Cross-Team Dependencies**: None

**Cognitive Load Assessment**: Medium — adds framework-specific parsers, but each is isolated and independently testable.

---

## 11. Traceability

**Endpoints**: None

**Tables**: None

**Modules**:
- `evospec.reverse.api` — deep schema extraction per framework
- `evospec.reverse.db` — invariant detection + state machine extraction
- `evospec.reverse.deps` — deep dependency mapping
- `evospec.core.config` — load deep reverse output

**Related ADRs**:
- Confidence levels on suggested invariants (not auto-confirmed)
- Static analysis only (no runtime)

---

## 12. Anti-Requirements

1. **No auto-writing without confirmation** — Deep reverse suggests, human confirms. Use `--write` to persist.
2. **No runtime analysis** — Static analysis only, keeps results deterministic.
3. **No ML/LLM dependency** — Pattern matching and AST parsing, not AI inference.
4. **No modification of existing shallow reverse** — `--deep` is purely additive.
