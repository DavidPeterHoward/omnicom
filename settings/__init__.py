from settings.pages.utils import load_config, save_config, get_default_config
from settings.pages.main_window import SettingsWindow
from settings.pages.appearance import AppearancePage
from settings.pages.behavior import BehaviorPage
from settings.pages.modules import ModulesPage
from settings.pages.shortcuts import ShortcutsPage

__version__ = "1.0.0"

__all__ = [
    'load_config',
    'save_config',
    'get_default_config',
    'SettingsWindow',
    'AppearancePage',
    'BehaviorPage',
    'ModulesPage',
    'ShortcutsPage'
]
