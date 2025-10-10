#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
ADW Plan & Build - AI Developer Workflow (ADW)

Usage: uv run adws/adw_plan_build.py <github-issue-number> [adw-id]

Workflow:
1. Fetch GitHub issue details
2. Create feature branch: feature/issue-{number}-{slug}
3. Plan Agent: Generate implementation plan
   - Prompt Claude Code with issue context
   - Comment plan on issue
   - Commit: "chore: add implementation plan for #{number}"
4. Build Agent: Implement the solution
   - Prompt Claude Code with plan + codebase context
   - Comment implementation summary on issue
   - Commit: "feature: implement #{number} - {title}"
5. Create PR with full context

Environment Requirements:
- ANTHROPIC_API_KEY: Anthropic API key
- CLAUDE_CODE_PATH: Path to Claude CLI
- GITHUB_PAT: (Optional) GitHub Personal Access Token - only if using a different account than 'gh auth login'
"""

import subprocess
import sys
import os
import logging
from typing import Tuple, Optional, Union
from dotenv import load_dotenv
from data_types import (
    AgentTemplateRequest,
    GitHubIssue,
    AgentPromptResponse,
    IssueClassSlashCommand,
)
from agent import execute_template
from github import (
    extract_repo_path,
    fetch_issue,
    make_issue_comment,
    mark_issue_in_progress,
    get_repo_url,
)
from utils import make_adw_id, setup_logger

# Agent name constants
AGENT_PLANNER = "sdlc_planner"
AGENT_IMPLEMENTOR = "sdlc_implementor"
AGENT_CLASSIFIER = "issue_classifier"
AGENT_PLAN_FINDER = "plan_finder"
AGENT_BRANCH_GENERATOR = "branch_generator"
AGENT_PR_CREATOR = "pr_creator"


def check_env_vars(logger: Optional[logging.Logger] = None) -> None:
    """Check that all required environment variables are set."""
    required_vars = [
        "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_PATH",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        error_msg = "Error: Missing required environment variables:"
        if logger:
            logger.error(error_msg)
            for var in missing_vars:
                logger.error(f"  - {var}")
        else:
            print(error_msg, file=sys.stderr)
            for var in missing_vars:
                print(f"  - {var}", file=sys.stderr)
        sys.exit(1)


def parse_args(logger: Optional[logging.Logger] = None) -> Tuple[str, Optional[str]]:
    """Parse command line arguments.
    Returns (issue_number, adw_id) where adw_id may be None."""
    if len(sys.argv) < 2:
        usage_msg = [
            "Usage: uv run adw_plan_build.py <issue-number> [adw-id]",
            "Example: uv run adw_plan_build.py 123",
            "Example: uv run adw_plan_build.py 123 abc12345",
        ]
        if logger:
            for msg in usage_msg:
                logger.error(msg)
        else:
            for msg in usage_msg:
                print(msg)
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    return issue_number, adw_id


def format_issue_message(
    adw_id: str, agent_name: str, message: str, session_id: Optional[str] = None
) -> str:
    """Format a message for issue comments with ADW tracking."""
    if session_id:
        return f"{adw_id}_{agent_name}_{session_id}: {message}"
    return f"{adw_id}_{agent_name}: {message}"


def classify_issue(
    issue: GitHubIssue, adw_id: str, logger: logging.Logger
) -> Tuple[Optional[IssueClassSlashCommand], Optional[str]]:
    """Classify GitHub issue and return appropriate slash command.
    Returns (command, error_message) tuple."""
    issue_template_request = AgentTemplateRequest(
        agent_name=AGENT_CLASSIFIER,
        slash_command="/classify_issue",
        args=[issue.model_dump_json(indent=2, by_alias=True)],
        adw_id=adw_id,
        model="sonnet",
    )

    logger.debug(
        f"issue_template_request: {issue_template_request.model_dump_json(indent=2, by_alias=True)}"
    )

    issue_response = execute_template(issue_template_request)

    logger.debug(
        f"issue_response: {issue_response.model_dump_json(indent=2, by_alias=True)}"
    )

    if not issue_response.success:
        return None, issue_response.output

    issue_command = issue_response.output.strip()

    if issue_command == "0":
        return None, f"No command selected: {issue_response.output}"

    if issue_command not in ["/chore", "/bug", "/feature"]:
        return None, f"Invalid command selected: {issue_response.output}"

    return issue_command, None  # type: ignore


def build_plan(
    issue: GitHubIssue, command: str, adw_id: str, logger: logging.Logger
) -> AgentPromptResponse:
    """Build implementation plan for the issue using the specified command."""
    issue_plan_template_request = AgentTemplateRequest(
        agent_name=AGENT_PLANNER,
        slash_command=command,
        args=[issue.title + ": " + issue.body],
        adw_id=adw_id,
        model="sonnet",
    )

    logger.debug(
        f"issue_plan_template_request: {issue_plan_template_request.model_dump_json(indent=2, by_alias=True)}"
    )

    issue_plan_response = execute_template(issue_plan_template_request)

    logger.debug(
        f"issue_plan_response: {issue_plan_response.model_dump_json(indent=2, by_alias=True)}"
    )

    return issue_plan_response


def get_plan_file(
    plan_output: str, adw_id: str, logger: logging.Logger
) -> Tuple[Optional[str], Optional[str]]:
    """Get the path to the plan file that was just created.
    Returns (file_path, error_message) tuple."""
    request = AgentTemplateRequest(
        agent_name=AGENT_PLAN_FINDER,
        slash_command="/find_plan_file",
        args=[plan_output],
        adw_id=adw_id,
        model="sonnet",
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    # Clean up the response - get just the file path
    file_path = response.output.strip()

    # Validate it looks like a file path
    if file_path and file_path != "0" and "/" in file_path:
        return file_path, None
    elif file_path == "0":
        return None, "No plan file found in output"
    else:
        # If response doesn't look like a path, return error
        return None, f"Invalid file path response: {file_path}"


def implement_plan(
    plan_file: str, adw_id: str, logger: logging.Logger
) -> AgentPromptResponse:
    """Implement the plan using the /implement command."""
    implement_template_request = AgentTemplateRequest(
        agent_name=AGENT_IMPLEMENTOR,
        slash_command="/implement",
        args=[plan_file],
        adw_id=adw_id,
        model="sonnet",
    )

    logger.debug(
        f"implement_template_request: {implement_template_request.model_dump_json(indent=2, by_alias=True)}"
    )

    implement_response = execute_template(implement_template_request)

    logger.debug(
        f"implement_response: {implement_response.model_dump_json(indent=2, by_alias=True)}"
    )

    return implement_response


def git_branch(
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger,
) -> Tuple[Optional[str], Optional[str]]:
    """Generate and create a git branch for the issue.
    Returns (branch_name, error_message) tuple."""
    # Remove the leading slash from issue_class for the branch name
    issue_type = issue_class.replace("/", "")

    request = AgentTemplateRequest(
        agent_name=AGENT_BRANCH_GENERATOR,
        slash_command="/generate_branch_name",
        args=[issue_type, adw_id, issue.model_dump_json(by_alias=True)],
        adw_id=adw_id,
        model="sonnet",
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    branch_name = response.output.strip()
    logger.info(f"Created branch: {branch_name}")
    return branch_name, None


def git_commit(
    agent_name: str,
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a git commit with a properly formatted message.
    Returns (commit_message, error_message) tuple."""
    # Remove the leading slash from issue_class
    issue_type = issue_class.replace("/", "")

    # Create unique committer agent name by suffixing '_committer'
    unique_agent_name = f"{agent_name}_committer"

    request = AgentTemplateRequest(
        agent_name=unique_agent_name,
        slash_command="/commit",
        args=[agent_name, issue_type, issue.model_dump_json(by_alias=True)],
        adw_id=adw_id,
        model="sonnet",
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    commit_message = response.output.strip()
    logger.info(f"Created commit: {commit_message}")
    return commit_message, None


def pull_request(
    branch_name: str,
    issue: GitHubIssue,
    plan_file: str,
    adw_id: str,
    logger: logging.Logger,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a pull request for the implemented changes.
    Returns (pr_url, error_message) tuple."""
    request = AgentTemplateRequest(
        agent_name=AGENT_PR_CREATOR,
        slash_command="/pull_request",
        args=[branch_name, issue.model_dump_json(by_alias=True), plan_file, adw_id],
        adw_id=adw_id,
        model="sonnet",
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    pr_url = response.output.strip()
    logger.info(f"Created pull request: {pr_url}")
    return pr_url, None


def check_error(
    error_or_response: Union[Optional[str], AgentPromptResponse],
    issue_number: str,
    adw_id: str,
    agent_name: str,
    error_prefix: str,
    logger: logging.Logger,
) -> None:
    """Check for errors and handle them uniformly.

    Args:
        error_or_response: Either an error string or an AgentPromptResponse
        issue_number: GitHub issue number
        adw_id: ADW workflow ID
        agent_name: Name of the agent
        error_prefix: Prefix for error message (e.g., "Error creating branch")
        logger: Logger instance
    """
    error = None

    # Handle AgentPromptResponse
    if isinstance(error_or_response, AgentPromptResponse):
        if not error_or_response.success:
            error = error_or_response.output
    else:
        # Handle string error
        error = error_or_response

    if error:
        logger.error(f"{error_prefix}: {error}")
        make_issue_comment(
            issue_number,
            format_issue_message(adw_id, agent_name, f"❌ {error_prefix}: {error}"),
        )
        sys.exit(1)


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse arguments (before we have logger)
    issue_number, adw_id = parse_args()

    # Generate ADW ID if not provided
    if not adw_id:
        adw_id = make_adw_id()

    # Set up logger with ADW ID
    logger = setup_logger(adw_id, "adw_plan_build")
    logger.info(f"ADW ID: {adw_id}")

    # Validate environment (now with logger)
    check_env_vars(logger)

    # Get repo information from git remote
    try:
        github_repo_url: str = get_repo_url()
        repo_path: str = extract_repo_path(github_repo_url)
    except ValueError as e:
        logger.error(f"Error getting repository URL: {e}")
        sys.exit(1)

    # Fetch and display issue
    issue: GitHubIssue = fetch_issue(issue_number, repo_path)

    logger.debug(f"issue: {issue.model_dump_json(indent=2, by_alias=True)}")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, "ops", f"✅ Starting ADW workflow")
    )

    # Classify the issue
    issue_command: IssueClassSlashCommand
    issue_command, error = classify_issue(issue, adw_id, logger)

    check_error(error, issue_number, adw_id, "ops", "Error classifying issue", logger)

    logger.info(f"issue_command: {issue_command}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ Issue classified as: {issue_command}"),
    )

    # Create git branch
    branch_name, error = git_branch(issue, issue_command, adw_id, logger)

    check_error(error, issue_number, adw_id, "ops", "Error creating branch", logger)

    logger.info(f"Working on branch: {branch_name}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ Working on branch: {branch_name}"),
    )

    # Build the implementation plan
    logger.info("\n=== Building implementation plan ===")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_PLANNER, "✅ Building implementation plan"),
    )

    issue_plan_response: AgentPromptResponse = build_plan(
        issue, issue_command, adw_id, logger
    )

    check_error(
        issue_plan_response,
        issue_number,
        adw_id,
        AGENT_PLANNER,
        "Error building plan",
        logger,
    )

    logger.debug(f"issue_plan_response.output: {issue_plan_response.output}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_PLANNER, "✅ Implementation plan created"),
    )

    # Get the path to the plan file that was created
    logger.info("\n=== Finding plan file ===")

    plan_file_path, error = get_plan_file(issue_plan_response.output, adw_id, logger)

    check_error(error, issue_number, adw_id, "ops", "Error finding plan file", logger)

    logger.info(f"plan_file_path: {plan_file_path}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ Plan file created: {plan_file_path}"),
    )

    # Commit the plan
    logger.info("\n=== Committing plan ===")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, AGENT_PLANNER, "✅ Committing plan")
    )
    commit_msg, error = git_commit(AGENT_PLANNER, issue, issue_command, adw_id, logger)

    check_error(
        error, issue_number, adw_id, AGENT_PLANNER, "Error committing plan", logger
    )

    # Implement the plan
    logger.info("\n=== Implementing solution ===")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_IMPLEMENTOR, "✅ Implementing solution"),
    )
    implement_response: AgentPromptResponse = implement_plan(
        plan_file_path, adw_id, logger
    )

    check_error(
        implement_response,
        issue_number,
        adw_id,
        AGENT_IMPLEMENTOR,
        "Error implementing solution",
        logger,
    )

    logger.debug(f"implement_response.output: {implement_response.output}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_IMPLEMENTOR, "✅ Solution implemented"),
    )

    # Commit the implementation
    logger.info("\n=== Committing implementation ===")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_IMPLEMENTOR, "✅ Committing implementation"),
    )
    commit_msg, error = git_commit(
        AGENT_IMPLEMENTOR, issue, issue_command, adw_id, logger
    )

    check_error(
        error,
        issue_number,
        adw_id,
        AGENT_IMPLEMENTOR,
        "Error committing implementation",
        logger,
    )

    # Create pull request
    logger.info("\n=== Creating pull request ===")
    make_issue_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Creating pull request")
    )

    pr_url, error = pull_request(branch_name, issue, plan_file_path, adw_id, logger)

    check_error(
        error, issue_number, adw_id, "ops", "Error creating pull request", logger
    )

    logger.info(f"\nPull request created: {pr_url}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ Pull request created: {pr_url}"),
    )

    logger.info(f"ADW workflow completed successfully for issue #{issue_number}")
    make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ ADW workflow completed successfully"),
    )


if __name__ == "__main__":
    main()
