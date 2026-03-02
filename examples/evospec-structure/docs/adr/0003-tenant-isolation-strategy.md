# ADR-0003: Tenant Isolation via Row-Level Filtering

> Status: **accepted** | Date: 2025-06-01 | Zone: core

---

## Context

The platform is multi-tenant. Every business (tenant) must see only its own data.
We need a strategy that is simple, auditable, and hard to bypass accidentally.

## Decision

Enforce tenant isolation via row-level filtering:
- Every table with tenant-scoped data includes a `tenant_id` column
- Every query MUST filter by `tenant_id` from the authenticated user's JWT token
- A fitness function (`tests/fitness/test_tenant_isolation.py`) scans all query builders to verify tenant filtering
- No application-level "superuser" can bypass tenant isolation

## Consequences

### Positive
- Simple to understand and audit
- Fitness function catches missing filters at CI time
- Works with any SQL database
- Invariant INV-002 is automatically enforced

### Negative
- Every new query must remember to include tenant_id filter
- Cross-tenant reporting requires a separate, privileged service
- Slight index overhead on tenant_id columns

## Alternatives Considered

1. **Separate databases per tenant**: Maximum isolation but operational nightmare at scale
2. **PostgreSQL Row-Level Security**: Strong but vendor-specific, harder to test
3. **Schema-per-tenant**: Good isolation but migration complexity

## Reversibility

**Assessment**: difficult — tenant_id is baked into every table and query. Migration to a different strategy would require touching all data access code.
