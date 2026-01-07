"""
Sequence dependency installer.

Reads pyproject.toml from sequence directories and installs missing dependencies.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

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
    Check if a package is installed using pip show.

    Args:
        package: Package name (with optional version specifier)

    Returns:
        True if installed
    """
    # Remove version specifiers to get base package name
    base_name = package.split(">=")[0].split("<=")[0].split("==")[0]
    base_name = base_name.split("<")[0].split(">")[0].split("~=")[0]
    base_name = base_name.strip()

    # Try multiple pip commands
    pip_commands = [
        [sys.executable, "-m", "pip", "show", base_name],
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
            logger.debug(f"Package check: {base_name} -> {'installed' if installed else 'not installed'}")
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
    logger.info(f"Dependencies from pyproject.toml: {deps}")

    if not deps:
        logger.debug("No dependencies found in pyproject.toml")
        return []

    # Filter to only missing packages
    missing = get_missing_packages(deps)
    if not missing:
        logger.debug(f"All dependencies already installed for {sequence_dir.name}")
        return []

    logger.info(f"Installing missing dependencies for {sequence_dir.name}: {missing}")

    try:
        # First, ensure pip is available in the current environment
        pip_check = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
        )
        if pip_check.returncode != 0:
            logger.warning("pip not available, attempting to install via ensurepip...")
            ensurepip_result = subprocess.run(
                [sys.executable, "-m", "ensurepip", "--upgrade"],
                capture_output=True,
                text=True,
            )
            if ensurepip_result.returncode == 0:
                logger.info("Successfully installed pip via ensurepip")
            else:
                logger.warning(f"ensurepip failed: {ensurepip_result.stderr}")

        # Try using sys.executable first, fallback to pip3/pip if pip module not available
        pip_commands = [
            [sys.executable, "-m", "pip", "install", *missing],
            ["pip3", "install", "--user", *missing],
            ["pip", "install", "--user", *missing],
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
