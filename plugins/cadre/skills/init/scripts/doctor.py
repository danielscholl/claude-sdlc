#!/usr/bin/env python3
"""Validate the integrity of a .claude/cadre/ setup.

Checks:
- Required files exist
- config.yaml is valid YAML with expected structure
- All agents referenced in routing exist as .md files
- All agent .md files are referenced in config.yaml
- CLAUDE.md has the cadre section
- decisions.md exists

Usage:
    python doctor.py [project_dir]

Exits 0 if healthy, 1 if issues found. Outputs JSON report.
"""

import json
import sys
from pathlib import Path


def check_file_exists(path: Path, description: str) -> dict:
    """Check if a file exists and return a check result."""
    exists = path.exists()
    return {
        "check": f"{description} exists",
        "path": str(path),
        "status": "pass" if exists else "fail",
        "message": "" if exists else f"Missing: {path}",
    }


def _parse_config_agents(content: str) -> set:
    """Extract agent names from the top-level agents: section of config.yaml."""
    config_agents = set()
    in_agents = False
    for line in content.splitlines():
        stripped = line.strip()
        if line.startswith("agents:"):
            in_agents = True
            continue
        if in_agents:
            if line and not line[0].isspace() and ":" in line:
                in_agents = False
                continue
            if stripped.startswith("- name:"):
                name = stripped.split(":", 1)[1].strip()
                config_agents.add(name)
    return config_agents


def _parse_routing_agents(content: str) -> set:
    """Extract agent names from routing rules in config.yaml.

    Distinguishes per-rule 'agents:' (indented) from the top-level 'agents:' section
    by checking indentation level.
    """
    in_routing = False
    in_rule_agents = False
    routing_agents = set()
    for line in content.splitlines():
        stripped = line.strip()
        if line.startswith("routing:"):
            in_routing = True
            continue
        if in_routing:
            if line and not line[0].isspace() and ":" in line:
                in_routing = False
                continue
            # Per-rule agents: is always indented (4+ spaces)
            if stripped == "agents:" and len(line) > len(stripped):
                in_rule_agents = True
                continue
            if in_rule_agents and stripped.startswith("- "):
                name = stripped[2:].strip()
                routing_agents.add(name)
            elif in_rule_agents and not stripped.startswith("-"):
                in_rule_agents = False
    return routing_agents


def check_config_yaml(project_dir: Path) -> list:
    """Validate config.yaml structure."""
    checks = []
    config_path = project_dir / ".claude" / "cadre" / "config.yaml"

    if not config_path.exists():
        checks.append({
            "check": "config.yaml exists",
            "status": "fail",
            "message": f"Missing: {config_path}",
        })
        return checks

    checks.append({
        "check": "config.yaml exists",
        "status": "pass",
    })

    content = config_path.read_text()

    # Basic YAML structure checks (without importing yaml)
    has_name = "name:" in content
    has_agents = "agents:" in content
    has_routing = "routing:" in content
    has_settings = "settings:" in content

    for field, present in [("name", has_name), ("agents", has_agents),
                           ("routing", has_routing), ("settings", has_settings)]:
        checks.append({
            "check": f"config.yaml has '{field}' field",
            "status": "pass" if present else "warn",
            "message": "" if present else f"Missing '{field}' in config.yaml",
        })

    return checks


def check_agents(project_dir: Path) -> list:
    """Validate agent files match config references."""
    checks = []
    agents_dir = project_dir / ".claude" / "agents"
    config_path = project_dir / ".claude" / "cadre" / "config.yaml"

    # Collect agent names from config.yaml
    config_agents = set()
    if config_path.exists():
        config_agents = _parse_config_agents(config_path.read_text())

    # Collect agent .md files
    file_agents = set()
    if agents_dir.exists():
        for f in agents_dir.iterdir():
            if f.suffix == ".md" and f.is_file():
                file_agents.add(f.stem)

    # Check agents in config have files
    for name in sorted(config_agents):
        has_file = name in file_agents
        checks.append({
            "check": f"Agent '{name}' has .md file",
            "status": "pass" if has_file else "fail",
            "message": "" if has_file else f"Missing .claude/agents/{name}.md",
        })

    # Check orphan agent files (files without config entry)
    orphans = file_agents - config_agents
    for name in sorted(orphans):
        checks.append({
            "check": f"Agent file '{name}.md' referenced in config",
            "status": "warn",
            "message": f"Orphan agent file: .claude/agents/{name}.md (not in config.yaml)",
        })

    return checks


def check_routing_agents(project_dir: Path) -> list:
    """Validate all agents in routing rules exist."""
    checks = []
    config_path = project_dir / ".claude" / "cadre" / "config.yaml"

    if not config_path.exists():
        return checks

    content = config_path.read_text()
    config_agents = _parse_config_agents(content)
    routing_agents = _parse_routing_agents(content)

    # Check routing agents exist in config
    for name in sorted(routing_agents):
        exists = name in config_agents
        checks.append({
            "check": f"Routing agent '{name}' defined in config",
            "status": "pass" if exists else "fail",
            "message": "" if exists else f"Routing references unknown agent: {name}",
        })

    return checks


def check_claude_md(project_dir: Path) -> list:
    """Validate CLAUDE.md has cadre section."""
    checks = []
    claude_md = project_dir / ".claude" / "CLAUDE.md"

    if not claude_md.exists():
        checks.append({
            "check": "CLAUDE.md exists",
            "status": "fail",
            "message": f"Missing: {claude_md}",
        })
        return checks

    content = claude_md.read_text()
    has_start = "<!-- cadre:start -->" in content
    has_end = "<!-- cadre:end -->" in content

    checks.append({
        "check": "CLAUDE.md has cadre section",
        "status": "pass" if (has_start and has_end) else "fail",
        "message": "" if (has_start and has_end) else "CLAUDE.md missing <!-- cadre:start/end --> markers",
    })

    return checks


def check_skill(project_dir: Path) -> list:
    """Validate local /cadre skill exists."""
    checks = []
    skill_path = project_dir / ".claude" / "skills" / "cadre" / "SKILL.md"

    checks.append(check_file_exists(skill_path, "Local /cadre skill"))
    return checks


def check_adr_directory(project_dir: Path) -> list:
    """Validate docs/decisions/ ADR directory and required files."""
    checks = []
    adr_dir = project_dir / "docs" / "decisions"

    # Check directory exists
    dir_exists = adr_dir.is_dir()
    checks.append({
        "check": "ADR directory exists",
        "path": str(adr_dir),
        "status": "pass" if dir_exists else "warn",
        "message": "" if dir_exists else "Missing docs/decisions/ — run init to scaffold ADR templates",
    })

    if not dir_exists:
        return checks

    # Check required template files
    for filename, desc in [
        ("index.md", "ADR index"),
        ("adr-template.md", "ADR full template"),
        ("adr-short-template.md", "ADR short template"),
    ]:
        filepath = adr_dir / filename
        exists = filepath.exists()
        checks.append({
            "check": f"{desc} exists",
            "path": str(filepath),
            "status": "pass" if exists else "warn",
            "message": "" if exists else f"Missing: {filepath}",
        })

    return checks


def doctor(project_dir: str) -> dict:
    """Run all checks and return a report."""
    project_path = Path(project_dir).resolve()
    all_checks = []

    # File existence checks
    all_checks.append(check_file_exists(
        project_path / ".claude" / "cadre" / "config.yaml", "config.yaml"))
    all_checks.append(check_file_exists(
        project_path / ".claude" / "cadre" / "routing.md", "routing.md"))
    all_checks.append(check_file_exists(
        project_path / ".claude" / "cadre" / "decisions.md", "decisions.md"))

    # Structural checks
    all_checks.extend(check_config_yaml(project_path))
    all_checks.extend(check_agents(project_path))
    all_checks.extend(check_routing_agents(project_path))
    all_checks.extend(check_claude_md(project_path))
    all_checks.extend(check_skill(project_path))
    all_checks.append(check_file_exists(
        project_path / "docs" / "architecture.md", "docs/architecture.md"))
    all_checks.extend(check_adr_directory(project_path))

    # Deduplicate
    seen = set()
    deduped = []
    for check in all_checks:
        key = check.get("check", "")
        if key not in seen:
            seen.add(key)
            deduped.append(check)

    # Summary
    fails = sum(1 for c in deduped if c["status"] == "fail")
    warns = sum(1 for c in deduped if c["status"] == "warn")
    passes = sum(1 for c in deduped if c["status"] == "pass")

    return {
        "checks": deduped,
        "summary": {
            "total": len(deduped),
            "pass": passes,
            "warn": warns,
            "fail": fails,
            "healthy": fails == 0,
        },
    }


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    report = doctor(target)

    print(json.dumps(report, indent=2))

    if not report["summary"]["healthy"]:
        sys.exit(1)
