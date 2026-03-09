---
name: init
description: >
  Initialize a multi-agent development team for any project. Use this skill whenever
  the user wants to set up, bootstrap, create, or design specialized agents for their
  codebase — including requests to "set up agents", "create a team", "organize work
  into agents", "bootstrap cadre", or "generate agent configuration". Also triggers
  for requests to scope agents to project directories (monorepo packages, microservices,
  frontend/backend splits). Handles both existing projects (analyzes codebase structure)
  and greenfield projects (interviews user first). Generates .claude/agents/*.md files,
  config.yaml, routing rules, and a local /cadre coordinator skill.
allowed-tools: Bash, Read, Write, Glob, Agent, TeamCreate, SendMessage, ToolSearch
---

# Cadre Init — Bootstrap a Multi-Agent Team

You are the init orchestrator for Claude Cadre. Your job is to analyze a project, design an optimal agent team through a structured debate, and generate all the files needed for multi-agent coordination.

**After init completes, the user runs `/cadre` (the local project skill) — not `/cadre:init` again.**

## Prerequisites

Before starting, load the deferred tools needed for the debate step:

```
Use ToolSearch to load: "select:TeamCreate,SendMessage"
```

---

## Mode Detection

First, determine which mode to use:

### Check for Existing Cadre
Read `.claude/cadre/config.yaml`. If it exists with active agents:
- Tell the user: "This project already has a cadre. Use `/cadre` to manage it, or say 'reinit' to start fresh."
- Stop unless they confirm reinit.

### Detect Project Type
Look for config files: `package.json`, `go.mod`, `pyproject.toml`, `Cargo.toml`, `composer.json`, `Gemfile`, `build.gradle`, `pom.xml`, `CMakeLists.txt`, `mix.exs`.

- **Config files found** → **Mode B: Existing Project** (analyze the codebase)
- **No config files** → **Mode A: Greenfield** (ask the user what they want to build)

---

## Mode A: Greenfield (No Existing Code)

Ask the user these questions to build a project brief:

1. **What are you building?** (e.g., "a REST API for task management", "a full-stack e-commerce app")
2. **What tech stack?** (e.g., "TypeScript, React, Express, PostgreSQL")
3. **Any specific architectural preferences?** (e.g., monorepo, microservices, serverless)

Assemble their answers into a `projectBrief` and proceed to Step 2 (Debate).

---

## Mode B: Existing Project (Code Present)

### Step 1: Analyze the Project

Run the analysis script to get structured signals:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/analyze_project.py" "$(pwd)"
```

This outputs JSON with: project name, languages, frameworks, directories, test patterns, CI, monorepo detection.

Then spawn an **Explore agent** for deeper analysis:

```
Explore this codebase thoroughly. I need to understand:
1. The major modules/packages and what each does
2. Key entry points and how they connect
3. Shared code and cross-cutting concerns
4. Test organization and patterns
5. Build/deploy pipeline
6. Any existing conventions (naming, patterns, architecture)

Focus on understanding ownership boundaries — which parts of the codebase are independent enough to be owned by a single agent.
```

Combine the script output and the Explore agent's findings into a `projectBrief`. Example:

```
Project: my-app (TypeScript monorepo, npm workspaces)
Languages: TypeScript
Frameworks: React, Express, Prisma, Vitest
Structure:
  packages/frontend/ — React app (components, pages, hooks)
  packages/api/ — Express server (routes, middleware, models)
  packages/shared/ — Shared types and utilities
  test/ — Integration tests
CI: GitHub Actions
Patterns: Feature-based organization, barrel exports, Prisma for ORM
Key concern: frontend and API share types via packages/shared/
```

---

## Step 2: Debate the Team Composition

Create a team and spawn two agents simultaneously. Both receive the `projectBrief`.

### TeamCreate
Create a team named `"cadre-debate"`. Then spawn both agents with `team_name: "cadre-debate"` and `mode: "auto"`.

### Spawn: cadre-proposer
```
You are the 'cadre-proposer' in a debate about the best agent team for a project.

Project brief:
{projectBrief}

Propose 4-6 agents. For each, provide:
- name (kebab-case, e.g. "api-dev")
- role (one sentence, e.g. "Backend developer for Express routes and database models")
- description (2-3 sentences about expertise and working style)
- owns (specific paths in THIS project the agent is responsible for)
- boundaries (what this agent should NOT modify — typically other agents' owned paths)

Also propose routing rules: regex patterns that map categories of user requests to agents.
Include a catch-all "team" rule for cross-cutting features.

Send your proposal to 'cadre-critic' via SendMessage.
When you get feedback, revise and resend.
When the critic sends "AGREED", format your final proposal as JSON and return it as your result:
{
  "agents": [
    {
      "name": "agent-name",
      "role": "one-line role",
      "description": "detailed description",
      "owns": ["path1/", "path2/"],
      "boundaries": ["Do not modify path3/"]
    }
  ],
  "routing": [
    {
      "pattern": "regex|pattern",
      "agents": ["agent-name"],
      "mode": "auto",
      "description": "what this rule covers"
    }
  ]
}

Design principles:
- Fewer well-scoped agents beat many narrow ones (4-5 is typical, 6 only for genuinely complex projects)
- Every source path should be owned by exactly one agent — no orphans, no overlaps
- Boundaries are symmetric: if agent A owns src/api/, agent B's boundary includes "Do not modify src/api/"
- Every agent must be reachable by at least one routing rule
- Include one "team" mode rule for cross-cutting work (features, refactors that span boundaries)
- Routing patterns should cover the common request types for this project type
```

### Spawn: cadre-critic
```
You are the 'cadre-critic' in a debate about the best agent team for a project.

Project brief:
{projectBrief}

Wait for 'cadre-proposer' to send their proposal, then evaluate it for:
- Missing coverage: project areas with no agent owner?
- Redundant agents: could two be merged without losing effectiveness?
- Boundary gaps: can agents accidentally step on each other?
- Routing holes: common request types that won't match any rule?
- Over-engineering: agents not justified by this project's actual structure?
- Role clarity: is each agent's purpose distinct?

Send specific, actionable feedback to 'cadre-proposer' via SendMessage.
Review their revision. If solid, send "AGREED".
Maximum 3 rounds — if not converged by round 3, send "AGREED" on the best version.
```

---

## Step 3: Generate the Team

After both agents complete, parse the proposer's final JSON result. Extract the `cadre_name` from the `projectBrief` (use the project name in kebab-case).

### 3a: Save debate JSON to a temp file
Write the JSON to a temporary file (e.g., `/tmp/cadre-debate-result.json`).

### 3b: Run generation scripts
Execute these scripts sequentially:

```bash
# Generate agent .md files and local /cadre skill
python3 "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/generate_agents.py" /tmp/cadre-debate-result.json "{cadre_name}" "$(pwd)"

# Generate config.yaml, routing.md, decisions.md, CLAUDE.md section
python3 "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/compile_config.py" /tmp/cadre-debate-result.json "{cadre_name}" "$(pwd)"
```

### 3c: Validate the setup
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/init/scripts/doctor.py" "$(pwd)"
```

If doctor reports failures, fix them before proceeding.

### 3d: Clean up
```bash
rm /tmp/cadre-debate-result.json
```

---

## Step 4: Display the Result

Present the newly created cadre to the user. Read `.claude/cadre/config.yaml` and display:

```markdown
**Your cadre is live!**

| Agent | Role | Owns |
|-------|------|------|
| **{name}** | {role} | `{paths}` |
| ... | ... | ... |

**Routing active** — {N} rules compiled. Use `/cadre` to route work to your team.

**Generated files:**
- `.claude/agents/*.md` — agent definitions
- `.claude/skills/cadre/SKILL.md` — local team coordinator
- `.claude/cadre/config.yaml` — team configuration
- `.claude/cadre/routing.md` — routing reference
- `.claude/cadre/decisions.md` — shared decisions log
- `docs/architecture.md` — system architecture overview
- `docs/decisions/` — ADR templates and index
- `.claude/CLAUDE.md` — updated with team info

Want to adjust? Say "add a ___ agent", "retire ___", or "show the team" anytime via `/cadre`.
```

---

## Error Handling

- If `analyze_project.py` fails, fall back to Mode A (ask the user)
- If the debate produces invalid JSON, ask the proposer agent to retry with correct formatting
- If `doctor.py` reports failures after generation, attempt to fix the issues automatically
- If scripts are not found at `${CLAUDE_PLUGIN_ROOT}`, inform the user the cadre plugin may not be installed correctly
