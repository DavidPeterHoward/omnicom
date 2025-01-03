from modules.base_module import EnhancedBaseModule
from modules.chemistry import ChemistryModule
from modules.concept import ConceptModule
from modules.nearby_words import NearbyWordsModule
from modules.spelling import SpellingModule
from typing import Dict


def initialize_modules() -> Dict[str, EnhancedBaseModule]:
    """Initialize all available modules"""
    modules = {}
    
    try:
        modules["Nearby Words"] = NearbyWordsModule()
    except Exception as e:
        print(f"Error initializing Nearby Words module: {e}")
    
    try:
        modules["Spelling"] = SpellingModule()
    except Exception as e:
        print(f"Error initializing Spelling module: {e}")
    
    try:
        modules["Concepts"] = ConceptModule()
    except Exception as e:
        print(f"Error initializing Concepts module: {e}")
    
    try:
        modules["Chemistry"] = ChemistryModule()
    except Exception as e:
        print(f"Error initializing Chemistry module: {e}")
    
    return modules


available_modules = initialize_modules()

__all__ = [
    'EnhancedBaseModule',
    'ChemistryModule',
    'ConceptModule',
    'NearbyWordsModule',
    'SpellingModule',
    'available_modules'
]
