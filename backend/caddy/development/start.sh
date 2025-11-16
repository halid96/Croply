#!/bin/bash

# Load environment variables from local.env
# This script loads the Caddy environment variables and starts Caddy

# Get the project root directory (3 levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Load local.env file
if [ -f "$PROJECT_ROOT/local.env" ]; then
    echo "Loading environment variables from local.env..."
    set -a  # automatically export all variables
    source "$PROJECT_ROOT/local.env"
    set +a  # stop automatically exporting
else
    echo "Error: local.env file not found at $PROJECT_ROOT/local.env"
    exit 1
fi

# Check if required Caddy environment variables are set
if [ -z "$CADDY_ADMIN_ADDRESS" ] || [ -z "$CADDY_DOMAIN" ] || [ -z "$CADDY_PROJECT_ROOT" ] || \
   [ -z "$CADDY_BACKEND_ROOT" ] || [ -z "$CADDY_PHP_FASTCGI_ADDRESS" ] || [ -z "$CADDY_REVERSE_PROXY_URL" ]; then
    echo "Error: Required Caddy environment variables are not set in local.env"
    echo "Required variables:"
    echo "  - CADDY_ADMIN_ADDRESS"
    echo "  - CADDY_DOMAIN"
    echo "  - CADDY_PROJECT_ROOT"
    echo "  - CADDY_BACKEND_ROOT"
    echo "  - CADDY_PHP_FASTCGI_ADDRESS"
    echo "  - CADDY_REVERSE_PROXY_URL"
    exit 1
fi

# Get the Caddyfile path
CADDYFILE="$SCRIPT_DIR/Caddyfile"

# Start Caddy
echo "Starting Caddy with config: $CADDYFILE"
caddy run --config "$CADDYFILE"

