# tray.py — System tray icon and notifications

import threading
import pystray
from PIL import Image, ImageDraw
from i18n import t


import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def _create_icon_image():
    """Load the app icon for the tray."""
    icon_path = resource_path('icon.ico')
    if os.path.exists(icon_path):
        try:
            return Image.open(icon_path)
        except Exception:
            pass
    # Fallback if not found
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill='#cc0000')
    draw.polygon([(24, 16), (24, 48), (48, 32)], fill='white')
    return img


class TrayManager:
    def __init__(self, show_callback=None, quit_callback=None):
        self.show_callback = show_callback
        self.quit_callback = quit_callback
        self.icon = None
        self._thread = None

    def start(self):
        """Start the system tray icon in a background thread."""
        def _run():
            menu = pystray.Menu(
                pystray.MenuItem(t('show_window'), self._on_show, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(t('quit'), self._on_quit),
            )
            self.icon = pystray.Icon(
                'yt_downloader',
                _create_icon_image(),
                'YouTube Downloader',
                menu
            )
            self.icon.run()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the tray icon."""
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass

    def notify(self, title, message):
        """Show a system notification."""
        if self.icon:
            try:
                self.icon.notify(message, title)
            except Exception:
                pass

    def _on_show(self, icon=None, item=None):
        if self.show_callback:
            self.show_callback()

    def _on_quit(self, icon=None, item=None):
        if self.quit_callback:
            self.quit_callback()
