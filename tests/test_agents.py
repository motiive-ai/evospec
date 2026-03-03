"""Tests for AI agent file generation with skills injection."""

import tempfile
from pathlib import Path

import pytest
import yaml

from evospec.core.agents import generate_agents, _format_skills_markdown


SAMPLE_SKILLS = [
    {
        "category": "error-handling",
        "rules": [
            "Use Result<T, E> pattern for domain operations",
            "Map all external API errors to domain-specific error types",
        ],
    },
    {
        "category": "testing",
        "rules": [
            "Write integration tests for every API endpoint",
            "Use factory functions for test data",
        ],
    },
]


@pytest.fixture
def project_dir():
    """Create a temporary project with evospec.yaml and skills."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Minimal evospec.yaml
        (root / "evospec.yaml").write_text(yaml.dump({
            "project": {"name": "test-project"},
        }))
        yield root


@pytest.fixture
def project_with_skills(project_dir):
    """Project with skills.yaml containing sample skills."""
    domain_dir = project_dir / "specs" / "domain"
    domain_dir.mkdir(parents=True)
    (domain_dir / "skills.yaml").write_text(yaml.dump({
        "skills": SAMPLE_SKILLS,
    }))
    return project_dir


@pytest.fixture
def project_without_skills(project_dir):
    """Project without skills.yaml."""
    return project_dir


class TestFormatSkillsMarkdown:
    def test_empty_skills(self):
        assert _format_skills_markdown([]) == ""

    def test_skills_formatted(self):
        result = _format_skills_markdown(SAMPLE_SKILLS)
        assert "## Implementation Skills" in result
        assert "### Error Handling" in result
        assert "### Testing" in result
        assert "- Use Result<T, E> pattern for domain operations" in result
        assert "- Write integration tests for every API endpoint" in result

    def test_category_title_casing(self):
        skills = [{"category": "error-handling", "rules": ["rule1"]}]
        result = _format_skills_markdown(skills)
        assert "### Error Handling" in result


class TestClaudeSkillsInjection:
    """SKILLS-001: Skills MUST be included in generated CLAUDE.md."""

    def test_claude_includes_skills(self, project_with_skills):
        results = generate_agents(dest=project_with_skills, platforms=["claude"])
        claude_md = project_with_skills / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert "## Implementation Skills" in content
        assert "Error Handling" in content
        assert "Use Result<T, E> pattern" in content
        assert "Write integration tests" in content

    def test_claude_no_skills_section_without_skills(self, project_without_skills):
        results = generate_agents(dest=project_without_skills, platforms=["claude"])
        claude_md = project_without_skills / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert "## Implementation Skills" not in content


class TestWindsurfSkillsInjection:
    """SKILLS-001: Skills MUST be included in generated .windsurf/ files."""

    def test_windsurf_implement_includes_skills(self, project_with_skills):
        results = generate_agents(dest=project_with_skills, platforms=["windsurf"])
        implement_md = project_with_skills / ".windsurf" / "workflows" / "evospec.implement.md"
        assert implement_md.exists()
        content = implement_md.read_text()
        assert "## Implementation Skills" in content
        assert "Error Handling" in content

    def test_windsurf_discover_no_skills(self, project_with_skills):
        """Skills only injected into implement workflow, not discovery."""
        results = generate_agents(dest=project_with_skills, platforms=["windsurf"])
        discover_md = project_with_skills / ".windsurf" / "workflows" / "evospec.discover.md"
        assert discover_md.exists()
        content = discover_md.read_text()
        assert "## Implementation Skills" not in content


class TestCursorSkillsInjection:
    """SKILLS-001: Skills MUST be included in generated .cursor/ files."""

    def test_cursor_context_includes_skills(self, project_with_skills):
        results = generate_agents(dest=project_with_skills, platforms=["cursor"])
        cursor_mdc = project_with_skills / ".cursor" / "rules" / "evospec.mdc"
        assert cursor_mdc.exists()
        content = cursor_mdc.read_text()
        assert "## Implementation Skills" in content
        assert "Error Handling" in content

    def test_cursor_no_skills_without_skills(self, project_without_skills):
        results = generate_agents(dest=project_without_skills, platforms=["cursor"])
        cursor_mdc = project_without_skills / ".cursor" / "rules" / "evospec.mdc"
        assert cursor_mdc.exists()
        content = cursor_mdc.read_text()
        assert "## Implementation Skills" not in content


class TestAgentSkillsInjection:
    """SKILLS-001: Skills MUST be included in generated .agents/skills/ files."""

    def test_skills_context_includes_project_skills(self, project_with_skills):
        results = generate_agents(dest=project_with_skills, platforms=["skills"])
        # Check the shared context.md in any skill directory
        implement_ctx = (
            project_with_skills / ".agents" / "skills" / "evospec-implement"
            / "references" / "context.md"
        )
        assert implement_ctx.exists()
        content = implement_ctx.read_text()
        assert "## Implementation Skills" in content
        assert "Error Handling" in content
