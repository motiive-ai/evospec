# EvoSpec Worked Example: Multi-System UX Discovery

## The Scenario

A company runs two backend microservices that maintain core domain logic:

1. **Order Service** (Java/Spring Boot) — manages orders, line items, payments
2. **Inventory Service** (Python/FastAPI) — manages products, stock, reservations

Both backends have well-defined invariants (e.g., "an order must have at least one line item", "stock cannot go negative"). These backends are maintained by backend engineers who care deeply about data integrity.

A **product designer** (non-programmer) wants to vibe-code a new UX: a "Smart Cart" that lets users build orders with real-time availability checking and one-click checkout. The designer will use an AI coding agent (Windsurf/Cursor) to build a React prototype and test it with users.

### Two Personas

| Persona | Example | How they use EvoSpec |
|---------|---------|---------------------|
| **Internal** — backend engineer maintaining a service | Order Service developer | Agent Skills for workflow, MCP tools for spec management |
| **External** — designer/dev consuming upstream contracts | Product designer building Smart Cart UI | Agent Skills for discovery, MCP tools for entity/invariant/API visibility across systems |

### The Problem

The designer's prototype might:
- **Break invariants**: e.g., allow checkout with empty cart, or reserve stock without a corresponding order
- **Cross bounded contexts**: the Smart Cart touches both Order and Inventory domains
- **Create implicit backend requirements**: features that look simple in the UI need new API endpoints or state transitions in the backends

### What EvoSpec Does

1. **Reverse-engineer** both backends into core domain specs (invariants, entities, API contracts)
2. **Serve the safety net** to the designer's AI agent via MCP — the agent knows what the backends require
3. **Detect invariant conflicts** when the UX experiment touches core domain rules
4. **Warn the designer** before they ship something that violates backend contracts
5. **Generate a backlog** of what must be built in the backends to support the new UX

## Directory Structure

```
order-service/        ← Java/Spring Boot backend (simulated source)
inventory-service/    ← Python/FastAPI backend (simulated source)
smart-cart-ui/        ← React/TS UX prototype (vibe-coded)
specs/                ← EvoSpec output: core contracts + edge discovery
```

## The Walkthrough

### Step 1: Reverse-engineer both backends

```bash
# From the example directory (after evospec init)
evospec reverse api --framework spring --source order-service
evospec reverse db --source order-service
evospec reverse api --framework fastapi --source inventory-service
evospec reverse db --source inventory-service
evospec reverse cli --source smart-cart-ui
```

### Step 2: Create core domain specs for each backend

```bash
evospec new "order-service-domain" --zone core --type improvement
evospec new "inventory-service-domain" --zone core --type improvement
```

Then fill in the domain contracts with the reverse-engineered data.

### Step 3: The designer creates an edge discovery spec

```bash
evospec new "smart-cart-ux" --zone edge --type experiment
```

The discovery spec describes the hypothesis, assumptions, and kill criteria.

### Step 4: Explore upstream APIs and entities

The designer's AI agent uses MCP tools to understand the upstream systems:

```
# What APIs are available from the backends?
MCP call: evospec:get_upstream_apis(upstream_name="order-service")
→ ["POST /orders", "GET /orders/{id}", "POST /orders/{id}/checkout", ...]

# What entities exist in the order domain?
MCP call: evospec:get_entities(upstream="order-service")
→ Order (aggregate root), LineItem, Payment, ...

# The designer has an API response file — parse it to understand entities
MCP call: evospec:parse_contract_file("order-response.json")
→ Extracted: Order{id, status, items[], total}, LineItem{product_id, qty, price}
```

### Step 5: Check invariant impact BEFORE building

The designer's AI agent calls `evospec:check_invariant_impact` via MCP:

```
MCP call: evospec:check_invariant_impact(
  entities: ["Order", "LineItem", "Product", "StockReservation"],
  contexts: ["orders", "inventory"],
  description: "Smart Cart with real-time availability and one-click checkout"
)
```

**Result**: ⚠ Conflicts detected!
- INV-001: "Every Order MUST have at least one LineItem" — the cart might create empty orders
- INV-003: "Stock reservation MUST be released within 30 minutes if not confirmed" — the UX needs a timer
- INV-005: "Payment MUST be authorized before order status changes to confirmed" — one-click checkout must handle payment first

### Step 6: The designer knows what to respect and what to propose

The designer can now:
- **Exempt** (use feature flags to avoid touching invariants during prototyping)
- **Shadow** (build the UX against a mock, test with users, then propose backend changes)
- **Propose** (create a hybrid spec requesting new backend capabilities)

### Step 7: After user testing, generate backend requirements

```bash
evospec new "smart-cart-backend-support" --zone hybrid --type improvement
```

This hybrid spec captures what the backends need to build, with clear traceability to the UX experiment.

---

## Key Insight

> **The UX experiment (edge) is free to move fast. The backend contracts (core) are the guardrails.
> EvoSpec's job is to make the guardrails visible to everyone — including non-programmers 
> using AI agents to vibe-code prototypes.**

The designer never needs to read Java or Python code. They just need to know:
- What APIs are available (via `evospec:get_upstream_apis` MCP tool)
- What entities exist (via `evospec:get_entities` MCP tool)
- What an API response means (via `evospec:parse_contract_file` MCP tool)
- What rules they can't break (via `evospec:check_invariant_impact` MCP tool)
- What they need to propose if the UX requires backend changes (via hybrid specs)

All of this is accessible through **Agent Skills** (`evospec-discover`) which guide the AI agent
through the discovery workflow, referencing the right MCP tools at each step.
