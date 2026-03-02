# Implementation Spec: {{ title }}

> Zone: **{{ zone }}** | Status: **{{ status }}** | Last updated: {{ updated_at }}
>
> This document is the **as-built blueprint** — it describes what was actually implemented,
> how the pieces connect, and everything needed to reproduce or maintain this component.
> Created as a skeleton by `/evospec.tasks`, filled in during `/evospec.implement`.

---

## 1. Overview

**What was built**: <!-- One paragraph: what this component does, in plain language -->

**Architecture style**: <!-- SPA / SSR / API / CLI / library / microservice / worker / ... -->

**Tech stack**:

| Layer | Technology | Version | Why |
|-------|-----------|---------|-----|
| | | | |

**Key decisions**: <!-- Link to ADRs if they exist, otherwise list the 2-3 most important choices -->

---

## 2. Component Architecture

<!-- Describe how the system is structured. For a UI: components, hooks, pages.
     For an API: routes, controllers, services. For a CLI: commands, handlers. -->

```
<!-- ASCII or mermaid diagram of the component tree / module graph -->
```

### Components / Modules

| Component | Responsibility | File Path | Dependencies |
|-----------|---------------|-----------|-------------|
| | | | |

### Data Flow

<!-- How data moves through the system. Request → response for APIs.
     User action → state change → render for UIs. -->

```
<!-- Sequence diagram or data flow description -->
```

---

## 3. API Integration

<!-- How this component talks to other systems. For each external API: -->

### Upstream APIs Consumed

| API | Base URL | Auth | Timeout | Retry | Circuit Breaker |
|-----|---------|------|---------|-------|----------------|
| | | | | | |

### Endpoints Used

| Method | Path | Request | Response | Error Handling |
|--------|------|---------|----------|---------------|
| | | | | |

### API Client Configuration

<!-- How the API client is set up: base URL, auth headers, interceptors, error mapping -->

---

## 4. State Management

<!-- How state is managed. For UIs: React state, context, stores, URL params.
     For APIs: session, cache, database. For workers: queue state. -->

**State architecture**: <!-- local state / context / Redux / Zustand / URL params / ... -->

### State Shape

```
<!-- TypeScript interface, Python dataclass, or pseudocode showing the state structure -->
```

### State Transitions

| Trigger | From State | To State | Side Effects |
|---------|-----------|----------|-------------|
| | | | |

---

## 5. Configuration & Environment

| Variable | Purpose | Default | Required |
|----------|---------|---------|----------|
| | | | |

### Feature Flags

| Flag | Purpose | Default | Rollout |
|------|---------|---------|---------|
| | | | |

---

## 6. Error Handling & Resilience

### Error Scenarios

| Scenario | Detection | User Experience | Recovery |
|----------|----------|----------------|----------|
| | | | |

### Fallback Behavior

<!-- What happens when dependencies are unavailable? Graceful degradation strategy. -->

---

## 7. Testing Strategy

| Type | Tool | Coverage Target | Key Files |
|------|------|----------------|-----------|
| Unit | | | |
| Integration | | | |
| E2E | | | |

### Key Test Scenarios

<!-- The 5-10 most important test cases that verify this implementation works -->

1. ...

---

## 8. Deployment & Operations

**Build command**: <!-- npm run build / mvn package / docker build / ... -->

**Deploy target**: <!-- Vercel / K8s / Lambda / static CDN / ... -->

**Health check**: <!-- How to verify the deployment is healthy -->

**Monitoring**:

| Metric | Tool | Alert Threshold |
|--------|------|----------------|
| | | |

---

## 9. Invariant Compliance

<!-- How does this implementation comply with the invariants from the spec?
     Map each invariant to the specific code that enforces it. -->

| Invariant | How Enforced | File:Line | Test |
|-----------|-------------|-----------|------|
| | | | |

---

## 10. Reproduction Instructions

<!-- Step-by-step instructions to rebuild this from scratch.
     Someone with this document and the spec should be able to reproduce the implementation. -->

### Prerequisites

- ...

### Setup

```bash
# Commands to set up the development environment
```

### Build & Run

```bash
# Commands to build and run locally
```

### Verify

```bash
# Commands to verify it works (run tests, hit health check, etc.)
```

---

## 11. Known Limitations & Tech Debt

| Item | Impact | Planned Fix | Priority |
|------|--------|------------|----------|
| | | | |

---

## 12. Changelog

<!-- Updated by /evospec.implement as tasks are completed -->

| Date | Phase | What Changed |
|------|-------|-------------|
| | | |
