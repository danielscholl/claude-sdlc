"""
GitLab Operations Module - AI Developer Workflow (ADW)

This module contains all GitLab-related operations including:
- Issue fetching and manipulation
- Comment posting
- Project path extraction
- Issue status management
- Merge request creation

Uses the glab CLI for GitLab API operations.
"""

import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional

from sdlc.lib.gitlab_models import GitLabIssue, GitLabIssueListItem


def get_gitlab_env() -> Optional[dict]:
    """Get environment with GitLab token set up. Returns None if no GITLAB_TOKEN.

    Subprocess env behavior:
    - env=None -> Inherits parent's environment (default)
    - env={} -> Empty environment (no variables)
    - env=custom_dict -> Only uses specified variables

    So this will work with glab authentication:
    # These are equivalent:
    result = subprocess.run(cmd, capture_output=True, text=True)
    result = subprocess.run(cmd, capture_output=True, text=True, env=None)

    But this will NOT work (no PATH, no auth):
    result = subprocess.run(cmd, capture_output=True, text=True, env={})
    """
    gitlab_token = os.getenv("GITLAB_TOKEN")
    if not gitlab_token:
        return None

    # Only create minimal env with GitLab token
    # Note: glab CLI expects GITLAB_TOKEN directly (unlike gh CLI which uses GH_TOKEN)
    env = {
        "GITLAB_TOKEN": gitlab_token,
        "PATH": os.environ.get("PATH", ""),
    }
    return env


def get_repo_url() -> str:
    """Get GitLab repository URL from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise ValueError(
            "No git remote 'origin' found. Please ensure you're in a git repository with a remote."
        )
    except FileNotFoundError:
        raise ValueError("git command not found. Please ensure git is installed.")


def extract_project_path(gitlab_url: str) -> str:
    """Extract project path from GitLab URL.

    Handles various GitLab URL formats:
    - https://gitlab.com/owner/repo
    - https://gitlab.com/owner/repo.git
    - https://community.opengroup.org/owner/repo
    - git@gitlab.com:owner/repo.git
    - https://gitlab.com/group/subgroup/repo

    Args:
        gitlab_url: The GitLab repository URL

    Returns:
        str: The project path (e.g., "owner/repo" or "group/subgroup/repo")
    """
    # Handle SSH URLs (git@host:path.git)
    if gitlab_url.startswith("git@"):
        # git@gitlab.com:owner/repo.git -> owner/repo
        match = re.match(r"git@[^:]+:(.+?)(?:\.git)?$", gitlab_url)
        if match:
            return match.group(1)

    # Handle HTTPS URLs
    # Remove .git suffix if present
    url = gitlab_url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]

    # Extract path after the host
    # https://gitlab.com/owner/repo -> owner/repo
    # https://community.opengroup.org/owner/repo -> owner/repo
    match = re.match(r"https?://[^/]+/(.+)$", url)
    if match:
        return match.group(1)

    raise ValueError(f"Could not extract project path from URL: {gitlab_url}")


def get_gitlab_host(gitlab_url: str) -> str:
    """Extract the GitLab host from a URL.

    Args:
        gitlab_url: The GitLab repository URL

    Returns:
        str: The host (e.g., "gitlab.com" or "community.opengroup.org")
    """
    # Handle SSH URLs
    if gitlab_url.startswith("git@"):
        match = re.match(r"git@([^:]+):", gitlab_url)
        if match:
            return match.group(1)

    # Handle HTTPS URLs
    match = re.match(r"https?://([^/]+)/", gitlab_url)
    if match:
        return match.group(1)

    return "gitlab.com"  # Default fallback


def fetch_issue(issue_number: str, project_path: str) -> GitLabIssue:
    """Fetch GitLab issue using glab CLI and return typed model.

    Args:
        issue_number: The issue IID (project-scoped ID)
        project_path: The project path (e.g., "owner/repo")

    Returns:
        GitLabIssue: The issue data as a Pydantic model
    """
    # Use JSON output for structured data
    cmd = [
        "glab",
        "issue",
        "view",
        issue_number,
        "-R",
        project_path,
        "--output",
        "json",
    ]

    # Set up environment with GitLab token if available
    env = get_gitlab_env()

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, env=env, timeout=30
        )

        if result.returncode == 0:
            # Parse JSON response into Pydantic model
            issue_data = json.loads(result.stdout)
            issue = GitLabIssue(**issue_data)

            return issue
        else:
            print(result.stderr, file=sys.stderr)
            sys.exit(result.returncode)
    except subprocess.TimeoutExpired:
        print("Error: GitLab CLI timed out.", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: GitLab CLI (glab) is not installed.", file=sys.stderr)
        print("\nTo install glab:", file=sys.stderr)
        print("  - macOS: brew install glab", file=sys.stderr)
        print(
            "  - Linux: See https://gitlab.com/gitlab-org/cli#installation",
            file=sys.stderr,
        )
        print(
            "  - Windows: See https://gitlab.com/gitlab-org/cli#installation",
            file=sys.stderr,
        )
        print(
            "\nAfter installation, authenticate with: glab auth login", file=sys.stderr
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing issue data: {e}", file=sys.stderr)
        sys.exit(1)


def make_issue_comment(issue_id: str, comment: str, project_path: Optional[str] = None) -> None:
    """Post a comment to a GitLab issue using glab CLI.

    Args:
        issue_id: The issue IID
        comment: The comment text to post
        project_path: Optional project path. If not provided, uses current repo.
    """
    # Get repo information from git remote if not provided
    if project_path is None:
        gitlab_repo_url = get_repo_url()
        project_path = extract_project_path(gitlab_repo_url)

    # Build command
    cmd = [
        "glab",
        "issue",
        "note",
        issue_id,
        "-R",
        project_path,
        "--message",
        comment,
    ]

    # Set up environment with GitLab token if available
    env = get_gitlab_env()

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, env=env, timeout=30
        )

        if result.returncode == 0:
            print(f"Successfully posted comment to issue #{issue_id}")
        else:
            print(f"Error posting comment: {result.stderr}", file=sys.stderr)
            sys.exit(result.returncode)
    except subprocess.TimeoutExpired:
        print("Error: GitLab CLI timed out.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error posting comment: {e}", file=sys.stderr)
        sys.exit(1)


def mark_issue_in_progress(issue_id: str, project_path: Optional[str] = None) -> None:
    """Mark issue as in progress by adding label and assigning.

    Args:
        issue_id: The issue IID
        project_path: Optional project path. If not provided, uses current repo.
    """
    # Get repo information from git remote if not provided
    if project_path is None:
        gitlab_repo_url = get_repo_url()
        project_path = extract_project_path(gitlab_repo_url)

    # Set up environment with GitLab token if available
    env = get_gitlab_env()

    # Add "in_progress" label
    cmd = [
        "glab",
        "issue",
        "update",
        issue_id,
        "-R",
        project_path,
        "--label",
        "in_progress",
    ]

    # Try to add label (may fail if label doesn't exist)
    result = subprocess.run(
        cmd, capture_output=True, text=True, env=env, timeout=30
    )
    if result.returncode != 0:
        print(f"Note: Could not add 'in_progress' label: {result.stderr}")

    # Assign to self
    cmd = [
        "glab",
        "issue",
        "update",
        issue_id,
        "-R",
        project_path,
        "--assignee",
        "@me",
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, env=env, timeout=30
    )
    if result.returncode == 0:
        print(f"Assigned issue #{issue_id} to self")


def fetch_open_issues(project_path: str) -> List[GitLabIssueListItem]:
    """Fetch all open issues from the GitLab project.

    Args:
        project_path: The project path (e.g., "owner/repo")

    Returns:
        List[GitLabIssueListItem]: List of open issues
    """
    try:
        cmd = [
            "glab",
            "issue",
            "list",
            "-R",
            project_path,
            "--state",
            "opened",
            "--output",
            "json",
            "--per-page",
            "100",
        ]

        # Set up environment with GitLab token if available
        env = get_gitlab_env()

        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, env=env, timeout=30
        )

        issues_data = json.loads(result.stdout)
        issues = [GitLabIssueListItem(**issue_data) for issue_data in issues_data]
        print(f"Fetched {len(issues)} open issues")
        return issues

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to fetch issues: {e.stderr}", file=sys.stderr)
        return []
    except subprocess.TimeoutExpired:
        print("ERROR: GitLab CLI timed out.", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse issues JSON: {e}", file=sys.stderr)
        return []


def fetch_issue_notes(project_path: str, issue_number: int) -> List[Dict]:
    """Fetch all notes (comments) for a specific issue.

    Args:
        project_path: The project path (e.g., "owner/repo")
        issue_number: The issue IID

    Returns:
        List[Dict]: List of note objects
    """
    try:
        cmd = [
            "glab",
            "issue",
            "view",
            str(issue_number),
            "-R",
            project_path,
            "--output",
            "json",
        ]

        # Set up environment with GitLab token if available
        env = get_gitlab_env()

        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, env=env, timeout=30
        )
        data = json.loads(result.stdout)
        notes = data.get("notes", [])

        # Sort notes by creation time
        notes.sort(key=lambda n: n.get("created_at", ""))

        return notes

    except subprocess.CalledProcessError as e:
        print(
            f"ERROR: Failed to fetch notes for issue #{issue_number}: {e.stderr}",
            file=sys.stderr,
        )
        return []
    except subprocess.TimeoutExpired:
        print("ERROR: GitLab CLI timed out.", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(
            f"ERROR: Failed to parse notes JSON for issue #{issue_number}: {e}",
            file=sys.stderr,
        )
        return []


def create_merge_request(
    title: str,
    description: str,
    source_branch: str,
    target_branch: str = "main",
    project_path: Optional[str] = None,
) -> Optional[str]:
    """Create a GitLab merge request using glab CLI.

    Args:
        title: MR title
        description: MR description/body
        source_branch: The branch with changes
        target_branch: The branch to merge into (default: main)
        project_path: Optional project path. If not provided, uses current repo.

    Returns:
        Optional[str]: The MR URL if created, None otherwise
    """
    # Get repo information from git remote if not provided
    if project_path is None:
        gitlab_repo_url = get_repo_url()
        project_path = extract_project_path(gitlab_repo_url)

    # Set up environment with GitLab token if available
    env = get_gitlab_env()

    # Push the branch first
    push_cmd = ["git", "push", "-u", "origin", source_branch]
    result = subprocess.run(
        push_cmd, capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"Warning: git push may have failed: {result.stderr}")

    # Create the MR
    cmd = [
        "glab",
        "mr",
        "create",
        "-R",
        project_path,
        "--title",
        title,
        "--description",
        description,
        "--source-branch",
        source_branch,
        "--target-branch",
        target_branch,
        "--no-editor",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, env=env, timeout=60
        )

        if result.returncode == 0:
            # Extract MR URL from output
            output = result.stdout.strip()
            # glab typically outputs the MR URL
            for line in output.split("\n"):
                if "http" in line:
                    # Extract URL from the line
                    match = re.search(r"(https?://[^\s]+)", line)
                    if match:
                        return match.group(1)
            # If no URL found, return the output
            return output
        else:
            print(f"Error creating MR: {result.stderr}", file=sys.stderr)
            return None

    except subprocess.TimeoutExpired:
        print("Error: GitLab CLI timed out.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error creating MR: {e}", file=sys.stderr)
        return None
