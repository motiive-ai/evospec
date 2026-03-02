---
name: evospec-discover
description: Create or update a Discovery Spec from a natural language feature description. Uses Design Thinking + Continuous Discovery to explore the Mystery → Heuristic stage. Helps model entities, explore design options, and iterate.
---

# Discover

## Context

This workflow operates in the **Discovery Layer** of EvoSpec. The Discovery Layer is where:
- Knowledge is in the **Mystery → Heuristic** stage (Roger Martin's Knowledge Funnel)
- We use **Design Thinking** (Empathize → Define → Ideate → Prototype → Test) to explore
- We use **Continuous Discovery** (Teresa Torres) to structure learning
- Specs are hypotheses, not contracts
- The goal is **learning**, not shipping

See [references/context.md](references/context.md) for full framework context.

## Steps

1. **Find or create the spec directory**
   - Check if `evospec.yaml` exists in the project root. If not, instruct user to run `evospec init`.
   - Parse the user's feature description.
   - Generate a slug from the description (lowercase, hyphens, 2-5 words).
   - Create directory: `specs/changes/YYYY-MM-DD-<slug>/`

2. **Classify the change *(interactive)***
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

3. **Explore and model the domain (interactive) *(interactive)***
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

4. **Generate spec.yaml**
   - Use the classification answers and domain exploration to populate `spec.yaml`
   - Fill in: id, title, zone, status (draft), created_at, classification fields
   - For edge/hybrid: populate discovery section with outcome, opportunity, assumptions
   - Include entities_touched and contexts_touched from the modeling conversation

5. **Generate discovery-spec.md**
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

6. **Check invariant impact *(CRITICAL)***
   Before proceeding, check which core invariants this change may conflict with.
   - Read all existing core/hybrid specs and collect their invariants.
   - Compare against the entities and bounded contexts this change touches (from Section 10).
   - If MCP is available, call `evospec:check_invariant_impact(entities=[...], contexts=[...], description="...")`.
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

7. **Generate domain-contract.md (if hybrid/core)**
   - For hybrid: only Sections 1 (Context), 3 (Entities), 4 (Invariants), 7 (Authorization)
   - For core: full domain-contract.md (recommend running `/evospec.contract` for thorough generation)

8. **Report**
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

## Rules

- YOU (the AI) generate ALL content — the user provides a short description, you produce the full spec
- Do NOT leave empty sections or placeholder comments. Make informed guesses for everything.
- NEVER include implementation details (languages, frameworks, APIs) in the discovery spec — EXCEPT during entity modeling (step 3) where technical context helps the user think
- Focus on WHAT users need and WHY, not HOW
- Maximum 3 [NEEDS CLARIFICATION] markers — make informed guesses for everything else
- Use the project's evospec.yaml strategy context if available
- Keep it concise — one page per section is the target
- The domain exploration step (step 3) is INTERACTIVE — ask questions, wait for answers, iterate
- Read specs/domain/entities.yaml and upstream entities to help the user understand existing domain
- Adapt the depth of exploration to the user's confidence level — don't over-specify for someone who just wants to experiment

---

*Full framework context: [references/context.md](references/context.md)*
