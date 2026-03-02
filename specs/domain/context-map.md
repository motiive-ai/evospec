# Context Map — EvoSpec

> How bounded contexts relate to each other (DDD strategic design).

## Contexts

| Context | Type | Owner | Description |
|---------|------|-------|-------------|
| spec-engine | core | evospec-core | Change specs, invariants, fitness functions, classification, checking, discovery loop |
| domain-management | core | evospec-core | Entity registry, bounded contexts, features, glossary, context map |
| agent-integration | supporting | evospec-core | Canonical workflows, multi-platform generator, MCP server |
| reverse-engineering | supporting | evospec-core | API/DB/CLI/deps scanning, entity extraction |
| cli | generic | evospec-core | Click-based CLI layer, thin wrapper over core modules |

## Relationships

| Upstream | Downstream | Relationship | Notes |
|----------|-----------|-------------|-------|
| spec-engine | cli | open-host | CLI calls core functions directly |
| spec-engine | agent-integration | published-language | MCP server exposes spec-engine entities as tools/resources |
| domain-management | spec-engine | shared-kernel | Config loader merges domain files (entities, contexts, features) into config dict |
| domain-management | agent-integration | published-language | MCP `evospec://entities` resource reads from domain files |
| reverse-engineering | domain-management | conformist | Reverse scanners output entity registry YAML that conforms to domain-management format |
| spec-engine | reverse-engineering | open-host | Reverse deps reads spec.yaml traceability to map endpoints |
| agent-integration | cli | conformist | CLI `generate agents` command wraps the generator |

## Diagram

```
                    ┌─────────────────┐
                    │   cli (generic)  │
                    └────────┬────────┘
                             │ calls
                    ┌────────▼────────┐
                    │  spec-engine    │◄──── shared-kernel ────┐
                    │     (core)      │                        │
                    └───┬─────────┬───┘              ┌────────▼────────┐
                        │         │                  │ domain-management│
           open-host    │         │ published-lang   │     (core)      │
                        │         │                  └────────▲────────┘
               ┌────────▼──┐  ┌──▼──────────────┐           │ conformist
               │ reverse-  │  │ agent-integration│           │
               │engineering│  │  (supporting)    │    ┌──────┴──────┐
               │(supporting│  └─────────────────┘    │  (outputs)  │
               └───────────┘                         └─────────────┘
```
