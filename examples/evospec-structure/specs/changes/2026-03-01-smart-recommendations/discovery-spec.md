# Discovery Spec: Smart Product Recommendations

> Zone: **edge** | Type: **experiment** | Knowledge Stage: **mystery → heuristic**

---

## 1. Strategic Fit (Roger Martin — Playing to Win)

**Winning Aspiration**: Be the most relevant product discovery experience for SMBs.

**Where to Play**: Returning customers who browse the catalog but struggle to find what they want.

**How to Win**: Personalized recommendations based on browsing and purchase history, reducing time-to-purchase and increasing conversion.

**What would have to be true** (Roger Martin):
- We have enough purchase history data to generate meaningful recommendations
- Users actually want personalized suggestions (not just better search)
- Our catalog is large enough that recommendations add value over manual browsing
- We can serve recommendations fast enough for a seamless UX (< 200ms)

---

## 2. Outcome & Opportunity (Teresa Torres — Continuous Discovery)

**Product Outcome**: Increase product page conversion rate by 10% within 3 months.

**Customer Opportunity**: Returning customers find relevant products faster.
<!-- HMW help returning customers find products they'll love without endless browsing? -->

**Opportunity Tree**:
```
Outcome: +10% product page conversion
├── Opportunity 1: Customers can't find relevant products quickly
│   ├── Solution A: Personalized recommendations based on purchase history
│   ├── Solution B: Improved search with faceted filters
│   └── Solution C: Curated collections by product category
└── Opportunity 2: Customers don't return frequently enough
    └── (out of scope for this spec)
```

**Selected Approach**: Solution A — Personalized recommendations. Riskiest but highest potential impact.

---

## 3. Empathy & Research (Design Thinking — Empathize)

**Research conducted**:
- [x] User interviews (N=12): Returning customers describe "browsing fatigue"
- [x] Heatmap analysis: 60% of users scroll past the fold but don't click product cards
- [x] Competitor analysis (Amazon, Shopify apps, Algolia Recommend)
- [ ] Survey on recommendation preferences (planned for week 2)

**Key insights**:
- Users with 3+ past purchases are most likely to benefit from recommendations
- "I know what I like, I just can't find it fast enough" — recurring theme in interviews
- Competitors show 15-25% conversion lift from recommendations

---

## 4. Problem Definition (Design Thinking — Define)

**Problem Statement**: Returning customers spend an average of 8 minutes browsing before finding a product they want, leading to 40% abandonment before purchase.

**Reframes**:
1. "How might we surface the right product in the first 30 seconds?"
2. "How might we learn from what customers bought before to predict what they'll buy next?"

---

## 5. Ideation (Design Thinking — Ideate)

| # | Idea | Feasibility | Impact | Notes |
|---|------|------------|--------|-------|
| 1 | Collaborative filtering ("customers who bought X also bought Y") | High | High | Simple to implement, proven pattern |
| 2 | Content-based filtering (similar product attributes) | High | Medium | Good for cold start, less serendipity |
| 3 | Hybrid approach (collaborative + content-based) | Medium | High | Best quality but more complex |
| 4 | LLM-powered natural language recommendations | Low | Unknown | Novel but slow and expensive |

**Selected**: Start with #1 (collaborative filtering). If results are promising, add #2 for hybrid approach.

---

## 6. Assumptions & Experiments (Teresa Torres)

| # | Assumption | Risk | Category | Test Method | Status |
|---|-----------|------|----------|-------------|--------|
| 1 | Users prefer personalized recs over generic bestsellers | High | Desirability | A/B test (N=2000) | Testing |
| 2 | Collaborative filtering outperforms content-based for our catalog | Medium | Feasibility | Offline evaluation on historical data | Untested |
| 3 | Recommendations can be generated in < 200ms | Low | Feasibility | Load test with pre-computed embeddings | Validated |

**What would have to be true** for this to work:
- Assumption 1 must hold: personalized > generic (desirability)
- Latency must stay under 200ms at scale (feasibility) ✓ Validated
- Recommendation quality must be "good enough" with simple collaborative filtering

---

## 7. Prototype & Test Plan (Design Thinking — Prototype + Test)

**Prototype type**: Code spike (working service behind feature flag)

**Test plan**:
1. Week 1: Build recommendation service with pre-computed embeddings → validate latency ✓
2. Week 2-3: A/B test personalized vs. generic with 2000 users → validate desirability
3. Week 4: If positive, offline evaluation of collaborative vs. content-based → validate approach

**Success criteria**: ≥ 15% click-through improvement AND ≥ 5% conversion improvement.

---

## 8. Kill Criteria

> If after 4 weeks of A/B testing, conversion rate doesn't improve by at least 5%, abandon personalized recommendations and focus on improved search (Solution B) instead.

**Hard deadline**: 2026-04-01

**Metrics to watch**:
- Click-through rate on recommendations widget
- Product page conversion rate (primary)
- Time-to-first-click after page load

---

## 9. Organizational Risk (Hogan)

**Derailer risks**:
- **Scope creep**: Temptation to build a full ML pipeline before validating the value proposition
- **Perfectionism**: Data team may want "perfect" recommendations before testing with users

**Mitigation**: Start with simple collaborative filtering. Ship a "good enough" version in 2 weeks. Validate value before investing in sophistication.

---

## 10. Domain Boundaries

**Bounded contexts touched**: None directly. This is a stateless service that reads from the existing `catalog` and `orders` contexts but doesn't write to them.

**Entities affected**: None (read-only access to Product, Order, LineItem)

**Core invariants at risk**: None — this is a pure edge experiment with no schema changes.

---

## Learning Log

| Date | Iteration | Experiment | Learning | Decision |
|------|-----------|-----------|---------|----------|
| 2026-03-05 | 1 | EXP-001 (latency spike) | Pre-computed embeddings keep p99 < 200ms | Continue |
| 2026-03-13 | 1 | EXP-002 (A/B test round 1) | 12% CTR improvement but not significant (p=0.08) | Continue with larger sample |
