#!/usr/bin/env -S uv run
# /// script
# dependencies = ["fastapi", "uvicorn", "python-dotenv"]
# ///

"""
GitHub Webhook Trigger - AI Developer Workflow (ADW)

FastAPI webhook endpoint that receives GitHub issue events and triggers ADW workflows.
Responds immediately to meet GitHub's 10-second timeout by launching adw_plan_build.py
in the background.

Usage: uv run watcher.py

Environment Requirements:
- PORT: Server port (default: 8001)
- All adw_plan_build.py requirements (GITHUB_PAT, ANTHROPIC_API_KEY, etc.)
"""

import os
import subprocess
import sys
import signal
import atexit
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import uvicorn
from utils import make_adw_id


def resolve_devtunnel_id() -> str:
    """Determine the devtunnel ID to use, mirroring start_webhook.sh logic."""
    env_tunnel_id = os.getenv("DEVTUNNEL_ID")
    if env_tunnel_id:
        return env_tunnel_id

    try:
        repo_url_result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )
        repo_url = repo_url_result.stdout.strip()
        if repo_url:
            repo_name = os.path.basename(repo_url.rstrip("/"))
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
            if repo_name:
                return f"{repo_name}-tunnel"
    except Exception:
        pass

    return "webhook-tunnel"

# Load environment variables
load_dotenv()

# Configuration
PORT = int(os.getenv("PORT", "8001"))
DEVTUNNEL_ID = resolve_devtunnel_id()

# Create FastAPI app
app = FastAPI(title="ADW Webhook Trigger", description="GitHub webhook endpoint for ADW")

print(f"Starting ADW Webhook Trigger on port {PORT}")
print(f"Using devtunnel ID: {DEVTUNNEL_ID}")


@app.on_event("startup")
async def configure_github_webhook():
    """Configure GitHub webhook after server is ready."""
    import asyncio

    # Give the server a moment to fully start
    await asyncio.sleep(2)

    print("\n🔗 Configuring GitHub webhook...")

    try:
        # Run webhook configuration in subprocess
        config_env = os.environ.copy()
        config_env["DEVTUNNEL_ID"] = DEVTUNNEL_ID
        config_env["SPI_AGENT_WEBHOOK_PORT"] = str(PORT)

        result = subprocess.run(
            ["bash", "-c", """
            # Get repository
            REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
            if [ -z "$REPO" ]; then
                echo "ERROR: Not in a git repository"
                exit 1
            fi

            # Get tunnel ID and construct URL
            if [ -z "$DEVTUNNEL_ID" ]; then
                echo "ERROR: DEVTUNNEL_ID not set"
                exit 1
            fi

            TUNNEL_OUTPUT=$(devtunnel show "$DEVTUNNEL_ID" 2>/dev/null)
            FULL_TUNNEL_ID=$(echo "$TUNNEL_OUTPUT" | grep "^Tunnel ID" | awk '{print $NF}')
            if [ -z "$FULL_TUNNEL_ID" ]; then
                echo "ERROR: Could not determine tunnel host for $DEVTUNNEL_ID"
                exit 1
            fi
            TUNNEL_NAME=$(echo "$FULL_TUNNEL_ID" | cut -d'.' -f1)
            TUNNEL_REGION=$(echo "$FULL_TUNNEL_ID" | cut -d'.' -f2-)
            WEBHOOK_PORT="${SPI_AGENT_WEBHOOK_PORT:-8001}"
            WEBHOOK_URL="https://${TUNNEL_NAME}-${WEBHOOK_PORT}.${TUNNEL_REGION}.devtunnels.ms/gh-webhook"

            echo "Webhook URL: $WEBHOOK_URL"

            # Check if webhook already exists
            HOOKS_JSON=$(gh api "repos/$REPO/hooks" 2>/dev/null)
            EXISTING=$(echo "$HOOKS_JSON" | grep -o "$WEBHOOK_URL" || true)

            if [ -n "$EXISTING" ]; then
                echo "Webhook already exists"
                exit 0
            fi

            # Remove old devtunnel webhooks
            HOOK_IDS=$(echo "$HOOKS_JSON" | grep -B 5 "devtunnels.ms" | grep '"id":' | grep -o '[0-9]*' || true)
            if [ -n "$HOOK_IDS" ]; then
                echo "Removing old webhooks..."
                while IFS= read -r HOOK_ID; do
                    gh api "repos/$REPO/hooks/$HOOK_ID" -X DELETE &> /dev/null
                done <<< "$HOOK_IDS"
            fi

            # Create new webhook
            echo "Creating webhook..."
            RESULT=$(gh api "repos/$REPO/hooks" -X POST \
                -f name=web \
                -f "config[url]=$WEBHOOK_URL" \
                -f "config[content_type]=json" \
                -f "events[]=issues" \
                -f "events[]=issue_comment" \
                -F active=true 2>&1)

            if [ $? -eq 0 ]; then
                WEBHOOK_ID=$(echo "$RESULT" | grep -o '"id": *[0-9]*' | head -1 | grep -o '[0-9]*' || echo "unknown")
                echo "Webhook created: ID $WEBHOOK_ID"
            else
                echo "ERROR: Failed to create webhook"
                exit 1
            fi
            """],
            capture_output=True,
            text=True,
            timeout=30,
            env=config_env,
        )

        for line in result.stdout.strip().split('\n'):
            if line.startswith("ERROR:"):
                print(f"   ❌ {line}")
            elif "Webhook URL:" in line:
                webhook_url = line.split(": ", 1)[1]
                print(f"   📡 {webhook_url}")
            elif "Webhook created:" in line or "already exists" in line:
                print(f"   ✅ {line}")
            elif line:
                print(f"   {line}")

        if result.returncode == 0:
            print("✅ GitHub webhook configured successfully!\n")
        else:
            print("⚠️  Webhook configuration had issues\n")

    except Exception as e:
        print(f"⚠️  Could not configure webhook: {e}\n")


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
        
        print(f"Received webhook: event={event_type}, action={action}, issue_number={issue_number}")

        # Handle ping events from GitHub (sent when webhook is created/tested)
        if event_type == "ping":
            zen = payload.get("zen", "GitHub Webhook Active")
            print(f"Received ping event: {zen}")
            return {
                "status": "ok",
                "message": "Webhook is active and receiving events",
                "pong": zen
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
            
            # Build command to run adw_plan_build.py with adw_id
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            trigger_script = os.path.join(script_dir, "adw_plan_build.py")
            
            cmd = ["uv", "run", trigger_script, str(issue_number), adw_id]
            
            print(f"Launching background process: {' '.join(cmd)} (reason: {trigger_reason})")
            
            # Launch in background using Popen
            # Run from project root - adw_plan_build.py will handle its own logging
            process = subprocess.Popen(
                cmd,
                cwd=project_root,  # Run from project root, not adws directory
                env=os.environ.copy()  # Pass all environment variables
            )
            
            print(f"Background process started for issue #{issue_number} with ADW ID: {adw_id}")
            print(f"Logs will be written to: agents/{adw_id}/adw_plan_build/execution.log")
            
            # Return immediately
            return {
                "status": "accepted",
                "issue": issue_number,
                "adw_id": adw_id,
                "message": f"ADW workflow triggered for issue #{issue_number}",
                "reason": trigger_reason,
                "logs": f"agents/{adw_id}/adw_plan_build/"
            }
        else:
            print(f"Ignoring webhook: event={event_type}, action={action}, issue_number={issue_number}")
            return {
                "status": "ignored",
                "reason": f"Not a triggering event (event={event_type}, action={action})"
            }
            
    except Exception as e:
        print(f"Error processing webhook: {e}")
        # Always return 200 to GitHub to prevent retries
        return {
            "status": "error",
            "message": "Internal error processing webhook"
        }


@app.get("/health")
async def health():
    """Health check endpoint - runs comprehensive system health check."""
    try:
        # Run the health check script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        health_check_script = os.path.join(script_dir, "health_check.py")
        
        # Run health check with timeout
        result = subprocess.run(
            ["uv", "run", health_check_script],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=script_dir
        )
        
        # Print the health check output for debugging
        print("=== Health Check Output ===")
        print(result.stdout)
        if result.stderr:
            print("=== Health Check Errors ===")
            print(result.stderr)
        
        # Parse the output - look for the overall status
        output_lines = result.stdout.strip().split('\n')
        is_healthy = result.returncode == 0
        
        # Extract key information from output
        warnings = []
        errors = []
        
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
            "service": "adw-webhook-trigger",
            "health_check": {
                "success": is_healthy,
                "warnings": warnings,
                "errors": errors,
                "details": "Run health_check.py directly for full report"
            }
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "unhealthy",
            "service": "adw-webhook-trigger",
            "error": "Health check timed out"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "service": "adw-webhook-trigger",
            "error": f"Health check failed: {str(e)}"
        }


if __name__ == "__main__":
    # Global variable to track the devtunnel process
    devtunnel_process = None

    def cleanup_devtunnel():
        """Clean up the devtunnel process on exit."""
        global devtunnel_process
        if devtunnel_process and devtunnel_process.poll() is None:
            print("\n🛑 Stopping devtunnel...")
            devtunnel_process.terminate()
            try:
                devtunnel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                devtunnel_process.kill()
            print("✅ Devtunnel stopped")

    # Register cleanup handler
    atexit.register(cleanup_devtunnel)
    signal.signal(signal.SIGINT, lambda sig, frame: (cleanup_devtunnel(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda sig, frame: (cleanup_devtunnel(), sys.exit(0)))

    # Start devtunnel in the background
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    expose_script = os.path.join(project_root, "scripts", "start_webhook.sh")

    if os.path.exists(expose_script):
        print("🚀 Starting devtunnel...")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        try:
            # Run start_webhook.sh in the background
            tunnel_env = os.environ.copy()
            tunnel_env.setdefault("DEVTUNNEL_ID", DEVTUNNEL_ID)
            tunnel_env.setdefault("PORT", str(PORT))
            devtunnel_process = subprocess.Popen(
                [expose_script],
                cwd=project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=tunnel_env,
            )

            # Give it a moment to start and print initial output
            import time
            import select

            print("")
            timeout = time.time() + 5  # 5 second timeout
            while time.time() < timeout:
                if devtunnel_process.poll() is not None:
                    # Process exited
                    output, _ = devtunnel_process.communicate()
                    print(output)
                    print("\n⚠️  Devtunnel failed to start. Continuing without tunnel...")
                    devtunnel_process = None
                    break

                # Check if there's output to read
                if devtunnel_process.stdout:
                    try:
                        line = devtunnel_process.stdout.readline()
                        if line:
                            print(line, end='')
                            # Stop printing once we see "Starting tunnel host"
                            if "Starting tunnel host" in line:
                                break
                    except:
                        break

                time.sleep(0.1)

            if devtunnel_process:
                print("\n✅ Devtunnel running in background")
                print("   Webhook will be configured after server starts...")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        except Exception as e:
            print(f"\n⚠️  Could not start devtunnel: {e}")
            print("Continuing without tunnel...")
            devtunnel_process = None
    else:
        print("⚠️  start_webhook.sh not found, skipping devtunnel setup")

    print(f"\nStarting webhook server on http://0.0.0.0:{PORT}")
    print(f"Webhook endpoint: POST /gh-webhook")
    print(f"Health check: GET /health")
    print("\nPress Ctrl+C to stop\n")

    try:
        uvicorn.run(app, host="0.0.0.0", port=PORT)
    finally:
        cleanup_devtunnel()
