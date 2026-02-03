@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================
:: F2X NeuroHub Station Service - Build Script
:: ============================================
:: Builds Windows EXE deployment package
:: Usage: build.bat [version]
:: ============================================

echo.
echo ========================================
echo   F2X Station Service - EXE Builder
echo ========================================
echo.

:: Set project root
cd /d "%~dp0"
set "PROJECT_ROOT=%CD%"

:: Parse version from pyproject.toml or use argument
set "VERSION="
if not "%~1"=="" (
    set "VERSION=%~1"
    echo Using provided version: %VERSION%
) else (
    echo Reading version from pyproject.toml...
    for /f "tokens=2 delims== " %%i in ('findstr /r "^version" pyproject.toml') do (
        set "VERSION=%%i"
        set "VERSION=!VERSION:"=!"
    )
    if defined VERSION (
        echo Found version: !VERSION!
    ) else (
        echo ERROR: Could not extract version from pyproject.toml
        set "VERSION=1.0.0"
        echo Using default version: !VERSION!
    )
)

set "BUILD_NAME=StationService_v%VERSION%_Windows_x64"
set "DIST_DIR=%PROJECT_ROOT%\dist"
set "BUILD_DIR=%PROJECT_ROOT%\build"
set "OUTPUT_DIR=%DIST_DIR%\%BUILD_NAME%"

echo.
echo Configuration:
echo   Version: %VERSION%
echo   Output: %OUTPUT_DIR%
echo   Platform: Windows x64
echo.

:: ============================================
:: Step 1: Clean previous builds
:: ============================================
echo [1/7] Cleaning previous builds...

:: Kill running StationService processes (ignore errors if not running or access denied)
taskkill /F /IM StationService.exe >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo   Stopped running StationService processes.
    timeout /t 2 /nobreak >nul
) else (
    echo   No StationService process running ^(or already stopped^).
)

if exist "%BUILD_DIR%" (
    echo   Removing build\
    rmdir /s /q "%BUILD_DIR%" 2>nul
)
if exist "%DIST_DIR%" (
    echo   Removing dist\
    rmdir /s /q "%DIST_DIR%" 2>nul
)
echo   Done.

:: ============================================
:: Step 2: Setup Python environment
:: ============================================
echo.
echo [2/7] Setting up Python environment...

:: Check if venv exists
if not exist ".venv\Scripts\activate.bat" (
    echo   Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Please ensure Python 3.10+ is installed
        pause
        exit /b 1
    )
)

:: Activate venv
echo   Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

:: Install dependencies
echo   Installing Python dependencies...
pip install --upgrade pip setuptools wheel --quiet
pip install -e . --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

:: Install PyInstaller
echo   Installing PyInstaller...
pip install pyinstaller --quiet
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

echo   Done.

:: ============================================
:: Step 3: Build React UI
:: ============================================
echo.
echo [3/7] Building React UI...
cd "%PROJECT_ROOT%\station_ui"

:: Check Node.js
where node >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found in PATH
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

:: Install dependencies
echo   Installing Node dependencies...
call npm install --silent
if errorlevel 1 (
    echo ERROR: npm install failed
    pause
    exit /b 1
)

:: Build UI (outputs to station_service/static/)
echo   Building production bundle...
call npm run build
if errorlevel 1 (
    echo ERROR: UI build failed
    pause
    exit /b 1
)

:: Verify build output
if not exist "%PROJECT_ROOT%\station_service\static\index.html" (
    echo ERROR: UI build did not produce expected output
    echo Expected: station_service\static\index.html
    pause
    exit /b 1
)

echo   Done. UI built to station_service\static\

cd "%PROJECT_ROOT%"

:: ============================================
:: Step 4: Build EXE with PyInstaller
:: ============================================
echo.
echo [4/7] Building EXE with PyInstaller...
echo   This may take several minutes...

pyinstaller station_service.spec --clean --noconfirm
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    echo Check the build logs above for details
    pause
    exit /b 1
)

:: Verify EXE was created
if not exist "%DIST_DIR%\StationService\StationService.exe" (
    echo ERROR: EXE was not created
    pause
    exit /b 1
)

echo   Done. EXE built to dist\StationService\

:: ============================================
:: Step 5: Package deployment folder
:: ============================================
echo.
echo [5/7] Creating deployment package...

:: Create output directory
echo   Creating deployment structure...
mkdir "%OUTPUT_DIR%" 2>nul
mkdir "%OUTPUT_DIR%\sequences" 2>nul
mkdir "%OUTPUT_DIR%\data" 2>nul
mkdir "%OUTPUT_DIR%\logs" 2>nul

:: Copy EXE and _internal
echo   Copying EXE and dependencies...
xcopy /E /I /Y "%DIST_DIR%\StationService" "%OUTPUT_DIR%" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy EXE files
    pause
    exit /b 1
)

:: Copy sequences (external)
echo   Copying test sequences...
xcopy /E /I /Y "%PROJECT_ROOT%\sequences" "%OUTPUT_DIR%\sequences" >nul

:: Copy config template
echo   Copying configuration template...
copy /Y "%PROJECT_ROOT%\config\station.yaml.example" "%OUTPUT_DIR%\config\station.yaml" >nul
if not exist "%OUTPUT_DIR%\config\station.yaml" (
    echo WARNING: Config template not found, using current config
    mkdir "%OUTPUT_DIR%\config" 2>nul
    copy /Y "%PROJECT_ROOT%\config\station.yaml" "%OUTPUT_DIR%\config\station.yaml" >nul
)

:: Create .gitkeep files
type nul > "%OUTPUT_DIR%\data\.gitkeep"
type nul > "%OUTPUT_DIR%\logs\.gitkeep"

:: Create VERSION.txt
echo %VERSION% > "%OUTPUT_DIR%\VERSION.txt"

:: Create README
(
echo F2X NeuroHub Station Service - Version %VERSION%
echo ================================================
echo.
echo Quick Start:
echo   1. Edit config\station.yaml with your station settings
echo   2. Run StationService.exe
echo   3. Access UI at http://localhost:8080/ui
echo.
echo Directory Structure:
echo   StationService.exe     - Main executable
echo   _internal\             - Bundled dependencies ^(do not modify^)
echo   python\                - Embedded Python for sequence execution
echo   config\                - Configuration files
echo   sequences\             - Test sequences ^(external, updatable^)
echo   data\                  - Runtime data ^(SQLite DB^)
echo   logs\                  - Application logs
echo.
echo Configuration:
echo   Edit config\station.yaml to configure:
echo   - Station ID and name
echo   - Backend API URL
echo   - Server port ^(default: 8080^)
echo   - Sequences directory path
echo.
echo Support: https://github.com/Soochol/F2X_NeuroHub_Station
) > "%OUTPUT_DIR%\README.txt"

echo   Done.

:: ============================================
:: Step 6: Setup Embedded Python
:: ============================================
echo.
echo [6/7] Setting up Embedded Python for sequence execution...

set "PYTHON_VERSION=3.11.9"
set "PYTHON_ZIP=python-%PYTHON_VERSION%-embed-amd64.zip"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_ZIP%"
set "EMBEDDED_PYTHON_DIR=%OUTPUT_DIR%\python"

:: Download Python embeddable package
echo   Downloading Python %PYTHON_VERSION% embeddable package...
if not exist "%PROJECT_ROOT%\%PYTHON_ZIP%" (
    powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PROJECT_ROOT%\%PYTHON_ZIP%'"
    if errorlevel 1 (
        echo ERROR: Failed to download Python embeddable package
        echo URL: %PYTHON_URL%
        pause
        exit /b 1
    )
) else (
    echo   Using cached %PYTHON_ZIP%
)

:: Extract to python/ folder
echo   Extracting Python to %EMBEDDED_PYTHON_DIR%...
mkdir "%EMBEDDED_PYTHON_DIR%" 2>nul
powershell -Command "Expand-Archive -Path '%PROJECT_ROOT%\%PYTHON_ZIP%' -DestinationPath '%EMBEDDED_PYTHON_DIR%' -Force"
if errorlevel 1 (
    echo ERROR: Failed to extract Python embeddable package
    pause
    exit /b 1
)

:: Enable pip and add app root to Python path
echo   Configuring Python paths...
set "PTH_FILE=%EMBEDDED_PYTHON_DIR%\python311._pth"
if exist "%PTH_FILE%" (
    :: Rewrite the _pth file to include app root (parent of python folder)
    :: This allows: python -m sequences.xxx.main to find the sequences folder
    (
        echo python311.zip
        echo .
        echo ..
        echo Lib\site-packages
        echo import site
    ) > "%PTH_FILE%"
    echo   Updated python311._pth with app root path
)

:: Download and run get-pip.py
echo   Installing pip...
set "GET_PIP_URL=https://bootstrap.pypa.io/get-pip.py"
set "GET_PIP_FILE=%EMBEDDED_PYTHON_DIR%\get-pip.py"
powershell -Command "Invoke-WebRequest -Uri '%GET_PIP_URL%' -OutFile '%GET_PIP_FILE%'"
if errorlevel 1 (
    echo ERROR: Failed to download get-pip.py
    pause
    exit /b 1
)

"%EMBEDDED_PYTHON_DIR%\python.exe" "%GET_PIP_FILE%" --no-warn-script-location
if errorlevel 1 (
    echo ERROR: Failed to install pip
    pause
    exit /b 1
)

:: Install SDK as base dependency for all sequences
echo   Installing station-service-sdk...
"%EMBEDDED_PYTHON_DIR%\python.exe" -m pip install station-service-sdk --no-warn-script-location --quiet
if errorlevel 1 (
    echo WARNING: Failed to install station-service-sdk
    echo Sequences may need to install it on first run
)

:: Clean up get-pip.py
del "%GET_PIP_FILE%" 2>nul

echo   Done. Embedded Python ready at python\

:: ============================================
:: Step 7: Generate checksums and compress
:: ============================================
echo.
echo [7/7] Finalizing deployment package...

:: Generate SHA256 checksum
echo   Generating SHA256 checksums...
cd "%OUTPUT_DIR%"
certutil -hashfile StationService.exe SHA256 > "StationService.exe.sha256"
if errorlevel 1 (
    echo WARNING: Could not generate checksum
)

:: Create ZIP archive (optional, requires 7-Zip or PowerShell)
cd "%DIST_DIR%"
echo   Creating ZIP archive...
powershell -Command "Compress-Archive -Path '%BUILD_NAME%' -DestinationPath '%BUILD_NAME%.zip' -Force"
if errorlevel 1 (
    echo WARNING: Could not create ZIP archive
    echo Please install 7-Zip or use PowerShell 5.0+
) else (
    echo   Created: %BUILD_NAME%.zip
)

:: Calculate sizes
for %%F in ("%OUTPUT_DIR%\StationService.exe") do set "EXE_SIZE=%%~zF"
set /a "EXE_SIZE_MB=EXE_SIZE / 1048576"

echo.
echo ========================================
echo   Build Completed Successfully!
echo ========================================
echo   Version: %VERSION%
echo   Output: %OUTPUT_DIR%
echo   EXE Size: %EXE_SIZE_MB% MB
echo.
echo Next Steps:
echo   1. Test the deployment:
echo      cd "%OUTPUT_DIR%"
echo      StationService.exe
echo   2. Configure station.yaml
echo   3. Deploy to production
echo.
echo   ZIP archive: %DIST_DIR%\%BUILD_NAME%.zip
echo ========================================

cd "%PROJECT_ROOT%"
endlocal
pause
exit /b 0
