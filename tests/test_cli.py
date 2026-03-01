"""Tests for the EvoSpec CLI."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from evospec.cli.main import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def project_dir():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestVersion:
    def test_version(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "evospec" in result.output


class TestInit:
    def test_init_creates_structure(self, runner, project_dir):
        os.chdir(project_dir)
        result = runner.invoke(cli, ["init"], input="test-project\n\n")
        assert result.exit_code == 0
        assert "initialized successfully" in result.output

        # Check files created
        assert (project_dir / "evospec.yaml").exists()
        assert (project_dir / "specs" / "changes").exists()
        assert (project_dir / "specs" / "_templates").exists()
        assert (project_dir / "docs" / "adr").exists()
        assert (project_dir / "specs" / "domain").exists()
        assert (project_dir / "specs" / "domain" / "glossary.md").exists()
        assert (project_dir / "specs" / "domain" / "context-map.md").exists()
        assert (project_dir / "docs" / "adr" / "0001-adopt-evospec.md").exists()

    def test_init_sets_project_name(self, runner, project_dir):
        os.chdir(project_dir)
        result = runner.invoke(cli, ["init", "--name", "my-project"])
        assert result.exit_code == 0

        config = yaml.safe_load((project_dir / "evospec.yaml").read_text())
        assert config["project"]["name"] == "my-project"

    def test_init_idempotent(self, runner, project_dir):
        os.chdir(project_dir)
        runner.invoke(cli, ["init", "--name", "test"])
        result = runner.invoke(cli, ["init", "--name", "test"])
        assert "already exists" in result.output


class TestNew:
    def test_new_edge_spec(self, runner, project_dir):
        os.chdir(project_dir)
        runner.invoke(cli, ["init", "--name", "test"])
        result = runner.invoke(cli, ["new", "user-onboarding", "--zone", "edge"])
        assert result.exit_code == 0
        assert "Created spec" in result.output

        # Find the created spec directory
        specs_dir = project_dir / "specs" / "changes"
        spec_dirs = list(specs_dir.iterdir())
        assert len(spec_dirs) == 1

        spec_dir = spec_dirs[0]
        assert (spec_dir / "spec.yaml").exists()
        assert (spec_dir / "discovery-spec.md").exists()
        assert not (spec_dir / "domain-contract.md").exists()

    def test_new_core_spec(self, runner, project_dir):
        os.chdir(project_dir)
        runner.invoke(cli, ["init", "--name", "test"])
        result = runner.invoke(cli, ["new", "auth-redesign", "--zone", "core"])
        assert result.exit_code == 0

        specs_dir = project_dir / "specs" / "changes"
        spec_dir = list(specs_dir.iterdir())[0]
        assert (spec_dir / "domain-contract.md").exists()
        assert not (spec_dir / "discovery-spec.md").exists()

    def test_new_hybrid_spec(self, runner, project_dir):
        os.chdir(project_dir)
        runner.invoke(cli, ["init", "--name", "test"])
        result = runner.invoke(cli, ["new", "pricing-page", "--zone", "hybrid"])
        assert result.exit_code == 0

        specs_dir = project_dir / "specs" / "changes"
        spec_dir = list(specs_dir.iterdir())[0]
        assert (spec_dir / "discovery-spec.md").exists()
        assert (spec_dir / "domain-contract.md").exists()

    def test_new_without_init(self, runner, project_dir):
        os.chdir(project_dir)
        result = runner.invoke(cli, ["new", "something"])
        assert "evospec init" in result.output


class TestAdr:
    def test_adr_new(self, runner, project_dir):
        os.chdir(project_dir)
        runner.invoke(cli, ["init", "--name", "test"])
        result = runner.invoke(cli, ["adr", "new", "use-postgres"])
        assert result.exit_code == 0
        assert "ADR-0002" in result.output  # 0001 is created by init

        adr_file = project_dir / "docs" / "adr" / "0002-use-postgres.md"
        assert adr_file.exists()
        content = adr_file.read_text()
        assert "use-postgres" in content
        assert "proposed" in content

    def test_adr_list(self, runner, project_dir):
        os.chdir(project_dir)
        runner.invoke(cli, ["init", "--name", "test"])
        runner.invoke(cli, ["adr", "new", "use-postgres"])
        result = runner.invoke(cli, ["adr", "list"])
        assert result.exit_code == 0
        assert "Adopt EvoSpec" in result.output
        assert "use-postgres" in result.output


class TestStatus:
    def test_status_empty(self, runner, project_dir):
        os.chdir(project_dir)
        runner.invoke(cli, ["init", "--name", "test"])
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0

    def test_status_with_specs(self, runner, project_dir):
        os.chdir(project_dir)
        runner.invoke(cli, ["init", "--name", "test"])
        runner.invoke(cli, ["new", "feature-a", "--zone", "edge"])
        runner.invoke(cli, ["new", "feature-b", "--zone", "core"])
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "feature-a" in result.output
        assert "feature-b" in result.output


class TestCheck:
    def test_check_valid_edge(self, runner, project_dir):
        os.chdir(project_dir)
        runner.invoke(cli, ["init", "--name", "test"])
        runner.invoke(cli, ["new", "experiment", "--zone", "edge"])

        # Update spec with required edge fields
        specs_dir = project_dir / "specs" / "changes"
        spec_dir = list(specs_dir.iterdir())[0]
        spec_yaml = spec_dir / "spec.yaml"
        spec = yaml.safe_load(spec_yaml.read_text())
        spec["discovery"] = {
            "outcome": "Increase activation by 10%",
            "opportunity": "Users don't understand onboarding",
            "kill_criteria": "If no improvement after 2 weeks",
            "assumptions": [],
        }
        with open(spec_yaml, "w") as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

        result = runner.invoke(cli, ["check"])
        assert result.exit_code == 0

    def test_check_core_missing_invariants(self, runner, project_dir):
        os.chdir(project_dir)
        runner.invoke(cli, ["init", "--name", "test"])
        runner.invoke(cli, ["new", "auth-change", "--zone", "core"])

        result = runner.invoke(cli, ["check"])
        # Should fail because core requires bounded_context, invariants, fitness_functions
        assert result.exit_code == 1


class TestRender:
    def test_render_creates_file(self, runner, project_dir):
        os.chdir(project_dir)
        runner.invoke(cli, ["init", "--name", "test"])
        runner.invoke(cli, ["new", "feature-a", "--zone", "edge"])
        result = runner.invoke(cli, ["render"])
        assert result.exit_code == 0
        assert (project_dir / "SPECS.md").exists()

        content = (project_dir / "SPECS.md").read_text()
        assert "feature-a" in content
