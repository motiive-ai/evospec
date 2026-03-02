---
name: evospec-fix
description: Diagnose and fix a bug — root cause analysis, invariant check, regression test, minimal fix. No discovery needed.
---

# Fix

## Context

This workflow is for **bug fixes** — changes where:
- Something is broken and needs to be fixed
- Knowledge is at the **Algorithm** stage (we know the correct behavior)
- The fix should be minimal, upstream, and include a regression test
- No discovery, no experimentation — diagnose, fix, verify

See [references/context.md](references/context.md) for full framework context.

## When to Use

| Situation | Workflow |
|-----------|----------|
| "We want to experiment with X" | `/evospec.discover` |
| "We know we need to do X" | `/evospec.improve` |
| "There's a bug in X" | **`/evospec.fix`** ← this one |

## Steps

1. **Create the bugfix spec directory**
   - Check if `evospec.yaml` exists.
   - Parse the bug description from user input.
   - Create directory: `specs/changes/YYYY-MM-DD-fix-<slug>/`

2. **Root Cause Analysis**
   Investigate the bug systematically (before touching code):
   - **Reproduce**: Can we reproduce it? What are the exact steps?
   - **Locate**: Where in the codebase does the failure occur?
   - **Root cause**: What is the actual cause? (Not the symptom)
   - **Upstream vs downstream**: Is this the root, or a symptom of a deeper issue?
   
   Use `evospec reverse` or read the codebase to trace the issue.

3. **Check invariant impact *(CRITICAL)***
   - Which entities and bounded contexts does this bug touch?
   - Read existing invariants to understand:
     a. Does an invariant already cover this case? (If yes, why did it fail?)
     b. Is there a missing invariant that should have caught this?
   - If MCP is available, call `evospec:check_invariant_impact(entities=[...], contexts=[...], description="...")`.
   
   This step answers a critical question: **Is this a bug in the code, or a gap in the spec?**
   - **Bug in code**: Invariant exists, code doesn't implement it correctly → fix the code
   - **Gap in spec**: No invariant covers this case → fix the code AND add the invariant + fitness function

4. **Generate spec.yaml**
   - Set `change_type: "bugfix"`
   - Set `classification.is_hypothesis: false`
   - Set `classification.risk_level` based on severity
   - Skip the `discovery` section
   - Fill in `invariant_impact` with any related invariants

5. **Generate bugfix-report.md**
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

6. **Generate tasks**
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

7. **Report**
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

## Rules

- NEVER create a discovery-spec.md for bug fixes
- ALWAYS start with reproduction — if you can't reproduce it, you can't fix it
- ALWAYS add a regression test — this is non-negotiable
- If the bug reveals a missing invariant, add it to the domain-contract.md
- If the fix is trivial (typo, config error), still create the spec but keep it minimal
- If the 'bug' is actually a feature request in disguise, redirect to `/evospec.discover` or `/evospec.improve`

---

*Full framework context: [references/context.md](references/context.md)*
