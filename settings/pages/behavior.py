from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QComboBox, QCheckBox, QGroupBox,
                           QSpinBox, QPushButton, QKeySequenceEdit)
from PyQt5.QtCore import Qt

class BehaviorPage(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Startup Group
        startup_group = QGroupBox("Startup Settings")
        startup_layout = QVBoxLayout()
        
        self.start_with_windows = QCheckBox("Start with Windows")
        self.minimize_to_tray = QCheckBox("Minimize to system tray")
        self.remember_position = QCheckBox("Remember window position")
        self.always_top = QCheckBox("Always on top")
        
        startup_layout.addWidget(self.start_with_windows)
        startup_layout.addWidget(self.minimize_to_tray)
        startup_layout.addWidget(self.remember_position)
        startup_layout.addWidget(self.always_top)
        startup_group.setLayout(startup_layout)
        
        # Shortcuts Group
        shortcuts_group = QGroupBox("Shortcut Settings")
        shortcuts_layout = QVBoxLayout()
        
        shortcut_layout = QHBoxLayout()
        shortcut_label = QLabel("Activation Shortcut:")
        self.activation_shortcut = QComboBox()
        self.activation_shortcut.addItems(["Win+Space", "Alt+Space", "Ctrl+Space", "Custom"])
        self.custom_shortcut = QKeySequenceEdit()
        self.custom_shortcut.setEnabled(False)
        
        self.activation_shortcut.currentTextChanged.connect(self._on_shortcut_changed)
        
        shortcut_layout.addWidget(shortcut_label)
        shortcut_layout.addWidget(self.activation_shortcut)
        shortcut_layout.addWidget(self.custom_shortcut)
        shortcut_layout.addStretch()
        
        shortcuts_layout.addLayout(shortcut_layout)
        shortcuts_group.setLayout(shortcuts_layout)
        
        # Search Behavior Group
        behavior_group = QGroupBox("Search Behavior")
        behavior_layout = QVBoxLayout()
        
        # Typing settings
        typing_layout = QHBoxLayout()
        typing_layout.addWidget(QLabel("Typing Delay (ms):"))
        self.typing_delay = QSpinBox()
        self.typing_delay.setRange(0, 1000)
        self.typing_delay.setSingleStep(50)
        typing_layout.addWidget(self.typing_delay)
        typing_layout.addStretch()
        
        # Results settings
        results_layout = QHBoxLayout()
        results_layout.addWidget(QLabel("Max Results:"))
        self.max_results = QSpinBox()
        self.max_results.setRange(5, 50)
        results_layout.addWidget(self.max_results)
        results_layout.addStretch()
        
        # Search options
        self.instant_search = QCheckBox("Enable instant search")
        self.fuzzy_match = QCheckBox("Enable fuzzy matching")
        self.show_icons = QCheckBox("Show result icons")
        self.save_history = QCheckBox("Save search history")
        
        behavior_layout.addLayout(typing_layout)
        behavior_layout.addLayout(results_layout)
        behavior_layout.addWidget(self.instant_search)
        behavior_layout.addWidget(self.fuzzy_match)
        behavior_layout.addWidget(self.show_icons)
        behavior_layout.addWidget(self.save_history)
        behavior_group.setLayout(behavior_layout)
        
        # History Group
        history_group = QGroupBox("History Settings")
        history_layout = QVBoxLayout()
        
        history_size_layout = QHBoxLayout()
        history_size_layout.addWidget(QLabel("History Size:"))
        self.history_size = QSpinBox()
        self.history_size.setRange(0, 1000)
        history_size_layout.addWidget(self.history_size)
        history_size_layout.addStretch()
        
        clear_history_btn = QPushButton("Clear History")
        clear_history_btn.clicked.connect(self._clear_history)
        
        history_layout.addLayout(history_size_layout)
        history_layout.addWidget(clear_history_btn)
        history_group.setLayout(history_layout)
        
        # Add all groups to main layout
        layout.addWidget(startup_group)
        layout.addWidget(shortcuts_group)
        layout.addWidget(behavior_group)
        layout.addWidget(history_group)
        layout.addStretch()
        
        self._apply_styles()

    def _apply_styles(self):
        style = """
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
            QSpinBox, QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                min-width: 80px;
            }
            QCheckBox {
                spacing: 8px;
            }
        """
        self.setStyleSheet(style)

    def _on_shortcut_changed(self, text):
        self.custom_shortcut.setEnabled(text == "Custom")

    def _clear_history(self):
        # Clear history functionality would be implemented here
        pass

    def load_settings(self, config):
        self.start_with_windows.setChecked(config.get('start_with_windows', False))
        self.minimize_to_tray.setChecked(config.get('minimize_to_tray', True))
        self.remember_position.setChecked(config.get('remember_position', False))
        self.always_top.setChecked(config.get('always_on_top', True))
        
        shortcut = config.get('activation_shortcut', 'Win+Space')
        if shortcut in ["Win+Space", "Alt+Space", "Ctrl+Space"]:
            self.activation_shortcut.setCurrentText(shortcut)
        else:
            self.activation_shortcut.setCurrentText("Custom")
            self.custom_shortcut.setKeySequence(shortcut)
        
        self.typing_delay.setValue(config.get('typing_delay_ms', 200))
        self.max_results.setValue(config.get('max_results', 10))
        self.instant_search.setChecked(config.get('instant_search', True))
        self.fuzzy_match.setChecked(config.get('fuzzy_match', True))
        self.show_icons.setChecked(config.get('show_icons', True))
        self.save_history.setChecked(config.get('save_history', True))
        self.history_size.setValue(config.get('history_size', 100))

    def save_settings(self, config):
        config['start_with_windows'] = self.start_with_windows.isChecked()
        config['minimize_to_tray'] = self.minimize_to_tray.isChecked()
        config['remember_position'] = self.remember_position.isChecked()
        config['always_on_top'] = self.always_top.isChecked()
        
        if self.activation_shortcut.currentText() == "Custom":
            config['activation_shortcut'] = self.custom_shortcut.keySequence().toString()
        else:
            config['activation_shortcut'] = self.activation_shortcut.currentText()
        
        config['typing_delay_ms'] = self.typing_delay.value()
        config['max_results'] = self.max_results.value()
        config['instant_search'] = self.instant_search.isChecked()
        config['fuzzy_match'] = self.fuzzy_match.isChecked()
        config['show_icons'] = self.show_icons.isChecked()
        config['save_history'] = self.save_history.isChecked()
        config['history_size'] = self.history_size.value()