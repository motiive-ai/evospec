"""Tests for user journey gap fixes (G1-G11)."""

import os
import shutil
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
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def _init_project(runner, project_dir):
    os.chdir(project_dir)
    runner.invoke(cli, ["init", "--name", "test"])


def _safe_chdir(path: Path):
    os.chdir(path)


# ---------------------------------------------------------------------------
# G1: evospec status --include-archived
# ---------------------------------------------------------------------------


class TestG1StatusArchived:
    def test_status_shows_archived_count(self, runner, project_dir):
        """evospec status shows how many archived specs are hidden."""
        _init_project(runner, project_dir)
        runner.invoke(cli, ["new", "feat-done", "--zone", "edge"])

        # Mark as completed and archive
        specs_dir = project_dir / "specs" / "changes"
        for d in specs_dir.iterdir():
            if "feat-done" in d.name:
                spec_yaml = d / "spec.yaml"
                spec = yaml.safe_load(spec_yaml.read_text())
                spec["status"] = "completed"
                spec_yaml.write_text(yaml.dump(spec))

        _safe_chdir(project_dir)
        runner.invoke(cli, ["archive"])

        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "archived" in result.output.lower()
        _safe_chdir(Path(__file__).parent)

    def test_status_include_archived_flag(self, runner, project_dir):
        """evospec status --include-archived shows archived specs."""
        _init_project(runner, project_dir)
        runner.invoke(cli, ["new", "feat-done", "--zone", "edge"])

        specs_dir = project_dir / "specs" / "changes"
        for d in specs_dir.iterdir():
            if "feat-done" in d.name:
                spec_yaml = d / "spec.yaml"
                spec = yaml.safe_load(spec_yaml.read_text())
                spec["status"] = "completed"
                spec_yaml.write_text(yaml.dump(spec))

        _safe_chdir(project_dir)
        runner.invoke(cli, ["archive"])

        result = runner.invoke(cli, ["status", "--include-archived"])
        assert result.exit_code == 0
        assert "feat-done" in result.output.lower() or "archived" in result.output.lower()
        _safe_chdir(Path(__file__).parent)


# ---------------------------------------------------------------------------
# G2: evospec render --include-archived
# ---------------------------------------------------------------------------


class TestG2RenderArchived:
    def test_render_include_archived_flag(self, runner, project_dir):
        """evospec render --include-archived includes archived specs in SPECS.md."""
        _init_project(runner, project_dir)
        runner.invoke(cli, ["new", "archived-feat", "--zone", "edge"])

        specs_dir = project_dir / "specs" / "changes"
        for d in specs_dir.iterdir():
            if "archived-feat" in d.name:
                spec_yaml = d / "spec.yaml"
                spec = yaml.safe_load(spec_yaml.read_text())
                spec["status"] = "completed"
                spec_yaml.write_text(yaml.dump(spec))

        _safe_chdir(project_dir)
        runner.invoke(cli, ["archive"])

        result = runner.invoke(cli, ["render", "--include-archived"])
        assert result.exit_code == 0
        specs_md = (project_dir / "SPECS.md").read_text()
        assert "archived-feat" in specs_md
        _safe_chdir(Path(__file__).parent)


# ---------------------------------------------------------------------------
# G4: evospec new suggests feature add
# ---------------------------------------------------------------------------


class TestG4NewFeatureLink:
    def test_new_suggests_feature_add(self, runner, project_dir):
        """evospec new outputs a suggestion to track as feature."""
        _init_project(runner, project_dir)

        result = runner.invoke(cli, ["new", "my-cool-feature", "--zone", "edge"])
        assert result.exit_code == 0
        assert "feature add" in result.output.lower()
        _safe_chdir(Path(__file__).parent)


# ---------------------------------------------------------------------------
# G7: CLI stubs for contract/tasks/implement
# ---------------------------------------------------------------------------


class TestG7WorkflowStubs:
    def test_contract_stub(self, runner, project_dir):
        result = runner.invoke(cli, ["contract"])
        assert result.exit_code == 0
        assert "AI agent workflow" in result.output or "evospec.contract" in result.output

    def test_tasks_stub(self, runner, project_dir):
        result = runner.invoke(cli, ["tasks"])
        assert result.exit_code == 0
        assert "AI agent workflow" in result.output or "evospec.tasks" in result.output

    def test_implement_stub(self, runner, project_dir):
        result = runner.invoke(cli, ["implement"])
        assert result.exit_code == 0
        assert "AI agent workflow" in result.output or "evospec.implement" in result.output


# ---------------------------------------------------------------------------
# G8: capture --help shows distinction
# ---------------------------------------------------------------------------


class TestG8CaptureNaming:
    def test_capture_help_mentions_workflow(self, runner, project_dir):
        """capture --help clarifies the difference from /evospec.capture."""
        result = runner.invoke(cli, ["capture", "--help"])
        assert "evospec.capture" in result.output
        assert "git history" in result.output.lower()


# ---------------------------------------------------------------------------
# G10: evospec deprecate contract/entity
# ---------------------------------------------------------------------------


class TestG10DeprecateCli:
    def test_deprecate_contract(self, runner, project_dir):
        """evospec deprecate contract marks endpoint as deprecated."""
        _init_project(runner, project_dir)
        domain_dir = project_dir / "specs" / "domain"
        contracts = {
            "contracts": [
                {"endpoint": "GET /api/orders/all", "response": {200: {"fields": []}}, "tags": ["orders"]},
                {"endpoint": "GET /api/orders", "response": {200: {"fields": []}}, "tags": ["orders"]},
            ]
        }
        (domain_dir / "api-contracts.yaml").write_text(yaml.dump(contracts))

        _safe_chdir(project_dir)
        try:
            result = runner.invoke(cli, ["deprecate", "contract", "GET /api/orders/all",
                                         "--replacement", "GET /api/orders", "--sunset", "2026-06-01"])
            assert result.exit_code == 0
            assert "Deprecated" in result.output

            # Verify file was updated
            updated = yaml.safe_load((domain_dir / "api-contracts.yaml").read_text())
            deprecated_c = [c for c in updated["contracts"] if "all" in c["endpoint"]][0]
            assert deprecated_c["status"] == "deprecated"
            assert deprecated_c["replacement"] == "GET /api/orders"
            assert deprecated_c["sunset_date"] == "2026-06-01"
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_deprecate_entity(self, runner, project_dir):
        """evospec deprecate entity marks entity as deprecated."""
        _init_project(runner, project_dir)
        domain_dir = project_dir / "specs" / "domain"
        entities = [
            {"name": "OrderV1", "context": "orders", "fields": []},
            {"name": "OrderV2", "context": "orders", "fields": []},
        ]
        (domain_dir / "entities.yaml").write_text(yaml.dump(entities))

        _safe_chdir(project_dir)
        try:
            result = runner.invoke(cli, ["deprecate", "entity", "OrderV1",
                                         "--replacement", "OrderV2"])
            assert result.exit_code == 0
            assert "Deprecated" in result.output

            updated = yaml.safe_load((domain_dir / "entities.yaml").read_text())
            deprecated_e = [e for e in updated if e["name"] == "OrderV1"][0]
            assert deprecated_e["status"] == "deprecated"
            assert deprecated_e["replacement"] == "OrderV2"
        finally:
            _safe_chdir(Path(__file__).parent)


# ---------------------------------------------------------------------------
# G11: evospec archive updates features.yaml paths
# ---------------------------------------------------------------------------


class TestG11ArchiveFeatures:
    def test_archive_updates_features_yaml(self, runner, project_dir):
        """evospec archive updates features.yaml spec_path references."""
        _init_project(runner, project_dir)
        runner.invoke(cli, ["new", "done-feat", "--zone", "edge"])

        # Find the spec dir name
        specs_dir = project_dir / "specs" / "changes"
        spec_dir_name = None
        for d in specs_dir.iterdir():
            if "done-feat" in d.name:
                spec_dir_name = d.name
                spec_yaml = d / "spec.yaml"
                spec = yaml.safe_load(spec_yaml.read_text())
                spec["status"] = "completed"
                spec_yaml.write_text(yaml.dump(spec))

        # Create a feature entry pointing to this spec
        features_path = project_dir / "specs" / "domain" / "features.yaml"
        features = [
            {
                "id": "feat-test",
                "title": "Done Feature",
                "zone": "edge",
                "status": "shipped",
                "knowledge_stage": "mystery",
                "spec_path": f"specs/changes/{spec_dir_name}",
                "owner": "test",
                "created_at": "2026-03-03",
                "shipped_at": "2026-03-03",
                "kill_reason": "",
            }
        ]
        features_path.write_text(yaml.dump(features))

        _safe_chdir(project_dir)
        try:
            from evospec.core.archive import run_archive
            run_archive()

            # Check that features.yaml was updated
            updated = yaml.safe_load(features_path.read_text())
            assert updated[0]["spec_path"] == f"specs/archive/{spec_dir_name}"
        finally:
            _safe_chdir(Path(__file__).parent)


# ---------------------------------------------------------------------------
# G9: list_specs includes invariant_count
# ---------------------------------------------------------------------------


class TestG9ListSpecsInvariants:
    def test_list_specs_has_invariant_count(self, runner, project_dir):
        """list_specs() includes invariant_count in each entry."""
        from evospec.mcp.server import list_specs

        _init_project(runner, project_dir)
        runner.invoke(cli, ["new", "core-feat", "--zone", "core"])

        _safe_chdir(project_dir)
        try:
            result = list_specs()
            assert result["count"] >= 1
            for spec in result["specs"]:
                assert "invariant_count" in spec
        finally:
            _safe_chdir(Path(__file__).parent)
