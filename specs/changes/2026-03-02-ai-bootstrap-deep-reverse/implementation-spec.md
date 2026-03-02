# Implementation Spec: AI Bootstrap Prompt + Deep Reverse Engineering

> Zone: **hybrid** | Status: **implemented** | Created by `/evospec.tasks`
>
> This document will be updated incrementally during `/evospec.implement`.

---

## 1. Overview

- **Tech Stack**: Python 3.10+, Click CLI, Jinja2 templates, FastMCP
- **Architecture Style**: CLI command + core module + template
- **Zone**: Hybrid (crosses reverse-engineering → agent-integration boundary)
- **Key Decisions**: Jinja2 for prompt template (consistent with existing template system), dataclasses for detection results

## 2. Component Architecture

| Component | File | Responsibility |
|-----------|------|---------------|
| Prompt core | `src/evospec/core/prompt.py` | Detection logic + prompt generation |
| Bootstrap template | `src/evospec/templates/prompts/bootstrap.md` | Jinja2 template for AI prompt |
| CLI command | `src/evospec/cli/main.py` | `evospec prompt` registration |
| MCP resource | `src/evospec/mcp/server.py` | `evospec://bootstrap` resource |
| Init enhancement | `src/evospec/core/init.py` | Pre-fill from detection |

## 3. API Integration

N/A — this is a CLI tool, not an API consumer.

## 4. State Management

N/A — stateless detection. No persistent state.

## 5. Configuration

| Config | Source | Default |
|--------|--------|---------|
| `--detect` | CLI flag | `false` |
| `--format` | CLI flag | `markdown` |

## 6. Invariant Compliance

| Invariant | Status | Implementation |
|-----------|--------|---------------|
| BOOT-INV-001: works without evospec.yaml | ✅ done | `prompt` CLI command never calls `find_project_root()`. Tests: `test_prompt_without_evospec_yaml`, `test_prompt_json_without_evospec_yaml` |
| BOOT-INV-002: graceful git degradation | ✅ done | `analyze_git_history()` catches `FileNotFoundError`, `TimeoutExpired`, non-zero returncode → returns `None`. Tests: `test_no_git_binary`, `test_not_a_git_repo`, `test_git_timeout` |
| BOOT-INV-003: read-only detection | ✅ done | All detect_* functions only call `Path.exists()`, `Path.read_text()`, `Path.iterdir()` — no writes. By design. |
| BOOT-INV-004: valid JSON output | ✅ done | `generate_bootstrap_json()` uses `json.dumps(data, indent=2)`. Tests: `test_prompt_json_output`, `test_prompt_json_with_detect` parse output with `json.loads()` |

## 7. Reproduction Instructions

```bash
# Basic prompt (no detection)
evospec prompt

# With auto-detection (scans build files, dependencies, git history)
evospec prompt --detect

# JSON format for programmatic use
evospec prompt --format json --detect

# Init with auto-detection pre-fill
evospec init --name my-project --detect

# MCP resource (via MCP client)
# Read evospec://bootstrap

# Run tests
pytest tests/test_prompt.py -v
```

## 8. Known Limitations & Tech Debt

- **Single-stack detection**: picks the first matching build file by priority order (pom.xml > package.json > etc.). Monorepos with multiple languages will only detect the first one.
- **No lock file analysis**: doesn't parse yarn.lock, poetry.lock, go.sum for transitive dependency accuracy.
- **Framework detection heuristic**: checks dependency names in build files, not actual source imports. A stale `requirements.txt` with Django listed as a transitive dep could false-positive.
- **Git analysis subprocess**: shells out to `git` binary. Adds ~100ms on typical repos. Timeout set to 5-10s per command.

---

## Changelog

| Date | Phase | What changed |
|------|-------|-------------|
| 2026-03-02 | /evospec.tasks | Skeleton created |
| 2026-03-02 | /evospec.implement | Full implementation: prompt.py (detection + generation), bootstrap.md template, CLI command, MCP resource, enhanced init, 48 tests |
