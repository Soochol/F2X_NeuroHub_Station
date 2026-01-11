#Requires -RunAsAdministrator
<#
.SYNOPSIS
    로컬 빌드를 C:\StationService에 배포하는 스크립트

.DESCRIPTION
    - StationService 중지
    - 기존 파일 백업
    - 새 빌드 복사
    - Config 및 Data 복원
    - 서비스 시작

.EXAMPLE
    .\deploy_local.ps1

.EXAMPLE
    .\deploy_local.ps1 -BuildPath "C:\StationService_NEW"
#>

param(
    [string]$BuildPath = "C:\StationService_NEW",
    [string]$InstallPath = "C:\StationService",
    [string]$ServiceName = "StationService"
)

$ErrorActionPreference = "Stop"

# =============================================================================
# Functions
# =============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host "`n[*] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[+] $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "[-] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "[i] $Message" -ForegroundColor Yellow
}

# =============================================================================
# Main
# =============================================================================

Write-Host "=============================================" -ForegroundColor Yellow
Write-Host " F2X Station Service - Local Deployment" -ForegroundColor Yellow
Write-Host "=============================================" -ForegroundColor Yellow
Write-Host ""

# Verify build path exists
if (-not (Test-Path $BuildPath)) {
    Write-Fail "Build path not found: $BuildPath"
    Write-Info "Please build the project first using build.bat"
    exit 1
}

$buildExe = Join-Path $BuildPath "StationService.exe"
if (-not (Test-Path $buildExe)) {
    Write-Fail "StationService.exe not found in: $BuildPath"
    exit 1
}

Write-Success "Build found: $BuildPath"

# Check if service exists
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $service) {
    Write-Fail "Service '$ServiceName' not found"
    Write-Info "Please install the service first using update.ps1"
    exit 1
}

# Stop service and all related processes
Write-Step "Stopping service and all related processes..."

# Stop Windows Service first
if ($service.Status -eq "Running") {
    Stop-Service -Name $ServiceName -Force
    Start-Sleep -Seconds 2
    Write-Success "Service stopped"
} else {
    Write-Info "Service was not running"
}

# Force kill any remaining StationService processes (parent and child workers)
$processes = Get-Process -Name "StationService" -ErrorAction SilentlyContinue
if ($processes) {
    Write-Info "Cleaning up remaining processes: $($processes.Id -join ', ')"
    $processes | Stop-Process -Force
    Start-Sleep -Seconds 2
    Write-Success "All processes terminated"
}

# Verify critical ports are free
$port5555 = netstat -ano | Select-String ":5555.*LISTENING"
$port8080 = netstat -ano | Select-String ":8080.*LISTENING"
if ($port5555 -or $port8080) {
    Write-Fail "Critical ports still in use after cleanup!"
    if ($port5555) { Write-Info "Port 5555 (IPC): $port5555" }
    if ($port8080) { Write-Info "Port 8080 (HTTP): $port8080" }
    Write-Info "Please manually kill the processes or reboot"
    pause
    exit 1
}
Write-Success "All ports verified free"

# Backup config and data
Write-Step "Backing up config and data..."
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupBase = Join-Path $env:TEMP "StationService_backup_$timestamp"

$configPath = Join-Path $InstallPath "config"
$dataPath = Join-Path $InstallPath "data"
$logsPath = Join-Path $InstallPath "logs"

$backupConfig = Join-Path $backupBase "config"
$backupData = Join-Path $backupBase "data"
$backupLogs = Join-Path $backupBase "logs"

New-Item -ItemType Directory -Path $backupBase -Force | Out-Null

if (Test-Path $configPath) {
    Copy-Item -Path $configPath -Destination $backupConfig -Recurse
    Write-Success "Config backed up"
}

if (Test-Path $dataPath) {
    Copy-Item -Path $dataPath -Destination $backupData -Recurse
    Write-Success "Data backed up"
}

if (Test-Path $logsPath) {
    Copy-Item -Path $logsPath -Destination $backupLogs -Recurse
    Write-Success "Logs backed up"
}

# Keep nssm.exe
$nssmPath = Join-Path $InstallPath "nssm.exe"
$backupNssm = Join-Path $backupBase "nssm.exe"
if (Test-Path $nssmPath) {
    Copy-Item -Path $nssmPath -Destination $backupNssm
}

Write-Info "Backup location: $backupBase"

# Remove old files (except backups)
Write-Step "Removing old files..."
Get-ChildItem -Path $InstallPath | Where-Object {
    $_.Name -notin @("config", "data", "logs", "nssm.exe")
} | Remove-Item -Recurse -Force
Write-Success "Old files removed"

# Copy new build
Write-Step "Copying new build..."
Get-ChildItem -Path $BuildPath | Where-Object {
    $_.Name -notin @("config", "data", "logs")
} | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $InstallPath -Recurse -Force
}
Write-Success "New build copied"

# Restore config and data
Write-Step "Restoring config and data..."

if (Test-Path $backupConfig) {
    if (-not (Test-Path $configPath)) {
        New-Item -ItemType Directory -Path $configPath -Force | Out-Null
    }
    Copy-Item -Path "$backupConfig\*" -Destination $configPath -Recurse -Force
    Write-Success "Config restored"
}

if (Test-Path $backupData) {
    if (-not (Test-Path $dataPath)) {
        New-Item -ItemType Directory -Path $dataPath -Force | Out-Null
    }
    Copy-Item -Path "$backupData\*" -Destination $dataPath -Recurse -Force
    Write-Success "Data restored"
}

if (Test-Path $backupLogs) {
    if (-not (Test-Path $logsPath)) {
        New-Item -ItemType Directory -Path $logsPath -Force | Out-Null
    }
    Copy-Item -Path "$backupLogs\*" -Destination $logsPath -Recurse -Force
    Write-Success "Logs restored"
}

# Restore nssm.exe
if (Test-Path $backupNssm) {
    Copy-Item -Path $backupNssm -Destination $nssmPath -Force
}

# Get version
$versionFile = Join-Path $InstallPath "VERSION.txt"
$version = if (Test-Path $versionFile) { (Get-Content $versionFile -Raw).Trim() } else { "Unknown" }

# Start service
Write-Step "Starting service..."
Start-Service -Name $ServiceName
Start-Sleep -Seconds 3

# Verify
$service = Get-Service -Name $ServiceName
if ($service.Status -eq "Running") {
    Write-Success "Service started successfully"
} else {
    Write-Fail "Service failed to start"
    Write-Info "Check logs at: $logsPath"
    exit 1
}

# Summary
Write-Host "`n=============================================" -ForegroundColor Green
Write-Host " Deployment Complete!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host "Version:  $version"
Write-Host "Status:   $($service.Status)"
Write-Host "Backup:   $backupBase"
Write-Host ""
Write-Host "Access UI at: http://localhost:8080/ui" -ForegroundColor Cyan
Write-Host ""
Write-Host "Logs: $logsPath\service.log" -ForegroundColor Cyan
Write-Host ""
Write-Host "To monitor logs:"
Write-Host "  Get-Content '$logsPath\service.log' -Wait -Tail 20"
Write-Host "============================================="
