# Domain Contract: Inventory Service

## Bounded Context

**Inventory** — manages the product catalog, stock levels, and time-bounded stock reservations.

## Ubiquitous Language

| Term | Definition |
|------|-----------|
| **Product** | A physical item in the catalog with a SKU, price, and stock quantity |
| **Stock Quantity** | The total number of units physically available in the warehouse |
| **Reserved Quantity** | The number of units held for pending orders (not yet confirmed) |
| **Available Quantity** | stock_quantity − reserved_quantity. The amount a customer can actually buy |
| **Stock Reservation** | A time-bounded hold on inventory for a pending order. Expires in 30 minutes |
| **Confirmation** | Converting a reservation into a permanent stock decrement (order was paid) |
| **Release** | Returning reserved units back to available stock (order cancelled or reservation expired) |

## Entities

### Product (Aggregate Root)
| Field | Type | Nullable | Notes |
|-------|------|----------|-------|
| id | UUID | no | Primary key |
| name | String(255) | no | Display name |
| sku | String(100) | no | Unique stock-keeping unit |
| category | String(100) | no | Product category |
| price | Decimal(10,2) | no | Current selling price |
| stock_quantity | Integer | no | Physical units on hand. Must be ≥ 0 |
| reserved_quantity | Integer | no | Units held for pending orders. Must be ≤ stock_quantity |
| is_active | Boolean | no | Whether product is listed |
| created_at | Timestamp | no | |
| updated_at | Timestamp | yes | |

### StockReservation
| Field | Type | Nullable | Notes |
|-------|------|----------|-------|
| id | UUID | no | Primary key |
| product_id | UUID | no | FK → Product |
| order_id | String | no | References Order Service |
| quantity | Integer | no | Must be > 0 |
| status | String(20) | no | pending, confirmed, released, expired |
| expires_at | Timestamp | no | 30 minutes after creation |
| created_at | Timestamp | no | |
| confirmed_at | Timestamp | yes | Set when payment confirmed |

## State Machine: Stock Reservation Lifecycle

```
(create) ──> pending
pending ──[payment confirmed]──> confirmed  (permanently decrements stock)
pending ──[order cancelled]──> released     (restores reserved_quantity)
pending ──[30 min timeout]──> expired       (restores reserved_quantity)
confirmed ──> (terminal)
released ──> (terminal)
expired ──> (terminal)
```

## Invariants

1. **INV-INV-001**: Product stock_quantity MUST NOT go below zero
2. **INV-INV-002**: Product reserved_quantity MUST NOT exceed stock_quantity
3. **INV-INV-003**: StockReservation MUST be released or confirmed within 30 minutes of creation
4. **INV-INV-004**: A confirmed StockReservation MUST permanently decrement stock_quantity
5. **INV-INV-005**: StockReservation quantity MUST be greater than zero
6. **INV-INV-006**: A released or expired StockReservation MUST restore reserved_quantity to Product
7. **INV-INV-007**: Product availability check MUST account for both stock_quantity and reserved_quantity

## Cross-Context Dependencies

| Dependency | Context | Integration Pattern |
|-----------|---------|-------------------|
| Order lifecycle events | Order Service | Webhook/event — confirm reservation on payment, release on cancel |
| Reservation expiry | Internal | Scheduled job — runs every minute, expires stale reservations |

## Anti-Requirements

- Inventory does NOT manage pricing rules or discounts (only stores the base price)
- Inventory does NOT handle order creation or payment
- Inventory does NOT know about customers (only order_id)
