# Feature: GitLab Webhook Watcher

## Feature Description

Implement a GitLab webhook watcher that enables autonomous execution of SDLC commands via GitLab issue comments, mirroring the functionality of the existing GitHub watcher. This feature will allow users to trigger AI-driven development workflows by commenting on GitLab issues, with the system automatically creating branches, generating plans, implementing solutions, and creating merge requests.

The watcher will use the `glab` CLI for GitLab API operations and Microsoft devtunnel for exposing the webhook endpoint to the internet.

## User Story

As a developer using GitLab
I want to trigger SDLC workflows by commenting on GitLab issues
So that I can automate feature development, bug fixes, and chores without manual intervention

## Problem Statement

The current claude-sdlc project only supports GitHub webhooks for autonomous workflow execution. Teams using GitLab (including self-hosted instances like community.opengroup.org) cannot benefit from the automated SDLC workflow capabilities. This limits the adoption and usefulness of the tool for GitLab-based teams.

## Solution Statement

Create a parallel implementation of the watcher functionality for GitLab that:
1. Uses the `glab` CLI instead of `gh` CLI for GitLab API operations
2. Handles GitLab-specific webhook event formats (Issue Hook, Note Hook)
3. Creates merge requests instead of pull requests
4. Supports both gitlab.com and self-hosted GitLab instances
5. Follows the same architectural patterns as the GitHub implementation for maintainability

## Related Documentation

### Requirements
- No existing requirements documents in docs/design/

### Architecture Decisions
- No existing ADRs in docs/decisions/
- This implementation follows the established patterns from the GitHub watcher

## Codebase Analysis Findings

### Architecture Patterns
- **Library-Command Separation**: Core logic in `sdlc/lib/`, commands in `sdlc/commands/`
- **Subprocess-based Integration**: All external tools (gh, devtunnel, claude) invoked via subprocess
- **Model-Driven Design**: Pydantic models for type safety and validation
- **Event-Driven Webhooks**: FastAPI server handles webhook events
- **Background Execution**: Threading for long-running agent workflows

### Naming Conventions
- Python modules: `lowercase_with_underscores.py`
- Functions: `lowercase_with_underscores()`
- Classes: `PascalCase`
- Constants: `UPPERCASE_WITH_UNDERSCORES`

### Similar Implementations
- `sdlc/commands/watcher.py` - GitHub watcher command (526 lines)
- `sdlc/lib/webhook.py` - GitHub webhook operations (231 lines)
- `sdlc/lib/github.py` - GitHub API operations (277 lines)

### Integration Patterns
- All VCS operations use CLI tools via subprocess
- Environment variables for authentication tokens (GITHUB_PAT)
- Silent operations pattern (return bool, print only on error)
- Timeout protection on all subprocess calls

### Key Differences Between GitHub and GitLab

| Aspect | GitHub | GitLab |
|--------|--------|--------|
| CLI Tool | `gh` | `glab` |
| Env Var | `GITHUB_PAT` | `GITLAB_TOKEN` |
| Issue Event Header | `X-GitHub-Event: issues` | `X-Gitlab-Event: Issue Hook` |
| Comment Event Header | `X-GitHub-Event: issue_comment` | `X-Gitlab-Event: Note Hook` |
| PR/MR | Pull Request | Merge Request |
| API Pattern | `gh api repos/{owner}/{repo}/...` | `glab api projects/{id}/...` |

## Archon Project

project_id: e7b7c60c-0a00-4b78-bced-79d496b20b39

## Relevant Files

### Existing Files to Reference
- `sdlc/commands/watcher.py`: GitHub watcher implementation to mirror
- `sdlc/lib/webhook.py`: GitHub webhook operations
- `sdlc/lib/github.py`: GitHub API operations via gh CLI
- `sdlc/lib/devtunnel.py`: Devtunnel management (fully reusable)
- `sdlc/lib/agent.py`: Agent workflow orchestration (mostly reusable)
- `sdlc/lib/models.py`: Pydantic data models
- `sdlc/lib/utils.py`: Utilities (fully reusable)
- `sdlc/cli.py`: CLI entry point for command registration
- `tests/commands/test_watcher.py`: Test patterns to follow

### New Files to Create
- `sdlc/lib/gitlab.py`: GitLab API operations via glab CLI
- `sdlc/lib/gitlab_webhook.py`: GitLab webhook management
- `sdlc/lib/gitlab_models.py`: GitLab-specific Pydantic models
- `sdlc/commands/gitlab_watcher.py`: GitLab watcher command
- `tests/lib/test_gitlab.py`: GitLab library tests
- `tests/lib/test_gitlab_webhook.py`: GitLab webhook tests
- `tests/commands/test_gitlab_watcher.py`: GitLab watcher command tests

## Implementation Plan

### Phase 1: Foundation
Create the GitLab library modules that mirror the GitHub functionality:
1. GitLab models for issues/merge requests
2. GitLab API operations using glab CLI
3. GitLab webhook management functions

### Phase 2: Core Implementation
Implement the GitLab watcher command:
1. FastAPI app with GitLab webhook endpoint
2. GitLab-specific event handling (Issue Hook, Note Hook)
3. Integration with existing agent workflow
4. CLI command registration

### Phase 3: Integration
Ensure seamless integration with existing SDLC workflow:
1. Update agent.py to support GitLab issues
2. Ensure slash commands work with GitLab context
3. Handle merge request creation instead of pull requests

## Step by Step Tasks

### Task 1: Create GitLab Models
- Description: Create Pydantic models for GitLab API responses
- Files to create: `sdlc/lib/gitlab_models.py`
- Details:
  - `GitLabUser` model
  - `GitLabLabel` model
  - `GitLabMilestone` model
  - `GitLabNote` (comment) model
  - `GitLabIssue` model
  - `GitLabMergeRequest` model

### Task 2: Create GitLab API Operations Module
- Description: Create GitLab operations module using glab CLI
- Files to create: `sdlc/lib/gitlab.py`
- Details:
  - `get_gitlab_env()` - Get environment with GITLAB_TOKEN
  - `get_repo_url()` - Get GitLab repository URL from git remote
  - `extract_project_path()` - Extract project path from GitLab URL
  - `fetch_issue()` - Fetch GitLab issue using glab CLI
  - `make_issue_comment()` - Post comment to GitLab issue
  - `mark_issue_in_progress()` - Add label and assign issue
  - `fetch_open_issues()` - List open issues
  - `create_merge_request()` - Create MR using glab CLI

### Task 3: Create GitLab Webhook Module
- Description: Create GitLab webhook management functions
- Files to create: `sdlc/lib/gitlab_webhook.py`
- Details:
  - `get_webhook_url_from_tunnel()` - Construct webhook URL (reuse from webhook.py)
  - `list_gitlab_webhooks()` - List webhooks using glab api
  - `create_gitlab_webhook()` - Create webhook with issue/note events
  - `delete_gitlab_webhook()` - Delete webhook by ID
  - `remove_devtunnel_webhooks()` - Remove devtunnel webhooks
  - `ensure_webhook_configured()` - Ensure webhook exists

### Task 4: Create GitLab Watcher Command
- Description: Create the main GitLab watcher CLI command
- Files to create: `sdlc/commands/gitlab_watcher.py`
- Details:
  - Click command with --remove, --port, --tunnel-id options
  - FastAPI app creation with `/gl-webhook` endpoint
  - Handle `Issue Hook` events (action: open)
  - Handle `Note Hook` events (noteable_type: Issue, body contains "sdlc")
  - Background execution of agent workflow
  - Health check endpoint
  - Cleanup handlers for graceful shutdown

### Task 5: Update Agent Module for GitLab Support
- Description: Extend agent.py to support GitLab issues
- Files to modify: `sdlc/lib/agent.py`
- Details:
  - Add `execute_gitlab_agent_workflow()` function
  - Support GitLab issue model in workflow
  - Create merge request instead of pull request for GitLab
  - Update comment posting to use GitLab functions

### Task 6: Register GitLab Watcher Command
- Description: Add gitlab-watcher command to CLI
- Files to modify: `sdlc/cli.py`
- Details:
  - Import gitlab_watcher command
  - Register with `main.add_command(gitlab_watcher)`

### Task 7: Create GitLab Library Tests
- Description: Create unit tests for GitLab library modules
- Files to create: `tests/lib/test_gitlab.py`, `tests/lib/test_gitlab_webhook.py`
- Details:
  - Test `get_gitlab_env()` with/without GITLAB_TOKEN
  - Test `extract_project_path()` for various URL formats
  - Test `fetch_issue()` mocking glab CLI
  - Test webhook list/create/delete operations
  - Test `ensure_webhook_configured()` logic

### Task 8: Create GitLab Watcher Command Tests
- Description: Create integration tests for gitlab-watcher command
- Files to create: `tests/commands/test_gitlab_watcher.py`
- Details:
  - Test command help text
  - Test --remove flag cleanup
  - Test server startup with mocked dependencies
  - Test webhook endpoint handlers (Issue Hook, Note Hook)
  - Test health endpoint

### Task 9: Update Documentation
- Description: Update README and add GitLab watcher documentation
- Files to modify: `README.md`, `sdlc/README.md`
- Details:
  - Add GitLab Watcher section
  - Document glab CLI requirement
  - Add GITLAB_TOKEN environment variable
  - Provide usage examples

## Testing Strategy

### Unit Tests
- Test each function in gitlab.py with mocked subprocess calls
- Test webhook operations with mocked glab API responses
- Test model validation with various GitLab API response formats
- Test command parsing and option handling

### Integration Tests
- Test FastAPI webhook endpoints with TestClient
- Test end-to-end webhook handling with mocked agent workflow
- Test cleanup operations on --remove flag
- Test authentication flow for devtunnel

### Edge Cases
- Self-hosted GitLab instances with custom URLs
- Issues without body text
- Comments from bots (should ignore)
- Concurrent webhook events
- Network timeouts on glab CLI calls
- Invalid webhook payloads

## Acceptance Criteria

- [x] `sdlc gitlab-watcher` command starts successfully
- [x] Devtunnel is created and managed automatically
- [x] GitLab webhook is configured for issues and notes
- [x] Webhook receives and processes Issue Hook events
- [x] Webhook receives and processes Note Hook events with "sdlc" trigger
- [x] Agent workflow executes and creates merge request
- [x] Comments are posted to GitLab issue during workflow
- [x] `--remove` flag cleans up webhooks and tunnel
- [x] Health endpoint returns service status
- [x] All tests pass (63 GitLab-specific tests)
- [x] Works with gitlab.com and self-hosted instances

## Validation Commands

```bash
# Run all tests
cd /Users/danielscholl/source/github/danielscholl/claude-sdlc
uv run pytest tests/ -v --cov=sdlc --cov-report=term-missing

# Run specific GitLab tests
uv run pytest tests/lib/test_gitlab.py tests/lib/test_gitlab_webhook.py tests/commands/test_gitlab_watcher.py -v

# Run linting
uv run ruff check .

# Format code
uv run ruff format .

# Manual testing - start gitlab watcher
sdlc gitlab-watcher --port 8002

# Check CLI registration
sdlc --help | grep gitlab
```

## Notes

### Reusable Components from GitHub Implementation
- `sdlc/lib/devtunnel.py` - 100% reusable, no changes needed
- `sdlc/lib/utils.py` - 100% reusable
- `sdlc/lib/claude.py` - 100% reusable
- `sdlc/lib/agent.py` - 90% reusable, minor modifications for GitLab model

### glab CLI Commands Reference
```bash
# Authentication
glab auth login
glab auth status

# Issue operations
glab issue view <number> --json number,title,description,state,author,assignees,labels,notes
glab issue comment <number> --body "message"
glab issue update <number> --add-label "in_progress"

# Merge request operations
glab mr create --title "Title" --description "Body" --source-branch "branch"

# API operations (for webhooks)
glab api projects/:id/hooks
glab api projects/:id/hooks -X POST -f url="..." -f issues_events=true -f note_events=true
glab api projects/:id/hooks/:hook_id -X DELETE
```

### GitLab Webhook Event Formats

**Issue Hook (issue opened)**:
```json
{
  "object_kind": "issue",
  "event_type": "issue",
  "object_attributes": {
    "action": "open",
    "iid": 123,
    "title": "Issue title",
    "description": "Issue body"
  },
  "project": {
    "id": 456,
    "path_with_namespace": "user/repo"
  }
}
```

**Note Hook (comment on issue)**:
```json
{
  "object_kind": "note",
  "event_type": "note",
  "object_attributes": {
    "noteable_type": "Issue",
    "note": "sdlc /feature implement this"
  },
  "issue": {
    "iid": 123,
    "title": "Issue title"
  },
  "project": {
    "id": 456,
    "path_with_namespace": "user/repo"
  }
}
```

### Target Test Project
- URL: https://community.opengroup.org/danielscholl/osdu-agent
- This self-hosted GitLab instance will be used for development and testing

## Execution

This spec can be implemented using: `/implement docs/specs/gitlab-watcher.md`
