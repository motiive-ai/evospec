"""Reverse-engineer API endpoints into spec stubs."""

import re
from pathlib import Path

from rich.console import Console

from evospec.core.config import find_project_root, load_config

console = Console()

# Supported frameworks by language
SUPPORTED_FRAMEWORKS = {
    "python": ["fastapi", "django", "flask"],
    "go": ["gin", "echo", "fiber", "chi", "gorilla", "net-http"],
    "java": ["spring"],
    "js": ["express", "nextjs", "nestjs", "hono", "fastify"],
}

ALL_FRAMEWORKS = sorted(
    fw for fws in SUPPORTED_FRAMEWORKS.values() for fw in fws
)


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


def reverse_engineer_api(
    framework: str | None = None,
    source: str | None = None,
    deep: bool = False,
    write: bool = False,
) -> None:
    """Scan source code for API endpoints and generate spec stubs."""
    root = find_project_root()
    if root is None:
        console.print("[red]✗ No evospec.yaml found. Run `evospec init` first.[/red]")
        return

    if write and not deep:
        console.print("[yellow]⚠ --write requires --deep. Running shallow scan.[/yellow]")
        write = False

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

    mode = "[bold magenta]deep[/bold magenta] " if deep else ""
    console.print(f"[bold]Scanning for {fw} endpoints ({mode}scan)...[/bold]")

    endpoints: list[dict[str, str]] = []

    # --- Python frameworks ---
    if fw == "fastapi":
        endpoints = _scan_fastapi(source_dirs)
    elif fw == "django":
        endpoints = _scan_django(source_dirs)
    elif fw == "flask":
        endpoints = _scan_flask(source_dirs)
    # --- Go frameworks ---
    elif fw == "gin":
        endpoints = _scan_gin(source_dirs)
    elif fw == "echo":
        endpoints = _scan_echo(source_dirs)
    elif fw in ("fiber", "chi", "gorilla", "net-http"):
        endpoints = _scan_go_generic(source_dirs, fw)
    # --- Java frameworks ---
    elif fw == "spring":
        endpoints = _scan_spring(source_dirs)
    # --- JS/TS frameworks ---
    elif fw == "express":
        endpoints = _scan_express(source_dirs)
    elif fw == "nextjs":
        endpoints = _scan_nextjs(source_dirs)
    elif fw == "nestjs":
        endpoints = _scan_nestjs(source_dirs)
    elif fw in ("hono", "fastify"):
        endpoints = _scan_express(source_dirs)  # similar pattern
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

    # Deep extraction: walk DTOs, extract schemas, detect auth/errors
    deep_contracts: list[dict] = []
    if deep:
        console.print(f"\n[bold magenta]Deep extraction:[/bold magenta]")
        deep_contracts = _deep_extract_api(endpoints, source_dirs, fw)
        if deep_contracts:
            console.print(f"  [green]✓[/green] Extracted schemas for {len(deep_contracts)} endpoint(s)")
            for dc in deep_contracts:
                ep = dc.get("endpoint", "?")
                req_fields = len(dc.get("request", {}).get("fields", []))
                resp_fields = sum(
                    len(r.get("fields", [])) for r in dc.get("response", {}).values()
                )
                auth = dc.get("auth", "")
                parts = []
                if req_fields:
                    parts.append(f"{req_fields} request fields")
                if resp_fields:
                    parts.append(f"{resp_fields} response fields")
                if auth:
                    parts.append(f"auth: {auth}")
                detail = ", ".join(parts) if parts else "no schema details"
                console.print(f"    {ep} — {detail}")
        else:
            console.print("  [yellow]⚠ No deep schema details extracted.[/yellow]")

    # Group by path prefix to suggest bounded contexts
    contexts = _suggest_contexts(endpoints)

    if contexts:
        console.print(f"\n[bold]Suggested bounded contexts:[/bold]\n")
        for ctx, eps in contexts.items():
            console.print(f"  [cyan]{ctx}[/cyan] ({len(eps)} endpoints)")

    # Write to api-contracts.yaml if --write
    if write and deep_contracts:
        _write_api_contracts(root, config, deep_contracts)

    console.print(
        f"\n[dim]Use these findings to populate traceability.endpoints in your spec.yaml files.[/dim]"
    )


# ---------------------------------------------------------------------------
# Python scanners
# ---------------------------------------------------------------------------

def _scan_fastapi(source_dirs: list[Path]) -> list[dict[str, str]]:
    """Scan FastAPI source files for route decorators."""
    endpoints: list[dict[str, str]] = []
    http_methods = {"get", "post", "put", "patch", "delete", "head", "options"}

    for py_file in _iter_files(source_dirs, {".py"}):
        content = _read_safe(py_file)
        if content is None:
            continue

        # Match @router.get("/path") or @app.post("/path") patterns
        pattern = r'@\w+\.(' + '|'.join(http_methods) + r')\(\s*["\']([^"\']+)["\']'
        for match in re.finditer(pattern, content):
            method = match.group(1)
            path = match.group(2)

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
            for ep in endpoints:
                if ep["module"] == str(py_file) and not ep["path"].startswith(prefix):
                    ep["path"] = prefix + ep["path"]

    return endpoints


def _scan_django(source_dirs: list[Path]) -> list[dict[str, str]]:
    """Scan Django source files for URL patterns."""
    endpoints: list[dict[str, str]] = []

    for py_file in _iter_files(source_dirs, {".py"}):
        if "urls" not in py_file.stem:
            continue
        content = _read_safe(py_file)
        if content is None:
            continue

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


def _scan_flask(source_dirs: list[Path]) -> list[dict[str, str]]:
    """Scan Flask source files for @app.route / @bp.route decorators."""
    endpoints: list[dict[str, str]] = []
    http_methods_set = {"get", "post", "put", "patch", "delete", "head", "options"}

    for py_file in _iter_files(source_dirs, {".py"}):
        content = _read_safe(py_file)
        if content is None:
            continue

        # @app.route("/path", methods=["GET", "POST"]) or @bp.route(...)
        route_pattern = r'@\w+\.route\(\s*["\']([^"\']+)["\'](?:[^)]*methods\s*=\s*\[([^\]]*)\])?'
        for match in re.finditer(route_pattern, content):
            path = match.group(1)
            methods_str = match.group(2) or '"GET"'
            methods = re.findall(r'["\'](\w+)["\']', methods_str)

            remaining = content[match.end():]
            func_match = re.search(r'(?:async\s+)?def\s+(\w+)', remaining)
            func_name = func_match.group(1) if func_match else "unknown"

            for method in methods:
                if method.lower() in http_methods_set:
                    endpoints.append({
                        "method": method.lower(),
                        "path": path,
                        "function": func_name,
                        "module": str(py_file),
                    })

        # Also match @app.get("/path"), @app.post("/path") style (Flask 2.0+)
        method_pattern = r'@\w+\.(' + '|'.join(http_methods_set) + r')\(\s*["\']([^"\']+)["\']'
        for match in re.finditer(method_pattern, content):
            method = match.group(1)
            path = match.group(2)

            remaining = content[match.end():]
            func_match = re.search(r'(?:async\s+)?def\s+(\w+)', remaining)
            func_name = func_match.group(1) if func_match else "unknown"

            endpoints.append({
                "method": method,
                "path": path,
                "function": func_name,
                "module": str(py_file),
            })

    return endpoints


# ---------------------------------------------------------------------------
# Go scanners
# ---------------------------------------------------------------------------

def _scan_gin(source_dirs: list[Path]) -> list[dict[str, str]]:
    """Scan Go Gin source files for route definitions."""
    endpoints: list[dict[str, str]] = []
    http_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}

    for go_file in _iter_files(source_dirs, {".go"}):
        content = _read_safe(go_file)
        if content is None:
            continue

        # Match r.GET("/path", handler) or group.POST("/path", handler)
        pattern = r'(\w+)\.(' + '|'.join(http_methods) + r')\(\s*["`]([^"`]+)["`]\s*,\s*(\w[\w.]*)'
        for match in re.finditer(pattern, content):
            method = match.group(2)
            path = match.group(3)
            handler = match.group(4)
            endpoints.append({
                "method": method.lower(),
                "path": path,
                "function": handler,
                "module": str(go_file),
            })

        # Match router.Group("/prefix")
        group_pattern = r'(\w+)\s*(?::=|=)\s*\w+\.Group\(\s*["`]([^"`]+)["`]'
        groups: dict[str, str] = {}
        for match in re.finditer(group_pattern, content):
            groups[match.group(1)] = match.group(2)

        # Prepend group prefixes
        for ep in endpoints:
            if ep["module"] == str(go_file):
                for group_var, prefix in groups.items():
                    if prefix and not ep["path"].startswith(prefix):
                        # Check if the route was registered on this group
                        route_pattern = rf'{re.escape(group_var)}\.(?:GET|POST|PUT|PATCH|DELETE)\(\s*["`]{re.escape(ep["path"])}["`]'
                        if re.search(route_pattern, content):
                            ep["path"] = prefix.rstrip("/") + ep["path"]

    return endpoints


def _scan_echo(source_dirs: list[Path]) -> list[dict[str, str]]:
    """Scan Go Echo source files for route definitions."""
    endpoints: list[dict[str, str]] = []
    http_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}

    for go_file in _iter_files(source_dirs, {".go"}):
        content = _read_safe(go_file)
        if content is None:
            continue

        # Match e.GET("/path", handler) or g.POST("/path", handler)
        pattern = r'(\w+)\.(' + '|'.join(http_methods) + r')\(\s*["`]([^"`]+)["`]\s*,\s*(\w[\w.]*)'
        for match in re.finditer(pattern, content):
            endpoints.append({
                "method": match.group(2).lower(),
                "path": match.group(3),
                "function": match.group(4),
                "module": str(go_file),
            })

    return endpoints


def _scan_go_generic(source_dirs: list[Path], fw: str) -> list[dict[str, str]]:
    """Scan Go source files for common HTTP route patterns (fiber, chi, gorilla, net/http)."""
    endpoints: list[dict[str, str]] = []

    for go_file in _iter_files(source_dirs, {".go"}):
        content = _read_safe(go_file)
        if content is None:
            continue

        # net/http: http.HandleFunc("/path", handler) or mux.HandleFunc("/path", handler)
        hf_pattern = r'(?:http\.HandleFunc|(\w+)\.HandleFunc)\(\s*["`]([^"`]+)["`]\s*,\s*(\w[\w.]*)'
        for match in re.finditer(hf_pattern, content):
            endpoints.append({
                "method": "ALL",
                "path": match.group(2),
                "function": match.group(3),
                "module": str(go_file),
            })

        # chi / gorilla: r.Get("/path", handler), r.Post(...)
        chi_pattern = r'(\w+)\.(Get|Post|Put|Patch|Delete|Head|Options)\(\s*["`]([^"`]+)["`]\s*,\s*(\w[\w.]*)'
        for match in re.finditer(chi_pattern, content):
            endpoints.append({
                "method": match.group(2).lower(),
                "path": match.group(3),
                "function": match.group(4),
                "module": str(go_file),
            })

        # chi: r.Route("/prefix", func(r chi.Router) { ... })
        route_pattern = r'(\w+)\.Route\(\s*["`]([^"`]+)["`]'
        for match in re.finditer(route_pattern, content):
            endpoints.append({
                "method": "GROUP",
                "path": match.group(2),
                "function": "subrouter",
                "module": str(go_file),
            })

        # fiber: app.Get("/path", handler)
        fiber_pattern = r'(\w+)\.(Get|Post|Put|Patch|Delete|Head|Options|All)\(\s*["`]([^"`]+)["`]\s*,\s*(\w[\w.]*)'
        for match in re.finditer(fiber_pattern, content):
            if match.group(0) not in [m.group(0) for m in re.finditer(chi_pattern, content)]:
                endpoints.append({
                    "method": match.group(2).lower(),
                    "path": match.group(3),
                    "function": match.group(4),
                    "module": str(go_file),
                })

    return endpoints


# ---------------------------------------------------------------------------
# Java scanners
# ---------------------------------------------------------------------------

def _scan_spring(source_dirs: list[Path]) -> list[dict[str, str]]:
    """Scan Spring Boot source files for @RequestMapping, @GetMapping, etc."""
    endpoints: list[dict[str, str]] = []

    method_annotations = {
        "GetMapping": "GET",
        "PostMapping": "POST",
        "PutMapping": "PUT",
        "PatchMapping": "PATCH",
        "DeleteMapping": "DELETE",
    }

    for java_file in _iter_files(source_dirs, {".java", ".kt"}):
        content = _read_safe(java_file)
        if content is None:
            continue

        # Extract class-level @RequestMapping prefix
        class_prefix = ""
        class_rm = re.search(
            r'@RequestMapping\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']',
            content,
        )
        if class_rm:
            class_prefix = class_rm.group(1).rstrip("/")

        # Detect @RequestMapping(value="/path", method=RequestMethod.GET)
        rm_pattern = (
            r'@RequestMapping\(\s*'
            r'(?:value\s*=\s*)?["\']([^"\']+)["\']'
            r'(?:\s*,\s*method\s*=\s*RequestMethod\.(\w+))?'
        )
        for match in re.finditer(rm_pattern, content):
            path = match.group(1)
            method = match.group(2) or "ALL"
            func_name = _java_next_method(content, match.end())
            full_path = class_prefix + path if not path.startswith(class_prefix) else path
            endpoints.append({
                "method": method.lower(),
                "path": full_path,
                "function": func_name,
                "module": str(java_file),
            })

        # Detect @GetMapping("/path"), @PostMapping("/path"), etc.
        for annotation, http_method in method_annotations.items():
            ann_pattern = rf'@{annotation}\(\s*(?:value\s*=\s*)?["\'](/[^"\']*)["\']'
            for match in re.finditer(ann_pattern, content):
                path = match.group(1)
                func_name = _java_next_method(content, match.end())
                full_path = class_prefix + path if not path.startswith(class_prefix) else path
                endpoints.append({
                    "method": http_method.lower(),
                    "path": full_path,
                    "function": func_name,
                    "module": str(java_file),
                })

            # Also handle annotation without explicit path value: @GetMapping("/path")
            ann_pattern_simple = rf'@{annotation}\(\s*["\']([^"\']+)["\']'
            for match in re.finditer(ann_pattern_simple, content):
                path = match.group(1)
                if not path.startswith("/"):
                    path = "/" + path
                func_name = _java_next_method(content, match.end())
                full_path = class_prefix + path if not path.startswith(class_prefix) else path
                # Avoid duplicates
                if not any(e["path"] == full_path and e["function"] == func_name for e in endpoints):
                    endpoints.append({
                        "method": http_method.lower(),
                        "path": full_path,
                        "function": func_name,
                        "module": str(java_file),
                    })

    return endpoints


def _java_next_method(content: str, after_pos: int) -> str:
    """Find the next Java/Kotlin method name after a given position."""
    remaining = content[after_pos:]
    # Java: public ResponseEntity<X> methodName(
    # Kotlin: fun methodName(
    match = re.search(
        r'(?:public|protected|private|internal)?\s*'
        r'(?:[\w<>,\s\[\]]+\s+)?'
        r'(\w+)\s*\(',
        remaining,
    )
    if match:
        name = match.group(1)
        # Filter out common false positives
        if name not in {"class", "interface", "enum", "if", "for", "while", "switch", "return"}:
            return name
    return "unknown"


# ---------------------------------------------------------------------------
# JS / TS scanners
# ---------------------------------------------------------------------------

def _scan_express(source_dirs: list[Path]) -> list[dict[str, str]]:
    """Scan Express.js / Hono / Fastify source files for route definitions."""
    endpoints: list[dict[str, str]] = []
    http_methods = {"get", "post", "put", "patch", "delete"}

    for js_file in _iter_files(source_dirs, {".js", ".ts", ".mjs", ".mts"}):
        content = _read_safe(js_file)
        if content is None:
            continue

        # Match app.get("/path", ...) or router.post("/path", ...)
        pattern = r'(\w+)\.(' + '|'.join(http_methods) + r')\(\s*["\'/`]([^"\'`]+)["\'/`]'
        for match in re.finditer(pattern, content):
            var_name = match.group(1)
            method = match.group(2)
            path = match.group(3)

            # Try to find handler name
            remaining = content[match.end():]
            handler_match = re.search(r',\s*(\w+)', remaining)
            handler = handler_match.group(1) if handler_match else "handler"

            endpoints.append({
                "method": method,
                "path": path,
                "function": handler,
                "module": str(js_file),
            })

        # Match router.use("/prefix", subRouter)
        use_pattern = r'(\w+)\.use\(\s*["\']([^"\']+)["\']'
        for match in re.finditer(use_pattern, content):
            endpoints.append({
                "method": "USE",
                "path": match.group(2),
                "function": "middleware/subrouter",
                "module": str(js_file),
            })

    return endpoints


def _scan_nextjs(source_dirs: list[Path]) -> list[dict[str, str]]:
    """Scan Next.js App Router and Pages API routes."""
    endpoints: list[dict[str, str]] = []

    for js_file in _iter_files(source_dirs, {".js", ".ts", ".jsx", ".tsx"}):
        content = _read_safe(js_file)
        if content is None:
            continue

        file_str = str(js_file)

        # App Router: app/**/route.ts — export async function GET/POST/PUT/DELETE/PATCH
        if js_file.name.startswith("route."):
            # Derive API path from directory structure
            api_path = _nextjs_path_from_file(js_file, "app")

            http_funcs = re.findall(
                r'export\s+(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)',
                content,
            )
            for method in http_funcs:
                endpoints.append({
                    "method": method.lower(),
                    "path": api_path,
                    "function": method,
                    "module": file_str,
                })

        # Pages Router: pages/api/**/*.ts — export default function handler
        if "/pages/api/" in file_str or "\\pages\\api\\" in file_str:
            api_path = _nextjs_path_from_file(js_file, "pages")

            # Check for method switching: if (req.method === "POST")
            method_checks = re.findall(r'req\.method\s*===?\s*["\'](\w+)["\']', content)
            if method_checks:
                for method in method_checks:
                    endpoints.append({
                        "method": method.lower(),
                        "path": api_path,
                        "function": "handler",
                        "module": file_str,
                    })
            else:
                endpoints.append({
                    "method": "ALL",
                    "path": api_path,
                    "function": "handler",
                    "module": file_str,
                })

    return endpoints


def _nextjs_path_from_file(file_path: Path, root_dir: str) -> str:
    """Derive an API path from a Next.js file path."""
    parts = file_path.parts
    try:
        idx = parts.index(root_dir)
    except ValueError:
        # Try to find "app" or "pages" in the path
        for i, p in enumerate(parts):
            if p in ("app", "pages"):
                idx = i
                break
        else:
            return "/" + file_path.stem

    path_parts = list(parts[idx + 1:])
    # Remove the file name (route.ts, index.ts, etc.)
    if path_parts and path_parts[-1].startswith(("route.", "index.")):
        path_parts = path_parts[:-1]
    elif path_parts:
        # Remove extension from last part
        path_parts[-1] = path_parts[-1].rsplit(".", 1)[0]

    # Convert Next.js dynamic segments: [id] -> :id, [...slug] -> :slug*
    converted = []
    for part in path_parts:
        if part.startswith("[...") and part.endswith("]"):
            converted.append(":" + part[4:-1] + "*")
        elif part.startswith("[") and part.endswith("]"):
            converted.append(":" + part[1:-1])
        else:
            converted.append(part)

    return "/" + "/".join(converted) if converted else "/"


def _scan_nestjs(source_dirs: list[Path]) -> list[dict[str, str]]:
    """Scan NestJS source files for decorator-based routes."""
    endpoints: list[dict[str, str]] = []

    method_decorators = {
        "Get": "GET",
        "Post": "POST",
        "Put": "PUT",
        "Patch": "PATCH",
        "Delete": "DELETE",
        "Head": "HEAD",
        "Options": "OPTIONS",
    }

    for ts_file in _iter_files(source_dirs, {".ts"}):
        content = _read_safe(ts_file)
        if content is None:
            continue

        # Extract @Controller("/prefix") class-level prefix
        ctrl_prefix = ""
        ctrl_match = re.search(r"@Controller\(\s*['\"]([^'\"]+)['\"]", content)
        if ctrl_match:
            ctrl_prefix = ctrl_match.group(1).rstrip("/")

        # Match @Get("/path"), @Post("/path"), etc.
        for decorator, http_method in method_decorators.items():
            dec_pattern = rf"@{decorator}\(\s*['\"]([^'\"]*)['\"]"
            for match in re.finditer(dec_pattern, content):
                path = match.group(1)
                func_name = _ts_next_method(content, match.end())
                full_path = ctrl_prefix + "/" + path.lstrip("/") if path else ctrl_prefix or "/"
                endpoints.append({
                    "method": http_method.lower(),
                    "path": full_path,
                    "function": func_name,
                    "module": str(ts_file),
                })

            # Also handle @Get() with no path argument
            dec_pattern_empty = rf"@{decorator}\(\s*\)"
            for match in re.finditer(dec_pattern_empty, content):
                func_name = _ts_next_method(content, match.end())
                endpoints.append({
                    "method": http_method.lower(),
                    "path": ctrl_prefix or "/",
                    "function": func_name,
                    "module": str(ts_file),
                })

    return endpoints


def _ts_next_method(content: str, after_pos: int) -> str:
    """Find the next TypeScript method name after a position."""
    remaining = content[after_pos:]
    match = re.search(r'(?:async\s+)?(\w+)\s*\(', remaining)
    if match:
        name = match.group(1)
        if name not in {"if", "for", "while", "switch", "return", "class", "async"}:
            return name
    return "unknown"


# ---------------------------------------------------------------------------
# Generic scanner (fallback)
# ---------------------------------------------------------------------------

def _scan_generic(source_dirs: list[Path]) -> list[dict[str, str]]:
    """Generic scan looking for common HTTP route patterns across all languages."""
    endpoints: list[dict[str, str]] = []
    http_methods = {"get", "post", "put", "patch", "delete"}
    all_extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".mts", ".rb", ".java", ".kt", ".go"}

    # JS/Python style: .get("/path", ...)
    js_pattern = r'\.(' + '|'.join(http_methods) + r')\(\s*["\'/`]([^"\'`]+)["\'/`]'
    # Go style: .GET("/path", ...) or .Get("/path", ...)
    go_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "Get", "Post", "Put", "Patch", "Delete"}
    go_pattern = r'\.(' + '|'.join(go_methods) + r')\(\s*["`]([^"`]+)["`]'
    # Java annotation style: @GetMapping("/path")
    java_pattern = r'@(Get|Post|Put|Patch|Delete)Mapping\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'

    for src_file in _iter_files(source_dirs, all_extensions):
        content = _read_safe(src_file)
        if content is None:
            continue

        for match in re.finditer(js_pattern, content):
            endpoints.append({
                "method": match.group(1),
                "path": match.group(2),
                "function": "unknown",
                "module": str(src_file),
            })

        for match in re.finditer(go_pattern, content):
            endpoints.append({
                "method": match.group(1).lower(),
                "path": match.group(2),
                "function": "unknown",
                "module": str(src_file),
            })

        for match in re.finditer(java_pattern, content):
            endpoints.append({
                "method": match.group(1).lower(),
                "path": match.group(2),
                "function": "unknown",
                "module": str(src_file),
            })

    return endpoints


# ---------------------------------------------------------------------------
# Context suggestion
# ---------------------------------------------------------------------------

def _suggest_contexts(endpoints: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    """Group endpoints by path prefix to suggest bounded contexts."""
    contexts: dict[str, list[dict[str, str]]] = {}

    for ep in endpoints:
        path = ep.get("path", "")
        parts = [p for p in path.split("/") if p and not p.startswith("{") and not p.startswith(":")]
        # Use first 2 non-param segments as context key
        if len(parts) >= 2:
            ctx = f"/{parts[0]}/{parts[1]}"
        elif len(parts) == 1:
            ctx = f"/{parts[0]}"
        else:
            ctx = "/"

        contexts.setdefault(ctx, []).append(ep)

    return contexts


# ---------------------------------------------------------------------------
# Deep extraction — DTO field walking, validation, auth, errors
# ---------------------------------------------------------------------------

def _deep_extract_api(
    endpoints: list[dict[str, str]],
    source_dirs: list[Path],
    framework: str,
) -> list[dict]:
    """Extract request/response schemas from endpoint handler code.

    Walks DTO/model classes referenced by each endpoint to build structured
    API contracts with field types, validation constraints, auth, and errors.
    """
    # Build a class/struct → fields index from all source files
    class_index = _build_class_index(source_dirs, framework)

    contracts: list[dict] = []
    for ep in endpoints:
        method = ep.get("method", "?").upper()
        path = ep.get("path", "?")
        func = ep.get("function", "?")
        module_path = ep.get("module", "")

        if method in ("USE", "GROUP"):
            continue

        contract: dict = {
            "endpoint": f"{method} {path}",
            "description": "",
            "tags": _tags_from_path(path),
        }

        # Read the handler file to extract details
        content = _read_safe(Path(module_path)) if module_path else None
        if content is None:
            contracts.append(contract)
            continue

        # Extract auth annotations
        auth = _detect_auth(content, func, framework)
        if auth:
            contract["auth"] = auth

        # Extract request body type and fields
        req_type = _detect_request_type(content, func, framework)
        if req_type and req_type in class_index:
            contract["request"] = {
                "content_type": "application/json",
                "body_class": req_type,
                "fields": class_index[req_type],
            }

        # Extract response type and fields
        resp_type = _detect_response_type(content, func, framework)
        if resp_type and resp_type in class_index:
            contract["response"] = {
                200: {"body_class": resp_type, "fields": class_index[resp_type]},
            }

        # Detect error responses
        errors = _detect_error_responses(content, func)
        if errors:
            resp = contract.get("response", {})
            for err in errors:
                resp[err["status"]] = {"description": err.get("when", "")}
            contract["response"] = resp

        contracts.append(contract)

    return contracts


def _build_class_index(
    source_dirs: list[Path], framework: str,
) -> dict[str, list[dict]]:
    """Build index mapping class/struct names to their field definitions."""
    index: dict[str, list[dict]] = {}

    py_extensions = {".py"}
    java_extensions = {".java", ".kt"}
    ts_extensions = {".ts", ".tsx"}
    go_extensions = {".go"}

    if framework in ("fastapi", "django", "flask"):
        extensions = py_extensions
    elif framework == "spring":
        extensions = java_extensions
    elif framework in ("express", "nextjs", "nestjs", "hono", "fastify"):
        extensions = ts_extensions
    elif framework in ("gin", "echo", "fiber", "chi", "gorilla", "net-http"):
        extensions = go_extensions
    else:
        extensions = py_extensions | java_extensions | ts_extensions | go_extensions

    for src_file in _iter_files(source_dirs, extensions):
        content = _read_safe(src_file)
        if content is None:
            continue

        if src_file.suffix == ".py":
            _index_python_classes(content, index)
        elif src_file.suffix in (".java", ".kt"):
            _index_java_classes(content, index)
        elif src_file.suffix in (".ts", ".tsx"):
            _index_ts_classes(content, index)
        elif src_file.suffix == ".go":
            _index_go_structs(content, index)

    return index


def _index_python_classes(content: str, index: dict[str, list[dict]]) -> None:
    """Index Python classes (Pydantic models, dataclasses) into field maps."""
    # Pydantic BaseModel / dataclass
    class_pattern = r'class\s+(\w+)\s*\([^)]*(?:BaseModel|BaseSchema|Schema)[^)]*\)\s*:'
    for match in re.finditer(class_pattern, content):
        name = match.group(1)
        body_start = match.end()
        next_class = re.search(r'\nclass\s+', content[body_start:])
        body = content[body_start:body_start + next_class.start() if next_class else len(content)]

        fields = []
        # field_name: Type = Field(...) or field_name: Type
        field_pattern = r'(\w+)\s*:\s*([\w\[\], |]+)(?:\s*=\s*(.+))?'
        for fm in re.finditer(field_pattern, body):
            fname = fm.group(1)
            ftype = fm.group(2).strip()
            default_or_field = fm.group(3) or ""

            if fname.startswith("_") or fname in ("model_config", "Config"):
                continue

            constraints = []
            if "Field(" in default_or_field:
                # Extract constraints from Field(min_length=1, max_length=100, ge=0, ...)
                for c in re.finditer(r'(min_length|max_length|ge|le|gt|lt|regex|pattern)\s*=\s*([^,)]+)', default_or_field):
                    constraints.append(f"{c.group(1)}={c.group(2).strip()}")

            required = "None" not in ftype and "Optional" not in ftype and "= None" not in default_or_field
            field_info: dict = {"name": fname, "type": ftype, "required": required}
            if constraints:
                field_info["constraints"] = ", ".join(constraints)
            fields.append(field_info)

        if fields:
            index[name] = fields


def _index_java_classes(content: str, index: dict[str, list[dict]]) -> None:
    """Index Java DTO/record classes into field maps."""
    # Java record: public record CreateOrderRequest(String customerId, ...)
    record_pattern = r'(?:public\s+)?record\s+(\w+)\s*\(([^)]+)\)'
    for match in re.finditer(record_pattern, content):
        name = match.group(1)
        params = match.group(2)
        fields = []
        for param in params.split(","):
            param = param.strip()
            parts = param.rsplit(None, 1)
            if len(parts) == 2:
                ftype, fname = parts
                constraints = []
                # Look for validation annotations above
                above = content[:match.start()]
                for ann in re.finditer(rf'@(\w+)(?:\(([^)]*)\))?\s*$', above):
                    ann_name = ann.group(1)
                    if ann_name in ("NotNull", "NotBlank", "NotEmpty", "Size", "Min", "Max", "Pattern", "Email", "Valid"):
                        detail = ann.group(2) or ""
                        constraints.append(f"@{ann_name}({detail})" if detail else f"@{ann_name}")
                field_info: dict = {"name": fname.strip(), "type": ftype.strip(), "required": True}
                if constraints:
                    field_info["constraints"] = ", ".join(constraints)
                fields.append(field_info)
        if fields:
            index[name] = fields

    # Java class with fields
    class_pattern = r'(?:public\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{'
    for match in re.finditer(class_pattern, content):
        name = match.group(1)
        if name in index:
            continue
        # Extract fields up to first method or closing brace
        body_start = match.end()
        body_end = content.find("}", body_start)
        if body_end == -1:
            continue
        body = content[body_start:body_end]

        fields = []
        field_pattern = r'(?:@(\w+)(?:\(([^)]*)\))?\s+)*(?:private|protected|public)\s+([\w<>,\s\[\]?]+?)\s+(\w+)\s*[;=]'
        for fm in re.finditer(field_pattern, body):
            ftype = fm.group(3).strip()
            fname = fm.group(4)
            if ftype in ("static", "final", "transient"):
                continue
            # Look for validation annotations in the preceding 200 chars
            preceding = body[max(0, fm.start() - 200):fm.start()]
            constraints = []
            for ann in re.finditer(r'@(NotNull|NotBlank|NotEmpty|Size|Min|Max|Pattern|Email|Valid)(?:\(([^)]*)\))?', preceding):
                ann_name = ann.group(1)
                detail = ann.group(2) or ""
                constraints.append(f"@{ann_name}({detail})" if detail else f"@{ann_name}")
            required = any("NotNull" in c or "NotBlank" in c or "NotEmpty" in c for c in constraints)
            field_info = {"name": fname, "type": ftype, "required": required}
            if constraints:
                field_info["constraints"] = ", ".join(constraints)
            fields.append(field_info)

        if fields:
            index[name] = fields


def _index_ts_classes(content: str, index: dict[str, list[dict]]) -> None:
    """Index TypeScript interfaces/types/classes into field maps."""
    # interface or type
    iface_pattern = r'(?:export\s+)?(?:interface|type)\s+(\w+)\s*(?:=\s*)?\{([^}]+)\}'
    for match in re.finditer(iface_pattern, content):
        name = match.group(1)
        body = match.group(2)
        fields = []
        for line in body.split("\n"):
            line = line.strip().rstrip(";").rstrip(",")
            fm = re.match(r'(\w+)(\??):\s*(.+)', line)
            if fm:
                fname = fm.group(1)
                optional = fm.group(2) == "?"
                ftype = fm.group(3).strip()
                fields.append({"name": fname, "type": ftype, "required": not optional})
        if fields:
            index[name] = fields


def _index_go_structs(content: str, index: dict[str, list[dict]]) -> None:
    """Index Go structs into field maps."""
    struct_pattern = r'type\s+(\w+)\s+struct\s*\{'
    for match in re.finditer(struct_pattern, content):
        name = match.group(1)
        brace_start = match.end() - 1
        depth = 1
        pos = brace_start + 1
        while pos < len(content) and depth > 0:
            if content[pos] == '{':
                depth += 1
            elif content[pos] == '}':
                depth -= 1
            pos += 1
        body = content[brace_start + 1:pos - 1]

        fields = []
        field_pattern = r'(\w+)\s+([\w.*\[\]]+)\s*`([^`]*)`'
        for fm in re.finditer(field_pattern, body):
            fname = fm.group(1)
            ftype = fm.group(2)
            tags = fm.group(3)
            if fname in ("Model", "DeletedAt"):
                continue
            json_name = re.search(r'json:"(\w+)', tags)
            display_name = json_name.group(1) if json_name else fname
            required = "required" in tags or "binding:\"required\"" in tags
            constraints = []
            # binding:"required,min=1,max=100"
            binding = re.search(r'binding:"([^"]+)"', tags)
            if binding:
                for part in binding.group(1).split(","):
                    part = part.strip()
                    if part and part != "required":
                        constraints.append(part)
            validate = re.search(r'validate:"([^"]+)"', tags)
            if validate:
                for part in validate.group(1).split(","):
                    part = part.strip()
                    if part and part != "required":
                        constraints.append(part)
            field_info: dict = {"name": display_name, "type": ftype, "required": required}
            if constraints:
                field_info["constraints"] = ", ".join(constraints)
            fields.append(field_info)

        if fields:
            index[name] = fields


def _detect_auth(content: str, func_name: str, framework: str) -> str:
    """Detect authentication requirements from annotations/decorators."""
    if framework == "spring":
        if "@PreAuthorize" in content or "@Secured" in content:
            return "role-based"
        if "SecurityContext" in content or "Authentication" in content:
            return "bearer token"
    elif framework == "fastapi":
        if "Depends(get_current_user)" in content or "Depends(oauth2" in content:
            return "bearer token"
        if "HTTPBearer" in content or "OAuth2PasswordBearer" in content:
            return "bearer token"
        if "APIKey" in content:
            return "api-key"
    elif framework in ("express", "nestjs", "hono", "fastify"):
        if "@UseGuards(AuthGuard" in content or "@UseGuards(JwtAuthGuard" in content:
            return "bearer token"
        if "passport.authenticate" in content or "jwt" in content.lower():
            return "bearer token"
    elif framework in ("gin", "echo"):
        if "AuthMiddleware" in content or "JWTMiddleware" in content:
            return "bearer token"
    return ""


def _detect_request_type(content: str, func_name: str, framework: str) -> str | None:
    """Detect the request body type for a handler function."""
    # Find the function/method definition
    if framework == "fastapi":
        # def handler(body: CreateOrderRequest) or def handler(order: OrderCreate)
        func_match = re.search(rf'def\s+{re.escape(func_name)}\s*\(([^)]+)\)', content)
        if func_match:
            params = func_match.group(1)
            # Look for typed params that aren't Request, Response, Depends, etc.
            for p in params.split(","):
                p = p.strip()
                type_match = re.match(r'\w+\s*:\s*(\w+)', p)
                if type_match:
                    ptype = type_match.group(1)
                    if ptype not in ("Request", "Response", "str", "int", "float", "bool", "None", "Optional", "Query", "Path", "Header", "Cookie"):
                        return ptype
    elif framework == "spring":
        func_match = re.search(rf'{re.escape(func_name)}\s*\([^)]*@RequestBody\s+([\w<>]+)\s+\w+', content)
        if func_match:
            return func_match.group(1).split("<")[0]
    elif framework == "nestjs":
        func_match = re.search(rf'{re.escape(func_name)}\s*\([^)]*@Body\(\)\s+\w+\s*:\s*(\w+)', content)
        if func_match:
            return func_match.group(1)
    elif framework in ("gin", "echo"):
        # Look for ShouldBindJSON(&req) where req is typed
        func_match = re.search(rf'func\s+[^)]*\)\s*{re.escape(func_name)}\(', content)
        if func_match:
            body_after = content[func_match.end():]
            bind_match = re.search(r'(?:ShouldBindJSON|Bind)\(&(\w+)\)', body_after[:500])
            if bind_match:
                var_name = bind_match.group(1)
                type_match = re.search(rf'var\s+{re.escape(var_name)}\s+(\w+)', body_after[:500])
                if type_match:
                    return type_match.group(1)
    return None


def _detect_response_type(content: str, func_name: str, framework: str) -> str | None:
    """Detect the response type for a handler function."""
    if framework == "fastapi":
        # response_model=OrderResponse or -> OrderResponse
        func_match = re.search(rf'response_model\s*=\s*(\w+).*?def\s+{re.escape(func_name)}', content, re.DOTALL)
        if func_match:
            return func_match.group(1)
        # Return type annotation
        func_match = re.search(rf'def\s+{re.escape(func_name)}\s*\([^)]*\)\s*->\s*(\w+)', content)
        if func_match:
            rtype = func_match.group(1)
            if rtype not in ("None", "Response", "JSONResponse", "dict"):
                return rtype
    elif framework == "spring":
        # ResponseEntity<OrderResponse> or just OrderResponse as return type
        func_match = re.search(rf'(?:ResponseEntity<)?(\w+)>?\s+{re.escape(func_name)}\s*\(', content)
        if func_match:
            rtype = func_match.group(1)
            if rtype not in ("void", "ResponseEntity", "String", "Object"):
                return rtype
    return None


def _detect_error_responses(content: str, func_name: str) -> list[dict]:
    """Detect error response patterns in handler code."""
    errors: list[dict] = []
    seen_statuses: set[int] = set()

    # HTTP status codes in exceptions/responses
    patterns = [
        (r'status[_.]?code\s*=\s*(\d{3})', None),
        (r'HttpStatus\.(\w+)', None),
        (r'raise\s+HTTPException\s*\(\s*status_code\s*=\s*(\d{3})', None),
        (r'status\((\d{3})\)', None),
        (r'\.status\((\d{3})\)', None),
        (r'http\.Status(\w+)', None),
    ]

    for pattern, _ in patterns:
        for match in re.finditer(pattern, content):
            val = match.group(1)
            # Convert HttpStatus name to code
            status_map = {
                "BAD_REQUEST": 400, "UNAUTHORIZED": 401, "FORBIDDEN": 403,
                "NOT_FOUND": 404, "CONFLICT": 409, "INTERNAL_SERVER_ERROR": 500,
                "BadRequest": 400, "Unauthorized": 401, "Forbidden": 403,
                "NotFound": 404, "Conflict": 409, "InternalServerError": 500,
            }
            if val in status_map:
                code = status_map[val]
            else:
                try:
                    code = int(val)
                except ValueError:
                    continue
            if code >= 400 and code not in seen_statuses:
                seen_statuses.add(code)
                errors.append({"status": code, "when": _error_reason(code)})

    return errors


def _error_reason(code: int) -> str:
    """Return a generic reason for an HTTP error code."""
    reasons = {
        400: "validation fails",
        401: "not authenticated",
        403: "not authorized",
        404: "not found",
        409: "conflict",
        422: "unprocessable entity",
        500: "internal server error",
    }
    return reasons.get(code, f"HTTP {code}")


def _tags_from_path(path: str) -> list[str]:
    """Extract tags from an API path (first non-param segment)."""
    parts = [p for p in path.split("/") if p and not p.startswith("{") and not p.startswith(":")]
    if len(parts) >= 2:
        return [parts[1]]  # e.g., /api/orders → "orders"
    elif parts:
        return [parts[0]]
    return []


def _write_api_contracts(root: Path, config: dict, contracts: list[dict]) -> None:
    """Write deep reverse output to specs/domain/api-contracts.yaml (DEEP-REV-001 safe)."""
    import yaml

    from evospec.core.config import get_paths

    paths = get_paths(config)
    domain_dir = root / paths["domain"]
    contracts_path = domain_dir / "api-contracts.yaml"

    # DEEP-REV-001: Don't overwrite existing manually-curated data
    if contracts_path.exists():
        existing = yaml.safe_load(contracts_path.read_text()) or {}
        existing_contracts = existing.get("contracts", [])
        if existing_contracts:
            console.print(
                f"[yellow]⚠ {contracts_path.relative_to(root)} already has "
                f"{len(existing_contracts)} contract(s). Use --force to overwrite.[/yellow]"
            )
            return

    domain_dir.mkdir(parents=True, exist_ok=True)
    output = {"contracts": contracts}
    contracts_path.write_text(yaml.dump(output, default_flow_style=False, sort_keys=False))
    console.print(f"[green]✓[/green] Wrote {len(contracts)} contract(s) to {contracts_path.relative_to(root)}")
