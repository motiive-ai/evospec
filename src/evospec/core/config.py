"""EvoSpec project configuration loader.

Configuration is split across files for maintainability:

  evospec.yaml                  — project config (paths, classification, strategy, teams)
  specs/domain/entities.yaml    — domain entity registry (replaces domain.entities in evospec.yaml)
  specs/domain/contexts.yaml    — bounded contexts (replaces bounded_contexts in evospec.yaml)
  specs/domain/features.yaml    — feature lifecycle registry (replaces features in evospec.yaml)

For backwards compatibility, if domain files don't exist the loader falls back to
reading those sections from evospec.yaml.

Cross-repo sharing uses an ``upstreams`` list in evospec.yaml that references
published contracts from other repositories.
"""

from pathlib import Path
from typing import Any

import yaml


CONFIG_FILENAME = "evospec.yaml"

# Domain files that live under specs/domain/ instead of evospec.yaml
DOMAIN_FILES = {
    "entities.yaml": ("domain", "entities"),
    "contexts.yaml": ("bounded_contexts",),
    "features.yaml": ("features",),
}


def find_project_root(start: Path | None = None) -> Path | None:
    """Walk up from start directory to find evospec.yaml."""
    current = start or Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / CONFIG_FILENAME).exists():
            return parent
    return None


def load_config(project_root: Path | None = None) -> dict[str, Any]:
    """Load project configuration from evospec.yaml + domain files.

    Domain files (entities.yaml, contexts.yaml, features.yaml) in specs/domain/
    take precedence over the same keys in evospec.yaml.  This keeps evospec.yaml
    lean while allowing richer domain descriptions in dedicated files.
    """
    root = project_root or find_project_root()
    if root is None:
        return {}
    config_path = root / CONFIG_FILENAME
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    # Merge domain files
    domain_dir = root / get_paths(config)["domain"]
    _merge_domain_files(config, domain_dir)

    # Merge upstream published contracts
    _merge_upstreams(config, root)

    return config


def _merge_domain_files(config: dict, domain_dir: Path) -> None:
    """Merge specs/domain/*.yaml into config, taking precedence over evospec.yaml."""
    for filename, key_path in DOMAIN_FILES.items():
        file_path = domain_dir / filename
        if not file_path.exists():
            continue
        data = yaml.safe_load(file_path.read_text())
        if data is None:
            continue

        # Navigate to the right place in config and set the value
        if len(key_path) == 1:
            # e.g. ("features",) → config["features"] = data
            config[key_path[0]] = data
        elif len(key_path) == 2:
            # e.g. ("domain", "entities") → config["domain"]["entities"] = data
            config.setdefault(key_path[0], {})[key_path[1]] = data


def _merge_upstreams(config: dict, root: Path) -> None:
    """Merge published contracts from upstream repositories.

    evospec.yaml can declare:
        upstreams:
          - name: "order-service"
            path: "../order-service"       # relative path to sibling repo
          - name: "inventory-service"
            path: "../inventory-service"

    Each upstream's published contract (specs/domain/published-contract.yaml)
    is loaded and its entities and invariants are made available under
    config["_upstreams"][name].
    """
    upstreams = config.get("upstreams", [])
    if not upstreams:
        return

    merged: dict[str, dict] = {}
    for upstream in upstreams:
        name = upstream.get("name", "")
        rel_path = upstream.get("path", "")
        if not name or not rel_path:
            continue

        upstream_root = (root / rel_path).resolve()
        contract_path = upstream_root / "specs" / "domain" / "published-contract.yaml"

        if not contract_path.exists():
            # Fall back: try loading their full config
            upstream_config_path = upstream_root / CONFIG_FILENAME
            if upstream_config_path.exists():
                upstream_cfg = yaml.safe_load(upstream_config_path.read_text()) or {}
                upstream_domain_dir = upstream_root / get_paths(upstream_cfg).get("domain", "specs/domain")
                _merge_domain_files(upstream_cfg, upstream_domain_dir)
                merged[name] = {
                    "root": str(upstream_root),
                    "entities": upstream_cfg.get("domain", {}).get("entities", []),
                    "bounded_contexts": upstream_cfg.get("bounded_contexts", []),
                    "invariants": _collect_upstream_invariants(upstream_root, upstream_cfg),
                }
            continue

        contract = yaml.safe_load(contract_path.read_text()) or {}
        merged[name] = {
            "root": str(upstream_root),
            "entities": contract.get("entities", []),
            "bounded_contexts": contract.get("bounded_contexts", []),
            "invariants": contract.get("invariants", []),
        }

    if merged:
        config["_upstreams"] = merged


def _collect_upstream_invariants(upstream_root: Path, upstream_cfg: dict) -> list[dict]:
    """Collect all invariants from an upstream repo's core/hybrid specs."""
    specs_dir = upstream_root / get_paths(upstream_cfg).get("specs", "specs/changes")
    if not specs_dir.exists():
        return []

    invariants = []
    for spec_dir in sorted(specs_dir.iterdir()):
        spec_yaml = spec_dir / "spec.yaml"
        if not spec_yaml.exists():
            continue
        spec = yaml.safe_load(spec_yaml.read_text()) or {}
        zone = spec.get("zone", "")
        if zone not in ("core", "hybrid"):
            continue
        for inv in spec.get("invariants", []):
            inv["_spec_title"] = spec.get("title", spec_dir.name)
            inv["_spec_path"] = str(spec_dir.relative_to(upstream_root))
            inv["_bounded_context"] = spec.get("bounded_context", "")
            invariants.append(inv)

    return invariants


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
