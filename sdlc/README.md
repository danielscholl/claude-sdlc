# SDLC - Software Development Lifecycle Commands

A unified CLI tool for development workflow automation.

## Overview

SDLC provides a consistent, discoverable interface for project automation tasks. Instead of navigating multiple script files, all commands are accessible through a single `sdlc` entry point.

## Installation

```bash
# Install dependencies
uv sync

# Option 1: Install as a global tool (recommended)
uv tool install --editable .

# Option 2: Run with uv prefix (no global install needed)
# Just use 'uv run sdlc' instead of 'sdlc'
```

## Available Commands

### Health Check

Run comprehensive system health checks:

```bash
sdlc health

# Or with uv run
uv run sdlc health

# Post results to a GitHub issue
sdlc health --issue-number 123
```

The health command validates:
- Environment variables (ANTHROPIC_API_KEY, etc.)
- Git repository configuration
- Claude Code CLI functionality
- GitHub CLI authentication
- Devtunnel CLI (optional)

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=sdlc --cov-report=html
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Check code
uv run ruff check .
```

### Building

```bash
# Build package
uv build
```

## Project Structure

```
sdlc/
├── __init__.py           # Package version and exports
├── cli.py               # Main CLI entry point
├── commands/            # Command implementations
│   ├── __init__.py
│   └── health.py        # Health check command
├── lib/                 # Shared library code
│   ├── __init__.py
│   ├── github.py        # GitHub operations
│   ├── models.py        # Pydantic data models
│   └── utils.py         # Utility functions
└── py.typed             # PEP 561 type checking marker
```

## Adding New Commands

To add a new command:

1. Create a new file in `sdlc/commands/` (e.g., `mycommand.py`)
2. Implement the command using Click decorators
3. Register the command in `sdlc/cli.py`

Example:

```python
# sdlc/commands/mycommand.py
import click

@click.command()
@click.option('--name', help='Your name')
def mycommand(name: str):
    """Description of my command."""
    click.echo(f"Hello, {name}!")
```

```python
# sdlc/cli.py
from sdlc.commands.mycommand import mycommand

# In main() function:
main.add_command(mycommand)
```

## Environment Variables

The following environment variables are used:

**Required:**
- `ANTHROPIC_API_KEY` - Anthropic API Key for Claude Code

**Optional:**
- `CLAUDE_CODE_PATH` - Path to Claude Code CLI (defaults to 'claude')
- `GITHUB_PAT` - GitHub Personal Access Token (alternative to `gh auth login`)
- `E2B_API_KEY` - E2B API Key for sandbox environments
- `DEVTUNNEL_ID` - Microsoft devtunnel ID for webhook exposure (defaults to 'webhook-tunnel')

## Migration from Scripts

This CLI tool replaces the standalone scripts in `plugins/sdlc/scripts/`:

- `scripts/health_check.py` → `sdlc health`

The original scripts remain available for backward compatibility but are deprecated in favor of the unified CLI.
