# Claude Software Development Lifecycle

A Software Development Lifecycle for use with Claude Code.

## Quick Start (Plugin)

Install the SDLC plugin in Claude Code:

```
/plugin marketplace add https://github.com/danielscholl/claude-sdlc
/plugin install sdlc
```

## SDLC Slash Commands

The plugin provides slash commands for Claude Code to manage development workflows:

- `/sdlc:install` - Install dependencies and run setup
- `/sdlc:prime` - Analyze and understand the codebase
- `/sdlc:reset` - Clean up untracked files
- `/sdlc:feature [description]` - Create a new feature with plan and implementation
- `/sdlc:bug [description]` - Fix a bug with plan and implementation
- `/sdlc:chore [description]` - Handle maintenance tasks
- `/sdlc:branch [spec-file]` - Create a git branch
- `/sdlc:implement [spec-file]` - Implement from a plan file
- `/sdlc:pull_request [spec-file]` - Create a pull request
- `/sdlc:commit [spec-file]` - Commit changes
- `/sdlc:locate [spec-file]` - Locate plan files
- `/sdlc:tools` - List available development tools

## CLI Tool Installation

The SDLC CLI tool enables automation via GitHub webhooks.

### Install from GitHub (recommended)

```bash
# Install directly from GitHub
uv tool install git+https://github.com/danielscholl/claude-sdlc

# Verify installation
sdlc --help
sdlc health
```

### Install from local clone

```bash
# Clone and install locally
git clone https://github.com/danielscholl/claude-sdlc
cd claude-sdlc
uv tool install --editable .
```

See [sdlc/README.md](sdlc/README.md) for detailed CLI documentation.

## GitHub Watcher (Automation)

The watcher enables autonomous execution of SDLC commands via GitHub issue comments - no human input required.

### Prerequisites

- SDLC CLI tool installed (see above)
- Claude Code CLI installed and in PATH

### Usage

1. Start the watcher:
   ```bash
   sdlc watcher --port 8001
   ```

2. Comment on a GitHub issue with `sdlc`:
   ```
   # Explicit commands
   sdlc /feature add user profile page
   sdlc /bug fix login error

   # AI classification (analyzes issue to determine type)
   sdlc please implement this

   # Plan-only
   sdlc /feature add dark mode --plan-only
   ```

### Plan-Only Mode

Add flags to generate only the plan without implementation:
- `--plan-only`, `plan only`, `don't implement`, `no implementation`

This is useful when you want to:
- Review the approach before auto-implementing
- Get human approval on the plan
- Manually implement after planning

### Workflow

**Full Automation** (default):
1. Creates branch → 2. Generates plan → 3. Implements → 4. Commits → 5. Creates PR

**Plan-Only**:
1. Creates branch → 2. Generates plan → 3. Commits plan (stops here)

### Monitoring

Logs are written to: `agents/{adw_id}/agent_workflow/execution.log`
