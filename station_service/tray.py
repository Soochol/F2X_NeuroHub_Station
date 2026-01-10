"""
System Tray Icon with Balloon Notifications for Station Service.

Provides:
- System tray icon with right-click menu
- Balloon notifications for status changes
- Quick access to UI, logs, and service control
"""

import logging
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Only import pystray on Windows
if sys.platform == "win32":
    try:
        import pystray
        from PIL import Image, ImageDraw
        TRAY_AVAILABLE = True
    except ImportError:
        TRAY_AVAILABLE = False
        logger.warning("pystray or PIL not available, tray icon disabled")
else:
    TRAY_AVAILABLE = False


class TrayIcon:
    """System tray icon manager with balloon notifications."""

    def __init__(
        self,
        port: int = 8080,
        on_exit: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize tray icon.

        Args:
            port: Server port for UI access
            on_exit: Callback when user requests exit from tray menu
        """
        self.port = port
        self.on_exit = on_exit
        self._icon: Optional["pystray.Icon"] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def _create_icon_image(self, color: str = "green") -> "Image.Image":
        """
        Create a simple icon image.

        Args:
            color: Icon color (green=running, yellow=warning, red=error)

        Returns:
            PIL Image for the tray icon
        """
        # Create a 64x64 image
        size = 64
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Color mapping
        colors = {
            "green": "#22c55e",
            "yellow": "#eab308",
            "red": "#ef4444",
            "blue": "#3b82f6",
        }
        fill_color = colors.get(color, colors["green"])

        # Draw a filled circle
        margin = 4
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=fill_color,
            outline="#1e293b",
            width=2,
        )

        # Draw "S" letter in the center
        try:
            # Try to use a font, fall back to default
            from PIL import ImageFont
            font = ImageFont.truetype("arial.ttf", 32)
        except Exception:
            font = None

        text = "S"
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width, text_height = 20, 20

        x = (size - text_width) // 2
        y = (size - text_height) // 2 - 4
        draw.text((x, y), text, fill="white", font=font)

        return image

    def _create_menu(self) -> "pystray.Menu":
        """Create the right-click context menu."""
        return pystray.Menu(
            pystray.MenuItem(
                "Open UI",
                self._on_open_ui,
                default=True,  # Double-click action
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Status: Running", None, enabled=False),
            pystray.MenuItem(
                f"Port: {self.port}",
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Logs Folder", self._on_open_logs),
            pystray.MenuItem("Open Config", self._on_open_config),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._on_exit),
        )

    def _on_open_ui(self, icon: "pystray.Icon", item: "pystray.MenuItem") -> None:
        """Open the web UI in default browser."""
        url = f"http://localhost:{self.port}/ui/"
        logger.info(f"Opening UI: {url}")
        webbrowser.open(url)

    def _on_open_logs(self, icon: "pystray.Icon", item: "pystray.MenuItem") -> None:
        """Open the logs folder."""
        from station_service.main import get_application_root
        logs_dir = get_application_root() / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            import os
            os.startfile(str(logs_dir))

    def _on_open_config(self, icon: "pystray.Icon", item: "pystray.MenuItem") -> None:
        """Open the config file."""
        from station_service.main import get_application_root
        config_file = get_application_root() / "config" / "station.yaml"
        if config_file.exists() and sys.platform == "win32":
            import os
            os.startfile(str(config_file))

    def _on_exit(self, icon: "pystray.Icon", item: "pystray.MenuItem") -> None:
        """Handle exit request from tray menu."""
        logger.info("Exit requested from tray menu")
        self.stop()
        if self.on_exit:
            self.on_exit()

    def start(self) -> None:
        """Start the tray icon in a background thread."""
        logger.info(f"[Tray] start() called, TRAY_AVAILABLE={TRAY_AVAILABLE}")

        if not TRAY_AVAILABLE:
            logger.info("System tray not available on this platform")
            return

        if self._running:
            logger.info("[Tray] Already running, skipping")
            return

        try:
            self._running = True
            logger.info("[Tray] Creating icon image...")
            icon_image = self._create_icon_image("green")
            logger.info(f"[Tray] Icon image created: {icon_image.size}")

            logger.info("[Tray] Creating menu...")
            menu = self._create_menu()
            logger.info("[Tray] Menu created")

            logger.info("[Tray] Creating pystray.Icon...")
            self._icon = pystray.Icon(
                name="StationService",
                icon=icon_image,
                title="Station Service - Running",
                menu=menu,
            )
            logger.info("[Tray] pystray.Icon created")

            # Run in background thread
            def run_with_error_handling():
                try:
                    logger.info("[Tray] Icon.run() starting...")
                    self._icon.run()
                    logger.info("[Tray] Icon.run() finished")
                except Exception as e:
                    logger.error(f"[Tray] Icon.run() error: {e}", exc_info=True)

            self._thread = threading.Thread(
                target=run_with_error_handling,
                daemon=True,
                name="TrayIconThread",
            )
            self._thread.start()
            logger.info("[Tray] Thread started, waiting for icon to be visible...")

            # Give the icon time to appear
            import time
            time.sleep(0.5)

            if self._icon.visible:
                logger.info("[Tray] Icon is visible!")
            else:
                logger.warning("[Tray] Icon may not be visible yet")

            logger.info("System tray icon started")

            # Show startup notification
            self.notify("Station Service", "Service started successfully", "info")

        except Exception as e:
            logger.error(f"[Tray] Failed to start: {e}", exc_info=True)
            self._running = False

    def stop(self) -> None:
        """Stop and remove the tray icon."""
        if not self._running:
            return

        self._running = False
        if self._icon:
            try:
                self._icon.stop()
            except Exception as e:
                logger.warning(f"Error stopping tray icon: {e}")
            self._icon = None

        logger.info("System tray icon stopped")

    def notify(
        self,
        title: str,
        message: str,
        level: str = "info",
    ) -> None:
        """
        Show a balloon notification.

        Args:
            title: Notification title
            message: Notification message
            level: Notification level (info, warning, error)
        """
        if not TRAY_AVAILABLE or not self._icon:
            return

        try:
            # Update icon color based on level
            color_map = {
                "info": "green",
                "warning": "yellow",
                "error": "red",
            }
            color = color_map.get(level, "green")

            # Show notification
            self._icon.notify(message, title)
            logger.debug(f"Tray notification: [{level}] {title}: {message}")

        except Exception as e:
            logger.warning(f"Failed to show notification: {e}")

    def update_status(self, status: str, color: str = "green") -> None:
        """
        Update the tray icon status.

        Args:
            status: Status text to show in tooltip
            color: Icon color (green, yellow, red)
        """
        if not TRAY_AVAILABLE or not self._icon:
            return

        try:
            self._icon.icon = self._create_icon_image(color)
            self._icon.title = f"Station Service - {status}"
        except Exception as e:
            logger.warning(f"Failed to update tray status: {e}")


# Global tray icon instance
_tray_icon: Optional[TrayIcon] = None


def get_tray_icon() -> Optional[TrayIcon]:
    """Get the global tray icon instance."""
    return _tray_icon


def set_tray_icon(icon: Optional[TrayIcon]) -> None:
    """Set the global tray icon instance."""
    global _tray_icon
    _tray_icon = icon


def notify(title: str, message: str, level: str = "info") -> None:
    """
    Show a balloon notification using the global tray icon.

    Args:
        title: Notification title
        message: Notification message
        level: Notification level (info, warning, error)
    """
    if _tray_icon:
        _tray_icon.notify(title, message, level)
