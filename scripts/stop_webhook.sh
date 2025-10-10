#!/bin/bash

# Stop the webhook server and devtunnel host gracefully
# This script cleanly shuts down the watcher.py process and associated devtunnel
#
# Usage:
#   ./stop_webhook.sh                  # Stop services only
#   ./stop_webhook.sh --remove-webhook # Stop services, remove GitHub webhook, and delete devtunnel
#   ./stop_webhook.sh -r               # Short form of --remove-webhook

set -e  # Exit on error

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛑 Stopping webhook server and tunnel..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Track if anything was stopped
STOPPED_SOMETHING=false

# Find and kill the webhook server process (watcher.py)
if pgrep -f "watcher.py" > /dev/null 2>&1; then
    echo "Found webhook server process, stopping..."
    pkill -TERM -f "watcher.py" 2>/dev/null || true
    sleep 1  # Give it a moment to terminate gracefully

    # Force kill if still running
    if pgrep -f "watcher.py" > /dev/null 2>&1; then
        pkill -KILL -f "watcher.py" 2>/dev/null || true
    fi
    echo "✅ Webhook server stopped"
    STOPPED_SOMETHING=true
else
    echo "ℹ️  No webhook server process found"
fi

# Find and kill devtunnel host processes
if pgrep -f "devtunnel host" > /dev/null 2>&1; then
    echo "Found devtunnel process, stopping..."
    pkill -TERM -f "devtunnel host" 2>/dev/null || true
    sleep 1  # Give it a moment to terminate gracefully

    # Force kill if still running
    if pgrep -f "devtunnel host" > /dev/null 2>&1; then
        pkill -KILL -f "devtunnel host" 2>/dev/null || true
    fi
    echo "✅ Devtunnel stopped"
    STOPPED_SOMETHING=true
else
    echo "ℹ️  No devtunnel process found"
fi

# Check for any remaining uvicorn processes on port 8001
PORT=${PORT:-8001}
if lsof -i ":$PORT" > /dev/null 2>&1; then
    echo "Found process on port $PORT, cleaning up..."

    # Try graceful termination first
    lsof -ti ":$PORT" | xargs kill -TERM 2>/dev/null || true
    sleep 1

    # Force kill if still running
    if lsof -i ":$PORT" > /dev/null 2>&1; then
        lsof -ti ":$PORT" | xargs kill -KILL 2>/dev/null || true
    fi

    echo "✅ Port $PORT cleared"
    STOPPED_SOMETHING=true
fi

# Final status
echo ""
if [ "$STOPPED_SOMETHING" = true ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ All services stopped successfully"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "ℹ️  No services were running"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

# Optional: Remove GitHub webhook if requested
if [ "$1" = "--remove-webhook" ] || [ "$1" = "-r" ]; then
    echo ""
    echo "🔗 Removing GitHub webhook..."

    # Get repository info
    REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
    if [ -z "$REPO" ]; then
        echo "⚠️  Not in a git repository or gh not configured"
    else
        # Find and remove devtunnel webhooks
        TUNNEL_ID="${DEVTUNNEL_ID:-spi-agent-tunnel}"
        HOOKS_JSON=$(gh api "repos/$REPO/hooks" 2>/dev/null)

        # Look for webhooks with devtunnels.ms URLs
        HOOK_IDS=$(echo "$HOOKS_JSON" | jq -r ".[] | select(.config.url | contains(\"devtunnels.ms\")) | .id" 2>/dev/null)

        if [ -n "$HOOK_IDS" ]; then
            while IFS= read -r HOOK_ID; do
                WEBHOOK_URL=$(echo "$HOOKS_JSON" | jq -r ".[] | select(.id == $HOOK_ID) | .config.url")
                echo "   Removing webhook: $WEBHOOK_URL"
                gh api "repos/$REPO/hooks/$HOOK_ID" -X DELETE &> /dev/null
                echo "   ✅ Webhook ID $HOOK_ID removed"
            done <<< "$HOOK_IDS"
            STOPPED_SOMETHING=true
        else
            echo "   ℹ️  No devtunnel webhooks found"
        fi
    fi

    # Also delete the devtunnel itself
    if command -v devtunnel &> /dev/null; then
        echo ""
        echo "🗑️  Removing devtunnel..."
        TUNNEL_ID="${DEVTUNNEL_ID:-spi-agent-tunnel}"

        if devtunnel show "$TUNNEL_ID" &> /dev/null; then
            devtunnel delete "$TUNNEL_ID" -f &> /dev/null
            echo "   ✅ Devtunnel '$TUNNEL_ID' deleted"
        else
            echo "   ℹ️  Devtunnel '$TUNNEL_ID' not found"
        fi
    fi
else
    # Only show tunnel status if we're not removing everything
    if command -v devtunnel &> /dev/null; then
        echo ""
        echo "📊 Tunnel status:"
        TUNNEL_ID="${DEVTUNNEL_ID:-spi-agent-tunnel}"
        if devtunnel show "$TUNNEL_ID" &> /dev/null; then
            devtunnel show "$TUNNEL_ID" | grep -E "^(Host connections|Client connections)" | sed 's/^/   /'
        else
            echo "   Tunnel '$TUNNEL_ID' does not exist"
        fi
    fi

    # Show usage hint if webhook wasn't removed
    echo ""
    echo "💡 Tip: Use '$0 --remove-webhook' to also remove GitHub webhooks and devtunnel"
fi