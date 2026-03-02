---
name: evospec-adr
description: Create a new Architecture Decision Record with structured analysis of options, consequences, and reversibility.
---

# ADR

## Context

Architecture Decision Records capture the **why** behind significant technical choices. ADRs are first-class citizens in EvoSpec — they explain what code never can.

See [references/context.md](references/context.md) for full framework context.

## Steps

1. **Find the project**
   - Check `evospec.yaml` exists. If not: instruct user to run `evospec init`.
   - Determine the ADR directory from config (default: `docs/adr/`).

2. **Parse the decision topic**
   - Extract the core decision to be documented from user input.
   - If no input provided, ask: "What decision do you want to record?"

3. **Determine next ADR number**
   - Scan existing ADR files in the directory.
   - Find the highest number and increment by 1.

4. **Generate the ADR**
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

5. **Write the ADR file**
   - Filename: `NNNN-<slug>.md` (e.g., `0003-use-jwt-for-auth.md`)
   - Status: `proposed` (human must accept)

6. **Report**
   - Print the ADR path and number.
   - Remind: "ADR status is 'proposed'. Review and change to 'accepted' when approved."
   - If related specs exist, suggest linking them in spec.yaml.

## Rules

- ADRs are never deleted, only superseded
- Status lifecycle: proposed → accepted → deprecated → superseded
- Keep ADRs short — one decision, one page
- Always include the 'What Would Have to Be True' section
- Always include reversibility assessment
- If the decision is about a core zone change, flag that fitness functions may be needed

---

*Full framework context: [references/context.md](references/context.md)*
