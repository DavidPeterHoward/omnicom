from PyQt5.QtWidgets import (QListWidget, QListWidgetItem, QStyledItemDelegate,
                           QStyle, QApplication)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath, QFontMetrics
from typing import Optional
from components.loading_indicator import LoadingIndicator, SearchingIndicator

class ResultItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.margin = 8
        self.icon_size = 24
        self.corner_radius = 4

    def sizeHint(self, option, index):
        text = index.data()
        if not text:
            return QSize(0, 0)
            
        fm = QApplication.fontMetrics()
        lines = text.split('\n')
        
        width = option.rect.width() - (self.margin * 2)
        if index.data(Qt.DecorationRole):
            width -= self.icon_size + self.margin
            
        height = 0
        for line in lines:
            line_rect = fm.boundingRect(0, 0, width, 1000,
                                      Qt.TextWordWrap, line)
            height += line_rect.height()
            
        return QSize(option.rect.width(),
                    height + (self.margin * 2))

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw selection/hover background
        if option.state & QStyle.State_Selected:
            color = QColor("#e3f2fd")
            text_color = QColor("#1976d2")
        elif option.state & QStyle.State_MouseOver:
            color = QColor("#f5f5f5")
            text_color = QColor("#000000")
        else:
            color = QColor("#ffffff")
            text_color = QColor("#000000")

        path = QPainterPath()
        path.addRoundedRect(QRect(option.rect), self.corner_radius, self.corner_radius)
        painter.fillPath(path, color)

        # Draw icon if present
        icon = index.data(Qt.DecorationRole)
        icon_rect = QRect()
        if icon:
            icon_rect = QRect(option.rect.left() + self.margin,
                            option.rect.top() + self.margin,
                            self.icon_size, self.icon_size)
            icon.paint(painter, icon_rect)

        # Draw text
        text = index.data()
        if text:
            painter.setPen(text_color)
            text_rect = option.rect.adjusted(
                self.margin + (icon_rect.width() + self.margin if icon else 0),
                self.margin,
                -self.margin,
                -self.margin
            )
            painter.drawText(text_rect, Qt.AlignLeft | Qt.TextWordWrap, text)

        painter.restore()

class EnhancedResultsWidget(QListWidget):
    item_selected = pyqtSignal(QListWidgetItem)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.NoFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Set custom delegate
        self.setItemDelegate(ResultItemDelegate(self))
        
        # Loading indicators
        self.loading_indicator = LoadingIndicator(self)
        self.searching_indicator = SearchingIndicator(self)
        self._update_indicators_position()
        
        # Connect signals
        self.itemClicked.connect(self.item_selected.emit)
        
        self._apply_styles()

    def _apply_styles(self):
        self.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                outline: none;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px 4px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f5f5f5;
                width: 8px;
                margin: 4px 0;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #e0e0e0;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #bdbdbd;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                border: none;
                background: none;
            }
        """)

    def show_loading(self, module_name: Optional[str] = None):
        self.loading_indicator.start()
        if module_name:
            self.searching_indicator.start(module_name)
        self._update_indicators_position()

    def hide_loading(self):
        self.loading_indicator.stop()
        self.searching_indicator.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_indicators_position()

    def _update_indicators_position(self):
        # Position loading indicator in the top-right corner
        self.loading_indicator.move(
            self.width() - self.loading_indicator.width() - 8,
            8
        )
        # Position searching indicator in the top-center
        self.searching_indicator.move(
            (self.width() - self.searching_indicator.width()) // 2,
            8
        )

    def showEvent(self, event):
        super().showEvent(event)
        # Apply drop shadow effect
        self.setGraphicsEffect(self._create_shadow_effect())

    def hideEvent(self, event):
        super().hideEvent(event)
        self.setGraphicsEffect(None)
        self.hide_loading()

    def _create_shadow_effect(self):
        effect = QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(20)
        effect.setXOffset(0)
        effect.setYOffset(2)
        effect.setColor(QColor(0, 0, 0, 50))
        return effect

    def update_max_height(self, available_height: int):
        """Update maximum height based on content and available space"""
        total_height = 0
        for i in range(self.count()):
            item = self.item(i)
            total_height += self.sizeHintForRow(i)
        
        padding = 8  # Account for padding
        scrollbar_height = 0
        if self.verticalScrollBar().isVisible():
            scrollbar_height = self.verticalScrollBar().height()
        
        max_height = min(total_height + padding + scrollbar_height,
                        available_height)
        self.setMaximumHeight(max_height)