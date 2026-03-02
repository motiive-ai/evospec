# EvoSpec Manifesto

**Progressive specs at the edge. Contracts in the core.**

---

## The Problem

Software teams are caught between two forces:

1. **Discovery never stops.** Products evolve through continuous learning (Teresa Torres). Hypotheses change weekly. UX experiments invalidate assumptions. Business strategy pivots mid-quarter. Trying to freeze requirements before building is fiction.

2. **Domains demand stability.** Core business rules, data invariants, authorization policies, and audit trails cannot be "explored" safely. When you break an invariant, you break trust — with users, regulators, and your future self.

The error most organizations make is **treating everything the same way**: either fully exploratory ("move fast and break things") or fully specified ("nothing ships without a 40-page SDD"). Both fail.

**EvoSpec exists because not every part of the system should be specified the same way.**

---

## Intellectual Foundations

EvoSpec is not invented from scratch. It synthesizes decades of proven thinking into a single, coherent delivery system.

### 1. Domain-Driven Design — Eric Evans, Vaughn Vernon

> "The heart of software is its ability to solve domain-related problems for its users." — Eric Evans

**What we take:**
- **Bounded Contexts**: Every change lives inside a context with explicit boundaries
- **Ubiquitous Language**: Domain terms are defined once, used everywhere — in specs, code, tests, and conversations
- **Aggregates & Invariants**: Core state has rules that must never be violated
- **Context Mapping**: Relationships between contexts are explicit (conformist, anti-corruption layer, shared kernel, etc.)
- **Strategic Design**: Not all parts of the system deserve the same investment — identify the core domain vs. supporting vs. generic

**How it shapes EvoSpec:**
- Every `domain-contract.md` declares a bounded context, its entities, and its invariants
- Invariants are written as testable propositions, not prose
- The classification system (edge/hybrid/core) maps directly to strategic design

### 2. Continuous Discovery — Teresa Torres

> "Good product discovery starts with a clear outcome, not a feature list."

**What we take:**
- **Opportunity Solution Trees**: Outcomes → Opportunities → Solutions → Experiments
- **Assumption Testing**: Every solution carries assumptions; the riskiest ones get tested first
- **Weekly Touchpoints**: Discovery is continuous, not a phase
- **Learning Over Shipping**: The goal isn't to build features; it's to learn what creates value

**How it shapes EvoSpec:**
- `discovery-spec.md` is structured as an opportunity tree, not a feature spec
- Every discovery spec has explicit assumptions and falsification criteria
- Edge-zone work is governed by learning milestones, not delivery milestones
- "Kill criteria" are first-class: when do we stop if the hypothesis fails?

### 3. Design Thinking — IDEO, Stanford d.school

> "Design thinking is a human-centered approach to innovation that draws from the designer's toolkit to integrate the needs of people, the possibilities of technology, and the requirements for business success." — Tim Brown

**What we take:**
- **Empathize → Define → Ideate → Prototype → Test**: The non-linear, iterative loop
- **Diverge before you converge**: Generate many options before choosing
- **"How Might We" framing**: Problems as opportunities, not constraints
- **Rapid prototyping**: Make ideas tangible quickly to learn
- **Double Diamond**: Discover the right problem, then discover the right solution

**How it shapes EvoSpec:**
- Edge-zone specs use the Design Thinking loop explicitly
- `discovery-spec.md` has dedicated sections for empathy research, problem reframing, and ideation
- Prototyping is a valid "deliverable" for edge work — not just code
- The framework encourages divergent thinking before converging on implementation
- AI agents in the exploratory zone operate as "ideation accelerators", generating options for human evaluation

### 4. Evolutionary Architecture — Neal Ford, Rebecca Parsons, Patrick Kua

> "An evolutionary architecture supports guided, incremental change across multiple dimensions."

**What we take:**
- **Fitness Functions**: Measurable, automated checks that protect architectural properties
- **Incremental Change**: Architecture evolves one decision at a time
- **Multiple Dimensions**: Performance, security, data integrity, operability — all need protection
- **Guided, Not Accidental**: Evolution has direction; it's not random mutation

**How it shapes EvoSpec:**
- Core-zone changes require at least one fitness function
- `domain-contract.md` has a dedicated `fitness_functions` section
- Guardrails are executable (tests, CI checks, schema validation), not just documented
- The `evospec check` command runs fitness functions as part of the development loop

### 5. Architecture Decision Records — Michael Nygard

> "Architecture represents the significant design decisions that shape a system, where 'significant' is measured by cost of change." — Grady Booch

**What we take:**
- **Lightweight governance**: One decision, one record, one page
- **Context + Decision + Consequences**: The minimum viable structure
- **Immutable log**: Decisions are never deleted, only superseded
- **Status lifecycle**: Proposed → Accepted → Deprecated → Superseded

**How it shapes EvoSpec:**
- Every spec can link to one or more ADRs
- ADRs include a **reversibility assessment** (how hard is it to undo this?)
- The `evospec adr` command manages the decision log
- ADRs are first-class citizens in the spec graph, not an afterthought

### 6. Team Topologies — Matthew Skelton, Manuel Pais

> "The primary benefit of a platform is to reduce the cognitive load on stream-aligned teams." — Martin Fowler, summarizing Team Topologies

**What we take:**
- **Four team types**: Stream-aligned, Platform, Enabling, Complicated-subsystem
- **Three interaction modes**: Collaboration, X-as-a-Service, Facilitating
- **Cognitive load as a design constraint**: Teams can only handle so much complexity
- **Conway's Law (and the Inverse)**: Architecture mirrors communication structures — design both intentionally

**How it shapes EvoSpec:**
- Every spec declares an **owner** (which team, which type)
- The classification system considers cognitive load: is this change adding complexity to a team that's already overloaded?
- Platform-provided capabilities are referenced, not re-specified
- Interaction mode between teams is documented when a change crosses context boundaries

### 7. Strategy as Choice — Roger Martin, A.G. Lafley

> "Strategy is an integrated set of choices that uniquely positions the firm to create sustainable advantage and superior value relative to the competition."

**What we take:**
- **The Strategy Choice Cascade**: Winning Aspiration → Where to Play → How to Win → Must-Have Capabilities → Enabling Management Systems
- **Choices, not plans**: Strategy is a set of bets, not a roadmap
- **Integrated set**: Choices must reinforce each other
- **Reverse logic**: Start from "what would have to be true" for each option to work

**How it shapes EvoSpec:**
- Discovery specs include a "strategic fit" section: how does this change connect to where we play and how we win?
- The classification system asks: does this change strengthen a must-have capability or undermine one?
- "What would have to be true" is a required framing for high-risk assumptions

### 8. Organizational Personality & Leadership Risk — Robert Hogan

> "The personality of the leader becomes the personality of the organization."

**What we take:**
- **Dark-side derailers**: Under stress, strengths become liabilities (e.g., "attention to detail" becomes "micromanagement"; "boldness" becomes "over-promising")
- **Organizational risk signals**: The culture and personality of the team/org shapes what risks are likely to be missed
- **Leadership as constraint**: Technical decisions are shaped by organizational dynamics, not just technical logic

**How it shapes EvoSpec:**
- The classification system includes an **organizational risk** dimension: is this change likely to be derailed by cultural patterns?
- ADRs can reference organizational constraints (e.g., "this decision was made because team X has a pattern of over-engineering")
- The framework acknowledges that **process alone doesn't fix behavioral patterns** — awareness is the first step

### 9. The Knowledge Funnel — Roger Martin

> "The most successful businesses move knowledge through the funnel: from mystery to heuristic to algorithm." — Roger Martin, *The Design of Business*

**What we take:**
- **Mystery**: A question we can't yet answer. We don't know what we don't know. The problem space is wide open.
- **Heuristic**: A rule of thumb. We've learned enough to have a pattern, but it still requires judgment and adaptation.
- **Algorithm**: A codified, repeatable process. It can be automated, delegated, or enforced without judgment.

**The funnel is directional but not instant:**
```
Mystery ──── "We don't know what users need"
   │
   ▼  (Design Thinking: Empathize → Define → Ideate → Prototype → Test)
   │
Heuristic ── "Users who see personalized recommendations convert 2x better"
   │
   ▼  (Domain Modeling: Entities, invariants, contracts, fitness functions)
   │
Algorithm ── "Every Order MUST have at least one LineItem before checkout"
              → enforced by schema validation, API contract, CI gate
```

**How it shapes EvoSpec:**
- **Edge zone = Mystery territory.** We use Design Thinking and Continuous Discovery to explore. Specs are hypotheses. The goal is learning.
- **Hybrid zone = Heuristic territory.** We've learned something, but the domain model is emerging. Specs start to include invariants, but they're still negotiable.
- **Core zone = Algorithm territory.** Knowledge has been codified. Invariants are non-negotiable. Fitness functions enforce them automatically.
- **The framework's job is to help teams move knowledge through the funnel** — from mystery to heuristic to algorithm — without forcing premature codification or allowing permanent ambiguity.
- Design Thinking is the engine that drives knowledge from Mystery to Heuristic. DDD is the engine that drives knowledge from Heuristic to Algorithm.

---

## The Two Layers

EvoSpec makes an explicit architectural separation that most frameworks leave implicit:

### Discovery Layer (the edge)

| Property | Character |
|----------|----------|
| **Pace** | Fast, iterative, experimental |
| **Artifacts** | Discovery Specs, prototypes, A/B tests, user interviews |
| **Governance** | Metrics + kill criteria. Light touch. |
| **What lives here** | UX flows, experimental features, new workflows, hypotheses |
| **Knowledge stage** | Mystery → Heuristic |
| **Design Thinking phase** | Empathize → Define → Ideate → Prototype → Test |
| **Can change** | Yes, freely. That's the point. |
| **Risk of change** | Low — isolated, reversible, user-facing |

### Core Engine (the center)

| Property | Character |
|----------|----------|
| **Pace** | Deliberate, versioned, audited |
| **Artifacts** | Domain Contracts, ADRs, fitness functions, schema migrations |
| **Governance** | Invariants + fitness functions + CI gates. Strict. |
| **What lives here** | Canonical entities, validation rules, authorization policies, state machines, API contracts, billing logic, audit trails |
| **Knowledge stage** | Heuristic → Algorithm |
| **DDD focus** | Aggregates, bounded contexts, ubiquitous language, invariants |
| **Can change** | Yes, but through contracts, migrations, and versioning |
| **Risk of change** | High — affects data integrity, security, compliance |

### The Boundary Between Them

The most dangerous place in any system is where **Discovery touches Core**. This is the Hybrid zone.

When an experimental feature needs to write to a canonical entity, or when a UX flow needs to trigger a state transition, you're crossing the boundary. This is where:
- Discovery Specs need Domain Contracts (at least minimal ones)
- Contract tests protect the Core from Discovery volatility
- ADRs document why the boundary was crossed and what the consequences are

**The error most teams make**: treating the whole system as either Discovery ("move fast") or Core ("spec everything"). The skill is knowing which layer you're in and applying the right governance.

---

## AI Agent Integration

EvoSpec is designed to work **with** AI coding agents (Windsurf/Cascade, Claude Code, Cursor, GitHub Copilot Workspace, etc.), not as a replacement for them.

### The AI Contract

1. **AI generates, humans review.** AI can draft discovery specs, suggest invariants, reverse-engineer domain contracts from code, and generate implementation tasks. Humans approve, refine, and own the consequences.
2. **Specs are the AI's instructions.** A well-written spec.yaml + discovery-spec.md or domain-contract.md gives an AI agent enough context to implement correctly.
3. **Guardrails constrain the AI.** Fitness functions and invariants are the "narrow bridges" (Anthropic) where AI must follow strict rules.
4. **Tasks are the AI's work queue.** The tasks.md file is a dependency-ordered, machine-parseable implementation plan.

### Supported Agents

EvoSpec ships with integration files for:
- **Windsurf (Cascade)**: `.windsurf/workflows/evospec.*.md` — slash commands for the full delivery loop
- **Claude Code**: `CLAUDE.md` — project context file that Claude Code reads automatically
- **Generic**: Any agent can read `spec.yaml`, `discovery-spec.md`, `domain-contract.md`, and `tasks.md` as structured context

### The Delivery Loop with AI

```
Human: /evospec.discover "smart recommendations" → AI drafts discovery-spec.md
Human: reviews, refines
Human: /evospec.contract                        → AI drafts domain-contract.md (if hybrid/core)
Human: reviews, adds invariants
Human: /evospec.tasks                           → AI generates tasks.md
Human: reviews task order
Human: /evospec.implement                       → AI executes tasks phase by phase
Human: reviews code
Human: /evospec.check                           → AI runs fitness functions + spec validation
```

---

## The EvoSpec Model

### Three Zones

Every change is classified into one of three zones:

| Zone | Character | Spec Required | Guardrails |
|------|-----------|---------------|------------|
| **Edge** (Exploratory) | Hypothesis-driven, fast iteration, learning-first | Discovery Spec | Metrics + kill criteria |
| **Hybrid** | Touches UX and domain; needs coordination | Discovery Spec + Domain Contract (minimal) | Contract tests at boundaries |
| **Core** (Structural) | Invariants, state, authorization, audit, billing | Domain Contract (full) | Fitness functions + CI gates |

### Three Artifacts

| Artifact | Purpose | Required For |
|----------|---------|--------------|
| **Discovery Spec** | What we're learning, why, and how we'll know | Edge, Hybrid |
| **Domain Contract** | What must remain true, always | Core, Hybrid (minimal) |
| **ADR** | Why we chose X over Y, and what it costs | Any zone, when decisions are architecturally significant |

### The Delivery Loop

```
Classify → Specify → Decide → Implement → Guard → Learn → (loop)
```

1. **Classify**: What zone is this? What risk level? Who owns it?
2. **Specify**: Write the appropriate artifacts (discovery spec, domain contract, or both)
3. **Decide**: Record architectural decisions (ADRs)
4. **Implement**: Build the thing
5. **Guard**: Run fitness functions, contract tests, schema validations
6. **Learn**: Did the hypothesis hold? Did the invariants survive? Update specs.

---

## What EvoSpec Is Not

- **Not a replacement for Agile/Scrum/Kanban.** It's a specification layer, not a delivery methodology.
- **Not architecture astronautics.** Specs should be short. One page is better than ten.
- **Not documentation for documentation's sake.** Every artifact must be either actionable or verifiable.
- **Not a new religion.** Use what helps. Skip what doesn't. Adapt to your context.

---

## Guiding Principles

1. **Specs are proportional to risk.** Low-risk edge work gets a one-page hypothesis. High-risk core work gets invariants, contracts, and fitness functions.
2. **Invariants are testable propositions, not prose.** "Every query on a tenant-scoped entity must filter by tenant_id" is a fitness function, not a paragraph.
3. **Decisions are logged, not buried.** ADRs are first-class. They explain *why*, which code never can.
4. **Discovery is continuous.** Specs evolve. The framework supports iteration, not waterfall.
5. **Teams own contexts.** Specs map to bounded contexts, bounded contexts map to teams.
6. **AI accelerates, humans decide.** AI can generate specs, reverse-engineer contracts, and suggest fitness functions. Humans review, approve, and own the consequences.
7. **Guardrails are executable.** A guardrail that lives only in a document is a suggestion, not a guardrail.

---

## References

- Evans, E. (2003). *Domain-Driven Design: Tackling Complexity in the Heart of Software*. Addison-Wesley.
- Vernon, V. (2013). *Implementing Domain-Driven Design*. Addison-Wesley.
- Torres, T. (2021). *Continuous Discovery Habits*. Product Talk LLC.
- Ford, N., Parsons, R., Kua, P. (2017). *Building Evolutionary Architectures*. O'Reilly.
- Skelton, M., Pais, M. (2019). *Team Topologies*. IT Revolution.
- Martin, R., Lafley, A.G. (2013). *Playing to Win: How Strategy Really Works*. Harvard Business Review Press.
- Hogan, R. (2006). *Personality and the Fate of Organizations*. Psychology Press.
- Nygard, M. (2011). "Documenting Architecture Decisions." Cognitect Blog.
- Brown, T. (2009). *Change by Design: How Design Thinking Transforms Organizations*. HarperBusiness.
- Anthropic. (2024). "Building effective agents." Anthropic Research.
- Thoughtworks. (2025). *Technology Radar Vol. 32*.

---

*EvoSpec: Progressive specs at the edge. Contracts in the core.*
