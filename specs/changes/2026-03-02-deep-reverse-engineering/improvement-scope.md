# Improvement Scope: Deep Reverse Engineering (schema extraction, invariant detection, state machines)

> Zone: **core** | Type: **improvement** | Status: **draft**

---

## What Needs to Change

Current `evospec reverse` commands extract **structural skeletons** but miss the rich domain knowledge that makes specs useful. `reverse api` produces `GET /api/orders/{id} → OrderController.getOrder` but no request/response schemas, no field types, no validation rules. `reverse db` produces entity names and fields but no invariants, no state machines, no relationship constraints. This change adds a `--deep` flag to all reverse commands that performs semantic analysis beyond structural scanning.

## Why Now

The quality of MCP context depends on the quality of specs. When reverse engineering is shallow, MCP context is shallow — defeating the purpose of the safety net. Deep reverse engineering is the foundation that makes consumer-facing MCP, auto-spec sync, and verification meaningful. Without it, teams must manually curate everything that could be auto-detected.

## Scope

### In Scope

**1A. API Schema Extraction** (`evospec reverse api --deep`)
- DTO/model field walking for request/response types
- Validation annotation extraction (→ field constraints)
- Auth annotation detection
- Error response mapping
- Per-framework: Spring Boot (`@RequestBody` DTO), FastAPI (Pydantic model), Django REST (serializer_class), Express/NestJS (`@Body()` type), Gin/Echo (struct tags)

**1B. Invariant Detection** (`evospec reverse db --deep`)
- Database constraints → uniqueness/required invariants (high confidence)
- Validation annotations → range/length invariants (high confidence)
- Enum types → valid values invariants (high confidence)
- Custom validation methods → business rules (medium confidence)
- Exception throwing patterns → guard clauses (medium confidence)
- Confidence levels on all suggestions

**1C. State Machine Detection** (`evospec reverse db --deep`)
- Detect enum-typed status/state fields
- Analyze service code for `setStatus()` / `.status =` patterns
- Build transition graph with triggers
- Infer forbidden transitions (no outgoing edge)
- Generate ASCII diagram

**1D. External Dependency Mapping** (`evospec reverse deps --deep`)
- Detect actual service calls with payloads (not just URLs)
- Message queue producers/consumers with schemas
- Storage operations with types
- Client class identification

**1E. Domain Event Detection**
- Event publishing patterns per framework
- Payload field extraction
- Consumer identification
- Channel/topic mapping

### Out of Scope

- Auto-writing to `specs/domain/` without user confirmation (requires `--write` flag)
- Code generation from detected schemas
- Runtime analysis (static analysis only)

## Affected Areas

**Endpoints**: None

**Tables**: None

**Modules**:
- `evospec.reverse.api` — deep schema extraction per framework
- `evospec.reverse.db` — invariant detection + state machine extraction
- `evospec.reverse.deps` — deep dependency mapping with payloads
- `evospec.reverse.cli` — enhanced module analysis
- `evospec.core.config` — load/merge deep reverse output

**Bounded Contexts**:
- `reverse-engineering` — enhanced extraction
- `domain-management` — suggested invariants and state machines
- `spec-engine` — output format and confidence scoring

## Invariant Impact

No conflicts with existing invariants. Shallow reverse (without `--deep`) continues to work unchanged.

## Acceptance Criteria

### API Schema Extraction
- [ ] `evospec reverse api --deep --framework spring` extracts request/response schemas with field names, types, and validation constraints
- [ ] `evospec reverse api --deep --framework fastapi` extracts Pydantic model fields and response_model
- [ ] Works for all supported frameworks (Spring, FastAPI, Django, Express, NestJS, Gin, Echo)
- [ ] Output includes auth annotations, error responses, async markers

### Invariant Detection
- [ ] `evospec reverse db --deep` produces suggested invariants from `@Column`, `@UniqueConstraint`, enum fields, `@NotNull`
- [ ] Each suggested invariant has confidence level (high/medium/low) and source code reference
- [ ] At least 5 invariants suggested for a typical project with entity annotations

### State Machine Detection
- [ ] State machines detected for any entity with an enum-typed status/state field
- [ ] Transitions include trigger description and source code reference
- [ ] Forbidden transitions inferred from missing edges
- [ ] ASCII diagram generated

### External Dependencies
- [ ] Service calls detected with payload schemas
- [ ] Message queue producers/consumers identified with topics
- [ ] Storage operations mapped

### General
- [ ] `--deep` flag added to `reverse api`, `reverse db`, `reverse deps`
- [ ] Deep reverse output can be written to `specs/domain/` files with `--write`
- [ ] Existing shallow reverse (without `--deep`) continues to work unchanged

### Example: Deep API Output

```yaml
# Output of: evospec reverse api --deep --framework spring
endpoints:
  - method: POST
    path: /api/orders
    handler: OrderController.createOrder

    request:
      content_type: application/json
      body_class: CreateOrderRequest
      fields:
        - name: customerId
          type: String
          required: true
          constraints: "UUID format"
        - name: items
          type: List<OrderItem>
          required: true

    response:
      success:
        status: 201
        body_class: OrderResponse
        fields:
          - name: orderId
            type: String
          - name: status
            type: OrderStatus
      errors:
        - status: 400
          when: "validation fails"
        - status: 409
          when: "duplicate order"

    annotations:
      transactional: true
      auth: bearer-token
```

### Example: Suggested Invariants

```yaml
# Output of: evospec reverse db --deep
suggested_invariants:
  - id: "INV-ORD-001"
    entity: Order
    rule: "orderId MUST be unique"
    source: "@Column(unique = true)"
    confidence: high
    enforcement: database-constraint

  - id: "INV-ORD-002"
    entity: Order
    rule: "status MUST be one of: DRAFT, CONFIRMED, SHIPPED, DELIVERED, CANCELLED"
    source: "OrderStatus enum"
    confidence: high
    enforcement: domain-logic

  - id: "INV-ORD-003"
    entity: Order
    rule: "Cancelled orders cannot transition to any other status"
    source: "OrderService.cancel() checks status"
    confidence: medium
    enforcement: domain-logic
```

## Risks & Rollback

**Risk level**: medium — complex code analysis with framework-specific parsers

**Rollback plan**: Remove `--deep` flag handling; shallow reverse unaffected

**Reversibility**: trivial — additive flag, no changes to existing behavior

## ADRs

- ADR: Confidence levels on suggested invariants rather than auto-confirming — prevents false positives from entering the safety net
- ADR: Static analysis only (no runtime) — keeps `reverse` deterministic and fast
