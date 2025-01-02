from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QComboBox, QSpinBox, QGroupBox,
                           QFontComboBox, QCheckBox, QColorDialog, QPushButton)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt

class AppearancePage(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Fonts Group
        fonts_group = QGroupBox("Font Settings")
        fonts_layout = QVBoxLayout()
        
        # Font family
        family_layout = QHBoxLayout()
        family_label = QLabel("Font Family:")
        self.font_family = QFontComboBox()
        family_layout.addWidget(family_label)
        family_layout.addWidget(self.font_family)
        family_layout.addStretch()
        
        # Font sizes
        sizes_layout = QHBoxLayout()
        self.input_font_size = QSpinBox()
        self.input_font_size.setRange(8, 24)
        self.results_font_size = QSpinBox()
        self.results_font_size.setRange(8, 24)
        
        sizes_layout.addWidget(QLabel("Input Size:"))
        sizes_layout.addWidget(self.input_font_size)
        sizes_layout.addSpacing(20)
        sizes_layout.addWidget(QLabel("Results Size:"))
        sizes_layout.addWidget(self.results_font_size)
        sizes_layout.addStretch()
        
        fonts_layout.addLayout(family_layout)
        fonts_layout.addLayout(sizes_layout)
        fonts_group.setLayout(fonts_layout)
        
        # Colors Group
        colors_group = QGroupBox("Colors")
        colors_layout = QVBoxLayout()
        
        # Theme selection
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        colors_layout.addLayout(theme_layout)
        
        # Custom colors
        self.accent_color_btn = QPushButton("Accent Color")
        self.accent_color_btn.clicked.connect(self._choose_accent_color)
        self.accent_color = QColor("#2196f3")  # Default blue
        
        colors_layout.addWidget(self.accent_color_btn)
        colors_group.setLayout(colors_layout)
        
        # Window Group
        window_group = QGroupBox("Window Settings")
        window_layout = QVBoxLayout()
        
        self.show_shadow = QCheckBox("Show Window Shadow")
        self.blur_bg = QCheckBox("Blur Background (if supported)")
        window_layout.addWidget(self.show_shadow)
        window_layout.addWidget(self.blur_bg)
        
        # Window size
        size_layout = QHBoxLayout()
        self.window_width = QSpinBox()
        self.window_width.setRange(400, 1200)
        self.window_height = QSpinBox()
        self.window_height.setRange(40, 200)
        
        size_layout.addWidget(QLabel("Width:"))
        size_layout.addWidget(self.window_width)
        size_layout.addSpacing(20)
        size_layout.addWidget(QLabel("Height:"))
        size_layout.addWidget(self.window_height)
        size_layout.addStretch()
        
        window_layout.addLayout(size_layout)
        window_group.setLayout(window_layout)
        
        # Add all groups to main layout
        layout.addWidget(fonts_group)
        layout.addWidget(colors_group)
        layout.addWidget(window_group)
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
            QSpinBox, QComboBox, QFontComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """
        self.setStyleSheet(style)

    def _choose_accent_color(self):
        color = QColorDialog.getColor(self.accent_color, self, "Choose Accent Color")
        if color.isValid():
            self.accent_color = color
            self.accent_color_btn.setStyleSheet(
                f"background-color: {color.name()};"
                f"color: {'white' if color.lightness() < 128 else 'black'};"
            )

    def load_settings(self, config):
        self.font_family.setCurrentFont(QFont(config.get('font_family', 'Segoe UI')))
        self.input_font_size.setValue(config.get('input_font_size', 11))
        self.results_font_size.setValue(config.get('results_font_size', 10))
        self.theme_combo.setCurrentText(config.get('theme', 'Light'))
        self.show_shadow.setChecked(config.get('show_shadow', True))
        self.blur_bg.setChecked(config.get('blur_background', False))
        self.window_width.setValue(config.get('window_width', 650))
        self.window_height.setValue(config.get('window_height', 65))
        
        accent_color = config.get('accent_color', '#2196f3')
        self.accent_color = QColor(accent_color)
        self.accent_color_btn.setStyleSheet(
            f"background-color: {accent_color};"
            f"color: {'white' if self.accent_color.lightness() < 128 else 'black'};"
        )

    def save_settings(self, config):
        config['font_family'] = self.font_family.currentFont().family()
        config['input_font_size'] = self.input_font_size.value()
        config['results_font_size'] = self.results_font_size.value()
        config['theme'] = self.theme_combo.currentText()
        config['show_shadow'] = self.show_shadow.isChecked()
        config['blur_background'] = self.blur_bg.isChecked()
        config['window_width'] = self.window_width.value()
        config['window_height'] = self.window_height.value()
        config['accent_color'] = self.accent_color.name()