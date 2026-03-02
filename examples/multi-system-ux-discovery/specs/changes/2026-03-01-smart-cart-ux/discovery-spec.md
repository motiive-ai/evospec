# Discovery Spec: Smart Cart — Real-time Availability + One-Click Checkout

## Opportunity

### Problem Statement
Users abandon carts at a high rate (68% abandonment). Exit surveys and session recordings reveal two primary friction points:
1. **Out-of-stock surprise at checkout** — users add items, fill in shipping details, then discover an item is unavailable. This causes rage-quits.
2. **Too many steps** — current checkout is 5 pages (cart review → shipping → billing → confirmation → receipt). Each page transition loses ~15% of users.

### How Might We...
- ...show product availability in real-time so users never get surprised at checkout?
- ...reduce checkout from 5 steps to 1 click for returning users with saved payment methods?
- ...build and validate this UX without changing the backend services?

### Persona
**Sarah, the Busy Parent** — shops on mobile during lunch breaks. Has 10 minutes. Knows what she wants. Gets frustrated by long checkout flows. Has a saved credit card.

## Hypothesis

> **If** we show real-time product availability in the cart and offer one-click checkout for users with saved payment methods,
> **then** cart-to-checkout conversion will increase by ≥25%,
> **because** the two biggest abandonment causes (stock surprises and multi-step checkout) are eliminated.

## Assumptions (Riskiest First)

| ID | Assumption | Risk | Test Method | Status |
|----|-----------|------|-------------|--------|
| A001 | Users abandon carts primarily due to out-of-stock surprises at checkout | High | User interviews (n=10) + funnel analytics | 🧪 Testing |
| A002 | One-click checkout reduces friction enough to improve conversion | Medium | A/B test with prototype | ⏳ Untested |
| A003 | Real-time availability checking does not degrade UX performance (<200ms) | Low | Performance testing | ⏳ Untested |

## Kill Criteria

**Stop this experiment if:**
- Cart-to-checkout conversion does not improve by ≥10% after 2 weeks of A/B testing
- Real-time availability API adds >500ms latency to the cart experience
- User interviews reveal the primary abandonment cause is unrelated to stock/checkout friction

## Design Thinking Phase

**Current phase: Prototype → Test**

### Empathize
- 10 user interviews completed — 7/10 mentioned stock surprises as #1 frustration
- Session recordings show 42% of cart abandoners leave on the checkout confirmation page
- NPS for checkout flow: 23 (below company average of 45)

### Define
- Primary job-to-be-done: "Help me buy what I want without wasting my time"
- Key metric: Cart-to-checkout conversion rate (currently 32%)

### Ideate
Options considered:
1. ✅ **Smart Cart with real-time availability + one-click checkout** (selected)
2. Pre-checkout stock validation modal (too interruptive)
3. Stock notifications ("back in stock" alerts) (doesn't solve checkout friction)
4. Progressive checkout (save state between steps) (incremental, not transformative)

### Prototype
- React/TypeScript prototype built via vibe-coding with AI agent
- Talks to existing backend APIs (no backend changes needed for prototype)
- Deployed behind feature flag for A/B testing

### Test
- A/B test: 50/50 split, 2-week duration, targeting 1000 checkout sessions per variant
- Primary metric: Cart-to-checkout conversion rate
- Secondary metrics: Average order value, time-to-checkout, cart abandonment rate

## ⚠️ Backend Invariant Conflicts

The following core invariants are potentially affected by this UX experiment.
These were detected by `evospec check_invariant_impact`.

### Conflict 1: Empty Cart Checkout (ORD-INV-001)
- **Invariant**: "Every Order MUST have at least one LineItem before status can change from draft"
- **How the UX might violate it**: The one-click checkout button is visible even when the cart is empty
- **Resolution**: Shadow — add client-side validation to disable checkout when cart is empty. Backend will also reject it, but the UX should prevent the call entirely.

### Conflict 2: Payment Timing (ORD-INV-003)
- **Invariant**: "Payment MUST be authorized before Order status changes to confirmed"
- **How the UX might violate it**: The prototype creates the order first, then authorizes payment. If the flow is: createOrder → reserveStock → authorizePayment, then the order exists in draft state with reserved stock but no payment. If the user closes the browser, stock is locked until reservation expires.
- **Resolution**: Redesign — change the checkout flow to: authorizePayment → createOrder (with payment_id) → reserveStock → confirmOrder. This matches the backend's expected state machine.

### Conflict 3: Reservation Expiry UX (INV-INV-003)
- **Invariant**: "StockReservation MUST be released or confirmed within 30 minutes of creation"
- **How the UX might violate it**: The UX reserves stock when the user clicks "checkout" but doesn't show that the reservation has a 30-minute TTL. If the user walks away, the reservation expires silently.
- **Resolution**: Shadow — add a countdown timer in the checkout UI: "Complete your purchase within 28:32 or items will be released back to stock."

### Conflict 4: Reservation Rollback (INV-INV-002)
- **Invariant**: "Product reserved_quantity MUST NOT exceed stock_quantity"
- **How the UX might violate it**: If payment authorization fails after stock is reserved, the UX doesn't explicitly release the reservation. The backend's scheduled job will handle it in ≤30 minutes, but during that time the available quantity is incorrectly reduced.
- **Resolution**: Exempt — the backend handles this automatically. But the UX should show the user: "Payment failed. Your items have been returned to your cart. Stock is held for 30 minutes."

## What the Backends Need (Post-Experiment)

If the experiment succeeds (conversion ≥ +10%), the following backend capabilities are needed:

### Order Service
1. **New endpoint**: `POST /api/orders/one-click` — atomic operation that creates order + authorizes payment in one call
2. **Payment-first flow**: Accept payment_id in the create order request to enforce ORD-INV-003
3. **Idempotency key**: Prevent duplicate one-click orders from double-taps

### Inventory Service
1. **Reservation TTL in response**: Return `expires_at` timestamp in reservation response so the UI can show a countdown
2. **Batch availability check**: `POST /api/products/availability` — check multiple products in one call instead of N individual requests
3. **WebSocket availability**: Real-time stock updates pushed to the UI (future, if latency is a problem)

> **These backend changes would be specified as a Hybrid zone spec** — they add new capabilities to support a validated UX pattern, crossing the discovery-core boundary with explicit contracts.

## Experiment Timeline

| Week | Activity | Gate |
|------|---------|------|
| 1 | Build prototype, deploy behind feature flag | Prototype reviews with 3 users |
| 2-3 | A/B test (1000 sessions per variant) | Conversion ≥ +10%? |
| 4 | Analyze results, conduct 5 exit interviews | Kill or continue? |
| 5 | If continue: create Hybrid spec for backend changes | Backend team review |
| 6-8 | Implement backend support, integration testing | Fitness functions pass |
| 9 | Full rollout | Monitor conversion for 2 more weeks |
