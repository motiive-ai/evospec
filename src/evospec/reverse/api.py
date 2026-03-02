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

    # Group by path prefix to suggest bounded contexts
    contexts = _suggest_contexts(endpoints)

    if contexts:
        console.print(f"\n[bold]Suggested bounded contexts:[/bold]\n")
        for ctx, eps in contexts.items():
            console.print(f"  [cyan]{ctx}[/cyan] ({len(eps)} endpoints)")

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
