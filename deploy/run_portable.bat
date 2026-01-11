@echo off
:: =============================================================================
:: F2X NeuroHub Station Service - Quick Run Script
::
:: 설치 없이 바로 실행하는 배치 파일
:: 최초 실행 시 자동으로 다운로드 및 설치됩니다.
:: =============================================================================

setlocal

set "INSTALL_PATH=C:\StationService_Portable"
set "UPDATE_SCRIPT=%~dp0update_portable.bat"

:: Check if installed
if not exist "%INSTALL_PATH%\StationService.exe" (
    echo =============================================
    echo  F2X NeuroHub Station Service
    echo =============================================
    echo.
    echo StationService is not installed yet.
    echo.
    echo Installing now...
    echo.
    call "%UPDATE_SCRIPT%"
    exit /b %errorlevel%
)

:: Check for updates in background (optional - silent)
:: Uncomment to enable automatic update checks
:: start /min "" "%UPDATE_SCRIPT%"

:: Check for running processes and stop them
tasklist /FI "IMAGENAME eq StationService.exe" 2>NUL | find /I /N "StationService.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Stopping existing StationService processes...
    powershell -Command "Get-Process -Name StationService -ErrorAction SilentlyContinue | Stop-Process -Force"
    timeout /t 2 /nobreak >nul
    echo Stopped.
    echo.
)

:: Run directly
echo =============================================
echo  F2X NeuroHub Station Service
echo =============================================
echo.
echo Starting StationService...
echo.
echo UI: http://localhost:8080/ui
echo.
echo Press Ctrl+C to stop
echo =============================================
echo.

cd /d "%INSTALL_PATH%"
"%INSTALL_PATH%\StationService.exe"
