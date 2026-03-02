---
name: evospec-contract
description: Create or update a Domain Contract for a change spec. Operates in the Core Engine layer, moving knowledge from Heuristic → Algorithm.
---

# Contract

## Context

This workflow operates in the **Core Engine** layer of EvoSpec. The Core Engine is where:
- Knowledge is in the **Heuristic → Algorithm** stage (Roger Martin's Knowledge Funnel)
- We use **DDD** (Evans/Vernon) to model bounded contexts, entities, invariants
- We use **Evolutionary Architecture** (Neal Ford) to define fitness functions
- Invariants are non-negotiable and must be enforceable
- The goal is **stability and correctness**, not exploration

See [references/context.md](references/context.md) for full framework context.

## Steps

1. **Find the spec directory**
   - Check if `evospec.yaml` exists. If not, instruct user to run `evospec init`.
   - If user input contains a spec path, use it.
   - Otherwise, list available specs and let the user choose.
   - Read the existing `spec.yaml` to understand the change context.

2. **Load project context**
   - Read `evospec.yaml` for bounded contexts registry, team topology, strategy
   - Read `specs/domain/glossary.md` for ubiquitous language
   - Read `specs/domain/context-map.md` for bounded context relationships
   - If a `discovery-spec.md` exists for this change, read it for context

3. **Reverse-engineer if possible *(interactive)***
   - Ask: "Should I scan existing code to pre-populate the domain contract?"
   - If yes, scan for:
     - Database models/tables (SQLAlchemy, Django, etc.)
     - API endpoints (FastAPI, Django, Express, etc.)
     - Existing validation rules and business logic
   - Use findings as a starting point for the contract

4. **Generate domain-contract.md**
   **Section 1 — Context & Purpose**:
   - Identify the bounded context (use glossary and context map if available)
   - Determine context map position (conformist, ACL, shared kernel, etc.)
   - Define ubiquitous language terms specific to this context
   
   **Section 2 — Strategic Classification** (Evans):
   - Classify as core / supporting / generic domain
   - Determine investment level based on competitive differentiation
   
   **Section 3 — Aggregates & Entities**:
   - Define the aggregate root and its entities
   - List value objects with constraints
   - If reverse-engineered from code, validate against actual schema
   
   **Section 4 — Invariants** (DDD + Evolutionary Architecture):
   - **CRITICAL**: Every invariant MUST be written as a testable proposition
   - Every invariant MUST have an enforcement mechanism (test, ci-check, schema, policy)
   - Every invariant SHOULD reference a fitness function
   - Common invariant patterns:
     - Ownership: "Entity X must belong to its owning user"
     - Data isolation: "Every query must scope to the current tenant"
     - State transitions: "Entity can only transition from state A to state B"
     - Data integrity: "Field X must not be null when status is Y"
     - Authorization: "Only role Z can perform operation W"
   
   **Section 5 — State Machine & Transitions**:
   - Draw the state diagram
   - Define transition rules with guards and side effects
   - Define forbidden transitions (anti-requirements)
   
   **Section 6 — Domain Events**:
   - List events produced and consumed
   - Define ordering guarantees and idempotency requirements
   
   **Section 7 — Authorization & Policies**:
   - Map operations to allowed roles
   - Define tenant isolation strategy
   - Classify data sensitivity
   
   **Section 8 — Backwards Compatibility & Migration**:
   - Identify breaking changes
   - Define migration strategy and rollback plan
   - Assess reversibility
   
   **Section 9 — Fitness Functions** (Neal Ford):
   - **REQUIRED**: At least one automated fitness function per invariant
   - Types: unit-test, integration-test, contract-test, schema-check, lint-rule, ci-gate
   - Dimensions: security, data-integrity, performance, operability
   
   **Section 10 — Team Ownership** (Team Topologies):
   - Identify owning team and type
   - List cross-team dependencies with interaction modes
   - Assess cognitive load impact
   
   **Section 11 — Traceability**:
   - List endpoints, tables, modules affected
   - Link to related ADRs
   
   **Section 12 — Anti-Requirements**:
   - Explicitly state what is NOT in scope

5. **Update spec.yaml**
   - Set `bounded_context` field
   - Add invariants array with enforcement mechanisms
   - Add fitness_functions array
   - Update traceability with discovered endpoints/tables/modules
   - If zone was "edge", suggest upgrading to "hybrid" or "core"

6. **Update domain glossary**
   - If new ubiquitous language terms were defined, append to `specs/domain/glossary.md`

7. **Suggest ADRs**
   - If significant architectural decisions were made during contract creation, suggest creating ADRs
   - Example: "Consider creating an ADR for: 'Use event sourcing for order state transitions'"

8. **Report**
   - Print created/updated files
   - List invariants defined and their enforcement status
   - List fitness functions needed
   - Suggest next steps:
     - "Run `/evospec.tasks` to generate implementation tasks"
     - "Run `/evospec.check` to validate the spec"

## Rules

- Invariants are non-negotiable — do not skip or soften them
- Every invariant needs enforcement — text alone is not a guardrail
- Use existing ubiquitous language from the glossary
- Core zone MUST have: bounded_context, invariants, fitness_functions in spec.yaml
- Keep contracts focused — one bounded context per contract
- If the user hasn't done discovery yet, suggest running `/evospec.discover` first

---

*Full framework context: [references/context.md](references/context.md)*
