"""Reverse-engineer cross-system dependencies from source code.

Scans source files for HTTP calls (fetch, axios, http.get, etc.) and maps them
to known backend endpoints declared in core/hybrid spec traceability sections.
This is the bridge between edge UX code and core backend contracts.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from rich.console import Console

from evospec.core.config import find_project_root, load_config, get_paths

console = Console()


def reverse_engineer_deps(source: str | None = None) -> None:
    """Scan source files for backend API calls and map to known specs."""
    root = find_project_root()
    if root is None:
        console.print("[red]✗ No evospec.yaml found. Run `evospec init` first.[/red]")
        return

    config = load_config(root)

    # Determine source directories
    if source:
        source_dirs = [root / source]
    else:
        cfg_dirs = config.get("reverse", {}).get("source_dirs", ["src"])
        source_dirs = [root / d for d in cfg_dirs]

    # Step 1: Collect all known endpoints from core/hybrid specs
    known_endpoints = _collect_known_endpoints(root, config)

    if not known_endpoints:
        console.print("[yellow]No endpoints found in core/hybrid specs. "
                       "Run `evospec reverse api` first and populate spec traceability.[/yellow]")
        return

    console.print(f"Loaded [bold]{len(known_endpoints)}[/bold] known endpoint(s) "
                  f"from core/hybrid specs.\n")

    # Step 2: Scan source files for HTTP calls
    calls = _scan_http_calls(source_dirs)

    if not calls:
        console.print("[yellow]No HTTP API calls found in source files.[/yellow]")
        return

    console.print(f"Found [bold]{len(calls)}[/bold] API call(s) in source code.\n")

    # Step 3: Match calls to known endpoints
    matched, unmatched = _match_calls_to_endpoints(calls, known_endpoints)

    # Step 4: Print results
    if matched:
        console.print("[bold green]Matched API calls → Core/Hybrid specs:[/bold green]\n")
        # Group by spec
        by_spec: dict[str, list[dict]] = {}
        for m in matched:
            by_spec.setdefault(m["spec_title"], []).append(m)

        for spec_title, spec_matches in by_spec.items():
            console.print(f"  [bold]{spec_title}[/bold] [dim]({spec_matches[0]['spec_zone']})[/dim]")
            for m in spec_matches:
                console.print(
                    f"    [green]✓[/green] {m['method']} {m['path']}"
                )
                console.print(
                    f"      [dim]← {m['source_file']}:{m['line']}[/dim]"
                )
            console.print()

    if unmatched:
        console.print("[bold yellow]Unmatched API calls (may need new backend work):[/bold yellow]\n")
        for u in unmatched:
            console.print(f"  [yellow]⚠[/yellow] {u['method']} {u['url']}")
            console.print(f"    [dim]← {u['source_file']}:{u['line']}[/dim]")
        console.print()

    # Summary
    console.print("─" * 50)
    total = len(matched) + len(unmatched)
    console.print(f"[bold]API dependencies: {total} total[/bold]")
    if matched:
        console.print(f"  [green]✓ {len(matched)} traced to core/hybrid specs[/green]")
    if unmatched:
        console.print(f"  [yellow]⚠ {len(unmatched)} unmatched (new backend work?)[/yellow]")
    console.print()
    console.print(
        "Use these findings to populate traceability.endpoints in your edge/hybrid spec.yaml."
    )


def _collect_known_endpoints(root: Path, config: dict) -> list[dict]:
    """Collect all endpoints from core/hybrid specs."""
    paths = get_paths(config)
    specs_root = root / paths["specs"]

    if not specs_root.exists():
        return []

    endpoints: list[dict] = []
    for spec_dir in sorted(specs_root.iterdir()):
        spec_yaml = spec_dir / "spec.yaml"
        if not spec_yaml.exists():
            continue
        spec = yaml.safe_load(spec_yaml.read_text()) or {}
        zone = spec.get("zone", "")
        if zone not in ("core", "hybrid"):
            continue

        title = spec.get("title", spec_dir.name)
        bc = spec.get("bounded_context", "")

        for ep in spec.get("traceability", {}).get("endpoints", []):
            ep = ep.strip()
            parts = ep.split(" ", 1)
            if len(parts) == 2:
                method = parts[0].upper()
                path = parts[1].strip()
            else:
                method = "ALL"
                path = parts[0].strip()

            endpoints.append({
                "method": method,
                "path": path,
                "spec_title": title,
                "spec_zone": zone,
                "bounded_context": bc,
            })

    return endpoints


def _scan_http_calls(source_dirs: list[Path]) -> list[dict]:
    """Scan source files for HTTP API calls."""
    calls: list[dict] = []
    extensions = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".mts", ".py", ".go", ".java", ".kt"}

    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for src_file in sorted(source_dir.rglob("*")):
            if src_file.suffix not in extensions:
                continue
            if not src_file.is_file():
                continue
            file_str = str(src_file)
            if any(skip in file_str for skip in [
                "node_modules", ".next", "dist/", "build/", "__pycache__", ".d.ts"
            ]):
                continue

            try:
                content = src_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue

            file_calls = []

            if src_file.suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".mts"}:
                file_calls.extend(_scan_js_http_calls(content, str(src_file)))
            elif src_file.suffix == ".py":
                file_calls.extend(_scan_python_http_calls(content, str(src_file)))
            elif src_file.suffix == ".go":
                file_calls.extend(_scan_go_http_calls(content, str(src_file)))
            elif src_file.suffix in {".java", ".kt"}:
                file_calls.extend(_scan_java_http_calls(content, str(src_file)))

            calls.extend(file_calls)

    return calls


def _scan_js_http_calls(content: str, file_path: str) -> list[dict]:
    """Scan JS/TS for fetch(), axios, and similar HTTP calls."""
    calls: list[dict] = []

    # fetch('url') or fetch(`url`) with template literals
    fetch_pattern = r'fetch\(\s*[`"\']([^`"\']+)[`"\']'
    for m in re.finditer(fetch_pattern, content):
        url = m.group(1)
        method = "GET"
        # Check if there's a method option nearby
        context = content[m.start():min(m.end() + 200, len(content))]
        method_match = re.search(r"method:\s*['\"](\w+)['\"]", context)
        if method_match:
            method = method_match.group(1).upper()
        calls.append({
            "url": url,
            "method": method,
            "source_file": file_path,
            "line": content[:m.start()].count("\n") + 1,
            "type": "fetch",
        })

    # fetch with template literal containing variables: `${BASE_URL}/api/...`
    fetch_template_pattern = r'fetch\(\s*`([^`]+)`'
    for m in re.finditer(fetch_template_pattern, content):
        url = m.group(1)
        # Already captured by simple pattern if no variables
        if "${" not in url:
            continue
        # Extract the path part after the variable
        path_match = re.search(r'\$\{[^}]+\}(/[^\s`"\']+)', url)
        if path_match:
            method = "GET"
            context = content[m.start():min(m.end() + 200, len(content))]
            method_match = re.search(r"method:\s*['\"](\w+)['\"]", context)
            if method_match:
                method = method_match.group(1).upper()
            calls.append({
                "url": path_match.group(1),
                "method": method,
                "source_file": file_path,
                "line": content[:m.start()].count("\n") + 1,
                "type": "fetch-template",
            })

    # axios.get/post/put/delete('url')
    axios_pattern = r'axios\.(\w+)\(\s*[`"\']([^`"\']+)[`"\']'
    for m in re.finditer(axios_pattern, content):
        method = m.group(1).upper()
        url = m.group(2)
        calls.append({
            "url": url,
            "method": method,
            "source_file": file_path,
            "line": content[:m.start()].count("\n") + 1,
            "type": "axios",
        })

    return calls


def _scan_python_http_calls(content: str, file_path: str) -> list[dict]:
    """Scan Python for requests.get/post/etc and httpx calls."""
    calls: list[dict] = []

    # requests.get/post/put/delete/patch("url")
    req_pattern = r'(?:requests|httpx|client|self\.client)\.(\w+)\(\s*[f]?["\']([^"\']+)["\']'
    for m in re.finditer(req_pattern, content):
        method = m.group(1).upper()
        url = m.group(2)
        if method in {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}:
            calls.append({
                "url": url,
                "method": method,
                "source_file": file_path,
                "line": content[:m.start()].count("\n") + 1,
                "type": "requests",
            })

    return calls


def _scan_go_http_calls(content: str, file_path: str) -> list[dict]:
    """Scan Go for http.Get/Post and similar calls."""
    calls: list[dict] = []

    # http.Get("url"), http.Post("url", ...)
    go_pattern = r'http\.(Get|Post|Head)\(\s*["`]([^"`]+)["`]'
    for m in re.finditer(go_pattern, content):
        calls.append({
            "url": m.group(2),
            "method": m.group(1).upper(),
            "source_file": file_path,
            "line": content[:m.start()].count("\n") + 1,
            "type": "net/http",
        })

    # http.NewRequest("METHOD", "url", ...)
    req_pattern = r'http\.NewRequest\(\s*["`](\w+)["`]\s*,\s*["`]([^"`]+)["`]'
    for m in re.finditer(req_pattern, content):
        calls.append({
            "url": m.group(2),
            "method": m.group(1).upper(),
            "source_file": file_path,
            "line": content[:m.start()].count("\n") + 1,
            "type": "net/http",
        })

    return calls


def _scan_java_http_calls(content: str, file_path: str) -> list[dict]:
    """Scan Java/Kotlin for RestTemplate, WebClient, and OkHttp calls."""
    calls: list[dict] = []

    # RestTemplate: restTemplate.getForObject("url", ...)
    rest_pattern = r'restTemplate\.(\w+)For\w+\(\s*["\']([^"\']+)["\']'
    for m in re.finditer(rest_pattern, content):
        calls.append({
            "url": m.group(2),
            "method": m.group(1).upper(),
            "source_file": file_path,
            "line": content[:m.start()].count("\n") + 1,
            "type": "RestTemplate",
        })

    # WebClient: .get().uri("url") or .post().uri("url")
    webclient_pattern = r'\.(get|post|put|delete|patch)\(\)\.uri\(\s*["\']([^"\']+)["\']'
    for m in re.finditer(webclient_pattern, content):
        calls.append({
            "url": m.group(2),
            "method": m.group(1).upper(),
            "source_file": file_path,
            "line": content[:m.start()].count("\n") + 1,
            "type": "WebClient",
        })

    return calls


def _match_calls_to_endpoints(
    calls: list[dict],
    known_endpoints: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Match detected HTTP calls to known backend endpoints."""
    matched: list[dict] = []
    unmatched: list[dict] = []

    for call in calls:
        call_url = call["url"]
        call_method = call["method"]

        # Normalize URL: extract path, resolve template variables
        call_path = _normalize_url_to_path(call_url)
        if not call_path:
            continue

        best_match = None
        for ep in known_endpoints:
            if _paths_match(call_path, ep["path"]):
                if ep["method"] == "ALL" or ep["method"] == call_method:
                    best_match = ep
                    break
                # Method mismatch but path matches — still a match
                if best_match is None:
                    best_match = ep

        if best_match:
            matched.append({
                "method": call_method,
                "path": best_match["path"],
                "url": call_url,
                "source_file": call["source_file"],
                "line": call["line"],
                "spec_title": best_match["spec_title"],
                "spec_zone": best_match["spec_zone"],
                "bounded_context": best_match["bounded_context"],
            })
        else:
            unmatched.append(call)

    return matched, unmatched


def _normalize_url_to_path(url: str) -> str | None:
    """Extract the API path from a URL, handling template variables."""
    # Remove protocol and host
    path = url
    if "://" in path:
        path = path.split("://", 1)[1]
        # Remove host:port
        if "/" in path:
            path = "/" + path.split("/", 1)[1]
        else:
            return None

    # Replace template variables: ${productId} → {productId}
    path = re.sub(r'\$\{(\w+)\}', r'{\1}', path)
    # Replace query strings
    path = path.split("?")[0]

    if not path.startswith("/"):
        return None

    return path


def _paths_match(call_path: str, spec_path: str) -> bool:
    """Check if a call path matches a spec endpoint path.

    Handles path parameter variations:
    - /api/orders/{orderId} matches /api/orders/{order_id}
    - /api/orders/123 matches /api/orders/{orderId}
    """
    # Split into segments
    call_parts = [p for p in call_path.split("/") if p]
    spec_parts = [p for p in spec_path.split("/") if p]

    if len(call_parts) != len(spec_parts):
        return False

    for cp, sp in zip(call_parts, spec_parts):
        # Both are path parameters
        if cp.startswith("{") and sp.startswith("{"):
            continue
        # Spec has a parameter, call has a literal value
        if sp.startswith("{") and not cp.startswith("{"):
            continue
        # Call has a template variable, spec has a parameter
        if cp.startswith("{") and sp.startswith("{"):
            continue
        # Both are literals — must match
        if cp.lower() != sp.lower():
            return False

    return True
