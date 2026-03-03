# Context Map — Orders System

## Bounded Contexts

```
┌─────────────────────────────────┐
│         Orders Context          │
│                                 │
│  Order ◄──── Item ────► Category│
│  (aggregate)  (child)   (ref)   │
│                                 │
│  Invariant: chemical + food     │
│  items CANNOT coexist in same   │
│  order (restriction_group)      │
└─────────────────────────────────┘
```

## Relationships

- **Orders ↔ External Consumers**: Published Language — the Orders system exposes API contracts and file schemas that external teams (UX, data analytics) consume to build integrations.
