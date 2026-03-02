---
description: Plan and execute a well-known improvement — skip discovery, go straight to tasks. For changes where you already know the solution.
handoffs:
  - label: Generate Tasks
    agent: evospec.tasks
    prompt: Generate implementation tasks from this improvement spec
    send: true
  - label: Check Specs
    agent: evospec.check
    prompt: Validate the spec and run fitness functions
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Context

This workflow is for **well-known improvements** — changes where:
- You already know what needs to be done (knowledge is at the **Algorithm** stage)
- There's no hypothesis to test, no discovery needed
- Examples: refactoring, adding a known feature, performance optimization, UX polish, tech debt

This workflow **skips the Discovery Layer entirely** and goes straight to classification, invariant check, and tasks.

## When to Use This vs Other Workflows

| Situation | Workflow |
|-----------|----------|
| "We want to experiment with X" | `/evospec.discover` |
| "We know we need to do X" | **`/evospec.improve`** ← this one |
| "There's a bug in X" | `/evospec.fix` |

## Outline

1. **Find or create the spec directory**:
- Check if `evospec.yaml` exists. If not, instruct user to run `evospec init`.
- Parse the improvement description from user input.
- Generate a slug from the description.
- Create directory: `specs/changes/YYYY-MM-DD-<slug>/`

2. **Classify the change (interactive)**:
Ask classification questions to determine the zone (edge/hybrid/core).
Set `change_type: "improvement"` and `classification.is_hypothesis: false` in spec.yaml.

For improvements, the zone still matters:
- **edge improvement**: UI polish, copy changes, feature flags → minimal spec
- **hybrid improvement**: New endpoint, schema addition → needs invariant check
- **core improvement**: Schema migration, auth change → needs full contract + fitness functions

3. **Check invariant impact**:
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

## Rules

- NEVER create a discovery-spec.md for improvements — that's for experiments
- ALWAYS run invariant impact check — even for 'simple' improvements
- For core improvements: require fitness function updates in the tasks
- Keep the scope document SHORT — this is not a discovery spec
- If the user describes something that sounds like a hypothesis, suggest `/evospec.discover` instead
- If the user describes a bug, suggest `/evospec.fix` instead
