from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                           QLabel, QCheckBox, QSpinBox, QComboBox, QPushButton,
                           QScrollArea, QFrame, QTabWidget, QLineEdit, QGridLayout,
                           QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from modules import available_modules
import time
from utils.icons import IconRegistry
import json
from modules import available_modules

class ModuleConfigWidget(QFrame):
    """Widget for configuring a single module"""
    configChanged = pyqtSignal(str, dict)  # module_name, config
    
    def __init__(self, module_name: str, module: Any, parent=None):
        super().__init__(parent)
        self.module_name = module_name
        self.module = module
        self.icon_registry = IconRegistry()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        
        # Module icon
        icon_label = QLabel()
        if hasattr(self.module, 'icon'):
            icon = self.icon_registry.get_qicon(
                self.module.icon.lower(),
                size=24
            )
            icon_label.setPixmap(icon.pixmap(QSize(24, 24)))
        header.addWidget(icon_label)
        
        # Module title
        title = QLabel(self.module_name)
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(title)
        
        # Enable/Disable toggle
        self.enabled_check = QCheckBox("Enabled")
        header.addWidget(self.enabled_check)
        
        header.addStretch()
        layout.addLayout(header)
        
        # Module settings
        settings_group = QGroupBox("Settings")
        settings_layout = QGridLayout()
        self.setting_widgets = {}
        
        if hasattr(self.module, 'get_settings'):
            settings = self.module.get_settings()
            for row, setting in enumerate(settings):
                label = QLabel(setting['label'])
                settings_layout.addWidget(label, row, 0)
                
                if setting['type'] == 'bool':
                    widget = QCheckBox()
                    widget.setChecked(setting.get('default', False))
                elif setting['type'] == 'int':
                    widget = QSpinBox()
                    widget.setRange(setting.get('min', 0), 
                                 setting.get('max', 100))
                    widget.setValue(setting.get('default', 0))
                elif setting['type'] == 'choice':
                    widget = QComboBox()
                    widget.addItems(setting.get('choices', []))
                    widget.setCurrentText(setting.get('default', ''))
                elif setting['type'] == 'text':
                    widget = QLineEdit()
                    widget.setText(setting.get('default', ''))
                else:
                    continue
                
                if 'tooltip' in setting:
                    widget.setToolTip(setting['tooltip'])
                
                settings_layout.addWidget(widget, row, 1)
                self.setting_widgets[setting['key']] = widget
                
                # Connect change signals
                if isinstance(widget, QCheckBox):
                    widget.stateChanged.connect(self._on_config_changed)
                elif isinstance(widget, QSpinBox):
                    widget.valueChanged.connect(self._on_config_changed)
                elif isinstance(widget, QComboBox):
                    widget.currentTextChanged.connect(self._on_config_changed)
                elif isinstance(widget, QLineEdit):
                    widget.textChanged.connect(self._on_config_changed)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Statistics
        if hasattr(self.module, 'get_statistics'):
            stats_group = QGroupBox("Statistics")
            stats_layout = QVBoxLayout()
            
            stats = self.module.get_statistics()
            for key, value in stats.items():
                stats_layout.addWidget(QLabel(f"{key}: {value}"))
            
            stats_group.setLayout(stats_layout)
            layout.addWidget(stats_group)
        
        # Actions
        if hasattr(self.module, 'get_actions'):
            actions_group = QGroupBox("Actions")
            actions_layout = QHBoxLayout()
            
            actions = self.module.get_actions()
            for action in actions:
                btn = QPushButton(action['label'])
                btn.clicked.connect(action['callback'])
                if 'tooltip' in action:
                    btn.setToolTip(action['tooltip'])
                actions_layout.addWidget(btn)
            
            actions_layout.addStretch()
            actions_group.setLayout(actions_layout)
            layout.addWidget(actions_group)
        
        # Cache control
        if hasattr(self.module, 'clear_cache'):
            cache_group = QGroupBox("Cache")
            cache_layout = QHBoxLayout()
            
            clear_cache_btn = QPushButton("Clear Cache")
            clear_cache_btn.clicked.connect(self._clear_cache)
            cache_layout.addWidget(clear_cache_btn)
            
            cache_layout.addStretch()
            cache_group.setLayout(cache_layout)
            layout.addWidget(cache_group)
        
        # Add stretch at the end
        layout.addStretch()
        
        # Connect enabled toggle
        self.enabled_check.stateChanged.connect(self._on_config_changed)
        
        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #f5f5f5;
            }
            QCheckBox {
                spacing: 8px;
            }
            QSpinBox, QComboBox, QLineEdit {
                padding: 4px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)

    def _on_config_changed(self):
        """Handle any configuration change"""
        config = self.get_config()
        self.configChanged.emit(self.module_name, config)
        
    def get_config(self) -> dict:
        """Get current module configuration"""
        config = {
            'enabled': self.enabled_check.isChecked()
        }
        
        for key, widget in self.setting_widgets.items():
            if isinstance(widget, QCheckBox):
                config[key] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                config[key] = widget.value()
            elif isinstance(widget, QComboBox):
                config[key] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                config[key] = widget.text()
                
        return config

    def load_config(self, config: dict):
        """Load configuration into widgets"""
        self.enabled_check.setChecked(config.get('enabled', True))
        
        for key, widget in self.setting_widgets.items():
            if key in config:
                if isinstance(widget, QCheckBox):
                    widget.setChecked(config[key])
                elif isinstance(widget, QSpinBox):
                    widget.setValue(config[key])
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(config[key])
                elif isinstance(widget, QLineEdit):
                    widget.setText(config[key])

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
    """Main modules configuration page"""
    configChanged = pyqtSignal(dict)  # All module configs
    
    def __init__(self):
        super().__init__()
        self.module_widgets = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Controls
        controls = QHBoxLayout()
        
        # Global enable/disable
        enable_all = QPushButton("Enable All")
        disable_all = QPushButton("Disable All")
        enable_all.clicked.connect(self._enable_all_modules)
        disable_all.clicked.connect(self._disable_all_modules)
        controls.addWidget(enable_all)
        controls.addWidget(disable_all)
        
        # Cache controls
        clear_all_cache = QPushButton("Clear All Caches")
        clear_all_cache.clicked.connect(self._clear_all_caches)
        controls.addWidget(clear_all_cache)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Container for modules
        container = QWidget()
        self.modules_layout = QVBoxLayout(container)
        
        # Add module widgets
        for module_name, module in available_modules.items():
            widget = ModuleConfigWidget(module_name, module)
            widget.configChanged.connect(self._on_module_config_changed)
            self.module_widgets[module_name] = widget
            self.modules_layout.addWidget(widget)
        
        self.modules_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Apply styles
        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background: white;
            }
            QPushButton:hover {
                background: #f5f5f5;
                border-color: #2196f3;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

    def _enable_all_modules(self):
        """Enable all modules"""
        for widget in self.module_widgets.values():
            widget.enabled_check.setChecked(True)

    def _disable_all_modules(self):
        """Disable all modules"""
        for widget in self.module_widgets.values():
            widget.enabled_check.setChecked(False)

    def _clear_all_caches(self):
        """Clear caches for all modules"""
        try:
            for module_name, widget in self.module_widgets.items():
                if hasattr(widget.module, 'clear_cache'):
                    widget.module.clear_cache()
            
            QMessageBox.information(
                self,
                "Success",
                "All module caches cleared successfully"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to clear some caches: {str(e)}"
            )

    def _on_module_config_changed(self, module_name: str, config: dict):
        """Handle module configuration changes"""
        configs = self.get_all_configs()
        self.configChanged.emit(configs)

    def get_all_configs(self) -> dict:
        """Get configurations for all modules"""
        return {
            name: widget.get_config()
            for name, widget in self.module_widgets.items()
        }

    def load_configs(self, configs: dict):
        """Load configurations for all modules"""
        for module_name, config in configs.items():
            if module_name in self.module_widgets:
                self.module_widgets[module_name].load_config(config)

    def save_configs(self) -> dict:
        """Save current configurations"""
        return self.get_all_configs()

    def validate_configs(self) -> tuple[bool, str]:
        """Validate all module configurations"""
        for module_name, widget in self.module_widgets.items():
            config = widget.get_config()
            if hasattr(widget.module, 'validate_config'):
                valid, message = widget.module.validate_config(config)
                if not valid:
                    return False, f"Invalid configuration for {module_name}: {message}"
        return True, ""