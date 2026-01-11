@echo off
:: =============================================================================
:: F2X NeuroHub Station Service - Portable Update & Run Script
::
:: GitHub에서 최신 릴리스를 다운로드하고 실행하는 배치 파일
:: 서비스 등록 없이 일반 프로그램으로 실행됩니다.
:: =============================================================================

setlocal EnableDelayedExpansion

:: Configuration
set "INSTALL_PATH=C:\StationService_Portable"
set "GITHUB_REPO=Soochol/F2X_NeuroHub_Station"
set "TEMP_DIR=%TEMP%\StationService_Update"

:: Colors (using PowerShell for colored output)
set "PS_CYAN=Write-Host '[*]' -ForegroundColor Cyan -NoNewline; Write-Host"
set "PS_GREEN=Write-Host '[+]' -ForegroundColor Green -NoNewline; Write-Host"
set "PS_RED=Write-Host '[-]' -ForegroundColor Red -NoNewline; Write-Host"
set "PS_YELLOW=Write-Host '[i]' -ForegroundColor Yellow -NoNewline; Write-Host"

echo =============================================
echo  F2X NeuroHub Station Service (Portable)
echo =============================================
echo.

:: Check if PowerShell is available
where powershell >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: PowerShell not found. This script requires PowerShell.
    pause
    exit /b 1
)

:: Create install directory if not exists
if not exist "%INSTALL_PATH%" (
    powershell -Command "%PS_CYAN% ' Creating install directory...'"
    mkdir "%INSTALL_PATH%"
    if %errorlevel% neq 0 (
        powershell -Command "%PS_RED% ' Failed to create directory: %INSTALL_PATH%'"
        pause
        exit /b 1
    )
    powershell -Command "%PS_GREEN% ' Directory created'"
)

:: Check current version
set "CURRENT_VERSION="
if exist "%INSTALL_PATH%\VERSION.txt" (
    set /p CURRENT_VERSION=<"%INSTALL_PATH%\VERSION.txt"
    powershell -Command "%PS_YELLOW% ' Current version: !CURRENT_VERSION!'"
) else (
    powershell -Command "%PS_YELLOW% ' Not installed'"
)

:: Get latest release info from GitHub
powershell -Command "%PS_CYAN% ' Checking latest release...'"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ErrorActionPreference = 'Stop'; " ^
    "$release = Invoke-RestMethod -Uri 'https://api.github.com/repos/%GITHUB_REPO%/releases/latest' -UseBasicParsing; " ^
    "$release.tag_name | Out-File -FilePath '%TEMP%\latest_version.txt' -Encoding ASCII -Force; " ^
    "$zipAsset = $release.assets | Where-Object { $_.name -like '*.zip' } | Select-Object -First 1; " ^
    "$zipAsset.browser_download_url | Out-File -FilePath '%TEMP%\download_url.txt' -Encoding ASCII -Force; " ^
    "$zipAsset.name | Out-File -FilePath '%TEMP%\zip_name.txt' -Encoding ASCII -Force"

if %errorlevel% neq 0 (
    powershell -Command "%PS_RED% ' Failed to fetch release info'"
    pause
    exit /b 1
)

set /p LATEST_VERSION=<"%TEMP%\latest_version.txt"
set /p DOWNLOAD_URL=<"%TEMP%\download_url.txt"
set /p ZIP_NAME=<"%TEMP%\zip_name.txt"

powershell -Command "%PS_GREEN% ' Latest version: %LATEST_VERSION%'"

:: Check if update needed
if "%CURRENT_VERSION%"=="%LATEST_VERSION%" (
    powershell -Command "%PS_GREEN% ' Already up to date!'"
    echo.
    goto :RUN_APP
)

:: Update needed
if "%CURRENT_VERSION%"=="" (
    powershell -Command "%PS_YELLOW% ' Installing version %LATEST_VERSION%...'"
) else (
    powershell -Command "%PS_YELLOW% ' Updating from %CURRENT_VERSION% to %LATEST_VERSION%...'"
)

:: Kill existing processes
powershell -Command "%PS_CYAN% ' Checking for running processes...'"
tasklist /FI "IMAGENAME eq StationService.exe" 2>NUL | find /I /N "StationService.exe">NUL
if "%ERRORLEVEL%"=="0" (
    powershell -Command "%PS_YELLOW% ' Stopping StationService.exe...'"
    taskkill /F /IM StationService.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    powershell -Command "%PS_GREEN% ' Process stopped'"
) else (
    powershell -Command "%PS_GREEN% ' No running processes'"
)

:: Create temp directory
if exist "%TEMP_DIR%" (
    rmdir /s /q "%TEMP_DIR%"
)
mkdir "%TEMP_DIR%"

:: Download ZIP
powershell -Command "%PS_CYAN% ' Downloading %ZIP_NAME%...'"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ErrorActionPreference = 'Stop'; " ^
    "Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%TEMP_DIR%\%ZIP_NAME%' -UseBasicParsing"

if %errorlevel% neq 0 (
    powershell -Command "%PS_RED% ' Download failed'"
    rmdir /s /q "%TEMP_DIR%"
    pause
    exit /b 1
)

powershell -Command "%PS_GREEN% ' Downloaded'"

:: Backup config if exists
if exist "%INSTALL_PATH%\config" (
    powershell -Command "%PS_CYAN% ' Backing up configuration...'"
    if exist "%TEMP_DIR%\config_backup" (
        rmdir /s /q "%TEMP_DIR%\config_backup"
    )
    xcopy "%INSTALL_PATH%\config" "%TEMP_DIR%\config_backup\" /E /I /Y >nul
    powershell -Command "%PS_GREEN% ' Config backed up'"
)

:: Extract ZIP
powershell -Command "%PS_CYAN% ' Extracting files...'"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ErrorActionPreference = 'Stop'; " ^
    "Expand-Archive -Path '%TEMP_DIR%\%ZIP_NAME%' -DestinationPath '%TEMP_DIR%\extract' -Force"

if %errorlevel% neq 0 (
    powershell -Command "%PS_RED% ' Extraction failed'"
    rmdir /s /q "%TEMP_DIR%"
    pause
    exit /b 1
)

powershell -Command "%PS_GREEN% ' Extracted'"

:: Find content folder (may be nested)
set "SOURCE_FOLDER="
for /d %%D in ("%TEMP_DIR%\extract\*") do (
    set "SOURCE_FOLDER=%%D"
    goto :FOUND_SOURCE
)
set "SOURCE_FOLDER=%TEMP_DIR%\extract"

:FOUND_SOURCE

:: Delete old files (preserve config, logs, data)
powershell -Command "%PS_CYAN% ' Updating files...'"

for /d %%D in ("%INSTALL_PATH%\*") do (
    set "DIR_NAME=%%~nxD"
    if not "!DIR_NAME!"=="config" (
        if not "!DIR_NAME!"=="logs" (
            if not "!DIR_NAME!"=="data" (
                rmdir /s /q "%%D" 2>nul
            )
        )
    )
)

for %%F in ("%INSTALL_PATH%\*") do (
    set "FILE_NAME=%%~nxF"
    if not "!FILE_NAME!"=="VERSION.txt" (
        del /f /q "%%F" 2>nul
    )
)

:: Copy new files (except config)
xcopy "%SOURCE_FOLDER%\*" "%INSTALL_PATH%\" /E /I /Y /EXCLUDE:%TEMP_DIR%\exclude.txt >nul 2>nul
if not exist "%TEMP_DIR%\exclude.txt" (
    xcopy "%SOURCE_FOLDER%\*" "%INSTALL_PATH%\" /E /I /Y >nul
)

:: Restore config
if exist "%TEMP_DIR%\config_backup" (
    powershell -Command "%PS_CYAN% ' Restoring configuration...'"
    if not exist "%INSTALL_PATH%\config" (
        mkdir "%INSTALL_PATH%\config"
    )
    xcopy "%TEMP_DIR%\config_backup\*" "%INSTALL_PATH%\config\" /E /I /Y >nul
    powershell -Command "%PS_GREEN% ' Config restored'"
)

:: Save version
echo %LATEST_VERSION%>"%INSTALL_PATH%\VERSION.txt"

:: Create logs directory if not exists
if not exist "%INSTALL_PATH%\logs" (
    mkdir "%INSTALL_PATH%\logs"
)

:: Create data directory if not exists
if not exist "%INSTALL_PATH%\data" (
    mkdir "%INSTALL_PATH%\data"
)

:: Cleanup
rmdir /s /q "%TEMP_DIR%" >nul 2>nul

powershell -Command "%PS_GREEN% ' Update complete!'"
echo.

:RUN_APP
:: Check if EXE exists
if not exist "%INSTALL_PATH%\StationService.exe" (
    powershell -Command "%PS_RED% ' StationService.exe not found at: %INSTALL_PATH%'"
    pause
    exit /b 1
)

:: Show summary
echo =============================================
echo  Version: %LATEST_VERSION%
echo  Location: %INSTALL_PATH%
echo =============================================
echo.
powershell -Command "%PS_CYAN% ' Starting StationService...'"
echo.
echo UI will be available at: http://localhost:8080/ui
echo.
echo Press Ctrl+C or close this window to stop the service.
echo =============================================
echo.

:: Run the application
cd /d "%INSTALL_PATH%"
"%INSTALL_PATH%\StationService.exe"

:: If EXE exits, show message
echo.
powershell -Command "%PS_YELLOW% ' StationService stopped'"
pause
