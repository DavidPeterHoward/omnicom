from settings.pages.appearance import AppearancePage
from settings.pages.behavior import BehaviorPage
from settings.pages.modules import ModulesPage
from settings.pages.shortcuts import ShortcutsPage
from settings.pages.main_window import SettingsWindow

__version__ = "1.0.0"
__author__ = "Omnibar Team"

# Page registry for dynamic loading
PAGES = {
    'appearance': AppearancePage,
    'behavior': BehaviorPage,
    'modules': ModulesPage,
    'shortcuts': ShortcutsPage
}


def get_available_pages():
    """Get list of available settings pages"""
    return list(PAGES.keys())


def get_page_class(page_name: str):
    """Get page class by name"""
    return PAGES.get(page_name)


__all__ = [
    'AppearancePage',
    'BehaviorPage',
    'ModulesPage',
    'ShortcutsPage',
    'SettingsWindow',
    'PAGES',
    'get_available_pages',
    'get_page_class'
]
