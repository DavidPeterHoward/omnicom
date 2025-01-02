from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QComboBox, QSpinBox, QFontComboBox,
                             QCheckBox, QColorDialog, QPushButton, QSlider)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt


class ColorButton(QPushButton):
    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(40, 40)
        self._update_style()

    def _update_style(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color.name()};
                border: 1px solid #ccc;
                border-radius: 20px;
            }}
            QPushButton:hover {{
                border: 2px solid #2196f3;
            }}
        """)

    @property
    def color(self) -> QColor:
        return self._color

    @color.setter
    def color(self, value: QColor):
        self._color = value
        self._update_style()


class AppearancePage(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Theme Group
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout()
        
        # Theme selection
        theme_row = QHBoxLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        theme_row.addWidget(QLabel("Theme:"))
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch()
        theme_layout.addLayout(theme_row)
        
        # Colors
        colors_layout = QHBoxLayout()
        
        # Primary color
        primary_layout = QVBoxLayout()
        primary_layout.addWidget(QLabel("Primary Color"))
        self.primary_color_btn = ColorButton(QColor("#2196f3"))
        self.primary_color_btn.clicked.connect(
            lambda: self._choose_color(self.primary_color_btn)
        )
        primary_layout.addWidget(self.primary_color_btn, alignment=Qt.AlignCenter)
        colors_layout.addLayout(primary_layout)
        
        # Accent color
        accent_layout = QVBoxLayout()
        accent_layout.addWidget(QLabel("Accent Color"))
        self.accent_color_btn = ColorButton(QColor("#1976d2"))
        self.accent_color_btn.clicked.connect(
            lambda: self._choose_color(self.accent_color_btn)
        )
        accent_layout.addWidget(self.accent_color_btn, alignment=Qt.AlignCenter)
        colors_layout.addLayout(accent_layout)
        
        colors_layout.addStretch()
        theme_layout.addLayout(colors_layout)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Fonts Group
        fonts_group = QGroupBox("Fonts")
        fonts_layout = QVBoxLayout()
        
        # Font family
        family_layout = QHBoxLayout()
        self.font_family = QFontComboBox()
        family_layout.addWidget(QLabel("Font Family:"))
        family_layout.addWidget(self.font_family)
        family_layout.addStretch()
        fonts_layout.addLayout(family_layout)
        
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
        fonts_layout.addLayout(sizes_layout)
        
        fonts_group.setLayout(fonts_layout)
        layout.addWidget(fonts_group)
        
        # Window Group
        window_group = QGroupBox("Window Appearance")
        window_layout = QVBoxLayout()
        
        # Window effects
        self.show_shadow = QCheckBox("Show Window Shadow")
        self.blur_background = QCheckBox("Blur Background")
        self.animate_transitions = QCheckBox("Animate Transitions")
        
        window_layout.addWidget(self.show_shadow)
        window_layout.addWidget(self.blur_background)
        window_layout.addWidget(self.animate_transitions)
        
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
        
        # Opacity
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Window Opacity:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(50, 100)
        self.opacity_slider.setValue(100)
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("100%")
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_label.setText(f"{v}%")
        )
        opacity_layout.addWidget(self.opacity_label)
        
        window_layout.addLayout(opacity_layout)
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)
        
        # Add stretch at the end
        layout.addStretch()
        
        self._apply_styles()

    def _choose_color(self, button: ColorButton):
        color = QColorDialog.getColor(
            button.color,
            self,
            "Choose Color",
            QColorDialog.ShowAlphaChannel
        )
        if color.isValid():
            button.color = color

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
            QComboBox, QSpinBox, QFontComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QCheckBox {
                spacing: 8px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #ccc;
                margin: 2px 0;
            }
            QSlider::handle:horizontal {
                background: #2196f3;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
        """)

    def _choose_accent_color(self):
        color = QColorDialog.getColor(self.accent_color, self, "Choose Accent Color")
        if color.isValid():
            self.accent_color = color
            self.accent_color_btn.setStyleSheet(
                f"background-color: {color.name()};"
                f"color: {'white' if color.lightness() < 128 else 'black'};"
            )

    def load_settings(self, config: dict):
        self.theme_combo.setCurrentText(config.get('theme', 'Light'))
        self.primary_color_btn.color = QColor(config.get('primary_color', '#2196f3'))
        self.accent_color_btn.color = QColor(config.get('accent_color', '#1976d2'))
        
        self.font_family.setCurrentFont(QFont(config.get('font_family', 'Segoe UI')))
        self.input_font_size.setValue(config.get('input_font_size', 11))
        self.results_font_size.setValue(config.get('results_font_size', 10))
        
        self.show_shadow.setChecked(config.get('show_shadow', True))
        self.blur_background.setChecked(config.get('blur_background', False))
        self.animate_transitions.setChecked(config.get('animate_transitions', True))
        
        self.window_width.setValue(config.get('window_width', 650))
        self.window_height.setValue(config.get('window_height', 65))
        
        self.opacity_slider.setValue(int(config.get('window_opacity', 1.0) * 100))

    def save_settings(self, config: dict):
        config['theme'] = self.theme_combo.currentText()
        config['primary_color'] = self.primary_color_btn.color.name()
        config['accent_color'] = self.accent_color_btn.color.name()
        
        config['font_family'] = self.font_family.currentFont().family()
        config['input_font_size'] = self.input_font_size.value()
        config['results_font_size'] = self.results_font_size.value()
        
        config['show_shadow'] = self.show_shadow.isChecked()
        config['blur_background'] = self.blur_background.isChecked()
        config['animate_transitions'] = self.animate_transitions.isChecked()
        
        config['window_width'] = self.window_width.value()
        config['window_height'] = self.window_height.value()
        
        config['window_opacity'] = self.opacity_slider.value() / 100.0

    def apply_settings(self):
        """Apply settings changes immediately"""
        # Emit signal to notify main window of appearance changes
        window = self.window()
        if window and hasattr(window, 'appearance_changed'):
            window.appearance_changed.emit()