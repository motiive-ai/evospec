# Glossary — Orders System

| Term | Definition | Not to be confused with |
|------|-----------|------------------------|
| **Order** | A request by a customer to purchase one or more items. Has a lifecycle (draft → confirmed → shipped → delivered). Can be cancelled. | Shopping cart (transient, not persisted) |
| **Item** | A single product line within an order, with quantity and unit price. Always belongs to exactly one category. | Product (catalog entity — Items reference products but are order-scoped) |
| **Category** | A classification for products (e.g., "food", "chemical", "electronics"). Some categories have restriction groups that prevent them from coexisting in the same order. | Tag (categories are structural, not just labels) |
| **Restriction Group** | A named group of categories that are mutually exclusive within a single order. Example: "hazmat-food" group means chemical and food items cannot coexist. | Category itself — restriction groups span multiple categories |
| **Order Total** | The sum of (quantity × unit_price) for all items in the order. Must always be accurate and ≥ 0. | Payment amount (may differ due to discounts, taxes) |
| **Draft** | Initial order status. Items can be added/removed freely. No restrictions on modification. | Confirmed (once confirmed, items are locked) |
| **Confirmed** | Order has been reviewed and accepted. Items are frozen. Triggers fulfillment. | Shipped (confirmed ≠ in transit) |
