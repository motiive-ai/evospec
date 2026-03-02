"""Reverse-engineer CLI commands and module structure into spec stubs.

Supports:
- Python: Click commands + module/class/function structure
- Go: Cobra commands + package/struct/function structure
- Java: Picocli / Spring Shell commands + package/class/method structure
- JS/TS: module/class/function/export structure
"""

import ast
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


def reverse_engineer_cli(source: str | None = None) -> None:
    """Scan source code for CLI commands and module structure across languages."""
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

    # Detect which languages are present
    has_py = bool(_iter_files(source_dirs, {".py"}))
    has_go = bool(_iter_files(source_dirs, {".go"}))
    has_java = bool(_iter_files(source_dirs, {".java", ".kt"}))
    has_js = bool(_iter_files(source_dirs, {".js", ".ts", ".jsx", ".tsx", ".mjs", ".mts"}))

    langs = []
    if has_py:
        langs.append("Python")
    if has_go:
        langs.append("Go")
    if has_java:
        langs.append("Java/Kotlin")
    if has_js:
        langs.append("JS/TS")

    console.print(f"[bold]Scanning for CLI commands and module structure ({', '.join(langs) or 'no source files found'})...[/bold]\n")

    # --- Phase 1: CLI commands (all languages) ---
    all_commands: list[dict] = []

    if has_py:
        py_cmds = _scan_click_commands(source_dirs)
        if py_cmds:
            all_commands.extend(py_cmds)

    if has_go:
        go_cmds = _scan_cobra_commands(source_dirs)
        if go_cmds:
            all_commands.extend(go_cmds)

    if has_java:
        java_cmds = _scan_java_cli_commands(source_dirs)
        if java_cmds:
            all_commands.extend(java_cmds)

    if all_commands:
        console.print(f"[green]Found {len(all_commands)} CLI command(s):[/green]\n")
        _print_command_tree(all_commands)
    else:
        console.print("[yellow]No CLI commands found.[/yellow]\n")

    # --- Phase 2: Module structure (all languages) ---
    all_modules: list[dict] = []

    if has_py:
        all_modules.extend(_scan_python_modules(source_dirs))
    if has_go:
        all_modules.extend(_scan_go_modules(source_dirs))
    if has_java:
        all_modules.extend(_scan_java_modules(source_dirs))
    if has_js:
        all_modules.extend(_scan_js_modules(source_dirs))

    if all_modules:
        console.print(f"\n[green]Found {len(all_modules)} module(s):[/green]\n")
        for mod in all_modules:
            _print_module(mod)

    # --- Phase 3: Suggest bounded contexts ---
    contexts = _suggest_contexts_from_packages(source_dirs, has_py, has_go, has_java, has_js)
    if contexts:
        console.print(f"\n[bold]Suggested bounded contexts (from package structure):[/bold]\n")
        for ctx_name, ctx_info in contexts.items():
            mod_count = ctx_info["module_count"]
            total_loc = ctx_info["total_loc"]
            lang_tag = f" [{ctx_info.get('lang', '')}]" if ctx_info.get("lang") else ""
            console.print(
                f"  [cyan]{ctx_name}[/cyan] "
                f"({mod_count} modules, {total_loc} lines){lang_tag}"
            )

    # --- Phase 4: Summary ---
    console.print(
        f"\n[dim]Use these findings to populate traceability.modules in your spec.yaml files.[/dim]"
    )
    if all_commands:
        console.print(
            f"[dim]CLI commands can map to domain operations in your domain-contract.md.[/dim]"
        )


def _print_module(mod: dict) -> None:
    """Print a single module's structure."""
    name = mod["module"]
    classes = mod.get("classes", [])
    functions = mod.get("functions", [])
    exports = mod.get("exports", [])
    loc = mod.get("loc", 0)
    lang = mod.get("lang", "")

    class_str = f", {len(classes)} class(es)" if classes else ""
    func_str = f", {len(functions)} function(s)" if functions else ""
    export_str = f", {len(exports)} export(s)" if exports else ""
    lang_str = f" [{lang}]" if lang else ""
    console.print(
        f"  [cyan]{name}[/cyan] [dim]({loc} lines{class_str}{func_str}{export_str}){lang_str}[/dim]"
    )

    for cls in classes:
        methods = cls.get("methods", [])
        bases = cls.get("bases", [])
        base_str = f"({', '.join(bases)})" if bases else ""
        console.print(
            f"    [dim]├─[/dim] [bold]{cls['name']}[/bold]{base_str}"
            f" [dim]({len(methods)} methods)[/dim]"
        )
        for method in methods:
            is_last = method == methods[-1]
            prefix = "└─" if is_last else "├─"
            console.print(f"    [dim]│  {prefix}[/dim] {method['name']}()")

    for func in functions:
        is_last = func == functions[-1] and not exports
        prefix = "└─" if is_last else "├─"
        decorator_str = ""
        if func.get("decorators"):
            decorator_str = f" [dim]@{', @'.join(func['decorators'])}[/dim]"
        console.print(
            f"    [dim]{prefix}[/dim] {func['name']}(){decorator_str}"
        )

    for exp in exports:
        is_last = exp == exports[-1]
        prefix = "└─" if is_last else "├─"
        console.print(
            f"    [dim]{prefix}[/dim] export {exp['name']} [dim]({exp.get('type', '?')})[/dim]"
        )


def _scan_click_commands(source_dirs: list[Path]) -> list[dict]:
    """Scan Python files for Click command decorators and extract command structure."""
    commands: list[dict] = []

    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for py_file in source_dir.rglob("*.py"):
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue

            if "click" not in content:
                continue

            try:
                tree = ast.parse(content, filename=str(py_file))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue

                cmd_info = _extract_click_command(node, content, py_file)
                if cmd_info:
                    commands.append(cmd_info)

    return commands


def _extract_click_command(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    content: str,
    py_file: Path,
) -> dict | None:
    """Extract Click command info from a function definition AST node."""
    command_type = None
    parent_group = None
    options: list[dict] = []
    arguments: list[dict] = []

    for decorator in node.decorator_list:
        dec_str = _decorator_to_string(decorator)

        # Detect @cli.command(), @group.command(), @click.command()
        if ".command(" in dec_str or dec_str.endswith(".command"):
            command_type = "command"
            parts = dec_str.split(".")
            if len(parts) >= 2 and parts[0] != "click":
                parent_group = parts[0]

        # Detect @cli.group(), @click.group()
        elif ".group(" in dec_str or dec_str.endswith(".group"):
            command_type = "group"
            parts = dec_str.split(".")
            if len(parts) >= 2 and parts[0] != "click":
                parent_group = parts[0]

        # Detect @click.option(...)
        elif "click.option(" in dec_str or ".option(" in dec_str:
            opt_info = _extract_click_option(decorator)
            if opt_info:
                options.append(opt_info)

        # Detect @click.argument(...)
        elif "click.argument(" in dec_str or ".argument(" in dec_str:
            arg_info = _extract_click_argument(decorator)
            if arg_info:
                arguments.append(arg_info)

    if command_type is None:
        return None

    # Extract command name from decorator or function name
    cmd_name = node.name

    # Extract docstring
    docstring = ast.get_docstring(node) or ""

    return {
        "name": cmd_name,
        "type": command_type,
        "parent": parent_group,
        "options": options,
        "arguments": arguments,
        "docstring": docstring,
        "module": str(py_file),
        "line": node.lineno,
    }


def _decorator_to_string(decorator: ast.expr) -> str:
    """Convert a decorator AST node to a readable string."""
    if isinstance(decorator, ast.Call):
        return _decorator_to_string(decorator.func)
    elif isinstance(decorator, ast.Attribute):
        value_str = _decorator_to_string(decorator.value)
        return f"{value_str}.{decorator.attr}"
    elif isinstance(decorator, ast.Name):
        return decorator.id
    return ""


def _extract_click_option(decorator: ast.expr) -> dict | None:
    """Extract option info from a @click.option() decorator."""
    if not isinstance(decorator, ast.Call):
        return None

    option_name = ""
    option_help = ""
    option_type = ""
    option_default = None
    is_flag = False

    # First positional arg is the option name
    if decorator.args:
        first_arg = decorator.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            option_name = first_arg.value

    for kw in decorator.keywords:
        if kw.arg == "help" and isinstance(kw.value, ast.Constant):
            option_help = str(kw.value.value)
        elif kw.arg == "type":
            option_type = _ast_value_to_string(kw.value)
        elif kw.arg == "default":
            option_default = _ast_value_to_string(kw.value)
        elif kw.arg == "is_flag" and isinstance(kw.value, ast.Constant):
            is_flag = bool(kw.value.value)

    if not option_name:
        return None

    result: dict = {"name": option_name, "help": option_help}
    if option_type:
        result["type"] = option_type
    if option_default is not None:
        result["default"] = option_default
    if is_flag:
        result["is_flag"] = True

    return result


def _extract_click_argument(decorator: ast.expr) -> dict | None:
    """Extract argument info from a @click.argument() decorator."""
    if not isinstance(decorator, ast.Call):
        return None

    arg_name = ""
    required = True

    if decorator.args:
        first_arg = decorator.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            arg_name = first_arg.value

    for kw in decorator.keywords:
        if kw.arg == "required" and isinstance(kw.value, ast.Constant):
            required = bool(kw.value.value)

    if not arg_name:
        return None

    return {"name": arg_name, "required": required}


def _ast_value_to_string(node: ast.expr) -> str:
    """Convert an AST value node to a human-readable string."""
    if isinstance(node, ast.Constant):
        return repr(node.value)
    elif isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return f"{_ast_value_to_string(node.value)}.{node.attr}"
    elif isinstance(node, ast.Call):
        func_str = _ast_value_to_string(node.func)
        args = [_ast_value_to_string(a) for a in node.args]
        return f"{func_str}({', '.join(args)})"
    return "..."


def _print_command_tree(commands: list[dict]) -> None:
    """Print CLI commands in a tree structure."""
    # Separate groups and commands
    groups = {c["name"]: c for c in commands if c["type"] == "group"}
    cmds = [c for c in commands if c["type"] == "command"]

    # Print groups and their subcommands
    printed_cmds: set[str] = set()
    for group_name, group in groups.items():
        console.print(f"  [bold cyan]{group_name}[/bold cyan] [dim](group)[/dim]")
        if group.get("docstring"):
            console.print(f"    [dim]{group['docstring']}[/dim]")

        # Find subcommands of this group
        sub_cmds = [c for c in cmds if c.get("parent") == group_name]
        for cmd in sub_cmds:
            is_last = cmd == sub_cmds[-1]
            prefix = "└─" if is_last else "├─"
            console.print(
                f"    [dim]{prefix}[/dim] [cyan]{cmd['name']}[/cyan]"
            )
            if cmd.get("docstring"):
                console.print(f"    [dim]   {cmd['docstring']}[/dim]")

            # Print options and arguments
            for opt in cmd.get("options", []):
                console.print(
                    f"    [dim]      --{opt['name'].lstrip('-')}[/dim]"
                    f" {opt.get('help', '')}"
                )
            for arg in cmd.get("arguments", []):
                req = "" if arg.get("required", True) else " (optional)"
                console.print(
                    f"    [dim]      <{arg['name']}>{req}[/dim]"
                )

            printed_cmds.add(cmd["name"])

    # Print top-level commands (no parent group)
    top_cmds = [c for c in cmds if c["name"] not in printed_cmds]
    for cmd in top_cmds:
        parent_str = f" [dim](under {cmd['parent']})[/dim]" if cmd.get("parent") else ""
        console.print(f"  [cyan]{cmd['name']}[/cyan]{parent_str}")
        if cmd.get("docstring"):
            console.print(f"    [dim]{cmd['docstring']}[/dim]")

        for opt in cmd.get("options", []):
            console.print(
                f"    [dim]  --{opt['name'].lstrip('-')}[/dim]"
                f" {opt.get('help', '')}"
            )
        for arg in cmd.get("arguments", []):
            req = "" if arg.get("required", True) else " (optional)"
            console.print(f"    [dim]  <{arg['name']}>{req}[/dim]")


def _scan_python_modules(source_dirs: list[Path]) -> list[dict]:
    """Scan Python files and extract module structure (classes, functions)."""
    modules: list[dict] = []

    for py_file in sorted(_iter_files(source_dirs, {".py"})):
        if py_file.name == "__init__.py":
            continue

        content = _read_safe(py_file)
        if content is None:
            continue

        try:
            tree = ast.parse(content, filename=str(py_file))
        except SyntaxError:
            continue

        loc = len(content.splitlines())
        classes: list[dict] = []
        functions: list[dict] = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                        methods.append({"name": item.name, "line": item.lineno})

                bases = []
                for base in node.bases:
                    bases.append(_ast_value_to_string(base))

                classes.append({
                    "name": node.name,
                    "bases": bases,
                    "methods": methods,
                    "line": node.lineno,
                    "docstring": ast.get_docstring(node) or "",
                })

            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                decorators = []
                for dec in node.decorator_list:
                    decorators.append(_decorator_to_string(dec))

                functions.append({
                    "name": node.name,
                    "decorators": decorators,
                    "line": node.lineno,
                    "docstring": ast.get_docstring(node) or "",
                })

        module_name = _path_to_module(py_file, source_dirs)

        modules.append({
            "module": module_name,
            "path": str(py_file),
            "loc": loc,
            "classes": classes,
            "functions": functions,
            "lang": "python",
        })

    return modules


def _path_to_module(py_file: Path, source_dirs: list[Path]) -> str:
    """Convert a Python file path to a dotted module name."""
    for source_dir in source_dirs:
        try:
            rel = py_file.relative_to(source_dir)
            parts = list(rel.parts)
            if parts[-1] == "__init__.py":
                parts = parts[:-1]
            else:
                parts[-1] = parts[-1].replace(".py", "")
            return ".".join(parts)
        except ValueError:
            continue
    return str(py_file)


def _file_to_module(src_file: Path, source_dirs: list[Path]) -> str:
    """Convert any source file path to a module-like name."""
    for source_dir in source_dirs:
        try:
            rel = src_file.relative_to(source_dir)
            parts = list(rel.parts)
            # Remove extension from last part
            if parts:
                parts[-1] = parts[-1].rsplit(".", 1)[0]
            return "/".join(parts)
        except ValueError:
            continue
    return str(src_file)


# ---------------------------------------------------------------------------
# Go: Cobra CLI commands + module scanning
# ---------------------------------------------------------------------------

def _scan_cobra_commands(source_dirs: list[Path]) -> list[dict]:
    """Scan Go files for Cobra command definitions."""
    commands: list[dict] = []

    for go_file in _iter_files(source_dirs, {".go"}):
        content = _read_safe(go_file)
        if content is None or "cobra" not in content.lower():
            continue

        # Match: &cobra.Command{ Use: "name", Short: "...", ... }
        cmd_pattern = r'&cobra\.Command\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        for match in re.finditer(cmd_pattern, content, re.DOTALL):
            block = match.group(1)

            use_match = re.search(r'Use:\s*["`](\S+)["`]', block)
            short_match = re.search(r'Short:\s*["`]([^"`]+)["`]', block)
            long_match = re.search(r'Long:\s*["`]([^"`]+)["`]', block)

            if not use_match:
                continue

            cmd_name = use_match.group(1).split()[0]  # "serve [flags]" -> "serve"
            docstring = (short_match.group(1) if short_match else
                         long_match.group(1) if long_match else "")

            commands.append({
                "name": cmd_name,
                "type": "command",
                "parent": None,
                "options": [],
                "arguments": [],
                "docstring": docstring,
                "module": str(go_file),
                "line": content[:match.start()].count("\n") + 1,
                "lang": "go/cobra",
            })

        # Detect AddCommand relationships: rootCmd.AddCommand(serveCmd)
        add_pattern = r'(\w+)\.AddCommand\(\s*(\w+)'
        for match in re.finditer(add_pattern, content):
            parent_var = match.group(1)
            child_var = match.group(2)
            # Try to link child to parent by variable name
            for cmd in commands:
                if cmd["module"] == str(go_file):
                    # Heuristic: if the child var contains the command name
                    if cmd["name"].lower() in child_var.lower():
                        cmd["parent"] = parent_var.replace("Cmd", "").replace("cmd", "") or None

        # Detect flags: cmd.Flags().StringVarP(...)
        flag_pattern = r'(\w+)\.(?:Persistent)?Flags\(\)\.(\w+)(?:VarP?|P)?\(\s*[^,]*,\s*["`]([^"`]+)["`]'
        for match in re.finditer(flag_pattern, content):
            flag_type = match.group(2)  # String, Bool, Int, etc.
            flag_name = match.group(3)
            # Try to associate with commands
            for cmd in commands:
                if cmd["module"] == str(go_file):
                    cmd["options"].append({
                        "name": f"--{flag_name}",
                        "help": "",
                        "type": flag_type,
                    })
                    break

    return commands


def _scan_go_modules(source_dirs: list[Path]) -> list[dict]:
    """Scan Go files and extract package/struct/function structure."""
    modules: list[dict] = []

    for go_file in sorted(_iter_files(source_dirs, {".go"})):
        # Skip test files
        if go_file.name.endswith("_test.go"):
            continue

        content = _read_safe(go_file)
        if content is None:
            continue

        loc = len(content.splitlines())

        # Extract package name
        pkg_match = re.search(r'^package\s+(\w+)', content, re.MULTILINE)
        pkg_name = pkg_match.group(1) if pkg_match else "unknown"

        classes: list[dict] = []  # structs
        functions: list[dict] = []

        # Extract structs: type Name struct { ... }
        struct_pattern = r'type\s+(\w+)\s+struct\s*\{'
        for struct_match in re.finditer(struct_pattern, content):
            struct_name = struct_match.group(1)

            # Find methods: func (r *StructName) MethodName(...)
            method_pattern = rf'func\s+\(\s*\w+\s+\*?{struct_name}\s*\)\s+(\w+)\s*\('
            methods = []
            for method_match in re.finditer(method_pattern, content):
                methods.append({
                    "name": method_match.group(1),
                    "line": content[:method_match.start()].count("\n") + 1,
                })

            # Extract embedded types as "bases"
            brace_start = struct_match.end()
            depth = 1
            pos = brace_start
            while pos < len(content) and depth > 0:
                if content[pos] == '{':
                    depth += 1
                elif content[pos] == '}':
                    depth -= 1
                pos += 1
            struct_body = content[brace_start:pos]

            bases = []
            embed_pattern = r'^\s+(\w+(?:\.\w+)?)\s*$'
            for embed_match in re.finditer(embed_pattern, struct_body, re.MULTILINE):
                bases.append(embed_match.group(1))

            classes.append({
                "name": struct_name,
                "bases": bases,
                "methods": methods,
                "line": content[:struct_match.start()].count("\n") + 1,
                "docstring": "",
            })

        # Extract standalone functions: func FuncName(...)
        func_pattern = r'^func\s+(\w+)\s*\('
        for func_match in re.finditer(func_pattern, content, re.MULTILINE):
            func_name = func_match.group(1)
            # Skip if it's a method (already captured)
            pre_context = content[max(0, func_match.start() - 5):func_match.start()]
            if ")" in pre_context:  # method receiver
                continue
            functions.append({
                "name": func_name,
                "decorators": [],
                "line": content[:func_match.start()].count("\n") + 1,
                "docstring": "",
            })

        module_name = _file_to_module(go_file, source_dirs)

        modules.append({
            "module": f"{module_name} (pkg {pkg_name})",
            "path": str(go_file),
            "loc": loc,
            "classes": classes,
            "functions": functions,
            "lang": "go",
        })

    return modules


# ---------------------------------------------------------------------------
# Java: Picocli / Spring Shell CLI commands + module scanning
# ---------------------------------------------------------------------------

def _scan_java_cli_commands(source_dirs: list[Path]) -> list[dict]:
    """Scan Java/Kotlin files for Picocli @Command and Spring Shell @ShellMethod."""
    commands: list[dict] = []

    for java_file in _iter_files(source_dirs, {".java", ".kt"}):
        content = _read_safe(java_file)
        if content is None:
            continue

        # Picocli: @Command(name = "serve", description = "...")
        picocli_pattern = r'@Command\(\s*([^)]+)\)'
        for match in re.finditer(picocli_pattern, content):
            attrs = match.group(1)
            name_match = re.search(r'name\s*=\s*["\'](\w+)["\']', attrs)
            desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', attrs)
            if name_match:
                commands.append({
                    "name": name_match.group(1),
                    "type": "command",
                    "parent": None,
                    "options": [],
                    "arguments": [],
                    "docstring": desc_match.group(1) if desc_match else "",
                    "module": str(java_file),
                    "line": content[:match.start()].count("\n") + 1,
                    "lang": "java/picocli",
                })

        # Picocli subcommands: @Command(subcommands = {SubCmd.class, ...})
        sub_match = re.search(r'subcommands\s*=\s*\{([^}]+)\}', content)
        if sub_match:
            sub_classes = re.findall(r'(\w+)\.class', sub_match.group(1))
            for cmd in commands:
                if cmd["module"] == str(java_file) and cmd.get("parent") is None:
                    # Mark this as a group
                    cmd["type"] = "group"

        # Spring Shell: @ShellMethod("description")
        shell_pattern = r'@ShellMethod\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'
        for match in re.finditer(shell_pattern, content):
            desc = match.group(1)
            # Find method name
            remaining = content[match.end():]
            method_match = re.search(r'(?:public|private|protected)?\s*\w+\s+(\w+)\s*\(', remaining)
            method_name = method_match.group(1) if method_match else "unknown"

            commands.append({
                "name": method_name.replace("_", "-"),
                "type": "command",
                "parent": "shell",
                "options": [],
                "arguments": [],
                "docstring": desc,
                "module": str(java_file),
                "line": content[:match.start()].count("\n") + 1,
                "lang": "java/spring-shell",
            })

        # Picocli @Option: @Option(names = {"--name", "-n"}, description = "...")
        option_pattern = r'@Option\(\s*([^)]+)\)'
        for match in re.finditer(option_pattern, content):
            attrs = match.group(1)
            names_match = re.search(r'names\s*=\s*\{([^}]+)\}', attrs)
            if not names_match:
                names_match = re.search(r'names\s*=\s*["\']([^"\']+)["\']', attrs)
            desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', attrs)
            if names_match:
                opt_name = re.findall(r'["\']([^"\']+)["\']', names_match.group(1))
                # Associate with the last command from this file
                for cmd in reversed(commands):
                    if cmd["module"] == str(java_file):
                        cmd["options"].append({
                            "name": opt_name[0] if opt_name else "unknown",
                            "help": desc_match.group(1) if desc_match else "",
                        })
                        break

    return commands


def _scan_java_modules(source_dirs: list[Path]) -> list[dict]:
    """Scan Java/Kotlin files and extract class/method structure."""
    modules: list[dict] = []

    for java_file in sorted(_iter_files(source_dirs, {".java", ".kt"})):
        content = _read_safe(java_file)
        if content is None:
            continue

        loc = len(content.splitlines())

        # Extract package
        pkg_match = re.search(r'^package\s+([\w.]+)', content, re.MULTILINE)
        pkg_name = pkg_match.group(1) if pkg_match else ""

        classes: list[dict] = []
        functions: list[dict] = []

        # Extract classes: public class Name extends Base implements Iface { ... }
        class_pattern = r'(?:public|private|protected)?\s*(?:abstract\s+)?(?:class|interface|enum)\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?'
        for class_match in re.finditer(class_pattern, content):
            class_name = class_match.group(1)
            bases = []
            if class_match.group(2):
                bases.append(class_match.group(2))
            if class_match.group(3):
                bases.extend([b.strip() for b in class_match.group(3).split(",")])

            # Find methods in this class
            methods = []
            method_pattern = r'(?:public|private|protected)\s+(?:static\s+)?(?:[\w<>,\[\]\s]+\s+)?(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{'
            for method_match in re.finditer(method_pattern, content):
                method_name = method_match.group(1)
                if method_name not in {"if", "for", "while", "switch", "class", class_name}:
                    methods.append({
                        "name": method_name,
                        "line": content[:method_match.start()].count("\n") + 1,
                    })

            # Get annotations on the class
            annotations = []
            pre_class = content[:class_match.start()]
            for ann_match in re.finditer(r'@(\w+)', pre_class[-200:]):
                annotations.append(ann_match.group(1))

            classes.append({
                "name": class_name,
                "bases": bases,
                "methods": methods,
                "line": content[:class_match.start()].count("\n") + 1,
                "docstring": "",
            })

        module_name = pkg_name + "." + java_file.stem if pkg_name else java_file.stem

        modules.append({
            "module": module_name,
            "path": str(java_file),
            "loc": loc,
            "classes": classes,
            "functions": functions,
            "lang": "java",
        })

    return modules


# ---------------------------------------------------------------------------
# JS/TS: module/class/function/export scanning
# ---------------------------------------------------------------------------

def _scan_js_modules(source_dirs: list[Path]) -> list[dict]:
    """Scan JS/TS files and extract module structure (classes, functions, exports)."""
    modules: list[dict] = []

    for js_file in sorted(_iter_files(source_dirs, {".js", ".ts", ".jsx", ".tsx", ".mjs", ".mts"})):
        # Skip common non-source directories
        file_str = str(js_file)
        if any(skip in file_str for skip in ["node_modules", ".next", "dist/", "build/", ".d.ts"]):
            continue

        content = _read_safe(js_file)
        if content is None:
            continue

        loc = len(content.splitlines())
        classes: list[dict] = []
        functions: list[dict] = []
        exports: list[dict] = []

        # Extract classes: class Name extends Base { ... }
        class_pattern = r'(?:export\s+)?(?:default\s+)?class\s+(\w+)(?:\s+extends\s+([\w.]+))?(?:\s+implements\s+([\w,\s]+))?'
        for class_match in re.finditer(class_pattern, content):
            class_name = class_match.group(1)
            bases = []
            if class_match.group(2):
                bases.append(class_match.group(2))

            # Find methods
            methods = []
            # Simple heuristic: method patterns after class declaration
            class_start = class_match.end()
            next_class = re.search(r'\n(?:export\s+)?(?:default\s+)?class\s+', content[class_start:])
            class_body = content[class_start:class_start + next_class.start() if next_class else len(content)]

            method_pattern = r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[\w<>|\[\],\s]+)?\s*\{'
            for method_match in re.finditer(method_pattern, class_body):
                method_name = method_match.group(1)
                if method_name not in {"if", "for", "while", "switch", "return", "catch", "function"}:
                    methods.append({
                        "name": method_name,
                        "line": content[:class_start + method_match.start()].count("\n") + 1,
                    })

            classes.append({
                "name": class_name,
                "bases": bases,
                "methods": methods,
                "line": content[:class_match.start()].count("\n") + 1,
                "docstring": "",
            })

        # Extract standalone functions
        func_pattern = r'(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)\s*\('
        for func_match in re.finditer(func_pattern, content):
            func_name = func_match.group(1)
            decorators = []
            is_exported = "export" in content[max(0, func_match.start() - 20):func_match.start() + 10]
            if is_exported:
                decorators.append("export")

            functions.append({
                "name": func_name,
                "decorators": decorators,
                "line": content[:func_match.start()].count("\n") + 1,
                "docstring": "",
            })

        # Extract arrow function exports: export const name = (...) => { ... }
        arrow_pattern = r'export\s+(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*(?::\s*[\w<>|\[\],\s]+)?\s*=>'
        for arrow_match in re.finditer(arrow_pattern, content):
            func_name = arrow_match.group(1)
            # Don't duplicate if already found as function
            if not any(f["name"] == func_name for f in functions):
                functions.append({
                    "name": func_name,
                    "decorators": ["export"],
                    "line": content[:arrow_match.start()].count("\n") + 1,
                    "docstring": "",
                })

        # Extract named exports: export { name1, name2 }
        named_export_pattern = r'export\s*\{([^}]+)\}'
        for export_match in re.finditer(named_export_pattern, content):
            export_names = re.findall(r'(\w+)(?:\s+as\s+\w+)?', export_match.group(1))
            for name in export_names:
                exports.append({"name": name, "type": "named"})

        # Extract default export: export default ...
        default_pattern = r'export\s+default\s+(?:class\s+)?(\w+)'
        for default_match in re.finditer(default_pattern, content):
            exports.append({"name": default_match.group(1), "type": "default"})

        module_name = _file_to_module(js_file, source_dirs)

        modules.append({
            "module": module_name,
            "path": str(js_file),
            "loc": loc,
            "classes": classes,
            "functions": functions,
            "exports": exports,
            "lang": "js/ts",
        })

    return modules


# ---------------------------------------------------------------------------
# Bounded context suggestion (multi-language)
# ---------------------------------------------------------------------------

def _count_dir_stats(directory: Path, extensions: set[str]) -> tuple[int, int]:
    """Count source files and total LOC in a directory."""
    files = [f for f in directory.rglob("*") if f.suffix in extensions and f.name != "__init__.py"]
    total_loc = 0
    for f in files:
        content = _read_safe(f)
        if content:
            total_loc += len(content.splitlines())
    return len(files), total_loc


def _suggest_contexts_from_packages(
    source_dirs: list[Path],
    has_py: bool,
    has_go: bool,
    has_java: bool,
    has_js: bool,
) -> dict[str, dict]:
    """Suggest bounded contexts based on package structure across languages."""
    contexts: dict[str, dict] = {}

    for source_dir in source_dirs:
        if not source_dir.exists():
            continue

        # --- Python: sub-packages under top-level packages ---
        if has_py:
            for pkg_dir in sorted(source_dir.iterdir()):
                if not pkg_dir.is_dir() or not (pkg_dir / "__init__.py").exists():
                    continue

                for sub_dir in sorted(pkg_dir.iterdir()):
                    if not sub_dir.is_dir() or not (sub_dir / "__init__.py").exists():
                        continue
                    if sub_dir.name.startswith("_"):
                        continue

                    module_count, total_loc = _count_dir_stats(sub_dir, {".py"})
                    ctx_name = f"{pkg_dir.name}.{sub_dir.name}"
                    contexts[ctx_name] = {
                        "module_count": module_count,
                        "total_loc": total_loc,
                        "path": str(sub_dir),
                        "lang": "python",
                    }

        # --- Go: top-level directories with .go files (packages) ---
        if has_go:
            for sub_dir in sorted(source_dir.rglob("*")):
                if not sub_dir.is_dir():
                    continue
                go_files = list(sub_dir.glob("*.go"))
                if not go_files:
                    continue
                # Only immediate .go files (not recursive)
                non_test = [f for f in go_files if not f.name.endswith("_test.go")]
                if not non_test:
                    continue

                try:
                    rel = sub_dir.relative_to(source_dir)
                except ValueError:
                    continue
                ctx_name = "/".join(rel.parts)
                if ctx_name and ctx_name not in contexts:
                    module_count = len(non_test)
                    total_loc = sum(
                        len((_read_safe(f) or "").splitlines()) for f in non_test
                    )
                    contexts[ctx_name] = {
                        "module_count": module_count,
                        "total_loc": total_loc,
                        "path": str(sub_dir),
                        "lang": "go",
                    }

        # --- Java: directories with .java files (packages) ---
        if has_java:
            for sub_dir in sorted(source_dir.rglob("*")):
                if not sub_dir.is_dir():
                    continue
                java_files = list(sub_dir.glob("*.java")) + list(sub_dir.glob("*.kt"))
                if not java_files:
                    continue

                try:
                    rel = sub_dir.relative_to(source_dir)
                except ValueError:
                    continue
                ctx_name = ".".join(rel.parts)
                if ctx_name and ctx_name not in contexts:
                    module_count = len(java_files)
                    total_loc = sum(
                        len((_read_safe(f) or "").splitlines()) for f in java_files
                    )
                    contexts[ctx_name] = {
                        "module_count": module_count,
                        "total_loc": total_loc,
                        "path": str(sub_dir),
                        "lang": "java",
                    }

        # --- JS/TS: directories with source files ---
        if has_js:
            js_exts = {".js", ".ts", ".jsx", ".tsx", ".mjs", ".mts"}
            for sub_dir in sorted(source_dir.rglob("*")):
                if not sub_dir.is_dir():
                    continue
                dir_str = str(sub_dir)
                if any(skip in dir_str for skip in ["node_modules", ".next", "dist", "build"]):
                    continue
                js_files = [f for f in sub_dir.glob("*") if f.suffix in js_exts and not f.name.endswith(".d.ts")]
                if not js_files:
                    continue

                try:
                    rel = sub_dir.relative_to(source_dir)
                except ValueError:
                    continue
                ctx_name = "/".join(rel.parts)
                if ctx_name and ctx_name not in contexts:
                    module_count = len(js_files)
                    total_loc = sum(
                        len((_read_safe(f) or "").splitlines()) for f in js_files
                    )
                    contexts[ctx_name] = {
                        "module_count": module_count,
                        "total_loc": total_loc,
                        "path": str(sub_dir),
                        "lang": "js/ts",
                    }

    return contexts
