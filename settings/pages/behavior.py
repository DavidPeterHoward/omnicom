from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                           QLabel, QComboBox, QCheckBox, QSpinBox, QPushButton,
                           QKeySequenceEdit, QMessageBox, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence
import json
from pathlib import Path

class KeyboardShortcutWidget(QWidget):
    shortcutChanged = pyqtSignal(str, str)  # action, shortcut

    def __init__(self, action: str, default_shortcut: str, parent=None):
        super().__init__(parent)
        self.action = action
        self._setup_ui(default_shortcut)

    def _setup_ui(self, default_shortcut: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Action label
        label = QLabel(self.action)
        label.setMinimumWidth(150)
        layout.addWidget(label)

        # Shortcut edit
        self.shortcut_edit = QKeySequenceEdit()
        self.shortcut_edit.setKeySequence(QKeySequence(default_shortcut))
        self.shortcut_edit.editingFinished.connect(self._on_shortcut_changed)
        layout.addWidget(self.shortcut_edit)

        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(lambda: self.shortcut_edit.setKeySequence(
            QKeySequence(default_shortcut)
        ))
        layout.addWidget(reset_btn)

    def _on_shortcut_changed(self):
        self.shortcutChanged.emit(
            self.action,
            self.shortcut_edit.keySequence().toString()
        )

    def get_shortcut(self) -> str:
        return self.shortcut_edit.keySequence().toString()

class BehaviorPage(QWidget):
    def __init__(self):
        super().__init__()
        self.shortcuts = {}
        self._setup_ui()

    def _setup_ui(self):
        # Create scroll area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        # Main widget inside scroll area
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(20)

        # General Group
        general_group = QGroupBox("General Behavior")
        general_layout = QVBoxLayout()

        # Startup options
        self.start_with_windows = QCheckBox("Start with Windows")
        self.minimize_to_tray = QCheckBox("Minimize to system tray")
        self.remember_position = QCheckBox("Remember window position")
        self.always_on_top = QCheckBox("Always on top")
        self.focus_on_show = QCheckBox("Focus input on show")
        self.hide_on_blur = QCheckBox("Hide when losing focus")

        general_layout.addWidget(self.start_with_windows)
        general_layout.addWidget(self.minimize_to_tray)
        general_layout.addWidget(self.remember_position)
        general_layout.addWidget(self.always_on_top)
        general_layout.addWidget(self.focus_on_show)
        general_layout.addWidget(self.hide_on_blur)

        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        # Keyboard Shortcuts Group
        shortcuts_group = QGroupBox("Keyboard Shortcuts")
        shortcuts_layout = QVBoxLayout()

        # Default shortcuts
        self.shortcuts = {
            "Show/Hide Window": "Meta+Space",
            "Quick Access Menu": "Meta+Q",
            "Settings": "Meta+,",
            "Clear Input": "Esc",
            "Focus Results": "Down",
            "Previous Result": "Up",
            "Select Result": "Return"
        }

        # Add shortcut editors
        for action, default in self.shortcuts.items():
            shortcut_widget = KeyboardShortcutWidget(action, default)
            shortcut_widget.shortcutChanged.connect(self._on_shortcut_changed)
            shortcuts_layout.addWidget(shortcut_widget)

        shortcuts_group.setLayout(shortcuts_layout)
        layout.addWidget(shortcuts_group)

        # Search Behavior Group
        search_group = QGroupBox("Search Behavior")
        search_layout = QVBoxLayout()

        # Typing settings
        typing_layout = QHBoxLayout()
        typing_layout.addWidget(QLabel("Typing Delay (ms):"))
        self.typing_delay = QSpinBox()
        self.typing_delay.setRange(0, 1000)
        self.typing_delay.setSingleStep(50)
        typing_layout.addWidget(self.typing_delay)
        typing_layout.addStretch()
        search_layout.addLayout(typing_layout)

        # Minimum input length
        min_length_layout = QHBoxLayout()
        min_length_layout.addWidget(QLabel("Minimum Search Length:"))
        self.min_search_length = QSpinBox()
        self.min_search_length.setRange(1, 5)
        min_length_layout.addWidget(self.min_search_length)
        min_length_layout.addStretch()
        search_layout.addLayout(min_length_layout)

        # Results settings
        results_layout = QHBoxLayout()
        results_layout.addWidget(QLabel("Max Results:"))
        self.max_results = QSpinBox()
        self.max_results.setRange(5, 50)
        results_layout.addWidget(self.max_results)
        results_layout.addStretch()
        search_layout.addLayout(results_layout)

        # Search options
        self.instant_search = QCheckBox("Enable instant search")
        self.fuzzy_match = QCheckBox("Enable fuzzy matching")
        self.show_icons = QCheckBox("Show result icons")
        self.show_descriptions = QCheckBox("Show result descriptions")
        self.group_results = QCheckBox("Group results by module")

        search_layout.addWidget(self.instant_search)
        search_layout.addWidget(self.fuzzy_match)
        search_layout.addWidget(self.show_icons)
        search_layout.addWidget(self.show_descriptions)
        search_layout.addWidget(self.group_results)

        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        # History Group
        history_group = QGroupBox("History")
        history_layout = QVBoxLayout()

        # History options
        self.save_history = QCheckBox("Save search history")
        history_layout.addWidget(self.save_history)

        history_size_layout = QHBoxLayout()
        history_size_layout.addWidget(QLabel("History Size:"))
        self.history_size = QSpinBox()
        self.history_size.setRange(0, 1000)
        history_size_layout.addWidget(self.history_size)
        history_size_layout.addStretch()
        history_layout.addLayout(history_size_layout)

        # Clear history button
        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.clicked.connect(self._clear_history)
        history_layout.addWidget(clear_history_btn)

        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        # Session Group
        session_group = QGroupBox("Session")
        session_layout = QVBoxLayout()

        self.restore_last_query = QCheckBox("Restore last query on startup")
        self.save_module_state = QCheckBox("Save module state between sessions")
        self.auto_backup = QCheckBox("Auto-backup settings")

        session_layout.addWidget(self.restore_last_query)
        session_layout.addWidget(self.save_module_state)
        session_layout.addWidget(self.auto_backup)

        # Backup/Restore buttons
        backup_layout = QHBoxLayout()
        backup_btn = QPushButton("Backup Settings")
        restore_btn = QPushButton("Restore Settings")
        backup_btn.clicked.connect(self._backup_settings)
        restore_btn.clicked.connect(self._restore_settings)
        backup_layout.addWidget(backup_btn)
        backup_layout.addWidget(restore_btn)
        session_layout.addLayout(backup_layout)

        session_group.setLayout(session_layout)
        layout.addWidget(session_group)

        # Set the scroll area widget
        scroll.setWidget(main_widget)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #f0f0f0;
            }
            QSpinBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QCheckBox {
                spacing: 8px;
            }
            QKeySequenceEdit {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)

    def _on_shortcut_changed(self, action: str, shortcut: str):
        self.shortcuts[action] = shortcut

    def _clear_history(self):
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear the search history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            history_file = Path.home() / '.omnibar' / 'history.json'
            if history_file.exists():
                history_file.unlink()
            QMessageBox.information(self, "Success", "Search history cleared.")

    def _backup_settings(self):
        try:
            from settings.utils import save_config
            backup_path = Path.home() / '.omnibar' / 'backup'
            backup_path.mkdir(parents=True, exist_ok=True)
            
            config = {}
            self.save_settings(config)
            
            backup_file = backup_path / f'settings_backup_{int(time.time())}.json'
            with open(backup_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            QMessageBox.information(
                self,
                "Success",
                f"Settings backed up to:\n{backup_file}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to backup settings: {str(e)}"
            )

    def _restore_settings(self):
        try:
            backup_path = Path.home() / '.omnibar' / 'backup'
            if not backup_path.exists():
                QMessageBox.warning(
                    self,
                    "No Backups",
                    "No backup files found."
                )
                return

            # Find most recent backup
            backups = list(backup_path.glob('settings_backup_*.json'))
            if not backups:
                QMessageBox.warning(
                    self,
                    "No Backups",
                    "No backup files found."
                )
                return

            latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
            
            reply = QMessageBox.question(
                self,
                "Restore Settings",
                f"Restore settings from:\n{latest_backup}\n\nThis will overwrite current settings.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                with open(latest_backup, 'r') as f:
                    config = json.load(f)
                self.load_settings(config)
                QMessageBox.information(
                    self,
                    "Success",
                    "Settings restored successfully."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to restore settings: {str(e)}"
            )

    def load_settings(self, config: dict):
        self.start_with_windows.setChecked(config.get('start_with_windows', False))
        self.minimize_to_tray.setChecked(config.get('minimize_to_tray', True))
        self.remember_position.setChecked(config.get('remember_position', False))
        self.always_on_top.setChecked(config.get('always_on_top', True))
        self.focus_on_show.setChecked(config.get('focus_on_show', True))
        self.hide_on_blur.setChecked(config.get('hide_on_blur', False))
        
        # Load shortcuts
        shortcuts = config.get('shortcuts', self.shortcuts)
        for action, shortcut in shortcuts.items():
            self.shortcuts[action] = shortcut
        
        self.typing_delay.setValue(config.get('typing_delay_ms', 200))
        self.min_search_length.setValue(config.get('min_search_chars', 2))
        self.max_results.setValue(config.get('max_results', 10))
        
        self.instant_search.setChecked(config.get('instant_search', True))
        self.fuzzy_match.setChecked(config.get('fuzzy_match', True))
        self.show_icons.setChecked(config.get('show_icons', True))
        self.show_descriptions.setChecked(config.get('show_descriptions', True))
        self.group_results.setChecked(config.get('group_results', True))
        
        self.save_history.setChecked(config.get('save_history', True))
        self.history_size.setValue(config.get('history_size', 100))
        
        self.restore_last_query.setChecked(config.get('restore_last_query', False))
        self.save_module_state.setChecked(config.get('save_module_state', True))
        self.auto_backup.setChecked(config.get('auto_backup', True))

    def save_settings(self, config: dict):
        config['start_with_windows'] = self.start_with_windows.isChecked()
        config['minimize_to_tray'] = self.minimize_to_tray.isChecked()
        config['remember_position'] = self.remember_position.isChecked()
        config['always_on_top'] = self.always_on_top.isChecked()
        config['focus_on_show'] = self.focus_on_show.isChecked()
        config['hide_on_blur'] = self.hide_on_blur.isChecked()
        
        # Save shortcuts
        config['shortcuts'] = self.shortcuts
        
        config['typing_delay_ms'] = self.typing_delay.value()
        config['min_search_chars'] = self.min_search_length.value()
        config['max_results'] = self.max_results.value()
        
        config['instant_search'] = self.instant_search.isChecked()
        config['fuzzy_match'] = self.fuzzy_match.isChecked()
        config['show_icons'] = self.show_icons.isChecked()
        config['show_descriptions'] = self.show_descriptions.isChecked()
        config['group_results'] = self.group_results.isChecked()
        
        config['save_history'] = self.save_history.isChecked()
        config['history_size'] = self.history_size.value()
        
        config['restore_last_query'] = self.restore_last_query.isChecked()
        config['save_module_state'] = self.save_module_state.isChecked()
        config['auto_backup'] = self.auto_backup.isChecked()

    def get_keyboard_shortcuts(self) -> dict:
        """Get all current keyboard shortcuts"""
        return self.shortcuts.copy()

    def validate_settings(self) -> tuple[bool, str]:
        """Validate current settings configuration"""
        # Check for shortcut conflicts
        used_shortcuts = set()
        for action, shortcut in self.shortcuts.items():
            if shortcut in used_shortcuts:
                return False, f"Duplicate shortcut: {shortcut}"
            used_shortcuts.add(shortcut)
            
        # Validate other settings
        if self.typing_delay.value() < 0:
            return False, "Typing delay cannot be negative"
            
        if self.history_size.value() < 0:
            return False, "History size cannot be negative"
            
        return True, ""