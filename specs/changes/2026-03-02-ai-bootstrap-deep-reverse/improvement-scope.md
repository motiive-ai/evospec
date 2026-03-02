# Improvement Scope: AI Bootstrap Prompt + Deep Reverse Engineering

## What

Add `evospec prompt [--detect]` — a new CLI command that emits a self-contained AI bootstrap prompt, giving any AI agent everything it needs to configure EvoSpec on an existing project without reading EvoSpec source code. Additionally, enhance reverse engineering to analyze **git history** and **project structure** for deeper context during AI-assisted onboarding.

**Two capabilities:**
1. **`evospec prompt`** — Emit a markdown bootstrap prompt (~2-3KB) with CLI reference, step-by-step instructions, and (with `--detect`) auto-detected project stack
2. **Deep reverse engineering** — Enhance `evospec init` and reverse commands to analyze git log (recent changes, hot files, contributors), project structure (languages, frameworks, ORMs), and existing documentation to pre-populate `evospec.yaml` and domain files intelligently

## Why

When an AI agent encounters a project with `evospec` installed via `pipx`, it has **zero context** about what EvoSpec is or how to use it. The generated `CLAUDE.md` only exists **after** `evospec init` runs — a chicken-and-egg problem.

**Observed in practice** (Claude Code + Spring Boot project):
- Agent read the entire evospec source (~90K tokens) just to learn CLI commands
- Took ~60s of exploration to discover `evospec reverse api --framework spring`
- Framework detection was manual — agent had to figure out it was Spring Boot
- After init, agent had to manually update `evospec.yaml` with reverse config
- **Total bootstrap: ~3 minutes of AI exploration**, most of which was just learning what evospec can do

With `evospec prompt --detect`: **~30 seconds**, ~800 tokens instead of ~90K.

## Scope

### In Scope

**1. `evospec prompt` command**
- `src/evospec/core/prompt.py` — prompt generation + project detection logic
- `src/evospec/templates/prompts/bootstrap.md` — Jinja2 template for the bootstrap prompt
- `src/evospec/cli/main.py` — register `prompt` command
- `--detect` flag: auto-detect language, framework, source dirs, ORM, project name
- `--format markdown|json` — markdown for humans/agents, JSON for MCP/programmatic use

**2. Deep project detection**
- Scan build files: `pom.xml`, `build.gradle`, `package.json`, `go.mod`, `pyproject.toml`, `requirements.txt`
- Match dependencies → framework (spring, fastapi, express, gin, etc.)
- Detect ORM: JPA, SQLAlchemy, Prisma, TypeORM, GORM, etc.
- Detect source directories by convention
- Extract project name from build file metadata

**3. Git history analysis** (new capability)
- `git log --oneline -50` → recent change velocity and focus areas
- `git log --format='%aN' | sort -u` → contributors/team size
- `git diff --stat HEAD~20` → hot files (most changed recently)
- Map hot files to potential bounded contexts
- Suggest classification signals based on what changes most

**4. Enhanced `evospec init`**
- When AI agent runs init, auto-detect and pre-fill:
  - `reverse.framework` and `reverse.source_dirs`
  - Team name suggestion from git contributors
  - Project description from README.md or package metadata
- Pass detection results to init so the generated `evospec.yaml` is pre-configured

**5. MCP bootstrap resource**
- `evospec://bootstrap` — returns the bootstrap prompt via MCP
- Allows agents that connect to MCP before init to get configuration instructions

### Not In Scope

- Changes to existing reverse engineering output format (api, db, cli, deps)
- Automatic execution of reverse commands (prompt instructs, doesn't execute)
- IDE-specific integrations beyond the existing Windsurf/Claude/Cursor generation
- Natural language classification (that's a separate experiment)

## Invariant Impact

✓ No invariant conflicts. This adds new commands without modifying existing behavior.

Entities touched: `ProjectConfig` (enhanced init pre-fills config), `CanonicalWorkflow` (no changes, but bootstrap prompt references all workflows).

## Acceptance Criteria

1. `evospec prompt` outputs a complete bootstrap prompt (~2-3KB markdown) with CLI reference, workflow instructions, and step-by-step guide
2. `evospec prompt --detect` in a Spring Boot project correctly identifies: language=java, framework=spring, source_dirs=[src/main/java], orm=jpa
3. `evospec prompt --detect` in a FastAPI project correctly identifies: language=python, framework=fastapi
4. `evospec prompt --detect` in a Next.js project correctly identifies: language=typescript, framework=nextjs
5. `evospec prompt --format json` outputs valid JSON parseable by MCP clients
6. `evospec prompt --detect` analyzes git log and reports: recent velocity, hot files, contributors
7. `evospec init` with detection pre-fills `reverse.framework` and `reverse.source_dirs` in `evospec.yaml`
8. MCP `evospec://bootstrap` resource returns the bootstrap prompt
9. All existing tests pass (no regressions)
10. New tests cover detection logic for each supported language/framework

## Risks

- **Detection false positives**: A project with both `package.json` (frontend) and `pom.xml` (backend) could be misdetected. Mitigation: detect all stacks and present as suggestions, don't assume single-stack.
- **Git not available**: Some CI environments or fresh clones may not have git history. Mitigation: gracefully degrade — skip git analysis if `git` not found.
- **Stale build files**: A `requirements.txt` with Django doesn't mean the project uses Django if it's a transitive dependency. Mitigation: check for actual imports in source files, not just dependency declarations.

## Not In Scope

- Automatic reverse engineering execution (the prompt guides, the agent decides)
- Multi-language detection in monorepos (future improvement)
- Package manager lock file analysis (yarn.lock, poetry.lock)
