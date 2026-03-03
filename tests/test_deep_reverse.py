"""Tests for deep reverse engineering (--deep flag).

Tests cover:
- Deep API extraction: class indexing, auth detection, request/response type detection
- Deep DB extraction: invariant suggestion, state machine detection, enum value finding
- Deep deps extraction: message queue scanning, storage op scanning
- CLI flag wiring: --deep and --write flags accepted
- Backward compatibility: shallow reverse unchanged when --deep not passed
"""

import re
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from evospec.cli.main import cli


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal evospec project with source files for testing."""
    # evospec.yaml
    (tmp_path / "evospec.yaml").write_text(textwrap.dedent("""\
        project:
          name: test-project
        reverse:
          framework: fastapi
          source_dirs:
            - src
    """))

    # specs dir
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "domain").mkdir(parents=True)
    (specs / "changes").mkdir()

    # Source dir
    src = tmp_path / "src"
    src.mkdir()

    import os
    old_cwd = None
    try:
        old_cwd = os.getcwd()
    except (FileNotFoundError, OSError):
        pass
    os.chdir(tmp_path)
    yield tmp_path
    if old_cwd and Path(old_cwd).exists():
        os.chdir(old_cwd)


# ---------------------------------------------------------------------------
# Deep API extraction tests
# ---------------------------------------------------------------------------

class TestDeepApiExtraction:
    """Test _deep_extract_api and helper functions."""

    def test_index_python_pydantic_class(self, tmp_path):
        """Index Pydantic BaseModel classes into field maps."""
        from evospec.reverse.api import _index_python_classes

        content = textwrap.dedent("""\
            from pydantic import BaseModel, Field

            class CreateOrderRequest(BaseModel):
                customer_id: str
                amount: float = Field(ge=0, le=10000)
                notes: str | None = None
        """)
        index: dict = {}
        _index_python_classes(content, index)

        assert "CreateOrderRequest" in index
        fields = index["CreateOrderRequest"]
        assert len(fields) == 3

        # customer_id: required str
        cid = next(f for f in fields if f["name"] == "customer_id")
        assert cid["type"] == "str"
        assert cid["required"] is True

        # amount: with constraints
        amt = next(f for f in fields if f["name"] == "amount")
        assert "ge=0" in amt.get("constraints", "")
        assert "le=10000" in amt.get("constraints", "")

        # notes: optional
        notes = next(f for f in fields if f["name"] == "notes")
        assert notes["required"] is False

    def test_index_ts_interface(self):
        """Index TypeScript interfaces into field maps."""
        from evospec.reverse.api import _index_ts_classes

        content = textwrap.dedent("""\
            export interface CreateOrderDTO {
                customerId: string;
                amount: number;
                notes?: string;
            }
        """)
        index: dict = {}
        _index_ts_classes(content, index)

        assert "CreateOrderDTO" in index
        fields = index["CreateOrderDTO"]
        assert len(fields) == 3

        cid = next(f for f in fields if f["name"] == "customerId")
        assert cid["required"] is True

        notes = next(f for f in fields if f["name"] == "notes")
        assert notes["required"] is False

    def test_index_go_struct(self):
        """Index Go structs with struct tags into field maps."""
        from evospec.reverse.api import _index_go_structs

        content = textwrap.dedent("""\
            type CreateOrderRequest struct {
                CustomerID string `json:"customer_id" binding:"required"`
                Amount     float64 `json:"amount" binding:"required,min=0,max=10000"`
                Notes      string `json:"notes"`
            }
        """)
        index: dict = {}
        _index_go_structs(content, index)

        assert "CreateOrderRequest" in index
        fields = index["CreateOrderRequest"]
        assert len(fields) == 3

        cid = next(f for f in fields if f["name"] == "customer_id")
        assert cid["required"] is True

        amt = next(f for f in fields if f["name"] == "amount")
        assert amt["required"] is True
        assert "min=0" in amt.get("constraints", "")

    def test_index_java_record(self):
        """Index Java record classes into field maps."""
        from evospec.reverse.api import _index_java_classes

        content = textwrap.dedent("""\
            public record CreateOrderRequest(String customerId, Double amount) {
            }
        """)
        index: dict = {}
        _index_java_classes(content, index)

        assert "CreateOrderRequest" in index
        fields = index["CreateOrderRequest"]
        assert len(fields) == 2
        assert fields[0]["name"] == "customerId"
        assert fields[0]["type"] == "String"

    def test_detect_auth_fastapi(self):
        """Detect auth from FastAPI dependency injection."""
        from evospec.reverse.api import _detect_auth

        content = "def create_order(body: OrderCreate, user = Depends(get_current_user)):"
        assert _detect_auth(content, "create_order", "fastapi") == "bearer token"

        content_no_auth = "def list_orders():"
        assert _detect_auth(content_no_auth, "list_orders", "fastapi") == ""

    def test_detect_auth_spring(self):
        """Detect auth from Spring Security annotations."""
        from evospec.reverse.api import _detect_auth

        content = "@PreAuthorize(\"hasRole('ADMIN')\")\npublic ResponseEntity create() {}"
        assert _detect_auth(content, "create", "spring") == "role-based"

    def test_detect_request_type_fastapi(self):
        """Detect request body type from FastAPI handler signature."""
        from evospec.reverse.api import _detect_request_type

        content = "def create_order(body: CreateOrderRequest, db: Session):"
        result = _detect_request_type(content, "create_order", "fastapi")
        assert result == "CreateOrderRequest"

    def test_detect_request_type_spring(self):
        """Detect request body type from Spring @RequestBody."""
        from evospec.reverse.api import _detect_request_type

        content = "public ResponseEntity createOrder(@RequestBody CreateOrderRequest body) {"
        result = _detect_request_type(content, "createOrder", "spring")
        assert result == "CreateOrderRequest"

    def test_detect_response_type_fastapi(self):
        """Detect response type from FastAPI response_model."""
        from evospec.reverse.api import _detect_response_type

        content = "@app.get('/orders/{id}', response_model=OrderResponse)\ndef get_order(id: int):"
        result = _detect_response_type(content, "get_order", "fastapi")
        assert result == "OrderResponse"

    def test_detect_error_responses(self):
        """Detect HTTP error status codes from handler code."""
        from evospec.reverse.api import _detect_error_responses

        content = textwrap.dedent("""\
            def create_order(body):
                if not body.customer_id:
                    raise HTTPException(status_code=400, detail="Missing customer")
                order = db.get(body.id)
                if not order:
                    raise HTTPException(status_code=404, detail="Not found")
        """)
        errors = _detect_error_responses(content, "create_order")
        status_codes = {e["status"] for e in errors}
        assert 400 in status_codes
        assert 404 in status_codes

    def test_tags_from_path(self):
        """Extract tags from API path."""
        from evospec.reverse.api import _tags_from_path

        assert _tags_from_path("/api/orders/{id}") == ["orders"]
        assert _tags_from_path("/orders") == ["orders"]
        assert _tags_from_path("/") == []

    def test_build_class_index_filters_by_framework(self, tmp_path):
        """Class index only scans relevant file extensions per framework."""
        from evospec.reverse.api import _build_class_index

        # Create a Python file
        (tmp_path / "models.py").write_text(textwrap.dedent("""\
            from pydantic import BaseModel
            class OrderCreate(BaseModel):
                name: str
        """))

        # Create a TS file
        (tmp_path / "models.ts").write_text(textwrap.dedent("""\
            export interface OrderDTO { name: string; }
        """))

        # FastAPI should only pick up Python
        py_index = _build_class_index([tmp_path], "fastapi")
        assert "OrderCreate" in py_index
        assert "OrderDTO" not in py_index

        # Express should only pick up TS
        ts_index = _build_class_index([tmp_path], "express")
        assert "OrderDTO" in ts_index
        assert "OrderCreate" not in ts_index


# ---------------------------------------------------------------------------
# Deep DB extraction tests
# ---------------------------------------------------------------------------

class TestDeepDbExtraction:

    def test_suggest_invariants_not_null(self):
        """Suggest NOT NULL invariants from entity fields."""
        from evospec.reverse.db import _suggest_invariants

        entities = [{
            "name": "Order",
            "module": "models.py",
            "fields": [
                {"name": "id", "type": "Integer", "nullable": False},
                {"name": "customer_id", "type": "String", "nullable": False},
                {"name": "notes", "type": "String", "nullable": True},
            ],
        }]

        suggested = _suggest_invariants(entities, [], "")
        not_null = [s for s in suggested if "MUST NOT be null" in s["rule"]]
        # id is excluded, customer_id should be there
        assert any("customer_id" in s["rule"] for s in not_null)
        assert not any(s["rule"] == "id MUST NOT be null" for s in not_null)

    def test_suggest_invariants_enum(self):
        """Suggest enum value invariants from enum-typed fields."""
        from evospec.reverse.db import _suggest_invariants

        entities = [{
            "name": "Order",
            "module": "models.py",
            "fields": [
                {"name": "status", "type": "OrderStatus", "nullable": False},
            ],
        }]

        suggested = _suggest_invariants(entities, [], "")
        enum_inv = [s for s in suggested if "defined" in s["rule"] and "OrderStatus" in s["rule"]]
        assert len(enum_inv) >= 1
        assert enum_inv[0]["confidence"] == "high"

    def test_suggest_invariants_fk(self):
        """Suggest FK cardinality invariants."""
        from evospec.reverse.db import _suggest_invariants

        entities = [{
            "name": "OrderItem",
            "module": "models.py",
            "fields": [
                {"name": "order_id", "type": "Integer", "nullable": False},
            ],
        }]

        suggested = _suggest_invariants(entities, [], "")
        fk_inv = [s for s in suggested if "reference exactly one" in s["rule"]]
        assert len(fk_inv) >= 1
        assert "Order" in fk_inv[0]["rule"]

    def test_suggest_invariants_confidence_and_source(self):
        """All suggested invariants must have confidence and source fields (DEEP-REV-002)."""
        from evospec.reverse.db import _suggest_invariants

        entities = [{
            "name": "Order",
            "module": "models.py",
            "fields": [
                {"name": "customer_id", "type": "String", "nullable": False},
                {"name": "status", "type": "OrderStatus", "nullable": False},
            ],
        }]

        suggested = _suggest_invariants(entities, [], "")
        for inv in suggested:
            assert "confidence" in inv, f"Missing confidence in {inv}"
            assert inv["confidence"] in ("high", "medium", "low")
            assert "source" in inv, f"Missing source in {inv}"

    def test_find_enum_values_python(self, tmp_path):
        """Find Python enum values from source code."""
        from evospec.reverse.db import _find_enum_values

        (tmp_path / "enums.py").write_text(textwrap.dedent("""\
            from enum import Enum

            class OrderStatus(str, Enum):
                DRAFT = "draft"
                CONFIRMED = "confirmed"
                SHIPPED = "shipped"
                CANCELLED = "cancelled"
        """))

        values = _find_enum_values("OrderStatus", [tmp_path])
        assert "DRAFT" in values
        assert "CONFIRMED" in values
        assert "SHIPPED" in values
        assert "CANCELLED" in values

    def test_find_enum_values_java(self, tmp_path):
        """Find Java enum values from source code."""
        from evospec.reverse.db import _find_enum_values

        (tmp_path / "OrderStatus.java").write_text(textwrap.dedent("""\
            public enum OrderStatus {
                DRAFT,
                CONFIRMED,
                SHIPPED,
                CANCELLED;
            }
        """))

        values = _find_enum_values("OrderStatus", [tmp_path])
        assert "DRAFT" in values
        assert "CANCELLED" in values

    def test_find_enum_values_typescript(self, tmp_path):
        """Find TypeScript enum values from source code."""
        from evospec.reverse.db import _find_enum_values

        (tmp_path / "enums.ts").write_text(textwrap.dedent("""\
            enum OrderStatus {
                Draft = "DRAFT",
                Confirmed = "CONFIRMED",
                Shipped = "SHIPPED",
            }
        """))

        values = _find_enum_values("OrderStatus", [tmp_path])
        assert "Draft" in values
        assert "Confirmed" in values

    def test_detect_state_machines(self, tmp_path):
        """Detect state machines from status/state enum fields."""
        from evospec.reverse.db import _detect_state_machines

        (tmp_path / "enums.py").write_text(textwrap.dedent("""\
            from enum import Enum
            class OrderStatus(str, Enum):
                DRAFT = "draft"
                CONFIRMED = "confirmed"
                SHIPPED = "shipped"
        """))

        entities = [{
            "name": "Order",
            "fields": [
                {"name": "status", "type": "OrderStatus"},
            ],
        }]

        machines = _detect_state_machines(entities, [tmp_path])
        assert len(machines) >= 1
        sm = machines[0]
        assert sm["entity"] == "Order"
        assert sm["field"] == "status"
        assert "DRAFT" in sm["states"]
        assert "CONFIRMED" in sm["states"]

    def test_find_transitions(self, tmp_path):
        """Detect state transitions from assignment patterns."""
        from evospec.reverse.db import _find_transitions

        (tmp_path / "service.py").write_text(textwrap.dedent("""\
            def confirm_order(order):
                if order.status == "DRAFT":
                    order.status = "CONFIRMED"

            def ship_order(order):
                if order.status == "CONFIRMED":
                    order.status = "SHIPPED"
        """))

        states = ["DRAFT", "CONFIRMED", "SHIPPED"]
        transitions, forbidden = _find_transitions("Order", "status", states, [tmp_path])

        # Should detect DRAFT → CONFIRMED and CONFIRMED → SHIPPED
        from_map = {t["from"]: t["to"] for t in transitions}
        assert "CONFIRMED" in from_map.get("DRAFT", [])
        assert "SHIPPED" in from_map.get("CONFIRMED", [])

        # SHIPPED should be terminal (forbidden)
        terminal_froms = {f["from"] for f in forbidden}
        assert "SHIPPED" in terminal_froms

    def test_no_state_machine_for_non_status_fields(self, tmp_path):
        """Non-status/state fields should not trigger state machine detection."""
        from evospec.reverse.db import _detect_state_machines

        entities = [{
            "name": "Order",
            "fields": [
                {"name": "customer_name", "type": "String"},
                {"name": "amount", "type": "Float"},
            ],
        }]

        machines = _detect_state_machines(entities, [tmp_path])
        assert len(machines) == 0


# ---------------------------------------------------------------------------
# Deep deps extraction tests
# ---------------------------------------------------------------------------

class TestDeepDepsExtraction:

    def test_scan_message_queues_kafka(self, tmp_path):
        """Detect Kafka producer/consumer patterns."""
        from evospec.reverse.deps import _scan_message_queues

        (tmp_path / "producer.ts").write_text(textwrap.dedent("""\
            await producer.send('order-events', { orderId: '123' });
        """))
        (tmp_path / "consumer.py").write_text(textwrap.dedent("""\
            consumer.subscribe('order-events')
        """))

        deps = _scan_message_queues([tmp_path])
        assert len(deps) >= 2
        topics = {d["topic"] for d in deps}
        assert "order-events" in topics
        roles = {d["role"] for d in deps}
        assert "producer" in roles
        assert "consumer" in roles

    def test_scan_message_queues_rabbitmq(self, tmp_path):
        """Detect RabbitMQ publish patterns."""
        from evospec.reverse.deps import _scan_message_queues

        (tmp_path / "publisher.py").write_text(textwrap.dedent("""\
            channel.publish('order-exchange', message)
        """))

        deps = _scan_message_queues([tmp_path])
        assert len(deps) >= 1
        assert deps[0]["system"] == "rabbitmq"

    def test_scan_message_queues_spring_kafka_listener(self, tmp_path):
        """Detect Spring @KafkaListener annotation."""
        from evospec.reverse.deps import _scan_message_queues

        (tmp_path / "OrderConsumer.java").write_text(textwrap.dedent("""\
            @KafkaListener(topics = "order-created")
            public void onOrderCreated(String message) {}
        """))

        deps = _scan_message_queues([tmp_path])
        assert len(deps) >= 1
        assert deps[0]["topic"] == "order-created"
        assert deps[0]["role"] == "consumer"

    def test_scan_storage_ops_s3(self, tmp_path):
        """Detect S3 storage operations."""
        from evospec.reverse.deps import _scan_storage_ops

        (tmp_path / "uploader.ts").write_text(textwrap.dedent("""\
            await s3.putObject({ Bucket: 'my-bucket', Key: 'file.pdf', Body: data });
        """))

        ops = _scan_storage_ops([tmp_path])
        assert len(ops) >= 1
        assert ops[0]["type"] == "s3"
        assert ops[0]["target"] == "my-bucket"

    def test_scan_storage_ops_redis(self, tmp_path):
        """Detect Redis data storage operations."""
        from evospec.reverse.deps import _scan_storage_ops

        (tmp_path / "cache.py").write_text(textwrap.dedent("""\
            redis.set('user:123', json.dumps(user_data))
        """))

        ops = _scan_storage_ops([tmp_path])
        assert len(ops) >= 1
        assert ops[0]["type"] == "redis-store"

    def test_scan_skips_node_modules(self, tmp_path):
        """Message queue scanning should skip node_modules."""
        from evospec.reverse.deps import _scan_message_queues

        nm = tmp_path / "node_modules" / "kafka"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("producer.send('internal-topic', {})")

        deps = _scan_message_queues([tmp_path])
        assert len(deps) == 0


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

class TestCliDeepFlags:
    """Test that --deep and --write flags are wired correctly."""

    def test_reverse_api_deep_flag_accepted(self, tmp_project):
        """reverse api --deep flag is accepted without error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["reverse", "api", "--framework", "fastapi", "--deep"], catch_exceptions=False)
        # May find 0 endpoints but should not error
        assert result.exit_code == 0

    def test_reverse_db_deep_flag_accepted(self, tmp_project):
        """reverse db --deep flag is accepted without error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["reverse", "db", "--deep"], catch_exceptions=False)
        assert result.exit_code == 0

    def test_reverse_deps_deep_flag_accepted(self, tmp_project):
        """reverse deps --deep flag is accepted without error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["reverse", "deps", "--deep"], catch_exceptions=False)
        assert result.exit_code == 0

    def test_write_without_deep_warns(self, tmp_project):
        """--write without --deep should warn and run shallow."""
        runner = CliRunner()
        result = runner.invoke(cli, ["reverse", "api", "--framework", "fastapi", "--write"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "--write requires --deep" in result.output

    def test_shallow_reverse_unchanged(self, tmp_project):
        """Shallow reverse (no --deep) still works as before."""
        runner = CliRunner()
        result = runner.invoke(cli, ["reverse", "api", "--framework", "fastapi"], catch_exceptions=False)
        assert result.exit_code == 0
        # Should NOT contain deep extraction output
        assert "Deep extraction" not in result.output


# ---------------------------------------------------------------------------
# Write output tests
# ---------------------------------------------------------------------------

class TestWriteOutput:

    def test_write_api_contracts(self, tmp_project):
        """--deep --write creates api-contracts.yaml."""
        from evospec.reverse.api import _write_api_contracts
        from evospec.core.config import load_config

        config = load_config(tmp_project)
        contracts = [
            {"endpoint": "POST /api/orders", "tags": ["orders"]},
        ]
        _write_api_contracts(tmp_project, config, contracts)

        contracts_path = tmp_project / "specs" / "domain" / "api-contracts.yaml"
        assert contracts_path.exists()
        content = contracts_path.read_text()
        assert "POST /api/orders" in content

    def test_write_api_contracts_no_overwrite(self, tmp_project):
        """DEEP-REV-001: Don't overwrite existing contracts without --force."""
        import yaml
        from evospec.reverse.api import _write_api_contracts
        from evospec.core.config import load_config

        config = load_config(tmp_project)

        # Pre-populate with existing contracts
        contracts_path = tmp_project / "specs" / "domain" / "api-contracts.yaml"
        contracts_path.write_text(yaml.dump({
            "contracts": [{"endpoint": "GET /api/existing", "tags": ["existing"]}]
        }))

        # Try to write new contracts
        _write_api_contracts(tmp_project, config, [
            {"endpoint": "POST /api/orders", "tags": ["orders"]},
        ])

        # Original should be preserved
        content = contracts_path.read_text()
        assert "GET /api/existing" in content
        assert "POST /api/orders" not in content

    def test_write_deep_db_output(self, tmp_project):
        """--deep --write creates suggested-invariants.yaml and state-machines.yaml."""
        from evospec.reverse.db import _write_deep_db_output
        from evospec.core.config import load_config

        config = load_config(tmp_project)
        suggested = [
            {"id": "INV-ORDER-001", "entity": "Order", "rule": "customer_id MUST NOT be null",
             "source": "NOT NULL", "confidence": "high", "enforcement": "database-constraint"},
        ]
        state_machines = [
            {"entity": "Order", "field": "status", "states": ["DRAFT", "CONFIRMED"],
             "transitions": [{"from": "DRAFT", "to": ["CONFIRMED"]}], "forbidden": []},
        ]

        _write_deep_db_output(tmp_project, config, suggested, state_machines)

        inv_path = tmp_project / "specs" / "domain" / "suggested-invariants.yaml"
        sm_path = tmp_project / "specs" / "domain" / "state-machines.yaml"
        assert inv_path.exists()
        assert sm_path.exists()
        assert "INV-ORDER-001" in inv_path.read_text()
        assert "Order" in sm_path.read_text()
