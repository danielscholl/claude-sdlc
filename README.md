# Claude Software Development Lifecycle

A Software Development Lifecycle for use with Claude Code.

## Quick start

Run Claude and add the marketplace:

```
/plugin marketplace add https://github.com/danielscholl/claude-sldc
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

