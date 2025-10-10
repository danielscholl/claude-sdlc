# Feature: @agent Detection in Watcher

## Feature Description

Enhance the GitHub webhook watcher to detect when issue comments contain the "@agent" tag and trigger the AI Developer Workflow (ADW) with appropriate slash command mapping. The system supports both explicit command specification (e.g., "@agent /chore fix this bug") and automatic classification (e.g., "@agent please implement this"). This feature integrates the functionality from the legacy `scripts/adw_plan_build.py` script into the modern SDLC CLI tool architecture, executing a complete end-to-end workflow: branch creation, plan generation, implementation, and pull request creation.

## User Story

As a developer using the SDLC workflow
I want the watcher to automatically detect "@agent" mentions in GitHub issue comments
So that I can trigger AI-powered development workflows without manual intervention

## Problem Statement

Currently, the watcher only responds to new issues being opened or comments containing exactly "adw". The legacy `adw_plan_build.py` script performs a complete end-to-end workflow:
1. Classifies issues into appropriate slash commands (/feature, /bug, /chore)
2. Creates a git branch using `/branch` command
3. Builds implementation plans using the classified command
4. Locates created plan files using `/locate` command
5. Commits the plan to git
6. Implements the plan using `/implement` command
7. Commits the implementation
8. Creates a pull request using `/pull_request` command

This logic needs to be modernized and integrated into the SDLC CLI tool with support for:
- Explicit command specification: "@agent /chore fix this"
- Automatic classification: "@agent please implement this feature"
- Flexible mapping to existing slash commands

## Solution Statement

Create a new `sdlc/lib/agent.py` module that encapsulates the agent execution logic from the legacy script. Enhance the watcher command to detect "@agent" tags in comments and route them through a new agent workflow system. Implement a configurable mapping between GitHub issue types and slash commands, allowing the system to automatically select the appropriate workflow based on issue classification.

## Relevant Files

**Files to modify:**
- `sdlc/commands/watcher.py` - Add @agent detection logic and integrate with new agent module
- `sdlc/lib/models.py` - Already contains necessary data models (GitHubIssue, AgentTemplateRequest, etc.)
- `sdlc/lib/utils.py` - Already contains ADW ID generation and logging utilities
- `sdlc/lib/github.py` - Already contains GitHub API operations

### New Files

- `sdlc/lib/agent.py` - Core agent execution logic migrated from adw_plan_build.py
- `sdlc/lib/claude.py` - Claude Code CLI interaction module
- `sdlc/commands/agent.py` - New CLI command for manual agent triggering (optional)
- `tests/lib/test_agent.py` - Unit tests for agent module
- `tests/lib/test_claude.py` - Unit tests for Claude Code interaction

## Implementation Plan

### Phase 1: Foundation
Create the core agent execution infrastructure by extracting and modernizing the logic from `adw_plan_build.py`. This includes creating the Claude Code interaction layer and agent template execution system.

### Phase 2: Core Implementation
Integrate the agent system into the watcher command, implementing @agent detection in issue comments and the issue classification workflow. Map issues to appropriate slash commands and execute the full ADW pipeline.

### Phase 3: Integration
Ensure seamless integration with existing SDLC components, including proper error handling, logging, and GitHub webhook response management. Add configuration options for customizing the agent behavior.

## Step by Step Tasks

### Create Claude Code Interaction Module

- Create `sdlc/lib/claude.py` with functions to execute Claude Code CLI commands
- Implement `execute_claude_command()` function that runs claude CLI with proper error handling
- Add support for both prompt-based and template-based execution
- Implement response parsing for Claude Code JSON output
- Add session ID tracking for multi-turn conversations

### Create Agent Execution Module

- Create `sdlc/lib/agent.py` with core agent logic from adw_plan_build.py
- Implement `execute_template()` function to run slash commands through Claude Code
- Add `parse_agent_command()` function to extract explicit commands from "@agent /command" format
- Add `classify_issue()` function to automatically determine appropriate slash command when not explicitly specified
- Implement `resolve_command()` function to check for user commands and fall back to SDLC commands:
  - Check if /feature exists, otherwise use /sdlc:feature
  - Check if /bug exists, otherwise use /sdlc:bug
  - Check if /chore exists, otherwise use /sdlc:chore
- Implement complete workflow orchestration:
  - `create_branch()` - Execute `/branch` command with issue details
  - `build_plan()` - Execute resolved /feature, /bug, or /chore command
  - `locate_plan_file()` - Execute `/locate` command to find created plan
  - `commit_changes()` - Create git commits with proper messages
  - `implement_plan()` - Execute `/implement` command with plan file
  - `create_pull_request()` - Execute `/pull_request` command

### Enhance Watcher Command

- Modify `sdlc/commands/watcher.py` to detect "@agent" in comment body
- Parse comment for explicit command specification:
  - "@agent /chore fix this bug" → Use /chore directly
  - "@agent /bug something is broken" → Use /bug directly
  - "@agent /feature add new capability" → Use /feature directly
  - "@agent please help" → Auto-classify the issue
- Add logic to differentiate between "adw" and "@agent" triggers
- Implement full agent workflow execution:
  1. Parse or classify command type
  2. Create branch
  3. Build plan
  4. Locate plan file
  5. Commit plan
  6. Implement solution
  7. Commit implementation
  8. Create pull request
- Add proper error handling and logging for agent workflows
- Update webhook response to include agent execution details

### Add Configuration Support

- Create configuration structure for agent slash command mappings
- Add environment variable support for customizing agent behavior
- Implement smart command resolution:
  - First check for user-defined commands: /feature, /bug, /chore
  - Fall back to built-in SDLC commands if not found: /sdlc:feature, /sdlc:bug, /sdlc:chore
- Allow override of default Claude model (sonnet vs opus)
- Add configuration for agent naming conventions

### Implement Error Handling

- Add comprehensive error checking for Claude Code availability
- Implement retry logic for transient failures
- Add proper error messages to GitHub issue comments on failure
- Create fallback mechanisms for classification failures
- Add timeout handling for long-running operations

### Add Logging and Monitoring

- Extend existing ADW logging to include agent operations
- Add detailed debug logging for troubleshooting
- Implement execution tracking with ADW IDs
- Add performance metrics logging
- Create audit trail for all agent actions

### Create Tests

- Write unit tests for `sdlc/lib/claude.py`
- Add tests for `sdlc/lib/agent.py` functions
- Create integration tests for watcher @agent detection
- Add end-to-end test scenarios
- Implement mock GitHub webhook payloads for testing

### Update Documentation

- Document @agent feature in README.md
- Add configuration examples
- Create troubleshooting guide
- Document slash command mapping system
- Add examples of agent workflows

## Testing Strategy

### Unit Tests
- Test Claude Code command execution with mocked subprocess calls
- Verify issue classification logic with various issue types
- Test plan file detection patterns
- Validate git operations (branch, commit, PR creation)
- Test error handling scenarios

### Integration Tests
- Test complete @agent workflow from webhook to PR creation
- Verify proper GitHub API interactions
- Test concurrent agent executions
- Validate logging and monitoring outputs
- Test configuration override mechanisms

### Edge Cases
- Handle missing Claude Code CLI installation
- Process malformed issue descriptions
- Handle GitHub API rate limiting
- Manage concurrent @agent requests
- Handle network failures during execution
- Process issues with no clear classification
- Handle plan creation failures
- Manage git conflicts during branch creation

## Acceptance Criteria

- ✅ Watcher detects "@agent" tag in issue comments (case-insensitive)
- ✅ System parses explicit commands: "@agent /chore", "@agent /bug", "@agent /feature"
- ✅ System auto-classifies issues when no explicit command is provided
- ✅ Agent checks for user-defined slash commands first (/feature, /bug, /chore)
- ✅ Agent falls back to built-in SDLC commands (/sdlc:feature, /sdlc:bug, /sdlc:chore) if user commands don't exist
- ✅ Complete workflow executes in order:
  - Branch created using `/branch` command
  - Plan generated using appropriate command
  - Plan file located using `/locate` command
  - Plan committed to git
  - Solution implemented using `/implement` command
  - Implementation committed to git
  - Pull request created using `/pull_request` command
- ✅ All operations are logged with ADW ID tracking
- ✅ Errors are properly reported to GitHub issue comments
- ✅ System handles concurrent agent requests gracefully
- ✅ Configuration allows customization of slash command mappings

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run all tests to ensure no regressions
uv run pytest tests/ -v

# Test the watcher with agent detection
sdlc watcher --port 8001

# In another terminal, verify health check
curl http://localhost:8001/health

# Simulate webhook with @agent comment (requires test issue)
curl -X POST http://localhost:8001/gh-webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: issue_comment" \
  -d '{"action":"created","issue":{"number":1},"comment":{"body":"@agent please implement this feature"}}'

# Check agent execution logs
ls -la agents/*/adw_plan_build/execution.log

# Verify Claude Code integration
claude --version

# Run specific agent tests
uv run pytest tests/lib/test_agent.py -v
uv run pytest tests/lib/test_claude.py -v

# Check for any linting issues
uv run ruff check sdlc/
```

## Notes

- The migration from `scripts/adw_plan_build.py` should preserve all existing functionality while modernizing the architecture
- **Explicit Command Support**: Users can specify commands directly in comments:
  - "@agent /chore fix this typo"
  - "@agent /bug the login is broken"
  - "@agent /feature add dark mode support"
- **Command Resolution Strategy**:
  - First check if command is explicitly specified in comment
  - If not, auto-classify the issue
  - Check for user-defined commands (/feature, /bug, /chore)
  - Fall back to built-in SDLC commands (/sdlc:feature, /sdlc:bug, /sdlc:chore)
- **Workflow Execution**: The system executes the complete ADW workflow:
  1. Branch creation (using `/branch`)
  2. Plan generation (using classified command)
  3. Plan location (using `/locate`)
  4. Plan commit
  5. Implementation (using `/implement`)
  6. Implementation commit
  7. Pull request creation (using `/pull_request`)
- Consider adding support for "@agent help" to show available commands
- The system should gracefully degrade if Claude Code is unavailable, logging errors appropriately
- May need to handle rate limiting from Claude API
- Should support both Claude Sonnet and Opus models with configuration