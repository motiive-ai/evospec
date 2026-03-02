# EvoSpec — AI Agent Context

> This file is auto-generated from canonical workflow specs.
> Edit the source in `src/evospec/templates/workflows/` and run `evospec generate agents`.
> These instructions ensure Claude Code produces the **same artifacts** as
> Windsurf `/evospec.*` workflows and Cursor rules.

## Framework

This project uses **EvoSpec** — a spec-driven delivery toolkit.

**Core principle**: Progressive specs at the edge. Contracts in the core.

## Two Layers

| Layer | Knowledge Stage | Approach | Artifacts |
|-------|----------------|----------|-----------|
| **Discovery Layer** (edge) | Mystery → Heuristic | Design Thinking + Continuous Discovery | discovery-spec.md |
| **Core Engine** (core) | Heuristic → Algorithm | DDD + Evolutionary Architecture | domain-contract.md |

## Spec Structure

```
specs/
├── changes/                    # Change specifications
│   └── YYYY-MM-DD-<slug>/
│       ├── spec.yaml           # Machine-readable classification + metadata
│       ├── discovery-spec.md   # Hypothesis, experiments, learning (edge/hybrid)
│       ├── domain-contract.md  # Entities, invariants, fitness functions (core/hybrid)
│       ├── improvement-scope.md # Brief scope doc (improvements only)
│       ├── bugfix-report.md    # Root cause + fix strategy (bugfixes only)
│       ├── tasks.md            # Implementation tasks (AI work queue)
│       ├── implementation-spec.md # As-built blueprint (created by tasks, updated by implement)
│       └── checks/             # Executable guardrails
├── domain/
│   ├── entities.yaml           # Domain entity registry (fields, relationships, invariants)
│   ├── contexts.yaml           # Bounded contexts (owner, type, description)
│   ├── features.yaml           # Feature lifecycle registry
│   ├── glossary.md             # Ubiquitous language
│   └── context-map.md          # Bounded context relationships
docs/
└── adr/                        # Architecture Decision Records
```

## Zone Classification

| Zone | Required Artifacts | Guardrails |
|------|-------------------|------------|
| **edge** | discovery-spec.md, spec.yaml with discovery section | Metrics + kill criteria |
| **hybrid** | discovery-spec.md + domain-contract.md (minimal) | Contract tests at boundaries |
| **core** | domain-contract.md, spec.yaml with invariants + fitness_functions | Fitness functions + CI gates |

## Three Entry Points

| Type | When | Artifacts |
|------|------|-----------|
| **Experiment** | Unknown if users want it | discovery-spec.md, spec.yaml |
| **Improvement** | Known need, known solution | improvement-scope.md, spec.yaml, tasks.md |
| **Bug fix** | Something is broken | bugfix-report.md, spec.yaml, tasks.md |

All three entry points **MUST** run the invariant impact check before proceeding.

## Invariant Safety Net

**Resolution options** for invariant conflicts:
- **exempt** — Experiment behind a feature flag, don't touch the invariant
- **evolve** — Propose INV-001-v2 with migration path + new fitness function
- **shadow** — Validate need via interviews/analytics BEFORE touching schema
- **redesign** — Change approach to avoid the conflict

MCP tool: `check_invariant_impact(entities=[...], contexts=[...], description="...")`
MCP resource: `evospec://invariants` — all invariants from core/hybrid specs

---

# Workflow Procedures

These procedures define exactly what artifacts to produce and how.
Follow them step by step to ensure output is compatible across all AI platforms.

## Procedure: ADR

Equivalent to Windsurf `/evospec.adr`.

1. **Find the project**:
   - Check `evospec.yaml` exists. If not: instruct user to run `evospec init`.
   - Determine the ADR directory from config (default: `docs/adr/`).

2. **Parse the decision topic**:
   - Extract the core decision to be documented from user input.
   - If no input provided, ask: "What decision do you want to record?"

3. **Determine next ADR number**:
   - Scan existing ADR files in the directory.
   - Find the highest number and increment by 1.

4. **Generate the ADR**:
   **Context**:
   - What is the issue motivating this decision?
   - If a related spec exists, reference it.
   - Include relevant technical and organizational constraints.
   
   **Options Considered** (at least 2, ideally 3):
   - For each option: describe it, list pros and cons.
   - If the user mentioned alternatives, use those.
   - If not, generate reasonable alternatives based on the decision context.
   
   **"What Would Have to Be True"** (Roger Martin):
   - For the chosen option: what assumptions must hold for this to be the right choice?
   - This is the most valuable section — it makes implicit assumptions explicit.
   
   **Decision**:
   - Clear statement of what was chosen.
   
   **Consequences**:
   - Positive consequences
   - Negative consequences (be honest)
   - Risks
   
   **Reversibility**:
   - Assessment: trivial / moderate / difficult / irreversible
   - Rollback plan: what's involved if we need to reverse this?
   
   **Organizational Risk** (Hogan):
   - Are there behavioral or cultural patterns that could derail this decision?
   
   **Related**:
   - Link to related specs, other ADRs, or external references.

5. **Write the ADR file**:
   - Filename: `NNNN-<slug>.md` (e.g., `0003-use-jwt-for-auth.md`)
   - Status: `proposed` (human must accept)

6. **Report**:
   - Print the ADR path and number.
   - Remind: "ADR status is 'proposed'. Review and change to 'accepted' when approved."
   - If related specs exist, suggest linking them in spec.yaml.

**Rules**: ADRs are never deleted, only superseded Status lifecycle: proposed → accepted → deprecated → superseded Keep ADRs short — one decision, one page
- Always include the 'What Would Have to Be True' section
- Always include reversibility assessment
- If the decision is about a core zone change, flag that fitness functions may be needed

## Procedure: Capture

Equivalent to Windsurf `/evospec.capture`.

1. **Find the spec directory and codebase**:
   - Check `evospec.yaml` exists. If not: instruct user to run `evospec init`.
   - If user specifies a spec path, use it. Otherwise list available specs.
   - Read `spec.yaml` to understand the zone, classification, and traceability.
   - If `spec.yaml` doesn't exist yet (user built without specs), create one:
     - Ask the user to describe what they built in 1-2 sentences
     - Auto-classify the zone (edge/hybrid/core)

2. **Scan the implementation**:
   Use `spec.yaml → traceability.modules` to find the code. If traceability is empty,
   ask the user which directories/files contain the implementation.
   
   **Scan for**:
   - **Components/Modules**: file structure, exports, responsibilities
   - **API calls**: HTTP clients, fetch calls, service URLs, endpoints consumed
   - **State management**: useState, Redux stores, database models, caches
   - **Configuration**: env vars, feature flags, config files
   - **Tests**: test files, coverage, test frameworks
   - **Dependencies**: package.json, requirements.txt, pom.xml, go.mod
   
   Build a mental model of the implementation before writing anything.

3. **Generate implementation-spec.md**:
   Use the `implementation-spec.md` template. Fill in every section from the code scan:
   
   - **§1 Overview**: tech stack, architecture style, key decisions (infer from code)
   - **§2 Component Architecture**: module tree, responsibilities, file paths (from scan)
   - **§3 API Integration**: endpoints, auth, error handling (from HTTP client code)
   - **§4 State Management**: state shape, transitions (from state code)
   - **§5 Configuration**: env vars, feature flags (from config/env files)
   - **§6 Error Handling**: error scenarios, fallbacks (from try/catch patterns)
   - **§7 Testing Strategy**: test files found, coverage gaps
   - **§8 Deployment**: build commands (from package.json/Makefile), deploy target
   - **§9 Invariant Compliance**: map spec.yaml invariants to code locations
   - **§10 Reproduction Instructions**: setup, build, run, verify steps
   - **§11 Known Limitations**: tech debt, TODOs found in code, missing error handling
   - **§12 Changelog**: single entry "Captured retroactively from existing implementation"
   
   **Quality bar**: Someone reading this document should be able to understand, maintain,
   or reproduce the implementation without reading the source code first.

4. **Update domain artifacts**:
   Based on the code scan, update domain files if the implementation reveals new information:
   
   **specs/domain/entities.yaml**:
   - If the implementation introduces new entities not in the registry, suggest adding them
   - Show the user: "I found these entities in your code that aren't in the registry: ..."
   - Ask permission before modifying
   
   **specs/domain/contexts.yaml**:
   - If the implementation touches bounded contexts not yet registered, suggest adding them
   
   **spec.yaml → traceability**:
   - Update endpoints, tables, modules, events with actual values from the code scan

5. **Gap analysis**:
   Compare the implementation against the spec artifacts:
   
   **If discovery-spec.md exists**:
   - Are all assumptions addressed in the implementation?
   - Are kill criteria measurable with the current instrumentation?
   - Are invariant conflict resolutions actually implemented?
   
   **If domain-contract.md exists**:
   - Are all invariants enforced in code? (fill §9 of implementation-spec.md)
   - Are all state machine transitions implemented?
   - Are fitness functions written?
   
   **If neither exists** (greenfield capture):
   - Suggest which spec artifacts should be created
   - Offer to run `/evospec.discover` to create discovery-spec.md retroactively
   
   Report gaps clearly:
   ```
   ⚠ Gap Analysis:
   - INV-001: enforced ✓ (src/guards/order.ts:42)
   - INV-002: NOT enforced ✗ — no code found that validates this
   - Assumption A001: no metrics instrumented to test this
   ```

6. **Report**:
   - List all files created or updated
   - Show implementation coverage (% of spec covered by code)
   - Show invariant compliance (% of invariants enforced)
   - Show domain registry updates (new entities/contexts added)
   - Suggest next steps:
     - If gaps found: "Fix the gaps, then run `/evospec.check` to validate"
     - If experiment: "Record what you learned with `/evospec.learn`"
     - If ready for production: "Run `/evospec.tasks` to plan remaining work"

**Rules**: ALWAYS read the actual source code — do NOT ask the user to describe their implementation Generate ALL content — the user should not have to write docs manually Be honest about gaps — if invariants aren't enforced, say so clearly
- Ask permission before modifying domain files (entities.yaml, contexts.yaml)
- Do NOT modify the source code — this workflow only creates/updates spec artifacts
- If no spec directory exists, create one and generate spec.yaml from the implementation
- Include file:line references in invariant compliance mapping
- The implementation-spec.md must be detailed enough for someone to reproduce the build

## Procedure: Check

Equivalent to Windsurf `/evospec.check`.

1. **Find specs**:
   - Check `evospec.yaml` exists.
   - If user input specifies a path, validate that spec only.
   - Otherwise, validate ALL specs in `specs/changes/`.

2. **Run checks for each spec**:
   ### A. Schema Validation
   - Validate `spec.yaml` against the JSON Schema (`schemas/spec.schema.json`)
   - Report any schema violations
   
   ### B. Zone-Specific Checks
   
   **Edge Zone**:
   - [ ] `discovery-spec.md` exists
   - [ ] `discovery.outcome` is set in spec.yaml
   - [ ] `discovery.kill_criteria` is set
   - [ ] At least 1 assumption listed
   - [ ] Problem statement is human-centered (not business-centered)
   
   **Hybrid Zone**:
   - [ ] `discovery-spec.md` exists
   - [ ] `domain-contract.md` exists
   - [ ] At least 1 invariant defined (even if minimal)
   - [ ] Boundary between discovery and core is documented
   
   **Core Zone**:
   - [ ] `domain-contract.md` exists
   - [ ] `bounded_context` is set in spec.yaml
   - [ ] At least 1 invariant with enforcement mechanism
   - [ ] At least 1 fitness function defined
   - [ ] Every invariant has an enforcement type (test/ci-check/schema/policy)
   - [ ] Every fitness function references an implementation path
   - [ ] State transitions have forbidden transitions documented
   - [ ] Authorization rules are defined
   - [ ] Backwards compatibility/migration strategy documented
   
   ### C. Cross-Artifact Consistency
   - Invariants in `spec.yaml` match those in `domain-contract.md`
   - Fitness functions in `spec.yaml` match those in `domain-contract.md`
   - Entities in `domain-contract.md` match `traceability.tables` in `spec.yaml`
   - Endpoints in `domain-contract.md` match `traceability.endpoints`
   - Ubiquitous language terms match `specs/domain/glossary.md`
   
   ### D. Entity Registry Validation
   - `entities_touched` references valid entities from `evospec.yaml` `domain.entities`
   - `contexts_touched` references valid contexts from `bounded_contexts`
   - `traceability.tables` references valid tables from entity registry
   
   ### E. Cross-Spec Invariant Impact
   - Edge/hybrid specs touching core entities have declared conflicts
   - Undeclared potential conflicts are flagged as warnings
   
   ### F. Cross-Spec Endpoint Traceability
   - Edge/hybrid spec endpoints trace to core spec endpoints
   
   ### G. Knowledge Funnel Position Check
   - Edge specs should NOT have rigid invariants (Mystery territory)
   - Core specs should NOT have unresolved hypotheses (Algorithm territory)
   - Hybrid specs should have both discovery and contract elements
   
   ### H. Team Topology Check
   - `ownership.team` is set
   - If `crosses_context_boundary` is true, interaction_mode should be documented
   - Owning team type matches the zone
   
   ### I. Tasks Coverage (if tasks.md exists)
   - Every invariant has at least one corresponding task
   - Every fitness function has an implementation task
   - No orphan tasks (tasks that don't trace to spec requirements)
   
   ### J. ADR Check
   - If significant decisions exist in domain-contract.md, corresponding ADRs should exist
   - ADRs referenced in spec.yaml should exist on disk

3. **Classify severity**:
   - **ERROR**: Missing required artifact for zone, invariant without enforcement, core without fitness functions
   - **WARNING**: Missing optional fields, incomplete classification, no team ownership
   - **INFO**: Suggestions for improvement, missing optional sections

4. **Report**:
   Display results as a table:
   ```
   | Check | Status | Details |
   |-------|--------|---------|
   | Schema validation | ✓ PASS | |
   | Zone requirements | ✗ FAIL | Missing domain-contract.md |
   | Invariant coverage | ⚠ WARN | INV-002 has no fitness function |
   ```
   
   Summary:
   ```
   Checked: [N] spec(s)
   Errors: [N]
   Warnings: [N]
   
   Overall: PASS / FAIL
   ```

5. **Next Actions**:
   - If errors: list specific fixes needed before implementation
   - If warnings only: user may proceed, but suggest improvements
   - If all pass: "Specs are valid. Ready for the Implement workflow."

**Rules**: STRICTLY READ-ONLY — do NOT modify any files Report findings accurately — do not hallucinate missing sections Prioritize errors over warnings over info
- For core zone: treat missing fitness functions as ERRORS, not warnings
- Constitution/invariant violations are always ERRORS

## Procedure: Contract

Equivalent to Windsurf `/evospec.contract`.

1. **Find the spec directory**:
   - Check if `evospec.yaml` exists. If not, instruct user to run `evospec init`.
   - If user input contains a spec path, use it.
   - Otherwise, list available specs and let the user choose.
   - Read the existing `spec.yaml` to understand the change context.

2. **Load project context**:
   - Read `evospec.yaml` for bounded contexts registry, team topology, strategy
   - Read `specs/domain/glossary.md` for ubiquitous language
   - Read `specs/domain/context-map.md` for bounded context relationships
   - If a `discovery-spec.md` exists for this change, read it for context

3. **Reverse-engineer if possible**:
   - Ask: "Should I scan existing code to pre-populate the domain contract?"
   - If yes, scan for:
     - Database models/tables (SQLAlchemy, Django, etc.)
     - API endpoints (FastAPI, Django, Express, etc.)
     - Existing validation rules and business logic
   - Use findings as a starting point for the contract

4. **Generate domain-contract.md**:
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

5. **Update spec.yaml**:
   - Set `bounded_context` field
   - Add invariants array with enforcement mechanisms
   - Add fitness_functions array
   - Update traceability with discovered endpoints/tables/modules
   - If zone was "edge", suggest upgrading to "hybrid" or "core"

6. **Update domain glossary**:
   - If new ubiquitous language terms were defined, append to `specs/domain/glossary.md`

7. **Suggest ADRs**:
   - If significant architectural decisions were made during contract creation, suggest creating ADRs
   - Example: "Consider creating an ADR for: 'Use event sourcing for order state transitions'"

8. **Report**:
   - Print created/updated files
   - List invariants defined and their enforcement status
   - List fitness functions needed
   - Suggest next steps:
     - "Run `/evospec.tasks` to generate implementation tasks"
     - "Run `/evospec.check` to validate the spec"

**Rules**: Invariants are non-negotiable — do not skip or soften them Every invariant needs enforcement — text alone is not a guardrail Use existing ubiquitous language from the glossary
- Core zone MUST have: bounded_context, invariants, fitness_functions in spec.yaml
- Keep contracts focused — one bounded context per contract
- If the user hasn't done discovery yet, suggest running `/evospec.discover` first

## Procedure: Discover

Equivalent to Windsurf `/evospec.discover`.

1. **Find or create the spec directory**:
   - Check if `evospec.yaml` exists in the project root. If not, instruct user to run `evospec init`.
   - Parse the user's feature description.
   - Generate a slug from the description (lowercase, hyphens, 2-5 words).
   - Create directory: `specs/changes/YYYY-MM-DD-<slug>/`

2. **Classify the change**:
   Ask these questions to determine the zone:
   - Does this change alter database schema or persistent state? (→ core signal)
   - Does this change affect authentication, authorization, or identity? (→ core signal)
   - Does this change affect billing, plans, or subscriptions? (→ core signal)
   - Does this change affect tenant isolation? (→ core signal)
   - Is this driven by a hypothesis that needs validation? (→ edge signal)
   - How hard is it to undo? (trivial/moderate/difficult/irreversible)
   
   **Auto-classification**:
   - 0 core signals + hypothesis = **edge**
   - 1 core signal or crosses context boundary = **hybrid**
   - 2+ core signals or irreversible = **core**
   
   Let the user override if they disagree.

3. **Explore and model the domain (interactive)**:
   Before writing any spec files, help the user understand what they're building.
   This step is **conversational** — ask questions, suggest structures, iterate.
   
   **Entity Modeling**:
   - Ask: "What are the main things (entities) in your system?"
   - Suggest entity names, fields, and relationships based on the user's description
   - Show a simple entity diagram or table:
     ```
     Entity: Cart
     Fields: items[], total, status
     Relationships: Cart → Product (references), Cart → Order (creates)
     ```
   - Ask: "Does this look right? What's missing?"
   - Check `specs/domain/entities.yaml` — if entities already exist, show them
   - If upstream repos exist, show their entities too (helps UX teams understand backend domains)
   
   **Bounded Context Mapping**:
   - Ask: "Which team/system owns this? Does it cross into other teams' territory?"
   - If it touches entities from upstream repos, flag the boundary
   - Show the context map if it exists (`specs/domain/context-map.md`)
   
   **Design Exploration**:
   - Ask: "How confident are you about the solution? (1-10)"
     - 1-3: "Let's explore more. Here are 3-4 different approaches..."
     - 4-6: "You have a direction. Let's refine it and test assumptions."
     - 7-10: "You seem confident. Consider `/evospec.improve` for a faster path."
   - For each approach, briefly sketch: components needed, APIs consumed, state shape
   - Help the user pick an approach or combine ideas
   
   **This step can loop** — the user may want to explore multiple times before committing.
   When the user says something like "ok let's go with this" or "I'm ready", proceed to step 4.

4. **Generate spec.yaml**:
   - Use the classification answers and domain exploration to populate `spec.yaml`
   - Fill in: id, title, zone, status (draft), created_at, classification fields
   - For edge/hybrid: populate discovery section with outcome, opportunity, assumptions
   - Include entities_touched and contexts_touched from the modeling conversation

5. **Generate discovery-spec.md**:
   Follow the template structure. For each section, use the user's feature description + Design Thinking to generate content:
   
   **Section 1 — Strategic Fit** (Roger Martin):
   - Connect the feature to winning aspiration, where to play, how to win
   - If `evospec.yaml` has strategy context, use it
   
   **Section 2 — Outcome & Opportunity** (Teresa Torres):
   - Frame as Opportunity Solution Tree: Outcome → Opportunities → Solutions
   - Identify the product outcome metric this change aims to influence
   - Use "How Might We" framing for the opportunity
   
   **Section 3 — Empathy & Research** (Design Thinking — Empathize):
   - List what research has been done or should be done
   - Generate a research checklist
   
   **Section 4 — Problem Definition** (Design Thinking — Define):
   - Write a human-centered problem statement (NOT business-centered)
   - Generate 2 alternative reframes
   
   **Section 5 — Ideation** (Design Thinking — Ideate):
   - Generate 3-4 solution ideas with feasibility/impact assessment
   - Mark the selected approach
   
   **Section 6 — Assumptions & Experiments** (Teresa Torres):
   - List the riskiest assumptions (ordered by risk)
   - For each, suggest a test method
   - Use "What would have to be true" framing (Roger Martin)
   
   **Section 7 — Prototype & Test Plan** (Design Thinking — Prototype + Test):
   - Suggest prototype type and test plan
   
   **Section 8 — Kill Criteria**:
   - Write specific, measurable criteria for when to abandon
   
   **Section 9 — Organizational Risk** (Hogan):
   - Identify potential derailers based on feature type
   
   **Section 10 — Domain Boundaries**:
   - List bounded contexts and entities this touches
   - If it touches core entities, flag that a domain-contract.md is needed

6. **Check invariant impact** (CRITICAL):
   Before proceeding, check which core invariants this change may conflict with.
   - Read all existing core/hybrid specs and collect their invariants.
   - Compare against the entities and bounded contexts this change touches (from Section 10).
   - If MCP is available, call `check_invariant_impact(entities=[...], contexts=[...], description="...")`.
   - Otherwise, manually scan `specs/changes/*/spec.yaml` for invariants that mention the same entities.
   
   If **conflicts are found**, display them prominently:
   ```
   ⚠ INVARIANT CONFLICTS DETECTED
   
   INV-001: "Every Order must have at least one LineItem"
     Source: specs/changes/2025-06-01-order-rules/spec.yaml
     Enforced by: tests/fitness/test_order_integrity.py
     Why it conflicts: touches entity 'order', same bounded context 'orders'
   
   Resolution options:
     1. exempt    — Experiment behind a feature flag, don't change the schema
     2. evolve    — Propose INV-001-v2 with a migration path
     3. shadow    — Validate need via interviews/analytics BEFORE touching schema
     4. redesign  — Change approach to avoid the conflict
   ```
   
   The user MUST choose a resolution for each conflict. Record it in `spec.yaml → invariant_impact.conflicts[]`.
   
   If **no conflicts**, display: `✓ No invariant conflicts — safe to experiment.`

7. **Generate domain-contract.md (if hybrid/core)**:
   - For hybrid: only Sections 1 (Context), 3 (Entities), 4 (Invariants), 7 (Authorization)
   - For core: full domain-contract.md (recommend running `/evospec.contract` for thorough generation)

8. **Report**:
   - Print the created files and their paths
   - Show the zone classification and risk level
   - Show invariant impact summary (conflicts found or safe)
   - Suggest next steps based on user's confidence and zone:
   
     **Edge + experimental (user exploring)**:
     - "Start building your prototype! When you're happy with what you've built, run `/evospec.capture` to formalize the implementation spec and domain artifacts."
   
     **Edge + confident (user knows what they want)**:
     - "Ready to implement. Run `/evospec.tasks` to generate the task list, or `/evospec.improve` for a faster path."
   
     **Edge + invariant conflicts**:
     - "Resolve invariant conflicts first. Consider `/evospec.improve` if this is a known need."
   
     **Hybrid**:
     - "Review the domain contract. Run `/evospec.contract` for a thorough contract."
   
     **Core**:
     - "This needs a full domain contract. Run `/evospec.contract`."

**Rules**: YOU (the AI) generate ALL content — the user provides a short description, you produce the full spec Do NOT leave empty sections or placeholder comments. Make informed guesses for everything. NEVER include implementation details (languages, frameworks, APIs) in the discovery spec — EXCEPT during entity modeling (step 3) where technical context helps the user think
- Focus on WHAT users need and WHY, not HOW
- Maximum 3 [NEEDS CLARIFICATION] markers — make informed guesses for everything else
- Use the project's evospec.yaml strategy context if available
- Keep it concise — one page per section is the target
- The domain exploration step (step 3) is INTERACTIVE — ask questions, wait for answers, iterate
- Read specs/domain/entities.yaml and upstream entities to help the user understand existing domain
- Adapt the depth of exploration to the user's confidence level — don't over-specify for someone who just wants to experiment

## Procedure: Fix

Equivalent to Windsurf `/evospec.fix`.

1. **Create the bugfix spec directory**:
   - Check if `evospec.yaml` exists.
   - Parse the bug description from user input.
   - Create directory: `specs/changes/YYYY-MM-DD-fix-<slug>/`

2. **Root Cause Analysis**:
   Investigate the bug systematically (before touching code):
   - **Reproduce**: Can we reproduce it? What are the exact steps?
   - **Locate**: Where in the codebase does the failure occur?
   - **Root cause**: What is the actual cause? (Not the symptom)
   - **Upstream vs downstream**: Is this the root, or a symptom of a deeper issue?
   
   Use `evospec reverse` or read the codebase to trace the issue.

3. **Check invariant impact** (CRITICAL):
   - Which entities and bounded contexts does this bug touch?
   - Read existing invariants to understand:
     a. Does an invariant already cover this case? (If yes, why did it fail?)
     b. Is there a missing invariant that should have caught this?
   - If MCP is available, call `check_invariant_impact(entities=[...], contexts=[...], description="...")`.
   
   This step answers a critical question: **Is this a bug in the code, or a gap in the spec?**
   - **Bug in code**: Invariant exists, code doesn't implement it correctly → fix the code
   - **Gap in spec**: No invariant covers this case → fix the code AND add the invariant + fitness function

4. **Generate spec.yaml**:
   - Set `change_type: "bugfix"`
   - Set `classification.is_hypothesis: false`
   - Set `classification.risk_level` based on severity
   - Skip the `discovery` section
   - Fill in `invariant_impact` with any related invariants

5. **Generate bugfix-report.md**:
   Create a structured bug report in the spec directory.
   **YOU (the AI) must fill in every section** based on the user's bug description, the root cause analysis (step 2), and the invariant check (step 3).
   Do NOT leave HTML comment placeholders — generate real content from your investigation.
   
   Sections to generate:
   - **Bug Description**: What is happening vs. what should happen (from user input + codebase investigation)
   - **Reproduction Steps**: Exact steps to reproduce (from your root cause analysis)
   - **Root Cause**: The actual cause, not the symptom (from step 2)
   - **Affected Invariants**: Which invariants are violated or missing (from step 3). State whether it's a code bug or a spec gap.
   - **Fix Strategy**: The minimal upstream fix. Prefer single-line changes. Reference exact file paths.
   - **Regression Test**: Exact test file path, what it tests, expected outcome.
   - **Not In Scope**: What is explicitly NOT being fixed in this change.

6. **Generate tasks**:
   Every bugfix should have at minimum these tasks:
   
   ```markdown
   ## Phase 1: Diagnose
   - [ ] T001 [Phase 1] Reproduce the bug with a failing test
   - [ ] T002 [Phase 1] Identify root cause (not symptom)
   
   ## Phase 2: Fix
   - [ ] T003 [Phase 2] Implement minimal upstream fix
   - [ ] T004 [Phase 2] Verify existing fitness functions still pass
   
   ## Phase 3: Harden
   - [ ] T005 [Phase 3] Add regression test
   - [ ] T006 [Phase 3] Add/update invariant if this was a spec gap
   - [ ] T007 [Phase 3] Update fitness function if needed
   ```

7. **Report**:
   ```
   Bugfix: [title]
   Zone: [zone] | Severity: [severity]
   Root cause: [one-line summary]
   Related invariants: [N existing / M to add]
   
   Created:
     specs/changes/YYYY-MM-DD-fix-slug/spec.yaml
     specs/changes/YYYY-MM-DD-fix-slug/bugfix-report.md
     specs/changes/YYYY-MM-DD-fix-slug/tasks.md
   
   Next: Start with T001 (write a failing test). Run `/evospec.implement` to execute.
   ```

**Rules**: NEVER create a discovery-spec.md for bug fixes ALWAYS start with reproduction — if you can't reproduce it, you can't fix it ALWAYS add a regression test — this is non-negotiable
- If the bug reveals a missing invariant, add it to the domain-contract.md
- If the fix is trivial (typo, config error), still create the spec but keep it minimal
- If the 'bug' is actually a feature request in disguise, redirect to `/evospec.discover` or `/evospec.improve`

## Procedure: Implement

Equivalent to Windsurf `/evospec.implement`.

1. **Find the spec directory**:
   - Check `evospec.yaml` exists. If not: instruct user to run `evospec init`.
   - If user input contains a spec path, use it.
   - Otherwise, list available specs and let user choose.
   - Read `tasks.md`. If it doesn't exist, instruct user to run the Tasks workflow.

2. **Load implementation context**:
   - Read `spec.yaml` for zone, classification, invariants, fitness functions
   - Read `tasks.md` for the complete task list and execution plan
   - Read `domain-contract.md` if it exists (for core/hybrid: entity definitions, state machines)
   - Read `discovery-spec.md` if it exists (for edge/hybrid: solution approach)
   - Read `implementation-spec.md` if it exists (skeleton from Tasks workflow)
   - Read `evospec.yaml` for project-level configuration

3. **Pre-flight checks**:
   - Count total tasks, completed tasks, remaining tasks
   - Identify current phase (first phase with incomplete tasks)
   - Check for blocking dependencies
   
   Display status:
   ```
   Spec: [title] (zone: [zone])
   Progress: [completed]/[total] tasks
   Current Phase: [phase name]
   Remaining: [count] tasks
   ```

4. **Execute tasks phase by phase**:
   For each phase (in order):
   a. Display phase name and task count
   b. For sequential tasks: execute one at a time, verify before proceeding
   c. For parallel tasks [P]: execute all parallel tasks in the phase
   d. After each task completion, mark as `[X]` in tasks.md
   e. After each phase, run a verification checkpoint
   
   **Execution rules by zone**:
   
   ### Edge Zone
   - Move fast — minimal verification between tasks
   - Prototype quality is acceptable (can be rough)
   - Focus on getting something testable in front of users
   - Skip polish tasks if prototype validates the hypothesis
   
   ### Core Zone
   - **Fitness functions FIRST**: implement test tasks before implementation tasks
   - After implementing each entity/service: run related fitness functions
   - If a fitness function fails: STOP and report the failure
   - Do NOT proceed past a failing invariant check
   - Schema migrations must be verified before building on top of them
   
   ### Hybrid Zone
   - Core-touching tasks follow Core rules (strict, TDD)
   - Edge-touching tasks follow Edge rules (fast, prototype)
   - Contract tests at boundaries must pass before integration

5. **Progress tracking + implementation-spec updates**:
   - After each completed task, update `tasks.md` with `[X]`
   - Report progress after each phase:
     ```
     Phase [N] complete: [completed]/[phase_total] tasks
     Remaining: [total_remaining] tasks across [phases_remaining] phases
     ```
   - If a task fails: report the error, suggest fix, ask user how to proceed
   
   **If implementation-spec.md exists**, update it after each phase:
   - §2 Component Architecture: add new components/modules created in this phase
   - §3 API Integration: update endpoints used, error handling decisions
   - §4 State Management: update state shape if it changed
   - §9 Invariant Compliance: fill in File:Line references for enforced invariants
   - §12 Changelog: add entry for the completed phase
   
   **If implementation-spec.md does NOT exist**, skip this — the user can create it
   later via `/evospec.capture` when they're ready to formalize.

6. **Post-implementation**:
   - Update `spec.yaml` traceability with actual file paths created
   - Update spec status to "in-progress" or "completed"
   - If core zone: verify all fitness functions pass
   - Suggest running the Check workflow for full validation
   
   **If implementation-spec.md exists**, finalize it:
   - §1 Overview: verify tech stack table is complete, update status
   - §5 Configuration: fill in all env vars and feature flags used
   - §6 Error Handling: document all error scenarios discovered during implementation
   - §7 Testing Strategy: list actual test files created
   - §8 Deployment: fill in build commands and deploy target
   - §10 Reproduction Instructions: verify setup/build/run/verify steps work
   - §11 Known Limitations: document any tech debt or gaps
   - §12 Changelog: add final entry
   The implementation-spec.md should now be a **complete as-built blueprint**.
   
   **If implementation-spec.md does NOT exist**, suggest:
   - "Run `/evospec.capture` to create an implementation spec from what was just built."

7. **Report**:
   - Summary of completed tasks
   - Any tasks that were skipped or failed
   - Fitness function results (for core/hybrid)
   - Next steps:
     - If all tasks done: "Run the Check workflow to validate"
     - If tasks remain: "Continue with the Implement workflow to resume"

**Rules**: NEVER skip fitness function tasks in core zone ALWAYS mark completed tasks as [X] in tasks.md ALWAYS run fitness functions after core entity implementation
- Report progress after every phase
- If tasks.md doesn't exist, do NOT improvise — instruct user to run the Tasks workflow
- For core zone, treat failing fitness functions as blocking errors

## Procedure: Improve

Equivalent to Windsurf `/evospec.improve`.

1. **Find or create the spec directory**:
   - Check if `evospec.yaml` exists. If not, instruct user to run `evospec init`.
   - Parse the improvement description from user input.
   - Generate a slug from the description.
   - Create directory: `specs/changes/YYYY-MM-DD-<slug>/`

2. **Classify the change**:
   Ask classification questions to determine the zone (edge/hybrid/core).
   Set `change_type: "improvement"` and `classification.is_hypothesis: false` in spec.yaml.
   
   For improvements, the zone still matters:
   - **edge improvement**: UI polish, copy changes, feature flags → minimal spec
   - **hybrid improvement**: New endpoint, schema addition → needs invariant check
   - **core improvement**: Schema migration, auth change → needs full contract + fitness functions

3. **Check invariant impact** (CRITICAL):
   - Identify which entities and bounded contexts this improvement touches.
   - Read all core/hybrid specs and collect their invariants.
   - If MCP is available, call `check_invariant_impact(entities=[...], contexts=[...], description="...")`.
   
   If **conflicts are found**:
   ```
   ⚠ INVARIANT CONFLICTS DETECTED
   
   INV-001: "Every Order must have at least one LineItem"
     This improvement may affect this invariant.
   
   For an improvement (not an experiment), you should:
     1. evolve  — Update the invariant and its fitness function together
     2. verify  — Ensure the improvement doesn't violate the invariant (run fitness functions)
   ```
   
   For improvements, the typical resolution is `evolve` (update invariant + fitness function in the same PR) or `verify` (run fitness functions to confirm no violation).
   
   If **no conflicts**: `✓ No invariant conflicts.`

4. **Generate spec.yaml**:
   - Set `change_type: "improvement"`
   - Set `classification.is_hypothesis: false`
   - Skip the `discovery` section (leave defaults)
   - Fill in `invariant_impact` with any conflicts found
   - For core: require invariants and fitness_functions sections

5. **Generate improvement-scope.md**:
   Create a concise `improvement-scope.md` in the spec directory.
   **YOU (the AI) must fill in every section** based on the user's description and project context.
   Do NOT leave HTML comment placeholders — generate real content.
   
   Structure:
   - **What**: One paragraph summarizing the change (infer from user description + codebase)
   - **Why**: One paragraph explaining why it's needed now (infer from context)
   - **Scope**: Specific components/areas affected (list exact files/modules if possible)
   - **Invariant Impact**: Auto-populated from the invariant check in step 3
   - **Acceptance Criteria**: Concrete, testable criteria (generate from the user's description)
   - **Risks**: What could go wrong (infer from zone, invariant conflicts, reversibility)
   - **Not In Scope**: What is explicitly excluded (infer boundaries from the description)

6. **Generate domain-contract.md (if hybrid/core)**:
   - For existing contracts: show what sections need updating
   - For new contracts: generate minimal contract with focus on invariants and fitness functions

7. **Auto-generate tasks**:
   Improvements go straight to tasks:
   - Call the tasks workflow or generate tasks.md directly
   - For core: include tasks for updating fitness functions
   - For hybrid: include tasks for integration tests

8. **Report**:
   ```
   Improvement: [title]
   Zone: [zone] | Type: improvement
   Invariant impact: [N conflicts / safe]
   
   Created:
     specs/changes/YYYY-MM-DD-slug/spec.yaml
     specs/changes/YYYY-MM-DD-slug/improvement-scope.md
     specs/changes/YYYY-MM-DD-slug/tasks.md
   
   Next: Review tasks and start implementing. Run `/evospec.implement` to execute.
   ```

**Rules**: NEVER create a discovery-spec.md for improvements — that's for experiments ALWAYS run invariant impact check — even for 'simple' improvements For core improvements: require fitness function updates in the tasks
- Keep the scope document SHORT — this is not a discovery spec
- If the user describes something that sounds like a hypothesis, suggest `/evospec.discover` instead
- If the user describes a bug, suggest `/evospec.fix` instead

## Procedure: Learn

Equivalent to Windsurf `/evospec.learn`.

1. **Find the spec**:
   - Check `evospec.yaml` exists.
   - If user input contains a spec path, use it.
   - Otherwise, list edge/hybrid specs and let user choose.
   - Read `spec.yaml` and `discovery-spec.md`.

2. **Identify what was tested**:
   - Show current assumptions from `spec.yaml` with their status.
   - Ask: "Which assumption(s) were tested?" (reference by ID, e.g., A-001)
   - If user input contains experiment results, extract them.

3. **Record the experiment**:
   Add to `discovery.experiments[]` in spec.yaml:
   - Generate next experiment ID (EXP-001, EXP-002, ...)
   - Capture:
     - `assumption_id`: which assumption was tested
     - `type`: prototype | interview | survey | A-B-test | wizard-of-oz | analytics | spike
     - `description`: what was done
     - `sample_size`: how many users/data points
     - `started_at` / `completed_at`: dates
     - `result`: qualitative or quantitative outcome
     - `confidence`: high | medium | low
   - Add the experiment to the experiments table in `discovery-spec.md`

4. **Update assumption status**:
   Based on the result and confidence, update the assumption:
   
   | Result + Confidence | New Status | Action |
   |-------------------|------------|--------|
   | Positive + high | `validated` | Consider promoting to core |
   | Positive + medium | `testing` | Design follow-up experiment |
   | Positive + low | `testing` | Need more data |
   | Negative + high | `invalidated` | Pivot or kill |
   | Negative + medium | `testing` | Re-examine test design |
   | Ambiguous | `testing` | Redesign experiment |
   
   Update the assumption in both `spec.yaml` and `discovery-spec.md`.

5. **Decide next step** (CRITICAL):
   Ask the user (or infer from results):
   
   ### Continue
   - Need more data on this assumption
   - Design the next experiment
   - Keep current iteration
   
   ### Pivot
   - Assumption invalidated, but opportunity is still valid
   - Update `assumption.pivot_to` with new direction
   - Increment `discovery.iteration` in spec.yaml
   - Add a pivot entry to the Pivots table in discovery-spec.md
   - May need to update problem statement and ideation sections
   
   ### Kill
   - Kill criteria met, or opportunity is not worth pursuing
   - Set feature status to `killed` in evospec.yaml
   - Record kill reason
   - Update spec.yaml status to `abandoned`
   
   ### Promote to Core
   - Assumption validated with high confidence
   - This pattern should become an invariant
   - Add to "Promotion Candidates" table in discovery-spec.md
   - Suggest running the Contract workflow to create a domain contract
   - Update feature knowledge_stage from `mystery` to `heuristic` or `algorithm`

6. **Log the learning**:
   Add to `discovery.learnings[]` in spec.yaml:
   - `date`: today
   - `iteration`: current iteration number
   - `experiment_id`: the experiment just recorded
   - `learning`: one-sentence summary of what was learned
   - `impact`: how this changes the spec or approach
   - `spec_changed`: true if the discovery-spec.md was modified
   
   Also update the Learning Log section in `discovery-spec.md`.

7. **Update discovery status**:
   - Recalculate: how many assumptions tested vs. total?
   - Set `discovery.next_checkpoint` to next cadence date
   - If all high-risk assumptions validated → suggest moving to the Tasks workflow
   - If most assumptions invalidated → suggest pivoting or killing

8. **Report**:
   Display a discovery dashboard:
   ```
   Spec: [title] (iteration [N])
   
   Assumptions:
     A-001: validated ✓ (desirability)
     A-002: testing ⟳ (feasibility)
     A-003: untested ○ (viability)
   
   Experiments: [completed]/[total]
   Last learning: "[summary]"
   Next checkpoint: [date]
   
   Decision: [continue/pivot/kill/promote]
   ```
   
   Suggest next action:
   - If continue: "Design next experiment for A-002"
   - If pivot: "Updated iteration to [N+1]. Review updated discovery-spec.md"
   - If kill: "Feature killed. Reason: [reason]"
   - If promote: "Run the Contract workflow to codify [assumption] as an invariant"

**Rules**: ALWAYS update both spec.yaml AND discovery-spec.md — they must stay in sync ALWAYS log a learning — even if the result is 'we learned nothing' NEVER skip the decision step — every experiment must lead to: continue, pivot, kill, or promote
- Pivots increment iteration — this is how we track how many times we've changed direction
- Promotions create contracts — when an assumption becomes an algorithm, it needs a domain-contract.md
- If an assumption has been testing for more than 3 experiments without resolution, flag it
- If kill deadline has passed, force a kill/continue decision

## Procedure: Tasks

Equivalent to Windsurf `/evospec.tasks`.

1. **Find the spec directory**:
   - Check `evospec.yaml` exists. If not: instruct user to run `evospec init`.
   - If user input contains a spec path, use it.
   - Otherwise, list available specs and let user choose.
   - Read `spec.yaml`, `discovery-spec.md`, `domain-contract.md` (whichever exist).

2. **Load implementation context**:
   - From `spec.yaml`: zone, classification, invariants, fitness_functions, traceability
   - From `discovery-spec.md`: selected solution approach, prototype plan
   - From `domain-contract.md`: entities, state machines, authorization rules, events
   - From `evospec.yaml`: project tech stack, team topology, bounded contexts

3. **Determine task generation strategy by zone**:
   ### Edge Zone (Discovery Layer)
   - Focus on **prototyping speed** and **learning instrumentation**
   - Phase structure:
     1. Setup: feature flag, experiment infrastructure
     2. Prototype: minimal UI/API to test hypothesis
     3. Instrumentation: metrics, analytics, A/B test setup
     4. Validation: smoke tests, user test scripts
   - Mark most tasks as [P] (parallelizable) — edge work is loosely coupled
   
   ### Hybrid Zone
   - Focus on **boundary protection** while allowing iteration
   - Phase structure:
     1. Setup: dependencies, configuration
     2. Foundation: schema migrations, base models (from domain contract)
     3. Contract Tests: boundary tests between discovery and core
     4. Core Implementation: entities, services matching domain contract
     5. Edge Implementation: UX, experimental features
     6. Guardrails: fitness functions for invariants
   - Sequential for core tasks, parallel for edge tasks
   
   ### Core Zone (Core Engine)
   - Focus on **correctness, invariants, and fitness functions**
   - Phase structure:
     1. Setup: dependencies, configuration
     2. Foundation: schema migrations, base models
     3. Fitness Functions: write tests FIRST (TDD for core)
     4. Core Implementation: entities, aggregates, services
     5. Authorization: role checks, tenant isolation
     6. Integration: wire endpoints, middleware
     7. Guardrails: run all fitness functions, contract tests
     8. Polish: logging, error handling, documentation
   - Strictly sequential — core changes must be verified at each step

4. **Generate tasks.md**:
   Use the tasks template. For each task:
   
   **Task Format** (REQUIRED):
   ```
   - [ ] T001 [P] [Phase] Description with exact file path
   ```
   
   **Format Rules**:
   - `- [ ]`: Checkbox (mark `[X]` when complete)
   - `T001`: Sequential task ID
   - `[P]`: Only if parallelizable (different files, no dependency on incomplete tasks)
   - `[Phase]`: Phase label (Setup, Foundation, Core, Integration, Guardrails, Polish)
   - Description: Clear action verb + exact file path
   
   **Task Quality Rules**:
   - Every task must reference an exact file path
   - Every task must be completable by an AI agent without additional context
   - Every task should be independently verifiable
   - Tasks affecting the same file must be sequential (not [P])

5. **Generate invariant-to-task mapping**:
   - Every invariant in spec.yaml must have at least one corresponding task
   - Every fitness function must have a task to implement it
   - Include this mapping in the tasks.md as a traceability section

6. **Generate dependency graph**:
   ```
   Phase 1 → Phase 2 → Phase 3 → ...
   Within phases: T001 → T003 (sequential), T002 || T004 (parallel)
   ```

7. **Report**:
   - Total task count
   - Tasks per phase
   - Parallel opportunities
   - Invariant coverage (% of invariants with tasks)
   - Suggested MVP scope
   - Estimated implementation phases

8. **Create implementation-spec.md skeleton (deliberate mode only)**:
   **Skip this step for edge/experimental specs** — those should use `/evospec.capture`
   after prototyping to formalize retroactively. Don't force documentation before the
   user is ready.
   
   **For core/hybrid specs or when the user is deliberate** (knows what they want):
   Create `implementation-spec.md` in the spec directory with:
   - Overview section: filled from spec.yaml (zone, tech stack from evospec.yaml)
   - Component Architecture: empty table, ready to fill during implementation
   - API Integration: pre-filled from traceability.endpoints in spec.yaml
   - State Management: empty
   - Configuration: pre-filled from known env vars
   - Invariant Compliance: pre-filled table from spec.yaml invariant_impact.conflicts
   - All other sections: skeleton headers only
   - Changelog: first entry "Skeleton created from /evospec.tasks"
   
   Use the `implementation-spec.md` template from `specs/_templates/`.
   
   This document will be updated incrementally during `/evospec.implement`.
   
   **For edge specs**: mention that `/evospec.capture` is available after prototyping.

**Rules**: NEVER generate tasks without reading the spec artifacts first Core zone: fitness function tasks BEFORE implementation tasks (TDD) Edge zone: prototype tasks BEFORE instrumentation tasks
- Every invariant must map to at least one task
- Every task must have an exact file path
- Tasks must be specific enough for an AI agent to execute without asking questions
- Maximum 50 tasks per spec (break into sub-specs if larger)

---

## Working with Specs

### Before implementing ANY change:
- Determine the change type: experiment, improvement, or bugfix
- Run invariant impact check (MCP check_invariant_impact or manual scan)
- Check if a spec exists in specs/changes/
- Read spec.yaml to understand the zone and classification
- Read the appropriate artifact (discovery-spec.md, improvement-scope.md, or bugfix-report.md)
- Read tasks.md if it exists — it's your implementation plan

### When implementing Core zone changes:
- **Invariants are non-negotiable — every invariant in spec.yaml must be enforced**
- **Write fitness functions FIRST (TDD for core)**
- **Check authorization rules in domain-contract.md before implementing endpoints**
- **Respect state machine transitions — forbidden transitions must raise errors**
- **Tenant isolation: every query on tenant-scoped entities must filter by tenant_id**

### When implementing Edge zone changes:
- **Prototype quality is acceptable — focus on validating the hypothesis**
- **Instrument metrics to test assumptions listed in discovery-spec.md**
- **Respect kill criteria — don't over-invest before validation**
- **Keep it reversible — edge changes should be easy to remove**

## Domain Entity Registry

`evospec.yaml` has a `domain.entities` section — specs/domain/entities.yaml is the canonical, machine-readable entity catalog.

Each entity defines: name, context, table, aggregate_root, description, fields (name/type/constraints), relationships (target/type), invariants (IDs)

- MCP resource: `evospec://entities` — returns the full entity registry
- `evospec reverse db` generates copy-pasteable YAML for this section
- evospec check validates entities_touched against registered entities

When creating specs, always check `evospec://entities` to use canonical entity names.

## MCP Server (Programmatic Access)

Start with: `evospec serve`

**Tools** (actions):
- `list_specs() — list all specs with zone, status, artifacts`
- `read_spec(spec_path) — read a spec with all artifacts`
- `check_spec(spec_path?) — run validation checks`
- `classify_change(...) — classify a change into edge/hybrid/core`
- `check_invariant_impact(entities, contexts, description) — safety net`
- `get_tasks(spec_path) — parse tasks.md into structured data`
- `update_task(spec_path, task_id, done) — mark tasks complete`
- `list_features() — list registered features with lifecycle status`
- `get_discovery_status(spec_path) — assumptions, experiments, health, deadlines`
- `record_experiment(spec_path, assumption_id, ...) — log experiment results`
- `update_assumption(spec_path, assumption_id, ...) — update assumption status`
- `run_fitness_functions(spec_path?) — execute fitness function tests`

**Resources** (context):
- `evospec://config — project configuration`
- `evospec://glossary — ubiquitous language`
- `evospec://context-map — bounded context relationships`
- `evospec://invariants — all invariants from core/hybrid specs (the safety net)`
- `evospec://entities — domain entity registry (canonical entity catalog)`

**Prompts** (templates):
- `discover_feature(description) — discovery spec generation prompt`
- `domain_contract(bounded_context) — domain contract generation prompt`

## CLI Commands

```bash
evospec init "project-name"              # Initialize project
evospec new "change title" --zone edge   # Create new spec
evospec check                            # Validate all specs
evospec check --run-fitness              # Validate + execute fitness functions
evospec fitness                          # Run fitness functions independently
evospec reverse api --framework fastapi  # Reverse-engineer API endpoints
evospec reverse db                       # Reverse-engineer DB entities + generate entity registry YAML
evospec reverse cli                      # Reverse-engineer CLI/module structure
evospec reverse deps --source src/       # Detect cross-system API dependencies
evospec feature list                     # List features with lifecycle status
evospec feature add "title"              # Register a new feature
evospec learn                            # Interactive experiment recording
evospec adr new "decision-title"         # Create ADR
evospec render                           # Render all specs into consolidated markdown
evospec serve                            # Start MCP server
evospec generate agents                  # Generate AI agent integration files
```

## Reverse Engineering

- `reverse api — scans source for REST endpoints (FastAPI, Django, Flask, Spring, Express, Next.js, NestJS, Hono, Fastify, Go frameworks)`
- `reverse db — scans for DB models (SQLAlchemy, Django ORM, JPA/Hibernate, GORM, Prisma, TypeORM, Sequelize) + outputs entity registry YAML`
- `reverse cli — scans module/class/function structure across Python, Go, Java, JS/TS`
- `reverse deps — scans source for HTTP calls (fetch, axios, requests, etc.) and maps to known backend endpoints from core/hybrid specs`

## Features Registry

Features in `evospec.yaml` track lifecycle: `discovery → specifying → implementing → validating → shipped / killed`

## Continuous Discovery Loop

```
Hypothesize → Experiment → Learn → Decide → (repeat or promote)
```

Assumption lifecycle: `untested → testing → validated / invalidated / pivoted`

Rules:
- Every assumption has a category: desirability, feasibility, viability, usability
- Every experiment ends with a decision: continue, pivot, kill, promote-to-core
- Pivots increment the iteration counter
- Kill deadlines are enforced
- When all high-risk assumptions resolved → generate tasks

## Knowledge Funnel (Roger Martin)

| Stage | Action | Zone |
|-------|--------|------|
| Mystery | Design Thinking to explore | edge |
| Heuristic | Patterns emerging, judgment needed | hybrid |
| Algorithm | Codified, enforceable, automated | core |

When you encounter ambiguity:
- Mystery → Prototype and learn, don't codify yet
- Heuristic → Document as invariant candidate, test it
- Algorithm → Enforce with a fitness function
