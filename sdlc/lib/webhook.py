"""
GitHub Webhook Operations Module

This module provides functions for managing GitHub webhooks via the gh CLI.
"""

import json
import subprocess
import sys
from typing import List, Dict, Optional

from sdlc.lib.github import get_repo_url, extract_repo_path, get_github_env
from sdlc.lib.devtunnel import get_devtunnel_url


def get_webhook_url_from_tunnel(tunnel_id: str, port: int, endpoint: str = "/gh-webhook") -> Optional[str]:
    """Construct webhook URL from devtunnel information.

    Args:
        tunnel_id: The devtunnel ID
        port: The port number
        endpoint: The webhook endpoint path (default: /gh-webhook)

    Returns:
        Optional[str]: The full webhook URL, or None if failed
    """
    base_url = get_devtunnel_url(tunnel_id, port)
    if not base_url:
        return None

    # Ensure endpoint starts with /
    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"

    return f"{base_url}{endpoint}"


def list_github_webhooks(repo_path: str) -> List[Dict]:
    """Fetch all webhooks for a GitHub repository.

    Args:
        repo_path: The repository path (owner/repo)

    Returns:
        List[Dict]: List of webhook objects
    """
    try:
        cmd = ["gh", "api", f"repos/{repo_path}/hooks"]

        # Set up environment with GitHub token if available
        env = get_github_env()

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

        if result.returncode == 0:
            webhooks = json.loads(result.stdout)
            return webhooks
        else:
            print(f"⚠️  Failed to list webhooks: {result.stderr}", file=sys.stderr)
            return []

    except Exception as e:
        print(f"⚠️  Error listing webhooks: {e}", file=sys.stderr)
        return []


def create_github_webhook(repo_path: str, webhook_url: str, events: List[str] = None) -> Optional[int]:
    """Create a new GitHub webhook.

    Args:
        repo_path: The repository path (owner/repo)
        webhook_url: The webhook URL to call
        events: List of events to subscribe to (default: ["issues", "issue_comment"])

    Returns:
        Optional[int]: The webhook ID if created, None otherwise
    """
    if events is None:
        events = ["issues", "issue_comment"]

    try:
        cmd = [
            "gh", "api", f"repos/{repo_path}/hooks",
            "-X", "POST",
            "-f", "name=web",
            "-f", f"config[url]={webhook_url}",
            "-f", "config[content_type]=json",
            "-F", "active=true",
        ]

        # Add event subscriptions
        for event in events:
            cmd.extend(["-f", f"events[]={event}"])

        # Set up environment with GitHub token if available
        env = get_github_env()

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

        if result.returncode == 0:
            webhook_data = json.loads(result.stdout)
            webhook_id = webhook_data.get("id")
            print(f"✅ Created webhook: ID {webhook_id}")
            return webhook_id
        else:
            print(f"⚠️  Failed to create webhook: {result.stderr}", file=sys.stderr)
            return None

    except Exception as e:
        print(f"⚠️  Error creating webhook: {e}", file=sys.stderr)
        return None


def delete_github_webhook(repo_path: str, webhook_id: int) -> bool:
    """Delete a GitHub webhook by ID.

    Args:
        repo_path: The repository path (owner/repo)
        webhook_id: The webhook ID to delete

    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        cmd = [
            "gh", "api",
            f"repos/{repo_path}/hooks/{webhook_id}",
            "-X", "DELETE"
        ]

        # Set up environment with GitHub token if available
        env = get_github_env()

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

        if result.returncode == 0 or result.returncode == 204:
            print(f"✅ Deleted webhook: ID {webhook_id}")
            return True
        else:
            print(f"⚠️  Failed to delete webhook {webhook_id}: {result.stderr}", file=sys.stderr)
            return False

    except Exception as e:
        print(f"⚠️  Error deleting webhook: {e}", file=sys.stderr)
        return False


def remove_devtunnel_webhooks(repo_path: str) -> int:
    """Remove all devtunnel-based webhooks from a repository.

    Args:
        repo_path: The repository path (owner/repo)

    Returns:
        int: Number of webhooks removed
    """
    webhooks = list_github_webhooks(repo_path)
    removed_count = 0

    for webhook in webhooks:
        config = webhook.get("config", {})
        url = config.get("url", "")

        # Check if this is a devtunnel webhook
        if "devtunnels.ms" in url:
            webhook_id = webhook.get("id")
            if webhook_id and delete_github_webhook(repo_path, webhook_id):
                removed_count += 1

    if removed_count > 0:
        print(f"✅ Removed {removed_count} devtunnel webhook(s)")
    else:
        print("ℹ️  No devtunnel webhooks found to remove")

    return removed_count


def ensure_webhook_configured(repo_path: str, webhook_url: str, events: List[str] = None) -> bool:
    """Ensure webhook is configured, creating it if necessary.

    This function checks if a webhook with the given URL already exists.
    If it does, nothing is done. If not, it removes old devtunnel webhooks
    and creates a new one.

    Args:
        repo_path: The repository path (owner/repo)
        webhook_url: The webhook URL to configure
        events: List of events to subscribe to (default: ["issues", "issue_comment"])

    Returns:
        bool: True if webhook is configured, False otherwise
    """
    if events is None:
        events = ["issues", "issue_comment"]

    # Check if webhook already exists
    webhooks = list_github_webhooks(repo_path)

    for webhook in webhooks:
        config = webhook.get("config", {})
        url = config.get("url", "")
        if url == webhook_url:
            print(f"ℹ️  Webhook already configured: {webhook_url}")
            return True

    # Remove old devtunnel webhooks
    print("🔄 Removing old devtunnel webhooks...")
    remove_devtunnel_webhooks(repo_path)

    # Create new webhook
    print(f"🔗 Creating new webhook: {webhook_url}")
    webhook_id = create_github_webhook(repo_path, webhook_url, events)

    return webhook_id is not None
