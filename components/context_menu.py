from PyQt5.QtWidgets import (QMenu, QAction, QWidget, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QIcon, QColor, QPainter, QPen
from utils.icons import IconRegistry
from typing import Dict, List, Optional, Callable, Any
import json
from pathlib import Path


class ModernMenuItem:
    def __init__(self, 
                 text: str,
                 icon: Optional[str] = None,
                 shortcut: Optional[str] = None,
                 callback: Optional[Callable] = None,
                 submenu: Optional[List['ModernMenuItem']] = None,
                 checkable: bool = False,
                 checked: bool = False,
                 enabled: bool = True,
                 tooltip: Optional[str] = None):
        self.text = text
        self.icon = icon
        self.shortcut = shortcut
        self.callback = callback
        self.submenu = submenu
        self.checkable = checkable
        self.checked = checked
        self.enabled = enabled
        self.tooltip = tooltip


class ModernContextMenu(QMenu):
    """Modern styled context menu with icons and animations"""
    
    menuTriggered = pyqtSignal(str, dict)  # action_id, data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_registry = IconRegistry()
        self._setup_style()
        self._load_menu_config()
        
    def _setup_style(self):
        """Apply modern styling to the menu"""
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 30px 8px 8px;
                border-radius: 4px;
                margin: 2px 4px;
            }
            QMenu::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QMenu::separator {
                height: 1px;
                background: #e0e0e0;
                margin: 4px 8px;
            }
            QMenu::indicator {
                width: 18px;
                height: 18px;
                margin-left: 8px;
            }
            QMenu::indicator:non-exclusive:checked {
                image: url(check.png);
            }
        """)

    def _load_menu_config(self):
        """Load menu configuration from file"""
        config_path = Path.home() / '.omnibar' / 'menu_config.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    self.menu_config = json.load(f)
            except Exception as e:
                print(f"Error loading menu config: {e}")
                self.menu_config = {}
        else:
            self.menu_config = {}

    def build_menu(self, items: List[ModernMenuItem]):
        """Build menu from list of menu items"""
        self.clear()
        for item in items:
            if item.text == "-":
                self.addSeparator()
                continue
                
            if item.submenu:
                submenu = ModernContextMenu(self)
                submenu.build_menu(item.submenu)
                action = self.addMenu(submenu)
            else:
                action = QAction(item.text, self)
                if item.callback:
                    action.triggered.connect(item.callback)
                self.addAction(action)
            
            if item.icon:
                icon = self.icon_registry.get_qicon(item.icon)
                action.setIcon(icon)
            
            if item.shortcut:
                action.setShortcut(item.shortcut)
                
            if item.tooltip:
                action.setToolTip(item.tooltip)
                
            action.setCheckable(item.checkable)
            if item.checkable:
                action.setChecked(item.checked)
                
            action.setEnabled(item.enabled)

    def popup_at_cursor(self):
        """Show menu at current cursor position"""
        pos = QApplication.desktop().cursor().pos()
        self.popup_at_position(pos)

    def popup_at_position(self, pos: QPoint):
        """Show menu at specific position with bounds checking"""
        screen = QApplication.screenAt(pos)
        if not screen:
            screen = QApplication.primaryScreen()
        
        screen_geom = screen.availableGeometry()
        menu_size = self.sizeHint()
        
        # Adjust position to keep menu on screen
        x = min(pos.x(), screen_geom.right() - menu_size.width())
        y = min(pos.y(), screen_geom.bottom() - menu_size.height())
        
        self.popup(QPoint(x, y))

    def paintEvent(self, event):
        """Custom paint event for modern look"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        bg_color = QColor("white")
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)
        
        # Draw border
        border_color = QColor("#e0e0e0")
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 8, 8)


class ContextMenuManager:
    """Manages context menus throughout the application"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ContextMenuManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.menus: Dict[str, Dict[str, Any]] = {}
        self._load_menus()
        
    def _load_menus(self):
        """Load menu definitions from configuration"""
        config_path = Path.home() / '.omnibar' / 'menus'
        if not config_path.exists():
            return
            
        for menu_file in config_path.glob('*.json'):
            try:
                with open(menu_file, 'r') as f:
                    menu_config = json.load(f)
                    self.menus[menu_file.stem] = menu_config
            except Exception as e:
                print(f"Error loading menu {menu_file}: {e}")
                
    def register_menu(self, menu_id: str, menu_config: Dict[str, Any]):
        """Register a new menu configuration"""
        self.menus[menu_id] = menu_config
        
        # Save to disk
        config_path = Path.home() / '.omnibar' / 'menus'
        config_path.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path / f"{menu_id}.json", 'w') as f:
                json.dump(menu_config, f, indent=2)
        except Exception as e:
            print(f"Error saving menu config: {e}")

    def create_menu(self, menu_id: str, context: Optional[Dict[str, Any]] = None) -> ModernContextMenu:
        """Create a menu instance from registered configuration"""
        if menu_id not in self.menus:
            raise KeyError(f"Menu '{menu_id}' not found")
            
        menu_config = self.menus[menu_id]
        menu = ModernContextMenu()
        
        # Build menu items
        items = self._build_menu_items(menu_config.get('items', []), context)
        menu.build_menu(items)
        
        return menu

    def _build_menu_items(self, 
                         items_config: List[Dict[str, Any]], 
                         context: Optional[Dict[str, Any]] = None) -> List[ModernMenuItem]:
        """Build menu items from configuration"""
        items = []
        
        for item_config in items_config:
            # Skip items that don't match context conditions
            if not self._check_context_conditions(item_config.get('conditions', []), context):
                continue
                
            # Create submenu if present
            submenu = None
            if 'submenu' in item_config:
                submenu = self._build_menu_items(item_config['submenu'], context)
                
            # Create callback if action specified
            callback = None
            if 'action' in item_config:
                action_id = item_config['action']
                callback = lambda aid=action_id: self._handle_action(aid, context)
                
            # Create menu item
            item = ModernMenuItem(
                text=item_config['text'],
                icon=item_config.get('icon'),
                shortcut=item_config.get('shortcut'),
                callback=callback,
                submenu=submenu,
                checkable=item_config.get('checkable', False),
                checked=item_config.get('checked', False),
                enabled=item_config.get('enabled', True),
                tooltip=item_config.get('tooltip')
            )
            
            items.append(item)
            
        return items

    def _check_context_conditions(self, 
                                conditions: List[Dict[str, Any]], 
                                context: Optional[Dict[str, Any]]) -> bool:
        """Check if all conditions match the current context"""
        if not conditions or not context:
            return True
            
        for condition in conditions:
            field = condition.get('field')
            operator = condition.get('operator', 'eq')
            value = condition.get('value')
            
            if not field or field not in context:
                return False
                
            context_value = context[field]
            
            if operator == 'eq' and context_value != value:
                return False
            elif operator == 'ne' and context_value == value:
                return False
            elif operator == 'contains' and value not in context_value:
                return False
            elif operator == 'in' and context_value not in value:
                return False
                
        return True

    def _handle_action(self, action_id: str, context: Optional[Dict[str, Any]] = None):
        """Handle menu action"""
        # Emit signal or call registered handler
        pass

    def show_menu(self, menu_id: str, 
                 position: Optional[QPoint] = None, 
                 context: Optional[Dict[str, Any]] = None):
        """Show a menu at specified position or cursor position"""
        menu = self.create_menu(menu_id, context)
        
        if position:
            menu.popup_at_position(position)
        else:
            menu.popup_at_cursor()

    def update_menu_config(self, menu_id: str, updates: Dict[str, Any]):
        """Update existing menu configuration"""
        if menu_id not in self.menus:
            raise KeyError(f"Menu '{menu_id}' not found")
            
        self.menus[menu_id].update(updates)
        self.register_menu(menu_id, self.menus[menu_id])

    def remove_menu(self, menu_id: str):
        """Remove a registered menu"""
        if menu_id in self.menus:
            del self.menus[menu_id]
            
            # Remove from disk
            config_path = Path.home() / '.omnibar' / 'menus' / f"{menu_id}.json"
            if config_path.exists():
                config_path.unlink()