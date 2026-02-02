"""
Path utilities for Station Service.

This module provides path-related utilities that can be safely imported
without triggering the main application initialization.

IMPORTANT: This module must NOT import from station_service.main or any
module that initializes the FastAPI app, IPC server, or other services.
"""

import sys
from pathlib import Path


def get_application_root() -> Path:
    """
    Get the application root directory.

    For PyInstaller frozen executables, this returns the directory containing the EXE.
    For normal Python execution, this returns the project root (parent of station_service/).

    Returns:
        Path to the application root directory
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle - EXE is in the root folder
        return Path(sys.executable).parent
    else:
        # Running as normal Python script
        # This file is at station_service/utils/paths.py
        # So parent.parent.parent gets us to the project root
        return Path(__file__).parent.parent.parent


def is_frozen() -> bool:
    """Check if running in a frozen (PyInstaller) environment."""
    return getattr(sys, 'frozen', False)


def get_embedded_python() -> Path | None:
    """
    Get the path to the embedded Python executable.

    In frozen (PyInstaller) builds, we include an embedded Python distribution
    for running sequences with dynamically installed dependencies.

    Returns:
        Path to embedded python.exe, or None if not found
    """
    if not is_frozen():
        # Not frozen - use system Python
        return None

    app_root = get_application_root()
    embedded_python = app_root / "python" / "python.exe"

    if embedded_python.exists():
        return embedded_python

    return None
