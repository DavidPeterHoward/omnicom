import json
from pathlib import Path
from typing import Dict, Any

CONFIG_DIR = Path.home() / '.omnibar'
CONFIG_FILE = CONFIG_DIR / 'config.json'

def ensure_config_dir():
    CONFIG_DIR.mkdir(exist_ok=True)

def get_default_config() -> Dict[str, Any]:
    return {
        'font_family': 'Segoe UI',
        'input_font_size': 11,
        'results_font_size': 10,
        'window_width': 650,
        'window_height': 65,
        'remember_position': False,
        'always_on_top': True,
        'show_shadow': True,
        'start_with_windows': False,
        'minimize_to_tray': True,
        'theme': 'Light',
        'activation_shortcut': 'Win+Space',
        'module_settings': {
            'Nearby Words': {
                'enabled': True,
                'max_results': 10,
                'min_similarity': 0.6
            },
            'Spelling': {
                'enabled': True,
                'max_suggestions': 10,
                'use_custom_dict': True
            },
            'Concepts': {
                'enabled': True,
                'web_search_enabled': False,
                'max_results': 10
            },
            'Chemistry': {
                'enabled': True,
                'show_3d': False
            },
            'Multi-domain Search': {
                'enabled': True,
                'domains_enabled': {}
            }
        }
    }

def load_config() -> Dict[str, Any]:
    ensure_config_dir()
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                default_config = get_default_config()
                # Merge with defaults to ensure all settings exist
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict) and key in config:
                        for sub_key, sub_value in value.items():
                            if sub_key not in config[key]:
                                config[key][sub_key] = sub_value
                return config
    except Exception as e:
        print(f"Error loading config: {e}")
    return get_default_config()

def save_config(config: Dict[str, Any]) -> bool:
    ensure_config_dir()
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False