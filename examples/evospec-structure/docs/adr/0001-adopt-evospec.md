# ADR-0001: Adopt EvoSpec for spec-driven delivery

> Status: **accepted** | Date: 2025-05-15 | Zone: core

---

## Context

We need a structured approach to specification that adapts rigor to risk.
Exploratory work (e.g., recommendations engine) needs speed and tolerance for ambiguity.
Core domain logic (e.g., order management) needs contracts, invariants, and executable guardrails.

Most frameworks treat everything the same — either over-specifying exploratory work or under-specifying structural changes. Both fail.

## Decision

Adopt EvoSpec as our spec-driven delivery framework.
Classify changes as edge/hybrid/core and apply appropriate artifacts:
- **Edge**: Discovery spec + kill criteria
- **Hybrid**: Discovery spec + lightweight domain contract
- **Core**: Full domain contract + fitness functions + ADRs

## Consequences

### Positive
- Proportional specification (no over-specifying edge, no under-specifying core)
- Executable guardrails via fitness functions in CI
- ADR trail for architectural decisions
- AI agent integration (Windsurf workflows + Claude Code)

### Negative
- Learning curve for the team
- Initial overhead to classify and document

## Reversibility

**Assessment**: trivial — specs are markdown files, easy to remove or migrate.
