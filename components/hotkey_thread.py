from PyQt5.QtCore import QThread, pyqtSignal
import keyboard
import logging

logger = logging.getLogger(__name__)

class HotkeyThread(QThread):
    """Thread for handling global hotkeys"""
    hotkey_pressed = pyqtSignal()

    def __init__(self, shortcut='windows+space'):
        super().__init__()
        self.shortcut = shortcut
        self.active = True
        self._hooked = False
        self.logger = logging.getLogger(__name__)

    def run(self):
        """Main thread loop"""
        while self.active:
            try:
                if not self._hooked:
                    keyboard.add_hotkey(
                        self.shortcut.lower(),
                        self._emit_signal,
                        suppress=True
                    )
                    self._hooked = True
                    keyboard.wait()
            except Exception as e:
                self.logger.error(f"Hotkey error: {e}")
                self._hooked = False
                self.msleep(1000)  # Wait before retry

    def _emit_signal(self):
        """Emit signal when hotkey is pressed"""
        if self.active:
            self.hotkey_pressed.emit()

    def update_shortcut(self, new_shortcut: str):
        """Update the hotkey shortcut"""
        try:
            if self._hooked:
                keyboard.unhook_all()
                self._hooked = False
            self.shortcut = new_shortcut
            if self.active:
                keyboard.add_hotkey(
                    self.shortcut.lower(),
                    self._emit_signal,
                    suppress=True
                )
                self._hooked = True
        except Exception as e:
            self.logger.error(f"Error updating shortcut: {e}")

    def stop(self):
        """Stop the hotkey thread"""
        self.active = False
        if self._hooked:
            try:
                keyboard.unhook_all()
            except Exception as e:
                self.logger.error(f"Error unhooking keyboard: {e}")
            self._hooked = False
        self.wait()

    def __del__(self):
        """Cleanup on deletion"""
        self.stop()