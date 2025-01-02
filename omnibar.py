from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLineEdit, QListWidget, QListWidgetItem, QLabel,
                           QPushButton, QSystemTrayIcon, QMenu, QStyle)
from PyQt5.QtCore import Qt, QPoint, QTimer, QSize
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QIcon
import keyboard
import pyautogui
from pathlib import Path
from typing import Dict, Any
import logging

from settings import SettingsWindow, load_config, save_config
from modules import available_modules
from components import ResultsWidget, SearchDebouncer, HotkeyThread

logger = logging.getLogger(__name__)


class OmnibarWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dragging = False
        self.offset = None
        self.current_query = None
        self.hotkey_thread = None
        self.settings_window = None
        self.tray_icon = None

        # Load configuration first
        self.config = load_config()

        # Initialize UI components
        self._setup_ui()
        self._apply_window_style()

        # Initialize modules after UI
        self.enabled_modules = self._initialize_modules()

        # Setup tray and hotkeys last
        self._setup_tray()
        self._setup_hotkeys()

        # Hide window initially
        self.hide()

    def _setup_ui(self):
        # Set window flags
        flags = Qt.FramelessWindowHint | Qt.Tool
        if self.config.get('always_on_top', True):
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        # Central widget setup
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Search container
        search_container = QWidget()
        search_container.setObjectName("searchContainer")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(15, 15, 15, 15)

        # Command icon
        self.command_icon = QLabel("⦿")
        font_size = self.config.get('input_font_size', 11) + 8
        self.command_icon.setStyleSheet(f"""
            QLabel {{
                color: {self.config.get('accent_color', '#2196f3')};
                font-size: {font_size}px;
                padding-right: 12px;
                font-weight: normal;
                font-family: {self.config.get('font_family', 'Segoe UI')};
            }}
        """)
        search_layout.addWidget(self.command_icon)

        # Search box
        self.search_box = QLineEdit()
        font = QFont(self.config.get('font_family', 'Segoe UI'),
                    self.config.get('input_font_size', 11))
        self.search_box.setFont(font)
        self.search_box.setPlaceholderText("Type a command (e.g. :n happy, :s word)")
        self.search_box.setStyleSheet("""
            QLineEdit {
                border: none;
                background-color: transparent;
                selection-background-color: #bbdefb;
                selection-color: #1976d2;
                padding: 5px;
                font-weight: 400;
            }
        """)
        search_layout.addWidget(self.search_box)

        # Settings button
        self.settings_button = QPushButton("⚙")
        self.settings_button.setStyleSheet("""
            QPushButton {
                color: #757575;
                font-size: 16px;
                background: transparent;
                border: none;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: #1976d2;
            }
        """)
        self.settings_button.clicked.connect(self._show_settings)
        search_layout.addWidget(self.settings_button)

        main_layout.addWidget(search_container)

        # Results widget
        self.results = ResultsWidget(self)
        self.results.setFont(QFont(self.config.get('font_family', 'Segoe UI'),
                                  self.config.get('results_font_size', 10)))
        self.results.item_selected.connect(self._on_result_selected)

        # Set size
        self.resize(self.config.get('window_width', 650),
                    self.config.get('window_height', 65))

        # Install event filter for the search box
        self.search_box.installEventFilter(self)

        # Setup search debouncer
        self.search_debouncer = SearchDebouncer(
            self.config.get('typing_delay_ms', 200)
        )
        self.search_debouncer.timer.timeout.connect(self._process_search)

        # Connect signals
        self.search_box.textChanged.connect(self._on_text_changed)
        self.search_box.returnPressed.connect(self._on_return_pressed)

    def _initialize_modules(self) -> Dict[str, Any]:
        """Initialize and return enabled modules based on configuration."""
        module_settings = self.config.get('module_settings', {})
        enabled_modules = {}

        for name, module in available_modules.items():
            try:
                if module_settings.get(name, {}).get('enabled', True):
                    logger.info(f"Initializing module: {name}")
                    enabled_modules[name] = module
                    if hasattr(module, 'apply_settings'):
                        module.apply_settings(module_settings.get(name, {}))
            except Exception as e:
                logger.error(f"Error initializing module {name}: {e}")

        return enabled_modules

    def _apply_window_style(self):
        theme = self.config.get('theme', 'Light')
        accent_color = self.config.get('accent_color', '#2196f3')

        if theme == 'Light':
            self.setStyleSheet(f"""
                QMainWindow {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ffffff, stop:1 #f8f9fa);
                    border: 1px solid #e0e0e0;
                    border-radius: 12px;
                }}
                #searchContainer {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #ffffff, stop:1 #f5f6f7);
                    border-radius: 12px;
                    margin: 2px;
                }}
                QLineEdit::selection {{
                    background-color: {accent_color}40;
                    color: {accent_color};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QMainWindow {{
                    background: #1e1e1e;
                    border: 1px solid #333333;
                    border-radius: 12px;
                }}
                #searchContainer {{
                    background: #2d2d2d;
                    border-radius: 12px;
                    margin: 2px;
                }}
                QLineEdit {{
                    color: #ffffff;
                }}
                QLineEdit::selection {{
                    background-color: {accent_color}40;
                    color: {accent_color};
                }}
            """)

    def _setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = Path(__file__).parent / 'icon.png'
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMenuButton))

        tray_menu = QMenu()
        settings_action = tray_menu.addAction("Settings")
        settings_action.triggered.connect(self._show_settings)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self._quit_application)

        self.tray_icon.setContextMenu(tray_menu)
        if self.config.get('minimize_to_tray', True):
            self.tray_icon.show()

    def _setup_hotkeys(self):
        shortcut = self.config.get('activation_shortcut', 'Win+Space')
        self.hotkey_thread = HotkeyThread(shortcut)
        self.hotkey_thread.hotkey_pressed.connect(self._toggle_visibility)
        self.hotkey_thread.start()

    def eventFilter(self, obj, event):
        if obj is self.search_box and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Escape:
                self.hide_all()
                return True
        return super().eventFilter(obj, event)

    def _on_text_changed(self, text):
        if not text:
            self.results.hide()
            self.current_query = None
            return
        
        self.current_query = text
        self.search_debouncer.debounce(self._process_search)

    def _process_search(self):
        if not self.current_query:
            return

        text = self.current_query.lower()
        self.results.clear()

        try:
            for module in self.enabled_modules.values():
                if any(text.startswith(cmd) for cmd in module.commands):
                    # Add module header
                    header_item = QListWidgetItem(
                        f"{module.icon} {module.name} - Example: {module.commands[0]} {module.example}"
                    )
                    header_item.setFlags(Qt.NoItemFlags)
                    header_item.setBackground(QColor("#fafafa"))
                    self.results.addItem(header_item)

                    # Add results if query exists
                    query = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
                    if query:
                        try:
                            results = module.get_results(query)
                            # If results is a coroutine, run it in a thread
                            if hasattr(results, '__await__'):
                                import asyncio
                                from concurrent.futures import ThreadPoolExecutor
                                with ThreadPoolExecutor() as executor:
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    results = loop.run_until_complete(results)
                                    loop.close()
                                    
                            for result in results:
                                item = QListWidgetItem(result["display"])
                                if self.config.get('show_icons', True) and "icon" in result:
                                    item.setIcon(QIcon(result["icon"]))
                                self.results.addItem(item)
                        except Exception as e:
                            error_item = QListWidgetItem(f"Error: {str(e)}")
                            error_item.setForeground(QColor("#dc3545"))
                            self.results.addItem(error_item)

            if self.results.count() > 0:
                max_height = min(
                    300,
                    self.results.sizeHintForRow(0) * min(
                        self.results.count(),
                        self.config.get('max_results', 10)
                    ) + 20
                )
                self.results.resize(self.width(), max_height)
                pos = self.mapToGlobal(QPoint(0, self.height()))
                self.results.move(pos)
                self.results.show()
                self.activateWindow()
                self.search_box.setFocus()

        except Exception as e:
            logger.error(f"Error processing search: {e}")
            error_item = QListWidgetItem(f"Error: {str(e)}")
            error_item.setForeground(QColor("#dc3545"))
            self.results.addItem(error_item)

    def _show_settings(self):
        if not hasattr(self, 'settings_window'):
            self.settings_window = SettingsWindow(self)
            self.settings_window.settingsChanged.connect(self.apply_settings)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def apply_settings(self):
        self.config = load_config()

        # Update fonts
        font = QFont(self.config.get('font_family', 'Segoe UI'))
        input_size = self.config.get('input_font_size', 11)
        results_size = self.config.get('results_font_size', 10)

        self.search_box.setFont(QFont(font.family(), input_size))
        self.results.setFont(QFont(font.family(), results_size))

        # Update command icon
        self.command_icon.setStyleSheet(f"""
            QLabel {{
                color: {self.config.get('accent_color', '#2196f3')};
                font-size: {input_size + 8}px;
                padding-right: 12px;
                font-weight: normal;
                font-family: {font.family()};
            }}
        """)

        # Update window properties
        self.resize(self.config.get('window_width', 650),
                    self.config.get('window_height', 65))

        # Update search debouncer
        self.search_debouncer.delay_ms = self.config.get('typing_delay_ms', 200)

        # Update modules
        self.enabled_modules = self._initialize_modules()

        # Update theme
        self._apply_window_style()

        # Update hotkey
        shortcut = self.config.get('activation_shortcut', 'Win+Space')
        self.hotkey_thread.update_shortcut(shortcut)

        # Update tray
        if self.config.get('minimize_to_tray', True):
            self.tray_icon.show()
        else:
            self.tray_icon.hide()

    def _toggle_visibility(self):
        if self.isVisible():
            self.hide_all()
        else:
            if self.config.get('remember_position', False) and hasattr(self, 'last_position'):
                self.move(self.last_position)
            else:
                self._center_on_screen()
            self.show()
            self.activateWindow()
            self.search_box.setFocus(Qt.OtherFocusReason)
            self.search_box.clear()
            self.search_box.setCursorPosition(0)

    def _center_on_screen(self):
        mouse_x, mouse_y = pyautogui.position()
        screen = QApplication.primaryScreen().geometry()
        center_x = max(0, min(mouse_x - self.width()//2, screen.width() - self.width()))
        center_y = max(0, min(mouse_y - self.height()//2, screen.height() - self.height()))
        self.move(center_x, center_y)

    def _on_result_selected(self, item):
        if not item.flags() & Qt.NoItemFlags:
            self.search_box.setText(item.text())
            self.search_box.setFocus()
            self.results.hide()

    def _on_return_pressed(self):
        command = self.search_box.text().strip()
        if command:
            if self.config.get('save_history', True):
                self._save_to_history(command)
            if self.config.get('remember_position', False):
                self.last_position = self.pos()
            self.hide_all()

    def _save_to_history(self, command: str):
        history_file = Path.home() / '.omnibar' / 'command_history.txt'
        try:
            history_file.parent.mkdir(parents=True, exist_ok=True)
            max_history = self.config.get('history_size', 100)

            # Read existing history
            history = []
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = [line.strip() for line in f if line.strip()]

            # Add new command and limit size
            if command not in history:
                history.insert(0, command)
            history = history[:max_history]

            # Save updated history
            with open(history_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(history))

        except Exception as e:
            logger.error(f"Error saving command history: {e}")

    def hide_all(self):
        self.hide()
        self.results.hide()
        self.search_box.clear()
        self.current_query = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging and self.offset:
            new_pos = event.globalPos() - self.offset
            self.move(new_pos)
            if self.results.isVisible():
                self.results.move(new_pos.x(), new_pos.y() + self.height())

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.offset = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.config.get('show_shadow', True):
            # Outer shadow
            painter.setBrush(QColor(0, 0, 0, 20))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.rect().adjusted(2, 2, 2, 2), 12, 12)

            # Mid shadow
            painter.setBrush(QColor(0, 0, 0, 10))
            painter.drawRoundedRect(self.rect().adjusted(1, 1, 1, 1), 12, 12)

        # Window background with theme-appropriate gradient
        if self.config.get('theme', 'Light') == 'Light':
            gradient = QColor("#ffffff")
            border_color = QColor("#e0e0e0")
            highlight_color = QColor(255, 255, 255, 180)
        else:
            gradient = QColor("#1e1e1e")
            border_color = QColor("#333333")
            highlight_color = QColor(255, 255, 255, 40)

        painter.setBrush(gradient)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(self.rect(), 12, 12)

        # Inner highlight for depth
        painter.setPen(QPen(highlight_color, 1))
        painter.drawLine(
            self.rect().left() + 12,
            self.rect().top() + 1,
            self.rect().right() - 12,
            self.rect().top() + 1
        )

    def _quit_application(self):
        self.hotkey_thread.stop()
        self.hotkey_thread.wait()
        QApplication.quit()

    def closeEvent(self, event):
        if self.config.get('minimize_to_tray', True) and event.spontaneous():
            event.ignore()
            self.hide()
        else:
            self.hotkey_thread.stop()
            self.hotkey_thread.wait()
            super().closeEvent(event)
