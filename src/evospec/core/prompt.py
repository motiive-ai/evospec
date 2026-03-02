"""AI Bootstrap Prompt generation and project stack detection.

Provides `evospec prompt [--detect]` — a self-contained bootstrap prompt that
gives any AI agent full EvoSpec context without reading source code.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader
from rich.console import Console

from evospec import __version__

console = Console()

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "prompts"

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class GitInfo:
    """Git history analysis results."""

    recent_commits: int = 0
    contributors: list[str] = field(default_factory=list)
    hot_files: list[str] = field(default_factory=list)
    primary_language_pct: float = 0.0


@dataclass
class ProjectDetection:
    """Auto-detected project stack information."""

    language: str | None = None
    framework: str | None = None
    source_dirs: list[str] = field(default_factory=list)
    orm: str | None = None
    project_name: str | None = None
    build_file: str | None = None
    git_info: GitInfo | None = None


# ---------------------------------------------------------------------------
# Build file → language mapping
# ---------------------------------------------------------------------------

_BUILD_FILES: dict[str, str] = {
    "pom.xml": "java",
    "build.gradle": "java",
    "build.gradle.kts": "java",
    "package.json": "javascript",
    "go.mod": "go",
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "setup.py": "python",
    "Cargo.toml": "rust",
    "Gemfile": "ruby",
}


# ---------------------------------------------------------------------------
# Detection functions (T003-T008)
# ---------------------------------------------------------------------------


def detect_language(root: Path) -> tuple[str | None, str | None]:
    """Scan for build files and return (language, build_file).

    Returns the first match in priority order. TypeScript is promoted over
    JavaScript when tsconfig.json is present.
    """
    for build_file, lang in _BUILD_FILES.items():
        if (root / build_file).exists():
            # Promote JS → TS when tsconfig exists
            if lang == "javascript" and (root / "tsconfig.json").exists():
                lang = "typescript"
            return lang, build_file
    return None, None


def detect_framework(root: Path, language: str | None, build_file: str | None) -> str | None:
    """Parse build file dependencies to identify the framework."""
    if not language or not build_file:
        return None

    build_path = root / build_file

    if language == "java":
        return _detect_java_framework(build_path)
    elif language in ("python",):
        return _detect_python_framework(root, build_path)
    elif language in ("javascript", "typescript"):
        return _detect_js_framework(build_path)
    elif language == "go":
        return _detect_go_framework(build_path)

    return None


def _detect_java_framework(build_path: Path) -> str | None:
    """Detect Java framework from pom.xml or build.gradle."""
    content = build_path.read_text()
    if "spring-boot" in content or "spring-boot-starter" in content:
        return "spring"
    return None


def _detect_python_framework(root: Path, build_path: Path) -> str | None:
    """Detect Python framework from pyproject.toml or requirements.txt."""
    content = build_path.read_text()
    # Also check requirements.txt if pyproject.toml doesn't have deps
    req_path = root / "requirements.txt"
    req_content = req_path.read_text() if req_path.exists() else ""
    combined = content + "\n" + req_content

    if "fastapi" in combined.lower():
        return "fastapi"
    if "django" in combined.lower():
        return "django"
    if "flask" in combined.lower():
        return "flask"
    return None


def _detect_js_framework(build_path: Path) -> str | None:
    """Detect JS/TS framework from package.json."""
    try:
        pkg = json.loads(build_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    all_deps = {}
    all_deps.update(pkg.get("dependencies", {}))
    all_deps.update(pkg.get("devDependencies", {}))

    if "next" in all_deps:
        return "nextjs"
    if "@nestjs/core" in all_deps:
        return "nestjs"
    if "hono" in all_deps:
        return "hono"
    if "fastify" in all_deps:
        return "fastify"
    if "express" in all_deps:
        return "express"
    return None


def _detect_go_framework(build_path: Path) -> str | None:
    """Detect Go framework from go.mod."""
    content = build_path.read_text()
    if "github.com/gin-gonic/gin" in content:
        return "gin"
    if "github.com/labstack/echo" in content:
        return "echo"
    if "github.com/gofiber/fiber" in content:
        return "fiber"
    if "github.com/go-chi/chi" in content:
        return "chi"
    return None


def detect_orm(root: Path, language: str | None, build_file: str | None) -> str | None:
    """Identify ORM from dependencies or common file patterns."""
    if not language or not build_file:
        return None

    build_path = root / build_file

    if language == "java":
        content = build_path.read_text()
        if "spring-boot-starter-data-jpa" in content or "hibernate" in content.lower():
            return "jpa"

    elif language == "python":
        combined = build_path.read_text()
        req_path = root / "requirements.txt"
        if req_path.exists():
            combined += "\n" + req_path.read_text()
        if "sqlalchemy" in combined.lower():
            return "sqlalchemy"
        if "django" in combined.lower():
            return "django-orm"

    elif language in ("javascript", "typescript"):
        try:
            pkg = json.loads(build_path.read_text())
        except (json.JSONDecodeError, OSError):
            return None
        all_deps = {}
        all_deps.update(pkg.get("dependencies", {}))
        all_deps.update(pkg.get("devDependencies", {}))
        if "prisma" in all_deps or "@prisma/client" in all_deps:
            return "prisma"
        if "typeorm" in all_deps:
            return "typeorm"
        if "sequelize" in all_deps:
            return "sequelize"

    elif language == "go":
        content = build_path.read_text()
        if "gorm.io/gorm" in content:
            return "gorm"

    return None


def detect_source_dirs(root: Path, language: str | None) -> list[str]:
    """Detect source directories by language convention."""
    candidates: list[str] = []

    if language == "java":
        for d in ["src/main/java", "src/main/kotlin"]:
            if (root / d).exists():
                candidates.append(d)
    elif language == "python":
        # Check for src layout or flat layout
        if (root / "src").exists():
            for child in (root / "src").iterdir():
                if child.is_dir() and (child / "__init__.py").exists():
                    candidates.append(str(child.relative_to(root)))
        if not candidates:
            for child in root.iterdir():
                if child.is_dir() and (child / "__init__.py").exists() and child.name not in ("tests", "test", "docs", "."):
                    candidates.append(child.name)
    elif language in ("javascript", "typescript"):
        for d in ["src", "app", "lib", "pages"]:
            if (root / d).exists():
                candidates.append(d)
    elif language == "go":
        for d in ["cmd", "internal", "pkg"]:
            if (root / d).exists():
                candidates.append(d)
        if not candidates:
            candidates.append(".")

    return candidates


def detect_project_name(root: Path, language: str | None, build_file: str | None) -> str | None:
    """Extract project name from build file metadata."""
    if not build_file:
        return root.name  # fallback to directory name

    build_path = root / build_file

    if build_file == "package.json":
        try:
            pkg = json.loads(build_path.read_text())
            return pkg.get("name")
        except (json.JSONDecodeError, OSError):
            pass

    elif build_file == "pyproject.toml":
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]
        try:
            data = tomllib.loads(build_path.read_text())
            name = data.get("project", {}).get("name") or data.get("tool", {}).get("poetry", {}).get("name")
            if name:
                return name
        except Exception:
            pass

    elif build_file == "pom.xml":
        content = build_path.read_text()
        # Simple XML extraction (no lxml dependency)
        import re
        m = re.search(r"<artifactId>([^<]+)</artifactId>", content)
        if m:
            return m.group(1)

    elif build_file == "go.mod":
        first_line = build_path.read_text().split("\n")[0]
        if first_line.startswith("module "):
            module = first_line.split(" ", 1)[1].strip()
            return module.rsplit("/", 1)[-1]

    return root.name


def detect_project_stack(root: Path) -> ProjectDetection:
    """Orchestrate all detection functions into a single ProjectDetection result."""
    language, build_file = detect_language(root)
    framework = detect_framework(root, language, build_file)
    orm = detect_orm(root, language, build_file)
    source_dirs = detect_source_dirs(root, language)
    project_name = detect_project_name(root, language, build_file)

    return ProjectDetection(
        language=language,
        framework=framework,
        source_dirs=source_dirs,
        orm=orm,
        project_name=project_name,
        build_file=build_file,
    )


# ---------------------------------------------------------------------------
# Git history analysis (T009-T010)
# ---------------------------------------------------------------------------


def analyze_git_history(root: Path) -> GitInfo | None:
    """Analyze git history for project context.

    Returns None if git is not available or this is not a git repo (BOOT-INV-002).
    """
    try:
        # Check if git is available and this is a repo
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, cwd=str(root), timeout=5,
        )
        if result.returncode != 0:
            return None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None

    info = GitInfo()

    # Recent commits (last 30 days)
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--since=30.days", "--format=%H"],
            capture_output=True, text=True, cwd=str(root), timeout=10,
        )
        if result.returncode == 0:
            info.recent_commits = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
    except (subprocess.TimeoutExpired, OSError):
        pass

    # Contributors
    try:
        result = subprocess.run(
            ["git", "log", "--format=%aN", "--since=90.days"],
            capture_output=True, text=True, cwd=str(root), timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            info.contributors = sorted(set(result.stdout.strip().split("\n")))
    except (subprocess.TimeoutExpired, OSError):
        pass

    # Hot files (most changed in last 20 commits)
    try:
        result = subprocess.run(
            ["git", "log", "--pretty=format:", "--name-only", "-20"],
            capture_output=True, text=True, cwd=str(root), timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            files = [f for f in result.stdout.strip().split("\n") if f.strip()]
            from collections import Counter
            counts = Counter(files)
            info.hot_files = [f for f, _ in counts.most_common(10)]
    except (subprocess.TimeoutExpired, OSError):
        pass

    # Primary language percentage (from git)
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, cwd=str(root), timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            all_files = result.stdout.strip().split("\n")
            ext_counts: dict[str, int] = {}
            for f in all_files:
                ext = Path(f).suffix
                if ext:
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1
            total = sum(ext_counts.values())
            if total > 0 and ext_counts:
                max_ext = max(ext_counts, key=ext_counts.get)  # type: ignore[arg-type]
                info.primary_language_pct = round(ext_counts[max_ext] / total * 100, 1)
    except (subprocess.TimeoutExpired, OSError):
        pass

    return info


# ---------------------------------------------------------------------------
# Prompt generation (T012-T013)
# ---------------------------------------------------------------------------


def generate_bootstrap_prompt(
    root: Path | None = None,
    detect: bool = False,
) -> str:
    """Generate the bootstrap prompt as markdown.

    Args:
        root: Project root for detection. If None, uses cwd.
        detect: Whether to run project detection.
    """
    root = root or Path.cwd()

    detection: ProjectDetection | None = None
    if detect:
        detection = detect_project_stack(root)
        detection.git_info = analyze_git_history(root)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
    )
    template = env.get_template("bootstrap.md")

    return template.render(
        version=__version__,
        detection=detection,
        detect=detect,
    )


def generate_bootstrap_json(
    root: Path | None = None,
    detect: bool = False,
) -> str:
    """Generate the bootstrap prompt as structured JSON (BOOT-INV-004).

    Args:
        root: Project root for detection. If None, uses cwd.
        detect: Whether to run project detection.
    """
    root = root or Path.cwd()

    detection: ProjectDetection | None = None
    if detect:
        detection = detect_project_stack(root)
        detection.git_info = analyze_git_history(root)

    data: dict[str, Any] = {
        "evospec_version": __version__,
        "description": "EvoSpec: Progressive specs at the edge. Contracts in the core.",
        "commands": {
            "init": "evospec init \"project-name\"",
            "new_spec": "evospec new \"title\" --zone edge|hybrid|core",
            "check": "evospec check",
            "reverse_api": "evospec reverse api --framework <framework>",
            "reverse_db": "evospec reverse db --source <dir>",
            "reverse_cli": "evospec reverse cli --source <dir>",
            "generate_agents": "evospec generate agents",
            "status": "evospec status",
            "fitness": "evospec fitness",
        },
        "workflows": [
            "/evospec.discover", "/evospec.improve", "/evospec.fix",
            "/evospec.contract", "/evospec.tasks", "/evospec.implement",
            "/evospec.learn", "/evospec.check", "/evospec.adr", "/evospec.capture",
        ],
        "post_init_files": [
            "evospec.yaml",
            "CLAUDE.md",
            ".windsurf/workflows/evospec.*.md",
            ".cursor/rules/evospec*.mdc",
            "specs/domain/entities.yaml",
            "specs/domain/contexts.yaml",
            "specs/domain/glossary.md",
        ],
    }

    if detection:
        det_dict = asdict(detection)
        # Remove None values for cleaner output
        det_dict = {k: v for k, v in det_dict.items() if v is not None}
        data["detection"] = det_dict

        # Add recommended commands based on detection
        recommended: list[str] = []
        recommended.append(f'evospec init "{detection.project_name or "my-project"}"')
        if detection.framework:
            recommended.append(f"evospec reverse api --framework {detection.framework}")
        if detection.source_dirs:
            recommended.append(f"evospec reverse db --source {detection.source_dirs[0]}")
            recommended.append(f"evospec reverse cli --source {detection.source_dirs[0]}")
        recommended.append("evospec generate agents")
        data["recommended_commands"] = recommended

    return json.dumps(data, indent=2)
