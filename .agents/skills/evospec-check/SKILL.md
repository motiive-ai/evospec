---
name: evospec-check
description: Validate specs, run fitness function checks, and verify cross-artifact consistency. Non-destructive analysis.
---

# Check

## Context

This workflow performs **non-destructive validation** across all EvoSpec artifacts. It is the guardrail enforcement mechanism — the automated equivalent of an architecture review.

See [references/context.md](references/context.md) for full framework context.

## Steps

1. **Find specs**
   - Check `evospec.yaml` exists.
   - If user input specifies a path, validate that spec only.
   - Otherwise, validate ALL specs in `specs/changes/`.

2. **Run checks for each spec**
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

3. **Classify severity**
   - **ERROR**: Missing required artifact for zone, invariant without enforcement, core without fitness functions
   - **WARNING**: Missing optional fields, incomplete classification, no team ownership
   - **INFO**: Suggestions for improvement, missing optional sections

4. **Report**
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

5. **Next Actions**
   - If errors: list specific fixes needed before implementation
   - If warnings only: user may proceed, but suggest improvements
   - If all pass: "Specs are valid. Ready for the Implement workflow."

## Rules

- STRICTLY READ-ONLY — do NOT modify any files
- Report findings accurately — do not hallucinate missing sections
- Prioritize errors over warnings over info
- For core zone: treat missing fitness functions as ERRORS, not warnings
- Constitution/invariant violations are always ERRORS

---

*Full framework context: [references/context.md](references/context.md)*
