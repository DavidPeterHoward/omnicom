from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                           QCheckBox, QScrollArea, QPushButton, QLabel,
                           QSpinBox, QComboBox, QGridLayout, QFrame,
                           QProgressBar, QDialog, QDialogButtonBox)
from PyQt5.QtCore import Qt, QTimer
from modules import available_modules
import time

class ModuleSettingsWidget(QFrame):
    def __init__(self, module_name, module, parent=None):
        super().__init__(parent)
        self.module_name = module_name
        self.module = module
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self._setup_ui()

    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setColumnStretch(1, 1)

        # Module Header
        header_layout = QHBoxLayout()
        self.enabled_checkbox = QCheckBox(self.module_name)
        self.enabled_checkbox.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.enabled_checkbox)
        
        # Module commands
        commands_label = QLabel(f"Commands: {', '.join(self.module.commands)}")
        commands_label.setStyleSheet("color: #666;")
        header_layout.addWidget(commands_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout, 0, 0, 1, 2)

        # Example usage
        example_layout = QHBoxLayout()
        example_label = QLabel(f"Example: {self.module.icon} {self.module.example}")
        example_label.setStyleSheet("color: #666;")
        example_layout.addWidget(example_label)
        example_layout.addStretch()
        layout.addLayout(example_layout, 1, 0, 1, 2)

        # Module-specific settings
        self.settings_widgets = {}
        row = 2

        if hasattr(self.module, 'get_settings'):
            settings = self.module.get_settings()
            for setting in settings:
                label = QLabel(setting['label'])
                layout.addWidget(label, row, 0)

                if setting['type'] == 'bool':
                    widget = QCheckBox()
                    widget.setChecked(setting.get('default', False))
                elif setting['type'] == 'int':
                    widget = QSpinBox()
                    widget.setRange(setting.get('min', 0), setting.get('max', 100))
                    widget.setValue(setting.get('default', 0))
                elif setting['type'] == 'choice':
                    widget = QComboBox()
                    widget.addItems(setting.get('choices', []))
                    widget.setCurrentText(setting.get('default', ''))
                
                if 'tooltip' in setting:
                    widget.setToolTip(setting['tooltip'])
                
                layout.addWidget(widget, row, 1)
                self.settings_widgets[setting['key']] = widget
                row += 1

        # Module actions
        if hasattr(self.module, 'get_actions'):
            actions = self.module.get_actions()
            for action in actions:
                btn = QPushButton(action['label'])
                btn.clicked.connect(action['callback'])
                if 'tooltip' in action:
                    btn.setToolTip(action['tooltip'])
                layout.addWidget(btn, row, 0, 1, 2)
                row += 1

        # Status indicators
        if hasattr(self.module, 'get_statistics'):
            stats = self.module.get_statistics()
            if stats:
                stats_text = " | ".join(f"{k}: {v}" for k, v in stats.items())
                stats_label = QLabel(stats_text)
                stats_label.setStyleSheet("color: #666; font-style: italic;")
                layout.addWidget(stats_label, row, 0, 1, 2)

    def get_settings(self) -> dict:
        settings = {
            'enabled': self.enabled_checkbox.isChecked()
        }
        for key, widget in self.settings_widgets.items():
            if isinstance(widget, QCheckBox):
                settings[key] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                settings[key] = widget.value()
            elif isinstance(widget, QComboBox):
                settings[key] = widget.currentText()
        return settings

    def load_settings(self, settings: dict):
        self.enabled_checkbox.setChecked(settings.get('enabled', True))
        for key, widget in self.settings_widgets.items():
            if key in settings:
                if isinstance(widget, QCheckBox):
                    widget.setChecked(settings[key])
                elif isinstance(widget, QSpinBox):
                    widget.setValue(settings[key])
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(settings[key])

class ClearCacheDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Clearing Caches")
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.status_label = QLabel("Clearing module caches...")
        layout.addWidget(self.status_label)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, len(available_modules))
        layout.addWidget(self.progress)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def update_progress(self, module_name, count):
        self.status_label.setText(f"Clearing cache: {module_name}")
        self.progress.setValue(count)

class ModulesPage(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Top controls
        top_controls = QHBoxLayout()
        self.enable_all = QPushButton("Enable All")
        self.disable_all = QPushButton("Disable All")
        self.enable_all.clicked.connect(self._enable_all_modules)
        self.disable_all.clicked.connect(self._disable_all_modules)
        top_controls.addWidget(self.enable_all)
        top_controls.addWidget(self.disable_all)
        top_controls.addStretch()
        layout.addLayout(top_controls)

        # Scroll area for modules
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        
        # Create module settings widgets
        self.module_widgets = {}
        for module_name, module in available_modules.items():
            module_widget = ModuleSettingsWidget(module_name, module)
            self.content_layout.addWidget(module_widget)
            self.module_widgets[module_name] = module_widget

        self.content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Bottom controls
        bottom_controls = QHBoxLayout()
        self.clear_cache = QPushButton("Clear All Caches")
        self.clear_cache.clicked.connect(self._clear_all_caches)
        bottom_controls.addWidget(self.clear_cache)
        bottom_controls.addStretch()
        layout.addLayout(bottom_controls)

        self._apply_styles()

    def _apply_styles(self):
        style = """
            QFrame {
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin: 2px;
                padding: 8px;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #f8f9fa;
            }
            QPushButton:hover {
                background: #e9ecef;
                border-color: #bbb;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #2196f3;
                border-color: #2196f3;
                image: url(check.png);
            }
            QSpinBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QSpinBox:hover {
                border-color: #bbb;
            }
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                min-width: 100px;
            }
            QComboBox:hover {
                border-color: #bbb;
            }
            QLabel {
                color: #333;
            }
            QScrollArea {
                border: none;
            }
            QPushButton#clearCache {
                color: #dc3545;
                border-color: #dc3545;
            }
            QPushButton#clearCache:hover {
                background: #dc3545;
                color: white;
            }
        """
        self.setStyleSheet(style)

    def _enable_all_modules(self):
        for widget in self.module_widgets.values():
            widget.enabled_checkbox.setChecked(True)

    def _disable_all_modules(self):
        for widget in self.module_widgets.values():
            widget.enabled_checkbox.setChecked(False)

    def _clear_all_caches(self):
        dialog = ClearCacheDialog(self)
        dialog.show()
        
        count = 0
        for module_name, module in available_modules.items():
            if hasattr(module, 'clear_cache'):
                dialog.update_progress(module_name, count)
                try:
                    module.clear_cache()
                except Exception as e:
                    print(f"Error clearing cache for {module_name}: {e}")
                count += 1
                QTimer.singleShot(100, lambda: None)  # Allow UI updates
        
        dialog.accept()

    def load_settings(self, config):
        module_settings = config.get('module_settings', {})
        for module_name, widget in self.module_widgets.items():
            settings = module_settings.get(module_name, {'enabled': True})
            widget.load_settings(settings)

    def save_settings(self, config):
        module_settings = {}
        for module_name, widget in self.module_widgets.items():
            module_settings[module_name] = widget.get_settings()
        config['module_settings'] = module_settings

    def apply_settings(self):
        for module_name, widget in self.module_widgets.items():
            settings = widget.get_settings()
            module = available_modules[module_name]
            if hasattr(module, 'apply_settings'):
                module.apply_settings(settings)