"""Tests for MCP + Skills redesign (Phases 1-8).

Covers:
- Skills emitter output (SKILL.md format, frontmatter, MCP refs)
- MCP resource deprecation aliases
- New MCP tools (get_entities, get_invariants, get_upstream_apis, parse_contract_file)
- Contract parser module
- Schema version gate
- Backwards compatibility (AGT-INV-010)
"""

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from evospec.cli.main import cli
from evospec.core.agents import (
    EMITTERS,
    PLATFORMS,
    _add_mcp_tool_refs,
    _build_skills_context_md,
)
from evospec.core.check import _version_newer
from evospec.mcp.contract_parser import parse_contract


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def project_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def initialized_project(runner, project_dir):
    """Create an initialized evospec project."""
    os.chdir(project_dir)
    runner.invoke(cli, ["init", "--name", "test-project"])
    return project_dir


# ---------------------------------------------------------------------------
# Phase 1: Setup
# ---------------------------------------------------------------------------


class TestSetup:
    def test_skills_in_platforms(self):
        assert "skills" in PLATFORMS

    def test_skills_in_emitters(self):
        assert "skills" in EMITTERS

    def test_cli_accepts_skills_platform(self, runner, initialized_project):
        result = runner.invoke(cli, ["generate", "agents", "--platform", "skills"])
        assert result.exit_code == 0
        assert "skills:" in result.output


# ---------------------------------------------------------------------------
# Phase 2: Skills Emitter
# ---------------------------------------------------------------------------


class TestSkillsEmitter:
    def test_skills_generates_skill_dirs(self, runner, initialized_project):
        result = runner.invoke(cli, ["generate", "agents", "--platform", "skills"])
        assert result.exit_code == 0

        skills_root = initialized_project / ".agents" / "skills"
        assert skills_root.exists()

        # Should have 10 skill directories
        skill_dirs = [d for d in skills_root.iterdir() if d.is_dir()]
        assert len(skill_dirs) == 10

    def test_skill_md_has_frontmatter(self, runner, initialized_project):
        runner.invoke(cli, ["generate", "agents", "--platform", "skills"])

        skill_md = (
            initialized_project
            / ".agents"
            / "skills"
            / "evospec-discover"
            / "SKILL.md"
        )
        assert skill_md.exists()
        content = skill_md.read_text()

        # Check YAML frontmatter
        assert content.startswith("---\n")
        parts = content.split("---\n", 2)
        assert len(parts) >= 3
        fm = yaml.safe_load(parts[1])
        assert fm["name"] == "evospec-discover"
        assert "description" in fm

    def test_skill_md_has_sections(self, runner, initialized_project):
        runner.invoke(cli, ["generate", "agents", "--platform", "skills"])

        skill_md = (
            initialized_project
            / ".agents"
            / "skills"
            / "evospec-discover"
            / "SKILL.md"
        )
        content = skill_md.read_text()

        assert "## Context" in content
        assert "## Steps" in content
        assert "references/context.md" in content

    def test_skill_has_references_context(self, runner, initialized_project):
        runner.invoke(cli, ["generate", "agents", "--platform", "skills"])

        ctx_md = (
            initialized_project
            / ".agents"
            / "skills"
            / "evospec-discover"
            / "references"
            / "context.md"
        )
        assert ctx_md.exists()
        content = ctx_md.read_text()

        assert "## Layers" in content
        assert "## MCP Server" in content
        assert "evospec:" in content

    def test_mcp_tool_refs_in_skills(self, runner, initialized_project):
        runner.invoke(cli, ["generate", "agents", "--platform", "skills"])

        skill_md = (
            initialized_project
            / ".agents"
            / "skills"
            / "evospec-discover"
            / "SKILL.md"
        )
        content = skill_md.read_text()

        # Should contain fully-qualified MCP tool references
        if "check_invariant_impact" in content:
            assert "evospec:check_invariant_impact" in content

    def test_add_mcp_tool_refs(self):
        text = "Call check_invariant_impact(entities=[]) to verify."
        result = _add_mcp_tool_refs(text)
        assert "evospec:check_invariant_impact(" in result

    def test_add_mcp_tool_refs_no_double_prefix(self):
        text = "Call evospec:check_invariant_impact(entities=[])."
        result = _add_mcp_tool_refs(text)
        assert "evospec:evospec:" not in result

    def test_build_skills_context_md(self):
        ctx_yaml = (
            Path(__file__).parent.parent
            / "src"
            / "evospec"
            / "templates"
            / "workflows"
            / "_context.yaml"
        )
        ctx = yaml.safe_load(ctx_yaml.read_text())
        result = _build_skills_context_md(ctx)

        assert "## Layers" in result
        assert "## Zone Classification" in result
        assert "## MCP Server" in result
        assert "evospec:" in result


# ---------------------------------------------------------------------------
# Phase 3: MCP Resource Deprecation
# ---------------------------------------------------------------------------


class TestMCPDeprecation:
    def test_deprecated_config_resource(self):
        from evospec.mcp.server import get_config

        # Can't call without project root, but we can verify it exists
        assert callable(get_config)

    def test_deprecated_entities_resource(self):
        from evospec.mcp.server import get_entity_registry

        assert callable(get_entity_registry)

    def test_deprecated_invariants_resource(self):
        from evospec.mcp.server import get_all_invariants

        assert callable(get_all_invariants)

    def test_project_resource_exists(self):
        from evospec.mcp.server import get_project

        assert callable(get_project)


# ---------------------------------------------------------------------------
# Phase 4: New MCP Tools
# ---------------------------------------------------------------------------


class TestNewMCPTools:
    def test_get_entities_tool_exists(self):
        from evospec.mcp.server import get_entities

        assert callable(get_entities)

    def test_get_invariants_tool_exists(self):
        from evospec.mcp.server import get_invariants

        assert callable(get_invariants)

    def test_get_upstream_apis_tool_exists(self):
        from evospec.mcp.server import get_upstream_apis

        assert callable(get_upstream_apis)

    def test_parse_contract_file_tool_exists(self):
        from evospec.mcp.server import parse_contract_file

        assert callable(parse_contract_file)


# ---------------------------------------------------------------------------
# Phase 4: Contract Parser
# ---------------------------------------------------------------------------


class TestContractParser:
    def test_parse_openapi_json(self, tmp_path):
        openapi = {
            "openapi": "3.0.0",
            "info": {"title": "Order API", "version": "1.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "Order": {
                        "type": "object",
                        "required": ["id", "status"],
                        "properties": {
                            "id": {"type": "string", "format": "uuid"},
                            "status": {
                                "type": "string",
                                "enum": ["draft", "confirmed", "cancelled"],
                            },
                            "items": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/LineItem"},
                            },
                        },
                    },
                    "LineItem": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string"},
                            "quantity": {"type": "integer", "minimum": 1},
                        },
                    },
                }
            },
        }
        f = tmp_path / "api.json"
        f.write_text(json.dumps(openapi))

        result = parse_contract(f)
        assert result["format"] == "openapi"
        assert result["total_entities"] == 2
        names = {e["name"] for e in result["entities"]}
        assert "Order" in names
        assert "LineItem" in names

    def test_parse_openapi_yaml(self, tmp_path):
        openapi = {
            "openapi": "3.0.0",
            "components": {
                "schemas": {
                    "Product": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "price": {"type": "number"},
                        },
                    }
                }
            },
        }
        f = tmp_path / "api.yaml"
        f.write_text(yaml.dump(openapi))

        result = parse_contract(f)
        assert result["format"] == "openapi"
        assert result["total_entities"] == 1

    def test_parse_json_schema(self, tmp_path):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "OrderResponse",
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string"},
                            "qty": {"type": "integer"},
                        },
                    },
                },
            },
        }
        f = tmp_path / "schema.json"
        f.write_text(json.dumps(schema))

        result = parse_contract(f)
        assert result["format"] == "json_schema"
        assert result["total_entities"] >= 2  # Root + Items entity
        rels = result["relationships"]
        assert any(r["type"] == "has_many" for r in rels)

    def test_parse_json_example(self, tmp_path):
        example = {
            "id": "ord-123",
            "status": "confirmed",
            "total": 99.50,
            "items": [
                {"product_id": "prod-1", "quantity": 2, "price": 49.75},
            ],
            "customer": {"name": "Jane", "email": "jane@example.com"},
        }
        f = tmp_path / "order-response.json"
        f.write_text(json.dumps(example))

        result = parse_contract(f)
        assert result["format"] == "json_example"
        assert result["total_entities"] >= 3  # Order-Response, Item, Customer
        names = {e["name"] for e in result["entities"]}
        assert "Order-Response" in names or "Order-response" in names or len(names) >= 3

    def test_parse_json_example_array(self, tmp_path):
        example = [
            {"id": 1, "name": "Widget", "active": True},
            {"id": 2, "name": "Gadget", "active": False},
        ]
        f = tmp_path / "products.json"
        f.write_text(json.dumps(example))

        result = parse_contract(f)
        assert result["format"] == "json_example"
        assert result["total_entities"] >= 1

    def test_unsupported_format(self, tmp_path):
        f = tmp_path / "data.xml"
        f.write_text("<root/>")

        result = parse_contract(f)
        assert "error" in result

    def test_openapi_relationships(self, tmp_path):
        openapi = {
            "openapi": "3.0.0",
            "components": {
                "schemas": {
                    "Order": {
                        "type": "object",
                        "properties": {
                            "items": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/LineItem"},
                            }
                        },
                    },
                    "LineItem": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                        },
                    },
                }
            },
        }
        f = tmp_path / "api.json"
        f.write_text(json.dumps(openapi))

        result = parse_contract(f)
        assert len(result["relationships"]) >= 1
        rel = result["relationships"][0]
        assert rel["source"] == "Order"
        assert rel["target"] == "LineItem"


# ---------------------------------------------------------------------------
# Phase 3: Schema Version Gate
# ---------------------------------------------------------------------------


class TestSchemaVersionGate:
    def test_version_newer_true(self):
        assert _version_newer("2.0.0", "1.0.0") is True
        assert _version_newer("1.1.0", "1.0.0") is True
        assert _version_newer("1.0.1", "1.0.0") is True

    def test_version_newer_false(self):
        assert _version_newer("1.0.0", "1.0.0") is False
        assert _version_newer("0.9.0", "1.0.0") is False

    def test_version_newer_invalid(self):
        assert _version_newer("abc", "1.0.0") is False
        assert _version_newer("", "1.0.0") is False

    def test_check_warns_on_newer_version(self, runner, project_dir):
        os.chdir(project_dir)
        runner.invoke(cli, ["init", "--name", "test"])

        # Set a newer schema version
        config_path = project_dir / "evospec.yaml"
        config = yaml.safe_load(config_path.read_text())
        config["schema"] = {"version": "99.0.0"}
        config_path.write_text(yaml.dump(config, default_flow_style=False))

        # Create a minimal edge spec so check has something to validate
        runner.invoke(cli, ["new", "test-feature", "--zone", "edge"])

        result = runner.invoke(cli, ["check"])
        assert "schema version 99.0.0" in result.output


# ---------------------------------------------------------------------------
# Backwards Compatibility (AGT-INV-010)
# ---------------------------------------------------------------------------


class TestBackwardsCompat:
    def test_schema_no_additional_properties_false(self):
        """Ensure spec.schema.json doesn't use additionalProperties: false at top level."""
        schema_path = (
            Path(__file__).parent.parent
            / "src"
            / "evospec"
            / "schemas"
            / "spec.schema.json"
        )
        schema = json.loads(schema_path.read_text())
        # Top level should NOT have additionalProperties: false
        assert schema.get("additionalProperties") is not False

    def test_old_spec_validates_with_new_schema(self):
        """A spec.yaml without new optional fields should still validate."""
        from jsonschema import Draft202012Validator

        schema_path = (
            Path(__file__).parent.parent
            / "src"
            / "evospec"
            / "schemas"
            / "spec.schema.json"
        )
        schema = json.loads(schema_path.read_text())
        validator = Draft202012Validator(schema)

        old_spec = {
            "id": "legacy-spec",
            "title": "Legacy Spec",
            "status": "draft",
            "created_at": "2026-01-01",
            "zone": "edge",
            "discovery": {
                "outcome": "Test",
                "opportunity": "Test",
                "kill_criteria": "If fails",
                "assumptions": [],
            },
        }

        errors = list(validator.iter_errors(old_spec))
        assert len(errors) == 0, f"Old spec should validate: {errors}"


# ---------------------------------------------------------------------------
# Integration: Full generate agents
# ---------------------------------------------------------------------------


class TestGenerateAgentsIntegration:
    def test_generate_all_platforms(self, runner, initialized_project):
        result = runner.invoke(cli, ["generate", "agents"])
        assert result.exit_code == 0
        assert "windsurf:" in result.output
        assert "claude:" in result.output
        assert "cursor:" in result.output
        assert "skills:" in result.output

        # Verify all platform outputs exist
        assert (initialized_project / ".windsurf" / "workflows").exists()
        assert (initialized_project / "CLAUDE.md").exists()
        assert (initialized_project / ".cursor" / "rules").exists()
        assert (initialized_project / ".agents" / "skills").exists()

    def test_generate_skills_only(self, runner, project_dir):
        os.chdir(project_dir)
        # Don't use initialized_project (init generates all platforms)
        runner.invoke(cli, ["init", "--name", "test"])

        # Remove the CLAUDE.md created by init
        claude_md = project_dir / "CLAUDE.md"
        if claude_md.exists():
            claude_md.unlink()

        result = runner.invoke(cli, ["generate", "agents", "--platform", "skills"])
        assert result.exit_code == 0
        assert "skills:" in result.output

        # Skills output should exist
        assert (project_dir / ".agents" / "skills").exists()
        # CLAUDE.md should NOT be regenerated by skills-only
        assert not claude_md.exists()
