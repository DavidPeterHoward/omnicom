from pathlib import Path
import json
import pickle
from typing import Dict, Any, Optional
import threading
import logging
from datetime import datetime
import shutil


class StatePersistence:
    """
    Manages persistent state across application sessions
    """
    
    def __init__(self, app_name: str = "Omnibar"):
        self.app_name = app_name
        self.state_dir = Path.home() / '.omnibar' / 'state'
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.state_dir / 'app_state.json'
        self.backup_dir = self.state_dir / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        
        self._lock = threading.Lock()
        self._state: Dict[str, Any] = {}
        self._module_states: Dict[str, Dict[str, Any]] = {}
        
        self.logger = logging.getLogger('StatePersistence')
        self._load_state()

    def _load_state(self):
        """Load state from disk"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self._state = data.get('global', {})
                    self._module_states = data.get('modules', {})
        except Exception as e:
            self.logger.error(f"Error loading state: {e}")
            self._create_backup('error_load')

    def _save_state(self):
        """Save state to disk"""
        try:
            with self._lock:
                state_data = {
                    'global': self._state,
                    'modules': self._module_states,
                    'last_saved': datetime.now().isoformat()
                }
                
                # Save to temporary file first
                temp_file = self.state_file.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(state_data, f, indent=2)
                
                # Rename temporary file to actual file
                temp_file.replace(self.state_file)
                
        except Exception as e:
            self.logger.error(f"Error saving state: {e}")
            self._create_backup('error_save')

    def _create_backup(self, reason: str):
        """Create backup of current state"""
        try:
            if not self.state_file.exists():
                return
                
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f'state_backup_{reason}_{timestamp}.json'
            shutil.copy2(self.state_file, backup_file)
            
            # Clean up old backups
            self._cleanup_backups()
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")

    def _cleanup_backups(self, max_backups: int = 10):
        """Clean up old backup files"""
        try:
            backups = sorted(self.backup_dir.glob('state_backup_*.json'),
                           key=lambda p: p.stat().st_mtime)
                           
            while len(backups) > max_backups:
                backups[0].unlink()
                backups = backups[1:]
        except Exception as e:
            self.logger.error(f"Error cleaning up backups: {e}")

    def get_global_state(self, key: str, default: Any = None) -> Any:
        """Get global state value"""
        with self._lock:
            return self._state.get(key, default)

    def set_global_state(self, key: str, value: Any):
        """Set global state value"""
        with self._lock:
            self._state[key] = value
            self._save_state()

    def get_module_state(self, module_name: str, 
                        key: str, default: Any = None) -> Any:
        """Get module-specific state value"""
        with self._lock:
            module_state = self._module_states.get(module_name, {})
            return module_state.get(key, default)

    def set_module_state(self, module_name: str, key: str, value: Any):
        """Set module-specific state value"""
        with self._lock:
            if module_name not in self._module_states:
                self._module_states[module_name] = {}
            self._module_states[module_name][key] = value
            self._save_state()

    def clear_module_state(self, module_name: str):
        """Clear all state for a specific module"""
        with self._lock:
            if module_name in self._module_states:
                del self._module_states[module_name]
                self._save_state()

    def get_all_module_states(self) -> Dict[str, Dict[str, Any]]:
        """Get all module states"""
        with self._lock:
            return self._module_states.copy()

    def restore_state(self, backup_file: Optional[Path] = None):
        """Restore state from backup"""
        try:
            if backup_file is None:
                # Find most recent backup
                backups = sorted(self.backup_dir.glob('state_backup_*.json'),
                               key=lambda p: p.stat().st_mtime,
                               reverse=True)
                if not backups:
                    raise FileNotFoundError("No backup files found")
                backup_file = backups[0]

            # Create backup of current state
            self._create_backup('pre_restore')

            # Load state from backup
            with open(backup_file, 'r') as f:
                data = json.load(f)
                with self._lock:
                    self._state = data.get('global', {})
                    self._module_states = data.get('modules', {})
                    self._save_state()
                    
        except Exception as e:
            self.logger.error(f"Error restoring state: {e}")
            raise

    def export_state(self, output_path: Path):
        """Export current state to file"""
        try:
            with self._lock:
                state_data = {
                    'global': self._state,
                    'modules': self._module_states,
                    'exported_at': datetime.now().isoformat(),
                    'app_name': self.app_name
                }
                
                with open(output_path, 'w') as f:
                    json.dump(state_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error exporting state: {e}")
            raise

    def import_state(self, input_path: Path, merge: bool = False):
        """Import state from file"""
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)
                
            with self._lock:
                if merge:
                    # Merge with existing state
                    self._state.update(data.get('global', {}))
                    for module, state in data.get('modules', {}).items():
                        if module not in self._module_states:
                            self._module_states[module] = {}
                        self._module_states[module].update(state)
                else:
                    # Replace existing state
                    self._state = data.get('global', {})
                    self._module_states = data.get('modules', {})
                
                self._save_state()
        except Exception as e:
            self.logger.error(f"Error importing state: {e}")
            raise

    def cleanup(self):
        """Perform cleanup operations"""
        try:
            self._save_state()
            self._cleanup_backups()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")