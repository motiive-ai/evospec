# EvoSpec Examples

| Example | What It Shows |
|---------|--------------|
| [`evospec-structure/`](evospec-structure/) | Complete single-repo project — core + edge specs, split domain files (`entities.yaml`, `contexts.yaml`, `features.yaml`), glossary, context map, ADRs, fitness functions |
| [`multi-system-ux-discovery/`](multi-system-ux-discovery/) | **Multi-repo** setup — 3 services (Java/Spring Boot, Python/FastAPI, React/TS), each with its own `evospec.yaml`. UX repo references backends via `upstreams[]` for cross-repo invariant checking |

## Quick Start

```bash
# Explore the structure example (single repo)
cd examples/evospec-structure
evospec check

# Explore the multi-system example (3 repos)
# Each service has its own evospec.yaml + specs/domain/
cd examples/multi-system-ux-discovery

# Check from the UX repo — it reads upstream invariants from order-service + inventory-service
cd smart-cart-ui
evospec check

# Or check from the top-level meta-project
cd ..
evospec check

# Reverse-engineer endpoints
evospec reverse api --framework spring --source order-service
evospec reverse api --framework fastapi --source inventory-service
evospec reverse deps --source smart-cart-ui
```

## Domain File Structure

Domain data lives in `specs/domain/` (not in `evospec.yaml`):

```
specs/domain/
├── entities.yaml    # Entity registry (fields, relationships, invariants)
├── contexts.yaml    # Bounded contexts (owner, type)
├── features.yaml    # Feature lifecycle (status, knowledge stage)
├── glossary.md      # Ubiquitous language
└── context-map.md   # Context relationships
```

## Cross-Repo Sharing

Downstream repos reference upstream repos in `evospec.yaml`:

```yaml
upstreams:
  - name: "order-service"
    path: "../order-service"
```

This makes upstream entities and invariants visible to `evospec check` and the MCP server.
