#!/usr/bin/env python3
"""Generate agent markdown files and the local /cadre skill from debate JSON.

Takes the agreed-upon team composition (JSON from the debate) and writes:
- .claude/agents/{name}.md for each agent
- .claude/skills/cadre/SKILL.md (local coordinator skill)

Usage:
    python generate_agents.py <debate_json_file> <cadre_name> [project_dir]

The debate JSON must have this shape:
    {
        "agents": [
            {
                "name": "api-dev",
                "role": "Backend developer for Express routes",
                "description": "Builds and maintains API endpoints...",
                "owns": ["packages/api/", "prisma/"],
                "boundaries": ["Do not modify frontend components"]
            }
        ],
        "routing": [
            {
                "pattern": "api|backend|route",
                "agents": ["api-dev"],
                "description": "Backend API tasks"
            }
        ]
    }
"""

import json
import sys
from pathlib import Path


AGENT_TEMPLATE = """---
name: {name}
description: "{role}"
model: {model}
---

# {name}

## Role
{role}

## Description
{description}

## What I Own
{owns}

## How I Work
- Read shared decisions before starting any task
- Read existing ADRs in `docs/decisions/` before making design choices
- Record architectural decisions to the shared decisions file
- Create formal ADRs for architecturally significant decisions
- Stay within owned paths unless coordinating with other agents

## Boundaries
**I handle:** {role}
**I don't:**
{boundaries}
**When unsure:** Escalate to the coordinator — it will route to the right agent.

## Collaboration
- Read shared decisions from `.claude/cadre/decisions.md` before starting work
- If a decision affects other agents, record it to the shared decisions file
- If work requires changes outside owned paths, escalate to the coordinator
- Cadre: {cadre_name}

## Architectural Decision Records
- **Read** existing ADRs in `docs/decisions/` before making design choices
- **Create** a new ADR when making an architecturally significant decision (see `docs/decisions/index.md` for criteria)
- Use `docs/decisions/adr-short-template.md` for smaller decisions, `docs/decisions/adr-template.md` for comprehensive ones
- Number ADRs sequentially: `NNNN-title-with-dashes.md`
- Set initial status to `proposed`; update to `accepted` once agreed upon
"""


def format_list(items: list, prefix: str = "- ") -> str:
    """Format a list of items as markdown bullet points."""
    if not items:
        return f"{prefix}(none specified)"
    return "\n".join(f"{prefix}`{item}`" if "/" in item else f"{prefix}{item}" for item in items)


def write_agent_file(agent: dict, cadre_name: str, model: str, agents_dir: Path):
    """Write a single agent .md file."""
    name = agent["name"]
    role = agent["role"]
    description = agent.get("description", role)
    owns = agent.get("owns", [])
    boundaries = agent.get("boundaries", [])

    content = AGENT_TEMPLATE.format(
        name=name,
        role=role,
        description=description,
        model=model,
        owns=format_list(owns),
        boundaries=format_list(boundaries, prefix="- "),
        cadre_name=cadre_name,
    )

    agent_file = agents_dir / f"{name}.md"
    agent_file.write_text(content.lstrip())
    return agent_file


def generate_skill(debate: dict, cadre_name: str, project_dir: Path):
    """Generate the local /cadre SKILL.md from the template."""
    template_path = Path(__file__).parent / "templates" / "cadre-skill.md"

    if not template_path.exists():
        print(f"Error: Template not found at {template_path}", file=sys.stderr)
        sys.exit(1)

    template = template_path.read_text()

    # Build agent list for the template
    agents = debate.get("agents", [])
    agent_names = [a["name"] for a in agents]
    agent_list = "\n".join(f"- **{a['name']}** — {a['role']}" for a in agents)

    # Build routing table
    routing = debate.get("routing", [])
    routing_rows = []
    for rule in routing:
        agents_str = ", ".join(rule.get("agents", []))
        mode = rule.get("mode", "auto")
        desc = rule.get("description", "")
        pattern = rule.get("pattern", "")
        routing_rows.append(f"| `{pattern}` | {agents_str} | {mode} | {desc} |")
    routing_table = "\n".join(routing_rows)

    # Replace template placeholders
    content = template.replace("{{CADRE_NAME}}", cadre_name)
    content = content.replace("{{AGENT_LIST}}", agent_list)
    content = content.replace("{{AGENT_NAMES}}", ", ".join(agent_names))
    content = content.replace("{{ROUTING_TABLE}}", routing_table)

    # Write skill file
    skill_dir = project_dir / ".claude" / "skills" / "cadre"
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(content)
    return skill_file


def main():
    if len(sys.argv) < 3:
        print("Usage: generate_agents.py <debate_json_file> <cadre_name> [project_dir]", file=sys.stderr)
        sys.exit(1)

    debate_file = sys.argv[1]
    cadre_name = sys.argv[2]
    project_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(".")

    # Load debate JSON
    with open(debate_file) as f:
        debate = json.load(f)

    agents = debate.get("agents", [])
    if not agents:
        print("Error: No agents in debate JSON", file=sys.stderr)
        sys.exit(1)

    model = debate.get("settings", {}).get("defaultModel", "sonnet")

    # Create agents directory
    agents_dir = project_dir / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Write agent files
    created = []
    for agent in agents:
        agent_file = write_agent_file(agent, cadre_name, model, agents_dir)
        created.append(str(agent_file))
        print(f"Created agent: {agent_file}")

    # Write local /cadre skill
    skill_file = generate_skill(debate, cadre_name, project_dir)
    created.append(str(skill_file))
    print(f"Created skill: {skill_file}")

    # Output summary
    print(json.dumps({"created": created, "agent_count": len(agents)}))


if __name__ == "__main__":
    main()
