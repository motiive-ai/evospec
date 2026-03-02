# Domain Contract: evospec-core-domain

> Zone: **core** | Bounded Context: **Spec Engine** | Status: **draft**

---

## 1. Context & Purpose

**Bounded Context**: Spec Engine — the core system that manages spec lifecycle, classification, validation, and fitness function execution.

**Context Map Position**: open-host / published language — the Spec Engine exposes its domain via CLI, MCP server, and Windsurf workflows. All other contexts (Reverse Engineering, AI Agent Integration) consume it.

**Ubiquitous Language** (terms specific to this context):

| Term | Definition | Not to be confused with |
|------|-----------|------------------------|
| Change Spec | A versioned specification describing a proposed change, classified by zone and type | A PR or ticket |
| Zone | Risk classification of a change: edge (experimental), hybrid (emerging), core (contractual) | Environment (dev/staging/prod) |
| Invariant | A testable proposition that must always hold true within a bounded context | A validation rule or assertion |
| Fitness Function | An automated test that guards an architectural property over time | A unit test (fitness functions guard architecture, not behavior) |
| Discovery Spec | A hypothesis-driven artifact for edge/hybrid changes, with assumptions and experiments | A requirements document |
| Domain Contract | A DDD-based artifact for core/hybrid changes, with entities, invariants, and state machines | An API contract or schema |
| Knowledge Funnel | The progression Mystery → Heuristic → Algorithm (Roger Martin) | A sales funnel |
| Kill Criteria | Specific measurable criteria for abandoning an experiment | Failure conditions |
| Classification | The process of determining a change's zone based on risk signals | Categorization or tagging |
| ADR | Architecture Decision Record — documents why a decision was made | A design doc or RFC |

---

## 2. Strategic Classification (Evans — Strategic Design)

**Domain Type**: core

**Investment Level**: high (core differentiator)

**Rationale**: The Spec Engine is what makes EvoSpec unique — the proportional governance model (edge/hybrid/core), the classification algorithm, and the invariant safety net. Without these, EvoSpec is just another template generator.

---

## 3. Aggregates & Entities

### Aggregate: ChangeSpec

**Root Entity**: ChangeSpec

**Entities**:

| Entity | Key Fields | Description |
|--------|-----------|-------------|
| ChangeSpec | id, title, zone, change_type, status, created_at | Root aggregate — a proposed change with its classification and artifacts |
| Classification | touches_*, reversibility, risk_level, rationale | Risk signal assessment that determines zone placement |
| InvariantImpact | conflicts[], entities_touched, contexts_touched, reviewed | Safety net check result showing which invariants a change may affect |
| Discovery | outcome, opportunity, iteration, assumptions[], experiments[], learnings[] | Edge/hybrid learning loop tracking |
| Assumption | id, statement, category, risk, status, test_method, result | A riskiest-thing-first hypothesis within a discovery |
| Experiment | id, assumption_id, type, result, confidence, decision | A concrete test run against an assumption |

**Value Objects**:

| Value Object | Fields | Constraints |
|-------------|--------|-------------|
| Zone | value: edge / hybrid / core | Must be one of three values |
| ChangeType | value: experiment / improvement / bugfix | Must be one of three values |
| SpecStatus | value: draft / proposed / accepted / in-progress / completed / abandoned / superseded | Follows state machine |
| RiskLevel | value: low / medium / high / critical | Derived from classification signals |
| Reversibility | value: trivial / moderate / difficult / irreversible | Assessed during classification |
| InvariantRef | invariant_id, statement, enforcement, fitness_function | Reference to an invariant definition |
| FitnessFunction | id, type, dimension, path | Reference to an executable guardrail |

### Aggregate: Feature

**Root Entity**: Feature

**Entities**:

| Entity | Key Fields | Description |
|--------|-----------|-------------|
| Feature | id, title, zone, status, knowledge_stage, owner, spec_ids[] | A tracked feature across the Knowledge Funnel lifecycle |

### Aggregate: ADR

**Root Entity**: ADR

**Entities**:

| Entity | Key Fields | Description |
|--------|-----------|-------------|
| ADR | number, title, status, date, zone, content | An Architecture Decision Record |

---

## 4. Invariants (DDD + Evolutionary Architecture)

> Invariants are testable propositions that must ALWAYS hold true within this bounded context.
> Every invariant should have an enforcement mechanism. Text alone is not a guardrail.

| ID | Invariant Statement | Enforcement | Fitness Function |
|----|-------------------|-------------|-----------------|
| INV-001 | Every core-zone spec MUST have at least one invariant defined | ci-check | tests/fitness/test_spec_invariants.py |
| INV-002 | Every core-zone spec MUST have at least one fitness function | ci-check | tests/fitness/test_spec_invariants.py |
| INV-003 | Every core-zone spec MUST have a domain-contract.md file | ci-check | tests/fitness/test_spec_invariants.py |
| INV-004 | Every edge-zone spec MUST have a discovery-spec.md file | ci-check | tests/fitness/test_spec_invariants.py |
| INV-005 | Every invariant MUST have an enforcement mechanism (not empty) | ci-check | tests/fitness/test_spec_invariants.py |
| INV-006 | Classification MUST be reviewed (invariant_impact.reviewed = true) before a spec moves to in-progress | policy | tests/fitness/test_spec_invariants.py |
| INV-007 | spec.yaml MUST validate against the JSON Schema (schemas/spec.schema.json) | schema | tests/fitness/test_spec_schema.py |
| INV-008 | An evospec.yaml config file MUST exist at the project root before any command other than `init` runs | ci-check | tests/fitness/test_spec_invariants.py |

---

## 5. State Machine & Transitions

### ChangeSpec Status

**States**:
```
[draft] --> [proposed] --> [accepted] --> [in-progress] --> [completed]
   |            |              |               |
   +---> [abandoned] <--------+---------------+
                               |
                         [superseded]
```

**Transition Rules**:

| From | To | Trigger | Guard Condition | Side Effects |
|------|----|---------|----------------|-------------|
| draft | proposed | Author submits for review | Zone and classification must be set | — |
| proposed | accepted | Reviewer approves | Invariant impact must be reviewed (INV-006) | — |
| accepted | in-progress | Work begins | — | Tasks file may be generated |
| in-progress | completed | All acceptance criteria met | Fitness functions pass | — |
| * | abandoned | Decision to abandon | — | Reason logged |
| accepted | superseded | Replaced by newer spec | Successor spec ID must be set | — |

**Forbidden Transitions** (anti-requirements):

| From | To | Why |
|------|----|-----|
| completed | draft | Completed specs are immutable records |
| abandoned | in-progress | Must create a new spec if revisiting |
| draft | in-progress | Cannot skip review (proposed → accepted) |

### Assumption Status (Discovery)

**States**:
```
[untested] --> [testing] --> [validated]    --> [promoted-to-core]
                         --> [invalidated]  --> [pivoted]
```

### Feature Lifecycle

**States**:
```
[discovery] --> [specifying] --> [implementing] --> [validating] --> [shipped]
     |               |                |                |
     +---------------+----------------+----------------+--> [killed]
```

---

## 6. Domain Events

| Event | Produced By | Payload | Consumers |
|-------|------------|---------|-----------|
| SpecCreated | `evospec new` | spec_id, title, zone, change_type | MCP server, status dashboard |
| SpecClassified | `evospec classify` | spec_id, zone, risk_level, classification | Artifact generator (creates missing templates) |
| InvariantConflictDetected | `check_invariant_impact` | spec_id, invariant_id, impact, resolution | Spec author, MCP clients |
| ChecksPassed | `evospec check` | spec_id, errors, warnings | CI pipeline |
| ChecksFailed | `evospec check` | spec_id, errors, warnings | CI pipeline, spec author |
| FitnessFunctionExecuted | `evospec fitness` | ff_id, spec_id, result (pass/fail/skip) | CI pipeline |
| ExperimentRecorded | `evospec learn` | spec_id, experiment_id, decision | Discovery dashboard |
| AssumptionUpdated | `evospec learn` | spec_id, assumption_id, old_status, new_status | Discovery dashboard |
| FeatureStatusChanged | `evospec feature update` | feature_id, old_status, new_status | Status dashboard |

**Event Ordering Guarantees**: per-aggregate (events within a spec are ordered by timestamp)

**Idempotency**: Yes — all file-based operations are idempotent (writing the same content twice produces the same result)

---

## 7. Authorization & Policies

**Access Rules**:

| Operation | Allowed Roles | Additional Conditions |
|-----------|--------------|----------------------|
| evospec init | Any developer | Only once per project (idempotent) |
| evospec new | Any developer | evospec.yaml must exist |
| evospec classify | Spec author / reviewer | Spec must be in draft status |
| evospec check | Any (CI included) | Read-only operation |
| evospec reverse * | Any developer | evospec.yaml must exist |

**Tenant Isolation**: N/A — EvoSpec is a single-project tool, no multi-tenancy.

**Data Sensitivity**: None — specs are markdown/YAML files, no PII or secrets.

---

## 8. Backwards Compatibility & Migration

**Breaking changes**: This is the initial domain contract (v0.1.0), no existing clients to break.
- [ ] Schema migration required
- [ ] API contract change
- [ ] Event schema change
- [ ] Data backfill needed

**Migration strategy**: N/A (initial version)

**Rollback plan**: Delete spec files, revert `evospec init`.

**Reversibility**: trivial — all artifacts are markdown/YAML files that can be deleted without side effects.

---

## 9. Fitness Functions (Neal Ford — Evolutionary Architecture)

> Every core change must have at least one automated fitness function.

| Name | Type | Dimension | Implementation |
|------|------|-----------|---------------|
| Spec schema validation | contract-test | data-integrity | tests/fitness/test_spec_schema.py |
| Core zone invariant enforcement | integration-test | data-integrity | tests/fitness/test_spec_invariants.py |
| CLI smoke tests | integration-test | operability | tests/test_cli.py |

---

## 10. Team Ownership (Team Topologies)

**Owning Team**: EvoSpec Core

**Team Type**: platform (EvoSpec is a platform that stream-aligned teams consume)

**Cross-Team Dependencies**:

| Team | Interaction Mode | What's Needed |
|------|-----------------|--------------|
| AI Agent teams (Windsurf, Claude Code) | x-as-a-service | MCP server protocol stability |
| Adopting project teams | x-as-a-service | CLI stability, template quality |

**Cognitive Load Assessment**: Low — EvoSpec's core is a CLI tool with file-based state. No databases, no services, no infrastructure.

---

## 11. Traceability

**Endpoints**: N/A (CLI tool, no HTTP endpoints — MCP server uses stdio transport)

**Tables**: N/A (file-based, no database)

**Modules**:
- `evospec.cli.main` — Click CLI entry point, all commands
- `evospec.core.config` — Project root detection, config loading, path resolution
- `evospec.core.init` — Project initialization, template copying, AI agent setup
- `evospec.core.new_spec` — Spec creation with template rendering
- `evospec.core.classify` — Interactive zone classification algorithm
- `evospec.core.check` — Spec validation, schema checks, fitness function runner
- `evospec.core.discovery` — Experiment recording, assumption lifecycle
- `evospec.core.features` — Feature registry and lifecycle management
- `evospec.core.adr` — ADR creation and listing
- `evospec.core.render` — Consolidated markdown rendering
- `evospec.core.status` — Status dashboard for all specs
- `evospec.reverse.api` — Reverse-engineer API endpoints (FastAPI, Django, Express)
- `evospec.reverse.db` — Reverse-engineer database models (SQLAlchemy, Django ORM)
- `evospec.mcp.server` — MCP server exposing tools and resources for AI agents
- `evospec.templates` — Jinja-style templates for all artifacts

**Related ADRs**:
- docs/adr/0001-adopt-evospec.md

---

## 12. Anti-Requirements (What This Is NOT)

1. EvoSpec is NOT a project management tool — it does not replace Jira, Linear, or GitHub Issues
2. EvoSpec is NOT a CI/CD pipeline — it provides fitness functions but does not run deployments
3. EvoSpec is NOT an AI agent — it provides specs and tools for AI agents to consume, but humans decide
4. EvoSpec is NOT a code generator — reverse engineering extracts domain knowledge, it does not generate application code
5. EvoSpec is NOT a database — all state is file-based (YAML + Markdown), no server or persistence layer
