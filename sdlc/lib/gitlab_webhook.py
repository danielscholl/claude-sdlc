"""
GitLab Webhook Operations Module

This module provides functions for managing GitLab webhooks via the glab CLI.
"""

import json
import subprocess
import sys
import urllib.parse
from typing import Dict, List, Optional

from sdlc.lib.gitlab import get_gitlab_env
from sdlc.lib.devtunnel import get_devtunnel_url


def get_webhook_url_from_tunnel(
    tunnel_id: str, port: int, endpoint: str = "/gl-webhook"
) -> Optional[str]:
    """Construct webhook URL from devtunnel information.

    Args:
        tunnel_id: The devtunnel ID
        port: The port number
        endpoint: The webhook endpoint path (default: /gl-webhook)

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


def get_project_id(project_path: str) -> Optional[str]:
    """Get the GitLab project ID for API calls.

    GitLab API requires the project ID to be URL-encoded when used in paths.

    Args:
        project_path: The project path (e.g., "owner/repo")

    Returns:
        Optional[str]: URL-encoded project path for API use
    """
    # URL encode the project path for API calls
    return urllib.parse.quote(project_path, safe="")


def list_gitlab_webhooks(project_path: str) -> List[Dict]:
    """Fetch all webhooks for a GitLab project.

    Args:
        project_path: The project path (e.g., "owner/repo")

    Returns:
        List[Dict]: List of webhook objects
    """
    try:
        # URL encode the project path
        encoded_path = get_project_id(project_path)

        cmd = ["glab", "api", f"projects/{encoded_path}/hooks"]

        # Set up environment with GitLab token if available
        env = get_gitlab_env()

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

        if result.returncode == 0:
            webhooks = json.loads(result.stdout)
            return webhooks if isinstance(webhooks, list) else []
        else:
            print(f"Warning: Failed to list webhooks: {result.stderr}", file=sys.stderr)
            return []

    except json.JSONDecodeError:
        print("Warning: Invalid JSON response from webhook list", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Warning: Error listing webhooks: {e}", file=sys.stderr)
        return []


def create_gitlab_webhook(
    project_path: str,
    webhook_url: str,
    issues_events: bool = True,
    note_events: bool = True,
    merge_requests_events: bool = False,
) -> Optional[int]:
    """Create a new GitLab webhook.

    Args:
        project_path: The project path (e.g., "owner/repo")
        webhook_url: The webhook URL to call
        issues_events: Subscribe to issue events (default: True)
        note_events: Subscribe to note/comment events (default: True)
        merge_requests_events: Subscribe to MR events (default: False)

    Returns:
        Optional[int]: The webhook ID if created, None otherwise
    """
    try:
        # URL encode the project path
        encoded_path = get_project_id(project_path)

        cmd = [
            "glab",
            "api",
            f"projects/{encoded_path}/hooks",
            "-X",
            "POST",
            "-f",
            f"url={webhook_url}",
            "-f",
            f"issues_events={str(issues_events).lower()}",
            "-f",
            f"note_events={str(note_events).lower()}",
            "-f",
            f"merge_requests_events={str(merge_requests_events).lower()}",
            "-f",
            "enable_ssl_verification=true",
        ]

        # Set up environment with GitLab token if available
        env = get_gitlab_env()

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
            # Silent - will be shown in summary
            return webhook_id
        else:
            print(f"Warning: Failed to create webhook: {result.stderr}", file=sys.stderr)
            return None

    except Exception as e:
        print(f"Warning: Error creating webhook: {e}", file=sys.stderr)
        return None


def delete_gitlab_webhook(project_path: str, webhook_id: int) -> bool:
    """Delete a GitLab webhook by ID.

    Args:
        project_path: The project path (e.g., "owner/repo")
        webhook_id: The webhook ID to delete

    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        # URL encode the project path
        encoded_path = get_project_id(project_path)

        cmd = [
            "glab",
            "api",
            f"projects/{encoded_path}/hooks/{webhook_id}",
            "-X",
            "DELETE",
        ]

        # Set up environment with GitLab token if available
        env = get_gitlab_env()

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

        # DELETE returns 204 No Content on success
        if result.returncode == 0:
            return True
        else:
            print(
                f"Warning: Failed to delete webhook {webhook_id}: {result.stderr}",
                file=sys.stderr,
            )
            return False

    except Exception as e:
        print(f"Warning: Error deleting webhook: {e}", file=sys.stderr)
        return False


def remove_devtunnel_webhooks(project_path: str, silent: bool = False) -> int:
    """Remove all devtunnel-based webhooks from a GitLab project.

    Args:
        project_path: The project path (e.g., "owner/repo")
        silent: If True, suppress output messages

    Returns:
        int: Number of webhooks removed
    """
    webhooks = list_gitlab_webhooks(project_path)
    removed_count = 0

    for webhook in webhooks:
        url = webhook.get("url", "")

        # Check if this is a devtunnel webhook
        if "devtunnels.ms" in url:
            webhook_id = webhook.get("id")
            if webhook_id and delete_gitlab_webhook(project_path, webhook_id):
                removed_count += 1

    # Only print if not silent and for backward compatibility
    if not silent and removed_count == 0:
        print("  Info: No devtunnel webhooks found")

    return removed_count


def ensure_webhook_configured(
    project_path: str,
    webhook_url: str,
    issues_events: bool = True,
    note_events: bool = True,
) -> bool:
    """Ensure webhook is configured, creating it if necessary.

    This function checks if a webhook with the given URL already exists.
    If it does, nothing is done. If not, it removes old devtunnel webhooks
    and creates a new one.

    Args:
        project_path: The project path (e.g., "owner/repo")
        webhook_url: The webhook URL to configure
        issues_events: Subscribe to issue events
        note_events: Subscribe to note events

    Returns:
        bool: True if webhook is configured, False otherwise
    """
    # Check if webhook already exists
    webhooks = list_gitlab_webhooks(project_path)

    for webhook in webhooks:
        url = webhook.get("url", "")
        if url == webhook_url:
            # Webhook already exists, silently return success
            return True

    # Remove old devtunnel webhooks silently
    remove_devtunnel_webhooks(project_path, silent=True)

    # Create new webhook
    webhook_id = create_gitlab_webhook(
        project_path,
        webhook_url,
        issues_events=issues_events,
        note_events=note_events,
    )

    return webhook_id is not None
