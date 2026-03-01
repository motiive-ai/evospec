"""Reverse-engineer database schema into domain contract stubs."""

import re
from pathlib import Path

from rich.console import Console

from evospec.core.config import find_project_root, load_config

console = Console()


def reverse_engineer_db(source: str | None = None) -> None:
    """Scan database models or migrations to extract entity information."""
    root = find_project_root()
    if root is None:
        console.print("[red]✗ No evospec.yaml found. Run `evospec init` first.[/red]")
        return

    config = load_config(root)

    source_dirs = []
    if source:
        source_dirs = [root / source]
    else:
        configured = config.get("reverse", {}).get("source_dirs", [])
        source_dirs = [root / d for d in configured] if configured else [root]

    framework = config.get("reverse", {}).get("framework", "")

    console.print("[bold]Scanning for database models...[/bold]")

    entities: list[dict] = []

    if framework == "fastapi":
        entities = _scan_sqlalchemy(source_dirs)
    elif framework == "django":
        entities = _scan_django_models(source_dirs)
    else:
        # Try SQLAlchemy first, then Django
        entities = _scan_sqlalchemy(source_dirs)
        if not entities:
            entities = _scan_django_models(source_dirs)

    if not entities:
        console.print("[yellow]No database models found.[/yellow]")
        return

    console.print(f"\n[green]Found {len(entities)} entity/entities:[/green]\n")

    for entity in entities:
        name = entity.get("name", "?")
        table = entity.get("table", "?")
        fields = entity.get("fields", [])
        module = entity.get("module", "?")

        console.print(f"  [bold cyan]{name}[/bold cyan] [dim](table: {table})[/dim]")
        for field in fields:
            fname = field.get("name", "?")
            ftype = field.get("type", "?")
            nullable = " (nullable)" if field.get("nullable") else ""
            console.print(f"    [dim]├─[/dim] {fname}: {ftype}{nullable}")
        console.print(f"    [dim]└─ {module}[/dim]")
        console.print()

    # Suggest relationships
    relationships = _detect_relationships(entities)
    if relationships:
        console.print("[bold]Detected relationships:[/bold]\n")
        for rel in relationships:
            console.print(f"  {rel['from']} → {rel['to']} [dim]({rel['type']})[/dim]")

    console.print(
        f"\n[dim]Use these findings to populate domain-contract.md entities and "
        f"traceability.tables in spec.yaml.[/dim]"
    )


def _scan_sqlalchemy(source_dirs: list[Path]) -> list[dict]:
    """Scan SQLAlchemy model files."""
    entities = []

    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for py_file in source_dir.rglob("*.py"):
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue

            # Find classes that inherit from Base or DeclarativeBase
            class_pattern = r'class\s+(\w+)\s*\([^)]*(?:Base|DeclarativeBase|Model)[^)]*\)\s*:'
            for class_match in re.finditer(class_pattern, content):
                class_name = class_match.group(1)
                class_start = class_match.end()

                # Find next class or end of file
                next_class = re.search(r'\nclass\s+', content[class_start:])
                class_body = content[class_start:class_start + next_class.start() if next_class else len(content)]

                # Extract __tablename__
                table_match = re.search(r'__tablename__\s*=\s*["\'](\w+)["\']', class_body)
                table_name = table_match.group(1) if table_match else class_name.lower() + "s"

                # Extract columns
                fields = []
                col_pattern = r'(\w+)\s*(?::\s*Mapped\[.*?\]\s*=\s*mapped_column|=\s*(?:Column|mapped_column))\s*\(([^)]*)\)'
                for col_match in re.finditer(col_pattern, class_body):
                    field_name = col_match.group(1)
                    col_args = col_match.group(2)

                    # Determine type
                    type_match = re.search(r'(String|Integer|Boolean|DateTime|UUID|Text|Float|Numeric|JSON|JSONB)', col_args)
                    field_type = type_match.group(1) if type_match else "unknown"

                    nullable = "nullable=True" in col_args or "nullable" not in col_args
                    if "nullable=False" in col_args or "primary_key=True" in col_args:
                        nullable = False

                    fields.append({
                        "name": field_name,
                        "type": field_type,
                        "nullable": nullable,
                    })

                # Also detect simpler Column assignments
                simple_col_pattern = r'(\w+)\s*=\s*Column\((\w+)'
                for col_match in re.finditer(simple_col_pattern, class_body):
                    field_name = col_match.group(1)
                    field_type = col_match.group(2)
                    if not any(f["name"] == field_name for f in fields):
                        fields.append({
                            "name": field_name,
                            "type": field_type,
                            "nullable": True,
                        })

                if fields or table_match:
                    entities.append({
                        "name": class_name,
                        "table": table_name,
                        "fields": fields,
                        "module": str(py_file),
                    })

    return entities


def _scan_django_models(source_dirs: list[Path]) -> list[dict]:
    """Scan Django model files."""
    entities = []

    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for py_file in source_dir.rglob("models.py"):
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue

            class_pattern = r'class\s+(\w+)\s*\(models\.Model\)\s*:'
            for class_match in re.finditer(class_pattern, content):
                class_name = class_match.group(1)
                class_start = class_match.end()

                next_class = re.search(r'\nclass\s+', content[class_start:])
                class_body = content[class_start:class_start + next_class.start() if next_class else len(content)]

                fields = []
                field_pattern = r'(\w+)\s*=\s*models\.(\w+Field)\('
                for field_match in re.finditer(field_pattern, class_body):
                    fields.append({
                        "name": field_match.group(1),
                        "type": field_match.group(2),
                        "nullable": True,
                    })

                if fields:
                    entities.append({
                        "name": class_name,
                        "table": class_name.lower() + "s",
                        "fields": fields,
                        "module": str(py_file),
                    })

    return entities


def _detect_relationships(entities: list[dict]) -> list[dict]:
    """Detect relationships between entities based on field naming conventions."""
    relationships = []
    entity_names = {e["name"].lower() for e in entities}

    for entity in entities:
        for field in entity.get("fields", []):
            fname = field["name"]
            # Check for foreign key patterns: xxx_id
            if fname.endswith("_id"):
                ref_name = fname[:-3]
                if ref_name in entity_names:
                    relationships.append({
                        "from": entity["name"],
                        "to": ref_name.capitalize(),
                        "type": f"FK via {fname}",
                    })

    return relationships
