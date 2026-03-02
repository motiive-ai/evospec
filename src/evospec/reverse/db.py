"""Reverse-engineer database schema into domain contract stubs."""

import re
from pathlib import Path

from rich.console import Console

from evospec.core.config import find_project_root, load_config

console = Console()


def _iter_files(source_dirs: list[Path], extensions: set[str]) -> list[Path]:
    """Yield source files matching the given extensions from source_dirs."""
    files: list[Path] = []
    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for src_file in source_dir.rglob("*"):
            if src_file.suffix in extensions:
                files.append(src_file)
    return files


def _read_safe(path: Path) -> str | None:
    """Read file text, returning None on error."""
    try:
        return path.read_text()
    except (UnicodeDecodeError, PermissionError):
        return None


def _extract_body(content: str, start: int) -> str:
    """Extract a class/struct body from start position to next class/struct or EOF."""
    next_class = re.search(r'\n(?:class|type)\s+', content[start:])
    return content[start:start + next_class.start() if next_class else len(content)]


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

    # --- Python ---
    if framework in ("fastapi", "flask"):
        entities = _scan_sqlalchemy(source_dirs)
    elif framework == "django":
        entities = _scan_django_models(source_dirs)
    # --- Go ---
    elif framework in ("gin", "echo", "fiber", "chi", "gorilla", "net-http"):
        entities = _scan_gorm(source_dirs)
    # --- Java ---
    elif framework == "spring":
        entities = _scan_jpa(source_dirs)
    # --- JS/TS ---
    elif framework in ("express", "nextjs", "nestjs", "hono", "fastify"):
        entities = _scan_prisma(source_dirs)
        if not entities:
            entities = _scan_typeorm(source_dirs)
        if not entities:
            entities = _scan_sequelize(source_dirs)
    else:
        # Auto-detect: try all scanners
        entities = _scan_sqlalchemy(source_dirs)
        if not entities:
            entities = _scan_django_models(source_dirs)
        if not entities:
            entities = _scan_gorm(source_dirs)
        if not entities:
            entities = _scan_jpa(source_dirs)
        if not entities:
            entities = _scan_prisma(source_dirs)
        if not entities:
            entities = _scan_typeorm(source_dirs)
        if not entities:
            entities = _scan_sequelize(source_dirs)

    if not entities:
        console.print("[yellow]No database models found.[/yellow]")
        return

    console.print(f"\n[green]Found {len(entities)} entity/entities:[/green]\n")

    for entity in entities:
        name = entity.get("name", "?")
        table = entity.get("table", "?")
        fields = entity.get("fields", [])
        module = entity.get("module", "?")
        lang = entity.get("lang", "")

        lang_tag = f" [dim][{lang}][/dim]" if lang else ""
        console.print(f"  [bold cyan]{name}[/bold cyan] [dim](table: {table})[/dim]{lang_tag}")
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

    # Generate entity registry YAML for evospec.yaml
    console.print()
    console.print("[bold]Entity registry YAML (paste into evospec.yaml → domain.entities):[/bold]")
    console.print()
    registry_lines = _generate_entity_registry(entities, relationships)
    for line in registry_lines:
        console.print(f"[dim]{line}[/dim]")

    console.print(
        f"\n[dim]Use these findings to populate domain-contract.md entities and "
        f"traceability.tables in spec.yaml.[/dim]"
    )


# ---------------------------------------------------------------------------
# Python scanners
# ---------------------------------------------------------------------------

def _scan_sqlalchemy(source_dirs: list[Path]) -> list[dict]:
    """Scan SQLAlchemy model files."""
    entities = []

    for py_file in _iter_files(source_dirs, {".py"}):
        content = _read_safe(py_file)
        if content is None:
            continue

        # Find classes that inherit from Base or DeclarativeBase
        class_pattern = r'class\s+(\w+)\s*\([^)]*(?:Base|DeclarativeBase|Model)[^)]*\)\s*:'
        for class_match in re.finditer(class_pattern, content):
            class_name = class_match.group(1)
            class_body = _extract_body(content, class_match.end())

            # Extract __tablename__
            table_match = re.search(r'__tablename__\s*=\s*["\'](\w+)["\']', class_body)
            table_name = table_match.group(1) if table_match else class_name.lower() + "s"

            # Extract columns
            fields = []
            col_pattern = r'(\w+)\s*(?::\s*Mapped\[.*?\]\s*=\s*mapped_column|=\s*(?:Column|mapped_column))\s*\(([^)]*)\)'
            for col_match in re.finditer(col_pattern, class_body):
                field_name = col_match.group(1)
                col_args = col_match.group(2)

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
                    "lang": "python/sqlalchemy",
                })

    return entities


def _scan_django_models(source_dirs: list[Path]) -> list[dict]:
    """Scan Django model files."""
    entities = []

    for py_file in _iter_files(source_dirs, {".py"}):
        if "models" not in py_file.stem:
            continue
        content = _read_safe(py_file)
        if content is None:
            continue

        class_pattern = r'class\s+(\w+)\s*\(models\.Model\)\s*:'
        for class_match in re.finditer(class_pattern, content):
            class_name = class_match.group(1)
            class_body = _extract_body(content, class_match.end())

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
                    "lang": "python/django",
                })

    return entities


# ---------------------------------------------------------------------------
# Go scanners
# ---------------------------------------------------------------------------

def _scan_gorm(source_dirs: list[Path]) -> list[dict]:
    """Scan Go GORM model structs with gorm tags."""
    entities = []

    for go_file in _iter_files(source_dirs, {".go"}):
        content = _read_safe(go_file)
        if content is None:
            continue

        # Match type User struct { ... }
        struct_pattern = r'type\s+(\w+)\s+struct\s*\{'
        for struct_match in re.finditer(struct_pattern, content):
            struct_name = struct_match.group(1)
            # Find closing brace
            brace_start = struct_match.end() - 1
            depth = 1
            pos = brace_start + 1
            while pos < len(content) and depth > 0:
                if content[pos] == '{':
                    depth += 1
                elif content[pos] == '}':
                    depth -= 1
                pos += 1
            struct_body = content[brace_start:pos]

            # Check if this struct has gorm tags or embeds gorm.Model
            has_gorm = 'gorm.Model' in struct_body or '`gorm:' in struct_body or '`json:' in struct_body

            if not has_gorm:
                continue

            # Extract table name from TableName() method or derive from struct name
            table_pattern = rf'func\s+\(\s*\w+\s+\*?{struct_name}\s*\)\s+TableName\(\)\s+string\s*\{{\s*return\s+["`](\w+)["`]'
            table_match = re.search(table_pattern, content)
            table_name = table_match.group(1) if table_match else _go_pluralize(struct_name)

            # Extract fields: FieldName Type `gorm:"..." json:"..."`
            fields = []
            field_pattern = r'(\w+)\s+([\w.*\[\]]+)\s*`([^`]*)`'
            for field_match in re.finditer(field_pattern, struct_body):
                field_name = field_match.group(1)
                field_type = field_match.group(2)
                tags = field_match.group(3)

                # Skip embedded structs like gorm.Model
                if field_name in ("Model", "DeletedAt"):
                    continue

                # Check gorm tag for column name
                gorm_col = re.search(r'gorm:"[^"]*column:(\w+)', tags)
                col_name = gorm_col.group(1) if gorm_col else _go_to_snake(field_name)

                nullable = "not null" not in tags.lower()

                fields.append({
                    "name": col_name,
                    "type": field_type,
                    "nullable": nullable,
                })

            # Also extract fields without tags (bare struct fields)
            bare_field_pattern = r'^\s+(\w+)\s+([\w.*\[\]]+)\s*$'
            for field_match in re.finditer(bare_field_pattern, struct_body, re.MULTILINE):
                field_name = field_match.group(1)
                field_type = field_match.group(2)
                if field_name[0].isupper() and field_name not in ("Model", "DeletedAt"):
                    col_name = _go_to_snake(field_name)
                    if not any(f["name"] == col_name for f in fields):
                        fields.append({
                            "name": col_name,
                            "type": field_type,
                            "nullable": True,
                        })

            if fields:
                entities.append({
                    "name": struct_name,
                    "table": table_name,
                    "fields": fields,
                    "module": str(go_file),
                    "lang": "go/gorm",
                })

    return entities


def _go_to_snake(name: str) -> str:
    """Convert Go CamelCase to snake_case."""
    result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    result = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', result)
    return result.lower()


def _go_pluralize(name: str) -> str:
    """Simple pluralization for Go struct names to table names."""
    snake = _go_to_snake(name)
    if snake.endswith("s"):
        return snake
    if snake.endswith("y"):
        return snake[:-1] + "ies"
    return snake + "s"


# ---------------------------------------------------------------------------
# Java scanners
# ---------------------------------------------------------------------------

def _scan_jpa(source_dirs: list[Path]) -> list[dict]:
    """Scan Java JPA/Hibernate @Entity classes."""
    entities = []

    for java_file in _iter_files(source_dirs, {".java", ".kt"}):
        content = _read_safe(java_file)
        if content is None:
            continue

        # Check for @Entity annotation
        if "@Entity" not in content:
            continue

        # Find class name
        class_match = re.search(r'(?:public\s+)?class\s+(\w+)', content)
        if not class_match:
            continue
        class_name = class_match.group(1)

        # Extract @Table(name = "table_name")
        table_match = re.search(r'@Table\(\s*(?:name\s*=\s*)?["\'](\w+)["\']', content)
        table_name = table_match.group(1) if table_match else class_name.lower() + "s"

        # Extract fields with @Column or type annotations
        fields = []

        # Pattern: @Column(...) private Type fieldName;
        # Or: private Type fieldName;  (with @Id, etc. above)
        col_blocks = re.finditer(
            r'(?:(@(?:Id|Column|GeneratedValue|Enumerated|Lob|Temporal|Basic)[^\n]*\n\s*)*)'
            r'(?:private|protected|public)?\s+([\w<>,\s\[\]?]+?)\s+(\w+)\s*[;=]',
            content,
        )
        for col_match in col_blocks:
            annotations = col_match.group(1) or ""
            field_type = col_match.group(2).strip()
            field_name = col_match.group(3)

            # Skip common non-column fields
            if field_type in ("static", "final", "transient") or field_name.startswith("serial"):
                continue

            # Check @Column details
            col_detail = re.search(r'@Column\(([^)]*)\)', annotations)
            col_name = field_name
            nullable = True
            if col_detail:
                name_match = re.search(r'name\s*=\s*["\'](\w+)["\']', col_detail.group(1))
                if name_match:
                    col_name = name_match.group(1)
                if "nullable = false" in col_detail.group(1).lower() or "nullable=false" in col_detail.group(1).lower():
                    nullable = False

            if "@Id" in annotations:
                nullable = False

            fields.append({
                "name": col_name,
                "type": field_type,
                "nullable": nullable,
            })

        # Also try simpler field detection for Kotlin data classes
        if not fields and ".kt" in str(java_file):
            kt_field_pattern = r'(?:val|var)\s+(\w+)\s*:\s*([\w<>?,\s]+?)(?:\s*=|\s*,|\s*\))'
            for field_match in re.finditer(kt_field_pattern, content):
                field_name = field_match.group(1)
                field_type = field_match.group(2).strip()
                nullable = field_type.endswith("?")
                fields.append({
                    "name": _go_to_snake(field_name),
                    "type": field_type.rstrip("?"),
                    "nullable": nullable,
                })

        if fields:
            entities.append({
                "name": class_name,
                "table": table_name,
                "fields": fields,
                "module": str(java_file),
                "lang": "java/jpa",
            })

    return entities


# ---------------------------------------------------------------------------
# JS/TS scanners
# ---------------------------------------------------------------------------

def _scan_prisma(source_dirs: list[Path]) -> list[dict]:
    """Scan Prisma schema files (schema.prisma)."""
    entities = []

    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for prisma_file in source_dir.rglob("*.prisma"):
            content = _read_safe(prisma_file)
            if content is None:
                continue

            # Match model User { ... }
            model_pattern = r'model\s+(\w+)\s*\{([^}]+)\}'
            for model_match in re.finditer(model_pattern, content):
                model_name = model_match.group(1)
                model_body = model_match.group(2)

                # Extract @@map("table_name") for custom table names
                map_match = re.search(r'@@map\(\s*["\'](\w+)["\']', model_body)
                table_name = map_match.group(1) if map_match else model_name.lower() + "s"

                fields = []
                # field_name Type modifiers @attributes
                field_pattern = r'^\s+(\w+)\s+([\w\[\]?]+)(.*)$'
                for line in model_body.splitlines():
                    field_match = re.match(field_pattern, line)
                    if not field_match:
                        continue
                    field_name = field_match.group(1)
                    field_type = field_match.group(2)
                    modifiers = field_match.group(3)

                    # Skip relation fields and directives
                    if field_type[0].isupper() and field_type not in (
                        "String", "Int", "Float", "Boolean", "DateTime",
                        "BigInt", "Decimal", "Bytes", "Json",
                    ) and not field_type.endswith("[]"):
                        if "@relation" in modifiers:
                            continue

                    nullable = field_type.endswith("?")

                    # Check @map for column name
                    map_col = re.search(r'@map\(\s*["\'](\w+)["\']', modifiers)
                    col_name = map_col.group(1) if map_col else field_name

                    fields.append({
                        "name": col_name,
                        "type": field_type.rstrip("?").rstrip("[]"),
                        "nullable": nullable,
                    })

                if fields:
                    entities.append({
                        "name": model_name,
                        "table": table_name,
                        "fields": fields,
                        "module": str(prisma_file),
                        "lang": "prisma",
                    })

    return entities


def _scan_typeorm(source_dirs: list[Path]) -> list[dict]:
    """Scan TypeORM entity files with @Entity() and @Column() decorators."""
    entities = []

    for ts_file in _iter_files(source_dirs, {".ts"}):
        content = _read_safe(ts_file)
        if content is None:
            continue

        if "@Entity" not in content:
            continue

        # Extract class name
        class_match = re.search(r'@Entity\([^)]*\)\s*(?:export\s+)?class\s+(\w+)', content)
        if not class_match:
            continue
        class_name = class_match.group(1)

        # Extract table name from @Entity("table_name") or @Entity({ name: "table_name" })
        table_match = re.search(r'@Entity\(\s*["\'](\w+)["\']', content)
        if not table_match:
            table_match = re.search(r'@Entity\(\s*\{[^}]*name\s*:\s*["\'](\w+)["\']', content)
        table_name = table_match.group(1) if table_match else class_name.lower() + "s"

        fields = []
        # Match @Column() fieldName: type;
        col_pattern = r'@(?:Column|PrimaryGeneratedColumn|PrimaryColumn|CreateDateColumn|UpdateDateColumn)\([^)]*\)\s+(\w+)\s*(?:!?\s*:\s*([\w\[\]|<>,\s?]+))?'
        for col_match in re.finditer(col_pattern, content):
            field_name = col_match.group(1)
            field_type = (col_match.group(2) or "unknown").strip().rstrip(";")
            nullable = "| null" in field_type or field_type.endswith("?")
            fields.append({
                "name": field_name,
                "type": field_type.replace("| null", "").strip().rstrip("?"),
                "nullable": nullable,
            })

        if fields:
            entities.append({
                "name": class_name,
                "table": table_name,
                "fields": fields,
                "module": str(ts_file),
                "lang": "ts/typeorm",
            })

    return entities


def _scan_sequelize(source_dirs: list[Path]) -> list[dict]:
    """Scan Sequelize model definitions."""
    entities = []

    for ts_file in _iter_files(source_dirs, {".js", ".ts", ".mjs"}):
        content = _read_safe(ts_file)
        if content is None:
            continue

        # Match sequelize.define("ModelName", { ... }) or Model.init({ ... })
        define_pattern = r'(?:sequelize\.define|(\w+)\.init)\(\s*["\']?(\w+)["\']?\s*,\s*\{'
        for define_match in re.finditer(define_pattern, content):
            model_name = define_match.group(2) or define_match.group(1) or "Unknown"
            # Try to extract the fields block
            start = define_match.end()
            depth = 1
            pos = start
            while pos < len(content) and depth > 0:
                if content[pos] == '{':
                    depth += 1
                elif content[pos] == '}':
                    depth -= 1
                pos += 1
            fields_block = content[start:pos - 1]

            fields = []
            # Match fieldName: { type: DataTypes.STRING, allowNull: false }
            field_pattern = r'(\w+)\s*:\s*\{([^}]+)\}'
            for field_match in re.finditer(field_pattern, fields_block):
                field_name = field_match.group(1)
                field_body = field_match.group(2)

                type_match = re.search(r'type\s*:\s*DataTypes\.(\w+)', field_body)
                field_type = type_match.group(1) if type_match else "unknown"

                nullable = "allowNull: false" not in field_body.replace(" ", "")

                fields.append({
                    "name": field_name,
                    "type": field_type,
                    "nullable": nullable,
                })

            # Also match shorthand: fieldName: DataTypes.STRING
            shorthand_pattern = r'(\w+)\s*:\s*DataTypes\.(\w+)'
            for field_match in re.finditer(shorthand_pattern, fields_block):
                field_name = field_match.group(1)
                field_type = field_match.group(2)
                if not any(f["name"] == field_name for f in fields):
                    fields.append({
                        "name": field_name,
                        "type": field_type,
                        "nullable": True,
                    })

            if fields:
                entities.append({
                    "name": model_name,
                    "table": model_name.lower() + "s",
                    "fields": fields,
                    "module": str(ts_file),
                    "lang": "js/sequelize",
                })

    return entities


# ---------------------------------------------------------------------------
# Relationship detection (cross-language)
# ---------------------------------------------------------------------------

def _generate_entity_registry(
    entities: list[dict], relationships: list[dict],
) -> list[str]:
    """Generate YAML lines for evospec.yaml domain.entities section."""
    # Build relationship lookup: from_entity -> [(to_entity, type)]
    rel_map: dict[str, list[dict]] = {}
    for rel in relationships:
        rel_map.setdefault(rel["from"], []).append(rel)

    lines: list[str] = ["domain:", "  entities:"]

    for entity in entities:
        name = entity.get("name", "?")
        table = entity.get("table", "")
        fields = entity.get("fields", [])

        # Heuristic: entity is aggregate root if no FK fields point to it from itself
        # (simple: if it's not referenced by FK from another entity, assume aggregate root)
        has_fk_to_self = any(
            f["name"].endswith("_id") or f["name"].endswith("Id")
            for f in fields
            if f["name"] not in ("id",)
        )
        aggregate_root = not has_fk_to_self

        lines.append(f"    - name: \"{name}\"")
        lines.append(f"      context: \"\"  # TODO: assign to a bounded context")
        if table:
            lines.append(f"      table: \"{table}\"")
        lines.append(f"      aggregate_root: {'true' if aggregate_root else 'false'}")

        if fields:
            lines.append("      fields:")
            for field in fields:
                fname = field.get("name", "?")
                ftype = field.get("type", "?")
                lines.append(f"        - name: \"{fname}\"")
                lines.append(f"          type: \"{ftype}\"")

        entity_rels = rel_map.get(name, [])
        if entity_rels:
            lines.append("      relationships:")
            for rel in entity_rels:
                lines.append(f"        - target: \"{rel['to']}\"")
                lines.append(f"          type: \"many-to-one\"")

        lines.append("      invariants: []  # TODO: link invariant IDs")

    return lines


def _detect_relationships(entities: list[dict]) -> list[dict]:
    """Detect relationships between entities based on field naming conventions."""
    relationships = []
    entity_names = {e["name"].lower() for e in entities}

    for entity in entities:
        for field in entity.get("fields", []):
            fname = field["name"]
            # Check for foreign key patterns: xxx_id, xxxId, xxx_ID
            if fname.endswith("_id") or fname.endswith("_ID"):
                ref_name = fname[:-3].rstrip("_")
            elif fname.endswith("Id") and len(fname) > 2:
                ref_name = fname[:-2]
            else:
                continue

            ref_lower = ref_name.lower()
            if ref_lower in entity_names:
                relationships.append({
                    "from": entity["name"],
                    "to": ref_name.capitalize(),
                    "type": f"FK via {fname}",
                })

    return relationships
