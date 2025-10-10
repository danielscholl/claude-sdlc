---
description: Install & Prime - Install dependencies and run setup scripts
allowed-tools: Bash, Read, Write
---

# Install & Prime
> Execute the following sections to understand the codebase then summarize your understanding.

## Run
git ls-files

## Read
@README.md

## Execute
Follow all installation steps from the README.md file in order.
Look for sections titled "Installation", "Setup", "Getting Started", or "Quick Start".
Run every command shown in those sections sequentially.

## Execute (if .env.sample exists)
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/map_env.py [.env.sample] [.env]

## Summarize
Provide a concise summary of:
- What the project does
- Key technologies and frameworks used
- Project structure and main components
- Current installation status