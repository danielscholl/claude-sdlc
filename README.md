# Claude Software Development Lifecycle

The location for sharing workflows.

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
cd sdlc
uv sync
uv pip install -e .
```

### Usage

```bash
# Run health checks
sdlc health

# Get help
sdlc --help
```

See [sdlc/README.md](sdlc/README.md) for detailed documentation.

## Available plugins

### sdlc

An exploration of software development lifecycle activities.

