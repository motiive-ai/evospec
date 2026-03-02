# Implementation Spec: AI Bootstrap Prompt + Deep Reverse Engineering

> Zone: **hybrid** | Status: **skeleton** | Created by `/evospec.tasks`
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
| BOOT-INV-001: works without evospec.yaml | ⬜ pending | |
| BOOT-INV-002: graceful git degradation | ⬜ pending | |
| BOOT-INV-003: read-only detection | ⬜ pending | |
| BOOT-INV-004: valid JSON output | ⬜ pending | |

## 7. Reproduction Instructions

*To be filled after implementation.*

## 8. Known Limitations & Tech Debt

*To be filled after implementation.*

---

## Changelog

| Date | Phase | What changed |
|------|-------|-------------|
| 2026-03-02 | /evospec.tasks | Skeleton created |
