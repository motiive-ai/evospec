"""EvoSpec project configuration loader."""

from pathlib import Path
from typing import Any

import yaml


CONFIG_FILENAME = "evospec.yaml"


def find_project_root(start: Path | None = None) -> Path | None:
    """Walk up from start directory to find evospec.yaml."""
    current = start or Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / CONFIG_FILENAME).exists():
            return parent
    return None


def load_config(project_root: Path | None = None) -> dict[str, Any]:
    """Load evospec.yaml from project root."""
    root = project_root or find_project_root()
    if root is None:
        return {}
    config_path = root / CONFIG_FILENAME
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def get_paths(config: dict[str, Any]) -> dict[str, str]:
    """Get configured paths with defaults."""
    paths = config.get("paths", {})
    return {
        "specs": paths.get("specs", "specs/changes"),
        "templates": paths.get("templates", "specs/_templates"),
        "adrs": paths.get("adrs", "docs/adr"),
        "domain": paths.get("domain", "specs/domain"),
        "checks": paths.get("checks", "specs/checks"),
    }
