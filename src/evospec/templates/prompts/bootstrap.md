# EvoSpec Bootstrap — v{{ version }}

> **EvoSpec** is a spec-driven delivery toolkit. It classifies changes as **edge** (experiments), **hybrid** (crossing boundaries), or **core** (domain contracts) — and applies proportional governance.

---

## Quick Start

```bash
# 1. Initialize EvoSpec in this project
evospec init "{{ detection.project_name or 'my-project' if detection else 'my-project' }}"

# 2. Reverse-engineer existing domain (optional but recommended)
{% if detection and detection.framework -%}
evospec reverse api --framework {{ detection.framework }}
{% else -%}
evospec reverse api --framework <fastapi|spring|express|gin|...>
{% endif -%}
{% if detection and detection.source_dirs -%}
evospec reverse db --source {{ detection.source_dirs[0] }}
evospec reverse cli --source {{ detection.source_dirs[0] }}
{% else -%}
evospec reverse db --source <source-dir>
evospec reverse cli --source <source-dir>
{% endif %}
# 3. Curate the generated domain files
#    - specs/domain/entities.yaml — entity registry
#    - specs/domain/contexts.yaml — bounded contexts
#    - specs/domain/glossary.md — ubiquitous language

# 4. Regenerate AI agent files (CLAUDE.md, .windsurf/, .cursor/)
evospec generate agents
```

After `evospec init`, read the generated **CLAUDE.md** for full framework context.

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `evospec init "name"` | Initialize project (creates evospec.yaml + agent files) |
| `evospec new "title" --zone edge\|hybrid\|core` | Create a new change spec |
| `evospec classify` | Interactively classify a change by zone |
| `evospec check [--strict]` | Validate specs and run fitness checks |
| `evospec fitness` | Execute fitness function tests |
| `evospec sync [--since REF]` | Detect spec drift from git changes |
| `evospec verify [--strict]` | Verify spec accuracy against code (5 levels) |
| `evospec capture --from-history` | Generate retroactive specs from git history |
| `evospec reverse api` | Reverse-engineer API endpoints (auto-detects framework) |
| `evospec reverse db --source <dir>` | Reverse-engineer database schema |
| `evospec reverse cli --source <dir>` | Reverse-engineer CLI/module structure |
| `evospec reverse deps --source <dir>` | Reverse-engineer cross-system API deps |
| `evospec deprecate contract <endpoint>` | Mark an API endpoint as deprecated |
| `evospec deprecate entity <name>` | Mark a domain entity as deprecated |
| `evospec archive [--dry-run]` | Archive completed/abandoned specs |
| `evospec status [--include-archived]` | Show status of all change specs |
| `evospec render [--include-archived]` | Render specs into consolidated markdown |
| `evospec generate agents` | Regenerate AI agent integration files |
| `evospec adr new "title"` | Create Architecture Decision Record |
| `evospec feature add "title"` | Register a new feature |
| `evospec learn` | Record experiment results |
| `evospec contract` | (AI workflow) Create domain contract |
| `evospec tasks` | (AI workflow) Generate implementation tasks |
| `evospec implement` | (AI workflow) Execute tasks phase by phase |
| `evospec serve` | Start MCP server for AI agent integration |
| `evospec prompt [--detect]` | Show this bootstrap prompt |

## MCP Server (for AI agent integration)

```bash
# Start the MCP server (after pipx install evospec)
evospec serve
# Or directly:
evospec-mcp
```

Configure in your AI tool:

```json
// Claude Desktop / Cursor / Windsurf MCP config:
{
  "mcpServers": {
    "evospec": {
      "command": "evospec-mcp"
    }
  }
}
```

Once connected, the agent can read `evospec://guide` for a full consumer walkthrough.

## Workflows (after init)

| Workflow | When to use |
|----------|-------------|
| `/evospec.discover` | Explore a new feature idea (edge zone) |
| `/evospec.improve` | Plan a well-understood improvement (skip discovery) |
| `/evospec.fix` | Diagnose and fix a bug |
| `/evospec.contract` | Create a domain contract (core/hybrid) |
| `/evospec.tasks` | Generate implementation tasks from spec |
| `/evospec.implement` | Execute tasks phase by phase |
| `/evospec.check` | Validate specs and run fitness functions |
| `/evospec.learn` | Record experiment results |
| `/evospec.adr` | Create an Architecture Decision Record |
| `/evospec.capture` | Retroactively formalize existing work into specs |

## Deprecation & Lifecycle

API contracts and entities support lifecycle management:
- `status: active|deprecated|removed` with `deprecated_at`, `sunset_date`, `replacement`
- MCP tools hide deprecated items by default and show warnings
- `evospec archive` moves completed/abandoned specs to `specs/archive/`

## Supported Frameworks

| Language | API Frameworks | ORM/DB | Build File |
|----------|---------------|--------|------------|
| Java | Spring Boot | JPA/Hibernate | pom.xml, build.gradle |
| Python | FastAPI, Django, Flask | SQLAlchemy, Django ORM | pyproject.toml, requirements.txt |
| Go | Gin, Echo, Fiber, Chi | GORM | go.mod |
| JS/TS | Express, Next.js, NestJS, Hono, Fastify | Prisma, TypeORM, Sequelize | package.json |

{% if detect and detection -%}
---

## Detected Project Stack

| Property | Value |
|----------|-------|
| **Language** | {{ detection.language or 'unknown' }} |
| **Framework** | {{ detection.framework or 'not detected' }} |
| **ORM** | {{ detection.orm or 'not detected' }} |
| **Build file** | {{ detection.build_file or 'none found' }} |
| **Project name** | {{ detection.project_name or 'unknown' }} |
{% if detection.source_dirs -%}
| **Source dirs** | {{ detection.source_dirs | join(', ') }} |
{% endif -%}

{% if detection.git_info -%}
### Git Analysis

| Metric | Value |
|--------|-------|
| Recent commits (30d) | {{ detection.git_info.recent_commits }} |
| Contributors (90d) | {{ detection.git_info.contributors | join(', ') if detection.git_info.contributors else 'none' }} |
| Primary language % | {{ detection.git_info.primary_language_pct }}% |
{% if detection.git_info.hot_files -%}

**Hot files** (most changed recently):
{% for f in detection.git_info.hot_files[:5] -%}
- `{{ f }}`
{% endfor -%}
{% endif -%}
{% endif -%}

### Recommended Commands

```bash
evospec init "{{ detection.project_name or 'my-project' }}"
{% if detection.framework -%}
evospec reverse api --framework {{ detection.framework }}
{% endif -%}
{% if detection.source_dirs -%}
evospec reverse db --source {{ detection.source_dirs[0] }}
evospec reverse cli --source {{ detection.source_dirs[0] }}
{% endif -%}
evospec generate agents
```
{% endif -%}
