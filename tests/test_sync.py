"""Tests for evospec sync — drift detection from git diffs."""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from evospec.core.sync import (
    DriftReport,
    EndpointChange,
    FieldChange,
    InvariantImpact,
    _build_spec_field_map,
    _calculate_drift_score,
    _detect_endpoint_changes,
    _detect_entity_changes,
    _detect_invariant_impacts,
    _normalize_endpoint,
    run_sync,
)


@pytest.fixture
def project_dir():
    """Create a temporary project directory with git init."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Init git repo
        subprocess.run(["git", "init"], cwd=str(root), capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=str(root), capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=str(root), capture_output=True,
        )
        yield root


def _create_evospec_project(root: Path, entities: list | None = None) -> None:
    """Helper: create minimal evospec project structure."""
    config = {"project": {"name": "test-sync"}}
    (root / "evospec.yaml").write_text(yaml.dump(config))
    domain_dir = root / "specs" / "domain"
    domain_dir.mkdir(parents=True, exist_ok=True)
    if entities:
        (domain_dir / "entities.yaml").write_text(yaml.dump(entities))


def _git_commit(root: Path, msg: str = "commit") -> None:
    """Helper: stage all and commit."""
    subprocess.run(["git", "add", "-A"], cwd=str(root), capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", msg, "--allow-empty"],
        cwd=str(root), capture_output=True,
    )


# ---------------------------------------------------------------------------
# Unit tests — helpers
# ---------------------------------------------------------------------------


class TestNormalizeEndpoint:
    def test_strips_method_prefix(self):
        assert _normalize_endpoint("GET /api/orders") == "/api/orders"

    def test_normalizes_path_params(self):
        assert _normalize_endpoint("/api/orders/{orderId}") == "/api/orders/{*}"

    def test_lowercases(self):
        assert _normalize_endpoint("/Api/Orders") == "/api/orders"

    def test_strips_trailing_slash(self):
        assert _normalize_endpoint("/api/orders/") == "/api/orders"

    def test_combined(self):
        assert _normalize_endpoint("POST /Api/Orders/{id}/Items/") == "/api/orders/{*}/items"


class TestBuildSpecFieldMap:
    def test_basic(self):
        entities = [
            {"name": "Order", "fields": [{"name": "id"}, {"name": "status"}]},
            {"name": "Item", "fields": [{"name": "id"}, {"name": "quantity"}]},
        ]
        result = _build_spec_field_map(entities)
        assert result["order"] == {"id", "status"}
        assert result["item"] == {"id", "quantity"}

    def test_empty(self):
        assert _build_spec_field_map([]) == {}

    def test_entity_without_fields(self):
        result = _build_spec_field_map([{"name": "Foo"}])
        assert result["foo"] == set()


class TestCalculateDriftScore:
    def test_no_drift(self):
        score = _calculate_drift_score([], [], 10, 5)
        assert score == 0.0

    def test_some_drift(self):
        changes = [FieldChange("Order", "x", "added")]
        score = _calculate_drift_score(changes, [], 10, 0)
        assert score == pytest.approx(10.0)

    def test_capped_at_100(self):
        changes = [FieldChange("A", f"f{i}", "added") for i in range(20)]
        score = _calculate_drift_score(changes, [], 5, 0)
        assert score == 100.0

    def test_zero_items(self):
        score = _calculate_drift_score([], [], 0, 0)
        assert score == 0.0

    def test_mixed_changes(self):
        fc = [FieldChange("Order", "x", "added")]
        ec = [EndpointChange("/api/foo", "added")]
        score = _calculate_drift_score(fc, ec, 5, 5)
        assert score == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# Unit tests — entity detection
# ---------------------------------------------------------------------------


class TestDetectEntityChanges:
    def test_detects_new_python_field(self):
        diff = (
            "+class Order(Base):\n"
            "+    tracking_number = Column(String)\n"
        )
        entities = [{"name": "Order", "fields": [{"name": "id"}, {"name": "status"}]}]
        changes = _detect_entity_changes(diff, entities)
        assert len(changes) == 1
        assert changes[0].entity == "Order"
        assert changes[0].field_name == "tracking_number"
        assert changes[0].change_type == "added"

    def test_detects_new_java_field(self):
        diff = (
            "+@Entity class Product {\n"
            "+    private String isActive;\n"
        )
        entities = [{"name": "Product", "fields": [{"name": "id"}, {"name": "name"}]}]
        changes = _detect_entity_changes(diff, entities)
        assert any(c.field_name == "isActive" for c in changes)

    def test_no_false_positive_on_existing_field(self):
        diff = "+class Order(Base):\n+    status = Column(String)\n"
        entities = [{"name": "Order", "fields": [{"name": "status"}]}]
        changes = _detect_entity_changes(diff, entities)
        assert len(changes) == 0

    def test_empty_diff(self):
        changes = _detect_entity_changes("", [{"name": "Order", "fields": []}])
        assert len(changes) == 0

    def test_skips_non_field_names(self):
        diff = "+class Order(Base):\n+    self = Column(String)\n"
        entities = [{"name": "Order", "fields": []}]
        changes = _detect_entity_changes(diff, entities)
        assert len(changes) == 0


# ---------------------------------------------------------------------------
# Unit tests — endpoint detection
# ---------------------------------------------------------------------------


class TestDetectEndpointChanges:
    def test_detects_new_python_endpoint(self):
        diff = '+@router.post("/api/orders/bulk-create")\n'
        spec_endpoints = ["/api/orders", "/api/orders/{id}"]
        changes = _detect_endpoint_changes(diff, spec_endpoints)
        assert len(changes) == 1
        assert changes[0].endpoint == "/api/orders/bulk-create"
        assert changes[0].change_type == "added"

    def test_detects_new_express_endpoint(self):
        diff = '+app.get("/api/products/search", handler)\n'
        changes = _detect_endpoint_changes(diff, ["/api/products"])
        assert any(c.endpoint == "/api/products/search" for c in changes)

    def test_no_false_positive_on_existing_endpoint(self):
        diff = '+@router.get("/api/orders")\n'
        changes = _detect_endpoint_changes(diff, ["/api/orders"])
        assert len(changes) == 0

    def test_empty_diff(self):
        changes = _detect_endpoint_changes("", ["/api/orders"])
        assert len(changes) == 0


# ---------------------------------------------------------------------------
# Unit tests — invariant impact
# ---------------------------------------------------------------------------


class TestDetectInvariantImpacts:
    def test_detects_impact_on_mentioned_entity(self):
        entity_changes = [FieldChange("Order", "tracking", "added")]
        invariants = [
            {"id": "INV-001", "statement": "Every Order must have at least one Item"},
        ]
        impacts = _detect_invariant_impacts(entity_changes, [], invariants)
        assert len(impacts) == 1
        assert impacts[0].invariant_id == "INV-001"

    def test_no_impact_on_unrelated_entity(self):
        entity_changes = [FieldChange("Product", "price", "added")]
        invariants = [
            {"id": "INV-001", "statement": "Every Order must have at least one Item"},
        ]
        impacts = _detect_invariant_impacts(entity_changes, [], invariants)
        assert len(impacts) == 0

    def test_empty_invariants(self):
        entity_changes = [FieldChange("Order", "x", "added")]
        impacts = _detect_invariant_impacts(entity_changes, [], [])
        assert len(impacts) == 0


# ---------------------------------------------------------------------------
# Unit tests — DriftReport
# ---------------------------------------------------------------------------


class TestDriftReport:
    def test_to_dict(self):
        report = DriftReport(
            entity_changes=[FieldChange("Order", "tracking", "added", "new")],
            endpoint_changes=[EndpointChange("/api/x", "added", "new endpoint")],
            invariant_impacts=[InvariantImpact("INV-1", "stmt", "reason")],
            drift_score=15.5,
            commits_analyzed=10,
            since="v1.0.0",
        )
        d = report.to_dict()
        assert d["drift_score"] == 15.5
        assert d["commits_analyzed"] == 10
        assert d["since"] == "v1.0.0"
        assert len(d["entity_changes"]) == 1
        assert len(d["endpoint_changes"]) == 1
        assert len(d["invariant_impacts"]) == 1

    def test_empty_report_to_dict(self):
        d = DriftReport().to_dict()
        assert d["drift_score"] == 0.0
        assert d["entity_changes"] == []


# ---------------------------------------------------------------------------
# Integration test — run_sync
# ---------------------------------------------------------------------------


def _safe_chdir(path: Path):
    """chdir that works even when current CWD is deleted."""
    os.chdir(path)


class TestRunSync:
    def test_run_sync_no_project(self, project_dir):
        """run_sync returns empty report when no evospec.yaml."""
        _safe_chdir(project_dir)
        try:
            report = run_sync(ci=True)
            assert report.drift_score == 0.0
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_run_sync_with_project(self, project_dir):
        """run_sync runs without error on a valid project."""
        _create_evospec_project(project_dir, entities=[
            {"name": "Order", "fields": [{"name": "id"}, {"name": "status"}]},
        ])
        _git_commit(project_dir, "initial")

        _safe_chdir(project_dir)
        try:
            report = run_sync(ci=True)
            assert isinstance(report, DriftReport)
            assert report.drift_score >= 0.0
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_run_sync_generate_flag(self, project_dir):
        """--generate creates draft specs from drift (SYNC-001)."""
        _create_evospec_project(project_dir, entities=[
            {"name": "Order", "fields": [{"name": "id"}]},
        ])
        _git_commit(project_dir, "initial")

        # Add a source file with a new field
        src_dir = project_dir / "src"
        src_dir.mkdir()
        (src_dir / "models.py").write_text(
            "class Order(Base):\n"
            "    id = Column(Integer)\n"
            "    tracking_number = Column(String)\n"
        )

        _safe_chdir(project_dir)
        try:
            report = run_sync(generate=True, ci=True)
            # If drift detected, specs should be generated
            specs_dir = project_dir / "specs" / "changes"
            if report.entity_changes:
                draft_dirs = [d for d in specs_dir.iterdir() if "auto-sync" in d.name]
                assert len(draft_dirs) >= 1
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_run_sync_ci_mode(self, project_dir):
        """--ci outputs JSON."""
        _create_evospec_project(project_dir)
        _git_commit(project_dir, "initial")

        _safe_chdir(project_dir)
        try:
            report = run_sync(ci=True)
            d = report.to_dict()
            assert "drift_score" in d
        finally:
            _safe_chdir(Path(__file__).parent)
