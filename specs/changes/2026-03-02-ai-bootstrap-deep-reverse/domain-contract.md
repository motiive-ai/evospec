# Domain Contract: AI Bootstrap Prompt + Deep Reverse Engineering

> Zone: **hybrid** | Bounded Context: **reverse-engineering** | Status: **draft**
>
> *Light contract (hybrid zone) — Sections 1, 3, 4, 7 only.*

---

## 1. Context & Purpose

**Bounded Context**: reverse-engineering (supporting)

**Context Map Position**: open-host — emits detection results consumed by agent-integration (bootstrap prompt) and spec-engine (init pre-fill)

**Ubiquitous Language** (terms specific to this change):

| Term | Definition | Not to be confused with |
|------|-----------|------------------------|
| Bootstrap Prompt | A self-contained markdown document (~2-3KB) that gives any AI agent full EvoSpec context without reading source code | "CLAUDE.md" — the bootstrap prompt exists *before* init, CLAUDE.md exists *after* |
| Project Detection | Auto-detection of language, framework, ORM, and source dirs from build files and dependencies | "Reverse engineering" — detection identifies the stack, reverse engineering extracts domain |
| Deep Reverse | Enhanced reverse engineering that also analyzes git history, hot files, and project structure | "Shallow reverse" — existing commands that only scan source code |

---

## 3. Aggregates & Entities

### Value Object: ProjectDetection

Not an aggregate — this is a transient value object produced by `detect_project_stack()` and consumed by the prompt generator and init command.

| Field | Type | Description |
|-------|------|-------------|
| language | String | python, java, go, typescript, javascript |
| framework | String? | spring, fastapi, express, nextjs, etc. |
| source_dirs | String[] | Detected source code directories |
| orm | String? | jpa, sqlalchemy, prisma, typeorm, gorm, etc. |
| project_name | String? | Extracted from build file metadata |
| build_file | String | Primary build file found (pom.xml, package.json, etc.) |
| git_info | GitInfo? | Git history analysis (if available) |

### Value Object: GitInfo

| Field | Type | Description |
|-------|------|-------------|
| recent_commits | int | Number of commits in last 30 days |
| contributors | String[] | Unique contributor names |
| hot_files | String[] | Most changed files recently |
| primary_language_pct | float | % of code in primary language |

---

## 4. Invariants

> Hybrid zone — light invariants. No fitness functions required.

| ID | Invariant Statement | Enforcement |
|----|-------------------|-------------|
| BOOT-INV-001 | `evospec prompt` MUST work without `evospec.yaml` existing (pre-init) | ci-check |
| BOOT-INV-002 | `evospec prompt --detect` MUST gracefully degrade when git is not available | ci-check |
| BOOT-INV-003 | Detection MUST NOT modify any files (read-only operation) | ci-check |
| BOOT-INV-004 | `evospec prompt --format json` MUST output valid JSON | ci-check |

---

## 7. Authorization & Policies

**Access Rules**: N/A — CLI command, no auth.

**Data Sensitivity**: None — reads only build files, git log, and source structure. No PII, credentials, or secrets.

---

## 12. Anti-Requirements (What This Is NOT)

1. This does NOT automatically execute reverse engineering commands — it instructs the agent to do so
2. This does NOT replace CLAUDE.md or .windsurf/workflows — those are post-init artifacts
3. This does NOT handle monorepo multi-language detection (future improvement)
4. This does NOT parse lock files (yarn.lock, poetry.lock, go.sum)
