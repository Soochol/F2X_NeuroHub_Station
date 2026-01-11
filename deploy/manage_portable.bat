@echo off
:: =============================================================================
:: F2X NeuroHub Station Service - Portable Management Script
::
:: Portable 모드 관리를 위한 유틸리티 스크립트
:: =============================================================================

setlocal

set "INSTALL_PATH=C:\StationService_Portable"

:MENU
cls
echo =============================================
echo  F2X Station Service - Portable Manager
echo =============================================
echo.

:: Check installation status
if exist "%INSTALL_PATH%\StationService.exe" (
    echo Status: INSTALLED
    if exist "%INSTALL_PATH%\VERSION.txt" (
        set /p VERSION=<"%INSTALL_PATH%\VERSION.txt"
        echo Version: !VERSION!
    )

    :: Check if running
    tasklist /FI "IMAGENAME eq StationService.exe" 2>NUL | find /I /N "StationService.exe">NUL
    if "%ERRORLEVEL%"=="0" (
        echo Running: YES
    ) else (
        echo Running: NO
    )
) else (
    echo Status: NOT INSTALLED
)

echo.
echo =============================================
echo  Menu
echo =============================================
echo.
echo  1. Install / Update
echo  2. Run
echo  3. Stop
echo  4. View Logs
echo  5. Open Install Folder
echo  6. Open Config File
echo  7. Check Version
echo  8. Uninstall
echo  9. Exit
echo.
set /p CHOICE=Select option (1-9):

if "%CHOICE%"=="1" goto :INSTALL
if "%CHOICE%"=="2" goto :RUN
if "%CHOICE%"=="3" goto :STOP
if "%CHOICE%"=="4" goto :LOGS
if "%CHOICE%"=="5" goto :FOLDER
if "%CHOICE%"=="6" goto :CONFIG
if "%CHOICE%"=="7" goto :VERSION
if "%CHOICE%"=="8" goto :UNINSTALL
if "%CHOICE%"=="9" goto :EXIT

echo Invalid choice!
timeout /t 2 >nul
goto :MENU

:INSTALL
cls
echo =============================================
echo  Install / Update
echo =============================================
echo.
call "%~dp0update_portable.bat"
pause
goto :MENU

:RUN
cls
echo =============================================
echo  Run StationService
echo =============================================
echo.
if not exist "%INSTALL_PATH%\StationService.exe" (
    echo ERROR: Not installed. Install first (option 1).
    pause
    goto :MENU
)

echo Starting StationService...
echo.
echo UI: http://localhost:8080/ui
echo.
echo Press Ctrl+C to stop
echo.
cd /d "%INSTALL_PATH%"
"%INSTALL_PATH%\StationService.exe"
pause
goto :MENU

:STOP
cls
echo =============================================
echo  Stop StationService
echo =============================================
echo.
tasklist /FI "IMAGENAME eq StationService.exe" 2>NUL | find /I /N "StationService.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Stopping all StationService processes...
    taskkill /F /IM StationService.exe
    echo Done!
) else (
    echo StationService is not running.
)
pause
goto :MENU

:LOGS
cls
echo =============================================
echo  View Logs
echo =============================================
echo.
if not exist "%INSTALL_PATH%\logs\service.log" (
    echo No logs found.
    pause
    goto :MENU
)

echo Last 50 lines:
echo.
powershell -Command "Get-Content '%INSTALL_PATH%\logs\service.log' -Tail 50"
echo.
pause
goto :MENU

:FOLDER
cls
echo =============================================
echo  Open Install Folder
echo =============================================
echo.
if exist "%INSTALL_PATH%" (
    echo Opening: %INSTALL_PATH%
    explorer "%INSTALL_PATH%"
) else (
    echo Folder not found: %INSTALL_PATH%
)
timeout /t 2 >nul
goto :MENU

:CONFIG
cls
echo =============================================
echo  Open Config File
echo =============================================
echo.
set "CONFIG_FILE=%INSTALL_PATH%\config\station.yaml"
if exist "%CONFIG_FILE%" (
    echo Opening: %CONFIG_FILE%
    notepad "%CONFIG_FILE%"
) else (
    echo Config file not found: %CONFIG_FILE%
    echo.
    echo Do you want to create a default config? (Y/N)
    set /p CREATE_CONFIG=
    if /i "%CREATE_CONFIG%"=="Y" (
        if not exist "%INSTALL_PATH%\config" mkdir "%INSTALL_PATH%\config"
        echo Creating default config...

        :: Copy from example if available
        if exist "%INSTALL_PATH%\config\station.yaml.example" (
            copy "%INSTALL_PATH%\config\station.yaml.example" "%CONFIG_FILE%"
            echo Config created from example.
        ) else (
            echo # Station Configuration > "%CONFIG_FILE%"
            echo station: >> "%CONFIG_FILE%"
            echo   id: test_001 >> "%CONFIG_FILE%"
            echo   name: Test Station >> "%CONFIG_FILE%"
            echo   location: Factory >> "%CONFIG_FILE%"
            echo. >> "%CONFIG_FILE%"
            echo api: >> "%CONFIG_FILE%"
            echo   host: 0.0.0.0 >> "%CONFIG_FILE%"
            echo   port: 8080 >> "%CONFIG_FILE%"
            echo. >> "%CONFIG_FILE%"
            echo Default config created.
        )
        notepad "%CONFIG_FILE%"
    )
)
goto :MENU

:VERSION
cls
echo =============================================
echo  Version Information
echo =============================================
echo.

if exist "%INSTALL_PATH%\VERSION.txt" (
    set /p CURRENT_VERSION=<"%INSTALL_PATH%\VERSION.txt"
    echo Current Version: !CURRENT_VERSION!
) else (
    echo Current Version: NOT INSTALLED
)

echo.
echo Checking latest version from GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$release = Invoke-RestMethod -Uri 'https://api.github.com/repos/Soochol/F2X_NeuroHub_Station/releases/latest' -UseBasicParsing; " ^
    "Write-Host 'Latest Version: ' $release.tag_name -ForegroundColor Green; " ^
    "Write-Host 'Published: ' $release.published_at; " ^
    "Write-Host 'URL: ' $release.html_url"

echo.
pause
goto :MENU

:UNINSTALL
cls
echo =============================================
echo  Uninstall StationService
echo =============================================
echo.
echo WARNING: This will delete all files including:
echo   - Application files
echo   - Configuration
echo   - Logs
echo   - Database
echo.
echo Location: %INSTALL_PATH%
echo.
set /p CONFIRM=Are you sure? (YES to confirm):

if not "%CONFIRM%"=="YES" (
    echo Cancelled.
    pause
    goto :MENU
)

echo.
echo Stopping processes...
taskkill /F /IM StationService.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo Deleting files...
if exist "%INSTALL_PATH%" (
    rmdir /s /q "%INSTALL_PATH%"
    echo Uninstall complete!
) else (
    echo Nothing to uninstall.
)

pause
goto :MENU

:EXIT
echo.
echo Goodbye!
timeout /t 1 >nul
exit /b 0
