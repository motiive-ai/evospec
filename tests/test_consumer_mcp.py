"""Tests for consumer-facing MCP: API contracts, file schemas, check validation."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from evospec.cli.main import cli
from evospec.core.check import _check_api_contracts


SAMPLE_CONTRACTS = {
    "contracts": [
        {
            "endpoint": "GET /api/orders/{orderId}",
            "description": "Get order details",
            "params": [
                {"name": "orderId", "in": "path", "type": "String", "required": True},
            ],
            "response": {
                200: {
                    "fields": [
                        {"name": "orderId", "type": "String"},
                        {"name": "status", "type": "OrderStatus"},
                        {"name": "items", "type": "List<LineItem>"},
                    ],
                },
            },
            "auth": "bearer token",
            "tags": ["orders", "read"],
        },
        {
            "endpoint": "POST /api/orders",
            "description": "Create a new order",
            "request": {
                "content_type": "application/json",
                "fields": [
                    {"name": "customerId", "type": "String", "required": True},
                ],
            },
            "response": {
                201: {
                    "fields": [
                        {"name": "orderId", "type": "String"},
                        {"name": "status", "type": "OrderStatus"},
                    ],
                },
            },
            "auth": "bearer token",
            "tags": ["orders", "write"],
        },
    ]
}

SAMPLE_FILE_SCHEMAS = {
    "schemas": [
        {
            "name": "OrderExport",
            "format": "json",
            "description": "JSON export of order data",
            "version": "v1",
            "structure": [
                {"name": "orderId", "type": "String"},
                {"name": "items", "type": "List<LineItem>"},
            ],
        },
    ]
}


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


# ---------------------------------------------------------------------------
# Config loading tests
# ---------------------------------------------------------------------------

class TestConfigLoading:
    def test_api_contracts_loaded(self, runner, project_dir):
        """api-contracts.yaml loaded into config as api_contracts."""
        from evospec.core.config import load_config

        _init_project(runner, project_dir)
        domain_dir = project_dir / "specs" / "domain"
        (domain_dir / "api-contracts.yaml").write_text(yaml.dump(SAMPLE_CONTRACTS))

        config = load_config(project_dir)
        assert "api_contracts" in config
        contracts = config["api_contracts"]
        assert isinstance(contracts, dict)
        assert len(contracts["contracts"]) == 2

    def test_file_schemas_loaded(self, runner, project_dir):
        """file-schemas.yaml loaded into config as file_schemas."""
        from evospec.core.config import load_config

        _init_project(runner, project_dir)
        domain_dir = project_dir / "specs" / "domain"
        (domain_dir / "file-schemas.yaml").write_text(yaml.dump(SAMPLE_FILE_SCHEMAS))

        config = load_config(project_dir)
        assert "file_schemas" in config
        schemas = config["file_schemas"]
        assert isinstance(schemas, dict)
        assert len(schemas["schemas"]) == 1

    def test_init_creates_stubs(self, runner, project_dir):
        """evospec init creates api-contracts.yaml and file-schemas.yaml stubs."""
        _init_project(runner, project_dir)
        domain_dir = project_dir / "specs" / "domain"
        assert (domain_dir / "api-contracts.yaml").exists()
        assert (domain_dir / "file-schemas.yaml").exists()

        # Stubs should have empty contracts/schemas
        contracts = yaml.safe_load((domain_dir / "api-contracts.yaml").read_text())
        assert contracts["contracts"] == []

        schemas = yaml.safe_load((domain_dir / "file-schemas.yaml").read_text())
        assert schemas["schemas"] == []


# ---------------------------------------------------------------------------
# Check validation tests (CONSUMER-MCP-001, 002, 003)
# ---------------------------------------------------------------------------

class TestCheckApiContracts:
    def test_valid_contracts(self):
        """Valid contracts pass validation (CONSUMER-MCP-001)."""
        config = {"api_contracts": SAMPLE_CONTRACTS}
        errors, warnings = _check_api_contracts(config)
        assert errors == 0

    def test_contract_missing_endpoint(self):
        """Contract without endpoint is an error."""
        config = {"api_contracts": {"contracts": [
            {"description": "test", "response": {200: {"fields": []}}},
        ]}}
        errors, warnings = _check_api_contracts(config)
        assert errors >= 1

    def test_contract_missing_response_warns(self):
        """Contract without response is a warning."""
        config = {"api_contracts": {"contracts": [
            {"endpoint": "GET /test", "description": "test"},
        ]}}
        errors, warnings = _check_api_contracts(config)
        assert warnings >= 1

    def test_valid_file_schemas(self):
        """Valid file schemas pass validation (CONSUMER-MCP-002)."""
        config = {"file_schemas": SAMPLE_FILE_SCHEMAS}
        errors, warnings = _check_api_contracts(config)
        assert errors == 0
        assert warnings == 0

    def test_file_schema_missing_name(self):
        """File schema without name is an error."""
        config = {"file_schemas": {"schemas": [
            {"format": "json", "structure": [{"name": "id", "type": "String"}]},
        ]}}
        errors, warnings = _check_api_contracts(config)
        assert errors >= 1

    def test_file_schema_missing_format_warns(self):
        """File schema without format is a warning."""
        config = {"file_schemas": {"schemas": [
            {"name": "Test", "structure": [{"name": "id", "type": "String"}]},
        ]}}
        errors, warnings = _check_api_contracts(config)
        assert warnings >= 1

    def test_entity_cross_reference(self):
        """Entity types in contracts checked against entities.yaml (CONSUMER-MCP-003)."""
        config = {
            "api_contracts": {"contracts": [
                {
                    "endpoint": "GET /test",
                    "response": {200: {"fields": [
                        {"name": "status", "type": "OrderStatus"},
                    ]}},
                },
            ]},
            "domain": {"entities": [
                {"name": "Order"},
                {"name": "OrderStatus"},
            ]},
        }
        errors, warnings = _check_api_contracts(config)
        # OrderStatus exists in entities → no warning
        assert warnings == 0

    def test_entity_cross_reference_unknown(self):
        """Unknown entity types in contracts warn (CONSUMER-MCP-003)."""
        config = {
            "api_contracts": {"contracts": [
                {
                    "endpoint": "GET /test",
                    "response": {200: {"fields": [
                        {"name": "status", "type": "UnknownType"},
                    ]}},
                },
            ]},
            "domain": {"entities": [
                {"name": "Order"},
            ]},
        }
        errors, warnings = _check_api_contracts(config)
        assert warnings >= 1

    def test_primitive_types_not_warned(self):
        """Primitive types (String, Int, etc.) not warned as missing entities."""
        config = {
            "api_contracts": {"contracts": [
                {
                    "endpoint": "GET /test",
                    "response": {200: {"fields": [
                        {"name": "id", "type": "String"},
                        {"name": "count", "type": "Int"},
                        {"name": "amount", "type": "Decimal"},
                        {"name": "active", "type": "Boolean"},
                    ]}},
                },
            ]},
            "domain": {"entities": [{"name": "Order"}]},
        }
        errors, warnings = _check_api_contracts(config)
        assert warnings == 0

    def test_empty_contracts_no_output(self):
        """Empty contracts produce no errors or warnings."""
        config = {"api_contracts": {"contracts": []}}
        errors, warnings = _check_api_contracts(config)
        assert errors == 0
        assert warnings == 0
