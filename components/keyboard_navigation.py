from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QApplication
from typing import Dict, Set, Optional, Any, List
import json
from pathlib import Path


class NavigationContext:
    """Represents a navigation context with focusable elements"""
    def __init__(self, name: str):
        self.name = name
        self.focusable_widgets: List[QWidget] = []
        self.current_index = -1
        self.enabled = True

    def add_widget(self, widget: QWidget):
        """Add a focusable widget to the context"""
        if widget not in self.focusable_widgets:
            self.focusable_widgets.append(widget)
            widget.setFocusPolicy(Qt.StrongFocus)

    def remove_widget(self, widget: QWidget):
        """Remove a widget from the context"""
        if widget in self.focusable_widgets:
            self.focusable_widgets.remove(widget)

    def clear(self):
        """Clear all widgets from the context"""
        self.focusable_widgets.clear()
        self.current_index = -1

    def next(self) -> Optional[QWidget]:
        """Move to and return the next focusable widget"""
        if not self.focusable_widgets:
            return None

        self.current_index = (self.current_index + 1) % len(self.focusable_widgets)
        return self.focusable_widgets[self.current_index]

    def previous(self) -> Optional[QWidget]:
        """Move to and return the previous focusable widget"""
        if not self.focusable_widgets:
            return None

        self.current_index = (self.current_index - 1) % len(self.focusable_widgets)
        return self.focusable_widgets[self.current_index]

    def current(self) -> Optional[QWidget]:
        """Get current focused widget"""
        if 0 <= self.current_index < len(self.focusable_widgets):
            return self.focusable_widgets[self.current_index]
        return None

class KeyboardNavigator(QObject):
    """Manages keyboard navigation throughout the application"""
    
    contextChanged = pyqtSignal(str)  # Emitted when navigation context changes
    focusChanged = pyqtSignal(QWidget)  # Emitted when focus changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.contexts: Dict[str, NavigationContext] = {}
        self.active_context: Optional[str] = None
        self.shortcut_actions: Dict[str, Any] = {}
        self.modifier_keys: Set[int] = set()
        self._load_shortcuts()

    def _load_shortcuts(self):
        """Load keyboard shortcuts from configuration"""
        config_path = Path.home() / '.omnibar' / 'shortcuts.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    self.shortcut_actions = json.load(f)
            except Exception as e:
                print(f"Error loading shortcuts: {e}")

    def register_context(self, name: str) -> NavigationContext:
        """Register a new navigation context"""
        if name not in self.contexts:
            self.contexts[name] = NavigationContext(name)
        return self.contexts[name]

    def set_active_context(self, name: str):
        """Set the active navigation context"""
        if name in self.contexts:
            self.active_context = name
            self.contextChanged.emit(name)

    def get_active_context(self) -> Optional[NavigationContext]:
        """Get current active context"""
        if self.active_context:
            return self.contexts.get(self.active_context)
        return None

    def register_shortcut(self, key_sequence: str, action: Any):
        """Register a keyboard shortcut"""
        self.shortcut_actions[key_sequence] = action

    def handle_key_press(self, event) -> bool:
        """Handle key press events"""
        key = event.key()
        modifiers = event.modifiers()

        # Track modifier keys
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            self.modifier_keys.add(key)

        # Get active context
        context = self.get_active_context()
        if not context or not context.enabled:
            return False

        # Handle navigation keys
        if key == Qt.Key_Tab and not (modifiers & Qt.ShiftModifier):
            self._focus_next()
            return True
        elif key == Qt.Key_Tab and (modifiers & Qt.ShiftModifier):
            self._focus_previous()
            return True
        elif key == Qt.Key_Escape:
            self._handle_escape()
            return True

        # Check for registered shortcuts
        key_text = QKeySequence(int(modifiers) | key).toString()
        if key_text in self.shortcut_actions:
            action = self.shortcut_actions[key_text]
            if callable(action):
                action()
                return True

        return False

    def handle_key_release(self, event):
        """Handle key release events"""
        key = event.key()
        if key in self.modifier_keys:
            self.modifier_keys.remove(key)

    def _focus_next(self):
        """Focus next widget in current context"""
        context = self.get_active_context()
        if context:
            widget = context.next()
            if widget:
                widget.setFocus(Qt.TabFocusReason)
                self.focusChanged.emit(widget)

    def _focus_previous(self):
        """Focus previous widget in current context"""
        context = self.get_active_context()
        if context:
            widget = context.previous()
            if widget:
                widget.setFocus(Qt.BacktabFocusReason)
                self.focusChanged.emit(widget)

    def _handle_escape(self):
        """Handle escape key press"""
        # Clear focus if possible
        focused = QApplication.focusWidget()
        if focused:
            focused.clearFocus()

        # Emit signal for context-specific handling
        context = self.get_active_context()
        if context and context.current():
            # Let the context handle escape if needed
            pass

class NavigableMixin:
    """Mixin to make widgets keyboard navigable"""
    def __init__(self, context_name: str, navigator: KeyboardNavigator):
        self.navigator = navigator
        self.context_name = context_name
        self.navigation_context = navigator.register_context(context_name)
        self.setup_navigation()

    def setup_navigation(self):
        """Setup navigation for this widget"""
        self.setFocusPolicy(Qt.StrongFocus)
        self.navigation_context.add_widget(self)

    def keyPressEvent(self, event):
        """Handle key press events"""
        if not self.navigator.handle_key_press(event):
            # If not handled by navigator, call parent implementation
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Handle key release events"""
        self.navigator.handle_key_release(event)
        super().keyReleaseEvent(event)

    def focusInEvent(self, event):
        """Handle focus in"""
        super().focusInEvent(event)
        self.navigator.set_active_context(self.context_name)

class NavigableWidget(QWidget, NavigableMixin):
    """Base class for navigable widgets"""
    def __init__(self, context_name: str, navigator: KeyboardNavigator, parent=None):
        QWidget.__init__(self, parent)
        NavigableMixin.__init__(self, context_name, navigator)