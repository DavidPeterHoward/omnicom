from typing import Dict, Optional
from PyQt5.QtGui import QIcon, QPainter, QColor, QPainterPath
from PyQt5.QtCore import Qt, QSize, QRect, QPoint
from PyQt5.QtSvg import QSvgRenderer
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class IconInfo:
    name: str
    svg_path: str
    color: str = "#2196f3"
    size: int = 24
    

class IconRegistry:
    _instance = None
    _icons: Dict[str, IconInfo] = {
        'search': IconInfo('search', 'M15.5 14h-.79l-.28-.27a6.5 6.5 0 0 0 1.48-5.34c-.47-2.78-2.79-5-5.59-5.34a6.505 6.505 0 0 0-7.27 7.27c.34 2.8 2.56 5.12 5.34 5.59a6.5 6.5 0 0 0 5.34-1.48l.27.28v.79l4.25 4.25c.41.41 1.08.41 1.49 0 .41-.41.41-1.08 0-1.49L15.5 14zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z'),
        'settings': IconInfo('settings', 'M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z'),
        'close': IconInfo('close', 'M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z'),
        'chemistry': IconInfo('chemistry', 'M7 2v2h1v14c0 2.2 1.8 4 4 4s4-1.8 4-4V4h1V2H7zm5 18c-1.1 0-2-.9-2-2V4h4v14c0 1.1-.9 2-2 2z'),
        'concept': IconInfo('concept', 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z'),
        'spelling': IconInfo('spelling', 'M12.45 16h2.09L9.43 3H7.57L2.46 16h2.09l1.12-3h5.64l1.14 3zm-6.02-5L8.5 5.48 10.57 11H6.43zm15.16.59l-8.09 8.09L9.83 16l-1.41 1.41 5.09 5.09L23 13l-1.41-1.41z'),
        'words': IconInfo('words', 'M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0-2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9H9V9h10v2zm-4 4H9v-2h6v2zm4-8H9V5h10v2z'),
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IconRegistry, cls).__new__(cls)
            cls._instance._init_icons()
        return cls._instance

    def _init_icons(self):
        # Load custom icons if available
        custom_icons_file = Path.home() / '.omnibar' / 'icons.json'
        if custom_icons_file.exists():
            try:
                with open(custom_icons_file, 'r') as f:
                    custom_icons = json.load(f)
                for name, data in custom_icons.items():
                    self._icons[name] = IconInfo(**data)
            except Exception as e:
                print(f"Error loading custom icons: {e}")

    def get_qicon(self, name: str, color: Optional[str] = None, size: Optional[int] = None) -> QIcon:
        if name not in self._icons:
            return QIcon()

        icon_info = self._icons[name]
        icon_size = size or icon_info.size
        icon_color = color or icon_info.color

        # Create SVG renderer
        renderer = QSvgRenderer()
        svg_data = f'''
            <svg xmlns="http://www.w3.org/2000/svg" 
                 width="{icon_size}" height="{icon_size}" 
                 viewBox="0 0 24 24">
                <path fill="{icon_color}" d="{icon_info.svg_path}"/>
            </svg>
        '''
        renderer.load(bytes(svg_data, 'utf-8'))

        # Create icon
        icon = QIcon()
        for s in [16, 24, 32, 48]:  # Common icon sizes
            pixmap = renderer.createPixmap(QSize(s, s))
            icon.addPixmap(pixmap)

        return icon

    def register_icon(self, name: str, svg_path: str, color: str = "#2196f3", size: int = 24):
        self._icons[name] = IconInfo(name, svg_path, color, size)

    def get_all_icons(self) -> Dict[str, IconInfo]:
        return self._icons.copy()

class ModuleIcon(QIcon):
    def __init__(self, name: str, color: str = "#2196f3", size: int = 24):
        super().__init__()
        self.registry = IconRegistry()
        self.qicon = self.registry.get_qicon(name, color, size)
        
    def paint(self, painter: QPainter, rect: QRect, alignment: Qt.Alignment = Qt.AlignCenter):
        self.qicon.paint(painter, rect, alignment)