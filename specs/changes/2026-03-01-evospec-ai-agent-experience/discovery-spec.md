# Discovery Spec: evospec-ai-agent-experience

> Zone: **edge** | Status: **draft** | Created: 2026-03-01

---

## 1. Strategic Fit (Roger Martin — Playing to Win)

**Winning Aspiration**: Be the standard spec-driven delivery toolkit for AI-assisted software development — the tool AI agents reach for when they need to understand what to build and why.

**Where to Play**: Development teams using AI coding agents (Windsurf/Cascade, Claude Code, Cursor, custom MCP clients) who need structured governance without slowing down AI-assisted delivery.

**How to Win**: Seamless MCP integration that makes specs a natural part of AI agent workflows — agents don't just read specs, they co-author, validate, and evolve them in real time.

---

## 2. Outcome & Opportunity (Teresa Torres — Continuous Discovery)

**Product Outcome**: Increase the percentage of AI-generated code changes that have a corresponding spec from ~0% (industry baseline) to >50% for adopting teams within 6 months.

**Customer Opportunity**: HMW make spec-driven delivery feel like a natural extension of the AI coding workflow, rather than an overhead step that developers skip?

**Opportunity Tree**:
```
Outcome: >50% of AI changes have specs
├── Opportunity 1: Agents don't know specs exist
│   ├── Solution A: Auto-suggest spec creation when agent starts a task
│   ├── Solution B: MCP discovery protocol — agents find evospec automatically
│   └── Solution C: IDE integration that surfaces relevant specs in context
├── Opportunity 2: Spec creation feels like overhead
│   ├── Solution A: One-shot spec generation from natural language description
│   ├── Solution B: Reverse-engineer specs from code changes after the fact
│   └── Solution C: Progressive spec filling — start minimal, add detail as risk increases
└── Opportunity 3: Specs go stale after creation
    ├── Solution A: Fitness functions that detect spec drift
    └── Solution B: Agent-driven spec updates as part of PR workflow
```

---

## 3. Empathy & Research (Design Thinking — Empathize)

**Research conducted**:
- [ ] User interviews (N = ?)
- [ ] Observation / shadowing
- [x] Competitor analysis (Spec Kit, OpenSpec, Agent OS — see docs/COMPARISON.md)
- [x] Domain expert consultation (internal dogfooding of evospec on itself)

**Key insights**:
1. Existing spec tools treat all changes equally — no risk-based classification
2. AI agents can generate specs but have no framework for knowing *when* specs are needed or *how much* spec is enough
3. The MCP protocol provides a natural integration point but needs to be discoverable and ergonomic

**Empathy artifacts**:
- docs/COMPARISON.md — competitor analysis
- This dogfooding exercise — evospec specifying itself

---

## 4. Problem Definition (Design Thinking — Define)

**Problem Statement** (human-centered, not business-centered):

> Developers using AI agents want to move fast, but when AI-generated changes touch core domain logic, the lack of specifications leads to subtle invariant violations that are expensive to fix later. They need a way to get proportional governance without breaking their flow.

**Reframes explored**:
1. "AI agents need guardrails" → focuses on constraint, misses the collaboration angle
2. "Developers need specs that write themselves" → focuses on automation, misses the learning/discovery dimension

---

## 5. Ideation (Design Thinking — Ideate)

**Ideas generated**: (aim for quantity before quality)

| # | Idea | Feasibility | Impact | Notes |
|---|------|-------------|--------|-------|
| 1 | Auto-classify changes via MCP — agent describes what it's about to do, evospec returns zone + required artifacts | High | High | Leverages existing classify algorithm |
| 2 | "Spec-aware commits" — git hook that checks if changed files have a covering spec | High | Medium | Low friction, but reactive not proactive |
| 3 | Agent-driven reverse engineering — after coding, agent runs `reverse cli` to update traceability | High | Medium | Already partially built |
| 4 | Real-time invariant checking during agent coding sessions via MCP | Medium | High | Requires streaming MCP, more complex |

**Selected approach**: #1 + #3 — Auto-classification via MCP is the highest-impact, most feasible starting point. Reverse engineering as a follow-up keeps specs in sync.

---

## 6. Assumptions & Experiments (Teresa Torres)

**Riskiest assumptions** (ordered by risk, highest first):

| ID | Assumption | Category | Risk | Status | Success Criteria |
|----|-----------|----------|------|--------|-----------------|
| A-001 | AI agents will use MCP tools proactively (not just when prompted) if the tools are discoverable | desirability | high | untested | ≥3 out of 5 tested agents call evospec tools without explicit user instruction |
| A-002 | Auto-classification can accurately determine zone from a natural language change description | feasibility | high | untested | ≥80% agreement with human classification on 20 test cases |
| A-003 | Developers will accept AI-generated specs as "good enough" starting points | usability | medium | untested | ≥70% of generated specs accepted with minor edits in user testing |
| A-004 | The overhead of MCP server startup doesn't noticeably slow agent workflows | feasibility | medium | untested | <500ms cold start, <50ms per tool call |

> **Status lifecycle**: untested → testing → validated / invalidated → pivoted

**Categories**: desirability (do users want it?), feasibility (can we build it?), viability (should we build it?), usability (can users use it?)

**"What would have to be true"** for the selected solution to work? (Roger Martin)
1. AI agents must be capable of calling MCP tools proactively (not just reactively)
2. Natural language descriptions must contain enough signal to determine risk zone
3. Developers must trust AI-generated spec artifacts enough to use them as starting points
4. MCP server performance must be fast enough to not disrupt the coding flow

---

## 7. Experiments (Continuous Discovery — Weekly Cycle)

> Each experiment tests one or more assumptions. Record results here.

| ID | Assumption | Type | Description | N | Started | Result | Confidence | Decision |
|----|-----------|------|-------------|---|---------|--------|------------|----------|
| EXP-001 | A-002 | spike | Run classify algorithm against 20 natural language descriptions, compare with human judgment | 20 | | | | |
| EXP-002 | A-004 | spike | Benchmark MCP server cold start and tool call latency | 1 | | | | |

> **Types**: prototype, interview, survey, A/B-test, wizard-of-oz, analytics, spike
>
> **Decisions**: continue (need more data), pivot (change approach), kill (abandon), promote-to-core (codify as invariant)

### Current experiment

**What are we testing?** A-002 — Can auto-classification work from natural language?

**Test plan**:
- **Who**: Internal team (N = 1, dogfooding)
- **What**: 20 change descriptions covering edge, hybrid, and core zones
- **How**: Run through classify algorithm, compare with expert judgment
- **Success criteria**: ≥80% agreement (16 out of 20)
- **Timeline**: 1 week

**Prototype**: Use existing `classify_change` MCP tool with synthetic inputs

---

## 8. Kill Criteria & Deadline

**When do we stop?**

> If after 3 weeks of experimentation, auto-classification accuracy is below 60% OR MCP cold start exceeds 2 seconds, we pivot to a simpler "manual classify + template" approach without real-time agent integration.

**Hard deadline**: 2026-03-22 (3 weeks from creation)

**Escalation**: Project maintainers decide if results are ambiguous.

---

## 9. Organizational Risk (Hogan)

**Potential derailers**:
- Over-engineering the MCP integration before validating that agents actually use it
- Perfectionism on spec quality — "good enough" specs from AI are better than no specs at all

**Mitigation**:
- Time-box experiments strictly (1 week each)
- Ship the simplest version that proves the hypothesis

---

## 10. Domain Boundaries

**Bounded contexts touched**:
- MCP Server (supporting) — new tool capabilities
- Spec Engine (core) — classification algorithm consumed via MCP

**Entities affected**:
- ChangeSpec — may be auto-created by agents
- Classification — algorithm needs to work from natural language, not just interactive prompts

**Dependencies on other teams**:
- AI agent providers (Windsurf, Claude Code) — need MCP client support (x-as-a-service)

---

## 11. Learning Log (Living Section)

> **This is the most important section.** Update it after every experiment or checkpoint.
> Each entry should answer: What did we learn? What changed? What's next?

### Iteration 1

| Date | Experiment | What we learned | Impact on spec | What's next |
|------|-----------|----------------|----------------|------------|
| 2026-03-01 | Dogfooding | EvoSpec can spec itself; `reverse cli` fills a gap for non-web projects; domain contract template works well for capturing CLI tool domains | Added `reverse cli` command to evospec | Run EXP-001 (auto-classification accuracy) |

### Pivots

| Iteration | Date | From | To | Reason |
|-----------|------|------|----|--------|
| | | | | |

### Promotion Candidates

| Assumption | Evidence | Proposed Invariant | Ready? |
|-----------|----------|--------------------|--------|
| | | | |
