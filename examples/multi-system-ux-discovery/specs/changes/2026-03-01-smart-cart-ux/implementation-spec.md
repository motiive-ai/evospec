# Implementation Spec: Smart Cart — Real-time Availability + One-Click Checkout

> Zone: **edge** | Status: **prototype** | Last updated: 2026-03-01
>
> This document is the **as-built blueprint** — it describes what was actually implemented,
> how the pieces connect, and everything needed to reproduce or maintain this component.

---

## 1. Overview

**What was built**: A React single-page component that replaces the existing 5-step checkout flow with a smart cart showing real-time product availability and a one-click checkout button. The prototype talks directly to the existing Order Service (Spring Boot / Java) and Inventory Service (FastAPI / Python) APIs — no backend changes were needed.

**Architecture style**: SPA component (embedded in existing React app)

**Tech stack**:

| Layer | Technology | Version | Why |
|-------|-----------|---------|-----|
| UI Framework | React | 18.x | Existing app uses React |
| Language | TypeScript | 5.x | Type safety for API contracts |
| State Management | React hooks (useState, useCallback) | — | Lightweight, no global state needed for prototype |
| API Client | Native fetch | — | Zero dependencies, sufficient for prototype |
| Build | Vite / CRA | — | Existing app toolchain |

**Key decisions**:
- No state management library (Redux, Zustand) — local component state is sufficient for the prototype scope
- Native `fetch` instead of axios — fewer dependencies, simpler error model for initial validation
- No WebSocket for availability — polling on quantity change is good enough to test the hypothesis
- Feature flag controlled — deployed alongside existing checkout, activated per-user for A/B test

---

## 2. Component Architecture

```
SmartCart (main container)
├── ProductCard (per item — shows availability badge)
├── CartSummary (total, item count)
└── OneClickCheckout (checkout button + loading state)

Hooks:
└── useCart (state + API orchestration)

API Layer:
└── client.ts (typed fetch wrappers for both backends)
```

### Components / Modules

| Component | Responsibility | File Path | Dependencies |
|-----------|---------------|-----------|-------------|
| `SmartCart` | Main container. Renders cart items, summary, and checkout. Owns top-level checkout flow. | `src/components/SmartCart.tsx` | `useCart` hook |
| `ProductCard` | Renders a single cart item with quantity controls and real-time availability indicator (green/red badge). | `src/components/ProductCard.tsx` | — |
| `CartSummary` | Shows total price and item count. | `src/components/CartSummary.tsx` | — |
| `OneClickCheckout` | Checkout button with loading spinner. Disabled when cart is empty or checkout in progress. | `src/components/OneClickCheckout.tsx` | — |
| `useCart` | Custom hook: manages cart state, exposes `addItem`, `removeItem`, `updateQuantity`, `checkout`. Orchestrates all API calls. | `src/hooks/useCart.ts` | `client.ts` |
| `client.ts` | Typed fetch wrappers for Order Service and Inventory Service APIs. Handles base URLs from env vars. | `src/api/client.ts` | — |

### Data Flow

```
User adds item
  → useCart.addItem(productId, name, price)
    → client.checkAvailability(productId, qty=1)
      → GET {INVENTORY_SERVICE}/api/products/{id}/availability?quantity=1
    → setState: add item with available=true/false

User changes quantity
  → useCart.updateQuantity(productId, newQty)
    → client.checkAvailability(productId, newQty)
      → GET {INVENTORY_SERVICE}/api/products/{id}/availability?quantity={qty}
    → setState: update item quantity + available flag

User clicks "One-Click Checkout"
  → useCart.checkout()
    → client.createOrder(items)
      → POST {ORDER_SERVICE}/api/orders/
    → for each item: client.reserveStock(productId, orderId, qty)
      → POST {INVENTORY_SERVICE}/api/reservations
    → client.authorizePayment(orderId, total)
      → POST {ORDER_SERVICE}/api/payments/authorize
    → return { order, payment }
```

---

## 3. API Integration

### Upstream APIs Consumed

| API | Base URL | Auth | Timeout | Retry | Circuit Breaker |
|-----|---------|------|---------|-------|----------------|
| Order Service | `REACT_APP_ORDER_SERVICE_URL` (default: `http://localhost:8080`) | None (prototype) | Browser default | None | None |
| Inventory Service | `REACT_APP_INVENTORY_SERVICE_URL` (default: `http://localhost:8000`) | None (prototype) | Browser default | None | None |

### Endpoints Used

| Method | Path | Request Body | Response | Error Handling |
|--------|------|-------------|----------|---------------|
| GET | `/api/products/{id}/availability?quantity={n}` | — | `{ available: boolean }` | Returns `available: false` on error |
| POST | `/api/orders/` | `{ items: [{ productId, quantity, unitPrice }] }` | `{ id, status, total_amount }` | Unhandled (prototype) |
| POST | `/api/reservations` | `{ productId, orderId, quantity }` | `{ id, status, expires_at }` | Unhandled (prototype) |
| POST | `/api/reservations/{id}/confirm` | — | `{ id, status }` | Unhandled (prototype) |
| POST | `/api/payments/authorize` | `{ orderId, amount }` | `{ id, status }` | Unhandled (prototype) |

### API Client Configuration

```typescript
// src/api/client.ts
const ORDER_SERVICE_URL = process.env.REACT_APP_ORDER_SERVICE_URL || 'http://localhost:8080';
const INVENTORY_SERVICE_URL = process.env.REACT_APP_INVENTORY_SERVICE_URL || 'http://localhost:8000';
```

All calls use native `fetch` with JSON content type. No auth headers (prototype relies on same-origin or CORS). No retry logic. No timeout configuration.

---

## 4. State Management

**State architecture**: Local component state via `useState` in the `useCart` hook. No global store.

### State Shape

```typescript
interface CartItem {
  productId: string;
  productName: string;
  quantity: number;
  unitPrice: number;
  available: boolean;    // real-time availability from Inventory Service
}

// useCart hook state
items: CartItem[]        // managed via useState
isChecking: boolean      // checkout-in-progress flag (in SmartCart component)
total: number            // computed: items.reduce(sum + unitPrice * quantity)
```

### State Transitions

| Trigger | From State | To State | Side Effects |
|---------|-----------|----------|-------------|
| `addItem(id, name, price)` | items: [...] | items: [..., newItem] | API: checkAvailability |
| `removeItem(id)` | items: [..., item] | items: [...] (filtered) | None |
| `updateQuantity(id, qty)` | item.quantity: N | item.quantity: M, item.available: bool | API: checkAvailability |
| `checkout()` | isChecking: false | isChecking: true → false | API: createOrder → reserveStock × N → authorizePayment |

---

## 5. Configuration & Environment

| Variable | Purpose | Default | Required |
|----------|---------|---------|----------|
| `REACT_APP_ORDER_SERVICE_URL` | Order Service base URL | `http://localhost:8080` | No |
| `REACT_APP_INVENTORY_SERVICE_URL` | Inventory Service base URL | `http://localhost:8000` | No |
| `REACT_APP_FEATURE_SMART_CART` | Feature flag to enable smart cart | `false` | No |

### Feature Flags

| Flag | Purpose | Default | Rollout |
|------|---------|---------|---------|
| `smart_cart_enabled` | Enable smart cart for A/B test | `false` | 50/50 split via LaunchDarkly / env var |

---

## 6. Error Handling & Resilience

### Error Scenarios

| Scenario | Detection | User Experience | Recovery |
|----------|----------|----------------|----------|
| Inventory API down | fetch throws | Item shows as "availability unknown" | Retry on next quantity change |
| Order creation fails | fetch returns non-200 | Generic error message | User retries manually |
| Payment authorization fails | fetch returns non-200 | **BUG**: Stock remains reserved until backend TTL expires | ⚠ No rollback implemented |
| Stock reserved but user abandons | Timer expires (30 min) | **BUG**: No countdown shown to user | Backend auto-releases |

### Fallback Behavior

**Prototype has minimal error handling.** Known gaps:
1. No retry logic on any API call
2. No rollback if payment fails after stock reservation
3. No countdown timer for reservation expiry
4. Checkout button not disabled when cart is empty (violates ORD-INV-001)

These are documented in the discovery-spec.md as invariant conflicts with resolution plans.

---

## 7. Testing Strategy

| Type | Tool | Coverage Target | Key Files |
|------|------|----------------|-----------|
| Unit | Jest + React Testing Library | Components render correctly | `__tests__/SmartCart.test.tsx` |
| Integration | MSW (Mock Service Worker) | API integration flows | `__tests__/checkout.integration.test.tsx` |
| E2E | Playwright | Full checkout happy path | `e2e/smart-cart.spec.ts` |

### Key Test Scenarios

1. **Cart renders empty state** — no items, checkout button disabled
2. **Add item shows availability** — calls inventory API, renders green/red badge
3. **Quantity change re-checks availability** — API called on quantity update
4. **Checkout happy path** — createOrder → reserveStock → authorizePayment succeeds
5. **Checkout with unavailable item** — should warn user (currently doesn't)
6. **Empty cart checkout blocked** — checkout button disabled when items.length === 0

---

## 8. Deployment & Operations

**Build command**: `npm run build` (outputs to `dist/`)

**Deploy target**: Existing React app deployment (Vercel / Netlify / CDN), behind feature flag

**Health check**: Component renders without errors when feature flag is enabled

**Monitoring**:

| Metric | Tool | Alert Threshold |
|--------|------|----------------|
| Cart-to-checkout conversion | Amplitude / Mixpanel | Baseline: 32% → Target: ≥42% |
| Checkout error rate | Sentry | > 5% of checkout attempts |
| Availability API latency (P95) | Browser Performance API | > 500ms |
| Checkout flow completion time | Custom analytics event | > 10 seconds |

---

## 9. Invariant Compliance

| Invariant | How Enforced | File:Line | Test |
|-----------|-------------|-----------|------|
| ORD-INV-001 (order must have ≥1 item) | ⚠ **NOT enforced** — checkout button should be disabled when cart empty | `SmartCart.tsx:43` — `disabled={isChecking}` should also check `items.length === 0` | Missing |
| ORD-INV-003 (payment before confirmation) | ⚠ **VIOLATED** — current flow: createOrder → reserve → pay. Should be: pay → createOrder → reserve | `useCart.ts:41-49` — checkout function order is wrong | Missing |
| INV-INV-002 (reserved_qty ≤ stock_qty) | Delegated to backend — UI doesn't enforce | — | N/A |
| INV-INV-003 (reservation 30-min TTL) | ⚠ **NOT enforced** — no countdown timer shown | Missing component | Missing |

> **Action required**: Before promoting from prototype to production, fix ORD-INV-001 (disable button) and ORD-INV-003 (reorder checkout flow). See discovery-spec.md §Backend Invariant Conflicts for resolution plans.

---

## 10. Reproduction Instructions

### Prerequisites

- Node.js ≥ 18
- npm or yarn
- Order Service running on `localhost:8080` (Java/Spring Boot)
- Inventory Service running on `localhost:8000` (Python/FastAPI)

### Setup

```bash
cd smart-cart-ui
npm install
```

### Build & Run

```bash
# Development
npm run dev

# Production build
npm run build
npm run preview
```

### Environment

```bash
# .env.local
REACT_APP_ORDER_SERVICE_URL=http://localhost:8080
REACT_APP_INVENTORY_SERVICE_URL=http://localhost:8000
REACT_APP_FEATURE_SMART_CART=true
```

### Verify

```bash
# Unit tests
npm test

# E2E tests (requires both backends running)
npx playwright test
```

---

## 11. Known Limitations & Tech Debt

| Item | Impact | Planned Fix | Priority |
|------|--------|------------|----------|
| No error handling on API calls | Checkout silently fails | Add try/catch + error state in useCart | High (before A/B test) |
| Checkout flow order violates ORD-INV-003 | Payment after order creation | Reorder: pay → create → reserve | High (before production) |
| No empty-cart guard on checkout button | Violates ORD-INV-001 | Add `disabled={items.length === 0}` | High (before A/B test) |
| No reservation countdown timer | User unaware of 30-min TTL | Add countdown component from `expires_at` | Medium |
| No rollback on payment failure | Stock locked until backend TTL | Call release reservation on payment error | Medium |
| Sequential stock reservation (N calls) | Slow for large carts | Backend batch endpoint needed (post-experiment) | Low |
| No auth headers on API calls | Prototype only | Add JWT from session | Required for production |
| No optimistic UI updates | Cart feels slow on quantity change | Update UI immediately, reconcile after API response | Low |

---

## 12. Changelog

| Date | Phase | What Changed |
|------|-------|-------------|
| 2026-03-01 | Prototype | Initial implementation: SmartCart, useCart, client.ts |
| 2026-03-01 | Prototype | Discovery spec created with invariant conflict analysis |
| 2026-03-01 | Prototype | Implementation spec created (this document) |
