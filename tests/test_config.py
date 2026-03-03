"""Tests for config path resolution and skills loading."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from evospec.core.config import get_paths, load_config, load_skills


@pytest.fixture
def project_dir():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def _create_evospec_yaml(project_dir: Path, paths: dict | None = None) -> None:
    """Helper to create a minimal evospec.yaml."""
    config = {"project": {"name": "test"}}
    if paths:
        config["paths"] = paths
    (project_dir / "evospec.yaml").write_text(yaml.dump(config))


class TestGetPaths:
    def test_default_paths(self):
        """Default paths when no config provided (CUSTOM-PATH-002)."""
        result = get_paths({})
        assert result["specs"] == "specs/changes"
        assert result["domain"] == "specs/domain"
        assert result["templates"] == "specs/_templates"
        assert result["adrs"] == "docs/adr"
        assert result["checks"] == "specs/checks"

    def test_custom_specs_path(self):
        """Custom paths.specs respected (CUSTOM-PATH-001)."""
        config = {"paths": {"specs": "evospec/changes"}}
        result = get_paths(config)
        assert result["specs"] == "evospec/changes"

    def test_custom_domain_path(self):
        """Custom paths.domain respected independently."""
        config = {"paths": {"domain": "evospec/domain"}}
        result = get_paths(config)
        assert result["domain"] == "evospec/domain"
        # Other paths remain default
        assert result["specs"] == "specs/changes"

    def test_all_custom_paths(self):
        """All paths configurable simultaneously."""
        config = {"paths": {
            "specs": ".evospec/changes",
            "domain": ".evospec/domain",
            "templates": ".evospec/_templates",
            "adrs": ".evospec/adr",
            "checks": ".evospec/checks",
        }}
        result = get_paths(config)
        assert result["specs"] == ".evospec/changes"
        assert result["domain"] == ".evospec/domain"
        assert result["templates"] == ".evospec/_templates"
        assert result["adrs"] == ".evospec/adr"
        assert result["checks"] == ".evospec/checks"


class TestLoadConfigCustomPaths:
    def test_load_config_with_custom_domain(self, project_dir):
        """load_config() reads domain files from custom domain path."""
        # Setup custom paths
        _create_evospec_yaml(project_dir, paths={
            "specs": "evospec/changes",
            "domain": "evospec/domain",
        })

        # Create domain files at custom path
        domain_dir = project_dir / "evospec" / "domain"
        domain_dir.mkdir(parents=True)
        (domain_dir / "entities.yaml").write_text(
            yaml.dump([{"name": "Order", "context": "orders"}])
        )

        config = load_config(project_dir)
        assert config["domain"]["entities"] == [{"name": "Order", "context": "orders"}]

    def test_load_config_default_paths_backward_compat(self, project_dir):
        """load_config() works with default paths (backward compat CUSTOM-PATH-002)."""
        _create_evospec_yaml(project_dir)

        # Create domain files at default path
        domain_dir = project_dir / "specs" / "domain"
        domain_dir.mkdir(parents=True)
        (domain_dir / "entities.yaml").write_text(
            yaml.dump([{"name": "Product", "context": "catalog"}])
        )

        config = load_config(project_dir)
        assert config["domain"]["entities"] == [{"name": "Product", "context": "catalog"}]


class TestLoadSkills:
    def test_load_skills_empty(self, project_dir):
        """No skills when skills.yaml doesn't exist."""
        _create_evospec_yaml(project_dir)
        (project_dir / "specs" / "domain").mkdir(parents=True)
        result = load_skills(project_root=project_dir)
        assert result == []

    def test_load_skills_with_data(self, project_dir):
        """Load skills from skills.yaml."""
        _create_evospec_yaml(project_dir)
        domain_dir = project_dir / "specs" / "domain"
        domain_dir.mkdir(parents=True)
        (domain_dir / "skills.yaml").write_text(yaml.dump({
            "skills": [
                {"category": "testing", "rules": ["Write tests first"]},
                {"category": "architecture", "rules": ["Use hexagonal"]},
            ]
        }))

        result = load_skills(project_root=project_dir)
        assert len(result) == 2
        assert result[0]["category"] == "testing"
        assert result[0]["rules"] == ["Write tests first"]

    def test_load_skills_custom_domain_path(self, project_dir):
        """Skills loaded from custom domain path."""
        _create_evospec_yaml(project_dir, paths={"domain": "evospec/domain"})
        domain_dir = project_dir / "evospec" / "domain"
        domain_dir.mkdir(parents=True)
        (domain_dir / "skills.yaml").write_text(yaml.dump({
            "skills": [
                {"category": "security", "rules": ["Validate all input"]},
            ]
        }))

        result = load_skills(project_root=project_dir)
        assert len(result) == 1
        assert result[0]["category"] == "security"

    def test_load_skills_empty_skills_list(self, project_dir):
        """Empty skills list returns empty."""
        _create_evospec_yaml(project_dir)
        domain_dir = project_dir / "specs" / "domain"
        domain_dir.mkdir(parents=True)
        (domain_dir / "skills.yaml").write_text("skills: []\n")

        result = load_skills(project_root=project_dir)
        assert result == []

    def test_load_skills_no_project(self):
        """No project root returns empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_skills(project_root=Path(tmpdir))
            assert result == []
