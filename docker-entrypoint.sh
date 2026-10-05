#!/bin/sh
set -e

# Auto-generate .env from .env.example if missing
if [ ! -f /app/.env ] && [ -f /app/.env.example ]; then
    echo "[*] No .env found. Generating default from .env.example..."
    cp /app/.env.example /app/.env
fi

# Ensure required runtime directories exist
mkdir -p /app/data /app/.tmp

# Execute CMD
exec "$@"
