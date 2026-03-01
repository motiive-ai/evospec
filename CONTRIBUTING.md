# Contributing to EvoSpec

Thank you for your interest in contributing to EvoSpec!

## Development Setup

```bash
# Clone the repository
git clone https://github.com/evospec/evospec.git
cd evospec

# Install in development mode with pipx
pipx install -e ".[dev]"

# Or with a virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/ tests/

# Run type checker
mypy src/
```

## Project Structure

```
evospec/
├── src/evospec/
│   ├── cli/           # CLI commands (Click)
│   ├── core/          # Core logic (init, classify, check, etc.)
│   ├── reverse/       # Reverse engineering modules
│   ├── rules/         # Built-in validation rules
│   └── templates/     # Spec templates (Markdown + YAML)
├── schemas/           # JSON Schema for spec.yaml
├── tests/             # Test suite
├── examples/          # Worked examples
└── docs/              # Documentation
```

## How to Contribute

### Reporting Issues
- Use GitHub Issues
- Include steps to reproduce
- Include expected vs. actual behavior

### Branching Strategy

The `main` branch is **protected** — no direct commits allowed.

```bash
# Always work on a feature branch
git checkout -b feat/my-feature main

# When done, push and open a PR
git push origin feat/my-feature
```

Branch naming conventions:
- `feat/short-description` — new features
- `fix/short-description` — bug fixes
- `docs/short-description` — documentation changes
- `chore/short-description` — maintenance, CI, tooling

### Pull Requests
1. Fork the repository
2. Create a feature branch from `main`
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a PR with a clear description

### Adding a New Template
1. Create the template in `src/evospec/templates/`
2. Use `{{ variable }}` syntax for substitution
3. Update the `new_spec.py` or relevant command to use it
4. Add tests

### Adding a Reverse Engineering Module
1. Create a scanner in `src/evospec/reverse/`
2. Register it in the CLI (`cli/main.py`)
3. Add tests with sample fixtures

## Code Style

- Python 3.10+ with type hints
- Follow existing patterns
- Use `rich` for CLI output
- Use `click` for CLI commands
- Keep modules focused and small

## Philosophy

EvoSpec is guided by the principles in [MANIFESTO.md](MANIFESTO.md). When in doubt:

- **Proportional**: Don't over-engineer. Specs should be proportional to risk.
- **Executable**: Prefer automated checks over documented guidelines.
- **Minimal**: One page is better than ten. Keep templates lean.
- **Extensible**: Design for plugins and customization.
