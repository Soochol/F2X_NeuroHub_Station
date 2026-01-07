#!/bin/bash
set -e

echo "========================================"
echo "  F2X Station Service - Update and Run"
echo "  Port: 8080"
echo "========================================"

cd "$(dirname "$0")"

echo ""
echo "[1/3] Updating from GitHub..."
if [ -d ".git" ]; then
    if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
        git pull origin main || echo "WARNING: git pull failed. Continuing with local version."
    else
        echo "WARNING: .git folder found but not a valid git repository. Skipping update."
    fi
else
    echo "NOTE: Not a git repository. Skipping update."
fi

echo ""
echo "[2/3] Installing dependencies..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install -e . --quiet

echo ""
echo "[3/3] Starting Station Service..."
echo "Press Ctrl+C to stop"
export STATION_CONFIG=./config/station.yaml
python -m station_service.main
