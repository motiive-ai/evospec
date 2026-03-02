# Discovery Spec: {{ title }}

> Zone: **{{ zone }}** | Status: **{{ status }}** | Created: {{ created_at }}

---

## 1. Strategic Fit (Roger Martin — Playing to Win)

**Winning Aspiration**: How does this connect to what winning looks like?
<!-- e.g., "Be the most effective personal development platform for professionals." -->

**Where to Play**: Which customer segment, geography, or channel?
<!-- e.g., "Young professionals seeking career growth via mobile-first experience." -->

**How to Win**: What is the competitive advantage this change enables?
<!-- e.g., "AI-personalized learning paths that adapt to DISC behavioral profiles." -->

---

## 2. Outcome & Opportunity (Teresa Torres — Continuous Discovery)

**Product Outcome**: What metric will this change influence?
<!-- e.g., "Increase weekly active users by 15% within 3 months." -->

**Customer Opportunity**: What unmet need or pain point?
<!-- Use "How Might We" framing. -->
<!-- e.g., "HMW help users find relevant products without feeling overwhelmed by choices?" -->

**Opportunity Tree**:
```
Outcome: [metric]
├── Opportunity 1: [pain point / need]
│   ├── Solution A: [idea]
│   ├── Solution B: [idea]
│   └── Solution C: [idea]
└── Opportunity 2: [pain point / need]
    └── ...
```

---

## 3. Empathy & Research (Design Thinking — Empathize)

**Research conducted**:
- [ ] User interviews (N = ?)
- [ ] Observation / shadowing
- [ ] Journey mapping
- [ ] Survey / quantitative data
- [ ] Competitor analysis
- [ ] Domain expert consultation

**Key insights**:
1. ...
2. ...
3. ...

**Empathy artifacts**: <!-- links to recordings, transcripts, maps -->
- ...

---

## 4. Problem Definition (Design Thinking — Define)

**Problem Statement** (human-centered, not business-centered):
<!-- Bad: "We need to increase retention by 10%." -->
<!-- Good: "Users abandon onboarding because they can't articulate their goals without guidance." -->

> ...

**Reframes explored**:
<!-- Try at least 2 different framings of the same problem. -->
1. ...
2. ...

---

## 5. Ideation (Design Thinking — Ideate)

**Ideas generated**: (aim for quantity before quality)

| # | Idea | Feasibility | Impact | Notes |
|---|------|-------------|--------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

**Selected approach**: #? — Why?

---

## 6. Assumptions & Experiments (Teresa Torres)

**Riskiest assumptions** (ordered by risk, highest first):

| ID | Assumption | Category | Risk | Status | Success Criteria |
|----|-----------|----------|------|--------|-----------------|
| A-001 | | desirability | high | untested | |
| A-002 | | feasibility | medium | untested | |
| A-003 | | viability | low | untested | |

> **Status lifecycle**: untested → testing → validated / invalidated → pivoted

**Categories**: desirability (do users want it?), feasibility (can we build it?), viability (should we build it?), usability (can users use it?)

**"What would have to be true"** for the selected solution to work? (Roger Martin)
1. ...
2. ...
3. ...

---

## 7. Experiments (Continuous Discovery — Weekly Cycle)

> Each experiment tests one or more assumptions. Record results here.

| ID | Assumption | Type | Description | N | Started | Result | Confidence | Decision |
|----|-----------|------|-------------|---|---------|--------|------------|----------|
| EXP-001 | A-001 | | | | | | | |

> **Types**: prototype, interview, survey, A/B-test, wizard-of-oz, analytics, spike
>
> **Decisions**: continue (need more data), pivot (change approach), kill (abandon), promote-to-core (codify as invariant)

### Current experiment

**What are we testing?**
<!-- Link to assumption ID -->

**Test plan**:
- **Who**: target users (N = ?)
- **What**: what are they interacting with?
- **How**: moderated / unmoderated / analytics
- **Success criteria**: what does "this works" look like?
- **Timeline**: when will we have results?

**Prototype**: <!-- Figma mockup / code spike / paper prototype / wizard-of-oz / A-B test -->

---

## 8. Kill Criteria & Deadline

**When do we stop?**
<!-- Be specific. "If after 2 weeks of A/B testing, engagement doesn't increase by at least 5%, we abandon this approach." -->

> ...

**Hard deadline**: <!-- Date by which we must have a go/no-go decision -->

**Escalation**: <!-- Who decides if results are ambiguous? -->

---

## 9. Organizational Risk (Hogan)

**Potential derailers**:
<!-- Cultural or behavioral patterns that could derail this change. -->
- ...

**Mitigation**:
- ...

---

## 10. Domain Boundaries

**Bounded contexts touched**: <!-- If this touches core, a domain-contract.md is required. -->
- ...

**Entities affected**: <!-- Even for edge work, know what you're near. -->
- ...

**Dependencies on other teams**: <!-- Team Topologies interaction mode. -->
- ...

---

## 11. Learning Log (Living Section)

> **This is the most important section.** Update it after every experiment or checkpoint.
> Each entry should answer: What did we learn? What changed? What's next?

### Iteration {{ iteration | default(1) }}

| Date | Experiment | What we learned | Impact on spec | What's next |
|------|-----------|----------------|----------------|------------|
| | | | | |

### Pivots

<!-- Record major direction changes. Each pivot increments the iteration counter in spec.yaml. -->

| Iteration | Date | From | To | Reason |
|-----------|------|------|----|--------|
| | | | | |

### Promotion Candidates

<!-- Assumptions that have been validated and are ready to become invariants in the core. -->
<!-- When an assumption here reaches "algorithm" status, create a domain-contract.md and run /evospec.contract -->

| Assumption | Evidence | Proposed Invariant | Ready? |
|-----------|----------|--------------------|--------|
| | | | |
