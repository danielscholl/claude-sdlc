#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic"]
# ///

"""
GitHub Operations Module - AI Developer Workflow (ADW)

This module contains all GitHub-related operations including:
- Issue fetching and manipulation
- Comment posting
- Repository path extraction
- Issue status management
"""

import subprocess
import sys
import os
import json
from typing import Dict, List, Optional
from data_types import GitHubIssue, GitHubIssueListItem


def get_github_env() -> Optional[dict]:
    """Get environment with GitHub token set up. Returns None if no GITHUB_PAT.
    
    Subprocess env behavior:
    - env=None → Inherits parent's environment (default)
    - env={} → Empty environment (no variables)
    - env=custom_dict → Only uses specified variables
    
    So this will work with gh authentication:
    # These are equivalent:
    result = subprocess.run(cmd, capture_output=True, text=True)
    result = subprocess.run(cmd, capture_output=True, text=True, env=None)
    
    But this will NOT work (no PATH, no auth):
    result = subprocess.run(cmd, capture_output=True, text=True, env={})
    """
    github_pat = os.getenv("GITHUB_PAT")
    if not github_pat:
        return None
    
    # Only create minimal env with GitHub token
    env = {
        "GH_TOKEN": github_pat,
        "PATH": os.environ.get("PATH", ""),
    }
    return env


def get_repo_url() -> str:
    """Get GitHub repository URL from git remote."""
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


def extract_repo_path(github_url: str) -> str:
    """Extract owner/repo from GitHub URL."""
    # Handle both https://github.com/owner/repo and https://github.com/owner/repo.git
    return github_url.replace("https://github.com/", "").replace(".git", "")


def fetch_issue(issue_number: str, repo_path: str) -> GitHubIssue:
    """Fetch GitHub issue using gh CLI and return typed model."""
    # Use JSON output for structured data
    cmd = [
        "gh",
        "issue",
        "view",
        issue_number,
        "-R",
        repo_path,
        "--json",
        "number,title,body,state,author,assignees,labels,milestone,comments,createdAt,updatedAt,closedAt,url",
    ]

    # Set up environment with GitHub token if available
    env = get_github_env()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode == 0:
            # Parse JSON response into Pydantic model
            issue_data = json.loads(result.stdout)
            issue = GitHubIssue(**issue_data)

            return issue
        else:
            print(result.stderr, file=sys.stderr)
            sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: GitHub CLI (gh) is not installed.", file=sys.stderr)
        print("\nTo install gh:", file=sys.stderr)
        print("  - macOS: brew install gh", file=sys.stderr)
        print(
            "  - Linux: See https://github.com/cli/cli#installation",
            file=sys.stderr,
        )
        print(
            "  - Windows: See https://github.com/cli/cli#installation", file=sys.stderr
        )
        print("\nAfter installation, authenticate with: gh auth login", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing issue data: {e}", file=sys.stderr)
        sys.exit(1)


def make_issue_comment(issue_id: str, comment: str) -> None:
    """Post a comment to a GitHub issue using gh CLI."""
    # Get repo information from git remote
    github_repo_url = get_repo_url()
    repo_path = extract_repo_path(github_repo_url)

    # Build command
    cmd = [
        "gh",
        "issue",
        "comment",
        issue_id,
        "-R",
        repo_path,
        "--body",
        comment,
    ]

    # Set up environment with GitHub token if available
    env = get_github_env()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode == 0:
            print(f"Successfully posted comment to issue #{issue_id}")
        else:
            print(f"Error posting comment: {result.stderr}", file=sys.stderr)
            sys.exit(result.returncode)
    except Exception as e:
        print(f"Error posting comment: {e}", file=sys.stderr)
        sys.exit(1)


def mark_issue_in_progress(issue_id: str) -> None:
    """Mark issue as in progress by adding label and comment."""
    # Get repo information from git remote
    github_repo_url = get_repo_url()
    repo_path = extract_repo_path(github_repo_url)

    # Add "in_progress" label
    cmd = [
        "gh",
        "issue",
        "edit",
        issue_id,
        "-R",
        repo_path,
        "--add-label",
        "in_progress",
    ]

    # Set up environment with GitHub token if available
    env = get_github_env()

    # Try to add label (may fail if label doesn't exist)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"Note: Could not add 'in_progress' label: {result.stderr}")

    # Post comment indicating work has started
    # make_issue_comment(issue_id, "🚧 ADW is working on this issue...")

    # Assign to self (optional)
    cmd = [
        "gh",
        "issue",
        "edit",
        issue_id,
        "-R",
        repo_path,
        "--add-assignee",
        "@me",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode == 0:
        print(f"Assigned issue #{issue_id} to self")


def fetch_open_issues(repo_path: str) -> List[GitHubIssueListItem]:
    """Fetch all open issues from the GitHub repository."""
    try:
        cmd = [
            "gh",
            "issue",
            "list",
            "--repo",
            repo_path,
            "--state",
            "open",
            "--json",
            "number,title,body,labels,createdAt,updatedAt",
            "--limit",
            "1000",
        ]

        # Set up environment with GitHub token if available
        env = get_github_env()

        # DEBUG level - not printing command
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, env=env
        )

        issues_data = json.loads(result.stdout)
        issues = [GitHubIssueListItem(**issue_data) for issue_data in issues_data]
        print(f"Fetched {len(issues)} open issues")
        return issues

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to fetch issues: {e.stderr}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse issues JSON: {e}", file=sys.stderr)
        return []


def fetch_issue_comments(repo_path: str, issue_number: int) -> List[Dict]:
    """Fetch all comments for a specific issue."""
    try:
        cmd = [
            "gh",
            "issue",
            "view",
            str(issue_number),
            "--repo",
            repo_path,
            "--json",
            "comments",
        ]

        # Set up environment with GitHub token if available
        env = get_github_env()

        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, env=env
        )
        data = json.loads(result.stdout)
        comments = data.get("comments", [])

        # Sort comments by creation time
        comments.sort(key=lambda c: c.get("createdAt", ""))

        # DEBUG level - not printing
        return comments

    except subprocess.CalledProcessError as e:
        print(
            f"ERROR: Failed to fetch comments for issue #{issue_number}: {e.stderr}",
            file=sys.stderr,
        )
        return []
    except json.JSONDecodeError as e:
        print(
            f"ERROR: Failed to parse comments JSON for issue #{issue_number}: {e}",
            file=sys.stderr,
        )
        return []
