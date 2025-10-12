"""
Agent Execution Module - AI Developer Workflow (ADW)

This module contains the core agent logic for executing complete ADW workflows,
including issue classification, plan generation, implementation, and PR creation.
"""

import logging
import re
import subprocess
from typing import Optional, Tuple

from sdlc.lib.claude import (
    check_claude_installed,
    execute_slash_command,
    resolve_slash_command,
)
from sdlc.lib.github import make_issue_comment
from sdlc.lib.models import AgentPromptResponse, GitHubIssue, IssueClassSlashCommand


def parse_agent_command(comment_body: str) -> Tuple[Optional[str], Optional[str], bool]:
    """Parse an sdlc comment to extract explicit command, remaining text, and plan-only flag.

    Examples:
        "sdlc /chore fix this bug" -> ("/chore", "fix this bug", False)
        "sdlc /feature add dark mode --plan-only" -> ("/feature", "add dark mode", True)
        "sdlc please implement this" -> (None, "please implement this", False)
        "sdlc /bug fix login plan only" -> ("/bug", "fix login", True)

    Args:
        comment_body: The comment body containing sdlc trigger

    Returns:
        Tuple[Optional[str], Optional[str], bool]: (command, remaining_text, plan_only)
            command will be None if no explicit command is found
            plan_only will be True if plan-only flag is detected
    """
    # Normalize whitespace
    text = " ".join(comment_body.split())

    # Check for plan-only flags
    plan_only_patterns = [
        r'--plan-only',
        r'plan\s+only',
        r'don\'?t\s+implement',
        r'no\s+implementation',
        r'skip\s+implementation',
        r'planning\s+only',
    ]

    plan_only = False
    for pattern in plan_only_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            plan_only = True
            # Remove the plan-only flag from the text
            text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
            break

    # Pattern to match sdlc followed by optional slash command
    pattern = r'sdlc\s+(/(?:feature|bug|chore))?\s*(.*)'
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        command = match.group(1)  # Will be None if no command specified
        remaining = match.group(2).strip()
        return command, remaining, plan_only

    # If no match, just remove sdlc and return the rest
    cleaned = re.sub(r'sdlc\s*', '', text, flags=re.IGNORECASE).strip()
    return None, cleaned, plan_only


def classify_issue(
    issue: GitHubIssue,
    adw_id: str,
    logger: logging.Logger
) -> Tuple[Optional[IssueClassSlashCommand], Optional[str]]:
    """Classify a GitHub issue to determine the appropriate slash command.

    This function uses Claude to analyze the issue and determine if it's a
    feature request, bug report, or chore.

    Args:
        issue: The GitHub issue to classify
        adw_id: The ADW workflow ID
        logger: Logger instance

    Returns:
        Tuple[Optional[IssueClassSlashCommand], Optional[str]]:
            (command, error_message) where command is None on error
    """
    logger.info("=== Classifying issue ===")
    logger.debug(f"Issue #{issue.number}: {issue.title}")
    logger.debug(f"Issue body: {issue.body}")

    # Create a prompt for classification
    prompt = f"""Classify this GitHub issue as one of: /feature, /bug, or /chore

Issue Title: {issue.title}
Issue Body: {issue.body}

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


def create_branch(
    issue: GitHubIssue,
    issue_class: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger
) -> Tuple[Optional[str], Optional[str]]:
    """Create a git branch for the issue.

    Args:
        issue: The GitHub issue
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

    # Execute the /branch slash command
    response = execute_slash_command(
        slash_command=branch_command,
        args=[issue_type, adw_id, issue.model_dump_json(by_alias=True)],
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


def build_plan(
    issue: GitHubIssue,
    command: IssueClassSlashCommand,
    adw_id: str,
    logger: logging.Logger
) -> Tuple[Optional[str], Optional[str]]:
    """Build an implementation plan for the issue.

    Args:
        issue: The GitHub issue
        command: The slash command to use (/feature, /bug, /chore)
        adw_id: The ADW workflow ID
        logger: Logger instance

    Returns:
        Tuple[Optional[str], Optional[str]]: (plan_output, error_message)
    """
    logger.info(f"=== Building implementation plan ===")

    # Resolve the command (check user-defined first, then SDLC plugin)
    resolved_command = resolve_slash_command(command)
    logger.info(f"Executing slash command: {resolved_command}")

    # Execute the planning command
    response = execute_slash_command(
        slash_command=resolved_command,
        args=[f"{issue.title}: {issue.body}"],
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


def locate_plan_file(
    plan_output: str,
    adw_id: str,
    logger: logging.Logger
) -> Tuple[Optional[str], Optional[str]]:
    """Locate the plan file that was created using git status.

    Args:
        plan_output: The output from the plan creation step (not used, kept for compatibility)
        adw_id: The ADW workflow ID
        logger: Logger instance

    Returns:
        Tuple[Optional[str], Optional[str]]: (plan_file_path, error_message)
    """
    logger.info("=== Locating plan file ===")

    try:
        # Use git to find new untracked files in specs/ or ai-specs/ directories
        logger.debug("Checking git status for new spec files...")
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse git status output
        # Format: XY PATH where X is staged status, Y is unstaged status
        # ?? means untracked file
        # A  means added/staged file
        logger.debug(f"Git status output:\n{result.stdout}")

        spec_files = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            # Check for files in specs/ or ai-specs/ directories
            if ('specs/' in line or 'ai-specs/' in line) and line.endswith('.md'):
                # Extract file path (everything after the status code)
                file_path = line[3:].strip()
                spec_files.append(file_path)
                logger.debug(f"Found spec file: {file_path}")

        if not spec_files:
            logger.error("No spec files found in git status")
            return None, "No plan file found in git status"

        # Use the first spec file found (should only be one for this branch)
        file_path = spec_files[0]
        logger.info(f"Plan file located: {file_path}")
        return file_path, None

    except subprocess.CalledProcessError as e:
        error_msg = f"Git status failed: {e.stderr}"
        logger.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"Error locating plan file: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def commit_changes(
    message: str,
    logger: logging.Logger
) -> Tuple[bool, Optional[str]]:
    """Commit changes to git using aipr for commit message generation.

    Args:
        message: A descriptive message about what was changed
        logger: Logger instance

    Returns:
        Tuple[bool, Optional[str]]: (success, error_message)
    """
    logger.info(f"=== Committing {message} ===")

    try:
        # Stage all changes
        logger.debug("Staging changes: git add .")
        result = subprocess.run(
            ["git", "add", "."],
            capture_output=True,
            text=True,
            check=True
        )

        # Generate commit message using aipr
        logger.debug("Generating commit message with aipr...")
        result = subprocess.run(
            ["aipr", "commit", "-s", "-m", "claude"],
            capture_output=True,
            text=True,
            check=True
        )

        commit_msg = result.stdout.strip()
        logger.debug(f"Generated commit message: {commit_msg}")

        # Create the commit
        logger.debug("Creating commit...")
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            capture_output=True,
            text=True,
            check=True
        )
        logger.debug(f"Commit output: {result.stdout}")

        logger.info(f"Changes committed: {commit_msg}")
        return True, None

    except subprocess.CalledProcessError as e:
        error_msg = f"Git commit failed: {e.stderr}"
        logger.error(error_msg)
        logger.debug(f"Failed command stdout: {e.stdout}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Error committing changes: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def implement_plan(
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


def create_pull_request(
    branch_name: str,
    issue: GitHubIssue,
    plan_file: str,
    adw_id: str,
    logger: logging.Logger
) -> Tuple[Optional[str], Optional[str]]:
    """Create a pull request for the implemented changes.

    Args:
        branch_name: The git branch name
        issue: The GitHub issue
        plan_file: Path to the plan file
        adw_id: The ADW workflow ID
        logger: Logger instance

    Returns:
        Tuple[Optional[str], Optional[str]]: (pr_url, error_message)
    """
    logger.info("=== Creating pull request ===")
    logger.debug(f"Branch: {branch_name}")
    logger.debug(f"Plan file: {plan_file}")

    # Resolve the pull_request command
    pr_command = resolve_slash_command("/pull_request")
    logger.info(f"Executing slash command: {pr_command}")

    # Execute the /pull_request command
    response = execute_slash_command(
        slash_command=pr_command,
        args=[branch_name, issue.model_dump_json(by_alias=True), plan_file, adw_id],
        adw_id=adw_id,
        model="sonnet",
        agent_name="pr",
        logger=logger
    )

    logger.debug(f"PR response: {response.model_dump_json(indent=2)}")

    if not response.success:
        return None, response.output

    pr_url = response.output.strip()
    logger.info(f"Pull request created: {pr_url}")
    return pr_url, None


def execute_agent_workflow(
    issue: GitHubIssue,
    issue_number: str,
    adw_id: str,
    logger: logging.Logger,
    explicit_command: Optional[str] = None,
    plan_only: bool = False
) -> Tuple[bool, Optional[str]]:
    """Execute the complete agent workflow for an issue.

    Full workflow (plan_only=False):
    1. Classify issue (or use explicit command)
    2. Create branch
    3. Build plan
    4. Locate plan file
    5. Implement solution
    6. Commit everything (plan + implementation)
    7. Create pull request

    Plan-only workflow (plan_only=True):
    1. Classify issue (or use explicit command)
    2. Create branch
    3. Build plan
    4. Commit plan
    5. Stop

    Args:
        issue: The GitHub issue
        issue_number: The issue number as string
        adw_id: The ADW workflow ID
        logger: Logger instance
        explicit_command: Optional explicit command from comment (e.g., "/chore")
        plan_only: If True, only generate and commit plan, skip implementation

    Returns:
        Tuple[bool, Optional[str]]: (success, error_message)
    """
    logger.info("=" * 60)
    logger.info(f"Starting agent workflow for issue #{issue_number}")
    logger.info(f"ADW ID: {adw_id}")
    logger.info(f"Mode: {'plan-only' if plan_only else 'full'}")
    logger.info(f"Explicit command: {explicit_command if explicit_command else 'None (will auto-classify)'}")
    logger.info("=" * 60)

    logger.debug(f"Issue details: {issue.model_dump_json(indent=2, by_alias=True)}")

    # Check Claude CLI is installed
    if not check_claude_installed():
        error_msg = "Claude Code CLI is not installed"
        logger.error(error_msg)
        make_issue_comment(issue_number, f"❌ {error_msg}")
        return False, error_msg

    # Step 1: Determine command (explicit or classify)
    if explicit_command:
        command = explicit_command
        logger.info(f"Using explicit command: {command}")
        make_issue_comment(issue_number, f"✅ Using command: {command} (ADW ID: {adw_id})")
    else:
        logger.info("No explicit command, classifying issue...")
        command, error = classify_issue(issue, adw_id, logger)
        if error:
            logger.error(f"Classification failed: {error}")
            make_issue_comment(issue_number, f"❌ Classification failed: {error} (ADW ID: {adw_id})")
            return False, error
        make_issue_comment(issue_number, f"✅ Classified as: {command} (ADW ID: {adw_id})")

    # Step 2: Create branch
    branch_name, error = create_branch(issue, command, adw_id, logger)
    if error:
        logger.error(f"Branch creation failed: {error}")
        make_issue_comment(issue_number, f"❌ Branch creation failed: {error} (ADW ID: {adw_id})")
        return False, error
    make_issue_comment(issue_number, f"✅ Created branch: {branch_name} (ADW ID: {adw_id})")

    # Step 3: Build plan
    plan_output, error = build_plan(issue, command, adw_id, logger)
    if error:
        logger.error(f"Plan creation failed: {error}")
        make_issue_comment(issue_number, f"❌ Plan creation failed: {error} (ADW ID: {adw_id})")
        return False, error
    make_issue_comment(issue_number, f"✅ Plan created (ADW ID: {adw_id})")

    # If plan-only mode, commit and stop here
    if plan_only:
        success, error = commit_changes("plan", logger)
        if not success:
            logger.error(f"Plan commit failed: {error}")
            make_issue_comment(issue_number, f"❌ Plan commit failed: {error} (ADW ID: {adw_id})")
            return False, error
        make_issue_comment(issue_number, f"✅ Plan committed (ADW ID: {adw_id})")

        logger.info("=" * 60)
        logger.info(f"Plan-only mode: Workflow completed for issue #{issue_number}")
        logger.info(f"ADW ID: {adw_id}")
        logger.info("=" * 60)
        make_issue_comment(issue_number, f"✅ Plan-only workflow completed! (ADW ID: {adw_id})")
        return True, None

    # Step 4: Locate plan file (while untracked, before commit)
    plan_file, error = locate_plan_file(plan_output, adw_id, logger)
    if error:
        logger.error(f"Plan file location failed: {error}")
        make_issue_comment(issue_number, f"❌ Could not locate plan file: {error} (ADW ID: {adw_id})")
        return False, error
    make_issue_comment(issue_number, f"✅ Plan file: {plan_file} (ADW ID: {adw_id})")

    # Step 5: Implement solution
    impl_output, error = implement_plan(plan_file, adw_id, logger)
    if error:
        logger.error(f"Implementation failed: {error}")
        make_issue_comment(issue_number, f"❌ Implementation failed: {error} (ADW ID: {adw_id})")
        return False, error
    make_issue_comment(issue_number, f"✅ Implementation completed (ADW ID: {adw_id})")

    # Step 6: Commit everything (plan + implementation)
    success, error = commit_changes("plan and implementation", logger)
    if not success:
        logger.error(f"Commit failed: {error}")
        make_issue_comment(issue_number, f"❌ Commit failed: {error} (ADW ID: {adw_id})")
        return False, error
    make_issue_comment(issue_number, f"✅ Changes committed (ADW ID: {adw_id})")

    # Step 7: Create pull request
    pr_url, error = create_pull_request(branch_name, issue, plan_file, adw_id, logger)
    if error:
        logger.error(f"PR creation failed: {error}")
        make_issue_comment(issue_number, f"❌ PR creation failed: {error} (ADW ID: {adw_id})")
        return False, error
    make_issue_comment(issue_number, f"✅ Pull request created: {pr_url} (ADW ID: {adw_id})")

    logger.info("=" * 60)
    logger.info(f"Agent workflow completed successfully for issue #{issue_number}")
    logger.info(f"ADW ID: {adw_id}")
    logger.info(f"Pull Request: {pr_url}")
    logger.info("=" * 60)
    make_issue_comment(issue_number, f"✅ Workflow completed! PR: {pr_url} (ADW ID: {adw_id})")

    return True, None
