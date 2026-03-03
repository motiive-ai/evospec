"""Tests for evospec capture --from-history — retroactive spec generation."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

from evospec.core.capture import (
    CaptureReport,
    CommitInfo,
    FeatureCluster,
    _build_cochange_graph,
    _clean_label,
    _extract_entities_from_clusters,
    _extract_modules,
    _form_clusters,
    _generate_cluster_label,
    _is_source_file,
    _label_propagation,
    _parse_git_log,
    _update_entities_yaml,
    _update_features_yaml,
    run_capture_from_history,
)


@pytest.fixture
def project_dir():
    """Create a temporary project directory with git init."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
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


def _create_evospec_project(root: Path) -> None:
    config = {"project": {"name": "test-capture"}}
    (root / "evospec.yaml").write_text(yaml.dump(config))
    (root / "specs" / "domain").mkdir(parents=True, exist_ok=True)
    (root / "specs" / "changes").mkdir(parents=True, exist_ok=True)


def _git_commit(root: Path, msg: str = "commit") -> None:
    subprocess.run(["git", "add", "-A"], cwd=str(root), capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", msg, "--allow-empty"],
        cwd=str(root), capture_output=True,
    )


def _safe_chdir(path: Path):
    os.chdir(path)


# ---------------------------------------------------------------------------
# Unit tests — helpers
# ---------------------------------------------------------------------------


class TestIsSourceFile:
    def test_python_file(self):
        assert _is_source_file("src/models.py") is True

    def test_java_file(self):
        assert _is_source_file("com/example/Order.java") is True

    def test_go_file(self):
        assert _is_source_file("pkg/order/order.go") is True

    def test_ts_file(self):
        assert _is_source_file("src/order.ts") is True

    def test_config_file(self):
        assert _is_source_file("config.yaml") is False

    def test_doc_file(self):
        assert _is_source_file("README.md") is False

    def test_test_file(self):
        assert _is_source_file("tests/test_order.py") is False

    def test_vendor_file(self):
        assert _is_source_file("vendor/lib.go") is False

    def test_node_modules(self):
        assert _is_source_file("node_modules/pkg/index.js") is False


class TestCleanLabel:
    def test_simple(self):
        assert _clean_label("orders") == "orders"

    def test_spaces(self):
        assert _clean_label("order management") == "order-management"

    def test_special_chars(self):
        assert _clean_label("order@system!") == "order-system"

    def test_empty(self):
        assert _clean_label("") == "feature"


class TestExtractModules:
    def test_python_modules(self):
        files = ["src/evospec/core/config.py", "src/evospec/cli/main.py"]
        result = _extract_modules(files)
        assert "evospec.core.config" in result
        assert "evospec.cli.main" in result

    def test_non_python(self):
        files = ["Order.java", "order.go"]
        result = _extract_modules(files)
        assert result == []

    def test_init_excluded(self):
        files = ["src/pkg/__init__.py"]
        result = _extract_modules(files)
        assert result == []


# ---------------------------------------------------------------------------
# Unit tests — co-change graph
# ---------------------------------------------------------------------------


class TestBuildCochangeGraph:
    def test_basic(self):
        commits = [
            CommitInfo("a1", "feat: add order", ["order.py", "item.py"]),
            CommitInfo("a2", "fix: order bug", ["order.py", "db.py"]),
        ]
        graph = _build_cochange_graph(commits)
        assert "order.py" in graph
        assert "item.py" in graph["order.py"]
        assert graph["order.py"]["item.py"] == 1
        assert "db.py" in graph["order.py"]

    def test_weight_increments(self):
        commits = [
            CommitInfo("a1", "msg1", ["a.py", "b.py"]),
            CommitInfo("a2", "msg2", ["a.py", "b.py"]),
        ]
        graph = _build_cochange_graph(commits)
        assert graph["a.py"]["b.py"] == 2

    def test_isolated_file(self):
        commits = [
            CommitInfo("a1", "msg", ["only.py"]),
        ]
        graph = _build_cochange_graph(commits)
        assert "only.py" in graph

    def test_empty_commits(self):
        graph = _build_cochange_graph([])
        assert graph == {}


# ---------------------------------------------------------------------------
# Unit tests — label propagation
# ---------------------------------------------------------------------------


class TestLabelPropagation:
    def test_two_clusters(self):
        # Two disconnected groups: {a,b} and {c,d}
        graph = {
            "a": {"b": 5},
            "b": {"a": 5},
            "c": {"d": 5},
            "d": {"c": 5},
        }
        labels = _label_propagation(graph)
        assert labels["a"] == labels["b"]
        assert labels["c"] == labels["d"]
        assert labels["a"] != labels["c"]

    def test_single_cluster(self):
        graph = {
            "a": {"b": 3, "c": 3},
            "b": {"a": 3, "c": 3},
            "c": {"a": 3, "b": 3},
        }
        labels = _label_propagation(graph)
        assert labels["a"] == labels["b"] == labels["c"]

    def test_empty_graph(self):
        labels = _label_propagation({})
        assert labels == {}

    def test_isolated_nodes(self):
        graph = {"a": {}, "b": {}}
        labels = _label_propagation(graph)
        # Each keeps its own label
        assert labels["a"] != labels["b"]


# ---------------------------------------------------------------------------
# Unit tests — cluster formation
# ---------------------------------------------------------------------------


class TestFormClusters:
    def test_basic_clustering(self):
        labels = {"a.py": 0, "b.py": 0, "c.py": 1, "d.py": 1}
        commits = [
            CommitInfo("s1", "feat(orders): add order", ["a.py", "b.py"]),
            CommitInfo("s2", "feat(items): add items", ["c.py", "d.py"]),
        ]
        clusters = _form_clusters(labels, commits, min_cluster_size=2)
        assert len(clusters) == 2

    def test_min_cluster_size_filters(self):
        labels = {"a.py": 0, "b.py": 0, "c.py": 1}
        commits = [CommitInfo("s1", "msg", ["a.py", "b.py", "c.py"])]
        clusters = _form_clusters(labels, commits, min_cluster_size=2)
        assert len(clusters) == 1  # Only the cluster with 2+ files

    def test_empty_labels(self):
        clusters = _form_clusters({}, [], min_cluster_size=2)
        assert clusters == []


# ---------------------------------------------------------------------------
# Unit tests — cluster labeling
# ---------------------------------------------------------------------------


class TestGenerateClusterLabel:
    def test_from_conventional_commit_scope(self):
        files = ["src/orders/model.py"]
        messages = ["feat(orders): add order model", "fix(orders): fix validation"]
        label = _generate_cluster_label(files, messages)
        assert label == "orders"

    def test_from_directory_structure(self):
        files = ["src/billing/invoice.py", "src/billing/payment.py"]
        messages = ["update invoice", "add payment"]
        label = _generate_cluster_label(files, messages)
        assert label == "billing"

    def test_fallback_to_topic(self):
        files = ["main.py"]
        messages = ["feat: implement authentication flow"]
        label = _generate_cluster_label(files, messages)
        assert len(label) > 0

    def test_empty(self):
        label = _generate_cluster_label([], [])
        assert label == "unknown"


# ---------------------------------------------------------------------------
# Unit tests — entity extraction
# ---------------------------------------------------------------------------


class TestExtractEntitiesFromClusters:
    def test_python_class(self, project_dir):
        src = project_dir / "src" / "models.py"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text("class Order(Base):\n    pass\n")
        cluster = FeatureCluster(
            id=0, label="orders", files=["src/models.py"],
            commits=[], messages=[],
        )
        entities = _extract_entities_from_clusters([cluster], project_dir)
        assert any(e["name"] == "Order" for e in entities)

    def test_filters_test_classes(self, project_dir):
        src = project_dir / "src" / "models.py"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text("class TestOrder:\n    pass\nclass Config:\n    pass\n")
        cluster = FeatureCluster(
            id=0, label="test", files=["src/models.py"],
            commits=[], messages=[],
        )
        entities = _extract_entities_from_clusters([cluster], project_dir)
        assert not any(e["name"] == "TestOrder" for e in entities)
        assert not any(e["name"] == "Config" for e in entities)


# ---------------------------------------------------------------------------
# Unit tests — domain file updates
# ---------------------------------------------------------------------------


class TestUpdateEntitiesYaml:
    def test_creates_new_file(self, project_dir):
        _create_evospec_project(project_dir)
        from evospec.core.config import load_config
        config = load_config(project_dir)
        new_entities = [{"name": "Order", "context": "orders", "fields": []}]
        path = _update_entities_yaml(new_entities, project_dir, config)
        assert path is not None
        assert path.exists()
        data = yaml.safe_load(path.read_text())
        assert any(e["name"] == "Order" for e in data)

    def test_no_duplicates(self, project_dir):
        _create_evospec_project(project_dir)
        entities_path = project_dir / "specs" / "domain" / "entities.yaml"
        entities_path.write_text(yaml.dump([{"name": "Order", "fields": []}]))
        from evospec.core.config import load_config
        config = load_config(project_dir)
        new_entities = [{"name": "Order", "context": "orders", "fields": []}]
        path = _update_entities_yaml(new_entities, project_dir, config)
        assert path is None  # No changes needed


class TestUpdateFeaturesYaml:
    def test_creates_features(self, project_dir):
        _create_evospec_project(project_dir)
        from evospec.core.config import load_config
        config = load_config(project_dir)
        clusters = [FeatureCluster(
            id=0, label="orders", files=["a.py", "b.py"],
            commits=["s1"], messages=["feat: orders"],
        )]
        path = _update_features_yaml(clusters, project_dir, config)
        assert path is not None
        data = yaml.safe_load(path.read_text())
        assert len(data) == 1
        assert data[0]["title"].startswith("Retroactive:")


# ---------------------------------------------------------------------------
# Unit tests — data classes
# ---------------------------------------------------------------------------


class TestCaptureReport:
    def test_to_dict(self):
        cluster = FeatureCluster(
            id=0, label="orders", files=["a.py", "b.py"],
            commits=["sha1"], messages=["msg1"],
        )
        report = CaptureReport(
            commits_analyzed=10,
            files_analyzed=20,
            clusters=[cluster],
            specs_generated=["specs/changes/retroactive-orders/spec.yaml"],
            entities_found=["Order"],
            since="v1.0",
        )
        d = report.to_dict()
        assert d["commits_analyzed"] == 10
        assert d["files_analyzed"] == 20
        assert len(d["clusters"]) == 1
        assert d["clusters"][0]["label"] == "orders"
        assert d["since"] == "v1.0"

    def test_empty_report(self):
        d = CaptureReport().to_dict()
        assert d["commits_analyzed"] == 0
        assert d["clusters"] == []


class TestFeatureCluster:
    def test_post_init(self):
        cluster = FeatureCluster(
            id=0, label="test", files=["src/orders/model.py", "src/orders/api.py"],
            commits=[], messages=[],
        )
        assert cluster.size == 2
        assert cluster.dominant_dir == "src/orders"


# ---------------------------------------------------------------------------
# Integration test — run_capture_from_history
# ---------------------------------------------------------------------------


class TestRunCaptureFromHistory:
    def test_no_project(self, project_dir):
        """Returns empty report when no evospec.yaml."""
        _safe_chdir(project_dir)
        try:
            report = run_capture_from_history()
            assert report.commits_analyzed == 0
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_with_commits(self, project_dir):
        """Analyzes git history and produces clusters."""
        _create_evospec_project(project_dir)
        _git_commit(project_dir, "initial")

        # Create source files in two different features
        orders_dir = project_dir / "src" / "orders"
        orders_dir.mkdir(parents=True)
        (orders_dir / "model.py").write_text("class Order(Base):\n    pass\n")
        (orders_dir / "api.py").write_text("class OrderAPI:\n    pass\n")
        _git_commit(project_dir, "feat(orders): add order module")

        billing_dir = project_dir / "src" / "billing"
        billing_dir.mkdir(parents=True)
        (billing_dir / "invoice.py").write_text("class Invoice(Base):\n    pass\n")
        (billing_dir / "payment.py").write_text("class Payment(Base):\n    pass\n")
        _git_commit(project_dir, "feat(billing): add billing module")

        _safe_chdir(project_dir)
        try:
            report = run_capture_from_history(min_cluster_size=1)
            assert isinstance(report, CaptureReport)
            assert report.commits_analyzed >= 2
            assert report.files_analyzed >= 4
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_empty_history(self, project_dir):
        """Handles repos with no meaningful source commits."""
        _create_evospec_project(project_dir)
        _git_commit(project_dir, "initial: config only")

        _safe_chdir(project_dir)
        try:
            report = run_capture_from_history()
            assert report.commits_analyzed == 0
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_max_clusters_cap(self, project_dir):
        """Respects --max-clusters."""
        _create_evospec_project(project_dir)
        _git_commit(project_dir, "initial")

        # Create many files
        src_dir = project_dir / "src"
        for i in range(10):
            d = src_dir / f"mod{i}"
            d.mkdir(parents=True, exist_ok=True)
            (d / f"file{i}.py").write_text(f"class Mod{i}:\n    pass\n")
            _git_commit(project_dir, f"feat(mod{i}): add module {i}")

        _safe_chdir(project_dir)
        try:
            report = run_capture_from_history(max_clusters=3, min_cluster_size=1)
            assert len(report.clusters) <= 3
        finally:
            _safe_chdir(Path(__file__).parent)
