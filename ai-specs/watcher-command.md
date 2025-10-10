# Feature

Add Watcher Command to SDLC CLI

# Feature Description

This feature adds a new `watcher` command to the SDLC CLI tool that starts a GitHub webhook watcher server. The watcher monitors GitHub issues and triggers ADW (AI Developer Workflow) when specific events occur. The command will replace the current bash script-based approach with a cross-platform Python implementation that works on both Windows and macOS.

The watcher command will:
- Start a FastAPI server that receives GitHub webhook events
- Automatically create and host a Microsoft devtunnel for webhook exposure
- Configure GitHub webhooks pointing to the devtunnel URL
- Support cleanup operations to remove webhooks and delete devtunnels
- Provide proper error handling and cross-platform compatibility

# User Story

As a developer using the SDLC tool
I want to run `sdlc watcher` to start the webhook listener
So that I can automatically trigger ADW workflows when GitHub issues are created or commented on, without relying on platform-specific bash scripts

# Problem Statement

Currently, the watcher functionality (scripts/watcher.py) depends on bash scripts (start_webhook.sh and stop_webhook.sh) for devtunnel management and GitHub webhook configuration. These bash scripts:
1. Are not compatible with Windows systems
2. Are difficult to maintain and test
3. Are not integrated into the unified SDLC CLI tool
4. Require users to manage separate scripts instead of using a single CLI interface

This creates a poor user experience and limits the tool's cross-platform compatibility.

# Solution Statement

Implement a new `sdlc watcher` command that:
1. Integrates the watcher functionality directly into the SDLC CLI
2. Replaces bash script logic with Python subprocess calls for cross-platform compatibility
3. Uses the `devtunnel` CLI via subprocess instead of bash scripts
4. Implements `--remove` flag to cleanly stop and cleanup all resources
5. Leverages existing SDLC library modules (github.py, utils.py) for consistency
6. Provides proper error handling, logging, and status reporting

# Relevant Files

## Existing Files

- **scripts/watcher.py** (432 lines)
  - Contains the core FastAPI webhook server logic
  - Includes devtunnel management embedded in the main script
  - Has webhook configuration logic embedded as inline bash commands
  - Needs to be refactored into reusable library modules

- **scripts/start_webhook.sh** (137 lines)
  - Bash script that creates/manages devtunnels
  - Logic needs to be ported to Python for cross-platform support
  - Contains devtunnel creation, port configuration, and hosting logic

- **scripts/stop_webhook.sh** (142 lines)
  - Bash script that stops services and optionally removes webhooks/tunnels
  - Logic needs to be ported to Python for cleanup operations
  - Handles process termination, webhook removal, and devtunnel deletion

- **sdlc/cli.py** (35 lines)
  - Main CLI entry point using Click framework
  - Needs new `watcher` command registration

- **sdlc/lib/github.py** (277 lines)
  - Contains GitHub operations (issues, comments, repo info)
  - Can be extended with webhook-specific operations

- **sdlc/commands/health.py** (458 lines)
  - Example command structure to follow for the watcher command
  - Shows proper Click integration and error handling patterns

- **scripts/utils.py** (79 lines)
  - Contains utility functions like `make_adw_id()` and logging setup
  - May need to be moved/duplicated in sdlc/lib/ for library use

- **pyproject.toml** (48 lines)
  - Project dependencies configuration
  - Needs to add FastAPI and uvicorn dependencies

### New Files

- **sdlc/lib/devtunnel.py**
  - Module for devtunnel operations (create, show, delete, host)
  - Encapsulates all devtunnel CLI interactions
  - Provides cross-platform subprocess-based implementation

- **sdlc/lib/webhook.py**
  - Module for GitHub webhook operations
  - Create, list, and delete webhook configurations
  - Extract webhook URLs from devtunnel information

- **sdlc/commands/watcher.py**
  - Main watcher command implementation
  - Click command with start/stop/remove functionality
  - Integrates FastAPI server from scripts/watcher.py

# Implementation Plan

## Phase 1: Foundation

Create the core library modules that provide reusable devtunnel and webhook functionality. This includes:
- Extracting devtunnel logic from bash scripts into a Python module
- Creating webhook management functions for GitHub
- Moving shared utilities to the sdlc library

This phase establishes the building blocks needed for the command implementation.

## Phase 2: Core Implementation

Implement the main `watcher` command that integrates with the SDLC CLI. This includes:
- Creating the Click command structure
- Integrating the FastAPI server from scripts/watcher.py
- Implementing start, stop, and cleanup operations
- Adding proper error handling and status reporting

This phase brings the functionality into the CLI tool.

## Phase 3: Integration

Integrate the watcher command with existing SDLC functionality and ensure it works end-to-end. This includes:
- Testing the command with real GitHub webhooks
- Verifying cross-platform compatibility
- Updating documentation
- Ensuring proper cleanup on exit

This phase validates the complete feature works as intended.

# Step by Step Tasks

## 1. Update project dependencies

- Add `fastapi>=0.100.0` to pyproject.toml dependencies
- Add `uvicorn>=0.23.0` to pyproject.toml dependencies
- Run `uv sync` to install new dependencies

## 2. Create devtunnel library module (sdlc/lib/devtunnel.py)

- Create `resolve_devtunnel_id()` function to determine tunnel ID from env or git repo
- Create `check_devtunnel_installed()` function to verify devtunnel CLI is available
- Create `check_devtunnel_authenticated()` function to verify user is logged in
- Create `create_devtunnel()` function to create a new tunnel with anonymous access
- Create `configure_devtunnel_port()` function to add HTTP port to tunnel
- Create `show_devtunnel()` function to get tunnel information
- Create `delete_devtunnel()` function to remove a tunnel
- Create `start_devtunnel_host()` function to start hosting a tunnel (returns subprocess.Popen)
- Create `get_devtunnel_url()` function to extract the public URL for a port
- Add comprehensive docstrings and type hints to all functions
- Add proper error handling for subprocess failures

## 3. Create webhook library module (sdlc/lib/webhook.py)

- Create `get_webhook_url_from_tunnel()` function to construct webhook URL from devtunnel info
- Create `list_github_webhooks()` function to fetch all webhooks for a repo
- Create `create_github_webhook()` function to add a new webhook with specified URL and events
- Create `delete_github_webhook()` function to remove a webhook by ID
- Create `remove_devtunnel_webhooks()` function to remove all devtunnel-based webhooks
- Create `ensure_webhook_configured()` function that checks for existing webhook and creates if needed
- Add comprehensive docstrings and type hints to all functions
- Use existing `sdlc.lib.github` functions for repo operations

## 4. Copy shared utilities to sdlc library

- Copy `make_adw_id()` function from scripts/utils.py to sdlc/lib/utils.py (if not already there)
- Copy `setup_logger()` function from scripts/utils.py to sdlc/lib/utils.py (if not already there)
- Copy `get_logger()` function from scripts/utils.py to sdlc/lib/utils.py (if not already there)
- Ensure scripts/utils.py continues to work for backward compatibility

## 5. Create watcher command module (sdlc/commands/watcher.py)

- Import necessary libraries (click, asyncio, subprocess, signal, atexit)
- Import FastAPI and uvicorn
- Import devtunnel, webhook, and github library modules
- Create `@click.command()` decorated `watcher()` function
- Add `--remove` flag option for cleanup operations
- Add `--port` option (default 8001) for server port
- Add `--tunnel-id` option (default from env/repo) for devtunnel ID
- Implement command docstring explaining usage

## 6. Implement watcher start logic

- Check if devtunnel CLI is installed (using devtunnel.check_devtunnel_installed())
- Check if devtunnel is authenticated (using devtunnel.check_devtunnel_authenticated())
- Resolve tunnel ID (using devtunnel.resolve_devtunnel_id())
- Create or verify devtunnel exists (using devtunnel functions)
- Start devtunnel host in background (using devtunnel.start_devtunnel_host())
- Register cleanup handlers for Ctrl+C and normal exit
- Print startup information (tunnel ID, port, webhook URL)

## 7. Implement FastAPI server integration

- Copy FastAPI app creation from scripts/watcher.py
- Implement `/gh-webhook` endpoint handler for GitHub events
- Implement `/health` endpoint handler for health checks
- Configure webhook on server startup (async startup event)
- Import `make_adw_id()` for workflow tracking
- Ensure background process launching works for adw_plan_build.py
- Add proper error handling for webhook payload processing

## 8. Implement watcher cleanup logic (--remove flag)

- Stop any running uvicorn server processes
- Terminate devtunnel host process
- Remove GitHub webhooks (using webhook.remove_devtunnel_webhooks())
- Delete devtunnel (using devtunnel.delete_devtunnel())
- Kill processes on the configured port
- Print cleanup status messages

## 9. Register watcher command in CLI

- Import watcher command in sdlc/cli.py
- Add `main.add_command(watcher)` to register the command
- Verify command appears in `sdlc --help` output

## 10. Create unit tests for devtunnel module

- Create tests/lib/test_devtunnel.py
- Test `resolve_devtunnel_id()` with different scenarios (env var, git repo, default)
- Test `check_devtunnel_installed()` success and failure cases
- Test `check_devtunnel_authenticated()` success and failure cases
- Mock subprocess calls for deterministic testing
- Test error handling for subprocess failures

## 11. Create unit tests for webhook module

- Create tests/lib/test_webhook.py
- Test `get_webhook_url_from_tunnel()` URL construction
- Test `list_github_webhooks()` parsing
- Test `create_github_webhook()` command construction
- Test `delete_github_webhook()` command construction
- Test `ensure_webhook_configured()` logic (create vs skip)
- Mock subprocess and github module calls

## 12. Create integration tests for watcher command

- Create tests/commands/test_watcher.py
- Test command registration and help text
- Test `--remove` flag processing
- Test `--port` and `--tunnel-id` options
- Mock external dependencies (devtunnel CLI, GitHub API)
- Test cleanup handlers are registered correctly

## 13. Run validation commands

- Run all validation commands to ensure zero regressions
- Fix any issues that arise

# Testing Strategy

## Unit Tests

### Devtunnel Module Tests
- Test tunnel ID resolution from environment variables
- Test tunnel ID resolution from git repository
- Test tunnel ID fallback to default
- Test devtunnel CLI installation checks
- Test authentication status checks
- Test tunnel creation with correct parameters
- Test port configuration
- Test tunnel deletion
- Test error handling for missing devtunnel CLI
- Test error handling for authentication failures

### Webhook Module Tests
- Test webhook URL construction from devtunnel info
- Test webhook listing and parsing
- Test webhook creation with correct events (issues, issue_comment)
- Test webhook deletion by ID
- Test removal of multiple devtunnel webhooks
- Test ensure_webhook_configured when webhook exists
- Test ensure_webhook_configured when webhook needs creation
- Test error handling for GitHub API failures

### Watcher Command Tests
- Test command registration in CLI
- Test help text and option descriptions
- Test default port value (8001)
- Test custom port option
- Test custom tunnel ID option
- Test --remove flag processing
- Test cleanup handler registration

## Integration Tests

### End-to-End Watcher Flow
- Test `sdlc watcher` starts server successfully
- Test devtunnel is created if it doesn't exist
- Test devtunnel is reused if it exists
- Test GitHub webhook is configured on startup
- Test webhook receives and processes GitHub events
- Test health endpoint returns correct status
- Test Ctrl+C cleanup stops all processes
- Test `sdlc watcher --remove` removes all resources

### Cross-Platform Compatibility
- Test on macOS with devtunnel CLI
- Test graceful failure on Windows if devtunnel CLI not available
- Test subprocess calls work on both platforms
- Test path handling works cross-platform

## Edge Cases

- **Devtunnel CLI not installed**: Should show helpful error message
- **Devtunnel not authenticated**: Should show authentication instructions
- **Port already in use**: Should show clear error and suggest alternative port
- **GitHub webhook creation fails**: Should log error but continue running
- **Tunnel already exists but wrong port**: Should add the port configuration
- **Multiple devtunnel webhooks**: Should remove all old ones before creating new
- **Webhook receives malformed payload**: Should log error and return 200 to GitHub
- **Background ADW process fails to start**: Should log error but continue accepting webhooks
- **Cleanup runs multiple times**: Should handle idempotently without errors
- **Git repository not configured**: Should use default tunnel ID
- **GitHub CLI not authenticated**: Should show authentication error

# Acceptance Criteria

1. ✅ `sdlc watcher` command is registered and appears in help output
2. ✅ Running `sdlc watcher` starts FastAPI server on default port 8001
3. ✅ Running `sdlc watcher --port 9000` starts server on custom port
4. ✅ Devtunnel is automatically created if it doesn't exist
5. ✅ Devtunnel port is configured for HTTP traffic
6. ✅ GitHub webhook is automatically configured on startup
7. ✅ Webhook URL is displayed to user on startup
8. ✅ Receiving GitHub issue opened event triggers ADW workflow
9. ✅ Receiving issue comment with "adw" text triggers ADW workflow
10. ✅ Health endpoint returns comprehensive system status
11. ✅ Ctrl+C cleanly stops devtunnel and server
12. ✅ `sdlc watcher --remove` stops services, removes webhook, and deletes tunnel
13. ✅ Command works on macOS with devtunnel installed
14. ✅ Command shows helpful error if devtunnel not installed
15. ✅ Command shows helpful error if devtunnel not authenticated
16. ✅ All unit tests pass with >90% code coverage
17. ✅ All integration tests pass
18. ✅ No bash scripts are used in the implementation
19. ✅ All subprocess calls are cross-platform compatible
20. ✅ Cleanup is idempotent and safe to run multiple times

# Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run unit tests for new modules
uv run pytest tests/lib/test_devtunnel.py -v
```

```bash
# Run unit tests for webhook module
uv run pytest tests/lib/test_webhook.py -v
```

```bash
# Run integration tests for watcher command
uv run pytest tests/commands/test_watcher.py -v
```

```bash
# Run all tests with coverage
uv run pytest tests/ -v --cov=sdlc --cov-report=term-missing
```

```bash
# Verify command is registered
sdlc --help | grep watcher
```

```bash
# Verify watcher command help
sdlc watcher --help
```

```bash
# Test watcher start (manual test - requires devtunnel CLI)
# sdlc watcher
# Then Ctrl+C to test cleanup
```

```bash
# Test watcher cleanup (manual test - requires devtunnel CLI)
# sdlc watcher --remove
```

```bash
# Run health check to ensure no regressions
sdlc health
```

# Notes

## Cross-Platform Considerations

- All `devtunnel` CLI calls must use `subprocess.run()` with proper error handling
- Avoid using shell-specific features (pipes, redirects, etc.) - handle in Python instead
- Use `os.path.join()` or `pathlib.Path()` for all file paths
- Process termination should use cross-platform signals (SIGTERM, SIGKILL)
- The `lsof` command (used in stop_webhook.sh) is Unix-specific - consider using `psutil` library for cross-platform process management, or detect platform and use appropriate commands

## Dependencies

The feature requires adding these new dependencies:
- `fastapi>=0.118.3` - Web framework for webhook server
- `uvicorn>=0.37.0` - ASGI server for FastAPI
- Consider adding `psutil>=7.1.0` for cross-platform process management (optional)

## Backward Compatibility

The original `scripts/watcher.py` should continue to work for users who prefer the standalone script approach. The new `sdlc watcher` command provides a better integrated experience but doesn't break existing workflows.

## Future Enhancements

- Add `--daemon` flag to run watcher in background as a service
- Add `sdlc watcher status` to check if watcher is running
- Support multiple tunnel providers (ngrok, localhost.run, etc.)
- Add configuration file support for persistent settings
- Implement log rotation for long-running watcher processes
- Add metrics collection for webhook events

## Migration from Bash Scripts

After this feature is complete and tested, consider:
1. Updating documentation to recommend `sdlc watcher` over bash scripts
2. Adding deprecation notices to bash scripts
3. Eventually removing bash scripts in a future major version
4. Updating any CI/CD pipelines that use the bash scripts
