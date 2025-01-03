from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPainter, QPainterPath, QColor
from utils.icons import IconRegistry, ModuleIcon
from typing import Dict, List, Any

class ModuleButton(QPushButton):
    def __init__(self, name: str, icon_name: str, description: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.description = description
        self.setIcon(ModuleIcon(icon_name))
        self.setIconSize(QSize(24, 24))
        self.setFixedSize(40, 40)
        self.setToolTip(f"{name}\n{description}")
        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QPushButton {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 20px;
                padding: 8px;
            }
            QPushButton:hover {
                background: #f5f5f5;
                border-color: #2196f3;
            }
            QPushButton:pressed {
                background: #e3f2fd;
            }
        """)

class ModuleGroupWidget(QFrame):
    moduleSelected = pyqtSignal(str)  # Emits module name

    def __init__(self, title: str, modules: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.title = title
        self.modules = modules
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        layout.addWidget(title_label)

        # Module buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        for module in self.modules:
            btn = ModuleButton(
                module['name'],
                module.get('icon_name', 'search'),
                module.get('description', '')
            )
            btn.clicked.connect(lambda x, m=module['name']: 
                              self.moduleSelected.emit(m))
            buttons_layout.addWidget(btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        self.setStyleSheet("""
            ModuleGroupWidget {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)


class QuickAccessMenu(QWidget):
    moduleSelected = pyqtSignal(str)  # Emits module name

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | 
                          Qt.NoDropShadowWindowHint)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Content widget
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)

        # Add module groups
        self._add_module_groups()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Apply styles
        self.setStyleSheet("""
            QuickAccessMenu {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
            }
            QScrollArea {
                background: transparent;
            }
            QWidget#content {
                background: transparent;
            }
        """)

    def _add_module_groups(self):
        # Research group
        research_modules = [
            {
                'name': 'Concepts',
                'icon_name': 'concept',
                'description': 'Search concepts and relationships'
            },
            {
                'name': 'Chemistry',
                'icon_name': 'chemistry',
                'description': 'Chemical structures and reactions'
            }
        ]
        research_group = ModuleGroupWidget('Research', research_modules)
        research_group.moduleSelected.connect(self.moduleSelected.emit)
        self.content_layout.addWidget(research_group)

        # Language group
        language_modules = [
            {
                'name': 'Nearby Words',
                'icon_name': 'words',
                'description': 'Find related words'
            },
            {
                'name': 'Spelling',
                'icon_name': 'spelling',
                'description': 'Check spelling and suggestions'
            }
        ]
        language_group = ModuleGroupWidget('Language', language_modules)
        language_group.moduleSelected.connect(self.moduleSelected.emit)
        self.content_layout.addWidget(language_group)

        # Add stretch at the end
        self.content_layout.addStretch()

    def showEvent(self, event):
        super().showEvent(event)
        # Apply drop shadow effect
        self.setGraphicsEffect(self._create_shadow_effect())

    def hideEvent(self, event):
        super().hideEvent(event)
        self.setGraphicsEffect(None)

    def _create_shadow_effect(self):
        effect = QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(20)
        effect.setXOffset(0)
        effect.setYOffset(2)
        effect.setColor(QColor(0, 0, 0, 50))
        return effect

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 12, 12)

        painter.fillPath(path, QColor('white'))

        # Draw border
        painter.setPen(QPen(QColor('#e0e0e0'), 1))
        painter.drawPath(path)

    def show_at_button(self, button: QWidget):
        """Show the menu below the specified button"""
        pos = button.mapToGlobal(QPoint(0, button.height()))
        self.move(pos)
        self.show()
        self.raise_()
        self.activateWindow()

    def focusOutEvent(self, event):
        self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)