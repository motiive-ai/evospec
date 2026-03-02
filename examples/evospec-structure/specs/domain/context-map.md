# Context Map

> How bounded contexts relate to each other (DDD strategic design).

## Contexts

| Context | Type | Owner | Description |
|---------|------|-------|-------------|
| orders | core | commerce-core | Order lifecycle, line items, state machine |
| catalog | core | commerce-core | Products, categories, pricing, inventory |
| identity | generic | platform | Authentication, authorization, tenancy |
| recommendations | supporting | growth | Personalized product suggestions |
| notifications | supporting | growth | Email, push, in-app notifications |

## Relationships

| Upstream | Downstream | Relationship |
|----------|-----------|-------------|
| identity | orders | ACL — orders validate JWT tokens but own their authorization rules |
| catalog | orders | conformist — orders reference product IDs and prices from catalog |
| catalog | recommendations | open-host — recommendations read catalog data via public API |
| orders | recommendations | open-host — recommendations read purchase history via public API |
| orders | notifications | published-language — order events trigger notification workflows |

## Diagram

```
                    ┌──────────────┐
                    │   identity   │ (generic)
                    │   platform   │
                    └──────┬───────┘
                           │ ACL
                           ▼
┌──────────┐     ┌──────────────┐     ┌───────────────────┐
│  catalog  │────▶│    orders    │────▶│   notifications   │
│   core    │     │     core     │     │    supporting     │
└─────┬─────┘     └──────────────┘     └───────────────────┘
      │                  │
      │ open-host        │ open-host
      ▼                  ▼
┌─────────────────────────┐
│    recommendations      │
│      supporting         │
└─────────────────────────┘
```
