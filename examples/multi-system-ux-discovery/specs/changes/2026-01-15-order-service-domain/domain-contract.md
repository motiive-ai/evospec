# Domain Contract: Order Service

## Bounded Context

**Orders** — manages the full lifecycle of customer orders, from draft through payment to delivery.

## Ubiquitous Language

| Term | Definition |
|------|-----------|
| **Order** | A customer's intent to purchase one or more products. Has a lifecycle: draft → pending_payment → confirmed → shipped → delivered → cancelled |
| **LineItem** | A single product entry within an order, with quantity and price |
| **Checkout** | The process of transitioning an order from draft to pending_payment, then to confirmed after payment |
| **Payment Authorization** | A hold on the customer's payment method. Must succeed before order confirmation |
| **Payment Capture** | Converting an authorization into an actual charge. Happens after shipping |

## Entities

### Order (Aggregate Root)
| Field | Type | Nullable | Notes |
|-------|------|----------|-------|
| id | UUID | no | Primary key |
| customer_id | String | no | Must reference authenticated user |
| status | String | no | draft, pending_payment, confirmed, shipped, delivered, cancelled |
| total_amount | Decimal | no | Must equal sum of LineItem subtotals |
| currency | String | no | ISO 4217 |
| payment_id | String | yes | Set after payment authorization |
| created_at | Timestamp | no | |
| updated_at | Timestamp | yes | |

### LineItem
| Field | Type | Nullable | Notes |
|-------|------|----------|-------|
| id | UUID | no | Primary key |
| order_id | UUID | no | FK → Order |
| product_id | String | no | References Inventory Service |
| product_name | String | no | Denormalized for display |
| quantity | Integer | no | Must be > 0 |
| unit_price | Decimal | no | Price at time of addition |
| subtotal | Decimal | no | quantity × unit_price |

## State Machine: Order Lifecycle

```
draft ──[add items]──> draft
draft ──[checkout]──> pending_payment   (requires ≥1 LineItem)
pending_payment ──[payment authorized]──> confirmed
confirmed ──[ship]──> shipped
shipped ──[deliver]──> delivered
draft ──[cancel]──> cancelled
pending_payment ──[cancel]──> cancelled
confirmed ──[cancel]──> cancelled (triggers refund)
cancelled ──> (terminal, no transitions out)
```

## Invariants

1. **ORD-INV-001**: Every Order MUST have at least one LineItem before status can change from draft
2. **ORD-INV-002**: Order total_amount MUST equal the sum of all LineItem subtotals
3. **ORD-INV-003**: Payment MUST be authorized before Order status changes to confirmed
4. **ORD-INV-004**: A cancelled Order MUST NOT transition to any other status
5. **ORD-INV-005**: LineItem quantity MUST be greater than zero
6. **ORD-INV-006**: Order MUST have a valid customer_id that references an authenticated user

## Cross-Context Dependencies

| Dependency | Context | Integration Pattern |
|-----------|---------|-------------------|
| Stock reservation | Inventory Service | API call (async) — reserve stock on checkout, confirm on payment, release on cancel |
| Product catalog | Inventory Service | API call (sync) — fetch product details when adding LineItem |
| Customer identity | Auth Service | Token validation — customer_id from JWT |

## Anti-Requirements

- Orders do NOT store full product details (only product_id and denormalized name/price)
- Orders do NOT manage stock levels (that's Inventory's responsibility)
- Orders do NOT handle shipping logistics (that's a separate Shipping context)
