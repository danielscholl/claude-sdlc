# Feature

Create SLDC CLI Tool - Unified Python Project Entry Point

# Feature Description

Transform the collection of standalone Python scripts in the `scripts/` directory into a professional, unified CLI tool called `sldc` (Software Development Lifecycle Commands). This tool will be a proper uv Python project with a clean command-line interface, making it easier to discover, use, and maintain development workflow commands. The first command to implement will be `sldc health`, which will provide all the functionality currently available in `scripts/health_check.py`.

# User Story

As a developer working on the Claude marketplace project
I want to use a unified CLI tool (`sldc`) to run development workflow commands
So that I have a consistent, discoverable interface for all project automation tasks instead of navigating multiple script files

# Problem Statement

Currently, the project has multiple Python scripts scattered in the `scripts/` directory, each functioning as standalone tools with their own dependencies declared inline using uv's PEP 723 format. While this works, it creates several challenges:

1. **Discoverability**: Users must know which script files exist and what they do
2. **Inconsistent Interface**: Each script has its own argument parsing and usage patterns
3. **Maintainability**: Shared code is duplicated or imported directly from other scripts
4. **Distribution**: Scripts can't be easily packaged or installed as a unified tool
5. **Documentation**: Help text and usage information is spread across multiple files

This makes it harder for developers to discover and use the available automation tools, and makes the codebase harder to maintain as it grows.

# Solution Statement

Create a new uv Python project called `sldc` that serves as a unified entry point for all development workflow commands. The project will:

1. Use uv's modern Python project structure with `pyproject.toml` at the repository root
2. Provide a clean CLI interface using Click
3. Organize commands into logical groups (e.g., `sldc health`, `sldc github`, etc.)
4. Share common code through a proper Python package structure
5. Be installable and easily extended with new commands

The first implementation will focus on the `health` command, migrating the functionality from `scripts/health_check.py` into the new structure. This provides a working example for migrating other scripts in the future.

# Relevant Files

## Existing Files

- **scripts/health_check.py** - The source script to migrate; performs comprehensive health checks for environment variables, git repository, Claude Code CLI, GitHub CLI, and devtunnel
- **scripts/github.py** - Contains GitHub operations that health_check.py depends on (`get_repo_url`, `extract_repo_path`, `make_issue_comment`)
- **scripts/utils.py** - Contains utility functions for logging and ADW ID generation
- **scripts/data_types.py** - Contains Pydantic models used across scripts
- **scripts/watcher.py** - FastAPI webhook server that calls health_check.py via subprocess
- **scripts/adw_plan_build.py** - Another script that could be migrated in the future
- **scripts/map_env.py** - Environment mapping utility that could be migrated
- **README.md** - Project documentation that will need updating

## New Files

- **pyproject.toml** - Project configuration file with dependencies and CLI entry points (at repository root)
- **.python-version** - Python version specification for uv (at repository root)
- **sldc/__init__.py** - Package initialization
- **sldc/cli.py** - Main CLI entry point using Click
- **sldc/commands/__init__.py** - Commands package
- **sldc/commands/health.py** - Health check command implementation
- **sldc/lib/__init__.py** - Shared library code
- **sldc/lib/github.py** - GitHub operations (migrated from scripts/)
- **sldc/lib/models.py** - Pydantic models (migrated from scripts/data_types.py)
- **sldc/lib/utils.py** - Utility functions (migrated from scripts/utils.py)
- **sldc/py.typed** - PEP 561 marker for type checking support
- **tests/__init__.py** - Test package (at repository root)
- **tests/test_health.py** - Tests for health command

# Implementation Plan

## Phase 1: Foundation

Set up the basic uv project structure and tooling:

1. Create `pyproject.toml` at the repository root
2. Create `.python-version` at the repository root
3. Create the `sldc/` package directory at the repository root
4. Configure CLI framework (Click) as the command dispatcher
5. Create basic package structure with `__init__.py` files

## Phase 2: Core Implementation

Migrate the health check functionality into the new structure:

1. Migrate shared code from `scripts/` into `sldc/lib/`:
   - Copy and adapt `github.py` → `lib/github.py`
   - Copy and adapt `data_types.py` → `lib/models.py`
   - Copy and adapt relevant parts of `utils.py` → `lib/utils.py`

2. Implement the `health` command:
   - Create `commands/health.py` with all health check logic from `scripts/health_check.py`
   - Adapt the code to use the new lib modules
   - Ensure all check functions work correctly
   - Maintain the same output format and behavior

3. Wire up the CLI:
   - Create `cli.py` with the main CLI group
   - Register the `health` command
   - Configure entry points in `pyproject.toml`

## Phase 3: Integration

Ensure the new tool integrates smoothly with existing workflows:

1. Update `scripts/watcher.py` to optionally call `sldc health` instead of `scripts/health_check.py`
2. Add migration notes to the original `scripts/health_check.py` directing users to the new tool
3. Update project documentation in README.md
4. Ensure backward compatibility - keep original scripts functional during transition

# Step by Step Tasks

## 1. Create Project Structure

- Create `pyproject.toml` at the repository root
- Create `.python-version` at the repository root specifying Python 3.12+
- Create the flat package structure:
  - `sldc/__init__.py`
  - `sldc/cli.py`
  - `sldc/commands/__init__.py`
  - `sldc/lib/__init__.py`
  - `sldc/py.typed`
  - `tests/__init__.py`

## 2. Configure pyproject.toml

- Add required dependencies to `pyproject.toml`:
  - `click` for CLI framework
  - `python-dotenv` for environment management
  - `pydantic` for data validation
- Add optional dependencies (for other commands that might be added later)
- Configure the CLI entry point: `sldc = "sldc.cli:main"`
- Set Python version requirement to >=3.12
- Configure development dependencies (pytest, ruff, etc.)
- Configure hatchling as the build backend with explicit package configuration

## 3. Migrate Shared Library Code

- Copy `scripts/data_types.py` to `sldc/lib/models.py`
  - Update imports and ensure all Pydantic models are properly exported
- Copy `scripts/github.py` to `sldc/lib/github.py`
  - Update imports to use local models from `sldc.lib.models`
  - Ensure all GitHub functions are properly exported
- Copy relevant utilities from `scripts/utils.py` to `sldc/lib/utils.py`
  - Include functions that might be reused across commands
  - Update imports as needed

## 4. Implement Health Command

- Create `sldc/commands/health.py`
- Migrate all health check functions from `scripts/health_check.py`:
  - `check_env_vars()`
  - `check_git_repo()`
  - `check_claude_code()`
  - `check_github_cli()`
  - `check_devtunnel()`
  - `run_health_check()`
- Update imports to use `sldc.lib` modules instead of direct script imports
- Implement the Click command decorator
- Add the `--issue-number` optional argument for posting to GitHub issues
- Ensure output formatting matches the original script (emojis, colors, structure)

## 5. Create CLI Entry Point

- Implement `sldc/cli.py`:
  - Create main CLI group using Click
  - Add version command showing the tool version
  - Import and register the health command
  - Add helpful description and usage examples
  - Configure command aliases if helpful (e.g., `sldc check` → `sldc health`)

## 6. Add Package Initialization

- Update `sldc/__init__.py`:
  - Set `__version__` variable
  - Export key components if needed
- Update `sldc/commands/__init__.py` to export commands
- Update `sldc/lib/__init__.py` to export library functions

## 7. Write Tests

- Create `tests/test_health.py`:
  - Test environment variable checking logic
  - Test git repository validation
  - Mock subprocess calls for CLI tool checks
  - Test health check result aggregation
  - Test command-line argument parsing
- Run tests with `uv run pytest`

## 8. Update Documentation

- Update project root `README.md`:
  - Add section about the sldc CLI tool
  - Document installation with `uv sync`
  - Document usage: `uv run sldc health` and `uv run sldc health --issue-number 123`
  - Explain the commands structure and how to extend it
  - Include examples

## 9. Integration Testing

- Run `uv sync` to install dependencies
- Test `uv run sldc --help` and verify help text
- Run `uv run sldc health` and verify it works correctly
- Run `uv run sldc health --issue-number <test-issue>` if applicable
- Compare output with original `scripts/health_check.py` to ensure parity

## 10. Update Dependent Scripts

- Update `scripts/watcher.py`:
  - Add a check to see if `sldc` is available
  - If available, call `uv run sldc health` instead of `scripts/health_check.py`
  - Fall back to the old script if sldc is not installed
  - Document this in comments
- Add a comment to `scripts/health_check.py`:
  - Note that this script is being deprecated in favor of `sldc health`
  - Direct users to the new tool
  - Keep the script functional for backward compatibility

## 11. Run Validation Commands

- Execute all validation commands to ensure zero regressions
- Verify the health command works end-to-end with all checks

# Testing Strategy

## Unit Tests

- **Model Validation**: Test all Pydantic models in `lib/models.py` to ensure proper validation
- **GitHub Functions**: Test repository URL extraction, path parsing (can be done with mock data)
- **Health Check Functions**: Test each individual check function (`check_env_vars`, `check_git_repo`, etc.) with mocked dependencies
- **CLI Argument Parsing**: Test that command-line arguments are parsed correctly
- **Result Aggregation**: Test that `HealthCheckResult` properly aggregates individual check results

## Integration Tests

- **Full Health Check**: Run complete health check in a controlled environment
- **CLI Invocation**: Test that `sldc health` can be invoked and produces expected output
- **Environment Handling**: Test with various .env configurations
- **GitHub Integration**: Test with mocked GitHub CLI responses
- **Subprocess Calls**: Mock subprocess calls to git, gh, claude, devtunnel

## Edge Cases

- **Missing Environment Variables**: Health check should detect and report missing required vars
- **Missing Optional Variables**: Should warn but not fail
- **Invalid Git Repository**: Should handle gracefully when not in a git repo
- **Unavailable Tools**: Should detect when gh, claude, or devtunnel are not installed
- **Timeout Scenarios**: Claude Code test should timeout appropriately
- **Invalid Issue Numbers**: Should handle gracefully when posting to GitHub
- **Empty/Malformed Responses**: Handle when subprocess commands return unexpected output

# Acceptance Criteria

1. ✅ A `sldc/` package directory exists at project root with proper flat structure
2. ✅ `pyproject.toml` at root is properly configured with all dependencies and entry points
3. ✅ The `sldc` command is available via `uv run sldc`
4. ✅ Running `uv run sldc --help` shows available commands including `health`
5. ✅ Running `uv run sldc health` performs all health checks that `scripts/health_check.py` does
6. ✅ Health check output format matches the original (same emojis, structure, messages)
7. ✅ The `--issue-number` argument works to post results to GitHub issues
8. ✅ All health check functions detect the same issues as the original
9. ✅ Tests pass with `uv run pytest`
10. ✅ Documentation clearly explains installation and usage
11. ✅ Original `scripts/health_check.py` still works (backward compatibility)
12. ✅ No regressions in existing functionality that depends on health checks

# Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

```bash
# Setup the project
uv sync

# Verify CLI is available
uv run sldc --version
uv run sldc --help

# Test health command
uv run sldc health

# Test with issue number (if applicable)
# uv run sldc health --issue-number <test-issue-number>

# Run unit tests
uv run pytest

# Run linting
uv run ruff check .

# Verify original script still works (backward compatibility)
uv run scripts/health_check.py

# Verify watcher can find and use the new command
uv run scripts/watcher.py &
sleep 5
curl http://localhost:8001/health
kill %1

# Build the package to ensure it's distributable
uv build
```

# Notes

## Architecture Decisions

1. **CLI Framework**: Using **Click** for this project because:
   - Click is mature and stable
   - Better suited for complex command structures
   - Excellent documentation and community support
   - More explicit control over command groups

2. **Project Structure**: Using the flat layout (`sldc/` at root) because:
   - Simpler structure for CLI tools
   - More conventional for single-package projects
   - Easier to navigate and understand
   - Reduces nesting complexity
   - Package is directly at root: `sldc/` contains all modules

3. **Build Backend**: Using **hatchling** instead of uv_build because:
   - Better support for flat package layouts
   - Explicit package configuration with `packages = ["sldc"]`
   - More flexible and widely supported

4. **Migration Strategy**: Keeping original scripts functional during transition to:
   - Avoid breaking existing workflows
   - Allow gradual migration
   - Provide fallback if issues are discovered

## Future Considerations

Once the `health` command is working, other scripts can be migrated following the same pattern:

- `sldc github issue <number>` - Interact with GitHub issues
- `sldc github comment <number> <text>` - Post comments to issues
- `sldc watch` - Start the webhook watcher
- `sldc env map` - Map environment variables (from map_env.py)
- `sldc adw build <issue>` - Run ADW workflow (from adw_plan_build.py)

## Dependencies to Add via uv

When setting up the project, these dependencies will be added:

```bash
uv add click python-dotenv pydantic
uv add --dev pytest pytest-cov ruff
```

## Python Version

The project should target Python 3.12+ to match the requirements in the existing scripts:
```python
# .python-version
3.12
```

## Entry Point Configuration

The `pyproject.toml` should include:

```toml
[project.scripts]
sldc = "sldc.cli:main"
```

This makes the `sldc` command available via `uv run sldc` after installation.

## Helpful Development Commands

```bash
# Sync dependencies
uv sync

# Run the CLI
uv run sldc --help
uv run sldc health

# Run tests with coverage
uv run pytest --cov=sldc --cov-report=html

# Format code
uv run ruff format .

# Check code
uv run ruff check .

# Build the package
uv build
```
