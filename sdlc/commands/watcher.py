"""
Watcher Command - GitHub Webhook Listener

This command starts a FastAPI server that listens for GitHub webhook events
and triggers ADW workflows. It automatically manages devtunnel setup and
GitHub webhook configuration.
"""

import asyncio
import atexit
import os
import signal
import subprocess
import sys
from typing import Optional

import click
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request

from sdlc.lib.devtunnel import (
    check_devtunnel_authenticated,
    check_devtunnel_installed,
    configure_devtunnel_port,
    create_devtunnel,
    delete_devtunnel,
    login_devtunnel,
    resolve_devtunnel_id,
    show_devtunnel,
    start_devtunnel_host,
)
from sdlc.lib.github import extract_repo_path, get_repo_url
from sdlc.lib.utils import make_adw_id
from sdlc.lib.webhook import (
    ensure_webhook_configured,
    get_webhook_url_from_tunnel,
    remove_devtunnel_webhooks,
)

# Load environment variables
load_dotenv()

# Global variables for cleanup
devtunnel_process: Optional[subprocess.Popen] = None
tunnel_id_global: Optional[str] = None


def cleanup_resources(tunnel_id: str, remove_all: bool = False):
    """Clean up devtunnel and related resources.

    Args:
        tunnel_id: The devtunnel ID
        remove_all: If True, also remove webhooks and delete tunnel
    """
    global devtunnel_process

    # Stop devtunnel host process
    if devtunnel_process and devtunnel_process.poll() is None:
        print("\n🛑 Stopping devtunnel host...")
        devtunnel_process.terminate()
        try:
            devtunnel_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            devtunnel_process.kill()
        print("✅ Devtunnel host stopped")
        devtunnel_process = None

    # If --remove flag was used, clean up everything
    if remove_all:
        try:
            # Get repository path
            repo_url = get_repo_url()
            repo_path = extract_repo_path(repo_url)

            # Remove webhooks
            print("🗑️  Deleting GitHub webhooks...")
            removed = remove_devtunnel_webhooks(repo_path, silent=False)
            if removed > 0:
                print(f"  ✅ Deleted {removed} webhook(s)")

            # Delete tunnel
            print(f"🗑️  Deleting devtunnel {tunnel_id}...")
            delete_devtunnel(tunnel_id)
        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}", file=sys.stderr)


def signal_handler(signum, frame, tunnel_id: str):
    """Handle interrupt signals."""
    cleanup_resources(tunnel_id, remove_all=False)
    sys.exit(0)


@click.command()
@click.option(
    "--remove",
    is_flag=True,
    default=False,
    help="Remove webhooks and delete devtunnel on exit",
)
@click.option(
    "--port",
    type=int,
    default=8001,
    help="Port to run the webhook server on (default: 8001)",
)
@click.option(
    "--tunnel-id",
    type=str,
    default=None,
    help="Devtunnel ID to use (defaults to repo name or DEVTUNNEL_ID env var)",
)
def watcher(remove: bool, port: int, tunnel_id: Optional[str]):
    """Start GitHub webhook watcher server.

    The watcher command starts a FastAPI server that receives GitHub webhook events
    and triggers ADW workflows. It automatically:

    \b
    - Creates and manages a Microsoft devtunnel for webhook exposure
    - Configures GitHub webhooks pointing to the devtunnel URL
    - Listens for issue events and triggers ADW workflows
    - Provides health check endpoint at /health

    Examples:

    \b
        # Start watcher with defaults
        sdlc watcher

    \b
        # Start on custom port
        sdlc watcher --port 9000

    \b
        # Stop and clean up all resources
        sdlc watcher --remove

    Press Ctrl+C to stop the server (keeps tunnel and webhooks unless --remove is used).
    """
    global devtunnel_process, tunnel_id_global

    # If --remove flag is set, clean up and exit
    if remove:
        tunnel_id = tunnel_id or resolve_devtunnel_id()
        tunnel_id_global = tunnel_id
        print(f"🧹 Cleaning up watcher resources for tunnel: {tunnel_id}")
        cleanup_resources(tunnel_id, remove_all=True)

        # Also kill any processes on the port
        try:
            subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
            )
        except Exception:
            pass  # lsof might not be available on all platforms

        return

    # Start watcher server
    print("🚀 Starting GitHub Webhook Watcher\n")

    # Check devtunnel installation
    if not check_devtunnel_installed():
        print("❌ Error: devtunnel CLI is not installed")
        print("\nTo install devtunnel:")
        print("  Visit: https://aka.ms/devtunnels/download")
        sys.exit(1)

    # Check authentication and auto-login if needed
    if not check_devtunnel_authenticated():
        print("⚠️  Not authenticated with devtunnel")

        # Attempt automatic login
        if not login_devtunnel():
            print("\n❌ Failed to authenticate with devtunnel")
            print("Please run manually: devtunnel user login -g")
            sys.exit(1)

        # Verify authentication succeeded
        if not check_devtunnel_authenticated():
            print("❌ Authentication verification failed")
            sys.exit(1)

    # Resolve tunnel ID
    tunnel_id = tunnel_id or resolve_devtunnel_id()
    tunnel_id_global = tunnel_id

    # Check if tunnel exists, create if not
    tunnel_info = show_devtunnel(tunnel_id)
    tunnel_created = False
    if not tunnel_info:
        if not create_devtunnel(tunnel_id):
            print("❌ Failed to create devtunnel")
            sys.exit(1)
        tunnel_info = show_devtunnel(tunnel_id)
        tunnel_created = True

    # Configure port
    configure_devtunnel_port(tunnel_id, port)

    # Get webhook URL
    webhook_url = get_webhook_url_from_tunnel(tunnel_id, port)
    if not webhook_url:
        print("❌ Failed to get webhook URL")
        sys.exit(1)

    # Print configuration summary
    print("Configuration:")
    print(f"  📡 Devtunnel: {tunnel_id} {'(created)' if tunnel_created else '(existing)'}")
    print(f"  🌐 Webhook URL: {webhook_url}")
    print(f"  🏥 Local server: http://0.0.0.0:{port}")
    print(f"\nPress Ctrl+C to stop")
    print("(tunnel and webhooks will persist unless --remove is used)\n")

    # Register cleanup handlers
    atexit.register(lambda: cleanup_resources(tunnel_id, remove_all=remove))
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, tunnel_id))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, tunnel_id))

    # Create FastAPI app (devtunnel will be started in startup event)
    app = create_fastapi_app(tunnel_id, port)

    # Run uvicorn server
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    finally:
        cleanup_resources(tunnel_id, remove_all=remove)


def create_fastapi_app(tunnel_id: str, port: int) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        tunnel_id: The devtunnel ID
        port: The server port

    Returns:
        FastAPI: Configured FastAPI application
    """
    app = FastAPI(
        title="ADW Webhook Trigger",
        description="GitHub webhook endpoint for AI Developer Workflow (ADW)",
    )

    @app.on_event("startup")
    async def configure_webhook():
        """Configure GitHub webhook and start devtunnel host after server starts."""
        global devtunnel_process

        print("\nSetting up services...")

        # Server is now listening, start devtunnel host
        devtunnel_process = start_devtunnel_host(tunnel_id)

        if not devtunnel_process:
            print("  ❌ Failed to start devtunnel host")
            return

        # Wait for devtunnel to be ready by reading its output
        tunnel_ready = False
        timeout = 10  # 10 second timeout
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            # Check if process exited
            if devtunnel_process.poll() is not None:
                print("  ❌ Devtunnel process exited unexpectedly")
                return

            # Read a line from stdout (non-blocking check)
            try:
                line = devtunnel_process.stdout.readline()
                if line:
                    # Silently consume output unless it's an error
                    if "error" in line.lower() or "failed" in line.lower():
                        print(f"  ⚠️  {line.rstrip()}")
                    # Look for indicators that tunnel is ready
                    if "Starting tunnel host" in line or "Ready to accept connections" in line:
                        tunnel_ready = True
                        break
            except Exception:
                pass

            await asyncio.sleep(0.1)

        if not tunnel_ready:
            print("  ⚠️  Devtunnel startup timeout - continuing anyway")
        else:
            print("  ✅ Devtunnel host ready")

        # Additional safety margin
        await asyncio.sleep(1)

        try:
            # Get repository information
            repo_url = get_repo_url()
            repo_path = extract_repo_path(repo_url)

            # Get webhook URL
            webhook_url = get_webhook_url_from_tunnel(tunnel_id, port)
            if not webhook_url:
                print("  ❌ Could not determine webhook URL")
                return

            # Ensure webhook is configured
            if ensure_webhook_configured(repo_path, webhook_url):
                # Extract webhook ID if it was created
                print("  ✅ GitHub webhook configured")
            else:
                print("  ❌ Could not configure webhook")

        except Exception as e:
            print(f"  ❌ Error configuring webhook: {e}")

    @app.post("/gh-webhook")
    async def github_webhook(request: Request):
        """Handle GitHub webhook events."""
        try:
            # Get event type from header
            event_type = request.headers.get("X-GitHub-Event", "")

            # Parse webhook payload
            payload = await request.json()

            # Extract event details
            action = payload.get("action", "")
            issue = payload.get("issue", {})
            issue_number = issue.get("number")

            print(
                f"Received webhook: event={event_type}, action={action}, issue_number={issue_number}"
            )

            # Handle ping events
            if event_type == "ping":
                zen = payload.get("zen", "GitHub Webhook Active")
                print(f"Received ping event: {zen}")
                return {
                    "status": "ok",
                    "message": "Webhook is active and receiving events",
                    "pong": zen,
                }

            should_trigger = False
            trigger_reason = ""

            # Check if this is an issue opened event
            if event_type == "issues" and action == "opened" and issue_number:
                should_trigger = True
                trigger_reason = "New issue opened"

            # Check if this is an issue comment with 'adw' text
            elif event_type == "issue_comment" and action == "created" and issue_number:
                comment = payload.get("comment", {})
                comment_body = comment.get("body", "").strip().lower()

                print(f"Comment body: '{comment_body}'")

                if comment_body == "adw":
                    should_trigger = True
                    trigger_reason = "Comment with 'adw' command"

            if should_trigger:
                # Generate ADW ID for this workflow
                adw_id = make_adw_id()

                # Find the script directory
                script_dir = os.path.join(os.getcwd(), "scripts")
                trigger_script = os.path.join(script_dir, "adw_plan_build.py")

                # Check if script exists
                if not os.path.exists(trigger_script):
                    print(f"⚠️  Script not found: {trigger_script}")
                    return {
                        "status": "error",
                        "message": "adw_plan_build.py script not found",
                    }

                # Build command
                cmd = ["uv", "run", trigger_script, str(issue_number), adw_id]

                print(
                    f"Launching background process: {' '.join(cmd)} (reason: {trigger_reason})"
                )

                # Launch in background
                process = subprocess.Popen(
                    cmd, cwd=os.getcwd(), env=os.environ.copy()
                )

                print(f"Background process started for issue #{issue_number} with ADW ID: {adw_id}")
                print(f"Logs will be written to: agents/{adw_id}/adw_plan_build/execution.log")

                return {
                    "status": "accepted",
                    "issue": issue_number,
                    "adw_id": adw_id,
                    "message": f"ADW workflow triggered for issue #{issue_number}",
                    "reason": trigger_reason,
                    "logs": f"agents/{adw_id}/adw_plan_build/",
                }
            else:
                print(
                    f"Ignoring webhook: event={event_type}, action={action}, issue_number={issue_number}"
                )
                return {
                    "status": "ignored",
                    "reason": f"Not a triggering event (event={event_type}, action={action})",
                }

        except Exception as e:
            print(f"Error processing webhook: {e}")
            # Always return 200 to GitHub to prevent retries
            return {"status": "error", "message": "Internal error processing webhook"}

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        try:
            # Run health check command
            result = subprocess.run(
                ["sdlc", "health"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Parse output
            is_healthy = result.returncode == 0
            warnings = []
            errors = []

            # Extract warnings and errors from output
            output_lines = result.stdout.strip().split("\n")
            capturing_warnings = False
            capturing_errors = False

            for line in output_lines:
                if "⚠️  Warnings:" in line:
                    capturing_warnings = True
                    capturing_errors = False
                    continue
                elif "❌ Errors:" in line:
                    capturing_errors = True
                    capturing_warnings = False
                    continue
                elif "📝 Next Steps:" in line:
                    break

                if capturing_warnings and line.strip().startswith("-"):
                    warnings.append(line.strip()[2:])
                elif capturing_errors and line.strip().startswith("-"):
                    errors.append(line.strip()[2:])

            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "service": "adw-webhook-watcher",
                "health_check": {
                    "success": is_healthy,
                    "warnings": warnings,
                    "errors": errors,
                    "details": "Run 'sdlc health' for full report",
                },
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "unhealthy",
                "service": "adw-webhook-watcher",
                "error": "Health check timed out",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "adw-webhook-watcher",
                "error": f"Health check failed: {str(e)}",
            }

    return app
