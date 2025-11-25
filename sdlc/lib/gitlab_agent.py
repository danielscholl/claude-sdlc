"""
GitLab Agent Execution Module - AI Developer Workflow (ADW)

This module contains the GitLab-specific agent logic for executing complete ADW workflows,
including issue classification, plan generation, implementation, and merge request creation.

This mirrors the functionality of agent.py but uses GitLab-specific models and API calls.
"""

import json
import logging
from typing import Optional, Tuple

from sdlc.lib.claude import (
    check_claude_installed,
    execute_slash_command,
    resolve_slash_command,
)
from sdlc.lib.gitlab import make_issue_comment, create_merge_request
from sdlc.lib.gitlab_models import GitLabIssue
from sdlc.lib.models import IssueClassSlashCommand
from sdlc.lib.agent import commit_changes


def classify_gitlab_issue(
    issue: GitLabIssue,
    adw_id: str,
    logger: logging.Logger
) -> Tuple[Optional[IssueClassSlashCommand], Optional[str]]:
    """Classify a GitLab issue to determine the appropriate slash command.

    This function uses Claude to analyze the issue and determine if it's a
    feature request, bug report, or chore.

    Args:
        issue: The GitLab issue to classify
        adw_id: The ADW workflow ID
        logger: Logger instance

    Returns:
        Tuple[Optional[IssueClassSlashCommand], Optional[str]]:
            (command, error_message) where command is None on error
    """
    logger.info("=== Classifying GitLab issue ===")
    logger.debug(f"Issue #{issue.iid}: {issue.title}")
    logger.debug(f"Issue description: {issue.description}")

    # Create a prompt for classification
    prompt = f"""Classify this GitLab issue as one of: /feature, /bug, or /chore

Issue Title: {issue.title}
Issue Body: {issue.description or '(no description)'}

Respond with ONLY one of these three options:
- /feature (for new functionality or enhancements)
- /bug (for defects or problems that need fixing)
- /chore (for maintenance, refactoring, or other non-feature work)

Your response:"""

    # Use Claude to classify
    from sdlc.lib.claude import execute_prompt
    response = execute_prompt(
        prompt=prompt,
        adw_id=adw_id,
        model="sonnet",
        agent_name="classify",
        logger=logger
    )

    logger.debug(f"Classification response: {response.model_dump_json(indent=2)}")

    if not response.success:
        return None, response.output

    # Parse the response
    command = response.output.strip().lower()

    # Validate the response
    if command not in ["/feature", "/bug", "/chore"]:
        return None, f"Invalid classification result: {command}"

    logger.info(f"Issue classified as: {command}")
    return command, None  # type: ignore


def create_gitlab_branch(
    issue: GitLabIssue,
    issue_class: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger
) -> Tuple[Optional[str], Optional[str]]:
    """Create a git branch for the GitLab issue.

    Args:
        issue: The GitLab issue
        issue_class: The classified issue type (/feature, /bug, /chore)
        adw_id: The ADW workflow ID
        logger: Logger instance

    Returns:
        Tuple[Optional[str], Optional[str]]: (branch_name, error_message)
    """
    logger.info("=== Creating git branch ===")

    # Resolve the branch command
    branch_command = resolve_slash_command("/branch")
    logger.info(f"Executing slash command: {branch_command}")

    # Remove leading slash from issue_class for the argument
    issue_type = issue_class.replace("/", "")

    # Convert GitLab issue to a format similar to GitHub for the branch command
    issue_data = {
        "number": issue.iid,
        "title": issue.title,
        "body": issue.description or "",
        "state": issue.state,
        "url": issue.web_url,
    }

    # Execute the /branch slash command
    response = execute_slash_command(
        slash_command=branch_command,
        args=[issue_type, adw_id, json.dumps(issue_data)],
        adw_id=adw_id,
        model="sonnet",
        agent_name="branch",
        logger=logger
    )

    logger.debug(f"Branch response: {response.model_dump_json(indent=2)}")

    if not response.success:
        return None, response.output

    branch_name = response.output.strip()
    logger.info(f"Branch created: {branch_name}")
    return branch_name, None


def build_gitlab_plan(
    issue: GitLabIssue,
    command: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger
) -> Tuple[Optional[str], Optional[str]]:
    """Build an implementation plan for the GitLab issue.

    Args:
        issue: The GitLab issue
        command: The slash command to use (/feature, /bug, /chore)
        adw_id: The ADW workflow ID
        logger: Logger instance

    Returns:
        Tuple[Optional[str], Optional[str]]: (plan_output, error_message)
    """
    logger.info("=== Building implementation plan ===")

    # Resolve the command (check user-defined first, then SDLC plugin)
    resolved_command = resolve_slash_command(command)
    logger.info(f"Executing slash command: {resolved_command}")

    # Execute the planning command
    response = execute_slash_command(
        slash_command=resolved_command,
        args=[f"{issue.title}: {issue.description or ''}"],
        adw_id=adw_id,
        model="sonnet",
        agent_name="plan",
        logger=logger
    )

    logger.debug(f"Plan response: {response.model_dump_json(indent=2)}")

    if not response.success:
        return None, response.output

    logger.info("Plan created successfully")
    return response.output, None


def locate_gitlab_plan_file(
    plan_output: str,
    adw_id: str,
    logger: logging.Logger
) -> Tuple[Optional[str], Optional[str]]:
    """Locate the plan file that was created using the /locate slash command.

    Args:
        plan_output: The output from the plan creation step
        adw_id: The ADW workflow ID
        logger: Logger instance

    Returns:
        Tuple[Optional[str], Optional[str]]: (plan_file_path, error_message)
    """
    logger.info("=== Locating plan file ===")

    # Resolve the locate command
    locate_command = resolve_slash_command("/locate")
    logger.info(f"Executing slash command: {locate_command}")

    # Execute the /locate command with the plan output as context
    response = execute_slash_command(
        slash_command=locate_command,
        args=[plan_output],
        adw_id=adw_id,
        model="sonnet",
        agent_name="locate",
        logger=logger
    )

    logger.debug(f"Locate response: {response.model_dump_json(indent=2)}")

    if not response.success:
        return None, response.output

    # Parse the response - should be just a file path or "0"
    plan_file = response.output.strip()

    if plan_file == "0" or not plan_file:
        logger.error("Could not locate plan file")
        return None, "Plan file not found"

    logger.info(f"Plan file located: {plan_file}")
    return plan_file, None


def implement_gitlab_plan(
    plan_file: str,
    adw_id: str,
    logger: logging.Logger
) -> Tuple[Optional[str], Optional[str]]:
    """Implement the plan using the /implement command.

    Args:
        plan_file: Path to the plan file
        adw_id: The ADW workflow ID
        logger: Logger instance

    Returns:
        Tuple[Optional[str], Optional[str]]: (implementation_output, error_message)
    """
    logger.info("=== Implementing solution ===")
    logger.debug(f"Plan file: {plan_file}")

    # Resolve the implement command
    implement_command = resolve_slash_command("/implement")
    logger.info(f"Executing slash command: {implement_command}")

    # Execute the /implement command
    response = execute_slash_command(
        slash_command=implement_command,
        args=[plan_file],
        adw_id=adw_id,
        model="sonnet",
        agent_name="implement",
        logger=logger
    )

    logger.debug(f"Implementation response: {response.model_dump_json(indent=2)}")

    if not response.success:
        return None, response.output

    logger.info("Implementation completed successfully")
    return response.output, None


def create_gitlab_merge_request(
    branch_name: str,
    issue: GitLabIssue,
    plan_file: str,
    adw_id: str,
    logger: logging.Logger,
    project_path: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a GitLab merge request for the implemented changes.

    Args:
        branch_name: The git branch name
        issue: The GitLab issue
        plan_file: Path to the plan file
        adw_id: The ADW workflow ID
        logger: Logger instance
        project_path: Optional project path

    Returns:
        Tuple[Optional[str], Optional[str]]: (mr_url, error_message)
    """
    logger.info("=== Creating merge request ===")
    logger.debug(f"Branch: {branch_name}")
    logger.debug(f"Plan file: {plan_file}")

    # Build MR title and description
    # Get issue type from branch name
    issue_type = "feat"
    if branch_name.startswith("fix/") or branch_name.startswith("bug/"):
        issue_type = "fix"
    elif branch_name.startswith("chore/"):
        issue_type = "chore"

    title = f"{issue_type}: {issue.title}"

    # Build description with reference to issue
    description = f"""## Summary

Implements #{issue.iid}: {issue.title}

## Changes

See plan file: `{plan_file}`

## ADW Workflow

- ADW ID: `{adw_id}`
- Closes #{issue.iid}
"""

    try:
        mr_url = create_merge_request(
            title=title,
            description=description,
            source_branch=branch_name,
            target_branch="main",
            project_path=project_path,
        )

        if mr_url:
            logger.info(f"Merge request created: {mr_url}")
            return mr_url, None
        else:
            return None, "Failed to create merge request"

    except Exception as e:
        error_msg = f"Error creating merge request: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def execute_gitlab_agent_workflow(
    issue: GitLabIssue,
    issue_number: str,
    adw_id: str,
    logger: logging.Logger,
    explicit_command: Optional[str] = None,
    plan_only: bool = False,
    project_path: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """Execute the complete agent workflow for a GitLab issue.

    Full workflow (plan_only=False):
    1. Classify issue (or use explicit command)
    2. Create branch
    3. Build plan
    4. Locate plan file
    5. Implement solution
    6. Commit everything (plan + implementation)
    7. Create merge request

    Plan-only workflow (plan_only=True):
    1. Classify issue (or use explicit command)
    2. Create branch
    3. Build plan
    4. Commit plan
    5. Stop

    Args:
        issue: The GitLab issue
        issue_number: The issue IID as string
        adw_id: The ADW workflow ID
        logger: Logger instance
        explicit_command: Optional explicit command from comment (e.g., "/chore")
        plan_only: If True, only generate and commit plan, skip implementation
        project_path: Optional project path for API calls

    Returns:
        Tuple[bool, Optional[str]]: (success, error_message)
    """
    logger.info("=" * 60)
    logger.info(f"Starting GitLab agent workflow for issue #{issue_number}")
    logger.info(f"ADW ID: {adw_id}")
    logger.info(f"Mode: {'plan-only' if plan_only else 'full'}")
    logger.info(f"Explicit command: {explicit_command if explicit_command else 'None (will auto-classify)'}")
    logger.info("=" * 60)

    logger.debug(f"Issue details: {issue.model_dump_json(indent=2, by_alias=True)}")

    # Check Claude CLI is installed
    if not check_claude_installed():
        error_msg = "Claude Code CLI is not installed"
        logger.error(error_msg)
        make_issue_comment(issue_number, f"Error: {error_msg}", project_path)
        return False, error_msg

    # Step 1: Determine command (explicit or classify)
    if explicit_command:
        command = explicit_command
        logger.info(f"Using explicit command: {command}")
        make_issue_comment(issue_number, f"Using command: {command} (ADW ID: {adw_id})", project_path)
    else:
        logger.info("No explicit command, classifying issue...")
        command, error = classify_gitlab_issue(issue, adw_id, logger)
        if error:
            logger.error(f"Classification failed: {error}")
            make_issue_comment(issue_number, f"Error: Classification failed: {error} (ADW ID: {adw_id})", project_path)
            return False, error
        make_issue_comment(issue_number, f"Classified as: {command} (ADW ID: {adw_id})", project_path)

    # Step 2: Create branch
    branch_name, error = create_gitlab_branch(issue, command, adw_id, logger)
    if error:
        logger.error(f"Branch creation failed: {error}")
        make_issue_comment(issue_number, f"Error: Branch creation failed: {error} (ADW ID: {adw_id})", project_path)
        return False, error
    make_issue_comment(issue_number, f"Created branch: {branch_name} (ADW ID: {adw_id})", project_path)

    # Step 3: Build plan
    plan_output, error = build_gitlab_plan(issue, command, adw_id, logger)
    if error:
        logger.error(f"Plan creation failed: {error}")
        make_issue_comment(issue_number, f"Error: Plan creation failed: {error} (ADW ID: {adw_id})", project_path)
        return False, error
    make_issue_comment(issue_number, f"Plan created (ADW ID: {adw_id})", project_path)

    # If plan-only mode, commit and stop here
    if plan_only:
        success, error = commit_changes("plan", logger)
        if not success:
            logger.error(f"Plan commit failed: {error}")
            make_issue_comment(issue_number, f"Error: Plan commit failed: {error} (ADW ID: {adw_id})", project_path)
            return False, error
        make_issue_comment(issue_number, f"Plan committed (ADW ID: {adw_id})", project_path)

        logger.info("=" * 60)
        logger.info(f"Plan-only mode: Workflow completed for issue #{issue_number}")
        logger.info(f"ADW ID: {adw_id}")
        logger.info("=" * 60)
        make_issue_comment(issue_number, f"Plan-only workflow completed! (ADW ID: {adw_id})", project_path)
        return True, None

    # Step 4: Locate plan file (while untracked, before commit)
    plan_file, error = locate_gitlab_plan_file(plan_output, adw_id, logger)
    if error:
        logger.error(f"Plan file location failed: {error}")
        make_issue_comment(issue_number, f"Error: Could not locate plan file: {error} (ADW ID: {adw_id})", project_path)
        return False, error
    make_issue_comment(issue_number, f"Plan file: {plan_file} (ADW ID: {adw_id})", project_path)

    # Step 5: Implement solution
    impl_output, error = implement_gitlab_plan(plan_file, adw_id, logger)
    if error:
        logger.error(f"Implementation failed: {error}")
        make_issue_comment(issue_number, f"Error: Implementation failed: {error} (ADW ID: {adw_id})", project_path)
        return False, error
    make_issue_comment(issue_number, f"Implementation completed (ADW ID: {adw_id})", project_path)

    # Step 6: Commit everything (plan + implementation)
    success, error = commit_changes("plan and implementation", logger)
    if not success:
        logger.error(f"Commit failed: {error}")
        make_issue_comment(issue_number, f"Error: Commit failed: {error} (ADW ID: {adw_id})", project_path)
        return False, error
    make_issue_comment(issue_number, f"Changes committed (ADW ID: {adw_id})", project_path)

    # Step 7: Create merge request
    mr_url, error = create_gitlab_merge_request(branch_name, issue, plan_file, adw_id, logger, project_path)
    if error:
        logger.error(f"MR creation failed: {error}")
        make_issue_comment(issue_number, f"Error: MR creation failed: {error} (ADW ID: {adw_id})", project_path)
        return False, error
    make_issue_comment(issue_number, f"Merge request created: {mr_url} (ADW ID: {adw_id})", project_path)

    logger.info("=" * 60)
    logger.info(f"Agent workflow completed successfully for issue #{issue_number}")
    logger.info(f"ADW ID: {adw_id}")
    logger.info(f"Merge Request: {mr_url}")
    logger.info("=" * 60)
    make_issue_comment(issue_number, f"Workflow completed! MR: {mr_url} (ADW ID: {adw_id})", project_path)

    return True, None
