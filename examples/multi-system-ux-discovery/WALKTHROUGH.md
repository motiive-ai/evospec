# Walkthrough: Two Backends + UX Vibe-Coding + Invariant Safety Net

> **Scenario**: A product designer (non-programmer) vibe-codes a React prototype
> using an AI agent. The prototype touches two existing backend services.
> EvoSpec ensures the designer knows what rules exist, warns when they're
> about to break one, and generates the backend backlog after user testing.

---

## Cast of Characters

| Who | Role | Uses EvoSpec How |
|-----|------|-----------------|
| **Backend Team A** | Owns Order Service (Java/Spring Boot) | Created core spec with invariants |
| **Backend Team B** | Owns Inventory Service (Python/FastAPI) | Created core spec with invariants |
| **Product Designer** | Vibe-codes the Smart Cart UX prototype | Creates edge spec, checks invariant impact via MCP |
| **AI Agent** (Windsurf/Cursor) | Builds the React prototype | Activates `evospec-discover` skill, calls MCP tools, warns designer of conflicts |

---

## Act 1: Backend Teams Reverse-Engineer Their Domains

Backend engineers run evospec's reverse engineer to extract their current domain structure into specs.

### Order Service (Java/Spring Boot)

```bash
# Reverse-engineer the API endpoints
evospec reverse api --framework spring --source order-service

# Output:
#   POST   /api/orders/           → OrderController.createOrder
#   GET    /api/orders/{orderId}  → OrderController.getOrder
#   POST   /api/orders/{orderId}/checkout → OrderController.checkout
#   ...13 total endpoints
#   Suggested bounded contexts: /api/orders (8), /api/payments (5)

# Reverse-engineer the database schema
evospec reverse db --source order-service

# Output:
#   Order (table: orders) — 8 fields
#   LineItem (table: line_items) — 7 fields
#   Relationship: LineItem → Order (FK via order_id)
```

The backend team creates a **core spec** and fills in the domain contract with invariants:

```
specs/changes/2026-01-15-order-service-domain/
├── spec.yaml           ← zone: core, 6 invariants, 2 fitness functions
└── domain-contract.md  ← entities, state machine, cross-context dependencies
```

**Key invariants** (from `spec.yaml`):

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| ORD-INV-001 | Every Order MUST have ≥1 LineItem before leaving draft | api-validation |
| ORD-INV-002 | Order total MUST equal sum of LineItem subtotals | domain-logic |
| ORD-INV-003 | Payment MUST be authorized before order confirmation | state-machine |
| ORD-INV-004 | Cancelled orders cannot transition to any other status | state-machine |
| ORD-INV-005 | LineItem quantity MUST be > 0 | schema-validation |
| ORD-INV-006 | Order MUST have valid customer_id from authenticated user | api-validation |

### Inventory Service (Python/FastAPI)

```bash
evospec reverse api --framework fastapi --source inventory-service

# Output:
#   GET  /api/products/{product_id}/availability → check_availability
#   POST /api/reservations                       → reserve_stock
#   POST /api/reservations/{id}/confirm          → confirm_reservation
#   ...9 total endpoints
#   Suggested bounded contexts: /api/products (5), /api/reservations (4)

evospec reverse db --source inventory-service

# Output:
#   Product (table: products) — 10 fields
#   StockReservation (table: stock_reservations) — 9 fields
#   Relationship: StockReservation → Product (FK via product_id)
```

**Key invariants**:

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| INV-INV-001 | Stock quantity MUST NOT go below zero | database-constraint |
| INV-INV-002 | Reserved quantity MUST NOT exceed stock quantity | domain-logic |
| INV-INV-003 | Reservation MUST be released/confirmed within 30 minutes | scheduled-job |
| INV-INV-004 | Confirmed reservation permanently decrements stock | domain-logic |
| INV-INV-007 | Availability check MUST account for reserved quantity | domain-logic |

---

## Act 2: The Designer Starts Vibe-Coding

The product designer opens Windsurf and says:

> "Build me a React Smart Cart component with real-time product availability
> and one-click checkout. Use these backend APIs..."

The AI agent builds the prototype. Before writing code, the agent activates the
`evospec-discover` skill and **reads the safety net** via EvoSpec's MCP tools:

### The AI Agent's First Move: Explore Upstream APIs and Entities

```
# Skill: evospec-discover, Step 3 — explore and model the domain

# What APIs does the Order Service expose?
MCP tool: evospec:get_upstream_apis(upstream_name="order-service")
→ ["POST /api/orders/", "GET /api/orders/{orderId}", "POST /api/orders/{orderId}/checkout", ...]

# What entities exist in the order domain?
MCP tool: evospec:get_entities(upstream="order-service")
→ Order (aggregate root), LineItem, Payment, ...

# The designer has an API response file from the order service
MCP tool: evospec:parse_contract_file("order-response.json")
→ Extracted: Order{id, status, items[], total, customer_id}, LineItem{product_id, qty, price}

# What invariants apply to the inventory context?
MCP tool: evospec:get_invariants(context="inventory")
→ INV-INV-001: Stock quantity MUST NOT go below zero, ...
```

### Then: Check Invariant Impact

```
# Skill: evospec-discover, Step 6 (CRITICAL) — check invariant impact
MCP tool: evospec:check_invariant_impact(
  entities: ["Order", "LineItem", "Product", "StockReservation"],
  contexts: ["Orders", "Inventory"],
  description: "Smart Cart with real-time availability and one-click checkout"
)
```

**Response** (what the AI agent sees):

```json
{
  "safe": false,
  "conflicts": [
    {
      "invariant_id": "ORD-INV-001",
      "statement": "Every Order MUST have at least one LineItem before status can change from draft",
      "spec": "Order Service Core Domain",
      "context": "orders",
      "reasons": ["touches entity 'order' mentioned in invariant",
                   "touches entity 'lineitem' mentioned in invariant"]
    },
    {
      "invariant_id": "ORD-INV-003",
      "statement": "Payment MUST be authorized before Order status changes to confirmed",
      "spec": "Order Service Core Domain",
      "context": "orders",
      "reasons": ["description shares keywords: checkout, order, payment"]
    },
    {
      "invariant_id": "INV-INV-003",
      "statement": "StockReservation MUST be released or confirmed within 30 minutes of creation",
      "spec": "Inventory Service Core Domain",
      "context": "inventory",
      "reasons": ["touches entity 'stockreservation' in same spec"]
    },
    {
      "invariant_id": "INV-INV-002",
      "statement": "Product reserved_quantity MUST NOT exceed stock_quantity",
      "spec": "Inventory Service Core Domain",
      "context": "inventory",
      "reasons": ["touches entity 'product' mentioned in invariant"]
    }
  ],
  "guidance": [
    "⚠ This change may affect existing core invariants.",
    "Options: exempt (feature flag) | evolve (new version) | shadow (mock first) | redesign"
  ]
}
```

### What the AI Agent Tells the Designer

> ⚠ **4 backend invariants may be affected by this UX:**
>
> 1. **Empty cart checkout**: The Order Service requires at least 1 item before checkout.
>    → I'll disable the checkout button when the cart is empty.
>
> 2. **Payment timing**: Payment must be authorized BEFORE the order is confirmed.
>    → I'll change the flow: authorize payment first, then create the confirmed order.
>
> 3. **30-minute reservation**: Stock reservations expire after 30 minutes.
>    → I'll add a countdown timer so the user knows.
>
> 4. **Stock overbooking**: If payment fails, stock stays reserved until timeout.
>    → The backend handles this, but I'll show the user a clear error message.

The designer says "OK, build it with those constraints." The AI generates
`SmartCart.tsx`, `useCart.ts`, and `client.ts` — already respecting the invariants.

---

## Act 3: The Designer Creates the Edge Spec

```bash
evospec new "smart-cart-ux" --zone edge --type experiment
```

The discovery spec captures:
- **Hypothesis**: One-click checkout + real-time availability → +25% conversion
- **Kill criteria**: Stop if <10% improvement after 2 weeks
- **Invariant conflicts**: 4 conflicts documented with resolutions
- **Backend requirements**: What the backends need to build IF the experiment succeeds

The edge spec lives in:
```
specs/changes/2026-03-01-smart-cart-ux/
├── spec.yaml           ← zone: edge, invariant_impact with 4 conflicts
└── discovery-spec.md   ← hypothesis, assumptions, experiment timeline, backend needs
```

---

## Act 4: User Testing

The designer deploys the prototype behind a feature flag and runs an A/B test.

**Results after 2 weeks:**
- Cart-to-checkout conversion: 32% → 41% (+28%) ✅ exceeds kill criteria
- Average order value: $67 → $72 (+7%)
- Time to checkout: 4.2 min → 1.1 min
- No backend errors (invariants were respected in the prototype)

The experiment succeeds. Time to make it permanent.

---

## Act 5: From Edge to Hybrid — Backend Requirements

```bash
evospec new "smart-cart-backend-support" --zone hybrid --type improvement
```

The designer (or the AI agent) creates a **hybrid spec** that captures what the
backends need to build:

### Order Service Changes
1. New endpoint: `POST /api/orders/one-click` (atomic create+pay)
2. Accept `payment_id` in create order request
3. Idempotency key for double-tap prevention

### Inventory Service Changes
1. Return `expires_at` in reservation response
2. Batch availability endpoint: `POST /api/products/availability`
3. (Future) WebSocket real-time stock updates

This hybrid spec references the edge spec's experiment results and links to the
core specs' invariants. The backend teams review and implement with full context.

---

## The Key Insight: Knowledge Funnel in Action

```
MYSTERY                    HEURISTIC                     ALGORITHM
─────────                  ──────────                    ──────────
"Users abandon carts,      "Real-time availability       "Order MUST have ≥1
 we don't know why"         + 1-click checkout            LineItem before
                             increases conversion          checkout"
                             by 28%"
     │                           │                            │
     ▼                           ▼                            ▼
 Edge Spec                  Hybrid Spec                  Core Spec
 (discovery-spec.md)        (both artifacts)             (domain-contract.md)
 Free to experiment         Needs coordination           Invariants enforced
```

- **The designer worked in the Mystery→Heuristic space** (edge zone)
- **The backends live in the Algorithm space** (core zone)
- **EvoSpec connected them** without the designer needing to read Java or Python
- **The invariants acted as guardrails**, not gatekeepers — the designer could experiment freely while knowing what rules to respect

---

## What Made This Work

1. **Reverse engineering extracted the safety net** — invariants, entities, and API contracts from real backend code
2. **MCP tools served the safety net to the AI agent** — the agent called `evospec:get_upstream_apis`, `evospec:get_entities`, `evospec:parse_contract_file`, and `evospec:check_invariant_impact` before writing code
3. **The edge spec was cheap to create** — just a hypothesis, kill criteria, and assumption list
4. **Invariant conflicts were documented, not blocked** — the designer chose resolution strategies (shadow, redesign, exempt)
5. **The experiment result flowed into a hybrid spec** — the backend teams got clear, validated requirements

---

## What EvoSpec Supports Today for This UC

| Capability | Status | How |
|-----------|--------|-----|
| Reverse-engineer Java/Spring API | ✅ | `evospec reverse api --framework spring` |
| Reverse-engineer Python/FastAPI API | ✅ | `evospec reverse api --framework fastapi` |
| Reverse-engineer JPA entities | ✅ | `evospec reverse db --source order-service` |
| Reverse-engineer SQLAlchemy models | ✅ | `evospec reverse db --source inventory-service` |
| Reverse-engineer React/TS modules | ✅ | `evospec reverse cli --source smart-cart-ui` |
| Core specs with invariants | ✅ | `spec.yaml` with `invariants:` section |
| Edge specs with discovery | ✅ | `discovery-spec.md` with hypothesis/kill criteria |
| Invariant impact checking (MCP) | ✅ | `evospec:check_invariant_impact` tool |
| Filtered entity registry (MCP) | ✅ | `evospec:get_entities(context?, upstream?)` tool |
| Filtered invariant listing (MCP) | ✅ | `evospec:get_invariants(context?)` tool |
| Upstream API discovery (MCP) | ✅ | `evospec:get_upstream_apis(upstream_name?)` tool |
| Contract file parsing (MCP) | ✅ | `evospec:parse_contract_file(file_path)` tool |
| Agent Skills (cross-platform) | ✅ | `evospec generate agents --platform skills` |
| Spec validation | ✅ | `evospec check` |
| Fitness function execution | ✅ | `evospec fitness` |
| Feature lifecycle tracking | ✅ | `evospec feature add/update/list` |
| ADR management | ✅ | `evospec adr new/list` |

## Gaps Identified — What Could Be Better

| Gap | Impact | Proposed Enhancement |
|-----|--------|---------------------|
| **No automatic invariant_impact in spec.yaml** — the designer has to manually call `check_invariant_impact` or the AI agent does it | Medium | Auto-run `check_invariant_impact` during `evospec check` for edge/hybrid specs that declare `contexts_touched` |
| **No "serve invariants as API"** — the MCP server requires running locally | Low | The MCP server already works; could add a REST mode for non-MCP clients |
| **No reservation timer / temporal invariant UX hint** — the invariant says "30 minutes" but there's no structured way to extract temporal constraints | Low | Add a `temporal_constraint` field to invariants (e.g., `ttl: 30m`) |

*Previously identified gaps now addressed:*
- ✅ Cross-system API visibility → `evospec:get_upstream_apis`
- ✅ Contract file parsing → `evospec:parse_contract_file`
- ✅ Cross-spec endpoint traceability → `evospec reverse deps` + `evospec check` cross-spec endpoint check
- ✅ Multi-repo support → `upstreams[]` in evospec.yaml with per-service evospec projects
