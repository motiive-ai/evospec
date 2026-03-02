# Ubiquitous Language — Glossary

> Define domain terms once, use them everywhere.

| Term | Definition | Context | Not to be confused with |
|------|-----------|---------|------------------------|
| Order | A customer's intent to purchase one or more products. Created in draft, submitted for processing. | orders | Shopping cart (which is pre-order) |
| LineItem | A single product entry within an order, with quantity and unit price. | orders | Cart item (pre-order) |
| Order Status | The lifecycle state of an order: draft → submitted → processing → shipped → delivered. | orders | Payment status (separate concern) |
| Tenant | An isolated business entity. All data belongs to exactly one tenant. | identity | User (a person within a tenant) |
| Product | A physical item available for sale in the catalog. | catalog | SKU (a specific variant of a product) |
| Recommendation | A personalized product suggestion based on user behavior and purchase history. | recommendations | Bestseller list (not personalized) |
| Fitness Function | An executable test that guards a domain invariant. Runs in CI. | evospec | Unit test (fitness functions guard invariants, not features) |
| Invariant | A business rule that must always be true. Violations indicate a bug. | evospec | Validation rule (which rejects input; invariants guard state) |
| Kill Criteria | Pre-defined conditions under which an experiment is abandoned. | evospec | Failure (kill criteria are healthy — they prevent over-investment) |
| Bounded Context | A boundary within which a domain model is consistent and well-defined. | DDD | Microservice (a context may span multiple services) |
