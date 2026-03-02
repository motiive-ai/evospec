# EvoSpec vs. Other Frameworks

A honest comparison of spec-driven development tools for AI-assisted coding.

---

## Overview

| | **EvoSpec** | **Spec Kit** (GitHub) | **OpenSpec** (Fission AI) | **Agent OS** (Builder Methods) |
|---|---|---|---|---|
| **Focus** | Two-layer spec system (Discovery + Core Engine) with domain modeling | Linear spec → plan → tasks pipeline | Lightweight proposal → specs → tasks flow | Codebase standards injection + spec shaping |
| **Language** | Python (pipx) | Python (pip) | Node.js (npm) | Shell scripts + YAML |
| **AI Agents** | Windsurf, Claude Code, **MCP (any agent)** | 11+ agents (Windsurf, Claude, Cursor, etc.) | 20+ tools | Claude Code, Cursor, Antigravity |
| **MCP Server** | ✅ 12 tools + 4 resources + 2 prompts | ❌ | ❌ | ❌ |
| **Fitness Runner** | ✅ Executes pytest/jest from spec.yaml | ❌ | ❌ | ❌ |
| **Features Registry** | ✅ Lifecycle tracking in evospec.yaml | ❌ | ❌ | ❌ |
| **License** | MIT | MIT | MIT | MIT |
| **Schema** | JSON Schema for spec.yaml | Markdown templates | YAML + Markdown | YAML config |

---

## What Each Framework Does Well

### Spec Kit (GitHub)
- **Mature pipeline**: Specify → Clarify → Plan → Tasks → Implement → Analyze
- **Constitution system**: Project-level principles that constrain all specs
- **Broad agent support**: Works with 11+ AI coding agents
- **Quality validation**: Built-in spec quality checklists and cross-artifact analysis
- **Battle-tested**: Backed by GitHub, large community

**Best for**: Teams that want a complete, opinionated linear pipeline from spec to code.

### OpenSpec (Fission AI)
- **Lightweight**: Minimal ceremony, fast to start
- **Propose workflow**: Single command creates proposal + specs + design + tasks
- **Fluid iteration**: No rigid phase gates, update any artifact anytime
- **Archive system**: Clean lifecycle management for completed features
- **Wide tool support**: 20+ AI assistants supported

**Best for**: Solo developers or small teams that want speed over structure.

### Agent OS (Builder Methods)
- **Standards-first**: Extracts and injects codebase conventions into AI context
- **Discover → Deploy pattern**: Learns your patterns, then enforces them
- **Spec shaping**: Helps write better specs based on your codebase
- **Minimal footprint**: Shell scripts + YAML, no heavy runtime

**Best for**: Teams that already have strong conventions and want to codify them for AI agents.

---

## What EvoSpec Does Differently

### 1. Two Layers, Not One Pipeline

Other frameworks treat all changes the same way. EvoSpec recognizes that **not every part of the system should be specified the same way**:

| | Spec Kit / OpenSpec / Agent OS | EvoSpec |
|---|---|---|
| UX experiment | Full spec pipeline | **Edge zone**: Discovery Spec + kill criteria. Light touch. |
| Database schema change | Full spec pipeline | **Core zone**: Domain Contract + invariants + fitness functions. Strict. |
| Feature touching both | Full spec pipeline | **Hybrid zone**: Both artifacts, contract tests at boundaries. |

### 2. Domain-Driven Design as First-Class Citizen

No other spec-kit integrates DDD (Evans/Vernon) at the model level:

| Concept | Spec Kit | OpenSpec | Agent OS | EvoSpec |
|---------|----------|---------|----------|---------|
| Bounded Contexts | ❌ | ❌ | ❌ | ✅ Context registry in evospec.yaml |
| Ubiquitous Language | ❌ | ❌ | ❌ | ✅ Glossary + context-map |
| Invariants | ❌ | ❌ | ❌ | ✅ Testable propositions in spec.yaml |
| Aggregates / Entities | ❌ | ❌ | ❌ | ✅ Domain contract template |
| State Machines | ❌ | ❌ | ❌ | ✅ Transitions + forbidden transitions |
| Strategic Design | ❌ | ❌ | ❌ | ✅ Core / supporting / generic classification |

### 3. Executable Guardrails (Fitness Functions)

EvoSpec requires core-zone changes to have **automated enforcement**, not just documentation:

```yaml
# spec.yaml — invariants are testable, not prose
invariants:
  - id: "INV-001"
    statement: "Every Order must have at least one LineItem"
    enforcement: "integration-test"
    fitness_function: "tests/fitness/test_order_integrity.py"
```

Other frameworks document requirements. EvoSpec **enforces** them.

### 4. The Knowledge Funnel (Roger Martin)

EvoSpec explicitly tracks where knowledge is on the Mystery → Heuristic → Algorithm continuum:

```
Mystery   → Design Thinking explores  → Edge zone (discovery-spec.md)
Heuristic → Patterns emerging          → Hybrid zone (both artifacts)
Algorithm → Codified, enforceable      → Core zone (domain-contract.md + fitness functions)
```

This prevents the two most common errors:
- **Premature codification**: Treating a mystery as an algorithm (over-specifying edge work)
- **Permanent ambiguity**: Treating an algorithm as a mystery (under-specifying core work)

### 5. Integrated Intellectual Framework

EvoSpec synthesizes 9 proven frameworks. Others use 1-2:

| Framework | Spec Kit | OpenSpec | Agent OS | EvoSpec |
|-----------|----------|---------|----------|---------|
| DDD (Evans/Vernon) | ❌ | ❌ | ❌ | ✅ |
| Continuous Discovery (Torres) | ❌ | ❌ | ❌ | ✅ |
| Design Thinking (IDEO) | ❌ | ❌ | ❌ | ✅ |
| Evolutionary Architecture (Ford) | ❌ | ❌ | ❌ | ✅ |
| Team Topologies (Skelton/Pais) | ❌ | ❌ | ❌ | ✅ |
| Strategy as Choice (Martin) | ❌ | ❌ | ❌ | ✅ |
| Knowledge Funnel (Martin) | ❌ | ❌ | ❌ | ✅ |
| ADRs (Nygard) | Partial | ❌ | ❌ | ✅ |
| Org Personality (Hogan) | ❌ | ❌ | ❌ | ✅ |

### 6. MCP Server (Programmatic Agent Access)

EvoSpec is the only spec framework that exposes an **MCP server**:

```
Agent → MCP Protocol → EvoSpec Server → list_specs / check_spec / run_fitness_functions / ...
```

Other frameworks rely on slash commands (text prompts). EvoSpec gives agents **structured tools** they can call programmatically with typed parameters and JSON responses. This means:
- Agents can programmatically read specs, check invariants, and run fitness functions
- Task progress is machine-tracked (not just markdown checkboxes)
- Feature lifecycle is queryable (`list_features()` returns structured data)
- Any MCP-compatible agent works — not just the ones with specific slash command support

### 7. Reverse Engineering

EvoSpec can scan existing codebases and generate spec stubs:

```bash
evospec reverse api --framework fastapi   # Discover endpoints → traceability
evospec reverse db --source app/models    # Discover entities → domain contract stubs
```

No other framework offers this.

---

## When to Use What

| Situation | Recommended |
|-----------|-------------|
| Solo dev, small features, want speed | **OpenSpec** |
| Team with existing conventions to codify | **Agent OS** |
| Linear pipeline, broad agent support, GitHub ecosystem | **Spec Kit** |
| Systems with both exploratory UX and stable core domain | **EvoSpec** |
| Multi-tenant SaaS with auth, billing, audit invariants | **EvoSpec** |
| DDD practitioners who want spec tooling | **EvoSpec** |
| Teams that need executable guardrails in CI | **EvoSpec** |

---

## Honest Limitations of EvoSpec

- **Newer**: Less battle-tested than Spec Kit (GitHub-backed) or OpenSpec
- **More conceptual overhead**: 9 intellectual frameworks is a lot to absorb. The MANIFESTO is dense.
- **Python-only CLI**: Spec Kit and OpenSpec offer Node.js. Agent OS is shell-based.
- **Fewer agent integrations** (currently): Windsurf + Claude Code. Others support 11-20+.
- **Opinionated about domain modeling**: If you don't care about DDD or bounded contexts, EvoSpec may feel heavyweight.

---

## Can They Be Combined?

Yes. EvoSpec is compatible with:
- **Agent OS**: Use Agent OS for standards injection, EvoSpec for spec governance. They solve different problems.
- **Spec Kit**: You could use Spec Kit's `specify` CLI for scaffolding and EvoSpec's domain contracts + fitness functions for core governance.
- **OpenSpec**: OpenSpec's lightweight proposal flow could feed into EvoSpec's classification system.

EvoSpec doesn't replace your AI agent workflow. It adds a **domain-aware governance layer** on top.

---

## Links

- **EvoSpec**: [github.com/evospec/evospec](https://github.com/evospec/evospec)
- **Spec Kit**: [github.com/github/spec-kit](https://github.com/github/spec-kit)
- **OpenSpec**: [github.com/Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec)
- **Agent OS**: [github.com/buildermethods/agent-os](https://github.com/buildermethods/agent-os)
