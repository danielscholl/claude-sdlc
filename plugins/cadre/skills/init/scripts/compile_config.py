#!/usr/bin/env python3
"""Compile debate JSON into config.yaml, routing.md, decisions.md, ADRs, and CLAUDE.md section.

Takes the agreed-upon team composition (JSON from the debate) and writes:
- .claude/cadre/config.yaml (source of truth)
- .claude/cadre/routing.md (human-readable routing table)
- .claude/cadre/decisions.md (empty template, only if not already present)
- docs/decisions/ (ADR directory with templates and index, only if not already present)
- .claude/CLAUDE.md (inject/update <!-- cadre:start --> section)

Usage:
    python compile_config.py <debate_json_file> <cadre_name> [project_dir]
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def _yaml_quote(value: str) -> str:
    """Quote a YAML scalar if it contains special characters."""
    if any(c in value for c in (":", "#", "{", "}", "[", "]", ",", "&", "*", "?", "|", "-", "<", ">", "=", "!", "%", "@", "`", '"', "'")):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def generate_config_yaml(debate: dict, cadre_name: str) -> str:
    """Generate config.yaml content from debate JSON."""
    agents = debate.get("agents", [])
    routing = debate.get("routing", [])
    settings = debate.get("settings", {})
    model = settings.get("defaultModel", "sonnet")

    lines = [f"name: {cadre_name}", "agents:"]

    for agent in agents:
        lines.append(f"  - name: {agent['name']}")
        lines.append(f"    role: {_yaml_quote(agent['role'])}")
        desc = agent.get("description", agent["role"])
        lines.append(f"    description: {_yaml_quote(desc)}")
        lines.append(f"    model: {model}")
        owns = agent.get("owns", [])
        if owns:
            lines.append("    owns:")
            for path in owns:
                lines.append(f"      - {path}")
        boundaries = agent.get("boundaries", [])
        if boundaries:
            lines.append("    boundaries:")
            for b in boundaries:
                lines.append(f"      - {_yaml_quote(b)}")
        lines.append("    status: active")

    lines.append("routing:")
    for rule in routing:
        pattern = rule.get("pattern", "")
        lines.append(f"  - pattern: \"{pattern}\"")
        rule_agents = rule.get("agents", [])
        lines.append("    agents:")
        for a in rule_agents:
            lines.append(f"      - {a}")
        lines.append(f"    priority: {rule.get('priority', 0)}")
        lines.append(f"    mode: {rule.get('mode', 'auto')}")
        lines.append(f"    matchMode: {rule.get('matchMode', 'additive')}")
        desc = rule.get("description", "")
        if desc:
            lines.append(f"    description: {_yaml_quote(desc)}")

    lines.append("settings:")
    lines.append(f"  defaultModel: {model}")
    lines.append("  decisionsFile: .claude/cadre/decisions.md")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    lines.append(f'compiledAt: "{now}"')

    return "\n".join(lines) + "\n"


def generate_routing_md(debate: dict) -> str:
    """Generate routing.md content from debate JSON."""
    routing = debate.get("routing", [])

    lines = [
        "# Routing Rules",
        "",
        "| Pattern | Agents | Mode | Priority | Description |",
        "|---------|--------|------|----------|-------------|",
    ]

    for rule in routing:
        pattern = rule.get("pattern", "")
        agents_str = ", ".join(rule.get("agents", []))
        mode = rule.get("mode", "auto")
        priority = rule.get("priority", 0)
        desc = rule.get("description", "")
        lines.append(f"| `{pattern}` | {agents_str} | {mode} | {priority} | {desc} |")

    return "\n".join(lines) + "\n"


ADR_TEMPLATE = """# ADR Template

Copy this file to `NNNN-title-with-dashes.md` and fill in the sections below. Add the following YAML frontmatter:

```yaml
---
status: proposed
contact: (person proposing the ADR)
date: YYYY-MM-DD
deciders: (list everyone involved in the decision)
consulted: (subject-matter experts with two-way communication)
informed: (stakeholders with one-way communication)
---
```

# {short title of solved problem and solution}

## Context and Problem Statement

{Describe the context and problem statement, e.g., in free form using two to three sentences or in the form of an illustrative story.
You may want to articulate the problem in form of a question and add links to collaboration boards or issue management systems.}

<!-- This is an optional element. Feel free to remove. -->

## Decision Drivers

- {decision driver 1, e.g., a force, facing concern, ...}
- {decision driver 2, e.g., a force, facing concern, ...}
- ... <!-- numbers of drivers can vary -->

## Considered Options

- {title of option 1}
- {title of option 2}
- {title of option 3}
- ... <!-- numbers of options can vary -->

## Decision Outcome

Chosen option: "{title of option 1}", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | ... | comes out best (see below)}.

<!-- This is an optional element. Feel free to remove. -->

### Consequences

- Good, because {positive consequence, e.g., improvement of one or more desired qualities, ...}
- Bad, because {negative consequence, e.g., compromising one or more desired qualities, ...}
- ... <!-- numbers of consequences can vary -->

<!-- This is an optional element. Feel free to remove. -->

## Validation

{describe how the implementation of/compliance with the ADR is validated. E.g., by a review or an ArchUnit test}

<!-- This is an optional element. Feel free to remove. -->

## Pros and Cons of the Options

### {title of option 1}

<!-- This is an optional element. Feel free to remove. -->

{example | description | pointer to more information | ...}

- Good, because {argument a}
- Good, because {argument b}
<!-- use "neutral" if the given argument weights neither for good nor bad -->
- Neutral, because {argument c}
- Bad, because {argument d}
- ... <!-- numbers of pros and cons can vary -->

### {title of other option}

{example | description | pointer to more information | ...}

- Good, because {argument a}
- Good, because {argument b}
- Neutral, because {argument c}
- Bad, because {argument d}
- ...

<!-- This is an optional element. Feel free to remove. -->

## More Information

{You might want to provide additional evidence/confidence for the decision outcome here and/or
document the team agreement on the decision and/or
define when this decision when and how the decision should be realized and if/when it should be re-visited and/or
how the decision is validated.
Links to other decisions and resources might appear here as well.}
"""

ADR_SHORT_TEMPLATE = """# ADR Short Template

Copy this file to `NNNN-title-with-dashes.md` and fill in the sections below. Add the following YAML frontmatter:

```yaml
---
status: proposed
contact: (person proposing the ADR)
date: YYYY-MM-DD
deciders: (list everyone involved in the decision)
---
```

# {short title of solved problem and solution}

## Context and Problem Statement

{Describe the context and problem statement, e.g., in free form using two to three sentences or in the form of an illustrative story.}

## Decision Drivers

- {decision driver 1, e.g., a force, facing concern, ...}
- {decision driver 2, e.g., a force, facing concern, ...}

## Considered Options

- {title of option 1}
- {title of option 2}
- {title of option 3}

## Decision Outcome

Chosen option: "{title of option 1}", because {justification}.

### Consequences

- Good, because {positive consequence}
- Bad, because {negative consequence}
"""

ADR_INDEX_TEMPLATE = """# Architectural Decision Records (ADRs)

An Architectural Decision (AD) is a justified software design choice that addresses a functional or non-functional requirement that is architecturally significant. An Architectural Decision Record (ADR) captures a single AD and its rationale.

For more information [see](https://adr.github.io/)

## How to Create an ADR

1. Copy `adr-template.md` to `NNNN-title-with-dashes.md`, where NNNN indicates the next number in sequence.
   - Check for existing PR's to make sure you use the correct sequence number.
   - There is also a short form template `adr-short-template.md` for smaller decisions.
2. Edit `NNNN-title-with-dashes.md`.
   - Status must initially be `proposed`
   - List `deciders` who will sign off on the decision
   - List people who were `consulted` or `informed` about the decision
3. For each option, list the good, neutral, and bad aspects of each considered alternative.
4. Share your PR with the deciders and other interested parties.
   - The status must be updated to `accepted` once a decision is agreed and the date must also be updated.
5. Decisions can be changed later and superseded by a new ADR.

## When to Create an ADR

Create ADRs for:

- Architecture patterns (tool registration, dependency injection, callbacks)
- Technology choices (framework selection, library decisions)
- Design patterns (component interaction, abstraction layers)
- API designs (public interfaces, method signatures, response formats)
- Naming conventions (class names, module structure, terminology)
- Testing strategies (test organization, mocking patterns, coverage targets)
- Performance trade-offs (caching strategies, optimization choices)
- Security decisions (authentication methods, data handling)

**Rule of thumb**: If the decision could be made differently and the alternative would be reasonable, document it with an ADR.

## Templates

- **Full Template**: [`adr-template.md`](./adr-template.md) - Comprehensive template with all sections
- **Short Template**: [`adr-short-template.md`](./adr-short-template.md) - Simplified template for smaller decisions

## ADR Index

| ADR | Title | Status |
|-----|-------|--------|
"""


ARCHITECTURE_TEMPLATE = """# Architecture

> This document describes the high-level architecture of this project.
> If you want to familiarize yourself with the codebase, this is a good place to start.

## Overview

<!-- Describe the overall system architecture at a high level -->

## Key Components

<!-- List the major components/modules and their responsibilities -->

## Data Flow

<!-- Describe how data flows through the system -->

## Directory Structure

<!-- Map out the key directories and what they contain -->

## Key Design Decisions

See [Architectural Decision Records](./decisions/) for detailed decision documentation.

## Technology Stack

<!-- List the core technologies and why they were chosen -->

## Development Workflow

<!-- Describe how development, testing, and deployment work -->
"""


def scaffold_architecture_doc(project_dir: Path) -> list:
    """Scaffold docs/architecture.md if it doesn't already exist.

    Returns:
        list: Paths of files that were created.
    """
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    created = []

    arch_file = docs_dir / "architecture.md"
    if not arch_file.exists():
        arch_file.write_text(ARCHITECTURE_TEMPLATE)
        created.append(str(arch_file))
        print(f"Created: {arch_file}")
    else:
        print(f"Skipped (already exists): {arch_file}")

    return created


def scaffold_adr_directory(project_dir: Path) -> list:
    """Scaffold the docs/decisions/ directory with ADR templates and index.

    Only creates files that don't already exist — never overwrites.

    Returns:
        list: Paths of files that were created.
    """
    adr_dir = project_dir / "docs" / "decisions"
    adr_dir.mkdir(parents=True, exist_ok=True)
    created = []

    files = {
        "index.md": ADR_INDEX_TEMPLATE,
        "adr-template.md": ADR_TEMPLATE,
        "adr-short-template.md": ADR_SHORT_TEMPLATE,
    }

    for filename, content in files.items():
        filepath = adr_dir / filename
        if not filepath.exists():
            filepath.write_text(content)
            created.append(str(filepath))
            print(f"Created: {filepath}")
        else:
            print(f"Skipped (already exists): {filepath}")

    return created


DECISIONS_TEMPLATE = """# Shared Decisions

This file contains architectural decisions shared across all agents in the cadre.
Each agent should read this file before starting work and append new decisions here.

## Format

```
### [YYYY-MM-DD] Decision Title
**Context:** Why was this decision needed?
**Decision:** What was decided?
**Agents involved:** Which agents participated?
```

---
"""


def generate_claude_md_section(debate: dict, cadre_name: str) -> str:
    """Generate the <!-- cadre:start --> section for CLAUDE.md."""
    agents = debate.get("agents", [])
    routing = debate.get("routing", [])

    lines = [
        "<!-- cadre:start -->",
        "",
        f"## Cadre: {cadre_name}",
        "",
        "This project uses **Claude Cadre** for multi-agent coordination.",
        "Use `/cadre` to route work to the right agent or manage the team.",
        "",
        "### Agents",
        "",
        "| Agent | Role | Owns |",
        "|-------|------|------|",
    ]

    for agent in agents:
        name = agent["name"]
        role = agent["role"]
        owns = agent.get("owns", [])
        owns_str = ", ".join(f"`{p}`" for p in owns)
        lines.append(f"| {name} | {role} | {owns_str} |")

    lines.extend([
        "",
        "### Routing",
        "",
        "| Pattern | Agents | Mode | Description |",
        "|---------|--------|------|-------------|",
    ])

    for rule in routing:
        pattern = rule.get("pattern", "")
        agents_str = ", ".join(rule.get("agents", []))
        mode = rule.get("mode", "auto")
        desc = rule.get("description", "")
        lines.append(f"| `{pattern}` | {agents_str} | {mode} | {desc} |")

    lines.extend([
        "",
        "### Key Files",
        "",
        "- `.claude/cadre/decisions.md` — shared team decisions (read before starting work)",
        "- `.claude/cadre/routing.md` — routing rules reference",
        "- `.claude/cadre/config.yaml` — compiled team configuration",
        "- `.claude/agents/*.md` — agent definitions (visible via `/agents`)",
        "- `docs/architecture.md` — system architecture overview",
        "- `docs/decisions/` — Architectural Decision Records (ADRs)",
        "",
        "<!-- cadre:end -->",
    ])

    return "\n".join(lines) + "\n"


def inject_claude_md(cadre_section: str, project_dir: Path) -> Path:
    """Inject or replace the cadre section in CLAUDE.md."""
    claude_md = project_dir / ".claude" / "CLAUDE.md"
    claude_md.parent.mkdir(parents=True, exist_ok=True)

    if claude_md.exists():
        content = claude_md.read_text()
        # Replace existing cadre section
        pattern = r"<!-- cadre:start -->.*?<!-- cadre:end -->\n?"
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, cadre_section, content, flags=re.DOTALL)
        else:
            # Append at the end
            content = content.rstrip() + "\n\n" + cadre_section
    else:
        content = cadre_section

    claude_md.write_text(content)
    return claude_md


def main():
    if len(sys.argv) < 3:
        print("Usage: compile_config.py <debate_json_file> <cadre_name> [project_dir]", file=sys.stderr)
        sys.exit(1)

    debate_file = sys.argv[1]
    cadre_name = sys.argv[2]
    project_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(".")

    # Load debate JSON
    with open(debate_file) as f:
        debate = json.load(f)

    # Create cadre directory
    cadre_dir = project_dir / ".claude" / "cadre"
    cadre_dir.mkdir(parents=True, exist_ok=True)

    # Write config.yaml
    config_yaml = cadre_dir / "config.yaml"
    config_yaml.write_text(generate_config_yaml(debate, cadre_name))
    print(f"Created: {config_yaml}")

    # Write routing.md
    routing_md = cadre_dir / "routing.md"
    routing_md.write_text(generate_routing_md(debate))
    print(f"Created: {routing_md}")

    # Write decisions.md (only if not present — never overwrite)
    decisions_md = cadre_dir / "decisions.md"
    decisions_created = not decisions_md.exists()
    if decisions_created:
        decisions_md.write_text(DECISIONS_TEMPLATE)
        print(f"Created: {decisions_md}")
    else:
        print(f"Skipped (already exists): {decisions_md}")

    # Scaffold docs/architecture.md
    arch_created = scaffold_architecture_doc(project_dir)

    # Scaffold ADR directory (only creates missing files)
    adr_created = scaffold_adr_directory(project_dir)

    # Inject CLAUDE.md section
    cadre_section = generate_claude_md_section(debate, cadre_name)
    claude_md = inject_claude_md(cadre_section, project_dir)
    print(f"Updated: {claude_md}")

    # Output summary
    created = [str(config_yaml), str(routing_md), str(claude_md)]
    if decisions_created:
        created.append(str(decisions_md))
    created.extend(arch_created)
    created.extend(adr_created)
    print(json.dumps({"created": created}))


if __name__ == "__main__":
    main()
