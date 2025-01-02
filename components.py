from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
import keyboard
import logging

logger = logging.getLogger(__name__)


class ResultsWidget(QListWidget):
    item_selected = pyqtSignal(QListWidgetItem)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.NoFocus)
        self.itemClicked.connect(self.item_selected.emit)
        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                outline: none;
                padding: 8px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px 0px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)


class SearchDebouncer:
    def __init__(self, delay_ms: int = 200):
        self.delay_ms = delay_ms
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.queued_search = None

    def debounce(self, func, *args, **kwargs):
        self.queued_search = lambda: func(*args, **kwargs)
        self.timer.stop()
        self.timer.start(self.delay_ms)


class HotkeyThread(QThread):
    hotkey_pressed = pyqtSignal()

    def __init__(self, shortcut='windows+space'):
        super().__init__()
        self.shortcut = shortcut
        self.active = True
        self._hooked = False

    def run(self):
        while self.active:
            try:
                if not self._hooked:
                    keyboard.add_hotkey(self.shortcut.lower(), self._emit_signal, suppress=True)
                    self._hooked = True
                    keyboard.wait()
            except Exception as e:
                logger.error(f"Hotkey error: {e}")
                self._hooked = False
                self.msleep(1000)

    def _emit_signal(self):
        if self.active:
            self.hotkey_pressed.emit()

    def update_shortcut(self, new_shortcut):
        if self._hooked:
            keyboard.unhook_all()
            self._hooked = False
        self.shortcut = new_shortcut
        if self.active:
            keyboard.add_hotkey(self.shortcut.lower(), self._emit_signal, suppress=True)
            self._hooked = True

    def stop(self):
        self.active = False
        if self._hooked:
            keyboard.unhook_all()
            self._hooked = False
        self.wait()
