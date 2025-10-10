"""
Devtunnel Operations Module

This module provides cross-platform Python functions for managing Microsoft devtunnels.
All devtunnel CLI operations are performed via subprocess for compatibility.
"""

import os
import subprocess
import sys
from typing import Optional


def resolve_devtunnel_id() -> str:
    """Determine the devtunnel ID to use.

    Priority:
    1. DEVTUNNEL_ID environment variable
    2. Git repository name + '-tunnel' suffix
    3. Default 'webhook-tunnel'

    Returns:
        str: The devtunnel ID to use
    """
    # Check environment variable first
    env_tunnel_id = os.getenv("DEVTUNNEL_ID")
    if env_tunnel_id:
        return env_tunnel_id

    # Try to get repository name from git
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        repo_url = result.stdout.strip()
        if repo_url:
            repo_name = os.path.basename(repo_url.rstrip("/"))
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
            if repo_name:
                return f"{repo_name}-tunnel"
    except Exception:
        pass

    # Fallback to default
    return "webhook-tunnel"


def check_devtunnel_installed() -> bool:
    """Check if devtunnel CLI is installed and available.

    Returns:
        bool: True if devtunnel is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["devtunnel", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_devtunnel_authenticated() -> bool:
    """Check if user is authenticated with devtunnel.

    Returns:
        bool: True if authenticated, False otherwise
    """
    try:
        result = subprocess.run(
            ["devtunnel", "user", "show"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Check for authentication issues in stderr or stdout
        output = result.stderr + result.stdout
        if any(phrase in output for phrase in ["Login token expired", "Login required", "not authenticated", "Not logged in"]):
            return False
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def login_devtunnel() -> bool:
    """Interactively log in to devtunnel.

    Returns:
        bool: True if login successful, False otherwise
    """
    try:
        print("\n🔐 Logging in to devtunnel...")
        print("Please follow the authentication prompts in your browser.\n")

        # Run login interactively (no capture_output so user can interact)
        result = subprocess.run(
            ["devtunnel", "user", "login", "-g"],
            timeout=120,  # Give user 2 minutes to complete login
        )

        if result.returncode == 0:
            print("\n✅ Successfully logged in to devtunnel!")
            return True
        else:
            print("\n❌ Login failed", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("\n❌ Login timed out", file=sys.stderr)
        return False
    except Exception as e:
        print(f"\n❌ Login error: {e}", file=sys.stderr)
        return False


def create_devtunnel(tunnel_id: str) -> bool:
    """Create a new devtunnel with anonymous access.

    Args:
        tunnel_id: The ID/name for the tunnel

    Returns:
        bool: True if created successfully, False otherwise
    """
    try:
        result = subprocess.run(
            ["devtunnel", "create", tunnel_id, "-a"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            # Silent success - will be shown in summary
            return True
        else:
            # Check for authentication issues
            error_output = result.stderr + result.stdout
            if any(phrase in error_output for phrase in ["Login token expired", "Login required", "not authenticated", "Unauthorized", "Not logged in"]):
                print("❌ Authentication required", file=sys.stderr)
                print("   Run: devtunnel user login -g", file=sys.stderr)
            else:
                print(f"⚠️  Failed to create devtunnel: {result.stderr.strip()}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"⚠️  Error creating devtunnel: {e}", file=sys.stderr)
        return False


def configure_devtunnel_port(tunnel_id: str, port: int) -> bool:
    """Add HTTP port configuration to a devtunnel.

    Args:
        tunnel_id: The tunnel ID
        port: The port number to configure

    Returns:
        bool: True if configured successfully, False otherwise
    """
    try:
        result = subprocess.run(
            ["devtunnel", "port", "create", tunnel_id, "-p", str(port), "--protocol", "http"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            # Silent success - configuration will be shown in summary
            return True
        else:
            # Port might already exist, which is fine
            if "already exists" in result.stderr.lower():
                return True
            print(f"⚠️  Failed to configure port: {result.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"⚠️  Error configuring port: {e}", file=sys.stderr)
        return False


def show_devtunnel(tunnel_id: str) -> Optional[str]:
    """Get devtunnel information as text.

    Args:
        tunnel_id: The tunnel ID

    Returns:
        Optional[str]: Tunnel information text, or None if failed
    """
    try:
        result = subprocess.run(
            ["devtunnel", "show", tunnel_id],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout
        else:
            # Check for authentication issues
            error_output = result.stderr + result.stdout
            if any(phrase in error_output for phrase in ["Login token expired", "Login required", "not authenticated", "Unauthorized", "Not logged in"]):
                print("❌ Authentication required", file=sys.stderr)
                print("   Run: devtunnel user login -g", file=sys.stderr)
            else:
                # Only print if it's not a "not found" error (which is expected)
                if "not found" not in result.stderr.lower():
                    print(f"⚠️  Failed to show devtunnel: {result.stderr.strip()}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"⚠️  Error showing devtunnel: {e}", file=sys.stderr)
        return None


def delete_devtunnel(tunnel_id: str, silent: bool = False) -> bool:
    """Delete a devtunnel.

    Args:
        tunnel_id: The tunnel ID to delete
        silent: If True, suppress output messages

    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        result = subprocess.run(
            ["devtunnel", "delete", tunnel_id, "-f"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            # Silent - will be shown in summary
            return True
        else:
            # If tunnel doesn't exist, consider it success
            if "not found" in result.stderr.lower():
                if not silent:
                    print(f"ℹ️  Devtunnel {tunnel_id} doesn't exist (already deleted)")
                return True
            if not silent:
                print(f"⚠️  Failed to delete devtunnel: {result.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"⚠️  Error deleting devtunnel: {e}", file=sys.stderr)
        return False


def start_devtunnel_host(tunnel_id: str, port: int = None) -> Optional[subprocess.Popen]:
    """Start hosting a devtunnel in the background.

    Args:
        tunnel_id: The tunnel ID to host
        port: The port number to expose (only used for temporary tunnels)

    Returns:
        Optional[subprocess.Popen]: The host process, or None if failed
    """
    try:
        # For existing tunnels with ports already configured, don't use -p flag
        # The port was already configured via 'devtunnel port create'
        cmd = ["devtunnel", "host", tunnel_id]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        # Silent - status will be shown after checking readiness
        return process
    except Exception as e:
        print(f"⚠️  Error starting devtunnel host: {e}", file=sys.stderr)
        return None


def get_devtunnel_url(tunnel_id: str, port: int) -> Optional[str]:
    """Get the public URL for a devtunnel port.

    Args:
        tunnel_id: The tunnel ID
        port: The port number

    Returns:
        Optional[str]: The public URL, or None if failed
    """
    tunnel_info = show_devtunnel(tunnel_id)
    if not tunnel_info:
        return None

    # Parse tunnel info to extract the tunnel host
    # Format: "Tunnel ID: tunnel-name.region.devtunnels.ms"
    full_tunnel_id = None
    for line in tunnel_info.split("\n"):
        if line.startswith("Tunnel ID"):
            # Extract the full tunnel ID (after the colon)
            parts = line.split(":")
            if len(parts) >= 2:
                full_tunnel_id = parts[1].strip()
                break

    if not full_tunnel_id:
        print("⚠️  Could not parse tunnel ID from output", file=sys.stderr)
        return None

    # Construct URL: https://tunnel-name-PORT.region.devtunnels.ms
    # Split full_tunnel_id into name and region
    tunnel_parts = full_tunnel_id.split(".", 1)
    if len(tunnel_parts) < 2:
        print("⚠️  Invalid tunnel ID format", file=sys.stderr)
        return None

    tunnel_name = tunnel_parts[0]
    tunnel_region = tunnel_parts[1]

    # The tunnel ID from 'devtunnel show' is like "tunnel-name.usw3"
    # We need to add the .devtunnels.ms suffix
    url = f"https://{tunnel_name}-{port}.{tunnel_region}.devtunnels.ms"
    return url
