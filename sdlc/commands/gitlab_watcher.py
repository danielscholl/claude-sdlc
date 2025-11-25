"""
GitLab Watcher Command - GitLab Webhook Listener

This command starts a FastAPI server that listens for GitLab webhook events
and triggers ADW workflows. It automatically manages devtunnel setup and
GitLab webhook configuration.
"""

import asyncio
import atexit
import signal
import subprocess
import sys
from typing import Optional

import click
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request

from sdlc.lib.agent import parse_agent_command
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
from sdlc.lib.gitlab import extract_project_path, fetch_issue, get_repo_url
from sdlc.lib.utils import make_adw_id, setup_logger
from sdlc.lib.gitlab_webhook import (
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
        devtunnel_process.terminate()
        try:
            devtunnel_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            devtunnel_process.kill()
        print("\n Devtunnel host stopped")
        devtunnel_process = None

    # If --remove flag was used, clean up everything
    if remove_all:
        try:
            # Get repository path
            repo_url = get_repo_url()
            project_path = extract_project_path(repo_url)

            # Remove webhooks
            removed = remove_devtunnel_webhooks(project_path, silent=True)
            if removed > 0:
                print(f"  Deleted {removed} webhook(s)")
            else:
                print("  No webhooks to delete")

            # Delete tunnel
            if delete_devtunnel(tunnel_id, silent=True):
                print(f"  Deleted devtunnel {tunnel_id}")
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}", file=sys.stderr)


def signal_handler(signum, frame, tunnel_id: str):
    """Handle interrupt signals."""
    cleanup_resources(tunnel_id, remove_all=False)
    sys.exit(0)


@click.command("gitlab-watcher")
@click.option(
    "--remove",
    is_flag=True,
    default=False,
    help="Remove webhooks and delete devtunnel on exit",
)
@click.option(
    "--port",
    type=int,
    default=8002,
    help="Port to run the webhook server on (default: 8002)",
)
@click.option(
    "--tunnel-id",
    type=str,
    default=None,
    help="Devtunnel ID to use (defaults to repo name or DEVTUNNEL_ID env var)",
)
def gitlab_watcher(remove: bool, port: int, tunnel_id: Optional[str]):
    """Start GitLab webhook watcher server.

    The gitlab-watcher command starts a FastAPI server that receives GitLab webhook events
    and triggers ADW workflows. It automatically:

    \b
    - Creates and manages a Microsoft devtunnel for webhook exposure
    - Configures GitLab webhooks pointing to the devtunnel URL
    - Listens for issue and note events and triggers ADW workflows
    - Provides health check endpoint at /health

    Examples:

    \b
        # Start watcher with defaults
        sdlc gitlab-watcher

    \b
        # Start on custom port
        sdlc gitlab-watcher --port 9000

    \b
        # Stop and clean up all resources
        sdlc gitlab-watcher --remove

    Press Ctrl+C to stop the server (keeps tunnel and webhooks unless --remove is used).
    """
    global devtunnel_process, tunnel_id_global

    # If --remove flag is set, clean up and exit
    if remove:
        tunnel_id = tunnel_id or resolve_devtunnel_id()
        tunnel_id_global = tunnel_id
        print(f"Cleaning up watcher resources for tunnel: {tunnel_id}")
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
    print("Starting GitLab Webhook Watcher\n")

    # Check devtunnel installation
    if not check_devtunnel_installed():
        print("Error: devtunnel CLI is not installed")
        print("\nTo install devtunnel:")
        print("  Visit: https://aka.ms/devtunnels/download")
        sys.exit(1)

    # Check authentication and auto-login if needed
    if not check_devtunnel_authenticated():
        print("Warning: Not authenticated with devtunnel")

        # Attempt automatic login
        if not login_devtunnel():
            print("\nError: Failed to authenticate with devtunnel")
            print("Please run manually: devtunnel user login -g")
            sys.exit(1)

        # Verify authentication succeeded
        if not check_devtunnel_authenticated():
            print("Error: Authentication verification failed")
            sys.exit(1)

    # Resolve tunnel ID
    tunnel_id = tunnel_id or resolve_devtunnel_id()
    tunnel_id_global = tunnel_id

    # Check if tunnel exists, create if not
    tunnel_info = show_devtunnel(tunnel_id)
    tunnel_created = False
    if not tunnel_info:
        if not create_devtunnel(tunnel_id):
            print("Error: Failed to create devtunnel")
            sys.exit(1)
        tunnel_info = show_devtunnel(tunnel_id)
        tunnel_created = True

    # Configure port
    configure_devtunnel_port(tunnel_id, port)

    # Get webhook URL
    webhook_url = get_webhook_url_from_tunnel(tunnel_id, port)
    if not webhook_url:
        print("Error: Failed to get webhook URL")
        sys.exit(1)

    # Print configuration summary
    print("Configuration:")
    print(f"  Devtunnel: {tunnel_id} {'(created)' if tunnel_created else '(existing)'}")
    print(f"  Webhook URL: {webhook_url}")
    print(f"  Local server: http://0.0.0.0:{port}")
    print("\nPress Ctrl+C to stop\n")

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
        title="ADW GitLab Webhook Trigger",
        description="GitLab webhook endpoint for AI Developer Workflow (ADW)",
    )

    @app.on_event("startup")
    async def configure_webhook():
        """Configure GitLab webhook and start devtunnel host after server starts."""
        global devtunnel_process

        print("\nSetting up services...")

        # Server is now listening, start devtunnel host
        devtunnel_process = start_devtunnel_host(tunnel_id)

        if not devtunnel_process:
            print("  Error: Failed to start devtunnel host")
            return

        # Wait for devtunnel to be ready by reading its output
        tunnel_ready = False
        timeout = 10  # 10 second timeout
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            # Check if process exited
            if devtunnel_process.poll() is not None:
                print("  Error: Devtunnel process exited unexpectedly")
                return

            # Read a line from stdout (non-blocking check)
            try:
                line = devtunnel_process.stdout.readline()
                if line:
                    # Silently consume output unless it's an error
                    if "error" in line.lower() or "failed" in line.lower():
                        print(f"  Warning: {line.rstrip()}")
                    # Look for indicators that tunnel is ready
                    if "Starting tunnel host" in line or "Ready to accept connections" in line:
                        tunnel_ready = True
                        break
            except Exception:
                pass

            await asyncio.sleep(0.1)

        if not tunnel_ready:
            print("  Warning: Devtunnel startup timeout - continuing anyway")
        else:
            print("  Devtunnel host ready")

        # Additional safety margin
        await asyncio.sleep(1)

        try:
            # Get repository information
            repo_url = get_repo_url()
            project_path = extract_project_path(repo_url)

            # Get webhook URL
            webhook_url = get_webhook_url_from_tunnel(tunnel_id, port)
            if not webhook_url:
                print("  Error: Could not determine webhook URL")
                return

            # Ensure webhook is configured
            if ensure_webhook_configured(project_path, webhook_url):
                print("  GitLab webhook configured")
            else:
                print("  Error: Could not configure webhook")

        except Exception as e:
            print(f"  Error configuring webhook: {e}")

    @app.post("/gl-webhook")
    async def gitlab_webhook(request: Request):
        """Handle GitLab webhook events."""
        try:
            # Get event type from header
            event_type = request.headers.get("X-Gitlab-Event", "")

            # Parse webhook payload
            payload = await request.json()

            # Extract basic info
            object_kind = payload.get("object_kind", "")
            project = payload.get("project", {})
            project_path = project.get("path_with_namespace", "")

            print(f"Received webhook: event={event_type}, object_kind={object_kind}")

            # Handle ping-like events (GitLab uses "Push Hook" for testing)
            if event_type == "Push Hook" and not payload.get("commits"):
                print("Received test push event (likely webhook test)")
                return {
                    "status": "ok",
                    "message": "Webhook is active and receiving events",
                }

            should_trigger = False
            trigger_reason = ""
            explicit_command = None
            plan_only = False
            issue_iid = None

            # Check if this is an Issue Hook event (issue opened)
            if event_type == "Issue Hook" or object_kind == "issue":
                object_attributes = payload.get("object_attributes", {})
                action = object_attributes.get("action", "")
                issue_iid = object_attributes.get("iid")

                print(f"Issue event: action={action}, iid={issue_iid}")

                if action == "open" and issue_iid:
                    should_trigger = True
                    trigger_reason = "New issue opened"

            # Check if this is a Note Hook event (comment on issue)
            elif event_type == "Note Hook" or object_kind == "note":
                object_attributes = payload.get("object_attributes", {})
                noteable_type = object_attributes.get("noteable_type", "")
                note_body = object_attributes.get("note", "").strip()

                # Get issue from the payload
                issue_data = payload.get("issue", {})
                issue_iid = issue_data.get("iid")

                print(f"Note event: noteable_type={noteable_type}, iid={issue_iid}")
                print(f"Note body: '{note_body[:100]}...' (truncated)" if len(note_body) > 100 else f"Note body: '{note_body}'")

                # Only process notes on issues that contain 'sdlc' trigger
                if noteable_type == "Issue" and issue_iid and "sdlc" in note_body.lower():
                    should_trigger = True
                    trigger_reason = "Comment with 'sdlc' trigger"

                    # Parse for explicit command and plan-only flag
                    explicit_command, _, plan_only = parse_agent_command(note_body)
                    if explicit_command:
                        print(f"Explicit command detected: {explicit_command}")
                    else:
                        print("No explicit command, will auto-classify")

                    if plan_only:
                        print("Plan-only mode detected")

            if should_trigger and issue_iid:
                # Generate ADW ID for this workflow
                adw_id = make_adw_id()

                print(f"Launching agent workflow for issue #{issue_iid} (reason: {trigger_reason})")

                # Fetch the issue details
                try:
                    if not project_path:
                        repo_url = get_repo_url()
                        project_path = extract_project_path(repo_url)

                    issue = fetch_issue(str(issue_iid), project_path)
                except Exception as e:
                    error_msg = f"Failed to fetch issue: {str(e)}"
                    print(f"Warning: {error_msg}")
                    return {
                        "status": "error",
                        "message": error_msg,
                    }

                # Set up logger for this workflow
                logger = setup_logger(adw_id, "agent_workflow")

                # Execute agent workflow in background
                def run_agent_workflow():
                    """Background task to run agent workflow"""
                    try:
                        # Import here to avoid circular imports
                        from sdlc.lib.gitlab_agent import execute_gitlab_agent_workflow

                        success, error = execute_gitlab_agent_workflow(
                            issue=issue,
                            issue_number=str(issue_iid),
                            adw_id=adw_id,
                            logger=logger,
                            explicit_command=explicit_command,
                            plan_only=plan_only,
                            project_path=project_path,
                        )
                        if not success:
                            logger.error(f"Agent workflow failed: {error}")
                    except Exception as e:
                        logger.error(f"Agent workflow exception: {str(e)}")

                # Import threading to run in background
                import threading
                thread = threading.Thread(target=run_agent_workflow)
                thread.daemon = True
                thread.start()

                mode_str = "plan-only" if plan_only else "full"
                print(f"Agent workflow started for issue #{issue_iid} with ADW ID: {adw_id} (mode: {mode_str})")
                print(f"Logs will be written to: agents/{adw_id}/agent_workflow/execution.log")

                return {
                    "status": "accepted",
                    "issue": issue_iid,
                    "adw_id": adw_id,
                    "message": f"Agent workflow triggered for issue #{issue_iid}",
                    "reason": trigger_reason,
                    "command": explicit_command if explicit_command else "auto-classify",
                    "plan_only": plan_only,
                    "logs": f"agents/{adw_id}/agent_workflow/",
                }
            else:
                print(f"Ignoring webhook: event={event_type}, object_kind={object_kind}")
                return {
                    "status": "ignored",
                    "reason": f"Not a triggering event (event={event_type}, object_kind={object_kind})",
                }

        except Exception as e:
            print(f"Error processing webhook: {e}")
            # Always return 200 to GitLab to prevent retries
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
                if "Warnings:" in line:
                    capturing_warnings = True
                    capturing_errors = False
                    continue
                elif "Errors:" in line:
                    capturing_errors = True
                    capturing_warnings = False
                    continue
                elif "Next Steps:" in line:
                    break

                if capturing_warnings and line.strip().startswith("-"):
                    warnings.append(line.strip()[2:])
                elif capturing_errors and line.strip().startswith("-"):
                    errors.append(line.strip()[2:])

            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "service": "adw-gitlab-webhook-watcher",
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
                "service": "adw-gitlab-webhook-watcher",
                "error": "Health check timed out",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "adw-gitlab-webhook-watcher",
                "error": f"Health check failed: {str(e)}",
            }

    return app
