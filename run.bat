@echo off
chcp 65001 >nul
echo ========================================
echo   F2X Station Service - Update and Run
echo   Port: 8080
echo ========================================

cd /d "%~dp0"

echo.
echo [1/3] Updating from GitHub...
if exist ".git" (
    git rev-parse --is-inside-work-tree >nul 2>&1
    if %errorlevel% equ 0 (
        git pull origin main
        if errorlevel 1 (
            echo WARNING: git pull failed. Continuing with local version.
            echo If you want to force an update, please check your internet connection.
        )
    ) else (
        echo WARNING: .git folder found but it is not a valid git repository.
        echo Skipping update and continuing with local version.
    )
) else (
    echo NOTE: Not a git repository. Skipping update.
)

echo.
echo [2/3] Installing dependencies...
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
echo [3/3] Starting Station Service...
echo Press Ctrl+C to stop
set STATION_CONFIG=./config/station.yaml
python -m station_service.main
pause
