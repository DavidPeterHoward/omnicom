import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import shutil
from datetime import datetime
import logging

CONFIG_DIR = Path.home() / '.omnibar'
CONFIG_FILE = CONFIG_DIR / 'config.json'
BACKUP_DIR = CONFIG_DIR / 'backups'

logger = logging.getLogger('settings')


def ensure_config_dirs():
    """Ensure configuration directories exist"""
    CONFIG_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)


def get_default_config() -> Dict[str, Any]:
    """Get default configuration with all new options"""
    return {
        # Appearance
        'theme': 'Light',
        'accent_color': '#2196f3',
        'primary_color': '#1976d2',
        'font_family': 'Segoe UI',
        'input_font_size': 11,
        'results_font_size': 10,
        'window_opacity': 1.0,
        'blur_background': False,
        'show_shadow': True,
        'animate_transitions': True,

        # Window
        'window_width': 650,
        'window_height': 65,
        'remember_position': False,
        'always_on_top': True,
        'show_in_taskbar': True,

        # Behavior
        'startup_behavior': {
            'start_with_windows': False,
            'minimize_to_tray': True,
            'restore_last_query': False,
            'show_on_startup': False
        },

        # Performance
        'typing_delay_ms': 200,
        'min_search_chars': 2,
        'max_results': 10,
        'cache_enabled': True,
        'cache_size_mb': 100,

        # Search
        'instant_search': True,
        'fuzzy_match': True,
        'show_icons': True,
        'group_results': True,
        'show_descriptions': True,

        # History
        'save_history': True,
        'history_size': 100,
        'auto_clear_history': False,
        'history_retention_days': 30,

        # Keyboard
        'activation_shortcut': 'Win+Space',
        'keyboard_navigation': {
            'enabled': True,
            'wrap_around': True,
            'arrow_keys': True,
            'tab_navigation': True
        },

        # Modules
        'module_settings': {
            'Chemistry': {
                'enabled': True,
                'auto_show_viewer': True,
                'cache_structures': True,
                'debounce_delay': 300
            },
            'Concepts': {
                'enabled': True,
                'web_enabled': False,
                'max_depth': 3,
                'show_mindmap': True
            },
            'Nearby Words': {
                'enabled': True,
                'show_definitions': True,
                'tts_enabled': True,
                'max_suggestions': 10
            },
            'Spelling': {
                'enabled': True,
                'min_similarity': 0.7,
                'show_definitions': True,
                'show_related_words': True
            }
        },

        # Error Handling
        'error_reporting': {
            'enabled': True,
            'include_system_info': True,
            'auto_send': False
        },

        # Advanced
        'advanced': {
            'debug_mode': False,
            'log_level': 'INFO',
            'max_memory_mb': 512,
            'cleanup_interval': 3600
        }
    }

def load_config() -> Dict[str, Any]:
    """Load configuration with backup handling"""
    ensure_config_dirs()
    config = get_default_config()

    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                user_config = json.load(f)
                config = deep_update(config, user_config)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        _create_backup('error_load')
        
    return config

def save_config(config: Dict[str, Any], create_backup: bool = True) -> bool:
    """Save configuration with optional backup"""
    ensure_config_dirs()
    try:
        if create_backup and CONFIG_FILE.exists():
            _create_backup('pre_save')

        # Save to temporary file first
        temp_file = CONFIG_FILE.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(config, f, indent=4)

        # Rename temporary file to actual config file
        temp_file.replace(CONFIG_FILE)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

def deep_update(base: dict, update: dict) -> dict:
    """Deep update a nested dictionary"""
    for key, value in update.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            base[key] = deep_update(base[key], value)
        else:
            base[key] = value
    return base

def _create_backup(reason: str):
    """Create a backup of current configuration"""
    if CONFIG_FILE.exists():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = BACKUP_DIR / f'config_backup_{reason}_{timestamp}.json'
        shutil.copy2(CONFIG_FILE, backup_file)
        _cleanup_backups()

def _cleanup_backups(max_backups: int = 10):
    """Clean up old backup files"""
    backups = sorted(
        BACKUP_DIR.glob('config_backup_*.json'),
        key=lambda p: p.stat().st_mtime
    )
    
    while len(backups) > max_backups:
        backups[0].unlink()
        backups = backups[1:]

def import_config(file_path: Path, merge: bool = False) -> bool:
    """Import configuration from file"""
    try:
        with open(file_path, 'r') as f:
            imported_config = json.load(f)

        if merge:
            current_config = load_config()
            config = deep_update(current_config, imported_config)
        else:
            config = deep_update(get_default_config(), imported_config)

        return save_config(config)

    except Exception as e:
        logger.error(f"Error importing config: {e}")
        return False

def export_config(file_path: Path) -> bool:
    """Export current configuration"""
    try:
        config = load_config()
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error exporting config: {e}")
        return False

def reset_config() -> bool:
    """Reset configuration to defaults"""
    try:
        _create_backup('pre_reset')
        return save_config(get_default_config(), create_backup=False)
    except Exception as e:
        logger.error(f"Error resetting config: {e}")
        return False

def get_config_path() -> Path:
    """Get path to configuration file"""
    return CONFIG_FILE

def validate_config(config: Dict[str, Any]):
    """Validate configuration structure and values"""
    try:
        default_config = get_default_config()
        
        # Check all required keys exist
        for key, value in default_config.items():
            if key not in config:
                return False, f"Missing required key: {key}"
            
            if isinstance(value, dict):
                if not isinstance(config[key], dict):
                    return False, f"Invalid type for key {key}"
                    
                # Recursively check nested dictionaries
                for sub_key in value.keys():
                    if sub_key not in config[key]:
                        return False, f"Missing required sub-key: {key}.{sub_key}"
        
        return True, ""
    except Exception as e:
        return False, f"Error validating config: {str(e)}"