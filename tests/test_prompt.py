"""Tests for AI Bootstrap Prompt + Deep Reverse Engineering.

Covers:
- Project stack detection (T019-T022)
- Git history graceful degradation (T023)
- CLI prompt command (T024-T026)
- JSON output validity (T025)
- Works without evospec.yaml (T026)
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from evospec.cli.main import cli
from evospec.core.prompt import (
    GitInfo,
    ProjectDetection,
    analyze_git_history,
    detect_framework,
    detect_language,
    detect_orm,
    detect_project_name,
    detect_project_stack,
    detect_source_dirs,
    generate_bootstrap_json,
    generate_bootstrap_prompt,
)


@pytest.fixture
def runner():
    return CliRunner()


# ---------------------------------------------------------------------------
# T019: Spring Boot detection
# ---------------------------------------------------------------------------


class TestSpringBootDetection:
    def test_detect_language_java(self, tmp_path):
        (tmp_path / "pom.xml").write_text(
            "<project><artifactId>order-service</artifactId></project>"
        )
        lang, build = detect_language(tmp_path)
        assert lang == "java"
        assert build == "pom.xml"

    def test_detect_framework_spring(self, tmp_path):
        (tmp_path / "pom.xml").write_text(
            "<project><dependencies>"
            "<dependency><artifactId>spring-boot-starter-web</artifactId></dependency>"
            "</dependencies></project>"
        )
        assert detect_framework(tmp_path, "java", "pom.xml") == "spring"

    def test_detect_orm_jpa(self, tmp_path):
        (tmp_path / "pom.xml").write_text(
            "<project><dependencies>"
            "<dependency><artifactId>spring-boot-starter-data-jpa</artifactId></dependency>"
            "</dependencies></project>"
        )
        assert detect_orm(tmp_path, "java", "pom.xml") == "jpa"

    def test_detect_source_dirs_java(self, tmp_path):
        (tmp_path / "src" / "main" / "java").mkdir(parents=True)
        dirs = detect_source_dirs(tmp_path, "java")
        assert "src/main/java" in dirs

    def test_detect_project_name_pom(self, tmp_path):
        (tmp_path / "pom.xml").write_text(
            "<project><artifactId>order-service</artifactId></project>"
        )
        name = detect_project_name(tmp_path, "java", "pom.xml")
        assert name == "order-service"

    def test_full_spring_boot_detection(self, tmp_path):
        (tmp_path / "pom.xml").write_text(
            "<project><artifactId>order-service</artifactId>"
            "<dependencies>"
            "<dependency><artifactId>spring-boot-starter-web</artifactId></dependency>"
            "<dependency><artifactId>spring-boot-starter-data-jpa</artifactId></dependency>"
            "</dependencies></project>"
        )
        (tmp_path / "src" / "main" / "java").mkdir(parents=True)

        det = detect_project_stack(tmp_path)
        assert det.language == "java"
        assert det.framework == "spring"
        assert det.orm == "jpa"
        assert "src/main/java" in det.source_dirs
        assert det.project_name == "order-service"


# ---------------------------------------------------------------------------
# T020: FastAPI detection
# ---------------------------------------------------------------------------


class TestFastAPIDetection:
    def test_detect_language_python(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "my-api"\ndependencies = ["fastapi"]\n'
        )
        lang, build = detect_language(tmp_path)
        assert lang == "python"
        assert build == "pyproject.toml"

    def test_detect_framework_fastapi(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "my-api"\ndependencies = ["fastapi", "uvicorn"]\n'
        )
        assert detect_framework(tmp_path, "python", "pyproject.toml") == "fastapi"

    def test_detect_framework_fastapi_requirements(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-api"\n')
        (tmp_path / "requirements.txt").write_text("fastapi>=0.100\nuvicorn\n")
        assert detect_framework(tmp_path, "python", "pyproject.toml") == "fastapi"

    def test_detect_orm_sqlalchemy(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\ndependencies = ["sqlalchemy"]\n'
        )
        assert detect_orm(tmp_path, "python", "pyproject.toml") == "sqlalchemy"

    def test_detect_source_dirs_python_src(self, tmp_path):
        pkg = tmp_path / "src" / "myapp"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        dirs = detect_source_dirs(tmp_path, "python")
        assert "src/myapp" in dirs

    def test_detect_project_name_pyproject(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "my-fastapi-app"\n'
        )
        name = detect_project_name(tmp_path, "python", "pyproject.toml")
        assert name == "my-fastapi-app"

    def test_full_fastapi_detection(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "my-api"\ndependencies = ["fastapi", "sqlalchemy"]\n'
        )
        pkg = tmp_path / "src" / "myapi"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("")

        det = detect_project_stack(tmp_path)
        assert det.language == "python"
        assert det.framework == "fastapi"
        assert det.orm == "sqlalchemy"
        assert det.project_name == "my-api"


# ---------------------------------------------------------------------------
# T021: Next.js detection
# ---------------------------------------------------------------------------


class TestNextJSDetection:
    def test_detect_language_typescript(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name": "my-app", "dependencies": {"next": "14.0"}}')
        (tmp_path / "tsconfig.json").write_text("{}")
        lang, build = detect_language(tmp_path)
        assert lang == "typescript"
        assert build == "package.json"

    def test_detect_language_javascript_no_tsconfig(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name": "my-app"}')
        lang, build = detect_language(tmp_path)
        assert lang == "javascript"

    def test_detect_framework_nextjs(self, tmp_path):
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"next": "14.0", "react": "18.0"}}'
        )
        assert detect_framework(tmp_path, "typescript", "package.json") == "nextjs"

    def test_detect_orm_prisma(self, tmp_path):
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"@prisma/client": "5.0"}, "devDependencies": {"prisma": "5.0"}}'
        )
        assert detect_orm(tmp_path, "typescript", "package.json") == "prisma"

    def test_detect_source_dirs_nextjs(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "app").mkdir()
        dirs = detect_source_dirs(tmp_path, "typescript")
        assert "src" in dirs
        assert "app" in dirs

    def test_detect_project_name_package_json(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name": "@org/my-nextjs-app"}')
        name = detect_project_name(tmp_path, "typescript", "package.json")
        assert name == "@org/my-nextjs-app"

    def test_full_nextjs_detection(self, tmp_path):
        (tmp_path / "package.json").write_text(
            '{"name": "smart-cart-ui", "dependencies": {"next": "14.0", "@prisma/client": "5.0"}}'
        )
        (tmp_path / "tsconfig.json").write_text("{}")
        (tmp_path / "src").mkdir()

        det = detect_project_stack(tmp_path)
        assert det.language == "typescript"
        assert det.framework == "nextjs"
        assert det.orm == "prisma"
        assert det.project_name == "smart-cart-ui"


# ---------------------------------------------------------------------------
# T022: Go/Gin detection
# ---------------------------------------------------------------------------


class TestGoGinDetection:
    def test_detect_language_go(self, tmp_path):
        (tmp_path / "go.mod").write_text("module github.com/org/my-service\n\ngo 1.21\n")
        lang, build = detect_language(tmp_path)
        assert lang == "go"
        assert build == "go.mod"

    def test_detect_framework_gin(self, tmp_path):
        (tmp_path / "go.mod").write_text(
            "module github.com/org/api\n\nrequire github.com/gin-gonic/gin v1.9.1\n"
        )
        assert detect_framework(tmp_path, "go", "go.mod") == "gin"

    def test_detect_orm_gorm(self, tmp_path):
        (tmp_path / "go.mod").write_text(
            "module github.com/org/api\n\nrequire gorm.io/gorm v1.25.0\n"
        )
        assert detect_orm(tmp_path, "go", "go.mod") == "gorm"

    def test_detect_source_dirs_go(self, tmp_path):
        (tmp_path / "cmd").mkdir()
        (tmp_path / "internal").mkdir()
        dirs = detect_source_dirs(tmp_path, "go")
        assert "cmd" in dirs
        assert "internal" in dirs

    def test_detect_project_name_gomod(self, tmp_path):
        (tmp_path / "go.mod").write_text("module github.com/org/my-service\n")
        name = detect_project_name(tmp_path, "go", "go.mod")
        assert name == "my-service"

    def test_full_go_gin_detection(self, tmp_path):
        (tmp_path / "go.mod").write_text(
            "module github.com/org/inventory-api\n\n"
            "require (\n"
            "\tgithub.com/gin-gonic/gin v1.9.1\n"
            "\tgorm.io/gorm v1.25.0\n"
            ")\n"
        )
        (tmp_path / "cmd").mkdir()
        (tmp_path / "internal").mkdir()

        det = detect_project_stack(tmp_path)
        assert det.language == "go"
        assert det.framework == "gin"
        assert det.orm == "gorm"
        assert det.project_name == "inventory-api"
        assert "cmd" in det.source_dirs


# ---------------------------------------------------------------------------
# T023: Git history graceful degradation
# ---------------------------------------------------------------------------


class TestGitHistoryDegradation:
    def test_no_git_binary(self, tmp_path):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = analyze_git_history(tmp_path)
        assert result is None

    def test_not_a_git_repo(self, tmp_path):
        # tmp_path is not a git repo
        result = analyze_git_history(tmp_path)
        assert result is None

    def test_git_timeout(self, tmp_path):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="git", timeout=5)):
            result = analyze_git_history(tmp_path)
        assert result is None


# ---------------------------------------------------------------------------
# T024: CLI prompt markdown output
# ---------------------------------------------------------------------------


class TestPromptCLI:
    def test_prompt_markdown_output(self, runner):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            result = runner.invoke(cli, ["prompt"])
            assert result.exit_code == 0
            assert "# EvoSpec Bootstrap" in result.output
            assert "evospec init" in result.output
            assert "CLI Reference" in result.output

    def test_prompt_with_detect(self, runner):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            # Create a package.json to detect
            Path(tmpdir, "package.json").write_text(
                '{"name": "test-app", "dependencies": {"express": "4.0"}}'
            )
            result = runner.invoke(cli, ["prompt", "--detect"])
            assert result.exit_code == 0
            assert "Detected Project Stack" in result.output
            assert "express" in result.output

    # T025: JSON format output
    def test_prompt_json_output(self, runner):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            result = runner.invoke(cli, ["prompt", "--format", "json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "evospec_version" in data
            assert "commands" in data
            assert "workflows" in data

    def test_prompt_json_with_detect(self, runner):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            Path(tmpdir, "pyproject.toml").write_text(
                '[project]\nname = "test"\ndependencies = ["fastapi"]\n'
            )
            result = runner.invoke(cli, ["prompt", "--format", "json", "--detect"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "detection" in data
            assert data["detection"]["framework"] == "fastapi"
            assert "recommended_commands" in data

    # T026: Works without evospec.yaml (BOOT-INV-001)
    def test_prompt_without_evospec_yaml(self, runner):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            # No evospec.yaml exists
            assert not Path(tmpdir, "evospec.yaml").exists()
            result = runner.invoke(cli, ["prompt"])
            assert result.exit_code == 0
            assert "# EvoSpec Bootstrap" in result.output

    def test_prompt_json_without_evospec_yaml(self, runner):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            assert not Path(tmpdir, "evospec.yaml").exists()
            result = runner.invoke(cli, ["prompt", "--format", "json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["evospec_version"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_project(self, tmp_path):
        det = detect_project_stack(tmp_path)
        assert det.language is None
        assert det.framework is None
        assert det.source_dirs == []
        assert det.project_name == tmp_path.name

    def test_multiple_build_files(self, tmp_path):
        # pom.xml has higher priority than package.json
        (tmp_path / "pom.xml").write_text("<project><artifactId>backend</artifactId></project>")
        (tmp_path / "package.json").write_text('{"name": "frontend"}')
        det = detect_project_stack(tmp_path)
        assert det.language == "java"

    def test_detect_framework_unknown_java(self, tmp_path):
        (tmp_path / "pom.xml").write_text("<project></project>")
        assert detect_framework(tmp_path, "java", "pom.xml") is None

    def test_detect_django_framework(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("django>=4.0\n")
        assert detect_framework(tmp_path, "python", "requirements.txt") == "django"

    def test_detect_express_framework(self, tmp_path):
        (tmp_path / "package.json").write_text('{"dependencies": {"express": "4.18"}}')
        assert detect_framework(tmp_path, "javascript", "package.json") == "express"

    def test_detect_nestjs_framework(self, tmp_path):
        (tmp_path / "package.json").write_text('{"dependencies": {"@nestjs/core": "10.0"}}')
        assert detect_framework(tmp_path, "typescript", "package.json") == "nestjs"

    def test_detect_echo_framework(self, tmp_path):
        (tmp_path / "go.mod").write_text("module x\nrequire github.com/labstack/echo v4\n")
        assert detect_framework(tmp_path, "go", "go.mod") == "echo"

    def test_detect_typeorm(self, tmp_path):
        (tmp_path / "package.json").write_text('{"dependencies": {"typeorm": "0.3"}}')
        assert detect_orm(tmp_path, "typescript", "package.json") == "typeorm"

    def test_detect_django_orm(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("django>=4.0\n")
        assert detect_orm(tmp_path, "python", "requirements.txt") == "django-orm"

    def test_generate_bootstrap_prompt_no_detect(self, tmp_path):
        result = generate_bootstrap_prompt(root=tmp_path, detect=False)
        assert "# EvoSpec Bootstrap" in result
        assert "Detected Project Stack" not in result

    def test_generate_bootstrap_prompt_with_detect(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name": "test", "dependencies": {"next": "14"}}')
        (tmp_path / "tsconfig.json").write_text("{}")
        result = generate_bootstrap_prompt(root=tmp_path, detect=True)
        assert "Detected Project Stack" in result
        assert "nextjs" in result

    def test_generate_bootstrap_json_valid(self, tmp_path):
        result = generate_bootstrap_json(root=tmp_path, detect=False)
        data = json.loads(result)
        assert data["evospec_version"]
        assert "init" in data["commands"]


# ---------------------------------------------------------------------------
# MCP bootstrap resource
# ---------------------------------------------------------------------------


class TestMCPBootstrap:
    def test_bootstrap_resource_exists(self):
        from evospec.mcp.server import get_bootstrap
        assert callable(get_bootstrap)
