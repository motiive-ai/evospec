"""Parse API contract files into domain entities.

Supports:
- OpenAPI/Swagger (definitions/components.schemas)
- JSON Schema (top-level object properties)
- JSON example files (infer entity structure from response)
"""

import json
from pathlib import Path
from typing import Any

import yaml


def parse_contract(file_path: Path) -> dict:
    """Parse a contract file and return extracted entities.

    Args:
        file_path: Path to the contract file (.json, .yaml, .yml)

    Returns:
        Dict with 'format', 'entities', and 'relationships' keys.
    """
    content = file_path.read_text()
    suffix = file_path.suffix.lower()

    if suffix == ".json":
        data = json.loads(content)
    elif suffix in (".yaml", ".yml"):
        data = yaml.safe_load(content) or {}
    else:
        return {"error": f"Unsupported format: {suffix}"}

    # Detect format and dispatch
    if _is_openapi(data):
        return _parse_openapi(data)
    elif _is_json_schema(data):
        return _parse_json_schema(data)
    else:
        return _parse_json_example(data, file_path.stem)


def _is_openapi(data: Any) -> bool:
    """Detect if data is an OpenAPI/Swagger spec."""
    if not isinstance(data, dict):
        return False
    return (
        "openapi" in data
        or "swagger" in data
        or "paths" in data
        or ("components" in data and "schemas" in data.get("components", {}))
        or "definitions" in data
    )


def _is_json_schema(data: Any) -> bool:
    """Detect if data is a JSON Schema document."""
    if not isinstance(data, dict):
        return False
    return "$schema" in data or (data.get("type") == "object" and "properties" in data)


def _parse_openapi(data: dict) -> dict:
    """Extract entities from OpenAPI/Swagger definitions/components.schemas."""
    schemas: dict = {}

    # OpenAPI 3.x
    if "components" in data and "schemas" in data.get("components", {}):
        schemas = data["components"]["schemas"]
    # Swagger 2.x
    elif "definitions" in data:
        schemas = data["definitions"]

    entities = []
    relationships = []

    for name, schema in schemas.items():
        entity = _schema_to_entity(name, schema)
        entities.append(entity)

        # Extract relationships from $ref
        for field in entity.get("fields", []):
            ref = field.get("_ref")
            if ref:
                relationships.append({
                    "source": name,
                    "target": ref,
                    "type": field.get("_ref_type", "references"),
                    "field": field["name"],
                })

    return {
        "format": "openapi",
        "version": data.get("openapi", data.get("swagger", "unknown")),
        "entities": entities,
        "relationships": relationships,
        "total_entities": len(entities),
    }


def _parse_json_schema(data: dict) -> dict:
    """Extract entities from a JSON Schema document."""
    entities = []
    relationships = []

    root_name = data.get("title", "Root")
    if data.get("type") == "object" and "properties" in data:
        entity = _schema_to_entity(root_name, data)
        entities.append(entity)

        # Check nested objects
        for prop_name, prop_schema in data.get("properties", {}).items():
            if prop_schema.get("type") == "object" and "properties" in prop_schema:
                nested = _schema_to_entity(prop_name.title(), prop_schema)
                entities.append(nested)
                relationships.append({
                    "source": root_name,
                    "target": prop_name.title(),
                    "type": "contains",
                    "field": prop_name,
                })
            elif prop_schema.get("type") == "array":
                items = prop_schema.get("items", {})
                if items.get("type") == "object" and "properties" in items:
                    nested = _schema_to_entity(prop_name.title(), items)
                    entities.append(nested)
                    relationships.append({
                        "source": root_name,
                        "target": prop_name.title(),
                        "type": "has_many",
                        "field": prop_name,
                    })

    # Check for $defs / definitions
    for defs_key in ("$defs", "definitions"):
        for name, schema in data.get(defs_key, {}).items():
            entity = _schema_to_entity(name, schema)
            entities.append(entity)

    return {
        "format": "json_schema",
        "entities": entities,
        "relationships": relationships,
        "total_entities": len(entities),
    }


def _parse_json_example(data: Any, name_hint: str = "Response") -> dict:
    """Infer entity structure from a JSON example response."""
    entities = []
    relationships = []

    def _infer_entity(name: str, obj: dict) -> dict:
        fields = []
        for key, value in obj.items():
            field: dict[str, Any] = {"name": key, "type": _infer_type(value)}
            if isinstance(value, dict) and value:
                nested_name = key.title()
                nested = _infer_entity(nested_name, value)
                entities.append(nested)
                relationships.append({
                    "source": name,
                    "target": nested_name,
                    "type": "contains",
                    "field": key,
                })
                field["type"] = nested_name
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                nested_name = key.rstrip("s").title()
                nested = _infer_entity(nested_name, value[0])
                entities.append(nested)
                relationships.append({
                    "source": name,
                    "target": nested_name,
                    "type": "has_many",
                    "field": key,
                })
                field["type"] = f"list[{nested_name}]"
            fields.append(field)
        return {"name": name, "fields": fields}

    if isinstance(data, dict):
        root = _infer_entity(name_hint.title(), data)
        entities.insert(0, root)
    elif isinstance(data, list) and data and isinstance(data[0], dict):
        root = _infer_entity(name_hint.rstrip("s").title(), data[0])
        entities.insert(0, root)
    else:
        return {
            "format": "json_example",
            "error": "Cannot infer entities from non-object JSON.",
            "entities": [],
            "relationships": [],
            "total_entities": 0,
        }

    return {
        "format": "json_example",
        "entities": entities,
        "relationships": relationships,
        "total_entities": len(entities),
    }


def _schema_to_entity(name: str, schema: dict) -> dict:
    """Convert an OpenAPI/JSON Schema object to an entity dict."""
    fields = []
    required = set(schema.get("required", []))

    for prop_name, prop_schema in schema.get("properties", {}).items():
        field: dict[str, Any] = {
            "name": prop_name,
            "type": _resolve_type(prop_schema),
        }

        constraints = []
        if prop_name in required:
            constraints.append("required")
        if "enum" in prop_schema:
            constraints.append(f"enum: {prop_schema['enum']}")
        if "minLength" in prop_schema:
            constraints.append(f"minLength: {prop_schema['minLength']}")
        if "maxLength" in prop_schema:
            constraints.append(f"maxLength: {prop_schema['maxLength']}")
        if "minimum" in prop_schema:
            constraints.append(f"min: {prop_schema['minimum']}")
        if "maximum" in prop_schema:
            constraints.append(f"max: {prop_schema['maximum']}")
        if "pattern" in prop_schema:
            constraints.append(f"pattern: {prop_schema['pattern']}")
        if "format" in prop_schema:
            constraints.append(f"format: {prop_schema['format']}")

        if constraints:
            field["constraints"] = ", ".join(constraints)

        # Track $ref for relationship extraction
        ref = prop_schema.get("$ref", "")
        if ref:
            field["_ref"] = ref.split("/")[-1]
            field["_ref_type"] = "references"
        elif prop_schema.get("type") == "array":
            items_ref = prop_schema.get("items", {}).get("$ref", "")
            if items_ref:
                field["_ref"] = items_ref.split("/")[-1]
                field["_ref_type"] = "has_many"

        fields.append(field)

    return {
        "name": name,
        "description": schema.get("description", ""),
        "fields": fields,
    }


def _resolve_type(schema: dict) -> str:
    """Resolve a JSON Schema type to a simple type string."""
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    t = schema.get("type", "any")
    if t == "array":
        items = schema.get("items", {})
        if "$ref" in items:
            return f"list[{items['$ref'].split('/')[-1]}]"
        return f"list[{items.get('type', 'any')}]"
    fmt = schema.get("format", "")
    if fmt:
        return f"{t}({fmt})"
    return t


def _infer_type(value: Any) -> str:
    """Infer a type string from a JSON value."""
    if value is None:
        return "nullable"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        if not value:
            return "list[any]"
        return f"list[{_infer_type(value[0])}]"
    if isinstance(value, dict):
        return "object"
    return "any"
