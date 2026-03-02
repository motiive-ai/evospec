# Improvement Scope: Auto-Spec Sync & Verification (evospec sync, verify, capture --from-history)

> Zone: **hybrid** | Type: **improvement** | Status: **draft**

---

## What Needs to Change

Three interconnected problems prevent specs from staying trustworthy: (1) **Drift** — teams commit code without updating specs, so entities.yaml and invariants silently become outdated. (2) **No baseline** — teams adopting EvoSpec on existing codebases have no way to generate specs from years of code history. (3) **No verification** — there's no way to check if a spec accurately describes what's actually implemented. This change adds three new CLI commands: `evospec sync` (drift detection), `evospec verify` (spec-vs-code accuracy), and `evospec capture --from-history` (retroactive spec generation from git history).

## Why Now

These are the **biggest adoption blockers** for EvoSpec. Teams with existing codebases won't adopt if they have to manually spec years of work. Teams that do adopt will see specs drift within weeks. And AI agents trusting stale MCP context will generate wrong code. Together, these three commands make specs self-maintaining.

## Scope

### In Scope

**Feature 1: `evospec sync`** — Git diff analysis to detect spec drift
- Detect new/modified/removed entity fields from git diff
- Detect new/modified/removed API endpoints from git diff
- Calculate drift score (0-100%)
- `--generate` flag to create draft change specs from detected changes
- `--ci` flag for machine-readable output in CI pipelines
- `--since <commit|tag|date>` to control analysis window

**Feature 2: `evospec verify`** — Spec-vs-implementation accuracy
- Level 1: Entity verification (spec fields vs code fields — name, type, presence)
- Level 2: API contract verification (documented endpoints vs actual controllers)
- Level 3: Invariant verification (declared invariants have enforcement in code + test files)
- Level 4: Bounded context verification (spec contexts match code package structure)
- Level 5: Cross-spec consistency (same entity in multiple specs has consistent fields)
- Verification score (0-100%) across all levels
- `--strict` mode exits non-zero for CI gates
- `--format json|markdown` for CI integration and PR comments
- Configurable minimum scores in evospec.yaml

**Feature 3: `evospec capture --from-history`** — Retroactive spec generation
- Git history mining with feature cluster detection (co-changed files + commit messages)
- Retroactive spec generation with `retroactive: true` flag
- Domain model bootstrap (entities.yaml, contexts.yaml, glossary.md from history)
- Glossary mining from code identifiers, enum values, commit messages
- `--interactive` mode walks user through each cluster
- `--since` flag limits analysis window
- `--dry-run` shows what would be generated

### Out of Scope

- Real-time file watching (sync is on-demand or CI-triggered)
- Auto-fixing drifted specs (sync reports, human reviews)
- Deep code analysis for verification (uses structural matching; deep analysis is the deep-reverse-engineering change)

## Affected Areas

**Endpoints**: None

**Tables**: None

**Modules**:
- `evospec.cli.main` — new `sync`, `verify` commands; enhanced `capture`
- `evospec.core.sync` — GitDiffAnalyzer, DriftScorer, DraftSpecGenerator
- `evospec.core.verify` — EntityVerifier, APIVerifier, InvariantVerifier, ContextVerifier
- `evospec.core.capture` — FeatureClusterDetector, GlossaryMiner (enhanced)
- `evospec.core.config` — verification thresholds
- `evospec.mcp.server` — `evospec://drift-report`, `evospec://verification` resources; `check_drift()`, `verify_spec()` tools

**Bounded Contexts**:
- `spec-engine` — drift scoring, verification pipeline
- `reverse-engineering` — code analysis for verification
- `domain-management` — retroactive domain model generation

## Invariant Impact

No conflicts. Fully additive — new commands alongside existing ones.

## Acceptance Criteria

### evospec sync
- [ ] Detects new/modified/removed entity fields from git diff
- [ ] Detects new/modified/removed API endpoints from git diff
- [ ] Calculates drift score (0-100%) comparing specs vs code
- [ ] `--generate` creates draft change specs grouped by logical change
- [ ] `--ci` produces machine-readable output
- [ ] Works without existing change specs (compares entities.yaml vs code)

### evospec verify
- [ ] Checks entity fields in specs match actual code (name, type, presence)
- [ ] Checks API endpoints in specs exist in actual controllers
- [ ] Checks declared invariants have enforcement in code
- [ ] Checks declared invariants have fitness functions (test files exist)
- [ ] Checks bounded context assignments match code package structure
- [ ] Cross-spec consistency: same entity in multiple specs has consistent fields
- [ ] Verification score (0-100%) calculated across all levels
- [ ] `--strict` exits non-zero on any failure
- [ ] `--format json|markdown` for CI integration
- [ ] Configurable minimum scores in evospec.yaml

### evospec capture --from-history
- [ ] Analyzes full git history and detects feature clusters
- [ ] Feature clusters grouped by co-changed files + commit message patterns
- [ ] Each cluster generates a retroactive spec (`retroactive: true`)
- [ ] Domain model bootstrapped from history + reverse engineering
- [ ] Glossary mined from code identifiers, enum values, commit messages
- [ ] `--interactive` mode walks user through each cluster
- [ ] `--since` limits history analysis
- [ ] Works on projects with 0 existing specs

### MCP Integration
- [ ] `evospec://drift-report` resource returns current drift score
- [ ] `evospec://verification` resource returns verification report
- [ ] `check_drift()` MCP tool runs drift analysis on demand
- [ ] `verify_spec()` MCP tool runs verification on demand

### Example: Sync Output

```
$ evospec sync --since v1.2.0

Analyzing 23 commits since v1.2.0...

Entity changes detected:
  + NEW FIELD: Order.trackingNumber (String, nullable)
  + NEW FIELD: Product.isActive (Boolean)
  ~ MODIFIED: OrderStatus enum — added PROCESSING state

API changes detected:
  + NEW ENDPOINT: POST /api/orders/bulk-create
  ~ MODIFIED: POST /api/orders — added priority parameter

Invariant impact:
  ⚠ INV-003 may need update: OrderStatus now includes PROCESSING

Drift score: 18% (entities.yaml is 18% outdated)
```

### Example: Verify Output

```
$ evospec verify

Entity verification: 85% (7/9 match)
  ✅ Order — all fields match
  ❌ Product — missing isActive field in spec
  ⚠ Customer — deprecated email field still in spec

API coverage: 76% (13/17 documented)
  ❌ 4 undocumented endpoints

Invariant enforcement: 80% (4/5)
  ❌ INV-004 — no guard clause found in code

Overall score: 80%
```

### Example: Capture from History

```
$ evospec capture --from-history --since 2025-01-01

Analyzing 347 commits (8 contributors, 14 months)...

Detected feature clusters:
  📦 "Order Processing" (78 commits, 2025-01 → 2025-06)
     Entities: Order, LineItem, Payment
     Suggested zone: core

  📦 "Product Catalog" (45 commits, 2025-03 → 2025-09)
     Entities: Product, Category
     Suggested zone: core

  📦 "Search & Filtering" (22 commits, 2025-07 → 2025-10)
     Entities: SearchIndex
     Suggested zone: edge

Generated: 3 retroactive specs + domain model baseline
```

## Risks & Rollback

**Risk level**: medium — git analysis and code parsing can produce false positives

**Rollback plan**: Remove new commands; no changes to existing commands or spec format

**Reversibility**: trivial — fully additive

## ADRs

- ADR: Drift scoring uses structural comparison (field names, types) not semantic — keeps it deterministic and fast
- ADR: Verification reports are informational, not auto-fixing — human reviews before accepting suggestions
- ADR: Feature cluster detection uses file co-change graph with community detection — no ML dependency, deterministic results
