@echo off
chcp 65001 >nul
echo ========================================
echo   F2X Station Service - Hot Reload Mode
echo   Port: 8080
echo ========================================

cd /d "%~dp0"

echo.
echo [1/2] Setting up environment...
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat
pip install -e . --quiet
if errorlevel 1 (
    echo ERROR: pip install failed
    pause
    exit /b 1
)

echo.
echo [2/2] Starting Station Service with Hot Reload...
echo File changes will auto-reload the server.
echo Press Ctrl+C to stop
set STATION_CONFIG=./config/station.yaml
uvicorn station_service.main:app --host 0.0.0.0 --port 8080 --reload --reload-dir station_service
pause
