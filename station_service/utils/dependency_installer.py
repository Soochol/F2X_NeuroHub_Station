"""
Sequence dependency installer.

Reads pyproject.toml from sequence directories and installs missing dependencies.

NOTE: In frozen (PyInstaller) environments, pip is not available via sys.executable.
This module detects frozen environments and skips pip operations, relying on
pre-bundled dependencies or system Python instead.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def is_frozen() -> bool:
    """Check if running in a frozen (PyInstaller) environment."""
    return getattr(sys, 'frozen', False)


def get_embedded_python() -> Optional[str]:
    """
    Get the path to embedded Python executable (bundled with the deployment).

    Returns:
        Path to embedded python.exe, or None if not found
    """
    if not is_frozen():
        return None

    from station_service.utils.paths import get_application_root
    app_root = get_application_root()
    embedded_python = app_root / "python" / "python.exe"

    if embedded_python.exists():
        logger.debug(f"Found embedded Python: {embedded_python}")
        return str(embedded_python)

    return None


def get_system_python() -> Optional[str]:
    """
    Get the path to a usable Python executable.

    Priority order:
    1. Embedded Python (bundled with deployment) - preferred for self-contained operation
    2. System Python (fallback)

    In non-frozen environments, returns sys.executable.

    Returns:
        Path to Python executable, or None if not found
    """
    if not is_frozen():
        return sys.executable

    # First, try embedded Python (self-contained, preferred)
    embedded = get_embedded_python()
    if embedded:
        logger.info(f"Using embedded Python: {embedded}")
        return embedded

    # Fallback: try to find system Python
    import shutil
    logger.info("Embedded Python not found, searching for system Python...")

    # Try common Python executables
    for python_name in ["python", "python3", "py"]:
        python_path = shutil.which(python_name)
        if python_path:
            # Skip Windows Store Python stub (it's not a real Python)
            if "WindowsApps" in python_path:
                logger.debug(f"Skipping Windows Store Python stub: {python_path}")
                continue

            # Verify it's a working Python by running a simple command
            try:
                result = subprocess.run(
                    [python_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    logger.info(f"Found working system Python: {python_path}")
                    return python_path
                else:
                    logger.debug(f"Python at {python_path} failed version check")
            except Exception as e:
                logger.debug(f"Python at {python_path} failed: {e}")
                continue

    logger.warning("No Python found (embedded or system)")
    return None

# Python 3.11+ has tomllib in stdlib, fallback to tomli for older versions
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


# Mapping from pip package name to import name
PACKAGE_IMPORT_MAP = {
    "pyserial": "serial",
    "pyyaml": "yaml",
    "pillow": "PIL",
    "scikit-learn": "sklearn",
    "opencv-python": "cv2",
}


def get_import_name(package: str) -> str:
    """
    Get the import name for a pip package.

    Args:
        package: Package name (with optional version specifier)

    Returns:
        Import name
    """
    # Remove version specifiers
    base_name = package.split(">=")[0].split("<=")[0].split("==")[0]
    base_name = base_name.split("<")[0].split(">")[0].split("~=")[0]
    base_name = base_name.strip().lower()

    return PACKAGE_IMPORT_MAP.get(base_name, base_name.replace("-", "_"))


def is_installed(package: str) -> bool:
    """
    Check if a package is installed.

    In frozen environments, checks using system Python since sequences run as subprocess.
    In normal environments, uses importlib first, then pip show.

    Args:
        package: Package name (with optional version specifier)

    Returns:
        True if installed
    """
    # Remove version specifiers to get base package name
    base_name = package.split(">=")[0].split("<=")[0].split("==")[0]
    base_name = base_name.split("<")[0].split(">")[0].split("~=")[0]
    base_name = base_name.strip()

    import_name = get_import_name(package)

    # In frozen environment, we must check system Python because sequences run as subprocess
    if is_frozen():
        python_exe = get_system_python()
        if not python_exe:
            logger.warning(f"Package check (frozen): {base_name} -> cannot check (no system Python)")
            return False

        # Use system Python to check if package is importable
        try:
            result = subprocess.run(
                [python_exe, "-c", f"import {import_name}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            installed = result.returncode == 0
            logger.debug(f"Package check (frozen/subprocess): {base_name} ({import_name}) -> {'installed' if installed else 'not installed'}")
            return installed
        except subprocess.TimeoutExpired:
            logger.warning(f"Package check timeout: {base_name}")
            return False
        except Exception as e:
            logger.warning(f"Package check error: {base_name} - {e}")
            return False

    # In normal environment, try import check first (faster)
    try:
        import importlib.util
        spec = importlib.util.find_spec(import_name)
        if spec is not None:
            logger.debug(f"Package check (import): {base_name} ({import_name}) -> installed")
            return True
    except (ImportError, ModuleNotFoundError, ValueError):
        pass

    # Fallback to pip show for packages with different import names
    python_exe = get_system_python()
    if not python_exe:
        logger.debug(f"Package check: {base_name} -> assuming not installed (no Python)")
        return False

    pip_commands = [
        [python_exe, "-m", "pip", "show", base_name],
        ["pip3", "show", base_name],
        ["pip", "show", base_name],
    ]

    try:
        for cmd in pip_commands:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )
            if "No module named pip" in result.stderr:
                continue
            installed = result.returncode == 0
            logger.debug(f"Package check (pip): {base_name} -> {'installed' if installed else 'not installed'}")
            return installed

        # All pip commands failed
        logger.warning(f"Could not check package {base_name}: pip not available")
        return False
    except Exception as e:
        logger.warning(f"Failed to check package {base_name}: {e}")
        return False


def get_missing_packages(packages: List[str]) -> List[str]:
    """
    Get list of packages that are not installed.

    Args:
        packages: List of package specs

    Returns:
        List of missing package specs
    """
    return [pkg for pkg in packages if not is_installed(pkg)]


def install_sequence_dependencies(sequence_dir: Path) -> List[str]:
    """
    Install dependencies from sequence's pyproject.toml.

    Args:
        sequence_dir: Path to sequence directory

    Returns:
        List of newly installed packages
    """
    logger.info(f"Checking dependencies for sequence: {sequence_dir}")

    if tomllib is None:
        logger.warning("tomllib/tomli not available, cannot parse pyproject.toml")
        return []

    pyproject_path = sequence_dir / "pyproject.toml"
    logger.debug(f"Looking for pyproject.toml at: {pyproject_path.absolute()}")

    if not pyproject_path.exists():
        logger.debug(f"pyproject.toml not found at {pyproject_path}")
        return []

    logger.info(f"Found pyproject.toml: {pyproject_path}")

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        logger.warning(f"Failed to parse {pyproject_path}: {e}")
        return []

    deps = data.get("project", {}).get("dependencies", [])

    # Always include SDK as implicit dependency (required for all sequences)
    SDK_DEPENDENCY = "station-service-sdk>=2.1.0"
    if SDK_DEPENDENCY not in deps and not any(d.startswith("station-service-sdk") for d in deps):
        deps = [SDK_DEPENDENCY] + list(deps)
        logger.info(f"Added implicit SDK dependency: {SDK_DEPENDENCY}")

    logger.info(f"Dependencies (including SDK): {deps}")

    if not deps:
        logger.debug("No dependencies found in pyproject.toml")
        return []

    # Filter to only missing packages
    logger.info(f"Checking which packages are missing...")
    missing = get_missing_packages(deps)
    if not missing:
        logger.info(f"All dependencies already installed for {sequence_dir.name}")
        return []

    logger.info(f"Installing missing dependencies for {sequence_dir.name}: {missing}")

    try:
        # Get Python executable (handles frozen vs normal environment)
        # In frozen environment, this finds system Python for pip install
        logger.info(f"Finding system Python for pip install (frozen={is_frozen()})...")
        python_exe = get_system_python()
        logger.info(f"System Python found: {python_exe}")
        if not python_exe:
            logger.error("No Python executable available for pip install. Please install Python on this system.")
            return []

        # First, ensure pip is available in the current environment
        pip_check = subprocess.run(
            [python_exe, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
        )
        if pip_check.returncode != 0:
            logger.warning("pip not available, attempting to install via ensurepip...")
            ensurepip_result = subprocess.run(
                [python_exe, "-m", "ensurepip", "--upgrade"],
                capture_output=True,
                text=True,
            )
            if ensurepip_result.returncode == 0:
                logger.info("Successfully installed pip via ensurepip")
            else:
                logger.warning(f"ensurepip failed: {ensurepip_result.stderr}")

        # Try using python_exe first, fallback to pip3/pip if pip module not available
        # Use --break-system-packages to bypass externally-managed-environment restriction
        pip_commands = [
            [python_exe, "-m", "pip", "install", "--break-system-packages", *missing],
            ["pip3", "install", "--user", "--break-system-packages", *missing],
            ["pip", "install", "--user", "--break-system-packages", *missing],
        ]

        result = None
        for cmd in pip_commands:
            logger.debug(f"Trying pip command: {cmd[0:3]}...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                logger.info(f"Successfully ran: {cmd[0:3]}")
                break
            elif "No module named pip" in result.stderr:
                logger.warning(f"pip not available via {cmd[0]}, trying next...")
                continue
            else:
                # Other error, don't try alternatives
                break

        if result.returncode != 0:
            logger.error(f"pip install failed with code {result.returncode}")
            if result.stdout:
                logger.error(f"pip stdout: {result.stdout}")
            if result.stderr:
                logger.error(f"pip stderr: {result.stderr}")
            return []

        logger.info(f"pip install completed: {missing}")

        # Verify installation
        still_missing = get_missing_packages(missing)
        if still_missing:
            logger.error(f"Installation verification failed. Still missing: {still_missing}")
            return [pkg for pkg in missing if pkg not in still_missing]

        logger.info(f"Successfully installed and verified: {missing}")
        return missing

    except Exception as e:
        logger.error(f"Failed to install dependencies: {e}")
        return []
