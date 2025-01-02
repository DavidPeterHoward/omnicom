from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QPen

class LoadingIndicator(QWidget):
    def __init__(self, parent=None, color=QColor("#2196f3")):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self._angle = 0
        self._color = color
        self._speed = 80  # Lower = faster
        
        self.animation = QPropertyAnimation(self, b"rotation")
        self.animation.setDuration(2000)
        self.animation.setStartValue(0)
        self.animation.setEndValue(360)
        self.animation.setLoopCount(-1)  # Infinite loop
        self.animation.setEasingCurve(QEasingCurve.Linear)
        
        self._is_spinning = False
        self.hide()

    @pyqtProperty(float)
    def rotation(self):
        return self._angle

    @rotation.setter
    def rotation(self, angle):
        self._angle = angle
        self.update()

    def start(self):
        self.show()
        self._is_spinning = True
        self.animation.start()

    def stop(self):
        self._is_spinning = False
        self.animation.stop()
        self.hide()

    def paintEvent(self, event):
        if not self._is_spinning:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Save current state
        painter.save()

        # Move to center and rotate
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)

        # Draw spinning arc
        pen = QPen(self._color)
        pen.setWidth(2)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        # Draw arc with gap
        rect = self.rect().adjusted(2, 2, -2, -2)
        rect.moveCenter(rect.center() - rect.topLeft())
        
        # Draw multiple segments with varying opacity
        for i in range(8):
            opacity = 0.2 + (i * 0.1)  # 0.2 to 0.9
            self._color.setAlphaF(opacity)
            pen.setColor(self._color)
            painter.setPen(pen)
            
            start_angle = (i * 45) * 16
            span_angle = 30 * 16
            painter.drawArc(rect, start_angle, span_angle)

        # Restore state
        painter.restore()

class SearchingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._animation_step = 0
        self._active = False
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_animation)
        self._dots = ['.'] * 3
        
    def _setup_ui(self):
        self.setFixedHeight(24)
        self.setStyleSheet("""
            SearchingIndicator {
                background: transparent;
                color: #666;
                font-size: 12px;
            }
        """)
        self.hide()

    def start(self, module_name: str = ''):
        self._active = True
        self.module_name = module_name
        self._timer.start(300)  # Update every 300ms
        self.show()

    def stop(self):
        self._active = False
        self._timer.stop()
        self.hide()

    def _update_animation(self):
        if not self._active:
            return
            
        self._animation_step = (self._animation_step + 1) % 4
        self._dots = ['.'] * 3
        for i in range(self._animation_step):
            self._dots[i] = '•'
        
        self.update()

    def paintEvent(self, event):
        if not self._active:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw text
        text = f"Searching{self.module_name and ' ' + self.module_name}{''.join(self._dots)}"
        painter.setPen(QColor("#666"))
        painter.drawText(self.rect(), Qt.AlignLeft | Qt.AlignVCenter, text)

class ProgressIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(2)  # Thin line
        self._progress = 0
        self._active = False
        self._color = QColor("#2196f3")
        
        self.animation = QPropertyAnimation(self, b"progress")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.hide()

    @pyqtProperty(float)
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        self._progress = max(0, min(value, 100))
        self.update()

    def start(self):
        self._active = True
        self.progress = 0
        self.show()

    def stop(self):
        self._active = False
        self.animation.setEndValue(100)
        self.animation.finished.connect(self.hide)
        self.animation.start()

    def set_progress(self, value):
        if not self._active:
            return
            
        self.animation.setEndValue(value)
        self.animation.start()

    def paintEvent(self, event):
        if not self._active and self._progress == 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background
        painter.fillRect(self.rect(), QColor("#f5f5f5"))

        # Draw progress
        width = int(self.width() * (self._progress / 100))
        if width > 0:
            progress_rect = self.rect()
            progress_rect.setWidth(width)
            painter.fillRect(progress_rect, self._color)