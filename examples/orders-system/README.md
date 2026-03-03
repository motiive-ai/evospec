# EvoSpec Example: Orders System — External Consumer Discovery

## The Scenario

A company runs an **Orders System** that manages orders, items, and categories.

**Key business rule**: An order **cannot** contain items from both `chemical` and `food` categories (the "hazmat-food" restriction group). This is enforced as invariant `ORD-INV-002`.

The system exposes:
- A **REST API** for order CRUD + category listing
- A **JSON file export** endpoint (`GET /api/orders/{orderId}/export`)

### The Consumer

An **external developer** (or data analyst) wants to:
1. Understand the Orders domain — what is an Order? What does it contain?
2. Build a **dashboard UI** or **data analysis tool** that works with order data
3. Know what rules exist before building something that breaks them

### What EvoSpec Does (and Does NOT Do)

| EvoSpec DOES | EvoSpec DOES NOT |
|-------------|-----------------|
| Explain what an Order is, its fields, relationships | Serve actual order data (e.g., order #123) |
| Show invariants (chemical + food restriction) | Enforce invariants at runtime |
| Provide API contract details (endpoints, params, responses) | Proxy API calls |
| Parse response files to extract entity structure | Store or cache API responses |
| Help AI agents generate correct integration code | Run the integration code |
| Warn when a proposed change conflicts with invariants | Block the change |

**In other words**: EvoSpec is the **knowledge layer**, not the **data layer**. It tells you *how* the system works and *what rules to follow*, but the consumer must build their own system to actually fetch and process data.

---

## What the MCP Provides

When the external developer's AI agent connects to the Orders System's MCP server:

### 1. Domain Exploration

```
# "What is the main entity?"
MCP tool: evospec:get_entities()
→ Order (aggregate root) — has Items, Items have Categories
→ 3 entities, 1 bounded context (orders)

# "What is an Order? What does it contain?"
MCP tool: evospec:get_entities(context="orders")
→ Order: id, customer_id, status, total_amount, created_at
→ Item: id, order_id, product_name, category_id, quantity, unit_price
→ Category: id, name, restriction_group

# "What do these terms mean?"
MCP resource: evospec://glossary
→ Order = "A request by a customer to purchase one or more items..."
→ Item ≠ Product (Items are order-scoped, Products are catalog entities)
→ Restriction Group = "Named group of categories that are mutually exclusive per order"
```

### 2. Rules Discovery

```
# "What rules exist that I need to respect?"
MCP tool: evospec:get_invariants(context="orders")
→ ORD-INV-001: Order MUST have ≥1 Item before leaving draft
→ ORD-INV-002: chemical + food items CANNOT coexist in same order
→ ORD-INV-003: total_amount MUST equal sum of item subtotals
```

### 3. API Contract Discovery

```
# "How do I get order data?"
MCP tool: evospec:get_api_contract(tag="orders")
→ GET /api/orders/{orderId} — returns Order with items
→ GET /api/orders — paginated list
→ GET /api/orders/{orderId}/export — JSON file download

# "What does the export file look like?"
MCP tool: evospec:get_file_schema(name="OrderExport")
→ OrderExport: order_id, customer_id, status, total_amount, items[]
→ ItemExport: item_id, product_name, category{id, name, restriction_group}, quantity, unit_price, subtotal
```

### 4. Parse a Real Response

```
# "I have a response file from the API — what entities are in it?"
MCP tool: evospec:parse_contract_file("order-response.json")
→ Extracted entities: Order-Response (root), Item (nested), Category (nested)
→ Relationships: Order-Response has_many Items, Item contains Category
```

### 5. Impact Check Before Building

```
# "I want to build a dashboard that groups orders by category"
MCP tool: evospec:check_invariant_impact(
  entities: ["Order", "Item", "Category"],
  contexts: ["orders"],
  description: "Dashboard grouping orders by item category with cross-category analytics"
)
→ ⚠ ORD-INV-002 may be relevant: chemical + food cannot coexist
→ Your dashboard should account for this restriction when displaying category combinations
```

---

## How Skills Help

**Agent Skills** (`evospec-discover`) guide the AI agent through a structured discovery workflow:

1. **Read the glossary** — understand the ubiquitous language first
2. **Explore entities** — understand the domain model
3. **Check invariants** — know what rules exist
4. **Explore API contracts** — understand how to get data
5. **Parse response files** — understand the data shape
6. **Check impact** — verify the proposed system won't violate any rules

Without Skills, the AI agent would need to know which MCP tools to call and in what order. Skills encode this workflow so the agent follows a structured path from "I know nothing" to "I can build a correct integration."

---

## Running This Example

```bash
# From the orders-system directory:
cd examples/orders-system

# Check the specs are valid
evospec check

# Explore what MCP would expose:
# (In practice, the AI agent calls these via MCP protocol)

# Parse the example response file
evospec parse_contract_file order-response.json  # (via MCP tool)
```

---

## Key Insight

> **EvoSpec bridges the gap between "I have access to an API" and "I understand the domain."**
>
> Without EvoSpec, the external developer would need to:
> - Read source code to understand entities and relationships
> - Discover invariants by trial and error (or reading docs that may be outdated)
> - Guess the API response shape from incomplete documentation
>
> With EvoSpec, the developer's AI agent can:
> - Call `evospec:get_entities()` to understand the domain in seconds
> - Call `evospec:get_invariants()` to know every rule
> - Call `evospec:parse_contract_file()` to understand real API responses
> - Call `evospec:check_invariant_impact()` to verify their design is safe
>
> **The MCP doesn't serve data — it serves understanding.**
