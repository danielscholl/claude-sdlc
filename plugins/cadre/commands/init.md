---
description: Bootstrap a multi-agent development team — analyzes your codebase and generates tailored agents via AI debate
argument-hint: [reinit]
allowed-tools: Bash, Read, Write, Glob, Agent, TeamCreate, SendMessage, ToolSearch
---

<cadre-init>
  <instruction>
    Execute the cadre init skill located at: ${CLAUDE_PLUGIN_ROOT}/skills/init/SKILL.md

    Read that file in full and follow its instructions exactly. It contains the complete
    orchestration logic for bootstrapping a multi-agent cadre team including:
    - Mode detection (greenfield vs existing project)
    - Project analysis via scripts
    - Team composition debate (proposer vs critic agents)
    - File generation (agents, config, routing, ADRs, architecture doc)
    - Validation via doctor script
  </instruction>

  <arguments>
    <variable>$ARGUMENTS</variable>
  </arguments>
</cadre-init>
