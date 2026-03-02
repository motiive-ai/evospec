---
spec_id: "smart-recommendations"
title: "Smart Product Recommendations"
zone: "edge"
status: "in-progress"
created_at: "2026-03-01"
total_tasks: 12
completed_tasks: 4
phases:
  - name: Setup
    tasks: ["T001", "T002"]
  - name: Foundation
    tasks: ["T003", "T004"]
  - name: Core Implementation
    tasks: ["T005", "T006", "T007"]
  - name: Integration
    tasks: ["T008", "T009"]
  - name: Guardrails
    tasks: ["T010", "T011"]
  - name: Polish
    tasks: ["T012"]
invariant_coverage: {}
---

# Implementation Tasks: Smart Product Recommendations

> Zone: **edge** | Status: **in-progress** | Generated: 2026-03-01

---

## Context

- **Spec**: specs/changes/2026-03-01-smart-recommendations/spec.yaml
- **Discovery Spec**: specs/changes/2026-03-01-smart-recommendations/discovery-spec.md

## Implementation Strategy

- **MVP first**: Ship simplest collaborative filtering behind a feature flag to validate the hypothesis
- **Incremental delivery**: Each phase should be independently testable
- **Kill-aware**: If kill criteria are met at any checkpoint, stop and archive

---

## Phase 1: Setup

- [X] T001 [Setup] Add `scikit-learn` and `numpy` to project dependencies
- [X] T002 [Setup] Create feature flag `RECOMMENDATIONS_ENABLED` in environment config

## Phase 2: Foundation

- [X] T003 [Foundation] Create recommendation service stub `app/services/recommendations.py`
- [X] T004 [Foundation] Build nightly embedding pre-computation job `scripts/compute_embeddings.py` — reads purchase history, outputs user-product similarity matrix

## Phase 3: Core Implementation

- [ ] T005 [Core] Implement collaborative filtering algorithm in `app/services/recommendations.py` — user-user similarity based on purchase history
- [ ] T006 [Core] Implement `GET /v1/recommendations/` endpoint — returns top-10 products for authenticated user, gated by feature flag
- [ ] T007 [P] [Core] Build fallback to bestsellers when user has < 3 purchases (cold start)

## Phase 4: Integration & Wiring

- [ ] T008 [Integration] Wire recommendation endpoint to FastAPI router with JWT auth
- [ ] T009 [Integration] Add A/B test variant assignment middleware — 50% personalized, 50% generic bestsellers

## Phase 5: Guardrails

- [ ] T010 [Guardrails] Instrument click-through rate tracking on recommendation widget
- [ ] T011 [Guardrails] Add latency monitoring — alert if p99 > 200ms (assumption A-003 threshold)

## Phase 6: Polish

- [ ] T012 [Polish] Update discovery-spec.md with experiment results after A/B test completes

---

## Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundation) → Phase 3 (Core) → Phase 4 (Integration) → Phase 5 (Guardrails) → Phase 6 (Polish)
```

## Parallel Opportunities

- T005 and T007 can run in parallel (main algorithm vs. cold start fallback)

## Kill Criteria Check

> At each weekly checkpoint, evaluate:
> - Is conversion improvement ≥ 5%? If not after 4 weeks → **kill**
> - Is p99 latency < 200ms? If not → **pause and investigate**
> - Hard deadline: 2026-04-01

## Completion Criteria

- [ ] All tasks marked [X]
- [ ] A/B test results recorded in discovery-spec.md
- [ ] Kill criteria evaluated at each checkpoint
- [ ] Spec.yaml traceability updated with actual file paths
- [ ] Decision: promote to hybrid zone OR kill
