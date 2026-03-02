"""Tests for relational and transition invariant validation.

Fitness functions:
- FF-REL-001: Relational invariant schema validation
- FF-REL-002: Backwards compatibility with existing invariants
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from evospec.cli.main import cli
from evospec.core.check import (
    _parse_cardinality,
    _validate_scoped_invariants,
    _validate_invariants_against_entities,
)


# ---------------------------------------------------------------------------
# Unit tests: cardinality parsing
# ---------------------------------------------------------------------------

class TestParseCardinality:
    def test_valid_standard(self):
        assert _parse_cardinality("0..1") is True
        assert _parse_cardinality("1..1") is True
        assert _parse_cardinality("0..*") is True
        assert _parse_cardinality("1..*") is True

    def test_valid_numeric_range(self):
        assert _parse_cardinality("2..5") is True
        assert _parse_cardinality("0..10") is True

    def test_invalid(self):
        assert _parse_cardinality("many") is False
        assert _parse_cardinality("1") is False
        assert _parse_cardinality("*..1") is False
        assert _parse_cardinality("") is False


# ---------------------------------------------------------------------------
# Unit tests: relationship invariant schema validation (REL-INV-SCHEMA-001)
# ---------------------------------------------------------------------------

class TestRelationshipInvariantSchema:
    def test_valid_relationship_invariant(self):
        invariants = [{
            "id": "REL-001",
            "scope": "relationship",
            "source": "Order",
            "target": "LineItem",
            "cardinality": "1..*",
            "statement": "Order must have at least 1 LineItem",
            "enforcement": "api-validation",
        }]
        errors, warnings = _validate_scoped_invariants(invariants)
        assert errors == 0
        assert warnings == 0

    def test_missing_source(self):
        invariants = [{
            "id": "REL-002",
            "scope": "relationship",
            "target": "LineItem",
            "cardinality": "1..*",
            "statement": "test",
            "enforcement": "test",
        }]
        errors, warnings = _validate_scoped_invariants(invariants)
        assert errors >= 1

    def test_missing_target(self):
        invariants = [{
            "id": "REL-003",
            "scope": "relationship",
            "source": "Order",
            "cardinality": "1..*",
            "statement": "test",
            "enforcement": "test",
        }]
        errors, warnings = _validate_scoped_invariants(invariants)
        assert errors >= 1

    def test_missing_cardinality(self):
        invariants = [{
            "id": "REL-004",
            "scope": "relationship",
            "source": "Order",
            "target": "LineItem",
            "statement": "test",
            "enforcement": "test",
        }]
        errors, warnings = _validate_scoped_invariants(invariants)
        assert errors >= 1

    def test_invalid_cardinality_warns(self):
        invariants = [{
            "id": "REL-005",
            "scope": "relationship",
            "source": "Order",
            "target": "LineItem",
            "cardinality": "many",
            "statement": "test",
            "enforcement": "test",
        }]
        errors, warnings = _validate_scoped_invariants(invariants)
        assert errors == 0
        assert warnings >= 1

    def test_all_cardinality_notations(self):
        """All standard cardinality notations pass validation."""
        for card in ["0..1", "1..1", "0..*", "1..*", "2..5"]:
            invariants = [{
                "id": f"REL-{card}",
                "scope": "relationship",
                "source": "A",
                "target": "B",
                "cardinality": card,
                "statement": "test",
                "enforcement": "test",
            }]
            errors, warnings = _validate_scoped_invariants(invariants)
            assert errors == 0, f"cardinality {card} should be valid"
            assert warnings == 0, f"cardinality {card} should not warn"


# ---------------------------------------------------------------------------
# Unit tests: transition invariant schema validation (REL-INV-SCHEMA-002)
# ---------------------------------------------------------------------------

class TestTransitionInvariantSchema:
    def test_valid_transition_invariant(self):
        invariants = [{
            "id": "TRANS-001",
            "scope": "transition",
            "entity": "Order",
            "field": "status",
            "statement": "Order status transitions",
            "enforcement": "domain-logic",
            "transitions": [
                {"from": "draft", "to": ["pending_payment", "cancelled"]},
                {"from": "pending_payment", "to": ["confirmed"]},
            ],
        }]
        errors, warnings = _validate_scoped_invariants(invariants)
        assert errors == 0
        assert warnings == 0

    def test_missing_entity(self):
        invariants = [{
            "id": "TRANS-002",
            "scope": "transition",
            "field": "status",
            "statement": "test",
            "enforcement": "test",
            "transitions": [{"from": "a", "to": ["b"]}],
        }]
        errors, warnings = _validate_scoped_invariants(invariants)
        assert errors >= 1

    def test_missing_field(self):
        invariants = [{
            "id": "TRANS-003",
            "scope": "transition",
            "entity": "Order",
            "statement": "test",
            "enforcement": "test",
            "transitions": [{"from": "a", "to": ["b"]}],
        }]
        errors, warnings = _validate_scoped_invariants(invariants)
        assert errors >= 1

    def test_missing_transitions(self):
        invariants = [{
            "id": "TRANS-004",
            "scope": "transition",
            "entity": "Order",
            "field": "status",
            "statement": "test",
            "enforcement": "test",
        }]
        errors, warnings = _validate_scoped_invariants(invariants)
        assert errors >= 1

    def test_transition_missing_from_warns(self):
        invariants = [{
            "id": "TRANS-005",
            "scope": "transition",
            "entity": "Order",
            "field": "status",
            "statement": "test",
            "enforcement": "test",
            "transitions": [{"to": ["b"]}],
        }]
        errors, warnings = _validate_scoped_invariants(invariants)
        assert warnings >= 1

    def test_with_forbidden_transitions(self):
        invariants = [{
            "id": "TRANS-006",
            "scope": "transition",
            "entity": "Order",
            "field": "status",
            "statement": "test",
            "enforcement": "test",
            "transitions": [{"from": "draft", "to": ["pending"]}],
            "forbidden": [{"from": "delivered", "to": "*", "reason": "terminal state"}],
        }]
        errors, warnings = _validate_scoped_invariants(invariants)
        assert errors == 0
        assert warnings == 0


# ---------------------------------------------------------------------------
# Unit tests: entity-scoped (existing) invariants still valid (REL-INV-COMPAT-001)
# ---------------------------------------------------------------------------

class TestBackwardsCompatibility:
    def test_entity_scoped_no_scope_field(self):
        """Existing invariants without 'scope' field remain valid."""
        invariants = [{
            "id": "INV-001",
            "statement": "Order total must be > 0",
            "enforcement": "domain-logic",
        }]
        errors, warnings = _validate_scoped_invariants(invariants)
        assert errors == 0
        assert warnings == 0

    def test_entity_scoped_explicit(self):
        """Explicitly entity-scoped invariants valid."""
        invariants = [{
            "id": "INV-002",
            "scope": "entity",
            "statement": "User email must be unique",
            "enforcement": "db-constraint",
        }]
        errors, warnings = _validate_scoped_invariants(invariants)
        assert errors == 0
        assert warnings == 0

    def test_mixed_scopes(self):
        """Mix of entity, relationship, and transition invariants all valid."""
        invariants = [
            {"id": "INV-001", "statement": "test", "enforcement": "test"},
            {
                "id": "REL-001", "scope": "relationship",
                "source": "A", "target": "B", "cardinality": "1..*",
                "statement": "test", "enforcement": "test",
            },
            {
                "id": "TRANS-001", "scope": "transition",
                "entity": "A", "field": "status",
                "transitions": [{"from": "a", "to": ["b"]}],
                "statement": "test", "enforcement": "test",
            },
        ]
        errors, warnings = _validate_scoped_invariants(invariants)
        assert errors == 0
        assert warnings == 0

    def test_unknown_scope_warns(self):
        invariants = [{
            "id": "INV-003",
            "scope": "temporal",
            "statement": "test",
            "enforcement": "test",
        }]
        errors, warnings = _validate_scoped_invariants(invariants)
        assert warnings >= 1


# ---------------------------------------------------------------------------
# Unit tests: entity cross-reference
# ---------------------------------------------------------------------------

class TestEntityCrossReference:
    def test_relationship_source_target_in_registry(self):
        config = {"domain": {"entities": [
            {"name": "Order"}, {"name": "LineItem"},
        ]}}
        invariants = [{
            "id": "REL-001", "scope": "relationship",
            "source": "Order", "target": "LineItem",
            "cardinality": "1..*", "statement": "test",
        }]
        _, warnings = _validate_invariants_against_entities(invariants, config)
        assert warnings == 0

    def test_relationship_source_not_in_registry(self):
        config = {"domain": {"entities": [{"name": "LineItem"}]}}
        invariants = [{
            "id": "REL-002", "scope": "relationship",
            "source": "Order", "target": "LineItem",
            "cardinality": "1..*", "statement": "test",
        }]
        _, warnings = _validate_invariants_against_entities(invariants, config)
        assert warnings >= 1

    def test_transition_entity_in_registry(self):
        config = {"domain": {"entities": [{"name": "Order"}]}}
        invariants = [{
            "id": "TRANS-001", "scope": "transition",
            "entity": "Order", "field": "status",
            "transitions": [{"from": "a", "to": ["b"]}],
            "statement": "test",
        }]
        _, warnings = _validate_invariants_against_entities(invariants, config)
        assert warnings == 0

    def test_transition_entity_not_in_registry(self):
        config = {"domain": {"entities": [{"name": "Product"}]}}
        invariants = [{
            "id": "TRANS-002", "scope": "transition",
            "entity": "Order", "field": "status",
            "transitions": [{"from": "a", "to": ["b"]}],
            "statement": "test",
        }]
        _, warnings = _validate_invariants_against_entities(invariants, config)
        assert warnings >= 1

    def test_no_entity_registry_skips(self):
        config = {}
        invariants = [{
            "id": "REL-001", "scope": "relationship",
            "source": "Order", "target": "LineItem",
            "cardinality": "1..*", "statement": "test",
        }]
        _, warnings = _validate_invariants_against_entities(invariants, config)
        assert warnings == 0


# ---------------------------------------------------------------------------
# Integration: evospec check with relational invariants
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def project_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestCheckIntegration:
    def test_check_core_with_valid_relational_invariants(self, runner, project_dir):
        """Core spec with valid relational + transition invariants passes check."""
        os.chdir(project_dir)
        runner.invoke(cli, ["init", "--name", "test"])
        runner.invoke(cli, ["new", "order-rules", "--zone", "core"])

        specs_dir = project_dir / "specs" / "changes"
        spec_dir = list(specs_dir.iterdir())[0]
        spec_yaml = spec_dir / "spec.yaml"
        spec = yaml.safe_load(spec_yaml.read_text())
        spec["bounded_context"] = "orders"
        spec["invariants"] = [
            {
                "id": "REL-001",
                "scope": "relationship",
                "source": "Order",
                "target": "LineItem",
                "cardinality": "1..*",
                "statement": "Order must have at least 1 LineItem",
                "enforcement": "api-validation",
            },
            {
                "id": "TRANS-001",
                "scope": "transition",
                "entity": "Order",
                "field": "status",
                "statement": "Order status transitions",
                "enforcement": "domain-logic",
                "transitions": [
                    {"from": "draft", "to": ["pending_payment", "cancelled"]},
                    {"from": "pending_payment", "to": ["confirmed"]},
                ],
            },
        ]
        spec["fitness_functions"] = [
            {"id": "FF-001", "name": "test", "type": "unit-test",
             "path": "tests/test_relational_invariants.py", "dimension": "test"},
        ]
        with open(spec_yaml, "w") as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

        result = runner.invoke(cli, ["check"])
        assert result.exit_code == 0
        assert "2 invariant(s) defined" in result.output

    def test_check_core_existing_invariants_still_valid(self, runner, project_dir):
        """REL-INV-COMPAT-001: Existing entity-scoped invariants still work."""
        os.chdir(project_dir)
        runner.invoke(cli, ["init", "--name", "test"])
        runner.invoke(cli, ["new", "existing-rules", "--zone", "core"])

        specs_dir = project_dir / "specs" / "changes"
        spec_dir = list(specs_dir.iterdir())[0]
        spec_yaml = spec_dir / "spec.yaml"
        spec = yaml.safe_load(spec_yaml.read_text())
        spec["bounded_context"] = "orders"
        spec["invariants"] = [
            {
                "id": "INV-001",
                "statement": "Order total must be > 0",
                "enforcement": "domain-logic",
            },
        ]
        spec["fitness_functions"] = [
            {"id": "FF-001", "name": "test", "type": "unit-test",
             "path": "tests/test_relational_invariants.py", "dimension": "test"},
        ]
        with open(spec_yaml, "w") as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

        result = runner.invoke(cli, ["check"])
        assert result.exit_code == 0
        assert "1 invariant(s) defined" in result.output
