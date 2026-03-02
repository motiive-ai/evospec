# Discovery Spec: Retroactive Spec Generation from Git History

> Zone: **edge** | Status: **draft** | Created: 2026-03-02

---

## 1. Strategic Fit (Roger Martin — Playing to Win)

**Winning Aspiration**: Be the standard spec-driven delivery toolkit for AI-assisted development

**Where to Play**: Teams adopting EvoSpec on existing codebases with years of unspecified code history — the "we have 500K lines and no specs" segment

**How to Win**: Automated feature cluster detection from git history + retroactive spec generation — teams get a spec baseline in minutes, not weeks. No other spec tool offers this.

---

## 2. Outcome & Opportunity (Teresa Torres — Continuous Discovery)

**Product Outcome**: Reduce time-to-first-spec for existing codebases from days to minutes. Increase EvoSpec adoption on brownfield projects.

**Customer Opportunity**: How might we help teams with existing codebases generate a spec baseline without manual effort?

**Opportunity Tree**:
```
Outcome: Reduce adoption friction for existing codebases
├── Opportunity 1: Teams can't justify weeks of manual spec-writing
│   ├── Solution A: evospec capture --from-history (git history → feature clusters → specs)
│   ├── Solution B: evospec reverse --deep + manual curation (code analysis only, no history)
│   └── Solution C: AI-assisted interview ("tell me about your features") → specs
└── Opportunity 2: Generated specs are too generic to be useful
    ├── Solution A: Interactive mode (--interactive) walks user through each cluster
    └── Solution B: Merge with deep reverse engineering for richer content
```

---

## 3. Empathy & Research (Design Thinking — Empathize)

**Research conducted**:
- [ ] User interviews (N = ?)
- [ ] Observation / shadowing
- [ ] Journey mapping
- [ ] Survey / quantitative data
- [x] Competitor analysis — no existing spec tool offers git-history-based spec generation
- [x] Domain expert consultation — git co-change analysis is established in mining software repositories (MSR) research

**Key insights**:
1. The biggest adoption barrier for spec tools on existing codebases is the "cold start problem" — no specs exist, and writing them manually for years of work is impractical
2. Git history contains implicit feature boundaries: files that change together tend to belong to the same feature (co-change coupling)
3. Conventional commit messages (feat:, fix:, refactor:) provide semantic labels, but many repos use free-form messages

**Empathy artifacts**:
- Mining Software Repositories literature on co-change coupling and community detection

---

## 4. Problem Definition (Design Thinking — Define)

**Problem Statement**:

> Developers adopting EvoSpec on existing projects face a "blank page" problem — they have thousands of lines of code with implicit domain knowledge but no specs. Writing specs manually requires understanding every feature's history, boundaries, and invariants — work that feels like documentation overhead rather than value-add.

**Reframes explored**:
1. "How might we make the first hour with EvoSpec productive for existing projects?" (time-focused)
2. "How might we extract the spec that already exists implicitly in git history?" (knowledge-extraction-focused)

---

## 5. Ideation (Design Thinking — Ideate)

**Ideas generated**:

| # | Idea | Feasibility | Impact | Notes |
|---|------|-------------|--------|-------|
| 1 | Git co-change graph → community detection → feature clusters → specs | Medium | High | Core approach. MSR-proven technique. Deterministic, no ML. |
| 2 | Commit message NLP → topic modeling → feature labels | Low | Medium | Requires good commit messages. Many repos have "fix stuff" messages. |
| 3 | AI-assisted interview ("describe your features, I'll find the code") | Medium | Medium | Requires human input. Doesn't scale to large codebases. |
| 4 | Reverse engineering only (deep reverse → entities.yaml + glossary) | High | Medium | No feature detection, just domain model baseline. Fallback option. |
| 5 | Combination: co-change clusters + reverse engineering + glossary mining | Medium | High | Best of both worlds. Cluster for features, reverse for entities. |

**Selected approach**: #5 (combination) — co-change clustering provides the feature structure, deep reverse engineering fills in domain content, glossary mining enriches the ubiquitous language. Falls back to #4 if clustering fails.

---

## 6. Assumptions & Experiments (Teresa Torres)

**Riskiest assumptions** (ordered by risk, highest first):

| ID | Assumption | Category | Risk | Status | Success Criteria |
|----|-----------|----------|------|--------|-----------------|
| A-001 | Git co-change graphs produce meaningful feature clusters (not random file groupings) | feasibility | high | untested | ≥ 60% of clusters map to recognizable features on 5 repos |
| A-002 | Commit messages contain enough semantic signal to label feature clusters | feasibility | high | untested | ≥ 50% of clusters get meaningful auto-generated labels on 5 repos |
| A-003 | Teams find retroactive specs valuable enough to curate them | desirability | medium | untested | ≥ 3/5 developers say they'd use or edit the generated specs |

**"What would have to be true"** for this to work? (Roger Martin)
1. Git history must contain signal about feature boundaries (co-change coupling is real)
2. The clustering algorithm must produce human-recognizable groups (not noise)
3. The generated specs must be useful enough to curate (not throwaway)

---

## 7. Experiments (Continuous Discovery — Biweekly Cycle)

| ID | Assumption | Type | Description | N | Started | Result | Confidence | Decision |
|----|-----------|------|-------------|---|---------|--------|------------|----------|
| EXP-001 | A-001 | spike | Run co-change analysis on 5 OSS repos with known feature boundaries | 5 | | | | |
| EXP-002 | A-002 | analytics | Analyze commit message patterns and label quality on same 5 repos | 5 | | | | |
| EXP-003 | A-003 | interview | Generate specs for 3 real projects, interview developers | 5 | | | | |

### Current experiment

**What are we testing?** A-001 — can co-change graphs produce recognizable feature clusters?

**Test plan**:
- **Who**: 5 open-source repositories with documented feature boundaries (e.g., repos with feature-based directory structure)
- **What**: Co-change graph construction → community detection algorithm → cluster output
- **How**: Automated analysis + manual comparison to known feature boundaries
- **Success criteria**: ≥ 60% of clusters map to features a developer would recognize
- **Timeline**: 1 spike (~2 days of implementation + analysis)

**Prototype**: Code spike implementing co-change graph + Louvain community detection

---

## 8. Kill Criteria & Deadline

**When do we stop?**

> If co-change clustering fails to produce recognizable features on 3+ of 5 test repos, kill the clustering approach. Fall back to reverse-engineering-only baseline generation (Solution #4 — entities.yaml + glossary from code, no feature detection).

**Hard deadline**: TBD (set after first experiment)

**Escalation**: Project maintainer decides if borderline results warrant another iteration

---

## 9. Organizational Risk (Hogan)

**Potential derailers**:
- Over-engineering risk: building a sophisticated MSR pipeline when a simpler approach (just deep reverse) would be "good enough"
- Perfectionism: wanting 90%+ cluster accuracy when 60% + human curation is sufficient

**Mitigation**:
- Kill criteria are explicit and measurable
- Fallback approach (Solution #4) is simple and high-feasibility
- Time-box the spike to 2 days

---

## 10. Domain Boundaries

**Bounded contexts touched**:
- `reverse-engineering` — primary home for git history analysis
- `spec-engine` — generates retroactive ChangeSpec artifacts
- `domain-management` — bootstraps entities.yaml, contexts.yaml, glossary.md

**Entities affected**:
- `ChangeSpec` — generates retroactive specs with `retroactive: true` flag
- `DomainEntity` — bootstraps entity registry from history + code
- `Feature` — auto-generates feature entries from clusters
- `BoundedContext` — infers contexts from code package structure

**Dependencies on other teams**: None (EvoSpec is the platform team)

---

## 11. Learning Log (Living Section)

> **This is the most important section.** Update it after every experiment or checkpoint.

### Iteration 1

| Date | Experiment | What we learned | Impact on spec | What's next |
|------|-----------|----------------|----------------|------------|
| | | | | |

### Pivots

| Iteration | Date | From | To | Reason |
|-----------|------|------|----|--------|
| | | | | |

### Promotion Candidates

| Assumption | Evidence | Proposed Invariant | Ready? |
|-----------|----------|--------------------|--------|
| | | | |
