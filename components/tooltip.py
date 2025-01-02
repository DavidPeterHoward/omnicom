from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                             QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtProperty, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QFontMetrics
from typing import Optional, Dict, Any
import json
from pathlib import Path


class EnhancedTooltip(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.BypassWindowManagerHint)
        self.setText("")
        self._setup_ui()
        self._setup_animations()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 6, 8, 6)
        
        # Main content label
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.RichText)
        self.layout.addWidget(self.label)
        
        # Apply styles
        self.setStyleSheet("""
            EnhancedTooltip {
                background: #424242;
                border-radius: 6px;
            }
            QLabel {
                color: white;
                font-size: 12px;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.setGraphicsEffect(shadow)

    def _setup_animations(self):
        # Opacity animation
        self._opacity = 0.0
        self.opacity_anim = QPropertyAnimation(self, b"opacity")
        self.opacity_anim.setDuration(200)
        self.opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        # Timer for delayed show
        self.show_timer = QTimer(self)
        self.show_timer.setSingleShot(True)
        self.show_timer.timeout.connect(self._do_show)
        
        # Timer for delayed hide
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._do_hide)

    @pyqtProperty(float)
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.update()

    def setText(self, text: str):
        self.label.setText(text)
        self.adjustSize()

    def showDelayed(self, pos: QPoint, delay: int = 500):
        """Show tooltip with delay"""
        self.target_pos = pos
        self.show_timer.start(delay)
        self.hide_timer.stop()

    def hideDelayed(self, delay: int = 200):
        """Hide tooltip with delay"""
        self.hide_timer.start(delay)
        self.show_timer.stop()

    def _do_show(self):
        """Perform show animation"""
        if not self.isVisible():
            # Position tooltip
            self.move(self._calculate_position(self.target_pos))
            self.show()
            
            # Start fade in
            self.opacity_anim.setStartValue(0.0)
            self.opacity_anim.setEndValue(1.0)
            self.opacity_anim.start()

    def _do_hide(self):
        """Perform hide animation"""
        if self.isVisible():
            # Start fade out
            self.opacity_anim.setStartValue(self.opacity)
            self.opacity_anim.setEndValue(0.0)
            self.opacity_anim.finished.connect(self.hide)
            self.opacity_anim.start()

    def _calculate_position(self, pos: QPoint) -> QPoint:
        """Calculate optimal tooltip position"""
        screen = self.screen()
        if not screen:
            return pos
            
        screen_geom = screen.availableGeometry()
        tooltip_size = self.sizeHint()
        
        # Try positions in order: below, above, right, left
        positions = [
            QPoint(pos.x(), pos.y() + 20),  # Below
            QPoint(pos.x(), pos.y() - tooltip_size.height() - 10),  # Above
            QPoint(pos.x() + 20, pos.y()),  # Right
            QPoint(pos.x() - tooltip_size.width() - 10, pos.y())  # Left
        ]
        
        for position in positions:
            rect = QRect(position, tooltip_size)
            if screen_geom.contains(rect):
                return position
                
        # If no position is perfect, default to below but ensure within screen
        x = max(screen_geom.left(), min(pos.x(), screen_geom.right() - tooltip_size.width()))
        y = max(screen_geom.top(), min(pos.y() + 20, screen_geom.bottom() - tooltip_size.height()))
        return QPoint(x, y)

    def paintEvent(self, event):
        """Custom paint for smooth corners and opacity"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create path for rounded rectangle
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 6, 6)
        
        # Set opacity
        painter.setOpacity(self._opacity)
        
        # Draw background
        painter.fillPath(path, QColor("#424242"))

class TooltipManager:
    """Manages tooltips throughout the application"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TooltipManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.tooltips = {}
        self.current_tooltip = None
        self._load_tooltips()

    def _load_tooltips(self):
        """Load tooltip definitions from configuration"""
        config_path = Path.home() / '.omnibar' / 'tooltips.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    self.tooltips = json.load(f)
            except Exception as e:
                print(f"Error loading tooltips: {e}")

    def register_tooltip(self, widget: QWidget, text: str):
        """Register a tooltip for a widget"""
        widget.setMouseTracking(True)
        widget.enterEvent = lambda e: self.show_tooltip(widget, text)
        widget.leaveEvent = lambda e: self.hide_tooltip()

    def show_tooltip(self, widget: QWidget, text: str):
        """Show tooltip for widget"""
        # Create tooltip if needed
        if not self.current_tooltip:
            self.current_tooltip = EnhancedTooltip()
        
        # Update text and show
        self.current_tooltip.setText(text)
        pos = widget.mapToGlobal(QPoint(0, widget.height()))
        self.current_tooltip.showDelayed(pos)

    def hide_tooltip(self):
        """Hide current tooltip"""
        if self.current_tooltip:
            self.current_tooltip.hideDelayed()

    def update_tooltip(self, widget: QWidget, text: str):
        """Update existing tooltip text"""
        if widget in self.tooltips:
            self.tooltips[widget] = text
            if self.current_tooltip and self.current_tooltip.parent() == widget:
                self.current_tooltip.setText(text)

    def clear_tooltips(self):
        """Clear all tooltips"""
        self.tooltips.clear()
        if self.current_tooltip:
            self.current_tooltip.hide()
            self.current_tooltip.deleteLater()
            self.current_tooltip = None