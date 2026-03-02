# ADR-0001: Adopt EvoSpec for spec-driven delivery

> Status: **accepted** | Date: 2026-03-01 | Zone: core

---

## Context

We need a structured approach to specification that adapts rigor to risk.
Exploratory work needs speed; core domain work needs contracts and guardrails.

## Decision

Adopt EvoSpec as our spec-driven delivery framework.
Classify changes as edge/hybrid/core and apply appropriate artifacts.

## Consequences

### Positive
- Proportional specification (no over-specifying edge, no under-specifying core)
- Executable guardrails via fitness functions
- ADR trail for architectural decisions

### Negative
- Learning curve for the team
- Initial overhead to classify and document

## Reversibility

**Assessment**: trivial — specs are markdown files, easy to remove or migrate.
