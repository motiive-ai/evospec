# Improvement Scope: Consumer-Facing MCP — API Contracts, File Schemas & Discovery Prompts

> Zone: **hybrid** | Type: **improvement** | Status: **draft**

---

## What Needs to Change

EvoSpec's MCP server today serves **the team that owns the spec** — internal governance, invariant checking, task management. But the highest-value use case is when **external consumers** (other teams, frontend developers, AI agents building integrations) query the MCP to understand how to use a system's API. Two gaps prevent this: (1) API contracts are just strings — `traceability.endpoints` stores `"GET /api/orders/{id}"` with no request/response schema, no param types, no error responses. (2) There's no file/response schema — when an endpoint returns a downloadable file or structured JSON, there's nowhere to describe what it looks like.

## Why Now

Without consumer-facing MCP, AI agents building integrations must read source code, guess the response format, and trial-and-error until the parser works. With structured API contracts and file schemas served via MCP, an AI agent can generate correct consumer code on the first try — the same value proposition EvoSpec delivers for internal governance, extended to external consumers.

## Scope

### In Scope

- **`specs/domain/api-contracts.yaml`** — structured API contracts with endpoint, params, request/response schemas, auth, tags
- **`specs/domain/file-schemas.yaml`** — file/response schemas with name, format, structure, example
- **MCP tools**: `get_api_contract(endpoint?, tag?)`, `get_file_schema(name?, format?)`, `get_consumer_context(intent)`
- **MCP resource**: `evospec://api-catalog` — browsable endpoint catalog
- **MCP prompts**: `consumer_discovery(use_case)`, `ux_discovery(bounded_context)` — context-aware discovery questions
- **`evospec check` validation** of api-contracts.yaml references (schema_ref → file-schema, entity types → entities.yaml)
- **Domain file loading** — api-contracts.yaml and file-schemas.yaml alongside existing entities.yaml, contexts.yaml

### Out of Scope

- `evospec reverse api --deep` auto-population of api-contracts.yaml (that's the deep-reverse-engineering change)
- Code generation from contracts (the MCP provides context, the AI agent generates code)
- OpenAPI/Swagger import/export (future enhancement)

## Affected Areas

**Endpoints**: None (MCP tools/resources, not HTTP endpoints)

**Tables**: None

**Modules**:
- `evospec.mcp.server` — new tools, resources, and prompts
- `evospec.core.config` — load api-contracts.yaml and file-schemas.yaml
- `evospec.core.init` — create stub domain files
- `evospec.core.check` — validate cross-references

**Bounded Contexts**:
- `domain-management` — new domain files
- `agent-integration` — new MCP surface
- `mcp-server` — new tools and resources

## Invariant Impact

No conflicts. Fully additive — new domain files and MCP surface alongside existing ones.

## Acceptance Criteria

- [ ] `specs/domain/api-contracts.yaml` supported with endpoint, params, request, response, auth, tags
- [ ] `specs/domain/file-schemas.yaml` supported with name, format, structure, example
- [ ] `get_api_contract(endpoint?, tag?)` MCP tool returns matching contracts
- [ ] `get_file_schema(name?, format?)` MCP tool returns file structure and example
- [ ] `get_consumer_context(intent)` combines contracts + schemas + entities + glossary for a given intent
- [ ] `evospec://api-catalog` resource returns browsable endpoint catalog grouped by tag
- [ ] `consumer_discovery` MCP prompt generates context-aware discovery questions from domain model
- [ ] `ux_discovery` MCP prompt generates UI-specific discovery questions per bounded context
- [ ] `evospec check` validates api-contracts.yaml references (schema_ref, entity types)
- [ ] Domain files loaded by config: api-contracts.yaml and file-schemas.yaml alongside existing domain files
- [ ] `evospec init` creates stub api-contracts.yaml and file-schemas.yaml

### Example: API Contract

```yaml
# specs/domain/api-contracts.yaml
contracts:
  - endpoint: "GET /api/orders/{orderId}"
    description: "Get order details"
    params:
      - name: orderId
        in: path
        type: String
        format: UUID
        required: true
    response:
      200:
        fields:
          - name: orderId
            type: String
          - name: status
            type: OrderStatus
          - name: items
            type: List<LineItem>
          - name: total
            type: Decimal
      404:
        body:
          message: String
    auth: "bearer token"
    tags: ["orders", "read"]

  - endpoint: "POST /api/orders"
    description: "Create a new order"
    request:
      content_type: application/json
      fields:
        - name: customerId
          type: String
          required: true
        - name: items
          type: List<OrderItem>
          required: true
          fields:
            - name: productId
              type: String
            - name: quantity
              type: int
              constraints: "> 0"
    response:
      201:
        fields:
          - name: orderId
            type: String
          - name: status
            type: OrderStatus
      400:
        body: { message: String }
    auth: "bearer token"
    tags: ["orders", "write"]
```

### Example: File Schema

```yaml
# specs/domain/file-schemas.yaml
schemas:
  - name: "OrderExport"
    format: json
    description: "JSON export of order data"
    version: "v1"
    structure:
      - name: orderId
        type: String
      - name: createdAt
        type: ISO8601 datetime
      - name: items
        type: List<LineItem>
        fields:
          - name: productId
            type: String
          - name: quantity
            type: int
          - name: price
            type: Decimal
      - name: summary
        type: Object
        fields:
          - name: totalAmount
            type: Decimal
          - name: itemCount
            type: int
    example: |
      {
        "orderId": "a1b2c3d4-...",
        "createdAt": "2026-03-01T10:00:00Z",
        "items": [
          { "productId": "P001", "quantity": 2, "price": 29.99 }
        ],
        "summary": { "totalAmount": 59.98, "itemCount": 1 }
      }
```

### Example: Consumer Context Flow

```
Developer: "Build a script to download and parse order exports"

AI Agent:
1. Calls get_consumer_context("download and parse order exports")
   → Returns:
     - Endpoint: GET /api/orders/{orderId}/export → downloads JSON
     - File schema: OrderExport with fields {orderId, items: [...], summary}
     - List endpoint: GET /api/orders?status=completed for finding order IDs
     - Glossary: "OrderStatus" = DRAFT | CONFIRMED | SHIPPED | DELIVERED

2. Asks developer: "Which order status should I filter by?"

3. Generates correct code with proper types, field names, error handling
```

## Risks & Rollback

**Risk level**: low — fully additive, no existing functionality changes

**Rollback plan**: Remove new domain files and MCP handlers; existing functionality unaffected

**Reversibility**: trivial

## ADRs

- ADR: Separate api-contracts.yaml and file-schemas.yaml rather than embedding in spec.yaml — keeps domain files focused and independently versionable
- ADR: Use `get_consumer_context(intent)` as the primary entry point — combines multiple data sources based on natural language intent rather than requiring consumers to know which tool to call
