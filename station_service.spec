# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for F2X NeuroHub Station Service
Builds a folder deployment (--onedir) with embedded React UI
"""
import os
import sys
from pathlib import Path

# Project paths (SPECPATH is provided by PyInstaller)
project_root = Path(SPECPATH)
station_service_dir = project_root / 'station_service'
static_dir = station_service_dir / 'static'
config_dir = project_root / 'config'

# Version extraction
version = '1.0.0'
try:
    import tomllib
    with open(project_root / 'pyproject.toml', 'rb') as f:
        pyproject = tomllib.load(f)
        version = pyproject['project']['version']
except Exception:
    pass

block_cipher = None

# Analysis: Discover all Python source files and dependencies
a = Analysis(
    [str(station_service_dir / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Static files (React UI build)
        (str(static_dir), 'station_service/static'),
        # Config template
        (str(config_dir / 'station.yaml.example'), 'config'),
        # Database schema
        (str(station_service_dir / 'storage' / 'schema.sql'), 'station_service/storage'),
    ],
    hiddenimports=[
        # FastAPI core
        'fastapi',
        'fastapi.routing',
        'fastapi.responses',
        'fastapi.staticfiles',
        'fastapi.middleware',
        'fastapi.middleware.cors',

        # Uvicorn server
        'uvicorn',
        'uvicorn.loops',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.websockets',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',

        # Pydantic v2
        'pydantic',
        'pydantic_core',
        'pydantic.json',
        'pydantic_settings',

        # PyZMQ for IPC
        'zmq',
        'zmq.backend',
        'zmq.backend.cython',
        'zmq.backend.select',

        # AsyncIO SQLite
        'aiosqlite',
        'sqlite3',

        # YAML configuration
        'yaml',

        # Logging
        'structlog',

        # HTTP client
        'httpx',
        'httpx._transports',
        'httpx._transports.default',

        # Serial communication
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'serial_asyncio',

        # Tornado (async networking)
        'tornado',
        'tornado.platform',
        'tornado.platform.asyncio',

        # Station Service SDK
        'station_service_sdk',

        # Excel/PDF generation
        'openpyxl',
        'reportlab',

        # Standard library hidden imports
        'asyncio',
        'asyncio.selector_events',
        'asyncio.windows_events',
        'asyncio.proactor_events',
        'email.mime.multipart',
        'email.mime.text',
        'email.mime.base',
        'encodings.idna',

        # All station_service submodules
        'station_service.api',
        'station_service.api.routes',
        'station_service.api.routes.system',
        'station_service.api.websocket',
        'station_service.batch',
        'station_service.core',
        'station_service.drivers',
        'station_service.hardware',
        'station_service.ipc',
        'station_service.models',
        'station_service.sequence',
        'station_service.services',
        'station_service.storage',
        'station_service.sync',
        'station_service.utils',
        'station_service.tray',

        # System tray support
        'pystray',
        'pystray._win32',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Development tools (not needed in production)
        'pytest',
        'pytest_asyncio',
        'pytest_cov',
        'black',
        'isort',
        'mypy',
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',

        # Exclude sequences (keep external)
        'sequences',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ: Compressed archive of pure Python modules
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE: Executable specification
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # --onedir mode
    name='StationService',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Don't use UPX compression (can cause issues)
    console=True,  # Enable console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Optional: Add icon file path here
)

# COLLECT: Gather all files into _internal folder
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='StationService',
)
