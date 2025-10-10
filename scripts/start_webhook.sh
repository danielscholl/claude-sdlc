#!/bin/bash

# Expose adws/watcher.py to the public internet using Microsoft devtunnels
# This script auto-creates the tunnel if it doesn't exist (self-healing)
# Requires: devtunnel CLI installed and authenticated

set -e  # Exit on error

# Determine tunnel ID from repository name unless already provided
if [ -z "$DEVTUNNEL_ID" ]; then
    if git rev-parse --git-dir &> /dev/null; then
        # Extract repo name from git remote URL
        REPO_URL=$(git remote get-url origin 2>/dev/null || echo "")
        if [ -n "$REPO_URL" ]; then
            # Extract repo name (e.g., spi-agent from https://github.com/owner/spi-agent.git)
            REPO_NAME=$(basename "$REPO_URL" .git)
            DEVTUNNEL_ID="${REPO_NAME}-tunnel"
        else
            DEVTUNNEL_ID="webhook-tunnel"
        fi
    else
        DEVTUNNEL_ID="webhook-tunnel"
    fi
fi

# Allow override from .env file when not provided via environment
if [ -z "$DEVTUNNEL_ID" ] && [ -f .env ]; then
    ENV_TUNNEL_ID=$(grep "^DEVTUNNEL_ID=" .env 2>/dev/null | tail -n 1 | cut -d '=' -f2-)
    if [ -n "$ENV_TUNNEL_ID" ]; then
        DEVTUNNEL_ID="$ENV_TUNNEL_ID"
    fi
fi

# Resolve port, preferring environment, then .env, defaulting to 8001
if [ -z "$PORT" ]; then
    if [ -f .env ]; then
        ENV_PORT=$(grep "^PORT=" .env 2>/dev/null | tail -n 1 | cut -d '=' -f2-)
        if [ -n "$ENV_PORT" ]; then
            PORT="$ENV_PORT"
        fi
    fi
fi

if [ -z "$PORT" ]; then
    PORT=8001
fi

echo "🚀 Starting devtunnel for webhook exposure..."
echo ""
echo "  • Tunnel ID: $DEVTUNNEL_ID"
echo "  • Local port: $PORT"
echo ""

# Check if devtunnel CLI is installed
if ! command -v devtunnel &> /dev/null; then
    echo "❌ devtunnel CLI is not installed"
    echo ""
    echo "Please install devtunnel:"
    echo "  brew install --cask devtunnel"
    echo ""
    echo "Then authenticate:"
    echo "  devtunnel user login -g"
    echo ""
    echo "For more information, see: docs/DEVTUNNEL_SETUP.md"
    exit 1
fi

# Check authentication status
if ! devtunnel user show &> /dev/null; then
    echo "❌ Not authenticated with devtunnel"
    echo ""
    echo "Please authenticate using GitHub:"
    echo "  devtunnel user login -g"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check if tunnel exists
if ! devtunnel show "$DEVTUNNEL_ID" &> /dev/null; then
    echo "🔧 Tunnel '$DEVTUNNEL_ID' not found - creating it now..."
    echo ""

    # Create persistent tunnel with 30-day expiration
    echo "Creating persistent tunnel with anonymous access..."
    devtunnel create "$DEVTUNNEL_ID" --allow-anonymous --expiration 30d

    echo "✅ Tunnel created"
    echo ""

    # Add port 8001 with HTTP protocol
    echo "Configuring port $PORT for HTTP traffic..."
    devtunnel port create "$DEVTUNNEL_ID" -p "$PORT" --protocol http

    echo "✅ Port configured"
    echo ""

    echo "🎉 Tunnel setup complete!"
    echo ""
else
    echo "✅ Using existing tunnel: $DEVTUNNEL_ID"
    echo ""

    # Verify port is configured (in case tunnel exists but port was removed)
    if ! devtunnel port list "$DEVTUNNEL_ID" 2>/dev/null | grep -q "^$PORT "; then
        echo "Adding port $PORT to existing tunnel..."
        devtunnel port create "$DEVTUNNEL_ID" -p "$PORT" --protocol http
        echo "✅ Port configured"
        echo ""
    else
        echo "✅ Port $PORT already configured"
        echo ""
    fi
fi

# Display tunnel info
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Tunnel Information"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Tunnel ID: $DEVTUNNEL_ID"
echo "Port: $PORT"
echo ""

# Note: Webhook creation happens in watcher.py AFTER tunnel is hosting
# This ensures GitHub's ping event succeeds when the webhook is created
echo "📝 Note: GitHub webhook will be configured after tunnel starts hosting"
echo ""

echo "Starting tunnel host (press Ctrl+C to stop)..."
echo ""

# Host the tunnel
# For existing tunnels with ports already configured, we don't need -p
# Anonymous access is already configured at the tunnel level
devtunnel host "$DEVTUNNEL_ID"
