# Claude Software Development Lifecycle

A Software Development Lifecycle for use with Claude Code.

## Quick start

Run Claude and add the marketplace:

```
/plugin marketplace add https://github.com/danielscholl/claude-sdlc
```

Then install the plugin:

```
/plugin install sdlc
```

## SDLC CLI Tool

This project includes a unified CLI tool called **SDLC** (Software Development Lifecycle Commands) for managing development workflows.

### Installation

```bash
# From the project root directory
uv sync

# Install as a global tool (recommended - makes 'sdlc' available globally)
uv tool install --editable .

# Or run with 'uv run' prefix (no global install)
# uv pip install -e .
```

### Usage

```bash
# If installed with 'uv tool install'
sdlc health
sdlc --help
```

See [sdlc/README.md](sdlc/README.md) for detailed documentation.

## AI Developer Workflow (ADW) with @agent

The SDLC tool includes an AI-powered development workflow that can be triggered via GitHub issue comments. This feature enables automated end-to-end development workflows from issue to pull request.

### How it Works

1. **Trigger**: Comment on a GitHub issue with `@agent`
2. **Execution**: The system automatically:
   - Creates a feature branch
   - Generates an implementation plan
   - Implements the solution
   - Creates a pull request

### Usage

There are two ways to use the @agent feature:

#### 1. Explicit Command Specification

Specify the exact workflow type in your comment:

```
@agent /feature add dark mode support
@agent /bug fix login validation error
@agent /chore update dependencies
```

#### 2. Automatic Classification

Let the AI classify the issue automatically:

```
@agent please implement this feature
@agent can you help with this?
```

The system will analyze the issue title and description to determine if it's a feature, bug, or chore.

#### 3. Plan-Only Mode

Generate a plan without implementation by adding a plan-only flag:

```
@agent /feature add dark mode --plan-only
@agent /bug fix login plan only
@agent /chore update deps don't implement
@agent create a plan for this feature no implementation
```

**Supported flags:**
- `--plan-only`
- `plan only`
- `don't implement`
- `no implementation`
- `skip implementation`
- `planning only`

**What happens in plan-only mode:**
1. Creates a feature branch
2. Generates an implementation plan
3. Commits the plan
4. **Stops here** - no implementation, no PR

This is useful when you want to:
- Review the approach before auto-implementing
- Get human approval on the plan
- Manually implement after planning

### Command Resolution

The @agent system intelligently resolves slash commands:
1. First checks for user-defined commands (`/feature`, `/bug`, `/chore`)
2. Falls back to built-in SDLC commands (`/sdlc:feature`, `/sdlc:bug`, `/sdlc:chore`)

### Complete Workflow

#### Full Workflow (default)

When you trigger `@agent` without plan-only flags:

1. **Branch Creation** - Creates a git branch using `/branch` command
2. **Plan Generation** - Builds an implementation plan using the classified command
3. **Plan Commit** - Commits the plan to git
4. **Plan Location** - Locates the created plan file using `/locate` command
5. **Implementation** - Implements the solution using `/implement` command
6. **Implementation Commit** - Commits the implementation
7. **Pull Request** - Creates a PR using `/pull_request` command

#### Plan-Only Workflow

When you add a plan-only flag:

1. **Branch Creation** - Creates a git branch using `/branch` command
2. **Plan Generation** - Builds an implementation plan using the classified command
3. **Plan Commit** - Commits the plan to git
4. **Done** - Workflow stops here

The plan is committed and ready for review. You can then manually implement or trigger the full workflow later.

### Setup

To use the @agent feature, ensure:

1. **Claude Code CLI** is installed and available in your PATH
2. **GitHub Watcher** is running:
   ```bash
   sdlc watcher
   ```
3. **Webhook configured** to receive GitHub events (the watcher sets this up automatically)

### Monitoring

Each workflow execution is tracked with an ADW ID and logs are written to:
```
agents/{adw_id}/agent_workflow/execution.log
```

Check the logs to monitor progress and debug any issues.

### Examples

```bash
# Start the watcher
sdlc watcher --port 8001

# In another terminal, check health
curl http://localhost:8001/health

# Comment on a GitHub issue:

# Full workflow (generates plan + implements + creates PR)
# "@agent /feature add user profile page"
# "@agent please fix this bug"

# Plan-only workflow (generates plan only)
# "@agent /feature add user profile page --plan-only"
# "@agent /bug fix this issue plan only"
# "@agent create a plan for this don't implement"
```

The watcher will detect the comment, execute the workflow, and post updates to the issue as it progresses.

