"""Tests for deprecation awareness in MCP tools and spec archiving."""

import os
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from evospec.cli.main import cli
from evospec.core.archive import run_archive


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
# API Contract deprecation tests
# ---------------------------------------------------------------------------


class TestApiContractDeprecation:
    def test_deprecated_contract_hidden_by_default(self, runner, project_dir):
        """Deprecated API contracts are hidden from get_api_contract by default."""
        from evospec.mcp.server import get_api_contract

        _init_project(runner, project_dir)
        domain_dir = project_dir / "specs" / "domain"
        contracts = {
            "contracts": [
                {"endpoint": "GET /api/v1/orders", "status": "deprecated",
                 "replacement": "GET /api/v2/orders", "sunset_date": "2026-06-01",
                 "response": {200: {"fields": []}}, "tags": ["orders"]},
                {"endpoint": "GET /api/v2/orders",
                 "response": {200: {"fields": []}}, "tags": ["orders"]},
            ]
        }
        (domain_dir / "api-contracts.yaml").write_text(yaml.dump(contracts))

        _safe_chdir(project_dir)
        try:
            result = get_api_contract()
            assert result["count"] == 1
            assert result["contracts"][0]["endpoint"] == "GET /api/v2/orders"
            assert result["deprecated_count"] == 1
            assert len(result["deprecation_warnings"]) == 1
            assert "GET /api/v1/orders" in result["deprecation_warnings"][0]
            assert "GET /api/v2/orders" in result["deprecation_warnings"][0]
            assert "sunset: 2026-06-01" in result["deprecation_warnings"][0]
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_deprecated_contract_shown_with_flag(self, runner, project_dir):
        """Deprecated contracts visible when include_deprecated=True."""
        from evospec.mcp.server import get_api_contract

        _init_project(runner, project_dir)
        domain_dir = project_dir / "specs" / "domain"
        contracts = {
            "contracts": [
                {"endpoint": "GET /api/v1/orders", "status": "deprecated",
                 "replacement": "GET /api/v2/orders",
                 "response": {200: {"fields": []}}, "tags": ["orders"]},
                {"endpoint": "GET /api/v2/orders",
                 "response": {200: {"fields": []}}, "tags": ["orders"]},
            ]
        }
        (domain_dir / "api-contracts.yaml").write_text(yaml.dump(contracts))

        _safe_chdir(project_dir)
        try:
            result = get_api_contract(include_deprecated=True)
            assert result["count"] == 2
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_active_contracts_unaffected(self, runner, project_dir):
        """Contracts without status field default to active."""
        from evospec.mcp.server import get_api_contract

        _init_project(runner, project_dir)
        domain_dir = project_dir / "specs" / "domain"
        contracts = {
            "contracts": [
                {"endpoint": "GET /api/orders",
                 "response": {200: {"fields": []}}, "tags": ["orders"]},
            ]
        }
        (domain_dir / "api-contracts.yaml").write_text(yaml.dump(contracts))

        _safe_chdir(project_dir)
        try:
            result = get_api_contract()
            assert result["count"] == 1
            assert "deprecated_count" not in result
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_removed_contract_hidden(self, runner, project_dir):
        """Removed contracts also hidden by default."""
        from evospec.mcp.server import get_api_contract

        _init_project(runner, project_dir)
        domain_dir = project_dir / "specs" / "domain"
        contracts = {
            "contracts": [
                {"endpoint": "GET /api/legacy", "status": "removed",
                 "response": {200: {"fields": []}}},
            ]
        }
        (domain_dir / "api-contracts.yaml").write_text(yaml.dump(contracts))

        _safe_chdir(project_dir)
        try:
            result = get_api_contract()
            assert result["count"] == 0
            assert result["deprecated_count"] == 1
        finally:
            _safe_chdir(Path(__file__).parent)


# ---------------------------------------------------------------------------
# Entity deprecation tests
# ---------------------------------------------------------------------------


class TestEntityDeprecation:
    def test_deprecated_entity_hidden(self, runner, project_dir):
        """Deprecated entities hidden from get_entities by default."""
        from evospec.mcp.server import get_entities

        _init_project(runner, project_dir)
        domain_dir = project_dir / "specs" / "domain"
        entities = [
            {"name": "OrderV1", "context": "orders", "status": "deprecated",
             "replacement": "OrderV2", "fields": []},
            {"name": "OrderV2", "context": "orders", "fields": []},
        ]
        (domain_dir / "entities.yaml").write_text(yaml.dump(entities))

        _safe_chdir(project_dir)
        try:
            result = get_entities()
            text = result["text"]
            assert "OrderV2" in text
            assert "OrderV1" not in text or "hidden" in text.lower()
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_deprecated_entity_shown_with_flag(self, runner, project_dir):
        """Deprecated entities visible with include_deprecated=True."""
        from evospec.mcp.server import get_entities

        _init_project(runner, project_dir)
        domain_dir = project_dir / "specs" / "domain"
        entities = [
            {"name": "OrderV1", "context": "orders", "status": "deprecated",
             "replacement": "OrderV2", "fields": []},
            {"name": "OrderV2", "context": "orders", "fields": []},
        ]
        (domain_dir / "entities.yaml").write_text(yaml.dump(entities))

        _safe_chdir(project_dir)
        try:
            result = get_entities(include_deprecated=True)
            text = result["text"]
            assert "OrderV1" in text
            assert "DEPRECATED" in text
            assert "OrderV2" in text
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_entity_without_status_defaults_active(self, runner, project_dir):
        """Entities without status field default to active."""
        from evospec.mcp.server import get_entities

        _init_project(runner, project_dir)
        domain_dir = project_dir / "specs" / "domain"
        entities = [{"name": "Order", "context": "orders", "fields": []}]
        (domain_dir / "entities.yaml").write_text(yaml.dump(entities))

        _safe_chdir(project_dir)
        try:
            result = get_entities()
            assert "Order" in result["text"]
        finally:
            _safe_chdir(Path(__file__).parent)


# ---------------------------------------------------------------------------
# Consumer context deprecation tests
# ---------------------------------------------------------------------------


class TestConsumerContextDeprecation:
    def test_deprecated_excluded_from_consumer_context(self, runner, project_dir):
        """get_consumer_context excludes deprecated contracts and entities."""
        from evospec.mcp.server import get_consumer_context

        _init_project(runner, project_dir)
        domain_dir = project_dir / "specs" / "domain"

        contracts = {
            "contracts": [
                {"endpoint": "GET /api/v1/orders", "status": "deprecated",
                 "replacement": "GET /api/v2/orders", "description": "old orders",
                 "response": {200: {"fields": []}}, "tags": ["orders"]},
                {"endpoint": "GET /api/v2/orders", "description": "get orders",
                 "response": {200: {"fields": []}}, "tags": ["orders"]},
            ]
        }
        (domain_dir / "api-contracts.yaml").write_text(yaml.dump(contracts))

        entities = [
            {"name": "OrderV1", "context": "orders", "status": "deprecated",
             "replacement": "OrderV2"},
            {"name": "OrderV2", "context": "orders", "description": "current order entity"},
        ]
        (domain_dir / "entities.yaml").write_text(yaml.dump(entities))

        _safe_chdir(project_dir)
        try:
            result = get_consumer_context("get orders")
            # Should only contain v2
            endpoints = [c["endpoint"] for c in result["api_contracts"]]
            assert "GET /api/v2/orders" in endpoints
            assert "GET /api/v1/orders" not in endpoints
            # Should have deprecation warnings
            assert "deprecation_warnings" in result
            assert len(result["deprecation_warnings"]) >= 1
        finally:
            _safe_chdir(Path(__file__).parent)


# ---------------------------------------------------------------------------
# list_specs filtering tests
# ---------------------------------------------------------------------------


class TestListSpecsFiltering:
    def test_list_specs_status_filter(self, runner, project_dir):
        """list_specs can filter by status."""
        from evospec.mcp.server import list_specs

        _init_project(runner, project_dir)
        runner.invoke(cli, ["new", "feature-a", "--zone", "edge"])
        runner.invoke(cli, ["new", "feature-b", "--zone", "core"])

        # Mark feature-a as completed
        specs_dir = project_dir / "specs" / "changes"
        for d in specs_dir.iterdir():
            if "feature-a" in d.name:
                spec_yaml = d / "spec.yaml"
                spec = yaml.safe_load(spec_yaml.read_text())
                spec["status"] = "completed"
                spec_yaml.write_text(yaml.dump(spec))

        _safe_chdir(project_dir)
        try:
            result = list_specs(status="completed")
            assert result["count"] == 1
            assert result["specs"][0]["status"] == "completed"

            all_result = list_specs()
            assert all_result["count"] == 2
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_list_specs_includes_archived(self, runner, project_dir):
        """list_specs includes archived specs when include_archived=True."""
        from evospec.mcp.server import list_specs

        _init_project(runner, project_dir)
        runner.invoke(cli, ["new", "feature-a", "--zone", "edge"])

        # Manually archive it
        specs_dir = project_dir / "specs" / "changes"
        archive_dir = project_dir / "specs" / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        for d in specs_dir.iterdir():
            if "feature-a" in d.name:
                shutil.move(str(d), str(archive_dir / d.name))

        _safe_chdir(project_dir)
        try:
            # Without flag — should be empty
            result = list_specs()
            assert result["count"] == 0

            # With flag — should show archived
            result = list_specs(include_archived=True)
            assert result["count"] == 1
            assert result["specs"][0].get("archived") is True
        finally:
            _safe_chdir(Path(__file__).parent)


# ---------------------------------------------------------------------------
# Archive command tests
# ---------------------------------------------------------------------------


class TestArchiveCommand:
    def test_archive_completed_specs(self, runner, project_dir):
        """evospec archive moves completed specs to specs/archive/."""
        _init_project(runner, project_dir)
        runner.invoke(cli, ["new", "feat-done", "--zone", "edge"])
        runner.invoke(cli, ["new", "feat-wip", "--zone", "edge"])

        # Mark feat-done as completed
        specs_dir = project_dir / "specs" / "changes"
        for d in specs_dir.iterdir():
            if "feat-done" in d.name:
                spec_yaml = d / "spec.yaml"
                spec = yaml.safe_load(spec_yaml.read_text())
                spec["status"] = "completed"
                spec_yaml.write_text(yaml.dump(spec))

        _safe_chdir(project_dir)
        try:
            result = run_archive()
            assert result["count"] == 1
            assert (project_dir / "specs" / "archive").exists()
            # feat-done should be in archive
            archived = list((project_dir / "specs" / "archive").iterdir())
            assert len(archived) == 1
            assert "feat-done" in archived[0].name
            # feat-wip should still be in changes
            remaining = list(specs_dir.iterdir())
            assert any("feat-wip" in d.name for d in remaining)
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_archive_by_id(self, runner, project_dir):
        """evospec archive --id <id> archives a specific spec."""
        _init_project(runner, project_dir)
        runner.invoke(cli, ["new", "specific-feat", "--zone", "edge"])

        _safe_chdir(project_dir)
        try:
            result = run_archive(spec_id="specific-feat")
            assert result["count"] == 1
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_archive_dry_run(self, runner, project_dir):
        """--dry-run shows what would be archived without moving."""
        _init_project(runner, project_dir)
        runner.invoke(cli, ["new", "to-archive", "--zone", "edge"])

        # Mark as completed
        specs_dir = project_dir / "specs" / "changes"
        for d in specs_dir.iterdir():
            if "to-archive" in d.name:
                spec_yaml = d / "spec.yaml"
                spec = yaml.safe_load(spec_yaml.read_text())
                spec["status"] = "completed"
                spec_yaml.write_text(yaml.dump(spec))

        _safe_chdir(project_dir)
        try:
            result = run_archive(dry_run=True)
            assert result["count"] == 1
            # Should NOT have actually moved anything
            assert not (project_dir / "specs" / "archive").exists()
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_archive_status_filter(self, runner, project_dir):
        """evospec archive --status abandoned only archives abandoned specs."""
        _init_project(runner, project_dir)
        runner.invoke(cli, ["new", "completed-feat", "--zone", "edge"])
        runner.invoke(cli, ["new", "abandoned-feat", "--zone", "edge"])

        specs_dir = project_dir / "specs" / "changes"
        for d in specs_dir.iterdir():
            if "completed-feat" in d.name:
                spec_yaml = d / "spec.yaml"
                spec = yaml.safe_load(spec_yaml.read_text())
                spec["status"] = "completed"
                spec_yaml.write_text(yaml.dump(spec))
            elif "abandoned-feat" in d.name:
                spec_yaml = d / "spec.yaml"
                spec = yaml.safe_load(spec_yaml.read_text())
                spec["status"] = "abandoned"
                spec_yaml.write_text(yaml.dump(spec))

        _safe_chdir(project_dir)
        try:
            result = run_archive(status_filter="abandoned")
            assert result["count"] == 1
            # completed-feat should still be in changes
            remaining = list(specs_dir.iterdir())
            assert any("completed-feat" in d.name for d in remaining)
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_archive_nothing_to_archive(self, runner, project_dir):
        """Returns empty when no specs match criteria."""
        _init_project(runner, project_dir)
        runner.invoke(cli, ["new", "wip-feat", "--zone", "edge"])

        _safe_chdir(project_dir)
        try:
            result = run_archive()
            assert result["count"] == 0
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_archive_cli_command(self, runner, project_dir):
        """evospec archive CLI works."""
        _init_project(runner, project_dir)
        runner.invoke(cli, ["new", "done-feat", "--zone", "edge"])

        specs_dir = project_dir / "specs" / "changes"
        for d in specs_dir.iterdir():
            if "done-feat" in d.name:
                spec_yaml = d / "spec.yaml"
                spec = yaml.safe_load(spec_yaml.read_text())
                spec["status"] = "completed"
                spec_yaml.write_text(yaml.dump(spec))

        result = runner.invoke(cli, ["archive"])
        assert result.exit_code == 0
        assert "Archived" in result.output or "archived" in result.output.lower()
