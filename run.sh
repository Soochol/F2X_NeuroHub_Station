#!/bin/bash
set -e

echo "========================================"
echo "  F2X Station Service - Hot Reload Mode"
echo "  Port: 8080"
echo "========================================"

cd "$(dirname "$0")"

echo ""
echo "[1/2] Setting up environment..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
fi

.venv/bin/pip3 install -e . --quiet
if [ $? -ne 0 ]; then
    echo "ERROR: pip install failed"
    exit 1
fi

echo ""
echo "[2/2] Starting Station Service with Hot Reload..."
echo "File changes will auto-reload the server."
echo "Press Ctrl+C to stop"
export STATION_CONFIG=./config/station.yaml
.venv/bin/uvicorn station_service.main:app --host 0.0.0.0 --port 8080 --reload --reload-dir station_service
