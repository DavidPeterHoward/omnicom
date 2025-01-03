from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication
import keyboard
import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import threading
import logging

class HotkeyManager(QObject):
    """Manages global and local hotkeys"""
    
    hotkeyTriggered = pyqtSignal(str)  # Emitted when hotkey is triggered
    hotkeyRegistered = pyqtSignal(str)  # Emitted when new hotkey is registered
    hotkeyUnregistered = pyqtSignal(str)  # Emitted when hotkey is unregistered
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger('HotkeyManager')
        
        # Hotkey storage
        self.global_hotkeys: Dict[str, Dict[str, Any]] = {}
        self.local_hotkeys: Dict[str, Dict[str, Any]] = {}
        self.context_hotkeys: Dict[str, Dict[str, Dict[str, Any]]] = {}
        
        # Active context tracking
        self.active_context: Optional[str] = None
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        # Load saved hotkeys
        self._load_hotkeys()
        
    def _load_hotkeys(self):
        """Load hotkey configurations from disk"""
        config_path = Path.home() / '.omnibar' / 'hotkeys.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    self.global_hotkeys = data.get('global', {})
                    self.local_hotkeys = data.get('local', {})
                    self.context_hotkeys = data.get('contexts', {})
                    
                # Register loaded global hotkeys
                for shortcut, config in self.global_hotkeys.items():
                    if config.get('enabled', True):
                        self._register_global_hotkey(shortcut)
                        
            except Exception as e:
                self.logger.error(f"Error loading hotkeys: {e}")
                
    def _save_hotkeys(self):
        """Save hotkey configurations to disk"""
        try:
            config_path = Path.home() / '.omnibar' / 'hotkeys.json'
            data = {
                'global': self.global_hotkeys,
                'local': self.local_hotkeys,
                'contexts': self.context_hotkeys
            }
            
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving hotkeys: {e}")
            
    def _register_global_hotkey(self, shortcut: str):
        """Register a global hotkey with the system"""
        try:
            keyboard.add_hotkey(
                shortcut.lower(),
                lambda s=shortcut: self._handle_global_hotkey(s),
                suppress=True
            )
        except Exception as e:
            self.logger.error(f"Error registering global hotkey {shortcut}: {e}")
            
    def _handle_global_hotkey(self, shortcut: str):
        """Handle global hotkey trigger"""
        try:
            config = self.global_hotkeys.get(shortcut)
            if config and config.get('enabled', True):
                action = config.get('action')
                if callable(action):
                    action()
                self.hotkeyTriggered.emit(shortcut)
        except Exception as e:
            self.logger.error(f"Error handling global hotkey {shortcut}: {e}")
            
    def register_local_hotkey(self, shortcut: str,
                            action: Callable,
                            description: Optional[str] = None):
        """Register a local (application-level) hotkey"""
        with self._lock:
            self.local_hotkeys[shortcut] = {
                'action': action,
                'description': description,
                'enabled': True
            }
            self._save_hotkeys()
            self.hotkeyRegistered.emit(shortcut)

    def register_context_hotkey(self, context: str,
                              shortcut: str,
                              action: Callable,
                              description: Optional[str] = None):
        """Register a context-specific hotkey"""
        with self._lock:
            if context not in self.context_hotkeys:
                self.context_hotkeys[context] = {}
                
            self.context_hotkeys[context][shortcut] = {
                'action': action,
                'description': description,
                'enabled': True
            }
            self._save_hotkeys()
            self.hotkeyRegistered.emit(f"{context}:{shortcut}")

    def set_active_context(self, context: Optional[str]):
        """Set the active hotkey context"""
        self.active_context = context

    def handle_key_event(self, event) -> bool:
        """Handle a key event and return True if handled"""
        # Create shortcut string from event
        modifiers = []
        if event.modifiers() & Qt.ControlModifier:
            modifiers.append('Ctrl')
        if event.modifiers() & Qt.ShiftModifier:
            modifiers.append('Shift')
        if event.modifiers() & Qt.AltModifier:
            modifiers.append('Alt')
        if event.modifiers() & Qt.MetaModifier:
            modifiers.append('Meta')
            
        key = event.text().upper() or QKeySequence(event.key()).toString()
        shortcut = '+'.join(modifiers + [key])

        # Check context hotkeys first
        if self.active_context:
            context_keys = self.context_hotkeys.get(self.active_context, {})
            if shortcut in context_keys:
                config = context_keys[shortcut]
                if config.get('enabled', True):
                    action = config.get('action')
                    if callable(action):
                        action()
                        self.hotkeyTriggered.emit(f"{self.active_context}:{shortcut}")
                        return True

        # Check local hotkeys
        if shortcut in self.local_hotkeys:
            config = self.local_hotkeys[shortcut]
            if config.get('enabled', True):
                action = config.get('action')
                if callable(action):
                    action()
                    self.hotkeyTriggered.emit(shortcut)
                    return True

        return False

    def unregister_hotkey(self, shortcut: str, context: Optional[str] = None):
        """Unregister a hotkey"""
        with self._lock:
            if context:
                if context in self.context_hotkeys:
                    if shortcut in self.context_hotkeys[context]:
                        del self.context_hotkeys[context][shortcut]
                        if not self.context_hotkeys[context]:
                            del self.context_hotkeys[context]
            else:
                if shortcut in self.global_hotkeys:
                    keyboard.remove_hotkey(shortcut.lower())
                    del self.global_hotkeys[shortcut]
                if shortcut in self.local_hotkeys:
                    del self.local_hotkeys[shortcut]
            
            self._save_hotkeys()
            self.hotkeyUnregistered.emit(
                f"{context}:{shortcut}" if context else shortcut
            )

    def enable_hotkey(self, shortcut: str, enabled: bool = True,
                     context: Optional[str] = None):
        """Enable or disable a hotkey"""
        with self._lock:
            if context:
                if context in self.context_hotkeys:
                    if shortcut in self.context_hotkeys[context]:
                        self.context_hotkeys[context][shortcut]['enabled'] = enabled
            else:
                if shortcut in self.global_hotkeys:
                    self.global_hotkeys[shortcut]['enabled'] = enabled
                    if enabled:
                        self._register_global_hotkey(shortcut)
                    else:
                        keyboard.remove_hotkey(shortcut.lower())
                if shortcut in self.local_hotkeys:
                    self.local_hotkeys[shortcut]['enabled'] = enabled
            
            self._save_hotkeys()

    def get_hotkey_info(self, shortcut: str, 
                       context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get information about a registered hotkey"""
        if context:
            if context in self.context_hotkeys:
                return self.context_hotkeys[context].get(shortcut)
        else:
            if shortcut in self.global_hotkeys:
                return self.global_hotkeys[shortcut]
            if shortcut in self.local_hotkeys:
                return self.local_hotkeys[shortcut]
        return None

    def get_context_hotkeys(self, context: str) -> Dict[str, Dict[str, Any]]:
        """Get all hotkeys for a specific context"""
        return self.context_hotkeys.get(context, {}).copy()

    def get_all_hotkeys(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered hotkeys"""
        return {
            'global': self.global_hotkeys.copy(),
            'local': self.local_hotkeys.copy(),
            'contexts': self.context_hotkeys.copy()
        }

    def cleanup(self):
        """Clean up registered hotkeys"""
        with self._lock:
            # Remove all global hotkeys
            for shortcut in self.global_hotkeys:
                try:
                    keyboard.remove_hotkey(shortcut.lower())
                except:
                    pass
            
            # Clear all hotkeys
            self.global_hotkeys.clear()
            self.local_hotkeys.clear()
            self.context_hotkeys.clear()
            
            # Save empty state
            self._save_hotkeys()