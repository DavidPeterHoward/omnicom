from PyQt5.QtWidgets import (QScrollBar, QStyleOptionSlider, QStyle, 
                           QWidget, QApplication)
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QSize
from PyQt5.QtGui import QPainter, QColor, QPainterPath

class ModernScrollBar(QScrollBar):
    """Modern-looking scrollbar with smooth animations and hover effects"""
    
    def __init__(self, orientation=Qt.Vertical, parent=None):
        super().__init__(orientation, parent)
        self._pressed = False
        self._hover = False
        self._hover_progress = 0
        
        # Customize appearance
        self.setFixedWidth(8 if orientation == Qt.Vertical else -1)
        self.setFixedHeight(-1 if orientation == Qt.Vertical else 8)
        self._update_stylesheet()

    def _update_stylesheet(self):
        self.setStyleSheet("""
            QScrollBar {
                background: transparent;
                margin: 0;
            }
            QScrollBar::add-line, QScrollBar::sub-line,
            QScrollBar::add-page, QScrollBar::sub-page {
                background: none;
                border: none;
                height: 0;
                width: 0;
            }
        """)

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._pressed = True
        self.update()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._pressed = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Get the scrollbar metrics
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        
        # Get the dimensions of the scrollbar
        rect = self.rect()
        mid_height = rect.height() / 2.0 if self.orientation() == Qt.Vertical else rect.width() / 2.0
        
        # Calculate handle position and size
        control_height = rect.height() if self.orientation() == Qt.Vertical else rect.width()
        range_size = self.maximum() - self.minimum()
        
        if range_size == 0:
            handle_size = control_height
            handle_pos = 0
        else:
            page_step = self.pageStep()
            visible_size = min(page_step * control_height / (range_size + page_step), control_height)
            handle_size = max(visible_size, 20)  # Minimum handle size
            
            value_range = range_size + page_step - handle_size
            value_pixel_ratio = (control_height - handle_size) / value_range
            handle_pos = (self.value() - self.minimum()) * value_pixel_ratio

        # Determine colors based on state
        if self._pressed:
            bg_color = QColor("#1976d2")
            bg_opacity = 0.3
            handle_color = QColor("#1976d2")
            handle_opacity = 1.0
        elif self._hover:
            bg_color = QColor("#2196f3")
            bg_opacity = 0.2
            handle_color = QColor("#2196f3")
            handle_opacity = 0.8
        else:
            bg_color = QColor("#757575")
            bg_opacity = 0.1
            handle_color = QColor("#757575")
            handle_opacity = 0.4

        # Draw background track
        track_path = QPainterPath()
        if self.orientation() == Qt.Vertical:
            track_path.addRoundedRect(
                rect.right() - 8, rect.top(),
                8, rect.height(),
                4, 4
            )
        else:
            track_path.addRoundedRect(
                rect.left(), rect.bottom() - 8,
                rect.width(), 8,
                4, 4
            )
            
        bg_color.setAlphaF(bg_opacity)
        painter.fillPath(track_path, bg_color)

        # Draw handle
        handle_path = QPainterPath()
        if self.orientation() == Qt.Vertical:
            handle_path.addRoundedRect(
                rect.right() - 6, handle_pos,
                6, handle_size,
                3, 3
            )
        else:
            handle_path.addRoundedRect(
                handle_pos, rect.bottom() - 6,
                handle_size, 6,
                3, 3
            )
            
        handle_color.setAlphaF(handle_opacity)
        painter.fillPath(handle_path, handle_color)

    def sizeHint(self):
        return QSize(8, super().sizeHint().height())

class ModernScrollArea(QWidget):
    """Custom scroll area with modern scrollbars"""
    
    scrolled = pyqtSignal(int, int)  # x, y positions
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        self.vertical_scroll = ModernScrollBar(Qt.Vertical, self)
        self.horizontal_scroll = ModernScrollBar(Qt.Horizontal, self)
        
        # Connect signals
        self.vertical_scroll.valueChanged.connect(
            lambda: self.scrolled.emit(
                self.horizontal_scroll.value(),
                self.vertical_scroll.value()
            )
        )
        self.horizontal_scroll.valueChanged.connect(
            lambda: self.scrolled.emit(
                self.horizontal_scroll.value(),
                self.vertical_scroll.value()
            )
        )
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scrollbar_geometry()
        
    def _update_scrollbar_geometry(self):
        rect = self.rect()
        scrollbar_width = self.vertical_scroll.sizeHint().width()
        scrollbar_height = self.horizontal_scroll.sizeHint().height()
        
        # Position vertical scrollbar
        self.vertical_scroll.setGeometry(
            rect.right() - scrollbar_width,
            rect.top(),
            scrollbar_width,
            rect.height() - scrollbar_height
        )
        
        # Position horizontal scrollbar
        self.horizontal_scroll.setGeometry(
            rect.left(),
            rect.bottom() - scrollbar_height,
            rect.width() - scrollbar_width,
            scrollbar_height
        )
        
    def set_ranges(self, h_min: int, h_max: int, v_min: int, v_max: int):
        """Set scrollbar ranges"""
        self.horizontal_scroll.setRange(h_min, h_max)
        self.vertical_scroll.setRange(v_min, v_max)
        
    def set_page_steps(self, h_step: int, v_step: int):
        """Set scrollbar page steps"""
        self.horizontal_scroll.setPageStep(h_step)
        self.vertical_scroll.setPageStep(v_step)
        
    def get_scroll_positions(self) -> tuple[int, int]:
        """Get current scroll positions"""
        return (self.horizontal_scroll.value(),
                self.vertical_scroll.value())
                
    def set_scroll_positions(self, x: int, y: int):
        """Set scroll positions"""
        self.horizontal_scroll.setValue(x)
        self.vertical_scroll.setValue(y)