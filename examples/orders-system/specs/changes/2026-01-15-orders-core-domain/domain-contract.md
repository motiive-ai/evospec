# Domain Contract: Orders Core Domain

> Zone: **core** | Bounded Context: **orders** | Status: **completed**

---

## 1. Context & Purpose

**Bounded Context**: orders

**Ubiquitous Language**:

| Term | Definition |
|------|-----------|
| Order | A customer order containing one or more items, subject to category restrictions |
| Item | A line item within an order, linked to exactly one category |
| Category | Product classification. Some categories are mutually exclusive per order |
| Restriction Group | Named group of categories that cannot coexist in the same order |

---

## 2. Aggregates & Entities

### Aggregate: Order

- **Order** (root): id, customer_id, status, total_amount, created_at
- **Item**: id, order_id, product_name, category_id, quantity, unit_price
- **Category** (reference): id, name, restriction_group

---

## 3. Invariants

| ID | Statement | Enforcement |
|----|-----------|-------------|
| ORD-INV-001 | Every Order MUST have ≥1 Item before leaving draft | api-validation |
| ORD-INV-002 | An Order MUST NOT contain Items from categories 'chemical' and 'food' simultaneously (hazmat-food restriction group) | domain-logic |
| ORD-INV-003 | Order total_amount MUST equal sum of (quantity × unit_price) for all Items | domain-logic |

### ORD-INV-002 Detail: Category Restriction

The restriction is enforced at two points:
1. **POST /api/orders** — when creating an order with items, the API checks all item categories
2. **POST /api/orders/{orderId}/items** — when adding an item to an existing draft order

If a violation is detected, the API returns `409 Conflict` with code `CATEGORY_RESTRICTION_VIOLATED`.

The restriction is based on `Category.restriction_group`: categories sharing the same non-null restriction_group value cannot appear together in one order. Currently, the only restriction group is `hazmat-food` (covering `chemical` and `food` categories).

---

## 4. API Surface

See `specs/domain/api-contracts.yaml` for full contract details.

## 5. File Export

The `GET /api/orders/{orderId}/export` endpoint returns a structured JSON file.
See `specs/domain/file-schemas.yaml` for the `OrderExport` schema.
See `order-response.json` for an example response.
