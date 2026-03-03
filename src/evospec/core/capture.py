"""Retroactive spec generation from git history.

Analyzes git commit history to detect feature clusters via co-change coupling,
then generates retroactive EvoSpec change specs + domain artifacts.

Algorithm:
  1. Parse git log → extract (commit, files_changed) pairs
  2. Build co-change graph: nodes = files, edges = files changed in same commit
  3. Community detection via label propagation (no external deps)
  4. Label clusters from commit messages + directory structure
  5. Generate specs/changes/ entries + update entities.yaml, features.yaml

This is an edge experiment — see spec for kill criteria.
"""

import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
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
class CommitInfo:
    sha: str
    message: str
    files: list[str]
    date: str = ""


@dataclass
class FeatureCluster:
    id: int
    label: str
    files: list[str]
    commits: list[str]  # SHAs
    messages: list[str]  # commit messages
    size: int = 0
    dominant_dir: str = ""

    def __post_init__(self):
        self.size = len(self.files)
        if self.files:
            dirs = [str(Path(f).parent) for f in self.files]
            most_common = Counter(dirs).most_common(1)
            self.dominant_dir = most_common[0][0] if most_common else ""


@dataclass
class CaptureReport:
    commits_analyzed: int = 0
    files_analyzed: int = 0
    clusters: list[FeatureCluster] = field(default_factory=list)
    specs_generated: list[str] = field(default_factory=list)
    entities_found: list[str] = field(default_factory=list)
    since: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "commits_analyzed": self.commits_analyzed,
            "files_analyzed": self.files_analyzed,
            "since": self.since,
            "clusters": [
                {
                    "id": c.id,
                    "label": c.label,
                    "files": c.files,
                    "size": c.size,
                    "dominant_dir": c.dominant_dir,
                    "commit_count": len(c.commits),
                }
                for c in self.clusters
            ],
            "specs_generated": self.specs_generated,
            "entities_found": self.entities_found,
        }


# ---------------------------------------------------------------------------
# Git history parsing
# ---------------------------------------------------------------------------


def _run_git(args: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=str(cwd),
            timeout=60,
        )
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def _parse_git_log(root: Path, since: str | None = None) -> list[CommitInfo]:
    """Parse git log into structured commit data."""
    args = ["log", "--name-only", "--pretty=format:__COMMIT__%H|%s|%ai"]
    if since:
        args.append(f"{since}..HEAD")

    output = _run_git(args, root)
    if not output.strip():
        return []

    commits: list[CommitInfo] = []
    current: CommitInfo | None = None

    for line in output.split("\n"):
        if line.startswith("__COMMIT__"):
            if current and current.files:
                commits.append(current)
            parts = line[len("__COMMIT__"):].split("|", 2)
            sha = parts[0] if len(parts) > 0 else ""
            msg = parts[1] if len(parts) > 1 else ""
            dt = parts[2].split()[0] if len(parts) > 2 else ""
            current = CommitInfo(sha=sha, message=msg, files=[], date=dt)
        elif line.strip() and current is not None:
            f = line.strip()
            # Filter to source files
            if _is_source_file(f):
                current.files.append(f)

    if current and current.files:
        commits.append(current)

    return commits


def _is_source_file(path: str) -> bool:
    """Check if a file is a source file (not config, docs, etc.)."""
    source_exts = {
        ".py", ".java", ".kt", ".go", ".ts", ".tsx", ".js", ".jsx",
        ".rs", ".rb", ".php", ".cs", ".swift", ".scala",
    }
    p = Path(path)
    if p.suffix not in source_exts:
        return False
    # Exclude common non-feature paths
    skip_prefixes = ("test", "spec", "docs", "vendor", "node_modules", ".git", "__pycache__")
    parts = p.parts
    return not any(part.lower().startswith(skip) for skip in skip_prefixes for part in parts)


# ---------------------------------------------------------------------------
# Co-change graph + community detection
# ---------------------------------------------------------------------------


def _build_cochange_graph(commits: list[CommitInfo]) -> dict[str, dict[str, int]]:
    """Build weighted co-change graph: files that change together get edges.

    Returns adjacency dict: {file_a: {file_b: weight, ...}, ...}
    Weight = number of commits where both files changed.
    """
    graph: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for commit in commits:
        files = commit.files
        for i, f1 in enumerate(files):
            for f2 in files[i + 1:]:
                graph[f1][f2] += 1
                graph[f2][f1] += 1
            # Ensure isolated files appear as nodes
            if f1 not in graph:
                graph[f1] = defaultdict(int)

    return dict(graph)


def _label_propagation(
    graph: dict[str, dict[str, int]],
    max_iterations: int = 50,
) -> dict[str, int]:
    """Simple label propagation community detection.

    No external dependencies. Each node starts with its own label,
    then iteratively adopts the most common label among neighbors (weighted).
    Deterministic: breaks ties by smallest label.
    """
    nodes = sorted(graph.keys())
    labels = {node: i for i, node in enumerate(nodes)}

    for _ in range(max_iterations):
        changed = False
        for node in nodes:
            neighbors = graph.get(node, {})
            if not neighbors:
                continue

            # Count weighted neighbor labels
            label_weights: dict[int, int] = defaultdict(int)
            for neighbor, weight in neighbors.items():
                label_weights[labels[neighbor]] += weight

            if not label_weights:
                continue

            # Pick label with highest weight, break ties by smallest label
            max_weight = max(label_weights.values())
            best_label = min(
                lbl for lbl, w in label_weights.items() if w == max_weight
            )

            if labels[node] != best_label:
                labels[node] = best_label
                changed = True

        if not changed:
            break

    return labels


def _form_clusters(
    labels: dict[str, int],
    commits: list[CommitInfo],
    min_cluster_size: int = 2,
) -> list[FeatureCluster]:
    """Group files by label, enrich with commit data."""
    # Group files by label
    groups: dict[int, list[str]] = defaultdict(list)
    for file, label in labels.items():
        groups[label].append(file)

    # Build file→commits lookup
    file_commits: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for commit in commits:
        for f in commit.files:
            file_commits[f].append((commit.sha, commit.message))

    clusters: list[FeatureCluster] = []
    for label_id, files in sorted(groups.items()):
        if len(files) < min_cluster_size:
            continue

        # Collect unique commits touching this cluster
        seen_shas: set[str] = set()
        cluster_commits: list[str] = []
        cluster_messages: list[str] = []
        for f in files:
            for sha, msg in file_commits.get(f, []):
                if sha not in seen_shas:
                    seen_shas.add(sha)
                    cluster_commits.append(sha)
                    cluster_messages.append(msg)

        cluster_label = _generate_cluster_label(files, cluster_messages)

        clusters.append(FeatureCluster(
            id=label_id,
            label=cluster_label,
            files=sorted(files),
            commits=cluster_commits,
            messages=cluster_messages,
        ))

    # Sort by size descending
    clusters.sort(key=lambda c: c.size, reverse=True)
    return clusters


# ---------------------------------------------------------------------------
# Cluster labeling
# ---------------------------------------------------------------------------


# Common conventional commit prefixes
_COMMIT_TYPE_RE = re.compile(
    r"^(?:feat|fix|refactor|chore|docs|test|style|perf|ci|build)"
    r"(?:\(([^)]+)\))?:\s*(.+)",
    re.IGNORECASE,
)


def _generate_cluster_label(files: list[str], messages: list[str]) -> str:
    """Generate a human-readable label for a feature cluster.

    Strategy:
      1. Try conventional commit scope (e.g., "feat(auth): ..." → "auth")
      2. Try most common directory name
      3. Fallback: most common filename stem
    """
    # Strategy 1: conventional commit scopes
    scopes: list[str] = []
    topics: list[str] = []
    for msg in messages:
        m = _COMMIT_TYPE_RE.match(msg)
        if m:
            if m.group(1):
                scopes.append(m.group(1).lower())
            topics.append(m.group(2).strip().lower())

    if scopes:
        most_common = Counter(scopes).most_common(1)[0][0]
        return _clean_label(most_common)

    # Strategy 2: directory structure
    dirs = []
    for f in files:
        parts = Path(f).parts
        # Skip top-level dirs like "src", "app", "lib"
        meaningful = [p for p in parts[:-1] if p.lower() not in ("src", "app", "lib", "main", "java", "kotlin")]
        if meaningful:
            dirs.append(meaningful[-1])

    if dirs:
        most_common = Counter(dirs).most_common(1)[0][0]
        return _clean_label(most_common)

    # Strategy 3: common topic words from commit messages
    if topics:
        words = []
        for topic in topics[:10]:
            words.extend(w for w in topic.split() if len(w) > 3)
        if words:
            most_common = Counter(words).most_common(1)[0][0]
            return _clean_label(most_common)

    # Fallback: first file's parent dir
    if files:
        return _clean_label(Path(files[0]).parent.name or "cluster")

    return "unknown"


def _clean_label(label: str) -> str:
    """Clean and normalize a label string."""
    label = re.sub(r"[^a-zA-Z0-9_\-]", "-", label.lower())
    label = re.sub(r"-+", "-", label).strip("-")
    return label or "feature"


# ---------------------------------------------------------------------------
# Spec generation
# ---------------------------------------------------------------------------


def _generate_retroactive_specs(
    clusters: list[FeatureCluster],
    root: Path,
    config: dict,
) -> list[Path]:
    """Generate retroactive change specs from feature clusters."""
    paths_cfg = get_paths(config)
    specs_dir = root / paths_cfg["specs"]
    created: list[Path] = []

    today = date.today().isoformat()

    for cluster in clusters:
        slug = f"retroactive-{cluster.label}"
        spec_dir = specs_dir / slug
        spec_dir.mkdir(parents=True, exist_ok=True)

        # spec.yaml
        spec_data = {
            "id": slug,
            "title": f"Retroactive: {cluster.label.replace('-', ' ').title()}",
            "zone": "edge",
            "change_type": "experiment",
            "status": "draft",
            "created_at": today,
            "updated_at": today,
            "retroactive": True,
            "classification": {
                "touches_persistence": False,
                "touches_auth": False,
                "touches_billing": False,
                "touches_audit": False,
                "touches_multi_tenancy": False,
                "hypothesis_driven": False,
                "reversibility": "trivial",
                "risk_level": "low",
                "rationale": f"Auto-generated from git history by evospec capture --from-history. "
                             f"Cluster of {cluster.size} files across {len(cluster.commits)} commits.",
            },
            "traceability": {
                "endpoints": [],
                "tables": [],
                "modules": _extract_modules(cluster.files),
                "events": [],
                "migrations": [],
            },
            "discovery": {
                "outcome": f"Feature cluster detected from git co-change analysis: {cluster.label}",
                "opportunity": "Retroactive spec — curate and promote to hybrid/core if needed",
                "kill_criteria": "",
                "assumptions": [],
            },
        }

        spec_path = spec_dir / "spec.yaml"
        spec_path.write_text(
            yaml.dump(spec_data, default_flow_style=False, sort_keys=False, allow_unicode=True)
        )
        created.append(spec_path)

        # discovery-spec.md
        lines = [
            f"# Discovery Spec: {cluster.label.replace('-', ' ').title()} (retroactive)",
            "",
            f"> Auto-generated by `evospec capture --from-history` on {today}",
            f"> Cluster: {cluster.size} files, {len(cluster.commits)} commits",
            "",
            "## Files",
            "",
        ]
        for f in cluster.files[:30]:
            lines.append(f"- `{f}`")
        if len(cluster.files) > 30:
            lines.append(f"- ... and {len(cluster.files) - 30} more")

        lines += [
            "",
            "## Sample Commits",
            "",
        ]
        for sha, msg in zip(cluster.commits[:10], cluster.messages[:10]):
            lines.append(f"- `{sha[:8]}` {msg}")
        if len(cluster.commits) > 10:
            lines.append(f"- ... and {len(cluster.commits) - 10} more")

        lines += [
            "",
            "## Suggested Actions",
            "",
            "1. Review the files and commits above — does this cluster represent a real feature?",
            "2. If yes: rename the spec, add invariants, promote to hybrid/core",
            "3. If no: delete this spec directory",
            "",
        ]

        disc_path = spec_dir / "discovery-spec.md"
        disc_path.write_text("\n".join(lines))
        created.append(disc_path)

    return created


def _extract_modules(files: list[str]) -> list[str]:
    """Extract Python module paths from file paths."""
    modules: list[str] = []
    for f in files:
        p = Path(f)
        if p.suffix == ".py" and p.stem != "__init__":
            # Convert path to module: src/foo/bar.py → foo.bar
            parts = list(p.with_suffix("").parts)
            if parts and parts[0] in ("src", "lib", "app"):
                parts = parts[1:]
            modules.append(".".join(parts))
    return modules[:10]  # Cap at 10


# ---------------------------------------------------------------------------
# Entity extraction from clusters
# ---------------------------------------------------------------------------


_CLASS_RE = re.compile(
    r"class\s+(\w+)\s*[(:{\[]"
)
_GO_STRUCT_RE = re.compile(
    r"type\s+(\w+)\s+struct\s*\{"
)


def _extract_entities_from_clusters(
    clusters: list[FeatureCluster],
    root: Path,
) -> list[dict]:
    """Scan files in clusters for entity/model class definitions."""
    entities: list[dict] = []
    seen: set[str] = set()

    for cluster in clusters:
        for f in cluster.files:
            fp = root / f
            if not fp.exists():
                continue
            try:
                content = fp.read_text(errors="ignore")
            except OSError:
                continue

            for pattern in [_CLASS_RE, _GO_STRUCT_RE]:
                for m in pattern.finditer(content):
                    name = m.group(1)
                    # Filter out test classes, base classes, mixins
                    if (
                        name.lower() in seen
                        or name.startswith("Test")
                        or name.startswith("_")
                        or name.endswith("Mixin")
                        or name.endswith("Base")
                        or name in ("Meta", "Config", "Settings", "Admin")
                    ):
                        continue
                    seen.add(name.lower())
                    entities.append({
                        "name": name,
                        "context": cluster.label,
                        "table": "",
                        "aggregate_root": False,
                        "description": f"Auto-detected in cluster '{cluster.label}' from {f}",
                        "fields": [],
                        "relationships": [],
                        "invariants": [],
                    })

    return entities


# ---------------------------------------------------------------------------
# Update domain files
# ---------------------------------------------------------------------------


def _update_entities_yaml(
    new_entities: list[dict],
    root: Path,
    config: dict,
) -> Path | None:
    """Append new entities to entities.yaml (without duplicating)."""
    paths_cfg = get_paths(config)
    domain_dir = root / paths_cfg["domain"]
    entities_path = domain_dir / "entities.yaml"

    existing: list[dict] = []
    if entities_path.exists():
        raw = yaml.safe_load(entities_path.read_text())
        if isinstance(raw, list):
            existing = raw

    existing_names = {e.get("name", "").lower() for e in existing}

    added = [e for e in new_entities if e["name"].lower() not in existing_names]
    if not added:
        return None

    all_entities = existing + added
    domain_dir.mkdir(parents=True, exist_ok=True)
    entities_path.write_text(
        yaml.dump(all_entities, default_flow_style=False, sort_keys=False, allow_unicode=True)
    )
    return entities_path


def _update_features_yaml(
    clusters: list[FeatureCluster],
    root: Path,
    config: dict,
) -> Path | None:
    """Add feature entries for each cluster."""
    paths_cfg = get_paths(config)
    domain_dir = root / paths_cfg["domain"]
    features_path = domain_dir / "features.yaml"

    existing: list[dict] = []
    if features_path.exists():
        raw = yaml.safe_load(features_path.read_text())
        if isinstance(raw, list):
            existing = raw

    # Find max existing id number
    max_id = 0
    for f in existing:
        fid = f.get("id", "")
        m = re.search(r"(\d+)", fid)
        if m:
            max_id = max(max_id, int(m.group(1)))

    today = date.today().isoformat()
    added = []
    for cluster in clusters:
        max_id += 1
        added.append({
            "id": f"feat-{max_id:03d}",
            "title": f"Retroactive: {cluster.label.replace('-', ' ').title()}",
            "zone": "edge",
            "status": "discovered",
            "knowledge_stage": "mystery",
            "spec_path": f"specs/changes/retroactive-{cluster.label}",
            "owner": "",
            "created_at": today,
            "shipped_at": "",
            "kill_reason": "",
        })

    if not added:
        return None

    all_features = existing + added
    domain_dir.mkdir(parents=True, exist_ok=True)
    features_path.write_text(
        yaml.dump(all_features, default_flow_style=False, sort_keys=False, allow_unicode=True)
    )
    return features_path


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_capture_from_history(
    *,
    since: str | None = None,
    min_cluster_size: int = 2,
    max_clusters: int = 20,
) -> CaptureReport:
    """Run retroactive spec generation from git history.

    Args:
        since: Git ref to start analysis from. If None, analyzes all history.
        min_cluster_size: Minimum files in a cluster to keep it.
        max_clusters: Maximum clusters to generate specs for.

    Returns:
        CaptureReport with analysis results.
    """
    root = find_project_root()
    if root is None:
        console.print("[red]ERROR:[/] No evospec.yaml found. Run `evospec init` first.")
        return CaptureReport()

    config = load_config(root)

    # Step 1: Parse git history
    console.print(f"[bold]Analyzing git history{' since ' + since if since else ''}...[/]")
    commits = _parse_git_log(root, since)
    if not commits:
        console.print("[yellow]No commits with source files found.[/]")
        return CaptureReport(since=since or "all")

    all_files = {f for c in commits for f in c.files}
    console.print(f"  Found {len(commits)} commit(s) touching {len(all_files)} source file(s)")

    # Step 2: Build co-change graph
    console.print("[bold]Building co-change graph...[/]")
    graph = _build_cochange_graph(commits)
    console.print(f"  {len(graph)} nodes, "
                  f"{sum(len(v) for v in graph.values()) // 2} edges")

    # Step 3: Community detection
    console.print("[bold]Detecting feature clusters...[/]")
    labels = _label_propagation(graph)
    clusters = _form_clusters(labels, commits, min_cluster_size=min_cluster_size)

    # Cap clusters
    clusters = clusters[:max_clusters]
    console.print(f"  Found {len(clusters)} cluster(s)")

    if not clusters:
        console.print("[yellow]No meaningful clusters detected.[/]")
        return CaptureReport(
            commits_analyzed=len(commits),
            files_analyzed=len(all_files),
            since=since or "all",
        )

    # Print clusters
    console.print()
    for i, cluster in enumerate(clusters):
        console.print(f"  [bold cyan]Cluster {i+1}:[/] {cluster.label} "
                      f"({cluster.size} files, {len(cluster.commits)} commits)")
        console.print(f"    Primary dir: {cluster.dominant_dir}")
        for f in cluster.files[:5]:
            console.print(f"    - {f}")
        if cluster.size > 5:
            console.print(f"    ... and {cluster.size - 5} more")
        console.print()

    # Step 4: Generate specs
    console.print("[bold]Generating retroactive specs...[/]")
    created_specs = _generate_retroactive_specs(clusters, root, config)
    spec_names = [str(p.relative_to(root)) for p in created_specs]

    # Step 5: Extract entities
    console.print("[bold]Extracting entities from code...[/]")
    new_entities = _extract_entities_from_clusters(clusters, root)
    entities_path = _update_entities_yaml(new_entities, root, config)
    entity_names = [e["name"] for e in new_entities]
    if entities_path:
        console.print(f"  Added {len(new_entities)} entities to {entities_path.relative_to(root)}")

    # Step 6: Update features
    features_path = _update_features_yaml(clusters, root, config)
    if features_path:
        console.print(f"  Added {len(clusters)} features to {features_path.relative_to(root)}")

    # Summary
    console.print()
    console.print("[bold green]Done![/]")
    console.print(f"  {len(clusters)} feature cluster(s) → {len(created_specs) // 2} spec(s) generated")
    console.print(f"  {len(new_entities)} entit(ies) discovered")
    console.print()
    console.print("[dim]Review generated specs in specs/changes/retroactive-* and curate.[/dim]")

    return CaptureReport(
        commits_analyzed=len(commits),
        files_analyzed=len(all_files),
        clusters=clusters,
        specs_generated=spec_names,
        entities_found=entity_names,
        since=since or "all",
    )
