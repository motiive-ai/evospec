"""Verify spec accuracy against implementation code.

Five verification levels:
  1. Entity verification — spec fields vs code fields
  2. API contract verification — documented endpoints vs actual controllers
  3. Invariant verification — declared invariants have enforcement in code + tests
  4. Bounded context verification — spec contexts match code package structure
  5. Cross-spec consistency — same entity in multiple specs has consistent fields

Produces a verification score (0–100%) across all levels.

Key invariant: SYNC-002 — verify MUST produce deterministic results for the same codebase + specs.
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

from evospec.core.config import find_project_root, get_paths, load_config

console = Console()


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class EntityResult:
    entity: str
    status: str  # "match" | "partial" | "missing" | "extra"
    matched_fields: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    extra_fields: list[str] = field(default_factory=list)
    score: float = 0.0


@dataclass
class APIResult:
    endpoint: str
    status: str  # "documented" | "undocumented" | "stale"
    detail: str = ""


@dataclass
class InvariantResult:
    invariant_id: str
    statement: str
    has_enforcement: bool = False
    has_test: bool = False
    status: str = "unchecked"  # "enforced" | "partial" | "unenforced"


@dataclass
class ContextResult:
    context: str
    packages_found: list[str] = field(default_factory=list)
    status: str = "match"  # "match" | "mismatch" | "unverifiable"


@dataclass
class ConsistencyResult:
    entity: str
    specs: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    status: str = "consistent"  # "consistent" | "inconsistent"


@dataclass
class VerificationReport:
    entity_results: list[EntityResult] = field(default_factory=list)
    api_results: list[APIResult] = field(default_factory=list)
    invariant_results: list[InvariantResult] = field(default_factory=list)
    context_results: list[ContextResult] = field(default_factory=list)
    consistency_results: list[ConsistencyResult] = field(default_factory=list)
    entity_score: float = 0.0
    api_score: float = 0.0
    invariant_score: float = 0.0
    context_score: float = 0.0
    consistency_score: float = 0.0
    overall_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_verification": {
                "score": round(self.entity_score, 1),
                "results": [
                    {"entity": r.entity, "status": r.status, "score": round(r.score, 1),
                     "matched": r.matched_fields, "missing": r.missing_fields, "extra": r.extra_fields}
                    for r in self.entity_results
                ],
            },
            "api_verification": {
                "score": round(self.api_score, 1),
                "results": [
                    {"endpoint": r.endpoint, "status": r.status, "detail": r.detail}
                    for r in self.api_results
                ],
            },
            "invariant_verification": {
                "score": round(self.invariant_score, 1),
                "results": [
                    {"id": r.invariant_id, "statement": r.statement, "status": r.status,
                     "has_enforcement": r.has_enforcement, "has_test": r.has_test}
                    for r in self.invariant_results
                ],
            },
            "context_verification": {
                "score": round(self.context_score, 1),
                "results": [
                    {"context": r.context, "status": r.status, "packages": r.packages_found}
                    for r in self.context_results
                ],
            },
            "consistency_verification": {
                "score": round(self.consistency_score, 1),
                "results": [
                    {"entity": r.entity, "status": r.status, "specs": r.specs, "conflicts": r.conflicts}
                    for r in self.consistency_results
                ],
            },
            "overall_score": round(self.overall_score, 1),
        }

    def to_markdown(self) -> str:
        lines = [
            "# Verification Report",
            "",
            f"**Overall Score: {self.overall_score:.1f}%**",
            "",
        ]

        # Entity
        lines.append(f"## Entity Verification: {self.entity_score:.1f}%")
        lines.append("")
        if self.entity_results:
            total = len(self.entity_results)
            matched = sum(1 for r in self.entity_results if r.status == "match")
            lines.append(f"({matched}/{total} match)")
            lines.append("")
            for r in self.entity_results:
                icon = {"match": "✅", "partial": "⚠", "missing": "❌", "extra": "❌"}[r.status]
                lines.append(f"  {icon} {r.entity} — {r.status}")
                for mf in r.missing_fields:
                    lines.append(f"    - missing: {mf}")
                for ef in r.extra_fields:
                    lines.append(f"    - extra (not in spec): {ef}")
        else:
            lines.append("  (no entities to verify)")
        lines.append("")

        # API
        lines.append(f"## API Coverage: {self.api_score:.1f}%")
        lines.append("")
        if self.api_results:
            documented = sum(1 for r in self.api_results if r.status == "documented")
            total = len(self.api_results)
            lines.append(f"({documented}/{total} documented)")
            lines.append("")
            for r in self.api_results:
                icon = {"documented": "✅", "undocumented": "❌", "stale": "⚠"}[r.status]
                lines.append(f"  {icon} {r.endpoint} — {r.status}")
        else:
            lines.append("  (no endpoints to verify)")
        lines.append("")

        # Invariants
        lines.append(f"## Invariant Enforcement: {self.invariant_score:.1f}%")
        lines.append("")
        if self.invariant_results:
            enforced = sum(1 for r in self.invariant_results if r.status == "enforced")
            total = len(self.invariant_results)
            lines.append(f"({enforced}/{total} enforced)")
            lines.append("")
            for r in self.invariant_results:
                icon = {"enforced": "✅", "partial": "⚠", "unenforced": "❌", "unchecked": "?"}[r.status]
                lines.append(f"  {icon} {r.invariant_id} — {r.status}")
        else:
            lines.append("  (no invariants to verify)")
        lines.append("")

        # Overall
        lines.append(f"## Overall Score: {self.overall_score:.1f}%")
        lines.append("")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Level 1: Entity verification
# ---------------------------------------------------------------------------


def _verify_entities(
    entities: list[dict], source_files: list[Path],
) -> list[EntityResult]:
    """Check if spec entity fields match what's defined in code."""
    results: list[EntityResult] = []

    # Build a map of entity → fields from source code
    code_entities = _scan_code_entities(source_files)

    for ent in entities:
        name = ent.get("name", "")
        spec_fields = {f.get("name", "").lower() for f in ent.get("fields", []) if f.get("name")}

        # Find matching code entity (case-insensitive)
        code_fields = code_entities.get(name.lower(), set())

        if not code_fields:
            results.append(EntityResult(
                entity=name,
                status="missing",
                missing_fields=[],
                score=0.0,
            ))
            continue

        matched = spec_fields & code_fields
        missing_in_code = spec_fields - code_fields
        extra_in_code = code_fields - spec_fields

        # Filter out common ORM/framework noise
        noise = {"id", "created_at", "updated_at", "deleted_at", "meta", "objects", "pk", "table_name"}
        extra_in_code -= noise

        if not missing_in_code and not extra_in_code:
            status = "match"
            score = 100.0
        elif missing_in_code or extra_in_code:
            status = "partial"
            total = len(spec_fields | code_fields)
            score = (len(matched) / total * 100) if total else 0.0
        else:
            status = "match"
            score = 100.0

        results.append(EntityResult(
            entity=name,
            status=status,
            matched_fields=sorted(matched),
            missing_fields=sorted(missing_in_code),
            extra_fields=sorted(extra_in_code),
            score=score,
        ))

    return results


def _scan_code_entities(source_files: list[Path]) -> dict[str, set[str]]:
    """Scan source files for entity/model class definitions and their fields."""
    entities: dict[str, set[str]] = {}

    # Patterns for class definitions
    class_patterns = [
        # Python: class Foo(Base/Model)
        re.compile(r"class\s+(\w+)\s*\("),
        # Java/Kotlin: class Foo / data class Foo
        re.compile(r"(?:public\s+|data\s+)?class\s+(\w+)"),
        # Go: type Foo struct
        re.compile(r"type\s+(\w+)\s+struct"),
        # TS: class Foo / interface Foo
        re.compile(r"(?:export\s+)?(?:class|interface)\s+(\w+)"),
    ]

    # Patterns for field definitions
    field_patterns = [
        # Python: field = Column/Field/mapped_column
        re.compile(r"^\s+(\w+)\s*[=:]\s*(?:Column|Field|mapped_column|db\.Column)\("),
        re.compile(r"^\s+(\w+)\s*:\s*(?:Mapped|Optional|str|int|float|bool|list|List|UUID|datetime|Decimal)"),
        # Java: private Type field;
        re.compile(r"^\s+(?:private|protected|public)\s+\S+\s+(\w+)\s*[;=]"),
        # TS: field: type / readonly field: type
        re.compile(r"^\s+(?:readonly\s+)?(\w+)\s*[?]?\s*:\s*\w+"),
        # Go: Field Type `tag`
        re.compile(r'^\s+(\w+)\s+\w+\s*(?:`|$)'),
        # Prisma: field Type
        re.compile(r"^\s+(\w+)\s+(?:String|Int|Float|Boolean|DateTime|Json|Bytes|BigInt|Decimal)\b"),
    ]

    skip_names = {"self", "cls", "return", "class", "def", "import", "from", "if", "else",
                  "try", "except", "for", "while", "with", "pass", "break", "continue",
                  "super", "this", "new", "var", "let", "const", "func", "fn"}

    for fp in source_files:
        try:
            content = fp.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue

        current_class = ""
        brace_depth = 0

        for line in content.split("\n"):
            stripped = line.strip()

            # Track class definitions
            for cp in class_patterns:
                m = cp.search(stripped)
                if m:
                    current_class = m.group(1).lower()
                    entities.setdefault(current_class, set())
                    break

            if not current_class:
                continue

            # Track fields
            for fp_pat in field_patterns:
                m = fp_pat.match(line)
                if m:
                    field_name = m.group(1).lower()
                    if field_name not in skip_names and len(field_name) > 1:
                        entities[current_class].add(field_name)
                    break

    return entities


# ---------------------------------------------------------------------------
# Level 2: API contract verification
# ---------------------------------------------------------------------------


def _verify_api_endpoints(
    spec_endpoints: list[str], source_files: list[Path],
) -> list[APIResult]:
    """Check if documented API endpoints exist in source code."""
    results: list[APIResult] = []

    # Scan code for endpoint definitions
    code_endpoints = _scan_code_endpoints(source_files)
    code_normalized = {_normalize_path(ep) for ep in code_endpoints}
    spec_normalized = {_normalize_path(ep): ep for ep in spec_endpoints}

    # Check documented endpoints
    for norm, original in spec_normalized.items():
        if norm in code_normalized:
            results.append(APIResult(endpoint=original, status="documented"))
        else:
            results.append(APIResult(
                endpoint=original,
                status="stale",
                detail="Documented in spec but not found in code",
            ))

    # Check undocumented endpoints
    for ep in code_endpoints:
        norm = _normalize_path(ep)
        if norm not in spec_normalized:
            results.append(APIResult(
                endpoint=ep,
                status="undocumented",
                detail="Found in code but not documented in spec",
            ))

    return results


def _scan_code_endpoints(source_files: list[Path]) -> list[str]:
    """Scan source files for API endpoint definitions."""
    endpoints: list[str] = []
    patterns = [
        re.compile(r'@\w+\.(?:get|post|put|patch|delete)\(\s*["\']([^"\']+)["\']'),
        re.compile(r'@(?:Get|Post|Put|Patch|Delete|Request)Mapping\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'),
        re.compile(r'\.(?:get|post|put|patch|delete)\(\s*["\']([^"\']+)["\']'),
        re.compile(r'\.(?:GET|POST|PUT|PATCH|DELETE|Handle|HandleFunc)\(\s*["\']([^"\']+)["\']'),
    ]

    for fp in source_files:
        try:
            content = fp.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue

        for line in content.split("\n"):
            for pattern in patterns:
                m = pattern.search(line)
                if m:
                    endpoints.append(m.group(1))
                    break

    return endpoints


def _normalize_path(endpoint: str) -> str:
    """Normalize endpoint path for comparison."""
    ep = re.sub(r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+", "", endpoint.strip())
    ep = re.sub(r"\{[^}]+\}", "{*}", ep)
    return ep.lower().rstrip("/")


# ---------------------------------------------------------------------------
# Level 3: Invariant verification
# ---------------------------------------------------------------------------


def _verify_invariants(
    invariants: list[dict], source_files: list[Path], test_files: list[Path],
) -> list[InvariantResult]:
    """Check if declared invariants have enforcement in code + tests."""
    results: list[InvariantResult] = []

    # Build searchable content from source and test files
    source_content = _read_all_content(source_files)
    test_content = _read_all_content(test_files)

    for inv in invariants:
        inv_id = inv.get("id", "?")
        statement = inv.get("statement", "")
        enforcement = inv.get("enforcement", "")

        # Search for invariant ID in code (guard clauses, validation, etc.)
        has_enforcement = inv_id.lower() in source_content.lower()
        # Also search for keywords from the statement
        if not has_enforcement:
            keywords = _extract_keywords(statement)
            if keywords:
                # At least 2 keywords must appear together in source
                matches = sum(1 for kw in keywords if kw in source_content.lower())
                has_enforcement = matches >= min(2, len(keywords))

        # Search for invariant ID in tests
        has_test = inv_id.lower() in test_content.lower()
        if not has_test:
            # Check if enforcement type has matching test patterns
            if enforcement in ("test", "unit-test", "integration-test"):
                keywords = _extract_keywords(statement)
                matches = sum(1 for kw in keywords if kw in test_content.lower())
                has_test = matches >= min(2, len(keywords))

        if has_enforcement and has_test:
            status = "enforced"
        elif has_enforcement or has_test:
            status = "partial"
        else:
            status = "unenforced"

        results.append(InvariantResult(
            invariant_id=inv_id,
            statement=statement,
            has_enforcement=has_enforcement,
            has_test=has_test,
            status=status,
        ))

    return results


# ---------------------------------------------------------------------------
# Level 4: Bounded context verification
# ---------------------------------------------------------------------------


def _verify_contexts(
    contexts: list[dict], source_root: Path,
) -> list[ContextResult]:
    """Check if declared bounded contexts match code package structure."""
    results: list[ContextResult] = []

    if not source_root.exists():
        return results

    # Get all package/directory names from source
    packages: set[str] = set()
    for p in source_root.rglob("*"):
        if p.is_dir() and not p.name.startswith(".") and p.name != "__pycache__":
            packages.add(p.name.lower())
        elif p.is_file() and p.suffix in (".py", ".java", ".kt", ".go", ".ts", ".js"):
            packages.add(p.stem.lower())

    for ctx in contexts:
        name = ctx.get("name", "")
        name_lower = name.lower()
        # Check for matching package/directory
        found = [
            pkg for pkg in packages
            if name_lower in pkg or pkg in name_lower
        ]

        if found:
            results.append(ContextResult(
                context=name,
                packages_found=sorted(found[:5]),
                status="match",
            ))
        else:
            results.append(ContextResult(
                context=name,
                status="mismatch",
            ))

    return results


# ---------------------------------------------------------------------------
# Level 5: Cross-spec consistency
# ---------------------------------------------------------------------------


def _verify_consistency(
    root: Path, config: dict,
) -> list[ConsistencyResult]:
    """Check if the same entity in multiple specs has consistent fields."""
    results: list[ConsistencyResult] = []
    paths_cfg = get_paths(config)
    specs_dir = root / paths_cfg["specs"]

    if not specs_dir.exists():
        return results

    # Collect entity definitions from all specs
    entity_specs: dict[str, list[tuple[str, set[str]]]] = {}

    for spec_dir in sorted(specs_dir.iterdir()):
        spec_yaml = spec_dir / "spec.yaml"
        if not spec_yaml.exists():
            continue
        spec = yaml.safe_load(spec_yaml.read_text()) or {}
        title = spec.get("title", spec_dir.name)

        # Get entities from traceability tables
        for table in spec.get("traceability", {}).get("tables", []):
            entity_specs.setdefault(table.lower(), []).append((title, set()))

    # Also compare domain entity fields across upstreams
    upstreams = config.get("_upstreams", {})
    for up_name, up_data in upstreams.items():
        for ent in up_data.get("entities", []):
            name = ent.get("name", "").lower()
            fields = {f.get("name", "").lower() for f in ent.get("fields", []) if f.get("name")}
            entity_specs.setdefault(name, []).append((f"upstream:{up_name}", fields))

    # Local entities
    for ent in config.get("domain", {}).get("entities", []):
        name = ent.get("name", "").lower()
        fields = {f.get("name", "").lower() for f in ent.get("fields", []) if f.get("name")}
        entity_specs.setdefault(name, []).append(("local", fields))

    # Check for inconsistencies
    for entity_name, specs_list in entity_specs.items():
        if len(specs_list) <= 1:
            continue

        spec_names = [s[0] for s in specs_list]
        field_sets = [s[1] for s in specs_list if s[1]]  # skip empty sets

        if len(field_sets) <= 1:
            results.append(ConsistencyResult(
                entity=entity_name,
                specs=spec_names,
                status="consistent",
            ))
            continue

        # Check if all field sets are equal
        conflicts = []
        base = field_sets[0]
        for i, fs in enumerate(field_sets[1:], 1):
            diff = base.symmetric_difference(fs)
            if diff:
                conflicts.append(f"{spec_names[0]} vs {spec_names[i]}: {', '.join(sorted(diff))}")

        results.append(ConsistencyResult(
            entity=entity_name,
            specs=spec_names,
            conflicts=conflicts,
            status="inconsistent" if conflicts else "consistent",
        ))

    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_all_content(files: list[Path]) -> str:
    """Read all files into a single string for searching."""
    parts = []
    for f in files:
        try:
            parts.append(f.read_text(errors="ignore"))
        except OSError:
            continue
    return "\n".join(parts)


def _extract_keywords(statement: str) -> list[str]:
    """Extract meaningful keywords from an invariant statement."""
    stop_words = {
        "the", "a", "an", "is", "must", "be", "to", "in", "of", "for", "and", "or",
        "not", "every", "all", "each", "by", "with", "from", "that", "this", "should",
        "can", "will", "have", "has", "at", "least", "one", "before", "after", "same",
        "its", "it", "than", "may", "no", "any", "only",
    }
    words = re.findall(r"[a-zA-Z_]\w+", statement.lower())
    return [w for w in words if w not in stop_words and len(w) > 2]


def _collect_source_files(root: Path) -> list[Path]:
    """Collect all source files in the project."""
    source_extensions = {".py", ".java", ".kt", ".go", ".ts", ".tsx", ".js", ".jsx"}
    files = []
    for ext in source_extensions:
        files.extend(root.rglob(f"*{ext}"))
    # Filter out common non-source dirs
    return [
        f for f in files
        if "node_modules" not in f.parts
        and ".git" not in f.parts
        and "__pycache__" not in f.parts
        and "venv" not in f.parts
        and ".venv" not in f.parts
    ]


def _collect_test_files(root: Path) -> list[Path]:
    """Collect test files."""
    files = []
    for pattern in ["tests/**/*.py", "test/**/*.py", "**/*_test.py", "**/*_test.go",
                     "**/*.test.ts", "**/*.test.js", "**/*.spec.ts", "**/*.spec.js",
                     "**/Test*.java", "**/*Test.java"]:
        files.extend(root.glob(pattern))
    return files


def _calculate_level_score(results: list, pass_key: str, pass_values: set[str]) -> float:
    """Calculate a score for a verification level."""
    if not results:
        return 100.0  # Nothing to verify = perfect
    passed = sum(1 for r in results if getattr(r, pass_key) in pass_values)
    return (passed / len(results)) * 100


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_verify(
    *,
    strict: bool = False,
    output_format: str = "text",
) -> VerificationReport:
    """Run spec verification against implementation.

    Args:
        strict: If True, exit non-zero on any failure (for CI gates).
        output_format: "text" | "json" | "markdown"

    Returns:
        VerificationReport with scores across all levels.
    """
    root = find_project_root()
    if root is None:
        console.print("[red]ERROR:[/] No evospec.yaml found. Run `evospec init` first.")
        return VerificationReport()

    config = load_config(root)
    entities = config.get("domain", {}).get("entities", [])
    contexts = config.get("bounded_contexts", [])
    if isinstance(contexts, dict):
        contexts = []

    # Collect endpoints from API contracts and spec traceability
    spec_endpoints = _collect_spec_endpoints(config, root)

    # Collect invariants
    invariants = _collect_invariants(root, config)

    # Collect source and test files
    source_files = _collect_source_files(root)
    test_files = _collect_test_files(root)

    # Determine source root (for context verification)
    source_root = root / "src"
    if not source_root.exists():
        source_root = root

    # Run all verification levels
    entity_results = _verify_entities(entities, source_files)
    api_results = _verify_api_endpoints(spec_endpoints, source_files)
    invariant_results = _verify_invariants(invariants, source_files, test_files)
    context_results = _verify_contexts(contexts, source_root)
    consistency_results = _verify_consistency(root, config)

    # Calculate scores
    entity_score = _calculate_level_score(entity_results, "status", {"match"})
    api_score = _calculate_level_score(api_results, "status", {"documented"})
    invariant_score = _calculate_level_score(invariant_results, "status", {"enforced"})
    context_score = _calculate_level_score(context_results, "status", {"match"})
    consistency_score = _calculate_level_score(consistency_results, "status", {"consistent"})

    # Weighted overall score
    weights = {"entity": 30, "api": 25, "invariant": 25, "context": 10, "consistency": 10}
    scores = {
        "entity": entity_score,
        "api": api_score,
        "invariant": invariant_score,
        "context": context_score,
        "consistency": consistency_score,
    }
    total_weight = sum(weights.values())
    overall = sum(scores[k] * weights[k] for k in weights) / total_weight

    report = VerificationReport(
        entity_results=entity_results,
        api_results=api_results,
        invariant_results=invariant_results,
        context_results=context_results,
        consistency_results=consistency_results,
        entity_score=entity_score,
        api_score=api_score,
        invariant_score=invariant_score,
        context_score=context_score,
        consistency_score=consistency_score,
        overall_score=overall,
    )

    # Output
    if output_format == "json":
        console.print(json.dumps(report.to_dict(), indent=2))
    elif output_format == "markdown":
        console.print(report.to_markdown())
    else:
        _print_report(report)

    # Strict mode: check thresholds
    if strict:
        thresholds = config.get("verification", {})
        min_overall = thresholds.get("min_overall_score", 0)
        min_entity = thresholds.get("min_entity_score", 0)
        min_api = thresholds.get("min_api_score", 0)

        failures = []
        if overall < min_overall:
            failures.append(f"Overall score {overall:.1f}% < minimum {min_overall}%")
        if entity_score < min_entity:
            failures.append(f"Entity score {entity_score:.1f}% < minimum {min_entity}%")
        if api_score < min_api:
            failures.append(f"API score {api_score:.1f}% < minimum {min_api}%")

        if failures:
            console.print()
            for f in failures:
                console.print(f"[red]FAIL:[/] {f}")
            raise SystemExit(1)

    return report


def _collect_spec_endpoints(config: dict, root: Path) -> list[str]:
    """Collect all documented endpoints from API contracts + spec traceability."""
    endpoints: list[str] = []

    # From api-contracts.yaml
    contracts = config.get("api_contracts", {})
    if isinstance(contracts, dict):
        for c in contracts.get("contracts", []):
            ep = c.get("endpoint", "")
            if ep:
                endpoints.append(ep)

    # From spec traceability
    paths_cfg = get_paths(config)
    specs_dir = root / paths_cfg["specs"]
    if specs_dir.exists():
        for spec_dir in sorted(specs_dir.iterdir()):
            spec_yaml = spec_dir / "spec.yaml"
            if not spec_yaml.exists():
                continue
            spec = yaml.safe_load(spec_yaml.read_text()) or {}
            for ep in spec.get("traceability", {}).get("endpoints", []):
                if ep not in endpoints:
                    endpoints.append(ep)

    return endpoints


def _collect_invariants(root: Path, config: dict) -> list[dict]:
    """Collect all invariants from core/hybrid specs."""
    paths_cfg = get_paths(config)
    specs_dir = root / paths_cfg["specs"]
    if not specs_dir.exists():
        return []

    invariants: list[dict] = []
    for spec_dir in sorted(specs_dir.iterdir()):
        spec_yaml = spec_dir / "spec.yaml"
        if not spec_yaml.exists():
            continue
        spec = yaml.safe_load(spec_yaml.read_text()) or {}
        zone = spec.get("zone", "")
        if zone not in ("core", "hybrid"):
            continue
        for inv in spec.get("invariants", []):
            invariants.append(inv)

    return invariants


def _print_report(report: VerificationReport) -> None:
    """Print human-readable verification report."""
    console.print()

    # Entity verification
    total_ent = len(report.entity_results)
    matched_ent = sum(1 for r in report.entity_results if r.status == "match")
    console.print(f"[bold]Entity verification: {report.entity_score:.0f}%[/] ({matched_ent}/{total_ent} match)")
    for r in report.entity_results:
        icon = {"match": "✅", "partial": "⚠", "missing": "❌", "extra": "❌"}[r.status]
        console.print(f"  {icon} {r.entity} — {r.status}")
        for mf in r.missing_fields:
            console.print(f"    [red]- missing: {mf}[/]")
        for ef in r.extra_fields:
            console.print(f"    [yellow]- extra: {ef}[/]")
    console.print()

    # API verification
    total_api = len(report.api_results)
    documented = sum(1 for r in report.api_results if r.status == "documented")
    undocumented = sum(1 for r in report.api_results if r.status == "undocumented")
    console.print(f"[bold]API coverage: {report.api_score:.0f}%[/] ({documented}/{total_api} documented)")
    if undocumented:
        console.print(f"  [red]❌ {undocumented} undocumented endpoint(s)[/]")
    for r in report.api_results:
        if r.status != "documented":
            icon = {"undocumented": "❌", "stale": "⚠"}[r.status]
            console.print(f"  {icon} {r.endpoint} — {r.detail}")
    console.print()

    # Invariant verification
    total_inv = len(report.invariant_results)
    enforced = sum(1 for r in report.invariant_results if r.status == "enforced")
    console.print(f"[bold]Invariant enforcement: {report.invariant_score:.0f}%[/] ({enforced}/{total_inv})")
    for r in report.invariant_results:
        if r.status != "enforced":
            icon = {"partial": "⚠", "unenforced": "❌", "unchecked": "?"}[r.status]
            console.print(f"  {icon} {r.invariant_id} — {r.status} (code: {r.has_enforcement}, test: {r.has_test})")
    console.print()

    # Overall
    console.print(f"[bold]Overall score: {report.overall_score:.0f}%[/]")
