"""Tests for evospec verify — spec accuracy verification."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from evospec.core.verify import (
    APIResult,
    ConsistencyResult,
    ContextResult,
    EntityResult,
    InvariantResult,
    VerificationReport,
    _calculate_level_score,
    _extract_keywords,
    _normalize_path,
    _scan_code_entities,
    _scan_code_endpoints,
    _verify_consistency,
    _verify_contexts,
    _verify_entities,
    _verify_invariants,
    run_verify,
)


@pytest.fixture
def project_dir():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def _create_evospec_project(
    root: Path,
    entities: list | None = None,
    contexts: list | None = None,
    api_contracts: dict | None = None,
) -> None:
    """Helper: create minimal evospec project."""
    config = {"project": {"name": "test-verify"}}
    (root / "evospec.yaml").write_text(yaml.dump(config))
    domain_dir = root / "specs" / "domain"
    domain_dir.mkdir(parents=True, exist_ok=True)
    changes_dir = root / "specs" / "changes"
    changes_dir.mkdir(parents=True, exist_ok=True)
    if entities:
        (domain_dir / "entities.yaml").write_text(yaml.dump(entities))
    if contexts:
        (domain_dir / "contexts.yaml").write_text(yaml.dump(contexts))
    if api_contracts:
        (domain_dir / "api-contracts.yaml").write_text(yaml.dump(api_contracts))


# ---------------------------------------------------------------------------
# Unit tests — helpers
# ---------------------------------------------------------------------------


class TestNormalizePath:
    def test_strips_method(self):
        assert _normalize_path("GET /api/orders") == "/api/orders"

    def test_normalizes_params(self):
        assert _normalize_path("/api/orders/{orderId}") == "/api/orders/{*}"

    def test_lowercases(self):
        assert _normalize_path("/Api/Orders") == "/api/orders"


class TestExtractKeywords:
    def test_filters_stop_words(self):
        kw = _extract_keywords("Every Order must have at least one Item")
        assert "order" in kw
        assert "item" in kw
        assert "must" not in kw
        assert "every" not in kw

    def test_short_words_filtered(self):
        kw = _extract_keywords("An id is required")
        assert "id" not in kw  # too short (2 chars)

    def test_empty_string(self):
        assert _extract_keywords("") == []


class TestCalculateLevelScore:
    def test_all_pass(self):
        results = [EntityResult("A", "match"), EntityResult("B", "match")]
        assert _calculate_level_score(results, "status", {"match"}) == 100.0

    def test_partial_pass(self):
        results = [EntityResult("A", "match"), EntityResult("B", "partial")]
        assert _calculate_level_score(results, "status", {"match"}) == 50.0

    def test_empty_results(self):
        assert _calculate_level_score([], "status", {"match"}) == 100.0

    def test_none_pass(self):
        results = [EntityResult("A", "missing"), EntityResult("B", "partial")]
        assert _calculate_level_score(results, "status", {"match"}) == 0.0


# ---------------------------------------------------------------------------
# Level 1: Entity verification
# ---------------------------------------------------------------------------


class TestScanCodeEntities:
    def test_python_sqlalchemy(self, project_dir):
        src = project_dir / "models.py"
        src.write_text(
            "class Order(Base):\n"
            "    id = Column(Integer)\n"
            "    status = Column(String)\n"
            "    total = Column(Decimal)\n"
        )
        entities = _scan_code_entities([src])
        assert "order" in entities
        assert "id" in entities["order"]
        assert "status" in entities["order"]
        assert "total" in entities["order"]

    def test_python_pydantic(self, project_dir):
        src = project_dir / "schemas.py"
        src.write_text(
            "class OrderSchema(BaseModel):\n"
            "    order_id: str\n"
            "    amount: float\n"
        )
        entities = _scan_code_entities([src])
        assert "orderschema" in entities
        assert "order_id" in entities["orderschema"]

    def test_java_entity(self, project_dir):
        src = project_dir / "Order.java"
        src.write_text(
            "@Entity\n"
            "public class Order {\n"
            "    private String id;\n"
            "    private String status;\n"
            "}\n"
        )
        entities = _scan_code_entities([src])
        assert "order" in entities
        assert "id" in entities["order"]
        assert "status" in entities["order"]

    def test_empty_file(self, project_dir):
        src = project_dir / "empty.py"
        src.write_text("")
        entities = _scan_code_entities([src])
        assert len(entities) == 0


class TestVerifyEntities:
    def test_all_match(self, project_dir):
        src = project_dir / "models.py"
        src.write_text(
            "class Order(Base):\n"
            "    id = Column(Integer)\n"
            "    status = Column(String)\n"
        )
        entities = [{"name": "Order", "fields": [{"name": "id"}, {"name": "status"}]}]
        results = _verify_entities(entities, [src])
        assert len(results) == 1
        assert results[0].status == "match"
        assert results[0].score == 100.0

    def test_missing_entity_in_code(self, project_dir):
        src = project_dir / "empty.py"
        src.write_text("")
        entities = [{"name": "Product", "fields": [{"name": "id"}]}]
        results = _verify_entities(entities, [src])
        assert results[0].status == "missing"
        assert results[0].score == 0.0

    def test_partial_match(self, project_dir):
        src = project_dir / "models.py"
        src.write_text(
            "class Order(Base):\n"
            "    id = Column(Integer)\n"
        )
        entities = [{"name": "Order", "fields": [{"name": "id"}, {"name": "status"}]}]
        results = _verify_entities(entities, [src])
        assert results[0].status == "partial"
        assert "status" in results[0].missing_fields


# ---------------------------------------------------------------------------
# Level 2: API verification
# ---------------------------------------------------------------------------


class TestScanCodeEndpoints:
    def test_python_fastapi(self, project_dir):
        src = project_dir / "routes.py"
        src.write_text(
            '@router.get("/api/orders")\n'
            'def list_orders(): pass\n'
            '@router.post("/api/orders")\n'
            'def create_order(): pass\n'
        )
        endpoints = _scan_code_endpoints([src])
        assert "/api/orders" in endpoints

    def test_express(self, project_dir):
        src = project_dir / "routes.js"
        src.write_text(
            'app.get("/api/products", handler)\n'
            'app.post("/api/products", createHandler)\n'
        )
        endpoints = _scan_code_endpoints([src])
        assert "/api/products" in endpoints


# ---------------------------------------------------------------------------
# Level 3: Invariant verification
# ---------------------------------------------------------------------------


class TestVerifyInvariants:
    def test_enforced_invariant(self, project_dir):
        src = project_dir / "validation.py"
        src.write_text(
            "# Enforcement for INV-001\n"
            "def validate_order(order):\n"
            "    if len(order.items) == 0:\n"
            "        raise ValueError('Order must have items')\n"
        )
        test_file = project_dir / "test_validation.py"
        test_file.write_text(
            "# Test for INV-001\n"
            "def test_order_must_have_items():\n"
            "    pass\n"
        )
        invariants = [{"id": "INV-001", "statement": "Every order must have items"}]
        results = _verify_invariants(invariants, [src], [test_file])
        assert results[0].status == "enforced"
        assert results[0].has_enforcement is True
        assert results[0].has_test is True

    def test_partial_invariant(self, project_dir):
        src = project_dir / "validation.py"
        src.write_text("# INV-002 check here\n")
        test_file = project_dir / "test_empty.py"
        test_file.write_text("# no tests\n")
        invariants = [{"id": "INV-002", "statement": "Max 100 items per order"}]
        results = _verify_invariants(invariants, [src], [test_file])
        assert results[0].status == "partial"
        assert results[0].has_enforcement is True
        assert results[0].has_test is False

    def test_unenforced_invariant(self, project_dir):
        src = project_dir / "empty.py"
        src.write_text("pass\n")
        test_file = project_dir / "empty_test.py"
        test_file.write_text("pass\n")
        invariants = [{"id": "INV-003", "statement": "Some obscure rule"}]
        results = _verify_invariants(invariants, [src], [test_file])
        assert results[0].status == "unenforced"


# ---------------------------------------------------------------------------
# Level 4: Context verification
# ---------------------------------------------------------------------------


class TestVerifyContexts:
    def test_matching_context(self, project_dir):
        (project_dir / "orders").mkdir()
        (project_dir / "orders" / "__init__.py").write_text("")
        contexts = [{"name": "orders"}]
        results = _verify_contexts(contexts, project_dir)
        assert len(results) == 1
        assert results[0].status == "match"

    def test_missing_context(self, project_dir):
        contexts = [{"name": "billing"}]
        results = _verify_contexts(contexts, project_dir)
        assert results[0].status == "mismatch"


# ---------------------------------------------------------------------------
# Level 5: Consistency verification
# ---------------------------------------------------------------------------


class TestVerifyConsistency:
    def test_consistent_entities(self, project_dir):
        _create_evospec_project(project_dir, entities=[
            {"name": "Order", "fields": [{"name": "id"}, {"name": "status"}]},
        ])
        from evospec.core.config import load_config
        config = load_config(project_dir)
        results = _verify_consistency(project_dir, config)
        # Single source — should be consistent
        for r in results:
            assert r.status == "consistent"


# ---------------------------------------------------------------------------
# VerificationReport
# ---------------------------------------------------------------------------


class TestVerificationReport:
    def test_to_dict(self):
        report = VerificationReport(
            entity_results=[EntityResult("Order", "match", score=100.0)],
            entity_score=100.0,
            api_score=75.0,
            invariant_score=80.0,
            context_score=100.0,
            consistency_score=100.0,
            overall_score=88.0,
        )
        d = report.to_dict()
        assert d["overall_score"] == 88.0
        assert d["entity_verification"]["score"] == 100.0
        assert len(d["entity_verification"]["results"]) == 1

    def test_to_markdown(self):
        report = VerificationReport(
            entity_results=[EntityResult("Order", "match")],
            entity_score=100.0,
            api_score=100.0,
            invariant_score=100.0,
            context_score=100.0,
            consistency_score=100.0,
            overall_score=100.0,
        )
        md = report.to_markdown()
        assert "# Verification Report" in md
        assert "Overall Score: 100.0%" in md
        assert "Order" in md

    def test_empty_report(self):
        d = VerificationReport().to_dict()
        assert d["overall_score"] == 0.0


# ---------------------------------------------------------------------------
# Integration test — run_verify
# ---------------------------------------------------------------------------


def _safe_chdir(path: Path):
    """chdir that works even when current CWD is deleted."""
    os.chdir(path)


class TestRunVerify:
    def test_run_verify_no_project(self, project_dir):
        """run_verify returns empty report when no evospec.yaml."""
        _safe_chdir(project_dir)
        try:
            report = run_verify(output_format="json")
            assert isinstance(report, VerificationReport)
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_run_verify_with_entities(self, project_dir):
        """run_verify checks entities against code."""
        _create_evospec_project(project_dir, entities=[
            {"name": "Order", "fields": [{"name": "id"}, {"name": "status"}]},
        ])
        src_dir = project_dir / "src"
        src_dir.mkdir()
        (src_dir / "models.py").write_text(
            "class Order(Base):\n"
            "    id = Column(Integer)\n"
            "    status = Column(String)\n"
        )

        _safe_chdir(project_dir)
        try:
            report = run_verify(output_format="json")
            assert report.entity_score > 0
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_run_verify_json_format(self, project_dir):
        """--format json works."""
        _create_evospec_project(project_dir)
        _safe_chdir(project_dir)
        try:
            report = run_verify(output_format="json")
            d = report.to_dict()
            assert "overall_score" in d
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_run_verify_markdown_format(self, project_dir):
        """--format markdown works."""
        _create_evospec_project(project_dir)
        _safe_chdir(project_dir)
        try:
            report = run_verify(output_format="markdown")
            md = report.to_markdown()
            assert "Verification Report" in md
        finally:
            _safe_chdir(Path(__file__).parent)

    def test_run_verify_strict_mode_passes(self, project_dir):
        """--strict passes when no thresholds configured."""
        _create_evospec_project(project_dir)
        _safe_chdir(project_dir)
        try:
            # No verification thresholds → strict should pass
            report = run_verify(strict=True, output_format="json")
            assert isinstance(report, VerificationReport)
        finally:
            _safe_chdir(Path(__file__).parent)
