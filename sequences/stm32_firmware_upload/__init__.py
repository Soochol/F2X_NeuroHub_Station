"""
STM32 Firmware Upload Sequence Package

ST-LINK를 사용하여 STM32 MCU에 펌웨어를 업로드하는 시퀀스.
"""

# Configure loguru to disable default stderr handler
# This prevents duplicate logging when running under station-service
import sys
from loguru import logger

logger.remove()  # Remove default stderr handler
logger.add(
    sys.stdout,
    level="DEBUG",
    format="{time:HH:mm:ss} | {name}:{function}:{line} - {message}"
)  # Custom format without level (UI badge shows level separately)

from .sequence import STM32FirmwareUpload

__all__ = ["STM32FirmwareUpload"]
