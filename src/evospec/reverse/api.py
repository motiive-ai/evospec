"""Reverse-engineer API endpoints into spec stubs."""

import ast
import re
from pathlib import Path

import yaml
from rich.console import Console

from evospec.core.config import find_project_root, load_config

console = Console()


def reverse_engineer_api(framework: str | None = None, source: str | None = None) -> None:
    """Scan source code for API endpoints and generate spec stubs."""
    root = find_project_root()
    if root is None:
        console.print("[red]✗ No evospec.yaml found. Run `evospec init` first.[/red]")
        return

    config = load_config(root)
    fw = framework or config.get("reverse", {}).get("framework", "")

    if not fw:
        console.print("[red]✗ No framework specified. Use --framework or set reverse.framework in evospec.yaml[/red]")
        return

    source_dirs = []
    if source:
        source_dirs = [root / source]
    else:
        configured = config.get("reverse", {}).get("source_dirs", [])
        source_dirs = [root / d for d in configured] if configured else [root]

    console.print(f"[bold]Scanning for {fw} endpoints...[/bold]")

    endpoints: list[dict[str, str]] = []

    if fw == "fastapi":
        endpoints = _scan_fastapi(source_dirs)
    elif fw == "django":
        endpoints = _scan_django(source_dirs)
    elif fw == "express":
        endpoints = _scan_express(source_dirs)
    else:
        console.print(f"[yellow]⚠ Framework '{fw}' scanning is basic. Results may be incomplete.[/yellow]")
        endpoints = _scan_generic(source_dirs)

    if not endpoints:
        console.print("[yellow]No endpoints found.[/yellow]")
        return

    console.print(f"\n[green]Found {len(endpoints)} endpoint(s):[/green]\n")
    for ep in endpoints:
        method = ep.get("method", "?").upper()
        path = ep.get("path", "?")
        func = ep.get("function", "?")
        module = ep.get("module", "?")
        console.print(f"  [cyan]{method:6s}[/cyan] {path}  [dim]→ {module}:{func}[/dim]")

    # Group by path prefix to suggest bounded contexts
    contexts = _suggest_contexts(endpoints)

    if contexts:
        console.print(f"\n[bold]Suggested bounded contexts:[/bold]\n")
        for ctx, eps in contexts.items():
            console.print(f"  [cyan]{ctx}[/cyan] ({len(eps)} endpoints)")

    console.print(
        f"\n[dim]Use these findings to populate traceability.endpoints in your spec.yaml files.[/dim]"
    )


def _scan_fastapi(source_dirs: list[Path]) -> list[dict[str, str]]:
    """Scan FastAPI source files for route decorators."""
    endpoints = []
    http_methods = {"get", "post", "put", "patch", "delete", "head", "options"}

    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for py_file in source_dir.rglob("*.py"):
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue

            # Match @router.get("/path") or @app.post("/path") patterns
            pattern = r'@\w+\.(' + '|'.join(http_methods) + r')\(\s*["\']([^"\']+)["\']'
            for match in re.finditer(pattern, content):
                method = match.group(1)
                path = match.group(2)

                # Try to find the function name (next def after decorator)
                remaining = content[match.end():]
                func_match = re.search(r'(?:async\s+)?def\s+(\w+)', remaining)
                func_name = func_match.group(1) if func_match else "unknown"

                endpoints.append({
                    "method": method,
                    "path": path,
                    "function": func_name,
                    "module": str(py_file),
                })
            
            # Match APIRouter prefix
            prefix_match = re.search(r'APIRouter\([^)]*prefix\s*=\s*["\']([^"\']+)["\']', content)
            if prefix_match:
                prefix = prefix_match.group(1)
                # Prepend prefix to endpoints from this file
                for ep in endpoints:
                    if ep["module"] == str(py_file) and not ep["path"].startswith(prefix):
                        ep["path"] = prefix + ep["path"]

    return endpoints


def _scan_django(source_dirs: list[Path]) -> list[dict[str, str]]:
    """Scan Django source files for URL patterns."""
    endpoints = []

    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for py_file in source_dir.rglob("*.py"):
            if "urls" not in py_file.stem:
                continue
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue

            # Match path("route", view) patterns
            pattern = r'path\(\s*["\']([^"\']*)["\']'
            for match in re.finditer(pattern, content):
                path = match.group(1)
                endpoints.append({
                    "method": "ALL",
                    "path": f"/{path}",
                    "function": "view",
                    "module": str(py_file),
                })

    return endpoints


def _scan_express(source_dirs: list[Path]) -> list[dict[str, str]]:
    """Scan Express.js source files for route definitions."""
    endpoints = []
    http_methods = {"get", "post", "put", "patch", "delete"}

    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for js_file in source_dir.rglob("*.{js,ts}"):
            try:
                content = js_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue

            pattern = r'\w+\.(' + '|'.join(http_methods) + r')\(\s*["\']([^"\']+)["\']'
            for match in re.finditer(pattern, content):
                method = match.group(1)
                path = match.group(2)
                endpoints.append({
                    "method": method,
                    "path": path,
                    "function": "handler",
                    "module": str(js_file),
                })

    return endpoints


def _scan_generic(source_dirs: list[Path]) -> list[dict[str, str]]:
    """Generic scan looking for common HTTP route patterns."""
    endpoints = []
    http_methods = {"get", "post", "put", "patch", "delete"}
    pattern = r'\.(' + '|'.join(http_methods) + r')\(\s*["\'/]([^"\']+)["\']'

    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for src_file in source_dir.rglob("*"):
            if src_file.suffix not in {".py", ".js", ".ts", ".rb", ".java", ".kt", ".go"}:
                continue
            try:
                content = src_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue

            for match in re.finditer(pattern, content):
                endpoints.append({
                    "method": match.group(1),
                    "path": match.group(2),
                    "function": "unknown",
                    "module": str(src_file),
                })

    return endpoints


def _suggest_contexts(endpoints: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    """Group endpoints by path prefix to suggest bounded contexts."""
    contexts: dict[str, list[dict[str, str]]] = {}

    for ep in endpoints:
        path = ep.get("path", "")
        parts = [p for p in path.split("/") if p and not p.startswith("{")]
        # Use first 2 non-param segments as context key
        if len(parts) >= 2:
            ctx = f"/{parts[0]}/{parts[1]}"
        elif len(parts) == 1:
            ctx = f"/{parts[0]}"
        else:
            ctx = "/"

        contexts.setdefault(ctx, []).append(ep)

    return contexts
